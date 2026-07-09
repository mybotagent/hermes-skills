# Repo Merging Workflow — Worked Example

> Consolidating two overlapping wiki repos into one.
> Real session from 2026-05-31: `fastcampus-harness-engineering-wiki` (part-based)
> and `harness-engineering-wiki` (topic-based) → unified `harness-engineering-wiki`.

## When to Use

- User has two repos covering the same domain
- One is part-based (part1/, part2/) and the other is topic-based (fundamentals/, tools/)
- User says "하나의 레포로 통합" or "merge into one repo"
- User says "불필요한 지식을 많이 쌓아두는건 좋지 않아보여" (basic content should be removed)
- User says "trade-pipeline 레포만 남기고 나머지 지워도 돌아가게끔" (consolidate into a single active repo, archive the rest)

## Step-by-Step Checklist

### 1. Survey Both Repos

```bash
# For each repo, map all .md files
find ~/.hermes/repo-A -name '*.md' -not -path '*/.git/*' | sort
find ~/.hermes/repo-B -name '*.md' -not -path '*/.git/*' | sort
```

**Goal:** Decide which repo becomes the target (B) and which gets archived (A).

### 2. Identify Overlap

Create a mapping like this pattern:

```
fastcampus (A)           → harness-engineering (B)
─────────────────────────────────────────────────
part1/01-*.md             → fundamentals/auto-complete-vs-agents.md  [OVERLAP - merge insights]
part1/02-*.md             → fundamentals/developer-role-shift.md     [OVERLAP - merge insights]
part2/01-07*.md           → instruction-files/ + context-management/ [OVERLAP - merge insights]
part3/01-delegation*.md   → delegation/delegation-policy.md          [OVERLAP - merge insights]
part3/02-claude-perms.md  → delegation/                              [UNIQUE - copy]
part3/03-codex-workspace.md → delegation/                            [UNIQUE - copy]
part3/04-epic-workflow.md → workflows/                               [UNIQUE - copy]
part3/05-branch-review-pr.md → workflows/                            [UNIQUE - copy]
part4/01-skill-basics.md  → skills/                                  [UNIQUE - copy]
part4/03-verify-debug.md  → skills/                                  [UNIQUE - copy]
skills/init-deep.md       → skills/                                  [UNIQUE - copy]
```

Mark each file as: **OVERLAP** (already covered in B), **UNIQUE** (no equivalent in B), or **BASIC** (remove).

### 3. Extract Unique Content from A → B

```bash
cd ~/.hermes/repo-B
mkdir -p workflows skills  # new directories needed
cp ~/temp/repo-A/part3/04-epic-workflow.md workflows/
cp ~/temp/repo-A/part3/05-branch-review-pr.md workflows/
cp ~/temp/repo-A/part4/01-skill-basics.md skills/
...
```

### 4. Prune BOTH Before Consolidating

**Always remove from both repos:**
- CLI basics (`cd`, `ls`, `pwd`, `grep`, `find`)
- Git basics (`git clone`, `git add`, `git commit`, `git push`)
- Install/setup guides for well-known tools
- Course/lecture orientations
- Tool comparisons that only restate official docs

**Rule:** The merged repo should have FEWER files than either original alone.

### 5. Rebuild INDEX.md (Karpathy Catalog)

Write a NEW `index.md` that lists ONLY the files that actually exist.

### 6. Update AGENTS.md

### 7. Commit and Push

### 8. Mark Source Repo as Merged

### 9. Register in Shared Wiki

## Post-Migration Verification (2026-06-07 추가)

> Migrating repo content is only half the work. The other half is updating **every system reference** to the old path.

### 10. Check Cron Prompts for Stale Paths

After content is merged into the target repo, check ALL cron jobs:

```bash
cronjob action=list
# For each job, verify the prompt_preview does NOT reference the old repo path
```

**What to look for:**
- `cd ~/old-repo/` → should be `cd ~/target-repo/`
- `python3 src/script.py` → verify the relative path still resolves in the target repo
- `~/old-repo/data/file.txt` → should be `~/target-repo/data/file.txt`

**Common blind spots:**
- Skill-based crons (`skills: [...]`) — the skill's SKILL.md may have been updated, but the **cron prompt** itself may still have old paths in its terminal commands
- LLM prompt crons — the `cd ~/...` prefix is easy to miss when updating just the script filename
- `no_agent` script crons — verify the `script:` field resolves correctly

**Real failure (2026-06-07):** After `trading-agents-nuri` → `trade-pipeline` migration, the 08:10 portfolio cron still had `cd ~/trading-agents-nuri && python3 src/analyst_target_collector.py`. The old directory was deleted. Cron would fail on next run. The 18:00 cron had already been updated, but 08:10 was missed — always check ALL jobs.

### 11. Update Skill Scripts Referencing Old Paths

```bash
# List skills loaded by cron jobs
cronjob action=list  # check skills: [...] for each job

# For each referenced skill, check its shell scripts
skill_view(name="<skill>", file_path="scripts/<name>.sh")

# If old path found, patch it
skill_manage(action="write_file", name="<skill>", file_path="scripts/<name>.sh", file_content="<updated>")
```

**Real failure (2026-06-07):** `fair-value-portfolio` skill's `collect_and_validate_targets.sh` referenced `/home/ubuntu/.hermes/scripts/analyst_target_collector.py` — but that symlink was deleted during migration.

### 12. Verify the Migration End-to-End

```bash
# Dry-run the main pipeline
cd ~/<target-repo> && python3 pipeline.py --phase 0
# Check data files
ls data/*.txt data/*.json
# Check logs
ls logs/
```

**Key check points:**
- `cd` commands resolve to the target repo
- Python scripts exist at the expected relative paths
- Data files are being written to the correct `data/` directory
- Import paths resolve correctly (especially `sys.path.insert` or `os.path.dirname` chains)

### 13. Archive Source Repos on GitHub

```bash
# Check current state
gh repo list mybotagent --visibility private --limit 50 | grep -i "repo-name"

# Archive via API (needs repo scope token)
gh api -X PATCH repos/mybotagent/repo-name -f archived=true
```

The `gh api -X PATCH` approach works with any `repo`-scope token. The `gh repo edit` command requires `--accept-visibility-change-consequences` flag.

### 14. Update Target Repo README

Add a consolidation table to the target repo's README:

```markdown
## 레포지토리 통합 현황

`<target-repo>`이 유일한 활성 레포입니다. 모든 구 레포는 GitHub에서 ARCHIVED 처리되었습니다.

| 구 레포 | 상태 | 현재 위치 |
|:--------|:----:|:---------|
| `old-repo-a` | ARCHIVED | `path/in/target/` |
| `old-repo-b` | ARCHIVED | `other/path/` |
```

## Extended Checklist

- [ ] Content copied from A to B
- [ ] Pruning pass done
- [ ] index.md rebuilt
- [ ] AGENTS.md updated
- [ ] Committed and pushed
- [ ] **ALL cron prompts checked for old paths** ← easy to miss
- [ ] **ALL skill scripts checked for old paths** ← easy to miss
- [ ] **End-to-end dry-run passed** ← only way to catch silent failures
- [ ] Source repos archived on GitHub
- [ ] Target repo README updated with consolidation table
