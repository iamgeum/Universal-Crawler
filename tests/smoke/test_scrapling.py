"""Scrapling 엔진 스모크 테스트 (네트워크 필요 시 skip)."""

import sqlite3
from pathlib import Path

import pytest

from core import storage
from core.runner import run_job
from core.schema import CrawlJob, CrawlStrategy, JobState

@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("config.DB_PATH", db_file)
    storage.init_db(db_file)
    return db_file


def test_scrapling_live_fetch_example_com(temp_db, monkeypatch):
    """example.com 실제 fetch (robots 허용)."""
    monkeypatch.setattr("config.RESPECT_ROBOTS_TXT", True)

    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(engine="scrapling", timeout=30),
    )
    job = storage.save_job(job, temp_db)

    result_job = run_job(job)
    assert result_job.state == JobState.COMPLETED
    assert result_job.result is not None
    assert result_job.result.success
    assert result_job.result.extracted_fields.get("title")

    try:
        row = storage.load_job(result_job.id, temp_db)
        assert row is not None
        assert row.state == JobState.COMPLETED
        assert storage.db_stats(temp_db)["crawl_events"] >= 2
    except sqlite3.Error as exc:
        pytest.fail(f"storage read failed: {exc}")
