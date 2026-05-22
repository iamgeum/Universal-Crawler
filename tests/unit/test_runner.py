"""runner.py 단위 테스트."""

from unittest.mock import patch

import pytest

from core.runner import run_job
from core.schema import CrawlJob, CrawlResult, CrawlStrategy, JobState, RetryPolicy


@patch("core.runner.storage")
@patch("core.runner.telemetry")
@patch("core.runner.default_checker")
def test_run_job_primary_fails_without_fallback(mock_policy, mock_telemetry, mock_storage):
    mock_policy.check_url.return_value = None

    job = CrawlJob(
        id=1,
        url="https://example.com",
        engine="scrapling",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(
            engine="scrapling",
            fallback_chain=[],
            retry_policy=RetryPolicy(max_retries=0),
        ),
    )

    fail = CrawlResult(
        success=False,
        partial=False,
        content_type="text",
        errors=["fail"],
        telemetry={"duration_ms": 1},
    )

    with patch("core.runner._execute_engine", return_value=fail):
        result = run_job(job)

    assert result.state == JobState.FAILED


@patch("core.runner.storage")
@patch("core.runner.telemetry")
@patch("core.runner.default_checker")
def test_run_job_scrapling_success(mock_policy, mock_telemetry, mock_storage):
    mock_policy.check_url.return_value = None

    ok = CrawlResult(
        success=True,
        partial=False,
        content_type="text",
        extracted_fields={"title": "Test"},
        telemetry={"duration_ms": 42},
    )

    job = CrawlJob(
        id=1,
        url="https://example.com",
        engine="scrapling",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(engine="scrapling", retry_policy=RetryPolicy(max_retries=0)),
    )

    with patch("core.runner._execute_engine", return_value=ok):
        result = run_job(job)

    assert result.state == JobState.COMPLETED
    assert result.result.success
    mock_telemetry.record_crawl.assert_called_once()
