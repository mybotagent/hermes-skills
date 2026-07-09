---
name: daily-repo-orchestrator
description: mybotagent 본인이 owner인 GitHub 레포를 매일 07:00 KST 진단하고 발견된 작업을 Linear / Kanban / GitHub issue-PR mirror로 등록하는 cron-friendly 단일 공식. STAGE별 dry 분리 (harvest/mirror/fix/email 각기 toggle) + Linear/Kanban idempotency 자동. IMAP read-only. **Gmail SMTP 발송 ❌, 외부 Collaborator 추가 ❌, push/PR/open 은 사용자 confirm 전까지 dry**. **🆕 v1.4 Config Sync Mode — 단방향 push-only mirror (사용자 정책 "github은 기록용")**, **DRY-first 신규 cron 등록 절차**, **mirror bare clone 패턴**. 2026-07-07 autonomous mode + config sync 통합.
version: 1.4.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github, linear, kanban, cron, automation, orchestrator, daily, autonomous, idempotency, stage-dry, config-sync, one-way-push, mirror-bare-clone]
    related: [bash-script-template, channel-context-discipline, pr-merge-gate, self-improvement-loop, system-health-monitoring]
---

# Daily Repo Orchestrator

매일 07:00 KST cron이 실행하는 단일 공식 (사용자 동작 0개):
**pre-flight → harvest → prioritize → mirror → fix → verify**

## 🆕 v1.4 — Config Sync Mode (단방향 Push-Only Mirror)

**배경 (2026-07-07)**: 사용자 (aiprofit) 명시 정책 — *"github은 기록용"*. 로컬 filesystem (`~/.hermes/{skills,scripts,cron,memories,wiki}`)을 GitHub에 **단방향 push**하는 신규 cron `hermes-config-sync (91059d1e3d31)` 가 user 요청으로 도입됨. 기존 daily-repo-orchestrator 와 책임이 다르므로 **별도 cron + 별도 sub-step 패턴**으로 통합.

### 사용자 정책 — Hard Rule

| 사용자 발언 | 적용 |
|---|---|
| "github은 기록용" / "기록용임" | **push only, 절대 pull/drift-pull ❌** |
| "기존 작업 통합" | **중복 cron 만들지 말고 흡수**, 기존 작업은 delete |
| 자율모드 ("알아서/왜 못함?") | **중간확인 X**, 끝까지 진행 후 사후 보고 |
| "DRY-first" (hermes 운영 정책) | **사용자 confirm 전까지 절대 push 안 함** |

### Config Sync Mode — Single Formula

```
[trigger] 매일 KST 22:30 (no_agent cron)
    ↓
[env load] HERMES_HOME + .env (GITHUB_TOKEN)
    ↓
[pre-flight] 4 repo HTTP HEAD probe (200/404/403/401)
    ↓
[4 sub-steps, failure-isolated]
    ① wiki       → existing origin → add+commit+push (DRY=0) or numstat preview (DRY=1)
    ② skills     → mirror bare clone → same
    ③ scripts    → mirror bare clone → same
    ④ config     → mirror bare clone → jobs.meta.json + .env.example + memory.md(reducted)
    ↓
[drift check] local HEAD vs origin/main (record only, blocking ❌)
    ↓
[로그]  ~/.hermes/cron/output/hermes-config-sync-YYYY-MM-DD-HHMMSS-UTC.log
    ↓
[stdout] 마지막 줄: "hermes-config-sync done — DRY=$DRY_RUN log=..."
```

### Mirror Bare Clone 패턴 (CRITICAL — git 아닌 fs push의 표준)

로컬 디렉토리(`~/.hermes/skills` 등)는 git repo가 아니므로 GitHub에 push하려면 mirror 구조 필요:

```
~/.hermes/.mirror/
├── skills.git/         ← bare repo (origin 역할)
└── skills-stage/       ← working tree (rsync로 src 복제)
```

