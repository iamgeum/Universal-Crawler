#!/usr/bin/env python3
"""Universal Crawler CLI."""

from __future__ import annotations

import argparse
import sqlite3
import sys

import config
from core import storage
from core.brains import heuristic
from core.logger import get_logger, setup_logging
from core.policy import PolicyError, default_checker
from core.runner import RunnerError, run_job
from core.schema import CrawlEvent, CrawlJob, JobState

logger = get_logger(__name__)

# Phase 1b에서 즉시 실행 가능한 엔진
RUNNABLE_ENGINES = {"scrapling"}


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


def _enqueue_url(url: str) -> CrawlJob:
    """정책 검사 + heuristic 라우팅 후 Job 저장."""
    default_checker.check_url(url)
    strategy = heuristic.build_strategy(url)
    job = CrawlJob(
        url=url,
        engine=strategy.engine,
        state=JobState.QUEUED,
        strategy=strategy,
        brain_used="heuristic",
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
            },
        )
    )
    return job


def cmd_enqueue(args: argparse.Namespace) -> int:
    _ensure_db()
    try:
        job = _enqueue_url(args.url)
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
            f"  note: engine '{job.engine}' is routed but not runnable until Phase 1c+",
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


def cmd_crawl(args: argparse.Namespace) -> int:
    """enqueue + run (scrapling 대상만)."""
    _ensure_db()
    try:
        job = _enqueue_url(args.url)
    except PolicyError as exc:
        print(f"Policy blocked: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, storage.StorageError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1

    print(f"Job #{job.id} queued → engine={job.engine}")

    if job.engine not in RUNNABLE_ENGINES:
        print(
            f"Cannot crawl: engine '{job.engine}' not available in Phase 1b. "
            f"Use a general HTML URL or wait for Phase 1c.",
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
    if job.result and job.result.extracted_fields.get("title"):
        print(f"  title={job.result.extracted_fields['title']}")
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

    p_enqueue = sub.add_parser("enqueue", help="URL을 Job 큐에 등록 (heuristic 라우팅)")
    p_enqueue.add_argument("url", help="크롤 대상 URL")
    p_enqueue.set_defaults(func=cmd_enqueue)

    p_run = sub.add_parser("run", help="queued Job 실행")
    p_run.add_argument("job_id", type=int, help="Job ID")
    p_run.set_defaults(func=cmd_run)

    p_crawl = sub.add_parser("crawl", help="URL 등록 후 즉시 실행 (scrapling)")
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
