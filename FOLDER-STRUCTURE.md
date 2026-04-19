# 📁 Folder Structure & Workflow

## Neue Ordner-Struktur

```
media-collection/
├── incoming/              # Downloads landen hier (auto)
├── sorted/
│   ├── bulk/             # 🆕 Masse für schnelle Video-Cuts
│   ├── favorites/        # 🆕 Handverlesen, spezielle Tags
│   ├── images/           # Generische Bilder (Archiv)
│   ├── gifs/             # GIFs
│   ├── videos/           # Videos
│   └── hypno/            # Hypno-Content
├── duplicates/           # 🆕 Gefundene Duplikate
└── scripts/
```

## Workflow

### 1️⃣ Bulk-Download (Masse sammeln)

**Purpose:** Viele Bilder für schnelle Video-Cuts (9k+ für 10min)

**Process:**
```bash
# Tag-Builder: Bulk-Preset erstellen
python3 scripts/tag-builder.py
→ Quick Presets → "Bulk - Balanced"
→ Download (Limit: 5000)

# Downloads landen in: incoming/

# Manuell nach bulk/ verschieben:
mv incoming/* sorted/bulk/

# Oder Auto-Sort mit bulk-Flag (TODO)
```

**Charakteristik:**
- Hohe Menge wichtiger als Perfektion
- Quality-Filter: `-ai_generated -low_quality -duplicate`
- Keine manuelle Review

---

### 2️⃣ Favorites-Download (Handverlesen)

**Purpose:** Spezielle Bilder für bestimmte Szenen/Moods

**Process:**
```bash
# Tag-Builder: Präzise Tag-Combo
python3 scripts/tag-builder.py
→ Tag-Builder
→ Base: sissy
→ Mood: cute + pink
→ Outfit: lingerie
→ Quality: score:>20
→ Download (Limit: 100)

# Downloads landen in: incoming/

# Review im Browser/Viewer
# Gute → favorites/ verschieben
# Rest → bulk/ oder löschen
```

**Charakteristik:**
- Qualität > Quantität
- Score-Filter aktiv
- Manuelle Review/Curation

---

### 3️⃣ Deduplizierung

**Purpose:** Identische und sehr ähnliche Bilder entfernen

**Process:**
```bash
# Deduplizierung laufen lassen
python3 scripts/deduplicate.py

# Optionen:
1. Scanne sorted/bulk  (vor Video-Erstellung)
2. Scanne sorted/favorites (nach Curation)
3. Scanne incoming (vor Sortierung)

# Threshold:
- Strict (0): Nur identische
- Normal (5): Sehr ähnlich (empfohlen)
- Loose (10): Auch leicht unterschiedliche
```

**Output:**
- Behält größte Datei (meist beste Qualität)
- Verschiebt Duplikate nach `duplicates/`
- Zeigt gesparten Speicherplatz

---

## Entscheidungsbaum

```
Download fertig (in incoming/)
    ↓
Bulk oder Favorites?
    ↓
┌─────────────┴─────────────┐
│                           │
Bulk                    Favorites
│                           │
→ Dedupe (optional)     → Review manuell
→ Move to bulk/         → Beste → favorites/
→ Fertig                → Rest → bulk/ oder delete
                        → Dedupe
                        → Fertig
```

---

## Auto-Sort Anpassung

**Aktuell:** `auto-sort.py` sortiert nur nach Dateityp
- images/ (Bilder)
- gifs/ (GIFs)
- videos/ (Videos)

**Neu (geplant):**
```python
# Download-Source detection
if from_rule34_bulk_preset:
    → sorted/bulk/
elif from_tag_builder_favorites:
    → sorted/favorites/
else:
    → sorted/images/ (default)
```

**Manuell vs Auto:**
- Bulk: Manuell verschieben (nach Download)
- Favorites: Manuell curate (Review erforderlich)
- Default: Auto (wie bisher)

---

## Verwendung in Video-Editing

### Hypno-Video (10min, schnelle Cuts)

**Material:**
```
sorted/bulk/         ~9,000+ Bilder (Masse)
sorted/favorites/    ~100-500 Bilder (Key frames)
```

**Strategy:**
- Bulk: Alle 2 Frames (Hauptmasse)
- Favorites: Key moments, wichtige Szenen
- Mix: Randomized aus bulk/, favorites für Highlights

---

## Dedupe-Strategy

### Wann deduplizieren?

**Bulk:**
- ✅ NACH Download, VOR Video-Erstellung
- Grund: Spart Speicher, vermeidet repeated frames

**Favorites:**
- ✅ NACH Curation
- Grund: Manuelle Selection könnte bereits Dupes enthalten

**Incoming:**
- ⚠️ Optional, vor Sortierung
- Grund: Spart Zeit beim Sortieren

### Threshold-Guide

**Bulk-Downloads:**
- Threshold: **5** (normal)
- Grund: Filtert Dupes + leichte Kompressions-Varianten

**Favorites:**
- Threshold: **0-3** (strict)
- Grund: Behalte auch leicht unterschiedliche Versionen

**Incoming (vor Review):**
- Threshold: **10** (loose)
- Grund: Aggressive Filterung, du kannst später noch curate

---

## Storage-Management

### Platzbedarf (geschätzt)

**Bulk (5,000 Bilder):**
- Avg 1 MB/Bild → ~5 GB
- Nach Dedupe (ca. -20%): ~4 GB

**Favorites (500 Bilder):**
- Avg 2 MB/Bild (höhere Qualität) → ~1 GB

**Duplicates:**
- Behalten als Backup (falls versehentlich gelöscht)
- Regelmäßig leeren (nach Review)

---

## Tools-Übersicht

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Tag-Builder | Tag-Kombos erstellen | Interactive | Presets + URLs |
| Media Manager | Downloads ausführen | URLs | incoming/ |
| Auto-Sort | Dateityp-Sortierung | incoming/ | sorted/images/gifs/videos |
| Deduplicate | Dupes entfernen | sorted/* | duplicates/ (moved) |

---

## Next Steps

1. ✅ Ordner-Struktur erstellen (bulk/, favorites/)
2. ✅ Dedupe-Tool testen
3. ⏳ Bulk-Download starten (Tag-Builder)
4. ⏳ Dedupe ausführen
5. ⏳ Video-Editing-Workflow bauen
