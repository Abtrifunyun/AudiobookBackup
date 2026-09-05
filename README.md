# Audiobook Backup Tool

Personal tool to log into your own Audible account, pull your purchased library, and convert
AAX/AAXC audiobooks to DRM-free MP3/M4B for offline listening. Single-user, local-only — not a
redistribution tool.

## Status

Phase 0-2 complete and verified against a real Audible account: project scaffold, real Audible
login through a browser-handoff flow, and a library view backed by a SQLite cache of your
purchased titles (covers, authors, narrators, runtime all confirmed populating correctly).

Phase 3 (AAXC download) complete and verified: per-book license request, voucher decryption
(key/iv), and a background-thread download with a persistent issue log for anything that fails
along the way. Downloaded files were confirmed with `ffprobe -audible_key ... -audible_iv ...` to
be valid, correctly-timed audio, not just successfully-saved bytes. The one real gotcha: Audible's
content CDN rejects the file GET with a 403 unless the request carries an Audible-iOS-shaped
`User-Agent` header (`app/audible_client/download.py`'s `DOWNLOAD_USER_AGENT`) — the license
request itself, and every other API call, works fine without it.

AAX (the older, whole-account-activation-bytes format) isn't implemented — this account's content
resolves to AAXC either way, so it was deliberately skipped rather than built speculatively.

Phase 4 (convert to M4B) complete and verified: `-audible_key`/`-audible_iv` decrypt the AAXC
directly into a lossless `-c copy` remux (no re-encoding — the source audio is already AAC, so
this is a true zero-quality-loss DRM strip, not a transcode), preserving the container's own
chapter markers and embedding title/author/narrator metadata. Output lands at
`library/<Author>/<Title>/<Title>.m4b`. Verified end-to-end: converted duration matched the
source to within 0.01s, all chapters intact, metadata tags correct. MP3 output isn't implemented
(would need real re-encoding, not a copy) — M4B was the natural default since it's genuinely
lossless and audiobook-native (single file, real chapter support).

Settings screen (partial) complete and verified: downloads folder and converted-output folder are
configurable in-app (`/settings.html`), persisted in the `app_settings` table, take effect on the
next download/convert with no restart needed, and validate/create the folder on save rather than
failing silently later. Default format/bitrate and delete-after-convert are not built - only
location is, since that's what was asked for.

Phase 5 (verify + player) complete and verified: a book detail page (`/book.html?asin=...`,
reachable by clicking any title in the library) with a real `<audio>` player streaming the
converted M4B (Range-request-enabled for seeking - confirmed via a manual `Range:` header test and
by actually playing audio and watching `currentTime` advance), a clickable chapter list that seeks
the player, and a "Run Verification" button. Verification re-probes the file with ffprobe and
reports duration match, chapter count, cover art presence, and metadata tags — persisted per book
(`verify_details_json`, added via a guarded schema migration that preserved the existing 26-book
library rather than a blind `CREATE TABLE`). Delete-original isn't built - verify only reports, it
doesn't act.

Not yet built: delete-original action, format/bitrate settings, batch operations.

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
