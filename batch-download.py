#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Downloader - Download multiple URLs from a file
"""

import sys
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS = BASE_DIR / "scripts"
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

def download(url):
    """Download single URL"""
    cmd = [sys.executable, str(SCRIPTS / "media-downloader.py"), url]
    subprocess.run(cmd)

def main():
    # WICHTIG: links/urls bleiben im Script-Ordner (BASE_DIR), nicht MEDIA_BASE!
    # Genau wie SCRIPTS auch im Original bleiben
    urls_file = BASE_DIR / "urls.txt"
    links_file = BASE_DIR / "links.txt"
    
    source_file = None
    if links_file.exists():
        source_file = links_file
    elif urls_file.exists():
        source_file = urls_file
    
    if not source_file:
        print("❌ Keine URL-Datei gefunden!")
        print(f"\nErstelle eine der Dateien im Script-Ordner:")
        print(f"  • {links_file} (via Link Monitor)")
        print(f"  • {urls_file} (manuell)")
        print("\nBeispiel urls.txt:")
        print("https://reddit.com/r/wallpapers")
        print("https://redgifs.com/watch/somegif")
        print("https://rule34.xxx/index.php?page=post&s=list&tags=tag1")
        sys.exit(1)
    
    print(f"📥 Lade URLs aus: {source_file.name}\n")
    
    # Read URLs
    with open(source_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print(f"❌ Keine URLs in {source_file.name} gefunden!")
        sys.exit(1)
    
    print(f"📥 Gefunden: {len(urls)} URLs\n")
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(urls)}] {url}")
        print('='*60)
        download(url)
    
    print(f"\n✅ Fertig! {len(urls)} URLs heruntergeladen")
    
    # Archiviere verarbeitete URLs (History behalten!)
    # Archiv bleibt im Script-Ordner (BASE_DIR)
    archive_dir = BASE_DIR / "processed"
    archive_dir.mkdir(exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_file = archive_dir / f"{source_file.stem}-{timestamp}.txt"
    
    print(f"\n📦 Archiviere {source_file.name} → {archive_file.name}")
    source_file.rename(archive_file)
    print(f"✅ Archiviert nach: processed/{archive_file.name}")
    
    print("\nJetzt Auto-Sort laufen lassen:")
    print("  python scripts/auto-sort.py")

if __name__ == "__main__":
    main()
