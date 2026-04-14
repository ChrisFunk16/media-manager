# 📦 Media Manager

Interactive CLI tool for downloading and organizing media from multiple sources.

## ✨ Features

- 📥 **Multi-Source Downloads**
  - Reddit (subreddits, posts, users)
  - Rule34.xxx (posts, tag searches)
  - Redgifs (GIFs, users, searches)
  - Twitter/X (tweets, timelines, media, likes)
  - 100+ other sites via gallery-dl
  
- 🏷️ **Tag Preset System**
  - Save favorite tag combinations
  - Mix multiple presets + custom tags
  - Perfect for testing different tag combinations
  
- 📦 **Auto-Sort**
  - Automatic file type detection
  - Sorts images/videos/GIFs into organized folders
  - Handles duplicates automatically
  
- 🎬 **WebM → MP4 Converter**
  - Batch convert all .webm videos to .mp4
  - Optional: Keep or delete originals
  - Requires ffmpeg (auto-checked)
  
- 🎨 **Interactive CLI**
  - Colorful menu interface
  - No long commands to remember
  - Built-in stats and browsing

## 🚀 Quick Start

**Linux/Mac:**
```bash
# Clone the repo
git clone https://github.com/ChrisFunk16/media-manager.git
cd media-manager

# Create data folders
mkdir -p incoming sorted/{images,gifs,videos,hypno}

# Run it!
./mm
```

**Windows:**
```cmd
# Clone the repo
git clone https://github.com/ChrisFunk16/media-manager.git
cd media-manager

# Create data folders
mkdir incoming
mkdir sorted\images sorted\gifs sorted\videos sorted\hypno

# Run it!
mm.bat
```

That's it! The tool will auto-install `gallery-dl` when you first download something.

## 📖 Usage

**Interactive Menu:**
```bash
# Linux/Mac
./mm

# Windows
mm.bat
```

**Menu options:**
```
1 - Download (Reddit)
2 - Download (Rule34.xxx)
3 - Download (Redgifs)
4 - Download (Twitter/X)
5 - Download (Custom URL)
6 - Auto-Sort
7 - WebM → MP4 Convert
8 - Browse Sorted Files
9 - Stats
0 - Tag-Presets
q - Quit
```

**Batch Download (Multiple URLs):**

1. Create `urls.txt` with one URL per line:
   ```
   https://reddit.com/r/wallpapers
   https://redgifs.com/watch/somegif
   https://rule34.xxx/...
   ```

2. Run batch downloader:
   ```bash
   # Linux/Mac
   python3 batch-download.py
   
   # Windows
   batch.bat
   ```

Perfect for downloading many links at once!

## 🏷️ Tag Presets

Save frequently used tag combinations:

```bash
# Create a preset
./mm → 8 → Add Preset
Name: catgirl
Tags: catgirl ears tail

# Use it
./mm → 2 → From Preset → catgirl
# Downloads: catgirl+ears+tail

# Mix presets
./mm → 2 → Mix Presets → catgirl anime 1girl
# Downloads: catgirl+ears+tail+anime+1girl
```

See `TAG-PRESETS.md` for details.

## 📁 Structure

```
media-manager/
├── incoming/          # Drop files here (manual or downloaded)
├── sorted/
│   ├── images/       # Auto-sorted images (jpg, png, webp, etc.)
│   ├── gifs/         # Auto-sorted GIFs
│   ├── videos/       # Auto-sorted videos (mp4, m4v, webm, etc.)
│   └── hypno/        # Manual category
├── scripts/          # Backend tools
├── media-manager.py  # Main CLI
├── mm                # Quick launcher
└── tag-presets.json  # Your saved presets
```

## 🔧 Requirements

- Python 3.6+
- `gallery-dl` (auto-installed on first use)
- `ffmpeg` (optional, for WebM → MP4 conversion)

**Install ffmpeg:**
```bash
# Windows
winget install ffmpeg
# or download from: https://ffmpeg.org/download.html

# Linux
sudo apt install ffmpeg

# Mac
brew install ffmpeg
```

## 💡 Supported Sites

Via [gallery-dl](https://github.com/mikf/gallery-dl):
- Reddit (subreddits, posts, users)
- Rule34.xxx, Gelbooru, Danbooru (all Booru sites)
- Redgifs, Gfycat
- Twitter/X (tweets, timelines, media, likes)
- Instagram, Imgur, Tumblr
- DeviantArt, Pixiv
- 100+ more

Full list: https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md

## 📚 Documentation

- `USAGE.md` - Detailed usage guide
- `TAG-PRESETS.md` - Tag preset system explained
- `README.md` - Quick reference

## 🤝 Contributing

PRs welcome! Ideas for improvements:
- Auto-watch incoming folder (inotify)
- Keyword-based sorting (hypno detection)
- Multi-threaded downloads
- Download queue system

## 📝 License

MIT

## ⚠️ Disclaimer

This tool is for personal use. Respect the terms of service of the sites you download from.
