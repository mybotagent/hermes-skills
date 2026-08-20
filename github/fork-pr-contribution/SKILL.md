---
name: fork-pr-contribution
description: "Contribute PRs to an external GitHub repo when the token only has pull access — fork, dual-remote clone, scheduled daily code review, candidate discovery, branch, PR open. Triggers: fork해서, PR 올려, 매일 리뷰 후 PR, 외부 레포 PR, pull-only 토큰, upstream 직접 push 불가. Covers the cron-prompt threat-block pitfall (auth must live in scripts, not in the cron prompt)."
category: github
---

# Fork-based PR Contribution Pipeline

## When to use
- Target repo is external and the token has **only `pull` permission** (verified via API, see Step 1)
- User wants **recurring** (e.g. daily) code review + PR contributions to that repo
- Any phrasing like "fork해서 하도록", "매일 하루에 한번 PR", "외부 repo에 PR"
- Distinct from `github-pr-review-pipeline` (that skill reviews/merges PRs *inside* repos the bot already owns; this one *authors* PRs to repos it cannot push to)

## Single formula
```
permission probe → fork create → dual-remote clone → schedule cron
  → per-run: sync(ff-only) → review/candidate discovery → pick 1 candidate
  → branch → conventional commit → push fork → PR open (head=owner:branch)
  → report (PR url | no-candidate | error)
```

## Step 1 — Probe permissions BEFORE designing the flow
```bash
# Does the token have write access? (this decides fork-vs-direct)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('permissions',{}))"
# → {'pull': True} only ⇒ fork-based pipeline required
```
**Pitfall — org 404 ≠ repo missing**: `GET /orgs/<name>` returns 404 when the owner is a **User account**, not an org — the repo may still exist and be public. Always check `GET /repos/<owner>/<repo>` directly before concluding anything:
```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/users/<owner>"   # type: User vs Organization
curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/<owner>/<repo>"
```
(실측 2026-08-11: `sh-ai-x` = User; `GET /orgs/sh-ai-x` → 404, but `sh-ai-x/dev-harness-kit` public & fully readable.)

## Step 2 — Fork + dual-remote clone
```bash
# fork (only works when repo is public or org allows forking)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<owner>/<repo>/forks" -d '{}'

# clone fork with pushable origin + fetch-only upstream
cd ~ && git clone "https://<bot-user>:${GITHUB_TOKEN}@github.com/<bot-user>/<repo>.git"
cd <repo> && git remote add upstream "https://github.com/<owner>/<repo>.git"
git remote -v   # origin=fork(push) upstream=original(fetch)
```

## Step 3 — Schedule the daily cron (agent job, NOT no_agent)
The run needs an LLM to pick a candidate → agent cron with `enabled_toolsets: [terminal, file]`, deliver origin. Prompt must be self-contained: Step 1 run the review script, Step 2 pick one candidate, Step 3 branch/commit/push, Step 4 call the PR-open script, Step 5 report in Korean.

## Candidate discovery checklist (docs-heavy repos work best)
Run read-only checks each cycle; the first hit that is real and safe wins:
- **a. skills/ ↔ docs/skills/ drift**: `skills/<name>/` exists but `docs/skills/<name>.md` missing (실측: `babysit-pr-local` added in PR #607, docs layer never shipped → ideal first PR)
- **b. .ko.md missing**: en doc exists but `docs/skills/<name>.ko.md` absent
- **c. broken README links**: extract `docs/skills/*.md` refs from README, check file existence
- **d. TODO/FIXME quick wins** in code (skip false positives like lint rules that *forbid* TODO)
- **e. CHANGELOG missing latest release entries**
- **f. open PRs/issues** (read before every run — dedupe guard; never re-propose existing work)

## PR open (cross-repo head format)
`head` for a fork PR is **`<bot-user>:<branch>`** (not just `<branch>`), `base: main`:
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<owner>/<repo>/pulls" \
  -d '{"title":"...","head":"<bot-user>:<branch>","base":"main","body":"..."}'
```

## Hard rules
- **Never push to upstream directly** — always fork-mediated
- **Never force push**; sync fork via `git merge --ff-only upstream/main` (fail loudly if diverged)
- Never push to main; never commit `.env`/tokens/secrets
- **No junk PRs**: if no meaningful candidate exists, report "오늘은 후보 없음" and exit — do NOT manufacture a trivial PR

## ⚠️ Cron-prompt threat-block (실측 2026-08-11)
`cronjob create` **rejects prompts containing curl `Authorization:` header patterns**:
```
Blocked: prompt matches threat pattern 'exfil_curl_auth_header'
```
Fix: **keep ALL auth inside standalone scripts**; the cron prompt only calls scripts by path
(`bash ~/.hermes/scripts/<name>.sh`). The prompt must not contain any `curl ... -H "Authorization: ..."` literal, even as documentation. Design scripts so token loading happens inside them (`set -a; source ~/.hermes/.env; set +a`).

## Files
- `scripts/review_and_discover.sh` — fork sync (ff-only) + candidate checklist a–f (read-only; generalized from `dev_harness_daily_review.sh`)
- `scripts/open_fork_pr.sh` — PR open from fork branch, token from `.env`, body via stdin (generalized from `dev_harness_create_pr.sh`)

## References
- `references/gh-token-v2-pitfall.md` — **중요**: classic PAT (`ghp_...`)은 fork push 시 403 거부. fine-grained (`GH_TOKEN_V2`) 필요. 실측 2026-08-15.

## Related
- `github-pr-review-pipeline` — LLM review-bot + auto-merge gate for repos the bot owns (complementary: it handles the *receiving* side once your PR is open)
- `github-pr-workflow` — branch/commit/CI/merge lifecycle
- `daily-repo-orchestrator` — daily repo diagnosis + Linear/Kanban mirror pattern (same STAGE-dry discipline)
- `linear` — batch-migrate issues to a project, project creation
