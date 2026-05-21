"""schema.py 단위 테스트."""

import pytest

from core.schema import (
    CrawlEvent,
    CrawlJob,
    CrawlResult,
    CrawlStrategy,
    JobState,
)


def test_event_masks_nested_secrets():
    event = CrawlEvent(
        job_id=1,
        event_type="engine_started",
        payload={
            "headers": {"Authorization": "Bearer secret-token"},
            "url": "https://api.test?token=abc123&foo=bar",
        },
    )
    assert event.payload["headers"]["Authorization"] == "***"
    assert "token=***" in event.payload["url"]
    assert "abc123" not in event.payload["url"]


def test_partial_success_empty_mandatory_completes():
    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        state=JobState.PARTIAL_SUCCESS,
        strategy=CrawlStrategy(engine="scrapling", mandatory_fields=[]),
        result=CrawlResult(success=True, partial=True, content_type="text"),
    )
    job.resolve_partial_success()
    assert job.state == JobState.COMPLETED


def test_partial_success_missing_field_fails():
    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        state=JobState.PARTIAL_SUCCESS,
        strategy=CrawlStrategy(engine="scrapling", mandatory_fields=["title"]),
        result=CrawlResult(
            success=True,
            partial=True,
            content_type="text",
            extracted_fields={},
        ),
    )
    job.resolve_partial_success()
    assert job.state == JobState.FAILED


def test_invalid_transition_raises():
    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        state=JobState.QUEUED,
        strategy=CrawlStrategy(engine="scrapling"),
    )
    with pytest.raises(ValueError, match="Invalid transition"):
        job.transition_to(JobState.COMPLETED)
