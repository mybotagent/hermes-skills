# hermes-config-sync 운영 패턴 (2026-07-09 자가진단 → fix → 문서화)

> `~/.hermes/scripts/hermes_config_sync.sh`로 GitHub 레포(`hermes-wiki` / `hermes-skills` / `hermes-scripts` / `hermes-config`)에 단방향 mirror하는 운영의 **함정·패턴·결정 기록**.
> 작성: 2026-07-09 aiprofit "자율운영 안됨" 진단 세션.

## 🎯 단일공식 (user rule, 2026-07-09 확정)

```
DRY-first (DRY_RUN=1 default) ❌  →  push-first (DRY_RUN=0 default) ✅
```

**이유**: 사용자가 "github은 기록용"이라 명시 → **기록 = 자동 push**. DRY-first는 "실행은 됐지만 push 안 됨" 형태로 **silent fail**. 17시간 동안 0 push = self-healing agent가 paused였기 때문.

**rule 영구화**: `~/.hermes/scripts/hermes_config_sync.sh` 헤더에 2026-07-09 결정 주석 박아둠. 1회 preview만 필요하면 `DRY_RUN=1 bash ~/.hermes/scripts/hermes_config_sync.sh`.

## 🚨 5가지 자가진단에서 발견된 함정

### 1. DRY-first silent fail (가장 위험)

**증상**: cron이 매일 KST 22:30에 실행은 됨, log에는 "DRY: would commit 45 file(s)" 출력, **실제 push는 0**. 17시간 무push. Self-healing agent 없어서 nobody noticed.

**root cause**:
```bash
: "${DRY_RUN:=1}"  # ← default
...
if [ "$DRY_RUN" = "1" ]; then
  say "  DRY: would commit $n file(s) → $github_repo"
  exit 0
fi
```

**fix**:
```bash
: "${DRY_RUN:=0}"  # 2026-07-09 user rule: push-first
```

**판단 신호**: cron log는 정상인데 GitHub에는 변화가 없을 때 → DRY-first 의심. **첫 번째로 확인할 것**.

### 2. `ensure_mirror_stage` rsync가 자기 stage의 `.git/`을 wipe

**증상**: stage 폴더는 rsync 결과물로 채워지는데 `.git` 폴더가 없어서 "is not a git repo" 에러 → 모든 sub-step SKIP.

**root cause**:
```bash
rsync -a --delete \
  --exclude '.bundled_manifest' \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$src"/ "$stage"/
```

`rsync --delete`는 stage에 있지만 src에는 없는 모든 것을 삭제. **stage의 `.git/`은 src에 없으므로 매번 wipe**.

**fix**:
```bash
rsync -a --delete \
  --exclude '.git' --exclude '.git/' --exclude '.git/**' \  # ← 추가
  --exclude '.bundled_manifest' \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.DS_Store' \
  ...
```

**판단 신호**: stage 폴더에 rsync 결과물은 있는데 `.git/`이 없을 때 (sub-step "is not a git repo" 에러) → 이 bug 의심.

### 3. config step의 무한 재귀

**증상**: timeout 60s. log에 "file has vanished" 메시지 수십 개.

**root cause**:
```bash
ensure_mirror_stage "config" ... "${HERMES_HOME}" ...
# ↑ ~/.hermes 전체를 src에 넣음
```

`~/.hermes` 안에 `.git/`, `.mirror/`, `wiki/`가 있고 rsync stage도 `~/.hermes/.mirror/config-stage/`라 **자기 자신을 stage로 복사 → 무한 재귀 → timeout**.

**fix**: `ensure_mirror_stage` 호출 안 함. config는 **선별 파일만 수동 cp**:
```bash
(
  cd "$CONFIG_MIRROR_STAGE"
  cat > .gitignore <<'GI'
.env
*.token
*.pem
memories/memory-current.md
.mirror/
.git/
GI
  # memory.md를 redact 후 복사
  cp "${HERMES_HOME}/memories/memory.md" memories/memory-current.md
  sed -E -i 's/(api_key|token|secret)=[^[:space:]]*/\1=<REDACTED>/g' memories/memory-current.md
  # jobs.json 메타 추출 (prompt/delivery/job_id/last_run 제외)
  python3 -c "..."  # jobs.meta.json
  # config.yaml + .env.example 복사
)
```

**판단 신호**: sync가 60s+ timeout + "file has vanished" 반복 → 이 bug 의심.

### 4. `jobs.meta.json` schema (민감정보 제외)

