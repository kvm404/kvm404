"""Render GitHub stats as a btop-style system monitor in Tokyo Night colours.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/btop.svg.

The panels map loosely onto btop's: cpu is daily contributions, the core list
is weekdays, mem is languages, net is lines added and removed, and proc lists
the repos with the most commits.
"""

from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import MONO, WEEKDAYS, compact, esc, hour_label, metrics, num, top_languages, write  # noqa: E402

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

# Tokyo Night
BG = "#1a1b26"
FG = "#c0caf5"
DIM = "#565f89"
LINE = "#3b4261"
BLUE = "#7aa2f7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
MAGENTA = "#bb9af7"
ORANGE = "#ff9e64"
RED = "#f7768e"
YELLOW = "#e0af68"
SEL = "#283457"

W, H = 1000, 640
CW = 7.2  # advance of the monospace face at 12px


def heat(frac: float) -> str:
    """btop's graph gradient: green, then yellow, then red."""
    stops = [GREEN, YELLOW, RED]
    frac = min(max(frac, 0), 1) * 2
    i = min(int(frac), 1)
    f = frac - i
    a, b = stops[i], stops[i + 1]
    rgb = [round(int(a[k:k + 2], 16) * (1 - f) + int(b[k:k + 2], 16) * f) for k in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in rgb)


def box(x, y, w, h, num_, title, right="", color=DIM, delay=0):
    """A rounded btop panel with its title cut into the top border."""
    tw = (len(title) + 1) * CW + 14
    parts = [
        f'<g class="in" style="animation-delay:{delay}ms">',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="none" stroke="{color}" stroke-width="1.2"/>',
        f'<rect x="{x + 14}" y="{y - 8}" width="{tw}" height="16" fill="{BG}"/>',
        f'<text x="{x + 20}" y="{y + 4}"><tspan fill="{ORANGE}" font-size="9" dy="-3">{num_}</tspan>'
        f'<tspan dy="3" fill="{FG}" font-weight="700">{esc(title)}</tspan></text>',
    ]
    if right:
        rw = len(right) * CW + 14
        parts.append(f'<rect x="{x + w - 14 - rw}" y="{y - 8}" width="{rw}" height="16" fill="{BG}"/>'
                     f'<text x="{x + w - 21}" y="{y + 4}" text-anchor="end" fill="{DIM}">{esc(right)}</text>')
    parts.append("</g>")
    return "".join(parts)


def dots(x, base, step, value, size, color_for):
    """A column of square dots, like btop's braille graph."""
    return "".join(
        f'<rect x="{x:.1f}" y="{base - (k + 1) * step:.1f}" width="{size}" height="{size}" fill="{color_for(k)}"/>'
        for k in range(value)
    )


def meter(x, y, cells, frac, color_for):
    """btop's block meter: lit cells in colour, the rest dim."""
    lit = round(cells * frac)
    return "".join(
        f'<rect x="{x + k * 6:.1f}" y="{y - 9}" width="4.5" height="10" rx="1" fill="{color_for(k / cells) if k < lit else LINE}"/>'
        for k in range(cells)
    )


