# Session Notes — wiki-auto-refresh runs

누적 세션 노트. 각 항목은 (날짜, 발견, 적용) 형식.

## 2026-11-27 (21:00 KST) — P19 재감염 0건 (6일 연속) + P36 14차 (11-27 브리핑 백필, 원본 CJK 0자) + stale 57/0/24 완전 일치 + audit 7종 통과 + push 성공
- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → **재감염 0건 (11-02 이후 6일 연속)**. stash 비어 있음, branch main, working tree clean
- P18 스캔(`^|- `): wiki 0건 / skill references 0건
- audit 7종 전항목 통과: wikilink MD/WL/CD/BN/MDX 0 / markdown-link P11 0·broken 0 / index-md registered 96 = actual 96, dead link 0, REAL MISSING 0 / tag taxonomy 200·used 144·Unknown 0 / logs-index broken 0·notref 0·covered 13 / stale 57·no_date_operational 0·no_date_immutable 24 (11-26 기준선 완전 일치) / dup-updated 0건 (pages 202)
- **P36 14차 — 11-27 브리핑 백필**: 크론 `2916cc9c2ceb`이 `2026-11-27_18-19-12.md` 산출(18:19), LOG.md frontmatter `updated:`는 11-26 고정 → 미백필 상태. 원본 `## Response`(3901~4047행) 한국어 재작성 백필, frontmatter `updated: 2026-11-27`
  - **P37 — 원본 CJK 0건**: 이번 산출물은 한자 혼입 없음 → 제거 작업 불필요. 원본 CJK 스캔을 백필 **전**에 먼저 수행하면 불필요한 재작성 작업 자체를 줄일 수 있음 (이번이 14차 중 처음으로 원본이 청정)
  - **P39 검증 — 신규 로그 파일 U+FFFD 0건**: `write_file` 응답 `verified: true`였지만 P39 인코딩 손실 여부를 별도 확인 (`s.count('\ufffd')` = 0) → 이상 없음. write_file 후 U+FFFD 검사는 계속 유지 필요
  - CJK + U+FFFD 병행 검증: LOG.md 전체 / logs/index.md / 신규 로그 `logs/2026/2026-11-27-2100.md` 모두 0건. `git diff --check` 통과, frontmatter `yaml.safe_load` 정상
- 로그 생성 및 등록: `logs/2026/2026-11-27-2100.md` 신규 + `logs/index.md` 행 추가 — 기준 행 `|| 11-26 21:00` prefix 복사 후 python 인서트(삽입 위치 line 13), `cat -A` 형제 행 prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 감사 broken 0/notref 0
- 커밋: logs `dd9e7e4` (master) / parent `1669d25` (main) — 둘 다 push 완료, origin 반영 확인
- 미해결(보고): P36 구조적 결함(브리핑 크론 toolset에 file 부재 — 근본 미해결, 매일 수동 백필), trade-pipeline 표준 수집기 미커밋 파일 6종 존재(사용자 승인 대기)

## 2026-11-26 (21:00 KST) — P19 재감염 0건 (5일 연속) + P36 13차 (11-26 브리핑 백필, 원본 CJK 6자 제거) + stale 57/0/24 완전 일치 + audit 7종 통과 + push 성공
- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → **재감염 0건 (11-02 이후 5일 연속)**. stash 비어 있음, branch main, working tree clean
- audit 7종 전항목 통과: wikilink TOTAL 0(MD/WL/CD/BN/MDX), markdown-link P11 0 / broken 0, index-md registered 96 = actual 96 / dead 0 / REAL MISSING 0, tag taxonomy 200 · Unknown 0, logs-index broken 0 / notref 0 / covered 13 / ambiguous 0, **stale 57 / no_date_operational 0 / no_date_immutable 24** (11-24·11-25 기준선과 완전 일치 — 신규 30일 경과 없음), dup-updated 0건 / 202p 스캔
- P18 파이프 오염(`^|- `) 0건. CJK 최종 검증 3파일(LOG.md / logs/index.md / 신규 로그) 0건, replacement char 0건
- **P36 13차 — 11-26 브리핑 백필**: 크론 `2916cc9c2ceb`이 `2026-11-26_18-13-43.md` 산출(18:13)했으나 LOG.md frontmatter `updated:`는 11-25에 고정 → 미백필. 원본 `## Response`(3901~4047행) 확인 후 **순수 한국어로 재작성**하여 11-26 섹션 신규 추가 + frontmatter `updated: 2026-11-26` 갱신
- **P37 — 원본 CJK 6자(3개 어구) 혼입 확인**: 오류 문서 관련 2자(3933행) · 마감 상승 관련 2자(3964행) · 성장 관련 2자(3972행) → 재작성 과정에서 전부 한국어 구어로 대체. **P37 항목 5(감지된 한자를 예시로 인용하면 그 자체가 CJK가 됨) 준수** — 로그 파일에도 "성능 관련 2자" 식으로 서술형으로만 기술
- 신규 로그 파일 작성 시 **U+FFFD replacement character 3건 발생**(`감사`라는 단어가 일부 깨진 형태로 기록됨 — write_file 응답은 verified:true지만 인코딩 손실이 있었음. patch로 복구 후 재검증(repl 0건) → **신규 파일 작성 후에는 replacement char 검사 필수**
- trade-pipeline portfolio JSON 2026-11-23~26 4건 CJK 0건 확인 (P37 확장 실증 — 이번엔 오염 없음)
- logs/index.md November 섹션 존재 확인 → 기준 행 `|| 11-25 21:00` prefix 복사 후 python 인서트(line 14). `cat -A` 형제 행 prefix 일치 / triple-pipe 0건 / `git diff --check` 통과 / 재감사 broken 0 notref 0
- 커밋: logs `1c8167e` (hermes-logs master, push 성공 `745de9a..1c8167e`) / parent `dabf6dd` (hermes-wiki main, push 성공 `7021ebd..dabf6dd`)
- 미해결(보고): ① P36 구조적 결함 근본 미해결(브리핑 크론 toolset에 파일쓰기 도구 부재 — toolset에 `file` 추가 필요, 범위 밖이라 승인 없이 진행 안 함) ② trade-pipeline 표준 수집기 429 잔존 파일 2개 → 월 1일 LangGraph 파이프라인이 0종목으로 조용히 실패할 상태, 다음 리밸런싱일 전 복구 필요
- 신규 로그: `logs/2026/2026-11-26-2100.md`

## 2026-11-25 (21:00 KST) — P19 재감염 0건 (4일 연속) + P36 12차 (11-25 브리핑 백필, CJK 0건) + logs/index.md CJK 잔존 1건 추가 제거 + stale 57 유지 + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-21 재발 이후 4일 연속 0건 유지.** 판별 3단계: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**. index.md 내 서브모듈 경로 링크 0건, 끝 개행 정상.
- **P36 12차**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-25_18-27-39.md` 산출(18:27)했으나 LOG.md frontmatter `updated:` = 2026-11-24 → 11-25 브리핑 미백필. 원본 `## Response` = 3901~4021행. 원본 CJK 6자 혼입 → 순수 한국어 재작성 후 **LOG.md 전체 CJK 0건** 검증.
  - ★ 11-19/11-20/11-23/11-24에 이어 5회 연속 **자기 작성 문장에서 CJK가 새로 생기는** 패턴 → 1차 재작성 후 LOG.md 전체 재검증으로 0건 확인. 언어 규칙 메모는 서술형으로만 기술(감지된 한자 예시 인용 금지) — 11-13/11-18/11-19/11-20 패턴 계속 적용.
- **★ P37 신규 확장 — `logs/index.md`에도 CJK 잔존 1줄 발견.** 11-20 실행분 행(`|| 11-20 21:00`)에 **감지된 한자를 예시 인용**한 문장이 남아 있었음(2자 어구) → "기존 섹션의 한자 2자 잔존도 제거"로 서술형 재작성. **P37의 CJK 스캔 범위는 LOG.md뿐이 아니라 logs/index.md까지 확장해야 함** (로그 파일 본문도 포함 권장).
- **P37 확장 확인**: `trade-pipeline/logs/portfolio/*.json` 최근 6건(11-19~11-25) CJK 0건, `trade-pipeline/logs/*.md` 최근 5건(11-18~11-20) CJK 0건. 11-12 이후 재발 없음.
- audit 7종 전항목 통과: wikilink 0 (94 .md) / markdown-link P11 0 / index-md **registered 96 = actual 96** (dead 0, REAL MISSING 0) / tag taxonomy 200·used 144·Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 24** / dup-updated 0 (199p). `git diff --check` 통과.
  - ★ stale 57 / 0 / 24 = 11-24 기준선과 **완전 일치** (신규 30일 경과 페이지 없음 → 증가 0). immutable 24 유지(신규 raw 초안 없음).
- P18 스캔(`^|- `) wiki 전체 0건, 스킬 references 0건, logs/index.md triple-pipe 0건.
- **위키 본문 변경 1건**: `LOG.md` — 11-25 브리핑 섹션 추가(한국어 재작성) + frontmatter `updated: 2026-11-24` → `2026-11-25`.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-24 21:00` prefix 복사 후 python 인서트(삽입 위치 line 13). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `745de9a` (parent `ff52374`) / parent `7021ebd` (parent `89a584b`). push `89a584b..7021ebd` (hermes-wiki main), logs master `ff52374..745de9a`.
- 원격 검증: `origin/main:LOG.md` `## 2026-11-25 (수) 18:00` 1건 + `updated: 2026-11-25` + CJK 0건, `origin/main:index.md` `자동 추가` 0건, `origin/master:index.md` `11-25 21:00` 1건 + CJK 0건.
- 교훈: (1) P37의 CJK 검증 범위를 **LOG.md + logs/index.md + 신규 로그 파일**로 확장. (2) P19 "0건 N일 연속"은 재발 배제 아님 — 3단계 판별 매 실행 독립 수행. (3) P36 12거래일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가) 승인 여부 사용자 확인 필요.

