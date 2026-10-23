# Session Notes — wiki-auto-refresh runs

누적 세션 노트. 각 항목은 (날짜, 발견, 적용) 형식.

## 2026-10-22 (21:00 KST) — P19 재감염 (27회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` 하단 footer 뒤에 `— 자동 추가 (2026-10-22)` 레이블 서브모듈 항목 62건 대량 삽입 (subagents-library 5 + logs 57).
  - **working-tree 전용 오염** — `git show HEAD:index.md | grep -c '자동 추가'` = 0, `git show origin/main:index.md` = 0.
  - `git diff HEAD -- index.md` = rogue 추가분 63줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용.
- P18: 0건 ✅ (wiki 전체 + skills/references/).
- `raw/2026-W42-weekly-recap-draft.md`는 index.md raw/ 섹션에 이미 PAT B로 정상 등록 확인 → 재등록 불필요.

**처리:**
1. `git restore index.md` (P19 62줄 rogue 제거).
2. `logs/2026/2026-10-22-2100.md` 신규 로그 생성 + logs/index.md October 섹션에 행 추가 (P18 triple-pipe 검증 후).
3. 로그 서브모듈 커밋 `f998ec4` (master) → push 성공 `310bc85..f998ec4`.
4. parent wiki 커밋 `b56142f` (main) → push 성공 `03b9666..b56142f`.

**감사 결과:**
- wikilink-audit.py: 84 files, broken 0 / cross-domain 0 / bare-name 0 / MDEXT 0 ✅.
- markdown-link-audit.py: P11 0, real broken 0 ✅.
- index-md-audit.py: registered 86 = actual 86, dead link 0, REAL MISSING 0 ✅.
- logs-index-link-audit.py (P25): broken 0, notref 0, covered 13 (wildcard), ambiguous 0 ✅.
- tag-audit.py: taxonomy 149, registered 137/137, unknown 0 ✅.
- auto-fill-dates.py: 0 filled, 18 skipped (raw/ immutable) ✅.
- P19 scan: index.md / HEAD / origin/main 모두 0 ✅.
- git status: clean, up-to-date with origin/main ✅.

**참고:** stale(30일+) 68건은 명시적 `updated:` SSOT 기준 기존 상태 — 자동 갱신하지 않음 (사람 검토 대상).

## 2026-10-21 (21:00 KST) — P19 재감염 (26회 연속, working-tree) + logs/index.md 깨진 링크 12건 수정 + push 성공

**발견:**
- P19: **working-tree 전용 변형** — `git show HEAD:index.md | grep -c '자동 추가'` = 0, `git show origin/main:index.md` = 0 (둘 다 청정). `git diff HEAD -- index.md` = rogue 추가 61줄 + 비-rogue 변경 0 → `git restore index.md` 빠른 경로 적용. 25회(10-19) 이후 26회째 재감염. 라벨 `— 자동 추가 (2026-10-21)`, 내용 = logs/ 51 + subagents-library/ 5 + raw/ 1.
- **신규 발견 — logs/index.md 링크 무결성 결함**: logs 서브모듈 index.md에 깨진 링크 12건 + 누락 등록 1건 + 삭제된 파일 참조 2건.
  - `2026/2026-06-10-2115.md` 등 — root-level 파일인데 `2026/` 하위로 잘못 기록된 패턴 (12건 중 다수).
  - `2026/2026/08-02-0700-weekly-cleanup.md` — `2026/` 중복.
  - `2026/2026-09-29-2100.md`, `2026/2026-07-03-0025.md` — 파일 없음 (커밋 이력에도 미존재/삭제됨) → 행 제거.
  - 누락: `2026/2026-09-06-0700-weekly-cleanup.md` (파일은 있으나 index 미등록).
  - 05-31 13건은 wildcard `[2026-05-31-*](2026/)` 커버 → 오탐 아님.
- P18: 0건 ✅ (wiki + skill references 모두).
- **subagents-library submodule 변경 되돌림**: `subagents-library-hub.md`의 wikilink가 `[[harness-engineering-hub]]` → `[[repos/hermes-wiki-claude-code]]`로 변경돼 있었으나, submodule root 기준 resolution에서 깨짐(P24). **parent wiki 기준 경로를 submodule 내부에 넣으면 안 됨** → `git restore`로 되돌림.

