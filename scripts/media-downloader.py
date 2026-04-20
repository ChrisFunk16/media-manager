#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Media Downloader
Lädt Bilder/Videos von verschiedenen Websites:
- Reddit (Posts, Subreddits, User)
- Rule34.xxx (Posts, Tags, Searches)
- Instagram, Twitter, Imgur, etc. (100+ Sites)

Benötigt: gallery-dl (pip install gallery-dl)
"""

import argparse
import subprocess
import sys
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

INCOMING = MEDIA_BASE / config['incoming']
SORTED = MEDIA_BASE / config['sorted']

def check_gallery_dl():
    """Prüft ob gallery-dl installiert ist"""
    try:
        subprocess.run(['gallery-dl', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_gallery_dl():
    """Installiert gallery-dl via pip"""
    print("📦 Installiere gallery-dl...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'gallery-dl'],
                      check=True)
        print("✅ Installation erfolgreich")
        return True
    except subprocess.CalledProcessError:
        print("❌ Installation fehlgeschlagen")
        return False

def download(url, dest='incoming', subfolder=None):
    """
    Lädt Medien von URL
    
    Args:
        url: Download-URL
        dest: Zielordner (incoming/bulk/favorites/images)
        subfolder: Optional subfolder name (z.B. preset name)
    """
    # Bestimme Zielpfad
    if dest == 'bulk':
        target_dir = SORTED / "bulk"
    elif dest == 'favorites':
        target_dir = SORTED / "favorites"
    elif dest == 'images':
        target_dir = SORTED / "images"
    else:
        target_dir = INCOMING
    
    # Subfolder hinzufügen wenn angegeben
    if subfolder:
        target_dir = target_dir / subfolder
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"⬇️ Lade: {url}")
    print(f"📁 Ziel: {target_dir}")
    
    cmd = [
        'gallery-dl',
        '--dest', str(target_dir),
        '--no-mtime',  # Keine Original-Timestamps
        url
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Download abgeschlossen")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Download:\n{e.stderr}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Universal Media Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Reddit
  media-downloader.py https://reddit.com/r/wallpapers
  
  # Rule34 nach bulk/
  media-downloader.py --dest bulk --subfolder sissy_general 'https://rule34.xxx/...'
  
  # Favorites mit Preset-Name
  media-downloader.py --dest favorites --subfolder makeup_closeup 'https://...'
  
  # Default (incoming/)
  media-downloader.py https://twitter.com/username/media
        """
    )
    
    parser.add_argument('url', help='Download-URL')
    parser.add_argument('--dest', 
                       choices=['incoming', 'bulk', 'favorites', 'images'],
                       default='incoming',
                       help='Zielordner (default: incoming)')
    parser.add_argument('--subfolder',
                       help='Subfolder name (z.B. preset name)')
    
    args = parser.parse_args()
    
    # Check/Install gallery-dl
    if not check_gallery_dl():
        print("⚠️ gallery-dl nicht gefunden")
        install = input("Installieren? (y/n): ")
        if install.lower() == 'y':
            if not install_gallery_dl():
                sys.exit(1)
        else:
            print("Abgebrochen")
            sys.exit(1)
    
    download(args.url, dest=args.dest, subfolder=args.subfolder)

if __name__ == "__main__":
    main()
