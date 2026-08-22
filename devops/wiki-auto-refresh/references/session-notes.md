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

## 2026-07-09 (P14 검증 + 신규 untracked 등록)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 0 broken, 4 cross-domain (P7, 의도된 외부 참조), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: 1 REAL MISSING — `raw/2026-W28-weekly-recap-draft.md`.

**발견:**
- `git status`에 `?? raw/2026-W28-weekly-recap-draft.md` (untracked) — 2026-W28 주간 회고 자동 생성 초안.
- raw/ 섹션은 PAT B (plain text bullet) 형식 — P14 false-positive 후보였지만 실제로는 진짜 미등록.
- index-md-audit.py의 PAT A+B+C 통합 매치가 raw/ 섹션의 PAT B도 정상 커버 → P14 fix 검증 성공.

**적용:**
- index.md raw/ 섹션에 PAT B 형식으로 등록: `- 2026-W28-weekly-recap-draft (raw/2026-W28-weekly-recap-draft.md) — 🆕 2026-W28 주간 회고 초안 (publish 전 사용자 확인 대기)`
- commit `1a17ddb auto-sync 2026-07-09 21:00 KST: register raw/2026-W28-weekly-recap-draft in index.md` (2 files, +28).
- push 성공 (774fe69..1a17ddb).

**Cross-domain (유지):** 4개 (harness-engineering-hub, macro-strategy, macro-indicators-hub, schedule-calendar-hub).

**Wiki 상태 (2026-07-09):**
- 65개 wiki 페이지 (submodule 제외), index.md 등록 64.
- 0 broken wikilink, 0 broken markdown link, 0 P11 sibling cross-ref.
- 1 untracked → 등록 처리.
- 0 stale (30일+) — 신규 draft만 +0일.

## 2026-07-10 (변경 없음)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 62 files, 0 broken, **4 cross-domain (P7, 의도된 외부 참조 — harness-engineering-hub, macro-strategy, macro-indicators-hub, schedule-calendar-hub)**, 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: 등록 65 (PAT A+B+C), 실제 64. 유일한 차이는 AGENTS.md/SCHEMA.md (의도된 제외) + `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` (P13/SNAPSHOT 예외, `hermes-memory-pipeline.md`에서 wikilink로 참조).

**발견:**
- `git status` clean, `git stash list` empty, origin/main과 up-to-date.
- untracked .md 0건.
- P15 의심 raw/ 신규 파일: 없음 (W28 draft는 2026-07-09에 이미 등록됨).
- P7 cross-domain 4건 모두 위치/섹션 정상:
  - `hermes-trading-hub.md:17` — Harness Engineering 행
  - `:43` — Macro Strategy Framework (cross-domain 명시)
  - `:69`, `:70` — 거시경제 지표 / 경제지표 캘린더

**적용:**
- 없음. 변경 사항 0건, commit/push 불필요.

**Wiki 상태 (2026-07-10):**
- 64개 wiki 페이지 (submodule 제외), index.md 등록 64 (1:1 일치, AGENTS/SCHEMA 제외 후).
- 0 broken wikilink, 0 broken markdown link, 0 orphan, 0 stale (30일+).
- 4 cross-domain (P7) 정상 유지.
- push: 없음.

## 2026-07-13 (날짜 메타데이터 보강)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 62 files, 0 broken, 4 cross-domain (P7), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: REAL MISSING 0, snapshot 예외 `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` 1건. AGENTS.md/SCHEMA.md dead-link 표시는 index의 의도된 스키마 참조로 확인.

**발견/적용:**
- orphan 0건, P13 multi-page `architecture/how-to-use-hermes/` 9개 sibling 모두 index에 등록됨.
- 날짜 필드 누락 14개 중 raw/sync 불변 원본 6개는 유지.
- 30일 미만이며 git 최종 커밋일이 확인된 operational 문서 8개에 `updated:` 자동 채움:
  - architecture 3개 (`5-stage-verify`, `memory-to-wiki-watcher-design`, `speculation-cascade-rule`)
  - infra 5개 (`bot-architecture`, `github-pr-automation-policy`, `hermes-config-sync`, `pr-review-policy`, `system-watchdog-disk`)
- YAML safe_load, `git diff --check`, audit 3종 재실행 모두 통과.

**Stale:**
- 30일+ 17개 (analysis 5, architecture 2, code 1, infra 5, people 1, solopreneur 2, watchlist 1). 내용 검토 없이 날짜만 갱신하지 않고 수동 확인 대상으로 유지.
- 날짜 정보 없음 6개: raw 5 + raw/sync snapshot 1 (불변 원본/예외라 자동 수정하지 않음).

