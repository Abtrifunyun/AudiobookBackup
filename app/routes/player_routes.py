import asyncio
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app import config
from app.convert import ffmpeg as convert_ffmpeg
from app.convert import verify as convert_verify
from app.models import (
    ChapterOut,
    ChaptersResponse,
    PlayerBookOut,
    PlayerBooksResponse,
    PlayerVerifyResponse,
)

router = APIRouter(prefix="/api/player", tags=["player"])


def _resolve_safe_path(raw_path: str) -> Path:
    root = config.get_library_output_dir().resolve()
    try:
        candidate = Path(raw_path).resolve()
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid path: {exc}")
    if candidate != root and root not in candidate.parents:
        raise HTTPException(status_code=400, detail="Path is outside the converted output folder")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


@router.get("/books", response_model=PlayerBooksResponse)
async def list_player_books() -> PlayerBooksResponse:
    root = config.get_library_output_dir()
    files = convert_ffmpeg.find_m4b_files(root)
    books = []
    for f in files:
        summary = convert_ffmpeg.probe_summary(f)
        books.append(
            PlayerBookOut(
                path=str(f),
                file_name=f.name,
                title=summary.get("title") or f.stem,
                artist=summary.get("artist"),
                composer=summary.get("composer"),
                duration_seconds=summary.get("duration_seconds"),
                chapter_count=summary.get("chapter_count", 0),
            )
        )
    return PlayerBooksResponse(books=books)


@router.get("/audio")
async def get_player_audio(path: str = Query(...)) -> FileResponse:
    file_path = _resolve_safe_path(path)
    return FileResponse(file_path, media_type="audio/mp4", filename=file_path.name)


@router.get("/chapters", response_model=ChaptersResponse)
async def get_player_chapters(path: str = Query(...)) -> ChaptersResponse:
    file_path = _resolve_safe_path(path)
    chapters = convert_ffmpeg.probe_chapters(file_path)
    return ChaptersResponse(chapters=[ChapterOut(**ch) for ch in chapters])


@router.get("/cover")
async def get_player_cover(path: str = Query(...)) -> Response:
    file_path = _resolve_safe_path(path)

    def _extract() -> bytes:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(file_path),
                "-an", "-c:v", "copy", "-frames:v", "1",
                "-f", "image2pipe", "-",
            ],
            capture_output=True,
        )
        return result.stdout if result.returncode == 0 else b""

    cover_bytes = await asyncio.to_thread(_extract)
    if not cover_bytes:
        raise HTTPException(status_code=404, detail="No cover art embedded in this file")
    return Response(content=cover_bytes, media_type="image/jpeg")


@router.post("/verify", response_model=PlayerVerifyResponse)
async def verify_player_file(path: str = Query(...)) -> PlayerVerifyResponse:
    file_path = _resolve_safe_path(path)
    result = convert_verify.verify_m4b(file_path)
    return PlayerVerifyResponse(
        valid=result.valid,
        duration_seconds=result.duration_seconds,
        chapter_count=result.chapter_count,
        has_audio_stream=result.has_audio_stream,
        has_cover_art=result.has_cover_art,
        title_tag=result.title_tag,
        artist_tag=result.artist_tag,
        composer_tag=result.composer_tag,
        issues=result.issues,
    )
