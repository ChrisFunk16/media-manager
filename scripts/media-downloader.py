#!/usr/bin/env python3
"""
Universal Media Downloader
Lädt Bilder/Videos von verschiedenen Websites:
- Reddit (Posts, Subreddits, User)
- Rule34.xxx (Posts, Tags, Searches)
- Instagram, Twitter, Imgur, etc. (100+ Sites)

Benötigt: gallery-dl (pip install gallery-dl)
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INCOMING = BASE_DIR / "incoming"

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

def download(url):
    """Lädt Medien von URL"""
    INCOMING.mkdir(parents=True, exist_ok=True)
    
    print(f"⬇️ Lade: {url}")
    
    cmd = [
        'gallery-dl',
        '--dest', str(INCOMING),
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
    if len(sys.argv) < 2:
        print("Usage: media-downloader.py <URL>")
        print("\nBeispiele:")
        print("  # Reddit")
        print("  media-downloader.py https://reddit.com/r/pics/comments/...")
        print("  media-downloader.py https://reddit.com/r/wallpapers")
        print("\n  # Rule34.xxx")
        print("  media-downloader.py https://rule34.xxx/index.php?page=post&s=view&id=12345")
        print("  media-downloader.py 'https://rule34.xxx/index.php?page=post&s=list&tags=tag_name'")
        print("\n  # Redgifs")
        print("  media-downloader.py https://redgifs.com/watch/uniquegifid")
        print("  media-downloader.py https://redgifs.com/users/username")
        print("\n  # Andere (Instagram, Twitter, Imgur, Gelbooru, etc.)")
        print("  media-downloader.py <URL>")
        sys.exit(1)
    
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
    
    url = sys.argv[1]
    download(url)

if __name__ == "__main__":
    main()