**Git:**
- commit `6c71912 auto-sync 2026-07-13 21:00 KST: fill recent updated dates` (8 files, +8).
- `git pull --rebase origin main` 후 push 성공 (`e550c5d..6c71912`).
- 최종 local/remote SHA 일치, ahead/behind 0/0, working tree clean, stash empty.


## 2026-07-16 (변경 없음)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 62 files, 0 broken, 4 cross-domain (P7, 의도된 외부 참조), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: 등록 63 (PAT A+B+C), 실제 64. snapshot 예외 `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` 1건. AGENTS.md/SCHEMA.md 의도된 제외.

**발견:**
- `git status` clean, `git stash list` empty, origin/main과 up-to-date.
- untracked .md 0건, auto-fill candidate 0건.
- P7 cross-domain 4건 정상 유지.
- 18개 stale (30일+, 사람 검토 대기): analysis 5, architecture 3 (ssot-single-source-of-truth 신규 진입), code 1, infra 6 (apify-mcp-supabase-automation 신규 진입), people 1, solopreneur 2.

**적용:**
- 없음. 변경 사항 0건, commit/push 불필요.

**Wiki 상태 (2026-07-16):**
- 64개 wiki 페이지 (submodule 제외), index.md 등록 63 (1:1 일치, AGENTS/SCHEMA 제외 후, snapshot 예외 1).
- 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 4 cross-domain (P7) 정상 유지.
- 18 stale (30일+, 수동 확인 대기).
- push: 없음.

## 2026-07-17 (index 등록 2건 + updated 자동 채움)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 67 files, 0 broken, 4 cross-domain (P7), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: REAL MISSING 2건 — `analysis/portfolio-postmortem-20260717.md`, `infra/selfheal-discord-thread-expiry.md`.

**발견/적용:**
- 2개 페이지 index.md에 등록 (infra/ + analysis/ 섹션).
- 신규 operational 페이지 2개에 `updated: 2026-07-17` 자동 채움 (frontmatter 삽입).
- 0 broken wikilink, 0 broken markdown link, 0 dead link.
- YAML safe_load + git diff --check + 3종 audit 재검증 모두 통과.

**Stale:**
- 30일+ 18개 (변동 없음 — 직전 실행과 동일).
- 날짜 정보 없음: 8개 (raw/ 6개 불변 예외 유지, 2개는 금일 자동 채움 처리).

**Git:**
- commit `d36802c auto-sync 2026-07-17 21:00 KST: register portfolio-postmortem and selfheal-discord-thread-expiry in index.md, fill updated dates` (3 files, +10).
- `git pull --rebase origin main` 후 push 성공 (`422914b..d36802c`).
- 최종 local/remote SHA 일치, ahead/behind 0/0, working tree clean, stash empty.

## 2026-07-19 (weekly cleanup — SCHEMA.md tag taxonomy 확장 + logs/index 수정)

**사전 점검 (3종 audit — lint 8종 직접 실행):**
- Lint ① (orphan): 2건 — `raw/2026-W29-weekly-recap-draft.md` (신규 draft, 정상), `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` (복제본, duplicate 표시).
- Lint ② (broken wikilink): 0건 ✅
- Lint ③ (index 누락): 0건 ✅ (false positive: index.md 자체만 — 정상)
- Lint ④ (frontmatter): research/ 3개 전부 유효 ✅
- Lint ⑤ (stale): 0건 (research/ 전부 90일 미만) ✅
- Lint ⑥ (모순): 0건 ✅
- Lint ⑦ (품질): 0건 (low confidence 없음) ✅
- Lint ⑧ (tag audit): **40개 파일**에서 미등록 태그 발견 ⚠️

**발견/적용:**
- tag audit ⑧: 대부분 infra/ (mcp, bot, messaging, auth 등), analysis/ (pipeline, stock), architecture/ (hermes, verify)에 집중.
  - **선택: 개별 수정 ❌, SCHEMA.md taxonomy 확장 ✅** — 29→55개 태그로 확장 (판단 프레임워크에 따라).
  - SCHEMA.md operational 태그 표에 26개 태그 추가 배치.
  - SCHEMA.md 테이블 `||` double pipe 형식에 patch 오염 발생 → `|||` triple pipe 발생 후 전체 블록 rewrite로 복구 (P18 심화).
