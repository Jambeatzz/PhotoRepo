#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           LENS — Portfolio Build Script                  ║
║                                                          ║
║  Ausführen:  python build.py                             ║
║  Dann:       Alles auf GitHub pushen — fertig!           ║
╚══════════════════════════════════════════════════════════╝

Wie es funktioniert:
  1. Scannt den Ordner `bilder/` nach Unterordnern (= Alben)
  2. Liest alle Bilder pro Album automatisch ein
  3. Liest optionale album.json für Metadaten (Titel, Beschreibung)
  4. Generiert index.html + je eine album-*.html pro Album
  5. Alles ist statisches HTML — direkt auf GitHub Pages hostbar

Ordnerstruktur:
  bilder/
  ├── mein-erstes-album/
  │   ├── album.json          ← optional: Titel & Beschreibung
  │   ├── foto1.jpg
  │   ├── foto2.jpg
  │   └── ...
  └── noch-ein-album/
      └── ...

album.json Format (optional):
  {
    "name": "Mein Album",
    "description": "Kurze Beschreibung des Albums."
  }
  Ohne album.json wird der Ordnername als Titel verwendet.
"""

import os
import json
import re
import sys
from pathlib import Path

# ─── KONFIGURATION ────────────────────────────────────────────────────────────
BILDER_DIR   = "bilder"          # Ordner mit deinen Album-Unterordnern
OUTPUT_DIR   = "."               # Wo die HTML-Dateien landen (gleicher Ordner)
SITE_TITLE   = "LENS"            # Dein Portfolio-Name (in <title>)
AUTHOR_NAME  = "Dein Name"       # Dein Name
EMAIL        = "deine@email.de"  # Kontakt-E-Mail
INSTAGRAM    = "@dein_handle"    # Instagram-Handle
INSTAGRAM_URL= "https://instagram.com/dein_handle"
LOCATION     = "Deutschland"     # Dein Standort
COORDINATES  = "48°08'N — 11°34'E"  # Koordinaten im Hero
ABOUT_TEXT_1 = "Schreib hier etwas über dich — deinen fotografischen Ansatz, deine Inspiration und was dich zur Architektur- und Abstraktfotografie gebracht hat."
ABOUT_TEXT_2 = '\u201eFür mich ist Fotografie die Kunst, im Alltäglichen das Außergewöhnliche zu sehen \u2014 eine Fassade, ein Schattenwurf, eine Kurve aus Beton.\u201c'
STAT_YEARS   = "5+"
STAT_PHOTOS  = "200+"
STAT_CITIES  = "12"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
# ──────────────────────────────────────────────────────────────────────────────

# Farben für Terminal-Output
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def log(msg, color=RESET):    print(f"{color}{msg}{RESET}")
def ok(msg):                  log(f"  ✓  {msg}", GREEN)
def info(msg):                log(f"  →  {msg}", CYAN)
def warn(msg):                log(f"  ⚠  {msg}", YELLOW)

def slugify(name):
    """Ordnername → URL-freundlicher Slug"""
    s = name.lower().strip()
    s = re.sub(r"[äÄ]", "ae", s)
    s = re.sub(r"[öÖ]", "oe", s)
    s = re.sub(r"[üÜ]", "ue", s)
    s = re.sub(r"[ß]",  "ss", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def title_from_slug(slug):
    """slug → lesbarer Titel als Fallback"""
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())

def scan_albums():
    """Scannt bilder/ und gibt Liste von Album-Dicts zurück."""
    bilder_path = Path(BILDER_DIR)
    if not bilder_path.exists():
        warn(f"Ordner '{BILDER_DIR}/' nicht gefunden — wird erstellt.")
        bilder_path.mkdir()
        warn("Lege Unterordner mit Fotos in 'bilder/' an und führe das Skript erneut aus.")
        return []

    albums = []
    subdirs = sorted([d for d in bilder_path.iterdir() if d.is_dir()])

    if not subdirs:
        warn(f"Keine Unterordner in '{BILDER_DIR}/' gefunden.")
        return []

    for folder in subdirs:
        slug = slugify(folder.name)

        # Metadaten aus album.json lesen (optional)
        meta_file = folder / "album.json"
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
            name        = meta.get("name", title_from_slug(slug))
            description = meta.get("description", "")
        else:
            name        = title_from_slug(folder.name)
            description = ""

        # Alle Bilddateien sammeln & natürlich sortieren
        photos = sorted(
            [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS],
            key=lambda p: natural_sort_key(p.name)
        )

        photo_list = [
            {
                "src":   f"{BILDER_DIR}/{folder.name}/{p.name}",
                "title": p.stem.replace("-", " ").replace("_", " ").title()
            }
            for p in photos
        ]

        albums.append({
            "slug":        slug,
            "folder":      folder.name,
            "name":        name,
            "description": description,
            "photos":      photo_list,
            "count":       len(photo_list),
        })

        status = f"{len(photo_list)} Fotos" if photo_list else "leer"
        info(f"{folder.name}  →  '{name}'  ({status})")

    return albums

def natural_sort_key(s):
    """Natürliche Sortierung: foto2 kommt vor foto10"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", s)]