```bash
# 1) bare repo가 없으면 clone (origin이 200일 때만) 또는 bare init
[ ! -d "$mirror" ] && git clone --bare https://github.com/$repo.git "$mirror"

# 2) stage working tree (없으면 clone, 없으면 bare init 결과물 활용)
[ ! -d "$stage" ] && git clone "$mirror" "$stage"

# 3) rsync src → stage (.gitignore로 secrets 제외)
rsync -a --delete \
  --exclude '.bundled_manifest' --exclude '__pycache__' \
  --exclude '*.pyc' --exclude '.DS_Store' \
  "$src"/ "$stage"/

# 4) stage에서 commit + push (DRY 모드면 numstat preview만)
```

**실측 검증 (2026-07-07 16:10 UTC)**: 4 sub-step 모두 정확 동작, 1초 내 종료, no-agent cron 적합.

### Secret Safety (.gitignore 자동 생성)

config stage에서 `.gitignore` 자동 작성:
```
.env, *.token, *.pem              # 절대 commit ❌
cron/jobs.json (12MB)              # ❌ raw, jobs.meta.json 만 푸시
memories/*.md                      # ❌ raw, redaction 거친 snapshot 만
cron/output/, cron/ticker_*        # local state noise
```

→ 사용자 .env / API key / 개인 메모리 누설 zero-risk.

### 4 Sub-step 책임 분리

| # | sub-step | target repo | 책임 |
|---|---|---|---|
| ① | wiki | mybotagent/hermes-wiki | 기존 origin 활용, wiki 기록은 push 가능 |
| ② | skills | mybotagent/hermes-skills | 40 skills (24MB) mirror — 사용자 생성 대기 가능 |
| ③ | scripts | mybotagent/hermes-scripts | cron 실행 스크립트 (256KB) |
| ④ | config | mybotagent/hermes-config | cron 정의 (jobs.meta.json), memories snapshot, .env.example |

→ 각 sub-step의 HTTP 상태 코드별 행동:
- **200**: mirror init → commit/push (DRY=0) or numstat preview (DRY=1)
- **404**: safe-skip + stdout 메시지 ("사용자에게 1회만 생성 요청")
- **401/403**: safe-skip + stdout 메시지 ("token 권한 부족")
- **000 (네트워크 오류)**: safe-skip + stderr 로그

### DRY-first 신규 cron 등록 절차 (사용자 정책 강화)

**Step 1**: DESIGN.md 작성 (단일공식 + DRY-first 명시)
**Step 2**: 스크립트 작성 + `bash -n` syntax check
**Step 3**: `DRY_RUN=1` 로 1회 수동 실행 → 4 sub-step 동작 확인
**Step 4**: no_agent cron 등록 (`--script <filename>` filename only)
**Step 5**: 24~48h dry cycle 누적 (실제 push 0)
**Step 6**: 사용자 "prod 켜" 1마디 → `DRY_RUN=0` 으로 cron update
**Step 7**: wiki 기록 + log push (index update)

**절대 안 되는 것**:
- ❌ 첫 cycle부터 `DRY_RUN=0` 으로 cron 등록
- ❌ 사용자 confirm 없이 `--script` 로 prod push
- ❌ dry-run stdout 누적 없이 prod 전환

### 실측 cron ID (2026-07-07 등록)

- `91059d1e3d31` hermes-config-sync (KST 22:30, DRY=1, no_agent) — 단방향 push sync
- `537dfbb83b81` wiki-auto-refresh (KST 21:00) — 흡수 예정 (다음 cycle 사용자 confirm 후 delete)

자세한 코드/함정/실측 transcript → `references/config-sync-mode.md`.

---

## When to Use

- `mybotagent/*` 레포의 일일 진단
- 발견된 작업을 SHO-XX Linear / `t_…` Kanban 태스크 / GitHub 이슈로 mirror (idempotent)
- top-3 작업 자동 PR + IMAP read-only 모니터로 watcher 발사 시점 측정
- risk-tiered 자동화 모드 preset (mirror-only / full prod / dry)

## Single Formula

```
pre-flight(token permission 5단계 probe + 부족 권한 명시)
  → harvest(레포 진단 → 후보 리스트, GET read-only)
  → prioritize(score = impact × certainty / effort → top-3)
  → mirror(Linear SHO + Kanban t_… + GitHub issue, idempotent)
  → fix(clone → branch → patch → push → PR.open)  ← 기본 dry
  → verify(read-only IMAP 모니터, GitHub /notifications 큐 조회)
  → report(send_email via himalaya, 기본 dry)
```

