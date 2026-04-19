# Tag-Strategien für Sissy Hypno Content

## Rule34.xxx Tag-Analyse

Basierend auf den 40k+ Posts mit `sissy` Tag.

---

## 🎯 BULK-DOWNLOAD Strategien (Masse)

### 1. Basis-Mix (breit, viel Material)
```
sissy+femboy+trap
```
**Erwartung:** ~500k+ Bilder (sissy 40k + femboy 433k + trap 120k)
**Vorteil:** Maximale Menge
**Nachteil:** Viel Anime/2D, Qualität variiert

### 2. Real/Photo Focus
```
sissy+crossdressing+photo
sissy+real_person
sissy+-anime+-cartoon+-3d
```
**Erwartung:** Weniger, aber mehr Real-Photos
**Vorteil:** Authentischer Look
**Nachteil:** Kleinere Menge

### 3. High-Quality Filter
```
sissy+high_resolution+uncensored
sissy+score:>10
```
**Erwartung:** Top-rated Posts
**Vorteil:** Bessere Qualität
**Nachteil:** Deutlich weniger Material

### 4. Mixed Quality (Balance)
```
sissy+femboy+-ai_generated+-low_quality
```
**Erwartung:** Gute Balance
**Vorteil:** Filtert Schrott, behält Masse
**Nachteil:** -

---

## 🎨 PRÄZISE SUCHE (Spezifische Szenen)

### Mood/Atmosphere Tags

#### 🌸 Soft/Cute
```
sissy+cute+pink+kawaii
sissy+soft+pastel
sissy+innocent+adorable
```
**Use-Case:** Sanfte Intro-Szenen, "awakening" moments

#### 🔥 Dominant/Intense
```
sissy+bdsm+dominant
sissy+leash+collar
sissy+chastity+cage
```
**Use-Case:** Power-dynamic Szenen, submission

#### 💄 Transformation/Makeup
```
sissy+makeup+lipstick
sissy+transformation+before_after
sissy+makeover+feminization
```
**Use-Case:** Verwandlungs-Sequenzen

#### 👗 Fashion/Outfit Focus
```
sissy+lingerie+stockings
sissy+maid+outfit
sissy+dress+heels
sissy+fishnet+thighhighs
```
**Use-Case:** Outfit-Fokus, Fashion-Cuts

#### 😳 Emotional States
```
sissy+blushing+embarrassed
sissy+ahegao+mindbreak
sissy+hypnotic+trance
sissy+submissive+obedient
```
**Use-Case:** Emotionale Reaktionen, Hypno-States

#### 🍑 Body Focus (NSFW)
```
sissy+big_ass+thick_thighs
sissy+flat_chest+feminine
sissy+small_penis+humiliation
sissy+anal+penetration
```
**Use-Case:** Body-Part Fokus für spezifische Cuts

---

## 🔍 KOMBINATIONS-PATTERNS

### AND-Logik (alle Tags müssen vorhanden sein)
```
sissy+pink+lingerie+makeup
```
= NUR Posts die ALLE 4 Tags haben

### OR-Logik (mit ~)
```
sissy ~femboy ~trap ~crossdressing
```
= Posts mit sissy ODER einem der anderen Tags
(⚠️ Nur auf manchen Boorus supported!)

### EXCLUSION (mit -)
```
sissy -anime -cartoon -furry -ai_generated
```
= Sissy OHNE diese Tags

### SCORE-Filter
```
sissy score:>20
sissy order:score
```
= Top-rated zuerst

---

## 💡 PRÄZISIONS-WORKFLOW

### Szenario: "Suche Bild für Lipstick-Close-Up"

**Strategie:**
```bash
1. Tag-Kombo: sissy+lipstick+close-up+lips
2. Sortierung: score:>10 (nur gute Quality)
3. Filter: -anime (nur Real)
4. Download: --range 1-20 (Top 20 checken)
```

**Media Manager Integration:**
```python
# Preset erstellen:
"lipstick_closeup": ["sissy", "lipstick", "close-up", "lips", "-anime"]

# Dann in Media Manager: Option 3 (From Preset)
```

---

## 🎬 HYPNO-VIDEO SPEZIFISCH

### Schnelle Cuts (alle 2 Frames)
**Braucht:** ~9,000 Bilder für 10min
**Strategie:** Bulk-Download Mix (Masse wichtiger als Perfektion)
```
sissy+femboy -ai_generated -low_quality
```

### Thematische Sequenzen
**Braucht:** 50-200 ähnliche Bilder pro Sequenz
**Strategie:** Präzise Tag-Kombos je Sequenz
```
Sequenz 1 (Intro):     sissy+cute+innocent
Sequenz 2 (Training):  sissy+bdsm+obedient
Sequenz 3 (Result):    sissy+confident+sexy
```

### Transition Frames
**Braucht:** Spezielle Bilder für Übergänge
**Strategie:**
```
sissy+spiral+hypnotic  (Hypno-Spiralen)
sissy+text+caption     (Text-Overlays)
sissy+glowing+eyes     (Trance-States)
```

---

## 📊 QUALITY TIERS

### Tier 1: Perfekt (manuell aussortiert)
- Score >20
- High resolution
- Professional quality
- **Use:** Key frames, important moments

### Tier 2: Gut (auto-filtered)
- Score >10
- -ai_generated -low_quality
- **Use:** Main content, 80% der Cuts

### Tier 3: Filler (Masse)
- Basis sissy tag
- Keine harten Exclusions
- **Use:** Schnelle Cuts wo Qualität egal

---

## 🛠️ TOOL-VORSCHLAG

### Tag-Kombinator Script

```python
# tag-builder.py
# Interaktiv Tags kombinieren + Preview
# Zeigt Anzahl Ergebnisse bevor Download

Kategorien:
1. Base (sissy/femboy/trap)
2. Style (real/anime/3d)
3. Mood (cute/dominant/submissive)
4. Body (ass/chest/legs)
5. Action (anal/oral/solo)
6. Quality (score, resolution)

Output: Finale URL + geschätzte Post-Anzahl
```

**Soll ich das bauen?**

---

## 🎯 KONKRETE EMPFEHLUNG

### Für Start:

**1. Bulk-Download (Basis-Material sammeln):**
```
sissy+femboy -ai_generated -low_quality
Limit: 5,000 Posts
```

**2. Präzisions-Presets erstellen** (für spätere gezielte Suchen):
```json
{
  "cute": ["sissy", "cute", "pink", "-anime"],
  "dominant": ["sissy", "bdsm", "leash"],
  "makeup": ["sissy", "makeup", "lipstick", "close-up"],
  "outfit": ["sissy", "lingerie", "stockings"],
  "body_focus": ["sissy", "big_ass", "thick_thighs", "-anime"]
}
```

**3. Tag-Builder Tool** für flexible Kombos

---

**Fragen:**
- Welche Mood/Themes sind dir wichtig? (cute, dominant, transformation, etc.)
- Lieber mehr Real oder mehr 2D/3D?
- Soll ich den Tag-Builder jetzt bauen?
