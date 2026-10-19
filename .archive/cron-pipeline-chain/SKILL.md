---
name: cron-pipeline-chain
description: "Chain multiple cron jobs where one job's output feeds another's input — with explicit intermediate data persistence."
version: 1.0.0
author: aiprofit / 채니봇
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cron, pipeline, data-pipeline, chaining, intermediate-data, workflow]
    related_skills: [fair-value-portfolio, webhook-subscriptions, meeting-documentation, linear]
---

# Cron Pipeline Chain

> **핵심 교훈**: Hermes cron jobs deliver their output as **chat messages** (Discord/Telegram), **NOT as files on disk**.  
> Job B cannot read Job A's output by default — the data is gone once the message is sent.

## Trigger

Use this skill when designing workflows where:
- Cron job A produces data (analysis, report, metrics)
- Cron job B needs to consume that data as input
- The jobs run on different schedules (A at 08:00, B at 19:00)

## Patterns

### ❌ Anti-Pattern: Assume files are saved

```python
# 틀린 가정: cron 출력이 JSON 파일로 저장되어 있다
data = json.load(open("data/output.json"))  # FileNotFoundError!
```

Hermes cron does NOT save stdout to files. Output goes to the chat platform only.

### ✅ Correct Pattern: Explicit Capture Layer

```
Cron Job A (08:00)             → Discord message (delivered)
                                   ↓
Capture Script (08:05)         → data/daily_snapshot.json (saved)
Subprocess re-runs Job A,       ↓
parses stdout → JSON file    Cron Job B (19:00) reads data/*.json
```

### Built-in: `context_from` (read-only)

If Job B is also a Hermes cron job, you can use `context_from` to inject Job A's **last completed output text** into Job B's prompt:

```bash
hermes cron create \
  --name "Job B" \
  --schedule "0 19 * * *" \
  --context_from JOB_A_ID \
  --prompt "Read the context from Job A and do something with it"
```

This injects Job A's last output as text into Job B's context. **Caveats:**
- Only the most recent run's output is available
- Output is raw text (not structured JSON)
- If Job A hasn't run yet, there's no context
- Context is text only — cannot inject binary files

### For JSON Data: Always Use Explicit File Save

For structured data pipelines, `context_from` is insufficient. Use a **capture script**:

```python
# capture_and_save.py — standalone, does NOT modify Job A's script
import subprocess, json, re

def capture_and_save():
    # 1. Re-run Job A's script (capture stdout, do NOT send to chat)
    result = subprocess.run(
        ["python3", "/path/to/job_a_script.py"],
        capture_output=True, text=True, timeout=180
    )
    stdout = result.stdout
    
    # 2. Parse structured data from stdout
    json_match = re.search(r'\{.*\}', stdout, re.DOTALL)
    data = json.loads(json_match.group()) if json_match else {}
    
    # 3. Save as JSON file for Job B
    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved: {len(data)} items")
```

### 🗂 Pattern: GitHub Report Archive (cron output → date-organized repo)

**Use case:** When stock briefing reports, market analyses, or periodic research outputs should be **persistently archived** to a private GitHub repo — organized by date for easy lookup.

**Architecture:**
```
Cron Job A (08:10 KST)    → ~/.hermes/cron/output/<job_id>/2026-06-29_08-XX-XX.md
Cron Job B (18:00 KST)    → ~/.hermes/cron/output/<job_id>/2026-06-29_18-XX-XX.md
                                ↓ (after all jobs complete)
Collector Script (no_agent) → mybotagent/hermes-stock-briefings/
                                ├── 2026-06-29/
                                │   ├── 01-오전-포트폴리오-브리핑.md
                                │   ├── 02-미국-증시-브리핑.md
                                │   └── 03-매크로-전략-리포트.md
                                └── README.md
```

