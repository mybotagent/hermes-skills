---
name: wiki-architecture
description: "Architect and maintain Karpathy-style wiki repos with per-thread/context routing for Hermes Agent — shared INDEX repo + thread-specific GitHub repos + AGENTS.md routing rules."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, knowledge, architecture, routing, threads, repos]
    related_skills: [writing-plans, requesting-code-review, wiki-save, newsletter-publishing]
---

# Wiki Architecture (Karpathy Pattern + Thread Routing)

## Overview

Structured knowledge base for Hermes Agent, following Karpathy's "LLM Wiki" gist pattern
(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) extended for
multi-thread/context environments.

The core idea: **one INDEX repo + per-context thread repos**, each with its own `index.md`
and `AGENTS.md`. The agent determines which context it's in from memory and loads the
correct thread repo via routing rules defined in the shared `AGENTS.md`.

## Architecture: Five Layers

```
1. Raw Sources (immutable)    — session_search, chat transcripts, external sources
2. Shared Wiki (INDEX repo)   — mybotagent/hermes-wiki
   ├── research/ (typed pages) — entities, concepts, comparisons
   └── operational (free-form) — analysis, infra, code, people, etc.
3. Thread Wikis (per-context) — separate GitHub repos per Discord thread
4. Logs (timestamped)         — mybotagent/hermes-logs (YYYY-MM-DD-HHMM.md)
5. Schema                     — SCHEMA.md + AGENTS.md (rules, tags, lint)
```

### Layer 1 — Raw Sources

## Core Principles (Karpathy-Style)

### 1. READMEs Are READ-ONLY LANDING PAGES

README.md must be **stable** — it should never need updating.

**Do NOT put in README:**
- Script/file lists (e.g. "scripts: orbit_v2.py, macro_strategy.py, ...") — scripts get added/renamed
- Cron schedules — schedules change
- Ticker/watchlist details — tickers change
- Any format that requires updating when the repo's content changes

**Real-world failure (2026-05-31):** `stock-analysis-toolkit` README listed 5 script names
(`orbit_v2.py`, `ai_stock_rating.py`, `macro_strategy.py`, ...) that did not match the
actual repo contents at all — the real scripts had been renamed and moved into `scripts/`.
The README was permanently out of sync. Fix: replaced with a general description and
a pointer to `hermes-wiki` for the actual script list.

**Rule of thumb:** If the README describes files/folders whose names change, it WILL
go stale. Keep it at directory-level description only.

**DO put in README:**
- One-line purpose statement
- Layout overview (which directories exist, not which files)
- Getting started (clone command, dependency install)
- Pointer to `index.md` for actual content
- Links to related repos

**Rule of thumb:** If a future change in the repo would force a README edit, don't put it there. Use `index.md` or wiki pages instead.

### 2. Only Non-Obvious Knowledge

Karpathy's LLM wiki principle: **store only what's hard to rediscover.**

**Remove from wikis:**
- ❌ CLI basics (`cd`, `ls`, `pwd`, `grep`, `find`) — anyone can `man` or Google
- ❌ Git basics (`git clone/add/commit/push/pull`) — same
- ❌ Install guides (Claude Code setup, Codex setup) — official docs are more current
- ❌ Course/lecture orientations — if you took the course, you don't need this
- ❌ Tool comparisons that just repeat official docs

**Keep in wikis:**
- ✅ Mental models and concepts (e.g. "developer role shift", "harness engineering defined")
- ✅ Patterns and anti-patterns (e.g. "context rot", "diff traps")
- ✅ Architecture decisions (e.g. "why per-thread repos, not subdirectories")
- ✅ Workflows with hard-won lessons (e.g. "EPIC workflow", "branch review PR")
- ✅ Edge cases and pitfalls discovered through use

### 3. INDEX.md Must Match Reality

Every page listed in `index.md` must actually exist. No stubs, no "planned pages", no dead links.

**Check:**
```bash
cd ~/.hermes/<wiki>
# Find all .md files
find . -name '*.md' -not -path '*/.git/*' | sort > /tmp/actual_files.txt
# Extract all links from index.md
grep -oP '(?<=\()[^)]+\.md' index.md | sort > /tmp/index_links.txt
# Compare
diff /tmp/index_links.txt /tmp/actual_files.txt
```

If `diff` shows files in `index_links.txt` that aren't in `actual_files.txt`, those are dead links — remove them from index.md or create the files.

### 4. Consolidate, Don't Duplicate

When multiple repos cover the same domain, **consolidate into one** instead of maintaining parallel sources.

**Signs of duplication:**
- Two repos with "harness-engineering" in the name
- Part-based + topic-based structure for the same content
- One repo's content is a subset of another's
- User says "하나의 레포로 통합" or "merge into one"

**Workflow — Merging Two Overlapping Repos (A → B):**

