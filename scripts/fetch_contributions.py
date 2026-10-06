"""Download the public contribution calendar. No token.

GitHub serves the same HTML fragment the profile graph uses:

    https://github.com/users/<username>/contributions

    python scripts/fetch_contributions.py
    python scripts/fetch_contributions.py someuser
"""

import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_USER", "geezkiran")
OUT = ROOT / "data" / "contributions.json"
URL = f"https://github.com/users/{USER}/contributions"
COUNT_RE = re.compile(r"(\d+)\s+contribution")


def contribution_count(label: str) -> int:
    if not label or label.lower().startswith("no contribution"):
        return 0
    match = COUNT_RE.search(label)
    return int(match.group(1)) if match else 0


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for day in days:
        if day["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    ordered = list(days)
    today = date.today().isoformat()
    if ordered and ordered[-1]["date"] == today and ordered[-1]["count"] == 0:
        ordered = ordered[:-1]
    current = 0
    for day in reversed(ordered):
        if day["count"] == 0:
            break
        current += 1
    return current, longest


def main() -> None:
    response = requests.get(
        URL,
        headers={"User-Agent": "geezkiran-profile-readme"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        tip = soup.find("tool-tip", attrs={"for": cell.get("id")})
        label = tip.get_text(" ", strip=True) if tip else ""
        days.append(
            {
                "date": cell["data-date"],
                "level": int(cell.get("data-level", "0")),
                "count": contribution_count(label),
            }
        )
    days.sort(key=lambda day: day["date"])
    if not days:
        raise SystemExit(f"no contribution cells found for {USER}")

    heading = soup.select_one("h2")
    heading_text = heading.get_text(" ", strip=True) if heading else ""
    total_match = re.search(r"([\d,]+)\s+contribution", heading_text)
    total = int(total_match.group(1).replace(",", "")) if total_match else sum(d["count"] for d in days)
    current, longest = streaks(days)
    best = max(days, key=lambda day: day["count"])

    payload = {
        "user": USER,
        "total": total,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"wrote {OUT}  {total} contributions  "
        f"streak {current}  longest {longest}  best {best['count']} on {best['date']}"
    )


if __name__ == "__main__":
    main()
