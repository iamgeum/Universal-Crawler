"""patchright_engine.py 단위 테스트."""

from unittest.mock import MagicMock, patch

from core.schema import CrawlJob, CrawlStrategy
from engines.patchright_engine import PatchrightEngine


@patch("engines.patchright_engine.default_pool")
def test_execute_urllib_when_pool_unavailable(mock_pool):
    mock_pool.is_available.return_value = False
    with patch("engines.scrapling_engine._fetch_urllib") as mock_fetch:
        mock_fetch.return_value = (
            "<html><head><title>FB</title></head><body></body></html>",
            200,
        )
        engine = PatchrightEngine()
        job = CrawlJob(
            url="https://example.com",
            engine="patchright",
            strategy=CrawlStrategy(engine="patchright"),
        )
        result = engine.execute(job)
    assert result.success
    assert result.metadata.get("fetcher_backend") == "urllib_fallback"


@patch("engines.patchright_engine.default_pool")
def test_execute_patchright_success(mock_pool):
    mock_pool.is_available.return_value = True
    mock_ctx = MagicMock()
    mock_ctx.context_id = "example.com-0"
    mock_page = MagicMock()
    mock_page.content.return_value = "<html><title>OK</title></html>"
    mock_page.title.return_value = "OK"
    mock_ctx._pw_page = mock_page
    mock_pool.acquire.return_value = mock_ctx

    engine = PatchrightEngine()
    job = CrawlJob(
        id=1,
        url="https://example.com",
        engine="patchright",
        strategy=CrawlStrategy(engine="patchright"),
    )
    result = engine.execute(job)
    assert result.success
    assert result.telemetry.get("fetcher_backend") != "urllib_fallback"
    mock_pool.release.assert_called_once()
