"""Policy Layer — robots.txt, blacklist/whitelist."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import config

DEFAULT_USER_AGENT = "UniversalCrawler/0.1 (+https://github.com/iamgeum/Universal-Crawler)"


class PolicyError(Exception):
    """URL이 정책에 의해 차단된 경우."""


@dataclass
class PolicyChecker:
    blacklist: list[str] = field(default_factory=lambda: list(config.BLACKLIST_DOMAINS))
    whitelist: list[str] = field(default_factory=lambda: list(config.WHITELIST_DOMAINS))
    respect_robots: bool = config.RESPECT_ROBOTS_TXT
    user_agent: str = DEFAULT_USER_AGENT
    _robots_cache: dict[str, RobotFileParser] = field(default_factory=dict, repr=False)
    _last_fetch: dict[str, float] = field(default_factory=dict, repr=False)
    robots_cache_ttl: int = 3600

    def check_url(self, url: str) -> None:
        """정책 통과 시 None, 위반 시 PolicyError."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise PolicyError(f"Unsupported URL scheme: {parsed.scheme!r}")
        if not parsed.netloc:
            raise PolicyError(f"Invalid URL (no host): {url}")

        host = parsed.netloc.lower()
        if self._is_blacklisted(host):
            raise PolicyError(f"Domain blacklisted: {host}")

        if self.whitelist and not self._is_whitelisted(host):
            raise PolicyError(f"Domain not in whitelist: {host}")

        if self.respect_robots and not self._robots_allowed(url):
            raise PolicyError(f"Blocked by robots.txt: {url}")

    def _is_blacklisted(self, host: str) -> bool:
        return any(self._host_matches(host, pattern) for pattern in self.blacklist)

    def _is_whitelisted(self, host: str) -> bool:
        return any(self._host_matches(host, pattern) for pattern in self.whitelist)

    @staticmethod
    def _host_matches(host: str, pattern: str) -> bool:
        pattern = pattern.lower().strip()
        if pattern.startswith("."):
            return host == pattern[1:] or host.endswith(pattern)
        return host == pattern or host.endswith(f".{pattern}")

    def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        now = time.time()

        rp = self._robots_cache.get(origin)
        last = self._last_fetch.get(origin, 0.0)
        if rp is None or (now - last) > self.robots_cache_ttl:
            rp = RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            try:
                rp.read()
            except Exception:
                # robots.txt 없거나 읽기 실패 → 허용 (보수적 차단은 Phase 2+)
                return True
            self._robots_cache[origin] = rp
            self._last_fetch[origin] = now

        return rp.can_fetch(self.user_agent, url)


# 모듈 기본 인스턴스
default_checker = PolicyChecker()
