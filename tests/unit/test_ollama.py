"""ollama.py 단위 테스트."""

import json
from unittest.mock import MagicMock, patch

from core.brains.ollama import OllamaBrain, _extract_json_object


def test_extract_json_from_markdown_fence():
    raw = '```json\n{"engine": "scrapling", "timeout": 30}\n```'
    data = _extract_json_object(raw)
    assert data["engine"] == "scrapling"


@patch("core.brains.ollama.urlopen")
def test_ollama_plan_parses_json(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.read.return_value = json.dumps(
        {
            "message": {
                "content": json.dumps(
                    {
                        "engine": "scrapling",
                        "timeout": 25,
                        "fallback_chain": ["scrapling"],
                        "reason": "test",
                        "telemetry_tags": ["ollama"],
                    }
                )
            }
        }
    ).encode()
    mock_urlopen.return_value = mock_resp

    brain = OllamaBrain(model="llama3.2", host="http://localhost:11434")
    with patch.object(brain, "is_available", return_value=True):
        result = brain.plan("https://example.com")
    assert result["engine"] == "scrapling"
    assert result["timeout"] == 25


@patch("core.brains.ollama.urlopen")
def test_ollama_is_available(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.status = 200
    mock_urlopen.return_value = mock_resp

    brain = OllamaBrain()
    assert brain.is_available() is True
