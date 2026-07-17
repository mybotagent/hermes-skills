---
name: autonomous-system-hygiene
description: Autonomous end-of-session maintenance — Kanban dedup, skill usage audits, wiki/submodule hygiene, memory checks, false-positive verification, cron deliver fixes, drift gap measurement, hermes-config-sync mirror 운영. Class-level umbrella for "when there's nothing to do, find and fix what's broken" workflows. Trigger when user says "자율로 처리해", "알아서 수정해", "idle 작업", or when a session has run out of explicit user tasks.
version: 1.4.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [autonomous, hygiene, kanban, wiki, cron, audit, drift, gap, pr-review, hermes-config-sync, github-mirror]
    related_skills: [kanban-worker, self-healing-cron, cron-delivery-routing, wiki-save, execution-discipline, github-pr-workflow]
---

# Autonomous System Hygiene

> Use when the user hands over open-ended autonomy: "자율로 처리해", "알아서 해줘", "작업 없을 때 수정할 거 찾아서 해줘". This skill encodes the **patterns proven in a 4-round autonomous cleanup that closed all 38 Kanban ready tasks without any user prompt** — dedup, false-positive verification, skill usage audit, wiki submodule hygiene, memory measurement, design-execution gap measurement, cron deliver target fixes, **hermes-config-sync mirror 운영** (added 2026-07-09).

## When to fire this skill

- User says "자율 진행", "자율 주행", "알아서 해줘", "idle 작업", "작업 없을 때 알아서 수정"
- **🆕 2026-07-17**: User says "메모리 정리해", "불필요한 메모리 정리", "memory 해결해", "알아서 정리" — memory audit + wiki 마이그레이션 트리거
- Session has completed the user's last explicit ask and the user has signaled open-ended autonomy
- A `hermes kanban list` shows ≥5 ready tasks with similar titles or duplicate `created` timestamps
- **2026-07-09 추가**: "자율운영 안됨" 진단 / "원인 찾아서 알아서 해결" / "각각에대해서 설명" / "각 cron마다 자세히 문서화" / "왜 자꾸 빼먹지?" — hermes-config-sync 자가진단 패턴

