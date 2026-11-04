"""Fetch the numbers behind the profile cards from the GitHub GraphQL API.

Standard library only, so the workflow needs no installs. The token decides
what gets counted: the default Actions token sees public repos only, while a
personal token with read access also folds private repos into the language
and repo totals. Contribution counts follow the profile's own setting for
showing private contributions, whichever token is used.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request

API = "https://api.github.com/graphql"


def _query(token: str, query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

PROFILE_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    id
    name
    login
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    merged: pullRequests(states: MERGED) { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, after: $after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        isPrivate
        isArchived
        stargazerCount
        createdAt
        primaryLanguage { name color }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


TOP_REPOS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      commitContributionsByRepository(maxRepositories: 10) {
        contributions { totalCount }
        repository { name owner { login } isPrivate primaryLanguage { name color } }
      }
    }
  }
}
"""

HISTORY_QUERY = """
query($owner: String!, $name: String!, $uid: ID!, $after: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after, author: {id: $uid}) {
            pageInfo { hasNextPage endCursor }
            nodes { authoredDate additions deletions }
          }
        }
      }
    }
  }
}
"""

# Commit times are shown in this offset from UTC, in minutes. 330 is IST.
TZ_MINUTES = int(os.environ.get("STATS_TZ_MINUTES", "330"))
MAX_PAGES_PER_REPO = 30


def _commits(token: str, login: str, uid: str, repos: list[dict]) -> list[dict]:
    """Every commit I authored on the default branch of my own repos."""
    tz = dt.timezone(dt.timedelta(minutes=TZ_MINUTES))
    out = []
    for repo in repos:
        after = None
        for _ in range(MAX_PAGES_PER_REPO):
            r = _query(token, HISTORY_QUERY, {"owner": login, "name": repo["name"], "uid": uid, "after": after})
            ref = (r.get("repository") or {}).get("defaultBranchRef")
            if not ref or "history" not in (ref.get("target") or {}):
                break
            hist = ref["target"]["history"]
            for n in hist["nodes"]:
                when = dt.datetime.fromisoformat(n["authoredDate"].replace("Z", "+00:00")).astimezone(tz)
                out.append({
                    "repo": repo["name"],
                    "private": repo["isPrivate"],
                    "local": when.isoformat(),
                    "additions": n["additions"],
                    "deletions": n["deletions"],
                })
            if not hist["pageInfo"]["hasNextPage"]:
                break
            after = hist["pageInfo"]["endCursor"]
    return out


def _streaks(days: list[tuple[dt.date, int]], today: dt.date) -> tuple[int, int]:
    """Return (current, longest) streaks of consecutive days with contributions.

    A current streak survives an empty today, since the day isn't over yet.
    """
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    current = 0
    for day, count in reversed(days):
        if day > today:
            continue
        if count:
            current += 1
        elif day == today:
            continue
        else:
            break
    return current, longest


