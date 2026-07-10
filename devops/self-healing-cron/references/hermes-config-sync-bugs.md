# `hermes_config_sync.sh` — 2 Critical Bugs (2026-07-09 발견+수정)

**발견일**: 2026-07-09 22:08 KST
**세션**: aiprofit "헤르메스 자율운영이 전혀 안되네 github 최근 변경이력이 17시간 전이야" 진단
**상태**: ✅ 2개 모두 fix + push 검증 완료 (2026-07-09 22:31 KST)

---

## TL;DR

`hermes_config_sync.sh` (cron `91059d1e3d31`, 매일 KST 22:30)가 17시간 동안 push 안 한 **진짜 원인 = 3가지 동시 발생**:

1. **DRY-first default** — `DRY_RUN=1` default라 push 안 함
2. **rsync가 stage의 `.git/` wipe** (Bug #1) — 첫 push만 성공, 그 후 영원히 SKIP
3. **config step이 `~/.hermes` 전체 rsync** (Bug #2) — 무한 재귀 + timeout

**수정 후**: push-first (DRY=0 default) + rsync에 `--exclude .git` 추가 + config step manual 빌드. 모든 4개 레포 `drift=0`.

---

## Bug #1 — rsync wipe of stage's `.git/`

### 코드 (before)

```bash
ensure_mirror_stage() {
  local label="$1" mirror="$2" stage="$3" src="$4" repo="$5"
  mkdir -p "$(dirname "$mirror")"
  if [ ! -d "$mirror" ]; then
    # git clone --bare → mirror
  fi
  if [ ! -d "$stage" ]; then
    # git clone mirror → stage (.git 생김)
  fi
  # rsync src → stage (--delete로 stage의 모든 게 src로 overwrite)
  rsync -a --delete \
    --exclude '.bundled_manifest' \
    --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.DS_Store' \
    "$src"/ "$stage"/
}
```

### 증상 timeline

| 실행 | stage 상태 | sync 결과 |
|---|---|---|
| 1회 (07-08 22:30) | `.git/` 살아있음 (clone이 막 생성) | push OK |
| 2회 (07-09 13:30) | rsync가 `.git/` 삭제 | sync_substep "is not a git repo" → SKIP |
| 3회 이후 | `.git/` 영구 부재 | 영원히 SKIP |

### Fix (코드)

```bash
rsync -a --delete \
  --exclude '.git' --exclude '.git/' --exclude '.git/**' \  # ← 3가지 추가
  --exclude '.bundled_manifest' \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$@" \
  "$src"/ "$stage"/
```

**3가지 exclude 추가 이유**:
- `.git` — bare name (rsync dir-traversal 안전)
- `.git/` — slash 접미 (디렉토리 명시)
- `.git/**` — 내부 모든 파일 (rsync 버전별 동작 차이 흡수)

**검증 (2026-07-09 22:31 KST)**:
```
wiki     : local=774fe69  remote=774fe69  ✓
skills   : local=449dd8d  remote=449dd8d  ✓
scripts  : local=007a542  remote=007a542  ✓
config   : local=64d6a3c  remote=64d6a3c  ✓
```

---

## Bug #2 — config step infinite recursion

### 코드 (before)

```bash
CONFIG_MIRROR_STAGE="${HERMES_HOME}/.mirror/config-stage"
code=$(gh_repo "mybotagent/hermes-config")
if [ "$code" = "200" ]; then
  ensure_mirror_stage "config" \
    "${HERMES_MIRROR:-${HERMES_HOME}/.mirror/config.git}" \
    "$CONFIG_MIRROR_STAGE" \
    "${HERMES_HOME}" \  # ← ❌ ~/.hermes 전체
    "mybotagent/hermes-config"
  # ... .gitignore 작성 + memory/cron cp + sync_substep
fi
```

### 증상 timeline (07-09 22:13 KST 직접 실행 시)

```
Cloning into 'config-stage'... done.
file has vanished: "/home/ubuntu/.hermes/.mirror/config-stage/README.md"
file has vanished: "/home/ubuntu/.hermes/.mirror/config-stage/.git/HEAD"
file has vanished: "/home/ubuntu/.hermes/.mirror/config-stage/.git/config"
... (30+ lines)
file has vanished: "/home/ubuntu/.hermes/.mirror/config-stage/.git/refs/remotes/origin/HEAD"
rsync error: received SIGINT, SIGTERM, or SIGHUP (code 20)
```

**왜 이런 일이?**:
1. `ensure_mirror_stage "config" ... "$HERMES_HOME" ...` → rsync `src=~/.hermes, dst=~/.hermes/.mirror/config-stage`
2. rsync가 `~/.hermes/wiki/`, `~/.hermes/skills/`, `~/.hermes/scripts/`, `~/.hermes/memories/`, `~/.hermes/.gitignore` 등을 stage에 복사
3. stage 자체가 `~/.hermes/.mirror/config-stage` 안에 있어서 자기 안에 `.mirror/...` 디렉토리 생김
4. `~/.hermes/.mirror` 도 stage에 들어감 → 무한 깊이
5. rsync가 working files 변경하다가 자기 자신을 지움 → "file has vanished"
6. 60초 timeout → `set -uo pipefail` 로 exit 124 (timeout)

**원인 (근본)**:
- `ensure_mirror_stage`는 `$src`를 그대로 rsync (per-label extras 지원 ❌)
- config의 src = `~/.hermes` 전체 → 자기 자신을 dst에 포함
- `.gitignore`로는 한계 (`.mirror/`, `wiki/`, `.git/` 등을 다 exclude 못 함 — rsync exclude와 gitignore는 별개)

### Fix — config step 전용 manual 빌드 (2026-07-09 적용)

```bash
CONFIG_MIRROR_STAGE="${HERMES_HOME}/.mirror/config-stage"
code=$(gh_repo "mybotagent/hermes-config")
if [ "$code" = "200" ]; then
  # ⚠️ config stage: ~/.hermes 전체 rsync → 무한 재귀
  # → HERMES_HOME을 src에 직접 넣지 말고, 선별된 파일만 stage에 직접 쓴다
  mkdir -p "$CONFIG_MIRROR_STAGE"
  if [ ! -d "$CONFIG_MIRROR_STAGE/.git" ]; then
    git clone "https://github.com/mybotagent/hermes-config.git" "$CONFIG_MIRROR_STAGE" >>"$LOG_FILE" 2>&1 || true
    (
      cd "$CONFIG_MIRROR_STAGE" 2>/dev/null || exit 0
      git checkout -B main 2>/dev/null || true
      git remote set-url origin "https://github.com/mybotagent/hermes-config.git" 2>/dev/null || \
        git remote add origin "https://github.com/mybotagent/hermes-config.git"
    )
  fi
  (
    cd "$CONFIG_MIRROR_STAGE"
    cat > .gitignore <<'GI'
# secrets — 절대 commit ❌
.env
*.token
*.pem
memories/memory-current.md

# noise
cron/output/
cron/jobs.json
cron/jobs.json.*
cron/ticker_*
cron/.*.lock

# local state (mirror 내부)
.mirror/
.git/
GI
    # cron 정의 (jobs.json 제외), memories → people/ memory-snapshot 추출, .env.example, config.yaml
    mkdir -p memories cron
    if [ -f "${HERMES_HOME}/memories/memory.md" ]; then
      cp "${HERMES_HOME}/memories/memory.md" memories/memory-current.md
      # secret line 제거
      sed -E -i 's/(api_key|token|secret)=[^[:space:]]*/\1=<REDACTED>/g' memories/memory-current.md
    fi
    # cron 정의 (jobs.json만 추출 메타: 이름/스케줄, 내용은 push ❌)
    python3 - <<'PY' 2>>"$LOG_FILE" || true
import json, os
p = os.path.expanduser("~/.hermes/cron/jobs.json")
out = os.path.expanduser("~/.hermes/.mirror/config-stage/cron/jobs.meta.json")
try:
    with open(p) as f: d = json.load(f)
    jobs = d.get('jobs', []) if isinstance(d, dict) else d
    meta = [
        {"name": j.get('name'), "schedule": j.get('schedule'),
         "script": j.get('script'), "enabled": j.get('enabled'),
         "no_agent": j.get('no_agent')}
        for j in jobs if isinstance(j, dict)
    ]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        json.dump({"count": len(meta), "jobs": meta}, f, indent=2, ensure_ascii=False)
except Exception as e:
    print('jobs.meta.json skip:', e)
PY
    [ -f "${HERMES_HOME}/config.yaml" ] && cp "${HERMES_HOME}/config.yaml" .
    if [ -f "${HERMES_HOME}/.env" ]; then
      awk -F= '/^[A-Z_]+=/{print $1"="}' "${HERMES_HOME}/.env" > .env.example 2>/dev/null || true
    fi
  ) >>"$LOG_FILE" 2>&1
  sync_substep "config-stage" "$CONFIG_MIRROR_STAGE" "mybotagent/hermes-config" "main"
else
  say "  SKIP (404): mybotagent/hermes-config — record only."
fi
```

**핵심 변경**:
- `ensure_mirror_stage` 호출 ❌ → manual git clone + 선별 cp
- rsync ❌ (Bug #2) → 직접 `cp` 4개
- `.gitignore` 강화 (`.mirror/`, `.git/`, `memories/memory-current.md` 등)

---

## DRY-first → push-first rule 변경

### 변경 전
```bash
: "${DRY_RUN:=1}"            # default dry; cron은 env에서 명시적으로 0 set 가능
```

### 변경 후
```bash
# push-first (사용자 2026-07-09 결정):
#   DRY_RUN=0이 default. cron이 push까지 끝냄. 사용자가 DRY_RUN=1 env로
#   1회 preview만 가능. (rule: github은 기록용, push는 자동)
: "${DRY_RUN:=0}"            # default push (2026-07-09 rule)
```

**header 주석**:
```bash
# push-first (사용자 2026-07-09 결정 — "자율운영 안 됨" 진단 후):
#   DRY_RUN=0이 default. cron이 push까지 끝냄. 사용자가 DRY_RUN=1 env로
#   1회 preview만 가능. (rule: github은 기록용, push는 자동)
# 404 sub-step: repo 없으면 그대로 skip (다음 sync 때 자동 retry).
```

---

## 검증 7단계 (2026-07-09 22:31 KST)

```bash
# 1) dry-run (DRY=1) — diff만 확인
DRY_RUN=1 timeout 50 bash ~/.hermes/scripts/hermes_config_sync.sh 2>&1 | tail -25
# → wiki: no changes, skills: would commit 25, scripts: would commit 45, config: no changes

# 2) push (DRY=0 default) — 실제 push
timeout 50 bash ~/.hermes/scripts/hermes_config_sync.sh 2>&1 | tail -10
# → 4개 레모 모두 PUSHED 또는 no local changes

# 3) drift 확인
grep 'drift\|local=\|remote=' ~/.hermes/cron/output/hermes-config-sync-*.log | tail -10
# → wiki: local=774fe69 remote=774fe69 / skills: local=449dd8d remote=449dd8d
# → scripts: local=007a542 remote=007a542 / config: local=64d6a3c remote=64d6a3c

# 4) GitHub API로 각 레포 직접 확인
TOK=$(grep ^GITHUB_TOKEN= ~/.hermes/.env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
for r in hermes-wiki hermes-skills hermes-scripts hermes-config; do
  curl -s --max-time 5 -H "Authorization: token $TOK" "https://api.github.com/repos/mybotagent/$r/commits?per_page=1" | head -c 200
  echo
done
# → 4개 모두 200 + SHA 일치
```

**결과**: 4개 레포 모두 17시간 gap → 즉시 sync. 다음 cron (KST 22:30 = 13:30 UTC) 부터 매일 자동 push.

---

## 운영 rule (2026-07-09 영구 HARD RULE)

- **`DRY_RUN` default = 0 (push-first)** — cron이 push까지 끝냄
- **`DRY_RUN=1`은 사용자가 명시 요청한 1회 preview에만** — `bash ~/.hermes/scripts/hermes_config_sync.sh` (env 없이 실행 = push)
- **github은 기록용** — push는 자동, 사용자가 끄려면 cron 자체를 pause
- **sub-step 4개 모두 push 또는 skip** (wiki + skills-stage + scripts-stage + config-stage). memories/cron stage는 사용자 archive 결정으로 영구 미사용

---

## 진단 reference (mirror sync 안 될 때 즉시 적용)

```bash
# 1) stage 상태 — .git/ 부재 = Bug #1
ls -la ~/.hermes/.mirror/{wiki,skills,scripts,config}-stage/.git 2>&1 | head -10

# 2) sync log 최근 — Bug #1 = "is not a git repo" / Bug #2 = "file has vanished" + "rsync SIGINT"
tail -50 ~/.hermes/cron/output/hermes-config-sync-*.log

# 3) drift 확인
grep -A 6 'drift check' ~/.hermes/cron/output/hermes-config-sync-*.log | tail -10

# 4) GitHub last commit 시각 확인
TOK=$(grep ^GITHUB_TOKEN= ~/.hermes/.env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
for r in hermes-wiki hermes-skills hermes-scripts hermes-config; do
  curl -s --max-time 5 -H "Authorization: token $TOK" "https://api.github.com/repos/mybotagent/$r/commits?per_page=1" | head -c 200
  echo
done
```

---

## 변경 이력

- **2026-07-09 (v1)**: Bug #1 + Bug #2 발견 + fix + push-first rule 전환 + 검증. cron `91059d1e3d31` 이름 `(KST 22:30, DRY-first)` → `🔄 hermes-config-sync (KST 22:30, push-first)` 변경.
- **2026-07-09 (v1.1)**: 사용자 archive 결정으로 `mybotagent/hermes-memories` + `mybotagent/hermes-cron` 영구 미사용. 4+2 매니페스트 확립.
