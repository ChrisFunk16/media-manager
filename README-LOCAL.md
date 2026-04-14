# Media Collection System

Organisiert Bilder & Videos automatisch.

## 🚀 Quick Start

**Einfachste Variante - Interaktives Menu:**

```bash
cd media-collection
./mm
```

Fertig! Alles weitere läuft über das Menu.

## 📁 Ordnerstruktur

```
media-collection/
├── incoming/          # Hier Files reinwerfen (manuell oder via Downloader)
├── sorted/
│   ├── images/       # Automatisch sortierte Bilder
│   ├── videos/       # Automatisch sortierte Videos
│   └── hypno/        # Für spezielle Medien (manuell)
├── scripts/          # Backend Tools
├── media-manager.py  # Interaktives CLI
└── mm                # Launcher (kurz)
```

## 🎮 Media Manager (Empfohlen!)

**Starten:**
```bash
cd media-collection
./mm
```

**Features:**
- 📥 Downloads (Reddit, Rule34.xxx, Redgifs, Custom URLs)
- 🏷️ Tag-Presets (Lieblings-Tags speichern & mixen)
- 📦 Auto-Sort (incoming → sorted)
- 📊 Stats & Browse
- Keine langen Commands mehr!

## 🔧 Manual Tools (Advanced)

### 1. Auto-Sortierer

Sortiert alle Files aus `incoming/` nach Typ:

```bash
cd media-collection
python3 scripts/auto-sort.py
```

**Was macht es:**
- Erkennt Bilder (.jpg, .png, .gif, .webp, etc.)
- Erkennt Videos (.mp4, .mkv, .mov, etc.)
- Verschiebt nach `sorted/images/` oder `sorted/videos/`
- Behandelt Duplikate automatisch (fügt _1, _2 hinzu)

**Tipp:** Du kannst das per Cron automatisieren (alle 5 Min):
```bash
*/5 * * * * cd /home/clawd/.openclaw/workspace/media-collection && python3 scripts/auto-sort.py
```

### 2. Media Downloader

Lädt Medien von verschiedenen Websites (Reddit, Rule34.xxx, Instagram, etc.):

```bash
cd media-collection
python3 scripts/media-downloader.py <URL>
```

**Beispiele:**
```bash
# Reddit - Einzelner Post
python3 scripts/media-downloader.py https://reddit.com/r/pics/comments/xyz123/

# Reddit - Ganzes Subreddit (Top 25 Posts)
python3 scripts/media-downloader.py https://reddit.com/r/wallpapers

# Rule34.xxx - Einzelner Post
python3 scripts/media-downloader.py https://rule34.xxx/index.php?page=post&s=view&id=12345

# Rule34.xxx - Tag Search (in Quotes wegen &-Zeichen)
python3 scripts/media-downloader.py 'https://rule34.xxx/index.php?page=post&s=list&tags=tag_name'

# Redgifs - Einzelnes GIF
python3 scripts/media-downloader.py https://redgifs.com/watch/uniquegifid

# Redgifs - User
python3 scripts/media-downloader.py https://redgifs.com/users/username

# Andere Sites (Instagram, Twitter, Imgur, Gelbooru, etc.)
python3 scripts/media-downloader.py <URL>
```

**Beim ersten Mal:** Installiert automatisch `gallery-dl` (fragt nach Bestätigung)

**Downloads landen in:** `incoming/` → Dann `auto-sort.py` laufen lassen

## 🎯 Workflow

1. **Download:** `media-downloader.py <URL>` → landet in `incoming/`
2. **Sortieren:** `auto-sort.py` → verschiebt nach `sorted/images|videos/`
3. **Hypno:** Manuell Dateien nach `sorted/hypno/` verschieben

## 💡 Erweiterungen

**Unterstützte Websites:** `gallery-dl` unterstützt 100+ Seiten:
- Reddit, Rule34.xxx, Instagram, Twitter, Imgur, DeviantArt, Tumblr, etc.
- Vollständige Liste: https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md

**Auto-Watch:** Incoming-Ordner automatisch überwachen (mit inotify):
```bash
# Todo: watch-script.py für automatisches Sortieren bei neuen Files
```

**Hypno-Erkennung:** Keywords in Dateinamen erkennen und automatisch sortieren
```bash
# Todo: Später hinzufügen wenn Patterns klar sind
```
