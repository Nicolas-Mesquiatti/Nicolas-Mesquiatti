#!/usr/bin/env python3
"""Genera los SVG del perfil (banner, radares, tarjetas) en versión dark y light.

Uso:
    python scripts/build_assets.py --user Nicolas-Mesquiatti

Lee los JSON de assets/ y consulta la API pública de GitHub para las stats.
Si la API falla, deja sin tocar las tarjetas que dependen de ella.
"""
import argparse
import json
import math
import os
import sys
import textwrap
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

FONT = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"

THEMES = {
    "dark": dict(bg="#0d1117", card="#161b22", border="#30363d", text="#e6edf3",
                 muted="#8b949e", accent="#39ff14", grid="#30363d", bar="#21262d"),
    "light": dict(bg="#f6f8fa", card="#ffffff", border="#d0d7de", text="#1f2328",
                  muted="#656d76", accent="#1a7f37", grid="#d0d7de", bar="#eaeef2"),
}

LANG_COLORS = {
    "Python": "#3572A5", "R": "#198CE7", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051",
    "SQL": "#e38c00", "Dockerfile": "#384d54",
}

SPRITE = [
    "00100000100",
    "00010001000",
    "00111111100",
    "01101110110",
    "11111111111",
    "10111111101",
    "10100000101",
    "00011011000",
]


def load(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return json.load(f)


def write(name, svg):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("escrito", name)


# --------------------------------------------------------------------------- #
# Banner de terminal
# --------------------------------------------------------------------------- #
def banner(theme, data):
    t = THEMES[theme]
    lines = data["lines"]
    w = 1000
    top = 36
    line_h = 34
    h = top + 70 + len(lines) * line_h + 40
    prompt = f'{data["user"]}@{data["host"]}:~$ {data["command"]}'
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="profile.sh --live">',
        "<style>",
        f"text{{font-family:{FONT};font-size:19px}}",
        ".fade{animation:in .5s backwards}",
        "@keyframes in{from{opacity:0}}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        ".cur{animation:blink 1s steps(1) infinite}",
        "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}",
        ".sprite{animation:float 3s ease-in-out infinite}",
        "</style>",
        f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{w-24}a12 12 0 0 1 12 12v{top-12}H0z" fill="{t["card"]}"/>',
        f'<line x1="0" y1="{top}" x2="{w}" y2="{top}" stroke="{t["border"]}"/>',
        '<circle cx="24" cy="18" r="6" fill="#ff5f56"/>',
        '<circle cx="46" cy="18" r="6" fill="#ffbd2e"/>',
        '<circle cx="68" cy="18" r="6" fill="#27c93f"/>',
        f'<text x="{w/2}" y="23" text-anchor="middle" fill="{t["muted"]}" style="font-size:13px">profile.sh</text>',
    ]
    y = top + 50
    out.append(
        f'<text x="30" y="{y}" fill="{t["accent"]}" class="fade" style="animation-delay:0.2s">{escape(prompt)}</text>'
    )
    delay = 0.9
    for item in lines:
        y += line_h
        out.append(
            f'<g class="fade" style="animation-delay:{delay:.1f}s">'
            f'<text x="30" y="{y}" fill="{t["muted"]}">&gt; {escape(item["k"])}</text>'
            f'<text x="175" y="{y}" fill="{t["text"]}">{escape(item["v"])}</text></g>'
        )
        delay += 0.5
    y += line_h
    out.append(
        f'<text x="30" y="{y}" fill="{t["accent"]}" class="fade" style="animation-delay:{delay:.1f}s">'
        f'{escape(data["user"])}@{escape(data["host"])}:~$ <tspan class="cur">█</tspan></text>'
    )
    # sprite pixel-art
    px = 8
    sx, sy = w - 30 - len(SPRITE[0]) * px - 10, top + 70
    out.append(f'<g class="sprite" fill="{t["accent"]}">')
    for r, row in enumerate(SPRITE):
        for c, ch in enumerate(row):
            if ch == "1":
                out.append(f'<rect x="{sx + c * px}" y="{sy + r * px}" width="{px}" height="{px}"/>')
    out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Radar
