# Audiobook Backup Tool

Personal tool to log into your own Audible account, pull your purchased library, and convert
AAX/AAXC audiobooks to DRM-free MP3/M4B for offline listening. Single-user, local-only — not a
redistribution tool.

> **What this is (and isn't):** source code shared for reference, not a packaged app for general
> use — there are no releases or pre-built binaries, and none are planned. Running it requires
> your own Python setup and your own Audible login; it can only ever access and decrypt content
> *that account already owns*, the same way [OpenAudible](https://openaudible.org),
> [Libation](https://getlibation.com), and [audible-cli](https://github.com/mkb79/audible-cli) do.
> It doesn't circumvent anything for content you don't already have a license to, and it isn't
> built to distribute converted files anywhere.

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

Phase 5 (verify + player), reworked since first built: originally a per-book page tied to the
Audible-authenticated library (ASIN-keyed, DB-backed). Now a standalone player (`/player.html`)
that scans the converted-output folder directly and reads each file's own embedded tags via
ffprobe — no Audible auth, no database, works before login. Opens as a genuinely separate native
window (pywebview `js_api` bridge, verified against pywebview's own source for the
already-running-GUI case) via "Open Player" on the login screen or library header. Has a real
`<audio>` player (Range-request-enabled, confirmed by watching `currentTime` actually advance), a
clickable chapter list, and on-demand verification (duration/chapters/cover/tags) that isn't
persisted anywhere, since there's no DB row to persist it to. Delete-original isn't built - verify
only reports, it doesn't act.

**Login is scoped to only what needs it**: pulling your library (`Refresh Library`) and
downloading (`Download`) are the only two actions that actually talk to Audible, so those are the
only things gated behind login - clicking either while logged out sends you to the login screen.
Everything else - viewing your cached library, converting already-downloaded books, Settings, and
the standalone Player - works without ever logging in. `library.html` is the real landing page
(`run_app.py` points the window there directly); the login screen is reachable from it and from
itself offers Settings/Player/Library so it's never a dead end.

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
