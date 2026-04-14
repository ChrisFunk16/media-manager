#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Sortierer für Media Files
Überwacht incoming/ und sortiert nach Dateityp
"""

import os
import shutil
from pathlib import Path
import mimetypes

# Pfade
BASE_DIR = Path(__file__).parent.parent
INCOMING = BASE_DIR / "incoming"
SORTED = BASE_DIR / "sorted"

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
    
    for file_path in files:
        category = get_category(file_path)
        
        if category:
            target_dir = SORTED / category
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_path = target_dir / file_path.name
            
            # Handle Duplikate
            if target_path.exists():
                base = target_path.stem
                ext = target_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            shutil.move(str(file_path), str(target_path))
            print(f"✅ {file_path.name} → {category}/")
            sorted_count += 1
        else:
            print(f"⚠️ Übersprungen (unbekannter Typ): {file_path.name}")
            skipped_count += 1
    
    # Cleanup: Lösche leere Unterordner in incoming/
    for root, dirs, files in os.walk(INCOMING, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # Leer?
                    dir_path.rmdir()
                    print(f"🗑️ Leerer Ordner entfernt: {dir_path.relative_to(INCOMING)}")
            except:
                pass  # Ignore errors
    
    print(f"\n📊 Fertig: {sorted_count} sortiert, {skipped_count} übersprungen")

if __name__ == "__main__":
    sort_files()
