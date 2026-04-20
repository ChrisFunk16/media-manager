# Media Manager Config

## config.json

Die `config.json` erlaubt dir, die Medien-Pfade anzupassen. Standard-Verhalten: Alles im Script-Ordner.

### Optionen

```json
{
  "media_base_dir": null,      // Hauptpfad für Medien (null = script dir)
  "incoming": "incoming",       // Name des incoming-Ordners
  "sorted": "sorted"            // Name des sorted-Ordners
}
```

**Wichtig:** 
- Scripts bleiben IMMER im Original-Ordner (wo `media-manager.py` liegt)
- Link-Files (`links.txt`, `urls.txt`, `processed/`) bleiben auch im Script-Ordner
- Nur Medien (`incoming/`, `sorted/`) werden nach `media_base_dir` verschoben

### Beispiel: Schnellere Festplatte

```json
{
  "media_base_dir": "D:/Media",
  "incoming": "incoming",
  "sorted": "sorted"
}
```

Das verschiebt alle Medien nach `D:/Media/`, während die Scripts im Original-Ordner bleiben.

### Struktur

Mit `media_base_dir` gesetzt:
```
D:/Media/                    (Schnelle Festplatte - nur Medien!)
  ├─ incoming/
  └─ sorted/
      ├─ images/
      ├─ gifs/
      ├─ videos/              (Videos in Datum-Unterordner!)
      │   ├─ 2026-04-20/
      │   ├─ 2026-04-21/
      │   └─ ...
      └─ hypno/

[Original-Ordner]/           (Scripts + Config + Link-Files!)
  ├─ scripts/
  ├─ media-manager.py
  ├─ config.json
  ├─ mm.bat
  ├─ tag-presets.json
  ├─ links.txt                 (Link Monitor speichert hier)
  └─ processed/                (Archiv für verarbeitete Links)
```

### Hinweise

- **Pfade:** Windows = `D:/Media` oder `D:\\Media`, Linux/Mac = `/mnt/ssd/media`
- **Tilde:** `~/media` wird zu deinem Home-Dir expandiert
- **Scripts:** Bleiben IMMER im Original-Ordner (werden nicht verschoben)
- **Nach Änderung:** Media Manager neu starten

### Troubleshooting

**Fehler: "incoming/ nicht gefunden"**
→ Ordner manuell erstellen: `mkdir D:\Media\incoming D:\Media\sorted`
