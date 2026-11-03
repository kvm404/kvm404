"""Render the profile header and activity card in the portfolio's palette.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/header-{light,dark}.svg and assets/activity-{light,dark}.svg.
"""

from __future__ import annotations

import base64
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import MONO, SANS, calendar_weeks, esc, heatmap, num, top_languages, write  # noqa: E402

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "canvas": "#FAF9F6", "border": "#E0DBD3", "muted": "#706A62", "body": "#3D3833",
        "primary": "#1A1714", "accent": "#FF3D00",
        "heat": ["#EEEAE4", "#FFD3C2", "#FFA07D", "#FF6B36", "#FF3D00"],
        "langs": ["#FF3D00", "#1A1714", "#4A453F", "#706A62", "#9C968E", "#C2BCB3", "#DDD8D0"],
    },
    "dark": {
        "canvas": "#000000", "border": "#282828", "muted": "#9C9892", "body": "#D6D2CC",
        "primary": "#F5F2ED", "accent": "#FF5B2A",
        "heat": ["#151515", "#4A1B0B", "#8C2E0E", "#D9420F", "#FF5B2A"],
        "langs": ["#FF5B2A", "#F5F2ED", "#BDB8B1", "#8E8A84", "#66625D", "#46433F", "#2E2C29"],
    },
}

W = 1000


