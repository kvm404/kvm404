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
from svg import (MONO, SANS, WEEKDAYS, WEEKDAYS_FULL, active_years, calendar_weeks, compact, esc,  # noqa: E402
                 metrics, monthly_totals, num, top_languages, write)

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "tile": "#ffffff", "border": "#e4e7eb", "text": "#0f172a", "muted": "#64748b", "faint": "#f1f5f9",
        "accent": "#059669", "accent_soft": "#c7f0de", "minus": "#f43f5e",
        "series": ["#059669", "#2563eb", "#d97706", "#db2777", "#7c3aed"], "other": "#cbd5e1",
    },
    "dark": {
        "tile": "#11161d", "border": "#262c36", "text": "#f1f5f9", "muted": "#8b96a5", "faint": "#1b222c",
        "accent": "#34d399", "accent_soft": "#134235", "minus": "#fb7185",
        "series": ["#0ea371", "#3b82f6", "#c98500", "#e1508a", "#8b5cf6"], "other": "#3a4250",
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
    r1, r2 = 0, 200 + GAP
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
        <rect width="122" height="28" rx="14" fill="{t['faint']}"/>
        <text class="chip" x="61" y="18.5" text-anchor="middle">krvaibhav.dev</text>
        <rect x="132" width="78" height="28" rx="14" fill="{t['faint']}"/>
        <text class="chip" x="171" y="18.5" text-anchor="middle">India</text>
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

    H = r2 + 200

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


def week_by_week(data: dict, t: dict, y0: float) -> tuple[str, float]:
    """Commits per week, stacked by repo, with releases marked under the axis."""
    weeks = calendar_weeks(data)
    index = {d["date"]: i for i, wk in enumerate(weeks) for d in wk}
    per_week: list[dict] = [{} for _ in weeks]
    totals: dict = {}
    for c in data["commit_log"]:
        i = index.get(c["local"][:10])
        if i is None:
            continue
        key = c["repo"] or "private"
        per_week[i][key] = per_week[i].get(key, 0) + 1
        totals[key] = totals.get(key, 0) + 1

    # Up to five named series by size, in the fixed palette order; the rest fold into "other".
    ranked = sorted(totals, key=lambda k: -totals[k])
    named = [k for k in ranked if totals[k] >= 15][:5]
    series = named + (["other"] if len(ranked) > len(named) else [])
    color = {k: t["series"][i] for i, k in enumerate(named)}
    color["other"] = t["other"]
    def bucket(k):
        return k if k in named else "other"
    stacks = []
    for wk in per_week:
        agg: dict = {}
        for k, v in wk.items():
            agg[bucket(k)] = agg.get(bucket(k), 0) + v
        stacks.append(agg)
    count = {k: sum(st.get(k, 0) for st in stacks) for k in series}
    names = {"private": "private repos", "other": "other"}

    h = 318
    left, right = 58, W - 22
    top, base = y0 + 132, y0 + 252
    slot = (right - left) / len(weeks)
    bw = slot - 4
    peak = max((sum(st.values()) for st in stacks), default=1) or 1
    step = next(s for s in (5, 10, 20, 25, 50, 100, 200, 250, 500) if peak / s <= 3)
    scale = (base - top) / max(peak, step)
    parts = []

    # legend
    lx = 22
    for k in series:
        label = names.get(k, k)
        parts.append(
            f'<rect x="{lx}" y="{y0 + 54}" width="10" height="10" rx="2.5" fill="{color[k]}"/>'
            f'<text class="small" x="{lx + 16}" y="{y0 + 63}" style="fill:{t["text"]}">{esc(label)}'
            f'<tspan class="tick" dx="6">{count[k]}</tspan></text>'
        )
        lx += 16 + len(label) * 7 + 6 + len(str(count[k])) * 6.4 + 26

    # grid
    v = step
    while v * scale <= base - top + 1:
        y = base - v * scale
        parts.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["border"]}" stroke-dasharray="2 4"/>'
                     f'<text class="tick" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{v}</text>')
        v += step
    parts.append(f'<line x1="{left}" x2="{right}" y1="{base}" y2="{base}" stroke="{t["border"]}"/>')

    # bars
    bars = []
    for i, st in enumerate(stacks):
        x = left + i * slot + 2
        y = base
        tip = ", ".join(f"{names.get(k, k)} {st[k]}" for k in series if st.get(k))
        for k in series:
            n = st.get(k, 0)
            if not n:
                continue
            seg = n * scale
            gap = 1.5 if y < base else 0
            bars.append(f'<rect x="{x:.1f}" y="{y - seg + gap:.1f}" width="{bw:.1f}" height="{max(seg - gap, 1):.1f}" rx="2.5" fill="{color[k]}"/>')
            y -= seg
        if tip:
            bars.append(f'<rect x="{x - 2:.1f}" y="{top - 10}" width="{slot:.1f}" height="{base - top + 10}" fill="transparent">'
                        f'<title>Week of {dt.date.fromisoformat(weeks[i][0]["date"]).strftime("%-d %b")}: {tip}</title></rect>')
    parts.append(f'<g class="rise" style="transform-origin:0 {base}px">{"".join(bars)}</g>')

    # month labels
    for i, wk in enumerate(weeks):
        d = dt.date.fromisoformat(wk[0]["date"])
        if d.day <= 7 and i:
            parts.append(f'<text class="tick" x="{left + i * slot:.1f}" y="{base + 38}">{d.strftime("%b")}</text>')

    # releases: a tick per release under the axis, and a label on each repo's first one
    seen: dict = {}
    first_labels = []
    for r in data["releases"]:
        i = index.get(r["date"])
        if i is None:
            continue
        k = bucket(r["repo"] or "private")
        n = seen.get(i, 0)
        seen[i] = n + 1
        cx = left + i * slot + slot / 2
        parts.append(f'<rect x="{cx - 7.5 + (n % 4) * 4:.1f}" y="{base + 6 + (n // 4) * 5}" width="3" height="3.5" rx="1" fill="{color.get(k, t["other"])}">'
                     f'<title>{esc((r["repo"] or "private repo") + " " + r["tag"])}, {r["date"]}</title></rect>')
        if r["repo"] and r["repo"] not in {f[0] for f in first_labels}:
            first_labels.append((r["repo"], r["tag"], cx))
    # The rightmost release gets the top row, so no label crosses another's leader line.
    for lvl, (repo, tag, cx) in enumerate(sorted(first_labels[:4], key=lambda f: -f[2])):
        ly = y0 + 92 + lvl * 13
        parts.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{ly + 4}" y2="{base}" stroke="{t["muted"]}" stroke-opacity=".6" stroke-dasharray="1.5 2.5"/>'
                     f'<circle cx="{cx:.1f}" cy="{ly}" r="2.5" fill="{color.get(bucket(repo), t["other"])}"/>'
                     f'<text class="tick" x="{cx - 7:.1f}" y="{ly + 4}" text-anchor="end" style="fill:{t["text"]}">{esc(repo)} {esc(tag)}</text>')

    nrel = sum(1 for r in data["releases"] if r["date"] in index)
    svg = tile(0, y0, W, h, t, 0,
               f'<text class="label" x="{W - 22}" y="{y0 + 32}" text-anchor="end">COMMITS PER WEEK · {nrel} RELEASES MARKED UNDER THE AXIS</text>'
               + "".join(parts), "The year, week by week")
    return svg, h