## 🆕 v1.3 — STAGE별 Dry 분리 + Idempotency

**배경 (2026-07-07)**: v1.2의 binary `DRY_RUN=0/1`은 위험 단계와 안전 단계가 묶여 있어 "mirror만 켜고 fix는 dry" 같은 부분 운영이 불가능했음. 매일 cron이 새 SHO-46/47/48을 중복 생성하는 문제도 있었음.

### STAGE별 DRY 분리

| env var | default | 영향 |
|---|---|---|
| `DRY_RUN` | `1` | true면 아래 4개 전부 dry (backward-compat) |
| `DRY_RUN_HARVEST` | DRY_RUN | GitHub `GET /user/repos`, `GET /repos/*/issues` 등 read-only call |
| `DRY_RUN_MIRROR` | DRY_RUN | Linear `issueCreate` + Kanban CLI create (idempotency 포함) |
| `DRY_RUN_FIX` | DRY_RUN | git clone + patch + push + PR open |
| `DRY_RUN_EMAIL` | DRY_RUN | `himalaya message send` |

**Mode presets (실전 검증된 3종)**:

```bash
# 1. Full dry (초기 / 사용자 confirm 전)
DRY_RUN=1 python3 scripts/daily_repo_orchestrator.py

# 2. Mirror-only prod (가장 흔한 운영 모드 — Linear/Kanban mirror만 push, fix/email dry)
DRY_RUN=0 DRY_RUN_FIX=1 DRY_RUN_EMAIL=1 python3 scripts/daily_repo_orchestrator.py

# 3. Full prod (사용자가 명시적으로 켠 후만)
DRY_RUN=0 python3 scripts/daily_repo_orchestrator.py
```

**Autonomous-mode 안전 추론**: 사용자가 "알아서 해라 / 위험한 것 제외 권한 모두 줌" 류 발언을 하면:
- `fix`/`email` 단계는 default dry 유지 (외부 영향 = 위험)
- `mirror`/`harvest` 만 활성화 (read + idempotent create)

### 🆕 Linear/Kanban Idempotency

매일 cron에서 같은 top-3가 다시 create되면 Linear에 SHO-46/47/48/49/... 누적됨. **2026-07-07 검증 — 자체 dedupe 작업**:

- **Linear**: `eqIgnoreCase` GraphQL filter로 동일 title 사전 검색 → 있으면 reuse (`linear-reuse` log), 없으면 issueCreate
- **Kanban**: `hermes kanban list --json` 으로 전체 title set 만들고 today marker가 있으면 skip (`kanban-reuse` log)

Unicode (한글/이모지) 정확히 매칭됨 (실측 — SHO-51 등). dedupe key: `repo::title[:80]` 정규화.

자세한 코드/함정 → `references/linear-kanban-idempotency.md`, `references/stage-flags-and-modes.md`.

## Mode

- `DRY_RUN=1` (default for first cycle): push/email 안 함. stdout에만 인쇄
- `DRY_RUN=0`: 실제 mutation. **첫 실행은 dry-run 1회 후 사용자 명령으로 production**
- v1.3+: STAGE별 분리는 위 "Mode presets" 참조

## 🚀 Pre-flight: Token Permission Probe (CRITICAL — 사용자 frustration 방지)

GitHub 자동화 시작 시 `pr-merge-gate` 의 pre-flight 5단계 probe를 **반드시** 실행. 부족한 permission 하나씩 발견될 때마다 사용자에게 요청하는 패턴은 사용자 답답함 누적 (= "왜 못함?", "또 부탁" 류).

```python
probe = {
    "repository_access": False,  # GET /user/repos → target 포함?
    "contents_rw":       False,  # PUT contents/<file>
    "workflows_rw":      False,  # PUT contents/.github/workflows/*
    "pull_requests_rw":  False,  # PR 코멘트/merge API
    "secrets_rw":        False,  # PUT actions/secrets/*
}
```

**5개 모두 True가 아니면 사용자에게 한 메시지에 부족 권한 모두 보고 → 사용자는 token edit 1회로 끝**.

세부 코드 + 에러 해독 → `pr-merge-gate` 의 `references/github-fine-grained-token-permissions.md`.

