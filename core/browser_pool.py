"""Browser Context Pool 인터페이스 (Phase 1c: 스텁, Phase 2b: 구현)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BrowserContext:
    """브라우저 컨텍스트 핸들 (Phase 2b에서 Playwright/Patchright 연동)."""

    domain: str
    context_id: str
    active: bool = True


class BrowserContextPool:
    MAX_CONTEXTS = 5
    MAX_BROWSERS = 2

    def __init__(self) -> None:
        self._contexts: dict[str, BrowserContext] = {}
        self._zombie_count = 0

    def acquire(self, domain: str) -> BrowserContext:
        if len(self._contexts) >= self.MAX_CONTEXTS:
            raise RuntimeError(
                f"Browser context limit reached (MAX_CONTEXTS={self.MAX_CONTEXTS})"
            )
        ctx_id = f"{domain}-{len(self._contexts)}"
        ctx = BrowserContext(domain=domain, context_id=ctx_id)
        self._contexts[ctx_id] = ctx
        logger.debug("acquired context %s for %s", ctx_id, domain)
        return ctx

    def release(self, domain: str, context: BrowserContext) -> None:
        self._contexts.pop(context.context_id, None)
        logger.debug("released context %s for %s", context.context_id, domain)

    def invalidate(self, domain: str) -> None:
        to_remove = [k for k, v in self._contexts.items() if v.domain == domain]
        for key in to_remove:
            self._contexts.pop(key, None)
        logger.info("invalidated %s context(s) for %s", len(to_remove), domain)

    def cleanup_zombies(self) -> int:
        """좀비 프로세스 정리 (Phase 2b에서 OS 프로세스 스캔)."""
        cleaned = self._zombie_count
        self._zombie_count = 0
        logger.debug("cleanup_zombies: %s stub cleaned", cleaned)
        return cleaned

    @property
    def active_count(self) -> int:
        return len(self._contexts)


# 모듈 기본 풀
default_pool = BrowserContextPool()
