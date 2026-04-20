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
│   ├── videos/           # Videos (automatisch in Datum-Ordner sortiert!)
│   │   ├── 2026-04-20/   # Videos vom 20. April
│   │   ├── 2026-04-21/   # Videos vom 21. April
│   │   └── ...
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
→ Download starten
→ Destination: bulk/
→ Subfolder: bulk_balanced (auto-vorgeschlagen)
→ Limit: 5000

# Downloads landen direkt in: sorted/bulk/bulk_balanced/
```

**Charakteristik:**
- Hohe Menge wichtiger als Perfektion
- Quality-Filter: `-ai_generated -low_quality -duplicate`
- Keine manuelle Review
- Auto-Destination via Tag-Builder

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
→ Download starten
→ Destination: favorites/
→ Subfolder: cute_pink_lingerie (auto-vorgeschlagen)
→ Limit: 100

# Downloads landen direkt in: sorted/favorites/cute_pink_lingerie/

# Optional: Review im Browser/Viewer
# Schlechte löschen, Beste behalten
```

**Charakteristik:**
- Qualität > Quantität
- Score-Filter aktiv
- Optional: Manuelle Review/Curation
- Auto-Destination + thematische Subfolder

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

## Auto-Sort vs Direct Download

**Zwei Wege:**

### 1. Direct Download (via Tag-Builder)
```bash
# Tag-Builder wählt Destination automatisch
→ Downloads gehen direkt nach sorted/bulk/ oder sorted/favorites/
→ Mit Subfolder für Organisation
→ KEIN auto-sort.py nötig
```

### 2. Incoming + Auto-Sort (Link Monitor, experimentell)
```bash
# Downloads landen in incoming/
→ auto-sort.py sortiert nach Typ (images/gifs/videos)
→ Manuell curate → bulk/ oder favorites/
```

**Empfehlung:**
- **Tag-Builder:** Direct download (bulk/favorites) ✅
- **Link Monitor:** incoming → manuell sortieren
- **auto-sort.py:** Nur für Dateityp-Sortierung (images/gifs/videos)

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
