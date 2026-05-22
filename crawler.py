#!/usr/bin/env python3
"""Universal Crawler CLI."""

from __future__ import annotations

import argparse
import sqlite3
import sys

import config
from core import storage
from core import planner
from core.logger import get_logger, setup_logging
from core.policy import PolicyError, default_checker
from core.runner import RunnerError, list_runnable_engines, run_job
from core.schema import CrawlEvent, CrawlJob, JobState

logger = get_logger(__name__)

RUNNABLE_ENGINES = set(list_runnable_engines())


def _ensure_db() -> None:
    if not config.DB_PATH.exists():
        storage.init_db()


def cmd_init_db(_: argparse.Namespace) -> int:
    try:
        path = storage.init_db()
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
    print(f"Database initialized: {path}")
    try:
        stats = storage.db_stats()
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
    for table, count in stats.items():
        print(f"  {table}: {count} rows")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    if not config.DB_PATH.exists():
        print("Database not found. Run: python crawler.py init-db")
        print(f"Expected path: {config.DB_PATH}")
        return 1
    try:
        stats = storage.db_stats()
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
    print(f"Database: {config.DB_PATH}")
    for table, count in stats.items():
        print(f"  {table}: {count}")
    return 0


def _enqueue_url(
    url: str,
    *,
    planner_mode: planner.PlannerMode = "auto",
    required_capabilities: list[str] | None = None,
) -> CrawlJob:
    """정책 검사 + planner(heuristic/ollama) + Dual-key 라우팅 후 Job 저장."""
    default_checker.check_url(url)
    strategy, brain_used = planner.plan_for_job(
        url,
        mode=planner_mode,
        required_capabilities=required_capabilities,
    )
    job = CrawlJob(
        url=url,
        engine=strategy.engine,
        state=JobState.QUEUED,
        strategy=strategy,
        brain_used=brain_used,
    )
    job = storage.save_job(job)
    storage.log_event(
        CrawlEvent(
            job_id=job.id,
            event_type="job_created",
            payload={
                "url": url,
                "engine": strategy.engine,
                "reason": strategy.reason,
                "brain_used": brain_used,
                "routing": strategy.telemetry_tags,
            },
        )
    )
    return job