def render(data: dict) -> str:
    m = metrics(data)
    today = dt.date.fromisoformat(data["generated"])
    body = []

    # cpu: daily contributions over the last 26 weeks
    cx, cy, cw, ch = 10, 12, 980, 270
    body.append(box(cx, cy, cw, ch, "¹", "contributions", f"{today.strftime('%a %-d %b %Y')}", BLUE))
    days = data["calendar"][-182:]
    gl, gr, gt, gb = cx + 16, 700, cy + 34, cy + ch - 34
    step = (gr - gl) / len(days)
    size = round(step - 1.2, 1)
    rows = int((gb - gt) / step)
    counts = sorted(d["count"] for d in days if d["count"])
    cap = counts[int(len(counts) * .97)] if counts else 1
    cols = []
    for i, d in enumerate(days):
        v = 0 if not d["count"] else max(1, round(rows * min(d["count"], cap) / cap))
        x = gl + i * step
        cols.append(f'<g class="up" style="animation-delay:{i * 6}ms"><title>{d["date"]}: {d["count"]}</title>'
                    + dots(x, gb, step, v, size, lambda k: heat(k / rows)) + "</g>")
    body.append("".join(cols))
    # month ticks under the graph
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        if date.day == 1:
            body.append(f'<text x="{gl + i * step:.1f}" y="{gb + 18}" fill="{DIM}">{date.strftime("%b").lower()}</text>')
    body.append(f'<text x="{gl}" y="{gt - 6}" fill="{DIM}">daily · top of scale <tspan fill="{FG}">{cap}+</tspan></text>')

    # core list: weekdays
    kx, ky, kw, kh = 716, cy + 22, 262, ch - 34
    body.append(f'<rect x="{kx}" y="{ky}" width="{kw}" height="{kh}" rx="6" fill="none" stroke="{LINE}"/>')
    body.append(f'<text x="{kx + 14}" y="{ky + 24}" fill="{FG}" font-weight="700">{LOGIN}</text>'
                f'<text x="{kx + kw - 14}" y="{ky + 24}" text-anchor="end" fill="{DIM}">up {today.year - data["joined"]}y</text>')
    wk = m["weekday_contrib"]
    total = sum(wk) or 1
    peak = max(wk) or 1
    for i, c in enumerate(wk):
        y = ky + 52 + i * 20
        hot = i == m["peak_weekday"]
        body.append(
            f'<text x="{kx + 14}" y="{y}" fill="{CYAN if hot else FG}">{WEEKDAYS[i]}</text>'
            + meter(kx + 52, y, 22, c / peak, heat)
            + f'<text x="{kx + kw - 14}" y="{y}" text-anchor="end" fill="{FG}">{100 * c / total:4.1f}%</text>'
        )
    l7, l30, l365 = m["load"]
    body.append(f'<text x="{kx + 14}" y="{ky + kh - 16}" fill="{DIM}">Load AVG: <tspan fill="{FG}">{l7:.2f} {l30:.2f} {l365:.2f}</tspan></text>')

    # mem: languages
    mx, my, mw, mh = 10, 296, 486, 170
    body.append(box(mx, my, mw, mh, "²", "languages", f"{len(data['languages'])} total", MAGENTA, 100))
    langs = top_languages(data, 5)
    for i, lang in enumerate(langs):
        y = my + 32 + i * 22
        body.append(
            f'<text x="{mx + 16}" y="{y}" fill="{FG}">{esc(lang["name"])}</text>'
            + meter(mx + 128, y, 46, lang["percent"] / 100, lambda f, c=lang["color"]: c)
            + f'<text x="{mx + mw - 16}" y="{y}" text-anchor="end" fill="{FG}">{lang["percent"]:5.1f}%</text>'
        )

    # net: lines added (up) and removed (down) per month
    nx, ny, nw, nh = 10, 480, 486, 150
    body.append(box(nx, ny, nw, nh, "³", "lines", "12 months", GREEN, 200))
    months: dict[str, list[int]] = {}
    for c in data["commit_log"]:
        months.setdefault(c["local"][:7], [0, 0])
        months[c["local"][:7]][0] += c["add"]
        months[c["local"][:7]][1] += c["del"]
    keys = []
    d = today.replace(day=1)
    for _ in range(12):
        keys.append(d.strftime("%Y-%m"))
        d = (d - dt.timedelta(days=1)).replace(day=1)
    keys.reverse()
    mid = ny + nh / 2 - 4
    biggest = max(max(months.get(k, [0, 0])) for k in keys) or 1
    nstep = 5.2
    nrows = 9
    for i, k in enumerate(keys):
        add, rem = months.get(k, [0, 0])
        bx = nx + 16 + i * 26
        for j in range(3):
            x = bx + j * nstep
            up = round(nrows * (add / biggest) ** .5) if add else 0
            dn = round(nrows * (rem / biggest) ** .5) if rem else 0
            body.append(dots(x, mid - 2, nstep, up, 4, lambda q: GREEN if q < 5 else YELLOW))
            body.append("".join(f'<rect x="{x:.1f}" y="{mid + 2 + q * nstep:.1f}" width="4" height="4" fill="{RED}" fill-opacity="{1 - q * .07:.2f}"/>' for q in range(dn)))
        body.append(f'<text x="{bx + 6.5:.1f}" y="{ny + nh - 12}" text-anchor="middle" fill="{DIM}" font-size="10">'
                    f'{dt.date.fromisoformat(k + "-01").strftime("%b")[0].lower()}</text>')
    body.append(f'<line x1="{nx + 14}" x2="{nx + 324}" y1="{mid}" y2="{mid}" stroke="{LINE}" stroke-dasharray="2 3"/>')
    sx = nx + 344
    body.append(
        f'<text x="{sx}" y="{ny + 36}" fill="{DIM}">▲ added</text>'
        f'<text x="{sx}" y="{ny + 56}" fill="{GREEN}" font-size="16" font-weight="700">+{compact(data["additions"])}</text>'
        f'<text x="{sx}" y="{ny + 90}" fill="{DIM}">▼ removed</text>'
        f'<text x="{sx}" y="{ny + 110}" fill="{RED}" font-size="16" font-weight="700">−{compact(data["deletions"])}</text>'
        f'<text x="{sx}" y="{ny + 134}" fill="{DIM}">{num(data["commits_total"])} commits</text>'
    )

    # proc: repos with the most commits
    px, py, pw, ph = 504, 296, 486, 334
    body.append(box(px, py, pw, ph, "⁴", "repos", "commits · last 12 months", RED, 300))
    hy = py + 30
    body.append(
        f'<text x="{px + 16}" y="{hy}" fill="{FG}" font-weight="700">Pid</text>'
        f'<text x="{px + 60}" y="{hy}" fill="{FG}" font-weight="700">Program:</text>'
        f'<text x="{px + 270}" y="{hy}" fill="{FG}" font-weight="700">Lang</text>'
        f'<text x="{px + pw - 16}" y="{hy}" text-anchor="end" fill="{FG}" font-weight="700">Commits</text>'
    )
    repos = data["top_repos"][:10]
    rpeak = max(r["commits"] for r in repos) or 1
    for i, r in enumerate(repos):
        y = hy + 24 + i * 22
        if i == 0:
            body.append(f'<rect x="{px + 6}" y="{y - 15}" width="{pw - 12}" height="21" rx="3" fill="{SEL}"/>')
        name = r["name"] if len(r["name"]) <= 24 else r["name"][:23] + "…"
        lang = (r["language"] or "—")[:10]
        body.append(
            f'<text x="{px + 16}" y="{y}" fill="{DIM}">{i + 1:>2}</text>'
            f'<text x="{px + 60}" y="{y}" fill="{FG if r["owned"] else CYAN}">{esc(name)}</text>'
            f'<text x="{px + 270}" y="{y}" fill="{r["color"]}">{esc(lang)}</text>'
            f'<rect x="{px + 360}" y="{y - 8}" width="{70 * r["commits"] / rpeak:.1f}" height="7" rx="1" fill="{heat(r["commits"] / rpeak)}"/>'
            f'<text x="{px + pw - 16}" y="{y}" text-anchor="end" fill="{FG}">{r["commits"]}</text>'
        )
    fy = py + ph - 16
    body.append(
        f'<text x="{px + 16}" y="{fy}" fill="{DIM}"><tspan fill="{CYAN}">cyan</tspan> = contributed to, not mine · '
        f'peak hour <tspan fill="{FG}">{hour_label(m["peak_hour"])}</tspan></text>'
    )

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="A btop-style monitor of GitHub activity for {LOGIN}: daily contributions for the last six months, share by weekday, languages, lines added and removed per month, and the repos with the most commits.">
  <style>
    text {{ font-family: {MONO}; font-size: 12px; }}
    .in {{ animation: in 600ms ease both; }}
    .up {{ animation: up 700ms cubic-bezier(.16,1,.3,1) both; transform-box: fill-box; transform-origin: 50% 100%; }}
    @keyframes in {{ from {{ opacity: 0; }} }}
    @keyframes up {{ from {{ transform: scaleY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{ .in, .up {{ animation: none; }} }}
  </style>
  <rect width="{W}" height="{H}" rx="12" fill="{BG}"/>
  {''.join(body)}
</svg>"""


def main() -> None:
    data = load(LOGIN)
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, "btop.svg"), render(data))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
