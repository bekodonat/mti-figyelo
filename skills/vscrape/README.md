# vscrape — collect text at scale, cheaply, with an AI coding agent (vanilla)

A skill for coding agents (the open SKILL.md format) for one common job: turning many web pages or
documents into one coded table, for example every amendment to a set of laws or constitutions. The
rule it teaches: **agents decide, code does the work.** A cheap script reads everything, a cheap model
extracts the fields in batch, and the expensive model or a human judges only the disagreements.

## Install
1. Copy the `vscrape` folder into your agent's skills folder:
   - **Claude Code:** `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`), or a project's
     own `.claude/skills/`.
   - **Codex and other agents:** `~/.agents/skills/` (Windows: `%USERPROFILE%\.agents\skills\`).
2. Ask the agent for the skill by name (in Claude Code: `/vscrape`; in Codex: `$vscrape`), or run the
   scripts yourself (on Windows use `py` instead of `python3`).

Needs only Python 3.9 or newer, no packages.

## The three scripts
- `scripts/fetch.py urls.txt --out data` — polite, resumable downloader: one request per second per
  host, retries with back-off, never re-fetches a page already on disk, writes a manifest CSV
  (url, saved path, HTTP status, SHA-1, UTC time). `--resample-404` re-checks a sample of recorded
  404s, because overloaded servers sometimes answer fake 404s.
- `scripts/check_complete.py rows.csv expected.csv` — the completeness test: per group, rows captured plus
  rows explained against the official count; exits non-zero if any group does not reconcile.
- `scripts/cost.py --items 12000 --in-tokens 650 --out-tokens 150 --prefix-tokens 1500` — planning
  calculator: cost per route (synchronous, cached, batch, batch + cached) for three model sizes.

## Tested
All three scripts were run on synthetic data: `fetch.py` against a local test server (three pages, one
missing page, a resumed run that fetched nothing, and a 404 re-probe that detected a page that had
appeared), `check_complete.py` on a table with a short group, a duplicate id and an explained gap, and
`cost.py` on a 12,000-item example. The dollar figures it prints are planning estimates at list prices
cached on September 25, 2026; check the live pricing page before budgeting.
