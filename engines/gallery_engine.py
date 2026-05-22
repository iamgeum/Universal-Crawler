"""gallery-dl 엔진 — 이미지/갤러리 URL 수집 → CrawlResult."""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Any
from urllib.parse import urlparse

from core.logger import get_logger
from core.plugin import EnginePlugin
from core.schema import CrawlJob, CrawlResult

logger = get_logger(__name__)

_GALLERY_HOST_HINTS = (
    "pixiv.net",
    "twitter.com",
    "x.com",
    "instagram.com",
    "imgur.com",
    "deviantart.com",
)


class GalleryDlEngine(EnginePlugin):
    capabilities = ["image", "gallery"]
    name = "gallery-dl"

    def can_handle(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        return any(h in host for h in _GALLERY_HOST_HINTS)

    def execute(self, job: CrawlJob) -> CrawlResult:
        started = time.perf_counter()
        if not self.can_handle(job.url):
            return self._fail(started, [f"URL not supported by gallery-dl: {job.url}"])

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "gallery_dl", "-g", job.url],
                capture_output=True,
                text=True,
                timeout=job.strategy.timeout,
                check=False,
            )
        except FileNotFoundError:
            return self._fail(
                started,
                ["gallery-dl not installed. pip install gallery-dl"],
            )
        except subprocess.TimeoutExpired:
            return self._fail(started, [f"gallery-dl timed out after {job.strategy.timeout}s"])
        except Exception as exc:
            return self._fail(started, [str(exc)])

        duration_ms = int((time.perf_counter() - started) * 1000)
        image_urls = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]

        if proc.returncode != 0 and not image_urls:
            stderr = (proc.stderr or "").strip()[:500]
            return self._fail(
                started,
                [f"gallery-dl exit {proc.returncode}: {stderr or 'no output'}"],
            )

        metadata: dict[str, Any] = {
            "url": job.url,
            "domain": urlparse(job.url).netloc,
            "image_url_count": len(image_urls),
            "returncode": proc.returncode,
        }

        return CrawlResult(
            success=True,
            partial=proc.returncode != 0 and bool(image_urls),
            content_type="image",
            images=image_urls,
            metadata=metadata,
            extracted_fields={"image_count": len(image_urls)},
            telemetry={
                "duration_ms": duration_ms,
                "engine": self.name,
                "mode": "gallery_dl -g",
            },
        )

    def _fail(self, started: float, errors: list[str]) -> CrawlResult:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return CrawlResult(
            success=False,
            partial=False,
            content_type="image",
            errors=errors,
            telemetry={"duration_ms": duration_ms, "engine": self.name},
        )
