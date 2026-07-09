---
tags: [config-sync, push-only, mirror-bare-clone, dry-first, cron, github]
related: [../SKILL.md]
---

# Config Sync Mode — 단방향 Push-Only Mirror Reference

> 출처: 2026-07-07 aiprofit Discord — "매일 헤르메스 설정(memory, cron, code 등)이 github 내용과 동기화. cron으로. 기존 작업 통합."
> 디자인 + 검증 완료. cron `91059d1e3d31` (KST 22:30, no_agent, DRY=1 default).
> 사용자 정책: **"github은 기록용"** = push only, 절대 pull/drift-pull ❌.

## 1. 단일공식 (Canonical Pattern)

```
[trigger] 매일 KST 22:30 (no_agent cron)
    ↓
[env load] HERMES_HOME=/home/ubuntu/.hermes + .env (GITHUB_TOKEN)
    ↓
[pre-flight] 4 repo HTTP HEAD probe (200/404/403/401)
    ↓
[4 sub-steps, try/catch isolated]
    ① wiki       → existing origin  → add+commit+push (DRY=0) or numstat preview (DRY=1)
    ② skills     → mirror bare clone → same
    ③ scripts    → mirror bare clone → same
    ④ config     → mirror bare clone → jobs.meta.json + .env.example + memory.md(reducted)
    ↓
[drift check] local HEAD vs origin/main (record only, blocking ❌)
    ↓
[로그]  ~/.hermes/cron/output/hermes-config-sync-YYYY-MM-DD-HHMMSS-UTC.log
```

## 2. Mirror Bare Clone 패턴 (CRITICAL)

**문제**: `~/.hermes/skills/`, `~/.hermes/scripts/` 등은 git repo가 아님. GitHub에 push하려면 mirror 구조 필요.

**해결**: bare repo + working tree 분리.

```
~/.hermes/.mirror/
├── skills.git/         ← bare repo (origin 역할, --bare clone)
└── skills-stage/       ← working tree (rsync로 src 복제)
```

### Bash 함수 (실측 검증 2026-07-07)

```bash
ensure_mirror_stage() {
  local label="$1" mirror="$2" stage="$3" src="$4" repo="$5"
  mkdir -p "$(dirname "$mirror")"

  if [ ! -d "$mirror" ]; then
    local code; code=$(gh_repo "$repo")
    if [ "$code" = "200" ]; then
      git clone --bare "https://github.com/${repo}.git" "$mirror" || {
        echo "clone fail → bare init"; git init --bare "$mirror"
      }
    else
      echo "remote unreachable ($code) → bare init locally"
      git init --bare "$mirror"
    fi
  fi

  if [ ! -d "$stage" ]; then
    git clone "$mirror" "$stage"
    (
      cd "$stage" 2>/dev/null
      git checkout -B main 2>/dev/null || true
      git remote set-url origin "https://github.com/${repo}.git" 2>/dev/null \
        || git remote add origin "https://github.com/${repo}.git"
    )
  fi

  rsync -a --delete \
    --exclude '.bundled_manifest' \
    --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.DS_Store' \
    "$src"/ "$stage/"
}
```

### ⚠️ 함정 (실측)

- **`$stage/.git` 없으면** clone 실패 → mirror에서 clone 1회 fallback. 그 다음에도 working tree 빈 상태 → `git checkout -B main` 필수.
- **`git diff --quiet HEAD`** 는 untracked file은 detect 못 함 → `git add -A` 로 staged 후 `git diff --cached --quiet` 사용.
- **rsync `--delete`** 는 stage에 있지만 src에 없는 파일 제거. **mirror bare가 비어있을 때 첫 실행이면 stage가 통째로 지워질 위험** → 첫 실행 전 `git clone` 결과 확인 필요.
- **`.bundled_manifest`** 는 hermes가 만든 lock 파일 (skill version snapshot) — push ❌.
- **`__pycache__`, `*.pyc`** 는 hermes plugins/skill runtime이 만듦 — exclude 필수.

## 3. 4 Sub-step 책임 분리 + 실측 결과 (2026-07-07 16:10 UTC)

| # | sub-step | local path | target repo | 16:10 UTC 결과 |
|---|---|---|---|---|
| ① | wiki | `~/.hermes/wiki` | mybotagent/hermes-wiki | ✅ 200 OK, 1 file dirty (logs submodule), DRY preview stdout |
| ② | skills | `~/.hermes/skills/` | mybotagent/hermes-skills | ⚠️ 404 — safe-skip + "사용자에게 1회만 생성 요청" |
| ③ | scripts | `~/.hermes/scripts/` | mybotagent/hermes-scripts | ⚠️ 404 — safe-skip |
| ④ | config | `~/.hermes/{cron/,memories/,config.yaml,.env.example}` | mybotagent/hermes-config | ⚠️ 404 — safe-skip |

