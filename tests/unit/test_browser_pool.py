"""browser_pool.py 단위 테스트."""

import pytest

from core.browser_pool import BrowserContextPool


def test_max_contexts_hard_limit():
    pool = BrowserContextPool()
    for i in range(5):
        pool.acquire(f"domain{i}.com")
    with pytest.raises(RuntimeError, match="MAX_CONTEXTS"):
        pool.acquire("overflow.com")


def test_release_and_invalidate():
    pool = BrowserContextPool()
    ctx = pool.acquire("example.com")
    assert pool.active_count == 1
    pool.release("example.com", ctx)
    assert pool.active_count == 0
    pool.acquire("example.com")
    pool.invalidate("example.com")
    assert pool.active_count == 0


def test_cleanup_zombies_returns_int():
    pool = BrowserContextPool()
    assert pool.cleanup_zombies() == 0
