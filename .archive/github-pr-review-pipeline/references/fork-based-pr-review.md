# Fork-based daily review + PR cron recipe (dev-harness-kit pattern, 2026-08-12)

Verified end-to-end with `sh-ai-x/dev-harness-kit` (public, AI-native dev harness plugin).
Our token (`mybotagent`) had only `pull` on the upstream. User's directive: fork and
configure everything on the fork — no upstream account access needed.

## Why fork-based works

| Need | Where it lives |
|---|---|
| Push branches / open PRs | `mybotagent/<repo>` fork (we own it) |
| LLM review secrets (`DEEPSEEK_API_KEY`) | fork secrets |
| Provider picker (`CI_REVIEW_PROVIDER=deepseek`) | fork variables |
| Review workflow execution | fork's copied `.github/workflows/review.yml` on `pull_request` |
| PR target | upstream (`sh-ai-x/dev-harness-kit:main`) via `head=mybotagent:<branch>` |

## Key facts learned (all measured)

- **Fork clone**: `git clone https://mybotagent:${GITHUB_TOKEN}@github.com/mybotagent/<repo>.git`
  then `git remote add upstream https://github.com/<owner>/<repo>.git`. origin=fork (push),
  upstream=original (fetch only).
- **Fork Actions start disabled-ish**: `GET /actions/workflows` returned `total: 0` until we
  ran `PUT /actions/permissions {"enabled": true}` — then all 7 workflows appeared.
- **workflow_dispatch cannot drive review.yml**: run fails at "Resolve PR + provider" step
  (no PR number context). Must use a real PR (`pull_request` event). For verification, open a
  fork-internal PR (fork branch → fork main), let the review run, then close it.
- **docs-only PRs skip the LLM review**: scope job detects no production-code touches →
  review/security jobs `skipped`, audit comment `verdict=MISSING`. This is by design, not a
  failure.
- **User rejected a docs-only PR** (#611, closed unmerged) with "프로젝트 목적을 이해못한거
  같은데". The daily PR must be real code review (bug fix, test gap, code smell) — not doc
  backfill. Read README/AGENTS.md first to understand what the repo actually is.

## Cron prompt structure (agent job, toolsets: terminal + file)

```
0. HARD: git pull upstream main --ff-only before reviewing; pull failure = abort + report
1. bash ~/.hermes/scripts/dev_harness_daily_review.sh   # fork sync + candidate scan
2. Candidate priority: ① code bug/edge case ② test gap ③ code smell ④ doc gap (LAST, never alone)
3. git checkout -b <type>/<slug>-$(date +%Y%m%d) → commit (conventional) → push origin
4. Create PR to upstream via helper script (token from .env, body on stdin)
5. Report PR URL / no-candidate / error
```

## Helper scripts (deployed at ~/.hermes/scripts/)

- `dev_harness_daily_review.sh` — fork sync (pull upstream ff-only + push origin), recent
  commits, candidate scan a~f (skills↔docs mismatch, ko-doc gaps, broken README links,
  TODO/FIXME, CHANGELOG, open PRs for dedup).
- `dev_harness_create_pr.sh <branch> <title>` — reads GITHUB_TOKEN from `.env`, body from
  stdin, POSTs PR to upstream `sh-ai-x/dev-harness-kit` with `head=mybotagent:<branch>`.

## Cron job

- `7cf332efe9e4` — daily KST 09:00 (UTC 00:00), deliver origin, agent mode.
- First validated PR: #611 (closed by user — docs-only, wrong kind of work).
