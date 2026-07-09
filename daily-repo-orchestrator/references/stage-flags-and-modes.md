# STAGE별 Dry Flags & Mode Presets (v1.3 — 2026-07-07)

`daily_repo_orchestrator.py` v1.3에서 도입된 4-단계 dry flag 시스템 + 검증된 운영 모드 preset.

## ⚠️ 왜 binary DRY_RUN이 부족했나

v1.2까지는 `DRY_RUN=1` / `DRY_RUN=0` 의 단순 binary 였음:

| 단계 | 위험도 | v1.2 default |
|---|---|---|
| `harvest` (GitHub GET) | 0 (read-only) | DRY_RUN 따라감 |
| `mirror` (Linear/Kanban create) | 중 (외부 시스템 mutation) | DRY_RUN 따라감 |
| `fix` (clone + push + PR open) | 높 (코드 push) | DRY_RUN 따라감 |
| `email` (himalaya send) | 중-높 (SMTP 발송) | DRY_RUN 따라감 |

→ "mirror 단계는 켜고 fix는 dry" 같은 partial 운영이 불가능. v1.3에서 4개 stage 각각 분리.

---

## Env var 매트릭스

| env var | default 값 | stage별 영향 |
|---|---|---|
| `DRY_RUN` | `1` | master switch. `1` 이면 4 sub-flag 모두 dry. `0` 이면 sub-flag들이 각각의 default 로 fall through |
| `DRY_RUN_HARVEST` | DRY_RUN if `--dry-run` | `harvest_repos()` / `harvest_candidates()` 안의 GitHub GET. dry-skip으로 empty list |
| `DRY_RUN_MIRROR` | DRY_RUN | Linear `issueCreate` + Kanban CLI create. dry면 stdout에만 fake_id |
| `DRY_RUN_FIX` | DRY_RUN | git clone + patch + push + `gh pr create`. dry면 branch name only |
| `DRY_RUN_EMAIL` | DRY_RUN | `himalaya message send`. dry면 `log_event('report', 'dry-skip-email')` |

**Backward compat**: 아무것도 안 set하면 v1.2와 동일하게 `DRY_RUN=1` default dry.

**Sub-flag precedence**: `DRY_RUN_{stage}=0` 으로 명시한 건 `DRY_RUN` 보다 우선.

```bash
# v1.2 호환
DRY_RUN=1 python3 daily_repo_orchestrator.py     # all dry

# v1.3 partial: harvest/mirror real, fix/email dry
DRY_RUN=0 DRY_RUN_FIX=1 DRY_RUN_EMAIL=1 python3 daily_repo_orchestrator.py

# v1.3 full prod (사용자 confirm 후만)
DRY_RUN=0 python3 daily_repo_orchestrator.py

# v1.3 harvest-only 진단 (Linear/Kanban 안 건드림)
DRY_RUN=0 DRY_RUN_MIRROR=1 DRY_RUN_FIX=1 DRY_RUN_EMAIL=1 python3 daily_repo_orchestrator.py
```

---

## Mode Presets (실전 운영 패턴)

### Preset A — **Dry-Run (초기 / 사용자 confirm 전)**

```bash
DRY_RUN=1 python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```

- 모든 stage stdout-only
- cycle 로그: `~/.hermes/scripts/logs/daily-repo-YYYY-MM-DD.jsonl`
- cron job: `1f0e383caa82` (dry-run mode) — 매일 1회
- 산출: candidates + fake_ids + (would-be) branches

### Preset B — **Mirror-Only Prod (자율 운영 권장)**

```bash
DRY_RUN=0 \
DRY_RUN_HARVEST=0 \
DRY_RUN_MIRROR=0 \
DRY_RUN_FIX=1 \
DRY_RUN_EMAIL=1 \
python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```

- harvest (GitHub GET), mirror (Linear + Kanban) 실제
- fix (push/PR), email (SMTP) dry
- cron job: `a79d072b2447` (mirror-only) — 매일 1회, 22:00 UTC
- **권장 운영 모드** (autonomous mode default)
- 사용자 선언 ("위험한 것 제외 모든 권한 줌") 시 권장 — 사용자가 명시적으로 fix=0 안 켰다면 push 안 됨

### Preset C — **Full Prod (사용자 명시 confirm 후만)**

```bash
DRY_RUN=0 python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```

- 모든 stage 실제
- 이메일 발송됨 → 절대 사용자 confirm 전 운영 모드로 등록 금지
- 사용자의 1회성 명령 (`DRY_RUN=0 python3 ...`) 으로만 실행

### Preset D — **Harvest-Only 진단**

