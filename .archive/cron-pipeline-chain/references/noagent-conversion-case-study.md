# no_agent Conversion Case Study: 새벽 Wiki Sync

**Date:** 2026-06-09  
**Cron Job:** `64adaa1d6b0e` (📚 새벽 wiki 동기화)

## Problem

The dawn wiki sync cron job ran as an LLM agent (DeepSeek V4 Flash) every weekday at 04:00 CST (05:00 KST). At this hour, DeepSeek API was consistently unreliable:

```
Stream stale for 180s → no chunks received → kill connection
→ [Errno 32] Broken pipe → 3 retries → all failed
```

The first API call succeeded, but every subsequent call timed out after 180 seconds. The job's core work was simple git operations (pull, submodule update, commit, push) — no reasoning was needed.

## Solution

1. Created `~/.hermes/scripts/dawn_wiki_sync.sh`:
   ```bash
   #!/bin/bash
   set -e
   WIKI_DIR="$HOME/.hermes/wiki"
   cd "$WIKI_DIR"
   git pull --rebase origin main
   git submodule update --init --recursive --remote --merge
   git add -A
   git diff --cached --quiet || (git commit -m "auto-sync $(date)" && git push)
   ```

2. Updated cron to no_agent mode:
   ```
   cronjob action=update job_id=64adaa1d6b0e no_agent=true script=dawn_wiki_sync.sh
   ```

3. Pre-cleanup: removed stale submodule reference `code/stock-analysis-toolkit` that was in `.git/config` but not `.gitmodules`, causing `git submodule update` to fail.

## Result

- **Before:** ~3-5 minute run, 10+ API calls, unreliable at dawn
- **After:** ~3 second run, zero API calls, always reliable
- Side benefit: no unnecessary Discord messages when nothing changed

## Key Lessons

- LLM agent mode for periodic git sync is wasteful — simple shell scripts are faster, cheaper, more reliable
- Always check for stale submodule refs when converting an LLM-based cron to no_agent
- no_agent mode with empty stdout = silent (no delivery) — desirable for no-change days
- Schedule the script at the same time — no_agent doesn't need API stability
