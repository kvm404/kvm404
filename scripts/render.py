"""Render the banner, tagline and stats cards for the showcase profile.

Run: GH_TOKEN=... python3 scripts/render.py
Writes into assets/: banner.svg, tagline.svg, and overview / languages /
monthly, clock, repos, years and churn cards in -light and
-dark variants.
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import (MONO, SANS, WEEKDAYS_FULL, active_years, compact, esc, hour_label, metrics,  # noqa: E402
                 monthly_totals, num, top_languages, write)

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

DUSK = ["#4C1D95", "#9333EA", "#DB2777", "#F97316"]

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "muted": "#59636e", "track": "#eff2f5", "grid": "#eaeef2"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#e6edf3", "muted": "#9198a1", "track": "#21262d", "grid": "#1c2128"},
}

TAGLINES = [
    "I build web apps that people use every day.",
    "I make Android apps that work without internet.",
    "I write small tools for my Arch + Hyprland setup.",
    "I make browser games where every asset is code.",
]


def dusk_gradient(gid: str, horizontal: bool = True) -> str:
    x2, y2 = ("1", "0") if horizontal else ("0", "1")
    stops = "".join(f'<stop offset="{i / (len(DUSK) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(DUSK))
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def wave_path(width: float, base: float, amp: float, period: float, bottom: float | None = None) -> str:
    """A closed path whose lower edge is a sine wave, repeated across `width`."""
    pts = [f"M0 0 H{width} V{base:.1f}"]
    steps = int(width / 10)
    for i in range(steps, -1, -1):
        x = i * width / steps
        y = base + amp * math.sin(2 * math.pi * x / period)
        pts.append(f"L{x:.1f} {y:.1f}")
    pts.append("Z")
    return " ".join(pts)


def banner() -> str:
    W, H = 1000, 250
    back = wave_path(2000, 200, 14, 500)
    front = wave_path(2000, 188, 18, 500)
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Kumar Vaibhav. Fullstack developer, data science at IIT Madras.">
  <defs>
    {dusk_gradient('g')}
    <mask id="mb"><path class="back" d="{back}" fill="#fff"/></mask>
    <mask id="mf"><path class="front" d="{front}" fill="#fff"/></mask>
    <clipPath id="round"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <style>
    .back {{ animation: drift 14s linear infinite; }}
    .front {{ animation: drift 9s linear infinite reverse; }}
    .name {{ font-family: {SANS}; font-size: 60px; font-weight: 800; letter-spacing: -1.5px; fill: #fff; }}
    .sub {{ font-family: {MONO}; font-size: 14px; letter-spacing: 3px; fill: #fff; fill-opacity: .85; }}
    .in {{ animation: up 1s cubic-bezier(.16,1,.3,1) both; }}
    @keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-1000px); }} }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(14px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .back, .front, .in {{ animation: none; }} }}
  </style>
  <g clip-path="url(#round)">
    <rect width="{W}" height="{H}" fill="url(#g)" mask="url(#mb)" opacity=".4"/>
    <rect width="{W}" height="{H}" fill="url(#g)" mask="url(#mf)"/>
  </g>
  <g class="in"><text class="name" x="{W / 2}" y="104" text-anchor="middle">Kumar Vaibhav</text></g>
  <g class="in" style="animation-delay:200ms"><text class="sub" x="{W / 2}" y="142" text-anchor="middle">FULLSTACK DEVELOPER · DATA SCIENCE @ IIT MADRAS</text></g>
</svg>"""


