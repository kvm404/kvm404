"""Render the profile as a tiled Hyprland desktop in Tokyo Night colours.

Run: GH_TOKEN=... python3 scripts/render.py
Writes assets/desktop.svg.
"""

from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from github_data import load  # noqa: E402
from svg import MONO, calendar_weeks, esc, heatmap, num, top_languages, write  # noqa: E402

LOGIN = "kvm404"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

# Tokyo Night
BG = "#1a1b26"
BG_DARK = "#16161e"
FG = "#c0caf5"
DIM = "#565f89"
BLUE = "#7aa2f7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
MAGENTA = "#bb9af7"
ORANGE = "#ff9e64"
RED = "#f7768e"
YELLOW = "#e0af68"
TEAL = "#73daca"
INACTIVE = "#3b4261"

W, H = 1000, 662
CW = 7.5  # approximate advance of the monospace face at 12.5px

ARCH = r"""                  -`
                 .o+`
                `ooo/
               `+oooo:
              `+oooooo:
              -+oooooo+:
            `/:-:++oooo+:
           `/++++/+++++++:
          `/++++++++++++++:
         `/+++ooooooooooooo/`
        ./ooosssso++osssssso+`
       .oossssso-````/ossssss+`
      -osssssso.      :ssssssso.
     :osssssss/        osssso+++.
    /ossssssss/        +ssssooo/-
  `/ossssso+/:-        -:/+osssso+-
 `+sso+:-`                 `.-/+oso:
`++:.                           `-/+/
.`                                 `/""".split("\n")


def window(x, y, w, h, active=False, delay=0):
    stroke = "url(#active)" if active else INACTIVE
    return (
        f'<g class="pop" style="animation-delay:{delay}ms;transform-origin:{x + w / 2}px {y + h / 2}px">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{BG}" fill-opacity=".94" stroke="{stroke}" stroke-width="2"/>'
    )


def prompt(x, y, cmd, delay=0):
    return (
        f'<text x="{x}" y="{y}" class="t"><tspan fill="{BLUE}">~</tspan>'
        f'<tspan fill="{MAGENTA}"> ❯ </tspan></text>'
        f'<g class="type" style="animation-delay:{delay}ms"><text x="{x + CW * 4}" y="{y}" class="t" fill="{FG}">{esc(cmd)}</text></g>'
    )