# ─── CSS & JS (geteilt) ──────────────────────────────────────────────────────
SHARED_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --black: #0a0a0a; --off-white: #f2efe9; --warm-gray: #b8b0a4;
      --accent: #c8a96e; --text: #1a1a1a;
      --serif: 'Playfair Display', Georgia, serif;
      --sans: 'Barlow', sans-serif;
      --condensed: 'Barlow Condensed', sans-serif;
    }
    html { scroll-behavior: smooth; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:none; } }
    .reveal { opacity:0; transform:translateY(30px); transition:opacity .8s ease,transform .8s ease; }
    .reveal.visible { opacity:1; transform:none; }
    .cursor { position:fixed; width:8px; height:8px; background:var(--accent); border-radius:50%;
      pointer-events:none; z-index:9999; transform:translate(-50%,-50%); transition:width .2s,height .2s; }
    .cursor-ring { position:fixed; width:32px; height:32px; border:1px solid var(--accent); border-radius:50%;
      pointer-events:none; z-index:9998; transform:translate(-50%,-50%); transition:all .12s ease-out; opacity:.6; }
    .cursor.hover { width:12px; height:12px; }
    .cursor-ring.hover { width:52px; height:52px; opacity:.2; }
    @media(max-width:900px) { body { cursor:auto !important; } .cursor,.cursor-ring { display:none; } }
"""

CURSOR_JS = """
  const _cur = document.getElementById('cursor');
  const _ring = document.getElementById('cursorRing');
  if (_cur && _ring) {
    let mx=0,my=0,rx=0,ry=0;
    document.addEventListener('mousemove', e => {
      mx=e.clientX; my=e.clientY;
      _cur.style.left=mx+'px'; _cur.style.top=my+'px';
    });
    (function animRing(){ rx+=(mx-rx)*.12; ry+=(my-ry)*.12;
      _ring.style.left=rx+'px'; _ring.style.top=ry+'px';
      requestAnimationFrame(animRing); })();
    document.querySelectorAll('a,button,[data-hover]').forEach(el => {
      el.addEventListener('mouseenter', ()=>{ _cur.classList.add('hover'); _ring.classList.add('hover'); });
      el.addEventListener('mouseleave', ()=>{ _cur.classList.remove('hover'); _ring.classList.remove('hover'); });
    });
  }
  const _obs = new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')}),{threshold:.08});
  document.querySelectorAll('.reveal').forEach(el=>_obs.observe(el));
