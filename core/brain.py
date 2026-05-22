"""LLMBrain 추상 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMBrain(ABC):
    """Provider 독립 LLM 어댑터."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def classify(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def plan(self, url: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def recover(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...