**포함**: name, schedule (kind/expr/display), script, enabled, no_agent
**제외** (push 안 함): prompt (secret 위험), delivery, job_id, last_run, next_run, status, toolsets, paused_at, last_delivery_error

**이유**: prompt에 Discord thread ID나 secret line 포함 가능. **defense in depth** — prompt 전체를 redact 안 하고 jobs.json 메타만 추출.

**검증 recipe**:
```bash
cat ~/.hermes/.mirror/config-stage/cron/jobs.meta.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'prompt' not in d['jobs'][0], 'prompt leaked!'
assert 'delivery' not in d['jobs'][0], 'delivery leaked!'
print('OK — no leaks')
"
```

### 5. PAT scope 부족으로 delete/archive 실패

**증상**: `curl -X DELETE https://api.github.com/repos/mybotagent/<repo>` → 403 "Must have admin rights to Repository."

**해결책 없음 (사용자 영역)**:
- 신규 생성한 `hermes-cron` / `hermes-memories`는 **빈 Initial commit만** 있어서 데이터 손실 없음
- 사용자가 GitHub UI에서 직접 Archive/Delete 진행 필요
- **PAT scope가 admin이어도 cron 자동화에 force push는 user rule상 절대 ❌**

## 🎯 사용자 결정: "운영이 어려우면 불필요한 레포 삭제하도록" (2026-07-09)

5+2 → 4개로 축소 결정:

| 유지 | 삭제 |
|:---|:---|
| hermes-wiki (wiki 본체) | hermes-cron (jobs.json 풀 정의 — prompt secret 위험) |
| hermes-skills (SKILL.md 백업) | hermes-memories (memory.md — wiki에 통합) |
| hermes-scripts (운영 스크립트) | |
| hermes-config (config + jobs 메타) | |

**판단 기준 (사용자 명시)**: "github은 기록용" → **기록 가치 있는 것만**. 운영 cron 정의는 `cron/jobs.meta.json` + 위키 `infra/cron-jobs.md`로 이미 충분히 기록됨. jobs.json 풀 버전은 prompt secret 위험 + jobs.meta.json이면 80% 정보 커버.

**처리 절차 (PAT scope 부족으로 반쯤 자동화)**:
1. local mirror stage 폴더 없음 확인 (없으면 정리할 것 ❌) → `ls ~/.hermes/.mirror/`
2. GitHub repo DELETE 시도 → 403 (admin rights 없음)
3. **사용자가 직접 GitHub UI에서 Archive/Delete** (force push user rule상 자동화 ❌)
4. sync 스크립트 수정 ❌ (sub-step에 cron/memories 없었음)

## 🔍 진단 recipe (다음 세션용)

```bash
# 1. last sync 시점
ls -t ~/.hermes/cron/output/hermes-config-sync-*.log | head -1 | xargs tail -20

# 2. DRY_FIRST or PUSH_FIRST 확인
grep "DRY_RUN=" ~/.hermes/scripts/hermes_config_sync.sh | head -3

# 3. repo 4개 + 2개 = 6개 중 4개만 살아있는지 확인
TOK=$(grep ^GITHUB_TOKEN= ~/.hermes/.env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
for r in hermes-wiki hermes-skills hermes-scripts hermes-config hermes-cron hermes-memories; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOK" https://api.github.com/repos/mybotagent/$r)
  echo "$r: $code"
done

# 4. dry-run (1회 preview)
DRY_RUN=1 bash ~/.hermes/scripts/hermes_config_sync.sh

# 5. 실제 push
bash ~/.hermes/scripts/hermes_config_sync.sh
```

## 📊 진실: hermes-config-sync 정상 운영 확인 (2026-07-09 11:08 UTC)

| 레포 | local SHA | remote SHA | drift |
|:---|:---|:---|:---:|
| hermes-wiki | 774fe6921e1adf8c371e8716cbb22426b2291ab6 | 774fe6921e1adf8c371e8716cbb22426b2291ab6 | 0 ✓ |
| hermes-skills | 449dd8d7f338e2fbce4845f487964b5986292ea1 | 449dd8d7f338e2fbce4845f487964b5986292ea1 | 0 ✓ |
| hermes-scripts | 007a5422a56277117e84e363c903bb2fa5439b78 | 007a5422a56277117e84e363c903bb2fa5439b78 | 0 ✓ |
| hermes-config | 64d6a3c848803e90b135095769fbba024d5f0c59 | 64d6a3c848803e90b135095769fbba024d5f0c59 | 0 ✓ |

**4개 레포 모두 sync 정상, drift 0**. 다음 자동 sync는 KST 22:30 (UTC 13:30).
