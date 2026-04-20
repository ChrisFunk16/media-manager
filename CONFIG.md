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

**Hinweis:** Scripts bleiben IMMER im Original-Ordner, nur die Medien werden verschoben.

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
D:/Media/                    (Schnelle Festplatte)
  ├─ incoming/
  ├─ sorted/
  │   ├─ images/
  │   ├─ gifs/
  │   ├─ videos/
  │   └─ hypno/
  ├─ tag-presets.json
  └─ links.txt

[Original-Ordner]/           (Scripts bleiben hier!)
  ├─ scripts/
  ├─ media-manager.py
  ├─ config.json
  └─ mm.bat
```

### Hinweise

- **Pfade:** Windows = `D:/Media` oder `D:\\Media`, Linux/Mac = `/mnt/ssd/media`
- **Tilde:** `~/media` wird zu deinem Home-Dir expandiert
- **Scripts:** Bleiben IMMER im Original-Ordner (werden nicht verschoben)
- **Nach Änderung:** Media Manager neu starten

### Troubleshooting

**Fehler: "incoming/ nicht gefunden"**
→ Ordner manuell erstellen: `mkdir D:\Media\incoming D:\Media\sorted`