1. **Survey both** — map every `.md` file in each repo. Decide which repo (B) becomes the target and which (A) gets archived.
2. **Identify overlap** — flag files in A that cover the same topic as existing files in B.
3. **Extract unique content from A** — copy files in A that have NO equivalent in B. Use `cp` into the appropriate directories of B.
4. **Prune BOTH before consolidating** — remove basic/beginner content from A's files BEFORE copying them in. Also audit B's existing content for the same patterns. The merged repo should be SMALLER than either original alone.
5. **Update B's index.md** — add new pages from A to the catalog. Remove dead links that pointed to now-deleted basic content.
6. **Update B's AGENTS.md** — reflect new directories or schema changes.
7. **Push B** — `git add -A && git commit -m "merge: consolidate [domain] from [repo-A]" && git push`
8. **Mark A as merged** — update A's README to point to B: "This repo is merged into [B]. See [B-link] for active content."
9. **(Optional) Delete A** if the user confirms.

10. **Check cron prompts for stale paths** — After migration, verify ALL cron jobs that reference the old repo:
    ```bash
    cronjob action=list  # list all jobs
    # For each job, check if the prompt_preview contains old path
    ```
    If any cron prompt still references the old repo path (e.g. `~/trading-agents-nuri/` when the target is `~/trade-pipeline/`), update it:
    ```bash
    cronjob action=update job_id=<ID> prompt="<updated prompt with new path>"
    ```
    
    **Common cron types to check:**
    - Skill-based crons (using `skills: [...]`): the prompt's terminal commands may still reference old paths even if the skill content is updated
    - LLM prompt crons: check the `cd ~/...` prefix in every terminal command
    - no_agent script crons: verify the `script:` path resolves to the target repo
    
    **Real failure (2026-06-07):** After migrating `trading-agents-nuri` → `trade-pipeline`, the 08:10 portfolio cron prompt still ran `cd ~/trading-agents-nuri && python3 src/analyst_target_collector.py`. The old directory had been deleted. Next day's cron would have failed. The 18:00 US briefing cron had already been updated, but 08:10 was missed — always check ALL jobs, not just one.

11. **Update skill scripts referencing old paths** — If any skill (loaded by cron jobs via `skills: [...]`) contains shell scripts or reference files with old repo paths, patch them:
    ```bash
    skill_view(name="<skill-name>", file_path="scripts/<script>.sh")
    # Fix if needed
    skill_manage(action="write_file", name="<skill-name>", file_path="scripts/<script>.sh", file_content="<updated content>")
    ```
    **Real failure (2026-06-07):** `fair-value-portfolio` skill's `collect_and_validate_targets.sh` referenced `/home/ubuntu/.hermes/scripts/` symlinks that were deleted during migration. Script would fail with `No such file or directory`.

12. **Verify the migration end-to-end** — Run the pipeline once to confirm everything works:
    ```bash
    cd ~/<target-repo> && python3 langgraph/pipeline.py --phase 0
    ls -la data/*.txt data/*.json
    ```
    
    **Key check points:**
    - `cd` commands resolve to the target repo, not the old one
    - Python scripts are at the expected relative paths
    - Data files are being written to the correct location
    - Import paths resolve correctly (especially `sys.path.insert` or `os.path.dirname` chains in submodule-style dirs)

13. **Update top-level repo README** — After merging everything into the target repo, update its README to document the consolidation:
    ```markdown
    ## 레포지토리 통합 현황
    
    `<target-repo>`이 유일한 활성 레포입니다. 모든 구 레포는 GitHub에서 ARCHIVED 처리되었습니다.
    
    | 구 레포 | 상태 | 현재 위치 |
    |:--------|:----:|:---------|
    | `repo-a` | ARCHIVED | `path/in/target/` |
    | `repo-b` | ARCHIVED | `other/path/` |
    ```

**Real example (2026-05-31):**
Two harness engineering wikis existed: `harness-engineering-wiki` (topic-organized) and `fastcampus-harness-engineering-wiki` (part-based). Combined: 40+ files. After consolidation: **24 files**, 7 new from fastcampus, 8 basic files removed. Smaller and more valuable than either alone.

See `references/repo-merging-workflow.md` for the full worked example.

**Move valuable unique content, then archive the duplicate.**
See `references/external-content-import.md` for the import conversion recipe — always add a PRUNING step: after merging, remove basic/beginner content from the unified repo. The merged result should be SMALLER than the sum of the parts.

**Pitfall — assuming remote state matches local perception.**

Before starting a merge, always `git pull` and check the latest commit message first:
```bash
git log --oneline -1
# If the latest commit says "cleanup" or "prune", someone already did work you're about to redo
```
**Real example (2026-05-31):** When merging `fastcampus-harness-engineering-wiki` into
`harness-engineering-wiki`, I assumed part1/ had 6 files (including install guides).
In reality, someone had already pushed a "cleanup: remove 10 basic/redundant pages"
commit. The remote had fewer files than expected. Always `git clone` or `git pull --dry-run`
first to discover the current state before planning the merge.

**Another pitfall — repo may have been deleted.** After a merge, when trying to update
the source repo's README to say "merged into X", the repo may 404 (already deleted).
Check existence with `GET /repos/<owner>/<name>` before attempting an update.

**When a repo is deleted, update wiki references in 9+ files.**

**Full checklist for repo deletion cleanup:**

