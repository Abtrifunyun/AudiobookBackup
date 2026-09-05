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
    download_status: str
    convert_status: str


class LibraryResponse(BaseModel):
    books: list[BookOut]
    last_synced_at: Optional[str] = None


class LibrarySyncResponse(BaseModel):
    books: list[BookOut]
    last_synced_at: str
    books_fetched: int


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
