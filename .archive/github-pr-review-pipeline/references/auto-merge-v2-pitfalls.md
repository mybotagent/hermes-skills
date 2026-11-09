# auto-merge.yml v2 — Race-Condition Hardening (2026-07-07)

## What broke in v1

v1 of `templates/auto-merge.yml` had two compounding bugs that caused
PR #1 fix-comments (verdict=Approve) to be ignored for 6+ minutes while
auto-merge runs sat `in_progress`:

### Bug 1 — "worst-of verdict polling" masks Approve re-reviews

`scripts/review_pr.py` writes one verdict comment per push. After a
fix-commit push, the new comment says `**Verdict:** Approve`. But the
older `**Verdict:** Changes Requested` comment is still on the timeline.
v1's poll loop did:

```bash
worst=""
worst_rank=-1
for v in $(... grep -oE '\*\*Verdict:\*\*\s*(Approve|Changes Requested|Blocked)' ...); do
  r=$(rank "$v")
  if [ "$r" -gt "$worst_rank" ]; then worst_rank=$r; worst=$v; fi
done
```

This ranks `Blocked(2) > Changes Requested(1) > Approve(0)` and picks
the highest. After fix, the timeline had:
[Blocked(2026-07-06), Approve(17:57:53), Approve(17:58:11),
Approve(17:58:18)], worst-of = Blocked → `VERDICT=Blocked` →
auto-merge skip → runs hold `in_progress` until 15-min timeout.

The OPPOSITE failure mode of what v1 set out to prevent ("a PR flagged
🟠 then re-reviewed as Approve will silently auto-merge"). Both
pitfalls are real, but **worst-of kills production PRs; fix
re-reviews should win**.

### Bug 2 — No concurrency control

Every `synchronize` push + every `workflow_dispatch` triggers a new
auto-merge run. Without `concurrency`, 3–4 runs queue up for the same
PR, each spinning the poll loop independently. First run's wait step
ends, but other runs are still polling stale comments.

## v2 fix (both bugs)

```yaml
concurrency:
  group: auto-merge-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

Verdict selection priority:

1. **sha-matched comment** — body contains `<!-- sha: <HEAD_SHA> -->`
   (write this marker in `review_pr.py` for ideal case)
2. **Latest github-actions[bot] verdict line** — `tail -1` over any
   verdict line in any bot comment on the PR, read fresh each poll
3. Anything else → `<timeout>`

Step 2 alone fixes Bug 1 (one bot comment per push, latest push wins).
Step 1 ties verdict commit-by-commit. Drop step 1 if `review_pr.py`
doesn't yet write the marker; step 2 still works.

Also: live `head_sha` fetch on `workflow_dispatch` path
(`github.event.pull_request.head.sha` is empty when dispatching
manually), and timeout reduced from 15 → 10 min.

## Apply to existing consumer repos

Hub + 2 consumers need this swap. Classic `GITHUB_TOKEN` with `repo`
scope does NOT have `workflow` scope — fine-grained
`GH_TOKEN_V2` (Contents + Workflows R&W on target repos) is required:

```text
"refusing to allow a Personal Access Token to create or update
workflow `.github/workflows/auto-merge.yml` without `workflow` scope"
```

PUT body per repo (`HEAD` + `FSHA` from Contents API, content from
`templates/auto-merge.yml` base64-encoded) — 3 commits on 2026-07-07:

| repo | commit |
|---|---|
| `mybotagent/hermes-pr-gate` | `bc8ea6ee` |
| `mybotagent/mybotagent.github.io` | `b1e188c3` |
| `mybotagent/hermes-wiki-super` | `79eb1394` |

## When reviewing a stuck auto-merge — the 60-second triage

When user reports "PR stuck / auto-merge not happening / 6 min
in_progress", check in this order:

1. **Is `auto-merge.yml` v2 installed?** (has `concurrency:` block +
   newest-sha verdict selection). If v1 worst-of, patch it.
2. **Is the verdict comment even there?** Run `gh api
   repos/OWN/REPO/issues/N/comments --jq '.[] |
   select(.user.login=="github-actions[bot]") | {created_at, body:
   .body[0:80]}'`. If empty, review-bot didn't run → check
   `review-bot.yml` trigger + secrets (`MINIMAX_API_KEY`,
   `MINIMAX_BASE_URL`).
3. **Is `mergeable_state` not in `{clean, unstable, behind}`?**
   That blocks the merge step independently of verdict. Run `gh pr
   view N --json mergeable,mergeableState`.
4. **Fallback when (1)–(3) all fine but run times out**: cancel
   in-progress runs + manual squash merge (Pitfall 12 in SKILL.md).

## Why this matters for future sessions

Don't burn 6 min waiting on a stuck run when the fix is one PUT away.
When touching any auto-merge related workflow, verify v2 markers
first; if absent, patch in place.
