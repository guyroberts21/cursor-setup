# Guy Weekly Workflow Dashboard

Personal dashboard for tracking MindfulOps weekly hours against GitHub Support priorities.

## Quick start

```bash
pip install -r requirements.txt
python3 scripts/sync-github.py      # fetch priorities from Mindful Support
python3 scripts/build-dashboard.py  # build site/data.json
python3 -m http.server 8080 --directory site
# open http://localhost:8080
```

## GitHub auth

Project board Status requires the `read:project` scope:

```bash
gh auth refresh -s read:project
```

Without it, sync still works using issue labels (Action needed, P1/P2, client:*) but Status column will be empty.

## Logging hours in Cursor

Tell the agent in chat:

- "Log 2h on Jamyang — fixed skus error"
- "1.5 hours EdMa today"
- Paste your MindfulOps weekly row to set targets

Or use the `/log-hours` skill.

## Data files

| File | Purpose |
|------|---------|
| `data/weeks/YYYY-Www.yaml` | Weekly hour targets per project |
| `data/hours-log.yaml` | Daily hour entries |
| `data/github-cache.json` | Synced GitHub priorities (generated) |
| `site/data.json` | Dashboard payload (generated) |

## GitHub Pages (private)

1. Push this repo to a **private** GitHub repo
2. Settings → Pages → Source: **GitHub Actions**
3. First push to `main` triggers deploy

The dashboard URL appears in Actions → Deploy dashboard to GitHub Pages.

## GitHub Actions sync

The `sync-dashboard.yml` workflow runs Mon–Sat at 07:00 UTC. It needs a PAT with access to `MindfulDesign-me/MindfulSupport`:

1. Create a fine-grained or classic PAT with `repo` and `read:project`
2. Add it as repo secret `GH_PAT`
3. The workflow uses `GH_PAT` for cross-org issue fetch

## Cursor daily automation

See `docs/automation-draft.md` for the Mon–Sat automation that syncs, commits, and posts a daily briefing.

Schedule: **Mon–Sat 8:00 AM** (set timezone in Automations editor).

## Priority logic

Open issues assigned to `guyroberts21` (or labelled `people:Guy`) where:

- Label includes **Action needed** AND (**P1** or **P2**)
- Sorted: P1 first, then P2, then oldest `updated_at` first

## Current week seed

Week 2026-W35 (31 Aug – 6 Sep 2026): 10h total across EdMa, FPMT, Jamyang, Rigpa.
