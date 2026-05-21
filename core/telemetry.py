"""Telemetry 집계 — 도메인별 성공/실패 통계."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from core import storage
from core.logger import get_logger

logger = get_logger(__name__)


def _domain_from_url(url: str) -> str:
    return (urlparse(url).hostname or urlparse(url).netloc or "unknown").lower()


def record_crawl(
    url: str,
    *,
    success: bool,
    partial: bool = False,
    fallback: bool = False,
    captcha: bool = False,
    duration_ms: Optional[int] = None,
    db_path=None,
) -> None:
    """crawl 완료 후 telemetry 테이블 UPSERT."""
    domain = _domain_from_url(url)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    try:
        with storage._connect(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM telemetry WHERE domain = ?", (domain,)
            ).fetchone()

            if row is None:
                conn.execute(
                    """
                    INSERT INTO telemetry (
                        domain, total_attempts, success_count, partial_count,
                        fallback_count, captcha_count, avg_duration_ms, last_updated
                    ) VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        domain,
                        1 if success else 0,
                        1 if partial else 0,
                        1 if fallback else 0,
                        1 if captcha else 0,
                        float(duration_ms) if duration_ms is not None else None,
                        now,
                    ),
                )
            else:
                total = row["total_attempts"] + 1
                success_count = row["success_count"] + (1 if success else 0)
                partial_count = row["partial_count"] + (1 if partial else 0)
                fallback_count = row["fallback_count"] + (1 if fallback else 0)
                captcha_count = row["captcha_count"] + (1 if captcha else 0)

                old_avg = row["avg_duration_ms"]
                if duration_ms is not None and old_avg is not None:
                    avg = old_avg + (duration_ms - old_avg) / total
                elif duration_ms is not None:
                    avg = float(duration_ms)
                else:
                    avg = old_avg

                conn.execute(
                    """
                    UPDATE telemetry SET
                        total_attempts=?, success_count=?, partial_count=?,
                        fallback_count=?, captcha_count=?, avg_duration_ms=?,
                        last_updated=?
                    WHERE domain=?
                    """,
                    (
                        total,
                        success_count,
                        partial_count,
                        fallback_count,
                        captcha_count,
                        avg,
                        now,
                        domain,
                    ),
                )
            conn.commit()
    except sqlite3.Error as exc:
        logger.warning("telemetry record failed for %s: %s", domain, exc)