1. **hermes-wiki submodule removal** — `git submodule deinit -f <path> && git rm -f <path>` + commit + push
2. **hermes-wiki-super submodule removal** — GitHub API tree surgery (see "Removing dead submodules from hermes-wiki-super" section above)
3. **Wiki file updates** (typically 9 files):
   - `code/scripts.md` — script descriptions pointing to old repo
   - `index.md` — submodule paths + repo map table (2–3 references)
   - `AGENTS.md` — directory structure diagram
   - `README.md` — submodule table
   - `infra/gh-token.md` — active repos list
   - `infra/obsidian-github-sync.md` — super repo submodule table
   - `infra/environment.md` — active repos line
   - plus any other files referencing the repo by name
4. **README in main project repo** — update archived/deleted status
5. **Memory update** — remove any references to deleted repo

Real example (2026-06-06): `stock-analysis-toolkit` deletion required 9 wiki file patches + 1 submodule removal + 2 super repo API calls + 1 README update + git-credentials token verification.

### Layer 2 — Shared Wiki (INDEX repo)
Cloned to `~/.hermes/wiki/`. Always loaded in every session. Contains:
- `AGENTS.md` — schema + routing rules (MANDATORY)
- `SCHEMA.md` — 🆕 공식 스키마 (tag taxonomy, page types, page thresholds, lint rules)
- `index.md` — master catalog with thread repo table
- `raw/` — 🆕 불변 원본 소스 저장소 (research 전용)
- `research/entities/` — 🆕 단일 주체 typed pages
- `research/concepts/` — 🆕 추상 개념 typed pages
- `research/comparisons/` — 🆕 비교 분석 typed pages
- `analysis/` — methodologies (valuation, macro, rating frameworks)
- `infra/` — server config, cron jobs, credentials REFERENCE only
- `watchlist/` — tickers, portfolio metadata
- `code/` — script documentation (scripts live on server)
- `people/` — user profiles
- `architecture/` — 시스템 설계 문서
- `solopreneur/` — 프리랜싱 전략
- `repos/` — 저장소 문서

### Layer 3 — Thread Wikis (per-context repos)
Each Discord thread gets its OWN GitHub repo. Cloned to `~/.hermes/thread-wikis/<name>/`.

**CRITICAL RULE:** Always use separate repos, NEVER subdirectories in the shared wiki.
A subdirectory approach fails because the agent has no way to discover or route to it
— a separate repo at its own path is loadable via AGENTS.md + memory.

