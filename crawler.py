#!/usr/bin/env python3
"""Universal Crawler CLI."""

from __future__ import annotations

import argparse
import sys

import config
from core.schema import CrawlEvent, CrawlJob, CrawlStrategy, JobState
from core import storage


def cmd_init_db(_: argparse.Namespace) -> int:
    path = storage.init_db()
    print(f"Database initialized: {path}")
    stats = storage.db_stats()
    for table, count in stats.items():
        print(f"  {table}: {count} rows")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    if not config.DB_PATH.exists():
        print(f"Database not found. Run: python crawler.py init-db")
        print(f"Expected path: {config.DB_PATH}")
        return 1
    stats = storage.db_stats()
    print(f"Database: {config.DB_PATH}")
    for table, count in stats.items():
        print(f"  {table}: {count}")
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    """URL을 Job 큐에 등록 (Phase 1b에서 엔진 실행 연결)."""
    if not config.DB_PATH.exists():
        storage.init_db()

    strategy = CrawlStrategy(
        engine="scrapling",
        reason="CLI enqueue (engine routing in Phase 1b)",
    )
    job = CrawlJob(
        url=args.url,
        engine=strategy.engine,
        state=JobState.QUEUED,
        strategy=strategy,
        brain_used=config.ACTIVE_BRAIN,
    )
    job = storage.save_job(job)
    storage.log_event(
        CrawlEvent(job_id=job.id, event_type="job_created", payload={"url": args.url})
    )
    print(f"Job #{job.id} queued: {args.url}")
    print(f"  engine={job.engine}  state={job.state.value}")
    return 0


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

    p_enqueue = sub.add_parser("enqueue", help="URL을 Job 큐에 등록")
    p_enqueue.add_argument("url", help="크롤 대상 URL")
    p_enqueue.set_defaults(func=cmd_enqueue)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