**Implementation (shell script):**
```bash
#!/bin/bash
# collect_and_push.sh — run as no_agent cron
REPO_DIR="$HOME/hermes-stock-briefings"
declare -A JOBS
JOBS["6297df83d4f3"]="01-오전-포트폴리오-브리핑"
JOBS["2916cc9c2ceb"]="02-미국-증시-브리핑"

for job_id in "${!JOBS[@]}"; do
    latest=$(ls -t "$HOME/.hermes/cron/output/$job_id" 2>/dev/null | head -1)
    [ -z "$latest" ] && continue
    date_str="${latest:0:10}"
    mkdir -p "$REPO_DIR/$date_str"
    src="$HOME/.hermes/cron/output/$job_id/$latest"
    dst="$REPO_DIR/$date_str/${JOBS[$job_id]}.md"
    # MD5 비교: 이미 같은 내용이면 스킵
    [ -f "$dst" ] && [ "$(md5sum "$src" | cut -d' ' -f1)" = "$(md5sum "$dst" | cut -d' ' -f1)" ] && continue
    cp "$src" "$dst"
done
cd "$REPO_DIR" && git add -A && git commit -m "📊 $(date +%Y-%m-%d) 자동 저장" && git push
```

**Key design decisions:**
| Decision | Reason |
|----------|--------|
| **no_agent mode** | No LLM tokens burned — just shell + git |
| **MD5 dedup** | Avoids empty commits when no new data |
| **deliver=local** | Suppresses Discord delivery — script output is not user-facing |
| **Date directories** | `YYYY-MM-DD/` makes browsing by date natural on GitHub UI |

**Setup steps:**
1. Create private repo: `curl POST /user/repos {"name":"reports-repo","private":true,"auto_init":true}`
2. Clone: `git clone https://github.com/owner/reports-repo.git ~/reports-repo`
3. Create script in `~/.hermes/scripts/` (NOT a symlink — see Pitfall 7)
4. Register no_agent cron:
   ```bash
   cronjob action=create name="📊 Reports Archive" schedule="40 18 * * 1-5" \
     script=collect_reports.sh no_agent=true deliver=local
   ```

### 🛠 Pattern: Recurring API Failure → no_agent Conversion

**Symptom:** A cron job using LLM agent mode repeatedly fails with `Broken pipe`, `stale_stream_kill`, or 3/3 retry exhaustion at a consistent time window (e.g., dawn hours).

**Root cause:** The LLM provider's API is unstable during certain time windows (low traffic maintenance, regional network issues). The retry mechanism keeps hitting the same dead window.

**Solution:** Convert the job to **no_agent mode** with a standalone shell script:

```bash
# 1. Create a shell script that does the work without LLM
cat > ~/.hermes/scripts/dawn_task.sh << 'SCRIPT'
#!/bin/bash
set -e
cd ~/repo
git pull --rebase origin main
git submodule update --init --recursive
git add -A
git diff --cached --quiet || (git commit -m "auto-sync $(date)" && git push)
SCRIPT
chmod +x ~/.hermes/scripts/dawn_task.sh

# 2. Update the cron job to no_agent mode
cronjob action=update \
  job_id=JOB_ID \
  no_agent=true \
  script=dawn_task.sh
```

**What changes:**
| Before | After |
|--------|-------|
| LLM agent mode (API calls, ~10-20 turns) | Shell script directly (zero API calls) |
| Each run costs tokens + depends on API | Free, runs in seconds |
| Retry logic can't bypass API downtime | Works regardless of API status |

**Recovery from stale git state:** Before the no_agent script can work, clean up any leftover git problems the failed agent runs caused:
- Dead submodule references: `git config --local --unset submodule.orphan-ref.url`
- Orphan empty dirs from deleted submodules: `git rm --cached orphans/`
- Detached HEAD from aborted submodule updates: `git checkout main`

### ✅ Pattern: Verifying no_agent Mode Works

After converting, test immediately:
```bash
cronjob action=run job_id=JOB_ID
# Check delivery: script stdout should arrive in Discord
```

