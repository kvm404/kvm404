"""Render the Skyline profile: a year of contributions as an isometric city,
an annotated activity line, and a ring of the year beside the languages.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/{skyline,pulse,orbit}-{light,dark}.svg.
"""

from __future__ import annotations

import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import (MONO, SANS, WEEKDAYS_FULL, calendar_weeks, compact, esc, hour_label,  # noqa: E402
                 metrics, num, top_languages, write)

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "bg": "#f8fafc", "border": "#e2e8f0", "text": "#0f172a", "muted": "#64748b", "faint": "#e2e8f0",
        "accent": "#2563eb", "glow": "#2563eb",
        "levels": ["#e2e8f0", "#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"],
        "shade": (0.88, 0.74),  # left face, front face brightness
    },
    "dark": {
        "bg": "#0a0f1f", "border": "#1c2540", "text": "#e6ecff", "muted": "#8590b3", "faint": "#161e36",
        "accent": "#38bdf8", "glow": "#38bdf8",
        "levels": ["#161e36", "#1e3a8a", "#2563eb", "#38bdf8", "#a5f3fc"],
        "shade": (0.72, 0.52),
    },
}


def shade(color: str, k: float) -> str:
    rgb = [min(255, round(int(color[i:i + 2], 16) * k)) for i in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in rgb)


def style(t: dict, extra: str = "") -> str:
    return f"""
  <style>
    .name {{ font-family: {SANS}; font-size: 40px; font-weight: 800; letter-spacing: -1.4px; fill: {t['text']}; }}
    .title {{ font-family: {SANS}; font-size: 17px; font-weight: 700; fill: {t['text']}; }}
    .sub {{ font-family: {SANS}; font-size: 15px; fill: {t['muted']}; }}
    .cap {{ font-family: {MONO}; font-size: 11px; letter-spacing: 1.5px; fill: {t['muted']}; }}
    .tick {{ font-family: {MONO}; font-size: 10.5px; fill: {t['muted']}; }}
    .big {{ font-family: {SANS}; font-size: 30px; font-weight: 800; letter-spacing: -1px; fill: {t['text']}; }}
    .val {{ font-family: {SANS}; font-size: 14px; font-weight: 700; fill: {t['text']}; }}
    .lbl {{ font-family: {SANS}; font-size: 13.5px; fill: {t['muted']}; }}
    .in {{ animation: in 800ms cubic-bezier(.16,1,.3,1) both; }}
    .rise {{ animation: rise 900ms cubic-bezier(.16,1,.3,1) both; transform-box: fill-box; transform-origin: 50% 100%; }}
    .draw {{ stroke-dasharray: 1; animation: draw 2.2s cubic-bezier(.45,0,.15,1) 200ms both; }}
    .fade {{ animation: fade 1.2s ease 1.4s both; }}
    .spin {{ animation: spin 1.4s cubic-bezier(.16,1,.3,1) both; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} }}
    @keyframes rise {{ from {{ transform: scaleY(0); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @keyframes spin {{ from {{ opacity: 0; transform: rotate(-40deg); }} }}
    {extra}
    @media (prefers-reduced-motion: reduce) {{ .in, .rise, .draw, .fade, .spin {{ animation: none; }} }}
  </style>"""


