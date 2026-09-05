import logging
import traceback as traceback_module
from datetime import datetime, timezone

from app.config import BASE_DIR

CHANGELOG_PATH = BASE_DIR / "CHANGELOG.md"
CHANGELOG_HEADER = "# Changelog\n\nErrors and failures the app has hit while running, most recent first.\n\n"


def log_exception(source: str, exc: BaseException) -> None:
    logging.getLogger(source).exception(str(exc))
    append_changelog_entry(source, str(exc), traceback_module.format_exc())


def append_changelog_entry(source: str, message: str, traceback_text: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"## {timestamp} — {source}\n\n{message}\n\n```\n{traceback_text.strip()}\n```\n\n---\n\n"

    existing_body = ""
    if CHANGELOG_PATH.exists():
        existing_body = CHANGELOG_PATH.read_text(encoding="utf-8")
        if existing_body.startswith(CHANGELOG_HEADER):
            existing_body = existing_body[len(CHANGELOG_HEADER):]

    CHANGELOG_PATH.write_text(CHANGELOG_HEADER + entry + existing_body, encoding="utf-8")
