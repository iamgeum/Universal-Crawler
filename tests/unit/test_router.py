"""router.py Dual-key 단위 테스트."""

from core.router import route
from core.schema import CrawlStrategy


def test_url_only_routing_example():
    s = CrawlStrategy(engine="scrapling", reason="test")
    r = route("https://example.com", s)
    assert r.engine == "scrapling"
    assert r.routing_key == "url_only"


def test_dual_key_video_youtube():
    s = CrawlStrategy(
        engine="scrapling",
        required_capabilities=["video", "streaming"],
        reason="need video",
    )
    r = route("https://www.youtube.com/watch?v=abc", s)
    assert r.engine == "yt-dlp"
    assert r.routing_key == "dual_key"


def test_default_fallback_no_capability_match():
    s = CrawlStrategy(
        engine="scrapling",
        required_capabilities=["captcha_bypass"],
        reason="need captcha",
    )
    r = route("https://example.com", s)
    assert r.engine == "patchright"
    assert r.routing_key == "dual_key"