## Autonomous Mode (사용자 의도: "알아서 해라")

사용자가 "알아서 해라 / 직접 관리해라 / 자율모드 / 위험한 것 제외 권한 줄 테니" 류 발언 시:
- **중간확인 X** — 끝까지 진행 후 한 번에 보고
- `[가정]/[결 결정]` 라벨로 자율 진행 후 사후 보고
- 외부 영향(push/PR/fork/delete/SMTP send)은 **사용자 명시 동의 없이 실행 금지**
- v1.3부터: `fix`/`email` stage는 default dry — 사용자가 안 켰다면 절대 push/send 안 됨
- 사용자가 좌절 시그널 보이면 즉시 OFF
- **token permission 부족만은 사용자에게 한 번에 권한 명시 보고** (= explicit user action 임)

**위험 분류 (체크리스트로 항상 검토)**:
| 위험 단계 | v1.3 default | 사용자 켜려면 |
|---|---|---|
| push new branch | ❌ dry | `DRY_RUN_FIX=0` |
| PR open | ❌ dry | `DRY_RUN_FIX=0` |
| SMTP send (himalaya) | ❌ dry | `DRY_RUN_EMAIL=0` |
| Linear issue create | ✅ mirror-only prod는 OK | `DRY_RUN_MIRROR=0` |
| Kanban task create | ✅ mirror-only prod는 OK | `DRY_RUN_MIRROR=0` |
| GitHub read (GET) | ✅ 항상 OK | `DRY_RUN_HARVEST=0` (read-only) |
| GitHub secret/PAT 변경 | ❌ 항상 dry (= manual confirm) | 자동화 불가 |

## Run

```bash
DRY_RUN=1 python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py

# mirror-only prod (가장 흔함)
DRY_RUN=0 DRY_RUN_FIX=1 DRY_RUN_EMAIL=1 DRY_RUN_HARVEST=0 \
  python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```

## Cron Registration (v1.3 검증된 2단 cron)

**dry-run + prod 둘 다 등록** (사용자 confirm 전 dry-run이 stage 통과 시 prod cron 가동):

```bash
# 1. Dry-run (default — 첫 cycle 검증용)
hermes cron create "0 22 * * *" \
  "Daily 07:00 KST daily-repo-orchestrator in DRY_RUN=1 mode ..." \
  --name "daily-repo-orchestrator-dryrun" \
  --deliver local

# 2. Mirror-only prod (스킬 autonomous mode 활성화 시)
hermes cron create "0 22 * * *" \
  "Daily 07:00 KST daily-repo-orchestrator mirror-only prod 모드 (harvest+mirror real, fix/email dry)..." \
  --name "daily-repo-orchestrator-mirror" \
  --script daily_repo_orchestrator_mirror.sh   # ~/.hermes/scripts/ 안의 wrapper script
  --deliver origin

# 3. Self-improvement / weekly (선택)
hermes cron create "0 12 * * 0" \
  "Weekly verdict pattern analysis (read-only)..." \
  --name "verdict-analyzer-weekly" \
  --script verdict_analyzer_weekly.sh \
  --deliver origin
```

**2026-07-07 실측 운영 cron ID**:
- `1f0e383caa82` daily-repo-orchestrator-dryrun (DRY_RUN=1, 단순 진단)
- `a79d072b2447` daily-repo-orchestrator-mirror (mirror-only prod)
- `1387af94df7d` verdict-analyzer-weekly (read-only, 매주 일)
- `4076b821ac31` memory-curator-weekly (read-only, 매주 월)

