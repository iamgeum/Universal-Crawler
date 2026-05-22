"""Patchright 브라우저 엔진 — SPA/Stealth → CrawlResult."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import config
from core.browser_pool import BrowserContext, default_pool, domain_from_url
from core.logger import get_logger
from core.plugin import EnginePlugin
from core.schema import CrawlJob, CrawlResult
from engines.scrapling_engine import extract_text_snippet, extract_title

logger = get_logger(__name__)


class PatchrightEngine(EnginePlugin):
    capabilities = [
        "spa_rendering",
        "infinite_scroll",
        "login_session",
        "captcha_bypass",
    ]
    name = "patchright"

    def can_handle(self, url: str) -> bool:
        return True

    def execute(self, job: CrawlJob) -> CrawlResult:
        started = time.perf_counter()
        timeout_ms = job.strategy.timeout * 1000
        domain = domain_from_url(job.url)

        if not default_pool.is_available():
            return self._urllib_fallback(job, started, "patchright unavailable")

        ctx: Optional[BrowserContext] = None
        try:
            ctx = default_pool.acquire(domain)
            page = ctx._pw_page
            page.goto(job.url, timeout=timeout_ms, wait_until="domcontentloaded")
            html = page.content()
            title = page.title() or extract_title(html)
            duration_ms = int((time.perf_counter() - started) * 1000)
            snippet = extract_text_snippet(html)
            out_path = self._save_html(job, html)

            extracted = {}
            if title:
                extracted["title"] = title

            return CrawlResult(
                success=True,
                partial=False,
                content_type="text",
                text=snippet,
                metadata={
                    "url": job.url,
                    "domain": domain,
                    "fetcher_backend": "patchright",
                },
                extracted_fields=extracted,
                telemetry={
                    "duration_ms": duration_ms,
                    "engine": self.name,
                    "context_id": ctx.context_id,
                    "output_path": str(out_path) if out_path else None,
                },
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            default_pool.invalidate(domain)
            logger.warning("patchright failed (%s), urllib fallback", exc)
            return self._urllib_fallback(job, started, str(exc), duration_ms)
        finally:
            if ctx is not None:
                default_pool.release(domain, ctx)

    def _urllib_fallback(
        self,
        job: CrawlJob,
        started: float,
        reason: str,
        duration_ms: Optional[int] = None,
    ) -> CrawlResult:
        from engines.scrapling_engine import _fetch_urllib

        try:
            html, status = _fetch_urllib(job.url, job.strategy.timeout)
            duration_ms = duration_ms or int((time.perf_counter() - started) * 1000)
            title = extract_title(html)
            return CrawlResult(
                success=True,
                partial=False,
                content_type="text",
                text=extract_text_snippet(html),
                metadata={
                    "url": job.url,
                    "status_code": status,
                    "fetcher_backend": "urllib_fallback",
                    "patchright_note": reason[:200],
                },
                extracted_fields={"title": title} if title else {},
                telemetry={"duration_ms": duration_ms, "engine": self.name},
            )
        except Exception as exc:
            duration_ms = duration_ms or int((time.perf_counter() - started) * 1000)
            return CrawlResult(
                success=False,
                partial=False,
                content_type="text",
                errors=[str(exc)],
                telemetry={"duration_ms": duration_ms, "engine": self.name},
            )

    def _save_html(self, job: CrawlJob, html: str) -> Optional[Path]:
        config.OUTPUT_TEXT.mkdir(parents=True, exist_ok=True)
        path = config.OUTPUT_TEXT / f"{job.id or 'unknown'}-patchright.html"
        try:
            path.write_text(html, encoding="utf-8")
            return path
        except OSError:
            return None
