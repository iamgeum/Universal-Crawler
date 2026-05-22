"""browser_pool.py 단위 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from core.browser_pool import BrowserContext, BrowserContextPool


@patch.object(BrowserContextPool, "_ensure_playwright")
def test_max_contexts_hard_limit(mock_ensure):
    mock_ensure.return_value = None
    pool = BrowserContextPool()
    pool._browser = MagicMock()
    pool._browser.new_context.return_value = MagicMock(new_page=MagicMock(return_value=MagicMock()))

    for i in range(5):
        pool.acquire(f"domain{i}.com")
    with pytest.raises(RuntimeError, match="MAX_CONTEXTS"):
        pool.acquire("overflow.com")


@patch.object(BrowserContextPool, "_ensure_playwright")
def test_release_and_invalidate(mock_ensure):
    mock_ensure.return_value = None
    pool = BrowserContextPool()
    pool._browser = MagicMock()
    pool._browser.new_context.return_value = MagicMock(
        new_page=MagicMock(return_value=MagicMock())
    )
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
