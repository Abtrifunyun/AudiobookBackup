import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app import config, db
from app.models import SettingsResponse, SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _build_response() -> SettingsResponse:
    return SettingsResponse(
        downloads_dir=str(config.get_downloads_dir()),
        library_output_dir=str(config.get_library_output_dir()),
        downloads_dir_is_default=db.get_setting("downloads_dir") in (None, ""),
        library_output_dir_is_default=db.get_setting("library_output_dir") in (None, ""),
    )


def _validate_and_prepare(raw_path: str, field_name: str) -> str:
    path = Path(raw_path.strip())
    if not path.is_absolute():
        raise HTTPException(status_code=400, detail=f"{field_name} must be an absolute path")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"Can't create {field_name} at {path}: {exc}")
    return str(path)


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return _build_response()


@router.post("/open-downloads-folder")
async def open_downloads_folder() -> dict:
    path = config.get_downloads_dir()
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))  # noqa: S606 - local single-user tool, opening its own configured folder
    return {"success": True}


@router.post("/open-library-folder")
async def open_library_folder() -> dict:
    path = config.get_library_output_dir()
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))  # noqa: S606 - local single-user tool, opening its own configured folder
    return {"success": True}


@router.post("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdateRequest) -> SettingsResponse:
    if body.downloads_dir is not None:
        value = "" if body.downloads_dir.strip() == "" else _validate_and_prepare(
            body.downloads_dir, "Downloads folder"
        )
        db.set_setting("downloads_dir", value)

    if body.library_output_dir is not None:
        value = "" if body.library_output_dir.strip() == "" else _validate_and_prepare(
            body.library_output_dir, "Converted output folder"
        )
        db.set_setting("library_output_dir", value)

    return _build_response()
