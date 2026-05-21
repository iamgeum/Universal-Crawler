"""Scrapling HTTP 엔진 — execute() → CrawlResult."""

from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import config
from core.logger import get_logger
from core.plugin import EnginePlugin
from core.schema import CrawlJob, CrawlResult

logger = get_logger(__name__)
DEFAULT_UA = "UniversalCrawler/0.1 (+https://github.com/iamgeum/Universal-Crawler)"


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: Optional[str] = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and self.title is None:
            self.title = data.strip()


def extract_title(html: str) -> Optional[str]:
    parser = _TitleParser()
    try:
        parser.feed(html[:500_000])
        if parser.title:
            return parser.title
    except Exception:
        pass
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_text_snippet(html: str, max_len: int = 2000) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _fetch_urllib(url: str, timeout: int) -> tuple[str, Optional[int]]:
    req = Request(url, headers={"User-Agent": DEFAULT_UA})
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        return body.decode("utf-8", errors="replace"), resp.getcode()


def _fetch_page(url: str, timeout: int) -> tuple[str, Optional[int], str]:
    """HTML, status, fetcher_backend (scrapling | urllib)."""
    try:
        from scrapling.fetchers import Fetcher

        response = Fetcher.fetch(url, timeout=timeout)
        html = getattr(response, "text", None) or str(response)
        return html, getattr(response, "status", None), "scrapling"
    except ImportError as exc:
        logger.warning("scrapling unavailable (%s), using urllib fallback", exc)
        html, status = _fetch_urllib(url, timeout)
        return html, status, "urllib"


class ScraplingEngine(EnginePlugin):
    capabilities = ["static_html", "basic_js"]
    name = "scrapling"

    def can_handle(self, url: str) -> bool:
        return True

    def execute(self, job: CrawlJob) -> CrawlResult:
        started = time.perf_counter()
        timeout = job.strategy.timeout

        try:
            html, status_code, backend = _fetch_page(job.url, timeout)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return CrawlResult(
                success=False,
                partial=False,
                content_type="text",
                errors=[str(exc)],
                telemetry={"duration_ms": duration_ms, "engine": self.name},
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        title = extract_title(html)
        snippet = extract_text_snippet(html)
        out_path = self._save_text(job, html)

        metadata = {
            "url": job.url,
            "domain": urlparse(job.url).netloc,
            "status_code": status_code,
            "fetcher_backend": backend,
        }
        extracted = {}
        if title:
            extracted["title"] = title

        return CrawlResult(
            success=True,
            partial=False,
            content_type="text",
            text=snippet,
            metadata=metadata,
            extracted_fields=extracted,
            telemetry={
                "duration_ms": duration_ms,
                "engine": self.name,
                "fetcher_backend": backend,
                "output_path": str(out_path) if out_path else None,
                "html_length": len(html),
            },
        )

    def _save_text(self, job: CrawlJob, html: str) -> Optional[Path]:
        config.OUTPUT_TEXT.mkdir(parents=True, exist_ok=True)
        job_id = job.id or "unknown"
        path = config.OUTPUT_TEXT / f"{job_id}.html"
        try:
            path.write_text(html, encoding="utf-8")
            return path
        except OSError:
            return None
