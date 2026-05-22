"""Anthropic Claude 어댑터 (primary / recover)."""

from __future__ import annotations

from typing import Any

import config
from core.brain import LLMBrain
from core.brains.cloud_base import (
    build_plan_prompt,
    classify_from_heuristic,
    extract_json_object,
    http_post_json,
)
from core.brains.heuristic import build_strategy


class ClaudeBrain(LLMBrain):
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self._model = model

    @property
    def name(self) -> str:
        return f"anthropic:{self._model}"

    def is_available(self) -> bool:
        return bool(config.ANTHROPIC_API_KEY)

    def _messages(self, user: str, system: str) -> str:
        body = http_post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": self._model,
                "max_tokens": 2048,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            {
                "Content-Type": "application/json",
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
        for block in body.get("content", []):
            if block.get("type") == "text":
                return block.get("text", "")
        return ""

    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return classify_from_heuristic(url, "anthropic", self._model)

    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        system, user = build_plan_prompt(url, context)
        return extract_json_object(self._messages(user, system))

    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        ctx["recover"] = True
        ctx["error"] = error
        url = ctx.get("url", "https://example.com")
        try:
            return self.plan(url, ctx)
        except OSError:
            strategy = build_strategy(url)
            strategy.reason = f"claude recover fallback: {error[:80]}"
            return strategy.model_dump()
