---
name: code-audit-fix-pack
description: Code sanity audit workflow (legacy / AI slop / code smell detection) + fix pack automation. Use when user requests "코드 세니티 검사", "AI slop 검토", "code smell", "레거시 코드 검사", or auto-fix of identified issues with commit + push + audit report to GitHub.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [code-audit, code-smell, ai-slop, legacy-code, fix-pack, github, kanban]
    related: [bash-script-template, wiki-save, meeting-documentation]
---

# Code Audit & Fix Pack Workflow

코드 sanity audit (legacy / AI slop / code smell) → 자동 fix → commit + push + audit report. 2026-07-02 `hermes-pipeline-scripts` repo에서 합의.

## When to Use

Trigger keywords:
- "코드 세니티 검사", "AI slop 검토", "code smell", "레거시 코드 검사"
- "발견된 거 fix", "자동으로 고쳐", "fix pack", "audit pack"
- "코드 정리 + 새 repo"

## Workflow

### Step 1: 자동 검사 (auto)
```bash
# Syntax
for f in scripts/*.sh; do bash -n "$f" || echo "ERR: $f"; done

# shellcheck (if installed)
which shellcheck && shellcheck scripts/*.sh

# Anti-pattern grep
grep -rE "TODO|FIXME|XXX|HACK" .
find . -name "*.sh" -exec head -1 {} \;  # shebang check
```

### Step 2: 수동 코드 리뷰 (file by file)
분류 — 발견 시그널:

| Category | Examples |
|----------|----------|
| **Legacy** | deprecated API, old patterns (`/dev/null` vs `>/dev/null`), dead code, unused imports, unused functions |
| **AI slop** | "단순 휴리스틱" / "TODO 나중에 수정" placeholder, unused import (python: `import json, os` 안 씀), magic number, weak commit message ("Updated"/"Fix"), 회의 phase name (`a-step-3`)이 코드/주석에 남음, README emoji 과다 |
| **Code smell** | hardcoded 절대경로, `set -e` only (no pipefail), heredoc unquoted + `$VAR` (injection), cron log dir 없음, `git reset --hard`, `\|\| true` silent fail, missing `usage()`, slug 정규화 없음 |

### Step 3: Severity 분류 (P/I/E/R)
각 발견을 P/I/E/R 형식으로:

| P (Problem) | I (Impact) | E (Evidence) | R (Recommendation) |
|---|---|---|---|
| 무엇이 문제인가 | 영향 범위 (실제 위험 / 개선 / minor) | 코드/라인 증거 | 권장 fix |

Severity 분류:
- **HIGH** — 실제 운영 위험 (security, data loss, fake measurement)
- **MEDIUM** — 개선 권장 (portability, robustness, maintainability)
- **LOW** — minor (cosmetic, debug ergonomics)

### Step 4: 카르간 등록
```bash
hermes kanban create "Audit & Fix pack: [scope] [date]" --priority 1 --body "[discoveries]"
# 또는 기존 task에 comment
hermes kanban comment <task_id> "audit result summary"
```

### Step 5: Fix 적용 (자동)
- HIGH/MEDIUM 우선
- 한 fix = 한 commit (atomic, clear message)
- `bash -n scripts/*.sh` 재확인
- `~/.hermes/scripts/` mirror (다른 위치에 동일 fix 적용)

### Step 6: Audit Report 작성
`AUDIT-YYYY-MM-DD.md` 형식 (private repo):
1. 발견 사항 (HIGH/MEDIUM/LOW 분류, file:line)
2. 적용된 Fix (commit hash + 변경)
3. 알려진 한계 (정직 보고 — 미해결 발견)
4. 후속 작업

### Step 7: Commit + Push
```bash
# 1. fix commit
git add scripts/*.sh
git commit -m "fix(audit-YYYY-MM-DD): HIGH+MEDIUM+LOW pack"
git push origin main

# 2. audit report commit
git add AUDIT-YYYY-MM-DD.md
git commit -m "docs(audit-YYYY-MM-DD): comprehensive audit report"
git push origin main
```

### Step 8: 검증
```bash
git ls-remote origin main  # commit hash 일치 확인
# raw.githubusercontent.com 404 → private repo 정상
```

## Output Format