def fetch(login: str, token: str) -> dict:
    today = dt.datetime.now(dt.timezone.utc).date()

    repos: list[dict] = []
    after = None
    while True:
        data = _query(token, PROFILE_QUERY, {"login": login, "after": after})
        user = data["user"]
        page = user["repositories"]
        repos.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]

    first_year = int(user["createdAt"][:4])
    years = []
    days: list[tuple[dt.date, int]] = []
    for year in range(first_year, today.year + 1):
        c = _query(
            token,
            YEAR_QUERY,
            {
                "login": login,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z",
            },
        )["user"]["contributionsCollection"]
        years.append(
            {
                "year": year,
                "total": c["contributionCalendar"]["totalContributions"],
                "commits": c["totalCommitContributions"],
                "prs": c["totalPullRequestContributions"],
                "issues": c["totalIssueContributions"],
                "reviews": c["totalPullRequestReviewContributions"],
                "private": c["restrictedContributionsCount"],
            }
        )
        for week in c["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days.append((dt.date.fromisoformat(d["date"]), d["contributionCount"]))

    days.sort()
    current, longest = _streaks(days, today)

    # Last 53 weeks, aligned so each column starts on a Sunday like GitHub's graph.
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    by_day = dict(days)
    calendar = []
    d = start
    while d <= today:
        calendar.append({"date": d.isoformat(), "count": by_day.get(d, 0)})
        d += dt.timedelta(days=1)

    langs: dict[str, dict] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            entry = langs.setdefault(name, {"name": name, "color": edge["node"]["color"] or "#888888", "bytes": 0})
            entry["bytes"] += edge["size"]
    total_bytes = sum(l["bytes"] for l in langs.values()) or 1
    languages = sorted(langs.values(), key=lambda l: -l["bytes"])
    for l in languages:
        l["percent"] = round(100 * l["bytes"] / total_bytes, 1)

    now = dt.datetime.now(dt.timezone.utc)
    top = _query(token, TOP_REPOS_QUERY, {
        "login": login,
        "from": (now - dt.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    })["user"]["contributionsCollection"]["commitContributionsByRepository"]
    top_repos = [
        {
            # Private repo names stay private on a public profile.
            "name": "private repo" if t["repository"]["isPrivate"] else t["repository"]["name"],
            "private": t["repository"]["isPrivate"],
            "owned": t["repository"]["owner"]["login"].lower() == login.lower(),
            "language": (t["repository"]["primaryLanguage"] or {}).get("name"),
            "color": (t["repository"]["primaryLanguage"] or {}).get("color") or "#8b949e",
            "commits": t["contributions"]["totalCount"],
        }
        for t in top
    ]

    commits = _commits(token, login, user["id"], repos)
    punch = [[0] * 24 for _ in range(7)]  # [monday..sunday][hour]
    for c in commits:
        when = dt.datetime.fromisoformat(c["local"])
        punch[when.weekday()][when.hour] += 1

    this_year = years[-1]
    last_year_window = sum(c["count"] for c in calendar if dt.date.fromisoformat(c["date"]) > today - dt.timedelta(days=365))

    return {
        "generated": today.isoformat(),
        "name": user["name"] or login,
        "login": user["login"],
        "joined": first_year,
        "followers": user["followers"]["totalCount"],
        "repos": len(repos),
        "public_repos": sum(1 for r in repos if not r["isPrivate"]),
        "stars": sum(r["stargazerCount"] for r in repos if not r["isPrivate"]),
        "prs_total": user["pullRequests"]["totalCount"],
        "prs_merged": user["merged"]["totalCount"],
        "contributions_all_time": sum(y["total"] for y in years),
        "contributions_last_year": last_year_window,
        "this_year": this_year,
        "years": years,
        "streak_current": current,
        "streak_longest": longest,
        "busiest_day": max(calendar, key=lambda c: c["count"]),
        "languages": languages,
        "calendar": calendar,
        "daily": [{"date": d.isoformat(), "count": n} for d, n in days if d <= today],
        "top_repos": top_repos,
        "commits_total": len(commits),
        "additions": sum(c["additions"] for c in commits),
        "deletions": sum(c["deletions"] for c in commits),
        "punchcard": punch,
        "commit_log": [{"local": c["local"][:16], "add": c["additions"], "del": c["deletions"]} for c in commits],
        "repo_years": sorted(int(r["createdAt"][:4]) for r in repos),
        "tz_minutes": TZ_MINUTES,
    }


def load(login: str) -> dict:
    """Fetch live data, or read a cached snapshot when STATS_CACHE is set."""
    cache = os.environ.get("STATS_CACHE")
    if cache and os.path.exists(cache):
        with open(cache) as f:
            return json.load(f)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN or GITHUB_TOKEN to fetch stats.")
    data = fetch(login, token)
    if cache:
        with open(cache, "w") as f:
            json.dump(data, f)
    return data
