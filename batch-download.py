#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Downloader - Download multiple URLs from a file
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS = BASE_DIR / "scripts"

def download(url):
    """Download single URL"""
    cmd = [sys.executable, str(SCRIPTS / "media-downloader.py"), url]
    subprocess.run(cmd)

def main():
    # Check beide Dateien (links.txt bevorzugt, da aktueller vom Link Monitor)
    urls_file = BASE_DIR / "urls.txt"
    links_file = BASE_DIR / "links.txt"
    
    source_file = None
    if links_file.exists():
        source_file = links_file
    elif urls_file.exists():
        source_file = urls_file
    
    if not source_file:
        print("❌ Keine URL-Datei gefunden!")
        print(f"\nErstelle eine der Dateien:")
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
    
    # Lösche verarbeitete URLs aus der Datei
    print(f"\n🗑️ Räume {source_file.name} auf...")
    source_file.unlink()  # Datei löschen
    print(f"✅ {source_file.name} geleert")
    
    print("\nJetzt Auto-Sort laufen lassen:")
    print("  python scripts/auto-sort.py")

if __name__ == "__main__":
    main()
