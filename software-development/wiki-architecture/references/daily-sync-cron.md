# Daily Wiki Sync Cron Workflow

> Routine daily pull-and-log cycle for the hermes-wiki repo family.
> Runs at 04:00 KST via cron. Even when local state is clean, remote
> changes may exist — the pull always reveals any overnight work.

## Workflow

### 1. Check All Three Repos

```bash
cd ~/.hermes/wiki && git status --short
cd ~/.hermes/hermes-wiki-claude-code && git status --short
cd ~/.hermes/hermes-wiki-codex && git status --short
```

### 2. Pull Remote Changes on All Three

```bash
cd ~/.hermes/wiki && git pull --ff-only origin main
cd ~/.hermes/hermes-wiki-claude-code && git pull --ff-only origin main
cd ~/.hermes/hermes-wiki-codex && git pull --ff-only origin main
```

**`git status --short` may show nothing, but `git pull` can still reveal significant remote work** — entire repo directories may be deleted or restructured. Always pull regardless of local status.

### 3. Commit Local Changes (if any)

If local changes exist (e.g. from wiki-save or another operation since last sync):

```bash
cd ~/.hermes/wiki
TIMESTAMP=$(TZ='Asia/Seoul' date '+%Y-%m-%d %H:%M KST')
git add -A
git commit -m "auto-sync ${TIMESTAMP}"
git push origin main
```

Repeat for claude-code and codex repos if they also have local changes.

### 4. Log Significant Remote Changes

When the pull reveals updates worth noting (file deletions, restructures, new content):

```bash
cd ~/.hermes/wiki/logs
TIMESTAMP=$(TZ='Asia/Seoul' date '+%Y-%m-%d-%H%M')
# Create log file with summary of changes
cat > "2026/${TIMESTAMP}.md" << 'EOF'
---
tags: ["log", "sync", "cleanup", "wiki"]
---
...
EOF
```

### 5. Commit Log + Update Parent Submodule Pointer

**Important — the logs submodule uses `master` as its branch, NOT `main`:**

```bash
cd ~/.hermes/wiki/logs
TIMESTAMP_FILE=$(TZ='Asia/Seoul' date '+%Y/%Y-%m-%d-%H%M.md')
git add "$TIMESTAMP_FILE"
git commit -m "auto-sync $(TZ='Asia/Seoul' date '+%Y-%m-%d %H:%M KST')"
git push origin HEAD:master      # ← detached HEAD → push to master, not main
```

Then update the parent repo's submodule pointer:

```bash
cd ~/.hermes/wiki
git add logs
git commit -m "auto-sync ... - logs submodule update"
git push origin main
```

## Pitfalls

### 1. Logs Submodule Branch Is `master`, Not `main`

The `logs` submodule (pointing to `mybotagent/hermes-logs`) uses the `master` branch.
After committing inside a detached HEAD, `git push origin main` fails with:

```
error: src refspec main does not match any
```

**Fix:** `git push origin HEAD:master`

**Permanent fix** (to work with normal `git push`):
```bash
cd ~/.hermes/wiki/logs
git checkout -b master          # create local branch tracking current HEAD
# Next time: git push works normally
```

### 2. Memory Tool Unavailable in Cron

The `memory()` tool is not loaded in cron/background sessions. Any step that reads
or writes memory (e.g. "clean stale memory entries") must be deferred to a
user-facing session or skipped. Use `terminal`, `file`, and `git` tools only.

### 3. Remote Changes Can Be Large Even When Local Is Clean

Real example (2026-06-08): `git pull --ff-only` in hermes-wiki revealed:
- 15 files changed (93 insertions, 294 deletions)
- 5 repo reference files deleted from `repos/` directory
- AGENTS.md, index.md, analysis/, code/, infra/ files all refactored

This was all remote-only work (from another session on a different machine).
**Always pull — never assume 'no local changes' means 'no work to log'.**

### 4. Submodule Sync Requires Two Commits + Two Pushes

A single log entry requires:
1. Commit inside `logs/` submodule → push to `master`
2. Commit in parent `hermes-wiki` repo (submodule pointer update) → push to `main`

Forgetting either step leaves the parent repo pointing to the old submodule commit.

## Branch Summary

| Repo | Local Path | GitHub Remote | Branch |
|:-----|:-----------|:--------------|:-------|
| hermes-wiki | `~/.hermes/wiki/` | mybotagent/hermes-wiki | `main` |
| hermes-wiki-claude-code | `~/.hermes/hermes-wiki-claude-code/` | mybotagent/hermes-wiki-claude-code | `main` |
| hermes-wiki-codex | `~/.hermes/hermes-wiki-codex/` | mybotagent/hermes-wiki-codex | `main` |
| hermes-logs | `~/.hermes/wiki/logs/` (submodule) | mybotagent/hermes-logs | `master` |