**총 소요**: ~1초 (no-agent cron에 적합). 실패 격리 완벽 — ②③④의 404가 ①을 막지 않음.

## 4. HTTP Status Code별 행동 (CRITICAL 매트릭스)

| HTTP | 의미 | 행동 |
|---|---|---|
| **200** | repo 존재 | mirror init → commit/push (DRY=0) or numstat preview (DRY=1) |
| **404** | repo 없음 | **safe-skip + stdout 메시지** ("사용자에게 1회만 생성 요청") |
| **401** | token 없음/expired | **safe-skip + stdout 메시지** ("GITHUB_TOKEN missing or invalid") |
| **403** | token 권한 부족 | **safe-skip + stdout 메시지** ("token lacks access to $repo") |
| **000** | 네트워크 오류 | **safe-skip + stderr 로그** |

→ 절대 hard-fail 금지. 한 sub-step의 외부 의존성이 다른 sub-step 막으면 안 됨 (단일공식).

## 5. Secret Safety (CRITICAL)

### .gitignore 자동 생성 (config stage)

```gitignore
# secrets — 절대 commit ❌
.env
*.token
*.pem
memories/*.md

# noise
cron/output/
cron/jobs.json
cron/jobs.json.*
cron/output/*
cron/ticker_*
cron/.*.lock
```

### Redaction 패턴 (memory.md → memory-current.md)

```bash
sed -E -i 's/(api_key|token|secret)=[^[:space:]]*/\1=<REDACTED>/g' \
  memories/memory-current.md
```

### jobs.json (12MB) → jobs.meta.json 변환 (cron 정의만 푸시)

```python
import json, os
p = os.path.expanduser("~/.hermes/cron/jobs.json")
out = os.path.expanduser("~/.hermes/.mirror/config-stage/cron/jobs.meta.json")
with open(p) as f: d = json.load(f)
jobs = d.get('jobs', []) if isinstance(d, dict) else d
meta = [
    {"name": j.get('name'), "schedule": j.get('schedule'),
     "script": j.get('script'), "enabled": j.get('enabled'),
     "no_agent": j.get('no_agent')}
    for j in jobs if isinstance(j, dict)
]
with open(out, 'w') as f:
    json.dump({"count": len(meta), "jobs": meta}, f, indent=2, ensure_ascii=False)
```

→ job 본문(prompt)은 push ❌, 메타(이름/스케줄/script)만 푸시.

## 6. DRY-first 신규 cron 등록 절차 (사용자 정책 강화)

### 7-Step 절차

1. **DESIGN.md 작성** — 단일공식 + DRY-first + 사용자 정책 명시
2. **스크립트 작성** + `bash -n` syntax check
3. **`DRY_RUN=1` 로 1회 수동 실행** → 4 sub-step stdout 확인 (실측 1초 내)
4. **no_agent cron 등록** — `hermes cron create "<schedule>" "<prompt>" --name "<name>" --script <filename> --deliver origin`
   - ⚠️ `filename` only (절대 ❌ `/abs/path`)
5. **24~48h dry cycle 누적** — 실제 push 0, stdout만 발송
6. **사용자 "prod 켜" 1마디** → `DRY_RUN=0` 으로 cron update
7. **wiki 기록 + log push** (index update + index.md 등록)

### 절대 안 되는 것

- ❌ 첫 cycle부터 `DRY_RUN=0` 으로 cron 등록
- ❌ 사용자 confirm 없이 `--script` 로 prod push
- ❌ dry-run stdout 누적 없이 prod 전환
- ❌ push 대상 repo 404를 hard-fail로 처리

## 7. 기존 cron 흡수 패턴 (사용자 정책 "기존 작업 통합")

### 결정 매트릭스

| 기존 cron | 흡수 여부 | 이유 |
|---|---|---|
| **wiki-auto-refresh** (537dfbb83b81) 21:00 KST | ✅ 흡수 | 동일 scope (wiki push), 본 cron ① sub-step이 동일 역할. **다음 cycle 사용자 confirm 후 delete** |
| **sync_survey_repo.sh** (fe96a2422b91) 11:00 KST | ❌ 제외 | survey는 별개 외부 도메인 (`~/daily-survey` 레포) — 본 cron 책임 아님 |
| **daily-repo-orchestrator-mirror** (a79d072b2447) 22:00 KST | ❌ 제외 | 레포 진단 + Linear mirror — 진단 vs 단순 sync는 책임 분리 |
| **(없음) memory_sync.sh 자동 cron** | ✅ 신설 | sub-step ④ config에 흡수 (audit OE5 해결) |

