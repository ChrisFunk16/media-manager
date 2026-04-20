#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Media Downloader
Lädt Bilder/Videos von verschiedenen Websites:
- Reddit (Posts, Subreddits, User)
- Rule34.xxx (Posts, Tags, Searches)
- HypnoTube (Videos, Users, Channels, Playlists)
- Instagram, Twitter, Imgur, etc. (100+ Sites)

Benötigt: gallery-dl (pip install gallery-dl)
Für HypnoTube: yt-dlp + plugin (auto-install)
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
from urllib.parse import urlparse

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

def is_hypnotube_url(url):
    """Prüft ob URL von HypnoTube ist"""
    parsed = urlparse(url)
    return 'hypnotube.com' in parsed.netloc.lower()

def check_gallery_dl():
    """Prüft ob gallery-dl installiert ist"""
    try:
        subprocess.run(['gallery-dl', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_ytdlp():
    """Prüft ob yt-dlp installiert ist"""
    try:
        subprocess.run(['yt-dlp', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_hypnotube_plugin():
    """Prüft ob HypnoTube Plugin installiert ist"""
    try:
        # Test mit yt-dlp ob Plugin funktioniert
        result = subprocess.run(
            ['yt-dlp', '--list-extractors'],
            capture_output=True,
            text=True,
            check=True
        )
        return 'hypnotube' in result.stdout.lower()
    except:
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

def install_ytdlp():
    """Installiert yt-dlp via pip"""
    print("📦 Installiere yt-dlp...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'],
                      check=True)
        print("✅ yt-dlp Installation erfolgreich")
        return True
    except subprocess.CalledProcessError:
        print("❌ yt-dlp Installation fehlgeschlagen")
        return False

def install_hypnotube_plugin():
    """Installiert HypnoTube Plugin für yt-dlp"""
    print("📦 Installiere HypnoTube Plugin + bs4...")
    try:
        # Install plugin + dependency
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-U',
            'https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin/archive/refs/heads/master.zip',
            'bs4'
        ], check=True)
        print("✅ HypnoTube Plugin Installation erfolgreich")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Plugin Installation fehlgeschlagen: {e}")
        return False

def download_with_gallery_dl(url, dest='incoming', subfolder=None):
    """
    Lädt Medien von URL via gallery-dl
    
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

def download_with_ytdlp(url, dest='incoming', subfolder=None):
    """
    Lädt Videos von HypnoTube via yt-dlp
    
    Args:
        url: HypnoTube URL (video/user/channel/playlist)
        dest: Zielordner (incoming/bulk/favorites/videos)
        subfolder: Optional subfolder name
    """
    # Bestimme Zielpfad (Videos!)
    if dest == 'bulk':
        target_dir = SORTED / "bulk"
    elif dest == 'favorites':
        target_dir = SORTED / "favorites"
    elif dest == 'images':
        # HypnoTube = Videos, nicht images
        target_dir = SORTED / "videos"
    else:
        target_dir = INCOMING
    
    # Subfolder hinzufügen wenn angegeben
    if subfolder:
        target_dir = target_dir / subfolder
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎬 Lade HypnoTube: {url}")
    print(f"📁 Ziel: {target_dir}")
    
    # yt-dlp Output-Template: filename only
    output_template = str(target_dir / "%(title)s-%(id)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '--add-headers', 'Referer: https://hypnotube.com',  # Für Thumbnails
        '-o', output_template,
        '--no-mtime',
        url
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Download abgeschlossen")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Download:\n{e.stderr}")
        return False
    
    return True

def download(url, dest='incoming', subfolder=None):
    """
    Smart Downloader - wählt automatisch das richtige Tool
    """
    if is_hypnotube_url(url):
        # HypnoTube → yt-dlp
        if not check_ytdlp():
            print("⚠️ yt-dlp nicht gefunden (benötigt für HypnoTube)")
            install = input("Installieren? (y/n): ")
            if install.lower() == 'y':
                if not install_ytdlp():
                    return False
            else:
                print("Abgebrochen")
                return False
        
        if not check_hypnotube_plugin():
            print("⚠️ HypnoTube Plugin nicht gefunden")
            install = input("Plugin + bs4 installieren? (y/n): ")
            if install.lower() == 'y':
                if not install_hypnotube_plugin():
                    return False
            else:
                print("Abgebrochen")
                return False
        
        return download_with_ytdlp(url, dest, subfolder)
    else:
        # Andere Sites → gallery-dl
        if not check_gallery_dl():
            print("⚠️ gallery-dl nicht gefunden")
            install = input("Installieren? (y/n): ")
            if install.lower() == 'y':
                if not install_gallery_dl():
                    return False
            else:
                print("Abgebrochen")
                return False
        
        return download_with_gallery_dl(url, dest, subfolder)

def main():
    parser = argparse.ArgumentParser(
        description='Universal Media Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Reddit
  media-downloader.py https://reddit.com/r/wallpapers
  
  # HypnoTube Video
  media-downloader.py https://hypnotube.com/video/shock-409.html
  
  # HypnoTube User (alle Videos)
  media-downloader.py https://hypnotube.com/user/ambersis-3082/
  
  # HypnoTube Channel
  media-downloader.py https://hypnotube.com/channels/38/hd/
  
  # HypnoTube Playlist
  media-downloader.py https://hypnotube.com/playlist/93707/stim-gooning/
  
  # Rule34 nach bulk/
  media-downloader.py --dest bulk --subfolder sissy_general 'https://rule34.xxx/...'
  
  # Favorites mit Preset-Name
  media-downloader.py --dest favorites --subfolder makeup_closeup 'https://...'
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
    
    download(args.url, dest=args.dest, subfolder=args.subfolder)

if __name__ == "__main__":
    main()