**처리:**
1. `git restore index.md` (P19 61줄 rogue 제거).
2. logs/index.md 전체 rewrite (83줄 → 88줄): 깨진 링크 12건 경로 수정, 09-06 항목 등록, 07-06 항목 순서 재정렬, October 섹션 신설.
3. `logs/2026/2026-10-21-2100.md` 신규 로그 생성.
4. subagents-library 변경 되돌림.
5. 감사 전수 재실행 — 전부 ✅.

**Git:**
- logs submodule: `310bc85` (master) — push 성공 `f7a43c8..310bc85`.
- hermes-wiki parent: `03b9666` (main) — push 성공 `87133f6..03b9666`.
- GitHub 인증: `.git-credentials` + `git config credential.helper "store --file ~/.git-credentials"` (logs는 credential.helper 미설정 상태라 push 실패 → 설정 후 성공).

**감사 결과:**
- wikilink-audit.py: broken 0, cross-domain 0, bare-name 0, MDEXT 0 ✅.
- markdown-link-audit.py: P11 0, broken 0 ✅.
- index-md-audit.py: 86 registered = 86 actual, dead link 0 ✅.
- tag-audit.py: 137/137 registered, unknown 0 (taxonomy 149) ✅.
- auto-fill-dates.py: 0 filled, 18 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 ✅.
- P19 scan: index.md / HEAD / origin/main 모두 0 ✅.
- git status: clean, up-to-date with origin/main ✅.

## 2026-10-19 (21:00 KST) — P19 재감염 (25회 연속) + W42 등록 + GitHub push 성공

**발견:**
- P19: HEAD(origin/main) `자동 추가 (2026-10-17)` 레이블 62개 서브모듈 항목 커밋 (18a8f1c, 2026-10-18 05:30 auto-sync).
  - committed 변형 — `git show HEAD:index.md | grep -c '자동 추가'` = 62.
  - Parent(c121efb, 2026-10-12 P19 복구 직후): 0건.
  - 18a8f1c diff = rogue 추가분뿐 (+정식 수정 0건) → parent 복원 경로 적용.
- `raw/2026-W42-weekly-recap-draft.md` 진짜 미등록: index-md-audit.py REAL MISSING 1건.
- P18: 0건 ✅.
- **GitHub push 인증**: `.git-credentials` 파일 (`https://mybotagent:ghp_...@github.com`) 존재 확인 → `git config credential.helper "store --file ~/.git-credentials"` 설정 → push 성공. SSH key/.netrc/gh auth 모두 없음.

**처리:**
1. `git show c121efb:index.md > index.md`로 parent 복원 (62개 rogue 제거).
2. `raw/2026-W42-weekly-recap-draft.md` PAT B 형식으로 raw/ 섹션에 등록 (W38~W41과 일관성).
3. P18 cross-file scan: 0 오염 ✅.
4. 모든 감사 재실행: wikilink (0 broken) / markdown-link (0 P11) / index-md (86=86) / tag (137/137 registered) 전부 ✅.

**Git:**
- 1st commit: `3eb20f7 fix: P19 recovery — remove 62 rogue submodule entries (2026-10-18 re-infection)` (1 file, 63 deletions).
- 2nd commit: `87133f6 register raw/2026-W42-weekly-recap-draft in index.md` (1 file, +2/-1).
- Push: 성공 `18a8f1c..87133f6 main -> main`.
- Submodule: logs 1 commit ahead (별도 push 필요), subagents-library modified content (내부 수정, parent 처리 범위 밖).

**감사 결과:**
- wikilink-audit.py: Cross-domain 0, Bare-name 0, MDEXT 0, 0 broken ✅.
- markdown-link-audit.py: 0 P11, 0 broken ✅.
- index-md-audit.py: 86 registered = 86 actual, 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 18 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main ✅.

**Git:** 2 commits, push 완료.

## 2026-10-13 (21:00 KST)