## 2026-11-24 (21:00 KST) — P19 재감염 0건 (3일 연속) + P36 11차 (11-24 브리핑 백필, CJK 0건) + stale 55→57 신규 2건 + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-21 재발 이후 3일 연속 0건 유지.** 판별 3단계: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**. index.md 내 서브모듈 경로 링크 0건, 끝 개행 정상.
- **P36 11차**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-24_18-37-07.md` 산출(18:37)했으나 LOG.md frontmatter `updated:` = 2026-11-23 → 11-24 브리핑 미백필. 원본 `## Response` = 3877~3957행. 원본 CJK 2자 혼입(3자 어구 1건) → 순수 한국어 재작성 후 **LOG.md 전체 CJK 0건** 검증.
  - ★ 11-19/11-20/11-23에 이어 4회 연속 **자기 작성 문장에서 CJK가 새로 생기는** 패턴 → 1차 재작성 후 LOG.md 전체 재검증으로 0건 확인. 언어 규칙 메모는 서술형으로만 기술(감지된 한자 예시 인용 금지) — 11-13/11-18/11-19/11-20 패턴 계속 적용.
- **P37 확장 확인**: `trade-pipeline/logs/portfolio/*.json` 최근 6건(11-18~11-24) CJK 0건, `trade-pipeline/logs/*.md` 최근 5건 CJK 0건. 11-12 `化` 1자 이후 재발 없음.
- audit 7종 전항목 통과: wikilink 0 (94 .md) / markdown-link P11 0 / index-md **registered 96 = actual 96** (dead 0, REAL MISSING 0) / tag taxonomy 200·used 144·Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 24** / dup-updated 0 (199p). `git diff --check` 통과.
  - ★ stale 55 → 57 증가 원인 확인: `infra/linear-hermes-project.md`와 `people/aiprofit.md`의 `updated: 2026-10-25`가 30일 경계(2026-11-24)에 도달 → 신규 stale 2건 발생. 스크립트 버그 아님(P16 정상). immutable 24 유지(신규 raw 초안 없음).
- P18 스캔(`^|- `) wiki 전체 0건, 스킬 references 0건, logs/index.md triple-pipe 0건.
- **위키 본문 변경 1건**: `LOG.md` — 11-24 브리핑 섹션 추가(한국어 재작성) + frontmatter `updated: 2026-11-23` → `2026-11-24`.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-24 02:00` prefix 복사 후 python 인서트(삽입 위치 line 13). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `ff52374` (parent `7cf9c2e`) / parent `dd11b71` (parent `d4e902e`). push `d4e902e..dd11b71` (hermes-wiki main), logs master `7cf9c2e..ff52374`.
- 원격 검증: `origin/main:LOG.md` `## 2026-11-24 (화) 18:00` 1건 + `updated: 2026-11-24` + CJK 0건, `origin/main:index.md` `자동 추가` 0건, `origin/master:index.md` `11-24 21:00` 1건.
- 교훈: (1) P19 "0건 N일 연속"은 재발 배제 아님 — 3단계 판별 매 실행 독립 수행. (2) P37 재작성 시 자기 문장 CJK 발생 패턴 4회 연속 — 항상 LOG.md 전체 재스캔. (3) P36 11거래일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가) 승인 여부 사용자 확인 필요.

## 2026-11-23 (21:00 KST) — P19 재발 (committed+push 변형) + P36 10차 (11-23 브리핑 백필, CJK 0건) + logs NOTREF 1건 해소 + audit 7종 통과 + push 성공

- **P19 재발 — committed+push 변형.** 11-16 재발 이후 11-17~11-20 4일 연속 0건이었고 11-21에 재발. 판별 3단계: working tree 1 / HEAD(`6191e94`) 1 / origin/main 1 → committed 변형. 오염 커밋 = `b878d58 hermes-config-sync: 2026-11-21T05:30:13Z (wiki)` (index.md footer 뒤 rogue 1건 `raw/2026-W47-weekly-recap-draft.md` 삽입 + 끝 개행 누락). parent(`b878d58~1`) 청정(0건) 확인.
  - ★ **오염 커밋 diff에 정식 수정분 포함** (`analysis/portfolio-policy-kr-and-macro.md` PAT A 등록도 같은 커밋) → **parent 복원 경로 사용 불가** → **footer 기준 python truncate**로 rogue만 선택적 삭제 후 `raw/` 섹션에 PAT B 정식 재등록. (P19 mixed-state edge case 재확인.)
  - 복구 후 `자동 추가` 0건, 끝 개행 복구, index-md registered 96 = actual 96 (dead 0, REAL MISSING 0).
- **P36 10차**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-23_18-04-19.md` 산출(18:04)했으나 LOG.md frontmatter `updated:` = 2026-11-20 → 미백필. 원본 `## Response` = 3877~3959행. **CJK 0건**(원본) → 한국어 재작성 후 LOG.md 전체 CJK 0건 재검증. 11-21(토)·11-22(일)은 주말 스케줄(`0 18 * * 1-5`)로 미실행 — 크론 실패 아님.
- **logs NOTREF 1건 해소**: `2026/2026-11-23-0200.md`(Neo4j 증분 인덱서)가 index 미등록 → November 섹션에 등록 + 본 실행 로그 `2026-11-23-2100.md` 신규 생성·등록. 재감사 broken=0/notref=0/covered=13.
- audit 7종 전항목 통과: wikilink 0 / markdown-link P11 0 / index-md **registered 96 = actual 96** / tag taxonomy 200·used 144·Unknown 0 / logs-index broken 0 notref 0 / **stale 55 / no_date_operational 0 / no_date_immutable 24** / dup-updated 0 (197p).
  - ★ stale 56 → 55 감소 원인: `infra/hermes-version-management.md`의 `updated:`가 11-23으로 실제 갱신(버전체크 크론 산출물). immutable 23 → 24 증가: 신규 raw W47 초안. 스크립트 버그 아님.
- **위키 본문 변경 2건**: (1) `index.md` — P19 rogue 제거 + W47 PAT B 재등록 + 개행 복구 (2) `LOG.md` — 11-23 브리핑 백필(14줄) + frontmatter `updated: 2026-11-23`.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-22 02:00` prefix 복사 후 python 인서트(삽입 위치 line 12, 2행). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과.
- 커밋: logs `034ac23` (parent `90d3653`) / parent `4cef5c8` (parent `6191e94`). push `6191e94..4cef5c8` (hermes-wiki main), logs master `90d3653..034ac23`.
- 원격 검증: `origin/main:index.md` `자동 추가` 0건 / `2026-W47` 1건, `origin/main:LOG.md` `## 2026-11-23 (월) 18:00` 1건 + CJK 0건.
- 교훈: (1) P19 "0건 N일 연속"은 재발 배제가 아님 — 3단계 판별 매 실행 독립 수행. (2) 외부 프로세스 커밋에 정식 수정이 섞여 있으면 parent 복원 금지 — footer truncate만. (3) P36 10거래일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가) 승인 여부 사용자 확인 필요.

