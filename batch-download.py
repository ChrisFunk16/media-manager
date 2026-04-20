#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Downloader - Download multiple URLs from a file
"""

import sys
import subprocess
import json
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent
SCRIPTS = BASE_DIR / "scripts"
CONFIG_FILE = BASE_DIR / "config.json"

# Helper-Funktionen für Setup-Checks
def is_hypnotube_url(url):
    """Prüft ob URL von HypnoTube ist"""
    parsed = urlparse(url)
    return 'hypnotube.com' in parsed.netloc.lower()

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
        result = subprocess.run(
            [sys.executable, '-c', 
             'import yt_dlp_plugins.extractor.hypnotube; print("OK")'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0 and 'OK' in result.stdout
    except:
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
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-U',
            'https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin/archive/refs/heads/master.zip',
            'bs4'
        ], check=True)
        print("✅ HypnoTube Plugin Installation erfolgreich")
        
        # Flag-File erstellen damit media-downloader.py nicht mehr fragt
        flag_file = BASE_DIR / ".hypnotube_plugin_installed"
        flag_file.touch()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Plugin Installation fehlgeschlagen: {e}")
        return False

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
    
    # PRE-CHECK: Dependencies prüfen
    has_hypnotube_urls = any(is_hypnotube_url(url) for url in urls)
    
    if has_hypnotube_urls:
        print("🔍 HypnoTube Links gefunden - prüfe Dependencies...\n")
        
        missing = []
        if not check_ytdlp():
            missing.append("yt-dlp")
        if not check_hypnotube_plugin():
            missing.append("HypnoTube Plugin")
        
        if missing:
            print(f"❌ Fehlende Dependencies: {', '.join(missing)}")
            print("\n🔧 Installation:")
            print("   pip install -r requirements.txt")
            print("\n   (installiert: gallery-dl, yt-dlp, HypnoTube Plugin, bs4)")
            sys.exit(1)
        
        print("✅ Alle Dependencies vorhanden!\n")
    
    # Download-Loop (jetzt ohne wiederholte Checks!)
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
