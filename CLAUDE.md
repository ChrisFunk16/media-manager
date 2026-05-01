# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```bash
# Web UI (primary interface)
python scripts/webui.py
python scripts/webui.py --port=8080

# CLI menu
python media-manager.py

# Individual operations
python scripts/auto-sort.py          # Sort incoming/ into sorted/
python scripts/convert-webm.py       # Convert WebM files to MP4
python scripts/deduplicate.py        # Remove duplicate images
python batch-download.py             # Download all URLs from urls.txt / links.txt
python scripts/scheduler.py          # Run due scheduled jobs

# Install dependencies
pip install flask gallery-dl yt-dlp pyperclip bs4
```

FFmpeg must be on PATH for WebM conversion and video thumbnail generation.

## Architecture

### Path Model
`config.json` controls all paths. `media_base_dir` can point to any drive (e.g. `F:/MediaManager/Media`) or be `null` to use the repo root. All scripts resolve this independently:
```python
MEDIA_BASE = Path(config['media_base_dir']).expanduser() if config['media_base_dir'] else BASE_DIR
SORTED = MEDIA_BASE / config['sorted']   # default: .../sorted
INCOMING = MEDIA_BASE / config['incoming']  # default: .../incoming
```
Script files and JSON state files always stay in the repo root (`BASE_DIR`). Media files live in `MEDIA_BASE`.

### Web UI (`scripts/webui.py`)
Single-file Flask app with the entire HTML/CSS/JS template embedded as a Python string (`TEMPLATE`). All state is file-based — no database:
- `favorites.json` — set of `rel_path` strings (relative to `SORTED/`)
- `sessions.json` — dict of `{ name: [rel_path, ...] }`
- `.thumbcache/` — FFmpeg-generated JPEG thumbnails, keyed by MD5 of filepath

Media is served via `/media/<path>` and `/thumb/<path>` with path-traversal guards (`resolve()` + `relative_to()`). All mutation routes are POST/DELETE JSON APIs under `/api/`.

The `outbox/` folder (`SORTED/outbox/`) is a special write-only staging area for files the user wants to send. It is not in `CATEGORIES` but handled as a special case in `search_files()`.

### Downloader (`scripts/media-downloader.py`)
Detects URL type and routes to either `gallery-dl` (images/Reddit/booru) or `yt-dlp` with a custom HypnoTube plugin. Installation state is tracked via a flag file (`.hypnotube_plugin_installed`) to avoid repeated pip calls.

### Sorter (`scripts/auto-sort.py`)
Recursively scans `incoming/`, classifies by extension, and moves files to `sorted/images/`, `sorted/gifs/`, or `sorted/videos/YYYY-MM-DD/`. Detects browser duplicate patterns (`filename (1).ext`) and discards them if the original already exists in the target.

### Video Categories
`sorted/videos/` contains both date-stamped subfolders (auto-created by sorter) and named category subfolders (`sissy`, `hypno`, `cock`, etc., created by `setup-video-folders.py`). The web UI treats all subdirectories dynamically as subcategories.

### Scheduler (`scripts/scheduler.py`) + `jobs.json`
Jobs are plain dicts with URL, tags, and a schedule. The scheduler checks `jobs.json` on each run and executes any job whose scheduled time has passed and hasn't run today.

### Tag Presets (`tag-presets.json`)
Hierarchical preset system: presets are named tag lists, mixes reference other presets by name. Resolved recursively at download time. Managed interactively via the CLI menu.