def skyline(data: dict, t: dict) -> str:
    """The last year as towers: one per day, height by contributions."""
    W, H = 1000, 500
    weeks = calendar_weeks(data)
    counts = sorted(d["count"] for d in data["calendar"] if d["count"])
    cap = counts[int(len(counts) * .97)] if counts else 1  # one record day shouldn't flatten the rest
    u = (14.2, -4.3)   # one week along
    v = (8.4, 6.2)     # one day down
    ox, oy, tall = 66, 424, 118

    def at(i, j):
        return ox + i * u[0] + j * v[0], oy + i * u[1] + j * v[1]

    cells = []
    for i, week in enumerate(weeks):
        first = (dt.date.fromisoformat(week[0]["date"]).weekday() + 1) % 7
        for k, day in enumerate(week):
            cells.append((i, first + k, day))
    # Paint far cells first: larger week index sits further back, larger weekday further forward.
    cells.sort(key=lambda c: at(c[0] + .5, c[1] + .5)[1])

    left_k, front_k = t["shade"]
    towers = []
    for i, j, day in cells:
        c = day["count"]
        ratio = min(c, cap) / cap if c else 0
        lv = 0 if not c else 1 if ratio <= .25 else 2 if ratio <= .5 else 3 if ratio <= .75 else 4
        h = 0 if not c else 4 + tall * math.sqrt(ratio)
        g = .9  # leave a hairline between towers
        p0 = at(i, j)
        p1 = (p0[0] + u[0] * g, p0[1] + u[1] * g)
        p3 = (p0[0] + v[0] * g, p0[1] + v[1] * g)
        p2 = (p1[0] + v[0] * g, p1[1] + v[1] * g)
        col = t["levels"][lv]
        top = [(x, y - h) for x, y in (p0, p1, p2, p3)]
        pts = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)  # noqa: E731
        title = f"<title>{day['date']}: {c}</title>"
        if not h:
            towers.append(f'<polygon points="{pts([p0, p1, p2, p3])}" fill="{col}">{title}</polygon>')
            continue
        left = [p0, p3, top[3], top[0]]
        front = [p3, p2, top[2], top[3]]
        towers.append(
            f'<g class="rise" style="animation-delay:{200 + i * 22}ms">{title}'
            f'<polygon points="{pts(left)}" fill="{shade(col, left_k)}"/>'
            f'<polygon points="{pts(front)}" fill="{shade(col, front_k)}"/>'
            f'<polygon points="{pts(top)}" fill="{col}"/></g>'
        )

    # Month labels along the front edge.
    months = []
    seen = None
    for i, week in enumerate(weeks):
        d = dt.date.fromisoformat(week[0]["date"])
        if d.month != seen and d.day <= 7 and i < len(weeks) - 2:
            seen = d.month
            x, y = at(i, 7.6)
            months.append(f'<text class="tick" x="{x:.1f}" y="{y + 12:.1f}" transform="rotate(-16.9 {x:.1f} {y + 12:.1f})">{d.strftime("%b")}</text>')

    m = metrics(data)
    busiest = dt.date.fromisoformat(data["busiest_day"]["date"])
    stats = [
        (num(data["contributions_last_year"]), "contributions"),
        (f"{data['streak_longest']} days", "longest streak"),
        (str(data["busiest_day"]["count"]), f"busiest day, {busiest.strftime('%-d %b')}"),
        (str(m["active_days"]), "active days"),
    ]
    stat_svg = []
    for k, (big, small) in enumerate(stats):
        x, y = 690 + (k % 2) * 160, 372 + (k // 2) * 64
        stat_svg.append(
            f'<g class="in" style="animation-delay:{1200 + k * 120}ms">'
            f'<text class="big" x="{x}" y="{y}">{esc(big)}</text>'
            f'<text class="lbl" x="{x}" y="{y + 22}" style="font-size:12.5px">{esc(small)}</text></g>'
        )

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Kumar Vaibhav. {num(data['contributions_last_year'])} contributions in the last year drawn as a city of towers, one per day. Longest streak {data['streak_longest']} days.">
  {style(t)}
  <defs>
    <radialGradient id="halo" cx="70%" cy="30%" r="70%">
      <stop offset="0" stop-color="{t['glow']}" stop-opacity=".12"/>
      <stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t['bg']}" stroke="{t['border']}"/>
  <rect width="{W}" height="{H}" rx="16" fill="url(#halo)"/>
  <g class="in"><text class="name" x="44" y="80">Kumar Vaibhav</text></g>
  <g class="in" style="animation-delay:120ms"><text class="sub" x="45" y="110">Fullstack developer · Data science at IIT Madras</text></g>
  <g class="in" style="animation-delay:240ms"><text class="cap" x="45" y="146">MY LAST 12 MONTHS ON GITHUB, ONE TOWER PER DAY</text></g>
  {''.join(towers)}
  <g class="fade">{''.join(months)}</g>
  {''.join(stat_svg)}
