"""planner.py 단위 테스트."""

from unittest.mock import patch

from core.planner import plan
from core.schema import CrawlStrategy


def test_plan_heuristic_mode():
    strategy, brain = plan("https://example.com", mode="heuristic")
    assert brain == "heuristic"
    assert strategy.engine == "scrapling"


def test_plan_youtube_heuristic():
    strategy, brain = plan("https://www.youtube.com/watch?v=x", mode="heuristic")
    assert strategy.engine == "yt-dlp"
    assert brain == "heuristic"


@patch("core.planner.brain_factory.get_active_brain")
def test_plan_auto_skips_llm_when_domain_matched(mock_get_brain):
    mock_get_brain.return_value.is_available.return_value = True
    strategy, brain = plan("https://www.youtube.com/watch?v=x", mode="auto")
    assert brain == "heuristic"
    mock_get_brain.return_value.plan.assert_not_called()


@patch("core.planner.brain_factory.get_active_brain")
def test_plan_auto_uses_llm_for_unknown_domain(mock_get_brain):
    mock_brain = mock_get_brain.return_value
    mock_brain.is_available.return_value = True
    mock_brain.name = "ollama:llama3.2"
    mock_brain.plan.return_value = CrawlStrategy(
        engine="scrapling",
        required_capabilities=["static_html"],
        reason="llm",
        telemetry_tags=["ollama"],
    ).model_dump()

    strategy, brain = plan("https://unknown-site-xyz.example/", mode="auto")
    assert mock_brain.plan.called
    assert "ollama" in brain
