import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class VerifyResult:
    valid: bool
    duration_seconds: Optional[float] = None
    expected_duration_seconds: Optional[float] = None
    chapter_count: int = 0
    has_audio_stream: bool = False
    has_cover_art: bool = False
    title_tag: Optional[str] = None
    artist_tag: Optional[str] = None
    composer_tag: Optional[str] = None
    issues: list[str] = field(default_factory=list)


def verify_m4b(path: Path, expected_duration_seconds: Optional[float] = None) -> VerifyResult:
    if not path.exists():
        return VerifyResult(valid=False, issues=[f"File does not exist: {path}"])

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_format", "-show_streams", "-show_chapters",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return VerifyResult(
            valid=False,
            issues=[f"ffprobe could not read the file: {probe.stderr.strip()[:500]}"],
        )

    try:
        data = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return VerifyResult(valid=False, issues=["ffprobe returned unparseable output"])

    fmt = data.get("format", {})
    duration_str = fmt.get("duration")
    duration = float(duration_str) if duration_str else None

    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    title_tag = tags.get("title")
    artist_tag = tags.get("artist")
    composer_tag = tags.get("composer")

    streams = data.get("streams", [])
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    has_cover = any(s.get("codec_type") == "video" for s in streams)
    chapters = data.get("chapters", [])

    # Critical: things that mean the file isn't safe to trust (and the original
    # shouldn't be deleted yet). Missing tags/cover/chapters are surfaced too,
    # but don't block "verified" - a book with no cover is still a real book.
    critical_issues: list[str] = []
    if not has_audio:
        critical_issues.append("No audio stream found")
    if duration is None:
        critical_issues.append("No duration reported - file may be corrupt")
    if expected_duration_seconds and duration:
        diff = abs(duration - expected_duration_seconds)
        tolerance = max(60.0, expected_duration_seconds * 0.05)
        if diff > tolerance:
            critical_issues.append(
                f"Duration differs from library metadata by {diff:.0f}s "
                f"(got {duration:.0f}s, expected ~{expected_duration_seconds:.0f}s)"
            )

    informational_issues: list[str] = []
    if not title_tag:
        informational_issues.append("Missing title metadata")
    if not artist_tag:
        informational_issues.append("Missing author (artist) metadata")
    if not has_cover:
        informational_issues.append("No embedded cover art")
    if not chapters:
        informational_issues.append("No chapter markers")

    return VerifyResult(
        valid=len(critical_issues) == 0,
        duration_seconds=duration,
        expected_duration_seconds=expected_duration_seconds,
        chapter_count=len(chapters),
        has_audio_stream=has_audio,
        has_cover_art=has_cover,
        title_tag=title_tag,
        artist_tag=artist_tag,
        composer_tag=composer_tag,
        issues=critical_issues + informational_issues,
    )
