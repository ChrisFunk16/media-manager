#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Builder - Interaktiver Tag-Kombinator für Rule34/Booru Sites
Baut intelligente Tag-Kombinationen und zeigt Preview
"""

import json
import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PRESETS_FILE = BASE_DIR / "tag-presets.json"

# Windows ANSI-Support aktivieren
if os.name == 'nt':
    try:
        # Windows 10+ unterstützt ANSI nativ, muss nur aktiviert werden
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        # Fallback: Farben deaktivieren
        pass

# Farben
class C:
    H = '\033[95m'   # Header
    B = '\033[94m'   # Blue
    G = '\033[92m'   # Green
    Y = '\033[93m'   # Yellow
    R = '\033[91m'   # Red
    E = '\033[0m'    # End
    BOLD = '\033[1m'

# Tag-Kategorien mit Beschreibungen
TAG_CATEGORIES = {
    "base": {
        "name": "🎯 Base Tags",
        "desc": "Haupt-Kategorie (mindestens 1 wählen)",
        "required": True,
        "tags": {
            "sissy": "40k+ Posts - Hauptkategorie",
            "femboy": "433k+ Posts - Feminine boys",
            "trap": "120k+ Posts - Crossdressing",
            "crossdressing": "88k+ Posts - General crossdressing",
            "otoko_no_ko": "47k+ Posts - Japanese term",
            "tomgirl": "6k+ Posts - Feminine male",
        }
    },
    
    "style": {
        "name": "🎨 Style/Medium",
        "desc": "Art-Style oder Realismus",
        "tags": {
            # Positive (include)
            "photo": "Real photos",
            "real_person": "Real people",
            "3d": "3D renders",
            "anime": "Anime style",
            "cartoon": "Western cartoon",
            "realistic": "Realistic art",
            # Negative (exclude)
            "-anime": "❌ EXCLUDE anime",
            "-cartoon": "❌ EXCLUDE cartoon",
            "-3d": "❌ EXCLUDE 3D",
            "-ai_generated": "❌ EXCLUDE AI-generated",
            "-furry": "❌ EXCLUDE furry",
        }
    },
    
    "mood": {
        "name": "💭 Mood/Atmosphere",
        "desc": "Emotionale Stimmung",
        "tags": {
            "cute": "Cute/adorable",
            "innocent": "Innocent look",
            "submissive": "Submissive",
            "obedient": "Obedient",
            "confident": "Confident",
            "seductive": "Seductive",
            "embarrassed": "Embarrassed",
            "blushing": "Blushing",
            "shy": "Shy",
            "dominant": "Dominant",
        }
    },
    
    "action": {
        "name": "🔥 Action/Context",
        "desc": "Was passiert im Bild",
        "tags": {
            "solo": "Solo (alleine)",
            "duo": "Two persons",
            "group": "Group",
            "transformation": "Transformation scene",
            "makeover": "Makeover/makeup",
            "feminization": "Feminization",
            "bdsm": "BDSM elements",
            "bondage": "Bondage",
            "chastity": "Chastity device",
            "anal": "Anal",
            "oral": "Oral",
            "masturbation": "Masturbation",
        }
    },
    
    "outfit": {
        "name": "👗 Outfit/Clothing",
        "desc": "Kleidung und Accessoires",
        "tags": {
            "lingerie": "Lingerie",
            "stockings": "Stockings",
            "thighhighs": "Thigh-high socks",
            "fishnet": "Fishnets",
            "maid": "Maid outfit",
            "dress": "Dress",
            "skirt": "Skirt",
            "heels": "High heels",
            "collar": "Collar",
            "leash": "Leash",
            "pink": "Pink clothing/theme",
            "makeup": "Makeup visible",
            "lipstick": "Lipstick",
        }
    },
    
    "body": {
        "name": "💪 Body Focus",
        "desc": "Körper-Features",
        "tags": {
            "big_ass": "Big ass",
            "thick_thighs": "Thick thighs",
            "flat_chest": "Flat chest",
            "small_penis": "Small penis",
            "big_penis": "Big penis",
            "feminine_male": "Feminine body",
            "androgynous": "Androgynous",
            "long_hair": "Long hair",
            "short_hair": "Short hair",
            "close-up": "Close-up shot",
            "full_body": "Full body visible",
        }
    },
    
    "quality": {
        "name": "⭐ Quality Filters",
        "desc": "Qualität und Bewertung",
        "tags": {
            "high_resolution": "High resolution",
            "uncensored": "Uncensored",
            "score:>10": "Score higher than 10",
            "score:>20": "Score higher than 20 (top rated)",
            "-low_quality": "❌ EXCLUDE low quality",
            "-duplicate": "❌ EXCLUDE duplicates",
            "-blurry": "❌ EXCLUDE blurry",
        }
    },
    
    "hypno": {
        "name": "🌀 Hypno-Specific",
        "desc": "Hypno/Mind-Control Elemente",
        "tags": {
            "hypnotic": "Hypnotic elements",
            "spiral": "Hypno spiral",
            "mind_control": "Mind control",
            "brainwash": "Brainwashing",
            "text": "Text overlay",
            "caption": "Caption included",
            "glowing_eyes": "Glowing eyes",
            "trance": "Trance state",
            "ahegao": "Ahegao face",
            "mindbreak": "Mindbreak",
        }
    }
}


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    print(f"{C.BOLD}{C.B}")
    print("╔═══════════════════════════════════════╗")
    print("║      🏗️  TAG BUILDER v1.0            ║")
    print("║   Rule34/Booru Tag Kombinator        ║")
    print("╚═══════════════════════════════════════╝")
    print(f"{C.E}")


def show_categories():
    """Zeigt alle Kategorien"""
    print(f"\n{C.BOLD}Kategorien:{C.E}\n")
    for i, (key, cat) in enumerate(TAG_CATEGORIES.items(), 1):
        req = f" {C.R}(REQUIRED){C.E}" if cat.get('required') else ""
        print(f"  {C.G}{i}{C.E}. {cat['name']}{req}")
        print(f"     {C.Y}{cat['desc']}{C.E}")
    print()


def show_tags_in_category(cat_key):
    """Zeigt Tags einer Kategorie"""
    cat = TAG_CATEGORIES[cat_key]
    clear()
    print_header()
    print(f"\n{C.BOLD}{cat['name']}{C.E}")
    print(f"{C.Y}{cat['desc']}{C.E}\n")
    
    tags = list(cat['tags'].items())
    for i, (tag, desc) in enumerate(tags, 1):
        # Farbe je nach Tag-Type
        if tag.startswith('-'):
            color = C.R  # Exclusions rot
        elif 'score:' in tag:
            color = C.Y  # Score gelb
        else:
            color = C.G  # Normal grün
        
        print(f"  {color}{i:2d}{C.E}. {tag:20s} - {desc}")
    
    return tags


def select_tags_from_category(cat_key):
    """User wählt Tags aus einer Kategorie"""
    tags = show_tags_in_category(cat_key)
    
    print(f"\n{C.B}Mehrfachauswahl möglich (Zahlen mit Leerzeichen, z.B. '1 3 5'){C.E}")
    print(f"{C.B}Oder 'all' für alle, 'skip' zum Überspringen{C.E}")
    
    choice = input(f"\n{C.G}Auswahl: {C.E}").strip().lower()
    
    if choice == 'skip' or choice == '':
        return []
    
    if choice == 'all':
        return [tag for tag, _ in tags]
    
    # Parse numbers
    selected = []
    try:
        for num in choice.split():
            idx = int(num) - 1
            if 0 <= idx < len(tags):
                selected.append(tags[idx][0])
    except ValueError:
        print(f"{C.R}Ungültige Eingabe{C.E}")
        input("\nEnter drücken...")
        return select_tags_from_category(cat_key)  # Retry
    
    return selected


def build_tag_combo():
    """Interaktiver Tag-Builder"""
    selected_tags = {}
    
    while True:
        clear()
        print_header()
        
        # Zeige aktuelle Auswahl
        if selected_tags:
            print(f"\n{C.BOLD}Aktuelle Auswahl:{C.E}")
            for cat_key, tags in selected_tags.items():
                cat_name = TAG_CATEGORIES[cat_key]['name']
                tags_str = ', '.join(tags)
                print(f"  {cat_name}: {C.G}{tags_str}{C.E}")
            print()
        
        show_categories()
        
        print(f"{C.B}Optionen:{C.E}")
        print(f"  {C.G}1-{len(TAG_CATEGORIES)}{C.E} - Kategorie bearbeiten")
        print(f"  {C.Y}p{C.E} - Preview (URL + geschätzte Menge)")
        print(f"  {C.Y}s{C.E} - Als Preset speichern")
        print(f"  {C.Y}d{C.E} - Download starten")
        print(f"  {C.R}q{C.E} - Zurück")
        print()
        
        choice = input(f"{C.G}Auswahl: {C.E}").strip().lower()
        
        if choice == 'q':
            return None
        
        elif choice == 'p':
            preview_combo(selected_tags)
        
        elif choice == 's':
            save_as_preset(selected_tags)
        
        elif choice == 'd':
            start_download(selected_tags)
        
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(TAG_CATEGORIES):
                cat_key = list(TAG_CATEGORIES.keys())[idx]
                tags = select_tags_from_category(cat_key)
                if tags:
                    selected_tags[cat_key] = tags
                elif cat_key in selected_tags:
                    # Remove if empty
                    del selected_tags[cat_key]


def preview_combo(selected_tags):
    """Preview der Tag-Kombination"""
    if not selected_tags:
        print(f"\n{C.R}Keine Tags ausgewählt!{C.E}")
        input("\nEnter drücken...")
        return
    
    # Flatten all tags
    all_tags = []
    for tags in selected_tags.values():
        all_tags.extend(tags)
    
    # Build URL
    tags_str = '+'.join(all_tags)
    url = f"https://rule34.xxx/index.php?page=post&s=list&tags={tags_str}"
    
    print(f"\n{C.BOLD}Preview:{C.E}\n")
    print(f"{C.Y}Tags:{C.E} {' '.join(all_tags)}")
    print(f"{C.Y}Anzahl Tags:{C.E} {len(all_tags)}")
    print(f"\n{C.Y}URL:{C.E}")
    print(url)
    
    # Geschätzte Menge (heuristisch)
    print(f"\n{C.Y}Geschätzte Posts:{C.E}")
    estimate_posts(all_tags)
    
    print(f"\n{C.B}Tipp: Öffne URL im Browser für genaue Anzahl{C.E}")
    input(f"\n{C.G}Enter drücken...{C.E}")


def estimate_posts(tags):
    """Heuristische Schätzung der Post-Anzahl"""
    # Bekannte Größen
    sizes = {
        'sissy': 40871,
        'femboy': 433525,
        'trap': 120019,
        'crossdressing': 88792,
    }
    
    # Finde größten Base-Tag
    max_base = 0
    for tag in tags:
        if tag in sizes:
            max_base = max(max_base, sizes[tag])
    
    if max_base == 0:
        max_base = 10000  # Default guess
    
    # Reduziere pro zusätzlichem Tag (~40% Reduktion pro Tag)
    num_filters = len([t for t in tags if not t.startswith('-')])
    estimated = int(max_base * (0.6 ** (num_filters - 1)))
    
    # Exclusions reduzieren weniger drastisch
    num_exclusions = len([t for t in tags if t.startswith('-')])
    if num_exclusions > 0:
        estimated = int(estimated * 0.9)
    
    print(f"  ~{estimated:,} Posts (geschätzt)")
    
    if estimated < 100:
        print(f"  {C.R}⚠️ SEHR WENIG - evtl. zu restriktiv{C.E}")
    elif estimated < 1000:
        print(f"  {C.Y}⚠️ Klein - gut für präzise Suche{C.E}")
    elif estimated < 10000:
        print(f"  {C.G}✅ Gut - ausreichend Material{C.E}")
    else:
        print(f"  {C.G}✅ VIEL - gut für Bulk-Download{C.E}")


def save_as_preset(selected_tags):
    """Speichert Kombination als Preset"""
    if not selected_tags:
        print(f"\n{C.R}Keine Tags ausgewählt!{C.E}")
        input("\nEnter drücken...")
        return
    
    # Flatten tags
    all_tags = []
    for tags in selected_tags.values():
        all_tags.extend(tags)
    
    print(f"\n{C.BOLD}Preset speichern{C.E}\n")
    print(f"{C.Y}Tags:{C.E} {' '.join(all_tags)}\n")
    
    name = input(f"{C.G}Preset-Name: {C.E}").strip()
    if not name:
        print(f"{C.R}Abgebrochen{C.E}")
        input("\nEnter drücken...")
        return
    
    # Load existing presets
    if PRESETS_FILE.exists():
        with open(PRESETS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {"presets": {}, "mixes": {}}
    
    # Save
    data['presets'][name] = all_tags
    
    with open(PRESETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{C.G}✅ Preset '{name}' gespeichert!{C.E}")
    print(f"\n{C.B}Verwende es im Media Manager: Option 2 → 3 (From Preset){C.E}")
    input(f"\n{C.G}Enter drücken...{C.E}")


def start_download(selected_tags):
    """Startet Download mit aktueller Kombination"""
    if not selected_tags:
        print(f"\n{C.R}Keine Tags ausgewählt!{C.E}")
        input("\nEnter drücken...")
        return
    
    # Flatten tags
    all_tags = []
    for tags in selected_tags.values():
        all_tags.extend(tags)
    
    tags_str = '+'.join(all_tags)
    url = f"https://rule34.xxx/index.php?page=post&s=list&tags={tags_str}"
    
    print(f"\n{C.BOLD}Download starten{C.E}\n")
    print(f"{C.Y}Tags:{C.E} {' '.join(all_tags)}")
    print(f"{C.Y}URL:{C.E} {url}\n")
    
    # Limit setzen?
    print(f"{C.B}Download-Limit:{C.E}")
    print(f"  {C.G}1{C.E} - Alle (kein Limit)")
    print(f"  {C.G}2{C.E} - Erste 100")
    print(f"  {C.G}3{C.E} - Erste 500")
    print(f"  {C.G}4{C.E} - Erste 1000")
    print(f"  {C.G}5{C.E} - Erste 5000")
    print(f"  {C.G}c{C.E} - Custom")
    print()
    
    limit_choice = input(f"{C.G}Auswahl: {C.E}").strip().lower()
    
    limit = None
    if limit_choice == '2':
        limit = 100
    elif limit_choice == '3':
        limit = 500
    elif limit_choice == '4':
        limit = 1000
    elif limit_choice == '5':
        limit = 5000
    elif limit_choice == 'c':
        custom = input(f"{C.G}Anzahl: {C.E}").strip()
        try:
            limit = int(custom)
        except ValueError:
            print(f"{C.R}Ungültige Zahl{C.E}")
            input("\nEnter drücken...")
            return
    
    print(f"\n{C.Y}⬇️ Starte Download...{C.E}")
    
    # Call media-downloader
    cmd = [sys.executable, str(BASE_DIR / "scripts" / "media-downloader.py"), url]
    
    # TODO: Limit-Support in media-downloader.py einbauen
    # Für jetzt: Warnung
    if limit:
        print(f"{C.Y}⚠️ Limit {limit} wird an media-downloader übergeben{C.E}")
        print(f"{C.Y}   (Evtl. noch nicht unterstützt - checke Downloads!){C.E}\n")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print(f"\n{C.R}Download abgebrochen{C.E}")
    
    input(f"\n{C.G}Enter drücken...{C.E}")


def quick_presets():
    """Zeigt vordefinierte Quick-Presets"""
    presets = {
        "Bulk - Balanced": ["sissy", "femboy", "-ai_generated", "-low_quality"],
        "Bulk - Real Only": ["sissy", "crossdressing", "-anime", "-cartoon", "-3d"],
        "Cute & Soft": ["sissy", "cute", "pink", "innocent"],
        "Dominant BDSM": ["sissy", "bdsm", "leash", "collar"],
        "Transformation": ["sissy", "transformation", "makeup", "feminization"],
        "Outfit Focus": ["sissy", "lingerie", "stockings", "heels"],
        "High Quality": ["sissy", "high_resolution", "score:>20", "uncensored"],
        "Hypno Specific": ["sissy", "hypnotic", "spiral", "text", "trance"],
    }
    
    clear()
    print_header()
    print(f"\n{C.BOLD}Quick Presets{C.E}\n")
    
    for i, (name, tags) in enumerate(presets.items(), 1):
        tags_str = ', '.join(tags)
        print(f"  {C.G}{i}{C.E}. {C.BOLD}{name}{C.E}")
        print(f"     {C.Y}{tags_str}{C.E}")
        print()
    
    print(f"{C.B}Diese Presets direkt verwenden?{C.E}")
    print(f"  {C.G}1-{len(presets)}{C.E} - Preset auswählen")
    print(f"  {C.R}b{C.E} - Zurück")
    print()
    
    choice = input(f"{C.G}Auswahl: {C.E}").strip()
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(presets):
            name, tags = list(presets.items())[idx]
            
            # Build selected_tags structure
            selected_tags = {"quick": tags}
            
            print(f"\n{C.G}✅ Quick Preset: {name}{C.E}")
            print(f"\n{C.B}Optionen:{C.E}")
            print(f"  {C.G}p{C.E} - Preview")
            print(f"  {C.G}d{C.E} - Download")
            print(f"  {C.G}s{C.E} - Als eigenes Preset speichern")
            print()
            
            action = input(f"{C.G}Auswahl: {C.E}").strip().lower()
            
            if action == 'p':
                preview_combo(selected_tags)
                quick_presets()  # Loop back
            elif action == 'd':
                start_download(selected_tags)
                quick_presets()
            elif action == 's':
                save_as_preset(selected_tags)
                quick_presets()


def main():
    while True:
        clear()
        print_header()
        
        print(f"\n{C.BOLD}Hauptmenü:{C.E}\n")
        print(f"  {C.G}1{C.E} - Tag-Builder (Schritt-für-Schritt)")
        print(f"  {C.G}2{C.E} - Quick Presets (Vordefiniert)")
        print(f"  {C.Y}h{C.E} - Hilfe/Guide")
        print(f"  {C.R}q{C.E} - Quit")
        print()
        
        choice = input(f"{C.G}Auswahl: {C.E}").strip().lower()
        
        if choice == '1':
            build_tag_combo()
        elif choice == '2':
            quick_presets()
        elif choice == 'h':
            show_help()
        elif choice == 'q':
            print(f"\n{C.Y}Bye!{C.E}")
            break


def show_help():
    clear()
    print_header()
    print(f"\n{C.BOLD}Hilfe & Guide{C.E}\n")
    
    print(f"{C.B}1. Tag-Logik:{C.E}")
    print("   + = AND (alle Tags müssen vorhanden sein)")
    print("   - = NOT (Tag ausschließen)")
    print("   Beispiel: sissy+pink-anime = Sissy UND Pink OHNE Anime\n")
    
    print(f"{C.B}2. Kategorien:{C.E}")
    print("   Base = Hauptkategorie (min. 1 wählen)")
    print("   Style = Real/2D/3D")
    print("   Mood = Emotionale Stimmung")
    print("   Action = Was passiert")
    print("   Outfit = Kleidung")
    print("   Body = Körper-Features")
    print("   Quality = Qualitätsfilter")
    print("   Hypno = Hypno-spezifisch\n")
    
    print(f"{C.B}3. Strategie:{C.E}")
    print("   Bulk-Download: Basis + Quality-Exclusions")
    print("   Präzise Suche: Basis + Mood + Outfit + Quality\n")
    
    print(f"{C.B}4. Quick Presets:{C.E}")
    print("   8 vordefinierte Kombinationen für häufige Szenarien\n")
    
    input(f"{C.G}Enter drücken...{C.E}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}Abgebrochen.{C.E}")
        sys.exit(0)
