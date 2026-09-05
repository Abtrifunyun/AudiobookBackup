# Audiobook Backup Tool

Personal tool to log into your own Audible account, pull your purchased library, and convert
AAX/AAXC audiobooks to DRM-free MP3/M4B for offline listening. Single-user, local-only — not a
redistribution tool.

## Status

Phase 0-2 complete and verified against a real Audible account: project scaffold, real Audible
login through a browser-handoff flow, and a library view backed by a SQLite cache of your
purchased titles (covers, authors, narrators, runtime all confirmed populating correctly).

Not yet built: downloading AAX/AAXC files, ffmpeg conversion, output verification, Settings screen.

## Running the app

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_app.py
```

This opens a native desktop window (via pywebview) — not a browser tab. `run_app.py` starts the
FastAPI backend in a background thread and points the window at it.

## Development

For active development with hot-reload in a browser instead of the packaged window:

```powershell
scripts\run_dev.ps1
```

Then open http://127.0.0.1:8000/ in a browser.

## Tests

```powershell
pytest
```