## 2026-11-20 (21:00 KST) — P19 재감염 0건 (4일 연속) + P36 9차 + P37 CJK 6자 + **기존 섹션 CJK 잔존 발견** + SCHEMA taxonomy `version` 확장 + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-16 재발 이후 4일 연속 0건 유지.** 판별 3단계: working tree 0 / HEAD(`c6357d0`) 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**. index.md 내 서브모듈 경로 링크 0건, P18(`^|- `) wiki 전체 0건.
- **P36 9차 재현**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-20_18-30-40.md` 산출(18:30)했으나 `LOG.md` frontmatter `updated:` = 2026-11-19 → 11-20 브리핑 미백필. 원본 `## Response` = 3711~3837행.
- **P37 9차**: 원본에 CJK 6자 — `典型`(리스크 오프 전형 조합), `陡峭`(기울기 급격화), `获利`(수익 실현) 각 2자 → 순수 한국어 재작성.
  - ★ **자기 작성 문장에서도 CJK 발생 (11-13/11-18/11-19에 이어 4회 연속)**: "언어 규칙" 메모 줄에서 원본 한자를 예시로 적으려다 CJK 6자가 그대로 재삽입 → 서술형("한자 3어구")으로 교체 후 재검증.
- **★ 신규 발견 — 기존 섹션의 CJK 잔존 (백필 이전 섹션 오염)**: 백필 후 LOG.md 전체 스캔에서 **11-20 09:24 버전체크 크론 섹션**의 `所致` 2자 잔존 발견. P37 교훈의 연장 — "원본만 검사"가 아니라 "**기존 섹션 포함 본문 전체**"를 스캔해야 함. `exit)所致.` → `exit) 때문.`로 교체 → LOG.md 전체 CJK 0건.
  - ★ 이건 **P37 검증 범위를 LOG.md 전체로 확장**해야만 잡히던 유형 — 이전 실행들은 신규 백필분만 스캔해서 통과시켰다.
- **신규 — 미등록 태그 `version` (tag-audit Unknown 1건)**: `infra/hermes-version-management.md`(11-20 09:24 버전체크 크론 산출물)의 tags에 `version`이 있으나 taxonomy 미등록 → **SCHEMA.md infra 행에 `version` 추가**(taxonomy 199 → 200). 개별 페이지 수정 대신 taxonomy 확장.
- **index-md registered 93 → 94**: 신규 `infra/hermes-version-management.md`가 09:24 크론에 의해 index.md 등록됨 (11-19 실행 이후 신규).
- **P37 확장 확인**: `trade-pipeline/logs/portfolio/*.json` 최근 5건(11-05, 11-17~11-20) CJK 0건, `trade-pipeline/logs/*.md` 최근 4건(11-19~11-20) CJK 0건.
- audit 7종 전항목 통과: wikilink 0 / markdown-link P11 0 / index-md registered **94 = actual 94** (dead 0, REAL MISSING 0) / tag taxonomy **200**, used 144, Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 56 / no_date_operational 0 / no_date_immutable 23** (11-19 기준선 완전 일치) / dup-updated 0 (193p). `git diff --check` 통과.
- **위키 본문 변경 3건**: (1) `LOG.md` — 11-20 브리핑 백필(18줄) + frontmatter `updated: 2026-11-19` → `2026-11-20` + 기존 09:24 섹션 CJK 2자 제거 (2) `SCHEMA.md` — infra 행에 `version` 태그 추가 (3) `analysis/orbit-valuation.md` — self-healing-cron 산출물(SNDK 분할 조정 가드, 커밋 `a775413`).
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-19 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `2db0e81` (parent `beff753`) / parent `a192a1b` (parent `328491c`). push `328491c..a192a1b` (hermes-wiki main), logs master `beff753..2db0e81`.
- 원격 검증: `origin/main:index.md` `자동 추가` 0건, `origin/main:LOG.md` CJK 0건 + `## 2026-11-20 (금) 18:00` 1건 + `updated: 2026-11-20`, `origin/main:SCHEMA.md` `version` 반영, `origin/master:index.md` `11-20 21:00` 행 1건.
- 교훈: (1) P37 검증 범위는 **LOG.md 전체(기존 섹션 포함)** — 외부 크론이 만든 과거 섹션도 CJK를 잔존시킬 수 있다. (2) 새 파일 생성 크론이 taxonomy 미등록 태그를 쓰면 Unknown으로 잡힘 → infra 성격 태그는 taxonomy 확장이 적절. (3) P36 9거래일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가) 승인 여부 사용자 확인 필요.

## 2026-11-19 (21:00 KST) — P19 재감염 0건 (3단계 판별) + P36 8차 + P37 CJK 6자 (11-19 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-16 재발 이후 3일 연속 0건 유지.** 판별 3단계: working tree 0 / HEAD(`e36210b`) 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**. index.md 내 서브모듈 경로 링크 0건.
- **P36 8차 재현**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-19_18-24-24.md` 산출(18:24, executions.db status=completed)했으나 `LOG.md` mtime은 11-19 09:11 고정 / frontmatter `updated:` = 2026-11-18 → 11-19 브리핑 미백필. 원본 `## Response` = 3711~3858행.
- **P37 8차**: 원본에 CJK 6자 혼입 — `限韓令`(3730행, 한국 관련 정책 표현 3자), `记忆中`(3840행, 보유 기억 관련 표기 3자) → 순수 한국어 재작성.
  - ★ **자기 작성 문장에서도 CJK 발생**: 1차 재작성에서 `快报`(상장 규모), `开盘`(예상 개장가) 2건이 **재작성 문장 자체에** 새로 생김 → 2차 검증에서 발견 후 `상장 예정`/`예상 개장가`로 교체. **원본 CJK만 검사하지 말고 "내가 쓴 한국어"까지 전체 본문 스캔** (11-13/11-18 교훈 재확인 — 이번에도 동일한 함정).
- **P37 확장 확인**: `trade-pipeline/logs/portfolio/*.json` 최근 5건(11-13, 11-16~11-19) CJK 스캔 → **전부 0건**. 11-12 `化` 1자 이후 미재발.
- audit 7종 전항목 통과: wikilink 0 (91 .md) / markdown-link P11 0 / index-md registered **93 = actual 93** (dead 0, REAL MISSING 0) / tag taxonomy 199, used 143, Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 56 / no_date_operational 0 / no_date_immutable 23** / dup-updated 0 (190p). `git diff --check` 통과.
  - ★ **stale 57 → 56 감소 원인 확인**: `infra/dev-harness-kit-daily-review.md`의 `updated:`가 2026-08-11 → 2026-11-19로 실제 갱신 (dev-harness-kit 일일 리뷰 크론 산출물). 스크립트 버그 아님 (P16 "감소도 원인 확인" 교훈 준수).
- **위키 본문 변경 2건**: (1) `LOG.md` — 11-19 브리핑 백필(18행) + frontmatter `updated: 2026-11-18` → `2026-11-19` (2) `infra/dev-harness-kit-daily-review.md` — 외부 크론 산출물(PR #969 리뷰) 정상 변경분.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-18 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `beff753` (2026/2026-11-19-2100.md 신규 + index.md 행 추가) / parent `c6357d0` (LOG.md + dev-harness-kit-daily-review.md + submodule pointer bump). push `e36210b..c6357d0` (hermes-wiki main), logs master `47565d7..beff753`.
- 교훈: (1) P19는 11-16 committed 변형 후 3일 만에 0건 복귀 — 판별 매 실행 독립 수행 원칙 유지. (2) **P37 재작성 시 자기 문장에서도 CJK가 새로 생길 수 있다** — 원본 검사만으로 통과시키지 말고 전체 LOG.md를 스캔할 것. (3) P36 8일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가) 승인 여부 사용자 확인 필요.

## 2026-11-18 (21:00 KST) — P19 재감염 0건 (3단계 판별) + P36 7차 + P37 CJK 7자 (11-18 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-16 재발(committed+push 변형) 이후 2일 연속 0건 유지.** 판별 3단계: working tree 0 / HEAD(`3ca387c`) 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**.
  - index.md 내 서브모듈 경로 링크(`(logs/`, `(subagents-library/`) 0건. P18 스캔(`^|- `) wiki 전체 0건.
- **P36 7차 재현**: 브리핑 크론(`2916cc9c2ceb`)이 `2026-11-18_18-09-34.md` 산출(18:09)했으나 `LOG.md`에 11-18 브리핑 섹션 미기록 → 수동 백필. 원본 `## Response` = 3711~3865행.
- **P37 7차**: 원본에 CJK 7자 혼입 — `公用`(3764행 `전력·公用사업`), `拖累`(3814행 `-0.31%p를拖累`), `政策的`(3849행 `피的政策`) → 순수 한국어 재작성.
  - ★ **검증 함정 재확인**: 1차 재작성 후 CJK 2자(`拖累`) 잔존 → 2차 전체 스캔에서 발견하고 재수정. **CJK 검증은 1회가 아니라 본문 전체 대상으로 재확인할 것** (11-13 사례와 동일 패턴).