Then verify the next scheduled run via `cronjob action=list` — `last_status` will show the next run's result.

## Pitfalls

### 🔴 Pitfall 1: stdout-only output (most common)
Most Python analysis scripts use `print()` for their final output. This works for human reading but is invisible to other cron jobs. **Always verify** whether the scripts you're chaining save files.

**How to check:**
```bash
grep -n 'print(' script.py | tail -5    # check for print
grep -n 'open(' script.py | tail -5     # check for file writes
grep -n 'json.dump' script.py | tail -5 # check for JSON saves
```

### 🔴 Pitfall 2: Modified scripts break silently
Never modify the original cron script. Instead, create a **wrapper** that re-runs it and captures output. This way:
- Original cron delivery to Discord is unaffected
- Pipeline data is produced independently
- If the wrapper breaks, the original cron still works

### 🟡 Pitfall 3: Stale data
The capture script and the consumer job run at different times. Ensure:
- Capture runs AFTER the source cron finishes
- Consumer runs AFTER capture finishes
- Timestamps are included in saved data for staleness checks

### 🔴 Pitfall 4: no_agent script path constraint (real file required)

When creating a no_agent cron job, the `script` parameter has a **strict security constraint**:
- **MUST be a real file** inside `~/.hermes/scripts/` (e.g., `collect_reports.sh`)
- **Absolute paths are REJECTED** (`/home/.../script.sh` → error)
- **Symlinks pointing outside `~/.hermes/scripts/` are REJECTED** (symlink → external file → "escapes via traversal" error)

**Workaround:** Copy the script into `~/.hermes/scripts/`:
```bash
# BAD — symlink
ln -sf /path/to/actual/script.sh ~/.hermes/scripts/collect.sh
# → Error: "Script path escapes the scripts directory via traversal"

# GOOD — real file
cp /path/to/actual/script.sh ~/.hermes/scripts/collect.sh
# → Success
```

**Why:** The security scanner resolves symlinks and rejects any that target files outside the sandboxed scripts directory.

### 🟡 Pitfall 5: Silent path failure after repo migration

When a repo is migrated or renamed (e.g. `trading-agents-nuri` → `trade-pipeline`), LLM prompt crons and skill-based crons may still contain the old `cd ~/old-repo/` path in their terminal commands. This causes a **silent failure** — the `cd` fails, but subsequent commands may confusingly run in `$HOME` and produce unexpected results, or crash entirely.

**Check ALL cron jobs after any repo migration:**

```bash
cronjob action=list
# Scan every prompt_preview for old paths
```

**Fix:**
```bash
cronjob action=update job_id=<ID> prompt="<updated prompt with new repo path>"
```

**Common types affected:**
- **LLM prompt crons** (most common) — the `cd ~/old-repo && python3 script.py` is in the prompt text
- **Skill-based crons** — the cron prompt's terminal commands may reference old paths independently of the skill content
- **no_agent script crons** — the `script:` field points to a path under `~/.hermes/scripts/` — less affected, but check anyway

**Verification:** After fixing, dry-run a single phase:
```bash
cd ~/new-repo && python3 pipeline.py --phase 0
# Confirm data files are created at the expected path
ls data/*.txt data/*.json
```

### 🟡 Pitfall 6: Skill scripts with hardcoded old paths

Shell scripts stored in skills (`skill_manage action=write_file file_path=scripts/*.sh`) may contain hardcoded absolute paths to the old repo. These aren't caught by cron prompt scanning because they live in Hermes' skill directory, not in the cron prompt text.

**Fix:**
```bash
skill_manage(action="write_file", name="<skill>", file_path="scripts/<script>.sh", file_content="<updated>")
```

**Real failure (2026-06-07):** `fair-value-portfolio` skill had `collect_and_validate_targets.sh` referencing `/home/ubuntu/.hermes/scripts/analyst_target_collector.py` — symlinks deleted during migration.

