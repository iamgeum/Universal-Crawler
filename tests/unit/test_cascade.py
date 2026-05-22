"""cascade.py 단위 테스트."""

from unittest.mock import MagicMock, patch

from core.cascade import cascade_plan, cascade_recover
from core.schema import CrawlStrategy


@patch("core.cascade.brain_factory.get_brain")
def test_cascade_plan_uses_executor_when_available(mock_get_brain):
    mock_brain = MagicMock()
    mock_brain.is_available.return_value = True
    mock_brain.name = "ollama:llama3.2"
    mock_brain.plan.return_value = CrawlStrategy(
        engine="scrapling",
        reason="ollama",
        telemetry_tags=["ollama"],
    ).model_dump()
    mock_get_brain.return_value = mock_brain

    strategy, used = cascade_plan("https://unknown.example/", full=False)
    assert used == "ollama:llama3.2"
    mock_brain.plan.assert_called()


@patch("core.cascade.brain_factory.get_brain")
def test_cascade_recover_returns_none_when_unavailable(mock_get_brain):
    mock_brain = MagicMock()
    mock_brain.is_available.return_value = False
    mock_get_brain.return_value = mock_brain

    strategy, brain = cascade_recover("https://example.com", "403 forbidden")
    assert strategy is None
    assert brain == ""
