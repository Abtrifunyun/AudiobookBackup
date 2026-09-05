import asyncio
import json
import logging
import sqlite3
import threading

from fastapi import APIRouter, HTTPException

from app import config, db
from app.audible_client import books as audible_books
from app.audible_client import download as audible_download
from app.auth import service as auth_service
from app.convert import ffmpeg as convert_ffmpeg
from app.error_log import log_exception
from app.models import BookOut, LibraryResponse, LibrarySyncResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])

IN_PROGRESS_DOWNLOAD_STATUSES = ("queued", "downloading")
IN_PROGRESS_CONVERT_STATUSES = ("queued", "converting")


def _book_out_from_row(row: sqlite3.Row) -> BookOut:
    return BookOut(
        asin=row["asin"],
        title=row["title"],
        subtitle=row["subtitle"],
        authors=json.loads(row["authors_json"] or "[]"),
        narrators=json.loads(row["narrators_json"] or "[]"),
        publisher=row["publisher"],
        series_title=row["series_title"],
        series_sequence=row["series_sequence"],
        language=row["language"],
        summary=row["summary"],
        runtime_length_min=row["runtime_length_min"],
        release_date=row["release_date"],
        purchase_date=row["purchase_date"],
        cover_url=row["cover_url"],
        cover_local_path=row["cover_local_path"],
        file_size_bytes=row["file_size_bytes"],
        download_status=row["download_status"],
        download_error=row["download_error"],
        convert_status=row["convert_status"],
        convert_error=row["convert_error"],
        output_file_path=row["output_file_path"],
    )


@router.get("", response_model=LibraryResponse)
async def get_library() -> LibraryResponse:
    rows = db.get_all_books()
    last_sync = db.get_last_sync()
    return LibraryResponse(
        books=[_book_out_from_row(row) for row in rows],
        last_synced_at=last_sync["finished_at"] if last_sync else None,
    )


@router.get("/{asin}", response_model=BookOut)
async def get_book(asin: str) -> BookOut:
    row = db.get_book_by_asin(asin)
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return _book_out_from_row(row)


def _run_download(asin: str) -> None:
    db.mark_download_status(asin, "downloading")
    try:
        auth = auth_service.load_authenticator()
        result = asyncio.run(audible_download.download_book(auth, asin))
        db.save_download_result(
            asin,
            result.download_format,
            result.raw_file_path,
            result.voucher_file_path,
            result.file_size_bytes,
        )
    except Exception as exc:
        log_exception(f"download:{asin}", exc)
        db.mark_download_status(asin, "failed", error=str(exc))


@router.post("/{asin}/download")
async def start_download(asin: str) -> dict:
    if not auth_service.is_logged_in():
        raise HTTPException(status_code=401, detail="Not authenticated")
    row = db.get_book_by_asin(asin)
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if row["download_status"] in IN_PROGRESS_DOWNLOAD_STATUSES:
        raise HTTPException(status_code=409, detail="Download already in progress")

    db.mark_download_status(asin, "queued")
    threading.Thread(target=_run_download, args=(asin,), daemon=True).start()
    return {"success": True}


def _run_convert(asin: str) -> None:
    db.mark_convert_status(asin, "converting")
    try:
        row = db.get_book_by_asin(asin)
        if row is None:
            raise ValueError(f"Book {asin} not found")
        if not row["raw_file_path"]:
            raise ValueError("Book has not been downloaded yet")

        authors = json.loads(row["authors_json"] or "[]")
        narrators = json.loads(row["narrators_json"] or "[]")
        title = row["title"]

        author_dir = convert_ffmpeg.sanitize_path_component(authors[0] if authors else "Unknown Author")
        title_dir = convert_ffmpeg.sanitize_path_component(title)
        output_path = config.get_library_output_dir() / author_dir / title_dir / f"{title_dir}.m4b"

        result = convert_ffmpeg.convert_to_m4b(
            row["raw_file_path"], row["voucher_file_path"], output_path, title, authors, narrators
        )

        expected_seconds = (row["runtime_length_min"] or 0) * 60
        if expected_seconds and abs(result.duration_seconds - expected_seconds) > max(120, expected_seconds * 0.05):
            logger.warning(
                "Converted duration for %s (%.0fs) differs notably from expected (%.0fs)",
                asin, result.duration_seconds, expected_seconds,
            )

        db.save_convert_result(asin, "m4b", result.output_file_path)
    except Exception as exc:
        log_exception(f"convert:{asin}", exc)
        db.mark_convert_status(asin, "failed", error=str(exc))


@router.post("/{asin}/convert")
async def start_convert(asin: str) -> dict:
    row = db.get_book_by_asin(asin)
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if row["download_status"] != "downloaded":
        raise HTTPException(status_code=400, detail="Book must be downloaded before converting")
    if row["convert_status"] in IN_PROGRESS_CONVERT_STATUSES:
        raise HTTPException(status_code=409, detail="Conversion already in progress")

    db.mark_convert_status(asin, "queued")
    threading.Thread(target=_run_convert, args=(asin,), daemon=True).start()
    return {"success": True}


@router.post("/sync", response_model=LibrarySyncResponse)
async def sync_library() -> LibrarySyncResponse:
    if not auth_service.is_logged_in():
        raise HTTPException(status_code=401, detail="Not authenticated")

    sync_id = db.record_sync_start()
    try:
        auth = auth_service.load_authenticator()
        fetched = await audible_books.fetch_library(auth)
        for book in fetched:
            db.upsert_book(book)
            local_path = await audible_books.cache_cover(book.asin, book.cover_url)
            if local_path:
                db.set_cover_local_path(book.asin, local_path)
    except Exception as exc:
        log_exception("library.sync", exc)
        db.record_sync_finish(sync_id, "error", error_message=str(exc))
        raise HTTPException(status_code=502, detail=f"Library sync failed: {exc}")

    db.record_sync_finish(sync_id, "success", books_fetched=len(fetched))
    rows = db.get_all_books()
    last_sync = db.get_last_sync()
    return LibrarySyncResponse(
        books=[_book_out_from_row(row) for row in rows],
        last_synced_at=last_sync["finished_at"],
        books_fetched=len(fetched),
    )
