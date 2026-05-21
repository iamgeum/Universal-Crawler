"""SQLite 저장소 — Job, Event Log, Selector Memory, Telemetry."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import config
from core.schema import CrawlEvent, CrawlJob, CrawlResult, CrawlStrategy, JobState


class StorageError(Exception):
    """SQLite 저장소 오류."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    engine          TEXT NOT NULL,
    content_type    TEXT,
    state           TEXT NOT NULL,
    retry_count     INTEGER DEFAULT 0,
    error_msg       TEXT,
    brain_used      TEXT,
    strategy_json   TEXT,
    result_json     TEXT,
    partial         INTEGER DEFAULT 0,
    duration_ms     INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crawl_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER,
    event_type  TEXT,
    payload     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id)
);

CREATE TABLE IF NOT EXISTS selector_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    domain      TEXT NOT NULL,
    selector    TEXT NOT NULL,
    status      TEXT NOT NULL,
    hit_count   INTEGER DEFAULT 1,
    last_seen   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry (
    domain              TEXT PRIMARY KEY,
    total_attempts      INTEGER DEFAULT 0,
    success_count       INTEGER DEFAULT 0,
    partial_count       INTEGER DEFAULT 0,
    fallback_count      INTEGER DEFAULT 0,
    captcha_count       INTEGER DEFAULT 0,
    avg_duration_ms     REAL,
    last_updated        DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def ensure_dirs() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_TEXT.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_VIDEOS.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Optional[Path] = None) -> Path:
    """DB 파일 및 테이블 생성."""
    ensure_dirs()
    path = db_path or config.DB_PATH
    with _connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    return path


@contextmanager
def _connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def save_job(job: CrawlJob, db_path: Optional[Path] = None) -> CrawlJob:
    """Job INSERT 또는 UPDATE."""
    now = _utc_now()
    strategy_json = job.strategy.model_dump_json()
    result_json = job.result.model_dump_json() if job.result else None

    with _connect(db_path) as conn:
        if job.id is None:
            cur = conn.execute(
                """
                INSERT INTO crawl_jobs (
                    url, engine, content_type, state, retry_count, error_msg,
                    brain_used, strategy_json, result_json, partial, duration_ms,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.url,
                    job.engine,
                    job.content_type,
                    job.state.value,
                    job.retry_count,
                    job.error_msg,
                    job.brain_used,
                    strategy_json,
                    result_json,
                    int(job.partial),
                    job.duration_ms,
                    now,
                    now,
                ),
            )
            job.id = cur.lastrowid
        else:
            conn.execute(
                """
                UPDATE crawl_jobs SET
                    url=?, engine=?, content_type=?, state=?, retry_count=?,
                    error_msg=?, brain_used=?, strategy_json=?, result_json=?,
                    partial=?, duration_ms=?, updated_at=?
                WHERE id=?
                """,
                (
                    job.url,
                    job.engine,
                    job.content_type,
                    job.state.value,
                    job.retry_count,
                    job.error_msg,
                    job.brain_used,
                    strategy_json,
                    result_json,
                    int(job.partial),
                    job.duration_ms,
                    now,
                    job.id,
                ),
            )
        conn.commit()
    return job


def load_job(job_id: int, db_path: Optional[Path] = None) -> Optional[CrawlJob]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM crawl_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    if not row:
        return None
    return _row_to_job(row)


def log_event(event: CrawlEvent, db_path: Optional[Path] = None) -> int:
    """마스킹된 payload를 Event Log에 append."""
    masked = CrawlEvent(
        job_id=event.job_id,
        event_type=event.event_type,
        payload=event.payload,
    )
    payload_json = json.dumps(masked.payload, ensure_ascii=False)

    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO crawl_events (job_id, event_type, payload)
            VALUES (?, ?, ?)
            """,
            (masked.job_id, masked.event_type, payload_json),
        )
        conn.commit()
        return cur.lastrowid


def db_stats(db_path: Optional[Path] = None) -> dict[str, int]:
    with _connect(db_path) as conn:
        jobs = conn.execute("SELECT COUNT(*) AS c FROM crawl_jobs").fetchone()["c"]
        events = conn.execute("SELECT COUNT(*) AS c FROM crawl_events").fetchone()["c"]
        selectors = conn.execute(
            "SELECT COUNT(*) AS c FROM selector_memory"
        ).fetchone()["c"]
        telemetry = conn.execute("SELECT COUNT(*) AS c FROM telemetry").fetchone()["c"]
    return {
        "crawl_jobs": jobs,
        "crawl_events": events,
        "selector_memory": selectors,
        "telemetry": telemetry,
    }


def _row_to_job(row: sqlite3.Row) -> CrawlJob:
    strategy = CrawlStrategy.model_validate_json(row["strategy_json"])
    result = None
    if row["result_json"]:
        result = CrawlResult.model_validate_json(row["result_json"])
    return CrawlJob(
        id=row["id"],
        url=row["url"],
        engine=row["engine"],
        content_type=row["content_type"],
        state=JobState(row["state"]),
        retry_count=row["retry_count"],
        error_msg=row["error_msg"],
        brain_used=row["brain_used"],
        strategy=strategy,
        result=result,
        partial=bool(row["partial"]),
        duration_ms=row["duration_ms"],
    )
