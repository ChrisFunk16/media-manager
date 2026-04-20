# Media Manager Config

## config.json

Die `config.json` erlaubt dir, die Medien-Pfade anzupassen. Standard-Verhalten: Alles im Script-Ordner.

### Optionen

```json
{
  "media_base_dir": null,      // Hauptpfad für Medien (null = script dir)
  "incoming": "incoming",       // Name des incoming-Ordners
  "sorted": "sorted",           // Name des sorted-Ordners
  "scripts": "scripts"          // Name des scripts-Ordners
}
```

### Beispiel: Schnellere Festplatte

```json
{
  "media_base_dir": "D:/Media",
  "incoming": "incoming",
  "sorted": "sorted",
  "scripts": "scripts"
}
```

Das verschiebt alle Medien nach `D:/Media/`, während die Scripts im Original-Ordner bleiben.

### Struktur

Mit `media_base_dir` gesetzt:
```
D:/Media/
  ├─ incoming/
  ├─ sorted/
  │   ├─ images/
  │   ├─ gifs/
  │   ├─ videos/
  │   └─ hypno/
  ├─ scripts/          (optional hier, oder im Original-Ordner)
  ├─ tag-presets.json
  └─ links.txt
```

### Hinweise

- **Pfade:** Windows = `D:/Media` oder `D:\\Media`, Linux/Mac = `/mnt/ssd/media`
- **Tilde:** `~/media` wird zu deinem Home-Dir expandiert
- **Scripts:** Bleiben im Original-Ordner, es sei denn du kopierst sie auch
- **Nach Änderung:** Media Manager neu starten

### Troubleshooting

**Fehler: "incoming/ nicht gefunden"**
→ Ordner manuell erstellen: `mkdir D:\Media\incoming D:\Media\sorted`

**Fehler: "scripts/ nicht gefunden"**
→ Entweder scripts kopieren oder `media_base_dir` auf `null` lassen