# --------------------------------------------------------------------------- #
def radar(theme, data):
    t = THEMES[theme]
    axes = data["axes"]
    n = len(axes)
    w, h = 540, 420
    cx, cy, r = w / 2, 225, 105

    def pt(i, frac, extra=0):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        rad = r * frac + extra
        return cx + rad * math.cos(ang), cy + rad * math.sin(ang), ang

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(data["title"])}">',
        f"<style>text{{font-family:{FONT}}}</style>",
        f'<text x="{cx}" y="30" text-anchor="middle" fill="{t["muted"]}" style="font-size:14px;letter-spacing:2px">{escape(data["title"].upper())}</text>',
    ]
    for frac in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(f"{pt(i, frac)[0]:.1f},{pt(i, frac)[1]:.1f}" for i in range(n))
        out.append(f'<polygon points="{pts}" fill="none" stroke="{t["grid"]}" stroke-width="1"/>')
    for i in range(n):
        x, y, _ = pt(i, 1)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{t["grid"]}"/>')
    vals = " ".join(
        f"{pt(i, max(0, min(100, a['value'])) / 100)[0]:.1f},{pt(i, max(0, min(100, a['value'])) / 100)[1]:.1f}"
        for i, a in enumerate(axes)
    )
    out.append(f'<polygon points="{vals}" fill="{t["accent"]}" fill-opacity="0.22" stroke="{t["accent"]}" stroke-width="2"/>')
    for i, a in enumerate(axes):
        x, y, _ = pt(i, max(0, min(100, a["value"])) / 100)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{t["accent"]}"/>')
        lx, ly, ang = pt(i, 1, 20)
        c = math.cos(ang)
        anchor = "start" if c > 0.3 else "end" if c < -0.3 else "middle"
        out.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
            f'fill="{t["text"]}" style="font-size:14px">{escape(a["label"])}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Tarjetas (GitHub API)
# --------------------------------------------------------------------------- #
def api(path, token=None):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def project_card(theme, repo, desc, info):
    t = THEMES[theme]
    w, h = 460, 150
    lines = textwrap.wrap(desc, width=58)[:3]
    if len(textwrap.wrap(desc, width=58)) > 3:
        lines[-1] = lines[-1].rstrip(".,;") + "…"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(repo)}">',
        f"<style>text{{font-family:{FONT}}}</style>",
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{t["card"]}" stroke="{t["border"]}"/>',
        f'<text x="20" y="34" fill="{t["accent"]}" style="font-size:17px;font-weight:700">{escape(repo)}</text>',
    ]
    y = 62
    for ln in lines:
        out.append(f'<text x="20" y="{y}" fill="{t["text"]}" style="font-size:12.5px">{escape(ln)}</text>')
        y += 19
    fx = 20
    if info:
        lang = info.get("language")
        if lang:
            col = LANG_COLORS.get(lang, t["accent"])
            out.append(f'<circle cx="{fx+5}" cy="{h-22}" r="5" fill="{col}"/>')
            out.append(f'<text x="{fx+16}" y="{h-18}" fill="{t["muted"]}" style="font-size:12px">{escape(lang)}</text>')
            fx += 30 + len(lang) * 7.4
        out.append(f'<text x="{fx}" y="{h-18}" fill="{t["muted"]}" style="font-size:12px">★ {info.get("stargazers_count", 0)}</text>')
        fx += 55
        out.append(f'<text x="{fx}" y="{h-18}" fill="{t["muted"]}" style="font-size:12px">forks {info.get("forks_count", 0)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def stats_card(theme, user_data, repos):
    t = THEMES[theme]
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    rows = [
        ("Repos públicos", user_data.get("public_repos", len(repos))),
        ("Estrellas recibidas", stars),
        ("Forks", forks),
        ("Seguidores", user_data.get("followers", 0)),
    ]
    w, h = 480, 60 + len(rows) * 34 + 20
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="GitHub stats">',
        f"<style>text{{font-family:{FONT}}}</style>",
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{t["card"]}" stroke="{t["border"]}"/>',
        f'<text x="24" y="38" fill="{t["accent"]}" style="font-size:17px;font-weight:700">GitHub stats</text>',
    ]
    y = 78
    for label, value in rows:
        out.append(f'<text x="24" y="{y}" fill="{t["muted"]}" style="font-size:14px">{escape(label)}</text>')
        out.append(f'<text x="{w-24}" y="{y}" text-anchor="end" fill="{t["text"]}" style="font-size:16px;font-weight:700">{value}</text>')
        out.append(f'<line x1="24" y1="{y+12}" x2="{w-24}" y2="{y+12}" stroke="{t["border"]}" stroke-opacity="0.6"/>')
        y += 34
    out.append("</svg>")
    return "\n".join(out)