</svg>"""


def pulse(data: dict, t: dict) -> str:
    """Seven-day rolling average across the last year, with notes on the peaks."""
    W, H = 1000, 270
    days = data["calendar"][-365:]
    counts = [d["count"] for d in days]
    roll = [sum(counts[max(0, i - 6):i + 1]) / len(counts[max(0, i - 6):i + 1]) for i in range(len(counts))]
    left, right, top, base = 44, W - 44, 92, 214
    peak = max(roll) or 1
    xs = [left + (right - left) * i / (len(roll) - 1) for i in range(len(roll))]
    ys = [base - (base - top) * r / peak for r in roll]

    def smooth(points):
        d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
        for k in range(1, len(points)):
            x0, y0 = points[k - 1]
            x1, y1 = points[k]
            mx = (x0 + x1) / 2
            d += f" C{mx:.1f},{y0:.1f} {mx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
        return d

    pts = list(zip(xs, ys))
    line = smooth(pts)
    area = line + f" L{xs[-1]:.1f},{base} L{xs[0]:.1f},{base} Z"

    # Longest run of active days inside the window, shaded.
    best, run_start, best_span = 0, None, None
    for i, c in enumerate(counts + [0]):
        if c and run_start is None:
            run_start = i
        if not c and run_start is not None:
            if i - run_start > best:
                best, best_span = i - run_start, (run_start, i - 1)
            run_start = None
    notes = []
    if best_span:
        a, b = best_span
        notes.append(
            f'<rect x="{xs[a]:.1f}" y="{top - 14}" width="{xs[b] - xs[a]:.1f}" height="{base - top + 14}" fill="{t["accent"]}" fill-opacity=".07"/>'
            f'<text class="tick" x="{(xs[a] + xs[b]) / 2:.1f}" y="{top - 20}" text-anchor="middle">{best}-day streak</text>'
        )
    pk = max(range(len(roll)), key=lambda i: roll[i])
    flip = xs[pk] > W * .6
    notes.append(
        f'<circle cx="{xs[pk]:.1f}" cy="{ys[pk]:.1f}" r="4.5" fill="{t["bg"]}" stroke="{t["accent"]}" stroke-width="2.5"/>'
        f'<text class="tick" x="{xs[pk] + (-10 if flip else 10):.1f}" y="{ys[pk] + 4:.1f}" text-anchor="{"end" if flip else "start"}" style="fill:{t["text"]}">{roll[pk]:.1f} a day, week of {dt.date.fromisoformat(days[pk]["date"]).strftime("%-d %b")}</text>'
    )

    grid = []
    for frac in (.5, 1):
        y = base - (base - top) * frac
        grid.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["border"]}" stroke-dasharray="2 4"/>'
                    f'<text class="tick" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">{peak * frac:.0f}</text>')
    months = []
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        if date.day == 1:
            months.append(f'<line x1="{xs[i]:.1f}" x2="{xs[i]:.1f}" y1="{base}" y2="{base + 5}" stroke="{t["muted"]}"/>'
                          f'<text class="tick" x="{xs[i] + 4:.1f}" y="{base + 20}">{date.strftime("%b")}</text>')

    m = metrics(data)
    l7, l30, l365 = m["load"]
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contributions per day over the last year as a seven-day average. Peak {roll[pk]:.1f} a day. Averages: {l7:.1f} this week, {l30:.1f} this month, {l365:.1f} this year.">
  {style(t)}
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['accent']}" stop-opacity=".28"/>
      <stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t['bg']}" stroke="{t['border']}"/>
  <text class="title" x="44" y="46">Pulse</text>
  <text class="lbl" x="98" y="46">contributions a day, seven-day average</text>
  <text class="cap" x="{W - 44}" y="46" text-anchor="end">AVG · WEEK {l7:.1f} · MONTH {l30:.1f} · YEAR {l365:.1f}</text>
  {''.join(grid)}
  <line x1="{left}" x2="{right}" y1="{base}" y2="{base}" stroke="{t['border']}"/>
  {''.join(months)}
  <g class="fade" style="animation-delay:600ms">{''.join(notes[:-1])}</g>
  <path class="fade" style="animation-delay:900ms" d="{area}" fill="url(#fill)"/>
  <path class="draw" d="{line}" pathLength="1" fill="none" stroke="{t['accent']}" stroke-width="2.4" stroke-linejoin="round"/>
  <g class="fade" style="animation-delay:2s">{notes[-1]}</g>
</svg>"""


