"""yt-dlp 엔진 — 동영상 메타/다운로드 → CrawlResult."""

from __future__ import annotations

import time
from typing import Any, Optional
from urllib.parse import urlparse

import config
from core.logger import get_logger
from core.plugin import EnginePlugin
from core.schema import CrawlJob, CrawlResult

logger = get_logger(__name__)

_YT_HOST_PATTERNS = (
    "youtube.com",
    "youtu.be",
    "youtube-nocookie.com",
)


class YtdlpEngine(EnginePlugin):
    capabilities = ["video", "streaming"]
    name = "yt-dlp"

    def can_handle(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        return any(p in host for p in _YT_HOST_PATTERNS)

    def execute(self, job: CrawlJob) -> CrawlResult:
        started = time.perf_counter()
        if not self.can_handle(job.url):
            return self._fail(
                started,
                [f"URL not supported by yt-dlp: {job.url}"],
            )

        try:
            import yt_dlp
        except ImportError as exc:
            return self._fail(started, [f"yt-dlp not installed: {exc}"])

        config.OUTPUT_VIDEOS.mkdir(parents=True, exist_ok=True)
        outtmpl = str(config.OUTPUT_VIDEOS / f"{job.id or 'unknown'}.%(ext)s")

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "outtmpl": outtmpl,
            "socket_timeout": job.strategy.timeout,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(job.url, download=False)
        except Exception as exc:
            return self._fail(started, [str(exc)])

        if not info:
            return self._fail(started, ["yt-dlp returned empty info"])

        duration_ms = int((time.perf_counter() - started) * 1000)
        title = info.get("title") or info.get("fulltitle")
        video_id = info.get("id")
        ext = info.get("ext") or "unknown"

        metadata = {
            "url": job.url,
            "domain": urlparse(job.url).netloc,
            "video_id": video_id,
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
        }
        extracted: dict[str, Any] = {}
        if title:
            extracted["title"] = title

        videos: list[str] = []
        if info.get("webpage_url"):
            videos.append(info["webpage_url"])

        return CrawlResult(
            success=True,
            partial=False,
            content_type="video",
            text=title,
            videos=videos,
            metadata=metadata,
            extracted_fields=extracted,
            telemetry={
                "duration_ms": duration_ms,
                "engine": self.name,
                "format": ext,
                "skip_download": True,
            },
        )

    def _fail(self, started: float, errors: list[str]) -> CrawlResult:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return CrawlResult(
            success=False,
            partial=False,
            content_type="video",
            errors=errors,
            telemetry={"duration_ms": duration_ms, "engine": self.name},
        )