def portrait() -> str:
    with open(os.path.join(OUT, "portrait.webp"), "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode()


def header(t: dict, photo: str) -> str:
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="330" viewBox="0 0 {W} 330" role="img" aria-label="Kumar Vaibhav. Fullstack developer, AI and data science, IIT Madras.">
  <style>
    .mono {{ font-family: {MONO}; font-size: 13px; letter-spacing: 2.5px; fill: {t['muted']}; }}
    .name {{ font-family: {SANS}; font-size: 112px; letter-spacing: -5px; fill: {t['primary']}; }}
    .slide {{ animation: slide 900ms cubic-bezier(.16,1,.3,1) both; }}
    .rule {{ transform-origin: 48px 0; animation: grow 1100ms cubic-bezier(.45,0,.15,1) 500ms both; }}
    .dot {{ animation: pulse 2.4s ease-in-out infinite; }}
    .fade {{ animation: fadein 1200ms ease-out both; }}
    @keyframes fadein {{ from {{ opacity: 0; }} }}
    @keyframes slide {{ from {{ opacity: 0; transform: translateX(-28px); }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes pulse {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ .slide, .rule, .dot, .fade {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="329" rx="10" fill="{t['canvas']}" stroke="{t['border']}"/>
  <text class="mono" x="48" y="52">KVM404 / README.MD</text>
  <g class="fade" style="animation-delay:350ms">
    <rect x="{W - 48 - 176 + 12}" y="48" width="176" height="220" fill="{t['accent']}" fill-opacity=".18"/>
    <image href="{photo}" x="{W - 48 - 176}" y="36" width="176" height="220" preserveAspectRatio="xMidYMid slice"/>
  </g>
  <g class="slide" style="animation-delay:80ms"><text class="name" x="42" y="158" font-weight="300">KUMAR</text></g>
  <g class="slide" style="animation-delay:220ms"><text class="name" x="42" y="252" font-weight="800">VAIBHAV</text></g>
  <rect class="rule" x="48" y="276" width="{W - 96}" height="3" fill="{t['accent']}"/>
  <text class="mono" x="48" y="306">FULLSTACK DEVELOPER · AI/DS · IIT MADRAS</text>
  <circle class="dot" cx="{W - 236}" cy="301" r="4.5" fill="{t['accent']}"/>
  <text class="mono" x="{W - 48}" y="306" text-anchor="end" fill="{t['body']}">OPEN TO WORK</text>
</svg>"""


def activity(data: dict, t: dict) -> str:
    stats = [
        (num(data["contributions_all_time"]), "contributions, all time"),
        (num(data["prs_merged"]), "pull requests merged"),
        (num(data["repos"]), "repositories"),
        (f"{data['streak_longest']}d", "longest streak"),
    ]
    col = (W - 96) / len(stats)
    figs = []
    for i, (value, label) in enumerate(stats):
        x = 48 + i * col
        rule = f'<rect x="{x - 24:.0f}" y="84" width="1" height="64" fill="{t["border"]}"/>' if i else ""
        figs.append(
            f'{rule}<g class="rise" style="animation-delay:{120 + i * 110}ms">'
            f'<text x="{x:.0f}" y="126" class="big">{esc(value)}</text>'
            f'<text x="{x:.0f}" y="150" class="mono">{esc(label.upper())}</text></g>'
        )

    weeks = calendar_weeks(data)
    gap = 3
    cell = round((W - 96 - gap * (len(weeks) - 1)) / len(weeks), 2)
    hm, _, hm_h = heatmap(data, 48, 196, cell, gap, t["heat"], radius=2.5, animate=True)

    months = []
    seen = set()
    for wi, week in enumerate(weeks):
        d = dt.date.fromisoformat(week[0]["date"])
        key = (d.year, d.month)
        if d.day <= 7 and key not in seen and wi < len(weeks) - 2:
            seen.add(key)
            months.append(f'<text x="{48 + wi * (cell + gap):.1f}" y="{196 + hm_h + 20:.0f}" class="mono sm">{d.strftime("%b").upper()}</text>')

    langs = top_languages(data, 6)
    bar_y = 196 + hm_h + 62
    x = 48.0
    segs, labels = [], []
    lx = 48.0
    for i, lang in enumerate(langs):
        w = (W - 96) * lang["percent"] / 100
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w - 2, 1):.1f}" height="8" fill="{t["langs"][i]}"/>')
        x += w
        label = f'{lang["name"]} {lang["percent"]:.1f}%'
        labels.append(
            f'<rect x="{lx:.1f}" y="{bar_y + 26}" width="8" height="8" fill="{t["langs"][i]}"/>'
            f'<text x="{lx + 14:.1f}" y="{bar_y + 34}" class="mono sm" fill="{t["body"]}">{esc(label.upper())}</text>'
        )
        lx += 14 + len(label) * 7.6 + 26
    h = bar_y + 64

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{num(data['contributions_all_time'])} contributions, {num(data['prs_merged'])} merged pull requests, {data['repos']} repositories, {data['streak_longest']} day longest streak.">
  <style>
    .mono {{ font-family: {MONO}; font-size: 11.5px; letter-spacing: 1.4px; fill: {t['muted']}; }}
    .sm {{ font-size: 10.5px; letter-spacing: 1.4px; }}
    .big {{ font-family: {SANS}; font-size: 50px; font-weight: 800; letter-spacing: -2px; fill: {t['primary']}; }}
    .rise {{ animation: rise 800ms cubic-bezier(.16,1,.3,1) both; }}
    .hm-col {{ animation: fade 500ms ease-out both; }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .rise, .hm-col {{ animation: none; }} }}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="10" fill="{t['canvas']}" stroke="{t['border']}"/>
  <text class="mono" x="48" y="50">01 / ACTIVITY</text>
  <text class="mono" x="{W - 48}" y="50" text-anchor="end">UPDATED {data['generated']}</text>
  {''.join(figs)}
  {hm}
  {''.join(months)}
  <text class="mono" x="48" y="{bar_y - 14}">02 / LANGUAGES, BY BYTES ACROSS MY REPOS</text>
  {''.join(segs)}
  {''.join(labels)}
</svg>"""


def main() -> None:
    data = load(LOGIN)
    os.makedirs(OUT, exist_ok=True)
    photo = portrait()
    for name, theme in THEMES.items():
        write(os.path.join(OUT, f"header-{name}.svg"), header(theme, photo))
        write(os.path.join(OUT, f"activity-{name}.svg"), activity(data, theme))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
