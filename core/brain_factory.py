"""Brain 팩토리 — config.BRAIN_CONFIG 기반 인스턴스 생성."""

from __future__ import annotations

from typing import Optional

import config
from core.brain import LLMBrain
from core.brains.heuristic import HeuristicBrain
from core.brains.ollama import OllamaBrain

_PROVIDERS: dict[str, type[LLMBrain]] = {
    "heuristic": HeuristicBrain,
    "ollama": OllamaBrain,
}


def get_brain(role: Optional[str] = None) -> LLMBrain:
    """role: primary | executor | fallback (기본 ACTIVE_BRAIN)."""
    role = role or config.ACTIVE_BRAIN
    if role not in config.BRAIN_CONFIG:
        raise KeyError(f"Unknown brain role: {role}")
    cfg = config.BRAIN_CONFIG[role]
    provider = cfg["provider"]
    model = cfg.get("model", "")

    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(f"Unsupported brain provider: {provider}")
    if provider == "ollama":
        return OllamaBrain(model=model, host=config.OLLAMA_HOST)
    return cls()


def get_active_brain() -> LLMBrain:
    return get_brain(config.ACTIVE_BRAIN)


def list_providers() -> list[str]:
    return list(_PROVIDERS.keys())
