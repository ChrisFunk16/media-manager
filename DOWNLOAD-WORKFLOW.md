# 📥 Download Workflow - Komplettanleitung

## Übersicht

```
Tag-Builder → URL generieren
    ↓
Destination wählen (bulk/favorites/incoming)
    ↓
Subfolder-Name (automatisch vorgeschlagen)
    ↓
Download → sorted/DEST/SUBFOLDER/
```

---

## 1️⃣ Bulk-Downloads (Masse für Videos)

**Use-Case:** 5,000-10,000 Bilder für schnelle Video-Cuts

### Schritt-für-Schritt

```bash
# 1. Tag-Builder starten
cd media-collection
python3 scripts/tag-builder.py

# 2. Quick Preset wählen
→ 2 (Quick Presets)
→ 1 (Bulk - Balanced)

# 3. Download starten
→ d (Download)

# 4. Konfiguration
Zielordner: 2 (bulk/)
Unterordner: [Enter] (nutzt Vorschlag: "bulk_balanced")
Limit: 5 (5000 Bilder)

# 5. Bestätigen
→ y (Fortfahren)
```

**Ergebnis:**
```
sorted/bulk/bulk_balanced/
├── image001.jpg
├── image002.jpg
├── ...
└── image5000.jpg
```

---

## 2️⃣ Favorites (Handverlesene Qualität)

**Use-Case:** 100-500 Bilder für spezifische Szenen/Moods

### Beispiel: Makeup Close-Ups

```bash
# 1. Tag-Builder → Tag-Builder (Schritt-für-Schritt)
→ 1 (Tag-Builder)

# 2. Tags wählen
Base: 1 (sissy)
Style: -anime (EXCLUDE anime)
Mood: skip
Action: skip
Outfit: 13 (makeup) + 14 (lipstick)
Body: 10 (close-up)
Quality: 1 (high_resolution) + 3 (score:>20)

# 3. Preview checken
→ p (Preview)
# Zeigt: ~200-500 Posts geschätzt

# 4. Download starten
→ d (Download)

# 5. Konfiguration
Zielordner: 3 (favorites/)
Unterordner: makeup_closeup [Enter]
Limit: 2 (100 Bilder)

# 6. Bestätigen
→ y
```

**Ergebnis:**
```
sorted/favorites/makeup_closeup/
├── high_quality_1.jpg
├── high_quality_2.jpg
├── ...
└── high_quality_100.jpg
```

---

## 3️⃣ Default (Incoming für manuelle Sortierung)

**Use-Case:** Link Monitor, experimentelle Downloads

### Via Link Monitor

```bash
# Link Monitor läuft (sammelt Links in links.txt)
python3 scripts/link-monitor.py

# Batch-Download (geht automatisch nach incoming/)
python3 batch-download.py

# Manuell sortieren
# Gute Bilder → favorites/
# Bulk → bulk/
# Rest → delete oder images/
```

### Via Tag-Builder (Default)

```bash
# Tag-Builder → Download
Zielordner: 1 (incoming/)  # Default
# Kein Subfolder bei incoming

# Später manuell sortieren
mv incoming/good/* sorted/favorites/my_collection/
mv incoming/bulk/* sorted/bulk/misc/
```

---

## 🗂️ Folder-Struktur Beispiele

### Bulk (nach Presets organisiert)

```
sorted/bulk/
├── sissy_general/         # Bulk-Preset: sissy+femboy
├── femboy_cute/           # Bulk-Preset: femboy+cute
├── real_only/             # Bulk-Preset: -anime-cartoon
├── mixed_20260419/        # Nach Datum
└── experimental/          # Test-Downloads
```

**Strategie:**
- Preset-Name = Ordnername
- Oder nach Datum/Thema
- Deduplizierung VOR Video-Erstellung

### Favorites (nach Themes)

```
sorted/favorites/
├── makeup_closeup/        # Spezifisch
├── pink_cute/             # Mood-basiert
├── bdsm_dominant/         # Action-basiert
├── lingerie_stockings/    # Outfit-basiert
├── transformation/        # Story-basiert
└── misc/                  # Einzelfunde, Link Monitor
```

**Strategie:**
- Tag-Combo = Ordnername
- Kleinere Mengen (100-500)
- Hohe Qualität (score:>10/20)
- Deduplizierung NACH Curation