def orbit(data: dict, t: dict) -> str:
    """The calendar year as a ring of day bars, next to languages and habits."""
    W, H = 1000, 380
    year = dt.date.fromisoformat(data["generated"]).year
    by_day = {d["date"]: d["count"] for d in data["daily"]}
    start = dt.date(year, 1, 1)
    n = 366 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 365
    counts = [by_day.get((start + dt.timedelta(days=k)).isoformat(), 0) for k in range(n)]
    nonzero = sorted(c for c in counts if c)
    cap = nonzero[int(len(nonzero) * .97)] if nonzero else 1
    cx, cy, r0, r1 = 200, 196, 82, 152
    today = dt.date.fromisoformat(data["generated"])
    bars = []
    for k, c in enumerate(counts):
        a = math.radians(k / n * 360 - 90)
        future = start + dt.timedelta(days=k) > today
        ln = 2.5 if not c else 5 + (r1 - r0 - 5) * min(c, cap) / cap
        col = t["faint"] if future or not c else t["accent"]
        op = 1 if future or not c else .35 + .65 * min(c, cap) / cap
        bars.append(
            f'<line x1="{cx + r0 * math.cos(a):.1f}" y1="{cy + r0 * math.sin(a):.1f}" '
            f'x2="{cx + (r0 + ln) * math.cos(a):.1f}" y2="{cy + (r0 + ln) * math.sin(a):.1f}" '
            f'stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="1.7" stroke-linecap="round"/>'
        )
    labels = []
    for mth in range(12):
        k = (dt.date(year, mth + 1, 1) - start).days + 15
        a = math.radians(k / n * 360 - 90)
        labels.append(f'<text class="tick" x="{cx + (r1 + 16) * math.cos(a):.1f}" y="{cy + (r1 + 16) * math.sin(a) + 4:.1f}" text-anchor="middle">{dt.date(year, mth + 1, 1).strftime("%b")[0]}</text>')
    # Today's hand
    a = math.radians((today - start).days / n * 360 - 90)
    hand = (f'<line x1="{cx + (r0 - 6) * math.cos(a):.1f}" y1="{cy + (r0 - 6) * math.sin(a):.1f}" x2="{cx + (r1 + 4) * math.cos(a):.1f}" y2="{cy + (r1 + 4) * math.sin(a):.1f}" '
            f'stroke="{t["muted"]}" stroke-width="1" stroke-dasharray="2 3"/>')
    total = sum(counts)

    # Languages, right column
    langs = top_languages(data, 6)
    lx, lw = 430, 250
    lrows = []
    for i, lang in enumerate(langs):
        y = 112 + i * 34
        lrows.append(
            f'<g class="in" style="animation-delay:{300 + i * 80}ms">'
            f'<text class="lbl" x="{lx}" y="{y}">{esc(lang["name"])}</text>'
            f'<text class="val" x="{lx + lw}" y="{y}" text-anchor="end">{lang["percent"]:.1f}%</text>'
            f'<rect x="{lx}" y="{y + 8}" width="{lw}" height="5" rx="2.5" fill="{t["faint"]}"/>'
            f'<rect x="{lx}" y="{y + 8}" width="{lw * lang["percent"] / langs[0]["percent"]:.1f}" height="5" rx="2.5" fill="{lang["color"]}"/></g>'
        )

    m = metrics(data)
    habits = [
        (hour_label(m["peak_hour"]), "busiest hour, IST"),
        (WEEKDAYS_FULL[m["peak_weekday"]], "busiest day of the week"),
        (f"+{compact(data['additions'])}", f"lines added in {num(data['commits_total'])} commits"),
        (f"{data['prs_merged']}", f"pull requests merged of {data['prs_total']}"),
    ]
    hx = 740
    hrows = []
    for i, (big, small) in enumerate(habits):
        y = 116 + i * 64
        hrows.append(
            f'<g class="in" style="animation-delay:{600 + i * 90}ms">'
            f'<text class="big" x="{hx}" y="{y}" style="font-size:26px">{esc(big)}</text>'
            f'<text class="lbl" x="{hx}" y="{y + 21}" style="font-size:12.5px">{esc(small)}</text></g>'
        )

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{year} as a ring of days: {num(total)} contributions so far. Languages: {', '.join(f"{l['name']} {l['percent']:.0f}%" for l in langs)}. Busiest hour {hour_label(m['peak_hour'])}, busiest day {WEEKDAYS_FULL[m['peak_weekday']]}.">
  {style(t)}
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t['bg']}" stroke="{t['border']}"/>
  <g class="spin" style="transform-origin:{cx}px {cy}px">{''.join(bars)}</g>
  {''.join(labels)}{hand}
  <text x="{cx}" y="{cy + 2}" text-anchor="middle" style="font-family:{SANS};font-size:34px;font-weight:800;letter-spacing:-1.2px" fill="{t['text']}">{num(total)}</text>
  <text class="cap" x="{cx}" y="{cy + 24}" text-anchor="middle">IN {year}</text>
  <line x1="{lx - 32}" x2="{lx - 32}" y1="44" y2="{H - 44}" stroke="{t['border']}"/>
  <text class="cap" x="{lx}" y="68">LANGUAGES</text>
  {''.join(lrows)}
  <line x1="{hx - 32}" x2="{hx - 32}" y1="44" y2="{H - 44}" stroke="{t['border']}"/>
  <text class="cap" x="{hx}" y="68">HABITS</text>
  {''.join(hrows)}
</svg>"""


def main() -> None:
    data = load(LOGIN)
    os.makedirs(OUT, exist_ok=True)
    for name, theme in THEMES.items():
        write(os.path.join(OUT, f"skyline-{name}.svg"), skyline(data, theme))
        write(os.path.join(OUT, f"pulse-{name}.svg"), pulse(data, theme))
        write(os.path.join(OUT, f"orbit-{name}.svg"), orbit(data, theme))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
