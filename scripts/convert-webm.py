#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Converter (WebM/M4V → MP4)
Konvertiert .webm und .m4v Videos zu .mp4 (benötigt ffmpeg)
"""

import os
import sys
import subprocess
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
SORTED_GIFS = MEDIA_BASE / config['sorted'] / "gifs"
SORTED_HYPNO = MEDIA_BASE / config['sorted'] / "hypno"

def check_ffmpeg():
    """Prüft ob ffmpeg installiert ist"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_webm_to_mp4(webm_file, delete_original=True):
    """Konvertiert einzelne WebM zu MP4"""
    mp4_file = webm_file.with_suffix('.mp4')
    
    # Skip if MP4 already exists
    if mp4_file.exists():
        print(f"⚠️ Übersprungen (MP4 existiert): {webm_file.name}")
        
        # Lösche Original trotzdem wenn gewünscht (ist redundant!)
        if delete_original:
            webm_file.unlink()
            print(f"🗑️ Original gelöscht: {webm_file.name}")
        
        return False
    
    print(f"🔄 Konvertiere: {webm_file.name}")
    
    cmd = [
        'ffmpeg',
        '-i', str(webm_file),
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure even dimensions
        '-c:v', 'libx264',      # H.264 codec
        '-c:a', 'aac',          # AAC audio
        '-strict', 'experimental',
        '-b:a', '192k',         # Audio bitrate
        '-movflags', '+faststart',  # Web-optimized
        '-loglevel', 'error',   # Nur Fehler zeigen
        str(mp4_file)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Fertig: {mp4_file.name}")
        
        # Lösche Original wenn gewünscht
        if delete_original:
            webm_file.unlink()
            print(f"🗑️ Original gelöscht: {webm_file.name}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler bei {webm_file.name}: {e}")
        return False

def find_files_to_convert():
    """Findet alle .webm und .m4v Dateien"""
    files_to_convert = []
    
    # Check videos folder
    if SORTED_VIDEOS.exists():
        files_to_convert.extend(SORTED_VIDEOS.glob('*.webm'))
        files_to_convert.extend(SORTED_VIDEOS.glob('*.m4v'))
    
    # Check gifs folder (manche WebMs sind animiert)
    if SORTED_GIFS.exists():
        files_to_convert.extend(SORTED_GIFS.glob('*.webm'))
        files_to_convert.extend(SORTED_GIFS.glob('*.m4v'))
    
    # Check hypno folder
    if SORTED_HYPNO.exists():
        files_to_convert.extend(SORTED_HYPNO.glob('*.webm'))
        files_to_convert.extend(SORTED_HYPNO.glob('*.m4v'))
    
    return files_to_convert

def main():
    # Check ffmpeg
    if not check_ffmpeg():
        print("❌ ffmpeg nicht gefunden!")
        print("\nInstallation:")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  oder: winget install ffmpeg")
        print("\n  Linux: sudo apt install ffmpeg")
        print("  Mac: brew install ffmpeg")
        sys.exit(1)
    
    # Find files to convert
    files = find_files_to_convert()
    
    if not files:
        print("✅ Keine Dateien zum Konvertieren gefunden (WebM/M4V)")
        return
    
    print(f"📦 Gefunden: {len(files)} Dateien (WebM/M4V)\n")
    
    # Ask for confirmation
    print("Optionen:")
    print("  1 - Konvertieren + Original behalten")
    print("  2 - Konvertieren + Original löschen")
    print("  3 - Abbrechen")
    
    choice = input("\nAuswahl: ").strip()
    
    if choice == '3':
        print("Abgebrochen")
        return
    
    delete_original = (choice == '2')
    
    # Convert all
    success_count = 0
    for file in files:
        if convert_webm_to_mp4(file, delete_original):
            success_count += 1
    
    print(f"\n📊 Fertig: {success_count}/{len(files)} konvertiert")

if __name__ == "__main__":
    main()
