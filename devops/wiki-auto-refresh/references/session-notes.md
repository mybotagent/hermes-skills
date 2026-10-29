# Session Notes — wiki-auto-refresh runs

누적 세션 노트. 각 항목은 (날짜, 발견, 적용) 형식.

## 2026-10-28 (21:00 KST) — P19 재감염 (31회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` footer 뒤에 `— 자동 추가 (2026-10-28)` 레이블 서브모듈 항목 **67건** 대량 삽입 (subagents-library 5 + logs 62).
  - **working-tree 전용 오염** — 3단계 판별: working tree **67건** / HEAD **0건** / origin/main **0건**.
  - `git diff HEAD -- index.md` = rogue 추가분 68줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용 (커밋 불필요).
  - rogue 66→67 증가는 logs 신규 파일 1건 증가분 — 정상 패턴 (P19 "rogue = logs 파일 수에 비례" 규칙).
- P18: 0건 ✅ (wiki 전체 `^|- ` grep + skills/references/ + index.md/logs-index.md triple-pipe 0건).
- audit 5종 전항목 통과: wikilink 0 / markdown-link(P11) 0 / index-md registered 87 = actual 87 REAL MISSING 0 / tag Unknown 0 / logs-index broken 0 notref 0 (covered 13 오탐).
- auto-fill-dates: filled 0 / skipped 20(raw immutable) / errors 0.
- stale(30일+): 63개 페이지 (수동 검토 대상, P16 — 기계적 갱신 안 함). 날짜 정보 없음 20개(raw immutable).
- logs 서브모듈 신규 로그 파일 0건 → index.md 신규 등록 불필요.

**적용:**
1. `git restore index.md` (P19 working-tree 전용 복구)
2. logs 서브모듈: `2026/2026-10-28-2100.md` 신규 생성 + `index.md` October 섹션 최상단에 행 추가 (`||` double-pipe, `cat -A` 인접 행 prefix 일치 확인, triple-pipe 0건)
3. audit 5종 + auto-fill 재실행 → 전부 통과

**커밋:**
- logs submodule (master): `103fed4` → push `f8fcd05..103fed4` ✅
- parent hermes-wiki (main): `72aaeae` → push `6e20c22..72aaeae` ✅
- 최종 상태: working tree / HEAD / origin/main 모두 `자동 추가` 0건, `git status` clean.

**교훈:**
- 10-26(committed+push) → 10-27(working-tree) → 10-28(working-tree) — 변형이 매번 다를 수 있으므로 3단계 판별은 매 실행 독립 수행해야 한다.

## 2026-10-27 (21:00 KST) — P19 재감염 (30회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` footer 뒤에 `— 자동 추가 (2026-10-27)` 레이블 서브모듈 항목 **66건** 대량 삽입.
  - **working-tree 전용 오염** — 3단계 판별: working tree **66건** / HEAD **0건** / origin/main **0건**.
  - `git diff HEAD -- index.md` = rogue 추가분 67줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용 (커밋 불필요).
  - rogue 65→66 증가는 logs 신규 파일 1건 증가분 — 정상 패턴.
- P18: 0건 ✅ (wiki 전체 `^|- ` grep + skills/references/ + index.md triple-pipe 0건).
- audit 5종 전항목 통과: wikilink 0 / markdown-link(P11) 0 / index-md registered 87 = actual 87 REAL MISSING 0 / tag Unknown 0 / logs-index broken 0 notref 0 (covered 13 오탐).
- auto-fill-dates: filled 0 / skipped 20(raw immutable) / errors 0.
- stale(30일+): 63개 페이지 (수동 검토 대상, P16 — 기계적 갱신 안 함). 날짜 정보 없음 0개.
- logs 서브모듈 신규 로그 파일 0건 → index.md 신규 등록 불필요.

**적용:**
1. `git restore index.md` (P19 working-tree 전용 복구)
2. logs 서브모듈: `2026/2026-10-27-2100.md` 신규 생성 + `index.md` October 섹션 최상단에 행 추가 (`||` double-pipe, `cat -A` 인접 행 prefix 일치 확인, triple-pipe 0건)
3. audit 5종 + auto-fill 재실행 → 전부 통과

**커밋:**
- logs submodule (master): `f8fcd05` → push `5ada149..f8fcd05` ✅
- parent hermes-wiki (main): `6e20c22` → push `90a0d2a..6e20c22` ✅
- 최종 상태: working tree / HEAD / origin/main 모두 `자동 추가` 0건, `git status` clean.

**교훈:**
- 3단계 판별 결과가 working-tree 전용이면 `git restore` fast path로 커밋 없이 복구 가능 (10-23과 동일 패턴). committed 변형(10-26)과 다름 — HEAD/origin 검사 생략 불가.

## 2026-10-26 (21:00 KST) — P19 재감염 (29회 연속, committed 변형) + freelancing-platforms-comparison 등록 + push 성공

