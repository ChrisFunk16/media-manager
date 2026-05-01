#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI - Lokales Browser-Dashboard für den Media Manager
Aufruf: python webui.py [--port=5000]
"""

import json
import sys
import datetime
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

try:
    from flask import Flask, render_template_string, request, send_file, abort
except ImportError:
    print("Flask nicht installiert. Bitte ausführen:")
    print("  pip install flask")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

CATEGORIES = ['images', 'gifs', 'videos', 'hypno']
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
GIF_EXTS = {'.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.m4v'}


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


config = load_config()
if config['media_base_dir']:
    MEDIA_BASE = Path(config['media_base_dir']).expanduser()
else:
    MEDIA_BASE = BASE_DIR
SORTED = MEDIA_BASE / config['sorted']

app = Flask(__name__)
app.jinja_env.filters['url_path'] = lambda s: quote(str(s), safe='/')


def get_file_type(path):
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return 'image'
    if ext in GIF_EXTS:
        return 'gif'
    if ext in VIDEO_EXTS:
        return 'video'
    return 'other'


def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


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
    stats['total'] = {'count': total_count, 'size_str': format_size(total_bytes)}
    return stats


def search_files(query='', category=None, sort='date', page=1, per_page=40):
    query = query.lower().strip()
    search_dirs = ([SORTED / category] if category in CATEGORIES else
                   [SORTED / cat for cat in CATEGORIES])

    results = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        cat_name = search_dir.name
        for f in search_dir.rglob('*'):
            if not f.is_file():
                continue
            if query and query not in f.name.lower():
                continue
            try:
                stat = f.stat()
                results.append({
                    'name': f.name,
                    'category': cat_name,
                    'size_str': format_size(stat.st_size),
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                    'type': get_file_type(f),
                    'rel_path': str(f.relative_to(SORTED)).replace('\\', '/'),
                })
            except OSError:
                pass

    if sort == 'size':
        results.sort(key=lambda x: x['size'], reverse=True)
    elif sort == 'name':
        results.sort(key=lambda x: x['name'].lower())
    else:
        results.sort(key=lambda x: x['mtime'], reverse=True)

    total = len(results)
    start = (page - 1) * per_page
    return results[start:start + per_page], total


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

header{background:#12121e;padding:14px 24px;display:flex;align-items:center;gap:20px;border-bottom:1px solid #1e1e36;position:sticky;top:0;z-index:200}
header h1{font-size:1.15rem;color:#8aacff;letter-spacing:1px;white-space:nowrap}
nav a{color:#888;text-decoration:none;font-size:.875rem;padding:4px 10px;border-radius:6px;transition:all .15s}
nav a:hover,nav a.active{color:#8aacff;background:#1a1a30}

.container{max-width:1700px;margin:0 auto;padding:24px 20px}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:32px}
.stat-card{background:#12121e;border:1px solid #1e1e36;border-radius:10px;padding:18px;text-align:center;cursor:pointer;transition:border-color .2s,transform .15s}
.stat-card:hover{border-color:#8aacff;transform:translateY(-2px)}
.stat-num{font-size:2rem;font-weight:700;color:#8aacff}
.stat-label{color:#666;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.stat-size{color:#444;font-size:.75rem;margin-top:2px}

h2{color:#8aacff;margin-bottom:18px;font-size:1rem;letter-spacing:.5px}

.search-bar{background:#12121e;border:1px solid #1e1e36;border-radius:10px;padding:14px 18px;margin-bottom:20px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.search-bar input[type=text]{flex:1;min-width:180px;background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:8px 12px;color:#ddd;font-size:.875rem;outline:none;transition:border-color .2s}
.search-bar input:focus{border-color:#8aacff}
select{background:#0d0d1a;border:1px solid #2a2a45;border-radius:7px;padding:8px 12px;color:#ddd;font-size:.875rem;cursor:pointer;outline:none}
.btn{background:#8aacff;color:#0d0d1a;border:none;border-radius:7px;padding:8px 18px;cursor:pointer;font-size:.875rem;font-weight:700;transition:background .15s}
.btn:hover{background:#a8c4ff}
.btn-ghost{background:transparent;border:1px solid #2a2a45;color:#888}
.btn-ghost:hover{border-color:#8aacff;color:#8aacff}

.results-info{color:#555;font-size:.8rem;margin-bottom:14px}
.results-info strong{color:#8aacff}

.media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.card{background:#12121e;border:1px solid #1e1e36;border-radius:9px;overflow:hidden;cursor:pointer;transition:transform .15s,border-color .15s}
.card:hover{transform:translateY(-3px);border-color:#8aacff}
.thumb{width:100%;aspect-ratio:1;object-fit:cover;display:block;background:#0a0a15}
.thumb-ph{width:100%;aspect-ratio:1;background:#0a0a15;display:flex;align-items:center;justify-content:center;font-size:2.8rem;color:#2a2a45}
.card-body{padding:8px 10px}
.card-name{font-size:.72rem;color:#bbb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-meta{display:flex;justify-content:space-between;font-size:.68rem;color:#484848;margin-top:3px}
.card-cat{font-size:.65rem;color:#8aacff;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}

.pagination{display:flex;justify-content:center;gap:6px;margin-top:30px;flex-wrap:wrap}
.page-link{background:#12121e;border:1px solid #1e1e36;color:#888;padding:6px 13px;border-radius:7px;text-decoration:none;font-size:.8rem;transition:all .15s}
.page-link:hover{border-color:#8aacff;color:#8aacff}
.page-link.active{background:#8aacff;color:#0d0d1a;border-color:#8aacff;font-weight:700}

.lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.93);z-index:9000;align-items:center;justify-content:center;flex-direction:column}
.lb.open{display:flex}
.lb-media{max-width:94vw;max-height:86vh;border-radius:8px;object-fit:contain}
.lb-close{position:fixed;top:14px;right:20px;font-size:1.8rem;color:#888;cursor:pointer;z-index:9001;line-height:1}
.lb-close:hover{color:#fff}
.lb-caption{margin-top:12px;font-size:.78rem;color:#888;max-width:80vw;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

.empty{text-align:center;padding:70px 20px;color:#333}
.empty-icon{font-size:3.5rem;margin-bottom:14px}

@media(max-width:600px){
  .media-grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}
  .stats-grid{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>

{% macro card(item) %}
<div class="card"
     data-type="{{ item.type }}"
     data-src="/media/{{ item.rel_path | url_path }}"
     data-name="{{ item.name | e }}"
     onclick="openLb(this)">
  {% if item.type in ['image','gif'] %}
  <img class="thumb" src="/media/{{ item.rel_path | url_path }}" loading="lazy" alt="{{ item.name | e }}">
  {% elif item.type == 'video' %}
  <div class="thumb-ph">🎬</div>
  {% else %}
  <div class="thumb-ph">📄</div>
  {% endif %}
  <div class="card-body">
    <div class="card-name" title="{{ item.name | e }}">{{ item.name }}</div>
    <div class="card-meta"><span>{{ item.size_str }}</span><span>{{ item.date }}</span></div>
    <div class="card-cat">{{ item.category }}</div>
  </div>
</div>
{% endmacro %}

<header>
  <h1>📦 Media Manager</h1>
  <nav>
    <a href="/" class="{{ 'active' if view=='dashboard' }}">Dashboard</a>
    <a href="/browse" class="{{ 'active' if view=='browse' }}">Browse</a>
  </nav>
</header>

<div class="container">

{% if view == 'dashboard' %}

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-num">{{ stats.total.count }}</div>
    <div class="stat-label">Gesamt</div>
    <div class="stat-size">{{ stats.total.size_str }}</div>
  </div>
  {% for cat in ['images','gifs','videos','hypno'] %}
  <div class="stat-card" onclick="location.href='/browse?cat={{ cat }}'">
    <div class="stat-num">{{ stats[cat].count }}</div>
    <div class="stat-label">{{ cat }}</div>
    <div class="stat-size">{{ stats[cat].size_str }}</div>
  </div>
  {% endfor %}
</div>

<h2>Neueste Medien</h2>
{% if recent %}
<div class="media-grid">
  {% for item in recent %}{{ card(item) }}{% endfor %}
</div>
<div style="margin-top:20px;text-align:center">
  <a href="/browse" class="btn" style="display:inline-block;text-decoration:none">Alle anzeigen →</a>
</div>
{% else %}
<div class="empty"><div class="empty-icon">📂</div>Noch keine Medien vorhanden.</div>
{% endif %}

{% elif view == 'browse' %}

<form method="get" action="/browse">
  <div class="search-bar">
    <input type="text" name="q" placeholder="Dateiname suchen…" value="{{ q | e }}">
    <select name="cat">
      <option value="">Alle Kategorien</option>
      {% for c in ['images','gifs','videos','hypno'] %}
      <option value="{{ c }}"{{ ' selected' if cat==c }}>{{ c }}</option>
      {% endfor %}
    </select>
    <select name="sort">
      <option value="date"{{ ' selected' if sort=='date' }}>Datum</option>
      <option value="size"{{ ' selected' if sort=='size' }}>Größe</option>
      <option value="name"{{ ' selected' if sort=='name' }}>Name</option>
    </select>
    <button type="submit" class="btn">Suchen</button>
    <a href="/browse" class="btn btn-ghost" style="text-decoration:none">Reset</a>
  </div>
</form>

<div class="results-info">
  <strong>{{ total }}</strong> Dateien — Seite {{ page }} / {{ pages }}
</div>

{% if items %}
<div class="media-grid">
  {% for item in items %}{{ card(item) }}{% endfor %}
</div>
{% else %}
<div class="empty"><div class="empty-icon">🔍</div>Keine Ergebnisse</div>
{% endif %}

{% if pages > 1 %}
<div class="pagination">
  {% if page > 1 %}
  <a class="page-link" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&page={{ page-1 }}">‹</a>
  {% endif %}
  {% for p in range([1, page-2]|max, [pages+1, page+3]|min) %}
  <a class="page-link{{ ' active' if p==page }}" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&page={{ p }}">{{ p }}</a>
  {% endfor %}
  {% if page < pages %}
  <a class="page-link" href="?q={{ q | e }}&cat={{ cat }}&sort={{ sort }}&page={{ page+1 }}">›</a>
  {% endif %}
</div>
{% endif %}

{% endif %}

</div>

<!-- Lightbox: DOM constructed via safe API calls, no innerHTML -->
<div class="lb" id="lb">
  <span class="lb-close" onclick="closeLb()">✕</span>
  <div id="lb-inner"></div>
  <div class="lb-caption" id="lb-cap"></div>
</div>

<script>
function openLb(card) {
  var type = card.dataset.type;
  var src  = card.dataset.src;
  var name = card.dataset.name;

  var inner = document.getElementById('lb-inner');
  while (inner.firstChild) { inner.removeChild(inner.firstChild); }

  var el;
  if (type === 'video') {
    el = document.createElement('video');
    el.className = 'lb-media';
    el.controls = true;
    el.autoplay = true;
    el.src = src;
  } else {
    el = document.createElement('img');
    el.className = 'lb-media';
    el.alt = name;
    el.src = src;
  }
  inner.appendChild(el);

  document.getElementById('lb-cap').textContent = name;
  document.getElementById('lb').classList.add('open');
}

function closeLb() {
  var inner = document.getElementById('lb-inner');
  while (inner.firstChild) { inner.removeChild(inner.firstChild); }
  document.getElementById('lb').classList.remove('open');
}

document.getElementById('lb').addEventListener('click', function(e) {
  if (e.target === this) { closeLb(); }
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeLb(); }
});
</script>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def dashboard():
    stats = get_stats()
    recent, _ = search_files(sort='date', page=1, per_page=16)
    return render_template_string(TEMPLATE, view='dashboard', stats=stats, recent=recent)


@app.route('/browse')
def browse():
    q = request.args.get('q', '')
    cat = request.args.get('cat', '')
    sort = request.args.get('sort', 'date')
    page = max(1, int(request.args.get('page', 1) or 1))
    per_page = 40

    items, total = search_files(
        query=q,
        category=cat if cat in CATEGORIES else None,
        sort=sort,
        page=page,
        per_page=per_page,
    )
    pages = max(1, (total + per_page - 1) // per_page)

    return render_template_string(
        TEMPLATE,
        view='browse',
        items=items, total=total, page=page, pages=pages,
        q=q, cat=cat, sort=sort,
    )


@app.route('/media/<path:filepath>')
def serve_media(filepath):
    try:
        target = (SORTED / filepath).resolve()
        target.relative_to(SORTED.resolve())  # path-traversal guard
    except (ValueError, Exception):
        abort(403)
    if not target.is_file():
        abort(404)
    return send_file(target)


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
