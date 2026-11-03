"""Render the profile as one bento-grid dashboard.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/bento-{light,dark}.svg.
"""

from __future__ import annotations

import base64
import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import MONO, SANS, calendar_weeks, esc, heatmap, monthly_totals, num, top_languages, write  # noqa: E402

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "tile": "#ffffff", "border": "#e4e7eb", "text": "#0f172a", "muted": "#64748b", "faint": "#f1f5f9",
        "accent": "#059669", "accent_soft": "#d1fae5",
        "heat": ["#eef2f6", "#a7f3d0", "#4ade80", "#10b981", "#047857"],
    },
    "dark": {
        "tile": "#11161d", "border": "#262c36", "text": "#f1f5f9", "muted": "#8b96a5", "faint": "#1b222c",
        "accent": "#34d399", "accent_soft": "#0f2e25",
        "heat": ["#1b222c", "#064e3b", "#047857", "#10b981", "#6ee7b7"],
    },
}

W, GAP = 1000, 12


def tile(x, y, w, h, t, i, body, label=None):
    head = f'<text class="label" x="{x + 22}" y="{y + 32}">{esc(label.upper())}</text>' if label else ""
    return (
        f'<g class="tile" style="animation-delay:{i * 70}ms">'
        f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="18" fill="{t["tile"]}" stroke="{t["border"]}"/>'
        f"{head}{body}</g>"
    )