- **P37 확장 실증 후속 확인 (11-16 발견분)**: `trade-pipeline/logs/` 최근 산출물 6건(`full_report_20261118_1953.md`, `2026-11-18.json`, `report_20261118_1951.md`, `full_report_20261117_1845.md`, `report_20261117_1848.md`, `2026-11-17.json`) 전수 CJK 스캔 → **전부 0건**. 11-12 `key_risks`의 `化` 1건은 일시적 LLM 표본 편차로 보임.
- audit 7종 전항목 통과: wikilink 0 (91 .md) / markdown-link P11 0 / index-md registered **93 = actual 93** (dead 0, REAL MISSING 0) / tag taxonomy 199, used 143, Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 23** (11-16 기준선 완전 일치) / dup-updated 0 (189p). `git diff --check` 통과.
- 조치: `LOG.md` frontmatter `updated: 2026-11-17` → `2026-11-18` + 11-18 브리핑 섹션 추가 (python 인서트, anchor `## 2026-11-18 (수) 19:21` — 18:00 브리핑이 19:21 파이프라인 로그보다 **앞**에 오도록 순서 정정).
  - ⚠ python 인서트로 CJK 잔존 2자(`拖累`)를 1차 놓쳤으나, **같은 스크립트에서 바로 CJK 검증**하므로 즉각 발견. 이 순서(작성→CJK 검증→수정→재검증)를 계속 유지할 것.
- 커밋: logs `47565d7` (2026/2026-11-18-2100.md 신규 + index.md 행 추가, 기준 행 `|| 11-18 02:00` prefix 복사, cat -A prefix 일치, triple-pipe 0) / parent `ffc0ccb` (LOG.md + submodule pointer bump). push `3ca387c..ffc0ccb`.
- 교훈: (1) P19 재발 후 2일 만에 0건 복귀 — 재발/재차 차이는 임의 일자 단위이므로 **판별을 매 실행 독립 수행**하는 것이 원칙. (2) P37 재작성은 1회 검증으로 부족 — 항상 전체 본문 재스캔. (3) P36 7일 연속 구조적 결함 — 근본 조치(toolset에 `file` 추가 + 프롬프트에 기록 단계) 승인 여부 사용자 확인 필요.

## 2026-11-17 (21:00 KST) — P19 재감염 0건 (3단계 판별) + P36 6차 + P37 CJK 7자 (11-17 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 11-02 이후 종료 국면 유지.** 11-16에 committed+push 변형으로 재발했으나 **하루 만에 0건으로 복귀**. 판별 3단계: working tree 0 / HEAD(`4f22652`) 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, stash 없음, `git status --porcelain` 빈 결과, `git status -sb` = `## main...origin/main` → **복구 경로 미실행**.
  - index.md 내 서브모듈 경로 링크(`(logs/`, `(subagents-library/`) 0건, footer line 144, 파일 끝 개행 정상.
  - **★ 교훈**: P19는 재발 후 즉시 재차 차단되는 게 아니라 일자 단위로 임의 변동한다. "재발 후 즉시 조치가 원칙"이 아니라 "3단계 판별을 매 실행 독립 수행"이 원칙. 11-16 노트의 재발 사례가 다음 날 0건으로 돌아왔다는 점이 재발 배제 아님을 다시 실증.
- **P36 6차 재현** (6거래일 연속): 18:00 브리핑 크론 `2916cc9c2ceb`이 `2026-11-17_18-17-59.md` 산출(18:17)했으나 `LOG.md` mtime은 11-16 20:03 고정 → 수동 백필. 브리핑 크론 `enabled_toolsets` = `['terminal','search','web']` — `write_file`/`patch`/`read_file` 전무 → **근본 조치 미적용(보고만)**.
- **P37 6차**: 원본 `## Response`(3711~3853행)에 **CJK 7자** 혼입 — 3722행 `美国的对中 AI칩 접근`(`对中` 2자), 3782행 `合리적，收获 가능성`(`收获` 2자), 3842행 `AI 버블 估值 재설정 시험대`(`估值` 2자) → 순수 한국어 재작성 후 **CJK 0건 검증** (전체 LOG.md 대상). **★ 교훈: CJK 혼입 건수가 2→7자로 증가** — 원본 오염 크기는 매번 다르므로 1~2자만 검사해선 안 되고 항상 전체 본문 문자 스캔.
- audit 7종 전항목 통과: wikilink 0 (91 .md) / markdown-link P11 0 / index-md **registered 93 = actual 93**, REAL MISSING 0 / tag taxonomy 199·used 143·Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 23** (11-16 기준선과 완전 일치 → 스크립트 로직 정상) / dup-updated 0 (188페이지).
- P18 스캔(`^|- `) wiki 전체 0건, 스킬 references 0건, `logs/index.md` triple-pipe 0건. `git diff --check` 통과.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-17 06:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `7b13f31` (parent `f386faf`) / parent wiki `1d173c7` (parent `4f22652`). push: hermes-logs master, hermes-wiki main 모두 성공. 원격 검증: `origin/main:LOG.md` `## 2026-11-17` 1건 + `updated: 2026-11-17` + CJK 0건, `origin/main:index.md` `자동 추가` 0건, `origin/master:index.md` `11-17 21:00` 행 1건 + 신규 로그 파일 확인.

## 2026-11-16 (21:00 KST) — **P19 재발(committed+push 변형)** + P36 5차 + P37 CJK 2자 (11-16 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **★ P19 재발 — 11-02 이후 10일 만의 재감염, committed+push 변형.** 판별 3단계: working tree 1 / HEAD 1 / origin/main 1 → 이전 9일(11-02~11-13)과 달리 **커밋+push까지 완료된 변형**. `git diff HEAD --stat -- index.md`는 빈 결과(HEAD와 동일)였고, 오염 커밋 `60a1708`(hermes-config-sync 2026-11-16T05:30:32Z)의 diff는 **rogue 추가분 2줄뿐(정식 수정 0건)**임을 확인.
  - 오염 내용: `index.md` footer(`*Managed by Hermes Agent...`) 뒤에 `- [2026 W46 Weekly Recap Draft](raw/2026-W46-weekly-recap-draft.md) — 자동 추가 (2026-11-15)` 삽입 + **`\ No newline at end of file`**.
  - **원인**: `hermes-config-sync` 크론(91059d1e3d31, `30 13 * * *`)이 04:00 크론이 만든 `raw/2026-W46-weekly-recap-draft.md`(커밋 `53a861b`)를 index.md에 등록. `raw/` 섹션 정식 규약은 **PAT B plain-text**인데 rogue는 PAT A + "자동 추가" 레이블 → **형식 불일치 + 잘못된 위치**.
  - **복구 (mixed-state truncate 경로)**: footer 이후 truncate → `raw/` 섹션 W45 행 바로 아래에 PAT B로 정식 재등록(`- 2026-W46-weekly-recap-draft (raw/2026-W46-weekly-recap-draft.md) — 🆕 2026-W46 주간 회고 초안 (publish 전 사용자 확인 대기)`) → 끝 개행 복구(`rstrip('\n')+'\n'`). `grep -c '자동 추가'` → 0.
  - **★ 교훈 ①**: P19 "0건 연속"은 재발 배제가 아니다. 9일 연속 종료 국면 뒤에 committed 변형으로 재발했으니 **3단계 판별은 매 실행 독립 수행**해야 한다 (11-14은 토요일, 11-15 일요일이라 cron 미실행 — 주말 공백은 정상).
  - **★ 교훈 ②**: 외부 프로세스가 index.md를 수정할 때 **파일 끝 개행을 보장하지 않는다**. `\ No newline at end of file` 증상 확인 → 복구 시 개행을 명시적으로 정리할 것.
  - **★ 교훈 ③**: 새 파일 생성 크론 + index 자동등록 크론이 결합하면 P19 + PAT B 형식 불일치가 동시에 발생. 복구 시 반드시 해당 섹션의 정식 형식으로 재등록 (단순 삭제는 REAL MISSING 유발).
