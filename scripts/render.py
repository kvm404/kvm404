"""Render the profile as one bento-grid dashboard.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/bento-{light,dark}.svg and assets/rhythm-{light,dark}.svg.
"""

from __future__ import annotations

import base64
import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import (MONO, SANS, WEEKDAYS, WEEKDAYS_FULL, active_years, calendar_weeks, compact, esc, heatmap,  # noqa: E402
                 hour_label, metrics, monthly_totals, num, top_languages, write)

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "tile": "#ffffff", "border": "#e4e7eb", "text": "#0f172a", "muted": "#64748b", "faint": "#f1f5f9",
        "accent": "#059669", "accent_soft": "#c7f0de", "minus": "#f43f5e",
        "heat": ["#eef2f6", "#a7f3d0", "#4ade80", "#10b981", "#047857"],
    },
    "dark": {
        "tile": "#11161d", "border": "#262c36", "text": "#f1f5f9", "muted": "#8b96a5", "faint": "#1b222c",
        "accent": "#34d399", "accent_soft": "#134235", "minus": "#fb7185",
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
      <text class="small" x="{sx + 22}" y="{r2 + 146}">Current {data['streak_current']} · last 14 days</text>
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

    return frame(W, H, t, "".join(tiles),
                 f"Kumar Vaibhav, fullstack developer. {num(data['contributions_all_time'])} contributions, "
                 f"{data['prs_merged']} merged pull requests, {data['repos']} repositories, {data['streak_longest']} day longest streak.")


def frame(w: float, h: float, t: dict, body: str, label: str) -> str:
    circ = 2 * math.pi * 30
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h:.0f}" viewBox="0 0 {w} {h:.0f}" role="img" aria-label="{esc(label)}">
  <style>
    .label {{ font-family: {MONO}; font-size: 11px; letter-spacing: 1.6px; fill: {t['muted']}; }}
    .h1 {{ font-family: {SANS}; font-size: 30px; font-weight: 800; letter-spacing: -.8px; fill: {t['text']}; }}
    .big {{ font-family: {SANS}; font-size: 46px; font-weight: 800; letter-spacing: -1.8px; fill: {t['text']}; }}
    .unit {{ font-size: 18px; font-weight: 600; letter-spacing: 0; fill: {t['muted']}; }}
    .body {{ font-family: {SANS}; font-size: 14px; fill: {t['muted']}; }}
    .strong {{ font-weight: 700; fill: {t['text']}; }}
    .small {{ font-family: {SANS}; font-size: 12.5px; fill: {t['muted']}; }}
    .tick {{ font-family: {MONO}; font-size: 10.5px; fill: {t['muted']}; }}
    .num {{ font-family: {MONO}; font-size: 12px; font-weight: 600; fill: {t['text']}; }}
    .chip {{ font-family: {SANS}; font-size: 12.5px; font-weight: 600; fill: {t['text']}; }}
    .ringtxt {{ font-family: {SANS}; font-size: 14px; font-weight: 700; fill: {t['text']}; }}
    .tile {{ animation: tile 700ms cubic-bezier(.16,1,.3,1) both; }}
    .draw {{ stroke-dasharray: 1; animation: draw 1.6s cubic-bezier(.45,0,.15,1) 400ms both; }}
    .ring {{ animation: ring 1.4s cubic-bezier(.16,1,.3,1) 400ms both; }}
    .grow {{ animation: grow 1s cubic-bezier(.16,1,.3,1) 500ms both; }}
    .rise {{ animation: rise 900ms cubic-bezier(.16,1,.3,1) 400ms both; }}
    .pop {{ animation: pop 600ms cubic-bezier(.34,1.56,.64,1) both; transform-box: fill-box; transform-origin: center; }}
    .pulse {{ animation: pulse 2s ease-in-out infinite; }}
    @keyframes tile {{ from {{ opacity: 0; transform: translateY(10px); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} }}
    @keyframes ring {{ from {{ stroke-dasharray: 0 {circ:.1f}; }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes rise {{ from {{ transform: scaleY(0); }} }}
    @keyframes pop {{ from {{ transform: scale(0); }} }}
    @keyframes pulse {{ 50% {{ opacity: .3; }} }}
    @media (prefers-reduced-motion: reduce) {{ .tile, .draw, .ring, .grow, .rise, .pop, .pulse {{ animation: none; }} }}
  </style>
  {body}
</svg>"""


def rhythm(data: dict, t: dict) -> str:
    """Second grid: when and how the work happens."""
    m = metrics(data)
    col = (W - 3 * GAP) / 4
    half = col * 2 + GAP
    tiles = []

    # Hour-of-day clock, with the day split into four parts beside it.
    ra, ha = 0, 224
    hours = m["hours"]
    peak = max(hours) or 1
    ccx, ccy, inner, outer = half - 118, ra + 116, 30, 76
    spokes = []
    for h, c in enumerate(hours):
        a = math.radians(h * 15 - 90)
        length = 4 + (outer - inner - 4) * c / peak
        x1, y1 = ccx + inner * math.cos(a), ccy + inner * math.sin(a)
        x2, y2 = ccx + (inner + length) * math.cos(a), ccy + (inner + length) * math.sin(a)
        op = 1 if h == m["peak_hour"] else .3 + .5 * c / peak
        spokes.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["accent"]}" stroke-opacity="{op:.2f}" '
            f'stroke-width="7" stroke-linecap="round"><title>{hour_label(h)}: {c} commits</title></line>'
        )
    ticks = "".join(
        f'<text class="tick" x="{ccx + (outer + 14) * math.cos(math.radians(h * 15 - 90)):.1f}" '
        f'y="{ccy + (outer + 14) * math.sin(math.radians(h * 15 - 90)) + 4:.1f}" text-anchor="middle">{lab}</text>'
        for h, lab in ((0, "12a"), (6, "6a"), (12, "12p"), (18, "6p"))
    )
    total = sum(c for _, c in m["dayparts"]) or 1
    parts = []
    for i, (name, c) in enumerate(m["dayparts"]):
        y = ra + 136 + i * 20
        share = c / total
        parts.append(
            f'<text class="small" x="22" y="{y}">{name}</text>'
            f'<rect x="100" y="{y - 8}" width="110" height="7" rx="3.5" fill="{t["faint"]}"/>'
            f'<rect class="grow" style="transform-origin:100px 0" x="100" y="{y - 8}" width="{110 * share:.1f}" height="7" rx="3.5" fill="{t["accent"]}"/>'
            f'<text class="num" x="252" y="{y}" text-anchor="end">{share * 100:.0f}%</text>'
        )
    tiles.append(tile(0, ra, half, ha, t, 0, f"""
      <text class="big" x="22" y="{ra + 84}">{hour_label(m['peak_hour'])}</text>
      <text class="body" x="22" y="{ra + 106}">is when I commit most (IST)</text>
      {''.join(parts)}
      <circle cx="{ccx}" cy="{ccy}" r="{inner - 9}" fill="{t['faint']}"/>
      <g class="pop">{''.join(spokes)}</g>{ticks}""", "When I commit"))

    # Weekday bars
    wx = half + GAP
    wk = m["weekday_contrib"]
    wpeak = max(wk) or 1
    bw, slot, base = 18, (col - 44) / 7, ra + ha - 38
    bars = []
    for i, c in enumerate(wk):
        bx = wx + 22 + i * slot + (slot - bw) / 2
        bh = max(3, 70 * c / wpeak)
        hot = i == m["peak_weekday"]
        bars.append(
            f'<rect x="{bx:.1f}" y="{base - bh:.1f}" width="{bw}" height="{bh:.1f}" rx="4" fill="{t["accent"] if hot else t["accent_soft"]}">'
            f'<title>{WEEKDAYS_FULL[i]}: {c}</title></rect>'
            f'<text class="tick" x="{bx + bw / 2:.1f}" y="{base + 18}" text-anchor="middle"{" style=\"fill:" + t["text"] + "\"" if hot else ""}>{WEEKDAYS[i][0]}</text>'
        )
    tiles.append(tile(wx, ra, col, ha, t, 1, f"""
      <text class="big" x="{wx + 22}" y="{ra + 84}">{WEEKDAYS[m['peak_weekday']]}</text>
      <text class="body" x="{wx + 22}" y="{ra + 106}">{m['weekend_share'] * 100:.0f}% on weekends</text>
      <g class="rise" style="transform-origin:0 {base}px">{''.join(bars)}</g>""", "Busiest day"))

    # Lines added and removed
    lx = wx + col + GAP
    add, dele = data["additions"], data["deletions"]
    share = add / max(1, add + dele)
    bar_w = col - 44
    tiles.append(tile(lx, ra, col, ha, t, 2, f"""
      <text class="big" x="{lx + 22}" y="{ra + 84}">+{compact(add)}</text>
      <text class="body" x="{lx + 22}" y="{ra + 106}">lines added, {compact(dele)} removed</text>
      <g class="grow" style="transform-origin:{lx + 22}px 0">
        <rect x="{lx + 22}" y="{ra + 140}" width="{bar_w * share - 2:.1f}" height="12" rx="4" fill="{t['accent']}"/>
        <rect x="{lx + 22 + bar_w * share + 2:.1f}" y="{ra + 140}" width="{max(bar_w * (1 - share) - 2, 3):.1f}" height="12" rx="4" fill="{t['minus']}"/>
      </g>
      <circle cx="{lx + 27}" cy="{ra + 172}" r="4" fill="{t['accent']}"/><text class="small" x="{lx + 37}" y="{ra + 176}">added</text>
      <circle cx="{lx + 92}" cy="{ra + 172}" r="4" fill="{t['minus']}"/><text class="small" x="{lx + 102}" y="{ra + 176}">removed</text>
      <text class="small" x="{lx + 22}" y="{ra + 202}">across {num(data['commits_total'])} commits</text>""", "Lines of code"))

    # Punch card: weekday by hour
    rb = ra + ha + GAP
    left, top, cw, rh = 74, rb + 64, (W - 74 - 26) / 24, 22
    punch = data["punchcard"]
    ppeak = max(max(r) for r in punch) or 1
    dots = []
    for w in range(7):
        y = top + w * rh
        dots.append(f'<text class="tick" x="22" y="{y + 4}">{WEEKDAYS[w]}</text>')
        for h in range(24):
            c = punch[w][h]
            x = left + h * cw + cw / 2
            if c:
                r = 2.2 + 7.3 * math.sqrt(c / ppeak)
                dots.append(
                    f'<circle class="pop" style="animation-delay:{300 + h * 25}ms" cx="{x:.1f}" cy="{y}" r="{r:.1f}" '
                    f'fill="{t["accent"]}" fill-opacity="{.35 + .65 * c / ppeak:.2f}"><title>{WEEKDAYS_FULL[w]} {hour_label(h)}: {c}</title></circle>'
                )
            else:
                dots.append(f'<circle cx="{x:.1f}" cy="{y}" r="1.6" fill="{t["border"]}"/>')
    for h in range(0, 24, 3):
        dots.append(f'<text class="tick" x="{left + h * cw + cw / 2:.1f}" y="{top + 7 * rh + 8}" text-anchor="middle">{hour_label(h).replace(" ", "")}</text>')
    hb = 64 + 7 * rh + 28
    tiles.append(tile(0, rb, W, hb, t, 3, f"""
      <text class="label" x="{W - 22}" y="{rb + 32}" text-anchor="end">{num(data['commits_total'])} COMMITS · {m['night_share'] * 100:.0f}% AFTER 10 PM</text>
      {''.join(dots)}""", "Commits by day and hour"))

    # Top repos this year
    rc = rb + hb + GAP
    hc = 212
    repos = data["top_repos"][:5]
    rpeak = max(r["commits"] for r in repos) or 1
    rows = []
    for i, r in enumerate(repos):
        y = rc + 70 + i * 28
        rows.append(
            f'<circle cx="27" cy="{y - 4.5}" r="5" fill="{r["color"]}"/>'
            f'<text class="body strong" x="40" y="{y}">{esc(r["name"])}</text>'
            f'<rect x="250" y="{y - 10}" width="{half - 250 - 66}" height="10" rx="5" fill="{t["faint"]}"/>'
            f'<rect class="grow" style="transform-origin:250px 0;animation-delay:{500 + i * 80}ms" x="250" y="{y - 10}" '
            f'width="{(half - 250 - 66) * r["commits"] / rpeak:.1f}" height="10" rx="5" fill="{t["accent"]}"/>'
            f'<text class="num" x="{half - 22}" y="{y}" text-anchor="end">{r["commits"]}</text>'
        )
    tiles.append(tile(0, rc, half, hc, t, 4, "".join(rows), "Most commits, last 12 months"))

    # Year by year
    yx = half + GAP
    years = active_years(data)
    ypeak = max(y["total"] for y in years) or 1
    yslot = (col - 44) / len(years)
    ybw = min(30, yslot * .6)
    ybase = rc + hc - 40
    ybars = []
    for i, y in enumerate(years):
        bx = yx + 22 + i * yslot + (yslot - ybw) / 2
        bh = max(3, 96 * y["total"] / ypeak)
        last = i == len(years) - 1
        ybars.append(
            f'<rect x="{bx:.1f}" y="{ybase - bh:.1f}" width="{ybw:.1f}" height="{bh:.1f}" rx="5" fill="{t["accent"] if last else t["accent_soft"]}"/>'
            f'<text class="num" x="{bx + ybw / 2:.1f}" y="{ybase - bh - 7:.1f}" text-anchor="middle">{compact(y["total"])}</text>'
            f'<text class="tick" x="{bx + ybw / 2:.1f}" y="{ybase + 20}" text-anchor="middle">\u2019{str(y["year"])[2:]}</text>'
        )
    tiles.append(tile(yx, rc, col, hc, t, 5, f'<g class="rise" style="transform-origin:0 {ybase}px">{"".join(ybars)}</g>', "Year by year"))

    # Load average, in contributions a day
    ox = yx + col + GAP
    l1, l7, l365 = m["load"]
    tiles.append(tile(ox, rc, col, hc, t, 6, f"""
      <text x="{ox + 22}" y="{rc + 90}" style="font-family:{MONO};font-size:22px;font-weight:700;letter-spacing:-.5px" fill="{t['text']}">{l1:.2f} <tspan fill="{t['muted']}">{l7:.2f} {l365:.2f}</tspan></text>
      <text class="small" x="{ox + 22}" y="{rc + 124}">contributions a day over</text>
      <text class="small" x="{ox + 22}" y="{rc + 142}">the last week, month, year</text>
      <text class="small" x="{ox + 22}" y="{rc + 182}">{m['active_days']} active days this year</text>""", "Load average"))

    H = rc + hc
    return frame(W, H, t, "".join(tiles),
                 f"When I work: most commits around {hour_label(m['peak_hour'])}, busiest on {WEEKDAYS_FULL[m['peak_weekday']]}s. "
                 f"{compact(add)} lines added across {data['commits_total']} commits. Top repo this year: {repos[0]['name']}.")


def main() -> None:
    data = load(LOGIN)
    with open(os.path.join(OUT, "avatar.webp"), "rb") as f:
        photo = "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    for name, theme in THEMES.items():
        write(os.path.join(OUT, f"bento-{name}.svg"), bento(data, theme, photo))
        write(os.path.join(OUT, f"rhythm-{name}.svg"), rhythm(data, theme))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