def tagline() -> str:
    W, H = 1000, 44
    slot = 3.5
    cycle = slot * len(TAGLINES)
    share = 100 / len(TAGLINES)
    lines = []
    for i, line in enumerate(TAGLINES):
        lines.append(
            f'<g class="line" style="animation-delay:{i * slot}s{";opacity:0" if i else ""}">'
            f'<text x="{W / 2}" y="28" text-anchor="middle">{esc(line)}</text></g>'
        )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(' '.join(TAGLINES))}">
  <defs>{dusk_gradient('g')}</defs>
  <style>
    text {{ font-family: {MONO}; font-size: 19px; fill: url(#g); }}
    .line {{ animation: cycle {cycle}s linear infinite both; }}
    @keyframes cycle {{
      0% {{ opacity: 0; transform: translateY(8px); }}
      {share * 0.08:.2f}% {{ opacity: 1; transform: none; }}
      {share * 0.88:.2f}% {{ opacity: 1; transform: none; }}
      {share:.2f}%, 100% {{ opacity: 0; transform: translateY(-8px); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .line {{ animation: none; }} }}
  </style>
  {''.join(lines)}
</svg>"""


def card(w: int, h: int, t: dict, title: str, body: str, label: str, extra_css: str = "") -> str:
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">
  <defs>{dusk_gradient('g')}{dusk_gradient('gv', horizontal=False)}</defs>
  <style>
    .title {{ font-family: {SANS}; font-size: 16px; font-weight: 700; fill: {t['text']}; }}
    .label {{ font-family: {SANS}; font-size: 13px; fill: {t['muted']}; }}
    .value {{ font-family: {SANS}; font-size: 14px; font-weight: 700; fill: {t['text']}; }}
    .mono {{ font-family: {MONO}; font-size: 11px; fill: {t['muted']}; }}
    .in {{ animation: in 700ms cubic-bezier(.16,1,.3,1) both; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} }}
    {extra_css}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t['bg']}" stroke="{t['border']}"/>
  <rect x="24" y="26" width="4" height="16" rx="2" fill="url(#gv)"/>
  <text class="title" x="36" y="39">{esc(title)}</text>
  {body}
</svg>"""


def overview(data: dict, t: dict) -> str:
    W, H = 490, 210
    rows = [
        ("Contributions, all time", num(data["contributions_all_time"])),
        ("Pull requests merged", num(data["prs_merged"])),
        ("Repositories", num(data["repos"])),
        ("Longest streak", f"{data['streak_longest']} days"),
        ("Busiest day", f"{data['busiest_day']['count']} contributions"),
    ]
    body = []
    for i, (k, v) in enumerate(rows):
        y = 76 + i * 26
        body.append(
            f'<g class="in" style="animation-delay:{i * 90}ms">'
            f'<circle cx="30" cy="{y - 4.5}" r="3.5" fill="{DUSK[min(i, 3)]}"/>'
            f'<text class="label" x="44" y="{y}">{esc(k)}</text>'
            f'<text class="value" x="300" y="{y}" text-anchor="end">{esc(v)}</text></g>'
        )
    # Ring: this year's share of everything since joining.
    cx, cy, r = 395, 118, 54
    share = data["this_year"]["total"] / max(1, data["contributions_all_time"])
    circ = 2 * math.pi * r
    body.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["track"]}" stroke-width="10"/>'
        f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#g)" stroke-width="10" stroke-linecap="round" '
        f'stroke-dasharray="{circ * share:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" style="font-family:{SANS};font-size:24px;font-weight:800" fill="{t["text"]}">{num(data["this_year"]["total"])}</text>'
        f'<text class="mono" x="{cx}" y="{cy + 22}" text-anchor="middle">IN {data["this_year"]["year"]}</text>'
    )
    css = (
        f".ring {{ animation: ring 1.4s cubic-bezier(.16,1,.3,1) 300ms both; }}"
        f"@keyframes ring {{ from {{ stroke-dasharray: 0 {circ:.1f}; }} }}"
    )
    return card(W, H, t, "GitHub at a glance", "".join(body),
                f"{num(data['contributions_all_time'])} contributions, {data['prs_merged']} merged pull requests, {data['repos']} repositories.", css)


def languages(data: dict, t: dict) -> str:
    W, H = 490, 210
    langs = top_languages(data, 5)
    palette = DUSK + ["#FBBF24", "#94a3b8"]
    cx, cy, r, sw = 110, 120, 52, 20
    circ = 2 * math.pi * r
    offset = 0.0
    arcs, legend = [], []
    for i, lang in enumerate(langs):
        length = circ * lang["percent"] / 100
        arcs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{palette[i]}" stroke-width="{sw}" '
            f'stroke-dasharray="{max(length - 2, 0.5):.1f} {circ:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += length
        y = 74 + i * 22
        legend.append(
            f'<g class="in" style="animation-delay:{i * 80}ms">'
            f'<rect x="216" y="{y - 10}" width="10" height="10" rx="3" fill="{palette[i]}"/>'
            f'<text class="label" x="236" y="{y}">{esc(lang["name"])}</text>'
            f'<text class="value" x="{W - 28}" y="{y}" text-anchor="end">{lang["percent"]:.1f}%</text></g>'
        )
    body = f'<g class="spin" style="transform-origin:{cx}px {cy}px">{"".join(arcs)}</g>' + "".join(legend)
    css = ".spin { animation: spin 1.2s cubic-bezier(.16,1,.3,1) both; } @keyframes spin { from { opacity: 0; transform: rotate(-60deg) scale(.9); } }"
    return card(W, H, t, "Languages I write", body,
                "Language split: " + ", ".join(f"{l['name']} {l['percent']:.0f}%" for l in langs), css)


def monthly(data: dict, t: dict) -> str:
    W, H = 1000, 250
    months = monthly_totals(data, 12)
    peak = max(c for _, c in months) or 1
    left, right, top, base = 40, W - 28, 70, 206
    slot = (right - left) / len(months)
    bw = slot * 0.56
    body = []
    for frac in (0.5, 1.0):
        y = base - (base - top) * frac
        body.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["grid"]}" stroke-dasharray="3 4"/>')
    body.append(f'<line x1="{left}" x2="{right}" y1="{base}" y2="{base}" stroke="{t["border"]}"/>')
    for i, (label, count) in enumerate(months):
        x = left + i * slot + (slot - bw) / 2
        bh = max(3, (base - top) * count / peak)
        last = i == len(months) - 1
        body.append(
            f'<g class="bar" style="animation-delay:{i * 60}ms;transform-origin:0 {base}px">'
            f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="url(#heat)"{" fill-opacity=\".45\"" if last else ""}/></g>'
            f'<text class="mono" x="{x + bw / 2:.1f}" y="{base - bh - 8:.1f}" text-anchor="middle" fill="{t["text"]}">{num(count)}</text>'
            f'<text class="mono" x="{x + bw / 2:.1f}" y="{base + 20}" text-anchor="middle">{label.upper()}{" ·" if last else ""}</text>'
        )
    body.append(
        f'<text class="mono" x="{right}" y="39" text-anchor="end">{num(data["contributions_last_year"])} IN THE LAST YEAR · CURRENT MONTH SO FAR</text>'
    )
    css = ".bar { animation: bar 900ms cubic-bezier(.16,1,.3,1) both; } @keyframes bar { from { transform: scaleY(0); } }"
    stops = "".join(f'<stop offset="{i / 3:.2f}" stop-color="{c}"/>' for i, c in enumerate(reversed(DUSK)))
    body.insert(0, f'<defs><linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="0" y1="{base}" x2="0" y2="{top}">{stops}</linearGradient></defs>')
    return card(W, H, t, "Contributions per month", "".join(body),
                "Monthly contributions: " + ", ".join(f"{m} {c}" for m, c in months), css)


def mix(frac: float) -> str:
    """A colour from the dusk ramp, 0 = violet, 1 = orange."""
    frac = min(max(frac, 0), 1) * (len(DUSK) - 1)
    i = min(int(frac), len(DUSK) - 2)
    f = frac - i
    a, b = DUSK[i], DUSK[i + 1]
    rgb = [round(int(a[k:k + 2], 16) * (1 - f) + int(b[k:k + 2], 16) * f) for k in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in rgb)


def clock(data: dict, t: dict) -> str:
    W, H = 490, 250
    m = metrics(data)
    hours = m["hours"]
    peak = max(hours) or 1
    cx, cy, inner, outer = 124, 150, 24, 66
    spokes = []
    for h, c in enumerate(hours):
        a = math.radians(h * 15 - 90)
        length = 4 + (outer - inner - 4) * c / peak
        spokes.append(
            f'<line x1="{cx + inner * math.cos(a):.1f}" y1="{cy + inner * math.sin(a):.1f}" '
            f'x2="{cx + (inner + length) * math.cos(a):.1f}" y2="{cy + (inner + length) * math.sin(a):.1f}" '
            f'stroke="{mix(c / peak)}" stroke-width="7" stroke-linecap="round"><title>{hour_label(h)}: {c} commits</title></line>'
        )
    ticks = "".join(
        f'<text class="mono" x="{cx + (outer + 13) * math.cos(math.radians(h * 15 - 90)):.1f}" '
        f'y="{cy + (outer + 13) * math.sin(math.radians(h * 15 - 90)) + 4:.1f}" text-anchor="middle">{lab}</text>'
        for h, lab in ((0, "12a"), (6, "6a"), (12, "12p"), (18, "6p"))
    )
    total = sum(c for _, c in m["dayparts"]) or 1
    rows = []
    for i, (name, c) in enumerate(m["dayparts"]):
        y = 156 + i * 22
        share = c / total
        rows.append(
            f'<text class="label" x="246" y="{y}">{name}</text>'
            f'<rect x="330" y="{y - 8}" width="90" height="7" rx="3.5" fill="{t["track"]}"/>'
            f'<rect class="grow" style="transform-origin:330px 0;animation-delay:{300 + i * 80}ms" x="330" y="{y - 8}" width="{90 * share:.1f}" height="7" rx="3.5" fill="url(#g)"/>'
            f'<text class="value" x="{W - 26}" y="{y}" text-anchor="end">{share * 100:.0f}%</text>'
        )
    body = f"""
      <g class="spin" style="transform-origin:{cx}px {cy}px">{''.join(spokes)}</g>{ticks}
      <text x="246" y="108" style="font-family:{SANS};font-size:34px;font-weight:800;letter-spacing:-1px" fill="url(#g)">{hour_label(m['peak_hour'])}</text>
      <text class="label" x="246" y="130">is my busiest hour (IST)</text>
      {''.join(rows)}"""
    css = (".spin { animation: spin 1.2s cubic-bezier(.16,1,.3,1) both; } @keyframes spin { from { opacity: 0; transform: rotate(-90deg) scale(.6); } }"
           ".grow { animation: grow 900ms cubic-bezier(.16,1,.3,1) both; } @keyframes grow { from { transform: scaleX(0); } }")
    return card(W, H, t, "Around the clock", body,
                f"Commits by hour of day. Busiest hour {hour_label(m['peak_hour'])}. "
                + ", ".join(f"{n} {c * 100 // total}%" for n, c in m["dayparts"]), css)


def repos(data: dict, t: dict) -> str:
    W, H = 490, 250
    top = data["top_repos"][:5]
    peak = max(r["commits"] for r in top) or 1
    rows = []
    for i, r in enumerate(top):
        y = 88 + i * 34
        rows.append(
            f'<g class="in" style="animation-delay:{i * 80}ms">'
            f'<circle cx="30" cy="{y - 4.5}" r="4.5" fill="{r["color"]}"/>'
            f'<text class="value" x="44" y="{y}">{esc(r["name"])}</text></g>'
            f'<rect x="250" y="{y - 9}" width="170" height="8" rx="4" fill="{t["track"]}"/>'
            f'<rect class="grow" style="transform-origin:250px 0;animation-delay:{300 + i * 80}ms" x="250" y="{y - 9}" '
            f'width="{170 * r["commits"] / peak:.1f}" height="8" rx="4" fill="url(#g)"/>'
            f'<text class="value" x="{W - 26}" y="{y}" text-anchor="end">{r["commits"]}</text>'
        )
    css = ".grow { animation: grow 900ms cubic-bezier(.16,1,.3,1) both; } @keyframes grow { from { transform: scaleX(0); } }"
    body = f'<text class="mono" x="{W - 26}" y="39" text-anchor="end">COMMITS · LAST 12 MONTHS</text>' + "".join(rows)
    return card(W, H, t, "Where the commits went", body,
                "Repos with the most commits in the last year: " + ", ".join(f"{r['name']} {r['commits']}" for r in top), css)


def years(data: dict, t: dict) -> str:
    W, H = 490, 210
    ys = active_years(data)
    peak = max(y["total"] for y in ys) or 1
    left, right, base, top = 30, W - 26, 172, 72
    slot = (right - left) / len(ys)
    bw = min(56, slot * .55)
    bars = []
    for i, y in enumerate(ys):
        x = left + i * slot + (slot - bw) / 2
        bh = max(3, (base - top) * y["total"] / peak)
        bars.append(
            f'<g class="bar" style="animation-delay:{i * 90}ms;transform-origin:0 {base}px">'
            f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="url(#heat)"/></g>'
            f'<text class="value" x="{x + bw / 2:.1f}" y="{base - bh - 8:.1f}" text-anchor="middle">{num(y["total"])}</text>'
            f'<text class="mono" x="{x + bw / 2:.1f}" y="{base + 20}" text-anchor="middle">{y["year"]}</text>'
        )
    stops = "".join(f'<stop offset="{i / 3:.2f}" stop-color="{c}"/>' for i, c in enumerate(DUSK))
    defs = f'<defs><linearGradient id="heat" gradientUnits="userSpaceOnUse" x1="0" y1="{base}" x2="0" y2="{top}">{stops}</linearGradient></defs>'
    css = ".bar { animation: bar 900ms cubic-bezier(.16,1,.3,1) both; } @keyframes bar { from { transform: scaleY(0); } }"
    return card(W, H, t, "Year by year", defs + "".join(bars),
                "Contributions per year: " + ", ".join(f"{y['year']} {y['total']}" for y in ys), css)


def churn(data: dict, t: dict) -> str:
    W, H = 490, 210
    m = metrics(data)
    add, dele, n = data["additions"], data["deletions"], max(1, data["commits_total"])
    share = add / max(1, add + dele)
    body = f"""
      <text x="28" y="104" style="font-family:{SANS};font-size:40px;font-weight:800;letter-spacing:-1.4px" fill="url(#g)">+{compact(add)}</text>
      <text class="label" x="28" y="126">lines added</text>
      <text x="250" y="104" style="font-family:{SANS};font-size:40px;font-weight:800;letter-spacing:-1.4px" fill="{t['muted']}">\u2212{compact(dele)}</text>
      <text class="label" x="250" y="126">lines removed</text>
      <g class="grow" style="transform-origin:28px 0">
        <rect x="28" y="146" width="{(W - 56) * share - 2:.1f}" height="8" rx="4" fill="url(#g)"/>
        <rect x="{28 + (W - 56) * share + 2:.1f}" y="146" width="{max((W - 56) * (1 - share) - 2, 3):.1f}" height="8" rx="4" fill="{t['muted']}" fill-opacity=".5"/>
      </g>
      <text class="mono" x="28" y="182">{num(data['commits_total'])} COMMITS · BUSIEST ON {WEEKDAYS_FULL[m['peak_weekday']].upper()}S · {m['active_days']} ACTIVE DAYS</text>"""
    css = ".grow { animation: grow 1s cubic-bezier(.16,1,.3,1) 300ms both; } @keyframes grow { from { transform: scaleX(0); } }"
    return card(W, H, t, "Lines of code", body,
                f"{add} lines added and {dele} removed across {data['commits_total']} commits.", css)


def main() -> None:
    data = load(LOGIN)
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, "banner.svg"), banner())
    write(os.path.join(OUT, "tagline.svg"), tagline())
    for name, theme in THEMES.items():
        write(os.path.join(OUT, f"overview-{name}.svg"), overview(data, theme))
        write(os.path.join(OUT, f"languages-{name}.svg"), languages(data, theme))
        write(os.path.join(OUT, f"monthly-{name}.svg"), monthly(data, theme))
        write(os.path.join(OUT, f"clock-{name}.svg"), clock(data, theme))
        write(os.path.join(OUT, f"repos-{name}.svg"), repos(data, theme))
        write(os.path.join(OUT, f"years-{name}.svg"), years(data, theme))
        write(os.path.join(OUT, f"churn-{name}.svg"), churn(data, theme))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
