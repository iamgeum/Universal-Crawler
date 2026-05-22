"""persona.py 단위 테스트."""

import pytest

from core.persona import get_persona


def test_get_persona_v1():
    text = get_persona("v1")
    assert "크롤러" in text
    assert "yt-dlp" in text


def test_unknown_persona_raises():
    with pytest.raises(KeyError):
        get_persona("v99")