⚠️ **CLI 함정**: 옵션을 `--schedule \"...\"` 처럼 쓰면 `schedule` 인자가 positional을 흡수해서 에러. positional 순수히 `schedule [prompt]` 후 옵션.
⚠️ **`--script` 경로 함정**: 절대경로/홈-상대경로 (`/home/ubuntu/.hermes/scripts/x.sh`) 안 받음. **filename만** 전달 (`x.sh`). 스크립트는 `~/.hermes/scripts/` 안.
⚠️ **Python `DRY_RUN` env 파싱 함정 (added 2026-07-08, from `hermes_disk_hygiene.py`)**: `DRY_RUN = os.environ.get("DRY_RUN", "1") == "0"` 형태는 깨지기 쉬움 — (a) `.env` 에 `DRY_RUN=` (빈 문자열) 가 있으면 `"1" == "0"` False → 의도와 다른 production mode 로 진입, (b) bash `DRY_RUN=1 python3 foo.py` 호출 시 env 값은 `"1"` 인데 코드는 False, (c) 직관과 반대 매핑. **안전 패턴**:
```python
DRY_RUN = os.environ.get("DRY_RUN", "1") not in ("0", "false", "False", "")
# → env 미설정 / "1" / "true" / "" → True (dry safe)
# → env "0" 또는 "false" → False (production)
```
그리고 **로그 라벨에 절대 `DRY_RUN={int(DRY_RUN)}` 처럼 boolean 을 0/1 로 매핑하지 말 것** — 실측: DRY 모드에서 `int(True)` → 1 출력되어 "production 으로 보임" 착각 야기. 대신 `mode={'DRY' if DRY_RUN else 'PROD'}`. 전체 패턴 + 함정 + 적용 cron list → `references/python-dry-run-pattern.md`.

## Priority Matrix

| 라벨 | impact |
|---|---|
| `bug` | 4 |
| `security` | 5 |
| `auto-detected` | 3 |
| `feature` | 3 |
| `docs` | 2 |
| `enhancement` | 3 |
| `cleanup` | 2 |
| `good first issue` | 2 |

`score = (impact × certainty) / effort`
- certainty: 자동 검출 = 4, 그 외 = 3
- effort: 본문 길이 기반 `max(1, 5 - body_len // 200)`

## Mirror IDs

- Linear team: `shootingstock` key=`SHO`, team_id=`acb9037a-9a30-4848-bb13-cf72c95c13e8`
- Kanban board: `hermes` (default board; `hermes kanban create` 가 positional title 받음 — `--title` 옵션 없음)
- GitHub owner: `mybotagent`
- IMAP monitor target: `sanghee.lee2222@gmail.com` (**read-only**)

⚠️ **`hermes kanban create` 호출 패턴** (실측 idempotency 작업 중 발견):
- positional title만 받음, `--title` 옵션 없음
- stdout = `Created t_xxxxxxxx  (ready, assignee=-)` 형식
- ID 추출: `re.search(r"(t_[a-z0-9]+)", stdout)`
- list 옵션: `--json` (전체 dump), `--status {archived,blocked,done,ready,review,running,scheduled,todo,triage}` 중 1개만

## Environment

필수 `.env` 키:
- `GITHUB_TOKEN` (repo scope, fine-grained or classic) — **pre-flight에서 충분성 검증**
- `LINEAR_API_KEY` (Linear OAuth token)
- `GH_TOKEN_V2` (선택, fine-grained with Workflows R&W, workflows push 용)

선택:
- `HERMES_HOME` — `/home/ubuntu` 또는 `/home/ubuntu/.hermes` 둘 다 처리 (코드에서 분기)
- `REPORT_TO` — 미래 SMTP 확장 시 사용 (현재 read-only)

## ⚠️ GitHub Notification Policy (CRITICAL — 자동 검증 한계)

GitHub는 다음 경우 본인에게 알림 메일을 보내지 않습니다:
1. **자신이 만든 issue**에 본인이 watcher로 등록돼 있어도 발송 안 함
2. **본인이 reviewer/recipient loop 안에 있어도 동일**

⇒ 사용자가 "이슈 메일 검증해달라"고 해도, **본인 계정에 본인 issue면 자동 검증 불가능**. 외부 Collaborator 1계정 추가 또는 GitHub App bot identity 등록 필요.

**PR → Gmail 자동 검증 가능**: token owner가 만든 본인 PR이라도 *watcher 발사로* token owner Gmail에 도착 (실측 6건 inbox 수신 확인). `verify_pr_cycle(p) := pr_opened → himalaya inbox 조회 (from github, subject 매칭) → arrived_within_60s` 이면 pass.

자세한 transcript → `references/github-notification-policy.md`.

## Anti-patterns (DO NOT)

