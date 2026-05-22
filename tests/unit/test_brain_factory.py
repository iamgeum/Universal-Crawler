"""brain_factory.py 단위 테스트."""

from core.brain_factory import get_brain, list_providers
from core.brains.ollama import OllamaBrain


def test_get_executor_returns_ollama():
    brain = get_brain("executor")
    assert isinstance(brain, OllamaBrain)


def test_list_providers():
    providers = list_providers()
    assert "ollama" in providers
    assert "anthropic" in providers
    assert "openai" in providers
