"""policy.py 단위 테스트."""

import pytest

from core.policy import PolicyChecker, PolicyError


def test_blacklist_blocks_domain():
    checker = PolicyChecker(blacklist=["evil.com"], respect_robots=False)
    with pytest.raises(PolicyError, match="blacklisted"):
        checker.check_url("https://evil.com/page")


def test_whitelist_allows_only_listed():
    checker = PolicyChecker(whitelist=["example.com"], respect_robots=False)
    checker.check_url("https://example.com")
    with pytest.raises(PolicyError, match="whitelist"):
        checker.check_url("https://other.com")


def test_invalid_scheme_rejected():
    checker = PolicyChecker(respect_robots=False)
    with pytest.raises(PolicyError, match="scheme"):
        checker.check_url("ftp://example.com")


def test_subdomain_blacklist():
    checker = PolicyChecker(blacklist=[".blocked.org"], respect_robots=False)
    with pytest.raises(PolicyError):
        checker.check_url("https://sub.blocked.org/x")
