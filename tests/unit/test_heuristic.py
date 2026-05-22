"""heuristic.py 단위 테스트."""

from core.brains.heuristic import build_strategy, select_engine


def test_youtube_routes_to_ytdlp():
    d = select_engine("https://www.youtube.com/watch?v=abc")
    assert d.engine == "yt-dlp"


def test_general_html_routes_to_scrapling():
    d = select_engine("https://example.com/page")
    assert d.engine == "scrapling"


def test_build_strategy_includes_fallback():
    s = build_strategy("https://example.com")
    assert s.engine == "scrapling"
    assert "scrapling" in s.fallback_chain
    assert "patchright" in s.fallback_chain
    assert s.reason


def test_youtube_fallback_includes_scrapling():
    s = build_strategy("https://www.youtube.com/watch?v=x")
    assert s.engine == "yt-dlp"
    assert "scrapling" in s.fallback_chain
