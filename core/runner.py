"""Job 실행 — policy → engine(+fallback) → storage/telemetry."""

from __future__ import annotations

import sqlite3
from typing import Optional

from core import cascade, storage, telemetry
from core.logger import get_logger
from core.policy import PolicyChecker, PolicyError, default_checker
from core.router import apply_routing
from core.schema import CrawlEvent, CrawlJob, CrawlResult, JobState
from engines.gallery_engine import GalleryDlEngine
from engines.patchright_engine import PatchrightEngine
from engines.scrapling_engine import ScraplingEngine
from engines.ytdlp_engine import YtdlpEngine

import config

logger = get_logger(__name__)

_ENGINE_REGISTRY = {
    "scrapling": ScraplingEngine(),
    "yt-dlp": YtdlpEngine(),
    "gallery-dl": GalleryDlEngine(),
    "patchright": PatchrightEngine(),
}


class RunnerError(Exception):
    """Job 실행 실패."""


def get_engine(name: str):
    return _ENGINE_REGISTRY.get(name)


def list_runnable_engines() -> list[str]:
    return list(_ENGINE_REGISTRY.keys())


def _fallback_chain(job: CrawlJob) -> list[str]:
    """실행 순서: primary → fallback_chain (등록된 엔진만)."""
    primary = job.strategy.engine
    chain = [primary]
    for name in job.strategy.fallback_chain:
        if name not in chain and name in _ENGINE_REGISTRY:
            chain.append(name)
    return chain


def _execute_engine(job: CrawlJob, engine_name: str) -> CrawlResult:
    plugin = get_engine(engine_name)
    if plugin is None:
        return CrawlResult(
            success=False,
            partial=False,
            content_type="text",
            errors=[f"Engine not registered: {engine_name}"],
            telemetry={"engine": engine_name},
        )
    job.engine = engine_name
    return plugin.execute(job)


def _apply_result(job: CrawlJob, result: CrawlResult, engine_name: str) -> None:
    job.result = result
    job.duration_ms = result.telemetry.get("duration_ms")
    job.content_type = result.content_type
    job.partial = result.partial

    if result.success:
        if result.partial:
            job.transition_to(JobState.PARTIAL_SUCCESS)
            job.resolve_partial_success()
        else:
            job.transition_to(JobState.COMPLETED)
    else:
        job.error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
        if job.state == JobState.RUNNING:
            job.transition_to(JobState.FAILED)


def _log_storage(job: CrawlJob, event_type: str, payload: dict) -> None:
    storage.save_job(job)
    storage.log_event(
        CrawlEvent(job_id=job.id, event_type=event_type, payload=payload)
    )


def run_job(
    job: CrawlJob,
    *,
    policy: PolicyChecker | None = None,
) -> CrawlJob:
    """단일 Job 실행. 실패 시 fallback_chain 및 retry_policy 적용."""
    checker = policy or default_checker

    try:
        checker.check_url(job.url)
    except PolicyError as exc:
        raise RunnerError(str(exc)) from exc

    if job.state == JobState.QUEUED:
        job.transition_to(JobState.RUNNING)

    chain = _fallback_chain(job)
    max_retries = job.strategy.retry_policy.max_retries
    last_result: Optional[CrawlResult] = None
    used_fallback = False

    try:
        _log_storage(
            job,
            "engine_started",
            {"engines_planned": chain, "url": job.url},
        )
    except (sqlite3.Error, storage.StorageError) as exc:
        raise RunnerError(f"Storage error before crawl: {exc}") from exc

    for idx, engine_name in enumerate(chain):
        if idx > 0:
            used_fallback = True
            if job.state == JobState.FAILED:
                job.transition_to(JobState.WAITING_RETRY)
            job.transition_to(JobState.FALLBACK)
            try:
                storage.log_event(
                    CrawlEvent(
                        job_id=job.id,
                        event_type="fallback_triggered",
                        payload={
                            "from_engine": chain[idx - 1],
                            "to_engine": engine_name,
                        },
                    )
                )
            except (sqlite3.Error, storage.StorageError) as exc:
                raise RunnerError(f"Storage error on fallback log: {exc}") from exc

        # primary 실패 후 재시도 (동일 엔진)
        attempts = 1 + (max_retries if idx == 0 else 0)
        for attempt in range(attempts):
            if idx == 0 and attempt > 0:
                if job.state == JobState.FAILED:
                    job.transition_to(JobState.WAITING_RETRY)
                job.transition_to(JobState.RUNNING)
                job.retry_count += 1

            last_result = _execute_engine(job, engine_name)
            job.engine = engine_name
            _apply_result(job, last_result, engine_name)

            try:
                _log_storage(
                    job,
                    "engine_finished",
                    {
                        "engine": engine_name,
                        "success": last_result.success,
                        "attempt": attempt + 1,
                    },
                )
            except (sqlite3.Error, storage.StorageError) as exc:
                raise RunnerError(f"Storage error during crawl: {exc}") from exc

            if last_result.success:
                break
            if idx == 0 and attempt < attempts - 1:
                logger.info(
                    "Job #%s retry %s/%s on %s",
                    job.id,
                    attempt + 1,
                    max_retries,
                    engine_name,
                )

        if last_result and last_result.success:
            break

    if not last_result:
        raise RunnerError("No engine executed")

    # 대→소: 전 엔진 실패 시 LLM recover 후 1회 추가 시도
    if (
        not last_result.success
        and config.USE_CASCADE
        and job.state == JobState.FAILED
    ):
        recovered, recover_brain = cascade.cascade_recover(
            job.url,
            job.error_msg or "unknown",
            {"strategy": job.strategy.model_dump()},
        )
        if recovered and recovered.engine in _ENGINE_REGISTRY:
            try:
                storage.log_event(
                    CrawlEvent(
                        job_id=job.id,
                        event_type="recover_planned",
                        payload={
                            "brain": recover_brain,
                            "engine": recovered.engine,
                        },
                    )
                )
                job.strategy = apply_routing(job.url, recovered)
                job.brain_used = recover_brain or job.brain_used
                job.transition_to(JobState.WAITING_RETRY)
                job.transition_to(JobState.FALLBACK)
                last_result = _execute_engine(job, recovered.engine)
                job.engine = recovered.engine
                _apply_result(job, last_result, recovered.engine)
                used_fallback = True
            except (sqlite3.Error, storage.StorageError) as exc:
                logger.warning("Recover execution storage error: %s", exc)

    try:
        storage.log_event(
            CrawlEvent(
                job_id=job.id,
                event_type="job_completed" if last_result.success else "job_failed",
                payload={
                    "engine": job.engine,
                    "success": last_result.success,
                    "errors": last_result.errors,
                    "used_fallback": used_fallback,
                },
            )
        )
        telemetry.record_crawl(
            job.url,
            success=last_result.success,
            partial=last_result.partial,
            fallback=used_fallback,
            duration_ms=job.duration_ms,
        )
    except (sqlite3.Error, storage.StorageError) as exc:
        raise RunnerError(f"Storage error after crawl: {exc}") from exc

    logger.info(
        "Job #%s %s engine=%s fallback=%s",
        job.id,
        job.state.value,
        job.engine,
        used_fallback,
    )
    return job
