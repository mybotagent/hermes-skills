---
name: bash-script-template
description: Bash script best-practice template for hermes-pipeline scripts (~/.hermes/scripts/*.sh). Use when writing a new shell script for hermes operations — applies set -euo pipefail, env var override, heredoc-safe printf pattern, log dir, usage(), git pull --ff-only for submodule sync. 2026-07-02 audit pack 합의.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [bash, shell-script, template, hermes-pipeline, best-practice]
    related: [code-audit-fix-pack, wiki-save]
---

# Bash Script Template (Hermes Pipeline)

`~/.hermes/scripts/*.sh` 작성 시 기본 패턴. 2026-07-02 audit pack 후 합의 (hermes-pipeline-scripts repo 3 scripts 검증).

## When to Use

새 shell script 작성 시 (특히 `~/.hermes/scripts/`에 위치하는 hermes 운영 도구).

## Template

### Header
```bash
#!/bin/bash
# ~/.hermes/scripts/SCRIPT_NAME.sh
# [1-line description]
# 사용법: ./SCRIPT_NAME.sh [ARGS]
#
# Audit YYYY-MM-DD:
#   - 변경 사항 1
#   - 변경 사항 2
set -euo pipefail
```

### env wrapper pattern (cron에서 호출되는 운영 스크립트)

**`daily_repo_orchestrator_mirror.sh` / `verdict_analyzer_weekly.sh` / `memory_auto_curator.sh` 에서 검증된 패턴** — cron job은 sub-shell 시작 시 `~/.env`를 자동으로 못 읽음. `set -e`만 켜고 시작하면 `$GITHUB_TOKEN` 등의 env var가 비어서 도구가 무너짐.

```bash
#!/bin/bash
# env-wrapper를 가장 위에 둔다
set -uo pipefail          # set -e 빼기: 로그 파일에 stage별 실패 한 줄씩 남기기 위함

# .env 자동 로드 (HERMES_HOME 분기 처리)
if [ -f "${HOME:-/home/ubuntu}/.hermes/.env" ]; then
    set -a; source "${HOME:-/home/ubuntu}/.hermes/.env"; set +a
elif [ -f "${HOME:-/home/ubuntu}/.env" ]; then
    set -a; source "${HOME:-/home/ubuntu}/.env"; set +a
else
    echo "[$(date -Iseconds)] .env not found" >&2
    exit 1
fi

# 운영 모드 flag (mirror vs full prod vs dry 등)
export DRY_RUN=0
export DRY_RUN_HARVEST=0   # read-only GET
export DRY_RUN_MIRROR=0    # Linear/Kanban create (idempotent)
export DRY_RUN_FIX=1       # ❌ push/PR/open 안 함 (사용자 confirm 전까지 dry)
export DRY_RUN_EMAIL=1     # ❌ SMTP send 안 함
export HERMES_HOME="${HERMES_HOME:-/home/ubuntu/.hermes}"

# 로그 파일 + tee (stage별 출력 보존)
LOG_DIR="${HERMES_HOME}/scripts/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(basename "$0" .sh)-$(date +%Y%m%d-%H%M%S).log"
echo "[$(date -Iseconds)] $(basename "$0") cycle" | tee -a "$LOG_FILE"
python3 "${HERMES_HOME}/skills/<skill>/scripts/<tool>.py" 2>&1 | tee -a "$LOG_FILE"
RC=${PIPESTATUS[0]}
echo "[$(date -Iseconds)] exit=$RC" | tee -a "$LOG_FILE"
exit $RC
```

**왜 `set -e` 빼고 `${PIPESTATUS[0]}`만 쓰나**: cron job은 실패해도 다음 턴에 재시도. `set -e`가 있으면 cycle 중간 error에서 즉시 죽어서 "왜 멈췄나" 진단이 어려움. `${PIPESTATUS[0]}`로 마지막 명령의 exit code만 잡으면 stderr에 한 줄 남기고 다음에도 실행됨.

**왜 `set -a` + `source`?**: `set -a` 가 모든 변수 자동 export 모드. env var를 한 줄 한 줄 export 안 해도 `python3 ...` 가 받음.

### Path + env var override (portability)
```bash
# Paths (env override for portability)
WIKI_DIR="${WIKI_DIR:-$HOME/.hermes/wiki}"
SLOT_DIR="${SLOT_DIR:-$WIKI_DIR/architecture/memory-snapshots}"
LOG_DIR="${LOG_DIR:-$HOME/.hermes/logs}"
mkdir -p "$LOG_DIR"
```

### Heredoc safe pattern (injection prevention)
```bash
# Raw + page 동시 저장 (Karpathy wiki-save 패턴, injection-safe)
{
  cat <<EOF
---
title: $TITLE
created: $DATE
tags: [memory-sync, snapshot]
---

EOF
  printf '%s\n' "$BODY"
  cat <<'FOOTER'

## Provenance
- Manual watcher (memory_sync.sh)
FOOTER
} > "$TARGET.md"
```

**왜 이 패턴?**
- `<<EOF` (unquoted) = 변수 확장 OK, BUT `$USER_INPUT` shell injection 위험
- `<<'EOF'` (single-quoted) = 변수 확장 X (정적 텍스트만)
- 해결: frontmatter (변수 OK) → `cat <<EOF`, body (사용자 입력) → `printf '%s' "$VAR"`, footer (정적) → `cat <<'FOOTER'`

### usage() + case
```bash
usage() {
  cat <<EOF
Usage: $0 [OPTION]

Options:
  (default)    description
  --all        full
  --status     show only
  --help       this help

Env overrides:
  WIKI_DIR     path override
  LOG_DIR      log directory
EOF
}

case "${1:-}" in
  --status) ... ;;
  --all) ... ;;
  --help|-h) usage ;;
  "") ... ;;
  *) usage; exit 1 ;;
esac
```

### git submodule sync (safe — refuse diverged)
```bash
cd "$SUBMODULE_DIR"
git fetch origin 2>&1 | tail -3
if ! git pull --ff-only origin main; then
  echo "ERR: submodule diverged from origin/main (refusing auto-sync to prevent data loss)" >&2
  echo "Hint: cd $SUBMODULE_DIR && git status && git log origin/main..HEAD" >&2
  exit 1
fi
```

### commit + push (only if changes)
```bash
cd "$WIKI_DIR"
git add raw/sync architecture/memory-snapshots
git diff --cached --quiet && { echo "no changes"; exit 0; }
git commit -m "[scope]: $ACTION"
git push origin main
```

### script chaining (optional reindex after sync)
```bash
# Step 4: submodule sync + Neo4j reindex (12s)
if [ -x "$HOME/.hermes/scripts/wiki_reindex.sh" ]; then
  echo "Step 4: wiki_reindex.sh..."
  "$HOME/.hermes/scripts/wiki_reindex.sh" 2>&1 | tail -5 || echo "  (failed, ignorable)"
fi
```

## Anti-patterns (DO NOT)

| ❌ Anti-pattern | ✅ Fix |
|----------------|--------|
| `set -e` only | `set -euo pipefail` |
| `<<EOF` + `$USER_INPUT` | `{ cat <<EOF; printf '%s' "$VAR" } > file` |
| hardcoded `/home/ubuntu/...` | `WIKI_DIR="${WIKI_DIR:-$HOME/...}"` |
| `git reset --hard` | `git pull --ff-only origin main` |
| `\|\| true` silent fail | explicit error handling + log |
| `set -e` 즉시 죽기 (cron wrapper) | `set -uo pipefail` + `PIPESTATUS[0]` 명시 (stage별 실패를 stderr에 남기고 cron 재시도 가능) |
| missing `mkdir -p $LOG_DIR` | at script start (cron 첫 실행 fail 방지) |
| unused import | remove (e.g. `import json, os` 안 쓰면 제거) |
| magic number (의미 불분명) | `THRESHOLD_PCT=90` 변수로 추출 |
| meeting phase name in code (`a-step-3`) | generic name (`manual memory-sync`) |
| weak commit message ("Updated") | scope + reason + summary (e.g. `fix(audit-2026-07-02): HIGH pack`) |
| placeholder comment ("단순 휴리스틱") | 정확한 측정 후속 또는 `NOTE:` 로 한계 명시 |
| README emoji 과다 | 사용자 패턴 따르기 (보통 moderate) |
| `\|\| echo ""` in `[ -x "$(... \|\| echo)" ]` | 명확한 `command -v` 또는 단축 평가 |
| **`python3 -c "..."` heredoc 안에 Python f-string (`{name}` 등)** | **bash wrapper = python 호출만, 본체는 별도 `.py` 파일**. 아래 "🐍 bash + Python pitfall" 섹션 참조. |

## 🐍 bash + Python pitfall — `python3 -c "..."` 안에 f-string 넣지 말 것 (2026-07-10 신규)

**증상** (실측 2026-07-10, self_healing_watchdog.sh 1차 구현):
```bash
python3 -c "
import json
data = {
    'job': f'{name}',  # bash가 {name}을 brace expansion으로 해석
    'err': f'**status**: {status}',  # 또 brace expansion
}
"
```

출력:
```
line 57: {name}: command not found
line 57: {jid[:12]}: command not found
line 57: {status}: command not found
```

Python 자체는 동작하지만 stderr에 noise. **원인**: bash의 brace expansion은 큰따옴표 안에서도 발생 (`{a,b}` 같은 콤마 패턴). `{name}`처럼 단일 변수도 큰따옴표 안에서 bash가 command로 해석 시도.

### 더 위험한 함정들

| 패턴 | 증상 | 원인 |
|:-----|:-----|:-----|
| f-string 안에 `\`backtick\`` | `command not found` (bash가 backtick을 command substitution으로 해석) | bash는 backtick = `$(...)`과 동치 |
| f-string 안에 `{"예" if ... else "아니오"}` | `SyntaxError: f-string: unmatched ('"')` | f-string expression 안의 quote 충돌 |
| heredoc 안 `'{"key": "val"}'` 한 줄 | bash가 `"`를 따옴표 매칭으로 오해, syntax error | 큰따옴표 escape 미흡 |
| heredoc 안 `f'''...{var}...'''` | `SyntaxError: unterminated triple-quoted string literal` | bash가 triple-quote를 닫지 못함 |

### 해결 (검증된 패턴): bash wrapper = python 호출만, 본체는 별도 `.py`

```bash
# ~/.hermes/scripts/self_healing_watchdog.sh
#!/bin/bash
# bash wrapper — python 호출만
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SCRIPT_DIR="$HERMES_HOME/scripts"
python3 "$SCRIPT_DIR/self_healing_watchdog.py"
exit 0
```

```python
# ~/.hermes/scripts/self_healing_watchdog.py (별도 .py)
import json, urllib.request

def call_llm_analyze(jid, name, deliver, status, last_error, recent_history, api_key):
    # prompt를 list + '\n'.join()으로 빌드 (큰따옴표 0개)
    prompt_lines = [
        '너는 시스템 자동복구 분석가다.',
        f'- id: {jid}',  # Python f-string OK, bash 간섭 없음
        f'- name: {name}',
        f'- status: {status}',
        f'- deliver: {deliver}',
        f'- last_error: {last_error[:300]}',
        '',
        '응답: root_cause, fix_action, auto_fixable(bool), confidence JSON',
    ]
    prompt = '\n'.join(prompt_lines)
    ...
```

### bash heredoc 안 Python이 정말 필요할 때 (극히 드묾)

부득이하게 inline python이 필요한 경우 (예: 빠른 일회성 스크립트), prompt 변수를 **heredoc 외부에서 미리 export**:

```bash
# ⚠️ 권장 안 함. 임시 디버깅용.
export PROMPT="Job: ${JOB_NAME}, Status: ${STATUS}"
python3 <<'PYEOF'
import os
prompt = os.environ['PROMPT']
# Python 내부에서 prompt 사용
PYEOF
```

`<<'PYEOF'` (single-quoted) = 변수 확장 X. 모든 입력은 env var로 받음. 그래도 inline은 디버깅 외엔 안티패턴 — 별도 `.py`가 정답.

### 검증 명령

```bash
# bash syntax
bash -n script.sh && echo "[bash OK]"

# Python syntax
python3 -c "import ast; ast.parse(open('script.py').read()); print('[py OK]')"
```

두 명령 모두 PASS면 inline 또는 분리된 python 어느 쪽이든 OK. 둘 다 PASS인데 실행 시 brace expansion noise 나오면 inline 구조 의심.

### 이 rule의 출처

- `self_healing_watchdog.sh` 1차 구현 (2026-07-10): 222줄 bash 안에 150줄 python heredoc → 3가지 syntax error 연쇄
- 해결: bash wrapper 14줄로 축소, 본체 360줄을 `self_healing_watchdog.py`로 분리
- 결과: syntax OK + f-string 자유 + 이모지 OK + 디버깅 쉬움

## Examples (3 reference scripts)

`memory_sync.sh` (82 lines):
- 입력: `./memory_sync.sh "TITLE" "BODY"`
- raw + page 2건 저장 (Karpathy 패턴)
- printf safe heredoc
- commit + push + auto reindex

`wiki_reindex.sh` (80 lines):
- `usage()` + `case "${1:-}"` 패턴
- submodule `git pull --ff-only` (refuse diverged)
- `--status` / `--all` / default 분기

`memory_alert.sh` (39 lines):
- proxy measurement (bytes / 4500B char-equivalent)
- ±25% 오차 `NOTE:` 명시
- 측정 불가 시 silent + log

## 5-Stage Verify 적용 (이 템플릿 자체)

- **why**: shell script 버그 / 보안 위험 / 운영 신뢰도 하락
- **what**: 코드 측정 (line, file size, syntax error count)
- **whether**: 측정 옳은가 (severity 분류 적절성)
- **what**: 진짜 fix (HIGH 우선, LOW skip 가능)
- **how**: atomic commit + env var + `set -euo pipefail`
- **validate**: `bash -n scripts/*.sh` syntax OK + mirror `~/.hermes/scripts/` sync

## Mirror rule

`~/.hermes/scripts/` (live) 와 `hermes-pipeline-scripts` repo (영속) 는 동일하게 유지. 작성 후:

```bash
cp new_script.sh ~/.hermes/scripts/new_script.sh
# 또는 mirror 없이 진행 시 운영 환경과 repo 사이 drift 발생
```

## Permission
새 script 작성 후:
```bash
chmod +x script.sh
```

## Related

- `code-audit-fix-pack` — 이 템플릿이 적용된 script 검사 workflow
- `wiki-save` (memory sync watcher section) — `memory_sync.sh` 가 적용하는 영속화 패턴