- logs/index.md: 4개 root-level 파일 누락 발견 (`2026-06-10-2115.md`, `2026-07-17-selfheal-discord-thread.md`, `2026-07-17-selfheal-fundamental-fix.md`, `hermes-logs-hub.md`).
  - July + June 테이블에 항목 추가, June 역순 정렬, 허브/기타 섹션 신설.
  - logs submodule commit + push (master) + parent submodule pointer commit.
- raw/sync/ duplicate: frontmatter에 `duplicate_of: architecture/memory-snapshots/...` 표시, canonical 위치 명시.
- `infra/` 디렉토리 (21개 파일): index.md와 전부 일치 ✅.

**Git:**
- hermes-wiki (main): `ccd1952 weekly-cleanup 2026-W29: SCHEMA.md tag taxonomy 확장, logs/index.md 수정, raw/sync duplicate 정리` (4 files, +47/-16).
- hermes-logs (master): `43d2316 weekly-cleanup: logs/index.md 업데이트 (+ self-heal log entries)` (3 files, +65/-16).

**교훈:**
- **tag audit 대량 발견 시 taxonomy 확장이 개별 수정보다 40x 효율적.** 판단 프레임워크 명문화 필요 → SKILL.md v1.14.0에 2c-bis 추가.
- **SCHEMA.md 테이블 `||` double pipe 형식은 patch 오염 위험 높음.** 확실하지 않으면 전체 블록 rewrite.
- **logs submodule index는 주기적으로 확인 필요** — 4개가 누락되어 있었음. SCHEMA.md lint에 포함되지 않는 영역이므로 별도 절차 필요 → SKILL.md v1.14.0에 2c-ter 추가.

## 2026-07-20 (W29 weekly-recap-draft 등록)

**사전 점검 (3종 audit 스크립트):**
- wikilink-audit.py: 68 files, 0 broken, 4 cross-domain (P7), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: REAL MISSING 1건 — `raw/2026-W29-weekly-recap-draft.md`.

**발견/적용:**
- `raw/2026-W29-weekly-recap-draft.md` tracked 상태지만 index.md 미등록 — PAT B 형식으로 raw/ 섹션에 등록 (2026-W28과 동일한 형식).
- YAML/diff/3종 audit 재검증 모두 통과.
- 0 broken wikilink, 0 broken markdown link, 0 dead link, REAL MISSING 0 (등록 완료).

**Stale:**
- 30일+ 18개 (변동 없음 — analysis 5, architecture 3, code 1, infra 5, people 1, solopreneur 2).

**Git:**
- commit `1dd3728 auto-sync 2026-07-20 21:00 KST: register raw/2026-W29-weekly-recap-draft in index.md` (1 file, +1).
- push 성공 (`ccd1952..1dd3728`).

## 2026-07-26 (주간 정리 — W30 등록, 중복 raw/sync 삭제, memory 비활성화 확인)

**사전 점검:**
- Memory tool: 환경에서 **비활성화됨** (config disabled) — 정리 불필요. wiki-architecture pitfall 8.5 재확인.
- User profile: 동일하게 비활성화 — 정리 불필요.

**발견/적용:**
- INDEX.md 누락: `raw/2026-W30-weekly-recap-draft.md` — 파일은 존재하나 index.md raw/ 섹션에 미등록. PAT B 형식으로 등록 (W28/W29와 동일 패턴).
- 중복 파일: `raw/sync/2026-07-02-2109-a-step-3-watcher--.md` — frontmatter에 `status: duplicate` 명시되어 있고, `architecture/memory-snapshots/`에 canonical 버전 존재. **삭제 완료** + 빈 `raw/sync/` 디렉토리 정리.
- Patch 포맷 이슈: index.md의 raw/ 섹션에 W30을 추가할 때 `- W29-weekly-recap-draft`가 2회 등장해 "Found 2 matches" 오류. 해결: 앞선 `memory-pipeline-design` 라인을 old_string에 포함시켜 unique 매치 확보. (P18 관련 — read_file 출력 line number 파싱 주의.)

**Wiki 상태 (2026-07-26):**
- 133개 wiki 파일 (logs + raw + subagents-library 포함). infra/ 21개 페이지 — index.md와 100% 일치.
- Memory: 비활성화 (추가 정리 불필요).
- `raw/sync/` duplicate: 해소 완료 (이전 2026-07-19 세션에서 발견, 1주간 방치 후 금일 삭제).

