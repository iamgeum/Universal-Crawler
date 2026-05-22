"""Google Gemini 어댑터."""

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


class GeminiBrain(LLMBrain):
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self._model = model

    @property
    def name(self) -> str:
        return f"gemini:{self._model}"

    def is_available(self) -> bool:
        return bool(config.GEMINI_API_KEY)

    def _generate(self, user: str, system: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={config.GEMINI_API_KEY}"
        )
        body = http_post_json(
            url,
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": user}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            {"Content-Type": "application/json"},
        )
        candidates = body.get("candidates", [])
        if not candidates:
            return "{}"
        parts = candidates[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "{}") if parts else "{}"

    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return classify_from_heuristic(url, "gemini", self._model)

    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        system, user = build_plan_prompt(url, context)
        return extract_json_object(self._generate(user, system))

    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        ctx["recover"] = True
        ctx["error"] = error
        url = ctx.get("url", "https://example.com")
        try:
            return self.plan(url, ctx)
        except OSError:
            return build_strategy(url).model_dump()
