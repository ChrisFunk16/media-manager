#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Video Category Folders
Erstellt Unterordner-Struktur in sorted/videos/
"""

import json
from pathlib import Path

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
        except:
            pass
    
    return default_config

# Config laden
config = load_config()

# Base dir für Medien
if config['media_base_dir']:
    MEDIA_BASE = Path(config['media_base_dir']).expanduser()
else:
    MEDIA_BASE = BASE_DIR

SORTED_VIDEOS = MEDIA_BASE / config['sorted'] / "videos"

# Video-Kategorien
VIDEO_CATEGORIES = [
    "anal",
    "blowjob",
    "cum",
    "cumshot",
    "deepthroat",
    "dick",
    "dildo",
    "feminization",
    "gangbang",
    "joi",
    "makeup",
    "oral",
    "pov",
    "sissy",
    "sissytraining",
    "solo",
    "toys",
    "uncategorized"
]

def setup_folders():
    """Erstellt alle Kategorie-Ordner"""
    SORTED_VIDEOS.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Erstelle Video-Kategorien in: {SORTED_VIDEOS}\n")
    
    created = 0
    exists = 0
    
    for category in VIDEO_CATEGORIES:
        category_path = SORTED_VIDEOS / category
        
        if category_path.exists():
            print(f"✓ {category}/ (existiert bereits)")
            exists += 1
        else:
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ {category}/ (erstellt)")
            created += 1
    
    print(f"\n📊 Fertig: {created} neu erstellt, {exists} bereits vorhanden")
    print(f"\n💡 Tipp: Verschiebe Videos manuell in passende Kategorien")
    print(f"   Oder: Auto-Sort lädt weiterhin in Datum-Ordner (2026-04-20/)")

if __name__ == "__main__":
    setup_folders()
