#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deduplicate - Findet identische und sehr ähnliche Bilder UND Videos
- Bilder: Perceptual Hashing (imagehash) für Ähnlichkeits-Detection
- Videos:  MD5-Hash für exakte Duplikate + optionaler Frame-Hash via FFmpeg
"""

import hashlib
import os
import subprocess
import sys
import tempfile
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

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v'}


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
        print(f"{C.R}Fehlende Dependencies:{C.E}")
        for pkg in missing:
            print(f"   - {pkg}")
        print(f"\n{C.Y}Installation:{C.E}")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True


def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_image_hash(image_path, hash_size=8):
    try:
        from PIL import Image
        import imagehash
        Image.MAX_IMAGE_PIXELS = None
        img = Image.open(image_path)
        return imagehash.average_hash(img, hash_size=hash_size)
    except Exception as e:
        print(f"{C.R}Fehler bei {image_path.name}: {e}{C.E}")
        return None


def get_video_frame_hash(video_path, hash_size=8):
    """Extrahiert ersten Frame per FFmpeg und berechnet perceptual hash."""
    try:
        from PIL import Image
        import imagehash
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        subprocess.run([
            'ffmpeg', '-y', '-ss', '2', '-i', str(video_path),
            '-vframes', '1', '-vf', 'scale=256:-1', '-q:v', '5', tmp_path
        ], capture_output=True, timeout=20)
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return None
        Image.MAX_IMAGE_PIXELS = None
        img = Image.open(tmp_path)
        h = imagehash.average_hash(img, hash_size=hash_size)
        os.unlink(tmp_path)
        return h
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return None


def get_file_md5(path, chunk=1 << 20):
    """MD5 der ersten 4 MB + Dateigröße als schneller Fingerprint."""
    h = hashlib.md5()
    size = path.stat().st_size
    h.update(str(size).encode())
    try:
        with open(path, 'rb') as f:
            for _ in range(4):
                block = f.read(chunk)
                if not block:
                    break
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


def find_image_duplicates(directory, similarity_threshold=5, hash_size=8):
    """Findet duplizierte Bilder per perceptual hash."""
    seen = set()
    image_files = []
    for ext in IMAGE_EXTS:
        for p in directory.rglob(f'*{ext}'):
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                image_files.append(p)

    if not image_files:
        return {}

    total = len(image_files)
    print(f"Bilder gefunden: {total}")
    print(f"Berechne Bild-Hashes...")

    hashes = {}
    for i, img_path in enumerate(image_files, 1):
        print(f"PROGRESS:{i}/{total}")
        h = get_image_hash(img_path, hash_size=hash_size)
        if h is not None:
            hashes[img_path] = h

    print(f"PROGRESS:{total}/{total}")
    print(f"{len(hashes)}/{total} erfolgreich gehashed")
    print(f"Suche Bild-Duplikate (threshold={similarity_threshold})...")

    groups = {}
    processed = set()
    hash_list = list(hashes.items())

    for i, (path1, hash1) in enumerate(hash_list):
        if path1 in processed:
            continue
        group = [path1]
        processed.add(path1)
        for path2, hash2 in hash_list[i + 1:]:
            if path2 in processed:
                continue
            if hash1 - hash2 <= similarity_threshold:
                group.append(path2)
                processed.add(path2)
        if len(group) > 1:
            groups[f"img_{hash1}"] = group

    return groups


def find_video_duplicates(directory, use_frame_hash=False, similarity_threshold=5, hash_size=8):
    """
    Findet duplizierte Videos.
    - Primär: MD5-Fingerprint (Größe + erste 4 MB) für exakte/fast-exakte Duplikate
    - Optional: FFmpeg-Frame-Hash für visuell ähnliche Videos (use_frame_hash=True)
    """
    seen = set()
    video_files = []
    for ext in VIDEO_EXTS:
        for p in directory.rglob(f'*{ext}'):
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                video_files.append(p)

    if not video_files:
        return {}

    total = len(video_files)
    print(f"Videos gefunden: {total}")

    # Source formats that get converted to MP4 — prefer MP4 over these
    CONVERT_EXTS = {'.webm', '.m4v'}
    PREFER_EXT   = '.mp4'

    groups = {}
    exact_paths = set()

    # ── Phase 0: Stem-Match (gleicher Name, verschiedene Extension) ───────────
    # Erkennt foo.webm + foo.mp4 im selben Ordner — typisches Konvertier-Duplikat.
    # Kein Hash nötig, läuft sofort.
    print(f"Pruefe Stem-Duplikate (gleicher Name, verschiedene Extension)...")
    stem_map = defaultdict(list)
    for vp in video_files:
        stem_map[(vp.parent, vp.stem.lower())].append(vp)

    for (parent, stem), files in stem_map.items():
        if len(files) < 2:
            continue
        exts = {f.suffix.lower() for f in files}
        # Nur als Duplikat werten wenn mind. eine Source-Extension dabei ist
        if not exts & CONVERT_EXTS:
            continue
        groups[f"vid_stem_{parent}_{stem}"] = files
        exact_paths.update(files)

    stem_count = sum(len(g) - 1 for g in groups.values())
    print(f"Stem-Duplikate (pre/post Konvertierung): {stem_count}")

    # ── Phase 1: MD5-Fingerprint (exakte Byte-Duplikate) ─────────────────────
    print(f"Berechne Video-Fingerprints (MD5)...")
    remaining_for_md5 = [vp for vp in video_files if vp not in exact_paths]
    md5_map = defaultdict(list)
    for i, vp in enumerate(remaining_for_md5, 1):
        print(f"PROGRESS:{i}/{len(remaining_for_md5)}")
        h = get_file_md5(vp)
        if h:
            md5_map[h].append(vp)
    if remaining_for_md5:
        print(f"PROGRESS:{len(remaining_for_md5)}/{len(remaining_for_md5)}")

    for h, files in md5_map.items():
        if len(files) > 1:
            groups[f"vid_exact_{h}"] = files
            exact_paths.update(files)

    exact_count = sum(1 for k, g in groups.items() if k.startswith('vid_exact_') for _ in g[1:])
    print(f"Exakte Video-Duplikate (gleicher Inhalt): {exact_count}")

    # ── Phase 2: Frame-Hash für ähnliche Videos (optional, braucht FFmpeg) ──
    if use_frame_hash:
        remaining = [vp for vp in video_files if vp not in exact_paths]
        if remaining:
            print(f"Berechne Frame-Hashes für {len(remaining)} Videos...")
            frame_hashes = {}
            for i, vp in enumerate(remaining, 1):
                print(f"PROGRESS:{i}/{len(remaining)}")
                h = get_video_frame_hash(vp, hash_size=hash_size)
                if h is not None:
                    frame_hashes[vp] = h
            print(f"PROGRESS:{len(remaining)}/{len(remaining)}")
            print(f"Suche ähnliche Videos (threshold={similarity_threshold})...")

            processed = set()
            fh_list = list(frame_hashes.items())
            for i, (p1, h1) in enumerate(fh_list):
                if p1 in processed:
                    continue
                group = [p1]
                processed.add(p1)
                for p2, h2 in fh_list[i + 1:]:
                    if p2 in processed:
                        continue
                    if h1 - h2 <= similarity_threshold:
                        group.append(p2)
                        processed.add(p2)
                if len(group) > 1:
                    groups[f"vid_similar_{h1}"] = group

    return groups


def find_duplicates(directory, similarity_threshold=5, hash_size=8, include_videos=True, use_frame_hash=False):
    """Findet Duplikate in Bildern und Videos."""
    print(f"\n{C.BOLD}Scanne Medien...{C.E}\n")

    all_groups = {}
    all_groups.update(find_image_duplicates(directory, similarity_threshold, hash_size))

    if include_videos:
        print()
        all_groups.update(find_video_duplicates(directory, use_frame_hash, similarity_threshold, hash_size))

    return all_groups


def _is_new(path: Path) -> bool:
    """True wenn die Datei in einem 'new/' Unterordner liegt."""
    return 'new' in path.parts


_CONVERT_EXTS = {'.webm', '.m4v'}

def _rank_file(path: Path, size: int) -> tuple:
    """
    Sortierkey (aufsteigend = wird behalten):
      1. Bibliotheks-Datei (nicht in new/) vor new/-Datei
      2. MP4 vor Source-Formaten (.webm, .m4v)
      3. Größere Datei vor kleinerer
    """
    is_new       = 1 if _is_new(path) else 0
    is_src_fmt   = 1 if path.suffix.lower() in _CONVERT_EXTS else 0
    return (is_new, is_src_fmt, -size)


def show_duplicates(groups):
    """Zeigt gefundene Duplikate"""
    if not groups:
        print(f"{C.G}Keine Duplikate gefunden!{C.E}")
        return

    total_dupes = sum(len(g) - 1 for g in groups.values())
    img_groups  = {k: v for k, v in groups.items() if k.startswith('img_')}
    vid_groups  = {k: v for k, v in groups.items() if k.startswith('vid_')}

    print(f"{C.BOLD}Gefundene Duplikate:{C.E}\n")
    print(f"  Gruppen gesamt:  {len(groups)}")
    print(f"  Bild-Gruppen:    {len(img_groups)}")
    print(f"  Video-Gruppen:   {len(vid_groups)}")
    print(f"  Duplikate total: {total_dupes}")
    print()

    for i, (hash_key, files) in enumerate(groups.items(), 1):
        kind = "Bild" if hash_key.startswith('img_') else "Video"
        if "stem" in hash_key:
            sim = "Konvertier-Duplikat (gleicher Name)"
        elif "similar" in hash_key:
            sim = "ähnlich (Frame-Hash)"
        else:
            sim = "exakt (gleicher Inhalt)"
        print(f"{C.Y}Gruppe {i} ({len(files)} {kind}s, {sim}):{C.E}")

        ranked = []
        for f in files:
            try:
                ranked.append((f, f.stat().st_size))
            except OSError:
                continue
        ranked.sort(key=lambda x: _rank_file(x[0], x[1]))

        for j, (f, size) in enumerate(ranked):
            marker  = f"{C.G}KEEP{C.E}" if j == 0 else f"{C.R}DUP{C.E}"
            loc     = f"{C.Y}[new]{C.E} " if _is_new(f) else f"{C.G}[lib]{C.E} "
            size_mb = size / (1024 * 1024)
            print(f"  {marker} {loc}{f.name} ({size_mb:.2f} MB)")
        print()


def remove_duplicates(groups, dry_run=True):
    """Entfernt Duplikate — bevorzugt Bibliotheks-Dateien (nicht in new/) über new/-Dateien."""
    if not groups:
        print(f"{C.G}Keine Duplikate zum Entfernen{C.E}")
        return 0, 0

    DUPLICATES_DIR.mkdir(exist_ok=True)
    total_removed = 0
    total_saved_mb = 0

    for files in groups.values():
        # stat() each file, skip missing (already moved by a previous run)
        ranked = []
        for f in files:
            try:
                ranked.append((f, f.stat().st_size))
            except OSError:
                print(f"{C.Y}Datei nicht gefunden (übersprungen): {f.name}{C.E}")
        if len(ranked) < 2:
            continue
        # Sort: library files first (is_new=False), then by size desc
        ranked.sort(key=lambda x: _rank_file(x[0], x[1]))

        to_remove = [f for f, _ in ranked[1:]]
        for dup_file in to_remove:
            try:
                size_mb = dup_file.stat().st_size / (1024 * 1024)
            except OSError:
                print(f"{C.Y}Datei nicht gefunden (übersprungen): {dup_file.name}{C.E}")
                continue
            if dry_run:
                print(f"{C.Y}[DRY] Would remove: {dup_file.name} ({size_mb:.2f} MB){C.E}")
            else:
                dest = DUPLICATES_DIR / dup_file.name
                counter = 1
                while dest.exists():
                    dest = DUPLICATES_DIR / f"{dup_file.stem}_{counter}{dup_file.suffix}"
                    counter += 1
                try:
                    shutil.move(str(dup_file), str(dest))
                    print(f"{C.G}Moved: {dup_file.name} -> duplicates/{dest.name}{C.E}")
                    total_removed += 1
                    total_saved_mb += size_mb
                except OSError as e:
                    print(f"{C.R}Fehler beim Verschieben von {dup_file.name}: {e}{C.E}")

    return total_removed, total_saved_mb


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Deduplicate images and videos')
    parser.add_argument('--auto', action='store_true',
                        help='Non-interactive: scan and move duplicates automatically')
    parser.add_argument('--dry-run', action='store_true',
                        help='Non-interactive: scan only, no changes')
    parser.add_argument('--dir', default=None,
                        help='Directory to scan (default: all of sorted/)')
    parser.add_argument('--threshold', type=int, default=5,
                        help='Similarity threshold 0-20 (default: 5)')
    parser.add_argument('--no-videos', action='store_true',
                        help='Skip video deduplication')
    parser.add_argument('--frame-hash', action='store_true',
                        help='Use FFmpeg frame hash for similar (not just exact) video detection')
    args = parser.parse_args()

    print(f"{C.BOLD}{C.B}")
    print("╔═══════════════════════════════════════╗")
    print("║      DEDUPLICATE v2.0                ║")
    print("║   Images + Videos Deduplication      ║")
    print("╚═══════════════════════════════════════╝")
    print(f"{C.E}\n")

    if not check_dependencies():
        sys.exit(1)

    use_frame_hash = args.frame_hash
    if use_frame_hash and not check_ffmpeg():
        print(f"{C.Y}FFmpeg nicht gefunden - Frame-Hash deaktiviert{C.E}")
        use_frame_hash = False

    if args.auto or args.dry_run or args.dir is not None:
        target_dir = Path(args.dir) if args.dir else BASE_DIR / "sorted"
        threshold  = args.threshold
    else:
        print(f"{C.BOLD}Verzeichnis zum Scannen:{C.E}\n")
        print(f"  {C.G}1{C.E} - sorted/images")
        print(f"  {C.G}2{C.E} - sorted/videos")
        print(f"  {C.G}3{C.E} - sorted/hypno")
        print(f"  {C.G}4{C.E} - incoming")
        print(f"  {C.G}5{C.E} - Alle sorted/ Ordner")
        print(f"  {C.G}c{C.E} - Custom path")
        print()
        choice = input(f"{C.G}Auswahl: {C.E}").strip()
        if choice == '1':
            target_dir = BASE_DIR / "sorted" / "images"
        elif choice == '2':
            target_dir = BASE_DIR / "sorted" / "videos"
        elif choice == '3':
            target_dir = BASE_DIR / "sorted" / "hypno"
        elif choice == '4':
            target_dir = BASE_DIR / "incoming"
        elif choice == '5':
            target_dir = BASE_DIR / "sorted"
        elif choice == 'c':
            target_dir = Path(input(f"{C.G}Pfad: {C.E}").strip())
        else:
            print(f"{C.R}Ungueltige Auswahl{C.E}")
            sys.exit(1)

        print(f"\n{C.BOLD}Similarity Threshold:{C.E}\n")
        print(f"  {C.G}1{C.E} - Strict (0) - nur identische")
        print(f"  {C.G}2{C.E} - Normal (5) - sehr aehnlich (empfohlen)")
        print(f"  {C.G}3{C.E} - Loose (10) - auch leicht unterschiedliche")
        print(f"  {C.G}c{C.E} - Custom")
        print()
        tc = input(f"{C.G}Auswahl: {C.E}").strip()
        if tc == '1':
            threshold = 0
        elif tc == '3':
            threshold = 10
        elif tc == 'c':
            threshold = int(input(f"{C.G}Threshold (0-20): {C.E}").strip())
        else:
            threshold = 5

        if not use_frame_hash and check_ffmpeg():
            fh = input(f"\n{C.G}Frame-Hash fuer aehnliche Videos aktivieren? (y/n): {C.E}").strip().lower()
            use_frame_hash = (fh == 'y')

    if not target_dir.exists():
        print(f"{C.R}Verzeichnis nicht gefunden: {target_dir}{C.E}")
        sys.exit(1)

    print(f"Scanne: {target_dir}  (threshold={threshold})")
    include_videos = not args.no_videos
    if include_videos:
        fh_info = " + Frame-Hash" if use_frame_hash else " (nur exakte Video-Duplikate)"
        print(f"Videos: aktiv{fh_info}")
    print()

    groups = find_duplicates(target_dir, similarity_threshold=threshold,
                             include_videos=include_videos, use_frame_hash=use_frame_hash)

    show_duplicates(groups)

    if not groups:
        return

    if args.dry_run:
        remove_duplicates(groups, dry_run=True)
        print(f"\n{C.B}Dry run - keine Aenderungen vorgenommen{C.E}")
        return

    if args.auto:
        removed, saved_mb = remove_duplicates(groups, dry_run=False)
        print(f"\n{C.G}Fertig!{C.E}")
        print(f"  Entfernt: {removed} Dateien")
        print(f"  Gespart:  {saved_mb:.2f} MB")
        print(f"  Duplikate in: {DUPLICATES_DIR}")
        return

    print(f"\n{C.BOLD}Aktion:{C.E}\n")
    print(f"  {C.G}1{C.E} - Duplikate entfernen (nach duplicates/ verschieben)")
    print(f"  {C.G}2{C.E} - Nur anzeigen (dry run)")
    print(f"  {C.R}q{C.E} - Abbrechen")
    print()
    action = input(f"{C.G}Auswahl: {C.E}").strip()

    if action == '1':
        print(f"\n{C.Y}Duplikate werden nach duplicates/ verschoben!{C.E}")
        confirm = input(f"{C.G}Fortfahren? (y/n): {C.E}").strip().lower()
        if confirm == 'y':
            removed, saved_mb = remove_duplicates(groups, dry_run=False)
            print(f"\n{C.G}Fertig!{C.E}")
            print(f"  Entfernt: {removed} Dateien")
            print(f"  Gespart:  {saved_mb:.2f} MB")
            print(f"  Duplikate in: {DUPLICATES_DIR}")
    elif action == '2':
        remove_duplicates(groups, dry_run=True)
        print(f"\n{C.B}Dry run - keine Aenderungen vorgenommen{C.E}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}Abgebrochen.{C.E}")
        sys.exit(0)