**교훈:**
- 주간 WXX draft 등록 패턴이 3주째 반복됨 (W28→W29→W30). raw/ 섹션의 PAT B 등록은 안정적으로 작동.
- `raw/sync/` duplicate는 2026-07-19에 발견됐으나 삭제되지 않고 1주 방치됨. **주의: 발견 시 즉시 삭제할 것** — 발견-처리 간격이 길어질수록 다른 cron이 같은 duplicate를 다시 찾아내는 중복 노동이 발생.
- Memory 비활성화는 이 cron 환경의 고정 특성. 주간 정리에서 memory 부분은 항상 skip.

## 2026-07-22 (tag audit fix — ax/hr/pm-prd-fast 제거, taxonomy SCHEMA 등록, gmail-himalaya updated: 채움)

**사전 점검 (4종 audit 스크립트):**
- wikilink-audit.py: 68 files, 0 broken, 4 cross-domain (P7), 0 P9/P10.
- markdown-link-audit.py: 0 broken, P11 0건.
- index-md-audit.py: 등록 69 (PAT A+B+C), 실제 70. snapshot 예외 `raw/sync/...` 1건.
- tag-audit.py: **4 unknown** — `ax` (1 file), `hr` (1 file), `pm-prd-fast` (1 file), `taxonomy` (1 file, SCHEMA.md).

**발견/적용:**
- 자동화 스크립트 `auto-fill-dates.py`가 P16 위반 — `updated:`가 이미 있는 38개 파일에 중복 `updated: 2026-07-21`을 추가. 사람이 직접 38개 revert. **=> auto-fill-dates.py 수정 필요 (기존 updated: 감지 후 skip).**
- tag audit: `ax`/`hr` → `architecture/ssot-single-source-of-truth.md`에서 제거 (1-file niche tag, `ssot`+`data-architecture`+`organization`으로 충분).
- tag audit: `pm-prd-fast` → `infra/project-harness.md`에서 제거 (1-file 외부 방법론명, `workflow`+`project-management`로 충분).
- tag audit: `taxonomy` → SCHEMA.md taxonomy 루트 태그에 추가 (운영상 유효한 루트 태그).
- genuine missing `updated:`: `infra/gmail-himalaya.md`에 `updated: 2026-07-06` 채움 (git log 기반, 16일 < 30일 threshold).

**Verification:**
- 4종 audit 모두 ✅ (unknown 0, broken 0).
- YAML safe_load + git diff --check ✅ (whitespace error 없음).
- 0 dead link, 0 real missing.

**Stale (30일+ 명시적 날짜):**
- 8개 (2026-07-20 기록 18개에서 감소 — 다수는 auto-fill로 "fresh"가 아니라, 이전 실행에서 이미 updated:가 있던 파일이 대부분).
- 실제 stale: architecture 3 (hybrid-ai-stack 48d, hermes-vs-chatbot 44d, ssot 36d), solopreneur 2 (upwork 43d, freelancing 43d), infra 3 (higgsfield 44d, apify 36d, obsidian 47d). 수동 확인 보류.

**Git:**
- commit `cf2fe1a auto-sync 2026-07-22 21:00 KST: fix unknown tags (ax/hr/pm-prd-fast→remove, taxonomy→add), fill gmail-himalaya updated: date` (4 files, +4/-3).
- push 성공 (`8771356..cf2fe1a`).
- 최종 local/remote SHA 일치, ahead/behind 0/0, working tree clean, stash empty.

## 2026-07-28 (index.md P18 복구 + 신규 infra 페이지 등록 + SCHEMA taxonomy 확장 + logs submodule 7건 등록)

**사전 점검 (5종 audit 스크립트):**
- wikilink-audit.py: 70 files, 0 broken, 4 cross-domain (P7), 0 P9/P10 ✅
- markdown-link-audit.py: 0 broken, P11 0건 ✅
- index-md-audit.py: 등록 127 (PAT A+B+C), 실제 72. submodule logs/subagents-library dead link만 (의도된 제외). **0 real missing** ✅
- tag-audit.py: 145 taxonomy, 137 used, **4 unknown** ⚠️ (`docker`, `management`, `self-improvement`, `meta` in 2 new infra files)
- auto-fill-dates.py: 0 filled (모든 existing 페이지에 updated: 있음)

