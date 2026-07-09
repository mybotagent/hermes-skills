# Session Notes — wiki-auto-refresh runs

누적 세션 노트. 각 항목은 (날짜, 발견, 적용) 형식.

## 2026-07-08 (pr-review-policy 인덱스 등록)

**발견:**
- 2a 불일치 체크 (정규식 기반 markdown link 인덱싱) 결과 7개 "누락"으로 보임:
  - `raw/hermes-agent-2026-07-07.md`, `raw/llm-wiki-pattern-2026-07-07.md`, `raw/llm-wiki-vs-rag-2026-07-07.md`, `raw/memory-pipeline-design-2026-07-02.md` → 모두 index.md에 plain text 형식 `(raw/...)`로 등록되어 있어 `[text](path)` 정규식이 못 잡음. **false positive (실제로는 등록됨).**
  - `architecture/memory-snapshots/2026-07-02-2109-a-step-3-watcher--.md`, `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` → snapshots/sync 디렉토리 (P13 예외) + `hermes-memory-pipeline.md`에서 wikilink로 참조. orphan 아님.
  - **`infra/pr-review-policy.md` → 진짜 누락.** 다른 페이지에서 markdown/wikilink로 참조되지 않고 logs/(submodule)에서만 언급됨. **index.md에 신규 등록 필요.**

**적용:**
- index.md infra/ 섹션에 `[pr-review-policy](infra/pr-review-policy.md) — 🆕 PR 2-tier 정책 (Tier1: review 필수, Tier2: 즉시 merge, force push 신중)` 추가.
- commit `774fe69 auto-sync 2026-07-08 21:00 KST: register infra/pr-review-policy.md in index` (1 file changed, 1 insertion).
- push to origin/main 성공 (`d9bd548..774fe69`).

**사전 점검 결과 (모두 깨끗):**
- wikilink-audit.py: 61 files, 0 broken, 4 cross-domain (P7 의도된 외부 위키 참조, 유지), 0 bare-name, 0 .md-extension.
- markdown-link-audit.py: 0 broken, 0 P11 sibling cross-ref.
- 0 orphan (raw/4 + memory-snapshots/1 + raw-sync/1 모두 정상 등록/참조 중).
- 0 P13 신규 — how-to-use-hermes 9개 sibling은 어제(2026-07-07) 이미 nested list로 등록됨.

