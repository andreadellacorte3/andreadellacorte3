"""Scrape the public GitHub contribution calendar (no token) into data/contributions.json."""

import datetime as dt
import json
import os
import re
from collections import OrderedDict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "andreadellacorte3")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch_html(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "profile-readme-bot"})
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    tooltips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tooltips.get(cell.get("id"), "")
        match = re.match(r"([\d,]+) contributions?", text)
        count = int(match.group(1).replace(",", "")) if match else 0
        days.append({"date": cell["data-date"], "count": count, "level": int(cell.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: today may still be empty, so don't let it break the streak
    current = 0
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def build_stats(days):
    total = sum(d["count"] for d in days)
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"]) if days else None
    monthly = OrderedDict()
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "best_day": {"date": best["date"], "count": best["count"]} if best else None,
        "monthly": monthly,
    }


def main():
    days = parse_days(fetch_html(USERNAME))
    if not days:
        raise SystemExit("No contribution cells found - GitHub markup may have changed.")
    payload = {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stats": build_stats(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    s = payload["stats"]
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current_streak']}/{s['longest_streak']}")


if __name__ == "__main__":
    main()
