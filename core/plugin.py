"""Engine Plugin 추상 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.schema import CrawlJob, CrawlResult


class EnginePlugin(ABC):
    capabilities: list[str] = []

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def can_handle(self, url: str) -> bool: ...

    @abstractmethod
    def execute(self, job: CrawlJob) -> CrawlResult: ...
