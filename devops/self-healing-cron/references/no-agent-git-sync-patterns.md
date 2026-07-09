# no_agent Git Sync Script — Robust Patterns

> Container: self-healing-cron skill
> Context: dawn_wiki_sync.sh — no_agent mode cron job that syncs git repos at dawn
> Origin: SHO-22 (2026-06-29) — `git push rejected → self-healing 미복구`

## Why This Exists

no_agent cron scripts (`script:` + `no_agent=true`) are pure bash — no LLM fallback, no retry logic beyond what the script itself implements. A buggy git workflow means the script fails silently every time, and the self-healing watchdog (which just re-runs the script) cannot break the cycle.

## Root Causes (dawn_wiki_sync.sh failure)

| Sequence | What Happened | Why It Broke |
|----------|---------------|--------------|
| ① `git pull --rebase` | Unstaged changes from concurrent cron jobs | `set -e` → `||` catch only logs warning, doesn't fix index state |
| ② `git push` | Remote had new commits (other cron pushed first) | No `pull`-before-`push` fallback → rejected |
| ③ `git rebase --abort` needed | Previous failed rebase left stale `.git/rebase-merge` | Next run's `pull --rebase` fails with "already in rebase" |
| ④ Submodule update | `code/stock-analysis-toolkit` in git index (mode 160000) but not in `.gitmodules` | Orphan submodule → `fatal: No url found for submodule path` |

## Robust no_agent Git Sync Pattern

```bash
#!/bin/bash
set -e

WIKI_DIR="$HOME/.hermes/wiki"
LOG_PREFIX="[dawn-wiki-sync]"

echo "$LOG_PREFIX 시작: $(date '+%Y-%m-%d %H:%M KST')"

cd "$WIKI_DIR"

# ── Step 1: Clean stale rebase state ──────────────────
echo "$LOG_PREFIX stale rebase cleanup..."
git rebase --abort 2>/dev/null || true
rm -rf .git/rebase-merge 2>/dev/null || true

# ── Step 2: Stash any local changes ─────────────────────
echo "$LOG_PREFIX stash + pull + pop..."
git stash push --include-untracked -m "auto-stash-$(date +%s)" 2>/dev/null || true

# ── Step 3: Pull with rebase ────────────────────────────
git pull --rebase origin main 2>&1 || echo "$LOG_PREFIX ⚠️ pull 실패 (무시 가능)"

# ── Step 4: Restore local changes ──────────────────────
git stash pop 2>/dev/null || true

# ── Step 5: Submodule update ───────────────────────────
echo "$LOG_PREFIX submodule update..."
git submodule update --init --recursive --remote --merge 2>&1 || \
    echo "$LOG_PREFIX ⚠️ submodule 업데이트 실패"

# ── Step 6: Stage, commit, push ────────────────────────
git add -A 2>&1

if ! git diff --cached --quiet 2>/dev/null; then
    COMMIT_MSG="auto-sync $(date '+%Y-%m-%d %H:%M') KST"
    git commit -m "$COMMIT_MSG"
    echo "$LOG_PREFIX ✅ commit: $COMMIT_MSG"

    echo "$LOG_PREFIX git push..."
    if git push origin main 2>&1; then
        echo "$LOG_PREFIX ✅ push 완료"
    else
        # ── Step 7: Retry on rejected ──────────────────
        echo "$LOG_PREFIX ⚠️ push rejected — pull --rebase 후 재시도"
        git pull --rebase origin main 2>&1 && git push origin main 2>&1
        echo "$LOG_PREFIX ✅ push 완료 (재시도)"
    fi
else
    echo "$LOG_PREFIX ✅ 변경사항 없음 — skip"
fi

echo "$LOG_PREFIX 완료: $(date '+%Y-%m-%d %H:%M KST')"
```

## Key Differences from Naive Approach

| Naive | Robust |
|-------|--------|
| `git pull --rebase` without pre-checks | `git rebase --abort + rm .git/rebase-merge + git stash push` first |
| `git push` with no fallback | `if git push fails → git pull --rebase && git push` |
| `set -e` + unchecked `git push` exit code | Every step has `||` fallback or explicit error handling |
| Submodule errors cause exit | `|| echo` catch → non-fatal |