**발견/적용:**
- **P18 pipe 오염**: `index.md` lines 54-55 `||- [hermes-config-sync]`, `||- [hermes-management]` → `|- `로 복구. `infra/cron-jobs.md` lines 405-406 동일 오염 복구.
- **잘못된 submodule 항목 제거**: index.md 하단에 `logs/` 및 `subagents-library/` 55개 항목이 "자동 추가"로 대량 삽입됨 (self_hermes.py 추정). 서브모듈이므로 전부 제거.
- **신규 untracked 등록**: `infra/hermes-management.md` (Docker 인프라 저장소) + `infra/self-hermes.md` (Self-Improving Hermes Engine) — index.md infra/ 섹션에 정식 등록.
- **SCHEMA.md taxonomy 확장 (+4):** `docker`, `management`, `self-improvement`, `meta`를 infra row에 추가.
- **logs submodule**: 7개 July 7 로그 파일이 logs/index.md에 미등록 (1734-wiki-lint-8-run ~ 2400-pr-2tier-policy). 역시간순 정렬하여 July 테이블에 추가 + commit/push.

**Git:**
- hermes-wiki (main): commit `b59c603` (5 files, +175/-1 — index.md/cron-jobs P18 fix + SCHEMA taxonomy + 2 new infra pages).
- hermes-wiki (main) 2nd: commit `5e5e06a` (logs submodule pointer bump).
- hermes-logs (master): commit `b45a091` (logs/index.md +7 rows).
- push 성공 (main + master). 최종 up-to-date.

**Wiki 상태 (2026-07-28):**
- 72개 wiki 페이지 (submodule 제외), index.md 등록 72 (1:1 일치).
- 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 4 cross-domain (P7) 정상 유지.
- SCHEMA.md taxonomy: 149 tags (145→+4), 0 unknown ✅.

## 2026-07-29 (P19 rogue submodule + P18 pipe fix)

**발견:**
- P19 — `self_hermes.py`가 index.md 하단에 submodule 경로(logs/ 49개 + subagents-library/ 5개) markdown link 54개 + `infra/self-hermes.md` 1개를 `— 자동 추가 (2026-07-29)` 레이블로 대량 삽입 (총 55개).
- P18 — 동시에 index.md raw/ 섹션 4개 줄에 `|- ` pipe corruption (P19 부수 효과).

**적용:**
- P19 복구: rogue 항목 55개 전부 index.md에서 제거.
- P18 복구: 4개 줄 `|- ` → `- ` 치환.
- auto-fill-dates.py: `infra/hermes-management.md` + `infra/self-hermes.md` → `updated: 2026-07-28` 추가.

**Commit:** `9ae9fbf` auto-sync 2026-07-29 21:00 KST (3 files, +7/-5).
- Push 성공. main up-to-date.

**Wiki 상태 (2026-07-29):**
- 72개 wiki 페이지, index.md 등록 72 (1:1 일치).
- 0 broken wikilink, 0 broken markdown link, 0 orphan.
- 4 cross-domain (P7) 정상 유지.
- SCHEMA.md taxonomy: 149 tags, 0 unknown ✅.
- updated: auto-fill 2건 완료.

## 2026-07-30

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 55개를 "자동 추가 (2026-07-30)" 레이블로 대량 삽입 (subagents-library 5 + logs 50).
- 이번에는 working tree 오염에 그침 (HEAD에는 미반영).

**적용:**
- P19 복구: rogue 항목 55개 전부 index.md에서 제거 (working tree clean으로 복원).
- commit/push 불필요 (HEAD가 이미 깨끗).

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 72 = 72 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅.
- auto-fill-dates.py: 0 filled, 7 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- logs/index.md: 13개 May 31 파일 wildcard로 커버 ✅.
- git status: clean, up-to-date with origin/main.

## 2026-07-31 (P19 4회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단(134~188줄)에 서브모듈 항목 55개를 "자동 추가 (2026-07-31)" 레이블로 대량 삽입 (subagents-library 5 + logs 50). 07-28/29/30에 이어 4일 연속 동일 패턴.
- 이번에도 working tree 오염에 그침 (HEAD에는 미반영 — `git show HEAD:index.md` tail 정상).
- P18 pipe 오염: 0건 (이번엔 부수 효과 없음).

**적용:**
- P19 복구: `git checkout HEAD -- index.md`로 working-tree 전용 오염 제거.
- 검증: `git diff HEAD -- index.md` 0줄 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 72 = 72 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 7 skipped (raw/ immutable) ✅.
- logs/index.md: 13개 May 31 파일 wildcard(`[2026-05-31-*]`)로 커버 확인 ✅.
- git status: clean, up-to-date with origin/main.

