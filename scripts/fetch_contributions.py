#!/usr/bin/env python3
"""Fetch the public GitHub contribution calendar and derive profile stats."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = os.environ.get("GH_PROFILE_USER", "StevenRv13")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_days() -> list[dict]:
    response = requests.get(URL, headers={"User-Agent": "StevenRv13-profile-readme/1.0"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        raise RuntimeError("GitHub returned no contribution calendar cells")

    days = []
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        count_value = cell.get("data-count")
        if count_value is not None:
            count = int(count_value)
        else:
            tooltip = soup.find("tool-tip", attrs={"for": cell.get("id")})
            text = tooltip.get_text(" ", strip=True) if tooltip else ""
            match = re.search(r"([\d,]+) contribution", text, flags=re.I)
            count = int(match.group(1).replace(",", "")) if match else 0
        level = int(cell.get("data-level") or 0)
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda item: item["date"])
    return days


def streaks(days: list[dict]) -> tuple[dict, dict]:
    current_end = len(days) - 1
    if current_end >= 0 and days[current_end]["count"] == 0:
        current_end -= 1
    current = 0
    index = current_end
    while index >= 0 and days[index]["count"] > 0:
        current += 1
        index -= 1
    current_start_index = index + 1

    longest = run = 0
    longest_start = longest_end = None
    run_start = None
    for day_index, day in enumerate(days):
        if day["count"]:
            if run == 0:
                run_start = day_index
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start]["date"]
                longest_end = day["date"]
        else:
            run = 0

    current_start = days[current_start_index]["date"] if current else None
    current_end_date = days[current_end]["date"] if current else None
    return (
        {"length": current, "start": current_start, "end": current_end_date},
        {"length": longest, "start": longest_start, "end": longest_end},
    )


def build(days: list[dict]) -> dict:
    current, longest = streaks(days)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max(days, key=lambda item: item["count"])
    monthly: dict[str, int] = {}
    for day in days:
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]
    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": month, "total": value} for month, value in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}: {data['total_contributions']} contributions")
