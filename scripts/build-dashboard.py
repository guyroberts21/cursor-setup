#!/usr/bin/env python3
"""Merge week config, hours log, GitHub cache, and personal markdown into site/data.json."""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Install PyYAML: pip install pyyaml", file=sys.stderr)
    raise

try:
    import markdown
except ImportError:
    print("Install markdown: pip install markdown", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
WEEKS_DIR = ROOT / "data" / "weeks"
HOURS_PATH = ROOT / "data" / "hours-log.yaml"
CACHE_PATH = ROOT / "data" / "github-cache.json"
NOTES_PATH = ROOT / "data" / "notes.md"
TODOS_PATH = ROOT / "data" / "todos.md"
PROJECTS_PATH = ROOT / "config" / "projects.yaml"
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


def hours_in_week(
    entries: list[dict], week_start: date, week_end: date, *, extra: bool | None = None
) -> dict[str, float]:
    totals: dict[str, float] = {}
    for entry in entries:
        if extra is not None and bool(entry.get("extra")) != extra:
            continue
        entry_date = date.fromisoformat(str(entry["date"]))
        if week_start <= entry_date <= week_end:
            pid = entry["project_id"]
            totals[pid] = totals.get(pid, 0.0) + float(entry["hours"])
    return totals


def project_names() -> dict[str, str]:
    config = load_yaml(PROJECTS_PATH)
    return {pid: data["name"] for pid, data in config.get("projects", {}).items()}


def normalize_time(value: str | datetime) -> str:
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    text = str(value).strip()
    if len(text) >= 5 and text[2] == ":":
        return text[:5]
    return text


def format_time_label(slots: list[dict] | None) -> str | None:
    if not slots:
        return None
    parts = []
    for slot in slots:
        start = normalize_time(slot["start"])
        end = normalize_time(slot["end"])
        parts.append(f"{start}–{end}")
    return ", ".join(parts)


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


def recent_entries(entries: list[dict], names: dict[str, str], limit: int = 14) -> list[dict]:
    enriched = []
    for entry in entries:
        entry_date = entry["date"]
        if not isinstance(entry_date, str):
            entry_date = entry_date.isoformat()
        slots = entry.get("slots") or []
        normalized_slots = [
            {"start": normalize_time(s["start"]), "end": normalize_time(s["end"])} for s in slots
        ]
        enriched.append(
            {
                **entry,
                "date": entry_date,
                "project_name": names.get(entry["project_id"], entry["project_id"]),
                "slots": normalized_slots,
                "time_label": format_time_label(normalized_slots),
            }
        )

    def sort_key(entry: dict) -> tuple:
        first_start = entry["slots"][0]["start"] if entry.get("slots") else "99:99"
        return (entry["date"], first_start, entry.get("note", ""))

    sorted_entries = sorted(enriched, key=sort_key, reverse=True)
    return sorted_entries[:limit]


def parse_todos(path: Path) -> list[dict]:
    if not path.exists():
        return []
    todos: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*-\s*\[( |x|X)\]\s+(.+)$", line)
        if match:
            todos.append({"text": match.group(2).strip(), "done": match.group(1).lower() == "x"})
    return todos


def load_personal() -> dict:
    notes_mtime = NOTES_PATH.stat().st_mtime if NOTES_PATH.exists() else None
    todos_mtime = TODOS_PATH.stat().st_mtime if TODOS_PATH.exists() else None
    notes_raw = NOTES_PATH.read_text(encoding="utf-8") if NOTES_PATH.exists() else ""
    notes_html = markdown.markdown(notes_raw, extensions=["extra"]) if notes_raw.strip() else ""
    todos = parse_todos(TODOS_PATH)
    updated = max((m for m in (notes_mtime, todos_mtime) if m), default=None)
    return {
        "notes_html": notes_html,
        "notes_source": "data/notes.md",
        "todos": todos,
        "todos_source": "data/todos.md",
        "updated_at": datetime.fromtimestamp(updated).astimezone().isoformat() if updated else None,
        "open_todos": sum(1 for t in todos if not t["done"]),
    }


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
    names = project_names()
    logged = hours_in_week(entries, week_start, week_end, extra=False)
    extra_logged = hours_in_week(entries, week_start, week_end, extra=True)

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
            "extra_logged": sum(extra_logged.values()),
            "extra_breakdown": [
                {"id": pid, "name": names.get(pid, pid), "logged_hours": hours}
                for pid, hours in sorted(extra_logged.items())
            ],
            "projects": projects,
        },
        "priorities": priorities[:8],
        "all_assigned_count": len(cache.get("all_assigned", [])),
        "all_assigned": [
            {**item, "days_since_update": days_since(item["updated_at"])}
            for item in cache.get("all_assigned", [])
        ],
        "recent_log": recent_entries(entries, names),
        "github_synced_at": cache.get("synced_at"),
        "personal": load_personal(),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Built dashboard → {OUT_PATH}")


if __name__ == "__main__":
    main()
