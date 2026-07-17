---
name: cron-delivery-routing
description: Validate that cron deliver targets match the cron's topic before create/update, and diagnose "I never received X" complaints where cron ran ok. Triggered when (a) creating/updating a cron with an explicit deliver field, (b) user reports missing reports but cron shows ok, (c) cron shows last_delivery_error, (d) auditing all cron jobs during session review.
---

# cron-delivery-routing

## Thread lifecycle (critical) — 2026-07-17
**Discord threads auto-archive after 7 days of inactivity.** They do NOT expire if messages arrive at least once every 7 days. Therefore:
- A cron that delivers daily or multiple times per week keeps its target thread alive forever
- Moving a cron to `origin` or a Home channel is rarely necessary — **keep delivering to the same active thread**
- When a 404 ("Unknown Channel") is detected, first check if the thread was archived (inactivity). If so, migrate to an active thread in the same topic, not to origin.

## Core principle
**A cron's `deliver` field must point to the thread whose TOPIC matches the cron's content.** Configuration silence ≠ correct routing. The cron will return `ok` either way — that's the trap.

## When to load this skill
- Creating any new cron with a `deliver:` field
- Updating a cron's deliver target
- User says "I never received X report" or "추천/리포트 안알려 주네?" but cron logs show successful runs
- Periodic audit of all active cron jobs

## Two failure modes (both observed in production)

### Mode A — Missing thread → 404
- **Symptom**: cron logs `last_delivery_error=Unknown Channel` (Discord 404)
- **Cause**: `deliver=discord:CHAT` (no `:THREAD` suffix)
- **Fix**: add `:THREAD` or use `origin` / `local`
- Caught once on 2026-07-01 (monthly cron batch)

### Mode B — Wrong thread → silent success ⚠️
- **Symptom**: cron runs `ok`, user says "I never got the portfolio/report"
- **Cause**: `deliver` set to a thread whose topic ≠ cron's content
- **The report is delivered successfully — just to the wrong place.** No error logged.
- Caught on 2026-07-02 (`afebf6cb0ab1` LangGraph portfolio → #일정 instead of #주식-증시)
- This is the dangerous mode because there's no signal in the logs to alert you.

## Thread-topic mapping (this Discord)

| Channel / Thread ID | Topic | Use for |
|:--|:--|:--|
| `#주식-증시` `1510404235915694170` | stock market | LangGraph portfolio, stock analysis, daily screener reports |
| `#일정` thread `1520640537995247698` | calendar / schedule | GCal events, time-blocked reminders |
| `1520255092413038732` | daily-survey | `clarify` 5-question daily checklist |
| Discord HomeID only (no thread) | bot home | Will 404 if used as `deliver` |

> ⚠️ **Mapping is deployment-specific.** Always verify before mapping a cron's deliver.
> ⚠️ **Survey thread ≠ calendar thread ≠ stock thread.** They look like threads but each is for one specific topic only.

## Diagnostic sequence

```
hermes cron list                          # all jobs + deliver targets
hermes cron list | grep <JOB_ID>          # one job in detail
```

Look at the `Deliver:` column. If the deliver thread's topic doesn't match the cron name/content, **that's the bug**.

Then check Discord in the topic channel the user expected, and search for the report in the wrong thread to confirm.

## Recovery procedure

```
hermes cron update JOB_ID deliver='discord:CHAT:THREAD'
```

⚠️ **Caveat 1**: `last_delivery_error` may NOT auto-clear from a deliver fix. If the cron still shows an error after a successful update, a manual patch is required.

⚠️ **Caveat 2**: The fix only applies forward. Past reports sent to the wrong thread are **lost to the user** unless you actively retrieve and forward them. For a portfolio/macro report that users care about, manually repost today's content to the correct thread.

## Pre-flight checklist (before cron create/update)

- [ ] Cron name/topic → matching thread ID identified in mapping table (or verified manually via `hermes cron list` if unsure)
- [ ] Test delivery with `repeat=1` and short schedule if uncertain
- [ ] Verify `deliver` field syntax: three colon-separated segments (chat ID + thread ID), no trailing space
- [ ] Run `scripts/audit_cron_deliver.sh` after the update to confirm

## Diagnostic shortcut for "where did X go?"

When user asks about a missing report:
1. `hermes cron list | grep <JOB_ID>` → check the `Deliver:` field first
2. `cat ~/.hermes/cron/output/<JOB_ID>/<latest>.md | tail -80` → see what was generated
3. If cron ran ok AND generated content: search Discord in the **deliver target thread**; if absent there, deliver is misrouted (Mode B)
4. If cron shows error: Mode A or transient failure — see `self-healing-cron`

## References

- `references/case-2026-07-02-portfolio-misroute.md` — afebf6cb0ab1 incident (Mode B in production)
- `references/case-2026-07-01-monthly-batch.md` — three monthly crons with Mode A 404 (deploy-time bug)

## Scripts

- `scripts/audit_cron_deliver.sh` — re-runnable probe that lists all active crons' deliver targets in a single table for manual review