## 2026-08-03 (P19 5회 연속 재발 — committed 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단(135~190줄)에 서브모듈 항목 56개를 "자동 추가 (2026-08-01)" 레이블로 삽입 (subagents-library 5 + logs 50 + raw W31 1).
- **이번엔 committed 오염** — HEAD와 origin/main(d9fe56d) 모두에 반영됨. `git show HEAD:index.md`에서 56개 확인. (07-30/31은 working-tree 전용이었으나 이번엔 weekly cleanup/Linear docs 커밋에 편승해 push됨)
- P18 pipe 오염: index.md 2건 (`|- [hermes-management]`, `|- [linear-hermes-project]` 55~56줄). infra/cron-jobs.md는 깨끗.
- tag-audit: `project` 1건 미등록 (infra/linear-hermes-project.md).
- logs submodule: `2026/2026-08-02-0700-weekly-cleanup.md`가 logs/index.md에 누락 (find 검사로 발견).

**적용:**
- P19 복구: rogue 항목 56개 전부 index.md에서 제거 (patch로 footer 이후 블록 전체 삭제).
- P18 복구: 2줄 `|- ` → `- ` 치환.
- raw/2026-W31-weekly-recap-draft.md 정식 재등록 (raw/ 섹션 PAT B, W28~W30과 일관).
- tag fix: `project` → `project-management` (1-file → 개별 페이지 수정 원칙).
- auto-fill-dates: `infra/linear-hermes-project.md`에 `updated: 2026-08-03` 1건 채움, raw/ 8건 immutable skip.
- logs: index.md August 섹션 신설 + 08-02 weekly cleanup 등록 → submodule commit `163a5c5` push (master).

**Commit:** `ebaec02` auto-sync 2026-08-03 21:00 KST (3 files, +7/-61). Push 성공 (d9fe56d..ebaec02). 미푸시 2건(971627a, 4c73f5e) 포함 전부 push 완료.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 74 = 74 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 1 filled, 8 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅.
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard + 08-02 신규 등록).

## 2026-08-04 (P19 6회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 56개를 "자동 추가 (2026-08-04)" 레이블로 대량 삽입 (subagents-library 5 + logs 50 + raw W31 1). 07-28~08-03에 이어 6일 연속 동일 패턴.
- 이번에도 working tree 오염에 그침 (HEAD 미반영 — `git show HEAD:index.md` footer 정상, `git diff HEAD --stat` +57/-1).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean.

