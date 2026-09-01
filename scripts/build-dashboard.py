#!/usr/bin/env python3
"""Merge week config, hours log, and GitHub cache into site/data.json."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Install PyYAML: pip install pyyaml", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
WEEKS_DIR = ROOT / "data" / "weeks"
HOURS_PATH = ROOT / "data" / "hours-log.yaml"
CACHE_PATH = ROOT / "data" / "github-cache.json"
OUT_PATH = ROOT / "site" / "data.json"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def find_current_week(today: date) -> Path | None:
    if not WEEKS_DIR.exists():
        return None
    candidates: list[tuple[date, date, Path]] = []
    for path in sorted(WEEKS_DIR.glob("*.yaml")):
        data = load_yaml(path)
        start = date.fromisoformat(str(data["week_start"]))
        end = date.fromisoformat(str(data["week_end"]))
        candidates.append((start, end, path))
    for start, end, path in candidates:
        if start <= today <= end:
            return path
    if candidates:
        return max(candidates, key=lambda c: c[0])[2]
    return None


def hours_in_week(entries: list[dict], week_start: date, week_end: date) -> dict[str, float]:
    totals: dict[str, float] = {}
    for entry in entries:
        entry_date = date.fromisoformat(str(entry["date"]))
        if week_start <= entry_date <= week_end:
            pid = entry["project_id"]
            totals[pid] = totals.get(pid, 0.0) + float(entry["hours"])
    return totals


def work_days_remaining(week_end: date, today: date) -> int:
    """Mon–Sat work week: count remaining work days including today."""
    if today > week_end:
        return 0
    count = 0
    d = today
    while d <= week_end:
        if d.weekday() < 6:  # Mon=0 … Sat=5
            count += 1
        d += timedelta(days=1)
    return count


def days_since(iso_ts: str) -> int:
    updated = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    delta = datetime.now(updated.tzinfo) - updated
    return max(0, delta.days)


def build_project_summary(week: dict, logged: dict[str, float]) -> list[dict]:
    projects = []
    for p in week.get("projects", []):
        pid = p["id"]
        target = float(p["target_hours"])
        done = logged.get(pid, 0.0)
        projects.append(
            {
                "id": pid,
                "name": p["name"],
                "target_hours": target,
                "logged_hours": done,
                "remaining_hours": max(0.0, target - done),
                "github_clients": p.get("github_clients", []),
            }
        )
    return projects


def recent_entries(entries: list[dict], limit: int = 14) -> list[dict]:
    sorted_entries = sorted(entries, key=lambda e: (e["date"], e.get("note", "")), reverse=True)
    return sorted_entries[:limit]


def main() -> None:
    today = date.today()
    week_path = find_current_week(today)
    if not week_path:
        print("No week config found in data/weeks/", file=sys.stderr)
        sys.exit(1)

    week = load_yaml(week_path)
    week_start = date.fromisoformat(str(week["week_start"]))
    week_end = date.fromisoformat(str(week["week_end"]))

    hours_data = load_yaml(HOURS_PATH)
    entries = hours_data.get("entries", [])
    logged = hours_in_week(entries, week_start, week_end)

    cache = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    projects = build_project_summary(week, logged)
    total_target = float(week.get("total_target", sum(p["target_hours"] for p in projects)))
    total_logged = sum(p["logged_hours"] for p in projects)

    priorities = []
    for item in cache.get("priorities", []):
        priorities.append({**item, "days_since_update": days_since(item["updated_at"])})

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "week": {
            "id": week_path.stem,
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
            "work_days_remaining": work_days_remaining(week_end, today),
        },
        "hours": {
            "total_target": total_target,
            "total_logged": total_logged,
            "total_remaining": max(0.0, total_target - total_logged),
            "projects": projects,
        },
        "priorities": priorities[:8],
        "all_assigned_count": len(cache.get("all_assigned", [])),
        "all_assigned": [
            {**item, "days_since_update": days_since(item["updated_at"])}
            for item in cache.get("all_assigned", [])
        ],
        "recent_log": recent_entries(entries),
        "github_synced_at": cache.get("synced_at"),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Built dashboard → {OUT_PATH}")


if __name__ == "__main__":
    main()
