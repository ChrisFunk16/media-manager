# 🏗️ Tag Builder - Quick Guide

## Start

```bash
cd media-collection
python3 scripts/tag-builder.py
```

## Features

### 1️⃣ Tag-Builder (Interaktiv)
Schritt-für-Schritt durch Kategorien:
- **Base** (sissy/femboy/trap) - REQUIRED
- **Style** (real/anime/3d + Exclusions)
- **Mood** (cute/dominant/submissive)
- **Action** (solo/transformation/bdsm)
- **Outfit** (lingerie/maid/heels)
- **Body** (ass/thighs/hair)
- **Quality** (score/resolution + Exclusions)
- **Hypno** (spiral/text/trance)

### 2️⃣ Quick Presets
8 vordefinierte Kombos:
- Bulk - Balanced
- Bulk - Real Only
- Cute & Soft
- Dominant BDSM
- Transformation
- Outfit Focus
- High Quality
- Hypno Specific

## Workflow

### Bulk-Download Vorbereitung
```
1. Tag-Builder starten
2. Base: sissy + femboy
3. Style: -ai_generated + -low_quality
4. Quality: -duplicate
5. Preview → zeigt URL + geschätzte Anzahl
6. Save as Preset: "bulk_balanced"
7. Download starten (Limit: 5000)
```

### Präzise Suche
```
1. Quick Preset wählen (z.B. "Cute & Soft")
2. Preview → URL checken
3. Im Browser öffnen → Sample ansehen
4. Wenn gut → Download (Limit: 100)
5. Save as Custom Preset für später
```

## Tag-Logik

### AND (Kombination)
```
sissy+pink+lingerie
```
= Alle 3 Tags müssen vorhanden sein

### NOT (Ausschluss)
```
sissy+pink-anime
```
= Sissy UND Pink OHNE Anime

### Score-Filter
```
score:>10   → Bewertung höher als 10
score:>20   → Top-rated
```

## Preset-System

### Speichern
Im Tag-Builder: `s` drücken → Name eingeben

### Verwenden
**In Media Manager:**
```
Option 2 (Rule34 Download)
→ 3 (From Preset)
→ Preset-Name eingeben
```

**In Tag-Builder:**
Gespeicherte Presets erscheinen automatisch

### Preset-Datei
Gespeichert in: `tag-presets.json`
```json
{
  "presets": {
    "bulk_balanced": ["sissy", "femboy", "-ai_generated"],
    "cute": ["sissy", "cute", "pink"]
  }
}
```

## Tipps

### Für Masse (9k+ Bilder)
- Base: sissy+femboy (kombiniert ~470k Posts)
- Exclusions: -ai_generated -low_quality -duplicate
- Score: NICHT verwenden (reduziert zu stark)
- Limit: 5000-10000

### Für Qualität
- Base: sissy
- Score: score:>20
- Quality: high_resolution + uncensored
- Style: -anime (wenn Real bevorzugt)
- Limit: 100-500

### Für Spezifische Szenen
- Base: sissy
- Mood: 1-2 Tags (z.B. cute+innocent)
- Outfit: 1-2 Tags (z.B. lingerie+stockings)
- Body: Optional (z.B. close-up für Detailshots)
- Limit: 50-100

## Geschätzte Anzahlen

Tag-Builder zeigt Schätzung:
- **< 100**: Zu restriktiv
- **100-1k**: Gut für präzise Suche
- **1k-10k**: Ausreichend Material
- **> 10k**: Perfekt für Bulk

⚠️ Schätzung ist heuristisch - im Browser checken für genaue Zahl!

## Integration mit Media Manager

Tag-Builder erstellt Presets → Media Manager verwendet sie:

```
Tag-Builder (Presets erstellen)
    ↓
tag-presets.json
    ↓
Media Manager (Presets verwenden)
    ↓
Download
```

## Troubleshooting

### "Keine Tags ausgewählt"
→ Mindestens 1 Base-Tag wählen (sissy/femboy/trap)

### "Zu wenige Ergebnisse"
→ Weniger Tags kombinieren oder Exclusions reduzieren

### "Download startet nicht"
→ Erst gallery-dl installieren (Media Manager macht das automatisch)

### "Preset nicht gefunden"
→ In Media Manager: Exakter Name aus tag-presets.json verwenden

## Beispiel-Session

```
$ python3 scripts/tag-builder.py

Hauptmenü:
  1 - Tag-Builder
  2 - Quick Presets
Auswahl: 2

Quick Presets:
  1. Bulk - Balanced (sissy, femboy, -ai_generated, -low_quality)
  2. Cute & Soft (sissy, cute, pink, innocent)
Auswahl: 1

Optionen:
  p - Preview
  d - Download
  s - Save
Auswahl: p

Preview:
Tags: sissy femboy -ai_generated -low_quality
~180,000 Posts (geschätzt)
✅ VIEL - gut für Bulk-Download

Auswahl: s
Preset-Name: my_bulk
✅ Preset 'my_bulk' gespeichert!
```

## Next Steps

Nach Tag-Builder:
1. ✅ Presets erstellt
2. → Media Manager nutzen für Download
3. → Auto-Sort für Organisation
4. → Deduplizierung (kommt noch)
5. → Video-Editing
