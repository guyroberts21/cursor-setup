# Cursor Automation Draft — Daily Workflow Briefing

Use this as reference when creating the automation in the Cursor Automations editor.

## Draft table

| Field | Value |
|-------|-------|
| Name | Guy Daily Workflow |
| Description | Sync GitHub priorities, rebuild dashboard, commit, and post daily hours briefing Mon–Sat |
| Trigger | Schedule — Mon–Sat at 8:00 AM (confirm timezone in editor) |
| Tools | Git (checkout/push on this repo) |
| Instructions | See prompt below |
| Repo | This repo (`cursor-setup`), branch `main` |
| To finish in editor | Confirm schedule timezone; confirm git push permissions |

## Prompt

```
You are Guy's weekly workflow assistant. Run the daily Mon–Sat briefing.

1. Pull latest from main
2. Run: python3 scripts/sync-github.py
3. Run: python3 scripts/build-dashboard.py
4. If data/github-cache.json or site/data.json changed, commit and push:
   git add data/github-cache.json site/data.json
   git commit -m "chore: daily sync YYYY-MM-DD"
   git push

5. Read site/data.json and post a briefing:

**Week** — {week.id} ({start} – {end}), {work_days_remaining} work days left
**Hours** — {total_logged}h logged / {total_target}h target ({total_remaining}h remaining)

Per project:
- {name}: {logged}/{target}h

**Top priorities** (Action needed + P1/P2, stale first):
1. MD-{n} — {title} ({days_since_update}d since update, {client})
...

**Suggested focus today:** Recommend which project to prioritize based on remaining hours and open tickets per client.

Keep the briefing concise. If sync fails due to gh auth, note that Guy should run: gh auth refresh -s read:project
```

## Cron expression

Mon–Sat at 8:00 AM:

```
0 8 * * 1-6
```

## Wire format (for open_automation prefill)

```json
{
  "name": "Guy Daily Workflow",
  "description": "Sync GitHub priorities, rebuild dashboard, commit, and post daily hours briefing Mon–Sat",
  "workflow": {
    "triggers": [{ "cron": { "cron": "0 8 * * 1-6" } }],
    "actions": [{ "git": {} }],
    "prompts": ["<prompt above>"],
    "memoryEnabled": true
  }
}
```

Note: Set `workflow.gitConfig.repo` and `workflow.gitConfig.branch` to this repo in the Automations editor.