Each thread repo has:
- `index.md` — thread-specific knowledge (this thread's purpose, cron jobs, key data)
- References to the shared wiki as "상위 위키" (parent wiki)

### Layer 4 — Logs
`mybotagent/hermes-logs` — timestamped markdown files (`YYYY/YYYY-MM-DD-HHMM.md`)
for all significant changes. Append-only. Never edit past entries.

### Layer 5 — Schema (AGENTS.md)
The shared wiki's `AGENTS.md` is the source of truth for routing rules.
Updated whenever a new thread or pattern is added.

## Thread Routing Rules

### Session Start — Auto-load Order

1. **Read memory** — find `This Discord thread (...)` entry, extract thread ID
2. **Load shared wiki** — `~/.hermes/wiki/` (always)
3. **Determine thread repo** — map thread ID → repo name via AGENTS.md table
4. **Load thread wiki** — `~/.hermes/thread-wikis/<name>/index.md`
5. **Combine knowledge** — shared + thread-specific used together
6. **Cron jobs** (no thread context) → shared wiki only, no thread wiki needed

### Thread ↔ Repo Mapping Table

Maintained in the shared wiki's `AGENTS.md` and `index.md`:

```markdown
| 스레드 | GitHub Repo | 로컬 경로 |
|:------|:-----------|:---------|
| `#project-manage / Hermes 일정관리` (thread:1510416479932121220) | mybotagent/hermes-wiki-schedule | ~/.hermes/thread-wikis/hermes-wiki-schedule/ |
| `#주식-증시 / Hermes` (thread:1510404235915694170) | mybotagent/hermes-wiki-portfolio | ~/.hermes/thread-wikis/hermes-wiki-portfolio/ |
| 크론 작업 (스레드 없음) | shared wiki only | ~/.hermes/wiki/ |
```

### Memory Integration

Store the routing rule as a compact memory entry:

```
Thread routing: wiki/AGENTS.md maps thread ID→별도 GitHub repo.
현재 스레드(#주식-증시) → mybotagent/hermes-wiki-portfolio → ~/.hermes/thread-wikis/hermes-wiki-portfolio/
일정관리 스레드(1510416479932121220) → hermes-wiki-schedule.
크론 → shared wiki만 사용.
```

## Setting Up a New Thread

### Step 1: Create the GitHub repo
```bash
curl -s -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{"name":"hermes-wiki-<thread-name>","description":"<thread description>","private":true}'
```

### Step 2: Clone locally and seed
```bash
mkdir -p ~/.hermes/thread-wikis
cd ~/.hermes/thread-wikis
git clone https://github.com/mybotagent/hermes-wiki-<thread-name>.git
```

### Step 3: Create thread index.md
Each thread repo needs an `index.md` with:

```markdown
# 🏷️ <Thread Name> Thread Wiki

> **스레드**: <Discord channel/thread name>
> **스레드 ID**: `<thread_id>`
> **목적**: <what this thread is for>
> **상위 위키**: [mybotagent/hermes-wiki](https://github.com/mybotagent/hermes-wiki)

## Core Knowledge
<thread-specific knowledge>

## Rules
1. <thread-specific conventions>
2. 변경사항은 mybotagent/hermes-logs에 기록
```

### Step 4: Push
```bash
cd ~/.hermes/thread-wikis/hermes-wiki-<thread-name>
git add -A && git commit -m "init: <thread-name> thread wiki"
# ⚠️ 'git init' creates 'master' branch, but GitHub default is 'main'
# If push fails with "src refspec main does not match any":
git branch -m master main   # if needed
git push -u origin main
```

### Step 5: Update AGENTS.md in shared wiki
Add the new thread to the routing table. Update both `AGENTS.md` (Five Layers section)
and `index.md` (Thread Wikis table).

### Step 6: Update memory
Store the routing entry with `memory(action='add', ...)`.

## Cleaning Up Thread Repos

### When a thread is no longer active:

1. **Update AGENTS.md** — remove from routing table
2. **Update index.md** — remove from thread wiki table
3. **Update memory** — remove routing entry
4. **Archive the repo** on GitHub (Settings → Danger Zone → Archive)
5. **Delete local clone**: `rm -rf ~/.hermes/thread-wikis/hermes-wiki-<name>`
6. **Log the change** in `hermes-logs`

## Repo Cleanup Patterns

### Identifying stale repos
```python
for name in repos_to_check:
    req = urllib.request.Request(f'https://api.github.com/repos/mybotagent/{name}')
    req.add_header('Authorization', f'token {token}')
    resp = urllib.request.urlopen(req)
    r = json.loads(resp.read())
    print(f"{'ARCHIVED' if r['archived'] else 'ACTIVE'} {name}")
```

### Before deleting repos: verify they're actually redundant

When a user mentions deleting a repo, check ALL of these first:
1. **Is the repo related to the consolidation target?** If no, it's a separate wiki/research repo — leave it.
2. **Does the repo serve a unique purpose?** Check description + all files in root via GitHub API.
3. **Has the content been migrated?** Search for the repo's content in target repos.
4. **Is the repo referenced in hermes-wiki submodules?** Check `.gitmodules`.
5. **Check memory for thread routing rules** — thread wiki removal breaks routing.

Real example (2026-06-06): User asked to check `hermes-wiki-portfolio` and `subagents-library`. Both were independent wiki repos with unique investment methodology content and sub-agent research catalog — no overlap with `stock-analysis-toolkit`. Result: keep both.

### Removing dead submodules from hermes-wiki (local)

**Always check BOTH hermes-wiki AND hermes-wiki-super** — a submodule is usually registered in both.

```bash
cd ~/.hermes/wiki
git submodule deinit -f path/to/submodule
git rm -f path/to/submodule
rm -rf .git/modules/path/to/submodule
git commit -m "cleanup: remove stale submodule"
git push origin main
```

### Removing dead submodules from hermes-wiki-super (GitHub API)

The super repo is typically cloned on the user's Mac (`~/Documents/Obsidian Vault/hermes-wiki-super/`), not on the server. When a submodule is deleted from `hermes-wiki`, it also needs removal from `hermes-wiki-super`. Use the GitHub API:

1. **Update `.gitmodules`** — fetch current content via API, remove the submodule block, PUT updated content.
2. **Create new Git tree** — fetch the repo's tree, remove the submodule entry, create a new tree.
3. **Create commit** pointing to the new tree.
4. **Update branch ref** to the new commit.

```python
# Simplified API workflow:
token = get_github_token()
headers = {"Authorization": f"token {token}"}

# Get latest commit SHA
ref = requests.get(f"{API}/git/ref/heads/main", headers=headers).json()
latest = ref['object']['sha']

# Get full tree
tree = requests.get(f"{API}/git/trees/{latest}?recursive=1", headers=headers).json()

# Build new tree WITHOUT the submodule
new_tree = [t for t in tree['tree'] if t['path'] != 'code/stock-analysis-toolkit']  # example

# Create new tree
new_tree_resp = requests.post(f"{API}/git/trees", headers=headers, json={
    "base_tree": latest, "tree": new_tree
}).json()

# Create commit
commit = requests.post(f"{API}/git/commits", headers=headers, json={
    "message": "cleanup: remove dead submodule",
    "tree": new_tree_resp['sha'],
    "parents": [latest]
}).json()

# Update branch
requests.patch(f"{API}/git/refs/heads/main", headers=headers, json={
    "sha": commit['sha']
})
```

**Note:** Submodules show as `type: "commit"` in the tree. The `.gitmodules` file is a regular file — update both independently.

**Pitfall — fine-grained token scope.** The API approach requires token with `repo` scope. If the token can read but not write, guide the user to their Mac to run the cleanup locally:
```bash
cd ~/Documents/Obsidian\ Vault/hermes-wiki-super
git submodule deinit -f code/stock-analysis-toolkit
git rm -f code/stock-analysis-toolkit
git commit -m "cleanup: remove stale submodule"
git push origin main
```

**Real example (2026-06-06):** `stock-analysis-toolkit` repo was deleted. Required:
1. `.gitmodules` update via API (1 endpoint)
2. Submodule entry removal via tree API (3 endpoints: get-tree → create-tree → create-commit → update-ref)
3. Plus 9 hermes-wiki file updates + submodule removal there

### Token limitations
GitHub tokens with `repo` scope CANNOT delete repos. Deleting requires `delete_repo`
scope. If the user's token lacks it, guide them to:
1. Visit `https://github.com/mybotagent/<repo>/settings`
2. Danger Zone → Delete this repository
3. Type repo name to confirm

### Fine-grained token quirk
`ghp_` tokens with `repo` scope **can create repos and access known repos by URL**,
but the **`/users/<name>/repos` list endpoint may return empty** due to fine-grained
token restrictions. Always use per-repo `GET /repos/<owner>/<name>` to check
existence rather than relying on the list API.

### 🆕 gh CLI auth without `gh auth login` — credential env-var pattern (2026-07-03)

When `gh auth status` reports "not logged in" but `~/.git-credentials` has a
`https://<user>:<token>@github.com` line, drive `gh` directly:

```bash
export GH_TOKEN=$(head -1 ~/.git-credentials \
  | sed 's|https://||;s|@github.com.*||' \
  | cut -d: -f2-)
export GH_HOST=github.com
gh auth status   # → Logged in to github.com account <user> (GH_TOKEN)
gh repo create mybotagent/<name> --private --description '...' --add-readme
gh api repos/mybotagent/<name>/contents/<path> --jq '.[] | {name, size}'
```

**Why:** `gh auth login` is interactive (browser OAuth) — useless in headless/cron.
`gh` auto-detects `GH_TOKEN` + `GH_HOST`. Covers `gh repo create`, `gh api`,
`gh release create` — full GitHub API surface without re-auth.

**Scope limits (still applies):**
- `repo` scope: ✅ create, push, read contents, releases
- ❌ `delete_repo` needed for `gh repo delete` — force-push empty content instead

**Validate step (post-push, 2026-07-03 newsletter-wiki 1호 패턴):**
```bash
gh api repos/mybotagent/<repo>/contents/<path> --jq '.[] | {name, path, size}'
```
Returned `size` (bytes) = ground-truth verification that `git push` succeeded
and the file exists on remote. **Anonymous `curl raw.githubusercontent.com/...`
returns 404 for private repos** — don't use it for validation; use `gh api` with token.

### 🆕 subagent timeout fallback — direct-execution re-routing (2026-07-03)

When `delegate_task(goal=..., role='leaf')` times out at 600s with `api_calls=50+`,
the subagent may have produced partial work in `/tmp/` or sandbox dirs. Recovery:

1. **Probe for partial work first** (cheap, ~1s):
   ```bash
   find /tmp -maxdepth 4 -type f \( -name '*.md' -o -name '*<topic>*' \) | head -20
   ```
2. **If partial file exists** → read it, integrate into final output, document the
   gap in the report. Don't restart the subagent — same calls likely time out again.
3. **If no partial work** → execute the same plan **directly** in the main session
   using `terminal` + `curl`/`web_extract`. Trade: more context consumed, but
   bounded time (no API call loop trap).

**Trigger pattern:** when the dispatched task is **browsing + summarizing many URLs**,
subagents frequently exceed 600s on slow sites. Direct execution with parallel
`curl --max-time 12` calls is usually faster than waiting for subagent retry.

**Anti-pattern:** re-dispatching the same subagent goal after timeout — almost
always hits the same 600s ceiling. Either change the prompt (narrower scope)
or switch to direct mode.

### 🆕 5-stage verify — validate stage = GitHub API bytes check (2026-07-03)

5-stage verify (why→what→whether→what→how→**validate**) is incomplete without
a real-side-effect check. For GitHub pushes:

```bash
# After git push, ALWAYS:
gh api repos/mybotagent/<repo>/contents/<path> --jq '.[] | {name, path, size}'
# Compare returned size (bytes) with local file size
ls -la <local-file>
```

**If sizes differ:** `git push` was incomplete (network blip, repo reject). Retry
push. **If API returns empty/null:** path doesn't exist on remote — push failed
silently. Re-run `git push origin main`.

This is stronger than `git ls-remote origin main` (which only confirms ref
update, not file content) and stronger than `curl raw.githubusercontent.com`
(404 on private repos). Only `gh api` with token + contents endpoint gives
real bytes-level confirmation.

**Compound with subagent work:** when subagent runs autonomous, use 5-stage verify
in the *parent* session after subagent returns — don't trust subagent's
self-reported "success" without re-verification.

### 🆕 Newsletter publishing pattern → reference `newsletter-publishing` skill

The user's "매일 1호 뉴스레터 → 새 GitHub 레포에 push" workflow is a **distinct
pattern** from wiki-save (which archives *given* text). Newsletter publishing
requires: external trend research → typed Issue page → raw source preservation
→ cadence/thesis stacking → gh repo creation. See the dedicated
`newsletter-publishing` skill for the full workflow.

The two skills live side-by-side:
- `wiki-save` = **archival** (text in → page out) for personal knowledge
- `newsletter-publishing` = **publishing** (research out → Issue + raw + cadence) for audience-facing content

## Logging Pattern

All significant changes must be logged to `mybotagent/hermes-logs`:

```bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
cd ~/.hermes/log-repo
cat > "2026/$TIMESTAMP.md" << LOGEOF
# [$(date '+%Y-%m-%d %H:%M')] Short Title

## Summary
What changed and why.

## Changes
- Bulleted list of specific changes
LOGEOF
git add -A && git commit -m "log: short description"
git pull --rebase origin master && git push
```

## Submodule Maintenance

See `references/submodule-maintenance.md` for:
- Repairing broken submodules (empty checkout, inaccessible remote)
- Detached HEAD in submodules — pushing to non-default branches (`master` vs `main`)
- Branch mismatch between submodule remote and local expectation

## Daily Sync Cron (04:00 KST)

The daily wiki sync cron runs at 04:00 KST. It pulls all three wiki repos (hermes-wiki,
hermes-wiki-claude-code, hermes-wiki-codex), checks for remote changes, logs significant
updates to hermes-logs, and commits the updated submodule pointer.

**Key fact:** Even when `git status --short` shows nothing, `git pull --ff-only` can
reveal significant remote work (file deletions, restructuring). Always pull.

**The logs submodule uses `master`, not `main`.** After committing inside the submodule,
push with `git push origin HEAD:master`.

See `references/daily-sync-cron.md` for the full step-by-step workflow, commands, and
all known pitfalls.

## Common Pitfalls

0. **Creating repos before clarifying ambiguous requests — user frustration risk.**

   **This is the most expensive mistake you can make in a wiki session.** Creating
   wrong repos means undoing submodules, reverting index.md, emptying GitHub repos,
   cleaning memory, and the user having to clean up remnants themselves. The user
   will say things like:
   - "아니 X는 내가 지울게" (No, I'll delete it myself — means YOU wasted their time)
   - "방금 한 건 지워줬으면 좋겠어" (I want what you just did deleted)
   - "그거 말고" (Not that)
   
   These are not mild corrections — they mean you misunderstood the task completely
   and created artifacts that need to be torn down. **Never assume. Always clarify.**
   
   When the user says something like "stars 많은 agents library도 리서치해서 정리해줘" —
   "agents" could mean agent frameworks (LangChain, AutoGen), or sub-agents
   (task-specific delegate agents within Claude Code), or agent-running infrastructure.
   Don't guess. Ask ONE clarifying question before touching anything:
   
   ```bash
   # Good: "Do you mean agent frameworks (LangChain, AutoGen) or sub-agents 
   #        (delegate agents within Claude Code)?"
   # Bad: Creating two repos based on guesses (wastes ~30min of cleanup)
   ```
   
   **Real-world failure (2026-05-31):** User (aiprofit) asked for "agents library."
   I created `agents-library` with 42 agent frameworks. User: "내말은 서브에이전트
   말하는거야." I created `subagents-library` with sub-agent collections. User:
   "서브에이전트 말고 방금 이야기한 기존내용은 지워줬으면 좋겠어" — neither was
   wanted. Had to delete both repos, remove submodules from hermes-wiki, revert
   index.md, and clean up memory. Total wasted effort: **~45 minutes of work +
   user frustration.**
   
   Then on the third try (subagents-library again), I finally got it right — user
   confirmed: "subagents-library에 사람들이 가장 많이 사용하고 best practice한
   subagent관련으로 리서치해서 저장해줘." If I had asked "Is that sub-agents or
   agent frameworks?" at the start, all the cleanup and frustration would have been
   avoided.
   
   **The fix is simple:** one clarifying question. "A minute of clarifying saves
   30 minutes of cleanup" is not an exaggeration — it's a measured ratio from
   actual cleanup sessions.

0.5 **Recovery pattern: when you create repos the user didn't want.**

   If you've already created repos the user rejects:
   
   1. **Clean up hermes-wiki submodules first:**
      ```bash
      cd ~/.hermes/wiki
      git rm <submodule-path>
      git commit -m "cleanup: remove <name> submodule"
      git push origin main
      ```
   2. **Revert index.md additions** — remove any Quick Reference entries
   3. **Empty the GitHub repos** (if token can't delete them):
      ```bash
      mkdir /tmp/scrub && cd /tmp/scrub
      git init --initial-branch=main
      echo "# <repo> - Removed" > README.md
      git add README.md && git commit -m "cleanup"
      git remote add origin https://github.com/mybotagent/<repo>.git
      git push -f origin main
      rm -rf /tmp/scrub
      ```
      Note: `ghp_` tokens with `repo` scope CAN create repos but CANNOT delete them
      (need `delete_repo` scope). Force-pushing empty content is the best workaround
      without user intervention.
   4. **Delete local clones:** `rm -rf ~/.hermes/<repo>`
   5. **Update memory** — remove entries referencing deleted repos

   See `references/repo-deletion-recovery.md` for the full step-by-step workflow with examples.

1. **Subdirectories instead of separate repos.** The agent has no mechanism to route
   to wiki subdirectories per thread. Separate repos at `~/.hermes/thread-wikis/<name>/`
   with explicit AGENTS.md routing rules are the only reliable approach.

   **Real-world story from 2026-05-31 session:** The agent first created `threads/` subdirectories
   inside the shared wiki. The user rejected this immediately: _"아니..쓰레드별로 리포를 다르게
   가져가고 싶은데?"_ The agent had to undo all the subdirectory work, create separate GitHub repos,
   write new AGENTS.md routing rules, and clean up the stale `threads/` dir. The user's point was
   correct — subdirectories lack a discovery mechanism; only separate repos at known local paths
   with explicit routing rules in AGENTS.md + memory actually work. **If you're considering a
   subdirectory approach, stop — the user has already rejected it.**

2. **Creating repos without routing rules.** A per-thread repo with no AGENTS.md entry
   and no memory entry is a dead repo — the agent won't know it exists. Always update
   all three: AGENTS.md + index.md + memory.

3. **Forgetting to clone the thread repo.** AGENTS.md can point to a repo that doesn't
   exist locally. After creating the GitHub repo, always clone it immediately.

4. **Branch name mismatch.** GitHub defaults to `main` branch. If the local clone has
   `master`, rename: `git branch -m master main` before pushing.

5. **Accidental force push.** Use `git pull --rebase && git push`, never `git push -f`
   unless explicitly handling branch name mismatch and user confirms.

6. **Memory growing stale with dead repo references.** Weekly cleanup cron should
   verify memory entries match actual repos.

8. **Logging only in wiki.** Logs belong in `hermes-logs` repo, NOT in the shared wiki.
   The shared wiki's `AGENTS.md` mentions it — no `log.md` file in the shared wiki.

8.5 **Memory tool unavailable in cron context.** Cron jobs cannot call `memory()` — the tool is not loaded in background/cron sessions. Any maintenance step that reads or writes memory (e.g. "clean stale memory entries after repo deletion", "verify memory matches actual repos") must be deferred to a user-facing session or handled by different means. The cron environment has access to `terminal`, `file` tools, and `git` — use those for cleanup and log what couldn't be done. See `references/submodule-maintenance.md` for submodule repair workflows that work fully in cron.

8. **Skipping the pruning step in external imports.** Converting a course repo to a wiki by topic inevitably pulls in basic content (install guides, CLI basics, orientation overviews). These accumulate and make the wiki feel noisy. Always run a pruning pass: "Would I Google this? If yes, delete it." See `references/external-content-import.md` Step 5 for the checklist and `references/repo-merging-workflow.md` Step 4 for the repo-merging variant.

## Verification Checklist

- [ ] The wiki-save skill (`wiki-save`) is the operational tool that implements this architecture — load it when the user says "저장" or "/wiki-save" to ingest content into the correct repo via the 2-layer pattern.
- [ ] **SCHEMA.md** exists and is up to date with tag taxonomy, page types, thresholds, and lint rules
- [ ] **raw/** directory exists with `.gitkeep` (research source preservation)
- [ ] **research/entities/**, **research/concepts/**, **research/comparisons/** exist with `.gitkeep`
- [ ] AGENTS.md has the routing table with all active threads
- [ ] index.md has the Thread Wikis table matching AGENTS.md
- [ ] Each thread repo exists at `~/.hermes/thread-wikis/<name>/`
- [ ] Each thread repo has an `index.md` with content
- [ ] Memory has a routing entry for thread→repo mapping
- [ ] No stale repos in `~/.hermes/thread-wikis/` that are no longer active
- [ ] No dead submodule references in `~/.hermes/wiki/.gitmodules`
- [ ] `~/.hermes/wiki/` has no `log.md` (logs are in `hermes-logs`)
- [ ] Recent changes logged to `hermes-logs` in timestamped format

## Importing External Content

When the user provides a link to a structured course repo or documentation site,
see `references/external-content-import.md` for the full conversion recipe:
clone → survey → restructure by topic → write AGENTS.md + index.md → push.

## 🆕 Research/ Seeding — typed pages 0건 → 3건 (2026-07-07 실전)

idle-time 자율 hygiene로 `research/{entities,concepts,comparisons}` 빈 디렉토리에 typed 페이지 시드할 때의 검증된 절차. raw → typed → INDEX.md → SCHEMA.md 8종 lint → git push까지 8단계 + 7 Pitfall. See `references/wiki-research-seeding.md`.

### Variant: Catalog-Type Wikis (Third-Party Resource Lists)

When the user asks to create a repo cataloging **external resources** (not importing
them) — e.g., a "claude skill library" or "awesome-*" style curated list.

**Difference from course import:**
- Course import: restructures source files by topic
- Catalog: researches and organizes external resources by popularity/category

**Workflow:**

1. **Research via GitHub API** — search by topic, sort by stars:
   ```bash
   curl -s "https://api.github.com/search/repositories?q=topic:claude-code+skill&sort=stars&per_page=30"
   ```
2. **Verify each repo** — use `GET /repos/<owner>/<name>` to confirm existence and get exact star count.
   NOT the user list endpoint (`GET /users/<name>/repos`) — fine-grained tokens often return empty lists.
3. **Organize by category** — group by use case (planning, testing, devops, design, finance, SEO, etc.)
4. **Use GitHub stars as quality signal** — only include repos with significant adoption (500+ ⭐ default).
5. **Include install instructions per source** — skills.sh CLI, GitHub direct, npm, etc.
6. **Add security notes** — each source type has different trust levels.
7. **Create as standalone private repo**, then add as submodule to `hermes-wiki`.

**Optional: ecosystem map.** For catalog wikis with multiple related categories, an
ASCII ecosystem map helps readers understand relationships:
```
         Agent CLI Tools
               │
          ┌────┴────┐
          │         │
 Agent Frameworks   Multi-Agent
          │
     ┌────┴──────┐
     │           │
 Agent UI/SDK  Infrastructure
```

**Pattern for submodule registration (after creating catalog repo):**
```bash
cd ~/.hermes/wiki
git submodule add https://github.com/mybotagent/<new-repo>.git <submodule-path>
git add .gitmodules <submodule-path>
git commit -m "feat: add <new-repo> as submodule"
git push origin main
```
Then update `hermes-wiki/index.md` quick reference table with the new entry.
**Star verification quirk — fine-grained tokens.** `ghp_` tokens with `repo` scope
> ⚠️ Earlier attempts at catalog wikis (`claude-skill-library`, `agents-library`) were rejected by the user and deleted. Always clarify the domain (skills vs agents vs sub-agents) before creating.

**Star verification quirk — fine-grained tokens.** `ghp_` tokens with `repo` scope
can create repos and access known repos by URL, but `GET /users/<name>/repos` may
return empty for fine-grained tokens. Always verify individual repos via
`GET /repos/<owner>/<name>` — never rely on the user's repo list endpoint.

**When to use per-repo API vs search API:**
- `GET /search/repositories?q=<name>+in:name` — find a repo by name, may miss or
  rank duplicates. Use for discovery (finding the top repo by stars).
- `GET /repos/<owner>/<name>` — verify a known repo. Guaranteed accuracy.
- `GET /repos/<owner>/<name>/contents/<path>` — read file contents from a known repo.
  Add `?ref=main` to avoid branch confusion.
- `GET /users/<name>/repos` — DO NOT USE with fine-grained tokens (returns empty).

**Star verification quirk — fine-grained tokens.** `ghp_` tokens with `repo` scope
Wiki content drifts over time. Run this scan every few weeks or when the user asks
to "check for outdated info". Full session recipe in
`references/wiki-health-check-session.md`.

### 1. Stale Root-Level Duplicates

Files that exist at both `~/.hermes/wiki/` root AND in a subdirectory (`analysis/`,
`infra/`, `code/`, `watchlist/`) are duplicates — the root copy is stale. Remove it:

```bash
cd ~/.hermes/wiki
# Files that should only live in subdirectories:
for f in methodology.md orbit-valuation.md stock-rating-system.md \
         cron-jobs.md discord-gateway.md environment.md gh-token.md \
         scripts.md tickers.md; do
  [ -f "$f" ] && echo "STALE: $f (maybe duplicates infra/$f or analysis/$f)"
done
```

### 2. Verify Infra Paths Are Current

Check these frequently-stale fields in `infra/environment.md`:

| Check | What to verify |
|-------|---------------|
| `User:` | Must match actual server user (e.g. `ubuntu`) — often says `root` |
| `Python:` | Must match actual venv path — old Hermes installs used `/usr/local/...` |
| `Token:` | Must point to `~/.git-credentials`, never `/tmp/ghtoken` |
| Repo list | Must include all active repos, none deleted |

Also check `infra/gh-token.md` for the same stale-path pattern.

### 3. Check Cron-Jobs Match Reality

Compare `infra/cron-jobs.md` table with `cronjob(action='list')` output:

- Every job in the doc must have a matching `job_id` in the actual list
- Every actual job must appear in the doc (missing jobs = stale doc)
- Schedules must match (CST vs KST conversion verified)
- Deleted/replaced jobs removed from doc

### 4. Update User Profile Page

Check `people/<username>.md` against current memory/user profile:

- Name/honorific must match current preference (e.g. "꼬북아" vs old "채워니")
- Referenced repos must still exist
- Preferences section must reflect current setup (e.g. per-thread repos vs old flat wiki)

### 5. Purge Root-Level README Duplicate

The root `README.md` often duplicates `watchlist/README.md` content. If they're
identical, remove root `README.md` — `index.md` serves as the repo landing page.

### 6. Verify Submodule State

```bash
cd ~/.hermes/wiki && cat .gitmodules
```
Every submodule must:
- Point to an existing GitHub repo (not deleted/archived)
- Have a local checkout that can be updated
- Be referenced in index.md's submodules table

## Operational Tooling

The [wiki-save](../wiki-save/SKILL.md) skill is the **operational implementation** of this architecture. It:
- Implements the 2-layer classification (GitHub repo → LLM Wiki within repo)
- Handles new repo creation when no existing category matches
- Manages the full ingest pipeline: classify → save → INDEX.md → log → push

Load `wiki-save` when the user says "저장", "/wiki-save", or pastes text to be archived.