def langs_card(theme, repos):
    t = THEMES[theme]
    counts = {}
    for r in repos:
        if r.get("fork"):
            continue
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:6]
    total = sum(c for _, c in top) or 1
    w, h = 480, 60 + max(len(top), 1) * 34 + 20
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Lenguajes">',
        f"<style>text{{font-family:{FONT}}}</style>",
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{t["card"]}" stroke="{t["border"]}"/>',
        f'<text x="24" y="38" fill="{t["accent"]}" style="font-size:17px;font-weight:700">Lenguajes más usados</text>',
    ]
    y = 78
    bar_x, bar_w = 160, w - 160 - 70
    for lang, c in top:
        pct = c * 100 / total
        col = LANG_COLORS.get(lang, t["accent"])
        out.append(f'<text x="24" y="{y}" fill="{t["text"]}" style="font-size:13px">{escape(lang)}</text>')
        out.append(f'<rect x="{bar_x}" y="{y-10}" width="{bar_w}" height="10" rx="5" fill="{t["bar"]}"/>')
        out.append(f'<rect x="{bar_x}" y="{y-10}" width="{max(bar_w*pct/100, 6):.1f}" height="10" rx="5" fill="{col}"/>')
        out.append(f'<text x="{w-24}" y="{y}" text-anchor="end" fill="{t["muted"]}" style="font-size:13px">{pct:.0f}%</text>')
        y += 34
    out.append("</svg>")
    return "\n".join(out)


def slug(name):
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--skip-api", action="store_true", help="no consultar la API de GitHub")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN")

    prof = load("profile.json")
    for theme in THEMES:
        write(f"banner-{theme}.svg", banner(theme, prof))
        write(f"radar-{theme}.svg", radar(theme, load("skills.json")))
        write(f"radar-stack-{theme}.svg", radar(theme, load("stack.json")))

    projects = load("projects.json")["projects"]
    repos, user_data, ok = [], {}, False
    if not args.skip_api:
        try:
            user_data = api(f"/users/{args.user}", token)
            repos = api(f"/users/{args.user}/repos?per_page=100&type=owner", token)
            ok = True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print("aviso: no se pudo consultar la API de GitHub:", e, file=sys.stderr)

    by_name = {r["name"].lower(): r for r in repos}
    for p in projects:
        info = by_name.get(p["repo"].lower())
        for theme in THEMES:
            write(f"card-{slug(p['repo'])}-{theme}.svg", project_card(theme, p["repo"], p["description"], info))

    if ok:
        for theme in THEMES:
            write(f"card-stats-{theme}.svg", stats_card(theme, user_data, repos))
            write(f"card-langs-{theme}.svg", langs_card(theme, repos))
    else:
        print("aviso: tarjetas de stats y lenguajes no regeneradas", file=sys.stderr)


if __name__ == "__main__":
    main()
