#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Manager - Interaktive CLI
Alles an einem Ort: Download, Sortieren, Browse
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Config laden
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """Lädt Config und setzt Pfade"""
    default_config = {
        "media_base_dir": None,
        "incoming": "incoming",
        "sorted": "sorted"
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Merge mit defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            return config
        except:
            pass
    
    return default_config

# Config laden und Pfade setzen
config = load_config()

# Base dir: custom oder script dir
if config['media_base_dir']:
    MEDIA_BASE = Path(config['media_base_dir']).expanduser()
else:
    MEDIA_BASE = BASE_DIR

INCOMING = MEDIA_BASE / config['incoming']
SORTED = MEDIA_BASE / config['sorted']
SCRIPTS = BASE_DIR / "scripts"  # Scripts bleiben IMMER im Original-Ordner
PRESETS_FILE = MEDIA_BASE / "tag-presets.json"

# Farben für Terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def load_presets():
    """Lädt Tag-Presets aus JSON"""
    if not PRESETS_FILE.exists():
        return {"presets": {}, "mixes": {}}
    try:
        with open(PRESETS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"presets": {}, "mixes": {}}

def save_presets(data):
    """Speichert Tag-Presets"""
    with open(PRESETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def resolve_tags(preset_name, data):
    """Löst Preset-Name in Tags auf (rekursiv für Mixes)"""
    # Check presets
    if preset_name in data['presets']:
        return data['presets'][preset_name]
    
    # Check mixes
    if preset_name in data['mixes']:
        tags = []
        for item in data['mixes'][preset_name]:
            if item in data['presets']:
                tags.extend(data['presets'][item])
            else:
                tags.append(item)  # Direct tag
        return tags
    
    return None

def print_header():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════╗")
    print("║      📦 MEDIA MANAGER v1.0           ║")
    print("╚═══════════════════════════════════════╝")
    print(f"{Colors.END}")

def print_menu():
    print(f"\n{Colors.BOLD}Hauptmenü:{Colors.END}")
    print(f"  {Colors.GREEN}1{Colors.END} - Download (Reddit)")
    print(f"  {Colors.GREEN}2{Colors.END} - Download (Rule34.xxx)")
    print(f"  {Colors.GREEN}3{Colors.END} - Download (Redgifs)")
    print(f"  {Colors.GREEN}4{Colors.END} - Download (Twitter/X)")
    print(f"  {Colors.GREEN}5{Colors.END} - Download (Custom URL)")
    print(f"  {Colors.GREEN}b{Colors.END} - Batch Download (urls.txt/links.txt)")
    print(f"  {Colors.BLUE}a{Colors.END} - 🚀 Alles (Download → Sort → Convert)")
    print(f"  {Colors.GREEN}6{Colors.END} - Auto-Sort (incoming → sorted)")
    print(f"  {Colors.GREEN}7{Colors.END} - WebM → MP4 konvertieren")
    print(f"  {Colors.GREEN}8{Colors.END} - Browse Sorted Files")
    print(f"  {Colors.GREEN}9{Colors.END} - Stats anzeigen")
    print(f"  {Colors.YELLOW}l{Colors.END} - Link Monitor starten")
    print(f"  {Colors.YELLOW}0{Colors.END} - Tag-Presets verwalten")
    print(f"  {Colors.RED}q{Colors.END} - Quit")
    print()

def download(url):
    """Führt media-downloader.py aus"""
    print(f"\n{Colors.YELLOW}⬇️ Starte Download...{Colors.END}")
    cmd = [sys.executable, str(SCRIPTS / "media-downloader.py"), url]
    subprocess.run(cmd)
    input(f"\n{Colors.BLUE}Enter drücken um fortzufahren...{Colors.END}")

def download_reddit():
    clear()
    print_header()
    print(f"{Colors.BOLD}Reddit Download{Colors.END}\n")
    print("Beispiele:")
    print("  https://reddit.com/r/wallpapers")
    print("  https://reddit.com/r/pics/comments/xyz123/")
    print("  https://reddit.com/user/username")
    print()
    
    url = input(f"{Colors.GREEN}URL eingeben:{Colors.END} ").strip()
    if url:
        download(url)

def download_rule34():
    clear()
    print_header()
    print(f"{Colors.BOLD}Rule34.xxx Download{Colors.END}\n")
    print("Optionen:")
    print("  1 - Post ID eingeben")
    print("  2 - Tag-Suche (manuell)")
    print("  3 - From Preset")
    print("  4 - Mix Presets")
    print("  5 - Custom URL")
    print()
    
    choice = input(f"{Colors.GREEN}Auswahl:{Colors.END} ").strip()
    
    if choice == "1":
        post_id = input(f"{Colors.GREEN}Post ID:{Colors.END} ").strip()
        url = f"https://rule34.xxx/index.php?page=post&s=view&id={post_id}"
        download(url)
    elif choice == "2":
        tags = input(f"{Colors.GREEN}Tags (Leerzeichen-getrennt):{Colors.END} ").strip()
        tags_formatted = tags.replace(' ', '+')
        url = f"https://rule34.xxx/index.php?page=post&s=list&tags={tags_formatted}"
        download(url)
    elif choice == "3":
        # From Preset
        data = load_presets()
        if not data['presets']:
            print(f"{Colors.RED}❌ Keine Presets vorhanden!{Colors.END}")
            print(f"{Colors.YELLOW}Erst Presets erstellen (Option 8 im Hauptmenü){Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Verfügbare Presets:{Colors.END}")
        for name, tags in data['presets'].items():
            tags_str = ', '.join(tags)
            print(f"  {Colors.GREEN}{name}{Colors.END}: {tags_str}")
        
        preset_name = input(f"\n{Colors.GREEN}Preset:{Colors.END} ").strip()
        tags_list = resolve_tags(preset_name, data)
        
        if tags_list:
            tags_formatted = '+'.join(tags_list)
            url = f"https://rule34.xxx/index.php?page=post&s=list&tags={tags_formatted}"
            print(f"{Colors.BLUE}Tags: {' '.join(tags_list)}{Colors.END}")
            download(url)
        else:
            print(f"{Colors.RED}❌ Preset nicht gefunden{Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
    
    elif choice == "4":
        # Mix Presets
        data = load_presets()
        if not data['presets']:
            print(f"{Colors.RED}❌ Keine Presets vorhanden!{Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Verfügbare Presets:{Colors.END}")
        for name, tags in data['presets'].items():
            tags_str = ', '.join(tags)
            print(f"  {Colors.GREEN}{name}{Colors.END}: {tags_str}")
        
        print(f"\n{Colors.YELLOW}Mehrere Presets/Tags kombinieren (Leerzeichen-getrennt){Colors.END}")
        mix_input = input(f"{Colors.GREEN}Presets/Tags:{Colors.END} ").strip().split()
        
        all_tags = []
        for item in mix_input:
            resolved = resolve_tags(item, data)
            if resolved:
                all_tags.extend(resolved)
            else:
                all_tags.append(item)  # Direkter Tag
        
        if all_tags:
            tags_formatted = '+'.join(all_tags)
            url = f"https://rule34.xxx/index.php?page=post&s=list&tags={tags_formatted}"
            print(f"{Colors.BLUE}Tags: {' '.join(all_tags)}{Colors.END}")
            download(url)
        else:
            print(f"{Colors.RED}❌ Keine gültigen Tags{Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
    
    elif choice == "5":
        url = input(f"{Colors.GREEN}URL:{Colors.END} ").strip()
        if url:
            download(url)

def download_redgifs():
    clear()
    print_header()
    print(f"{Colors.BOLD}Redgifs Download{Colors.END}\n")
    print("Optionen:")
    print("  1 - Einzelnes GIF (ID eingeben)")
    print("  2 - User/Creator")
    print("  3 - Search/Tags")
    print("  4 - Custom URL")
    print()
    
    choice = input(f"{Colors.GREEN}Auswahl:{Colors.END} ").strip()
    
    if choice == "1":
        gif_id = input(f"{Colors.GREEN}GIF ID:{Colors.END} ").strip()
        url = f"https://redgifs.com/watch/{gif_id}"
        download(url)
    elif choice == "2":
        username = input(f"{Colors.GREEN}Username:{Colors.END} ").strip()
        url = f"https://redgifs.com/users/{username}"
        download(url)
    elif choice == "3":
        query = input(f"{Colors.GREEN}Search Query:{Colors.END} ").strip()
        url = f"https://redgifs.com/gifs/search?query={query}"
        download(url)
    elif choice == "4":
        url = input(f"{Colors.GREEN}URL:{Colors.END} ").strip()
        if url:
            download(url)

def download_twitter():
    clear()
    print_header()
    print(f"{Colors.BOLD}Twitter/X Download{Colors.END}\n")
    print("Optionen:")
    print("  1 - Einzelner Tweet")
    print("  2 - User Timeline")
    print("  3 - User Media (nur Bilder/Videos)")
    print("  4 - User Likes")
    print("  5 - Custom URL")
    print()
    
    choice = input(f"{Colors.GREEN}Auswahl:{Colors.END} ").strip()
    
    if choice == "1":
        tweet_url = input(f"{Colors.GREEN}Tweet URL:{Colors.END} ").strip()
        if tweet_url:
            download(tweet_url)
    elif choice == "2":
        username = input(f"{Colors.GREEN}Username (ohne @):{Colors.END} ").strip()
        url = f"https://twitter.com/{username}"
        download(url)
    elif choice == "3":
        username = input(f"{Colors.GREEN}Username (ohne @):{Colors.END} ").strip()
        url = f"https://twitter.com/{username}/media"
        download(url)
    elif choice == "4":
        username = input(f"{Colors.GREEN}Username (ohne @):{Colors.END} ").strip()
        url = f"https://twitter.com/{username}/likes"
        download(url)
    elif choice == "5":
        url = input(f"{Colors.GREEN}URL:{Colors.END} ").strip()
        if url:
            download(url)

def download_custom():
    clear()
    print_header()
    print(f"{Colors.BOLD}Custom URL Download{Colors.END}\n")
    print("Unterstützt: Instagram, Imgur, DeviantArt, Gelbooru, Pixiv, etc.")
    print()
    
    url = input(f"{Colors.GREEN}URL eingeben:{Colors.END} ").strip()
    if url:
        download(url)

def auto_sort():
    clear()
    print_header()
    print(f"{Colors.BOLD}Auto-Sort{Colors.END}\n")
    
    # Count files first
    if not INCOMING.exists():
        print(f"{Colors.RED}❌ incoming/ Ordner nicht gefunden{Colors.END}")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    # Rekursiv suchen (wie auto-sort.py es macht!)
    files = []
    for root, dirs, filenames in os.walk(INCOMING):
        for filename in filenames:
            files.append(Path(root) / filename)
    
    if not files:
        print(f"{Colors.YELLOW}ℹ️ Keine Files zum Sortieren{Colors.END}")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    print(f"Gefunden: {len(files)} Files in incoming/\n")
    confirm = input(f"{Colors.GREEN}Sortieren? (y/n):{Colors.END} ").strip().lower()
    
    if confirm == 'y':
        cmd = [sys.executable, str(SCRIPTS / "auto-sort.py")]
        subprocess.run(cmd)
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")

def convert_webm():
    clear()
    print_header()
    print(f"{Colors.BOLD}WebM → MP4 Converter{Colors.END}\n")
    
    cmd = [sys.executable, str(SCRIPTS / "convert-webm.py")]
    subprocess.run(cmd)
    input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")

def browse_sorted():
    clear()
    print_header()
    print(f"{Colors.BOLD}Sorted Files{Colors.END}\n")
    
    categories = ['images', 'gifs', 'videos', 'hypno']
    
    for cat in categories:
        cat_path = SORTED / cat
        if cat_path.exists():
            files = list(cat_path.glob('*'))
            file_count = len([f for f in files if f.is_file()])
            print(f"  {Colors.GREEN}{cat:10s}{Colors.END}: {file_count} files")
        else:
            print(f"  {Colors.YELLOW}{cat:10s}{Colors.END}: Ordner nicht gefunden")
    
    print(f"\n{Colors.BLUE}Pfad: {SORTED}{Colors.END}")
    input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")

def show_stats():
    clear()
    print_header()
    print(f"{Colors.BOLD}Statistiken{Colors.END}\n")
    
    # Incoming (rekursiv!)
    incoming_count = 0
    if INCOMING.exists():
        for root, dirs, filenames in os.walk(INCOMING):
            incoming_count += len(filenames)
    
    # Sorted
    stats = {}
    for cat in ['images', 'gifs', 'videos', 'hypno']:
        cat_path = SORTED / cat
        if cat_path.exists():
            stats[cat] = len([f for f in cat_path.glob('*') if f.is_file()])
        else:
            stats[cat] = 0
    
    total_sorted = sum(stats.values())
    
    print(f"📥 Incoming:       {incoming_count} files")
    print(f"📊 Sorted (total): {total_sorted} files")
    print(f"   ├─ Images:      {stats['images']}")
    print(f"   ├─ GIFs:        {stats['gifs']}")
    print(f"   ├─ Videos:      {stats['videos']}")
    print(f"   └─ Hypno:       {stats['hypno']}")
    
    input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")

def batch_download():
    """Batch Download aus urls.txt oder links.txt"""
    clear()
    print_header()
    print(f"{Colors.BOLD}Batch Download{Colors.END}\n")
    
    urls_file = BASE_DIR / "urls.txt"
    links_file = BASE_DIR / "links.txt"
    
    # Check welche Datei existiert (links.txt bevorzugt)
    source_file = None
    if links_file.exists():
        source_file = links_file
    elif urls_file.exists():
        source_file = urls_file
    
    if not source_file:
        print(f"{Colors.RED}❌ Keine URLs gefunden!{Colors.END}\n")
        print("Erstelle eine der Dateien:")
        print(f"  • {urls_file.name} (manuell erstellt)")
        print(f"  • {links_file.name} (via Link Monitor)")
        print("\nFormat: Eine URL pro Zeile")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    # URLs laden
    with open(source_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print(f"{Colors.RED}❌ Keine URLs in {source_file.name}{Colors.END}")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    print(f"📥 Quelle: {source_file.name}")
    print(f"📊 URLs gefunden: {len(urls)}\n")
    
    # Preview erste 5 URLs
    print(f"{Colors.BOLD}Vorschau:{Colors.END}")
    for i, url in enumerate(urls[:5], 1):
        print(f"  {i}. {url[:60]}...")
    if len(urls) > 5:
        print(f"  ... und {len(urls) - 5} weitere")
    
    print()
    print(f"{Colors.YELLOW}ℹ️ Nach dem Download wird {source_file.name} geleert{Colors.END}")
    print()
    confirm = input(f"{Colors.GREEN}Alle herunterladen? (y/n):{Colors.END} ").strip().lower()
    
    if confirm == 'y':
        cmd = [sys.executable, str(BASE_DIR / "batch-download.py")]
        subprocess.run(cmd)
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")

def all_in_one():
    """Download → Sort → Convert - kompletter Workflow"""
    clear()
    print_header()
    print(f"{Colors.BOLD}🚀 Kompletter Workflow{Colors.END}\n")
    print(f"{Colors.BLUE}Schritte:{Colors.END}")
    print("  1️⃣  Batch Download (links.txt/urls.txt)")
    print("  2️⃣  Auto-Sort (incoming → sorted)")
    print("  3️⃣  WebM → MP4 Konvertierung")
    print()
    
    # Check ob URLs vorhanden
    urls_file = BASE_DIR / "urls.txt"
    links_file = BASE_DIR / "links.txt"
    
    source_file = None
    if links_file.exists():
        source_file = links_file
    elif urls_file.exists():
        source_file = urls_file
    
    if not source_file:
        print(f"{Colors.RED}❌ Keine URLs gefunden!{Colors.END}")
        print("\nErstelle erst URLs:")
        print(f"  • Link Monitor starten ({Colors.YELLOW}l{Colors.END})")
        print(f"  • Oder manuell urls.txt erstellen")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    # URLs preview
    with open(source_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print(f"{Colors.RED}❌ {source_file.name} ist leer{Colors.END}")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    print(f"{Colors.GREEN}📥 {len(urls)} URLs in {source_file.name}{Colors.END}")
    print()
    confirm = input(f"{Colors.GREEN}Workflow starten? (y/n):{Colors.END} ").strip().lower()
    
    if confirm != 'y':
        return
    
    # Step 1: Batch Download
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}1️⃣  BATCH DOWNLOAD{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    cmd = [sys.executable, str(BASE_DIR / "batch-download.py")]
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n{Colors.RED}❌ Batch Download fehlgeschlagen{Colors.END}")
        input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        return
    
    # Step 2: Auto-Sort
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}2️⃣  AUTO-SORT{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    cmd = [sys.executable, str(SCRIPTS / "auto-sort.py")]
    subprocess.run(cmd)
    
    # Step 3: WebM Conversion
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}3️⃣  WEBM → MP4 KONVERTIERUNG{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    cmd = [sys.executable, str(SCRIPTS / "convert-webm.py")]
    subprocess.run(cmd)
    
    # Fertig
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ WORKFLOW ABGESCHLOSSEN{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    input(f"{Colors.BLUE}Enter drücken...{Colors.END}")

def start_link_monitor():
    """Startet Link Monitor"""
    clear()
    print_header()
    print(f"{Colors.BOLD}Link Monitor{Colors.END}\n")
    print("Überwacht deine Zwischenablage und speichert automatisch kopierte Links.")
    print(f"Ziel: {BASE_DIR / 'links.txt'}\n")
    print(f"{Colors.YELLOW}ℹ️ Läuft im Vordergrund - neues Terminal für andere Aufgaben öffnen{Colors.END}")
    print(f"{Colors.YELLOW}ℹ️ Beenden mit Strg+C{Colors.END}\n")
    
    input(f"{Colors.GREEN}Enter drücken zum Starten...{Colors.END}")
    
    cmd = [sys.executable, str(SCRIPTS / "link-monitor.py")]
    subprocess.run(cmd)
    
    print()
    input(f"{Colors.BLUE}Enter drücken um fortzufahren...{Colors.END}")

def manage_tag_presets():
    """Tag-Preset Management"""
    while True:
        clear()
        print_header()
        print(f"{Colors.BOLD}Tag-Preset Management{Colors.END}\n")
        
        data = load_presets()
        
        # Show existing
        if data['presets']:
            print(f"{Colors.BOLD}Presets:{Colors.END}")
            for name, tags in data['presets'].items():
                tags_str = ', '.join(tags)
                print(f"  {Colors.GREEN}{name}{Colors.END}: {tags_str}")
        else:
            print(f"{Colors.YELLOW}Keine Presets vorhanden{Colors.END}")
        
        print(f"\n{Colors.BOLD}Optionen:{Colors.END}")
        print(f"  {Colors.GREEN}1{Colors.END} - Preset hinzufügen")
        print(f"  {Colors.GREEN}2{Colors.END} - Preset löschen")
        print(f"  {Colors.GREEN}3{Colors.END} - Preset bearbeiten")
        print(f"  {Colors.RED}b{Colors.END} - Zurück")
        print()
        
        choice = input(f"{Colors.GREEN}Auswahl:{Colors.END} ").strip().lower()
        
        if choice == '1':
            # Add
            print()
            name = input(f"{Colors.GREEN}Preset-Name:{Colors.END} ").strip()
            if not name:
                continue
            
            tags_input = input(f"{Colors.GREEN}Tags (Leerzeichen-getrennt):{Colors.END} ").strip()
            tags = [t.strip() for t in tags_input.split() if t.strip()]
            
            if tags:
                data['presets'][name] = tags
                save_presets(data)
                print(f"{Colors.BLUE}✅ Preset '{name}' gespeichert{Colors.END}")
                input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        
        elif choice == '2':
            # Delete
            if not data['presets']:
                print(f"{Colors.RED}Keine Presets zum Löschen{Colors.END}")
                input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
                continue
            
            print()
            name = input(f"{Colors.GREEN}Preset zum Löschen:{Colors.END} ").strip()
            if name in data['presets']:
                del data['presets'][name]
                save_presets(data)
                print(f"{Colors.BLUE}✅ Preset '{name}' gelöscht{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Preset nicht gefunden{Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        
        elif choice == '3':
            # Edit
            if not data['presets']:
                print(f"{Colors.RED}Keine Presets zum Bearbeiten{Colors.END}")
                input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
                continue
            
            print()
            name = input(f"{Colors.GREEN}Preset zum Bearbeiten:{Colors.END} ").strip()
            if name in data['presets']:
                current = ', '.join(data['presets'][name])
                print(f"{Colors.YELLOW}Aktuell: {current}{Colors.END}")
                
                tags_input = input(f"{Colors.GREEN}Neue Tags (Leerzeichen-getrennt):{Colors.END} ").strip()
                tags = [t.strip() for t in tags_input.split() if t.strip()]
                
                if tags:
                    data['presets'][name] = tags
                    save_presets(data)
                    print(f"{Colors.BLUE}✅ Preset '{name}' aktualisiert{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Preset nicht gefunden{Colors.END}")
            input(f"\n{Colors.BLUE}Enter drücken...{Colors.END}")
        
        elif choice == 'b':
            break

def main():
    while True:
        clear()
        print_header()
        print_menu()
        
        choice = input(f"{Colors.GREEN}Auswahl:{Colors.END} ").strip().lower()
        
        if choice == '1':
            download_reddit()
        elif choice == '2':
            download_rule34()
        elif choice == '3':
            download_redgifs()
        elif choice == '4':
            download_twitter()
        elif choice == '5':
            download_custom()
        elif choice == 'b':
            batch_download()
        elif choice == 'a':
            all_in_one()
        elif choice == '6':
            auto_sort()
        elif choice == '7':
            convert_webm()
        elif choice == '8':
            browse_sorted()
        elif choice == '9':
            show_stats()
        elif choice == 'l':
            start_link_monitor()
        elif choice == '0':
            manage_tag_presets()
        elif choice == 'q':
            print(f"\n{Colors.YELLOW}Bye!{Colors.END}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}Ungültige Auswahl{Colors.END}")
            input(f"{Colors.BLUE}Enter drücken...{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Abgebrochen.{Colors.END}")
        sys.exit(0)
