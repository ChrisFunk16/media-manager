# Link Monitor

Automatische Überwachung der Zwischenablage für Links.

## Installation

Benötigt `xclip`:

```bash
sudo apt install xclip
```

## Nutzung

### Über Media Manager

```bash
./media-manager.py
# Dann Option "l" wählen
```

### Direkt starten

```bash
./scripts/link-monitor.py
```

## Wie es funktioniert

1. **Monitor läuft im Hintergrund** und überwacht die Zwischenablage
2. **Kopierst du einen Link** (Strg+C oder Maus-Markierung)
3. **Wird automatisch in `links.txt` gespeichert**
4. **Duplikate werden übersprungen**

## Features

- ✅ Erkennt http/https URLs automatisch
- ✅ Speichert mit Timestamp
- ✅ Vermeidet Duplikate
- ✅ Funktioniert mit Strg+C UND Maus-Markierung
- ✅ Keine manuelle Eingabe nötig!

## Beispiel Output

```
🔍 Link Monitor gestartet
📝 Speichert in: /home/user/.../media-collection/links.txt
💾 Bereits 42 Links vorhanden

⌛ Überwache Zwischenablage... (Strg+C zum Beenden)

✅ [2026-04-19 10:55:32] Link gespeichert: https://reddit.com/r/pics
✅ [2026-04-19 10:56:01] Link gespeichert: https://twitter.com/user/status/123
```

## Tipps

- **Im Hintergrund laufen lassen** während du browsest
- **Neue Terminal-Instanz** für andere Aufgaben öffnen
- **Beenden mit Strg+C**
- Links können dann mit dem Media Downloader verarbeitet werden
