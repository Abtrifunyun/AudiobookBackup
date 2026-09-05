import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_DATA_DIR", BASE_DIR / "data"))
DB_PATH = DATA_DIR / "audiobookbackup.db"
AUTH_FILE_PATH = DATA_DIR / "auth.json"
COVERS_DIR = DATA_DIR / "covers"
LOGS_DIR = DATA_DIR / "logs"

STATIC_DIR = BASE_DIR / "app" / "static"

# Fallback paths, used until a user-chosen location is saved via the Settings
# screen (persisted in the `app_settings` table, not fixed at import time).
DEFAULT_DOWNLOADS_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_DOWNLOADS_DIR", BASE_DIR / "downloads"))
DEFAULT_LIBRARY_OUTPUT_DIR = Path(os.environ.get("AUDIOBOOKBACKUP_LIBRARY_DIR", BASE_DIR / "library"))

DEFAULT_LOCALE = "us"


def get_downloads_dir() -> Path:
    from app import db

    value = db.get_setting("downloads_dir")
    return Path(value) if value else DEFAULT_DOWNLOADS_DIR


def get_library_output_dir() -> Path:
    from app import db

    value = db.get_setting("library_output_dir")
    return Path(value) if value else DEFAULT_LIBRARY_OUTPUT_DIR


def get_organize_by_author() -> bool:
    from app import db

    value = db.get_setting("organize_by_author")
    return value != "false"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
