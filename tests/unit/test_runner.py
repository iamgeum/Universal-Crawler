"""runner.py 단위 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from core.runner import RunnerError, run_job
from core.schema import CrawlJob, CrawlResult, CrawlStrategy, JobState


def test_run_job_rejects_unavailable_engine():
    job = CrawlJob(
        id=1,
        url="https://www.youtube.com/watch?v=x",
        engine="yt-dlp",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(engine="yt-dlp", reason="test"),
    )
    with pytest.raises(RunnerError, match="not runnable"):
        run_job(job)


@patch("core.runner.storage")
@patch("core.runner.telemetry")
@patch("core.runner.default_checker")
def test_run_job_scrapling_success(mock_policy, mock_telemetry, mock_storage):
    mock_policy.check_url.return_value = None

    mock_engine = MagicMock()
    mock_engine.execute.return_value = CrawlResult(
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
        strategy=CrawlStrategy(engine="scrapling"),
    )

    with patch("core.runner.get_engine", return_value=mock_engine):
        result = run_job(job)

    assert result.state == JobState.COMPLETED
    assert result.result.success
    mock_storage.save_job.assert_called()
    mock_telemetry.record_crawl.assert_called_once()
