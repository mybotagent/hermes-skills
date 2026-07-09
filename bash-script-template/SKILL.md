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
