# Code Audit Checklist (quick reference)

빠른 검사용 체크리스트. SKILL.md Step 2와 함께 사용.

## 1. 자동 검사

```bash
# Syntax check
for f in scripts/*.sh; do bash -n "$f" || echo "ERR: $f"; done

# shellcheck (if installed)
which shellcheck && shellcheck scripts/*.sh

# Anti-pattern grep
grep -rE "TODO|FIXME|XXX|HACK" .

# Shebang check
find . -name "*.sh" -exec head -1 {} \;
```

## 2. Legacy

- [ ] deprecated API (`/dev/null` vs `>/dev/null`)
- [ ] 옛 패턴 (backtick vs `$(...)`)
- [ ] 사용되지 않는 함수/변수/import
- [ ] 주석 처리된 dead code (`# old_function()`)
- [ ] 옛 환경 가정 (PATH 하드코딩, /bin/sh vs /bin/bash)

## 3. AI slop

- [ ] "단순 휴리스틱" / "TODO 나중에 수정" placeholder 주석
- [ ] unused import (python: `import json, os` 안 씀)
- [ ] magic number (의미 불분명한 literal — `22.0`, `4500` 등)
- [ ] weak commit message ("Updated", "Fix", "Test")
- [ ] 회의 phase name (`a-step-3`, `Phase 5`)이 코드/주석에 남음
- [ ] README emoji 과다 (사람 작성 위주보다 많음)
- [ ] `print(len(...))` 같은 추측 기반 heuristic
- [ ] "추후 개선" 같이 의도가 불명확한 주석

## 4. Code smell (HIGH 위험)

- [ ] `<<EOF` unquoted + `$USER_INPUT` → heredoc shell injection
- [ ] `git reset --hard` → 데이터 손실 위험
- [ ] `git pull --rebase` 안 쓰고 force push (`git push -f`)
- [ ] hardcoded secret/token (`API_KEY="..."`, `export TOKEN=...`)
- [ ] sudo 호출 (`sudo -E`, `sudo bash`)
- [ ] `eval "$VAR"` → 임의 코드 실행

## 5. Code smell (MEDIUM 개선)

- [ ] `set -e` only (no pipefail) → `set -euo pipefail`
- [ ] hardcoded 절대경로 (`/home/ubuntu/...`)
- [ ] cron line에 log dir 보장 없음 → `mkdir -p $LOG_DIR` at start
- [ ] `|| true` silent fail → 명시적 error handling
- [ ] missing `usage()` (스크립트 옵션 불명)
- [ ] slug 정규화 없음 (`"a   b"` → `"a---b"`)
- [ ] `${VAR:-}` 빈 default + 후속 로직 (명확한 default로)
- [ ] unused env var / unused shell variable
- [ ] function이 너무 길거나 단일 책임 위반
- [ ] DRY 위반 (동일 로직 2곳 이상)

## 6. Code smell (LOW minor)

- [ ] 정보 손실 (`2>&1 | head -2` → `tail -5` 또는 full log)
- [ ] shellcheck 안 깔려있음 (CI workflow 추가 권장)
- [ ] 단위 테스트 없음 (bats 등 도입 권장)
- [ ] heredoc unquoted가 진짜 정당한지 (`<<EOF` 변수 사용 시 OK, `<<'EOF'` 정적)
- [ ] README에 emoji 패턴이 사용자 위키와 다른지

## 7. 정직한 negative result 보고

이게 가장 중요. **위 발견 후**:

- **한계 명시**: 측정 proxy, ±오차, 가정, 외부 의존 모두 보고
- **후속 작업 명시**: 미해결 발견은 다음 회의 안건으로
- **commits 분리**: fix (atomic) + docs (audit report) 분리
- **mirror sync**: `~/.hermes/scripts/` 와 영속 repo 동일하게 유지
- **private repo raw URL 404**: 정상. `git ls-remote`로 commit hash 검증

## Quick Decision Tree

```
발견 시그널
  ├── 보안 (injection, hardcoded secret) → 즉시 HIGH fix
  ├── 데이터 손실 (reset --hard, force push) → 즉시 HIGH fix
  ├── 가짜 측정 (heuristic ≠ 실측) → HIGH fix + 후속 측정
  ├── stale 잔재 (meeting phase name) → HIGH fix (search & replace)
  ├── AI slop 패턴 → MEDIUM/LOW fix
  ├── portability (hardcoded path) → MEDIUM env var
  ├── robustness (set -e only) → MEDIUM set -euo pipefail
  └── cosmetic (emoji, comment style) → LOW or skip
```

## Severity 분류 기준

| Severity | 기준 |
|----------|------|
| **HIGH** | 보안 위험 / 데이터 손실 / 가짜 측정 / 운영 신뢰도 손상 |
| **MEDIUM** | portability / robustness / maintainability 저하 |
| **LOW** | cosmetic / debug ergonomics / minor preference |

## Anti-anti-pattern (over-engineering)

- ❌ **과도한 fix**: 1 fix = 1 concern. wrapper가 wrapper를 감싸면 X
- ❌ **모든 LOW 시도**: 사용자 가성비 우선. LOW는 skip 정직
- ❌ **commit message 너무 길어**: 1줄 요약 + 변경 bullet list 충분
- ❌ **scope creep**: 한 commit에 여러 concern 묶지 말 것

## Time budget

- 자동 검사: 5분
- 수동 리뷰: 10-15분
- HIGH fix: 10분
- MEDIUM fix: 5분
- commit + push: 5분
- AUDIT-YYYY-MM-DD.md 작성: 10분

총 ~50분. 2026-07-02 50분 소요 일치.