def rhythm(data: dict, t: dict) -> str:
    """Second grid: the year week by week, top repos, years, busiest weekday."""
    m = metrics(data)
    col = (W - 3 * GAP) / 4
    half = col * 2 + GAP
    tiles = []

    weekly, hw = week_by_week(data, t, 0)
    tiles.append(weekly)

    # Top repos this year
    rc = hw + GAP
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

    # Busiest weekday
    wx = yx + col + GAP
    ra, ha = rc, hc
    wk = m["weekday_contrib"]
    wpeak = max(wk) or 1
    bw, slot, base = 18, (col - 44) / 7, ra + ha - 38
    bars = []
    for i, c in enumerate(wk):
        bx = wx + 22 + i * slot + (slot - bw) / 2
        bh = max(3, 54 * c / wpeak)
        hot = i == m["peak_weekday"]
        bars.append(
            f'<rect x="{bx:.1f}" y="{base - bh:.1f}" width="{bw}" height="{bh:.1f}" rx="4" fill="{t["accent"] if hot else t["accent_soft"]}">'
            f'<title>{WEEKDAYS_FULL[i]}: {c}</title></rect>'
            f'<text class="tick" x="{bx + bw / 2:.1f}" y="{base + 18}" text-anchor="middle"{" style=\"fill:" + t["text"] + "\"" if hot else ""}>{WEEKDAYS[i][0]}</text>'
        )
    tiles.append(tile(wx, ra, col, ha, t, 6, f"""
      <text class="big" x="{wx + 22}" y="{ra + 84}">{WEEKDAYS[m['peak_weekday']]}</text>
      <text class="body" x="{wx + 22}" y="{ra + 106}">{m['weekend_share'] * 100:.0f}% on weekends</text>
      <g class="rise" style="transform-origin:0 {base}px">{''.join(bars)}</g>""", "Busiest day"))

    H = rc + hc
    return frame(W, H, t, "".join(tiles),
                 f"Commits per week by repo, busiest on {WEEKDAYS_FULL[m['peak_weekday']]}s. "
                 f"Top repo this year: {repos[0]['name']}.")


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
