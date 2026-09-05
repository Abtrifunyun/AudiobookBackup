import json
import sqlite3

from fastapi import APIRouter, HTTPException

from app import db
from app.audible_client import books as audible_books
from app.auth import service as auth_service
from app.models import BookOut, LibraryResponse, LibrarySyncResponse

router = APIRouter(prefix="/api/library", tags=["library"])


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
        download_status=row["download_status"],
        convert_status=row["convert_status"],
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
