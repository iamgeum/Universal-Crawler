"""Planning Layer — heuristic → LLM cascade → Dual-key routing."""

from __future__ import annotations

from typing import Any, Literal, Optional

import config
from core import brain_factory
from core.brains import heuristic
from core.logger import get_logger
from core.router import apply_routing
from core.schema import CrawlStrategy
from pydantic import ValidationError

logger = get_logger(__name__)

PlannerMode = Literal["auto", "heuristic", "ollama"]


def _should_use_llm(url: str, mode: PlannerMode) -> bool:
    if mode == "heuristic":
        return False
    if mode == "ollama":
        return True
    if not config.USE_CASCADE:
        return False
    # auto: 휴리스틱이 확실히 매칭 못한 URL만 LLM
    decision = heuristic.select_engine(url)
    return decision.matched_rule is None


def plan(
    url: str,
    *,
    mode: PlannerMode = "auto",
    context: Optional[dict[str, Any]] = None,
) -> tuple[CrawlStrategy, str]:
    """
    CrawlStrategy 생성 + Dual-key engine 확정.
    Returns (strategy, brain_used).
    """
    ctx = dict(context or {})
    strategy = heuristic.build_strategy(url)
    brain_used = "heuristic"

    if _should_use_llm(url, mode):
        brain = brain_factory.get_active_brain()
        if brain.is_available() and brain.name != "heuristic":
            try:
                ctx["heuristic_hint"] = strategy.model_dump()
                raw = brain.plan(url, ctx)
                strategy = CrawlStrategy.model_validate(raw)
                brain_used = brain.name
                logger.info("Planner used %s for %s", brain_used, url)
            except (ValidationError, OSError, ValueError, KeyError) as exc:
                logger.warning("LLM plan failed (%s), keeping heuristic", exc)
        else:
            logger.debug("LLM brain unavailable, heuristic only")

    strategy = apply_routing(url, strategy)
    return strategy, brain_used


def plan_for_job(
    url: str,
    *,
    mode: PlannerMode = "auto",
    required_capabilities: Optional[list[str]] = None,
) -> tuple[CrawlStrategy, str]:
    ctx: dict[str, Any] = {}
    if required_capabilities:
        ctx["required_capabilities"] = required_capabilities
    strategy, brain = plan(url, mode=mode, context=ctx)
    if required_capabilities and not strategy.required_capabilities:
        strategy = strategy.model_copy(
            update={"required_capabilities": required_capabilities}
        )
        strategy = apply_routing(url, strategy)
    return strategy, brain
