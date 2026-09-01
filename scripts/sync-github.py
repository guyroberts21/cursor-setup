#!/usr/bin/env python3
"""Sync GitHub priorities from Mindful Support into data/github-cache.json."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.github import (  # noqa: E402
    fetch_issues_rest,
    fetch_project_status_map,
    has_project_scope,
)


def label_names(issue: dict) -> set[str]:
    return set(issue.get("labels", []))


def client_label(issue: dict) -> str | None:
    for name in label_names(issue):
        if name.startswith("client:"):
            return name.split(":", 1)[1]
    return None


def priority_rank(issue: dict) -> int:
    labels = label_names(issue)
    if "P1" in labels:
        return 0
    if "P2" in labels:
        return 1
    return 2


def is_guy_issue(issue: dict) -> bool:
    labels = label_names(issue)
    assignees = {a.get("login") for a in issue.get("assignees", [])}
    return "people:Guy" in labels or "guyroberts21" in assignees


def is_priority_issue(issue: dict) -> bool:
    labels = label_names(issue)
    return "Action needed" in labels and ("P1" in labels or "P2" in labels)


def normalize_issue(issue: dict, status_map: dict[int, str]) -> dict:
    number = issue["number"]
    return {
        "number": number,
        "title": issue["title"],
        "url": issue["url"],
        "labels": issue.get("labels", []),
        "client": client_label(issue),
        "updated_at": issue["updatedAt"],
        "status": status_map.get(number),
    }


def sort_priorities(issues: list[dict]) -> list[dict]:
    return sorted(
        issues,
        key=lambda i: (priority_rank(i), i["updated_at"]),
    )


def main() -> None:
    issues = fetch_issues_rest()
    guy_issues = [i for i in issues if is_guy_issue(i)]

    status_map: dict[int, str] = {}
    project_scope = has_project_scope()
    if project_scope:
        try:
            status_map = fetch_project_status_map()
        except RuntimeError as exc:
            print(f"Warning: could not fetch project status: {exc}", file=sys.stderr)
            project_scope = False

    normalized = [normalize_issue(i, status_map) for i in guy_issues]
    priorities = sort_priorities(
        [i for i in normalized if is_priority_issue({"labels": i["labels"], **i})]
    )

    payload = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "project_scope": project_scope,
        "priorities": priorities,
        "all_assigned": sorted(normalized, key=lambda i: i["updated_at"]),
    }

    out = ROOT / "data" / "github-cache.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Synced {len(priorities)} priorities, {len(normalized)} assigned issues → {out}")


if __name__ == "__main__":
    main()
