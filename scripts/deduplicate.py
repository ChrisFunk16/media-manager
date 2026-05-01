#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deduplicate - Findet identische und sehr ähnliche Bilder
Nutzt Perceptual Hashing (imagehash) für Ähnlichkeits-Detection
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import shutil

# Farben
class C:
    B = '\033[94m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    E = '\033[0m'
    BOLD = '\033[1m'

# Windows ANSI Support
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

BASE_DIR = Path(__file__).parent.parent
DUPLICATES_DIR = BASE_DIR / "duplicates"


def check_dependencies():
    """Prüft ob PIL und imagehash installiert sind"""
    missing = []
    
    try:
        from PIL import Image
    except ImportError:
        missing.append('Pillow')
    
    try:
        import imagehash
    except ImportError:
        missing.append('imagehash')
    
    if missing:
        print(f"{C.R}❌ Fehlende Dependencies:{C.E}")
        for pkg in missing:
            print(f"   - {pkg}")
        print(f"\n{C.Y}Installation:{C.E}")
        print(f"  pip install {' '.join(missing)}")
        print(f"\n{C.Y}Oder (user-install):{C.E}")
        print(f"  pip install --user {' '.join(missing)}")
        return False
    
    return True


def get_image_hash(image_path, hash_size=8):
    """
    Berechnet perceptual hash eines Bildes
    hash_size: Größe des Hash (8=64bit, 16=256bit)
              Größer = präziser, kleiner = findet mehr Ähnliche
    """
    try:
        from PIL import Image
        import imagehash
        
        img = Image.open(image_path)
        # Average hash - schnell und robust
        return imagehash.average_hash(img, hash_size=hash_size)
    except Exception as e:
        print(f"{C.R}Fehler bei {image_path.name}: {e}{C.E}")
        return None


def find_duplicates(directory, similarity_threshold=5, hash_size=8):
    """
    Findet Duplikate und ähnliche Bilder
    
    similarity_threshold: Hamming-Distanz für Ähnlichkeit
                         0 = identisch
                         1-5 = sehr ähnlich (leichte Kompression/Resize)
                         6-10 = ähnlich (Crop, leichte Änderungen)
                         >10 = unterschiedlich
    
    Returns: {hash: [files]} dict mit ähnlichen Bildern gruppiert
    """
    print(f"\n{C.BOLD}Scanne Bilder...{C.E}\n")
    
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Alle Bilder finden
    image_files = []
    for ext in image_exts:
        image_files.extend(directory.rglob(f'*{ext}'))
        image_files.extend(directory.rglob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"{C.Y}Keine Bilder gefunden in {directory}{C.E}")
        return {}
    
    print(f"Gefunden: {len(image_files)} Bilder")
    print(f"Berechne Hashes (hash_size={hash_size})...\n")
    
    # Hashes berechnen
    hashes = {}
    for i, img_path in enumerate(image_files, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(image_files)}...", end='\r')
        
        img_hash = get_image_hash(img_path, hash_size=hash_size)
        if img_hash:
            hashes[img_path] = img_hash
    
    print(f"  {len(hashes)}/{len(image_files)} erfolgreich gehashed")
    
    # Gruppiere ähnliche Bilder
    print(f"\n{C.BOLD}Suche Duplikate (threshold={similarity_threshold})...{C.E}\n")
    
    groups = defaultdict(list)
    processed = set()
    
    hash_list = list(hashes.items())
    
    for i, (path1, hash1) in enumerate(hash_list):
        if path1 in processed:
            continue
        
        group = [path1]
        processed.add(path1)
        
        # Vergleiche mit restlichen
        for path2, hash2 in hash_list[i+1:]:
            if path2 in processed:
                continue
            
            # Hamming-Distanz berechnen
            distance = hash1 - hash2
            
            if distance <= similarity_threshold:
                group.append(path2)
                processed.add(path2)
        
        # Nur Gruppen mit 2+ Bildern speichern
        if len(group) > 1:
            groups[str(hash1)] = group
    
    return groups


def show_duplicates(groups):
    """Zeigt gefundene Duplikate"""
    if not groups:
        print(f"{C.G}✅ Keine Duplikate gefunden!{C.E}")
        return
    
    total_dupes = sum(len(g) - 1 for g in groups.values())
    
    print(f"{C.BOLD}Gefundene Duplikate:{C.E}\n")
    print(f"  Gruppen: {len(groups)}")
    print(f"  Duplikate: {total_dupes} Bilder")
    print()
    
    for i, (hash_key, files) in enumerate(groups.items(), 1):
        print(f"{C.Y}Gruppe {i} ({len(files)} Bilder):{C.E}")
        
        # Sortiere nach Dateigröße (größtes = meist beste Qualität)
        files_with_size = [(f, f.stat().st_size) for f in files]
        files_with_size.sort(key=lambda x: x[1], reverse=True)
        
        for j, (f, size) in enumerate(files_with_size):
            marker = f"{C.G}✓ KEEP{C.E}" if j == 0 else f"{C.R}✗ DUP{C.E}"
            size_mb = size / (1024*1024)
            print(f"  {marker} {f.name} ({size_mb:.2f} MB)")
        print()


def remove_duplicates(groups, dry_run=True):
    """
    Entfernt Duplikate
    Behält größte Datei (meist beste Qualität)
    """
    if not groups:
        print(f"{C.G}Keine Duplikate zum Entfernen{C.E}")
        return 0, 0
    
    DUPLICATES_DIR.mkdir(exist_ok=True)
    
    total_removed = 0
    total_saved_mb = 0
    
    for files in groups.values():
        # Sortiere nach Größe (größtes behalten)
        files_with_size = [(f, f.stat().st_size) for f in files]
        files_with_size.sort(key=lambda x: x[1], reverse=True)
        
        # Erste = behalten, Rest = entfernen
        keep_file = files_with_size[0][0]
        to_remove = [f for f, _ in files_with_size[1:]]
        
        for dup_file in to_remove:
            size_mb = dup_file.stat().st_size / (1024*1024)
            
            if dry_run:
                print(f"{C.Y}[DRY] Would remove: {dup_file.name} ({size_mb:.2f} MB){C.E}")
            else:
                # Move to duplicates folder
                dest = DUPLICATES_DIR / dup_file.name
                
                # Handle name conflicts
                counter = 1
                while dest.exists():
                    dest = DUPLICATES_DIR / f"{dup_file.stem}_{counter}{dup_file.suffix}"
                    counter += 1
                
                shutil.move(str(dup_file), str(dest))
                print(f"{C.G}Moved: {dup_file.name} → duplicates/{dest.name}{C.E}")
                
                total_removed += 1
                total_saved_mb += size_mb
    
    return total_removed, total_saved_mb


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Deduplicate images')
    parser.add_argument('--auto', action='store_true',
                        help='Non-interactive: scan and move duplicates automatically')
    parser.add_argument('--dry-run', action='store_true',
                        help='Non-interactive: scan only, no changes')
    parser.add_argument('--dir', default=None,
                        help='Directory to scan (default: sorted/images). '
                             'Use "sorted" for all sorted subdirs.')
    parser.add_argument('--threshold', type=int, default=5,
                        help='Similarity threshold 0-20 (default: 5)')
    args = parser.parse_args()

    print(f"{C.BOLD}{C.B}")
    print("╔═══════════════════════════════════════╗")
    print("║      🔍 DEDUPLICATE v1.0             ║")
    print("║   Perceptual Image Deduplication     ║")
    print("╚═══════════════════════════════════════╝")
    print(f"{C.E}\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Determine target directory
    if args.auto or args.dry_run or args.dir is not None:
        if args.dir == 'sorted' or args.dir is None:
            target_dir = BASE_DIR / "sorted"
        else:
            target_dir = Path(args.dir)
        threshold = args.threshold
    else:
        # Welches Verzeichnis?
        print(f"{C.BOLD}Verzeichnis zum Scannen:{C.E}\n")
        print(f"  {C.G}1{C.E} - sorted/images")
        print(f"  {C.G}2{C.E} - sorted/bulk")
        print(f"  {C.G}3{C.E} - sorted/favorites")
        print(f"  {C.G}4{C.E} - incoming")
        print(f"  {C.G}5{C.E} - Alle sorted/ Ordner")
        print(f"  {C.G}c{C.E} - Custom path")
        print()

        choice = input(f"{C.G}Auswahl: {C.E}").strip()

        if choice == '1':
            target_dir = BASE_DIR / "sorted" / "images"
        elif choice == '2':
            target_dir = BASE_DIR / "sorted" / "bulk"
        elif choice == '3':
            target_dir = BASE_DIR / "sorted" / "favorites"
        elif choice == '4':
            target_dir = BASE_DIR / "incoming"
        elif choice == '5':
            target_dir = BASE_DIR / "sorted"
        elif choice == 'c':
            custom = input(f"{C.G}Pfad: {C.E}").strip()
            target_dir = Path(custom)
        else:
            print(f"{C.R}Ungültige Auswahl{C.E}")
            sys.exit(1)

        # Similarity threshold
        print(f"\n{C.BOLD}Similarity Threshold:{C.E}\n")
        print(f"  {C.G}1{C.E} - Strict (0) - nur identische")
        print(f"  {C.G}2{C.E} - Normal (5) - sehr ähnlich (empfohlen)")
        print(f"  {C.G}3{C.E} - Loose (10) - auch leicht unterschiedliche")
        print(f"  {C.G}c{C.E} - Custom")
        print()

        thresh_choice = input(f"{C.G}Auswahl: {C.E}").strip()

        if thresh_choice == '1':
            threshold = 0
        elif thresh_choice == '3':
            threshold = 10
        elif thresh_choice == 'c':
            threshold = int(input(f"{C.G}Threshold (0-20): {C.E}").strip())
        else:
            threshold = 5

    if not target_dir.exists():
        print(f"{C.R}Verzeichnis nicht gefunden: {target_dir}{C.E}")
        sys.exit(1)

    print(f"Scanne: {target_dir}  (threshold={threshold})\n")

    # Scan
    groups = find_duplicates(target_dir, similarity_threshold=threshold)

    # Show results
    show_duplicates(groups)

    if not groups:
        return

    # Action
    if args.dry_run:
        remove_duplicates(groups, dry_run=True)
        print(f"\n{C.B}Dry run - keine Änderungen vorgenommen{C.E}")
        return

    if args.auto:
        removed, saved_mb = remove_duplicates(groups, dry_run=False)
        print(f"\n{C.G}✅ Fertig!{C.E}")
        print(f"  Entfernt: {removed} Bilder")
        print(f"  Gespart: {saved_mb:.2f} MB")
        print(f"  Duplikate in: {DUPLICATES_DIR}")
        return

    print(f"\n{C.BOLD}Aktion:{C.E}\n")
    print(f"  {C.G}1{C.E} - Duplikate entfernen (nach duplicates/ verschieben)")
    print(f"  {C.G}2{C.E} - Nur anzeigen (dry run)")
    print(f"  {C.R}q{C.E} - Abbrechen")
    print()

    action = input(f"{C.G}Auswahl: {C.E}").strip()

    if action == '1':
        print(f"\n{C.Y}⚠️ Duplikate werden nach duplicates/ verschoben!{C.E}")
        confirm = input(f"{C.G}Fortfahren? (y/n): {C.E}").strip().lower()

        if confirm == 'y':
            removed, saved_mb = remove_duplicates(groups, dry_run=False)
            print(f"\n{C.G}✅ Fertig!{C.E}")
            print(f"  Entfernt: {removed} Bilder")
            print(f"  Gespart: {saved_mb:.2f} MB")
            print(f"  Duplikate in: {DUPLICATES_DIR}")

    elif action == '2':
        removed, saved_mb = remove_duplicates(groups, dry_run=True)
        print(f"\n{C.B}Dry run - keine Änderungen vorgenommen{C.E}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}Abgebrochen.{C.E}")
        sys.exit(0)
