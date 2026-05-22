"""Planning Layer — heuristic → cascade → Dual-key routing."""

from __future__ import annotations

from typing import Any, Literal, Optional

import config
from core import cascade
from core.brains import heuristic
from core.logger import get_logger
from core.router import apply_routing
from core.schema import CrawlStrategy

logger = get_logger(__name__)

PlannerMode = Literal["auto", "heuristic", "ollama", "cascade"]


def plan(
    url: str,
    *,
    mode: PlannerMode = "auto",
    context: Optional[dict[str, Any]] = None,
) -> tuple[CrawlStrategy, str]:
    """
    CrawlStrategy 생성 + Dual-key engine 확정.
    auto/cascade: 대→소 cascade (heuristic → ollama → openai mini)
    """
    ctx = dict(context or {})

    if mode == "heuristic":
        strategy = heuristic.build_strategy(url)
        brain_used = "heuristic"
    elif mode == "cascade":
        strategy, brain_used = cascade.cascade_plan(url, ctx, full=True)
    elif mode == "ollama":
        strategy, brain_used = cascade.cascade_plan(url, ctx, full=False)
        # ollama only: force executor attempt
        from core import brain_factory

        hint = heuristic.build_strategy(url)
        brain = brain_factory.get_brain("executor")
        if brain.is_available():
            from core.cascade import _try_brain_plan

            improved = _try_brain_plan(brain, url, ctx, hint)
            if improved:
                strategy, brain_used = improved, brain.name
            else:
                strategy = hint
        else:
            strategy = hint
            brain_used = "heuristic"
    else:
        # auto
        if config.USE_CASCADE:
            strategy, brain_used = cascade.cascade_plan(url, ctx, full=False)
        else:
            strategy = heuristic.build_strategy(url)
            brain_used = "heuristic"

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
