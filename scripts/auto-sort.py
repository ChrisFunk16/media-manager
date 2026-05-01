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
GIF_EXTS = {'.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v'}

def get_category(file_path):
    """Bestimmt Kategorie basierend auf Extension"""
    ext = file_path.suffix.lower()
    
    if ext in GIF_EXTS:
        return "gifs"
    elif ext in IMAGE_EXTS:
        return "images"
    elif ext in VIDEO_EXTS:
        return "videos"
    else:
        # Fallback: MIME-Type checken
        mime, _ = mimetypes.guess_type(str(file_path))
        if mime:
            if mime == 'image/gif':
                return "gifs"
            elif mime.startswith('image/'):
                return "images"
            elif mime.startswith('video/'):
                return "videos"
    
    return None  # Unbekannt

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

def sort_files():
    """Sortiert alle Files aus incoming/ (inkl. Unterordner)"""
    if not INCOMING.exists():
        print(f"❌ {INCOMING} existiert nicht")
        return
    
    # Find all files recursively (inkl. Unterordner)
    files = []
    for root, dirs, filenames in os.walk(INCOMING):
        for filename in filenames:
            files.append(Path(root) / filename)
    
    if not files:
        print("✅ Keine Files zum Sortieren")
        return
    
    sorted_count = 0
    skipped_count = 0
    duplicate_removed_count = 0
    
    for file_path in files:
        category = get_category(file_path)
        
        if category:
            # Videos: In Datum-Unterordner (z.B. sorted/videos/2026-04-20/)
            # Bilder/GIFs: Direkt (zu fragmentiert sonst)
            # Datum kommt aus mtime, damit Backlogs ihren Erstell-Zeitpunkt
            # behalten statt alle in den heutigen Ordner zu fallen.
            if category == "videos":
                try:
                    mtime = file_path.stat().st_mtime
                    date_folder = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                except OSError:
                    date_folder = datetime.now().strftime("%Y-%m-%d")
                target_dir = SORTED / category / date_folder
            else:
                target_dir = SORTED / category
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Prüfe ob Datei ein Duplikat ist (z.B. "bild (1).jpg")
            is_dup, original_name = is_duplicate_copy(file_path)
            
            if is_dup:
                # Prüfe ob Original im Zielordner existiert
                original_path = target_dir / original_name
                
                if original_path.exists():
                    # Original existiert → Duplikat löschen
                    file_path.unlink()
                    print(f"🗑️ Duplikat entfernt: {file_path.name} (Original: {original_name})")
                    duplicate_removed_count += 1
                    continue  # Nächste Datei
                # Falls Original nicht existiert, wird das "Duplikat" normal verschoben
            
            target_path = target_dir / file_path.name
            
            # Handle Duplikate (falls Datei mit gleichem Namen schon existiert)
            if target_path.exists():
                base = target_path.stem
                ext = target_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            shutil.move(str(file_path), str(target_path))
            
            # Anzeige: Mit Datum-Ordner wenn vorhanden
            if category == "videos":
                date_folder = target_dir.name  # z.B. "2026-04-20"
                print(f"✅ {file_path.name} → {category}/{date_folder}/")
            else:
                print(f"✅ {file_path.name} → {category}/")
            
            sorted_count += 1
        else:
            print(f"⚠️ Übersprungen (unbekannter Typ): {file_path.name}")
            skipped_count += 1
    
    # Cleanup: Lösche leere Unterordner in incoming/
    for root, dirs, _files in os.walk(INCOMING, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # Leer?
                    dir_path.rmdir()
                    print(f"🗑️ Leerer Ordner entfernt: {dir_path.relative_to(INCOMING)}")
            except OSError:
                pass  # Ordner nicht leer oder Permission-Error → ignorieren
    
    print(f"\n📊 Fertig: {sorted_count} sortiert, {duplicate_removed_count} Duplikate entfernt, {skipped_count} übersprungen")

if __name__ == "__main__":
    sort_files()
