"""ytdlp_engine.py 단위 테스트."""

from unittest.mock import MagicMock, patch

from core.schema import CrawlJob, CrawlStrategy
from engines.ytdlp_engine import YtdlpEngine


def test_can_handle_youtube():
    assert YtdlpEngine().can_handle("https://www.youtube.com/watch?v=abc")
    assert not YtdlpEngine().can_handle("https://example.com")


@patch("yt_dlp.YoutubeDL")
def test_execute_extract_info(MockYDL):
    mock_ydl = MagicMock()
    MockYDL.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        "title": "Test Video",
        "id": "abc123",
        "ext": "mp4",
        "webpage_url": "https://youtube.com/watch?v=abc123",
    }

    engine = YtdlpEngine()
    job = CrawlJob(
        url="https://www.youtube.com/watch?v=abc123",
        engine="yt-dlp",
        strategy=CrawlStrategy(engine="yt-dlp", timeout=30),
    )
    result = engine.execute(job)

    assert result.success
    assert result.content_type == "video"
    assert result.extracted_fields["title"] == "Test Video"
