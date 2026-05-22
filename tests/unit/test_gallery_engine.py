"""gallery_engine.py 단위 테스트."""

from unittest.mock import patch

from core.schema import CrawlJob, CrawlStrategy
from engines.gallery_engine import GalleryDlEngine


def test_can_handle_pixiv():
    assert GalleryDlEngine().can_handle("https://www.pixiv.net/artworks/1")
    assert not GalleryDlEngine().can_handle("https://example.com")


@patch("engines.gallery_engine.subprocess.run")
def test_execute_parses_urls(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "https://i.pixiv.net/img1.png\nhttps://i.pixiv.net/img2.png\n"
    mock_run.return_value.stderr = ""

    engine = GalleryDlEngine()
    job = CrawlJob(
        url="https://www.pixiv.net/artworks/1",
        engine="gallery-dl",
        strategy=CrawlStrategy(engine="gallery-dl"),
    )
    result = engine.execute(job)

    assert result.success
    assert len(result.images) == 2
    assert result.extracted_fields["image_count"] == 2