def cmd_plan(args: argparse.Namespace) -> int:
    """전략만 생성 (DB 저장 없음)."""
    try:
        default_checker.check_url(args.url)
    except PolicyError as exc:
        print(f"Policy blocked: {exc}", file=sys.stderr)
        return 1
    caps = args.capabilities.split(",") if args.capabilities else None
    if caps:
        caps = [c.strip() for c in caps if c.strip()]
    try:
        strategy, brain_used = planner.plan_for_job(
            args.url,
            mode=args.planner,
            required_capabilities=caps,
        )
    except Exception as exc:
        print(f"Plan failed: {exc}", file=sys.stderr)
        return 1
    print(f"brain={brain_used}")
    print(f"engine={strategy.engine}")
    print(f"reason={strategy.reason}")
    print(f"fallback_chain={strategy.fallback_chain}")
    print(f"required_capabilities={strategy.required_capabilities}")
    print(strategy.model_dump_json(indent=2))
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    _ensure_db()
    caps = _parse_capabilities(args)
    try:
        job = _enqueue_url(args.url, planner_mode=args.planner, required_capabilities=caps)
    except PolicyError as exc:
        print(f"Policy blocked: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    print(f"Job #{job.id} queued: {args.url}")
    print(f"  engine={job.engine}  state={job.state.value}")
    print(f"  reason={job.strategy.reason}")
    if job.engine not in RUNNABLE_ENGINES:
        print(
            f"  note: engine '{job.engine}' is not runnable (available: {sorted(RUNNABLE_ENGINES)})",
            file=sys.stderr,
        )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _ensure_db()
    try:
        job = storage.load_job(args.job_id)
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    if not job:
        print(f"Job #{args.job_id} not found", file=sys.stderr)
        return 1
    if job.state != JobState.QUEUED:
        print(
            f"Job #{args.job_id} is '{job.state.value}' (expected 'queued')",
            file=sys.stderr,
        )
        return 1

    try:
        job = run_job(job)
    except (PolicyError, RunnerError) as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    print(f"Job #{job.id} finished: {job.state.value}")
    if job.result:
        print(f"  success={job.result.success}  title={job.result.extracted_fields.get('title')}")
    if job.error_msg:
        print(f"  error={job.error_msg}", file=sys.stderr)
    return 0 if job.state == JobState.COMPLETED else 1


def _parse_capabilities(args: argparse.Namespace) -> list[str] | None:
    raw = getattr(args, "capabilities", None)
    if not raw:
        return None
    return [c.strip() for c in raw.split(",") if c.strip()]


def cmd_crawl(args: argparse.Namespace) -> int:
    """enqueue + run (planner + Dual-key + fallback)."""
    _ensure_db()
    caps = _parse_capabilities(args)
    try:
        job = _enqueue_url(args.url, planner_mode=args.planner, required_capabilities=caps)
    except PolicyError as exc:
        print(f"Policy blocked: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    print(f"Job #{job.id} queued → engine={job.engine}")
    print(f"  fallback_chain={job.strategy.fallback_chain}")

    if job.engine not in RUNNABLE_ENGINES:
        print(
            f"Cannot crawl: engine '{job.engine}' not runnable. "
            f"Available: {sorted(RUNNABLE_ENGINES)}",
            file=sys.stderr,
        )
        return 1

    try:
        job = run_job(job)
    except (PolicyError, RunnerError) as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    print(f"Job #{job.id} finished: {job.state.value} (engine={job.engine})")
    if job.result:
        r = job.result
        if r.extracted_fields.get("title"):
            print(f"  title={r.extracted_fields['title']}")
        if r.images:
            print(f"  images={len(r.images)} url(s)")
        if r.videos:
            print(f"  videos={len(r.videos)}")
    if job.error_msg:
        print(f"  error={job.error_msg}", file=sys.stderr)
    return 0 if job.state == JobState.COMPLETED else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="Universal Crawler — 범용 웹 크롤링 프레임워크",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="SQLite DB 및 테이블 초기화")
    p_init.set_defaults(func=cmd_init_db)

    p_status = sub.add_parser("status", help="DB 상태 확인")
    p_status.set_defaults(func=cmd_status)

    planner_args = argparse.ArgumentParser(add_help=False)
    planner_args.add_argument(
        "--planner",
        choices=("auto", "heuristic", "ollama", "cascade"),
        default="auto",
        help="auto=캐스케이드(휴리스틱→Ollama), cascade=+클라우드소형, heuristic, ollama",
    )
    planner_args.add_argument(
        "--capabilities",
        "-c",
        default=None,
        help="Dual-key 2차: 쉼표 구분 capability (예: video,static_html)",
    )

    p_plan = sub.add_parser("plan", help="CrawlStrategy만 생성 (저장 없음)")
    p_plan.add_argument("url", help="대상 URL")
    p_plan.add_argument(
        "--planner",
        choices=("auto", "heuristic", "ollama", "cascade"),
        default="auto",
    )
    p_plan.add_argument("--capabilities", "-c", default=None)
    p_plan.set_defaults(func=cmd_plan)

    p_enqueue = sub.add_parser(
        "enqueue",
        help="URL을 Job 큐에 등록 (planner + Dual-key)",
        parents=[planner_args],
    )
    p_enqueue.add_argument("url", help="크롤 대상 URL")
    p_enqueue.set_defaults(func=cmd_enqueue)

    p_run = sub.add_parser("run", help="queued Job 실행")
    p_run.add_argument("job_id", type=int, help="Job ID")
    p_run.set_defaults(func=cmd_run)

    p_crawl = sub.add_parser(
        "crawl",
        help="URL 등록 후 즉시 실행",
        parents=[planner_args],
    )
    p_crawl.add_argument("url", help="크롤 대상 URL")
    p_crawl.set_defaults(func=cmd_crawl)

    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
