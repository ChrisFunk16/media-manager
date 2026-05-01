#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI - Lokales Browser-Dashboard für den Media Manager
Aufruf: python webui.py [--port=5000]
"""

import json
import os
import sys
import hashlib
import shutil
import subprocess
import datetime
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

try:
    from flask import (Flask, render_template_string, request, send_file,
                       abort, jsonify, Response, stream_with_context)
except ImportError:
    print("Flask nicht installiert. Bitte ausführen:")
    print("  pip install flask")
    sys.exit(1)

BASE_DIR      = Path(__file__).parent.parent
CONFIG_FILE   = BASE_DIR / "config.json"
THUMB_CACHE   = BASE_DIR / '.thumbcache'
FAV_FILE      = BASE_DIR / 'favorites.json'
SESSIONS_FILE = BASE_DIR / 'sessions.json'

CATEGORIES = ['images', 'gifs', 'videos', 'hypno', 'audio']
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
GIF_EXTS   = {'.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.m4v'}
AUDIO_EXTS = {'.mp3', '.m4a', '.ogg', '.flac', '.wav', '.aac', '.opus', '.wma'}


def load_config():
    default = {"media_base_dir": None, "incoming": "incoming", "sorted": "sorted"}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
            for k, v in default.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception:
            pass
    return default


config       = load_config()
MEDIA_BASE   = Path(config['media_base_dir']).expanduser() if config['media_base_dir'] else BASE_DIR
SORTED       = MEDIA_BASE / config['sorted']
OUTBOX_DIR   = SORTED / 'outbox'
INCOMING_DIR = MEDIA_BASE / config['incoming']
SCRIPTS_DIR  = BASE_DIR / 'scripts'

app = Flask(__name__)
app.jinja_env.filters['url_path'] = lambda s: quote(str(s), safe='/')


@app.context_processor
def inject_globals():
    return {
        'outbox_count':    get_outbox_count(),
        'incoming_count':  get_incoming_count(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_file_type(path):
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS: return 'image'
    if ext in GIF_EXTS:   return 'gif'
    if ext in VIDEO_EXTS: return 'video'
    if ext in AUDIO_EXTS: return 'audio'
    return 'other'


def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_subcategories(category: str) -> list:
    cat_path = SORTED / category
    if not cat_path.exists():
        return []
    return sorted([d.name for d in cat_path.iterdir() if d.is_dir()])


def get_video_thumb(filepath: Path):
    THUMB_CACHE.mkdir(exist_ok=True)
    key   = hashlib.md5(str(filepath).encode()).hexdigest()
    thumb = THUMB_CACHE / f"{key}.jpg"
    if not thumb.exists() and filepath.exists():
        try:
            subprocess.run(
                ['ffmpeg', '-y', '-ss', '2', '-i', str(filepath),
                 '-vframes', '1', '-vf', 'scale=400:-1', '-q:v', '4', str(thumb)],
                capture_output=True, timeout=15
            )
        except Exception:
            return None
    return thumb if thumb.exists() else None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_favorites() -> set:
    if FAV_FILE.exists():
        try:
            return set(json.load(open(FAV_FILE, encoding='utf-8')))
        except Exception:
            pass
    return set()


def save_favorites(favs: set):
    with open(FAV_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted(favs), f, indent=2)


def load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            return json.load(open(SESSIONS_FILE, encoding='utf-8'))
        except Exception:
            pass
    return {}


def save_sessions(sessions: dict):
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Stats & search
# ---------------------------------------------------------------------------

def get_stats():
    stats = {}
    total_count = total_bytes = 0
    for cat in CATEGORIES:
        cat_path = SORTED / cat
        count = size = 0
        if cat_path.exists():
            for f in cat_path.rglob('*'):
                if f.is_file():
                    count += 1
                    try:
                        size += f.stat().st_size
                    except OSError:
                        pass
        stats[cat] = {'count': count, 'size_str': format_size(size)}
        total_count += count
        total_bytes += size
    outbox_count = sum(1 for f in OUTBOX_DIR.iterdir() if f.is_file()) if OUTBOX_DIR.exists() else 0
    stats['favorites'] = {'count': len(load_favorites()), 'size_str': ''}
    stats['sessions']  = {'count': len(load_sessions()),  'size_str': ''}
    stats['outbox']    = {'count': outbox_count,           'size_str': ''}
    stats['total']     = {'count': total_count, 'size_str': format_size(total_bytes)}
    return stats


def _build_item(f: Path, cat_name: str, favs: set):
    try:
        stat = f.stat()
    except OSError:
        return None
    rel = str(f.relative_to(SORTED)).replace('\\', '/')
    return {
        'name':      f.name,
        'category':  cat_name,
        'size_str':  format_size(stat.st_size),
        'size':      stat.st_size,
        'mtime':     stat.st_mtime,
        'date':      datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
        'type':      get_file_type(f),
        'rel_path':  rel,
        'favorited': rel in favs,
    }


def search_files(query='', category=None, subcat=None, sort='date', page=1, per_page=40):
    query = query.lower().strip()
    favs  = load_favorites()

    if category == 'favorites':
        results = []
        for rel in favs:
            f = SORTED / rel
            if not f.is_file():
                continue
            if query and query not in f.name.lower():
                continue
            item = _build_item(f, rel.split('/')[0], favs)
            if item:
                results.append(item)
    elif category == 'outbox':
        results = []
        if OUTBOX_DIR.exists():
            for f in sorted(OUTBOX_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if not f.is_file():
                    continue
                if query and query not in f.name.lower():
                    continue
                item = _build_item(f, 'outbox', favs)
                if item:
                    results.append(item)
    else:
        if category in CATEGORIES:
            base = (SORTED / category / subcat) if subcat else (SORTED / category)
            scan_dirs = [(base, category)]
        else:
            scan_dirs = [(SORTED / c, c) for c in CATEGORIES]

        results = []
        for search_dir, cat_name in scan_dirs:
            if not search_dir.exists():
                continue
            for f in search_dir.rglob('*'):
                if not f.is_file():
                    continue
                if query and query not in f.name.lower():
                    continue
                item = _build_item(f, cat_name, favs)
                if item:
                    results.append(item)

    if sort == 'size':
        results.sort(key=lambda x: x['size'], reverse=True)
    elif sort == 'name':
        results.sort(key=lambda x: x['name'].lower())
    else:
        results.sort(key=lambda x: x['mtime'], reverse=True)

    total = len(results)
    start = (page - 1) * per_page
    return results[start:start + per_page], total


def copy_to_outbox(rel_path: str) -> tuple:
    """Copy a file to OUTBOX_DIR. Returns (new_filename, error_str)."""
    try:
        src = (SORTED / rel_path).resolve()
        src.relative_to(SORTED.resolve())
    except (ValueError, Exception):
        return None, 'Ungültiger Pfad'
    if not src.is_file():
        return None, 'Datei nicht gefunden'
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    dst = OUTBOX_DIR / src.name
    if dst.exists():
        stem, suffix = src.stem, src.suffix
        for i in range(1, 1000):
            dst = OUTBOX_DIR / f"{stem}_{i}{suffix}"
            if not dst.exists():
                break
    shutil.copy2(str(src), str(dst))
    return dst.name, None


def get_outbox_count() -> int:
    if not OUTBOX_DIR.exists():
        return 0
    return sum(1 for f in OUTBOX_DIR.iterdir() if f.is_file())


def get_session_items(name: str) -> list:
    sessions = load_sessions()
    paths    = sessions.get(name, [])
    favs     = load_favorites()
    items    = []
    for rel in paths:
        f = SORTED / rel
        if f.is_file():
            cat  = rel.split('/')[0] if '/' in rel else ''
            item = _build_item(f, cat, favs)
            if item:
                items.append(item)
    return items


def get_incoming_count() -> int:
    if not INCOMING_DIR.exists():
        return 0
    return sum(1 for f in INCOMING_DIR.rglob('*') if f.is_file())


def list_incoming() -> list:
    if not INCOMING_DIR.exists():
        return []
    files = []
    for f in INCOMING_DIR.rglob('*'):
        if not f.is_file():
            continue
        try:
            st = f.stat()
            files.append({
                'name':     f.name,
                'rel_path': str(f.relative_to(INCOMING_DIR)).replace('\\', '/'),
                'type':     get_file_type(f),
                'size_str': format_size(st.st_size),
                'size':     st.st_size,
                'date':     datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d'),
                'mtime':    st.st_mtime,
            })
        except OSError:
            pass
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files


def load_tag_presets() -> dict:
    p = BASE_DIR / 'tag-presets.json'
    if p.exists():
        try:
            return json.load(open(p, encoding='utf-8'))
        except Exception:
            pass
    return {'presets': {}, 'mixes': {}}


def load_jobs_file() -> list:
    p = BASE_DIR / 'jobs.json'
    if p.exists():
        try:
            data = json.load(open(p, encoding='utf-8'))
            return data.get('jobs', [])
        except Exception:
            pass
    return []


def save_jobs_file(jobs: list):
    with open(BASE_DIR / 'jobs.json', 'w', encoding='utf-8') as f:
        json.dump({'jobs': jobs}, f, indent=2, ensure_ascii=False)


def _subprocess_env():
    """Return env with UTF-8 I/O so emoji in child scripts don't crash."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8:replace'
    return env


def _stream_subprocess(cmd: list):
    """Run cmd and yield SSE-formatted lines. Yields __DONE__ when finished."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=_subprocess_env(),
            cwd=str(BASE_DIR),
        )
        for line in proc.stdout:
            clean = line.rstrip()
            if clean:
                yield f"data: {clean}\n\n"
        proc.wait()
    except Exception as e:
        yield f"data: FEHLER: {e}\n\n"
    yield "data: __DONE__\n\n"


def _stream_subprocess_raw(cmd: list):
    """Like _stream_subprocess but no final __DONE__ (used mid-pipeline)."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=_subprocess_env(),
            cwd=str(BASE_DIR),
        )
        for line in proc.stdout:
            clean = line.rstrip()
            if clean:
                yield f"data: {clean}\n\n"
        proc.wait()
    except Exception as e:
        yield f"data: FEHLER: {e}\n\n"


def _stream_pipeline(steps: list):
    """Run list of (cmd, label) sequentially, yield SSE, final __DONE__."""
    for cmd, label in steps:
        yield f"data: \n\n"
        yield f"data: ━━━ {label} ━━━\n\n"
        yield from _stream_subprocess_raw(cmd)
    yield "data: __DONE__\n\n"


# ---------------------------------------------------------------------------
# Link-list helpers
# ---------------------------------------------------------------------------

LINKS_FILE = BASE_DIR / 'links.txt'

_monitor_proc = None  # background clipboard monitor process


def load_links() -> list:
    if not LINKS_FILE.exists():
        return []
    with open(LINKS_FILE, encoding='utf-8') as f:
        return [l.rstrip('\n') for l in f if l.strip() and not l.startswith('#')]


def save_links(links: list):
    with open(LINKS_FILE, 'w', encoding='utf-8') as f:
        for url in links:
            f.write(url + '\n')


def is_monitor_running() -> bool:
    global _monitor_proc
    if _monitor_proc is None:
        return False
    return _monitor_proc.poll() is None


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

TEMPLATE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Media Manager</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d12;color:#ddd;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}

