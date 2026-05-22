"""휴리스틱 라우터 — URL/도메인 패턴 → 엔진 (Phase 1: 1차 라우팅만)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import config
from core.schema import CrawlStrategy, EngineName

# (정규식, 엔진, 사유) — persona v1 도메인 규칙
DOMAIN_RULES: list[tuple[str, EngineName, str]] = [
    (r"(^|\.)youtube\.com$|^youtu\.be$", "yt-dlp", "YouTube → yt-dlp"),
    (r"(^|\.)pixiv\.net$", "gallery-dl", "Pixiv → gallery-dl"),
    (r"(^|\.)twitter\.com$|(^|\.)x\.com$", "gallery-dl", "Twitter/X media → gallery-dl"),
    (r"(^|\.)instagram\.com$", "gallery-dl", "Instagram → gallery-dl"),
]

DEFAULT_ENGINE: EngineName = "scrapling"
DEFAULT_REASON = "General HTML → scrapling (fallback: patchright)"


@dataclass(frozen=True)
class RouteDecision:
    engine: EngineName
    reason: str
    matched_rule: str | None = None


def _host(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def select_engine(url: str) -> RouteDecision:
    """URL에서 엔진 선택."""
    host = _host(url)
    for pattern, engine, reason in DOMAIN_RULES:
        if re.search(pattern, host):
            return RouteDecision(engine=engine, reason=reason, matched_rule=pattern)
    return RouteDecision(
        engine=DEFAULT_ENGINE,
        reason=DEFAULT_REASON,
        matched_rule=None,
    )


def build_strategy(url: str) -> CrawlStrategy:
    """Heuristic 기반 CrawlStrategy 생성."""
    decision = select_engine(url)
    # Phase 1c: scrapling만 실행 가능. patchright는 Phase 2b.
    fallback = list(
        dict.fromkeys(["scrapling", config.DEFAULT_FALLBACK_ENGINE, "patchright"])
    )
    return CrawlStrategy(
        engine=decision.engine,
        fallback_chain=fallback,
        reason=decision.reason,
        telemetry_tags=["heuristic", "phase1"],
    )
