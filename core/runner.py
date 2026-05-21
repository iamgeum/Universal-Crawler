"""Job 실행 — policy → engine → storage/telemetry."""

from __future__ import annotations

import sqlite3
from typing import Optional

from core import storage, telemetry
from core.logger import get_logger
from core.policy import PolicyChecker, PolicyError, default_checker
from core.schema import CrawlEvent, CrawlJob, CrawlResult, JobState
from engines.scrapling_engine import ScraplingEngine

logger = get_logger(__name__)

# Phase 1b: scrapling만 실행 가능
_ENGINE_REGISTRY = {
    "scrapling": ScraplingEngine(),
}


class RunnerError(Exception):
    """Job 실행 실패."""


def get_engine(name: str):
    return _ENGINE_REGISTRY.get(name)


def run_job(
    job: CrawlJob,
    *,
    policy: PolicyChecker | None = None,
) -> CrawlJob:
    """단일 Job 실행 후 상태·결과 반영."""
    checker = policy or default_checker
    engine_name = job.strategy.engine

    try:
        checker.check_url(job.url)
    except PolicyError as exc:
        raise RunnerError(str(exc)) from exc

    plugin = get_engine(engine_name)
    if plugin is None:
        raise RunnerError(
            f"Engine '{engine_name}' is not runnable in Phase 1b "
            f"(queued/routed only). Available: {list(_ENGINE_REGISTRY)}"
        )

    if job.state == JobState.QUEUED:
        job.transition_to(JobState.RUNNING)

    try:
        storage.save_job(job)
        storage.log_event(
            CrawlEvent(
                job_id=job.id,
                event_type="engine_started",
                payload={"engine": engine_name, "url": job.url},
            )
        )
    except (sqlite3.Error, storage.StorageError) as exc:
        raise RunnerError(f"Storage error before crawl: {exc}") from exc

    result: CrawlResult = plugin.execute(job)
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
        job.transition_to(JobState.FAILED)

    try:
        storage.save_job(job)
        storage.log_event(
            CrawlEvent(
                job_id=job.id,
                event_type="job_completed" if result.success else "job_failed",
                payload={
                    "engine": engine_name,
                    "success": result.success,
                    "errors": result.errors,
                },
            )
        )
        telemetry.record_crawl(
            job.url,
            success=result.success,
            partial=result.partial,
            duration_ms=job.duration_ms,
        )
    except (sqlite3.Error, storage.StorageError) as exc:
        raise RunnerError(f"Storage error after crawl: {exc}") from exc

    logger.info(
        "Job #%s %s engine=%s",
        job.id,
        job.state.value,
        engine_name,
    )
    return job