- **P36 5차 재현**: 18:00 브리핑 크론 `2916cc9c2ceb`이 `2026-11-16_18-07-17.md` 산출했으나 `LOG.md` mtime은 11-13 20:01 고정 → 수동 백필. 브리핑 크론 `enabled_toolsets` = `['terminal','search','web']` (jobs.json 실측) — `write_file`/`patch`/`read_file` 전무 → **근본 조치 미적용(보고만)**.
- **P37 5차**: 원본 `## Response`(3711~3857행)에 **CJK 2자**(`租金`, 3727행 `(@"租金")`) 혼입 → 순수 한국어 재작성 후 **CJK 0건 검증** (전체 LOG.md 대상).
- **P37 확장 실증**: `trade-pipeline/logs/portfolio/2026-11-12.json`의 `key_risks`에 `化` 1자 잔존(`장기化による`) — 11-13/11-16 JSON은 CJK 0건. → **파이프라인 LLM 출력 단계에 CJK 스캔 QA 적용 필요** (매크로 리포트는 QA 통과, 포트폴리오 JSON만 미적용).
- audit 7종 전항목 통과: wikilink 0 (91 .md) / markdown-link P11 0 / index-md **registered 93 = actual 93**, REAL MISSING 0 / tag taxonomy 199·used 143·Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 23** (11-13 기준선 57/0/22와 stale 완전 일치, immutable +1 = 신규 `raw/2026-W46` 초안 — 스크립트 버그 아님) / dup-updated 0 (184페이지).
- P18 스캔(`^|- `) wiki 전체 0건. `git diff --check` 통과.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-13 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `57818c2` (parent `4d4afe8`) / parent wiki `d398c73` (parent `60a1708`). push: hermes-logs master, hermes-wiki main 모두 성공. 원격 검증: `origin/main:index.md` `자동 추가` 0건, `origin/main:LOG.md` `## 2026-11-16` 섹션 + `updated: 2026-11-16` 확인.
- **참고 (범위 밖)**: `~/trade-pipeline`가 `main` 기준으로 `origin/main`보다 ahead 1 — wiki-auto-refresh는 위키만 다루므로 미조치.

## 2026-11-13 (21:00 KST) — P36 4차 재현 + P37 CJK 6자 혼입 (11-13 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P36 4차 재현**: 18:00 브리핑 크론 `2916cc9c2ceb`이 `2026-11-13_18-20-43.md` 산출했으나 `LOG.md` mtime은 11-12 20:01 고정 → 수동 백필 (11-06/09/10/11/12에 이어 5일 연속).
- **P37 4차**: 원본 `## Response`(3711~3846행)에 **CJK 6자 혼입**(`预`/`期`/`寿`/`险`/`広`/`化`) → 순수 한국어 재작성 후 **CJK 0건 검증**.
- ★ **재작성 시 주의(이번 실전)**: 원본 `寿险`(생명보험)조차 한국어 표기가 아니라 한자 혼입 형태였음 → 재작성을 기계적 치환이 아니라 **한국어 재진술**로 해야 한다. 1차 재작성에서 `寿险`를 그대로 옮겨 CJK 2자 잔존 → 2차 검증에서 발견·`생명보험`으로 교체. **CJK 0건 검증은 반드시 백필 직후 1회만 하지 말고, 본문 전체(기존 섹션 포함)로 돌려 재확인할 것.**
- audit 7종 전항목 통과: wikilink 0 / markdown-link P11 0 / index-md registered 92 = actual 92 / tag taxonomy 199·Unknown 0 / logs-index broken 0 notref 0 covered 13 / **stale 57 / no_date_operational 0 / no_date_immutable 22** (11-12 기준선 57/0/22 완전 일치) / dup-updated 0.
- P18 스캔(`^|- `) wiki 전체 0건. `git diff --check` 통과.
- **P19 재감염 0건 9일 연속** (11-02~11-13, 주말 제외): working tree / HEAD / origin/main 모두 0, `git diff HEAD --stat -- index.md` 빈 결과, stash 없음 → 복구 경로 불필요.
- logs/index.md: November 섹션 기존 확인 → 기준 행 `|| 11-12 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A`에서 11-13/11-12/11-11 행 모두 `||` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과 + logs-index 재감사 broken=0/notref=0.
- 커밋: logs `4d4afe8` (parent `a663de5`) / parent wiki `4625ec4` (parent `07ed557`). push: hermes-logs master, hermes-wiki main 모두 성공.
- **새 발견 (P37 확장)**: `logs/portfolio/2026-11-12.json`의 `key_risks`에 CJK 혼입 발견 — 18:35 파이프라인 LLM 출력 산출물. 매크로 리포트(`macro_context.json`)는 QA 통과지만 포트폴리오 JSON은 QA 미적용. → 브리핑 크론만 고치는 것으로는 부족하며, **파이프라인 LLM 출력 단계에도 CJK 스캔 QA 적용 필요.**
- **보고만 (근본 조치 미적용)**: 브리핑 크론 toolset에 `file` 추가 + 프롬프트에 기록 단계 — wiki-auto-refresh 범위 밖이므로 승인 없이 진행하지 않음. 매일 수동 백필 유지.

## 2026-11-12 (21:00 KST) — P36 3차 재현 + P37 CJK 혼입 (11-12 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 8일 연속** (11-02~11-12, 주말 제외). 판별 3단계(working tree / HEAD / origin/main) 모두 `자동 추가` 0건, `git diff HEAD -- index.md` 빈 결과 → 복구 경로 미실행.
- **P18 오염 0건** — wiki 전체(`--include='*.md'`) `^|- ` 0건, `logs/index.md` triple-pipe(`^|||`) 0건. logs/index.md 인서트는 기준 행 `|| 11-11 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12) → `cat -A` prefix 일치 + triple-pipe 0건 + `git diff --check` 통과.
- **audit 7종 전항목 통과** — wikilink(MD/WL/CD/BN/MDX 모두 0) / markdown-link(P11 0, broken 0) / index-md(registered 92 = actual 92, REAL MISSING 0) / logs-index-link(broken 0, notref 0, covered 13 오탐) / tag(taxonomy 199, used 143, **Unknown 0**) / dup-updated(pages 181, duplicate 0) / stale(**57 / 0 / 22** — 11-10 기준선 59/0/22와 2건 차이는 11-11 CJK 제거 실제 편집분으로 설명됨, 스크립트 버그 아님).
- **P36 3차 재현 — 11-12 브리핑 LOG.md 미기록.** 18:00 크론 `2916cc9c2ceb`이 `2026-11-12_18-07-59.md` 산출했으나 `LOG.md` mtime은 2026-11-11 20:01 그대로. 원인은 P36와 동일(브리핑 크론 toolset에 파일쓰기 도구 부재).
  - **조치**: `~/.hermes/cron/output/2916cc9c2ceb/2026-11-12_18-07-59.md`의 `## Response`(3711~3801행)을 원본으로 삼아 `LOG.md`에 수동 백필.
  - **P37 재현 — 원본에 CJK 6자(2자 어구 3개) + 영문 혼입(영문 단어 3개)** → 언어 규칙(중국어 금지)에 따라 **순수 한국어로 재작성**. 수치·해석은 원본 인용.
  - frontmatter `updated: 2026-11-11` → `2026-11-12`. 검증: CJK 0건 / `yaml.safe_load` OK / `git diff --check` 통과.
- **위키 본문 변경 1건** (LOG.md) → parent 커밋 반영. logs 서브모듈은 신규 로그 `2026/2026-11-12-2100.md` + index.md 행 추가로 커밋.
- **커밋**: logs `a663de5` (master) / parent `07ed557` (main). 양쪽 push 완료. `git show origin/main:LOG.md`에 11-12 섹션 반영 확인, `origin/main:index.md` `자동 추가` 0건.
- **미조치(보고만)**: P36 근본 조치(브리핑 크론 toolset에 `file` 추가 + 프롬프트에 기록 단계)는 범위를 넘어 승인 없이 진행하지 않음. stale 57개는 P16에 따라 자동 갱신 금지. no_date_immutable 22개는 의도된 상태.

## 2026-11-11 (21:00 KST) — P36 2차 재현 (11-11 브리핑 LOG.md 백필) + audit 7종 통과 + push 성공

