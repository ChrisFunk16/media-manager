# 🔍 Deduplicate - Setup & Usage

## Installation

Deduplicate benötigt zwei Python-Pakete:

```bash
# Linux/Mac
pip install Pillow imagehash

# Windows
pip install Pillow imagehash

# Oder user-install (ohne sudo)
pip install --user Pillow imagehash
```

**Was wird installiert:**
- **Pillow:** Image processing (öffnen/lesen)
- **imagehash:** Perceptual hashing (Ähnlichkeits-Erkennung)

---

## Usage

```bash
cd media-collection
python3 scripts/deduplicate.py
```

### Interactive Menu

**1. Verzeichnis wählen:**
- sorted/images
- sorted/bulk
- sorted/favorites
- incoming
- Alle sorted/
- Custom path

**2. Similarity Threshold:**
- **Strict (0):** Nur identische Bilder
- **Normal (5):** Sehr ähnlich (empfohlen) ✅
  - Findet: Gleiche Bilder mit leichter Kompression/Resize
- **Loose (10):** Auch leicht unterschiedliche
  - Findet: Crops, leichte Edits, ähnliche Posen
- **Custom:** 0-20 frei wählbar

**3. Aktion:**
- **Entfernen:** Verschiebt Duplikate nach `duplicates/`
- **Dry run:** Zeigt nur an, ändert nichts

---

## Wie es funktioniert

### Perceptual Hashing

1. Berechnet für jedes Bild einen "Fingerprint" (Hash)
2. Vergleicht Hashes miteinander (Hamming-Distanz)
3. Gruppiert ähnliche Bilder

**Vorteile gegenüber MD5/SHA:**
- Findet auch ähnliche Bilder (nicht nur identische)
- Ignoriert Kompression, Resize, leichte Änderungen
- Robust gegen JPEG-Artefakte

### Beispiel-Matches

**Threshold 0 (identisch):**
- `image.jpg` = `image_copy.jpg` ✅
- `image.jpg` ≠ `image_resized.jpg` ❌

**Threshold 5 (empfohlen):**
- `image.jpg` = `image_copy.jpg` ✅
- `image.jpg` = `image_80%quality.jpg` ✅
- `image.jpg` = `image_resized.jpg` ✅
- `image.jpg` ≠ `image_cropped.jpg` ❌

**Threshold 10 (loose):**
- Alles von Threshold 5 ✅
- `image.jpg` = `image_cropped.jpg` ✅
- `image.jpg` = `image_slightly_edited.jpg` ✅

---

## Welche Datei wird behalten?

**Strategie:** Größte Datei = beste Qualität

```
Gruppe 1:
  ✓ KEEP  image_original.jpg (5.2 MB)  ← Behalten
  ✗ DUP   image_compressed.jpg (1.8 MB)
  ✗ DUP   image_thumbnail.jpg (0.3 MB)
```

**Duplikate werden verschoben nach:** `duplicates/`

---

## Workflow-Beispiele

### Bulk-Download bereinigen

```bash
# 1. Bulk-Download (5000 Bilder)
python3 scripts/tag-builder.py
→ Download → incoming/

# 2. Nach bulk/ verschieben
mv incoming/* sorted/bulk/

# 3. Deduplizieren (vor Video-Erstellung)
python3 scripts/deduplicate.py
→ sorted/bulk
→ Threshold: 5 (normal)
→ Entfernen

# Ergebnis: ~20% weniger Bilder, 20% weniger Speicher
```

### Favorites curate

```bash
# 1. Präzise Download (100 Bilder)
python3 scripts/tag-builder.py
→ Favorites-Preset

# 2. Manuell review
# Beste → sorted/favorites/

# 3. Deduplizieren (strict)
python3 scripts/deduplicate.py
→ sorted/favorites
→ Threshold: 3 (strict)
→ Entfernen

# Behält auch leicht unterschiedliche Versionen
```

### Incoming vor Sortierung

```bash
# 1. Mehrere Downloads
# incoming/ hat jetzt 2000+ Bilder

# 2. Dedupe BEVOR sorting
python3 scripts/deduplicate.py
→ incoming/
→ Threshold: 10 (aggressive)
→ Entfernen

# 3. Dann auto-sort
python3 scripts/auto-sort.py

# Spart Zeit beim Sortieren
```

---

## Performance

**Geschwindigkeit:**
- ~1000 Bilder: 20-30 Sekunden
- ~5000 Bilder: 2-3 Minuten
- ~10000 Bilder: 5-10 Minuten

**Abhängig von:**
- CPU-Speed
- Bildgröße/Auflösung
- Hash-Size (Standard: 8x8 = schnell)

---

## Trouble shooting

### "ModuleNotFoundError: No module named 'PIL'"
```bash
pip install Pillow
```

### "ModuleNotFoundError: No module named 'imagehash'"
```bash
pip install imagehash
```

### "Permission denied"
```bash
pip install --user Pillow imagehash
```

### Zu viele False Positives
→ Threshold reduzieren (10 → 5 → 3)

### Zu wenige Matches
→ Threshold erhöhen (5 → 10 → 15)

### Falsche Datei behalten
- Aktuell: Größte Datei = beste Qualität
- Alternativ: Manuell aus `duplicates/` zurückholen

---

## Advanced: Hash-Size tuning

Standard: `hash_size=8` (64-bit hash)

**Größer = präziser, aber findet weniger Ähnliche:**
```python
hash_size=16  # 256-bit, sehr präzise
hash_size=8   # 64-bit, Standard
hash_size=4   # 16-bit, findet mehr Ähnliche
```

**Im Code ändern (scripts/deduplicate.py):**
```python
# Line ~50
def find_duplicates(directory, similarity_threshold=5, hash_size=8):
```

---

## Backup & Safety

**Duplikate werden VERSCHOBEN, nicht gelöscht:**
- Sichere Variante: Review in `duplicates/`
- Endgültig löschen: `rm -rf duplicates/*`

**Dry-Run nutzen:**
- Erst dry-run → checken was gelöscht würde
- Dann real-run

**Backup vor Mass-Dedupe:**
```bash
# Falls du 10k+ Bilder deduplizierst
cp -r sorted/bulk sorted/bulk_backup
```

---

## FAQ

**Q: Kann ich gleichzeitig mehrere Ordner deduplizieren?**
A: Ja, wähle "Alle sorted/" - dedupliziert alle Unterordner

**Q: Funktioniert es mit Videos?**
A: Aktuell nur Bilder (jpg/png/gif/webp/bmp)

**Q: Werden Metadaten/EXIF behalten?**
A: Ja, Files werden nur verschoben (keine Re-encoding)

**Q: Kann ich gelöschte Duplikate wiederherstellen?**
A: Ja, aus `duplicates/` Ordner zurückholen

**Q: Wie viel Speicher wird gespart?**
A: Durchschnitt: 15-25% bei Threshold 5
