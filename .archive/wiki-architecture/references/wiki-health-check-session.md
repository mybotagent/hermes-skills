# Wiki Health Check — Session Reference (2026-05-31)

This file captures the exact commands and scan patterns used during the
2026-05-31 wiki health check session. Use as a recipe for future scans.

## Session Context

User ("꼬북아") asked: "로컬에 outdate된 정보가 있는지 확인하고 정리"
The scan uncovered 14 stale files and 4 content errors in infra/people docs.

## Step-by-Step Scan

### 1. List All Wiki Files

```bash
cd ~/.hermes/wiki
for f in *.md analysis/*.md infra/*.md code/*.md watchlist/*.md people/*.md; do
    [ -f "$f" ] && echo "=== $f ===" && wc -l < "$f"
done
```

Look for files that appear at root AND in subdirectories — those are duplicates.

### 2. Compare Root vs Subdirectory Content

```bash
cd ~/.hermes/wiki
# For each file that exists in both places:
diff <(sed 's/[[:space:]]//g' methodology.md) <(sed 's/[[:space:]]//g' analysis/methodology.md)
# same? `echo $?` → 0 = identical → root copy is stale
```

Files checked in the 2026-05-31 session (all were duplicates):
- `methodology.md` ≡ `analysis/methodology.md`
- `orbit-valuation.md` ≡ `analysis/orbit-valuation.md`
- `stock-rating-system.md` ≡ `analysis/stock-rating-system.md`
- `cron-jobs.md` ≡ `infra/cron-jobs.md` (⚠️ NOT identical — root had job #7, infra didn't)
- `discord-gateway.md` ≡ `infra/discord-gateway.md`
- `environment.md` ≡ `infra/environment.md` (⚠️ NOT identical — path/user diffs)
- `gh-token.md` ≡ `infra/gh-token.md`
- `scripts.md` ≡ `code/scripts.md`
- `tickers.md` ≡ `watchlist/tickers.md`
- `README.md` ≡ `watchlist/README.md`

### 3. Check Server Paths

```bash
echo "User: $(whoami)"
echo "Python: $(which python3)"
echo "Hermes home: $HERMES_HOME"
echo "Git credential: $(cat ~/.git-credentials | head -c 10)..."
```

Cross-reference against `infra/environment.md`:
- `User:` should match `whoami` (e.g. `ubuntu` not `root`)
- `Python:` should match `which python3` (e.g. `/home/ubuntu/.hermes/hermes-agent/venv/bin/python3`)
- `Token:` should be `~/.git-credentials` not `/tmp/ghtoken`

### 4. Check Cron State

```bash
cronjob(action='list')
```

Compare against `infra/cron-jobs.md`. Every job in the doc must have a matching
`job_id` in actual cron output. Every actual job must appear in the doc.

### 5. Check User Profile

Read `people/<username>.md` and verify:
- Name matches current memory/user preference
- Referenced repos still exist (check with GitHub API)
- No references to deleted/archived repos

## Common Stale-Info Patterns Found

| Pattern | Example | Fix |
|---------|---------|-----|
| Root user path | `User: root` | Change to `ubuntu` |
| Old Python path | `/usr/local/lib/hermes-agent/venv/bin/python3` | Change to `/home/ubuntu/.hermes/hermes-agent/venv/bin/python3` |
| Old token path | `/tmp/ghtoken` | Change to `~/.git-credentials` |
| Old name/honorific | `채워니 (Chaewoni)` | Change to `꼬북아` |
| Missing cron job | Job #7 absent from doc | Add row |
| Duplicate root file | `methodology.md` at root + in `analysis/` | Delete root copy |
| Stale repo list | Missing `hermes-logs`, `hermes-wiki-schedule` | Update table |
