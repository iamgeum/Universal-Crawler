"""scrapling_engine.py 단위 테스트 (Fetcher 모킹)."""

from unittest.mock import patch

from core.schema import CrawlJob, CrawlStrategy
from engines.scrapling_engine import ScraplingEngine, extract_title


def test_extract_title_from_html():
    html = "<html><head><title>Hello World</title></head><body></body></html>"
    assert extract_title(html) == "Hello World"


@patch("engines.scrapling_engine._fetch_page")
def test_execute_success(mock_fetch):
    mock_fetch.return_value = (
        "<html><head><title>Example</title></head><body><p>Hi</p></body></html>",
        200,
        "scrapling",
    )
    engine = ScraplingEngine()
    job = CrawlJob(
        id=99,
        url="https://example.com",
        engine="scrapling",
        strategy=CrawlStrategy(engine="scrapling", timeout=10),
    )
    result = engine.execute(job)
    assert result.success is True
    assert result.extracted_fields.get("title") == "Example"
    assert result.telemetry["fetcher_backend"] == "scrapling"


@patch("engines.scrapling_engine._fetch_page")
def test_execute_fetch_failure(mock_fetch):
    mock_fetch.side_effect = RuntimeError("connection refused")
    engine = ScraplingEngine()
    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        strategy=CrawlStrategy(engine="scrapling"),
    )
    result = engine.execute(job)
    assert result.success is False
    assert "connection refused" in result.errors[0]


@patch("engines.scrapling_engine._fetch_page")
def test_execute_urllib_fallback(mock_fetch):
    mock_fetch.return_value = (
        "<html><head><title>Fallback</title></head><body></body></html>",
        200,
        "urllib",
    )
    engine = ScraplingEngine()
    job = CrawlJob(
        url="https://example.com",
        engine="scrapling",
        strategy=CrawlStrategy(engine="scrapling"),
    )
    result = engine.execute(job)
    assert result.success is True
    assert result.extracted_fields.get("title") == "Fallback"
    assert result.telemetry.get("fetcher_backend") == "urllib"
