"""Ollama 로컬 LLM 어댑터."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import config
from core.brain import LLMBrain
from core.brains.heuristic import build_strategy, select_engine
from core.logger import get_logger
from core.persona import PLAN_JSON_SCHEMA_HINT, get_persona

logger = get_logger(__name__)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


class OllamaBrain(LLMBrain):
    def __init__(self, model: str = "llama3.2", host: str | None = None) -> None:
        self._model = model
        self._host = (host or config.OLLAMA_HOST).rstrip("/")

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    def is_available(self) -> bool:
        try:
            req = Request(f"{self._host}/api/tags", method="GET")
            with urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except (URLError, OSError, TimeoutError):
            return False

    def _chat(self, user_prompt: str, system: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
        }
        data = json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self._host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("message", {}).get("content", "")

    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        hint = select_engine(url)
        return {
            "engine": hint.engine,
            "reason": hint.reason,
            "provider": "ollama",
            "model": self._model,
        }

    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        persona = get_persona(ctx.get("persona") or config.ACTIVE_PERSONA)
        heuristic_hint = ctx.get("heuristic_hint") or build_strategy(url).model_dump()

        user = (
            f"URL: {url}\n"
            f"Context: {json.dumps({k: v for k, v in ctx.items() if k != 'heuristic_hint'}, ensure_ascii=False)}\n"
            f"Heuristic hint: {json.dumps(heuristic_hint, ensure_ascii=False)}\n"
            f"Schema example:{PLAN_JSON_SCHEMA_HINT}\n"
            "Return CrawlStrategy JSON only."
        )
        raw = self._chat(user, persona)
        return _extract_json_object(raw)

    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        ctx["recover"] = True
        ctx["error"] = error
        plan = self.plan(ctx.get("url", "https://example.com"), ctx)
        plan["reason"] = f"ollama recover: {error[:80]}"
        plan.setdefault("telemetry_tags", []).append("recover")
        return plan