| ❌ Anti-pattern | ✅ Fix |
|---|---|
| **Skip pre-flight permission probe** | **5단계 probe 실행 후 부족 권한 모두 보고** |
| Push without dry-run first | DRY_RUN=1 default → 사용자 명령 후 0 |
| Hard-coded `/home/ubuntu/` | `HERMES_HOME` 동적 처리: `/home/ubuntu` 또는 `/home/ubuntu/.hermes` |
| Single error path stops all | per-stage try/except + log_event |
| **Gmail SMTP send on success** | **read-only IMAP monitor + stdout만 — 발송 ❌ (default DRY_RUN_EMAIL=1)** |
| **GitHub push/PR without explicit user OK** | **DRY_RUN_FIX=1 default — 사용자가 명시적으로 켜야 push** |
| **Assume GitHub email will reach owner for own issue** | **본인 → 본인 issue = 자동 메일 발사 안 됨** |
| **Ask mid-cycle "이렇게 할까요?"** | **autonomous mode: 끝까지 진행 후 사후 보고** |
| `--schedule \"...\"` in `hermes cron create` | positional `schedule [prompt]` 먼저, 옵션 뒤 |
| `--script /abs/path` in `hermes cron create` | filename only (relative to `~/.hermes/scripts/`) |
| `--status ready --status backlog` (kanban) | `--json` 한 번 + 직접 set lookup (반복 status 안 됨) |
| **`hermes kanban create --title ...`** (실측 — 옵션 없음) | `hermes kanban create <title> --body <body>` (positional) |
| **매일 cron이 같은 Linear issue 중복 생성** | **eqIgnoreCase filter 사전 검색 + reuse** |
| Silent fallback (random ID) | `log_event(\"...\", \"dry\", fake_id=fake)` 명시 |
| Production cron without user confirm | dry-run 1회 → 사용자 production 명령 후 등록 |
| Devolve to multiple bash + curls | 단일 Python 스크립트 1개로 종단간 |
| **"또 permission 하나 부족" 패턴 반복** | **한 번에 부족 권한 모두 명시** |
| **JSON.parse 없이 stdout 가공** | `re.search(...)` 또는 stdlib json.loads로 명시 추출 |
| **Idempotency 도입 전 누적된 SHO 중복 정리** | `issueArchive` mutation (close 대신 archive — 데이터 보존, 목록에서만 hidden) |
| **🆕 v1.4: 첫 cycle부터 `DRY_RUN=0` cron 등록** | **24~48h dry-run 누적 후 사용자 confirm → DRY_RUN=0** |
| **🆕 v1.4: `.env` / `*.token` / jobs.json (12MB) commit** | **config stage `.gitignore` 자동 생성, redaction 통과 후 push** |
| **🆕 v1.4: 사용자 confirm 없이 `--script` 로 prod push** | **dry-run 1회 실측 + cron 등록 + 24h dry + 사용자 한마디 → prod** |
| **🆕 v1.4: 4 sub-step 중 1개 fail이 전체 stop** | **`(...) || say "..."` 격리, set -uo pipefail (not -e)** |
| **🆕 v1.4: pull/drift-pull 추가** | **사용자 정책 "github은 기록용" — push only, 절대 pull ❌** |
| **🆕 v1.4: 기존 sync cron과 중복 등록** | **기존 cron 흡수 결정 후 delete (중복 cron = 단일공식 위반)** |
| **🆕 v1.4: 404 repo에 safe-skip 대신 hard-fail** | **safe-skip + stdout 메시지 ("사용자에게 1회만 생성 요청")** |
| **🆕 v1.4: bare clone 경로 hard-code** | **`$HERMES_HOME/.mirror/` 동적, env override 가능** |

## Examples

### dry-run cycle
```
$ DRY_RUN=1 python3 scripts/daily_repo_orchestrator.py
=== Hermes daily_repo_orchestrator.py | 2026-07-07 | DRY_RUN=True ===
[pre-flight] ✅ All 5 permissions OK
[harvest] scan n=14
[harvest] candidates n=3
[prioritize] score top=[...]
[mirror] linear-dry fake_id=SHO-851 ...
[fix] pr-dry title=fix: ...
MODE: DRY_RUN
  harvest=dry mirror=dry fix=dry email=dry
```

