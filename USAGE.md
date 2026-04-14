# Usage Guide - Media Manager

## Schnellstart

```bash
cd media-collection
./mm
```

## Menu-Optionen

### 1️⃣ Download (Reddit)

Lädt von Reddit runter - einfach URL eingeben:

**Beispiele:**
- Subreddit: `https://reddit.com/r/wallpapers`
- Einzelner Post: `https://reddit.com/r/pics/comments/abc123/`
- User: `https://reddit.com/user/username`

### 2️⃣ Download (Rule34.xxx)

Fünf Modi:
- **Post ID:** Nur ID eingeben (z.B. `12345`)
- **Tag-Suche (manuell):** Tags mit Leerzeichen trennen (z.B. `tag1 tag2`)
- **From Preset:** Gespeicherte Tag-Kombination verwenden
- **Mix Presets:** Mehrere Presets + eigene Tags kombinieren
- **Custom URL:** Komplette URL einfügen

**Presets:** Siehe Option 8 (Tag-Presets verwalten) oder `TAG-PRESETS.md`

### 3️⃣ Download (Redgifs)

Vier Modi:
- **GIF ID:** Nur ID eingeben (z.B. `uniquegifid`)
- **User/Creator:** Username eingeben
- **Search/Tags:** Suchbegriff eingeben
- **Custom URL:** Komplette URL einfügen

### 4️⃣ Download (Twitter/X)

Fünf Modi:
- **Einzelner Tweet:** Tweet-URL einfügen
- **User Timeline:** Alle Tweets eines Users
- **User Media:** Nur Tweets mit Bildern/Videos
- **User Likes:** Gelikte Tweets eines Users
- **Custom URL:** Komplette URL einfügen

**Beispiel:**
```
Username: elonmusk
→ Lädt Timeline/Media/Likes
```

### 5️⃣ Download (Custom URL)

Für alle anderen Sites (Instagram, Imgur, DeviantArt, Gelbooru, Pixiv, etc.)

Einfach URL pasten - gallery-dl erkennt die Site automatisch.

### 6️⃣ Auto-Sort

Sortiert alle Files aus `incoming/` nach Typ:
- Bilder → `sorted/images/`
- GIFs → `sorted/gifs/`
- Videos → `sorted/videos/`

Zeigt Vorschau und fragt vor dem Sortieren.

### 7️⃣ Browse Sorted Files

Zeigt Anzahl der Files pro Kategorie + Pfad.

### 8️⃣ Stats anzeigen

Übersicht:
- Wie viele Files in `incoming/` warten
- Wie viele Files bereits sortiert sind (gesamt + pro Kategorie)

### 9️⃣ Tag-Presets verwalten

Speichere häufig verwendete Tag-Kombinationen:
- **Hinzufügen:** Neue Presets erstellen
- **Löschen:** Presets entfernen
- **Bearbeiten:** Bestehende Presets anpassen

**Beispiel:**
```
Preset "catgirl": catgirl ears tail
Preset "anime": anime 1girl solo
```

Dann in Rule34-Download:
- "From Preset" → catgirl
- "Mix Presets" → catgirl anime rating:safe

Details: `TAG-PRESETS.md`

## Workflow

**Typischer Ablauf:**

1. `./mm` starten
2. `1`, `2`, `3` oder `4` - Download von Reddit/Rule34/Redgifs/Twitter
3. `6` - Auto-Sort laufen lassen
4. `7` oder `8` - Checken was angekommen ist
5. Fertig!

**Hypno-Files:** Manuell nach `sorted/hypno/` verschieben (vorerst)

## Tipps

**Mehrere URLs hintereinander:**
- Erst alle Downloads machen (Option 1-3 mehrfach)
- Dann 1x Auto-Sort (Option 4)

**Cron für Auto-Sort:**
```bash
# Alle 5 Min automatisch sortieren
*/5 * * * * cd /path/to/media-collection && python3 scripts/auto-sort.py
```

**Duplikate:** Auto-Sort fügt automatisch `_1`, `_2` hinzu wenn Dateiname existiert.

## Backend Tools (für Scripts/Automation)

Falls du doch Commands brauchst:

```bash
# Download
python3 scripts/media-downloader.py <URL>

# Sort
python3 scripts/auto-sort.py
```
