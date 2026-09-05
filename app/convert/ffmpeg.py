import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConvertError(Exception):
    pass


@dataclass
class ConvertResult:
    output_file_path: str
    duration_seconds: float


def sanitize_path_component(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip(" .")
    return name or "Unknown"


def _load_key_iv(voucher_path: Path) -> tuple[str, str]:
    voucher = json.loads(voucher_path.read_text())
    license_response = voucher["content_license"]["license_response"]
    return license_response["key"], license_response["iv"]


def probe_chapters(path: Path) -> list[dict]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return [
        {
            "title": (ch.get("tags") or {}).get("title", ""),
            "start_seconds": float(ch.get("start_time", 0)),
            "end_seconds": float(ch.get("end_time", 0)),
        }
        for ch in data.get("chapters", [])
    ]


def find_m4b_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.m4b"))


def probe_summary(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_chapters", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return {}
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    fmt = data.get("format", {})
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    duration_str = fmt.get("duration")
    return {
        "title": tags.get("title"),
        "artist": tags.get("artist"),
        "composer": tags.get("composer"),
        "duration_seconds": float(duration_str) if duration_str else None,
        "chapter_count": len(data.get("chapters", [])),
    }


def _probe_duration(path: Path) -> Optional[float]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def convert_to_m4b(
    raw_file_path: str,
    voucher_file_path: str,
    output_path: Path,
    title: str,
    authors: list[str],
    narrators: list[str],
) -> ConvertResult:
    key, iv = _load_key_iv(Path(voucher_file_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-audible_key", key,
        "-audible_iv", iv,
        "-i", raw_file_path,
        "-map", "0",
        "-map_chapters", "0",
        "-map_metadata", "0",
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={', '.join(authors)}",
        "-metadata", f"album={title}",
        "-metadata", f"composer={', '.join(narrators)}",
        "-f", "mp4",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise ConvertError(result.stderr[-4000:] or "ffmpeg failed with no stderr output")

    duration = _probe_duration(output_path)
    if duration is None:
        raise ConvertError("Converted file failed to probe - likely corrupt output")

    return ConvertResult(output_file_path=str(output_path), duration_seconds=duration)