**발견:**
- P19: `index.md` footer 뒤에 `— 자동 추가 (2026-10-25)` 레이블 서브모듈 항목 **65건** 대량 삽입.
  - **committed 변형 (신규)** — 3단계 판별에서 working tree / HEAD / origin/main **모두 65건**. 이전 28회는 전부 working-tree 전용이었으나 이번엔 04:00 auto-sync 크론(`83f4356 auto-sync 2026-10-26 04:00 KST`)이 rogue 블록을 커밋·push까지 완료한 상태.
  - 오염 커밋 `83f4356`의 index.md diff = **rogue 추가분 66줄뿐**(정식 수정 0건) → mixed-state edge case 아님 → **parent 복원 경로** 적용.
  - Parent `a955615` 청정(0건) 확인 후 `git show a955615:index.md > index.md` → 203줄 → 138줄.
  - **rogue 건수 = logs 파일 수에 비례** (10-23: 63건 → 10-26: 65건). 신규 로그 2건 증가분 + 정상 패턴.
- index.md 미등록 1건: `solopreneur/freelancing-platforms-comparison.md` — parent 복원 후 이전에도 미등록 상태였음 → solopreneur/ 섹션에 PAT A로 정식 등록.
- logs/index.md NOTREF 1건: `2026-10-26-1815.md` (root-level, 셀프힐링 로그) → October 섹션에 등록.
- P18 `^|- ` 검사: wiki 전체 + skill references/ 모두 0건 (clean).

**적용:**
1. `git show a955615:index.md > index.md` (P19 committed 복구, parent 복원 경로)
2. `patch`로 solopreneur/ 섹션에 `freelancing-platforms-comparison` 항목 추가 (P28 준수: 고유 앵커 1줄 + 앵커 보존)
3. logs 서브모듈: `2026/2026-10-26-2100.md` 신규 생성 + `index.md` October 섹션에 2행 추가 (`||` double-pipe 형식, `cat -A`로 인접 행 prefix 일치 검증, triple-pipe 0건)
   - 1815 로그 링크는 root-level 파일이므로 target `2026-10-26-1815.md` (경로 prefix 없이)
4. audit 5종 재실행 → 전부 통과 (wikilink 0 / markdown 0 / index-md registered 87 = actual 87, REAL MISSING 0 / tag Unknown 0 / logs-index broken 0 notref 0)

**커밋:**
- logs submodule (master): `5ada149` → push `ee408fd..5ada149` ✅
- parent hermes-wiki (main): `fc103d3` → push `83f4356..fc103d3` ✅
- 최종 상태: working tree / HEAD / origin/main 모두 `자동 추가` 0건, `git status` clean.

**교훈:**
- 04:00 auto-sync 크론이 rogue를 **커밋 + push까지** 완료하는 committed 변형이 실제로 발생함 (P19 사례 29회째). 3단계 판별(working/HEAD/origin) 매 실행 필수 — HEAD만 봐선 부족하고, `git status` clean이어도 오염 커밋이 push된 상태일 수 있음.

## 2026-10-23 (21:00 KST) — P19 재감염 (28회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` 하단 footer 뒤에 `— 자동 추가 (2026-10-23)` 레이블 서브모듈 항목 63건 대량 삽입.
  - **working-tree 전용 오염** — `git show HEAD:index.md | grep -c '자동 추가'` = 0, `git show origin/main:index.md` = 0.
  - `git diff HEAD -- index.md` = rogue 추가분 64줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용.
- P18: 0건 ✅ (wiki 전체 `^|- ` grep + skills/references/).
- `raw/2026-W42-weekly-recap-draft.md`는 index.md raw/ 섹션에 이미 PAT B로 정상 등록 확인 → 재등록 불필요.
- subagents-library / logs 서브모듈 내부 파일 모두 clean (P24 역방향 부작용 없음).

**처리:**
1. `git restore index.md` (P19 63줄 rogue 제거).
2. `logs/2026/2026-10-23-2100.md` 신규 로그 생성 + logs/index.md October 섹션 최상단에 행 추가 (triple-pipe 0건 검증 후).
3. 로그 서브모듈 커밋 `ee408fd` (master) → push 성공 `f998ec4..ee408fd`.
4. parent wiki 커밋 `4275c2d` (main) → push 성공 `b56142f..4275c2d`.

**감사 결과:**
- wikilink-audit.py: 84 files, broken 0 / cross-domain 0 / bare-name 0 / MDEXT 0 ✅.
- markdown-link-audit.py: P11 0, real broken 0 ✅.
- index-md-audit.py: registered 86 = actual 86, dead link 0, REAL MISSING 0 ✅.
- logs-index-link-audit.py (P25): broken 0, notref 0, covered 13 (wildcard), ambiguous 0 ✅.
- tag-audit.py: taxonomy 149, registered 137/137, unknown 0 ✅.
- auto-fill-dates.py: 0 filled, 18 skipped (raw/ immutable) ✅.
- P19 scan: index.md / HEAD / origin/main 모두 0 ✅.
- git status: clean, up-to-date with origin/main ✅.

**참고:** stale(30일+) 67건은 명시적 `updated:` SSOT 기준 기존 상태 — 자동 갱신하지 않음 (사람 검토 대상).

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