# 📁 Video Categories

## Ordnerstruktur

```
sorted/videos/
├── 2026-04-20/           # Auto-Sort: Nach Datum
├── 2026-04-21/
├── ...
├── anal/                 # Manuelle Kategorien
├── blowjob/
├── cum/
├── cumshot/
├── deepthroat/
├── dick/
├── dildo/
├── feminization/
├── gangbang/
├── joi/
├── makeup/
├── oral/
├── pov/
├── sissy/
├── sissytraining/
├── solo/
├── toys/
└── uncategorized/
```

## Setup

**Kategorien erstellen:**
```bash
# Alle Ordner auf einmal anlegen
python scripts/setup-video-folders.py
```

## Workflow

### Auto-Sort (Standard)
```
Download → incoming/ → Auto-Sort → videos/2026-04-20/
```

Videos landen erstmal in Datum-Ordner. Gut für:
- Schnellen Überblick (was hab ich heute geholt?)
- Bulk-Downloads
- Später manuell kategorisieren

### Manuelle Kategorisierung
```
videos/2026-04-20/video.mp4 → videos/cum/video.mp4
```

Verschiebe Videos manuell in passende Kategorien:
- Präzise Organisation
- Schnelles Finden später
- Themed Collections

## Kategorien

| Ordner | Inhalt |
|--------|--------|
| `anal/` | Anal content |
| `blowjob/` | Blowjob scenes |
| `cum/` | Cum focus |
| `cumshot/` | Cumshots |
| `deepthroat/` | Deepthroat |
| `dick/` | Dick focus |
| `dildo/` | Dildo/toy play |
| `feminization/` | Feminization content |
| `gangbang/` | Group scenes |
| `joi/` | JOI (Jerk-Off Instructions) |
| `makeup/` | Makeup tutorials/focus |
| `oral/` | Oral content (general) |
| `pov/` | POV perspective |
| `sissy/` | Sissy content (general) |
| `sissytraining/` | Training/hypno |
| `solo/` | Solo performances |
| `toys/` | Toys/accessories |
| `uncategorized/` | Noch nicht sortiert |

## Hybrid-Ansatz

**Best of both:**
1. Auto-Sort lädt in Datum-Ordner (schnell, automatisch)
2. Du verschiebst Highlights in Kategorien (gezielt, manuell)
3. Datum-Ordner = temporär, Kategorien = dauerhaft

**Beispiel:**
```
# Download 50 Videos
→ videos/2026-04-20/ (alle 50)

# Die besten 5 verschieben
→ videos/cum/best1.mp4
→ videos/sissy/best2.mp4
→ videos/joi/best3.mp4

# Rest bleibt in 2026-04-20/ (Bulk-Material)
```

## Erweitern

Weitere Kategorien hinzufügen:
```bash
mkdir sorted/videos/NEUE_KATEGORIE
```

Oder `setup-video-folders.py` editieren + neu ausführen.
