"""클라우드 Brain 단위 테스트."""

from core.brains.claude import ClaudeBrain
from core.brains.openai import OpenAIBrain
from core.brains.gemini import GeminiBrain


def test_claude_unavailable_without_key(monkeypatch):
    monkeypatch.setattr("config.ANTHROPIC_API_KEY", "")
    assert ClaudeBrain().is_available() is False


def test_openai_unavailable_without_key(monkeypatch):
    monkeypatch.setattr("config.OPENAI_API_KEY", "")
    assert OpenAIBrain().is_available() is False


def test_gemini_unavailable_without_key(monkeypatch):
    monkeypatch.setattr("config.GEMINI_API_KEY", "")
    assert GeminiBrain().is_available() is False
