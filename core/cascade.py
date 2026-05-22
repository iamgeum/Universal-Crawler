"""대→소 LLM 캐스케이드 — plan / recover."""

from __future__ import annotations

from typing import Any, Optional

import config
from core import brain_factory
from core.brain import LLMBrain
from core.brains import heuristic
from core.logger import get_logger
from core.schema import CrawlStrategy
from pydantic import ValidationError

logger = get_logger(__name__)

# 계획: executor(소형 로컬) → fallback(클라우드 소형)
PLAN_ROLES = ("executor", "fallback")
# 복구: primary(대형) → fallback → executor
RECOVER_ROLES = ("primary", "fallback", "executor")


def _try_brain_plan(
    brain: LLMBrain,
    url: str,
    ctx: dict[str, Any],
    hint: CrawlStrategy,
) -> Optional[CrawlStrategy]:
    if not brain.is_available() or brain.name == "heuristic":
        return None
    try:
        ctx = {**ctx, "heuristic_hint": hint.model_dump()}
        raw = brain.plan(url, ctx)
        return CrawlStrategy.model_validate(raw)
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        logger.warning("Cascade plan %s failed: %s", brain.name, exc)
        return None


def cascade_plan(
    url: str,
    context: Optional[dict[str, Any]] = None,
    *,
    full: bool = False,
) -> tuple[CrawlStrategy, str]:
    """
    1. heuristic (무료)
    2. executor — Ollama
    3. fallback — OpenAI mini (full=True 또는 unknown domain)
    """
    ctx = dict(context or {})
    strategy = heuristic.build_strategy(url)
    brain_used = "heuristic"
    unknown = heuristic.select_engine(url).matched_rule is None

    roles: tuple[str, ...] = PLAN_ROLES if (full or unknown) else ("executor",)

    for role in roles:
        try:
            brain = brain_factory.get_brain(role)
        except (KeyError, ValueError):
            continue
        improved = _try_brain_plan(brain, url, ctx, strategy)
        if improved:
            strategy = improved
            brain_used = brain.name

    return strategy, brain_used


def cascade_recover(
    url: str,
    error: str,
    context: Optional[dict[str, Any]] = None,
) -> tuple[Optional[CrawlStrategy], str]:
    """실패 시 대형→소형 순으로 recover 전략 생성."""
    ctx = dict(context or {})
    ctx["url"] = url
    ctx["error"] = error

    for role in RECOVER_ROLES:
        try:
            brain = brain_factory.get_brain(role)
        except (KeyError, ValueError):
            continue
        if not brain.is_available():
            continue
        try:
            raw = brain.recover(error, ctx)
            strategy = CrawlStrategy.model_validate(raw)
            logger.info("Cascade recover via %s for %s", brain.name, url)
            return strategy, brain.name
        except (ValidationError, OSError, ValueError, KeyError) as exc:
            logger.warning("Cascade recover %s failed: %s", role, exc)

    return None, ""
