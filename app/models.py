from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel


class LoginStartRequest(BaseModel):
    locale: str = "us"


class LoginStartResponse(BaseModel):
    session_id: str
    login_url: str


class LoginCompleteRequest(BaseModel):
    session_id: str
    postlogin_url: str


class LoginCompleteResponse(BaseModel):
    success: bool
    error: Optional[str] = None


class AuthStatusResponse(BaseModel):
    authenticated: bool


class BookOut(BaseModel):
    asin: str
    title: str
    subtitle: Optional[str] = None
    authors: list[str] = []
    narrators: list[str] = []
    publisher: Optional[str] = None
    series_title: Optional[str] = None
    series_sequence: Optional[str] = None
    language: Optional[str] = None
    summary: Optional[str] = None
    runtime_length_min: Optional[int] = None
    release_date: Optional[str] = None
    purchase_date: Optional[str] = None
    cover_url: Optional[str] = None
    cover_local_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_status: str
    download_error: Optional[str] = None
    convert_status: str
    convert_error: Optional[str] = None
    output_file_path: Optional[str] = None


class ChapterOut(BaseModel):
    title: str
    start_seconds: float
    end_seconds: float


class ChaptersResponse(BaseModel):
    chapters: list[ChapterOut]


class PlayerBookOut(BaseModel):
    path: str
    file_name: str
    title: str
    artist: Optional[str] = None
    composer: Optional[str] = None
    duration_seconds: Optional[float] = None
    chapter_count: int = 0


class PlayerBooksResponse(BaseModel):
    books: list[PlayerBookOut]


class PlayerVerifyResponse(BaseModel):
    valid: bool
    duration_seconds: Optional[float] = None
    chapter_count: int = 0
    has_audio_stream: bool = False
    has_cover_art: bool = False
    title_tag: Optional[str] = None
    artist_tag: Optional[str] = None
    composer_tag: Optional[str] = None
    issues: list[str] = []


class LibraryResponse(BaseModel):
    books: list[BookOut]
    last_synced_at: Optional[str] = None


class LibrarySyncResponse(BaseModel):
    books: list[BookOut]
    last_synced_at: str
    books_fetched: int


class ErrorOut(BaseModel):
    id: int
    occurred_at: str
    source: str
    message: str
    traceback: Optional[str] = None


class ErrorsResponse(BaseModel):
    errors: list[ErrorOut]


class SettingsResponse(BaseModel):
    downloads_dir: str
    library_output_dir: str
    downloads_dir_is_default: bool
    library_output_dir_is_default: bool


class SettingsUpdateRequest(BaseModel):
    downloads_dir: Optional[str] = None
    library_output_dir: Optional[str] = None


@dataclass
class BookIn:
    asin: str
    title: str
    subtitle: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    narrators: list[str] = field(default_factory=list)
    publisher: Optional[str] = None
    series_title: Optional[str] = None
    series_sequence: Optional[str] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    summary: Optional[str] = None
    runtime_length_min: Optional[int] = None
    release_date: Optional[str] = None
    purchase_date: Optional[str] = None
    cover_url: Optional[str] = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
