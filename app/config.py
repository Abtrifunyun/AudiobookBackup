import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_DATA_DIR", BASE_DIR / "data"))
DB_PATH = DATA_DIR / "audiobookbackup.db"
AUTH_FILE_PATH = DATA_DIR / "auth.json"
COVERS_DIR = DATA_DIR / "covers"
LOGS_DIR = DATA_DIR / "logs"

STATIC_DIR = BASE_DIR / "app" / "static"

# Reserved for Phase 3+ (download) and Phase 4+ (convert) - not created or used yet.
DOWNLOADS_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_DOWNLOADS_DIR", BASE_DIR / "downloads"))
LIBRARY_OUTPUT_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_LIBRARY_DIR", BASE_DIR / "library"))

DEFAULT_LOCALE = "us"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
