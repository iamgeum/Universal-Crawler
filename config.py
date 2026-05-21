"""프로젝트 설정. API 키는 .env에서만 로드."""

from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "db" / "crawl_history.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_TEXT = OUTPUT_DIR / "text"
OUTPUT_IMAGES = OUTPUT_DIR / "images"
OUTPUT_VIDEOS = OUTPUT_DIR / "videos"

DEFAULT_FALLBACK_ENGINE = "patchright"

BRAIN_CONFIG = {
    "primary": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    "executor": {"provider": "ollama", "model": "llama3.2"},
    "fallback": {"provider": "openai", "model": "gpt-4o-mini"},
}
ACTIVE_BRAIN = "executor"
USE_CASCADE = True
ACTIVE_PERSONA = "v1"

# .env 키 (하드코딩 금지)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
