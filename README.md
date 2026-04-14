# 📦 Media Manager

Interactive CLI tool for downloading and organizing media from multiple sources.

## ✨ Features

- 📥 **Multi-Source Downloads**
  - Reddit (subreddits, posts, users)
  - Rule34.xxx (posts, tag searches)
  - Redgifs (GIFs, users, searches)
  - 100+ other sites via gallery-dl
  
- 🏷️ **Tag Preset System**
  - Save favorite tag combinations
  - Mix multiple presets + custom tags
  - Perfect for testing different tag combinations
  
- 📦 **Auto-Sort**
  - Automatic file type detection
  - Sorts images/videos into organized folders
  - Handles duplicates automatically
  
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
mkdir -p incoming sorted/{images,videos,hypno}

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
mkdir sorted\images sorted\videos sorted\hypno

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
4 - Download (Custom URL)
5 - Auto-Sort
6 - Browse Sorted Files
7 - Stats
8 - Tag-Presets
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
│   ├── images/       # Auto-sorted images
│   ├── videos/       # Auto-sorted videos
│   └── hypno/        # Manual category
├── scripts/          # Backend tools
├── media-manager.py  # Main CLI
├── mm                # Quick launcher
└── tag-presets.json  # Your saved presets
```

## 🔧 Requirements

- Python 3.6+
- `gallery-dl` (auto-installed on first use)

## 💡 Supported Sites

Via [gallery-dl](https://github.com/mikf/gallery-dl):
- Reddit
- Rule34.xxx, Gelbooru, Danbooru, all Booru sites
- Redgifs, Gfycat
- Instagram, Twitter, Imgur
- DeviantArt, Tumblr, Pixiv
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
