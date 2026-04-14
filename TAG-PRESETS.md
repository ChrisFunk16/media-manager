# Tag-Presets Guide

Speichere deine Lieblings-Tag-Kombinationen und teste verschiedene Mixes!

## 📚 Konzept

**Presets:** Benannte Tag-Listen für schnellen Zugriff
```json
{
  "favorite1": ["tag1", "tag2", "tag3"],
  "favorite2": ["tag4", "tag5"]
}
```

**Mixes:** Kombiniere Presets + eigene Tags
```
favorite1 + favorite2 + custom_tag
→ tag1, tag2, tag3, tag4, tag5, custom_tag
```

## 🎮 Usage

### Preset erstellen

1. `./mm` starten
2. `8` - Tag-Presets verwalten
3. `1` - Preset hinzufügen
4. Name eingeben (z.B. "favorite1")
5. Tags eingeben (Leerzeichen-getrennt)

### Preset verwenden

**Option A: Einzelnes Preset**
1. `./mm` → `2` (Rule34)
2. `3` - From Preset
3. Preset-Name eingeben

**Option B: Mix**
1. `./mm` → `2` (Rule34)
2. `4` - Mix Presets
3. Mehrere Presets/Tags eingeben (z.B. "favorite1 favorite2 custom_tag")

### Preset bearbeiten/löschen

1. `./mm` → `8`
2. `2` - Löschen oder `3` - Bearbeiten
3. Preset-Name eingeben

## 💡 Beispiele

### Preset anlegen
```
Name: catgirl
Tags: catgirl ears tail
```

### Preset verwenden
```
Rule34 Download → From Preset → catgirl
→ Sucht: catgirl+ears+tail
```

### Mix erstellen
```
Rule34 Download → Mix Presets → catgirl anime 1girl
→ Sucht: catgirl+ears+tail+anime+1girl
```

### Spontane Variation
```
Rule34 Download → Mix Presets → catgirl solo rating:safe
→ Sucht: catgirl+ears+tail+solo+rating:safe
```

## 📝 Tipps

**Preset-Namen:**
- Kurz & prägnant (z.B. "neko", "mecha", "landscape")
- Keine Leerzeichen (benutze underscore: "sci_fi")

**Tag-Organisation:**
- Basis-Presets: Breite Kategorien (z.B. "anime", "3d", "western")
- Spezifische Presets: Nischen (z.B. "catgirl_blue_hair")
- Mix für Experimente: Kombiniere mehrere Basis-Presets

**Testing-Workflow:**
1. Preset erstellen
2. Download (wenige Results testen)
3. Preset anpassen wenn nötig
4. Mix für Variationen

## 🗂️ Storage

Presets werden in `tag-presets.json` gespeichert:
```json
{
  "presets": {
    "catgirl": ["catgirl", "ears", "tail"],
    "mecha": ["mecha", "robot", "sci-fi"]
  },
  "mixes": {}
}
```

Kannst du auch manuell editieren!
