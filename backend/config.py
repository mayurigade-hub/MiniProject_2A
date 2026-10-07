import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
AUDIO_DIR = STORAGE_DIR / "audio"
FRAMES_DIR = STORAGE_DIR / "frames"
METADATA_DIR = STORAGE_DIR / "metadata"
SAMPLES_DIR = BASE_DIR / "sample_diagrams"

for d in [STORAGE_DIR, UPLOAD_DIR, AUDIO_DIR, FRAMES_DIR, METADATA_DIR, SAMPLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024 * 1024)))

VISION_MODELS = [
    "qwen/qwen3.8-27b",
]

TEXT_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