```bash
DRY_RUN=0 \
DRY_RUN_HARVEST=0 \
DRY_RUN_MIRROR=1 \
DRY_RUN_FIX=1 \
DRY_RUN_EMAIL=1 \
python3 ~/.hermes/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py
```

- GitHub GET만. Linear/Kanban/fix/email 모두 dry
- 주간/월간 diagnostic 에 사용. cron 안 등록. manual run

---

## Autonomous Mode vs Mode Preset 의 차이

- **Autonomous mode**: Herm 사용자 프롬프트 신호 ("알아서 해라" / "위험한 것 제외 권한 줌"). 어떻게 동작할지 의사결정 패턴.
- **Mode preset**: env var 조합. 무엇을 켜고 끌지.

Autonomous mode 신호 받으면 → **자동으로 Mode B (mirror-only prod) 선택**. 사용자가 별도 명령 안 해도 cron 안에는 권장 모드가 박혀있음.

→ **mirror-only prod cron이 default 등록**되고, full prod cron은 **사용자 명령으로만** (`hermes cron update` 등) 추가로 등록.

---

## Cron 등록 패턴 (v1.3 이후 검증)

### Wrapper script 방식 (권장)

`hermes cron create` 의 `--script` 옵션은 **`~/.hermes/scripts/` 안의 filename 만** 받음. 절대 경로 (`/home/ubuntu/.hermes/scripts/...`) 안 됨.

```bash
cat > ~/.hermes/scripts/daily_repo_orchestrator_mirror.sh << 'EOF'
#!/bin/bash
set -uo pipefail                              # set -e 빼기: stage별 실패 한 줄씩 stderr에 남김
if [ -f "${HOME:-/home/ubuntu}/.hermes/.env" ]; then
    set -a; source "${HOME:-/home/ubuntu}/.hermes/.env"; set +a
elif [ -f "${HOME:-/home/ubuntu}/.env" ]; then
    set -a; source "${HOME:-/home/ubuntu}/.env"; set +a
fi
export DRY_RUN=0
export DRY_RUN_HARVEST=0
export DRY_RUN_MIRROR=0
export DRY_RUN_FIX=1
export DRY_RUN_EMAIL=1
export HERMES_HOME="${HERMES_HOME:-/home/ubuntu/.hermes}"
LOG_DIR="${HERMES_HOME}/scripts/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/orchestrator-$(date +%Y%m%d-%H%M%S).log"
echo "[$(date -Iseconds)] daily-repo-orchestrator cycle" | tee -a "$LOG_FILE"
python3 "${HERMES_HOME}/skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py" 2>&1 | tee -a "$LOG_FILE"
RC=${PIPESTATUS[0]}
echo "[$(date -Iseconds)] exit=$RC" | tee -a "$LOG_FILE"
exit $RC
EOF
chmod +x ~/.hermes/scripts/daily_repo_orchestrator_mirror.sh

hermes cron create "0 22 * * *" \
  "Daily 07:00 KST daily-repo-orchestrator mirror-only prod mode..." \
  --name "daily-repo-orchestrator-mirror" \
  --script daily_repo_orchestrator_mirror.sh \
  --deliver origin
```

**왜 wrapper 인가**: cron sub-shell은 `~/.bashrc` 로드 안 함 + `~/.env` 도 안 읽음. wrapper가 `set -a; source` 패턴으로 env load + flags 박고 + log file에 stdout 저장 + exit code 보고.

자세한 패턴 → `bash-script-template` SKILL.md 의 "env wrapper pattern" 섹션.

---

## Cycle Log 형식

`~/.hermes/scripts/logs/daily-repo-YYYY-MM-DD.jsonl` (각 cycle마다 append):

```json
{"ts": "2026-07-07T01:42:52", "stage": "mirror", "action": "linear-reuse",
 "dry_flags": {"harvest": false, "mirror": false, "fix": true, "email": true},
 "id": "SHO-49",
 "key": "mybotagent/hermes-wiki::[Audit 2026-07-03] 헤르메스 생태계 종합 감사"}
{"ts": "2026-07-07T01:42:52", "stage": "cycle", "action": "done",
 "dry_flags": {"harvest": false, "mirror": false, "fix": true, "email": true},
 "n_repos": 30, "n_cands": 7, "n_top": 3}
```

`dry_flags` dict로 어느 단계가 dry였는지 사후 추적 가능 → 사용자 audit 편함.

---

## Related

- `references/linear-kanban-idempotency.md` — mirror 단계의 dedupe 코드
- `bash-script-template` SKILL.md — env wrapper pattern (set -a + source + PIPESTATUS)
- `pr-merge-gate` SKILL.md — token permission probe (pre-flight 5단계)
- `self-improvement-loop` SKILL.md — autonomous mode 메타 신호
