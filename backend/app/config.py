import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (one level above backend/)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
TTS_VOICE = os.getenv("TTS_VOICE", "ne-NP-HemkalaNeural")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://192.168.23.144:8000").rstrip("/")

MEDIA_DIR = Path(__file__).resolve().parents[1] / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = 15
MAX_PDF_PAGES = 8
CHAT_HISTORY_LIMIT = 10
