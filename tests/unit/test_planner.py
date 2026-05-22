"""planner.py 단위 테스트."""

from unittest.mock import patch

from core.planner import plan


def test_plan_heuristic_mode():
    strategy, brain = plan("https://example.com", mode="heuristic")
    assert brain == "heuristic"
    assert strategy.engine == "scrapling"


def test_plan_youtube_heuristic():
    strategy, brain = plan("https://www.youtube.com/watch?v=x", mode="heuristic")
    assert strategy.engine == "yt-dlp"
    assert brain == "heuristic"


@patch("core.planner.cascade.cascade_plan")
def test_plan_cascade_delegates(mock_cascade):
    mock_cascade.return_value = (
        __import__("core.schema", fromlist=["CrawlStrategy"]).CrawlStrategy(
            engine="scrapling", reason="cascade"
        ),
        "ollama:llama3.2",
    )
    strategy, brain = plan("https://example.com", mode="cascade")
    mock_cascade.assert_called_once()
    assert brain == "ollama:llama3.2"