**Stale 점검 (리포트용 — 자동 수정 보류):**
- 30일+ stale 15개: analysis/* (5), architecture/hermes-vs-chatbot (30d), architecture/hybrid-ai-stack (34d), code/scripts (31d), infra/* (4 — discord-gateway, environment, gh-token, higgsfield-mcp 30d), infra/obsidian-github-sync (33d), people/aiprofit (35d), watchlist/README (35d).
- 모두 git log상 7월 1-7일 활동 있음. SKILL.md 지시 (30일+는 사람 검토)대로 자동 수정 보류, 리포트에 stale 카운트만 기재.

**교훈/개선 사항:**
- **2a 인덱스 diff의 false-positive 보강:** 정규식 `\[([^\]]+)\]\(([^)]+)\)`만으로는 plain text bullet (`- name (raw/file.md)`) 형태의 등록을 감지 못함. 향후 2a 단계에서 plain text 형식 raw/ 경로도 등록 카운트에 포함하도록 정밀화 권장. 이번 실행에서는 raw/ 4개 false positive를 사람이 cross-verify로 걸러냄.
- **pr-review-policy.md 누락 원인 추적:** 2026-07-07 23:35 logs/에 "위키 정책 페이지 신규: `wiki/infra/pr-review-policy.md`" 기록. wiki-auto-refresh는 그날 실행되지 않았거나 (21:00 vs 23:35 시차) 실행되었지만 pr-review-policy.md가 index.md에 추가되지 않은 채 종료됨. 향후 신규 정책 페이지 생성 시 wiki-auto-refresh가 index.md 등록까지 보장하도록 index-update hook 검토.

**Wiki 상태 (2026-07-08):**
- 65개 wiki 페이지 (submodule 제외) — 64 + 신규 pr-review-policy.md 1개 (이미 파일은 존재했으나 index 미등록이었음).
- index.md 등록: 60개 (P13/snapshot/raw-sync 예외 + AGENTS/README/SCHEMA/index 자기자신 제외).
- 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 4개 cross-domain wikilink (의도된 외부 위키 참조, 유지).
- 15개 stale (30일+, 사람 검토 대기).

## 2026-07-07 (P13 발견 + 검증된 깨끗한 baseline)

**발견:**
- 2a 불일치 체크 (index.md vs 실제 파일) 결과를 사람이 patch로 수동 처리해야 했음 — `architecture/how-to-use-hermes/01-what-is-hermes.md` ~ `09-troubleshooting.md` 9개 파일이 wiki에는 존재하지만 index.md는 README만 등록. 자동 검사가 잡지 못함.
- 위 9개 sibling 페이지는 README.md가 어떻게든 참조하지만, index.md(최상위 카탈로그)에는 일괄 등록되지 않은 anti-pattern.
- 48 wikilink 검사 (P12 적용): 44 resolved-local + 4 cross-domain, **broken 0** — P12 fix가 정확히 작동. 비교 (2026-07-06 첫 실행): 40/6/0 → P12 후: 44/4/0.
- 1개 stale (30일+): `architecture/hybrid-ai-stack.md` (33일) — 자동 수정 보류 (사람 결정 영역).

**적용:**
- P13 pitfall 신규 추가 (SKILL.md v1.9.0) — multi-page doc README 등록, sibling .md 누락 anti-pattern + 자동 등록 절차.
- `scripts/wikilink-audit.py` + `scripts/markdown-link-audit.py`에 대한 **사전 점검 단계**를 SKILL.md 최상단에 신설 — 인라인 audit 재작성 사고 방지.
- `execute_code`는 Hermes cron 모드에서 block됨을 명시 — `python3 <script>` 직접 실행 fallback.
- 실제 commit: `a6f71eb auto-sync 2026-07-07 21:00 KST` (1 file changed, +10줄).
  - index.md raw/ 섹션에 `memory-pipeline-design` (raw/memory-pipeline-design-2026-07-02.md) 추가.
  - index.md architecture/ 섹션에 how-to-use-hermes 01-09 9개 nested list 등록.

**Wiki 상태 (2026-07-07):**
- 64개 wiki 페이지 (submodule 제외), index.md 등록 50 → 이번 실행으로 11개 추가하여 카탈로그 정합성 회복.
- 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 4개 cross-domain wikilink (intent 유지): `harness-engineering-hub`, `macro-strategy`, `macro-indicators-hub`, `schedule-calendar-hub`.
- 1개 stale (30일+): hybrid-ai-stack.md — 자동 수정 보류, 사람 검토 대기.

**Cross-domain (유지):** `hermes-trading-hub.md`의 4개 cross-domain wikilink 여전히 정상 분류, P12 fix 후 변동 없음.

**사후 검증 사항 (다음 실행에서 확인):**
- P13 anti-pattern 방지를 위해, 다음 2a 단계에서 sibling .md 자동 등록 로직이 실제로 구현되어야 함 — 현재는 patch로 처리함. 자동화 시위 단계 추가 검토.
- 사전 점검 단계의 명령들이 실제 cron 실행에서 100% 신뢰성 있게 작동하는지 (scripts/ 경로가 cron 환경에서도 동일하게 보일지) 다음 실행에서 verify.

## 2026-07-06 (P12 패턴 출현)

**발견:**
- 첫 audit 실행 시 `[[solopreneur/upwork-strategy]]`가 cross-domain으로 잘못 분류됨 — `-strategy` suffix만 보고.
- 실제 `solopreneur/upwork-strategy.md`는 **로컬에 존재** → 정상 wikilink.
- 분류 결과 비교:
  - 첫 실행 (v1.7.0 로직): resolved-local 40, cross-domain 6 (오분류 1건 포함), broken 0
  - 검증 후 (v1.8.0 로직): resolved-local 44, cross-domain 4, broken 0
- P7 docstring의 "suffix는 위치 독립적" 정밀화가 **로컬 존재 검사를 우회하는 부작용**을 만듦.

**적용:**
- P12 pitfall 신규 추가 (SKILL.md v1.8.0) — "모든 분류는 existence check 이후에 적용" 원칙.
- `scripts/wikilink-audit.py` `is_cross_domain()` 시그니처 변경: `(target, lines, line_no)` → `(target, lines, line_no, wiki)`.
  - 첫 줄에서 `if (wiki / (target + ".md")).exists(): return False` short-circuit 추가.
  - 호출부(`audit_file`)에서 `wiki` 인자 전달.
- SKILL.md P7 본문에 2026-07-06 정밀화 문구 추가 (suffix는 "로컬 부재"가 보장된 경우에만 적용).
- SKILL.md P9 pseudocode의 suffix check에 `(BUT only if local doesn't exist — P12)` 주석 추가.

**Wiki 상태 (2026-07-06):**
- 50개 wiki 페이지, 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 2개 신규 페이지 등록: `infra/daily-repo-orchestrator.md`, `infra/gmail-himalaya.md` (index.md + created: 2026-07-06 추가).
- 7개 stale (30일+, 모두 기반 분석/인프라 문서 — 사람이 검토 필요, 자동 수정 보류).
- 4개 cross-domain wikilink (의도된 외부 위키 참조, 유지).

**실제 commit:** `6920072 auto-sync 2026-07-06 21:00 KST` (3 files changed, 136 insertions).

**Cross-domain (유지):** 이번 실행의 4개 cross-domain (`harness-engineering-hub`, `macro-strategy`, `macro-indicators-hub`, `schedule-calendar-hub`)는 모두 외부 위키 레포에 존재 — 정상 유지.

## 2026-07-03 (P11 패턴 출현)

**발견:**
- `architecture/how-to-use-hermes/README.md` 35, 36번 줄에서 bare-name markdown link 2건 깨짐:
  - `[hermes-vs-chatbot.md](hermes-vs-chatbot.md)` — sibling 디렉토리 페이지를 bare-name으로 참조
  - `[hermes-memory-pipeline.md](hermes-memory-pipeline.md)` — 동일 패턴
- `how-to-use-hermes/` 서브디렉토리(2026-07-03 신규 생성된 multi-page 가이드)의 README.md가 같은 wiki의 다른 섹션을 bare-name으로 참조.
- **wikilink 검사 (P7/P9/P10) 결과는 0 broken이었으나** markdown link 검사로만 발견됨 — 두 종류의 링크는 서로 다른 false-negative surface.

**적용:**
- P11 pitfall 신규 추가 (SKILL.md v1.7.0) — 형제 README cross-reference, `../` prefix 추가 메커니즘.
- `scripts/markdown-link-audit.py` 신규 — P11 자동 감지 + `--fix` 옵션으로 일괄 수정.
- P9 vs P11 구분 정리 (SKILL.md 본문): 같은 bare-name 시그널이지만 fix 메커니즘이 다름.
  - P9: wikilink `[[foo]]` → `[[dir/foo]]` (디렉토리 prefix)
  - P11: markdown `[foo](foo.md)` → `[foo](../foo.md)` (`../` prefix)
- 실제 수정 commit: `b1eed3e auto-sync 2026-07-03 21:00 KST: fix broken markdown links in how-to-use-hermes/README`.

**부수 발견:**
- `how-to-use-hermes/01-09.md` 9개 서브페이지는 모두 0일 stale — `README.md` 인덱스 테이블에서 참조되어 orphan 아님.
- `raw/memory-pipeline-design-2026-07-02.md` + `raw/sync/...` + `architecture/memory-snapshots/...` 3개 페이지가 index.md에는 없지만 모두 `hermes-memory-pipeline.md`에서 markdown link로 참조됨 — orphan 아님.
- 30일 경계 페이지 5개 (정확히 30일): 자동 채우기 불필요, 임계 미만. 다음 점검 시 stale로 진입.

**Cross-domain (유지):** 이번 실행에서도 `hermes-trading-hub.md`의 4개 cross-domain wikilink 정상 유지.

## 2026-07-02 (auto-refresh run)

**발견:**
- 7개 wikilink에 명시적 `.md` 확장자가 포함되어 broken 상태 (실제 resolver는 `target + ".md"`로 lookup하므로 `foo.md.md` 찾으러 가서 실패).
- 영향 파일: `architecture/hermes-vs-chatbot.md` (3개), `infra/higgsfield-mcp.md` (4개 — 1개는 `#anchor` 포함).
- `scripts/wikilink-audit.py` v1.5.0이 이 패턴을 false-negative로 통과시킴 (`target_with_md = raw if raw.endswith(".md") else raw + ".md"` 분기 때문에, `.md` 이미 있으면 `wiki/foo.md`를 그대로 검사 → 파일 존재로 OK 오인).

**적용:**
- P10 pitfall 신규 추가 (SKILL.md v1.6.0).
- `scripts/wikilink-audit.py` 패치: `.md`가 있으면 항상 strip한 후 lookup, `body != normalized`일 때만 `mdext` finding으로 보고. 앵커는 보존.
- 실제 수정 commit: `3e9645f fix(wiki): strip .md extension from 7 wikilinks`.

**부수 발견 (race condition):**
- cron 실행 도중(첫 pre-flight ~ 두 번째 status 사이) 사용자가 `271e571 arch: Hermes Memory Pipeline 4-Layer` 커밋을 manual로 push함.
- 첫 `git status -sb`에서는 `M index.md`, `?? architecture/hermes-memory-pipeline.md`, `?? raw/memory-pipeline-design-2026-07-02.md`로 uncommitted로 보였으나, commit 시점엔 모두 HEAD에 있었음.
- **교훈:** `git status`는 snapshot이므로 시간차로 stale할 수 있음. `git diff HEAD`로 working tree vs HEAD 직접 비교가 더 신뢰성 높음. cron에서는 큰 문제 없음 (작업 결과만 commit하면 됨).

**Cross-domain (유지):**
- `hermes-trading-hub.md`의 4개 wikilink (`[[harness-engineering-hub]]`, `[[macro-strategy]]`, `[[macro-indicators-hub]]`, `[[schedule-calendar-hub]]`)는 suffix 기반으로 cross-domain 식별되어 자동 수정 대상 아님. P7 패턴 정상 작동.

## 2026-07-01 (P9 패턴 출현)

`hermes-trading-hub.md`에서 bare-name wikilink 25개 발견 — 모두 unique basename 매칭으로 `[[people/aiprofit]]` 등 prefix 추가하여 auto-fix.

## 2026-06-30 (P7/P8 패턴 출현)

- P7: `hermes-trading-hub.md`의 4개 cross-domain wikilink — suffix(`-hub`, `-strategy`)로 식별.
- P8: `AGENTS.md`의 `[[link]]` 같은 문법 예시가 코드 블록 안에 있을 때 broken으로 오탐.

## 2026-06-29 (P1-P6 + 2a-bis)

- P1: assume-unchanged 인덱스 오염 — `hermes-trading-hub.md`가 58ddec3에서 삭제됐는데 index에 assume-unchanged로 남음.
- P2: dawn-wiki-auto-stash 잔재.
- 2a-bis: 깨진 markdown 링크 검사 추가.