### 🟡 Pitfall 7: Daily data lifecycle
Pipeline data is only valid for the current trading day. Implement **cleanup**:

```python
def cleanup_previous():
    """Delete yesterday's data before today's first run"""
    for f in glob.glob("data/*.json"):
        os.remove(f)
```

### 🔴 Pitfall 8: rsync --delete wipes the stage's .git/ (mirror-push scripts, 2026-07-09)

**Symptom:** Mirror-push pattern (`git clone --bare` → `git clone` → `rsync --delete` from local fs) reports `SKIP: stage is not a git repo (bare clone / init required)` on every sub-step, even though the previous log line shows `Cloning into 'stage'... done.`

**Root cause:** `rsync -a --delete` syncs the source fs into the stage dir. If source fs is a **plain directory** (e.g. `~/.hermes/skills/` — no `.git` of its own), rsync's `--delete` removes files in the stage that don't exist in source — including the `.git/` that the prior `git clone` step just created. The next sub-step then sees no `.git/` and reports the stage isn't a repo.

**Fix**: Add `.git` to rsync excludes — and use the glob form, since rsync needs all 3 patterns to catch directory + contents:
```bash
rsync -a --delete \
  --exclude '.git' --exclude '.git/' --exclude '.git/**' \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.DS_Store' \
  src/ stage/
```

**Verification**: After fix, stage `.git/HEAD` and `.git/config` should still exist post-rsync.

### 🔴 Pitfall 10: Collector cron runs before source job finishes (2026-07-17)

**Symptom**: A no_agent collector script runs but finds "변경 없음, 스킵" when new data should exist.

**Root cause**: The collector cron schedule is too close to the source cron's execution window. Source job is an LLM agent (multi-tool, 10-20 minute runtime), collector is a no_agent script that runs 5 minutes after source starts.

**Example**: Source `6297df83d4f3` at `10 8 * * 1-5` (08:10 KST, finishes ~08:22). Collector `7f8ba2820760` was at `15 8 * * 1-5` (08:15 KST) — ran BEFORE source finished. Fixed by moving collector to `50 8 * * 1-5` (08:50).

**Fix**: Add minimum 30-minute buffer after the source job's EXPECTED finish time:
```bash
# 1. Check how long the source actually takes (last_run_at in cron list)
# 2. Add buffer: 08:10 + 12min runtime + 28min buffer = 08:50
cronjob action=update job_id=COLLECTOR_JOB_ID schedule="50 8 * * 1-5"
```

**Rule of thumb**: LLM agent crons take 10-20 minutes. Schedule downstream no_agent collectors at least 40 minutes after source starts (e.g., 08:10 source → 08:50 collector).

### 🟡 Pitfall 9: rsync source = HERMES_HOME → infinite recursion (mirror-push, 2026-07-09)

**Symptom:** Mirror-push script hangs/times out with `rsync error: received SIGINT (code 20)` and `file has vanished` messages for every file in `~/.hermes/`. Cron log shows it's been running 60+ seconds with no progress.

**Root cause:** Generic `ensure_mirror_stage` was called with `src=${HERMES_HOME}` to sync the whole Hermes config dir into the config mirror. But `HERMES_HOME` contains `.mirror/` (the very dirs the rsync is writing to), `.git/`, `wiki/`, etc. — all of which rsync reads back into itself, then re-reads the new copies, etc. → infinite recursion / timeout.

**Fix**: Don't use generic rsync mirror for the config step. Build a **selective copy** of only the desired files (memory snapshot with secrets redacted, cron jobs meta JSON, config.yaml, .env.example). Add strong `.gitignore` in the stage:
```bash
# In the stage's .gitignore:
.env
*.token
*.pem
memories/memory-current.md
cron/jobs.json          # raw jobs not for public record
cron/output/            # delivery logs not for record
.mirror/                # never commit the mirror itself
.git/
```

**Generalization**: Any time the mirror's source could plausibly contain the mirror's destination, hand-pick the files instead of using a generic rsync-with-excludes pattern.

