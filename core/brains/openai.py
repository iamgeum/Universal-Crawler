"""OpenAI 어댑터 (fallback 소형 모델)."""

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


class OpenAIBrain(LLMBrain):
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._model = model

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def is_available(self) -> bool:
        return bool(config.OPENAI_API_KEY)

    def _chat(self, user: str, system: str) -> str:
        body = http_post_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
            },
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            },
        )
        return body["choices"][0]["message"]["content"]

    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return classify_from_heuristic(url, "openai", self._model)

    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        system, user = build_plan_prompt(url, context)
        return extract_json_object(self._chat(user, system))

    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        ctx["recover"] = True
        ctx["error"] = error
        url = ctx.get("url", "https://example.com")
        try:
            plan = self.plan(url, ctx)
            plan["reason"] = f"openai recover: {error[:80]}"
            return plan
        except OSError:
            return build_strategy(url).model_dump()
