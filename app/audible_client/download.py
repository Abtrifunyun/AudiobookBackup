import json
import logging
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import audible
import httpx
from audible.aescipher import decrypt_voucher_from_licenserequest

from app.config import get_downloads_dir

logger = logging.getLogger(__name__)

QUALITY_TO_API = {"best": "High", "high": "High", "normal": "Normal"}

EXPECTED_AUDIO_CONTENT_TYPES = (
    "audio/aax",
    "audio/vnd.audible.aax",
    "audio/audible",
    "audio/mp4",
    "audio/mpeg",
    "audio/mp3",
    "audio/x-m4a",
)


class LicenseDeniedError(Exception):
    pass


class NoDownloadUrlError(Exception):
    pass


class DownloadContentTypeError(Exception):
    pass


@dataclass
class DownloadResult:
    download_format: str
    raw_file_path: str
    voucher_file_path: str
    file_size_bytes: int


async def _get_license(client: audible.AsyncClient, asin: str, quality: str) -> dict:
    body = {
        "supported_drm_types": ["Mpeg", "Adrm"],
        "quality": QUALITY_TO_API[quality],
        "consumption_type": "Download",
        "response_groups": "last_position_heard, pdf_url, content_reference",
    }
    headers = {
        "X-Amzn-RequestId": secrets.token_hex(20).upper(),
        "X-ADP-SW": "37801821",
        "X-ADP-Transport": "WIFI",
        "X-ADP-LTO": "120",
        "X-Device-Type-Id": "A2CZJZGLK2JJVM",
        "device_idiom": "phone",
    }
    return await client.post(f"content/{asin}/licenserequest", body=body, headers=headers)


DOWNLOAD_USER_AGENT = "Audible, iPhone, 3.35.1 (644), iPhone XS (iPhone11,2), 238 GB, iOS, 14.1, Wifi"


async def _stream_download(session: httpx.AsyncClient, url: str, dest: Path) -> int:
    async with session.stream(
        "GET", url, follow_redirects=True, headers={"User-Agent": DOWNLOAD_USER_AGENT}
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in EXPECTED_AUDIO_CONTENT_TYPES:
            raise DownloadContentTypeError(
                f"Unexpected content type {content_type!r} - Audible likely returned "
                "an error page instead of audio"
            )
        size = 0
        with open(dest, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
                size += len(chunk)
    return size


async def download_book(
    auth: audible.Authenticator, asin: str, quality: str = "high"
) -> DownloadResult:
    downloads_dir = get_downloads_dir()
    downloads_dir.mkdir(parents=True, exist_ok=True)

    # Keep the license request and the file download on the SAME client/session
    # rather than opening a fresh one for each - if the licenserequest response
    # sets any cookies the CDN checks (common for CloudFront-fronted content),
    # a separate client would silently drop them and the file GET gets a 403
    # even though the pre-signed URL itself is otherwise valid.
    async with audible.AsyncClient(auth, timeout=120) as client:
        license_response = await _get_license(client, asin, quality)

        content_license = license_response["content_license"]
        if content_license.get("status_code") == "Denied":
            reasons = content_license.get("license_denial_reasons") or []
            message = content_license.get("message") or (
                reasons[0].get("message") if reasons else "Unknown reason"
            )
            raise LicenseDeniedError(message)

        content_metadata = content_license.get("content_metadata") or {}
        download_url = (content_metadata.get("content_url") or {}).get("offline_url")
        if not download_url:
            raise NoDownloadUrlError(f"No download URL in license response for {asin}")
        codec = content_metadata["content_reference"]["content_format"]

        try:
            voucher = decrypt_voucher_from_licenserequest(auth, license_response)
            content_license["license_response"] = voucher
        except Exception:
            logger.exception("Failed to decrypt voucher for %s", asin)

        ext = "mp3" if codec.lower() == "mpeg" else "aaxc"
        raw_path = downloads_dir / f"{asin}.{ext}"
        voucher_path = downloads_dir / f"{asin}.voucher"

        voucher_path.write_text(json.dumps(license_response, indent=2))

        file_size = await _stream_download(client.session, download_url, raw_path)

    return DownloadResult(
        download_format="aaxc",
        raw_file_path=str(raw_path),
        voucher_file_path=str(voucher_path),
        file_size_bytes=file_size,
    )
