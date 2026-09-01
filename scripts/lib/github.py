#!/usr/bin/env python3
"""Shared GitHub GraphQL helpers for Mindful Support sync."""
from __future__ import annotations

import json
import subprocess
from typing import Any

ORG = "MindfulDesign-me"
REPO = "MindfulSupport"
PROJECT_NUMBER = 2
GITHUB_USER = "guyroberts21"


def gql(query: str, variables: dict | None = None) -> dict[str, Any]:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in (variables or {}).items():
        flag = "-F" if isinstance(value, (int, float, bool)) else "-f"
        cmd.extend([flag, f"{key}={value}"])
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.output.strip()[:2000]) from exc
    data = json.loads(raw)
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=2)[:2000])
    return data["data"]


def has_project_scope() -> bool:
    try:
        gql(
            """
            query($org: String!, $num: Int!) {
              organization(login: $org) {
                projectV2(number: $num) { id }
              }
            }
            """,
            {"org": ORG, "num": PROJECT_NUMBER},
        )
        return True
    except RuntimeError:
        return False


def fetch_issues_rest() -> list[dict[str, Any]]:
    """Fetch open issues assigned to Guy via gh CLI (no project scope needed)."""
    raw = subprocess.check_output(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            f"{ORG}/{REPO}",
            "--assignee",
            GITHUB_USER,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,url,labels,updatedAt,assignees",
        ],
        text=True,
    )
    issues = json.loads(raw)
    for issue in issues:
        issue["labels"] = [label["name"] for label in issue.get("labels", [])]
    return issues


def fetch_project_status_map() -> dict[int, str]:
    """Map issue number → Project Status field value."""
    data = gql(
        """
        query($org: String!, $num: Int!) {
          organization(login: $org) {
            projectV2(number: $num) {
              items(first: 100) {
                nodes {
                  content {
                    ... on Issue { number }
                  }
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field { ... on ProjectV2SingleSelectField { name } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """,
        {"org": ORG, "num": PROJECT_NUMBER},
    )
    status_map: dict[int, str] = {}
    items = data["organization"]["projectV2"]["items"]["nodes"]
    for item in items:
        content = item.get("content")
        if not content or "number" not in content:
            continue
        number = content["number"]
        for fv in item.get("fieldValues", {}).get("nodes", []):
            field = fv.get("field") or {}
            if field.get("name") == "Status" and fv.get("name"):
                status_map[number] = fv["name"]
                break
    return status_map
