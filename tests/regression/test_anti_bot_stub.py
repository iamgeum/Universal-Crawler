"""regression: anti-bot / stealth 경로 스텁 검증."""

from core.router import route
from core.schema import CrawlStrategy


def test_spa_capability_routes_to_patchright_or_fallback():
    """captcha_bypass 필요 시 patchright 또는 scrapling fallback."""
    s = CrawlStrategy(
        engine="scrapling",
        required_capabilities=["spa_rendering", "captcha_bypass"],
        reason="spa site",
    )
    r = route("https://app.example.com", s)
    assert r.engine in ("patchright", "scrapling")
    assert r.routing_key in ("dual_key", "default_fallback")
