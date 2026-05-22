"""Browser Context Pool — Patchright/Playwright 연동."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BrowserContext:
    """브라우저 컨텍스트 핸들."""

    domain: str
    context_id: str
    active: bool = True
    _pw_context: Any = field(default=None, repr=False)
    _pw_page: Any = field(default=None, repr=False)


class BrowserContextPool:
    MAX_CONTEXTS = 5
    MAX_BROWSERS = 2

    def __init__(self) -> None:
        self._contexts: dict[str, BrowserContext] = {}
        self._playwright: Any = None
        self._browser: Any = None
        self._pw_cm: Any = None
        self._browser_count = 0

    def _ensure_playwright(self):
        if self._playwright is not None:
            return
        try:
            from patchright.sync_api import sync_playwright
        except ImportError:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:
                raise RuntimeError(
                    "patchright/playwright not installed. "
                    "pip install patchright && patchright install chromium"
                ) from exc
        self._pw_cm = sync_playwright()
        self._playwright = self._pw_cm.__enter__()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._browser_count = 1
        logger.info("Browser pool started (chromium)")

    def acquire(self, domain: str) -> BrowserContext:
        if len(self._contexts) >= self.MAX_CONTEXTS:
            raise RuntimeError(
                f"Browser context limit reached (MAX_CONTEXTS={self.MAX_CONTEXTS})"
            )
        self._ensure_playwright()
        if self._browser is None:
            raise RuntimeError("Browser not available")

        pw_ctx = self._browser.new_context()
        page = pw_ctx.new_page()
        ctx_id = f"{domain}-{len(self._contexts)}"
        ctx = BrowserContext(
            domain=domain,
            context_id=ctx_id,
            _pw_context=pw_ctx,
            _pw_page=page,
        )
        self._contexts[ctx_id] = ctx
        logger.debug("acquired context %s for %s", ctx_id, domain)
        return ctx

    def release(self, domain: str, context: BrowserContext) -> None:
        try:
            if context._pw_page:
                context._pw_page.close()
            if context._pw_context:
                context._pw_context.close()
        except Exception as exc:
            logger.warning("release context %s: %s", context.context_id, exc)
        self._contexts.pop(context.context_id, None)

    def invalidate(self, domain: str) -> None:
        to_remove = [c for c in self._contexts.values() if c.domain == domain]
        for ctx in to_remove:
            self.release(domain, ctx)
        logger.info("invalidated %s context(s) for %s", len(to_remove), domain)

    def cleanup_zombies(self) -> int:
        """열린 컨텍스트 정리 + 브라우저 재시작."""
        count = len(self._contexts)
        for ctx_id in list(self._contexts.keys()):
            ctx = self._contexts[ctx_id]
            self.release(ctx.domain, ctx)
        try:
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._pw_cm is not None:
                self._pw_cm.__exit__(None, None, None)
                self._pw_cm = None
                self._playwright = None
        except Exception as exc:
            logger.warning("cleanup_zombies browser stop: %s", exc)
        logger.info("cleanup_zombies: cleared %s context(s)", count)
        return count

    @property
    def active_count(self) -> int:
        return len(self._contexts)

    def is_available(self) -> bool:
        try:
            from patchright.sync_api import sync_playwright  # noqa: F401
            return True
        except ImportError:
            try:
                from playwright.sync_api import sync_playwright  # noqa: F401
                return True
            except ImportError:
                return False


def domain_from_url(url: str) -> str:
    return (urlparse(url).hostname or "default").lower()


default_pool = BrowserContextPool()