**Do NOT fire when:**
- User just asked a specific question (answer first, don't preempt)
- A task is actively in progress
- The user said "stop" / "멈춰" / "그만"

## Multi-round autonomy — how rounds chain

When the user keeps saying "자율 진행" / "알아서 다음 자율 진행" across multiple rounds in one session, **don't reset — chain rounds**. The 2026-07-07 session ran 4 rounds in one session:

- **Round 1**: initial dedup + false-positive close (15 tasks, ready 38→23)
- **Round 2**: re-survey revealed more ready tasks — same loop continues (9 tasks, 23→13)
- **Round 3**: deep dive on remaining meaningful tasks — wiki typed-page seeding, lint script authoring (9 tasks, 13→5)
- **Round 4**: zero in on user-decision tasks that turned out to be mechanically completable (5 tasks, 5→0)

**Round format** (always write log per round):

```
~/mybotagent/hermes-logs/logs/YYYY/YYYY-MM-DD-HHMM-autonomous-cleanup-round-N.md
```

**Stop signal** (only these, never assumed):
- User says "stop" / "멈춰" / "그만" / "충분"
- Kanban ready hits 0 AND no more safe work (cron fine, wiki fresh, scripts up to date)
- A round reveals a hard blocker (e.g. user-decision required, no executable path)

**Don't ask permission between rounds.** Just chain. The user asked for autonomy — re-asking mid-loop defeats the whole purpose.

## The 5-step autonomous hygiene cycle

### Step 1 — Survey: what's the actual state?

Run these in parallel (single message, multiple `terminal` calls):

```bash
# 1a) Kanban ready state (the main source of dedup opportunities)
hermes kanban list 2>&1 | grep -E '^\▶ |^\? '

# 1b) Submodule / wiki state
cd ~/.hermes/wiki && git status --short 2>&1 | head -20

# 1c) Cron state — anything failing silently?
hermes cron list 2>&1 | grep -E 'silent|error|404|⏰' | head -10

# 1d) Memory fill — close to cap?
python3 ~/.hermes/scripts/memory_alert.py check 2>&1 || echo "memory_alert.py not yet installed"

# 1e) Recent skill usage (90-day window from state.db)
sqlite3 ~/.hermes/state.db "SELECT content FROM messages WHERE tool_name='skill_view' AND timestamp > strftime('%s','now','-90 days');" 2>&1 | grep -oE '"name":\s*"([a-z][a-z0-9_-]+)"' | sort | uniq -c | sort -rn | head -20

# 1f) Design-execution gap (after round 1, helps prioritize)
python3 ~/.hermes/scripts/design_exec_gap.py 2>&1 || echo "design_exec_gap.py not yet installed"

# 1g) Linear — is there active work in the user's project?
LINEAR_KEY=$(grep -i "^LINEAR_API_KEY" ~/.hermes/.env | cut -d= -f2)
curl -s -X POST https://api.linear.app/graphql -H "Authorization: $LINEAR_KEY" -H "Content-Type: application/json" \
  -d '{"query":"{ issues(filter: { state: { type: { in: [\"unstarted\", \"started\"] } } }, first: 20) { nodes { identifier title state { name } priority } } }"}' 2>&1 | head -10

# 1h) 🆕 hermes-config-sync 자가진단 (2026-07-09)
# 마지막 sync 시각 + DRY_RUN default + 4개 레포 drift
ls -t ~/.hermes/cron/output/hermes-config-sync-*.log | head -1 | xargs tail -10
grep "DRY_RUN=" ~/.hermes/scripts/hermes_config_sync.sh | head -3
TOK=$(grep ^GITHUB_TOKEN= ~/.hermes/.env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
for r in hermes-wiki hermes-skills hermes-scripts hermes-config; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOK" https://api.github.com/repos/mybotagent/$r)
  echo "$r: $code"
done
```

**Don't just glance at the top — read the patterns.** Multiple tasks with the same `created` timestamp + similar titles are auto-generated duplicates. Tasks with `last_run_at: null` and a far-future `next_run_at` are usually orchestrator false-positives. **🆕 17시간 무push 같은 silent fail**: cron log는 정상인데 GitHub 변화 0 → DRY-first 1순위 의심.

### Step 2 — Classify: dup / false-positive / genuine work?

For each `ready` task, apply this decision tree:

| Signal | Verdict | Action |
|---|---|---|
| Same `created` timestamp + ≥80% title overlap with another ready task | **Duplicate** | Close one with `--summary 'duplicate of <id>'` |
| Orchestrator auto-task + claim verifiable to be false (e.g. "README.md missing" but file exists) | **False-positive** | Verify the path, close the original, close the orchestrator's flag |
| Body says "검토", "평가", "확인" and the underlying state is already correct | **Already-done** | Close with `--metadata '{\"verified\":\"state at <date>\"}'` |
| Body says "DESIGN" / "합의" — check if a measurable script would replace it | **Upgradable** | Author the script + close as "DESIGN basis established" |
| Genuine task that fits within `autonomous_mode` boundaries (read-only audits, dedup, script authoring, cron registration, deliver target fixes) | **Safe autonomous** | Do it |
| Blast radius is large (delete data, push to public repo, change credentials) | **User decision** | Surface as a 1-line "잔여 N개" report, do NOT execute |
| 🆕 **cron log 정상 + GitHub 변화 0** | **DRY-first silent fail 의심** | grep `DRY_RUN=` 으로 즉시 확인. push-first로 rule 변경 (사용자 결정) |

### Shipped Step-4 candidates (added 2026-07-08)

다음 후보들은 **이미 shipped** — 자율 idle 시 다시 작업 ❌:

- **(2) wiki cleanup alert** — `wiki_auto_maintainer.py` (cron `c172635927c2`, 매주 토 03:30 KST) 가 주간 alert_only 로 가동 중
- **(4) cron health check** — `self_improve_loop.py` + `self-consistency-check-3h` (cron `da557233e6ac`) 에 통합 완료
- **🆕 disk hygiene 6축 watchdog (2026-07-08 shipped)** — `~/.hermes/scripts/hermes_disk_hygiene.py` + cron `0e095c406dae` (매일 KST 06:50, DRY-first, no_agent). df/state.db/snapshots/sessions/logs/tmp_pack 6축 측정, 80/90/95% 3-tier. **단방향 alert only** (state.db/snapshot/session 삭제 절대 자동 안 함). 설계 상세 → `references/disk-hygiene-design.md`
- **🆕 hermes-config-sync push-first rule (2026-07-09 shipped)** — DRY-first → push-first 영구 rule. 5개 sub-step (wiki/skills/scripts/config/memories) + 4개 레포 운영. **mirror stage .git wipe fix** (rsync `--exclude .git`) + **config step 무한 재귀 fix** (수동 cp). `references/hermes-config-sync-patterns.md` 참조.

→ `references/step-4-candidates.md` 는 outdated; 추가 shipped 항목은 본 섹션에 누적.

### Step 3 — Dedup pattern (proven pattern, 2026-07-07)

When 5+ duplicates exist, the **best close order** is:

1. **Sort by created timestamp ASC** — close the oldest first, keep the newest (the most recent typically has the most up-to-date body)
2. **Within the same timestamp, sort by ID DESC** — `t_zzz` is more recent than `t_yyy` if same timestamp
3. **One pass per duplicate pair** — don't try to dedup 4 tasks at once; pair them off

```bash
# Close t_xxxx (older) with reference to t_yyyy (newer, kept)
hermes kanban complete t_xxxx \
  --summary 'duplicate of t_yyyy (same created YYYY-MM-DD HH:MM, same body). de-duped; keeping t_yyyy'
```

**Why this format matters**: the summary becomes part of the audit trail. A future session scanning `runs:` history can see WHY a task was closed without re-running the diagnosis.

### Step 4 — Do genuine work, capped

Pick the **3 highest-value tasks** you can complete in ≤10 minutes each. Skip the rest (let them stay `ready`). Better to complete 3 cleanly than half-finish 8.

**Examples of safe autonomous tasks** (proven):
- Author a script under `~/.hermes/scripts/` (memory_alert.py, wiki_lint.py, compression_drift_check.py, design_exec_gap.py)
- Author Kanban review/decision documents under `~/mybotagent/hermes-logs/logs/YYYY/`
- Register a `no_agent` cron for a script you just wrote
- Update a wiki submodule's index.md (commit + push inside the submodule, then parent updates its submodule pointer)
- **Fix cron deliver target mismatches** (when content goes to wrong thread — see "Cron deliver fix" below)
- **🆕 DRY-first → push-first rule 변경** + mirror stage 버그 fix (rsync .git wipe, config 무한 재귀). user rule "github은 기록용" = push-first default.

**Examples of unsafe tasks** (defer to user):
- Uninstalling skills (silent action with no rollback)
- Pushing to public repos (allowed via `hermes_config_sync.sh` only — push-first rule 적용 후 정상 운영)
- Modifying Linear/SHO issues that are linked to user-visible threads
- Touching the user's calendar (use Google OAuth, not auto-edit)
- **🆕 GitHub repo delete/archive** (PAT admin scope 부족 + user rule상 force push ❌ → 사용자가 GitHub UI에서 직접)

### Step 5 — Report, then log

Tell the user in **≤5 lines** what was done. Format:

```
자율 라운드 N — Kanban N건 close + 산출물 X개 + cron Y개
| 처리 | … |
| 잔여 ready | N개 (사용자 결정 영역) |
```

Then append a log entry to `~/mybotagent/hermes-logs/logs/YYYY/YYYY-MM-DD-HHMM-<round>.md` so the next session can see what was done.

**🆕 항상 전부 보고 (2026-07-09 user frustration signal)**: 사용자가 "왜 자꾸 빼먹지? 너무 많아서 그런가?"로 명시. 자가진단/보고 시 일부 sub-step만 다루지 말고 **전체 mirror list** + **전체 cron list** + **전체 deliver format** 항상 1-page 요약. 빠뜨림 = 다음 세션의 또 다른 자가진단 트리거.

## Cron deliver target fix — exact recipe (2026-07-07 proven)

When `cron-delivery-routing` flags or your own survey catches a cron whose `Deliver:` doesn't match its content topic, you CAN fix the obvious ones autonomously. The pattern is:

```bash
# 1) Verify the current state — read the cron list output
hermes cron list 2>&1 | grep -B 1 -A 5 "<job_id>"

# 2) For OBVIOUS mismatches (e.g. portfolio cron → #일정 thread), update
cronjob action=update job_id=<id> deliver="discord:<channel_id>:<correct_thread_id>"

# 3) Verify the update landed
hermes cron list 2>&1 | grep -A 5 "<job_id>"
```

**Topic→thread mapping for aiprofit's setup** (canonical, hard-coded — single source of truth lives in `~/.hermes/wiki/infra/multi-bot-discord-routing.md` or similar):

| Topic | Thread ID | Channel ID |
|---|---|---|
| Stock/portfolio/macro/earnings | `1510404235915694170` (#주식-증시) | `1510397804139515945` |
| Calendar/schedule | `1520640537995247698` (#일정) | `1510397804139515945` |
| Survey/checklist | `1520255092413038732` | `1510397804139515945` |

**Don't fix `deliver=origin`** — that means it goes to the user's current session, which is intentional for ad-hoc prompts. Only fix explicit discord: targets that are clearly wrong.

**Don't auto-fix cron SKILL deliver** if it's `deliver=local` (silent save only).

## Skill usage measurement — exact recipe (2026-07-07 proven)

When you need to know "which skills are actually used vs sitting on disk", do NOT grep session content. The right place is `state.db` `messages` table, `tool_name='skill_view'`, with the skill name extracted from the JSON in the `content` column.

```bash
# 90-day usage frequency
sqlite3 ~/.hermes/state.db "SELECT content FROM messages WHERE tool_name='skill_view' AND timestamp > strftime('%s','now','-90 days');" 2>&1 | \
  grep -oE '"name"\s*:\s*"([a-z][a-z0-9_-]+)"' | sort | uniq -c | sort -rn
```

**Why the regex is `"name":\s*"..."`**: the `skill_view` tool result is JSON in the `content` column. The skill name is `name` field (not `description`, not `path`). The first `"name"` occurrence in the row is always the skill name. There can be MULTIPLE `"name"` matches if the skill body itself references other skills — so use `head -1` of each row's match, not the count.

**Cron-only skills (separate signal)**:

```bash
hermes cron list 2>&1 | grep -oE "Skills:[[:space:]]+[a-z][^[:space:]]*(, [a-z][^[:space:]]*)*" | \
  sed 's/Skills:[[:space:]]*//' | tr ',' '\n' | tr -d ' ' | sort | uniq -c | sort -rn
```

Combine both: `(cron_used ∪ 90d_skill_view_used)` = "skills with evidence of use". The complement = candidates for uninstall (NEVER auto-uninstall; report only).

## Memory fill measurement — exact recipe (2026-07-07 proven)

The memory tool caps at 2,200 chars. The canonical file path is **`~/.hermes/memories/MEMORY.md`** (plural `memories/`, uppercase `MEMORY.md`). **Pitfall — wrong path**: `~/.hermes/memory.md` (singular, lowercase) does NOT exist; many scripts from earlier sessions reference it. Always verify the path with `ls` before assuming.

The tool itself reports `"usage": "99% — 2,191/2,200 chars"` on every write. **The most accurate local measurement is `wc -m` (codepoint count), NOT `wc -c` (byte count)**:

```bash
wc -m ~/.hermes/memories/MEMORY.md
# → 2191 chars (matches tool exactly)
wc -c ~/.hermes/memories/MEMORY.md
# → 2902 bytes (overcounts ~32% due to UTF-8 multibyte Korean/CJK)
```

**Why `wc -m` and not `wc -c`**: the memory tool measures by codepoint count. The 2,200-char cap is in codepoints. `wc -m` matches the tool's report exactly (verified 2026-07-07: both report 2,191 for the same file). `wc -c` overcounts by UTF-8 multibyte ratio (~1.32x for Korean text).

**Pitfall — verify current state, never trust compaction context numbers (2026-07-07)**: a previous session's compaction summary reported memory at "91.2%, 2,070 chars" but the actual `wc -m` showed "99.6%, 2,191 chars". Compaction can carry stale or miscalculated numbers because it derives from conversation history, not direct measurement. **Always run `wc -m ~/.hermes/memories/MEMORY.md` before any memory operation**; treat compaction numbers as stale-by-default.

**Reference scripts** (in `~/.hermes/scripts/`):
- `memory_alert.py check` — exit 1 if ≥90%, exit 0 if <90% (cron-friendly)
- `memory_alert.py stats` — full report
- `memory_alert.py fix` — print canonical paths + cap
- 🆕 `memory_auto_compact.py` — **사용자 룰 자동 압축** ("90% 넘으면 자율 정리"). drift pre-check + 12 rules. See `references/memory-compression-workflow.md` for the full pipeline.

## Design-execution gap measurement — exact recipe (2026-07-07 proven)

A 3-metric weighted gap score to catch "design looks complete but execution silently degrades":

```bash
python3 ~/.hermes/scripts/design_exec_gap.py
# → cron 100% (29/29 ok), drift 0, wiki 11.8d avg → TOTAL GAP 2.6% (OK <10%)
```

**Formula**:
- cron_gap = 100 - success_pct (weight 50%)
- drift_gap = min(100, avg_drift_min / 30min × 100) (weight 30%)
- wiki_gap = min(100, avg_age_days / 90d × 100) (weight 20%)
- TOTAL = 0.5×cron + 0.3×drift + 0.2×wiki

**Verdict**:
- < 10% OK
- 10–30% WARN
- ≥ 30% FAIL

**Cron registration**: register at `0 0 1 * *` (1st of month 09:00 KST) with `no_agent=true deliver=local`. Saves JSON for trending.

## Compression drift check — exact recipe (2026-07-07 proven)

Before enabling auto-compression (`/compress` slash or context-compression trigger), verify drift is low:

```bash
python3 ~/.hermes/scripts/compression_drift_check.py
# → 15 § facts, 14 matched, drift 6.7%, verdict: pass
```

**Why**: memory.md is single-source-of-truth for cross-session facts. If auto-compression drops key facts while state.db still has them, future sessions will see a memory/wiki mismatch.

**Algorithm**:
1. Parse `§` separated entries from `MEMORY.md` (the line after each `§`)
2. For each fact, LIKE-search state.db assistant messages for the first significant word
3. drift% = (1 - matched/total) × 100
4. Pass if < 10%

**Verified aiprofit memory format** (single-formula, no exceptions):
```
TZ:KST+9,...fact content...
§
API:.env.DeepSeek flash/pro/chat/...,...fact...
§
...
```

## Wiki submodule hygiene — exact recipe (2026-07-07 proven)

`~/.hermes/wiki/logs/` is a **git submodule** pointing to `mybotagent/hermes-logs`. New log files need to be:

1. **Written inside the submodule directory**, not the parent wiki:
   ```bash
   # CORRECT — file lands inside the submodule
   write_file(path="/home/ubuntu/.hermes/wiki/logs/2026/2026-07-07-1707-foo.md", content=...)
   
   # WRONG — file lands in a separate clone, parent never sees it
   write_file(path="/home/ubuntu/mybotagent/hermes-logs/logs/2026/...", content=...)
   ```

2. **Committed INSIDE the submodule**, then the parent commits the new submodule pointer:
   ```bash
   cd ~/.hermes/wiki/logs && git add -A && git commit -m "..." && git push origin master
   cd ~/.hermes/wiki && git add logs && git commit -m "wiki: bump logs to <hash>" && git push origin main
   ```

3. **index.md updated** in the same commit that adds new `.md` files, otherwise the catalog drifts.

If you write the log file in `~/mybotagent/hermes-logs/` (the bare clone) instead of the submodule path, you'll have to `cp` it over and re-commit. Cheap mistake, easy to avoid.

## False-positive verification pattern (2026-07-07)

Daily-repo-orchestrator emits false-positives. The recurring pattern is "X missing" where X actually exists. Always verify directly before creating a remediation task:

```bash
# Orchestrator says: "README.md missing in mybotagent/mybotagent.github.io"
ls -la ~/.hermes/wiki/README.md
# → exists (4.6KB, 2026-06-29) → false-positive

# Close the orchestrator's flag with verification evidence
hermes kanban complete <orchestrator_task_id> \
  --summary 'false-positive: <path> exists (N bytes, YYYY-MM-DD). orchestrator heuristic failure on owner repo without root README — expected pattern. follow-up: <separate epic for orchestrator patch>'
```

**Pitfall**: don't auto-close on suspicion. Spend one `ls` to verify. The orchestrator is right ~30% of the time; "false alarm" without evidence is itself a data corruption risk.

## Cron registration — exact recipe

When you write a new script and want it to run on a schedule:

```bash
# 1) Verify the schedule doesn't collide with existing crons
hermes cron list 2>&1 | grep -E "Schedule:|<your-time-pattern>"

# 2) Register with no_agent=True (read-only / output-only scripts only)
cronjob action=create \
  name="<emoji> <Name> (<schedule desc>)" \
  schedule="<cron expression>" \
  script="<filename relative to ~/.hermes/scripts/>" \
  no_agent=true \
  deliver="<target: origin | discord:CH:THREAD | local>"
```

**Why `no_agent=true`**: LLM-free scripts are deterministic, faster, and never hit the "Broken pipe" failure mode that agent-mode crons do. For pure measurement/alert scripts, always use `no_agent`.

**Cron expression examples**:
- `0 0 * * 1-5` = weekdays 09:00 KST (= UTC+9 → 00:00 UTC)
- `0 0 1 * *` = 1st of month 09:00 KST
- `30 18 * * 5` = Fridays 03:30 KST (= Saturday 18:30 UTC) — typical weekly slot
- `0 4 * * 1-5` = weekdays 13:00 KST (= 04:00 UTC)

## Environment-aware execution — `execute_code` in cron context

**Pitfall discovered 2026-07-07**: `execute_code` (Hermes Python sandbox) is BLOCKED in cron context because cron jobs run unattended and the tool's subprocess pattern could bypass approval gates.

```
# Symptom:
{"success": false, "error": "BLOCKED: execute_code runs arbitrary local Python ... 
 Cron jobs run without a user present to approve it. Use normal tools instead."}

# Workaround:
# Replace execute_code with a sequence of terminal() calls or write_file + terminal invocation.
# This is the only safe pattern in cron contexts. Live sessions CAN use execute_code.
```

**Live-session alternative**: when NOT in cron, `execute_code` is fine and faster than 5+ separate terminal calls. Check context first.

## 🆕 hermes-config-sync 운영 패턴 (2026-07-09)

`~/.hermes/scripts/hermes_config_sync.sh`로 4개 GitHub 레포(`hermes-wiki` / `hermes-skills` / `hermes-scripts` / `hermes-config`)에 단방향 mirror. **단일공식 = push-first (DRY_RUN=0 default)** — 사용자 rule "github은 기록용".

### 5가지 동시 발견된 함정 (전체 fix recipe + 진단 → `references/hermes-config-sync-patterns.md`)

1. **DRY-first silent fail (가장 위험)** — cron은 실행됐지만 push 0. log는 정상. **판단 신호**: cron log 정상 + GitHub 변화 0 → grep `DRY_RUN=` 즉시 확인.
2. **rsync가 stage의 `.git/`을 wipe** — `rsync --delete`가 자기 자신의 `.git`까지 삭제. fix: `rsync --exclude '.git' --exclude '.git/' --exclude '.git/**'`.
3. **config step 무한 재귀** — `~/.hermes`를 src에 넣으면 자기 자신이 stage로 들어가서 60s timeout. fix: config는 **선별 파일만 수동 cp** (memory.md redact, jobs.meta.json, config.yaml, .env.example).
4. **jobs.json secret 노출 위험** — `jobs.meta.json`은 name/schedule/script/enabled/no_agent만 push. prompt/delivery/job_id/last_run **절대 제외**.
5. **PAT admin scope 부족** — 자동 delete/archive ❌. 사용자가 GitHub UI에서 직접.

### Mirror repo 늘리기 전에 줄이기 (2026-07-09 user rule)

5+2 → 4개로 축소 결정: `hermes-cron` / `hermes-memories` 신규 생성했으나 secret 위험 + jobs.meta.json으로 80% 커버 → 삭제 우선. **판단 기준**: (1) 기록 가치? (2) 다른 곳에서 80%+ 커버? (3) secret 노출 위험? → 모두 yes면 삭제 후보. **force push / admin PAT 자동 delete는 user rule상 절대 ❌**.

### Self-healing agent vs no_agent 둘 다 활성 (2026-07-09 user clarification)

- `894e773a9a2b` (no_agent, 10분 간격, 96회/일) — rule-based 즉각 인프라 자가복구 (stale lock, Dashboard 재시작)
- `af8dcb9a1cce` (agent, 15분 간격, 61회/일) — LLM multi-step 근본 진단 + 자율 액션 (DRY-first→push-first rule 변경, repo 생성, 스크립트 fix)

**agent를 "no_agent가 같은 역할 중"으로 정리 ❌ — 절대 금지**. agent는 multi-step 자가 액션 가능. 사용자가 paused 1달 동안 self-heal 안 돼서 17시간 sync 안 됨 같은 문제 누적.

## Pitfalls

**Auto-uninstalling "unused" skills.** The 90-day filter catches skills the agent USED but happened not to load this session. Some skills are load-on-demand by category (`channel-context-discipline`, `code-audit-fix-pack`) — they appear "unused" but fire whenever relevant. **Report only; never uninstall without explicit user OK.**

**Closing tasks without verification.** If you close a "memory_alert" task claiming ±0% accuracy, you should have actually run the script and shown the output. Closing tasks on "should be fine" is the same self-deception that creates technical debt.

**Treating the parent wiki and submodule as one.** A `git commit` in `~/.hermes/wiki/` does NOT commit the submodule's contents. Two separate `git push` calls are needed. Forgetting the parent push means the new log file is on GitHub but the catalog (`index.md` references it) isn't — broken state for the next sync.

**Logging without a round number.** When you do 3+ rounds of autonomous cleanup in one day, number them: `round-1`, `round-2`, `round-3`. Otherwise the next session can't tell which log to read first.

**Surprising the user with cron creation.** A new `no_agent` cron is mostly harmless but still visible in `hermes cron list`. Always mention cron registrations in the report so the user knows the schedule changed.

**Asking permission mid-loop.** Once the user said "자율 진행", don't ask "더 진행할까요?" between rounds. Chain rounds until you hit a stop signal. Re-asking defeats the autonomy mandate.

**Closing DESIGN tasks as "done" without producing the design doc.** A task titled "Phase X DESIGN.md" requires an actual markdown deliverable under `~/.hermes/wiki/architecture/`. If you close it without one, you've lost the value. Author the file, update `wiki/index.md`, push, THEN close.

## Reference patterns

| Pattern | File |
|---|---|
| Skill usage measurement | `references/skill-usage-audit.md` |
| Wiki submodule hygiene | `references/wiki-submodule-hygiene.md` |
| Kanban dedup audit | `references/kanban-dedup-audit.md` |
| Step 4 자율운영 후보 | `references/step-4-candidates.md` |
| 🆕 Memory 90% 압축 워크플로 | `references/memory-compression-workflow.md` |
| 🆕 Memory lazy indexing (50% 이하, wiki 페이지 링크 + memory-map repo) | `references/memory-lazy-indexing.md` |
| 🆕 **Memory→Wiki 마이그레이션** (wiki-first 감사 → wiki 페이지 생성 → batch 제거 → index.md → 주간 cron) | `references/memory-wiki-migration.md` |
| 🆕 PR submission & review workflow (PR→Review 필수, **own vs external 분기**, Case A mybotagent own / Case B fork→upstream) | `references/external-pr-workflow.md` |
| 🆕 System audit (Hermes + GitHub 종합 진단 — disk/script/cron 3-tier) | `references/system-audit-methodology.md` |
| 🆕 Linear backfill (Kanban done → SHO issue, mapping.json 미존재 task 자동 승격) | `references/linear-backfill-workflow.md` |
| 🆕 **hermes-config-sync 운영 패턴** (DRY-first silent fail, rsync .git wipe, config 무한 재귀, mirror repo 줄이기, self-healing 이중 구조) | `references/hermes-config-sync-patterns.md` |

## Scripts (re-runnable)

| Script | Purpose | Usage |
|---|---|---|
| `scripts/memory_alert.py` | Memory cap check (≤90% silent, ≥90% alert) | `python3 ~/.hermes/scripts/memory_alert.py check` |
| `scripts/wiki_lint.py` | SCHEMA.md 8종 lint | `python3 ~/.hermes/scripts/wiki_lint.py [scope] [--json]` |
| `scripts/compression_drift_check.py` | Auto-compression drift verification | `python3 ~/.hermes/scripts/compression_drift_check.py` |
| `scripts/design_exec_gap.py` | 5-stage verify gap metric | `python3 ~/.hermes/scripts/design_exec_gap.py` |
| `scripts/self_improve_loop.py` | 자가개선 루프 (Step 2) — gap/drift/lint 통합 + Kanban 자동 생성 + alert_only | `python3 ~/.hermes/scripts/self_improve_loop.py [--dry-run]` |
| `scripts/kanban_linear_sync.py` | Kanban ↔ Linear 양방향 sync (Step 3, 보수적 매핑 기반) | `python3 ~/.hermes/scripts/kanban_linear_sync.py [--apply]` |
| `scripts/memory_auto_compact.py` | 🆕 Memory 90% 룰 자동 압축 (drift pre-check + 12 룰) | `python3 ~/.hermes/scripts/memory_auto_compact.py [--dry-run\|--force]` |
| `scripts/memory_lazy_fetch.py` | 🆕 Memory lazy indexing — § fact → wiki 페이지 on-demand fetch (50% 이하 목표) | `python3 ~/.hermes/scripts/memory_lazy_fetch.py [--fact N\|--search Q\|--list]` |

## Step Arc — 자율 기획 → 자가개선 → 진화 → 자율 운영 (2026-07-07 합의)

사용자 목표: "내가 지시하지 않아도 자율 기획 → 자가 개선 → evolve step → 자율 운영". 위 스크립트 + cron이 정확히 4-step으로 매핑됨:

```
Step 0: 수동 운영       → idle hygiene (이 skill 본문)         → Kanban ready cleanup
Step 1: 자율 기획       → daily-task-suggestion (별도 cron)    → 매일 07:00 KST Kanban 태스크 제안
Step 2: 자가 개선       → self_improve_loop.py                → 매주 일 21:00 KST gap/drift/lint 측정 + 개선 Kanban 자동 생성
Step 3: 진화           → kanban_linear_sync.py                → 평일 11:00 KST Kanban↔Linear 양방향 sync
Step 4: 자율 운영       → (다음 단계, 미구현)                  → 사람 개입 0, 자가 측정 + 자가 조정
```

**진행 방식**: Step 0 → 1 → 2 → 3은 자동 운영 중 (위 cron 가동). Step 4 후보는 다음 idle 시 자율 진행 가능 — `references/step-4-candidates.md` 참고.

### alert_only vs auto Kanban generation (자가개선 루프 핵심 패턴)

자가개선 루프의 4가지 detector 중 P0 (예: memory 99%+)는 **자동 Kanban 생성 ❌, alert only**:

```python
# self_improve_loop.py
issues.append({
    "priority": 1,
    "alert_only": True,   # ← 이 플래그가 있으면 Kanban 생성 스킵
    "title": "memory.md 99%+ — 사용자 결정 필요",
    "body": "...",
})

# main() 분리
auto_issues = [i for i in issues if not i.get("alert_only")]
alert_only  = [i for i in issues if i.get("alert_only")]
create_kanban_tasks(auto_issues)  # alert_only는 stdout에만 출력
```

**판단 기준**: 자동 변경 시 blast radius > 0이면 alert_only. 예:
- memory 압축/archive (단일공식 = 사용자 결정)
- GitHub push, SMTP send, payment
- 자격증명/secret 변경
- 외부 Collaborator 추가

### Kanban ↔ Linear sync — 보너스 fix 발견

라운드 4에서 SHO-39/43/44/45/49/50/51 (Linear) 이 Kanban에서 모두 close됐는데 Linear에는 미반영 상태였음. **kanban_linear_mapping.json에 매핑 8건만 있어서 자동 sync가 부분만 가능**. SHO-49/50/51은 매핑 부재 → 수동 처리.

**Pitfall (다음 회)**: Kanban close할 때 mapping에 없는 SHO가 있으면 즉시 SHO도 수동 close 필요. `~/.hermes/scripts/kanban_linear_sync.py`는 매핑 기반이라 신규 매핑 자동 추가 ❌.

## Pitfalls (added 2026-07-07)

**Assuming `kanban.db` has `updated_at`.** The `tasks` table uses `completed_at` for completion timestamp, NOT `updated_at`. SQL `SELECT updated_at FROM tasks` returns `no such column: updated_at`. See `scripts/kanban_linear_sync.py:65` for the verified schema.

**Hardcoding Linear state IDs in cron scripts.** `86cd9d73-2b97-49e9-8b16-95c1d08c29ad` (Done) and `cec5bc9e-3028-4f51-b3ad-1f60740a1812` (Backlog) are Shootingstock team workflow state UUIDs. They work today but will break if Linear workflow is reconfigured. Alternative: query states by name at script start (`{ team { states { nodes { id name } } } }`) and cache.

**Trusting compaction context numbers for memory size (added 2026-07-07).** Compaction can carry stale or miscalculated size/percentage numbers — it derives from conversation history, not direct measurement. Before any memory operation, ALWAYS run `wc -m ~/.hermes/memories/MEMORY.md` to get ground truth. Treat compaction numbers as stale-by-default; verify before acting.

**Wrong memory path in scripts (added 2026-07-07).** Canonical path is `~/.hermes/memories/MEMORY.md` (plural `memories/`, uppercase). The singular `~/.hermes/memory.md` does NOT exist. When importing or porting memory scripts, verify the path with `ls -la ~/.hermes/memories/` before assuming.

**Removing memory facts without wiki fallback (added 2026-07-07).** When compressing memory, the 12-rule strategy assumes the removed facts are already in the wiki. If a fact is memory-only (e.g., multi-bot infrastructure mapping that has no wiki page), compression will silently drop it. **Always check `grep -rn "<key phrase>" ~/.hermes/wiki/` before removing**; if no hit, write a wiki page FIRST, then compress.

**메모리 본질 비효율 함정 — "size 줄임 ≠ 문제 해결" (added 2026-07-07)**. memory.md가 90% → 50% → 44.9%로 줄면 사용자/에이전트 둘 다 "거의 끝났다"고 착각하기 쉬움. 하지만 **memory.md 본문은 매 세션 컨텍스트에 100% inject**되므로, 50%든 1,107 chars든 매 세션 동일하게 토큰 비용이 발생. 진짜 답은 memory.md를 본문 없이 **key만** 들고 `memory_query(key)` skill로 위키 lazy fetch하는 **tool-as-memory** 패턴. 50% 압축은 단기 개선일 뿐, **본질적 해결책이 아님**. 사용자에게 보고 시 "size 줄임"과 "본질적 해결"을 구분해서 전달 — 안 그러면 사용자가 진짜 문제가 해결됐다고 오해함.

**자율 사이클에서 PR target = own repo 기본값 착각 ❌ (added 2026-07-07)**. 사용자가 "Fix PR" 명령 시 GitHub 글로벌 issue search는 외부 upstream이 먼저 hit될 수 있음 (`NousResearch/hermes-agent` 등). 그러나 사용자 의도는 **mybotagent own repo PR (Case A)**. 외부 fork → upstream PR (Case B)은 **사용자 명시 OK 후에만**. autonomous mode에서 confirm 없이 Case B 진행했다가 사용자 교정 → close + fork 정리 비용. **판단 신호**: 사용자가 "우리 github" / "내 repo" / "mybotagent" 강조 → Case A. "외부" / "upstream" 명시 + OK → Case B. 애매하면 clarify. 전체 워크플로우 + 체크리스트는 `references/external-pr-workflow.md`.

**자율 사이클 결과 보고 부재 — Discord + dashboard 양쪽 다 ❌ (added 2026-07-07)**. 새벽 사이클(02:15~02:20 KST)이 실제로는 성공 (PR #1 squash merge, race-condition fix push)이었는데 사용자가 "아무것도 동작 안했음"으로 인지. 원인: (1) Discord 메시지 사용자가 수면 중 미수신, (2) 시각적 dashboard 없음 (terminal 로그만 push), (3) PR → Review 정책 명문화 부족. 자율 사이클 후 **사용자 인지 가능한 채널이 비어있으면 작업이 성공해도 사용자 인지는 0**. 최소 가드레일: 매일 아침 일과 시작 전 cron `1d795f36a5a4` (survey-morning, 06:00 KST)이 어제 작업 요약을 Discord로 push — 사용자가 매일 한 번은 본다는 가정. 또는 매일 아침 Kanban ready 변화량 + cron last_status 변화량을 1줄로 리포트하는 watchdog 추가.

**System audit 결과 보고 시 "즉시 처리" vs "보고만" 명확히 분리 (added 2026-07-07)**. audit 결과는 3-tier (P0/P1/P2) + 처리 방식 (즉시/보고/사용자 결정) 모두 명시. 섞어서 보고하면 사용자가 자율 운영 범위를 잘못 파악. 예: "tmp_pack 정리 ✅ done" + "state.db 백업 정책: 사용자 결정" — 다른 카테고리.

**Compaction context의 memory size 숫자는 stale일 수 있음 (added 2026-07-07)**. 이전 세션 compaction context: "memory 91.2%, 2,070 chars". 실제 측정: 99.6%, 2,191 chars. **disk/script/cron/memory 모든 audit 결과는 명령어로 직접 측정**. compaction은 conversation history 기반이라 측정값 자체를 verify하지 않음.

**자율 cleanup round 결과가 Linear에 backfill 안 됨 (added 2026-07-07, re-encountered)**. Round 2~4 (17:07/17:34/17:36/18:10 KST)에서 발견/해결한 14개 작업이 Kanban ready→done으로만 처리되고 SHO 티켓으로 자동 승격되지 않음. 사용자가 "Linear에 중간중간 이슈와 해결한것들이 전혀 업데이트 안됨"으로 인지. 원인: `kanban_linear_sync.py`는 **mapping.json 기반**만 sync → 신규/매핑 없는 task는 silent drop. **Fix**: round 끝날 때마다 SHO backfill — 모든 closed Kanban을 GraphQL `issueCreate` 후 state `Done` 일괄 변경. 또는 cron `4610bc039434` (kanban_linear_sync 평일 11:00 KST)에 `unmapped_done` 액션 추가. **판단 기준**: audit round N개를 close한 후 Kanban recent done 30건 ↔ SHO 최근 30건 diff → 차이만큼 backfill.

**hermes cloud 디스크 clone이 외부 repo default (added 2026-07-07)**. `~/.hermes/hermes-agent`가 `origin = NousResearch/hermes-agent`로 clone되어 있었음. 사용자 own repo는 `mybotagent/hermes-agent` fork인데. **증상**: (1) 우리 fork와 560 commits drift, (2) 우리가 만든 commit `316cc9a7b` (PR #60279 close되어도) cloud 디스크에 그대로 남음, (3) 외부 repo에서 작업한 것처럼 보임. **Fix**: `git remote set-url origin https://github.com/mybotagent/<repo>.git && git fetch origin && git reset --hard origin/main && git branch -D fix/...`. 모든 git 작업 전 `git remote -v`로 origin 확인 — `mybotagent` prefix 아니면 user confirm 또는 작업 거부. **판단 기준**: hermes cloud의 git clone은 모두 mybotagent org 소속이어야 함. upstream(NousResearch 등)은 별도 fork 경로 또는 절대 직접 clone ❌.

**Kanban → Linear sync silent drop (added 2026-07-07, v1.1 fix)**. `kanban_linear_sync.py` v1.0은 mapping.json 매핑만 sync → 신규 task는 누락. v1.1에서 `unmapped_done` action 추가 (감지만, 자동 생성 ❌). **판단 기준**: round 끝나면 unmapped_done 카운트 → 사용자 confirm 후 batch backfill (GraphQL `issueCreate` × N + state 변경). 또는 round 시작 시 mapping.json에 신규 kanban_id 미리 등록 (proactive).

**PR target 오해 — hermes cloud 디스크 ↔ github 2단계 인지 필요 (added 2026-07-07)**. 사용자가 "github과 hermes 클라우드 디스크 안의 코드를 대상으로" 명시. 1단계: hermes cloud 디스크 (`~/.hermes/...`) 안의 코드 변경. 2단계: github (`mybotagent/hermes-wiki`, `hermes-agent` fork 등)에 push → PR → Review. **흐름**:
```
[hermes cloud 디스크] → git add/commit/push (직접)
        ↓
[mybotagent github] → feature branch + PR
        ↓
[PR → Review] → CI + verdict → squash merge
        ↓
[hermes cloud 디스크로 pull] → cron/skills/위키 자동 reload
```
자율 cleanup에서 PR 생성만 ❌ — Reviewer 지정 + verdict 받기까지가 한 사이클. `references/external-pr-workflow.md` 참조.

**자율 cleanup 시 PR 2-tier 정책 적용 (added 2026-07-07)**. Trust-based 2-tier PR 정책 (사용자 확정, 2026-07-07 v2). 자율 cleanup에서 PR 만들 때 다음 분기:
- **Tier 1** (메인 서비스 / 인프라 / secret / 외부 repo / wiki 정책 페이지) → reviewer verdict + 사용자 확인 필수
- **Tier 2** (문서 typo / 1~2 line fix / 주석 / wiki raw/ / README 다듬기) → 사용자 1회 확인 → squash merge (reviewer 불필요)

**판단 기준**: 새 기능 / API 변경 / workflow/secret/.env 변경 → Tier 1. 1~2 line fix / typo / 주석 / wiki raw/ → Tier 2. 애매하면 Tier 1로 보수적 진행. 전체 정책은 wiki `infra/pr-review-policy.md` v2.0.

**절대 금지 (모든 tier 공통)**: ❌ force push, ❌ main/master 직접 push (PR 경유), ❌ 의미 있는 코드 삭제 commit, ❌ secret/API 키 커밋, ❌ 외부 repo force push. 자율 cleanup에서 이 중 하나라도 필요해지면 사용자 confirm.

**hermes-pr-gate self-import 범위 (added 2026-07-07)**: 우리 own repo 32개 중 **hermes-pr-gate만** auto-merge.yml + review-bot.yml 설치. 다른 31개는 Tier 2 정책으로 PR + 직접 squash merge. 잘못 self-import된 게 있으면 삭제:
- `hermes-wiki-super` (auto-merge.yml + review-bot.yml 삭제, 2026-07-07)
- `mybotagent.github.io` (auto-merge.yml + review-bot.yml 삭제, 2026-07-07)

## 🆕 Pitfalls (added 2026-07-09)

**DRY-first cron silent fail — single most dangerous pattern**. `hermes_config_sync.sh`가 `DRY_RUN=1` default로 만들어져 있었을 때, cron은 매일 정상 실행됐지만 **실제 push는 0** → 17시간 무push. log는 "DRY: would commit N files"로 정상처럼 보임. 사용자 명시 rule "github은 기록용" = push-first가 default여야 함. `DRY_RUN=1`은 1회 preview용. **판단 신호**: cron log는 정상 + GitHub 변화 0 → DRY-first 1순위 의심. `grep "DRY_RUN=" ~/.hermes/scripts/hermes_config_sync.sh | head -3`로 즉시 확인. fix recipe + 4개 동반 버그 (rsync .git wipe, config 무한 재귀, jobs.json secret 노출, PAT admin scope 부족) → `references/hermes-config-sync-patterns.md`.

**Mirror stage rsync가 자기 `.git/`을 wipe**. `rsync -a --delete`로 src→stage 동기화할 때 stage에만 있는 `.git/`이 src에 없으면 **매번 삭제됨**. 결과: sub-step "is not a git repo" 에러 + 모든 mirror SKIP. fix: `rsync --exclude '.git' --exclude '.git/' --exclude '.git/**'` 명시. **판단 신호**: stage 폴더에 rsync 결과물은 있는데 `.git/`이 없을 때. full fix + 4개 동반 패턴 → `references/hermes-config-sync-patterns.md`.

**Config step 무한 재귀 — `~/.hermes`를 src에 넣지 말 것**. `ensure_mirror_stage "config" ... "$HERMES_HOME" ...` 호출 시 `~/.hermes` 전체가 stage(`~/.hermes/.mirror/config-stage/`)로 들어가서 `.git/`, `.mirror/`, `wiki/` 등 자기 자신이 stage에 들어감 → rsync 무한 루프 + 60s timeout. fix: config는 **선별 파일만 수동 cp** (memory.md redact, jobs.meta.json, config.yaml, .env.example) + 강화된 .gitignore. **판단 신호**: sync 60s timeout + "file has vanished" 반복 출력.

**Self-healing agent vs no_agent 둘 다 활성 유지 (user clarification 2026-07-09)**. `894e773a9a2b` (no_agent, 10분)와 `af8dcb9a1cce` (agent, 15분)가 **상호보완적**이라 둘 다 켜야 함. agent는 LLM이 multi-step 근본 진단 + 자율 액션 (DRY-first→push-first rule 변경, repo 생성, 스크립트 fix 등), no_agent는 rule-based 즉각 인프라 자가복구 (stale lock 제거, Dashboard(:9199) 재시작). **판단 신호**: agent가 paused 1달 동안 self-heal 안 돼서 17시간 sync 안 됨 같은 문제가 누적됨. **agent를 "no_agent가 같은 역할 중"이라는 이유로 정리 ❌ — 절대 금지**. 사용자 명시 교정 (2026-07-09): "셀프 힐링 반드시 필요한데 왜 정리하려고함?".

**Mirror repo 늘리기 전에 줄이기 먼저 (user rule 2026-07-09)**. 사용자 명령: "운영이 어려우면 불필요한 레포 삭제하도록". 5개 신규 생성한 `hermes-cron` / `hermes-memories`는 jobs.json 풀 정의(memory.md)라 `hermes-config/cron/jobs.meta.json`(+ 위키 `infra/cron-jobs.md`)으로 80% 커버 + prompt secret 위험 → 삭제 우선. **판단 기준**: (1) "기록 가치"가 있는가? (2) 다른 곳에서 80%+ 정보가 커버되는가? (3) secret 노출 위험? → 모두 yes면 삭제 후보. force push / admin PAT 자동 delete는 user rule상 절대 ❌ — 사용자가 GitHub UI에서 직접 Archive.

**Cron 변경/문서화 시 빠뜨림 방지 — 항상 전부 보고 (user frustration signal 2026-07-09)**. 사용자가 "왜 자꾸 빼먹지? 너무 많아서 그런가?"로 명시. 자가진단/보고에서 일부 sub-step만 다루지 말고 **전체 mirror list** + **전체 cron list** + **전체 deliver format** 항상 1-page 요약. `hermes cron list` 42개 → `infra/cron-jobs.md`에 42개 다. 5개 레포 → 4개 + 2개 신규 = 6개 status 다. 빠뜨림 = 다음 세션의 또 다른 자가진단 트리거.

## 사용자 룰: memory 90% 자율 정리 (added 2026-07-07)

**사용자 메시지 (2026-07-07)**: "메모리 90 넘으면 알아서 자율적으로 정리하기"

이 룰은 `memory_auto_compact.py` + cron `cb2ee5fafc5d` (매일 06:30 KST, deliver=local)에 영구화. silent 성공 / drift block 또는 룰 부족 시에만 Discord 알림.

**전체 파이프라인 + 12개 압축 룰 + 안전 가드 + cron 등록 recipe** → `references/memory-compression-workflow.md`.

## 사용자 룰: memory ≤ 50% lazy indexing (added 2026-07-07)

**사용자 메시지 (2026-07-07)**: "메모리 50이하로 줄여져야함. 대부분의 메모리는 레이지 로딩 방식의 인댁싱 방식으로 정리되어야함. 메모리 맵을 만들어서 github으로 따로 관리해도 좋을 듯"

50% 임계치는 `memory_auto_compact.py`의 90% alert와 별개:
- **90% alert** = 압축 자동 트리거 (12 룰로 89%까지 도달 가능)
- **50% 설계 목표** = wiki lazy indexing으로 재설계 (구조 변경)

**구현**:
- memory.md: 16 facts → 17 facts (SYS 룰 추가), 모두 위키 링크로 변환
- `~/.hermes/scripts/memory_lazy_fetch.py`: § fact → 위키 페이지 on-demand fetch
- `https://github.com/mybotagent/memory-map` repo: 17 facts ↔ wiki 페이지 매핑 테이블
- 신규 위키 3페이지: `5-stage-verify`, `speculation-cascade-rule`, `github-pr-automation-policy`

**아키텍처 + 17 facts 매핑표 + 안전 가드 + 신규 위키 페이지 목록** → `references/memory-lazy-indexing.md`.

**Pitfall (lazy indexing 추가)**: 
- 압축 전 `grep -rn "<key phrase>" ~/.hermes/wiki/` 필수. 0건이면 wiki 페이지 먼저 작성 후 압축 (위임 fallback 없으면 사실 손실).
- FACT_MAP (스크립트 dict) ↔ memory-map README.md ↔ memory.md § facts = 3-way sync. 한쪽 변경 시 다른 쪽도 업데이트.
- 50% 추가 압축(현재 44.9%)은 사용자 명시 요청 시에만.

## 사용자 룰: hermes-config-sync push-first (added 2026-07-09)

**사용자 메시지 (2026-07-09)**: "원인을 찾아서 너가 알아서 해결해줘" (DRY-first silent fail 진단)

이 룰은 `hermes_config_sync.sh` 헤더에 영구화:
- `DRY_RUN=0` default (push-first)
- 1회 preview만 필요하면 `DRY_RUN=1 bash ~/.hermes/scripts/hermes_config_sync.sh`
- mirror stage .git wipe fix + config step 무한 재귀 fix + jobs.meta.json 민감정보 제외 (prompt/delivery/job_id/last_run 제외) + 강화된 .gitignore (.env, *.token, *.pem, memories/memory-current.md, .mirror/, .git/)
- 사용자 원칙 "github은 기록용" = push-first (cron이 자동 push)
- 4개 레포 운영: hermes-wiki / hermes-skills / hermes-scripts / hermes-config
- 2개 신규 생성했으나 삭제 우선: hermes-cron (jobs.json 풀 정의 secret 위험) / hermes-memories (memory.md 위키 통합) → 사용자 GitHub UI Archive

**전체 5가지 함정 + 진단 recipe + 4 레포 drift 확인** → `references/hermes-config-sync-patterns.md`.

## 사용자 룰: Self-healing agent + no_agent 병행 유지 (added 2026-07-09)

**사용자 메시지 (2026-07-09)**: "둘다 필요해? 둘다 필요하다고 생각하면 다시 키기"

agent (`af8dcb9a1cce`, 15분 간격) 재개 + no_agent (`894e773a9a2b`, 10분 간격) 유지. **agent를 "no_agent가 같은 역할 중"으로 정리 ❌** — multi-step LLM 자가 액션은 no_agent가 못 함.