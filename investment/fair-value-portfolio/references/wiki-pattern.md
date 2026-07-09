# Karpathy LLM Wiki Pattern — 지식 관리 아키텍처

> Reference: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
> 이 문서는 `fair-value-portfolio` 스킬이 참조하는 지식 관리 패턴입니다.

## 원칙

| 기존 (잘못된 방식) | Karpathy Wiki 방식 |
|-------------------|-------------------|
| 모든 정보를 메모리(~2KB)에 저장 | 메모리 = 포인터만 (wiki 위치, 사용자 선호) |
| 매 세션마다 정보 재탐색 (RAG) | 위키에 한 번 저장, 지속적 갱신 |
| 코드가 지식의 전부 | 마크다운 위키가 지식 = 실행 코드와 분리 |
| 정보 분산: 메모리/세션DB/스크립트/여기저기 | 단일 진실 공급원: GitHub wiki |

## 3계층 아키텍처

```
1. RAW SOURCES (불변)
   → 원본 문서 (기사, 논문, PDF, 메모)
   → LLM은 읽기만 함, 절대 수정 금지
   → GitHub repo의 raw/ 디렉토리

2. THE WIKI (LLM 유지보수)
   → LLM이 생성하고 갱신하는 마크다운 페이지
   → INDEX.md (카탈로그), wiki/xxx.md (지식 페이지)
   → LLM이 쓰고 인간이 읽음

3. THE SCHEMA (작동 규칙)
   → SCHEMA.md — LLM이 위키를 유지보수하는 방법
   → INDEX.md 먼저 → wiki/xxx.md 순서로 검색
   → LOG.md에 모든 변경 기록 (append-only)
```

## INDEX repo + Submodule 아키텍처

기본 Karpathy Wiki는 단일 저장소지만, **여러 지식 도메인을 분리**하고 싶다면:

```
mybotagent/hermes-wiki          ← INDEX repo (메인)
├── AGENTS.md / SCHEMA.md       ← 위키 유지보수 규칙
├── index.md                    ← 마스터 카탈로그 (모든 submodule의 INDEX를 여기서 관리)
├── log.md                      ← 변경 이력
├── analysis/                   ← 직접 관리하는 분석 페이지
├── infra/                      ← 환경/설정
├── code/stock-analysis-toolkit/ ← submodule → 별도 repo
└── work/portfolio-analysis/     ← submodule → mybotagent/logging
```

**동작 방식**:
- `git clone --recurse-submodules <INDEX_REPO>` → 모든 지식을 한 번에 가져옴
- INDEX repo의 `index.md`가 모든 submodule을 카탈로그
- 주제가 완료/outdated되면 submodule 제거 + GitHub repo archive
- 새 주제 발생 시: `git submodule add <repo_url> work/<topic>/`

**실제 적용 상태** (2026-05-31):
- INDEX: `mybotagent/hermes-wiki` — Karpathy wiki with submodules
- submodule: `work/portfolio-analysis` → `mybotagent/logging` (portfolio analysis)
- submodule: `code/stock-analysis-toolkit` → `mybotagent/stock-analysis-toolkit` (scripts)
- archived: 3 thread wikis (hermes-wiki-thread-*) — 1회성 세션 백업, 더 이상 사용 안 함

## 이 스킬에서의 적용

- `wiki/config.md` — GitHub 토큰, 서버 설정, Calendar 경로
- `wiki/methodology.md` — 적정 PER 분석, S+~F 등급 방법론
- `wiki/tickers.md` — 포트폴리오 종목 메타데이터
- `wiki/cron.md` — 크론 작업 (Job ID 포함)
- `wiki/scripts.md` — 서버 스크립트 참조

## 검색 프로토콜

```
모르는 게 있으면?
  → 1. INDEX.md 읽기 (무엇이 어디 있는지)
  → 2. wiki/xxx.md 읽기 (상세 정보)
  → 3. session_search (과거 대화 맥락)
  → 4. 사용자에게 질문 → 답변을 wiki에 기록
```

## 자신 없는 동작 금지

- GitHub 토큰 위치, 크론 Job ID, Calendar 경로 — **절대 추측 금지**
- 위키에서 먼저 확인할 것
- 위키에 없으면 기록할 것 (그래야 다음에 또 틀리지 않음)
