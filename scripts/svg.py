"""Small helpers shared by the card renderers."""

from __future__ import annotations

import datetime as dt
from html import escape

# Markup and build files skew byte counts without saying much about what I write.
SKIP_LANGUAGES = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile", "CMake", "Linker Script", "Mako", "EJS"}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def esc(text) -> str:
    return escape(str(text), quote=True)


def num(n: int) -> str:
    return f"{n:,}"


def top_languages(data: dict, n: int = 6) -> list[dict]:
    """Top n code languages, re-weighted to 100% once markup is dropped."""
    langs = [l for l in data["languages"] if l["name"] not in SKIP_LANGUAGES]
    total = sum(l["bytes"] for l in langs) or 1
    out = [dict(l, percent=100 * l["bytes"] / total) for l in langs[:n]]
    rest = 100 - sum(l["percent"] for l in out)
    if rest >= 0.5:
        out.append({"name": "Other", "color": "#8b949e", "percent": rest})
    return out


def calendar_weeks(data: dict) -> list[list[dict]]:
    """Group the daily calendar into Sunday-first weeks."""
    weeks: list[list[dict]] = []
    for day in data["calendar"]:
        if dt.date.fromisoformat(day["date"]).weekday() == 6 or not weeks:
            weeks.append([])
        weeks[-1].append(day)
    return weeks


def level(count: int, peak: int) -> int:
    """GitHub-style 0-4 intensity, scaled against a capped peak so one huge day
    doesn't wash out the rest of the year."""
    if count <= 0:
        return 0
    cap = max(4, min(peak, 30))
    ratio = min(count, cap) / cap
    return 1 if ratio <= 0.25 else 2 if ratio <= 0.5 else 3 if ratio <= 0.75 else 4


def heatmap(data: dict, x: float, y: float, cell: float, gap: float, palette: list[str],
            radius: float = 2, animate: bool = False, cls: str = "") -> tuple[str, float, float]:
    """Return (svg, width, height) for a contribution heatmap.

    palette is five colours, empty through busiest. With animate=True each column
    fades in left to right.
    """
    weeks = calendar_weeks(data)
    peak = max((d["count"] for d in data["calendar"]), default=0)
    parts = []
    for wi, week in enumerate(weeks):
        cx = x + wi * (cell + gap)
        first_dow = (dt.date.fromisoformat(week[0]["date"]).weekday() + 1) % 7
        style = f' style="animation-delay:{wi * 18}ms"' if animate else ""
        parts.append(f'<g class="hm-col {cls}"{style}>')
        for di, day in enumerate(week):
            cy = y + (first_dow + di) * (cell + gap)
            lv = level(day["count"], peak)
            parts.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" rx="{radius}" '
                f'fill="{palette[lv]}"><title>{day["date"]}: {day["count"]}</title></rect>'
            )
        parts.append("</g>")
    width = len(weeks) * (cell + gap) - gap
    height = 7 * (cell + gap) - gap
    return "".join(parts), width, height


def monthly_totals(data: dict, months: int = 12) -> list[tuple[str, int]]:
    """Contribution totals for the last `months` calendar months, oldest first."""
    sums: dict[str, int] = {}
    for day in data["calendar"]:
        key = day["date"][:7]
        sums[key] = sums.get(key, 0) + day["count"]
    keys = sorted(sums)[-months:]
    return [(dt.date.fromisoformat(k + "-01").strftime("%b"), sums[k]) for k in keys]


def write(path: str, svg: str) -> None:
    with open(path, "w") as f:
        f.write(svg.strip() + "\n")


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def hour_label(h: int) -> str:
    return f"{h % 12 or 12} {'am' if h < 12 else 'pm'}"


def metrics(data: dict) -> dict:
    """Numbers derived from the raw snapshot, shared by every layout."""
    punch = data["punchcard"]
    hours = [sum(punch[w][h] for w in range(7)) for h in range(24)]
    weekday_commits = [sum(row) for row in punch]
    commits = sum(hours) or 1

    # Weekday totals from the contribution calendar (includes private work).
    weekday_contrib = [0] * 7
    for day in data["calendar"]:
        weekday_contrib[dt.date.fromisoformat(day["date"]).weekday()] += day["count"]

    daily = [d["count"] for d in data["daily"]]
    last_year = daily[-365:]
    active = sum(1 for c in last_year if c)

    def avg(n):
        window = daily[-n:]
        return sum(window) / max(1, len(window))

    months = monthly_totals(data, 13)[:-1]
    best_month = max(months, key=lambda m: m[1])
    night = sum(hours[h] for h in (22, 23, 0, 1, 2, 3))
    morning = sum(hours[h] for h in range(5, 12))
    day_ = sum(hours[h] for h in range(12, 18))
    evening = sum(hours[h] for h in range(18, 22))

    peak_hour = max(range(24), key=lambda h: hours[h])
    return {
        "hours": hours,
        "peak_hour": peak_hour,
        "weekday_commits": weekday_commits,
        "weekday_contrib": weekday_contrib,
        "peak_weekday": max(range(7), key=lambda w: weekday_contrib[w]),
        "weekend_share": (weekday_contrib[5] + weekday_contrib[6]) / max(1, sum(weekday_contrib)),
        "dayparts": [("Morning", morning), ("Afternoon", day_), ("Evening", evening), ("Night", night)],
        "night_share": night / commits,
        "active_days": active,
        "per_active_day": sum(last_year) / max(1, active),
        "load": (avg(7), avg(30), avg(365)),
        "best_month": best_month,
        "months": months,
    }


def compact(n: float) -> str:
    """699,000 -> 699k, 1,250,000 -> 1.3M."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1000:.0f}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(int(n))


def active_years(data: dict) -> list[dict]:
    """Years from the first one with real activity onward."""
    years = data["years"]
    start = next((i for i, y in enumerate(years) if y["total"] >= 10), 0)
    return years[start:]
