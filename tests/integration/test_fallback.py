"""fallback + 상태 전이 통합 테스트."""

from unittest.mock import patch

from core.runner import run_job
from core.schema import CrawlJob, CrawlResult, CrawlStrategy, JobState, RetryPolicy


@patch("core.runner.storage")
@patch("core.runner.telemetry")
@patch("core.runner.default_checker")
def test_fallback_ytdlp_to_scrapling(mock_policy, mock_telemetry, mock_storage):
    mock_policy.check_url.return_value = None

    ytdlp_fail = CrawlResult(
        success=False,
        partial=False,
        content_type="video",
        errors=["yt-dlp blocked"],
        telemetry={"duration_ms": 10},
    )
    scrapling_ok = CrawlResult(
        success=True,
        partial=False,
        content_type="text",
        extracted_fields={"title": "Fallback OK"},
        telemetry={"duration_ms": 20},
    )

    def fake_execute(job, engine_name):
        job.engine = engine_name
        if engine_name == "yt-dlp":
            return ytdlp_fail
        if engine_name == "scrapling":
            return scrapling_ok
        return CrawlResult(
            success=False,
            partial=False,
            content_type="text",
            errors=["unknown"],
            telemetry={},
        )

    job = CrawlJob(
        id=10,
        url="https://www.youtube.com/watch?v=test",
        engine="yt-dlp",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(
            engine="yt-dlp",
            fallback_chain=["scrapling"],
            retry_policy=RetryPolicy(max_retries=0),
        ),
    )

    with patch("core.runner._execute_engine", side_effect=fake_execute):
        result = run_job(job)

    assert result.state == JobState.COMPLETED
    assert result.engine == "scrapling"
    assert result.result.success
    mock_telemetry.record_crawl.assert_called_once()
    assert mock_telemetry.record_crawl.call_args[1].get("fallback") is True