def bento(data: dict, t: dict, photo: str) -> str:
    col = (W - 3 * GAP) / 4  # quarter width
    half = col * 2 + GAP
    r1, r2, r3 = 0, 200 + GAP, 2 * (200 + GAP)
    tiles = []

    # Profile
    px, py = 0, r1
    tiles.append(tile(px, py, half, 200, t, 0, f"""
      <clipPath id="avatar"><circle cx="{px + 74}" cy="{py + 74}" r="46"/></clipPath>
      <circle cx="{px + 74}" cy="{py + 74}" r="50" fill="none" stroke="{t['accent']}" stroke-width="2" stroke-dasharray="4 5"/>
      <image href="{photo}" x="{px + 28}" y="{py + 28}" width="92" height="92" clip-path="url(#avatar)" preserveAspectRatio="xMidYMid slice"/>
      <text class="h1" x="{px + 144}" y="{py + 66}">Kumar Vaibhav</text>
      <text class="body" x="{px + 144}" y="{py + 92}">Fullstack developer, studying data science</text>
      <text class="body" x="{px + 144}" y="{py + 112}">at IIT Madras. Web, Android, Linux, games.</text>
      <g transform="translate({px + 28} {py + 148})">
        <rect width="118" height="28" rx="14" fill="{t['accent_soft']}"/>
        <circle class="pulse" cx="18" cy="14" r="4" fill="{t['accent']}"/>
        <text class="chip" x="30" y="18.5" fill="{t['accent']}">Open to work</text>
        <rect x="128" width="122" height="28" rx="14" fill="{t['faint']}"/>
        <text class="chip" x="189" y="18.5" text-anchor="middle">krvaibhav.dev</text>
        <rect x="260" width="78" height="28" rx="14" fill="{t['faint']}"/>
        <text class="chip" x="299" y="18.5" text-anchor="middle">India</text>
      </g>"""))

    # Contributions with a monthly sparkline
    cx = half + GAP
    months = monthly_totals(data, 13)[:-1]  # complete months only
    peak = max(c for _, c in months) or 1
    sw, sh = col - 44, 46
    pts = [(cx + 22 + i * sw / (len(months) - 1), r1 + 172 - sh * c / peak) for i, (_, c) in enumerate(months)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{pts[0][0]:.1f},{r1 + 172} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f},{r1 + 172} Z"
    tiles.append(tile(cx, r1, col, 200, t, 1, f"""
      <text class="big" x="{cx + 22}" y="{r1 + 84}">{num(data['contributions_all_time'])}</text>
      <text class="body" x="{cx + 22}" y="{r1 + 106}">contributions since {data['joined']}</text>
      <path d="{area}" fill="{t['accent']}" fill-opacity=".14"/>
      <polyline class="draw" points="{line}" fill="none" stroke="{t['accent']}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" pathLength="1"/>
      <circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3.5" fill="{t['accent']}"/>""", "All time"))

    # Merged PRs with merge-rate ring
    mx = cx + col + GAP
    rate = data["prs_merged"] / max(1, data["prs_total"])
    rr = 30
    circ = 2 * math.pi * rr
    rcx, rcy = mx + col - 56, r1 + 140
    tiles.append(tile(mx, r1, col, 200, t, 2, f"""
      <text class="big" x="{mx + 22}" y="{r1 + 84}">{num(data['prs_merged'])}</text>
      <text class="body" x="{mx + 22}" y="{r1 + 106}">pull requests merged</text>
      <text class="small" x="{mx + 22}" y="{r1 + 146}">{num(data['prs_total'])} opened</text>
      <text class="small" x="{mx + 22}" y="{r1 + 166}">{round(rate * 100)}% merge rate</text>
      <circle cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="{t['faint']}" stroke-width="8"/>
      <circle class="ring" cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="{t['accent']}" stroke-width="8" stroke-linecap="round"
        stroke-dasharray="{circ * rate:.1f} {circ:.1f}" transform="rotate(-90 {rcx} {rcy})"/>
      <text class="ringtxt" x="{rcx}" y="{rcy + 5}" text-anchor="middle">{round(rate * 100)}%</text>""", "Pull requests"))

    # Streak: last 14 days as dots
    sx = 0
    recent = data["calendar"][-14:]
    dots = "".join(
        f'<circle cx="{sx + 28 + i * ((col - 56) / 13):.1f}" cy="{r2 + 168}" r="5.5" fill="{t["accent"] if d["count"] else t["faint"]}"><title>{d["date"]}: {d["count"]}</title></circle>'
        for i, d in enumerate(recent)
    )
    tiles.append(tile(sx, r2, col, 200, t, 3, f"""
      <text class="big" x="{sx + 22}" y="{r2 + 84}">{data['streak_longest']}<tspan class="unit" dx="6">days</tspan></text>
      <text class="body" x="{sx + 22}" y="{r2 + 106}">longest streak</text>
      <text class="small" x="{sx + 22}" y="{r2 + 146}">Last 14 days</text>
      {dots}""", "Streak"))

    # Repos
    ex = col + GAP
    tiles.append(tile(ex, r2, col, 200, t, 4, f"""
      <text class="big" x="{ex + 22}" y="{r2 + 84}">{data['repos']}</text>
      <text class="body" x="{ex + 22}" y="{r2 + 106}">repositories, {data['public_repos']} public</text>
      <text class="small" x="{ex + 22}" y="{r2 + 146}">{data['stars']} stars on public repos</text>
      <text class="small" x="{ex + 22}" y="{r2 + 166}">{data['followers']} followers</text>""", "Repos"))

    # Languages
    lx = half + GAP
    langs = top_languages(data, 5)
    bar_w = half - 44
    x = lx + 22
    segs, legend = [], []
    for i, lang in enumerate(langs):
        w = bar_w * lang["percent"] / 100
        segs.append(f'<rect x="{x:.1f}" y="{r2 + 56}" width="{max(w - 3, 2):.1f}" height="14" rx="4" fill="{lang["color"]}"/>')
        x += w
        colx = lx + 22 + (i % 2) * (bar_w / 2 + 6)
        rowy = r2 + 104 + (i // 2) * 26
        legend.append(
            f'<circle cx="{colx + 5}" cy="{rowy - 4.5}" r="5" fill="{lang["color"]}"/>'
            f'<text class="body" x="{colx + 18}" y="{rowy}">{esc(lang["name"])}</text>'
            f'<text class="body strong" x="{colx + bar_w / 2 - 14:.1f}" y="{rowy}" text-anchor="end">{lang["percent"]:.1f}%</text>'
        )
    tiles.append(tile(lx, r2, half, 200, t, 5, f'<g class="grow" style="transform-origin:{lx + 22}px 0">{"".join(segs)}</g>{"".join(legend)}', "Languages by bytes"))

    # Heatmap
    weeks = calendar_weeks(data)
    gap = 3
    cell = round((W - 44 - gap * (len(weeks) - 1)) / len(weeks), 2)
    hm, _, hm_h = heatmap(data, 22, r3 + 52, cell, gap, t["heat"], radius=3)
    busiest = dt.date.fromisoformat(data["busiest_day"]["date"]).strftime("%-d %b")
    h3 = 52 + hm_h + 24
    tiles.append(tile(0, r3, W, h3, t, 6, f"""
      <text class="label" x="{W - 22}" y="{r3 + 32}" text-anchor="end">{num(data['contributions_last_year'])} IN THE LAST YEAR · BUSIEST DAY {busiest.upper()}, {data['busiest_day']['count']}</text>
      {hm}""", "Last 12 months"))
    H = r3 + h3

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Kumar Vaibhav, fullstack developer. {num(data['contributions_all_time'])} contributions, {data['prs_merged']} merged pull requests, {data['repos']} repositories, {data['streak_longest']} day longest streak.">
  <style>
    .label {{ font-family: {MONO}; font-size: 11px; letter-spacing: 1.6px; fill: {t['muted']}; }}
    .h1 {{ font-family: {SANS}; font-size: 30px; font-weight: 800; letter-spacing: -.8px; fill: {t['text']}; }}
    .big {{ font-family: {SANS}; font-size: 46px; font-weight: 800; letter-spacing: -1.8px; fill: {t['text']}; }}
    .unit {{ font-size: 18px; font-weight: 600; letter-spacing: 0; fill: {t['muted']}; }}
    .body {{ font-family: {SANS}; font-size: 14px; fill: {t['muted']}; }}
    .strong {{ font-weight: 700; fill: {t['text']}; }}
    .small {{ font-family: {SANS}; font-size: 12.5px; fill: {t['muted']}; }}
    .chip {{ font-family: {SANS}; font-size: 12.5px; font-weight: 600; fill: {t['text']}; }}
    .ringtxt {{ font-family: {SANS}; font-size: 14px; font-weight: 700; fill: {t['text']}; }}
    .tile {{ animation: tile 700ms cubic-bezier(.16,1,.3,1) both; }}
    .draw {{ stroke-dasharray: 1; animation: draw 1.6s cubic-bezier(.45,0,.15,1) 400ms both; }}
    .ring {{ animation: ring 1.4s cubic-bezier(.16,1,.3,1) 400ms both; }}
    .grow {{ animation: grow 1s cubic-bezier(.16,1,.3,1) 500ms both; }}
    .pulse {{ animation: pulse 2s ease-in-out infinite; }}
    @keyframes tile {{ from {{ opacity: 0; transform: translateY(10px); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} }}
    @keyframes ring {{ from {{ stroke-dasharray: 0 {circ:.1f}; }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes pulse {{ 50% {{ opacity: .3; }} }}
    @media (prefers-reduced-motion: reduce) {{ .tile, .draw, .ring, .grow, .pulse {{ animation: none; }} }}
  </style>
  {''.join(tiles)}
</svg>"""


def main() -> None:
    data = load(LOGIN)
    with open(os.path.join(OUT, "avatar.webp"), "rb") as f:
        photo = "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    for name, theme in THEMES.items():
        write(os.path.join(OUT, f"bento-{name}.svg"), bento(data, theme, photo))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
