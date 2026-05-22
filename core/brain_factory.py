"""Brain 팩토리 — config.BRAIN_CONFIG 기반 인스턴스 생성."""

from __future__ import annotations

from typing import Optional

import config
from core.brain import LLMBrain
from core.brains.claude import ClaudeBrain
from core.brains.gemini import GeminiBrain
from core.brains.heuristic import HeuristicBrain
from core.brains.ollama import OllamaBrain
from core.brains.openai import OpenAIBrain

_PROVIDER_MAP: dict[str, type[LLMBrain]] = {
    "heuristic": HeuristicBrain,
    "ollama": OllamaBrain,
    "anthropic": ClaudeBrain,
    "claude": ClaudeBrain,
    "openai": OpenAIBrain,
    "gemini": GeminiBrain,
    "google": GeminiBrain,
}


def _construct(provider: str, model: str) -> LLMBrain:
    cls = _PROVIDER_MAP.get(provider)
    if cls is None:
        raise ValueError(f"Unsupported brain provider: {provider}")
    if provider in ("ollama",):
        return OllamaBrain(model=model, host=config.OLLAMA_HOST)
    if provider in ("anthropic", "claude"):
        return ClaudeBrain(model=model)
    if provider == "openai":
        return OpenAIBrain(model=model)
    if provider in ("gemini", "google"):
        return GeminiBrain(model=model)
    return cls()


def get_brain(role: Optional[str] = None) -> LLMBrain:
    """role: primary | executor | fallback (기본 ACTIVE_BRAIN)."""
    role = role or config.ACTIVE_BRAIN
    if role not in config.BRAIN_CONFIG:
        raise KeyError(f"Unknown brain role: {role}")
    cfg = config.BRAIN_CONFIG[role]
    return _construct(cfg["provider"], cfg.get("model", ""))


def get_active_brain() -> LLMBrain:
    return get_brain(config.ACTIVE_BRAIN)


def list_providers() -> list[str]:
    return sorted(_PROVIDER_MAP.keys())