**단일공식**: integration = add (`wiki-auto-refresh` → ①로 흡수, **delete**) 만. 중복 cron 생성 ❌.

## 8. CLI 함정 (재확인 — v1.3과 동일)

| ❌ Anti-pattern | ✅ Fix |
|---|---|
| `--schedule \"...\"` in `hermes cron create` | positional `schedule [prompt]` 먼저, 옵션 뒤 |
| `--script /abs/path` in `hermes cron create` | filename only (relative to `~/.hermes/scripts/`) |
| `set -euo pipefail` in sub-step wrapper | `set -uo pipefail` (not -e) + `\|\| true` 격리 |

## 9. Self-Healing 다음 cycle 액션 (사용자 confirm 대기)

1. **GitHub 레포 3개 생성**: `mybotagent/hermes-skills`, `mybotagent/hermes-scripts`, `mybotagent/hermes-config` (private 권장)
   - 생성 후 자동으로 sub-step ②③④ push 작동 (mirror bare clone 1회 init)
2. **`wiki-auto-refresh` (537dfbb83b81) cron 삭제** (단일공식)
3. **24~48h dry 통과 후 "prod 켜" 1마디** → `DRY_RUN=0` prod 모드

## 10. 템플릿 — 신규 sync cron 등록 시 그대로 재활용

```bash
#!/usr/bin/env bash
# ~/.hermes/scripts/<name>_sync.sh
set -uo pipefail  # not -e: sub-step 격리

: "${HERMES_HOME:=/home/ubuntu/.hermes}"
: "${HOME:=/home/ubuntu}"
: "${DRY_RUN:=1}"  # default dry; cron은 env에서 명시적으로 0 set

LOG_DIR="${HERMES_HOME}/cron/output"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/<name>-$(date -u +%Y%m%d-%H%M%S)-UTC.log"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "[$(ts)] $*" | tee -a "$LOG_FILE"; }

say "===== <name> START (DRY_RUN=$DRY_RUN) ====="

# pre-flight
TOKEN=$(grep ^GITHUB_TOKEN= "${HERMES_HOME}/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
[ -z "${TOKEN:-}" ] && { DRY_RUN=1; say "TOKEN missing — DRY only"; }

gh_repo() {
  curl -sS -o /dev/null -w "%{http_code}" \
    -H "Authorization: token ${TOKEN:-nopentoken}" \
    "https://api.github.com/repos/$1"
}

# sub-step wrapper (failure-isolated)
sync_substep() {
  local label="$1" path="$2" repo="$3" branch="${4:-main}"
  [ ! -d "$path/.git" ] && { say "SKIP: $path not git"; return 0; }
  local code; code=$(gh_repo "$repo")
  case "$code" in
    200) ;;  # proceed
    404) say "SKIP (404): $repo — 사용자 생성 필요"; return 0 ;;
    *)    say "SKIP ($code): $repo"; return 0 ;;
  esac

  (
    cd "$path"
    git fetch origin "$branch" 2>>"$LOG_FILE" || true
    git add -A
    git diff --cached --quiet && { say "no changes"; exit 0; }

    if [ "$DRY_RUN" = "1" ]; then
      local n=$(git diff --cached --numstat | wc -l)
      say "DRY: would commit $n file(s) → $repo"
      exit 0
    fi

    git -c user.name="hermes-config-sync[bot]" \
        -c user.email="hermes-config-sync@users.noreply.github.com" \
        commit -m "<name>: $(ts) ($label)" >>"$LOG_FILE" 2>&1
    git push origin "$branch" 2>&1 | tee -a "$LOG_FILE"
    say "PUSHED → $repo@$branch"
  ) || say "sub-step '$label' failed (isolated)"
  return 0
}

# ... sub-step 호출 ...
sync_substep "wiki" "${HERMES_HOME}/wiki" "mybotagent/hermes-wiki"

say "===== END ====="
echo "<name> done — DRY=$DRY_RUN log=$LOG_FILE"
```

→ 이 템플릿은 다음에 다른 sync cron 만들 때 그대로 복사 + 변수만 교체.