**적용:**
- P19 복구: `git checkout HEAD -- index.md`로 working-tree 전용 오염 제거 (56개 rogue 항목).
- 검증: `git diff HEAD -- index.md` 0줄 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 74 = 74 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 8 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅.
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-05 (P19 7회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 56건을 "자동 추가 (2026-08-05)" 레이블로 대량 삽입 (subagents-library 5 + logs 51). 07-28~08-04에 이어 7일 연속 동일 패턴.
- 이번에도 working tree 오염에 그침 (HEAD 미반영 — `git show HEAD:index.md` '자동 추가' 0건, `git diff HEAD --stat` +57/-1).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (56개 rogue 항목).
- 검증: `git diff HEAD -- index.md` 0줄 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 74 = 74 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 8 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅.
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-06 (P19 8회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 56건을 "자동 추가 (2026-08-06)" 레이블로 대량 삽입 (subagents-library 5 + logs 51). 07-28~08-05에 이어 8일 연속 동일 패턴.
- 이번에도 working tree 오염에 그침 (HEAD 미반영 — `git show HEAD:index.md` '자동 추가' 0건, `git diff HEAD --stat` +57/-1).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (56개 rogue 항목).
- 검증: `git diff HEAD -- index.md` 0줄 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 74 = 74 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 8 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅.
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-07 (P19 9회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-07)" 레이블로 대량 삽입 (subagents-library 5 + logs 52). 07-28~08-06에 이어 9일 연속 동일 패턴.
- 이번에도 working tree 오염에 그침 (HEAD 미반영 — `git show HEAD:index.md` '자동 추가' 0건, `git diff HEAD --stat` +57/-1).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (57개 rogue 항목, 1.22.0 빠른 복구 경로).
- 검증: `git diff HEAD -- index.md` 0줄 → commit/push 불필요.

## 2026-08-10 (P19 10회 연속 재발 — committed 오염 복구 + push)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-08)" 레이블로 대량 삽입 (subagents-library 5 + logs 51 + raw W32 1). 07-28~08-09에 이어 10일 연속 동일 패턴.
- 이번엔 **committed 오염** — 08-08 오염분이 08-09 weekly cleanup 커밋(55a0768)에 편승해 HEAD와 origin/main 모두에 반영됨. `git status` clean이어도 `git show HEAD:index.md` '자동 추가' 57건 확인 (index-md-audit dead link 56건이 logs/·subagents-library/ 경로 → P19 의심).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git show ebaec02:index.md > index.md`로 committed 오염 제거 (57개 rogue 항목) — HEAD~1(ebaec02)이 깨끗함을 `grep -c '자동 추가'`=0으로 확인 후 이전 버전 복원 (57줄 patch의 P18/P20 위험 회피).
- raw/2026-W32-weekly-recap-draft.md는 실제 파일(08-07 생성)이므로 raw 섹션에 PAT B로 정식 재등록 (W28~W31 패턴과 동일, 🆕 마커 포함).
- commit `d9c577a` (1 file, +2/-58), push `55a0768..d9c577a` ✅.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 75 = 75 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 9 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅.
- P19 scan: index.md '자동 추가' 0건 ✅.
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-11 (P19 11회 연속 재발 — working-tree 전용 오염 복구 + P18 committed 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-11)" 레이블로 대량 삽입 (subagents-library 5 + logs 52). 07-28~08-10에 이어 11일 연속 동일 패턴. 이번엔 **working-tree 전용** (HEAD/origin/main 모두 '자동 추가' 0건).
- P18 pipe 오염: index.md 58-59행 `|- ` 2건 (linear-hermes-project, dev-harness-kit-daily-review) — **committed 상태** (39f01b2에서 도입, 아직 미push).
- session-notes.md: 08-10 섹션 뒤에 08-07 감사 결과 블록(74=74) 중복 복사 (P20 패턴) — 제거.

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (57개 rogue 항목, 빠른 복구 경로). 검증: `git diff HEAD -- index.md` 0줄.
- P18 복구: index.md 58-59행 `|- ` → `- ` (patch 2건).
- session-notes 중복 블록 제거 (594-603행, 08-07 감사 결과 74=74).
- tag fix: infra/dev-harness-kit-daily-review.md `dev-harness-kit` → `harness` (1-file 미등록 태그, taxonomy에 harness 기존 존재 — 2026-08-03 project→project-management 사례와 동일 패턴).
- auto-fill-dates: infra/dev-harness-kit-daily-review.md에 `updated: 2026-08-11` 채움 (1건).

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 76 = 76 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 1 filled, 9 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-12 (P19 12회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-12)" 레이블로 대량 삽입 (subagents-library 5 + logs 52). 07-28~08-11에 이어 12일 연속 동일 패턴. 이번엔 **working-tree 전용** (HEAD/origin/main 모두 '자동 추가' 0건, diff가 rogue 추가분 + newline 변경뿐 — raw/ 실제 파일 혼입 없음).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (57개 rogue 항목, 빠른 복구 경로). 검증: `git diff HEAD -- index.md` 0줄, `grep -c '자동 추가'` 0건 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 76 = 76 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 9 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-13 (P19 13회 연속 재발 — working-tree 전용 오염 복구 + 미push 커밋 동기화)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-13)" 레이블로 대량 삽입 (subagents-library 5 + logs 52). 07-28~08-12에 이어 13일 연속 동일 패턴. 이번엔 **working-tree 전용** (HEAD/origin/main 모두 '자동 추가' 0건, diff가 rogue 추가분뿐 — raw/ 실제 파일 혼입 없음).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).
- 미push 커밋 1건 발견: 58d2395 (infra/dev-harness-kit-daily-review.md, 08-12 생성) — index.md 오염 없음, 정상 커밋.

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (57개 rogue 항목, 빠른 복구 경로). 검증: `git diff HEAD -- index.md` 0줄, `grep -c '자동 추가'` 0건 → commit 불필요.
- git pull --rebase + push: `189721a..58d2395` (미push 커밋 58d2395 동기화).

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 76 = 76 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 9 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-14 (P19 14회 연속 재발 — working-tree 전용 오염 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 57건을 "자동 추가 (2026-08-14)" 레이블로 대량 삽입 (subagents-library 5 + logs 52). 07-28~08-13에 이어 14일 연속 동일 패턴. 이번엔 **working-tree 전용** (HEAD/origin/main 모두 '자동 추가' 0건, diff가 rogue 추가분 + newline 변경뿐 — raw/ 실제 파일 혼입 없음).
- P18 pipe 오염: 0건 (부수 효과 없음). logs submodule: clean (May 31 wildcard 커버로 2c-ter 누락 아님).

**적용:**
- P19 복구: `git restore index.md`로 working-tree 전용 오염 제거 (57개 rogue 항목, 빠른 복구 경로). 검증: `git diff HEAD -- index.md` 0줄, `grep -c '자동 추가'` 0건 → commit/push 불필요.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 76 = 76 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 9 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).

## 2026-08-17 (P19 15회 연속 재발 — committed+push 오염 복구, 첫 04:00 auto-sync 편승)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 58건을 "자동 추가 (2026-08-16)" 레이블로 대량 삽입 (subagents-library 5 + logs 53). 07-28~08-16에 이어 15일 연속 동일 패턴. 이번엔 **committed + pushed** — 08-17 04:00 auto-sync 커밋 `d36d3b3`이 footer 뒤 rogue 58건을 추가·push (HEAD + origin/main 모두 58건). 08-16 weekly cleanup `076bafb`가 전날 58줄 제거했지만 4시간 뒤 auto-sync가 재오염시킴 → **P19 오염이 매일 2회 실행(04:00/21:00) 중 어느 쪽에도 편승 가능하다는 첫 사례**.
- P18 pipe 오염: 0건. logs submodule: clean. untracked: 없음 (raw W34 draft 미발생, W33은 076bafb에서 이미 등록).

**적용:**
- P19 복구 (committed 경로): `git show 076bafb:index.md` 청정(0건) 확인 + `d36d3b3` diff가 rogue 추가분뿐(비-rogue 추가 0건) 확인 → `git show 076bafb:index.md > index.md`로 parent 복원 (58건 제거, 59줄 삭제).
- commit `4afdc74` (1 file, -59), push `d36d3b3..4afdc74`. origin/main '자동 추가' 0건 확인.
- P20 주의: session-notes append 시 08-14 헤더~끝 전체를 유일 앵커로 사용.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 77 = 77 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 10 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean, index 일치 (May 31 wildcard 커버 확인).
- stale 30일+: 60개 (참고 — 명시적 날짜 기준, 자동 수정 안 함).

## 2026-08-18 (P19 16회 연속 — working-tree 전용 오염, git restore로 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 58건을 "자동 추가 (2026-08-18)" 레이블로 대량 삽입 (subagents-library 5 + logs 53). 07-28~08-18에 이어 16일 연속 동일 패턴.
- **이번은 committed 아님** — HEAD(4afdc74) + origin/main 모두 0건. working-tree 전용 오염으로 `git restore index.md`로 간단히 복구.
- P18 pipe 오염: 0건. P18 cross-file scan: 0건. untracked: 없음.

**적용:**
- `git restore index.md`로 복구 (rogue 58건 제거).
- 모든 감사 통과 — 변경 없음.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 77 = 77 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 10 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean ( submodule pointer 변경 없음).

**Git:** 변경 없음 — git commit/push 불필요.

## 2026-08-21 (P19 17회 연속 — working-tree 전용 오염, git restore로 복구)

**발견:**
- P19 재발 — `self_hermes.py`가 index.md 하단에 서브모듈 항목 ~50건을 "자동 추가 (2026-08-21)" 레이블로 대량 삽입 (logs/ 항목 중심). 07-28~08-21에 이어 17일 연속 동일 패턴.
- **이번은 committed 아님** — HEAD(4afdc74) + origin/main 모두 0건. working-tree 전용 오염으로 `git restore index.md`로 간단히 복구.
- P18 pipe 오염: 0건. P18 cross-file scan: 0건. untracked: 없음.

**적용:**
- `git restore index.md`로 복구 (rogue ~50건 제거).
- 모든 감사 통과 — 변경 없음.

**감사 결과 (모두 통과):**
- wikilink-audit.py: 0 broken, 0 bare-name, 0 .md-ext, 4 cross-domain (P7) ✅.
- markdown-link-audit.py: 0 broken, 0 P11 ✅.
- index-md-audit.py: 77 = 77 (1:1 일치), 0 dead link ✅.
- tag-audit.py: 137/137 registered, 0 unknown ✅ (taxonomy 149).
- auto-fill-dates.py: 0 filled, 10 skipped (raw/ immutable) ✅.
- P18 cross-file scan: 0 실제 오염 ✅ (wiki + 스킬 references).
- P19 scan: index.md '자동 추가' 0건 ✅ (HEAD + origin/main).
- git status: clean, up-to-date with origin/main.
- logs submodule: clean (submodule pointer 변경 없음).

**Git:** 변경 없음 — git commit/push 불필요.
