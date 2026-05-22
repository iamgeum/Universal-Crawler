"""클라우드 LLM 공통 유틸 (urllib, API 키는 config/.env)."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.brains.heuristic import build_strategy, select_engine
from core.logger import get_logger
from core.persona import PLAN_JSON_SCHEMA_HINT, get_persona

logger = get_logger(__name__)


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def http_post_json(url: str, payload: dict, headers: dict[str, str], timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise OSError(f"HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise OSError(str(exc)) from exc


def build_plan_prompt(url: str, context: dict[str, Any] | None) -> tuple[str, str]:
    ctx = context or {}
    persona = get_persona(ctx.get("persona"))
    heuristic_hint = ctx.get("heuristic_hint") or build_strategy(url).model_dump()
    user = (
        f"URL: {url}\n"
        f"Context: {json.dumps({k: v for k, v in ctx.items() if k != 'heuristic_hint'}, ensure_ascii=False)}\n"
        f"Heuristic hint: {json.dumps(heuristic_hint, ensure_ascii=False)}\n"
        f"Schema example:{PLAN_JSON_SCHEMA_HINT}\n"
        "Return CrawlStrategy JSON only."
    )
    return persona, user


def classify_from_heuristic(url: str, provider: str, model: str) -> dict[str, Any]:
    hint = select_engine(url)
    return {
        "engine": hint.engine,
        "reason": hint.reason,
        "provider": provider,
        "model": model,
    }
