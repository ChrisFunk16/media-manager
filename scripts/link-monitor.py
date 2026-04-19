#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Link Monitor - Clipboard Überwachung
Erkennt automatisch kopierte URLs und fügt sie in links.txt ein
"""

import re
import time
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
LINKS_FILE = BASE_DIR / "links.txt"

# URL Pattern
URL_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+'
)

class ClipboardMonitor:
    def __init__(self):
        self.last_clipboard = ""
        self.saved_links = self._load_existing_links()
        
    def _load_existing_links(self):
        """Lädt bereits gespeicherte Links um Duplikate zu vermeiden"""
        if LINKS_FILE.exists():
            with open(LINKS_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip() and not line.startswith('#'))
        return set()
    
    def get_clipboard(self):
        """Holt aktuellen Clipboard-Inhalt (X11 PRIMARY + CLIPBOARD)"""
        try:
            # Versuche CLIPBOARD (Strg+C)
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            # Fallback: PRIMARY (Maus-Markierung)
            result = subprocess.run(
                ['xclip', '-selection', 'primary', '-o'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"❌ Clipboard-Fehler: {e}")
        
        return ""
    
    def extract_url(self, text):
        """Extrahiert URL aus Text"""
        match = URL_PATTERN.search(text)
        if match:
            return match.group(0)
        return None
    
    def save_link(self, url):
        """Speichert Link in Datei"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(LINKS_FILE, 'a') as f:
            f.write(f"{url}\n")
        
        self.saved_links.add(url)
        print(f"✅ [{timestamp}] Link gespeichert: {url}")
    
    def run(self):
        """Haupt-Loop"""
        print("🔍 Link Monitor gestartet")
        print(f"📝 Speichert in: {LINKS_FILE}")
        print(f"💾 Bereits {len(self.saved_links)} Links vorhanden")
        print("\n⌛ Überwache Zwischenablage... (Strg+C zum Beenden)\n")
        
        try:
            while True:
                clipboard = self.get_clipboard()
                
                # Nur wenn sich Clipboard geändert hat
                if clipboard and clipboard != self.last_clipboard:
                    self.last_clipboard = clipboard
                    
                    # Prüfe ob es eine URL ist
                    url = self.extract_url(clipboard)
                    
                    if url and url not in self.saved_links:
                        self.save_link(url)
                
                time.sleep(0.5)  # 500ms Polling
                
        except KeyboardInterrupt:
            print("\n\n👋 Link Monitor beendet")
            print(f"📊 Insgesamt {len(self.saved_links)} Links gespeichert")

if __name__ == "__main__":
    # Prüfe ob xclip installiert ist
    try:
        subprocess.run(['which', 'xclip'], capture_output=True, check=True)
    except:
        print("❌ xclip ist nicht installiert!")
        print("   Installiere mit: sudo apt install xclip")
        exit(1)
    
    monitor = ClipboardMonitor()
    monitor.run()
