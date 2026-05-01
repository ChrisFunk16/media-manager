#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Sortierer für Media Files
Überwacht incoming/ und sortiert nach Dateityp
"""

import os
import re
import shutil
import json
from datetime import datetime
from pathlib import Path
import mimetypes

# Pfade
BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """Lädt Config für Pfade"""
    default_config = {
        "media_base_dir": None,
        "incoming": "incoming",
        "sorted": "sorted"
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

            for key, value in default_config.items():
                if key not in config:
                    config[key] = value

            return config
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ Config konnte nicht geladen werden ({e}), nutze Defaults")

    return default_config

# Config laden
config = load_config()

# Base dir für Medien
if config['media_base_dir']:
    MEDIA_BASE = Path(config['media_base_dir']).expanduser()
else:
    MEDIA_BASE = BASE_DIR

INCOMING = MEDIA_BASE / config['incoming']
SORTED = MEDIA_BASE / config['sorted']

# Kategorien
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.svg'}
GIF_EXTS   = {'.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v'}
AUDIO_EXTS = {'.mp3', '.m4a', '.ogg', '.flac', '.wav', '.aac', '.opus', '.wma'}

def get_category(file_path):
    """Bestimmt Kategorie basierend auf Extension"""
    ext = file_path.suffix.lower()

    if ext in GIF_EXTS:   return "gifs"
    if ext in IMAGE_EXTS: return "images"
    if ext in VIDEO_EXTS: return "videos"
    if ext in AUDIO_EXTS: return "audio"

    # Fallback: MIME-Type
    mime, _ = mimetypes.guess_type(str(file_path))
    if mime:
        if mime == 'image/gif':       return "gifs"
        if mime.startswith('image/'): return "images"
        if mime.startswith('video/'): return "videos"
        if mime.startswith('audio/'): return "audio"

    return None

def is_duplicate_copy(file_path):
    """
    Prüft ob eine Datei ein Browser-Duplikat ist (z.B. "bild (1).jpg")
    Returns: (is_duplicate, original_name)
    """
    stem = file_path.stem
    ext = file_path.suffix
    
    # Pattern: "filename (1)", "filename (2)", etc.
    match = re.match(r'^(.+?)\s*\((\d+)\)$', stem)
    
    if match:
        original_stem = match.group(1).strip()
        original_name = original_stem + ext
        return (True, original_name)
    
    return (False, None)

# Top-Level-Kategorien die direkt als Ziel gelten
TOP_CATEGORIES = {'images', 'gifs', 'videos', 'hypno', 'audio'}

# Keyword-Mapping: Wenn Subfolder-Name dieses Wort enthält → diese Kategorie
CATEGORY_KEYWORDS = {
    'hypno': 'hypno',
    'image': 'images',
    'gif':   'gifs',
    'video': 'videos',
    'audio': 'audio',
    'sound': 'audio',
    'musik': 'audio',
    'music': 'audio',
}

# Audio-Subkategorien: Wenn Audiodatei AND Subfolder enthält dieses Keyword → audio/<subcat>/
AUDIO_SUBCAT_KEYWORDS = {
    'hypno': 'hypno',
    'sissy': 'sissy',
    'relax': 'relax',
    'sleep': 'sleep',
}


def _date_subfolder(file_path: Path) -> str:
    try:
        return datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now().strftime("%Y-%m-%d")


def resolve_target_dir(file_path: Path) -> tuple:
    """
    Returns (target_dir: Path, display: str) for a file from incoming/.

    All auto-sorted files land in  sorted/<cat>/new/YYYY-MM-DD/  so the user
    can review and re-sort them from the "New" view before they mix with the
    existing library.

    Routing priority (when file is in incoming/<subfolder>/):
      1. Exact top-level category match  →  sorted/<subfolder>/new/<date>/
      2. Existing video subcategory      →  sorted/videos/<subfolder>/new/<date>/
      3. Keyword in subfolder name       →  sorted/<matched_cat>/new/<date>/
      4. Default                         →  sorted/<type>/new/<date>/
    """
    file_cat = get_category(file_path)
    if not file_cat:
        return None, None

    date_dir = _date_subfolder(file_path)

    # Detect subfolder inside incoming/
    try:
        rel_parts = file_path.relative_to(INCOMING).parts
    except ValueError:
        rel_parts = ()

    subfolder = rel_parts[0] if len(rel_parts) > 1 else None
    sub_lower = subfolder.lower() if subfolder else ''

    def _new(base: Path, label: str):
        """Wrap target in new/<date>/ subfolder."""
        return base / 'new' / date_dir, f"{label}new/{date_dir}/"

    # ── Bilder und GIFs: immer eigene Kategorie ──────────────────────────────
    if file_cat in ('images', 'gifs'):
        return _new(SORTED / file_cat, f"{file_cat}/")

    # ── Audio ─────────────────────────────────────────────────────────────────
    if file_cat == 'audio':
        if sub_lower:
            for kw, subcat in AUDIO_SUBCAT_KEYWORDS.items():
                if kw in sub_lower:
                    return _new(SORTED / 'audio' / subcat, f"audio/{subcat}/")
        return _new(SORTED / 'audio', 'audio/')

    # ── Videos: Subfolder-Routing ─────────────────────────────────────────────
    if subfolder:
        # 1. Exact top-level category match (z.B. incoming/hypno/ → sorted/hypno/)
        if sub_lower in TOP_CATEGORIES:
            return _new(SORTED / sub_lower, f"{sub_lower}/")

        # 2. Bekannte Video-Subkategorie (z.B. incoming/sissy/ → sorted/videos/sissy/)
        video_sub = SORTED / 'videos' / subfolder
        if video_sub.exists():
            return _new(video_sub, f"videos/{subfolder}/")

        # 3. Keyword-Match (z.B. incoming/sissyhypno/ → sorted/hypno/)
        for keyword, mapped_cat in CATEGORY_KEYWORDS.items():
            if keyword in sub_lower:
                return _new(SORTED / mapped_cat, f"{mapped_cat}/")

    # 4. Default
    return _new(SORTED / 'videos', 'videos/')


def sort_files():
    """Sortiert alle Files aus incoming/ (inkl. Unterordner) mit intelligentem Subfolder-Routing."""
    if not INCOMING.exists():
        print(f"Fehler: {INCOMING} existiert nicht")
        return

    files = []
    for root, dirs, filenames in os.walk(INCOMING):
        for filename in filenames:
            files.append(Path(root) / filename)

    if not files:
        print("Keine Files zum Sortieren")
        return

    sorted_count = 0
    skipped_count = 0
    duplicate_removed_count = 0

    for file_path in files:
        target_dir, display = resolve_target_dir(file_path)

        if target_dir is None:
            print(f"Uebersprungen (unbekannter Typ): {file_path.name}")
            skipped_count += 1
            continue

        target_dir.mkdir(parents=True, exist_ok=True)

        # Duplikat-Check (z.B. "bild (1).jpg")
        is_dup, original_name = is_duplicate_copy(file_path)
        if is_dup and (target_dir / original_name).exists():
            file_path.unlink()
            print(f"Duplikat entfernt: {file_path.name}")
            duplicate_removed_count += 1
            continue

        target_path = target_dir / file_path.name
        if target_path.exists():
            base, ext = target_path.stem, target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{base}_{counter}{ext}"
                counter += 1

        shutil.move(str(file_path), str(target_path))
        print(f"OK {file_path.name} -> {display}")
        sorted_count += 1

    # Cleanup leere Unterordner in incoming/
    for root, dirs, _files in os.walk(INCOMING, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"Leerer Ordner entfernt: {dir_path.relative_to(INCOMING)}")
            except OSError:
                pass

    print(f"\nFertig: {sorted_count} sortiert, {duplicate_removed_count} Duplikate entfernt, {skipped_count} uebersprungen")

if __name__ == "__main__":
    sort_files()