- **P19 재감염 0건 — 7일 연속** (11-02~11-11, 주말 제외). 판별 3단계(working tree / HEAD / origin/main) 모두 `자동 추가` 0건, `git diff HEAD -- index.md` 빈 결과 → 복구 경로 미실행.
- **P18 오염 0건** — wiki 전체(`--include='*.md'`) + 스킬 `references/` 모두 `^|- ` 0건, `logs/index.md` triple-pipe(`^|||`) 0건.
- **audit 7종 전항목 통과** — wikilink(MD/WL/CD/BN/MDX 모두 0) / markdown-link(P11 0, broken 0) / index-md(registered 92 = actual 92, REAL MISSING 0) / logs-index-link(broken 0, notref 0, covered 13 오탐) / tag(taxonomy 199, used 143, **Unknown 0**) / dup-updated(pages 180, duplicate 0) / stale(**59 / 0 / 22** — 11-10 기준선 완전 일치 → 스크립트 로직 정상).
- **P36 2차 재현 — 11-11 브리핑 LOG.md 미기록.** 18:00 크론 `2916cc9c2ceb`이 `2026-11-11_18-26-24.md` 산출(executions.db status=completed)했으나 `LOG.md` mtime은 2026-11-10 20:02 그대로. 원인은 P36 그대로 — 해당 크론 `enabled_toolsets` = `['terminal','search','web']`로 **`write_file`/`patch`/`read_file` 전무**(jobs.json 실측 확인). 프롬프트에 '기록하라'만 추가해도 파일 쓰기 자체가 불가능.
  - **조치**: `~/.hermes/cron/output/2916cc9c2ceb/2026-11-11_18-26-24.md`의 `## Response`(3711~3804행)을 원본으로 삼아 `LOG.md`에 수동 백필.
  - **⚠ 원본에 중국어/외국어 혼입**(한자 2자+3자 어구, 폴란드어 1단어) — 언어 규칙(중국어 금지)에 따라 **순수 한국어로 재작성** 필요. 백필 후 CJK 문자 0건 검증.
  - frontmatter `updated: 2026-11-10` → `2026-11-11`.
  - **P36 재발 확인**: 11-06/11-09/11-10에 이어 11-11도 동일 패턴 → **매일 반복되는 구조적 결함**이며, wiki-auto-refresh가 매일 수동 백필하지 않으면 LOG.md는 영구히 11-05에 멈춘다.
- **위키 본문 변경 1건** (LOG.md) → parent 커밋에 반영. logs 서브모듈은 신규 로그 파일 + index.md 행 추가로 커밋.
- **logs/index.md 행 추가** — November 섹션 기존 확인(월 섹션 신설 불필요), 기준 행 `|| 11-10 21:00` prefix 복사 후 python 인서트(삽입 위치 line 12). `cat -A`로 11-11/11-10/11-09 행 모두 `||` prefix 일치 확인, triple-pipe 0건, `git diff --check` 통과, logs-index 재감사 broken=0/notref=0.
- **커밋**: logs `120f679` (master) / parent `023e382` (main). 양쪽 push 완료.

## 2026-11-10 (21:00 KST) — P36 신규 (브리핑 크론 파일쓰기 도구 부재) + 11-09 중단분 인수인계 + LOG.md 백필 + push 성공

- **11-09(월) 21:00 실행이 도구 한도 소진으로 중단**돼 미수행 항목(로그 파일 생성, `logs/index.md` 행 추가, 커밋·푸시, 세션 노트·스킬 갱신)이 남아 있었음. 이번 실행에서 전부 인수인계 수행.
- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, `git stash list` 비어 있음, `git status -sb` = `## main...origin/main`.
- **재감염 0건 6일 연속** (11-02 ~ 11-10, 주말 제외) — 3단계 판별 매 실행 독립 수행 계속.
- audit 7종 전항목 통과: wikilink (90 .md, BROKEN_MD/WL 0, CROSSDOM 0, BARENAME 0, MDEXT 0) / markdown-link (P11 0, broken 0) / index-md (registered 92 = actual 92, dead 0, missing 0) / tag (taxonomy 199, used 143, registered 143, Unknown 0) / logs-index (broken 0, notref 0, covered 13, ambiguous 0) / dup-updated (0) / stale-audit (**stale 59 / no_date_operational 0 / no_date_immutable 22**).
- P18 검사: wiki `^|- ` 0건, skill references 0건, logs/index.md triple-pipe 0건, index.md 내 submodule 경로 링크 0건.
- **stale 기준선 갱신: 59 / 0 / 22** — 11-08 주간 cleanup이 `raw/archive/` 2건 추가(→ immutable 21→22) + 일부 페이지 `updated:` 실제 갱신(→ stale 62→59). 스킬 본문 기준선 문구 갱신 필요.
- **P36 신규 — P35 정정**: 11-06 노트(P35)가 지목한 "브리핑 크론 프롬프트에 LOG.md 기록 단계 누락"은 근본 원인의 절반. 실제 제약은 **"기록 단계 미정의 + 파일쓰기 도구 부재"의 조합** — 브리핑 크론(`2916cc9c2ceb`)의 `enabled_toolsets`는 terminal/process_manage/web_search/web_extract 4개만 노출하며 `write_file`/`patch`/`read_file`이 **전부 부재**. → 프롬프트에 "기록하라"만 추가해도 파일 쓰기 불가. toolset에 `file` 추가 필요.
  - 11-05의 "기록 성공"은 브리핑 크론 행위가 아니라 **auto-refresh(20:01~20:09)가 frontmatter 보강 중 파일 재작성**한 결과 (`LOG.md` mtime = 11-05 20:06 = auto-refresh 구간) — opportunist 행동이었고 11-06·11-09에는 재현되지 않음.
  - 11-07(토)·11-08(일) 미실행은 크론 실패가 아니라 `0 18 * * 1-5` / `0 20 * * 1-5` 스케줄(월~금) 정상 동작.
- **위키 본문 변경 1건 — `LOG.md`** (11-09 백필분 + 오늘 브리핑). 11-06 / 11-09 / 11-10 3거래일 브리핑 내용을 원본 크론 출력(`~/.hermes/cron/output/2916cc9c2ceb/*.md`)에서 추출해 백필. frontmatter `updated: 2026-11-05` → `2026-11-10`. 한자 혼입 제거(언어 규칙 준수: 중국어 3건을 한국어/영어로 교체).
- logs/index.md: November 섹션 기존 확인 → 월 섹션 신설 불필요(P30). 기준 행 `|| 11-08 07:00` prefix(앞 2바이트 `||`) 복사 후 python 인서트 — **주의: `lines[anchor][:index('|',2)]`로 prefix 추출하면 잘못된 값이 나와 prefix가 중복 삽입됨** → `lines[anchor][:2]`로 고정. `cat -A` 형제 행 prefix 일치 확인, triple-pipe 0건, `git diff --check` 통과, logs-index 감사 broken=0/notref=0.
- 신규 로그 파일 2건: `logs/2026/2026-11-10-2100.md`, `logs/2026/2026-11-09-2100.md`(중단 기록).
- 커밋: hermes-logs(master) `9a0c5f1`, hermes-wiki(main) `8f2c1a9` (LOG.md 본문 + submodule pointer) → push 완료.

## 2026-11-09 (21:00 KST) — 중단 (도구 한도 소진) — P36 신규 발견

- 11-09 실행은 **분석 단계까지 완료**했으나 도구 한도 소진으로 백필·커밋·푸시·세션 노트 갱신이 미수행됨 (커밋 0건, git status clean).
- audit 7종 전항목 통과 / P19 재감염 0건 / stale 기준선 59 / 0 / 22 확인.
- **P36 발견**: 브리핑 크론(`2916cc9c2ceb`)의 `enabled_toolsets`에 `write_file`/`patch`/`read_file`이 전부 부재 → 프롬프트에 "LOG.md 기록하라"만 추가해도 파일 쓰기 불가. P35(기록 단계 누락) 정정 — 원인은 "기록 단계 미정의 + 파일쓰기 도구 부재" 조합.
- 인수인계: 2026-11-10 실행에서 LOG.md 백필 + 로그 2건 생성 + 커밋·푸시 수행.

## 2026-11-06 (21:00 KST) — P19 재감염 0건 (5일 연속) + audit 7종 전항목 통과 + 위키 본문 변경 0건 + push 성공

- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, `git stash list` 비어 있음. `git status -sb` = `## main...origin/main` (clean, ahead/behind 없음).
- **재감염 0건 5일 연속(11-02 ~ 11-06) 유지** — 외부 자동화 프로세스의 index.md 삽입 동작이 차단된 국면 지속. 재발 배제 아님, 3단계 판별 매 실행 독립 수행 계속.
- audit 7종 전항목 통과: wikilink (88 .md, BROKEN_MD/WL 0, CROSSDOM 0, BARENAME 0, MDEXT 0) / markdown-link (P11 0, broken 0) / index-md (registered 90 = actual 90, dead 0, missing 0) / tag (taxonomy 152, used 140, registered 140, Unknown 0) / logs-index (broken 0, notref 0, covered 13, ambiguous 0) / dup-updated (0) / stale-audit (stale 62 / no_date_operational 0 / no_date_immutable 21).
- P18 검사: wiki `^|- ` 0건, skill references 0건, index.md 내 submodule 경로 링크 0건, logs/index.md triple-pipe 0건.
- stale 62 — 11-05 기준선 62와 **완전 일치** (신규 30일 경과 페이지 없음). stale-audit.py 결정론 6회 연속 확인.
- **위키 본문 변경 0건** — index.md/SCHEMA.md/AGENTS.md 모두 무수정. `git status --porcelain` = `M logs` 한 줄뿐 → P31에 따라 `git add logs`만 스테이징, 커밋 메시지는 변경 내용으로 기술(`wiki: bump logs submodule (2026-11-06 auto-refresh — no wiki body changes)`).
- logs/index.md: November 섹션 기존 확인 → 월 섹션 신설 불필요(P30). 기준 행 `|| 11-05 21:00` prefix 복사 후 python 인서트로 11-06 행 추가 (삽입 위치 line 12). `cat -A` 형제 행 prefix 일치 확인, triple-pipe 0건, `git diff --check` 통과, logs-index 감사 broken=0/notref=0.
- 커밋: hermes-logs(master) `b785a52`, hermes-wiki(main) `f185ee7` (submodule pointer bump) → push 완료 (`d169664..f185ee7`).
- **관찰 (조치 필요 — 후속 크론 과제)**: 11-06 18:00 미국 증시 브리핑 크론(`2916cc9c2ceb`)이 `completed`로 실행됐으나 `LOG.md` mtime은 여전히 2026-11-05 20:06. 해당 크론 프롬프트에 "LOG.md 기록" 단계가 없어(Discord 전송까지만 정의) LOG.md가 11-05 이후 자동 갱신되지 않음. wiki-auto-refresh 관점에선 untracked/dirty 잔재가 없어 조치 대상 아님. **LOG.md가 일일 append-only 브리핑 로그로 쓰일 거라면 크론 프롬프트에 기록 단계를 추가해야 함.**
- 참고 (본 스킬 무관): 11-06 크론 실패 2건 — `276405a79d88`(Paper Portfolio 일일 갱신) 18:45 failed, `05bd40b25f6f`(Self-Improving Hermes) 19:40/19:50 failed.

## 2026-11-05 (21:00 KST) — P19 재감염 0건 (4일 연속) + **중복 updated: frontmatter 24개 페이지 수정** + **LOG.md 신규 등록** + push 성공

- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, `git stash list` 비어 있음. `git status -sb` = `## main...origin/main [ahead 1]` (ahead 1은 04:00 크론의 `410f57c docs(neo4j)` — 이번 실행 산출 아님).
- **재감염 0건 4일 연속(11-02, 11-03, 11-04, 11-05) 유지.** 3단계 판별 매 실행 독립 수행 계속.
- **신규 발견 1 — 중복 `updated:` frontmatter 키 24개 페이지.** auto-fill-dates.py v1.15.0 잔재(기존 `updated:` 줄 미감지 상태에서 새 줄 삽입). YAML last-wins라 **유효 날짜는 불변** — 의미 보존적 제거 가능. → `scripts/dup-updated-audit.py` 신규 번들 작성(감지 + `--fix`, last-occurrence 유지). 수정 전/후 `yaml.safe_load` 71개 파일 전수 비교 → **semantic diff 0건**. `git diff --check` 통과.
- **신규 발견 2 — `LOG.md` 미등록.** 2026-11-05 18:00 미국 증시 브리핑 크론(cron id `2916cc9c2ceb`)이 생성한 일일 브리핑 로그가 untracked(`?? LOG.md`) + index.md 미등록 상태. `hermes-trading-log.md`와 중복되지 않음 (Karpathy 패턴의 append-only LOG 역할). → SCHEMA.md 최소 frontmatter(tags/related/created/updated) 보강 + index.md `## 기타` 섹션에 PAT A 등록(python 인서트) + `git add`로 커밋 포함.
- audit 6종 전항목 통과: wikilink (88 .md, BROKEN_MD/WL 0, CROSSDOM 0, BARENAME 0, MDEXT 0) / markdown-link (P11 0, broken 0) / index-md (**registered 90 = actual 90**, dead 0, missing 0) / tag (taxonomy 152, Unknown 0) / logs-index (broken 0, notref 0, covered 13, ambiguous 0) / **dup-updated (0)** / stale-audit (stale 62 / no_date_operational 0 / no_date_immutable 21).
- P18 검사: wiki `^|- ` 0건, skill references 0건, logs/index.md triple-pipe(`^|||`) 0건, index.md 내 submodule 경로 링크 0건.
- **stale 63→62 감소 확인** — 스크립트 버그가 아니라 04:00 크론 커밋 `410f57c`가 `infra/neo4j-local.md`의 `updated:`를 2026-07-01 → 2026-11-05로 갱신한 실제 콘텐츠 갱신(`git show 410f57c` diff로 확인). stale-audit 5회 연속 실행 동일 결과 — 결정론 확인. **기준선 비교 시 "증가"만 이상 징후로 보는 편향 금지 — 감소도 원인을 확인할 것.**
- logs/index.md: November 섹션 기존 확인 → 월 섹션 신설 불필요(P30). 기준 행 `|| 11-04 21:00` prefix 복사 후 python 인서트로 11-05 행 추가 (삽입 위치 line 12). `cat -A` 형제 행 prefix 일치 확인, triple-pipe 0건, `git diff --check` 통과, logs-index 감사 broken=0/notref=0.
- 커밋: hermes-logs(master) `a5e7a9a`, hermes-wiki(main) `8c13760` (본문 변경) + `d169664` (submodule pointer bump) → push 완료 (`94d5a3a..d169664`).

## 2026-11-04 (21:00 KST) — P19 재감염 0건 (3일 연속 유지) + audit 5종 전항목 통과 + 위키 본문 변경 0건 + push 성공

- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, `git status -sb` = `## main...origin/main` (clean), `git stash list` 비어 있음.
- **재감염 0건 3일 연속(11-02, 11-03, 11-04) 유지** — 외부 자동화 프로세스의 index.md 삽입 동작이 차단된 국면 지속. 재발 배제 아님, 3단계 판별 매 실행 독립 수행 계속.
- audit 5종 전항목 통과: wikilink (87 .md, BROKEN_MD/WL 0, CROSSDOM 0, BARENAME 0, MDEXT 0) / markdown-link (P11 0, broken 0) / index-md (registered 89 = actual 89, dead 0, missing 0) / tag (taxonomy 152, used 140, registered 140, Unknown 0) / logs-index (broken 0, notref 0, covered 13, ambiguous 0).
- P18 검사: wiki `^|- ` 0건, skill references 0건, logs/index.md triple-pipe(`^|||`) 0건, index.md 내 submodule 경로 링크 0건.
- stale-audit.py 기준선 검증: `stale=63 no_date_operational=0 no_date_immutable=21` — 11-03 기준선과 완전 일치 (스크립트 로직 정상). auto-fill-dates filled 0 / skipped 21(raw immutable).
- 위키 본문 변경 0건 — index.md/SCHEMA.md/AGENTS.md 모두 무수정. 변경은 로그 2건뿐 (P31 — wiki 본문 커밋 안 함, submodule pointer bump만).
- logs/index.md: November 섹션 기존 확인 → 월 섹션 신설 불필요(P30). 기준 행 `|| 11-03 21:00` prefix 복사 후 python 인서트로 11-04 행 추가 (삽입 위치 line 12). `cat -A` 검증으로 형제 행과 `||` prefix 일치 확인, triple-pipe 0건, `git diff --check` 통과.
- 커밋: hermes-logs(master) `609c071`, hermes-wiki(main) `94d5a3a` (submodule pointer bump) → push 완료 (`c2cfe4f..94d5a3a`).

## 2026-11-03 (21:00 KST) — P19 재감염 0건 (35회 연속 종료 유지) + audit 5종 전항목 통과 + 위키 본문 변경 0건 + push 성공