def desktop(data: dict) -> str:
    gen = dt.date.fromisoformat(data["generated"])
    parts = []

    # Top bar
    ws = "".join(
        f'<text x="{24 + i * 22}" y="20" class="t" fill="{FG if i == 0 else DIM}">{i + 1}</text>' for i in range(5)
    )
    parts.append(
        f'<rect width="{W}" height="30" fill="{BG_DARK}" fill-opacity=".9"/>{ws}'
        f'<rect x="21" y="25" width="13" height="2" rx="1" fill="{CYAN}"/>'
        f'<text x="{W / 2}" y="20" class="t" fill="{FG}" text-anchor="middle">{gen.strftime("%A %d %B").replace(" 0", " ")}</text>'
        f'<text x="{W - 24}" y="20" class="t" fill="{DIM}" text-anchor="end"><tspan fill="{GREEN}">●</tspan> kvm404 · India</text>'
    )

    # A: fastfetch
    ax, ay, aw, ah = 10, 40, 600, 400
    parts.append(window(ax, ay, aw, ah, active=True, delay=0))
    parts.append(prompt(ax + 18, ay + 30, "fastfetch", 200))
    logo = "".join(
        f'<text x="{ax + 18}" y="{ay + 64 + i * 14}" class="logo" xml:space="preserve">{esc(line)}</text>'
        for i, line in enumerate(ARCH)
    )
    parts.append(f'<g class="out" style="animation-delay:900ms">{logo}')
    info = [
        ("", f'<tspan fill="{CYAN}">kvm404</tspan><tspan fill="{FG}">@</tspan><tspan fill="{CYAN}">krvaibhav.dev</tspan>'),
        ("", f'<tspan fill="{DIM}">{"-" * 20}</tspan>'),
        ("Name", "Kumar Vaibhav"),
        ("Role", "Fullstack developer"),
        ("Study", "BS Data Science, IIT Madras"),
        ("Builds", "Web, Android, Linux, games"),
        ("OS", "Arch Linux x86_64"),
        ("WM", "Hyprland (Omarchy)"),
        ("Langs", ", ".join([l["name"] for l in top_languages(data, 8) if l["name"] not in ("Other", "JavaScript")][:4])),
        ("AI", "Claude Code, Codex"),
        ("Uptime", f"{gen.year - data['joined']} years on GitHub"),
        ("Status", "Open to work"),
    ]
    ix = ax + 276
    for i, (label, value) in enumerate(info):
        y = ay + 64 + i * 19
        if label:
            parts.append(
                f'<text x="{ix}" y="{y}" class="t"><tspan fill="{BLUE}">{esc(label)}</tspan></text>'
                f'<text x="{ix + CW * 10}" y="{y}" class="t" fill="{FG}">{esc(value)}</text>'
            )
        else:
            parts.append(f'<text x="{ix}" y="{y}" class="t">{value}</text>')
    py = ay + 64 + len(info) * 19
    swatches = [BG_DARK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, FG]
    bright = [DIM, "#ff7a93", "#b9f27c", "#ff9e64", "#7da6ff", "#c0a8f9", "#0db9d7", "#e6ebff"]
    for row, cols in enumerate((swatches, bright)):
        for i, c in enumerate(cols):
            parts.append(f'<rect x="{ix + i * 22}" y="{py + row * 16}" width="22" height="16" fill="{c}"/>')
    parts.append("</g>")
    parts.append(prompt(ax + 18, ay + ah - 22, "", 0))
    parts.append(f'<rect class="cursor" x="{ax + 18 + CW * 4}" y="{ay + ah - 34}" width="8" height="15" fill="{FG}"/>')
    parts.append("</g>")

    # B: languages
    bx, by, bw, bh = 620, 40, 370, 195
    parts.append(window(bx, by, bw, bh, delay=150))
    parts.append(prompt(bx + 18, by + 30, "tokei ~/projects --sort bytes", 500))
    langs = top_languages(data, 6)[:6]
    colors = [BLUE, YELLOW, ORANGE, MAGENTA, CYAN, GREEN, DIM]
    rows = []
    for i, lang in enumerate(langs):
        y = by + 60 + i * 21
        track_x, track_w = bx + 18 + CW * 12, bw - 36 - CW * 12 - CW * 7
        fill_w = max(4, track_w * lang["percent"] / 100)
        rows.append(
            f'<text x="{bx + 18}" y="{y}" class="t" fill="{FG}">{esc(lang["name"])}</text>'
            f'<rect x="{track_x}" y="{y - 10}" width="{track_w:.1f}" height="11" rx="2" fill="{INACTIVE}" fill-opacity=".55"/>'
            f'<rect class="grow" style="animation-delay:{1300 + i * 90}ms;transform-origin:{track_x}px 0" x="{track_x}" y="{y - 10}" width="{fill_w:.1f}" height="11" rx="2" fill="{colors[i]}"/>'
            f'<text x="{bx + bw - 18}" y="{y}" class="t" fill="{DIM}" text-anchor="end">{lang["percent"]:.1f}%</text>'
        )
    parts.append(f'<g class="out" style="animation-delay:1300ms">{"".join(rows)}</g></g>')

    # C: numbers
    cx, cy, cw, ch = 620, 245, 370, 195
    parts.append(window(cx, cy, cw, ch, delay=300))
    parts.append(prompt(cx + 18, cy + 30, "gh stats kvm404", 800))
    stats = [
        ("contributions", num(data["contributions_all_time"]), GREEN),
        ("this year", num(data["this_year"]["total"]), TEAL),
        ("merged PRs", num(data["prs_merged"]), MAGENTA),
        ("repositories", num(data["repos"]), BLUE),
        ("best streak", f"{data['streak_longest']} days", ORANGE),
        ("busiest day", f"{data['busiest_day']['count']} in a day", YELLOW),
    ]
    srows = "".join(
        f'<text x="{cx + 18}" y="{cy + 60 + i * 21}" class="t" fill="{DIM}">{esc(k)}</text>'
        f'<text x="{cx + 18 + CW * 15}" y="{cy + 60 + i * 21}" class="t b" fill="{c}">{esc(v)}</text>'
        for i, (k, v, c) in enumerate(stats)
    )
    parts.append(f'<g class="out" style="animation-delay:1600ms">{srows}</g></g>')

    # D: heatmap
    dx, dy, dw, dh = 10, 450, 980, 202
    parts.append(window(dx, dy, dw, dh, delay=450))
    parts.append(prompt(dx + 18, dy + 30, "git activity --last 365d", 1100))
    palette = ["#24283b", "#2f4a3a", "#4d7a45", "#7bae57", GREEN]
    n_weeks = len(calendar_weeks(data))
    cell = round((dw - 60 - 18 - 3 * (n_weeks - 1)) / n_weeks, 2)
    hm, hw, hh = heatmap(data, dx + 60, dy + 48, cell, 3, palette, radius=2.5)
    for i, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="{dx + 18}" y="{dy + 48 + i * (cell + 3) + cell - 2:.1f}" class="t s" fill="{DIM}">{label}</text>')
    more_x = dx + dw - 18 - CW * 4
    legend_x = more_x - 8 - 5 * 16
    legend = "".join(f'<rect x="{legend_x + i * 16}" y="{dy + dh - 25}" width="12" height="12" rx="2" fill="{c}"/>' for i, c in enumerate(palette))
    parts.append(
        f'<g class="out" style="animation-delay:1900ms">{hm}'
        f'<text x="{dx + 60}" y="{dy + dh - 15}" class="t s" fill="{DIM}">{num(data["contributions_last_year"])} contributions in the last year</text>'
        f'<text x="{legend_x - 8}" y="{dy + dh - 15}" class="t s" fill="{DIM}" text-anchor="end">less</text>{legend}'
        f'<text x="{more_x}" y="{dy + dh - 15}" class="t s" fill="{DIM}">more</text></g></g>'
    )

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="A Hyprland desktop: fastfetch for kvm404, language split, {num(data['contributions_all_time'])} contributions, {data['prs_merged']} merged pull requests and a contribution heatmap.">
  <defs>
    <linearGradient id="wall" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1f2335"/><stop offset=".55" stop-color="#16161e"/><stop offset="1" stop-color="#232a4d"/>
    </linearGradient>
    <radialGradient id="glow" cx=".78" cy=".18" r=".6">
      <stop offset="0" stop-color="{MAGENTA}" stop-opacity=".22"/><stop offset="1" stop-color="{MAGENTA}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="active" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#33ccff"/><stop offset="1" stop-color="#00ff99"/>
    </linearGradient>
    <linearGradient id="arch" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{BLUE}"/>
    </linearGradient>
  </defs>
  <style>
    .t {{ font-family: {MONO}; font-size: 12.5px; }}
    .s {{ font-size: 11px; }}
    .b {{ font-weight: 700; }}
    .logo {{ font-family: {MONO}; font-size: 11px; fill: url(#arch); white-space: pre; }}
    .pop {{ animation: pop 500ms cubic-bezier(.34,1.56,.64,1) both; }}
    .type {{ animation: type 600ms steps(12) both; }}
    .out {{ animation: show 1ms both; }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    .grow {{ animation: grow 700ms cubic-bezier(.16,1,.3,1) both; }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(.94); }} }}
    @keyframes type {{ from {{ clip-path: inset(0 100% 0 0); }} }}
    @keyframes show {{ from {{ opacity: 0; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .pop, .type, .out, .cursor, .grow {{ animation: none; }} }}
  </style>
  <rect width="{W}" height="{H}" rx="12" fill="url(#wall)"/>
  <rect width="{W}" height="{H}" rx="12" fill="url(#glow)"/>
  <g clip-path="inset(0 round 12px)">{''.join(parts)}</g>
</svg>"""


def main() -> None:
    data = load(LOGIN)
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, "desktop.svg"), desktop(data))
    print("rendered", data["generated"])


if __name__ == "__main__":
    main()
