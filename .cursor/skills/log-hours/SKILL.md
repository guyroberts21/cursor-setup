---
name: log-hours
description: Log development hours, set weekly MindfulOps targets, and refresh GitHub priorities for Guy's workflow dashboard.
---

# Log Hours Skill

Use when Guy wants to log hours, set the weekly plan, or refresh priorities.

## Commands

| Intent | Action |
|--------|--------|
| Log hours | Append to `data/hours-log.yaml`, rebuild dashboard |
| Week plan | Create/update `data/weeks/YYYY-Www.yaml` |
| Priorities | Run `scripts/sync-github.py` + `scripts/build-dashboard.py` |

## Log hours procedure

1. Read current week from `data/weeks/` (file where today falls between week_start and week_end)
2. Match project mention to a `project_id` in that week file
3. Append entry with today's date (or user-specified date)
4. Run:
   ```bash
   python3 scripts/build-dashboard.py
   ```
5. Report totals per project and overall

## Week plan procedure

1. Determine ISO week from dates provided
2. Write `data/weeks/YYYY-Www.yaml` with projects and target_hours
3. Run build-dashboard.py
4. Confirm total target hours

## Valid project ids

`edma`, `fpmt`, `jamyang`, `rigpa`, `fdcw`, `tushita`, `yeshin`

## Validation

- Reject unknown project ids (list valid ones from current week)
- Hours must be positive numbers
- Do not edit `data/github-cache.json` manually — use sync-github.py

## Daily briefing format

When generating a standup/briefing:

```
Week: {id} ({start} – {end}) — {remaining} work days left
Hours: {logged}h / {target}h ({remaining}h left)

By project:
- {name}: {logged}/{target}h

Top priorities:
1. MD-{n} — {title} ({days}d stale, {client})
...

Suggested focus: {project with most remaining hours + matching open tickets}
```