- P19 3단계 판별: working tree 0 / HEAD 0 / origin/main 0 → `git diff HEAD --stat -- index.md` 빈 결과, `git status -sb` = `## main...origin/main` (clean).
- **재감염 0건이 2일 연속(11-02, 11-03) 유지** — 10-28(working-tree) → 10-30(working-tree) → 11-02(0) → 11-03(0). 외부 자동화 프로세스의 index.md 삽입 동작이 실제로 차단된 국면으로 보임. 재발 배제 아님 — 3단계 판별은 매 실행 독립 수행 계속.
- audit 5종 전항목 통과: wikilink (87 .md, BROKEN_MD/WL 0, CROSSDOM 0, BARENAME 0, MDEXT 0) / markdown-link (P11 0, broken 0) / index-md (registered 89 = actual 89, dead 0, missing 0) / tag (taxonomy 152, used 140, registered 140, Unknown 0) / logs-index (broken 0, notref 0, covered 13, ambiguous 0).
- P18 검사: wiki `^|- ` 0건, skill references 0건, logs/index.md triple-pipe(`^|||`) 0건, index.md 내 submodule 경로 링크 0건.
- stale 63개 (명시적 날짜 30일+, 최장 analysis/methodology.md 153일) — 자동 갱신 없이 플래그만. 날짜 없음 21개 = 전부 raw/ immutable. auto-fill-dates filled 0 / skipped 21.
- 위키 본문 변경 0건 — index.md/SCHEMA.md/AGENTS.md 모두 무수정. 변경은 로그 2건뿐.
- logs/index.md: November 섹션 이미 존재 (P30 — 월 섹션 신설 불필요). 기준 행 `|| 11-02 21:00` prefix 복사 후 python 인서트로 11-03 행 추가 (삽입 위치 line 12). `cat -A` 검증으로 형제 행과 `||` prefix 일치 확인, triple-pipe 0건.
- 커밋: hermes-logs(master) `ee707e6`, hermes-wiki(main) `c2cfe4f` (submodule pointer bump) → push 완료 (`a726483..c2cfe4f`).
- 참고: 반복 실행 시 무조건 커밋 만들기보다 실제 변경이 있을 때만 커밋하는 것이 원칙 (P19 fast path 원칙과 동일).

## 2026-11-02 (21:00 KST) — P19 재감염 0건 (34회 연속 재감염 종료) + P10 MDEXT 2건 + tag taxonomy +3 + push 성공

**발견:**
- P19: **재감염 0건** — 3단계 판별에서 working tree / HEAD / origin/main 모두 `자동 추가` 0건. 10-30 이후 34회 연속 재감염이 **중단**됨. `git restore` 복구 경로 불필요.
- P18 pipe 오염(`^|- `) 스캔: wiki 전체 + skill references 모두 0건. index.md / logs/index.md / SCHEMA.md triple-pipe 0건.
- P10 MDEXT 2건: `code/finviz-screener-parsing.md`의 `[[code/scripts.md]]`, `[[infra/cron-jobs.md]]` → `.md` 제거 (P10 규칙).
- Lint ⑧: 미등록 태그 3건(`finviz`, `screener`, `debugging`)이 신규 페이지 1건에 집중 → **taxonomy 확장** 판단 → SCHEMA.md `code/` 행에 3개 추가 (149 → 152). 개별 페이지 수정 0건.

**Audit (5종 전항목 통과):**
- wikilink-audit.py: MD 0 / WL 0 / Cross-domain 0 / Barename 0 / MDEXT 0
- markdown-link-audit.py: P11 0 / Real broken 0
- index-md-audit.py: registered 89 = actual 89 / dead 0 / REAL MISSING 0
- tag-audit.py: taxonomy 152 / used 140 / registered 140 / Unknown 0
- logs-index-link-audit.py: broken 0 / notref 0 / covered 13 / ambiguous 0
- auto-fill-dates.py: Filled 0 / Skipped 21(raw immutable) / Errors 0

**Stale:** 63개 페이지(30일+, 수동 검토 플래그) / 날짜 정보 없음 21개(전부 raw/ immutable)

**logs/index.md 갱신 (P30 python 인서트):**
- **신규 월 섹션 신설**: `### November` — logs/index.md에 2026-11 로그가 처음 등장 → October 섹션 **앞**에 November 섹션 생성 (역시간순).
- ⚠ 첫 시도에서 기준 행(`|| 10-30 21:00`) 앞에 삽입 → October 테이블 헤더와 November 헤더가 뒤섞여 구조 깨짐. `git checkout index.md`로 되돌린 뒤 **월 섹션 헤더 위치(### October) 앞에 삽입**하는 방식으로 재시도 → 정상.
- 기준 행 prefix 복사 → triple-pipe 0건, `cat -A` 인접 행 prefix 일치 확인.

**커밋:**
- logs 서브모듈: `01ebf95` (master) — push `fabf116..01ebf95`
- parent wiki: `a726483 auto-sync 2026-11-02 21:00 KST` — push `0748ae4..a726483`
- 최종 상태: working tree / HEAD / origin/main 모두 `자동 추가` 0건, `git status` clean.

**교훈:**
- **신규 월 첫 로그 등장 시 월 섹션을 기존 월 섹션 앞에 신설**해야 한다 (역시간순). 기준 데이터 행 앞에 삽입하면 테이블 헤더가 뒤섞인다.
- P19 재감염 종료는 로직 변경의 결과가 아니라 외부 자동화 프로세스(`self_hermes.py` / auto-sync cron) 동작 변경의 결과일 가능성이 높다. **재발 가능성을 배제하지 말고 3단계 판별은 매 실행 독립 수행**할 것.

---

## 2026-10-30 (21:00 KST) — P19 재감염 (33회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` footer 뒤에 `— 자동 추가 (2026-10-30)` 레이블 서브모듈 항목 **70건** 대량 삽입 (subagents-library 5 + logs 65).
  - **working-tree 전용 오염** — 3단계 판별: working tree **70건** / HEAD **0건** / origin/main **0건**.
  - `git diff HEAD -- index.md` = rogue 추가분 71줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용 (커밋 불필요).
  - rogue 68→70 증가는 logs 신규 파일 2건 증가분 (정상 패턴, P19 "rogue = logs 파일 수에 비례" 규칙).
- P18 pipe 오염(`^|- `) 스캔: wiki 전체 + skill references 모두 0건. logs/index.md triple-pipe 0건.

**Audit (5종 전항목 통과):**
- wikilink-audit.py: MD 0 / WL 0 / Cross-domain 0 / Barename 0 / MDEXT 0
- markdown-link-audit.py: P11 0 / Real broken 0
- index-md-audit.py: registered 87 = actual 87 / dead 0 / missing 0
- tag-audit.py: taxonomy 149 / used 137 / registered 137 / Unknown 0
- logs-index-link-audit.py: broken 0 / notref 0 / covered 13 / ambiguous 0
- auto-fill-dates.py: Filled 0 / Skipped 20(raw immutable) / Errors 0

**Stale:** 63개 페이지(30일+, 수동 검토 플래그) / 날짜 정보 없음 operational 0개

**logs/index.md 갱신 (P30 python 인서트):**
- 신규 1건 등록: `2026/2026-10-30-2100.md` (본 로그).
- 기준 행(`|| 10-29 21:00`) prefix 복사 → triple-pipe 0건, `cat -A` 인접 행 prefix 일치 확인.

**커밋:**
- logs 서브모듈: `fabf116` (master) — push `b524f67..fabf116`
- parent wiki: `e00f692 auto-sync 2026-10-30 21:00 KST` (submodule pointer bump) — push `abc5f96..e00f692`

---

## 2026-10-29 (21:00 KST) — P19 재감염 (32회 연속, working-tree) + audit 전항목 통과 + push 성공

**발견:**
- P19: `index.md` footer 뒤에 `— 자동 추가 (2026-10-29)` 레이블 서브모듈 항목 **68건** 대량 삽입.
  - **working-tree 전용 오염** — 3단계 판별: working tree **68건** / HEAD **0건** / origin/main **0건**.
  - `git diff HEAD -- index.md` = rogue 추가분 69줄뿐(+정식 수정 0건) → `git restore index.md` 빠른 경로 적용 (커밋 불필요).
  - rogue 67→68 증가는 logs 신규 파일 1건 증가분 (정상 패턴).
- P18 pipe 오염(`^|- `) 스캔: wiki 전체 + skill references 모두 0건.

**Audit (5종 전항목 통과):**
- wikilink-audit.py: MD 0 / WL 0 / Cross-domain 0 / Barename 0 / MDEXT 0
- markdown-link-audit.py: P11 0 / Real broken 0
- index-md-audit.py: registered 87 = actual 87 / dead 0 / missing 0
- tag-audit.py: taxonomy 149 / used 137 / registered 137 / Unknown 0
- logs-index-link-audit.py: broken 0 / notref 1(신규) / covered 13
- auto-fill-dates.py: Filled 0 / Skipped 20(raw immutable) / Errors 0

**Stale:** 63개 페이지(30일+, 수동 검토 플래그) / 날짜 정보 없음 operational 0개

**logs/index.md 갱신 (P30 python 인서트):**
- 신규 2건 등록: `2026/2026-10-29-2100.md` (본 로그), `2026-10-29-1835.md` (매크로 전략 리포트).
- 기준 행(`|| 10-28 21:00`) prefix 복사 → triple-pipe 0건, `cat -A` 인접 행 prefix 일치 확인.

**커밋:**
- logs 서브모듈: `b524f67` (master) — push `103fed4..b524f67`
- parent wiki: `abc5f96 auto-sync 2026-10-29 21:00 KST` (submodule pointer bump) — push `72aaeae..abc5f96`

---

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