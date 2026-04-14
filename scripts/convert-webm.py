#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebM to MP4 Converter
Konvertiert alle .webm Videos zu .mp4 (benötigt ffmpeg)
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SORTED_VIDEOS = BASE_DIR / "sorted" / "videos"
SORTED_GIFS = BASE_DIR / "sorted" / "gifs"

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

def find_webm_files():
    """Findet alle .webm Dateien"""
    webm_files = []
    
    # Check videos folder
    if SORTED_VIDEOS.exists():
        webm_files.extend(SORTED_VIDEOS.glob('*.webm'))
    
    # Check gifs folder (manche WebMs sind animiert)
    if SORTED_GIFS.exists():
        webm_files.extend(SORTED_GIFS.glob('*.webm'))
    
    return webm_files

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
    
    # Find WebM files
    webm_files = find_webm_files()
    
    if not webm_files:
        print("✅ Keine WebM-Dateien gefunden")
        return
    
    print(f"📦 Gefunden: {len(webm_files)} WebM-Dateien\n")
    
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
    for webm_file in webm_files:
        if convert_webm_to_mp4(webm_file, delete_original):
            success_count += 1
    
    print(f"\n📊 Fertig: {success_count}/{len(webm_files)} konvertiert")

if __name__ == "__main__":
    main()