"""

# ─── INDEX.HTML ───────────────────────────────────────────────────────────────
def build_index(albums):
    # Album-Grid JS-Objekte
    albums_js = json.dumps([{
        "name": a["name"], "slug": a["slug"],
        "description": a["description"], "count": a["count"],
        "cover": a["photos"][0]["src"] if a["photos"] else ""
    } for a in albums], ensure_ascii=False, indent=2)

    grid_positions = [
        "grid-column:span 7;grid-row:span 6",
        "grid-column:span 5;grid-row:span 4",
        "grid-column:span 5;grid-row:span 2",
        "grid-column:span 4;grid-row:span 5",
        "grid-column:span 4;grid-row:span 5",
        "grid-column:span 4;grid-row:span 5",
        "grid-column:span 5;grid-row:span 4",
        "grid-column:span 7;grid-row:span 4",
        "grid-column:span 6;grid-row:span 5",
        "grid-column:span 6;grid-row:span 5",
    ]

    n = len(albums)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{SITE_TITLE} — Architektur &amp; Abstrakt</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Barlow:wght@300;400;500&family=Barlow+Condensed:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
{SHARED_CSS}
    body {{ background:var(--off-white); color:var(--text); font-family:var(--sans); font-weight:300; overflow-x:hidden; cursor:none; }}
    nav {{ position:fixed; top:0; left:0; right:0; z-index:100; display:flex; justify-content:space-between;
      align-items:center; padding:2rem 3rem; }}
    .nav-logo {{ font-family:var(--condensed); font-size:1.4rem; font-weight:600; letter-spacing:.35em;
      text-transform:uppercase; color:var(--black); text-decoration:none; }}
    .nav-links {{ display:flex; gap:3rem; list-style:none; }}
    .nav-links a {{ font-family:var(--condensed); font-size:.8rem; letter-spacing:.2em; text-transform:uppercase;
      color:var(--black); text-decoration:none; opacity:.6; transition:opacity .2s; }}
    .nav-links a:hover {{ opacity:1; }}
    .hero {{ min-height:100vh; display:grid; grid-template-columns:1fr 1fr; overflow:hidden; }}
    .hero-left {{ display:flex; flex-direction:column; justify-content:flex-end; padding:8rem 3rem 5rem; }}
    .hero-eyebrow {{ font-family:var(--condensed); font-size:.75rem; letter-spacing:.4em; text-transform:uppercase;
      color:var(--accent); margin-bottom:1.5rem; opacity:0; animation:fadeUp .8s ease forwards .3s; }}
    .hero-title {{ font-family:var(--serif); font-size:clamp(3.5rem,6vw,6rem); font-weight:400; line-height:1.0;
      margin-bottom:2rem; opacity:0; animation:fadeUp .8s ease forwards .5s; }}
    .hero-title em {{ display:block; font-style:italic; color:var(--warm-gray); }}
    .hero-desc {{ font-size:.9rem; line-height:1.8; color:var(--warm-gray); max-width:320px; margin-bottom:3rem;
      opacity:0; animation:fadeUp .8s ease forwards .7s; }}
    .hero-cta {{ display:inline-flex; align-items:center; gap:1rem; font-family:var(--condensed); font-size:.8rem;
      letter-spacing:.25em; text-transform:uppercase; color:var(--black); text-decoration:none;
      opacity:0; animation:fadeUp .8s ease forwards .9s; }}
    .hero-cta::after {{ content:''; display:block; width:40px; height:1px; background:var(--accent); transition:width .3s; }}
    .hero-cta:hover::after {{ width:80px; }}
    .hero-right {{ background:var(--black); overflow:hidden; }}
    .hero-right svg {{ width:100%; height:100%; }}
    .hero-number {{ position:absolute; bottom:3rem; left:3rem; font-family:var(--condensed); font-size:.7rem;
      letter-spacing:.3em; color:var(--warm-gray); opacity:0; animation:fadeUp .8s ease forwards 1.1s; }}
    .albums-section {{ padding:8rem 3rem; }}
    .section-header {{ display:flex; align-items:baseline; gap:2rem; margin-bottom:4rem; }}
    .section-title {{ font-family:var(--serif); font-size:clamp(2rem,4vw,3.5rem); font-weight:400; }}
    .section-title em {{ font-style:italic; color:var(--warm-gray); }}
    .section-line {{ flex:1; height:1px; background:linear-gradient(to right,var(--warm-gray),transparent); opacity:.4; }}
    .section-count {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.3em; color:var(--accent); }}
    .album-grid {{ display:grid; grid-template-columns:repeat(12,1fr); grid-auto-rows:80px; gap:6px; }}
    .album-card {{ position:relative; overflow:hidden; cursor:none; text-decoration:none; display:block; }}
    .album-cover {{ width:100%; height:100%; object-fit:cover; display:block;
      transition:transform .7s cubic-bezier(.25,.46,.45,.94); }}
    .album-card:hover .album-cover {{ transform:scale(1.06); }}
    .album-overlay {{ position:absolute; inset:0;
      background:linear-gradient(to top,rgba(10,10,10,.85) 0%,rgba(10,10,10,.2) 50%,transparent 100%);
      display:flex; flex-direction:column; justify-content:flex-end; padding:1.8rem; transition:background .4s; }}
    .album-card:hover .album-overlay {{ background:linear-gradient(to top,rgba(10,10,10,.92) 0%,rgba(10,10,10,.4) 60%,transparent 100%); }}
    .album-count-badge {{ position:absolute; top:1rem; right:1rem; font-family:var(--condensed); font-size:.65rem;
      letter-spacing:.25em; text-transform:uppercase; color:var(--accent); background:rgba(10,10,10,.7);
      border:1px solid rgba(200,169,110,.3); padding:.3rem .7rem; backdrop-filter:blur(4px); }}
    .album-name {{ font-family:var(--serif); font-size:1.1rem; color:white; font-weight:400; margin-bottom:.3rem; }}
    .album-meta {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.2em; color:var(--accent); text-transform:uppercase; }}
    .album-arrow {{ position:absolute; bottom:1.8rem; right:1.8rem; width:36px; height:36px;
      border:1px solid rgba(200,169,110,.4); border-radius:50%; display:flex; align-items:center; justify-content:center;
      color:var(--accent); font-size:.9rem; transform:translateX(10px); opacity:0; transition:all .3s; }}
    .album-card:hover .album-arrow {{ transform:translateX(0); opacity:1; }}
    .empty-albums {{ padding:6rem 3rem; text-align:center; opacity:.4; font-family:var(--condensed);
      font-size:.8rem; letter-spacing:.3em; text-transform:uppercase; color:var(--warm-gray); }}
    .about-section {{ padding:8rem 3rem; background:var(--black); color:var(--off-white); display:grid;
      grid-template-columns:1fr 1fr; gap:6rem; align-items:center; }}
    .about-image-wrap {{ position:relative; }}
    .about-img {{ width:100%; aspect-ratio:3/4; object-fit:cover; display:block; background:#1a1a1a; }}
    .about-img-deco {{ position:absolute; top:-2rem; right:-2rem; width:60%; height:60%;
      border:1px solid var(--accent); opacity:.3; pointer-events:none; }}
    .about-eyebrow {{ font-family:var(--condensed); font-size:.75rem; letter-spacing:.4em; text-transform:uppercase; color:var(--accent); margin-bottom:2rem; }}
    .about-title {{ font-family:var(--serif); font-size:clamp(2rem,3.5vw,3rem); font-weight:400; line-height:1.2; margin-bottom:2rem; }}
    .about-title em {{ font-style:italic; color:var(--warm-gray); }}
    .about-text {{ font-size:.9rem; line-height:2; color:rgba(242,239,233,.6); margin-bottom:1.5rem; }}
    .about-stats {{ display:flex; gap:3rem; margin-top:3rem; padding-top:3rem; border-top:1px solid rgba(255,255,255,.1); }}
    .stat-num {{ font-family:var(--serif); font-size:2.5rem; color:var(--accent); display:block; }}
    .stat-label {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.25em; text-transform:uppercase; color:rgba(242,239,233,.4); }}
    .contact-section {{ padding:8rem 3rem; display:grid; grid-template-columns:1fr 1fr; gap:6rem; align-items:start; }}
    .contact-left h2 {{ font-family:var(--serif); font-size:clamp(2rem,4vw,3.5rem); font-weight:400; line-height:1.1; margin-bottom:2rem; }}
    .contact-left h2 em {{ font-style:italic; color:var(--warm-gray); }}
    .contact-left p {{ font-size:.9rem; line-height:1.8; color:var(--warm-gray); max-width:400px; }}
    .contact-item {{ display:flex; align-items:flex-start; gap:2rem; padding:2rem 0; border-bottom:1px solid rgba(26,26,26,.1); }}
    .contact-item:first-child {{ border-top:1px solid rgba(26,26,26,.1); }}
    .contact-label {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.3em; text-transform:uppercase; color:var(--accent); min-width:80px; }}
    .contact-value {{ font-family:var(--serif); font-size:1.1rem; color:var(--black); text-decoration:none; transition:color .2s; }}
    .contact-value:hover {{ color:var(--accent); }}
    .social-links {{ display:flex; gap:1.5rem; margin-top:3rem; }}
    .social-link {{ font-family:var(--condensed); font-size:.75rem; letter-spacing:.2em; text-transform:uppercase;
      color:var(--black); text-decoration:none; display:flex; align-items:center; gap:.5rem; opacity:.6; transition:opacity .2s; }}
    .social-link::before {{ content:'↗'; color:var(--accent); }}
    .social-link:hover {{ opacity:1; }}
    footer {{ padding:2rem 3rem; background:var(--black); display:flex; justify-content:space-between; }}
    footer p {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.2em; color:rgba(242,239,233,.3); text-transform:uppercase; }}
    @media(max-width:900px) {{
      nav {{ padding:1.5rem; }} .nav-links {{ gap:1.5rem; }}
      .hero {{ grid-template-columns:1fr; }} .hero-left {{ padding:7rem 1.5rem 3rem; }} .hero-right {{ height:55vw; }}
      .albums-section {{ padding:5rem 1.5rem; }}
      .album-grid {{ grid-template-columns:repeat(6,1fr); grid-auto-rows:60px; }}
      .about-section {{ grid-template-columns:1fr; gap:3rem; padding:5rem 1.5rem; }}
      .contact-section {{ grid-template-columns:1fr; gap:3rem; padding:5rem 1.5rem; }}
    }}
  </style>
</head>
<body>
<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<nav>
  <a href="index.html" class="nav-logo" data-hover>{SITE_TITLE}</a>
  <ul class="nav-links">
    <li><a href="#gallery" data-hover>Alben</a></li>
    <li><a href="#about" data-hover>Über mich</a></li>
    <li><a href="#contact" data-hover>Kontakt</a></li>
  </ul>
</nav>
<section class="hero">
  <div class="hero-left" style="position:relative">
    <p class="hero-eyebrow">Architektur &amp; Abstrakt — Portfolio</p>
    <h1 class="hero-title">Struktur<br><em>trifft Licht.</em></h1>
    <p class="hero-desc">Fotografische Erkundung von Form, Geometrie und dem Spiel zwischen Licht und Schatten in urbanen Räumen.</p>
    <a href="#gallery" class="hero-cta" data-hover>Alben entdecken</a>
    <p class="hero-number">{COORDINATES}</p>
  </div>
  <div class="hero-right">
    <svg viewBox="0 0 800 900" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
      <rect width="800" height="900" fill="#1a1a1a"/>
      <rect x="100" y="0" width="8" height="900" fill="#2d2d2d"/>
      <rect x="200" y="80" width="8" height="820" fill="#252525"/>
      <rect x="350" y="0" width="12" height="900" fill="#333"/>
      <rect x="500" y="60" width="8" height="840" fill="#2d2d2d"/>
      <rect x="650" y="0" width="8" height="900" fill="#252525"/>
      <rect x="100" y="450" width="560" height="3" fill="#c8a96e" opacity=".3"/>
      <circle cx="400" cy="450" r="180" fill="none" stroke="#c8a96e" stroke-width="1" opacity=".15"/>
    </svg>
  </div>
</section>
<section class="albums-section" id="gallery">
  <div class="section-header reveal">
    <h2 class="section-title">Alben <em>&amp; Serien</em></h2>
    <div class="section-line"></div>
    <span class="section-count">{n} {'Album' if n == 1 else 'Alben'}</span>
  </div>
  <div class="album-grid" id="albumGrid">
  </div>
  {'<p class="empty-albums">Noch keine Alben gefunden.<br>Lege Unterordner in bilder/ an und führe build.py aus.</p>' if n == 0 else ''}
</section>
<section class="about-section" id="about">
  <div class="about-image-wrap reveal">
    <svg class="about-img" viewBox="0 0 400 533" xmlns="http://www.w3.org/2000/svg">
      <rect width="400" height="533" fill="#1a1a1a"/>
      <defs><radialGradient id="gp" cx="40%" cy="35%"><stop offset="0%" style="stop-color:#2a2520;stop-opacity:.8"/><stop offset="100%" style="stop-color:#0a0a0a;stop-opacity:0"/></radialGradient></defs>
      <rect x="0" y="0" width="400" height="533" fill="url(#gp)"/>
      <circle cx="200" cy="180" r="80" fill="#2a2520"/>
      <rect x="80" y="300" width="240" height="233" fill="#222"/>
      <text x="200" y="490" text-anchor="middle" font-family="Georgia" font-size="12" fill="#555" letter-spacing="2">Dein Foto hier</text>
    </svg>
    <div class="about-img-deco"></div>
  </div>
  <div class="reveal">
    <p class="about-eyebrow">Über den Fotografen</p>
    <h2 class="about-title">{AUTHOR_NAME}<br><em>hinter der Kamera.</em></h2>
    <p class="about-text">{ABOUT_TEXT_1}</p>
    <p class="about-text">{ABOUT_TEXT_2}</p>
    <div class="about-stats">
      <div><span class="stat-num">{STAT_YEARS}</span><span class="stat-label">Jahre Erfahrung</span></div>
      <div><span class="stat-num">{STAT_PHOTOS}</span><span class="stat-label">Aufnahmen</span></div>
      <div><span class="stat-num">{STAT_CITIES}</span><span class="stat-label">Städte</span></div>
    </div>
  </div>
</section>
<section class="contact-section" id="contact">
  <div class="contact-left reveal">
    <h2>Lass uns<br><em>in Kontakt treten.</em></h2>
    <p>Für Kooperationen, Prints oder einfach um mehr über meine Arbeit zu erfahren — meld dich gerne.</p>
    <div class="social-links">
      <a href="{INSTAGRAM_URL}" target="_blank" class="social-link" data-hover>Instagram</a>
    </div>
  </div>
  <div class="contact-right reveal">
    <div class="contact-item"><span class="contact-label">E-Mail</span><a href="mailto:{EMAIL}" class="contact-value" data-hover>{EMAIL}</a></div>
    <div class="contact-item"><span class="contact-label">Instagram</span><a href="{INSTAGRAM_URL}" target="_blank" class="contact-value" data-hover>{INSTAGRAM}</a></div>
    <div class="contact-item"><span class="contact-label">Standort</span><span class="contact-value">{LOCATION}</span></div>
    <div class="contact-item"><span class="contact-label">Verfügbar</span><span class="contact-value">Ja — für Projekte</span></div>
  </div>
</section>
<footer>
  <p>© 2025 {AUTHOR_NAME} — Alle Rechte vorbehalten</p>
  <p>Architektur &amp; Abstrakt</p>
</footer>
<script>
  const ALBUMS = {albums_js};
  const GRID_POS = {json.dumps(grid_positions)};

  const grid = document.getElementById('albumGrid');
  if (grid && ALBUMS.length > 0) {{
    ALBUMS.forEach((album, i) => {{
      const pos = GRID_POS[i % GRID_POS.length];
      const card = document.createElement('a');
      card.href = 'album-' + album.slug + '.html';
      card.className = 'album-card';
      card.setAttribute('data-hover', '');
      card.style.cssText = pos + ';';
      const coverHtml = album.cover
        ? `<img class="album-cover" src="${{album.cover}}" alt="${{album.name}}" loading="lazy">`
        : `<div class="album-cover" style="background:#1e1e1e;display:flex;align-items:center;justify-content:center;">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="6" y="10" width="36" height="28" rx="2" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/>
              <circle cx="17" cy="21" r="4" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/>
              <path d="M6 34L16 24L22 30L30 22L42 34" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/>
            </svg>
           </div>`;
      card.innerHTML = coverHtml + `
        <div class="album-overlay">
          <p class="album-name">${{album.name}}</p>
          <p class="album-meta">${{album.description || 'Album'}}</p>
        </div>
        <span class="album-count-badge">${{album.count}} ${{album.count === 1 ? 'Foto' : 'Fotos'}}</span>
        <div class="album-arrow">→</div>`;
      grid.appendChild(card);
    }});
  }}
{CURSOR_JS}
</script>
</body>
</html>"""


