"""Dual-key Router — URL 1차 → Capability 2차 → Default Fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import config
from core.brains import heuristic
from core.logger import get_logger
from core.schema import CrawlStrategy, EngineName

logger = get_logger(__name__)

# 엔진별 Capability (plugin + Phase 2b patchright 선언)
ENGINE_CAPABILITIES: dict[str, list[str]] = {
    "scrapling": ["static_html", "basic_js"],
    "yt-dlp": ["video", "streaming"],
    "gallery-dl": ["image", "gallery"],
    "patchright": [
        "spa_rendering",
        "infinite_scroll",
        "login_session",
        "captcha_bypass",
    ],
}

# Phase 2a에서 실행 가능한 엔진 (registry와 동기)
RUNNABLE_ENGINES = frozenset({"scrapling", "yt-dlp", "gallery-dl", "patchright"})


@dataclass(frozen=True)
class RouteResult:
    engine: EngineName
    reason: str
    candidates: list[str]
    routing_key: str  # url_only | dual_key | default_fallback


def _url_candidates(url: str) -> list[str]:
    """1차: URL/domain 패턴 + can_handle 후보."""
    candidates: list[str] = []
    seen: set[str] = set()

    primary = heuristic.select_engine(url).engine
    for eng in (primary,):
        if eng not in seen:
            candidates.append(eng)
            seen.add(eng)

    try:
        from core.runner import get_engine, list_runnable_engines

        for name in list_runnable_engines():
            plugin = get_engine(name)
            if plugin and plugin.can_handle(url) and name not in seen:
                candidates.append(name)
                seen.add(name)
    except ImportError:
        pass

    return candidates or [heuristic.DEFAULT_ENGINE]


def _pick_by_capabilities(
    candidates: list[str],
    required: list[str],
) -> Optional[str]:
    if not required:
        return None
    req = set(required)
    matched = [
        e
        for e in candidates
        if req <= set(ENGINE_CAPABILITIES.get(e, []))
    ]
    return matched[0] if matched else None


def _default_fallback() -> EngineName:
    fb: str = config.DEFAULT_FALLBACK_ENGINE
    if fb in RUNNABLE_ENGINES:
        return fb  # type: ignore[return-value]
    logger.debug("fallback %s not runnable; using scrapling", fb)
    return "scrapling"


def route(
    url: str,
    strategy: CrawlStrategy,
    *,
    required_capabilities: Optional[list[str]] = None,
) -> RouteResult:
    """
    Dual-key 라우팅.
    1차 URL 후보 → 2차 capability 필터 → 실패 시 DEFAULT_FALLBACK.
    """
    caps = required_capabilities if required_capabilities is not None else strategy.required_capabilities
    candidates = _url_candidates(url)

    # planner/heuristic이 고른 엔진이 후보에 있으면 우선
    preferred = strategy.engine if strategy.engine in candidates else candidates[0]

    if not caps:
        return RouteResult(
            engine=preferred,
            reason=strategy.reason or f"url match → {preferred}",
            candidates=candidates,
            routing_key="url_only",
        )

    cap_match = _pick_by_capabilities(candidates, caps)
    if cap_match:
        reason = f"dual_key: {cap_match} (caps={caps})"
        if cap_match == preferred:
            reason = strategy.reason or reason
        return RouteResult(
            engine=cap_match,  # type: ignore[arg-type]
            reason=reason,
            candidates=candidates,
            routing_key="dual_key",
        )

    fb = _default_fallback()
    return RouteResult(
        engine=fb,
        reason=f"dual_key: no capability match {caps}, default fallback → {fb}",
        candidates=candidates,
        routing_key="default_fallback",
    )


def apply_routing(url: str, strategy: CrawlStrategy) -> CrawlStrategy:
    """strategy.engine/reason을 Dual-key 결과로 갱신."""
    result = route(url, strategy)
    tags = list(strategy.telemetry_tags)
    tags.append(f"route:{result.routing_key}")
    return strategy.model_copy(
        update={
            "engine": result.engine,
            "reason": result.reason,
            "telemetry_tags": tags,
        }
    )