### AUDIT-YYYY-MM-DD.md structure
```markdown
# Code Audit Report — YYYY-MM-DD

> Repo / Scope / Method / Result

## 발견 사항
### 🚨 HIGH (N)
| # | 파일 | 문제 | Severity | Fix |
### ⚠️ MEDIUM (N)
| ... |
### 🟢 LOW (N)
| ... |
### 🧹 Legacy code
0건 (신규) or N건

## 적용된 Fix
| Commit | 변경 |
| b3c8c98 (init) | ... |
| 07c83df (fix) | ... |

## ⚠️ 알려진 한계
1. ...
2. ...

## 후속 작업
- [ ] ...
```

## Pitfalls (Live Audit 시)

- **Fix 너무 크게**: atomicity 위반. 한 commit = 한 concern. 묶지 말 것.
- **silent fail**: `\|\| true`로 에러 무시. 명시적 error handling 사용.
- **stale 잔재**: 회의 phase 이름 (`a-step-3`, `Phase 5`)이 코드/주석에 남지 않게.
- **AI slop**: "단순 휴리스틱" 주석 + unused import + magic number + 의미 없는 commit message.
- **heredoc injection**: `<<EOF` unquoted + `$USER_INPUT` → shell injection. `printf '%s' "$VAR"` 사용.
- **cron log dir**: 첫 실행 시 `mkdir -p $LOG_DIR` 보장. `>> /path/log` cron line은 dir 없어도 fail silent.
- **`git reset --hard`**: 워크트리 손실. `git pull --ff-only`로 안전화.
- **mirroring**: `~/.hermes/scripts/` (live)와 `hermes-pipeline-scripts` repo — 동일하게 유지. cp 동기화.
- **private repo raw URL**: `raw.githubusercontent.com/<user>/<repo>/main/<file>` → 404. 정상. `ls-remote`로 검증.
- **commit message slop**: "Updated" / "Fix" / "Test" → 명확한 scope (fix/docs/refactor) + reason (audit-2026-07-02) + summary.
- **previous-audit reversal** (2026-07-03 발견): 새 audit의 TODO action 실행 전, **관련 repo의 git log를 확인해서 이전 audit 결정을 덮어쓰지 말 것**. 특히 "lean audit", "AI slop 제거", "간소화" commit이 결정을 명시적으로 뒤집었을 수 있음. **구체 사례**: 2026-07-03 새 audit이 `memory_alert.sh` = HIGH 발견 → live 작성 시도. 하지만 `hermes-pipeline-scripts` commit `4d27449` (1일 전)에서 동일 파일을 **"가짜 측정, AI slop"** 으로 명시 삭제한 이력이 있었음. git log 확인으로 즉시 정정 (live 작성 → 삭제). **Lesson**: TODO action 자동 실행 시, **이전 결정을 git log로 재확인 후 실행**. 이전 결정 존중 시 새 audit 보고서에 명시 기록 (정직 보고). 이걸 안 하면 같은 실수 1일 만에 반복.

## Reference

- `references/audit-checklist.md` — 발견 시그널 빠른 참조
- `bash-script-template` — fix 적용 시 표준 패턴
- `wiki-save` (memory sync watcher section) — 이 workflow로 작성된 3 scripts의 영속화

## Examples

2026-07-02 `hermes-pipeline-scripts` repo (today):
- 0 legacy / 4 HIGH / 6 MEDIUM / 3 LOW 발견
- 8 fix 적용, 3 skip (M3 SVG, M6 emoji, L2/L3 minor)
- 3 commits: b3c8c98 (init) + 07c83df (fix pack) + 147f674 (audit report)
- AUDIT-2026-07-02.md (5.2KB) push
- ~50% 코드 변경 (143 insert / 85 delete)
- 3 scripts 모두 `bash -n` syntax OK

## 5-Stage Verify 적용

이 workflow 자체가 5-stage verify method를 따름:
- **why**: 가치 검증 (legacy / AI slop 발견)
- **what**: 코드 측정 (line count, file size, syntax error count)
- **whether**: 측정 옳은가 (severity 분류의 적절성)
- **what**: 진짜 무엇을 fix (HIGH 우선, LOW skip 가능)
- **how**: 어떻게 fix (atomic commit, env var, `set -euo pipefail`)
- **validate**: `bash -n` + `git ls-remote` + manual review

## Related

- `bash-script-template` — fix 적용 시 bash script 표준 패턴
- `wiki-save` — memory sync watcher 섹션 (이 workflow의 결과)
- `meeting-documentation` — 5-stage verify methodology (audit의 정당화)
