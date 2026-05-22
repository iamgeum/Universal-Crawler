"""휴리스틱 라우터 — URL/도메인 패턴 → 엔진 (Phase 1: 1차 라우팅)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import config
from core.brain import LLMBrain
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
    fallback = list(
        dict.fromkeys(["scrapling", config.DEFAULT_FALLBACK_ENGINE, "patchright"])
    )
    return CrawlStrategy(
        engine=decision.engine,
        fallback_chain=fallback,
        reason=decision.reason,
        telemetry_tags=["heuristic"],
    )


class HeuristicBrain(LLMBrain):
    """AI 없는 URL 패턴 기반 Brain."""

    @property
    def name(self) -> str:
        return "heuristic"

    def is_available(self) -> bool:
        return True

    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        d = select_engine(url)
        return {
            "engine": d.engine,
            "reason": d.reason,
            "matched_rule": d.matched_rule,
            "confidence": 0.9 if d.matched_rule else 0.6,
        }

    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return build_strategy(url).model_dump()

    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        url = ctx.get("url", "")
        strategy = build_strategy(url) if url else build_strategy("https://example.com")
        strategy.fallback_chain = list(
            dict.fromkeys(["scrapling", config.DEFAULT_FALLBACK_ENGINE, "patchright"])
        )
        strategy.reason = f"heuristic recover: {error[:120]}"
        return strategy.model_dump()
