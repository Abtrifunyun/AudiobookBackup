import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

from app.config import DB_PATH
from app.models import BookIn

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    id                   INTEGER PRIMARY KEY,
    asin                 TEXT NOT NULL UNIQUE,

    title                TEXT NOT NULL,
    subtitle             TEXT,
    authors_json         TEXT NOT NULL DEFAULT '[]',
    narrators_json       TEXT NOT NULL DEFAULT '[]',
    publisher            TEXT,
    series_title         TEXT,
    series_sequence      TEXT,
    language             TEXT,
    isbn                 TEXT,
    summary              TEXT,
    runtime_length_min   INTEGER,
    release_date         TEXT,
    purchase_date        TEXT,
    cover_url            TEXT,
    cover_local_path     TEXT,
    raw_metadata_json    TEXT,

    download_status      TEXT NOT NULL DEFAULT 'not_downloaded'
                          CHECK (download_status IN ('not_downloaded','queued','downloading','downloaded','failed')),
    download_format       TEXT CHECK (download_format IN ('aax','aaxc')),
    raw_file_path          TEXT,
    voucher_file_path       TEXT,
    file_size_bytes           INTEGER,
    downloaded_at              TEXT,
    download_error              TEXT,

    convert_status         TEXT NOT NULL DEFAULT 'not_converted'
                            CHECK (convert_status IN ('not_converted','queued','converting','converted','failed')),
    convert_format           TEXT CHECK (convert_format IN ('mp3','m4b')),
    convert_bitrate            TEXT,
    output_file_path             TEXT,
    chapters_json                  TEXT,
    converted_at                    TEXT,
    convert_error                     TEXT,

    verified               INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
    verified_at             TEXT,
    original_deleted          INTEGER NOT NULL DEFAULT 0 CHECK (original_deleted IN (0,1)),

    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_books_download_status ON books(download_status);
CREATE INDEX IF NOT EXISTS idx_books_convert_status ON books(convert_status);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);

CREATE TABLE IF NOT EXISTS library_syncs (
    id             INTEGER PRIMARY KEY,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','error')),
    books_fetched  INTEGER,
    error_message  TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    key    TEXT PRIMARY KEY,
    value  TEXT
);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def upsert_book(book: BookIn) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO books (
                asin, title, subtitle, authors_json, narrators_json, publisher,
                series_title, series_sequence, language, isbn, summary,
                runtime_length_min, release_date, purchase_date, cover_url,
                raw_metadata_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asin) DO UPDATE SET
                title = excluded.title,
                subtitle = excluded.subtitle,
                authors_json = excluded.authors_json,
                narrators_json = excluded.narrators_json,
                publisher = excluded.publisher,
                series_title = excluded.series_title,
                series_sequence = excluded.series_sequence,
                language = excluded.language,
                isbn = excluded.isbn,
                summary = excluded.summary,
                runtime_length_min = excluded.runtime_length_min,
                release_date = excluded.release_date,
                purchase_date = excluded.purchase_date,
                cover_url = excluded.cover_url,
                raw_metadata_json = excluded.raw_metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                book.asin, book.title, book.subtitle,
                json.dumps(book.authors), json.dumps(book.narrators), book.publisher,
                book.series_title, book.series_sequence, book.language, book.isbn, book.summary,
                book.runtime_length_min, book.release_date, book.purchase_date, book.cover_url,
                json.dumps(book.raw_metadata), _now(),
            ),
        )


def set_cover_local_path(asin: str, cover_local_path: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE books SET cover_local_path = ?, updated_at = ? WHERE asin = ?",
            (cover_local_path, _now(), asin),
        )


def get_all_books() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM books ORDER BY title COLLATE NOCASE").fetchall()


def get_book_by_asin(asin: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM books WHERE asin = ?", (asin,)).fetchone()


def record_sync_start() -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO library_syncs (started_at, status) VALUES (?, 'running')",
            (_now(),),
        )
        return cursor.lastrowid


def record_sync_finish(
    sync_id: int,
    status: str,
    books_fetched: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE library_syncs SET finished_at = ?, status = ?, books_fetched = ?, error_message = ? WHERE id = ?",
            (_now(), status, books_fetched, error_message, sync_id),
        )


def get_last_sync() -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM library_syncs WHERE status = 'success' ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