### mirror-only prod (autonomous mode)
```
$ DRY_RUN=0 DRY_RUN_FIX=1 DRY_RUN_EMAIL=1 DRY_RUN_HARVEST=0 \
  python3 scripts/daily_repo_orchestrator.py
=== Hermes daily_repo_orchestrator.py | 2026-07-07 | DRY_RUN=False ===
[harvest] scan n=30
[harvest] candidates n=7
[prioritize] score top=[...]
[mirror] linear-reuse id=SHO-49 key=mybotagent/hermes-wiki::...
[mirror] kanban-reuse title=[Auto 2026-07-07] ...
[fix] pr-dry ...
MODE: PRODUCTION
  harvest=real mirror=real fix=dry email=dry
```

### Pre-flight에서 권한 부족 시 (사용자 보고)
```
=== Pre-flight probe ===
  ❌ repository_access   (403 — token has no access to mybotagent/hermes-pr-gate)
  ❌ secrets_rw          (403 — Secrets permission 누락)

[사용자 액션 — 1분이면 끝]
  https://github.com/settings/tokens → gh_token Edit →
  1. Repository access: 'All repositories' 또는 mybotagent/* 추가
  2. Permissions → Repository permissions → 'Secrets': Read and write

  → 다시 실행하면 pre-flight 5단계 모두 pass.
```

### verify PR registered + email arrived (read-only chain)
```bash
# 1) PR 존재 확인
curl -s -H "Authorization: token $(grep ^GITHUB_TOKEN= ~/.hermes/.env | cut -d= -f2- | tr -d '\"')" \
  https://api.github.com/repos/<owner>/<repo>/pulls/<n>

# 2) GitHub /notifications 큐 (token owner의 수신 알림)
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/notifications

# 3) IMAP read-only — github 발신 메일만
himalaya envelope list -o json 'from github'
```

## 5-Stage Verify

- **why**: 매일 반복 작업 → 운영 신뢰도 하락 방지
- **what**: pre-flight probe + dry-run + production 양쪽 모두 stdout + log_event
- **whether**: 매트릭스 합리성 (impact 1~5, certainty 3~4, effort 1~5)
- **what**: 단일 공식 `pre-flight→harvest→prioritize→mirror→fix→verify`
- **how**: DRY_RUN env var + `--dry-run` CLI flag 이중 잠금 + STAGE별 분기 (`DRY_RUN_{HARVEST,MIRROR,FIX,EMAIL}`) + pre-flight 5단계 probe
- **validate**: `scripts/logs/daily-repo-YYYY-MM-DD.jsonl` 매일 누적 + IMAP 모니터 cross-check + 주간 자가개선 (`verdict-analyzer-weekly` cron)

## Related

- `bash-script-template` — cron wrapper script 패턴 (env wrapper + tee log + PIPESTATUS)
- `pr-merge-gate` — fix 단계의 merge gate + token permission probe
- `references/linear-kanban-idempotency.md` — 🆕 Linear/Kanban dedupe 코드 패턴 + 함정
- `references/stage-flags-and-modes.md` — 🆕 STAGE별 dry flag + mode preset 매트릭스
- `references/github-notification-policy.md` — 본인→본인 PR/issue 메일 발사 정책
- `references/config-sync-mode.md` — 🆕 v1.4 단방향 push sync 패턴 + mirror bare clone + 4 sub-step 책임 분리 + DRY-first 신규 cron 절차
- wiki `infra/daily-repo-orchestrator.md`
- https://github.com/mybotagent/skills (mirror repo)
- **Autonomous mode 신호 + 위험 분류** → `self-improvement-loop`

## Files

```
~/.hermes/skills/daily-repo-orchestrator/
├── SKILL.md
├── references/
│   ├── github-notification-policy.md
│   ├── linear-kanban-idempotency.md     🆕 v1.3
│   └── stage-flags-and-modes.md         🆕 v1.3
└── scripts/
    └── daily_repo_orchestrator.py       (v1.3: STAGE별 dry + idempotency)

# GitHub mirror:
# https://github.com/mybotagent/skills
#   daily-repo-orchestrator/SKILL.md
#   daily-repo-orchestrator/references/{github-notification-policy,linear-kanban-idempotency,stage-flags-and-modes}.md
#   daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```