# ─── ALBUM-SEITE ──────────────────────────────────────────────────────────────
def build_album_page(album, all_albums):
    photos_js = json.dumps(album["photos"], ensure_ascii=False)
    idx = next((i for i, a in enumerate(all_albums) if a["slug"] == album["slug"]), 0)
    next_album = all_albums[(idx + 1) % len(all_albums)] if len(all_albums) > 1 else None
    prev_album = all_albums[(idx - 1) % len(all_albums)] if len(all_albums) > 1 else None

    title_parts = album["name"].split()
    if len(title_parts) > 1:
        title_html = " ".join(title_parts[:-1]) + "<br><em>" + title_parts[-1] + "</em>"
    else:
        title_html = album["name"]

    next_section = ""
    if next_album:
        next_section = f"""
<div class="next-album-section">
  <div>
    <p class="next-label">Nächstes Album</p>
    <p class="next-name">{next_album['name']}</p>
  </div>
  <a href="album-{next_album['slug']}.html" class="next-link" data-hover>Album öffnen</a>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{album['name']} — {SITE_TITLE}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Barlow:wght@300;400;500&family=Barlow+Condensed:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
{SHARED_CSS}
    body {{ background:var(--black); color:var(--off-white); font-family:var(--sans); font-weight:300; overflow-x:hidden; cursor:none; }}
    nav {{ position:fixed; top:0; left:0; right:0; z-index:100; display:flex; justify-content:space-between; align-items:center;
      padding:2rem 3rem; background:linear-gradient(to bottom,rgba(10,10,10,.9),transparent); }}
    .nav-logo {{ font-family:var(--condensed); font-size:1.4rem; font-weight:600; letter-spacing:.35em;
      text-transform:uppercase; color:var(--off-white); text-decoration:none; }}
    .nav-back {{ font-family:var(--condensed); font-size:.8rem; letter-spacing:.2em; text-transform:uppercase;
      color:var(--off-white); text-decoration:none; opacity:.6; transition:opacity .2s;
      display:flex; align-items:center; gap:.8rem; }}
    .nav-back::before {{ content:'←'; color:var(--accent); }}
    .nav-back:hover {{ opacity:1; }}
    .album-header {{ padding:10rem 3rem 4rem; position:relative; border-bottom:1px solid rgba(255,255,255,.06); }}
    .album-header::before {{ content:''; position:absolute; inset:0;
      background:radial-gradient(ellipse at 80% 50%,rgba(200,169,110,.05) 0%,transparent 70%); pointer-events:none; }}
    .album-breadcrumb {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.4em; text-transform:uppercase;
      color:var(--accent); margin-bottom:1.5rem; opacity:0; animation:fadeUp .6s ease forwards .2s; }}
    .album-title {{ font-family:var(--serif); font-size:clamp(3rem,6vw,5.5rem); font-weight:400; line-height:1;
      margin-bottom:1.5rem; opacity:0; animation:fadeUp .6s ease forwards .4s; }}
    .album-title em {{ font-style:italic; color:var(--warm-gray); }}
    .album-meta-row {{ display:flex; align-items:center; gap:3rem; opacity:0; animation:fadeUp .6s ease forwards .6s; }}
    .album-desc {{ font-size:.9rem; line-height:1.7; color:rgba(242,239,233,.5); max-width:500px; }}
    .album-stats {{ display:flex; gap:2.5rem; margin-left:auto; }}
    .album-stat .num {{ font-family:var(--serif); font-size:1.6rem; color:var(--accent); display:block; }}
    .album-stat .lbl {{ font-family:var(--condensed); font-size:.65rem; letter-spacing:.25em; text-transform:uppercase; color:rgba(242,239,233,.3); }}
    .view-controls {{ padding:2rem 3rem; display:flex; align-items:center; gap:1rem; border-bottom:1px solid rgba(255,255,255,.06); }}
    .view-label {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.2em; text-transform:uppercase; color:rgba(242,239,233,.25); margin-right:auto; }}
    .view-btn {{ background:none; border:1px solid rgba(255,255,255,.15); color:rgba(242,239,233,.4);
      padding:.5rem .9rem; font-family:var(--condensed); font-size:.7rem; letter-spacing:.2em; text-transform:uppercase;
      cursor:none; transition:all .2s; }}
    .view-btn.active {{ border-color:var(--accent); color:var(--accent); }}
    .view-btn:hover {{ border-color:rgba(200,169,110,.4); color:rgba(200,169,110,.7); }}
    .photos-section {{ padding:3rem; }}
    .grid-masonry {{ columns:3; column-gap:6px; }}
    .grid-masonry .photo-item {{ break-inside:avoid; margin-bottom:6px; }}
    .grid-uniform {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; }}
    .grid-uniform .photo-item {{ aspect-ratio:4/3; }}
    .grid-wide {{ display:flex; flex-direction:column; gap:6px; max-width:900px; margin:0 auto; }}
    .photo-item {{ position:relative; overflow:hidden; cursor:none; }}
    .photo-img {{ width:100%; height:auto; display:block; transition:transform .6s cubic-bezier(.25,.46,.45,.94); }}
    .grid-uniform .photo-img {{ height:100%; object-fit:cover; }}
    .photo-item:hover .photo-img {{ transform:scale(1.04); }}
    .photo-overlay {{ position:absolute; inset:0; background:linear-gradient(to top,rgba(10,10,10,.75) 0%,transparent 50%);
      opacity:0; transition:opacity .3s; display:flex; flex-direction:column; justify-content:flex-end; padding:1.2rem; }}
    .photo-item:hover .photo-overlay {{ opacity:1; }}
    .photo-item-title {{ font-family:var(--serif); font-size:.95rem; color:white; margin-bottom:.2rem; }}
    .photo-item-num {{ font-family:var(--condensed); font-size:.65rem; letter-spacing:.25em; color:var(--accent); text-transform:uppercase; }}
    .expand-icon {{ position:absolute; top:1rem; right:1rem; width:30px; height:30px;
      border:1px solid rgba(255,255,255,.25); background:rgba(10,10,10,.5); color:white; font-size:.75rem;
      display:flex; align-items:center; justify-content:center; opacity:0; transition:opacity .3s; backdrop-filter:blur(4px); }}
    .photo-item:hover .expand-icon {{ opacity:1; }}
    .placeholder-card {{ background:#1a1a1a; display:flex; flex-direction:column;
      align-items:center; justify-content:center; min-height:200px; gap:.8rem; padding:2rem; }}
    .placeholder-card p {{ font-family:var(--condensed); font-size:.65rem; letter-spacing:.2em; text-transform:uppercase; color:rgba(242,239,233,.2); text-align:center; }}
    .lightbox {{ position:fixed; inset:0; z-index:1000; background:rgba(5,5,5,.98);
      display:flex; align-items:center; justify-content:center; opacity:0; pointer-events:none; transition:opacity .35s; }}
    .lightbox.open {{ opacity:1; pointer-events:all; }}
    .lb-img-wrap {{ max-width:90vw; max-height:85vh; display:flex; align-items:center; justify-content:center; }}
    .lb-img {{ max-width:88vw; max-height:82vh; object-fit:contain; display:block; transition:opacity .2s; }}
    .lb-close {{ position:fixed; top:2rem; right:3rem; font-family:var(--condensed); font-size:.75rem;
      letter-spacing:.3em; text-transform:uppercase; color:rgba(242,239,233,.4); background:none; border:none; cursor:none; transition:color .2s; }}
    .lb-close:hover {{ color:var(--off-white); }}
    .lb-nav {{ position:fixed; top:50%; transform:translateY(-50%); background:none;
      border:1px solid rgba(255,255,255,.1); color:rgba(255,255,255,.5); padding:1.2rem 1.4rem;
      cursor:none; font-size:1rem; transition:all .2s; backdrop-filter:blur(8px); }}
    .lb-nav:hover {{ border-color:var(--accent); color:var(--accent); }}
    .lb-nav.prev {{ left:2rem; }} .lb-nav.next {{ right:2rem; }}
    .lb-info {{ position:fixed; bottom:0; left:0; right:0; padding:2rem 3rem; display:flex;
      justify-content:space-between; align-items:flex-end; background:linear-gradient(to top,rgba(5,5,5,.9),transparent); }}
    .lb-title {{ font-family:var(--serif); font-size:1.2rem; color:var(--off-white); }}
    .lb-counter {{ font-family:var(--condensed); font-size:.75rem; letter-spacing:.3em; color:var(--accent); }}
    .lb-progress {{ position:fixed; bottom:0; left:0; height:1px; background:var(--accent); transition:width .3s; }}
    .next-album-section {{ padding:5rem 3rem; border-top:1px solid rgba(255,255,255,.06);
      display:flex; justify-content:space-between; align-items:center; }}
    .next-label {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.3em; text-transform:uppercase; color:rgba(242,239,233,.3); margin-bottom:.8rem; }}
    .next-name {{ font-family:var(--serif); font-size:2rem; color:var(--off-white); }}
    .next-link {{ font-family:var(--condensed); font-size:.8rem; letter-spacing:.25em; text-transform:uppercase;
      color:var(--accent); text-decoration:none; display:flex; align-items:center; gap:1rem; transition:gap .3s; }}
    .next-link::after {{ content:'→'; }}
    .next-link:hover {{ gap:1.5rem; }}
    footer {{ padding:2rem 3rem; background:rgba(0,0,0,.5); display:flex; justify-content:space-between; }}
    footer p {{ font-family:var(--condensed); font-size:.7rem; letter-spacing:.2em; color:rgba(242,239,233,.2); text-transform:uppercase; }}
    @media(max-width:900px) {{
      nav {{ padding:1.5rem; }}
      .album-header {{ padding:7rem 1.5rem 3rem; }}
      .album-meta-row {{ flex-direction:column; align-items:flex-start; gap:1.5rem; }}
      .album-stats {{ margin-left:0; }}
      .view-controls {{ padding:1.5rem; }}
      .photos-section {{ padding:1.5rem; }}
      .grid-masonry {{ columns:2; }}
      .grid-uniform {{ grid-template-columns:repeat(2,1fr); }}
      .next-album-section {{ flex-direction:column; gap:2rem; align-items:flex-start; padding:3rem 1.5rem; }}
      footer {{ padding:1.5rem; }}
    }}
    @media(max-width:500px) {{ .grid-masonry {{ columns:1; }} .grid-uniform {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<nav>
  <a href="index.html" class="nav-logo" data-hover>{SITE_TITLE}</a>
  <a href="index.html" class="nav-back" data-hover>Alle Alben</a>
</nav>
<header class="album-header">
  <p class="album-breadcrumb">Portfolio — {album['name']}</p>
  <h1 class="album-title">{title_html}</h1>
  <div class="album-meta-row">
    <p class="album-desc">{album['description'] or 'Eine fotografische Serie.'}</p>
    <div class="album-stats">
      <div class="album-stat"><span class="num">{album['count']}</span><span class="lbl">{'Foto' if album['count'] == 1 else 'Fotos'}</span></div>
    </div>
  </div>
</header>
<div class="view-controls">
  <span class="view-label">Ansicht</span>
  <button class="view-btn active" id="btn-masonry" onclick="setView('masonry')" data-hover>Mosaik</button>
  <button class="view-btn" id="btn-uniform" onclick="setView('uniform')" data-hover>Raster</button>
  <button class="view-btn" id="btn-wide" onclick="setView('wide')" data-hover>Einzeln</button>
</div>
<section class="photos-section">
  <div class="grid-masonry" id="photoGrid"></div>
</section>
{next_section}
<footer>
  <p>© 2025 {AUTHOR_NAME}</p>
  <p>{album['name']}</p>
</footer>
<div class="lightbox" id="lightbox">
  <button class="lb-close" onclick="closeLB()" data-hover>Schließen ✕</button>
  <button class="lb-nav prev" onclick="navLB(-1)" data-hover>←</button>
  <div class="lb-img-wrap"><img src="" alt="" class="lb-img" id="lbImg"/></div>
  <button class="lb-nav next" onclick="navLB(1)" data-hover>→</button>
  <div class="lb-info">
    <p class="lb-title" id="lbTitle"></p>
    <p class="lb-counter" id="lbCounter"></p>
  </div>
  <div class="lb-progress" id="lbProgress"></div>
</div>
<script>
  const PHOTOS = {photos_js};
  let lbIdx = 0;

  function renderGrid() {{
    const grid = document.getElementById('photoGrid');
    if (!PHOTOS.length) {{
      grid.innerHTML = '<div class="placeholder-card" style="min-height:400px"><svg width="48" height="48" viewBox="0 0 48 48" fill="none"><rect x="6" y="10" width="36" height="28" rx="2" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/><circle cx="17" cy="21" r="4" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/><path d="M6 34L16 24L22 30L30 22L42 34" stroke="#c8a96e" stroke-width="1" stroke-opacity=".3"/></svg><p>Noch keine Fotos in diesem Album.<br>Bilder in bilder/{album['folder']}/ ablegen &amp; build.py ausführen.</p></div>';
      return;
    }}
    grid.innerHTML = '';
    PHOTOS.forEach((p, i) => {{
      const div = document.createElement('div');
      div.className = 'photo-item';
      div.setAttribute('data-hover','');
      div.onclick = () => openLB(i);
      div.innerHTML = `
        <img class="photo-img" src="${{p.src}}" alt="${{p.title}}" loading="lazy"
          onerror="this.parentElement.innerHTML='<div class=\\'placeholder-card\\'><p>${{p.src.split('/').pop()}}</p></div>'"/>
        <div class="photo-overlay">
          <p class="photo-item-title">${{p.title}}</p>
          <p class="photo-item-num">No. ${{String(i+1).padStart(2,'0')}}</p>
        </div>
        <div class="expand-icon">⤢</div>`;
      grid.appendChild(div);
    }});
  }}

  function setView(v) {{
    document.getElementById('photoGrid').className = 'grid-' + v;
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + v).classList.add('active');
  }}

  function openLB(i) {{ lbIdx=i; updateLB(); document.getElementById('lightbox').classList.add('open'); document.body.style.overflow='hidden'; }}
  function closeLB() {{ document.getElementById('lightbox').classList.remove('open'); document.body.style.overflow=''; }}
  function navLB(d) {{ lbIdx=(lbIdx+d+PHOTOS.length)%PHOTOS.length; updateLB(); }}
  function updateLB() {{
    const p=PHOTOS[lbIdx], img=document.getElementById('lbImg');
    img.style.opacity='0'; img.src=p.src; img.onload=()=>img.style.opacity='1';
    document.getElementById('lbTitle').textContent=p.title;
    document.getElementById('lbCounter').textContent=(lbIdx+1)+' / '+PHOTOS.length;
    document.getElementById('lbProgress').style.width=((lbIdx+1)/PHOTOS.length*100).toFixed(1)+'%';
  }}
  document.getElementById('lightbox').addEventListener('click', e => {{ if(e.target===e.currentTarget||e.target===document.querySelector('.lb-img-wrap')) closeLB(); }});
  document.addEventListener('keydown', e => {{
    if(!document.getElementById('lightbox').classList.contains('open')) return;
    if(e.key==='Escape') closeLB();
    if(e.key==='ArrowRight') navLB(1);
    if(e.key==='ArrowLeft') navLB(-1);
  }});

  renderGrid();
{CURSOR_JS}
</script>
</body>
</html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    log(f"\n{BOLD}╔══ LENS Portfolio Build ══╗{RESET}", CYAN)
    log(f"  Scanne '{BILDER_DIR}/'...\n")

    albums = scan_albums()

    if not albums:
        warn("\nKeine Alben gefunden. index.html wird trotzdem erstellt.")

    # index.html
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)
    index_path = out / "index.html"
    index_path.write_text(build_index(albums), encoding="utf-8")
    ok(f"index.html  ({len(albums)} Alben)")

    # Album-Seiten
    for album in albums:
        html = build_album_page(album, albums)
        path = out / f"album-{album['slug']}.html"
        path.write_text(html, encoding="utf-8")
        ok(f"album-{album['slug']}.html  ({album['count']} Fotos)")

    # Alte Album-Dateien aufräumen (Alben die gelöscht wurden)
    existing = {out / f"album-{a['slug']}.html" for a in albums}
    for old in out.glob("album-*.html"):
        if old not in existing:
            old.unlink()
            warn(f"Entfernt: {old.name}  (Album-Ordner nicht mehr vorhanden)")

    log(f"\n{BOLD}✓ Fertig!{RESET}", GREEN)
    log(f"  {len(albums)} Album{'s' if len(albums) != 1 else ''} + index.html generiert.", GREEN)
    log(f"\n  Nächste Schritte:", CYAN)
    log(f"  1. Alles in dein GitHub-Repo pushen")
    log(f"  2. Neue Alben? Einfach Ordner in bilder/ anlegen → build.py erneut ausführen\n")

if __name__ == "__main__":
    main()