## Orphan Submodule Detection & Fix

A submodule registered in the git index but missing from `.gitmodules`:

```bash
# Detect
git ls-files --stage | grep "^160000"
# → 160000 <hash> 0\tcode/stock-analysis-toolkit

# Fix (if it should not be a submodule)
git rm --cached code/stock-analysis-toolkit

# Fix (if it should be a submodule — add to .gitmodules)
git submodule add <url> code/stock-analysis-toolkit
```

## Self-Healing Gap

The no_agent watchdog (`self_healing_watchdog.sh`) calls `hermes cron run <job_id>` — it **re-runs the same broken script**. If the script has a logic bug (like no push-rejection retry), every re-run hits the same wall.

**Lesson**: no_agent scripts must be fully self-contained and handle all common git failure modes. If they can't (e.g., need conflict resolution), convert to agent mode or add a fallback that surfaces a clear error.

## Hardened Pattern (post-SHO-22, 2026-06-29)

The reference pattern above used `set -e` + `||` catch. In practice, this still failed when the push retry step itself failed — `set -e` would kill the script *after* the second `git push` rejected, leaving the watchdog with exit 1 but no clear signal that self-heal was needed.

**Final hardened version** — drop `set -e` entirely, exit 2 on terminal failure for explicit self-heal trigger:

```bash
#!/bin/bash
# no set -e — each step uses || to continue safely
# Final failure → exit 2 (not 1) so watchdog can distinguish

WIKI_DIR="$HOME/.hermes/wiki"
HERMES_ROOT="$HOME/.hermes"
LOG_DIR="$HERMES_ROOT/logs/dawn-wiki-sync"
LOG_PREFIX="[dawn-wiki-sync]"

# Persist log to file (for post-mortem) AND tee stdout
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date '+%Y%m%d_%H%M%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Step 0: orphan submodule cleanup (pre-pull, before any conflicts)
git rm --cached code/stock-analysis-toolkit 2>/dev/null || true

# Steps 1-4: rebase abort → stash → pull --rebase → stash pop (as before)
# ...

# Step 6-7: stage, commit, push with TWO-LEVEL retry
if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "auto-sync ..."
    if git push origin main; then
        echo "✅ push 완료 (1회)"
    else
        # Retry with rebase pull
        if git pull --rebase origin main && git push origin main; then
            echo "✅ push 완료 (재시도 성공)"
        else
            # Terminal failure — explicit signal for self-heal
            echo "❌ 푸시 최종 실패 — cron self-heal 대상"
            exit 2
        fi
    fi
fi

exit 0
```

### Key insights from SHO-22 patch

| Decision | Why |
|----------|-----|
| Drop `set -e` | `||` catchers can still let fatal errors through; explicit exit codes are more honest |
| `exit 2` for terminal failure | Watchdog can distinguish "expected skip" (0) from "needs human attention" (1) from "auto-retry target" (2) |
| Log to `$HERMES_ROOT/logs/<job>/<timestamp>.log` | Post-mortem without re-running the script; correlate with Linear issues |
| `git rm --cached <orphan>` pre-pull | Submodule index state must be cleaned before `submodule update` to avoid `fatal: No url found` |
| `tee` stdout to log | Discord delivery still works, but operator can also read the log file directly |

### Verification pattern after patch

```bash
# 1. Run script directly
~/.hermes/scripts/dawn_wiki_sync.sh
echo "exit: $?"  # Should be 0 (no changes) or 0 (committed + pushed)

# 2. Inspect log
ls -lt $HOME/.hermes/logs/dawn-wiki-sync/ | head
cat $HOME/.hermes/logs/dawn-wiki-sync/<latest>.log

# 3. Confirm on remote
cd $HOME/.hermes/wiki && git log --oneline -3
git ls-remote origin main
```

If exit code is **2** → script detected terminal failure; self-heal should fire. If exit **0** with no commit → nothing to sync (good).

### Exit code matrix

| Code | Meaning | Watchdog action |
|------|---------|-----------------|
| 0 | Success (committed + pushed, or no changes) | No-op |
| 1 | Unexpected (operator attention) | Alert |
| 2 | Terminal failure (auto-retry target) | Re-run script |