---

## 🔄 Kompletter Workflow (Bulk)

```bash
# 1. Tag-Builder: Preset erstellen
python3 scripts/tag-builder.py
→ Quick Presets → "Bulk - Balanced"
→ Download → bulk/sissy_general/ (5000 Bilder)

# 2. Warten... (~10-20 Min je nach Speed)

# 3. Deduplizieren
python3 scripts/deduplicate.py
→ sorted/bulk/sissy_general
→ Threshold: 5 (normal)
→ Entfernen

# Ergebnis: ~4000 Bilder (20% Dupes entfernt)

# 4. Video-Editing (kommt noch)
# → Nutze sorted/bulk/sissy_general/ als Source
```

---

## 🎨 Kompletter Workflow (Favorites)

```bash
# 1. Tag-Builder: Spezifische Combo
python3 scripts/tag-builder.py
→ Tag-Builder (Schritt-für-Schritt)
→ Tags wählen: sissy + cute + pink + high_resolution
→ Preview: ~500 Posts
→ Download → favorites/cute_pink/ (100 Bilder)

# 2. Manuelle Review (optional)
# Im File Explorer durchsehen
# Schlechte löschen, Beste behalten

# 3. Deduplizieren (strict)
python3 scripts/deduplicate.py
→ sorted/favorites/cute_pink
→ Threshold: 3 (strict, behält auch leicht unterschiedliche)
→ Entfernen

# Ergebnis: ~80-90 Bilder, handverlesen, dedupliziert

# 4. Nutzen für Video
# → Key frames, wichtige Szenen
```

---

## 📋 Checkliste: Bulk-Download

- [ ] Tag-Builder: Preset wählen/erstellen
- [ ] Destination: **bulk/**
- [ ] Subfolder: Aussagekräftiger Name
- [ ] Limit: 1000-5000 (je nach Bedarf)
- [ ] Download starten
- [ ] ☕ Warten...
- [ ] Deduplizieren (Threshold 5)
- [ ] Fertig für Video-Editing

## 📋 Checkliste: Favorites

- [ ] Tag-Builder: Spezifische Tags
- [ ] Preview checken (ca. Anzahl)
- [ ] Destination: **favorites/**
- [ ] Subfolder: Theme-Name (z.B. "makeup_closeup")
- [ ] Limit: 100-500
- [ ] Download starten
- [ ] Optional: Manuell review
- [ ] Deduplizieren (Threshold 3)
- [ ] Fertig für gezielte Nutzung

---

## 🛠️ Kommandozeilen-Optionen

### Media-Downloader (direkt nutzen)

```bash
# Bulk mit Subfolder
python3 scripts/media-downloader.py \
  --dest bulk \
  --subfolder sissy_custom \
  'https://rule34.xxx/...'

# Favorites
python3 scripts/media-downloader.py \
  --dest favorites \
  --subfolder makeup_closeup \
  'https://rule34.xxx/...'

# Default (incoming)
python3 scripts/media-downloader.py \
  'https://reddit.com/r/wallpapers'
```

---

## ❓ FAQ

**Q: Kann ich mehrere Bulk-Downloads parallel machen?**
A: Ja, unterschiedliche Subfolder nutzen:
   - bulk/preset1/
   - bulk/preset2/

**Q: Wohin gehen Link-Monitor Downloads?**
A: Standard: incoming/ (dann manuell sortieren)

**Q: Kann ich Subfolder später umbenennen?**
A: Ja, einfach im File Explorer (kein Problem)

**Q: Was wenn Subfolder schon existiert?**
A: Neue Downloads werden hinzugefügt (merge)

**Q: Bulk oder Favorites - Welche Tags?**
A: 
- **Bulk:** Basis-Tags (sissy+femboy), Quality-Exclusions
- **Favorites:** Spezifisch (mood+outfit+quality)

**Q: Wie viele Bilder für 10min Video?**
A: ~9,000 bei 30fps (alle 2 Frames = neues Bild)

---

## 🚀 Next Steps

Nach Download:
1. ✅ Bilder in sorted/bulk/ oder sorted/favorites/
2. → Deduplizierung laufen lassen
3. → Video-Editing-Workflow (kommt noch)
4. → Optional: Weitere Presets/Themes sammeln