/* ── Header ── */
header{background:#12121e;padding:10px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #1e1e36;position:sticky;top:0;z-index:200;min-width:0}
header h1{font-size:1rem;color:#8aacff;letter-spacing:1px;white-space:nowrap;flex-shrink:0}
nav{display:flex;gap:2px;flex-wrap:nowrap;overflow-x:auto;flex:1 1 0;min-width:0;scrollbar-width:none;-ms-overflow-style:none}
nav::-webkit-scrollbar{display:none}
nav a{color:#888;text-decoration:none;font-size:.78rem;padding:5px 10px;border-radius:6px;transition:all .15s;white-space:nowrap;flex-shrink:0}
nav a:hover,nav a.active{color:#8aacff;background:#1a1a30}
nav a.fav-link{color:#c06080}
nav a.fav-link:hover,nav a.fav-link.active{color:#ff6b8a;background:#2a1020}
nav a.outbox-link{color:#80b060}
nav a.outbox-link:hover,nav a.outbox-link.active{color:#a0d080;background:#162010}
.outbox-badge{display:inline-block;background:#a0d080;color:#0d1a08;border-radius:10px;padding:0 6px;font-size:.72rem;font-weight:700;margin-left:3px;vertical-align:middle}
.btn-outbox{background:#2a4020;border:1px solid #4a7030;color:#a0d080}
.btn-outbox:hover{background:#3a5828;color:#c0e090}
.outbox-bar{background:#141e10;border:1px solid #2a4020;border-radius:9px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;color:#6a9050;font-size:.85rem}

/* ── Layout ── */
.container{max-width:1700px;margin:0 auto;padding:24px 20px}

/* ── Stats ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:30px}
.stat-card{background:#12121e;border:1px solid #1e1e36;border-radius:10px;padding:16px;text-align:center;cursor:pointer;transition:border-color .2s,transform .15s}
.stat-card:hover{border-color:#8aacff;transform:translateY(-2px)}
.stat-num{font-size:1.9rem;font-weight:700;color:#8aacff}
.stat-label{color:#666;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.stat-size{color:#444;font-size:.72rem;margin-top:2px}
h2{color:#8aacff;margin-bottom:16px;font-size:1rem;letter-spacing:.5px}

/* ── Search bar ── */
.search-bar{background:#12121e;border:1px solid #1e1e36;border-radius:10px;padding:12px 16px;margin-bottom:10px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.search-bar input[type=text]{flex:1;min-width:160px;background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:7px 12px;color:#ddd;font-size:.875rem;outline:none;transition:border-color .2s}
.search-bar input:focus{border-color:#8aacff}
select{background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:7px 12px;color:#ddd;font-size:.875rem;cursor:pointer;outline:none}
.btn{background:#8aacff;color:#0d0d1a;border:none;border-radius:7px;padding:8px 18px;cursor:pointer;font-size:.875rem;font-weight:700;transition:background .15s;text-decoration:none;display:inline-block}
.btn:hover{background:#a8c4ff}
.btn-sm{padding:5px 12px;font-size:.78rem}
.btn-ghost{background:transparent;border:1px solid #2a2a45;color:#888}
.btn-ghost:hover{border-color:#8aacff;color:#8aacff}
.btn-danger{background:#8b2020;color:#fcc;border:none}
.btn-danger:hover{background:#a83030}

/* ── Subcategory chips ── */
.subcat-wrap{min-height:36px;margin-bottom:10px;overflow-x:auto;padding-bottom:2px}
.subcat-chips{display:flex;gap:7px;flex-wrap:nowrap}
.chip{background:#12121e;border:1px solid #2a2a45;border-radius:20px;padding:4px 14px;font-size:.78rem;color:#888;text-decoration:none;white-space:nowrap;transition:all .15s;cursor:pointer}
.chip:hover{border-color:#8aacff;color:#8aacff}
.chip.active{background:#8aacff;color:#0d0d1a;border-color:#8aacff;font-weight:700}

/* ── Results ── */
.results-info{color:#555;font-size:.8rem;margin-bottom:12px}
.results-info strong{color:#8aacff}

/* ── Media grid ── */
.media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.card{background:#12121e;border:1px solid #1e1e36;border-radius:9px;overflow:hidden;cursor:pointer;transition:transform .15s,border-color .15s;position:relative}
.card:hover{transform:translateY(-3px);border-color:#8aacff}
.card-thumb{position:relative;width:100%;aspect-ratio:1;background:#0a0a15;overflow:hidden}
.thumb{width:100%;height:100%;object-fit:cover;display:block}
.thumb-ph{width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:2.8rem;color:#2a2a45}
.audio-ph{background:linear-gradient(135deg,#12122a,#1a1a3a);color:#6a8aff;font-size:2.2rem}
.lb-audio{width:100%;max-width:560px;outline:none}
.audio-card-title{position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.7);padding:6px 8px;font-size:.7rem;color:#aaa;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* Overlay buttons */
.fav-btn,.sess-btn{position:absolute;top:6px;background:rgba(0,0,0,.6);border:none;border-radius:6px;padding:3px 8px;cursor:pointer;line-height:1.3;transition:background .15s;z-index:5}
.fav-btn{right:6px;font-size:1.1rem;color:#777}
.fav-btn:hover{background:rgba(0,0,0,.85);color:#ff6b8a}
.fav-btn.active{color:#ff6b8a}
.sess-btn{left:6px;font-size:1rem;color:#8aacff;font-weight:700}
.sess-btn:hover{background:rgba(0,0,0,.85)}

.card-body{padding:7px 10px}
.card-name{font-size:.72rem;color:#bbb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-meta{display:flex;justify-content:space-between;font-size:.67rem;color:#484848;margin-top:2px}
.card-cat{font-size:.64rem;color:#8aacff;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}

/* ── Pagination ── */
.pagination{display:flex;justify-content:center;gap:6px;margin-top:28px;flex-wrap:wrap}
.page-link{background:#12121e;border:1px solid #1e1e36;color:#888;padding:6px 13px;border-radius:7px;text-decoration:none;font-size:.8rem;transition:all .15s}
.page-link:hover{border-color:#8aacff;color:#8aacff}
.page-link.active{background:#8aacff;color:#0d0d1a;border-color:#8aacff;font-weight:700}

/* ── Lightbox ── */
.lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.95);z-index:9000;align-items:center;justify-content:center;flex-direction:column;padding:16px}
.lb.open{display:flex}
.lb-media{max-width:88vw;max-height:72vh;border-radius:8px;object-fit:contain}
.lb-close{position:fixed;top:12px;right:18px;font-size:1.7rem;color:#666;cursor:pointer;z-index:9001;background:none;border:none;line-height:1}
.lb-close:hover{color:#fff}
.lb-nav{position:fixed;top:50%;transform:translateY(-50%);font-size:2rem;color:#555;cursor:pointer;background:rgba(0,0,0,.4);border:none;padding:10px 14px;border-radius:8px;z-index:9001;transition:color .15s,background .15s;line-height:1}
.lb-nav:hover{color:#fff;background:rgba(0,0,0,.75)}
.lb-prev{left:8px}
.lb-next{right:8px}
.lb-caption{margin-top:8px;font-size:.77rem;color:#666;max-width:80vw;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lb-panel{margin-top:12px;background:#12121e;border:1px solid #1e1e36;border-radius:9px;padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;max-width:640px;width:100%}
.lb-panel label{color:#666;font-size:.78rem;white-space:nowrap}
.lb-panel select{padding:6px 10px;font-size:.82rem}

/* ── Session dropdown ── */
.sess-menu{display:none;position:fixed;background:#12121e;border:1px solid #2a2a45;border-radius:9px;z-index:9500;min-width:190px;box-shadow:0 8px 30px rgba(0,0,0,.7);overflow:hidden}
.sess-menu.open{display:block}
.sess-menu-item{display:block;width:100%;padding:9px 16px;background:none;border:none;color:#ccc;font-size:.82rem;text-align:left;cursor:pointer;transition:background .12s}
.sess-menu-item:hover{background:#1e1e36;color:#8aacff}
.sess-menu-new{color:#8aacff;border-top:1px solid #1e1e36}
.sess-menu hr{border:none;border-top:1px solid #1e1e36}
.sess-menu-empty{padding:9px 16px;color:#555;font-size:.82rem}

/* ── Sessions page ── */
.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:12px}
.new-sess-form{display:flex;gap:10px;margin-bottom:22px}
.new-sess-form input{flex:1;background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:8px 12px;color:#ddd;font-size:.875rem;outline:none;transition:border-color .2s;max-width:320px}
.new-sess-form input:focus{border-color:#8aacff}
.sess-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin-bottom:28px}
.sess-card{background:#12121e;border:1px solid #1e1e36;border-radius:9px;padding:18px;display:flex;flex-direction:column;gap:10px;transition:border-color .2s}
.sess-card:hover{border-color:#8aacff}
.sess-card-name{font-size:.95rem;color:#ddd;font-weight:600}
.sess-card-count{font-size:.78rem;color:#555}
.sess-card-actions{display:flex;gap:8px;margin-top:4px}

/* ── Slideshow ── */
.slideshow{display:none;position:fixed;inset:0;background:#000;z-index:9900;flex-direction:column;align-items:center;justify-content:center}
.slideshow.open{display:flex}
#ss-inner{display:flex;align-items:center;justify-content:center;flex:1;width:100%;overflow:hidden;padding:10px}
.ss-media{max-width:100%;max-height:calc(100vh - 72px);object-fit:contain}
.ss-controls{width:100%;background:rgba(0,0,0,.8);padding:10px 20px;display:flex;align-items:center;justify-content:center;gap:14px;flex-shrink:0}
.ss-controls button{background:#1e1e36;border:none;color:#ccc;padding:7px 16px;border-radius:7px;cursor:pointer;font-size:.85rem;transition:background .15s}
.ss-controls button:hover{background:#8aacff;color:#000}
.ss-counter{color:#888;font-size:.82rem;min-width:70px;text-align:center}
.ss-auto-label{color:#888;font-size:.82rem;display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}

/* ── Toast ── */
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(40px);background:#1a2240;border:1px solid #8aacff;color:#8aacff;padding:10px 22px;border-radius:8px;font-size:.85rem;opacity:0;transition:opacity .25s,transform .25s;pointer-events:none;z-index:9999;white-space:nowrap}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

/* ── Empty ── */
.empty{text-align:center;padding:60px 20px;color:#333}
.empty-icon{font-size:3.2rem;margin-bottom:12px}

/* ── Download / Sort / Scheduler ── */
.tool-section{background:#12121e;border:1px solid #1e1e36;border-radius:10px;padding:20px;margin-bottom:20px}
.form-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.form-row label{color:#666;font-size:.82rem;white-space:nowrap;min-width:60px}
.form-row input[type=text],.form-row select{background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:7px 12px;color:#ddd;font-size:.875rem;outline:none;transition:border-color .2s}
.form-row input[type=text]:focus,.form-row select:focus{border-color:#8aacff}
.form-row input.wide{flex:1;min-width:240px}
.log-wrap{margin-top:14px}
.log-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.log-header span{color:#666;font-size:.78rem;text-transform:uppercase;letter-spacing:.5px}
.log-terminal{background:#080810;border:1px solid #1e1e36;border-radius:8px;padding:14px;font-family:'Consolas','Courier New',monospace;font-size:.78rem;color:#a0c060;max-height:340px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
.log-terminal div{line-height:1.5}
.job-list{display:flex;flex-direction:column;gap:10px;margin-bottom:20px}
.job-row{background:#0d0d1a;border:1px solid #1e1e36;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.job-info{flex:1;min-width:180px}
.job-name{font-size:.9rem;color:#ddd;font-weight:600}
.job-url{font-size:.72rem;color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:340px;margin-top:2px}
.job-meta{font-size:.72rem;color:#8aacff;margin-top:3px}
.job-actions{display:flex;gap:7px;align-items:center;flex-shrink:0}
.toggle-btn{background:none;border:1px solid #2a2a45;border-radius:6px;padding:4px 10px;font-size:.75rem;cursor:pointer;transition:all .15s}
.toggle-btn.on{color:#80c050;border-color:#405030}
.toggle-btn.off{color:#666;border-color:#2a2a45}

/* ── Monitor dot ── */
.monitor-on{color:#50d080}
.monitor-off{color:#444}

/* ── Link list ── */
.link-list{display:flex;flex-direction:column;gap:6px;margin-bottom:16px;max-height:360px;overflow-y:auto}
.link-row{display:flex;align-items:center;gap:10px;background:#0d0d1a;border:1px solid #1e1e36;border-radius:7px;padding:8px 12px}
.link-row span{flex:1;font-size:.78rem;color:#aaa;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.link-add-area{display:flex;flex-direction:column;gap:8px;margin-bottom:14px}
.link-add-area textarea{background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:10px 12px;color:#ddd;font-size:.82rem;resize:vertical;min-height:80px;outline:none;font-family:inherit;transition:border-color .2s}
.link-add-area textarea:focus{border-color:#8aacff}
.pipeline-bar{background:#0d0d1a;border:1px solid #1e1e36;border-radius:8px;padding:12px 16px;display:flex;align-items:center;flex-wrap:wrap;gap:14px;margin-bottom:14px}
.pipeline-bar label{display:flex;align-items:center;gap:6px;font-size:.82rem;color:#aaa;cursor:pointer;user-select:none}
.pipeline-bar input[type=checkbox]{accent-color:#8aacff;width:15px;height:15px}

/* ── Multi-select ── */
.bulk-bar{position:fixed;bottom:0;left:0;right:0;background:#12121e;border-top:1px solid #8aacff;padding:12px 24px;display:flex;align-items:center;gap:14px;z-index:8000;transform:translateY(100%);transition:transform .2s}
.bulk-bar.open{transform:translateY(0)}
.bulk-count{color:#8aacff;font-size:.875rem;font-weight:600;flex:1}
.card.selected{border-color:#8aacff;box-shadow:0 0 0 2px #8aacff44}
.card.selected .card-thumb::after{content:'✓';position:absolute;top:6px;left:50%;transform:translateX(-50%);background:#8aacff;color:#000;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;z-index:4}
.select-mode .card{cursor:default}

@media(max-width:600px){
  .media-grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .lb-nav{display:none}
  .lb-panel{flex-direction:column;align-items:flex-start}
  .job-row{flex-direction:column;align-items:flex-start}
}
</style>
</head>
<body>

{%- macro card(item) %}
<div class="card"
     data-type="{{ item.type }}"
     data-src="/media/{{ item.rel_path | url_path }}"
     data-name="{{ item.name | e }}"
     data-path="{{ item.rel_path | e }}"
     onclick="openLb(this)">
  <div class="card-thumb">
    {%- if item.type in ['image','gif'] %}
    <img class="thumb" src="/media/{{ item.rel_path | url_path }}" loading="lazy" alt="{{ item.name | e }}">
    {%- elif item.type == 'video' %}
    <img class="thumb" src="/thumb/{{ item.rel_path | url_path }}" loading="lazy"
         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
         alt="{{ item.name | e }}">
    <div class="thumb-ph" style="display:none">&#127916;</div>
    {%- elif item.type == 'audio' %}
    <div class="thumb-ph audio-ph">&#127925;
      <div class="audio-card-title">{{ item.name }}</div>
    </div>
    {%- else %}
    <div class="thumb-ph">&#128196;</div>
    {%- endif %}
    <button class="fav-btn{% if item.favorited %} active{% endif %}"
            data-path="{{ item.rel_path | e }}"
            onclick="event.stopPropagation();toggleFav(this)"
            title="Favorit">{{ '♥' if item.favorited else '♡' }}</button>
    <button class="sess-btn"
            data-path="{{ item.rel_path | e }}"
            onclick="event.stopPropagation();showSessMenu(event,this.dataset.path)"
            title="Zu Session">+</button>
  </div>
  <div class="card-body">
    <div class="card-name" title="{{ item.name | e }}">{{ item.name }}</div>
    <div class="card-meta"><span>{{ item.size_str }}</span><span>{{ item.date }}</span></div>
    <div class="card-cat">{{ item.category }}</div>
  </div>
</div>
{%- endmacro %}

<header>
  <h1>&#128230; Media Manager</h1>
  <nav>
    <a href="/" class="{{ 'active' if view=='dashboard' }}">Dashboard</a>
    <a href="/browse" class="{{ 'active' if (view=='browse' and cat not in ['favorites']) }}">Browse</a>
    <a href="/browse?cat=favorites" class="fav-link {{ 'active' if (view=='browse' and cat=='favorites') }}">&hearts; Favoriten</a>
    <a href="/sessions" class="{{ 'active' if view in ['sessions','session_view'] }}">&#127902; Sessions</a>
    <a href="/download" class="{{ 'active' if view=='download' }}">&#8681; Download</a>
    <a href="/incoming" class="{{ 'active' if view=='incoming' }}">&#128229; Incoming{%- if incoming_count %} <span class="outbox-badge" style="background:#6080ff">{{ incoming_count }}</span>{%- endif %}</a>
    <a href="/scheduler" class="{{ 'active' if view=='scheduler' }}">&#9200; Scheduler</a>
    <a href="/links" class="{{ 'active' if view=='links' }}">&#128279; Links</a>
    <a href="/browse?cat=outbox" class="outbox-link {{ 'active' if (view=='browse' and cat=='outbox') }}">
      &#128228; Ausgang{%- if outbox_count %} <span class="outbox-badge">{{ outbox_count }}</span>{%- endif %}
    </a>
  </nav>
</header>

<div class="container">

{%- if view == 'dashboard' %}

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-num">{{ stats.total.count }}</div>
    <div class="stat-label">Gesamt</div>
    <div class="stat-size">{{ stats.total.size_str }}</div>
  </div>
  {%- for c in ['images','gifs','videos','hypno','audio'] %}
  <div class="stat-card" onclick="location.href='/browse?cat={{ c }}'">
    <div class="stat-num">{{ stats[c].count }}</div>
    <div class="stat-label">{{ c }}</div>
    <div class="stat-size">{{ stats[c].size_str }}</div>
  </div>
  {%- endfor %}
  <div class="stat-card" onclick="location.href='/browse?cat=favorites'">
    <div class="stat-num">{{ stats.favorites.count }}</div>
    <div class="stat-label">&hearts; Favoriten</div>
  </div>
  <div class="stat-card" onclick="location.href='/incoming'">
    <div class="stat-num">{{ incoming_count }}</div>
    <div class="stat-label">&#128229; Incoming</div>
  </div>
  <div class="stat-card" onclick="location.href='/sessions'">
    <div class="stat-num">{{ stats.sessions.count }}</div>
    <div class="stat-label">Sessions</div>
  </div>
</div>

<h2>Neueste Medien</h2>
{%- if recent %}
<div class="media-grid">
  {%- for item in recent %}{{ card(item) }}{%- endfor %}
</div>
<div style="margin-top:20px;text-align:center">
  <a href="/browse" class="btn">Alle anzeigen &#8594;</a>
</div>
{%- else %}
<div class="empty"><div class="empty-icon">&#128194;</div>Noch keine Medien vorhanden.</div>
{%- endif %}

{%- elif view == 'browse' %}

<form method="get" action="/browse" id="browse-form">
  <div class="search-bar">
    <input type="text" name="q" placeholder="Dateiname suchen&#8230;" value="{{ q | e }}">
    <select name="cat" id="cat-select" onchange="onCatChange(this.value)">
      <option value="">Alle Kategorien</option>
      {%- for c in ['images','gifs','videos','hypno','audio'] %}
      <option value="{{ c }}"{{ ' selected' if cat==c }}>{{ c }}</option>
      {%- endfor %}
      <option value="favorites"{{ ' selected' if cat=='favorites' }}>&hearts; Favoriten</option>
      <option value="outbox"{{ ' selected' if cat=='outbox' }}>&#128228; Ausgang</option>
    </select>
    <select name="sort">
      <option value="date"{{ ' selected' if sort=='date' }}>Datum</option>
      <option value="size"{{ ' selected' if sort=='size' }}>&#214;&#223;e</option>
      <option value="name"{{ ' selected' if sort=='name' }}>Name</option>
    </select>
    <input type="hidden" name="subcat" id="subcat-hidden" value="{{ subcat | e }}">
    <button type="submit" class="btn">Suchen</button>
    <a href="/browse" class="btn btn-ghost">Reset</a>
    <button type="button" class="btn btn-ghost" id="select-toggle" onclick="toggleSelectMode()">&#9745; Auswählen</button>
  </div>
</form>

<div class="subcat-wrap">
  <div class="subcat-chips" id="subcat-chips"></div>
</div>

{%- if cat == 'outbox' %}
<div class="outbox-bar">
  <span>&#128228; Ausgabe-Ordner &mdash; Dateien zum Versenden gesammelt</span>
  <div style="display:flex;gap:8px">
    <button class="btn btn-sm" onclick="openOutboxFolder()" title="Ordner in Explorer &#246;ffnen">&#128193; Im Explorer &#246;ffnen</button>
    <button class="btn btn-sm btn-danger" onclick="clearOutbox()">&#128465; Leeren</button>
  </div>
</div>
{%- endif %}

<div class="results-info">
  <strong>{{ total }}</strong> Dateien &#8212; Seite {{ page }} / {{ pages }}
</div>

{%- if items %}
<div class="media-grid">
  {%- for item in items %}{{ card(item) }}{%- endfor %}
</div>
{%- else %}
<div class="empty"><div class="empty-icon">&#128269;</div>Keine Ergebnisse</div>
{%- endif %}

{%- if pages > 1 %}
<div class="pagination">
  {%- if page > 1 %}
  <a class="page-link" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&subcat={{ subcat }}&page={{ page-1 }}">&#8249;</a>
  {%- endif %}
  {%- for p in range([1, page-2]|max, [pages+1, page+3]|min) %}
  <a class="page-link{{ ' active' if p==page }}" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&subcat={{ subcat }}&page={{ p }}">{{ p }}</a>
  {%- endfor %}
  {%- if page < pages %}
  <a class="page-link" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&subcat={{ subcat }}&page={{ page+1 }}">&#8250;</a>
  {%- endif %}
</div>
{%- endif %}

{%- elif view == 'sessions' %}

<div class="page-header">
  <h2>&#127902; Sessions</h2>
</div>

<div class="new-sess-form">
  <input type="text" id="new-sess-name" placeholder="Neue Session benennen&#8230;"
         onkeydown="if(event.key==='Enter')createSessionFromForm()">
  <button class="btn" onclick="createSessionFromForm()">Erstellen</button>
</div>

{%- if sessions %}
<div class="sess-grid">
  {%- for sname, spaths in sessions.items() %}
  <div class="sess-card">
    <div class="sess-card-name">{{ sname | e }}</div>
    <div class="sess-card-count">{{ spaths | length }} Medien</div>
    <div class="sess-card-actions">
      <a href="/sessions/{{ sname | url_path }}" class="btn btn-sm">&#214;ffnen</a>
      <button class="btn btn-sm btn-danger" data-name="{{ sname | e }}"
              onclick="deleteSession(this.dataset.name)">L&#246;schen</button>
    </div>
  </div>
  {%- endfor %}
</div>
{%- else %}
<div class="empty"><div class="empty-icon">&#127902;</div>Noch keine Sessions. Erstelle eine oben oder f&#252;ge Medien &#252;ber das +-Symbol hinzu!</div>
{%- endif %}

{%- elif view == 'session_view' %}

<div class="page-header">
  <h2>&#127902; {{ sess_name | e }}</h2>
  <div style="display:flex;gap:10px;flex-wrap:wrap">
    {%- if items %}
    <button class="btn" onclick="startSlideshow()">&#9654; Slideshow</button>
    {%- endif %}
    <a href="/sessions" class="btn btn-ghost">&#8592; Sessions</a>
  </div>
</div>

{%- if items %}
<div class="media-grid">
  {%- for item in items %}{{ card(item) }}{%- endfor %}
</div>
{%- else %}
<div class="empty"><div class="empty-icon">&#128194;</div>Session ist leer. F&#252;ge Medien &#252;ber das +-Symbol hinzu.</div>
{%- endif %}

{%- elif view == 'download' %}

<h2>&#8681; Download</h2>

<div class="tool-section">
  <div class="form-row">
    <label>URL</label>
    <input type="text" id="dl-url" class="wide" placeholder="https://reddit.com/r/… oder HypnoTube-Link&#8230;"
           onkeydown="if(event.key==='Enter')startDownload()">
  </div>
  <div class="form-row">
    <label>Ziel</label>
    <select id="dl-dest">
      <option value="incoming">incoming (dann sortieren)</option>
      <option value="bulk">bulk</option>
      <option value="images">images (direkt)</option>
    </select>
    <label style="margin-left:8px">Subfolder</label>
    <input type="text" id="dl-sub" placeholder="optional" list="preset-dl-list" style="width:180px">
    <datalist id="preset-dl-list">
      {%- for p in preset_names %}<option value="{{ p | e }}">{%- endfor %}
    </datalist>
  </div>
  <button class="btn" id="dl-btn" data-label="&#8681; Starten" onclick="startDownload()">&#8681; Starten</button>
</div>

<div class="log-wrap" id="dl-log-wrap" style="display:none">
  <div class="log-header">
    <span>Log</span>
    <button class="btn btn-sm btn-ghost" onclick="clearLogEl('dl-log')">Leeren</button>
  </div>
  <div class="log-terminal" id="dl-log"></div>
</div>

{%- elif view == 'incoming' %}

<div class="page-header">
  <h2>&#128229; Incoming ({{ count }})</h2>
  <div style="display:flex;gap:10px;flex-wrap:wrap">
    {%- if count %}
    <button class="btn" id="sort-btn" data-label="&#8635; Alle sortieren" onclick="startSort()">&#8635; Alle sortieren</button>
    {%- endif %}
    <a href="/download" class="btn btn-ghost">&#8681; Download</a>
  </div>
</div>

<div class="log-wrap" id="sort-log-wrap" style="display:none">
  <div class="log-terminal" id="sort-log"></div>
</div>

{%- if items %}
<div class="media-grid" style="margin-top:14px">
  {%- for item in items %}
  <div class="card"
       data-type="{{ item.type }}"
       data-src="/incoming-media/{{ item.rel_path | url_path }}"
       data-name="{{ item.name | e }}"
       onclick="openLb(this)">
    <div class="card-thumb">
      {%- if item.type in ['image','gif'] %}
      <img class="thumb" src="/incoming-media/{{ item.rel_path | url_path }}" loading="lazy" alt="{{ item.name | e }}">
      {%- elif item.type == 'video' %}
      <img class="thumb" src="/incoming-thumb/{{ item.rel_path | url_path }}" loading="lazy"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
           alt="{{ item.name | e }}">
      <div class="thumb-ph" style="display:none">&#127916;</div>
      {%- else %}
      <div class="thumb-ph">&#128196;</div>
      {%- endif %}
    </div>
    <div class="card-body">
      <div class="card-name" title="{{ item.name | e }}">{{ item.name }}</div>
      <div class="card-meta"><span>{{ item.size_str }}</span><span>{{ item.date }}</span></div>
    </div>
  </div>
  {%- endfor %}
</div>
{%- else %}
<div class="empty"><div class="empty-icon">&#128229;</div>Incoming-Ordner ist leer. Starte einen Download!</div>
{%- endif %}

<div style="margin-top:24px;display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div class="tool-section">
    <h2 style="margin-bottom:12px">&#128260; WebM &#8594; MP4 konvertieren</h2>
    <div class="form-row" style="margin-bottom:10px">
      <label style="color:#666;font-size:.82rem">Original:</label>
      <select id="conv-mode" style="padding:6px 10px;font-size:.82rem">
        <option value="keep">Behalten</option>
        <option value="delete">L&#246;schen</option>
      </select>
    </div>
    <button class="btn btn-sm" id="conv-btn" data-label="&#128260; Konvertieren" onclick="startConvert()">&#128260; Konvertieren</button>
    <div class="log-wrap" id="conv-log-wrap" style="display:none;margin-top:10px">
      <div class="log-terminal" id="conv-log" style="max-height:200px"></div>
    </div>
  </div>
  <div class="tool-section">
    <h2 style="margin-bottom:12px">&#128473; Duplikate entfernen</h2>
    <div class="form-row" style="margin-bottom:10px">
      <label style="color:#666;font-size:.82rem">Ordner:</label>
      <select id="dedup-dir" style="padding:6px 10px;font-size:.82rem">
        <option value="sorted">Alle sorted/</option>
        <option value="sorted/images">sorted/images</option>
        <option value="sorted/videos">sorted/videos</option>
      </select>
      <label style="color:#666;font-size:.82rem;margin-left:8px">Threshold:</label>
      <select id="dedup-thresh" style="padding:6px 10px;font-size:.82rem">
        <option value="0">0 - Identisch</option>
        <option value="5" selected>5 - Normal</option>
        <option value="10">10 - &#196;hnlich</option>
      </select>
    </div>
    <button class="btn btn-sm" id="dedup-btn" data-label="&#128473; Deduplizieren" onclick="startDedup()">&#128473; Deduplizieren</button>
    <div class="log-wrap" id="dedup-log-wrap" style="display:none;margin-top:10px">
      <div class="log-terminal" id="dedup-log" style="max-height:200px"></div>
    </div>
  </div>
</div>

{%- elif view == 'links' %}

<div class="page-header">
  <h2>&#128279; Link-Sammler</h2>
  <div style="display:flex;gap:10px;align-items:center">
    <span id="monitor-status-dot" style="font-size:1.1rem" title="Monitor-Status">&#9898;</span>
    <span id="monitor-status-txt" style="font-size:.82rem;color:#666">Inaktiv</span>
    <button class="btn btn-sm" id="monitor-btn" onclick="toggleMonitor()">&#128065; Monitor starten</button>
    <button class="btn btn-sm btn-ghost btn-danger" onclick="clearAllLinks()">&#128465; Leeren</button>
  </div>
</div>

<div style="background:#0d1218;border:1px solid #1e2e1e;border-radius:8px;padding:10px 16px;margin-bottom:14px;font-size:.8rem;color:#6a9050">
  &#128203; <strong>Clipboard-Monitor:</strong> Starte den Monitor und kopiere beliebige URLs &#8212; sie werden automatisch in die Liste gespeichert.
</div>

<div class="tool-section">
  <div class="link-add-area">
    <textarea id="link-input" placeholder="URLs manuell einfügen (eine pro Zeile)&#8230;"></textarea>
    <div style="display:flex;gap:8px">
      <button class="btn" onclick="addLinks()">&#43; Hinzuf&#252;gen</button>
    </div>
  </div>

  <div style="color:#555;font-size:.78rem;margin-bottom:8px" id="link-count">{{ links|length }} Link(s)</div>

  <div class="link-list" id="link-list">
    {%- if links %}
    {%- for url in links %}
    <div class="link-row" data-idx="{{ loop.index0 }}">
      <span title="{{ url | e }}">{{ url | e }}</span>
      <button class="btn btn-sm btn-ghost" onclick="copyLink(this)" data-url="{{ url | e }}" title="Kopieren">&#128203;</button>
      <button class="btn btn-sm btn-ghost" data-idx="{{ loop.index0 }}" onclick="removeLink(this.dataset.idx)">&#10005;</button>
    </div>
    {%- endfor %}
    {%- else %}
    <div class="empty" style="padding:20px 0"><div class="empty-icon">&#128279;</div>Keine Links gespeichert.</div>
    {%- endif %}
  </div>
</div>

<div class="tool-section">
  <h2 style="margin-bottom:14px">&#9654; Pipeline starten</h2>
  <div class="pipeline-bar">
    <label><input type="checkbox" id="p-download" checked> Download</label>
    <label><input type="checkbox" id="p-sort" checked> Sortieren</label>
    <label><input type="checkbox" id="p-convert" checked> Konvertieren</label>
    <label><input type="checkbox" id="p-dedup"> Deduplizieren</label>
    <label style="margin-left:8px;color:#888;font-size:.78rem">Threshold</label>
    <select id="p-threshold" style="padding:4px 8px;font-size:.78rem">
      <option value="0">0 - Nur identisch</option>
      <option value="5" selected>5 - Normal (empf.)</option>
      <option value="10">10 - Ähnlich</option>
    </select>
  </div>
  <button class="btn" id="pipeline-btn" data-label="&#9654; Starten" onclick="startPipeline()">&#9654; Starten</button>
</div>

<div class="log-wrap" id="pipeline-log-wrap" style="display:none">
  <div class="log-header">
    <span>Pipeline Log</span>
    <button class="btn btn-sm btn-ghost" onclick="clearLogEl('pipeline-log')">Leeren</button>
  </div>
  <div class="log-terminal" id="pipeline-log"></div>
</div>

{%- elif view == 'scheduler' %}

<div class="page-header">
  <h2>&#9200; Scheduler</h2>
  <button class="btn btn-ghost" onclick="runDueJobs()" id="due-btn" data-label="F&#228;llige starten">F&#228;llige starten</button>
</div>

<div class="log-wrap" id="sched-log-wrap" style="display:none">
  <div class="log-terminal" id="sched-log"></div>
</div>

<div class="job-list" id="job-list">
  {%- if jobs %}
  {%- for job in jobs %}
  <div class="job-row" data-idx="{{ loop.index0 }}">
    <div class="job-info">
      <div class="job-name">{{ job.name | e }}</div>
      <div class="job-url">{{ job.url | e }}</div>
      <div class="job-meta">&#9200; {{ job.schedule }}{%- if job.subfolder %} &nbsp;&#128193; {{ job.subfolder | e }}{%- endif %} &nbsp;&mdash;&nbsp; Letzter Lauf: {{ job.last_run[:10] if job.last_run else 'nie' }}</div>
    </div>
    <div class="job-actions">
      <button class="toggle-btn {{ 'on' if job.enabled else 'off' }}" data-idx="{{ loop.index0 }}"
              onclick="toggleJob(this)">{{ 'Aktiv' if job.enabled else 'Pausiert' }}</button>
      <button class="btn btn-sm" data-idx="{{ loop.index0 }}" onclick="runJob(this)">&#9654; Run</button>
      <button class="btn btn-sm btn-danger" data-idx="{{ loop.index0 }}" onclick="deleteJob(this)">&#10005;</button>
    </div>
  </div>
  {%- endfor %}
  {%- else %}
  <div class="empty" style="padding:30px 0"><div class="empty-icon">&#9200;</div>Keine Jobs konfiguriert.</div>
  {%- endif %}
</div>

<div class="tool-section">
  <h2 style="margin-bottom:14px">Neuer Job</h2>
  <div class="form-row">
    <label>Name</label>
    <input type="text" id="j-name" class="wide" placeholder="z.B. T&#228;glicher Sissy-Feed">
  </div>
  <div class="form-row">
    <label>URL</label>
    <input type="text" id="j-url" class="wide" placeholder="https://&#8230;">
  </div>
  <div class="form-row">
    <label>Uhrzeit</label>
    <input type="time" id="j-time" value="09:00" style="background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:7px 12px;color:#ddd;font-size:.875rem;outline:none">
    <label style="margin-left:8px">Subfolder</label>
    <input type="text" id="j-sub" placeholder="optional" list="preset-j-list" style="width:160px">
    <datalist id="preset-j-list">
      {%- for p in preset_names %}<option value="{{ p | e }}">{%- endfor %}
    </datalist>
  </div>
  <button class="btn" onclick="createJob()">&#43; Job erstellen</button>
</div>

{%- endif %}
</div>

<!-- Lightbox -->
<div class="lb" id="lb">
  <button class="lb-close" onclick="closeLb()">&#10005;</button>
  <button class="lb-nav lb-prev" onclick="lbPrev()">&#8249;</button>
  <button class="lb-nav lb-next" onclick="lbNext()">&#8250;</button>
  <div id="lb-inner"></div>
  <div class="lb-caption" id="lb-cap"></div>
  <div class="lb-panel">
    <label>Verschieben nach:</label>
    <select id="lb-cat-sel" onchange="lbLoadSubcats()">
      <option value="">Kategorie&#8230;</option>
      {%- for c in ['images','gifs','videos','hypno','audio'] %}
      <option value="{{ c }}">{{ c }}</option>
      {%- endfor %}
    </select>
    <select id="lb-sub-sel">
      <option value="">Unterkategorie&#8230;</option>
    </select>
    <button class="btn btn-sm" onclick="lbMoveFile()">Verschieben</button>
    <a id="lb-dl" href="#" class="btn btn-sm btn-ghost">&#8595; Download</a>
    <button class="btn btn-sm btn-outbox" onclick="lbCopyToOutbox()" title="Kopie in Ausgang-Ordner">&#128228; In Ausgang</button>
    <button class="btn btn-sm btn-danger" onclick="lbDeleteFile()" title="Datei unwiderruflich l&#246;schen">&#128465; L&#246;schen</button>
  </div>
  <input type="hidden" id="lb-path">
</div>

<!-- Bulk-select bar -->
<div class="bulk-bar" id="bulk-bar">
  <span class="bulk-count" id="bulk-count">0 ausgew&#228;hlt</span>
  <button class="btn btn-sm" onclick="bulkOutbox()">&#128228; In Ausgang</button>
  <button class="btn btn-sm" onclick="bulkToSession()">&#43; Session</button>
  <button class="btn btn-sm btn-danger" onclick="bulkDelete()">&#128465; L&#246;schen</button>
  <button class="btn btn-sm btn-ghost" onclick="exitSelectMode()">&#10005; Abbrechen</button>
</div>

<!-- Session dropdown -->
<div class="sess-menu" id="sess-menu"></div>

<!-- Slideshow -->
<div class="slideshow" id="slideshow">
  <div id="ss-inner"></div>
  <div class="ss-controls">
    <button onclick="ssPrev()">&#9664; Zur&#252;ck</button>
    <span class="ss-counter" id="ss-counter">0 / 0</span>
    <button onclick="ssNext()">Weiter &#9654;</button>
    <label class="ss-auto-label">
      <input type="checkbox" id="ss-auto"> Auto (5s)
    </label>
    <button onclick="ssClose()" style="margin-left:16px">&#10005; Schlie&#223;en</button>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// ── Server context ──
var PAGE_VIEW   = {{ view   | tojson }};
var CURRENT_CAT = {{ cat    | tojson }};
var CURRENT_SUB = {{ subcat | tojson }};

// ── DOM helpers ──
function clearEl(el) {
  var v = el && el.querySelector('video');
  if (v) { v.pause(); v.src = ''; }
  while (el && el.firstChild) el.removeChild(el.firstChild);
}

function makeOpt(value, label) {
  var o = document.createElement('option');
  o.value = value;
  o.textContent = label;
  return o;
}

function resetSubSel(sel) {
  clearEl(sel);
  sel.appendChild(makeOpt('', 'Unterkategorie…'));
}

// ── Toast ──
function showToast(msg) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(function() { t.classList.remove('show'); }, 2500);
}

// ── Favorites ──
function toggleFav(btn) {
  var path = btn.dataset.path;
  fetch('/api/favorite', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: path})
  }).then(function(r) { return r.json(); }).then(function(d) {
    btn.textContent = d.favorited ? '♥' : '♡';
    if (d.favorited) btn.classList.add('active');
    else btn.classList.remove('active');
    showToast(d.favorited ? 'Favorit gespeichert ♥' : 'Favorit entfernt');
  });
}

// ── Outbox ──
function lbCopyToOutbox() {
  var path = document.getElementById('lb-path').value;
  if (!path) return;
  fetch('/api/outbox/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: path})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    showToast('&#128228; In Ausgang kopiert: ' + d.filename);
    updateOutboxBadge(d.count);
  });
}

function openOutboxFolder() {
  fetch('/api/outbox/open').then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) showToast('Fehler: ' + d.error);
    else showToast('&#128193; Explorer ge&#246;ffnet');
  });
}

function clearOutbox() {
  if (!confirm('Ausgang wirklich leeren? Alle Kopien werden gel&#246;scht.')) return;
  fetch('/api/outbox/clear', {method: 'POST'})
    .then(function(r) { return r.json(); })
    .then(function() { location.reload(); });
}

function updateOutboxBadge(count) {
  var link = document.querySelector('.outbox-link');
  if (!link) return;
  var badge = link.querySelector('.outbox-badge');
  if (count > 0) {
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'outbox-badge';
      link.appendChild(badge);
    }
    badge.textContent = count;
  } else if (badge) {
    badge.remove();
  }
}

// ── Session menu ──
var _sessMenuPath = '';

function showSessMenu(evt, path) {
  _sessMenuPath = path;
  var menu = document.getElementById('sess-menu');
  // Capture rect NOW before the event object becomes stale inside async .then()
  var rect = evt.currentTarget.getBoundingClientRect();

  fetch('/api/sessions')
    .then(function(r) { return r.json(); })
    .then(function(sessions) {
      clearEl(menu);

      var keys = Object.keys(sessions);
      if (keys.length === 0) {
        var msg = document.createElement('div');
        msg.className = 'sess-menu-empty';
        msg.textContent = 'Keine Sessions vorhanden';
        menu.appendChild(msg);
      } else {
        keys.forEach(function(name) {
          var btn = document.createElement('button');
          btn.className = 'sess-menu-item';
          btn.textContent = name + ' (' + sessions[name].length + ')';
          btn.addEventListener('click', function() { addToSession(name); });
          menu.appendChild(btn);
        });
      }

      var hr = document.createElement('hr');
      menu.appendChild(hr);

      var newBtn = document.createElement('button');
      newBtn.className = 'sess-menu-item sess-menu-new';
      newBtn.textContent = '+ Neue Session';
      newBtn.addEventListener('click', function() {
        hideSessMenu();
        var n = prompt('Session-Name:');
        if (n && n.trim()) {
          fetch('/api/session/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: n.trim()})
          }).then(function(r) { return r.json(); }).then(function(d) {
            if (d.error) { showToast('Fehler: ' + d.error); return; }
            addToSession(n.trim());
          });
        }
      });
      menu.appendChild(newBtn);

      menu.style.top  = (rect.bottom + window.scrollY + 4) + 'px';
      menu.style.left = Math.min(rect.left, window.innerWidth - 210) + 'px';
      menu.classList.add('open');
    });
}

function hideSessMenu() {
  document.getElementById('sess-menu').classList.remove('open');
}

function addToSession(sessName) {
  hideSessMenu();
  fetch('/api/session/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session: sessName, path: _sessMenuPath})
  }).then(function(r) { return r.json(); }).then(function(d) {
    showToast(d.error || ('✓ Zu "' + sessName + '" hinzugefügt'));
  });
}

// ── Sessions page ──
function createSessionFromForm() {
  var inp = document.getElementById('new-sess-name');
  if (!inp) return;
  var n = inp.value.trim();
  if (!n) { showToast('Bitte einen Namen eingeben'); return; }
  fetch('/api/session/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: n})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    location.reload();
  });
}

function deleteSession(name) {
  if (!confirm('Session "' + name + '" wirklich löschen?')) return;
  fetch('/api/session/' + encodeURIComponent(name), {method: 'DELETE'})
    .then(function() { location.reload(); });
}

// ── Lightbox ──
var _lbCards = [];
var _lbIdx   = 0;

function openLb(card) {
  _lbCards = Array.from(document.querySelectorAll('.card'));
  _lbIdx   = _lbCards.indexOf(card);
  _renderLb(card);
}

function _renderLb(card) {
  var type = card.dataset.type;
  var src  = card.dataset.src;
  var name = card.dataset.name;
  var path = card.dataset.path;

  var inner = document.getElementById('lb-inner');
  clearEl(inner);

  var el;
  if (type === 'video') {
    el = document.createElement('video');
    el.className = 'lb-media';
    el.controls  = true;
    el.autoplay  = true;
    el.src       = src;
  } else if (type === 'audio') {
    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:16px;padding:20px';
    var icon = document.createElement('div');
    icon.style.cssText = 'font-size:5rem;color:#6a8aff';
    icon.textContent = '🎵';
    el = document.createElement('audio');
    el.className = 'lb-audio';
    el.controls  = true;
    el.autoplay  = true;
    el.src       = src;
    wrap.appendChild(icon);
    wrap.appendChild(el);
    inner.appendChild(wrap);
    el = null; // already appended
  } else {
    el = document.createElement('img');
    el.className = 'lb-media';
    el.alt       = name;
    el.src       = src;
  }
  if (el) inner.appendChild(el);

  document.getElementById('lb-cap').textContent = name;
  document.getElementById('lb-path').value      = path;

  var dl = document.getElementById('lb-dl');
  dl.href     = src;
  dl.download = name;

  document.getElementById('lb-cat-sel').value = '';
  resetSubSel(document.getElementById('lb-sub-sel'));

  document.getElementById('lb').classList.add('open');
}

function closeLb() {
  clearEl(document.getElementById('lb-inner'));
  document.getElementById('lb').classList.remove('open');
}

function lbPrev() {
  if (!_lbCards.length) return;
  _lbIdx = (_lbIdx - 1 + _lbCards.length) % _lbCards.length;
  _renderLb(_lbCards[_lbIdx]);
}

function lbNext() {
  if (!_lbCards.length) return;
  _lbIdx = (_lbIdx + 1) % _lbCards.length;
  _renderLb(_lbCards[_lbIdx]);
}

function lbLoadSubcats() {
  var cat = document.getElementById('lb-cat-sel').value;
  var sel = document.getElementById('lb-sub-sel');
  resetSubSel(sel);
  if (!cat) return;
  fetch('/api/subcats?cat=' + encodeURIComponent(cat))
    .then(function(r) { return r.json(); })
    .then(function(subs) {
      subs.forEach(function(s) { sel.appendChild(makeOpt(s, s)); });
    });
}

function lbMoveFile() {
  var path = document.getElementById('lb-path').value;
  var cat  = document.getElementById('lb-cat-sel').value;
  var sub  = document.getElementById('lb-sub-sel').value;
  if (!cat) { showToast('Bitte Kategorie wählen'); return; }

  fetch('/api/move', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: path, category: cat, subcat: sub})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    showToast('✓ Verschoben nach ' + cat + (sub ? '/' + sub : ''));
    if (_lbIdx >= 0 && _lbIdx < _lbCards.length) {
      _lbCards[_lbIdx].remove();
      _lbCards.splice(_lbIdx, 1);
    }
    closeLb();
  });
}

// ── Subcategory chips ──
function onCatChange(val) {
  document.getElementById('subcat-hidden').value = '';
  _renderSubcats(val, '');
}

function _renderSubcats(cat, activeSub) {
  var container = document.getElementById('subcat-chips');
  if (!container) return;
  clearEl(container);
  if (!cat || cat === 'favorites' || cat === 'outbox') return;

  fetch('/api/subcats?cat=' + encodeURIComponent(cat))
    .then(function(r) { return r.json(); })
    .then(function(subs) {
      if (!subs.length) return;

      function makeChip(label, sub) {
        var a = document.createElement('a');
        a.className = 'chip' + (activeSub === sub ? ' active' : '');
        a.href = _buildUrl({subcat: sub, page: 1});
        a.textContent = label;
        container.appendChild(a);
      }

      makeChip('Alle', '');
      subs.forEach(function(s) { makeChip(s, s); });
    });
}

function _buildUrl(overrides) {
  var params = new URLSearchParams(window.location.search);
  Object.keys(overrides).forEach(function(k) {
    var v = overrides[k];
    if (v === '' || v === null) params.delete(k);
    else params.set(k, v);
  });
  return '/browse?' + params.toString();
}

// ── Slideshow ──
var _ssItems = [];
var _ssIdx   = 0;
var _ssTimer = null;

function startSlideshow() {
  _ssItems = Array.from(document.querySelectorAll('.card')).map(function(c) {
    return {src: c.dataset.src, type: c.dataset.type, name: c.dataset.name};
  });
  if (!_ssItems.length) { showToast('Keine Medien vorhanden'); return; }
  _ssIdx = 0;
  document.getElementById('slideshow').classList.add('open');
  _ssShow();
}

function _ssShow() {
  var item  = _ssItems[_ssIdx];
  var inner = document.getElementById('ss-inner');
  clearEl(inner);

  var el;
  if (item.type === 'video') {
    el = document.createElement('video');
    el.src      = item.src;
    el.controls = true;
    el.autoplay = true;
    el.className = 'ss-media';
    el.onended  = function() {
      if (document.getElementById('ss-auto').checked) ssNext();
    };
  } else if (item.type === 'audio') {
    var awrap = document.createElement('div');
    awrap.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:20px';
    var aicon = document.createElement('div');
    aicon.style.cssText = 'font-size:8rem;color:#6a8aff';
    aicon.textContent = '🎵';
    var atitle = document.createElement('div');
    atitle.style.cssText = 'color:#aaa;font-size:.9rem;max-width:80vw;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
    atitle.textContent = item.name;
    el = document.createElement('audio');
    el.src      = item.src;
    el.controls = true;
    el.autoplay = true;
    el.style.width = '340px';
    el.onended  = function() {
      if (document.getElementById('ss-auto').checked) ssNext();
    };
    awrap.appendChild(aicon);
    awrap.appendChild(atitle);
    awrap.appendChild(el);
    inner.appendChild(awrap);
    el = null;
  } else {
    el = document.createElement('img');
    el.src       = item.src;
    el.className = 'ss-media';
    el.alt       = item.name;
  }
  if (el) inner.appendChild(el);

  document.getElementById('ss-counter').textContent =
    (_ssIdx + 1) + ' / ' + _ssItems.length;

  clearTimeout(_ssTimer); _ssTimer = null;
  if (document.getElementById('ss-auto').checked && item.type !== 'video') {
    _ssTimer = setTimeout(ssNext, 5000);
  }
}

function ssPrev() {
  clearTimeout(_ssTimer); _ssTimer = null;
  _ssIdx = (_ssIdx - 1 + _ssItems.length) % _ssItems.length;
  _ssShow();
}

function ssNext() {
  clearTimeout(_ssTimer); _ssTimer = null;
  _ssIdx = (_ssIdx + 1) % _ssItems.length;
  _ssShow();
}

function ssClose() {
  clearTimeout(_ssTimer); _ssTimer = null;
  clearEl(document.getElementById('ss-inner'));
  document.getElementById('slideshow').classList.remove('open');
}

document.getElementById('ss-auto').addEventListener('change', function() {
  clearTimeout(_ssTimer); _ssTimer = null;
  if (this.checked && _ssItems.length && _ssItems[_ssIdx].type !== 'video') {
    _ssTimer = setTimeout(ssNext, 5000);
  }
});

// ── Global events ──
document.getElementById('lb').addEventListener('click', function(e) {
  if (e.target === this) closeLb();
});

document.addEventListener('click', function(e) {
  if (!e.target.closest('.sess-btn') && !e.target.closest('#sess-menu')) {
    hideSessMenu();
  }
});

document.addEventListener('keydown', function(e) {
  var lbOpen = document.getElementById('lb').classList.contains('open');
  var ssOpen = document.getElementById('slideshow').classList.contains('open');
  if (lbOpen) {
    if (e.key === 'Escape')     closeLb();
    if (e.key === 'ArrowLeft')  { e.preventDefault(); lbPrev(); }
    if (e.key === 'ArrowRight') { e.preventDefault(); lbNext(); }
  } else if (ssOpen) {
    if (e.key === 'Escape')     ssClose();
    if (e.key === 'ArrowLeft')  { e.preventDefault(); ssPrev(); }
    if (e.key === 'ArrowRight') { e.preventDefault(); ssNext(); }
  }
});

// ── Init ──
if (PAGE_VIEW === 'browse' && CURRENT_CAT) {
  _renderSubcats(CURRENT_CAT, CURRENT_SUB);
}

if (PAGE_VIEW === 'links') {
  fetch('/api/monitor/status')
    .then(function(r){ return r.json(); })
    .then(function(d){
      _setMonitorUI(d.running);
      if (d.running) _monitorPoll = setInterval(_refreshLinkList, 2000);
    });
}

// ── SSE log helper ──
function clearLogEl(id) {
  var el = document.getElementById(id);
  if (el) while (el.firstChild) el.removeChild(el.firstChild);
}

function openSSELog(url, logId, wrapId, btnId, onDone) {
  var wrap = document.getElementById(wrapId);
  var log  = document.getElementById(logId);
  var btn  = btnId ? document.getElementById(btnId) : null;
  if (wrap) wrap.style.display = '';
  clearLogEl(logId);

  if (btn) { btn.disabled = true; btn.textContent = '⏳ Läuft…'; }

  var src = new EventSource(url);
  src.onmessage = function(e) {
    if (e.data === '__DONE__') {
      src.close();
      if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || 'Starten'; }
      if (typeof onDone === 'function') onDone();
      return;
    }
    if (log) {
      var line = document.createElement('div');
      line.textContent = e.data;
      log.appendChild(line);
      log.scrollTop = log.scrollHeight;
    }
  };
  src.onerror = function() {
    src.close();
    if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || 'Starten'; }
  };
}

// ── Download view ──
function startDownload() {
  var url = document.getElementById('dl-url');
  var dest = document.getElementById('dl-dest');
  var sub  = document.getElementById('dl-sub');
  if (!url || !url.value.trim()) { showToast('Bitte eine URL eingeben'); return; }
  var params = new URLSearchParams({
    url:  url.value.trim(),
    dest: dest ? dest.value : 'incoming',
    subfolder: sub ? sub.value.trim() : ''
  });
  openSSELog('/stream/download?' + params.toString(),
             'dl-log', 'dl-log-wrap', 'dl-btn', null);
}

// ── Incoming / sort view ──
function startSort() {
  openSSELog('/stream/sort', 'sort-log', 'sort-log-wrap', 'sort-btn', function() {
    showToast('✓ Sortierung abgeschlossen');
    setTimeout(function() { location.reload(); }, 1500);
  });
}

// ── Scheduler view ──
function runJob(btn) {
  var idx = btn.dataset.idx;
  var logId  = 'job-log-' + idx;
  var wrapId = 'job-wrap-' + idx;

  var row = btn.closest('.job-row');
  if (row) {
    var existing = row.parentNode.querySelector('#' + wrapId);
    if (!existing) {
      var wrap = document.createElement('div');
      wrap.className = 'log-wrap';
      wrap.id = wrapId;
      wrap.style.paddingLeft = '16px';
      var terminal = document.createElement('div');
      terminal.className = 'log-terminal';
      terminal.id = logId;
      wrap.appendChild(terminal);
      row.parentNode.insertBefore(wrap, row.nextSibling);
    }
  }

  openSSELog('/stream/job/' + idx, logId, wrapId, null, function() {
    showToast('✓ Job abgeschlossen');
  });
}

function deleteJob(btn) {
  var idx = btn.dataset.idx;
  if (!confirm('Job wirklich löschen?')) return;
  fetch('/api/jobs/' + idx, {method: 'DELETE'})
    .then(function() {
      var row = btn.closest('.job-row');
      if (row) row.remove();
      showToast('Job gelöscht');
    });
}

function toggleJob(btn) {
  var idx = btn.dataset.idx;
  fetch('/api/jobs/' + idx + '/toggle', {method: 'POST'})
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.enabled) {
        btn.textContent = 'Aktiv';
        btn.classList.remove('off');
        btn.classList.add('on');
      } else {
        btn.textContent = 'Pausiert';
        btn.classList.remove('on');
        btn.classList.add('off');
      }
    });
}

function createJob() {
  var name = document.getElementById('j-name');
  var url  = document.getElementById('j-url');
  var time = document.getElementById('j-time');
  var sub  = document.getElementById('j-sub');
  if (!name || !name.value.trim()) { showToast('Bitte einen Namen eingeben'); return; }
  if (!url  || !url.value.trim())  { showToast('Bitte eine URL eingeben'); return; }
  fetch('/api/jobs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      name:      name.value.trim(),
      url:       url.value.trim(),
      schedule:  time ? time.value : '09:00',
      subfolder: sub ? sub.value.trim() : ''
    })
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    location.reload();
  });
}

// ── Convert & Dedup ──
function startConvert() {
  var mode = document.getElementById('conv-mode');
  var del  = mode && mode.value === 'delete' ? '1' : '0';
  openSSELog('/stream/convert?delete=' + del, 'conv-log', 'conv-log-wrap', 'conv-btn', function() {
    showToast('✓ Konvertierung abgeschlossen');
  });
}

function startDedup() {
  var dir    = document.getElementById('dedup-dir');
  var thresh = document.getElementById('dedup-thresh');
  var params = new URLSearchParams({
    dir:       dir    ? dir.value    : 'sorted',
    threshold: thresh ? thresh.value : '5'
  });
  openSSELog('/stream/dedup?' + params.toString(),
             'dedup-log', 'dedup-log-wrap', 'dedup-btn', function() {
    showToast('✓ Deduplizierung abgeschlossen');
  });
}

// ── Link collector & monitor ──
var _monitorPoll    = null;
var _monitorRunning = false;

function _setMonitorUI(running) {
  _monitorRunning = running;
  var dot = document.getElementById('monitor-status-dot');
  var txt = document.getElementById('monitor-status-txt');
  var btn = document.getElementById('monitor-btn');
  if (!dot) return;
  if (running) {
    dot.textContent = '●';
    dot.className = 'monitor-on';
    if (txt) { txt.textContent = 'Aktiv — kopiere URLs'; txt.style.color = '#50d080'; }
    if (btn) btn.textContent = '⏹ Monitor stoppen';
  } else {
    dot.textContent = '○';
    dot.className = 'monitor-off';
    if (txt) { txt.textContent = 'Inaktiv'; txt.style.color = '#666'; }
    if (btn) btn.textContent = '👁 Monitor starten';
  }
}

function _refreshLinkList() {
  fetch('/api/links')
    .then(function(r){ return r.json(); })
    .then(function(links) {
      var list  = document.getElementById('link-list');
      var count = document.getElementById('link-count');
      if (!list) return;
      if (count) count.textContent = links.length + ' Link(s)';
      while (list.firstChild) list.removeChild(list.firstChild);
      if (!links.length) {
        var empty = document.createElement('div');
        empty.className = 'empty';
        empty.style.padding = '20px 0';
        var icon = document.createElement('div');
        icon.className = 'empty-icon';
        icon.textContent = '🔗';
        var msg = document.createTextNode('Keine Links gespeichert.');
        empty.appendChild(icon);
        empty.appendChild(msg);
        list.appendChild(empty);
        return;
      }
      links.forEach(function(url, idx) {
        var row = document.createElement('div');
        row.className = 'link-row';
        row.dataset.idx = idx;

        var span = document.createElement('span');
        span.title = url;
        span.textContent = url;

        var cpBtn = document.createElement('button');
        cpBtn.className = 'btn btn-sm btn-ghost';
        cpBtn.title = 'Kopieren';
        cpBtn.textContent = '📋';
        cpBtn.dataset.url = url;
        cpBtn.addEventListener('click', function(){ copyLink(this); });

        var rmBtn = document.createElement('button');
        rmBtn.className = 'btn btn-sm btn-ghost';
        rmBtn.textContent = '✕';
        rmBtn.dataset.idx = String(idx);
        rmBtn.addEventListener('click', function(){ removeLink(this.dataset.idx); });

        row.appendChild(span);
        row.appendChild(cpBtn);
        row.appendChild(rmBtn);
        list.appendChild(row);
      });
    });
}

function toggleMonitor() {
  if (_monitorRunning) {
    fetch('/api/monitor/stop', {method: 'POST'})
      .then(function(r){ return r.json(); })
      .then(function() {
        _setMonitorUI(false);
        clearInterval(_monitorPoll);
        _monitorPoll = null;
        showToast('Monitor gestoppt');
      });
  } else {
    fetch('/api/monitor/start', {method: 'POST'})
      .then(function(r){ return r.json(); })
      .then(function(d) {
        if (d.error) { showToast('Fehler: ' + d.error); return; }
        _setMonitorUI(true);
        _monitorPoll = setInterval(_refreshLinkList, 2000);
        showToast('Monitor gestartet — kopiere URLs');
      });
  }
}

function copyLink(btn) {
  var url = btn.dataset.url;
  if (!url) return;
  navigator.clipboard.writeText(url).then(function() {
    showToast('📋 Kopiert!');
  }).catch(function() {
    showToast('Kopieren fehlgeschlagen');
  });
}

function addLinks() {
  var ta = document.getElementById('link-input');
  if (!ta || !ta.value.trim()) { showToast('Keine URLs eingegeben'); return; }
  var lines = ta.value.split('\n').map(function(s){ return s.trim(); }).filter(Boolean);
  fetch('/api/links/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({urls: lines})
  }).then(function(r){ return r.json(); }).then(function(d){
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    ta.value = '';
    location.reload();
  });
}

function removeLink(idx) {
  fetch('/api/links/' + idx, {method: 'DELETE'})
    .then(function(){ location.reload(); });
}

function clearAllLinks() {
  if (!confirm('Alle Links wirklich löschen?')) return;
  fetch('/api/links/clear', {method: 'POST'})
    .then(function(){ location.reload(); });
}

function startPipeline() {
  var dl    = document.getElementById('p-download');
  var sort  = document.getElementById('p-sort');
  var conv  = document.getElementById('p-convert');
  var dedup = document.getElementById('p-dedup');
  var thresh= document.getElementById('p-threshold');
  var params = new URLSearchParams({
    download:  dl    && dl.checked    ? '1' : '0',
    sort:      sort  && sort.checked  ? '1' : '0',
    convert:   conv  && conv.checked  ? '1' : '0',
    dedup:     dedup && dedup.checked ? '1' : '0',
    threshold: thresh ? thresh.value  : '5'
  });
  openSSELog('/stream/pipeline?' + params.toString(),
             'pipeline-log', 'pipeline-log-wrap', 'pipeline-btn', function() {
    showToast('✓ Pipeline abgeschlossen');
  });
}

// ── Lightbox: delete file ──
function lbDeleteFile() {
  var path = document.getElementById('lb-path').value;
  if (!path) return;
  if (!confirm('Datei unwiderruflich löschen?\n\n' + path)) return;
  fetch('/api/file', {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: path})
  }).then(function(r){ return r.json(); }).then(function(d){
    if (d.error) { showToast('Fehler: ' + d.error); return; }
    showToast('🗑 Gelöscht');
    if (_lbIdx >= 0 && _lbIdx < _lbCards.length) {
      _lbCards[_lbIdx].remove();
      _lbCards.splice(_lbIdx, 1);
    }
    closeLb();
  });
}

// ── Multi-select ──
var _selectMode = false;
var _selected   = new Set();

function toggleSelectMode() {
  _selectMode = !_selectMode;
  _selected.clear();
  var grid = document.querySelector('.media-grid');
  var btn  = document.getElementById('select-toggle');
  if (_selectMode) {
    if (grid) grid.classList.add('select-mode');
    if (btn)  btn.style.background = '#8aacff';
    if (btn)  btn.style.color = '#000';
  } else {
    if (grid) grid.classList.remove('select-mode');
    document.querySelectorAll('.card.selected').forEach(function(c){ c.classList.remove('selected'); });
    if (btn)  btn.style.background = '';
    if (btn)  btn.style.color = '';
    document.getElementById('bulk-bar').classList.remove('open');
  }
}

function exitSelectMode() {
  if (_selectMode) toggleSelectMode();
}

function _updateBulkBar() {
  var bar   = document.getElementById('bulk-bar');
  var count = document.getElementById('bulk-count');
  if (_selected.size > 0) {
    bar.classList.add('open');
    count.textContent = _selected.size + ' ausgewählt';
  } else {
    bar.classList.remove('open');
  }
}

// Override openLb to handle select mode
var _origOpenLb = null;
(function() {
  _origOpenLb = openLb;
  openLb = function(card) {
    if (_selectMode) {
      var path = card.dataset.path;
      if (!path) return;
      if (_selected.has(path)) {
        _selected.delete(path);
        card.classList.remove('selected');
      } else {
        _selected.add(path);
        card.classList.add('selected');
      }
      _updateBulkBar();
      return;
    }
    _origOpenLb(card);
  };
})();

function bulkOutbox() {
  var paths = Array.from(_selected);
  if (!paths.length) return;
  var done = 0;
  paths.forEach(function(path) {
    fetch('/api/outbox/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: path})
    }).then(function(r){ return r.json(); }).then(function(d){
      done++;
      if (done === paths.length) {
        showToast(paths.length + ' Dateien in Ausgang kopiert');
        updateOutboxBadge(d.count);
        exitSelectMode();
      }
    });
  });
}

function bulkToSession() {
  var paths = Array.from(_selected);
  if (!paths.length) return;
  var n = prompt('Session-Name (neu oder vorhanden):');
  if (!n || !n.trim()) return;
  n = n.trim();
  fetch('/api/session/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: n})
  }).then(function(){ // ignore "already exists" error
    var done = 0;
    paths.forEach(function(path) {
      fetch('/api/session/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session: n, path: path})
      }).then(function(){
        done++;
        if (done === paths.length) {
          showToast(paths.length + ' Dateien zu "' + n + '" hinzugefügt');
          exitSelectMode();
        }
      });
    });
  });
}

function bulkDelete() {
  var paths = Array.from(_selected);
  if (!paths.length) return;
  if (!confirm(paths.length + ' Dateien unwiderruflich löschen?')) return;
  var done = 0;
  var cards = document.querySelectorAll('.card.selected');
  paths.forEach(function(path) {
    fetch('/api/file', {
      method: 'DELETE',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: path})
    }).then(function(){ done++; if (done === paths.length) {
      cards.forEach(function(c){ c.remove(); });
      showToast(paths.length + ' Dateien gelöscht');
      exitSelectMode();
    }});
  });
}

function runDueJobs() {
  var btn = document.getElementById('due-btn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Prüfe…'; }
  fetch('/api/jobs')
    .then(function(r) { return r.json(); })
    .then(function(jobs) {
      var now  = new Date();
      var hhmm = now.getHours().toString().padStart(2,'0') + ':' +
                 now.getMinutes().toString().padStart(2,'0');
      var due  = [];
      jobs.forEach(function(job, idx) {
        if (job.enabled && job.schedule === hhmm) due.push(idx);
      });
      if (!due.length) {
        showToast('Keine fälligen Jobs');
        if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || 'Fällige starten'; }
        return;
      }
      showToast(due.length + ' Job(s) gestartet');
      due.forEach(function(idx) {
        var runBtn = document.querySelector('.job-row[data-idx="' + idx + '"] .btn');
        if (runBtn) runJob(runBtn);
      });
      if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || 'Fällige starten'; }
    });
}
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

_TMPL_DEFAULTS = dict(cat='', subcat='', q='', sort='date', items=[])


@app.route('/')
def dashboard():
    stats  = get_stats()
    recent, _ = search_files(sort='date', page=1, per_page=16)
    return render_template_string(TEMPLATE, view='dashboard', stats=stats, recent=recent,
                                  **_TMPL_DEFAULTS)


@app.route('/browse')
def browse():
    q      = request.args.get('q', '')
    cat    = request.args.get('cat', '')
    subcat = request.args.get('subcat', '')
    sort   = request.args.get('sort', 'date')
    page   = max(1, int(request.args.get('page', 1) or 1))
    per_page = 40

    items, total = search_files(
        query=q,
        category=cat if (cat in CATEGORIES or cat in ('favorites', 'outbox')) else None,
        subcat=subcat or None,
        sort=sort,
        page=page,
        per_page=per_page,
    )
    pages = max(1, (total + per_page - 1) // per_page)

    return render_template_string(
        TEMPLATE,
        view='browse',
        items=items, total=total, page=page, pages=pages,
        q=q, cat=cat, subcat=subcat, sort=sort,
    )


@app.route('/sessions')
def sessions_view():
    return render_template_string(TEMPLATE, view='sessions',
                                  sessions=load_sessions(), **_TMPL_DEFAULTS)


@app.route('/sessions/<name>')
def session_detail(name):
    items = get_session_items(name)
    return render_template_string(TEMPLATE, view='session_view',
                                  sess_name=name, items=items,
                                  cat='', subcat='', q='', sort='date')


@app.route('/media/<path:filepath>')
def serve_media(filepath):
    try:
        target = (SORTED / filepath).resolve()
        target.relative_to(SORTED.resolve())
    except (ValueError, Exception):
        abort(403)
    if not target.is_file():
        abort(404)
    return send_file(target)


@app.route('/thumb/<path:filepath>')
def serve_thumb(filepath):
    try:
        target = (SORTED / filepath).resolve()
        target.relative_to(SORTED.resolve())
    except (ValueError, Exception):
        abort(403)
    if not target.is_file():
        abort(404)
    thumb = get_video_thumb(target)
    if thumb and thumb.exists():
        return send_file(thumb, mimetype='image/jpeg')
    abort(404)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route('/api/subcats')
def api_subcats():
    cat = request.args.get('cat', '')
    if cat not in CATEGORIES:
        return jsonify([])
    return jsonify(get_subcategories(cat))


@app.route('/api/sessions')
def api_sessions_list():
    return jsonify(load_sessions())


@app.route('/api/favorite', methods=['POST'])
def api_favorite():
    data = request.get_json(silent=True) or {}
    path = data.get('path', '')
    if not path:
        return jsonify({'error': 'path required'}), 400
    favs = load_favorites()
    if path in favs:
        favs.discard(path)
        state = False
    else:
        favs.add(path)
        state = True
    save_favorites(favs)
    return jsonify({'favorited': state})


@app.route('/api/move', methods=['POST'])
def api_move():
    data   = request.get_json(silent=True) or {}
    rel    = data.get('path', '')
    cat    = data.get('category', '')
    subcat = data.get('subcat', '')

    if cat not in CATEGORIES:
        return jsonify({'error': 'Ungültige Kategorie'}), 400
    try:
        src = (SORTED / rel).resolve()
        src.relative_to(SORTED.resolve())
    except (ValueError, Exception):
        return jsonify({'error': 'Ungültiger Pfad'}), 403
    if not src.is_file():
        return jsonify({'error': 'Datei nicht gefunden'}), 404

    dst_dir = (SORTED / cat / subcat) if subcat else (SORTED / cat)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        return jsonify({'error': 'Dateiname existiert bereits am Ziel'}), 409

    shutil.move(str(src), str(dst))

    old_rel = str(src.relative_to(SORTED)).replace('\\', '/')
    new_rel = str(dst.relative_to(SORTED)).replace('\\', '/')
    favs = load_favorites()
    if old_rel in favs:
        favs.discard(old_rel)
        favs.add(new_rel)
        save_favorites(favs)

    return jsonify({'new_path': new_rel})


@app.route('/api/session/create', methods=['POST'])
def api_session_create():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name erforderlich'}), 400
    sessions = load_sessions()
    if name in sessions:
        return jsonify({'error': 'Session existiert bereits'}), 409
    sessions[name] = []
    save_sessions(sessions)
    return jsonify({'ok': True, 'name': name})


@app.route('/api/session/add', methods=['POST'])
def api_session_add():
    data = request.get_json(silent=True) or {}
    name = data.get('session', '')
    path = data.get('path', '')
    if not name or not path:
        return jsonify({'error': 'session und path erforderlich'}), 400
    sessions = load_sessions()
    if name not in sessions:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    if path not in sessions[name]:
        sessions[name].append(path)
        save_sessions(sessions)
    return jsonify({'ok': True})


@app.route('/api/session/remove', methods=['POST'])
def api_session_remove():
    data = request.get_json(silent=True) or {}
    name = data.get('session', '')
    path = data.get('path', '')
    sessions = load_sessions()
    if name in sessions and path in sessions[name]:
        sessions[name].remove(path)
        save_sessions(sessions)
    return jsonify({'ok': True})


@app.route('/api/session/<name>', methods=['DELETE'])
def api_session_delete(name):
    sessions = load_sessions()
    sessions.pop(name, None)
    save_sessions(sessions)
    return jsonify({'ok': True})


@app.route('/api/outbox/add', methods=['POST'])
def api_outbox_add():
    data = request.get_json(silent=True) or {}
    rel  = data.get('path', '')
    filename, err = copy_to_outbox(rel)
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'ok': True, 'filename': filename, 'count': get_outbox_count()})


@app.route('/api/outbox/clear', methods=['POST'])
def api_outbox_clear():
    if OUTBOX_DIR.exists():
        for f in OUTBOX_DIR.iterdir():
            if f.is_file():
                f.unlink()
    return jsonify({'ok': True})


@app.route('/api/outbox/open')
def api_outbox_open():
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(OUTBOX_DIR))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Download / Sort / Incoming / Scheduler routes
# ---------------------------------------------------------------------------

@app.route('/links')
def links_view():
    return render_template_string(TEMPLATE, view='links',
                                  links=load_links(), **_TMPL_DEFAULTS)


@app.route('/download')
def download_view():
    presets = load_tag_presets()
    preset_names = sorted(list(presets.get('presets', {}).keys()) +
                          list(presets.get('mixes', {}).keys()))
    return render_template_string(TEMPLATE, view='download',
                                  preset_names=preset_names, **_TMPL_DEFAULTS)


@app.route('/incoming')
def incoming_view():
    items = list_incoming()
    presets = load_tag_presets()
    preset_names = sorted(list(presets.get('presets', {}).keys()) +
                          list(presets.get('mixes', {}).keys()))
    return render_template_string(TEMPLATE, view='incoming',
                                  items=items, count=len(items),
                                  preset_names=preset_names,
                                  cat='', subcat='', q='', sort='date')


@app.route('/scheduler')
def scheduler_view():
    jobs = load_jobs_file()
    presets = load_tag_presets()
    preset_names = sorted(list(presets.get('presets', {}).keys()) +
                          list(presets.get('mixes', {}).keys()))
    return render_template_string(TEMPLATE, view='scheduler',
                                  jobs=jobs, preset_names=preset_names, **_TMPL_DEFAULTS)


@app.route('/incoming-media/<path:filepath>')
def serve_incoming_media(filepath):
    try:
        target = (INCOMING_DIR / filepath).resolve()
        target.relative_to(INCOMING_DIR.resolve())
    except (ValueError, Exception):
        abort(403)
    if not target.is_file():
        abort(404)
    return send_file(target)


@app.route('/incoming-thumb/<path:filepath>')
def serve_incoming_thumb(filepath):
    try:
        target = (INCOMING_DIR / filepath).resolve()
        target.relative_to(INCOMING_DIR.resolve())
    except (ValueError, Exception):
        abort(403)
    if not target.is_file():
        abort(404)
    thumb = get_video_thumb(target)
    if thumb and thumb.exists():
        return send_file(thumb, mimetype='image/jpeg')
    abort(404)


@app.route('/stream/download')
def stream_download():
    url     = request.args.get('url', '').strip()
    dest    = request.args.get('dest', 'incoming')
    subfolder = request.args.get('subfolder', '').strip()
    if not url:
        def _err():
            yield "data: FEHLER: Keine URL angegeben\n\n"
            yield "data: __DONE__\n\n"
        return Response(stream_with_context(_err()), mimetype='text/event-stream')

    cmd = [sys.executable, str(SCRIPTS_DIR / 'media-downloader.py'), url,
           '--dest', dest]
    if subfolder:
        cmd += ['--subfolder', subfolder]
    return Response(stream_with_context(_stream_subprocess(cmd)),
                    mimetype='text/event-stream')


@app.route('/stream/sort')
def stream_sort():
    cmd = [sys.executable, str(SCRIPTS_DIR / 'auto-sort.py')]
    return Response(stream_with_context(_stream_subprocess(cmd)),
                    mimetype='text/event-stream')


@app.route('/stream/convert')
def stream_convert():
    delete = request.args.get('delete', '0') == '1'
    cmd = [sys.executable, str(SCRIPTS_DIR / 'convert-webm.py'), '--auto']
    if delete:
        cmd.append('--delete-original')
    return Response(stream_with_context(_stream_subprocess(cmd)),
                    mimetype='text/event-stream')


@app.route('/stream/dedup')
def stream_dedup():
    dir_arg   = request.args.get('dir', 'sorted')
    threshold = request.args.get('threshold', '5')
    target    = str(SORTED / dir_arg) if not dir_arg.startswith('/') else dir_arg
    cmd = [sys.executable, str(SCRIPTS_DIR / 'deduplicate.py'),
           '--auto', '--dir', target, '--threshold', threshold]
    return Response(stream_with_context(_stream_subprocess(cmd)),
                    mimetype='text/event-stream')


@app.route('/stream/pipeline')
def stream_pipeline():
    do_download = request.args.get('download', '0') == '1'
    do_sort     = request.args.get('sort',     '0') == '1'
    do_convert  = request.args.get('convert',  '0') == '1'
    do_dedup    = request.args.get('dedup',    '0') == '1'
    threshold   = request.args.get('threshold', '5')

    steps = []
    if do_download:
        steps.append(([sys.executable, str(BASE_DIR / 'batch-download.py')],
                      'Download'))
    if do_sort:
        steps.append(([sys.executable, str(SCRIPTS_DIR / 'auto-sort.py')],
                      'Sortieren'))
    if do_convert:
        steps.append(([sys.executable, str(SCRIPTS_DIR / 'convert-webm.py'), '--auto'],
                      'Konvertieren'))
    if do_dedup:
        steps.append(([sys.executable, str(SCRIPTS_DIR / 'deduplicate.py'),
                       '--auto', '--dir', str(SORTED), '--threshold', threshold],
                      'Deduplizieren'))

    if not steps:
        def _empty():
            yield "data: Keine Schritte ausgewählt\n\n"
            yield "data: __DONE__\n\n"
        return Response(stream_with_context(_empty()), mimetype='text/event-stream')

    return Response(stream_with_context(_stream_pipeline(steps)),
                    mimetype='text/event-stream')


@app.route('/stream/job/<int:idx>')
def stream_job(idx):
    jobs = load_jobs_file()
    if idx < 0 or idx >= len(jobs):
        def _err():
            yield "data: FEHLER: Job nicht gefunden\n\n"
            yield "data: __DONE__\n\n"
        return Response(stream_with_context(_err()), mimetype='text/event-stream')

    job = jobs[idx]
    cmd = [sys.executable, str(SCRIPTS_DIR / 'media-downloader.py'),
           job['url'], '--dest', job.get('dest', 'incoming')]
    if job.get('subfolder'):
        cmd += ['--subfolder', job['subfolder']]

    def _run_and_update():
        yield from _stream_subprocess(cmd)
        jobs[idx]['last_run'] = datetime.datetime.now().isoformat()
        save_jobs_file(jobs)

    return Response(stream_with_context(_run_and_update()),
                    mimetype='text/event-stream')


@app.route('/api/jobs', methods=['GET'])
def api_jobs_list():
    return jsonify(load_jobs_file())


@app.route('/api/jobs', methods=['POST'])
def api_jobs_create():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    url  = data.get('url', '').strip()
    if not name or not url:
        return jsonify({'error': 'name und url erforderlich'}), 400
    job = {
        'name':      name,
        'url':       url,
        'schedule':  data.get('schedule', '09:00'),
        'subfolder': data.get('subfolder', ''),
        'dest':      data.get('dest', 'incoming'),
        'enabled':   True,
        'last_run':  None,
    }
    jobs = load_jobs_file()
    jobs.append(job)
    save_jobs_file(jobs)
    return jsonify({'ok': True, 'idx': len(jobs) - 1})


@app.route('/api/jobs/<int:idx>', methods=['DELETE'])
def api_jobs_delete(idx):
    jobs = load_jobs_file()
    if 0 <= idx < len(jobs):
        jobs.pop(idx)
        save_jobs_file(jobs)
    return jsonify({'ok': True})


@app.route('/api/jobs/<int:idx>/toggle', methods=['POST'])
def api_jobs_toggle(idx):
    jobs = load_jobs_file()
    if idx < 0 or idx >= len(jobs):
        return jsonify({'error': 'Job nicht gefunden'}), 404
    jobs[idx]['enabled'] = not jobs[idx].get('enabled', True)
    save_jobs_file(jobs)
    return jsonify({'ok': True, 'enabled': jobs[idx]['enabled']})


@app.route('/api/monitor/status')
def api_monitor_status():
    return jsonify({'running': is_monitor_running()})


@app.route('/api/monitor/start', methods=['POST'])
def api_monitor_start():
    global _monitor_proc
    if is_monitor_running():
        return jsonify({'ok': True, 'running': True})
    monitor_script = SCRIPTS_DIR / 'link-monitor.py'
    if not monitor_script.exists():
        return jsonify({'error': 'link-monitor.py nicht gefunden'}), 404
    try:
        _monitor_proc = subprocess.Popen(
            [sys.executable, str(monitor_script)],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return jsonify({'ok': True, 'running': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitor/stop', methods=['POST'])
def api_monitor_stop():
    global _monitor_proc
    if _monitor_proc and _monitor_proc.poll() is None:
        _monitor_proc.terminate()
        try:
            _monitor_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _monitor_proc.kill()
    _monitor_proc = None
    return jsonify({'ok': True, 'running': False})


@app.route('/api/links', methods=['GET'])
def api_links_list():
    return jsonify(load_links())


@app.route('/api/links/add', methods=['POST'])
def api_links_add():
    data = request.get_json(silent=True) or {}
    urls = data.get('urls', [])
    if not urls:
        return jsonify({'error': 'urls erforderlich'}), 400
    existing = load_links()
    added = 0
    for u in urls:
        u = u.strip()
        if u and u not in existing:
            existing.append(u)
            added += 1
    save_links(existing)
    return jsonify({'ok': True, 'added': added, 'total': len(existing)})


@app.route('/api/links/<int:idx>', methods=['DELETE'])
def api_links_delete(idx):
    links = load_links()
    if 0 <= idx < len(links):
        links.pop(idx)
        save_links(links)
    return jsonify({'ok': True})


@app.route('/api/links/clear', methods=['POST'])
def api_links_clear():
    save_links([])
    return jsonify({'ok': True})


@app.route('/api/file', methods=['DELETE'])
def api_file_delete():
    data = request.get_json(silent=True) or {}
    rel  = data.get('path', '')
    if not rel:
        return jsonify({'error': 'path erforderlich'}), 400
    try:
        target = (SORTED / rel).resolve()
        target.relative_to(SORTED.resolve())
    except (ValueError, Exception):
        return jsonify({'error': 'Ungültiger Pfad'}), 403
    if not target.is_file():
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    target.unlink()
    favs = load_favorites()
    if rel in favs:
        favs.discard(rel)
        save_favorites(favs)
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _open_browser(port):
    import time
    time.sleep(1.2)
    webbrowser.open(f'http://localhost:{port}')


if __name__ == '__main__':
    port = 5000
    for arg in sys.argv[1:]:
        if arg.startswith('--port='):
            port = int(arg.split('=')[1])

    print(f"Media Manager Web UI")
    print(f"URL:    http://localhost:{port}")
    print(f"Medien: {SORTED}")
    print(f"Strg+C zum Beenden\n")

    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