## 🪞 Pattern: GitHub Mirror-Push (local → GitHub "기록용")

**Use case**: Push local `~/.hermes/{wiki,skills,scripts,cron,memories}` to GitHub for **record-only** persistence. Single-direction (local → GitHub), no drift correction, no pull. User principle: "github은 기록용" — push is automatic.

**Reference implementation**: `~/.hermes/scripts/hermes_config_sync.sh` (cron `91059d1e3d31`)

**4+1 sub-step architecture**:
```
ensure_mirror_stage(label, mirror.git, stage/, src/, repo, [excludes...])
  1. bare clone origin (200) OR bare init (404)
  2. stage clone from bare (origin URL fixed)
  3. rsync src → stage (--delete, .git EXCLUDED — see Pitfall 8)
  4. sync_substep: stage에서 git add → commit → push

config step: ensure_mirror_stage 우회 (Pitfall 9)
  → 선별 파일만 manual cp + 강화된 .gitignore
```

**DRY-first vs push-first (사용자 결정, 2026-07-09)**:
- ❌ DRY-first: cron logs only, push requires user confirm → forever no push
- ✅ push-first: cron pushes automatically, `DRY_RUN=1` env for 1-shot preview
- "github은 기록용" principle ⇒ **push must be automatic**

**Setup sequence (5 steps)**:
1. Create 5 repos via `curl POST /user/repos {auto_init:true}`:
   - `hermes-wiki` (existing — direct push from `~/.hermes/wiki`)
   - `hermes-skills`, `hermes-scripts`, `hermes-config` (mirror via bare clone + rsync)
2. Store `GITHUB_TOKEN` in `~/.hermes/.env` (PAT, `repo` scope)
3. `DRY_RUN=1 bash ~/.hermes/scripts/hermes_config_sync.sh` — preview what would be pushed
4. `DRY_RUN=0 bash ~/.hermes/scripts/hermes_config_sync.sh` — first real push
5. Verify drift: `local SHA == remote SHA` for all 4 repos

**Validation (post-push drift check)**:
```bash
TOK=$(grep ^GITHUB_TOKEN= ~/.hermes/.env | cut -d= -f2-)
for repo in hermes-wiki hermes-skills hermes-scripts hermes-config; do
  remote=$(curl -s -H "Authorization: token $TOK" \
    "https://api.github.com/repos/mybotagent/$repo/commits?per_page=1" | \
    python3 -c "import sys,json;print(json.load(sys.stdin)[0]['sha'])")
  echo "$repo: remote=$remote"
done
```

## Best Practices

1. **All intermediate data in `data/` directory** — convention-based, easy to clean
2. **Include timestamp** in every saved JSON — for staleness checks
3. **One-day retention** — delete yesterday's data at the start of today's first run
4. **Separate capture from analysis** — Phase 0 (capture) runs before Phase 1 (filter)
5. **Subprocess, don't import** — re-run the cron script instead of importing its functions. Imports can have side effects and version mismatches.

## Dependencies

- Python 3.11+
- Standard library only (`subprocess`, `json`, `re`, `os`, `datetime`, `glob`)

## References

- `references/noagent-conversion-case-study.md` — Real incident (2026-06-09): LLM cron → no_agent conversion for dawn wiki sync
- `references/cron-job-output-inspection.md` — How to check whether a cron job saves files or only prints to stdout
- `references/stdout-parse-regex-patterns.md` — Reusable regex patterns for parsing structured text output (fair_value_v3 lines, trailing JSON, Korean-name→ticker mapping)
- `references/kanban-linear-sync-workflow.md` — Concrete example: bidirectional Kanban↔Linear sync using cron pipeline + webhook patterns (ID mapping, status mapping, sync loop prevention)
- `references/kanban-db-schema.md` — Kanban SQLite DB schema (tasks, events, runs, comments, links) for direct query integration
