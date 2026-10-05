---
name: meeting-documentation
description: "3자회의 facilitation + 회의록 문서화 워크플로 — PM 라이브 facilitation(@mention 체인, 단일 공식) → 회의록 저장(HHMM_topic-slug/{agenda,discussion,decisions,next_steps,DESIGN}.md) → **중간 저장(incremental save) → phase 끝마다 commit** → git push → Linear/Kanban 업데이트 → 구현은 문서 이후"
version: 1.2.0
author: aiprofit
platforms: [linux]
metadata:
  hermes:
    tags: [meeting, documentation, workflow, design-doc, linear, kanban, time-prefix, topic-slug, incremental-save, in-progress-commit]
    related_skills: [kanban-orchestrator, kanban-worker, linear]
---

# Meeting Documentation Workflow

> **Core rule:** 문서가 먼저, 구현은 나중. 회의 결과는 반드시 정해진 형식으로 GitHub에 저장하고, Linear/Kanban을 동기화한 후에야 구현 진입.
>
> **Format upgrade (2026-06-29)**: 회의 폴더명에 시간 prefix (`HHMM_`) 필수. 한 회의 = 한 폴더 = 4-5개 파일 (agenda / discussion / decisions / next_steps / DESIGN).

## When This Skill Activates

**Live facilitation (Section 0)**:
- 사용자가 3자 회의(aiprofit + plannerbot + 채니봇)를 시작할 때
- "서로 멘션하면서 토론해" / "3자회의 시작" 같은 요청
- 복잡한 결정(직무, 아키텍처, 도구 선정) 진행 중

**Post-meeting documentation**:
- 사용자가 3자 회의를 마친 후
- 사용자가 "회의록 정리해" / "문서화해" / "정리해서 올려" 라고 요청
- 복잡한 기술 결정/아키텍처 논의가 끝난 후
- 사전 설계 문서가 필요한 구현 작업 전 ("문서 먼저")

**Time-prefixed meeting file restructure** (NEW 2026-06-29):
- 사용자가 "회의 GitHub에 올려" + "시간대-제목 형식으로" 요청
- 한 날 여러 회의를 4-파일 표준으로 분리
- 기존 `2026-06-29-1230.md` 단일 파일 → `2026/06/29/1230_topic-slug/{4 files}` 구조

## Repository Structure (v1.1 — HHMM topic-slug)

회의록은 **mybotagent/meeting-notes** (private)에 저장. **같은 날짜라도 회의를 시간대별로 분리** (aiprofit 명시 요구):

```
meeting-notes/
├── INDEX.md              ← 연도별/월별 회의록 목차
├── README.md             ← 저장소 설명
├── YYYY/                 ← 연도
│   └── MM/               ← 월
│       └── DD/           ← 일
│           ├── README.md                    ← 하루 전체 회의 인덱스 (필수)
│           ├── HHMM_<topic-slug>/            ← 회의 1 (시간 prefix 필수)
│           │   ├── agenda.md                 ← 안건
│           │   ├── discussion.md             ← 논의 내용 (자세히)
│           │   ├── decisions.md              ← 결정 사항 (가장 중요)
│           │   ├── next_steps.md             ← 다음 단계
│           │   └── DESIGN.md                 ← 기술 설계 문서 (구현 전 필수)
│           ├── HHMM_<topic-slug>/            ← 회의 2 (같은 날 다른 시간)
│           │   └── ... (4개 파일 + DESIGN)
│           └── HHMM_<topic-slug>/            ← 회의 3
│               └── ...
```

### Topic 네이밍 규칙 (aiprofit 명시 요구 — 2026-06-29 적용)

- 형식: `HHMM_<topic-slug>` (시간 prefix 4자리 + underscore + kebab-case 주제)
- 예시:
  - `0900_wiki-knowledge-search-onboarding`
  - `1230_phase5-operations-automation`
  - `1930_linear-sho22-kanban-sync`
  - `2020_sho24-roi-ir-guide-push`
- 시간은 KST 24시간제 4자리 (`0900` = 오전 9시, `2357` = 오후 11:57)
- 24시 넘기면 다음 날 날짜 폴더에 저장, 시간 표기는 실제 회의 시작 시간

### 왜 시간 prefix가 필수인가 (aiprofit이 직접 정착시킨 워크플로우)

- 하루에도 5-15개 회의를 함 (단순 대화 + 3자회의 + 단독 작업 + 1:1)
- 시간순 정렬이 자동으로 됨 (`ls`만 쳐도 chronological)
- "어느 회의에서 결정한 거였지?" → 시간대 기억나면 즉시 찾기 가능
- `agenda.md` / `discussion.md` / `decisions.md` / `next_steps.md` 4개 파일로 회의 내 role별 명확히 분리

### 4-파일 표준 구조 (각 회의 폴더에 필수)

- `agenda.md` — 안건 + 참고 자료 + 원래 안건 vs 실제 논의 흐름
- `discussion.md` — 시간순 논의 전개 (Phase 1, 2, 3 등)
- `decisions.md` — 결정 사항 (가장 중요, 한눈에 보기)
- `next_steps.md` — 다음 단계 + Linear/Kanban 의존성
- `DESIGN.md` — 기술 결정 포함 시 (선택, 구현 전 필수)

### 하루 인덱스 `README.md` 표준

`YYYY/MM/DD/README.md`에 그날 모든 회의를 시간순으로 인덱싱:

```markdown
# 2026-06-29 (월) 회의록

> **총 12개 회의** — 시간순으로 정렬

## 회의 목록
| 시작 | 제목 | 폴더 |
|------|------|------|
| 08:55 | Wiki 온보딩 | `0855_wiki-knowledge-search-onboarding/` |
| 12:30 | Phase 5 운영 자동화 | `1230_phase5-operations-automation/` |
| ... | ... | ... |

## 회의 의존성
```
0855 온보딩
  └── 0930 설계
        └── 1100 Neo4j 설치
              └── ...
```
```

**Template (3-proposal matrix)**: `templates/3-proposal-matrix.md` 참조 (재사용 가능한 12 cells 매트릭스 + 비교표 + deep tier 결정).
**Template (topic-based meeting note)**: `templates/topic-based-meeting-note.md` 참조 (재사용 가능 skeleton).
**Reference (paste-then-execute hybrid)**: `references/paste-then-execute-pattern.md` 참조 (3 봇 합의 후 velocity + discipline 양립 — paste + 60s veto + auto-execute).
**Reference (cross-bot verification)**: `references/cross-bot-verification.md` 참조 (Gate 1 paste 게이트 + sandbox 격차).
**Reference (Discord thread routing failure case study)**: `references/discord-thread-routing-failure.md` 참조 (chat_id 라우팅 실패 메커니즘 + 자가 점검 3초 체크).
**재구성 워크플로우**: `references/restructure-existing-notes.md` 참조.

### DESIGN.md Naming & Sibling Structure (NEW 2026-06-30)

## Mandatory Files Detail

### HHMM_topic-slug/agenda.md
```markdown
---
tags: ["meeting-notes", "hermes-agent", "wiki-knowledge"]
date: 2026-06-29
time: "08:55-09:50 KST"
participants: [aiprofit, 채니봇, plannerbot]
title: Wiki Knowledge Search — 온보딩
---

# Wiki Knowledge Search — 온보딩

> **일시**: 08:55-09:50 KST (55min)
> **참여**: aiprofit, 채니봇, plannerbot
> **목적**: Wiki Knowledge Search Plugin 온보딩 + 참고자료 분석

## 안건

1. Karpathy LLM Wiki / OpenKB / treylom/knowledge-manager 참고자료 분석
2. 우리 위키 구조 onboarding (hermes-wiki-super 12 repos)
3. 확장 가능한 skill plugin 설계 방향 도출

## 참고 자료

- [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [OpenKB](https://github.com/VectifyAI/OpenKB) (⭐2.7k)
```

### HHMM_topic-slug/discussion.md
- 시간순 논의 전개
- Phase 1, 2, 3 등 섹션 구분
- 사용자 의견은 인용 형식 ("> 사용자: ...")
- 코드 스니펫, 매트릭스 포함 가능

### HHMM_topic-slug/decisions.md (가장 중요한 파일)
```markdown
# 결정 사항

1. ✅ **Neo4j + Vector Index GraphRAG** 채택
2. ✅ 임베딩 모델: **BAAI/bge-m3** (384d, 무료 오픈소스, 다국어)
3. ✅ 비용: AuraDB Free → Local Community 결정

| 항목 | 결정 | 근거 | Risk | Action |
|---|---|---|---|---|
| Storage | Neo4j | Vector+Graph 통합 | RAM 1.9GB | systemd enable |
| 임베딩 | bge-m3 | 무료, 다국어 | 속도 | 캐싱 |
```

### HHMM_topic-slug/next_steps.md
```markdown
# 다음 단계

- Wiki Knowledge Search 설계 토론 (09:30)  ← 다음 회의 시간 prefix
- Neo4j vs SQLite vs Vector DB only 비교

## Linear/Kanban 의존성

- SHO-29 (Wiki Knowledge Search Plugin) - In Progress
- SHO-21 (Skill Dynamic Selection Phase ①) - Done
```

### HHMM_topic-slug/DESIGN.md (구현 전 필수 ⭐)
기술적 결정이 포함된 회의는 **반드시 DESIGN.md 작성 후에만 구현 진입.**

```markdown
# Wiki Knowledge Search — Design Document v0.1

> **Status:** Design Phase
> **Date:** 2026-06-29
> **Meeting:** [회의명](./README.md)

## 1. Overview
## 2. Architecture
## 3. Detailed Design
## 4. Query / Usage Patterns
## 5. Deployment
## 6. Future Extensions
## 7. Open Questions / 미합의 영역
## 8. References
```

### HHMM_topic-slug/README.md (선택)

회의 폴더 안에 별도 README는 불필요 (하루 단위 README에 인덱스 있음). 단, 회의가 매우 복잡하고 의존성이 많으면 폴더 내 README 추가 가능.

## Live 3자회의 Facilitation (PM Mode) — Section 0

3자회의는 **회고가 아니라 진행 중 패턴**이 있다. 회의록을 작성하기 전에 회의 자체를 어떻게 facilitation할지에 대한 규칙. **Hermes는 PM 역할**, 모든 turn에서 사회 진행.

### 🔴 이 skill이 자동 load 안 되는 함정

Hermes는 사용자가 "서로 멘션하면서 토론해" / "3자회의 시작" / "X 기획안 N개를 만들어" 패턴을 보내도 **이 skill을 자동으로 load하지 않는다**. Discord context에서 next turn에 본문이 주입되지 않으면 아래 규칙을 모르고 응답한다.

**필수 load 시점** (turn 시작 전 skill_view 1회):
- 사용자가 처음으로 3자회의/토론 패턴 보냄
- 이전 turn에서 봇 1개 이상 정정을 받음 (이전에도 위반했었음 신호)
- 새 thread의 첫 turn

**신호 받은 순간 즉시**: `skill_view(name='meeting-documentation')` 호출 → 컨텍스트 로드 후 진행.

### Discord Channel Hygiene (필수 — 반복 정정됨, 2026-06-29~)

`채니봇 = 봇 슬레이브, aiprofit = 마스터`. 채널별 엄격 격리:

| 채널 | 누가 활동 | 봇 응답 가능 시점 |
|---|---|---|
| **Main (#project-manage 등)** | aiprofit 위주, 봇은 핑 받기 전 무응답 | aiprofit가 **새 thread 열기 전** 또는 **직접 `<@채니봇ID>` ping** 한 경우만 |
| **Thread** | 봇 자유 활동 | Active turn / waiting mode 사이클 정상 진행 |

**aiprofit 명시 요구** (반복 정정됨):
- **"여기서 대화하지말기"** → main에서 즉시 대기 모드. 짧은 응답 1줄만 + 대기 선언
- **"쓰레드 연 곳에서만 대화하기"** → 활성 thread ID 추적하고 그 thread에서만 활동
- 봇이 main에서 합법적으로 응답하는 경우 = aiprofit이 직접 `<@채니봇ID>` ping 보낸 경우

**활성 thread 변경 감지** (Discord chat_id + thread_id 동시 추적):
- 새 메시지 도착 시 `channel_id` 확인 → main이면 inactive, thread면 active
- thread ID는 session_search 또는 memory의 `active_thread_id` 참조
- `chat_id`는 채널, `thread_id`는 그 안의 대화 위치 — 둘 다 필요

**🔴 Thread = Session Boundary 원칙 (aiprofit 2026-07-01 명시 요구)**:
- 각 thread = 독립 session (컨텍스트 격리)
- 새 thread = 새 session, 이전 thread 컨텍스트 누수 X
- 다른 채널 메시지 받으면 → 명시적으로 "다른 채널" 인지 후 그 채널의 chat_id로 reply
- 의심 시 `fetch_messages`로 채널 구조 재확인

**⚠️ 정확한 chat_id 라우팅 메커니즘 (2026-07-01 실패 인스턴스)**:
- ❌ 흔한 실수: parent `reply_to`가 정확한 thread를 가리켜도, **발송 chat_id가 채널 레벨**이면 → 응답이 main에 떨어짐
- ✅ 올바른 패턴: `reply_to` AND `chat_id` 둘 다 thread의 값이어야 함
- 봇이 main에 답한 후 → 즉시 짧은 사과 1줄 + "활성 thread X에서만 활동" 선언

**Pitfall (반복됨)**:
- 활성 thread가 있는데 main에서 응답 → chat_id 잘못 + thread 분실
- 메모리에 chat_id만 적고 thread_id는 누락 → 다음 turn에서 main에 잘못 응답
- "메인에서 응답 금지" 명시 직후에도 main에 답변 → rubber-stamp 위반
- **reply_to만 맞추고 chat_id는 채널 레벨** → 봇이 main에 답변 → 사용자 즉시 시정 ("여기서 대화하지말기! 쓰레드 연 곳에서만!")
- 봇이 자기 차례라고 판단하고 무리하게 main에서 활동 → aiprofit "메인 채널 무음, 직접 ping 없으면 절대 응답 X" 명시 위반

### Bot 역할 고정 (불변)

| Bot | 역할 | 책임 |
|---|---|---|
| **aiprofit** | 최종 결정권 | 모든 합의안의 ✅/수정/보류 권한 |
| **plannerbot** | Claude 분석 | 제안 반박, 보완, 보강 |
| **Hermes (채니봇)** | PM/사회 | 제안 → 종합 → 합의안 정리 → 승인 요청 |

### @mention 체인 프로토콜 (필수)

3자 모두 Discord에서 활동할 때의 turn 흐름:

```
Hermes (PM)
  → ① 안건 + Hermes 제안 + Plannerbot 질문 3-4개
  → @plannerbot 호출 (꼭 <@USER_ID> 형식)

Plannerbot
  → ① Hermes 제안 평가 (동의/반박/보완)
  → ② Q1-Q4 답변
  → @aiprofit 최종 승인 요청

aiprofit
  → ① 승인/수정/보류 결정
  → ② (승인 시) DESIGN.md + Linear + Kanban 등록 지시

Hermes (PM, 정리)
  → ① 합의안 v_n 확정
  → ② DESIGN.md 작성 시작 (승인 후)
```

**필수 규칙** (하드 — 위반 시 aiprofit 정정):

1. **`<@USER_ID>` 형식만 작동**. 평문 "@plannerbot @dsbot" 같은 텍스트는 봇이 시그널 못 받음 — 반드시 `<@1520719061498204262>` Discord mention 형식. 봇 ID는 memory의 `Plannerbot` 항목 참조.
2. **각 bot turn에 반드시 다음 봇 @mention** (없으면 dead-end)
3. **한 메시지에 모든 봇이 동시에 답하지 않음** (순차 진행)
4. **Hermes는 plannerbot 답변을 평가할 때 보완/반박을 명시** (rubber-stamp 금지)
5. **Waiting mode에서 @mention 금지** (아래 두 모드 섹션 참조)

**Pitfall (반복됨, 2026-06-30)**: 채니봇이 평문 "@plannerbot @dsbot 의견 주세요"로 쓰면 봇들이 시그널을 못 받음 → aiprofit "다른 봇들을 멘션을 제대로 안했는데?" 정정 받음. 매 turn에서 `<@...>` 형식 확인 필수.

---

### @mention 두 가지 모드 (필수)
|---|---|---|
| **Active turn** | 새 안건/제안/질문/합의안 제시 시 | ✅ 필수 (다음 봇 호출) |
| **Waiting mode** | 신호 대기 / aiprofit 승인 대기 / plannerbot 답변 대기 | ❌ 금지 (aiprofit 명시 요구) |

**Waiting mode 진입 조건**:
- aiprofit에게 옵션/승인/신호 요청한 직후
- plannerbot 답변 대기 중
- DESIGN.md/Linear/Kanban 생성 aiprofit 승인 대기 중
- aiprofit이 "대기모드 유지면 언급하지마" 명시 시

**Waiting mode 시 행동**:
- 짧은 상태 보고 1줄 (예: "대기모드 유지. 신호 대기 중")
- **@mention 일체 금지**
- 새 turn 들어와도 언급 없이 단순 응답만

**Pitfall**: Active turn이라고 잘못 판단하고 무리하게 @mention하면 aiprofit이 정정함 ("채니봇아 대기모드 유지면 언급하지마"). 확실하지 않으면 짧은 보고 + 명시적 대기 선언으로 안전하게.

### 단일 공식 원칙 (Single Recommendation)

aiprofit의 value investing 철학 (`단일공식, 조건문 금지, PER75:PBR25 고정`)을 회의 facilitation에 그대로 적용:

- **옵션 나열 금지**: "A 또는 B 또는 C" 식 분기 금지
- **단일 추천 + 근거**: 1순위 추천 + 2순위 fallback (최대 2개)
- **예외/조건/특례 금지**: 모든 합의안에 동일 공식 적용
- **매트릭스 5열 표준**: Item / Recommendation / Rationale / Risk / Action

```markdown
## 🎯 합의안 (단일 공식)

### 1순위: X
**근거**: ...
**반대 검토**: ...
**Fallback**: Y (조건: ...)

### Career Path / Timeline (단일 공식)
| Step | Item | Lock |
|------|------|------|
| M1 | ... | 🔒 필수 |
| M2 | ... | 🔒 필수 |
| M3 | ... | 🔓 선택 |
```

### Decision Matrix 템플릿 (재사용)

복잡한 결정(직무, 아키텍처, 도구 선정)에 사용하는 5열 매트릭스:

```markdown
| 항목 | 결정 | 근거 | Risk | Action |
|---|---|---|---|---|
| Track | B (AgentOps) | v3 §11 권장 + 활용도 80% | 신입 JD 적음 | M1 시작 |
| 지역 | 서울 한정 | 통근 + 생활권 | JD pool 축소 | Tier 1-4 scan |
| Timeline | 6개월 (M1-M6) | v3 §6.2 + 기존 자산 활용 | M3 delay 시 M4 압축 | 주차별 점검 |
```

### Career/Portfolio Discussion Pattern (특화)

직무/포트폴리오 논의 시 4-tier JD scan + Phase 1/2/3 portfolio 구조:

```
1) v3 문서 원문 확인 (직접 인용)
2) 기존 자산 활용도 매트릭스
3) Tier 1-4 JD scan (지역 한정)
4) Phase 1-3 portfolio (Foundation → Core → Portfolio)
5) 단일 공식 timeline (M1-M6)
```

**자주 쓰는 evaluation 4차원**:
- **v3 권장도**: ★★★ (1순위 명시) / ★★ (흡수) / ★ (career path)
- **지역 JD 수**: 잡코리아 기준 count
- **신입 친화**: 신입/Junior/주니어 JD count
- **활용도**: 기존 자산 재사용 %

### Ankor Pattern — Single-Track Multi-Anchor (NEW 2026-07-01) ⭐

aiprofit 반복 패턴: **"칸반보드랑 linear를 보고 오늘 해야할 업무에 대해서 회의를 시작하자"** — Kanban/Linear 데이터를 기반으로 한 회의 시작 시. **Multi-Proposal과 다르다**:

| 패턴 | 트랙 수 | 안건 수 | 구조 |
|------|---------|---------|------|
| Multi-Proposal | 1 | N개 기획안 | 봇 슬롯 병렬 + Round 1-3 |
| **Ankor** | **1** | **N개 안건** | **직렬 + 우선순위 압축 + value-first** |

#### Step 1: 데이터 수집 (PM 즉시)

회의 시작 시 Kanban + Linear 통합 조회 — **두 소스를 동시에 봐야 신뢰**:

| 소스 | 도구 | 핵심 |
|------|------|------|
| **Kanban** | `~/.hermes/kanban.db` (SQLite 직접 조회) | status / priority / exec_order / created_by |
| **Linear** | GraphQL API (`~/.hermes/.env`의 `LINEAR_API_KEY`) | identifier / state.type / priority / updatedAt |

**Pitfall**: 한 소스만 보고 시작 → 다른 쪽의 의존성 놓침. 항상 **두 소스 동시**.

**읽기 표준**:
- Kanban: `SELECT * FROM tasks WHERE status IN ('ready','backlog','in_progress') ORDER BY priority, exec_order`
- Linear: `issues(first:30, filter:{state:{type:{nin:["completed","canceled"]}}})` + 최근 Done 5개

#### Step 2: 안건 압축 — Ankor #1, #2, #3

수집된 태스크를 **P1 → Ankor #1, P2 → Ankor #2, P3 → Ankor #3**로 매핑:

```markdown
## 📋 READY 8개 — 우선순위 정렬

| # | ID | P | exec | 제목 | 비고 |
|---|---|---|---|---|------|
| 1 | `t_xxx` | P1 | 0 | Title | ⭐ 최우선 |
| 2 | `t_yyy` | P2 | 0 | Title | 메타 |
| 3 | `t_zzz` | P3 | 0 | Title | |
```

- **중복 발견 시 즉시 병합 표시** (예: t_beff4ce4 + t_e3627b3c = 동일 lint 작업 → Ankor #1에 병합)
- P2/P3가 5개 이상이면 → "내일 회의로 이연" 권고 (오늘 capacity 한정)

#### Step 3: Value-First 1분 검증 (Ankor #1만)

워크플로우 원칙 = **"가치 검증 선행"**. Ankor #1이 정말 오늘 1순위인가? 1분 체크:

| 평가 항목 | 점수 (1-10) | 근거 |
|-----------|------------|------|
| 사용자 자산 활용 | 🟢 9/10 | hermes-wiki 직접 사용 |
| JD 매칭 | 🟡 5/10 | AI Agent 직무 간접 |
| 미실행 기간 | 🟢 9/10 | 06-27 도입 후 한 번도 안 함 |
| 위생 리스크 | 🟢 9/10 | 위생 부채 누적 |
| 비용 | 🟢 8/10 | 2-4h, 외부 의존 0 |

→ **임계 7 통과** 시 시작. 미만이면 → 다른 Ankor 검토.

#### Step 4: 5-Dimension 합의 (Sequencing + Capacity + AC + Risk)

```markdown
### A. Sequencing
- Ankor #1 → FIRST / Ankor #2 → SECOND / Ankor #3 → LAST

### B. Capacity
- lint = 2-4h / split = 30min / Ankor #2 = capacity-dependent
- Realistic today = #1 + #3 / #2 defers to tomorrow

### C. AC (Acceptance Criteria)
| Ankor | AC |
|-------|-----|
| #1 | lint 실행 완료 + 결과 log + 발견 이슈 kanban 분리 |
| #3 | SHO-XX=Done + SHO-XX/v2.0 신규 epic + Linear sync |

### D. Risk
1. Lint scope creep — 100% clean 약속 X
2. Split stall repeat — owner 배정 필수
3. Meeting artifact drift — Obsidian mirror

### E. PM 결정
- 3 Ankors 병렬 ❌ → 직렬 #1 → #3 → #2 강제
```

#### Step 5: 사용자 1마디 결정 프레임 (3 옵션 고정)

| 옵션 | 의도 |
|------|------|
| ① | "전부 동의 — Ankor #1 시작" |
| ② | "수정 있음" — 어느 안건에 다른지 1줄 |
| ③ | "보류" → 기본값 ① 자동 적용 |

#### Pitfall (Ankor 패턴)

- **데이터 수집 없이 회의 시작** → aiprofit "칸반보드 보고" 명시 요청 무시
- **한 소스만 조회** (Kanban만 or Linear만) → 의존성 놓침
- **중복 태스크 병합 안 함** → 같은 lint task가 2개로 분산
- **모든 Ankors "오늘" 처리 약속** → capacity 무시 → quality 저하
- **value-first 검증 생략** → 즉시 시작 → 작업 가치 의문 시 시간 낭비
- **default ① 약속 후 침묵 시 강제 진행** → 명확한 fallback 선언 없이 시작

### Multi-Proposal Round Debate Pattern (NEW 2026-06-30)

aiprofit 반복 패턴: **"X 기획안 N개를 서로 멘션하면서 토론해"** 직무/포트폴리오/아키텍처 결정 시.

**구조** (3 기획안 = N=3 기준, 일반화 가능):

#### Step 0: Slot 할당 (PM이 즉시 공지)

```markdown
| Slot | 담당 봇 | 각도 |
|------|---------|------|
| A | <@plannerbot_id> | 1순위 (가장 적합한 각도) |
| B | <@dsbot_id> | 2순위 |
| C | PM (Hermes) | 3순위 또는 백업 |
```

→ 4개 이상 필요 시 추가 봇 or PM이 백업으로 나머지.

#### Step 1: Round 1 — 독립 제안 (병렬 가능)

각 봇이 자기 슬롯 1개씩, **6-8줄 단일 공식**:

```markdown
## Slot [X] — {각도 한 단어}

**1. 컨셉** — 1줄
**2. 데이터셋 후보** — 2-3개 + 추천 1
**3. 노트북 구조 (4개)** + 각 1줄
**4. 차별화 신호 2개** (신입 JD 관점)
**5. 리스크 1개** + 대응
**6. 일정 (M0-M3 주차별)**
```

- 각 봇 마지막 줄에 다음 봇 `<@ID>` mention (chain 형성)
- 6-8줄 짧게 (Discord 2000자 한도)

#### Step 2: Round 2 — 상호 비판 (순차, 의존성 있음)

각 봇이 **타 봇 제안 1개씩** 비판 + 보완 제안:

```markdown
## Round 2 — {타 봇} Slot [Y] 비판

**강점 1개** (명시 인정)
**약점/리스크 1개** + 보완 제안
**자신 Slot에 대한 반박 처리** (있으면)
```

- `<@타봇ID>` ping으로 대상 지정
- 자기 슬롯 반박도 1개 (rubber-stamp 방지)

#### Step 3: Round 3 — 확정본 + 비교표

비판 반영 후 v_n 확정 + 비교표:

```markdown
| Slot | 컨셉 | 데이터셋 | 신호 | 리스크 | 일정 |
|------|------|----------|------|--------|------|
| A | ... | ... | ... | ... | ... |
| B | ... | ... | ... | ... | ... |
| C | ... | ... | ... | ... | ... |
```

→ aiprofit OK 사인 → 1개 슬롯 freeze.

**PM (Hermes) 역할**:
- Round 1: 슬롯 할당 + 6-8줄 템플릿 공지
- Round 2: deadlock 시 중재, 봇 N개 합치기 가능
- Round 3: 비교표 작성 + aiprofit 결정 요청

**Pitfall (반복됨, 2026-06-30 데이터 분석 기획안 3개)**:
- 봇 없이 PM 혼자 3개 다 작성 → aiprofit "서로 멘션하면서" 위반
- slot 안 나누고 모두 다 다루기 → 동일 안건 반복 (WET)
- round 표시 없이 일렬로 쓰면 Round 어디서 끝나는지 모름
- Round 2에서 자기 슬롯은 방어만 하고 타 슬롯은 비판 안 함 → 비대칭 → aiprofit 정정

### 3-Dimension Proposal Evaluation Matrix (NEW 2026-06-30) ⭐

Multi-Proposal 라운드 외에 **단일 평가를 위한 3차원 매트릭스**가 필요할 때 사용 (직무/포트폴리오 기획안 비교, 아키텍처 옵션 비교 등).

#### 왜 3차원인가

- **5열 decision matrix** (Item/Recommendation/Rationale/Risk/Action) = 단일 결정용
- **3차원 매트릭스** (Whether/Feasibility/How to do better) = **N개 옵션 평면 비교용**
- aiprofit "가치 검증 선행" 원칙 → 실행 전에 진짜 가치 있는지 quantifiable하게 평가

#### 스키마 (12 cells/slot)

| 차원 | 4 sub-criteria | 평가 코드 |
|------|----------------|-----------|
| **Whether** (가치 입증) | signal-strength · ICP-fit · problem-freshness · 단일공식 부합 | 🟢 strong · 🟡 conditional · 🔴 weak |
| **Feasibility** (현실성) | dataset-access · infra-cost · time-budget · risk-mitigation | (동일) |
| **How to do better** (극대화) | methodology-rigor · differentiation · deliverable-quality · scope-discipline | (동일) |

#### 채니봇 적용 (Slot A/B/C 3 기획안 매핑 예시)

| Slot | Whether | Feasibility | How to do better |
|------|---------|-------------|------------------|
| **A** 코호트/퍼널/RFM | 🟢🟢🟡🟢 | 🟢🟡🟡🟡 | 🟢🟢🟢🟢 |
| **B** A/B + 인과 | 🟢🟢🟢🟢 | 🟡🟡🟢🟢 | 🟢🟢🟢🟢 |
| **C** ML LTV/Churn | 🟢🟢🟢🟢 | 🟢🟢🟢🟢 | 🟢🟢🟢🟢 |

→ 종합 점수 (🟢=3, 🟡=2, 🔴=1) × 12 cells = 비교 점수화. 동점 시 deep tier 우선.

#### PM 역할 (3 기획안 × 3 차원)

- Round 1 종료 후 각 슬롯의 3 차원 dry-fit
- Round 2에서 다른 봇 슬롯 12 cells 평가 (rubber-stamp 방지)
- Round 3에서 비교표 작성 + 종합 점수화 → aiprofit 결정 요청

**Template**: `templates/3-proposal-matrix.md` 참조.

### DESIGN.md Naming & Sibling Structure (NEW 2026-06-30)

#### Naming convention: `design.md` lowercase 강제
- 글로벌 rule (`~/.claude/CLAUDE.md`) 일관성
- cross-bot link / Linear ticket / commit message normalize
- "shouting" 회피 (lowercase = best practice)
- UPPERCASE 사용 시 override 사유 메모 필수

#### Sub-track sibling 구조
같은 repo 안에서 여러 track을 다룰 때:

```
portfolio-repo/
├── DESIGN.md                    ← main track (legacy UPPERCASE OK, 단 신규는 lowercase)
├── track-da/
│   └── design.md                ← 신입 DA track
├── track-ai-agent/
│   └── design.md                ← AI Agent Engineer track
└── ...
```

- 한 repo에 여러 track 디자인 doc → `track-<slug>/design.md`
- 메인 DESIGN.md는 legacy로 인정, 신규 sub-track은 sibling 구조
- cross-link 시 상대경로 (`./track-da/design.md`)

#### Path 검증 checklist
- [ ] 파일명 lowercase?
- [ ] UPPERCASE면 override 사유 메모?
- [ ] sibling 구조면 `track-<slug>/` prefix?
- [ ] sibling끼리 cross-link 가능?

### Cross-Bot Sandbox Verification Gate Pattern (NEW 2026-06-30) ⭐

각 봇이 **별도 sandbox / VM / working directory**에서 활동 (aiprofit workflow 필수 패턴):
- `plannerbot sees: ~/dev/projects/plannerbot/`
- `dsbot sees: ~/dev/projects/dsbot/`
- `chatni sees: ~/projects/portfolio-2026-track-b/`

→ **cross-sandbox file read = architecturally impossible**. "내가 봤어" = single-source-of-truth = process integrity 결손.

#### 🔴 Gate 패턴 (3-bot 합의 시 mandatory)

| Gate | 트리거 | 통과 조건 | 미통과 시 |
|------|--------|-----------|-----------|
| **Gate 1 — Verification** | PM이 "✅ 완료" 보고 시 | 대상 섹션 **chat-inline 본문 paste** (≤2500자/section) | 다른 봇 read 불가 → verdict 보류 |
| **Gate 2 — Decision Path** | aiprofit 결정 요청 시 | path-independent 결정만 summary commit 가능, path-dependent는 Gate 1 통과 후 | 결정 1·4·5 = Gate 1 의존, 결정 3 = summary commit 가능 |
| **Gate 3 — Pre-Flight** | 실행 직전 | `gh auth status` · `gh repo view` · local remote · Linear API key 4 check 전부 🟢 | 한 항목이라도 🔴 → 보류 |

#### Paste 프로토콜 (Gate 1 필수)

```markdown
## Gate 1 — §4 + §5 + §6 본문 paste (fresh read 결과)

**Fresh verification**:
- Path: `/home/ubuntu/projects/.../design.md`
- Size: N bytes · MD5: `xyz...`

### §4. {Slot X Title}
```
### 컨셉
{1줄}

### 노트북 4개
- 01_xxx.ipynb — {1줄}
- ...

### 3 차원 평가
| 차원 | 셀 | 평가 |
| ... | ... | ... |
```

### §5. {Cross-Bridge}
... (≤2500자/section)
```

**Pitfall (반복됨, 2026-06-30)**:
- "본인 인증 = verification" 가정 → dsbot/plannerbot 보류
- summary-only acceptance → 3-bot consensus 차단
- 자기 작성분(`§3 Slot B` 등)은 self-verify 가능, paste 생략 OK (3-bot 합의 권고)
- character limit 초과 시 section별 분할 paste

#### 결정 상태 언어 (canonical)

모든 결정 보고 시 **상태 코드 명시** (Gate 1/2/3 결과):

| 코드 | 의미 | 사용 시점 |
|------|------|-----------|
| 🟢 **active** | 결정 가능 상태, aiprofit OK 대기 | Gate 1 통과 후 |
| 🟢 **summary commit** | path-independent, summary 보고로 결정 가능 | Gate 2 통과 |
| ⏸ **blocked** | 의존성 (다른 결정/원격 URL 등) 대기 | path-dependent decision |
| 🔴 **verification incomplete** | Gate 1 미통과 | 본문 paste 전 |

### Pre-Flight Action Sequence (NEW 2026-06-30) ⭐

aiprofit OK 신호 받기 **전**에 실행 환경 4 check → 불필요 round-trip 방지:

#### 1️⃣ GitHub 인증
```bash
gh auth status          # user 확인 + token scope
gh api user --jq '.login'
gh repo view <org>/<repo>  # 존재 확인 (404면 생성 필요)
```

#### 2️⃣ Linear API
```bash
grep LINEAR_API_KEY ~/.hermes/.env | sed 's/=.*/=<REDACTED>/'
# workspace / team UUID 별도 확인 필요 시:
grep -iE 'linear.*workspace' ~/.hermes/.env
```

#### 3️⃣ Local repo 상태
```bash
git -C <repo> remote -v          # remote 비어있으면 push ready
git -C <repo> status --short     # untracked / modified 확인
```

#### 4️⃣ 파일 실재 검증 (verification gate용)
```bash
ls -la <path>                    # perms + owner + size + mtime
stat <path>                      # inode + access times
md5sum <path>                    # content fingerprint
git -C <repo> status --short      # 트랙킹 여부
```

#### 사전 보고 템플릿 (aiprofit에 제출)

```markdown
## ✅ Pre-flight 결과

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | `gh account` | 🟢 `mybotagent` active | Token scope: `repo` ✓ |
| 2 | `gh repo view` | 🔴 404 | 생성 필요 |
| 3 | local remote | 🟢 clean | push ready |
| 4 | Linear API key | 🟢 | workspace URL 별도 확인 필요 |
```

#### Pitfall (선 발견 후 적용)

- **pre-flight 없이 OK 요청** → aiprofit이 OK 사인 후 추가 확인 필요 → round-trip 1회 낭비
- **GitHub repo 404를 OK 요청 후에 발견** → 사용자 OK 무효화 → 비효율
- **`read:org` scope missing ≠ blocker** (push only 작업이면 충분), 모든 missing scope를 blocker로 잘못 보고하면 OK 보류 위험

### Pitfalls (Live Facilitation)

- **모든 turn에 @mention 빠뜨리지 마라.** 3자 중 1명이라도 missing → dead-end.
- **단일 공식 위반 금지.** "옵션 A/B/C" 형태 답변은 aiprofit이 수정 요청함. **1순위 추천 + fallback 1개**로 압축.
- **"본인 인증 = verification" 함정.** sandbox 격차는 architecturally absolute. 본인 sandbox에서 파일 봤어도 다른 봇 read 불가 → **paste 의무**.
- **Gate 1 본문 paste 거부 시 결정 보류 유지.** summary-only commit = single-source-of-truth = 보류.
- **rubber-stamp 금지.** PM이 plannerbot 답변을 그대로 합의안으로 만들지 마라. **반박/보완 1개 이상** 추가.
- **메시지 길이 관리.** Discord 2000자 한도. 매트릭스는 간결하게, narrative는 단축.
- **승인 받기 전 파일 생성 금지.** DESIGN.md / Linear / Kanban은 **aiprofit 명시 승인 후**에만 생성. 합의 도출 ≠ 승인.
- **3 기획안 × 3 차원 매트릭스는 종합 점수화까지.** 단순 나열 ❌ → 🟢=3 / 🟡=2 / 🔴=1 점수 매트릭스 + deep tier 우선순위로 압축 제공 필수 (aiprofit "option 나열 금지").

---

## Post-Meeting Workflow (순서대로)

### Step 0 — Verification (aiprofit 요청 시 또는 회의 종료 시)

aiprofit이 "X 충분히 토론함?" / "discussion enough?" 형태로 verification 요청할 수 있음. 회의록의 Open Questions 섹션을 기준으로 정직하게 답변:

```
## 🔍 포트폴리오/주제 토론 충분성 검증

**답변: 부분 충분 / 충분 / 부족**

### ✅ 충분히 합의된 영역
- 항목 1
- 항목 2

### ⚠️ 부분 합의 / 추가 deep dive 필요
1. 영역 1 - 현재 상태, 추가 토론 필요
2. 영역 2 - 현재 상태, 추가 토론 필요

### ❌ 미논의
- 영역 1
- 영역 2

### 📋 제안: 추가 회의 N개
| 회의 | 시점 | 내용 |
|---|---|---|
```

**왜 정직하게 답변해야 하는가**:
- aiprofit은 "가치 검증 선행" 철학 — 실행 전 진짜 필요성 평가 중시
- rubber-stamp 답변 (전부 합의) → 다음 회의에서 갭 발견 시 신뢰 하락
- 미합의 명시 → 다음 회의 agenda로 자연스럽게 흡수

### Step 1 — 회의록 작성
1. `INDEX.md` 확인 → 날짜 중복 방지
2. `YYYY/MM/DD/` 디렉토리 생성
3. `README.md` (하루 인덱스) 작성
4. `HHMM_topic-slug/` 폴더 생성
5. `agenda.md` / `discussion.md` / `decisions.md` / `next_steps.md` 4-파일 작성
6. 기술 결정 포함 시 `DESIGN.md` **반드시** 작성
7. `decisions.md`의 "실행 순서" 섹션에 Phase 0 (문서화) 상태를 🟢로 표시

### Step 2 — Git Push
```bash
cd /tmp/meeting-notes  # or local clone
git add -A
git commit -m "Restructure MM/DD: 회의 N개를 HHMM_topic-slug 폴더로 분리"
git push origin main
```

**Pitfall**: 기존 단일 파일 (`2026-06-29-1230.md`) → 새 폴더 구조로 옮길 때 `git rm` 잊지 말 것. 둘 다 있으면 충돌.

### Step 3 — Linear 업데이트
1. 오래된/취소된 태스크 → `Canceled` (update-status 이용)
2. 새 태스크 → `create-issue` (P1~P4, description에 회의 맥락 포함)
3. 유지 태스크 → 필요시 priority 조정
4. 신규 태스크는 **Todo** 상태로 (바로 In Progress 금지 — 문서 먼저)

**API key 위치 (중요)**: `~/.hermes/.env`에 `LINEAR_API_KEY` 존재. env에 export 안 됨 → Python에서 `os.environ` 동적 주입 필요. **GitHub `~/.hermes/mcp-tokens/linear.client.json`은 OAuth client_id만 있고 API token 아님**. 참고: `references/linear-graphql-patterns.md`

### Step 4 — Kanban 업데이트
1. 오래된 태스크 → `hermes kanban archive <task_id>`
2. 신규 태스크 생성 → `hermes kanban create "제목" --priority N --body "..."`
3. assign 필요시 `hermes kanban assign <task_id> --assignee 채니봇`

**Kanban DB 직접 접근 패턴**: `~/.hermes/kanban.db` (SQLite, schema: tasks 29 cols, task_links, task_comments, task_events, task_runs). web API가 401 막힐 때 sqlite3로 직접 처리 가능. 참고: `references/kanban-direct-access.md`

**Kanban-Linear mirror 동기화** (aiprofit 워크플로우): Linear 이슈 처리 시 같은 task_id로 Kanban mirror 태스크 생성 + `~/.hermes/data/kanban_linear_mapping.json`에 매핑 기록. 참고: `references/kanban-linear-mirror.md`

### Step 5 — 결과 보고
Discord에 정리된 요약 전송:
```
## ✅ 전체 정리 완료

### 📁 GitHub
mybotagent/meeting-notes YYYY/MM/DD/HHMM_topic-slug/
- agenda.md / discussion.md / decisions.md / next_steps.md
- DESIGN.md (설계 문서)

### 📋 Linear 상태
| 태스크 | 변경 |
|--------|------|
| SHO-XX | 상태변경 |

### 📋 Kanban 상태
| 태스크 | 변경 |
|--------|------|

### 현재 Active 태스크 (우선순위 순)
| P | 태스크 | Linear | 상태 |
|---|--------|--------|------|
| P1 | ... | SHO-XX | Todo |
```

## Critical Rules (🔥 절대 위반 금지)

1. **문서 먼저, 구현 나중.** Phase 0(문서화) 완료 전에는 절대 구현 코드를 작성하지 않음. DESIGN.md가 승인된 후에만 Phase 1+
2. **회의록은 반드시 GitHub에 push.** 로컬에만 두지 않음.
3. **Linear와 Kanban을 반드시 동기화.** 한쪽만 업데이트하고 다른 쪽을 놓치는 경우 금지.
4. **취소된 태스크는 Canceled/Archived 처리.** 방치 금지.
5. **기술 결정은 반드시 DESIGN.md로 문서화.** 결정만 하고 기록하지 않는 경우 금지.
6. **폴더명 시간 prefix 필수.** `HHMM_topic-slug` 형식. 시간 없으면 aiprofit이 "이 회의가 언제였지?"라며 다시 정정 요청함.
7. **🚪 Execution Gate (aiprofit 2026-07-02 요구 — convergence theater 방지)** — 회의록 4-파일 작성 + push 후, **디자인만으로 끝내지 마라.** 합의한 implementation을 같은 세션 안에서 최소 1개라도 validate 실행 (5-10분). 정직한 negative result도 성공. "우리는 분석·합의 머신이지, 실행 머신이 아님" (aiprofit 직설) → 디자인 단계에서 멈추면 회의 실패. See `execution-discipline` skill and templates/validate-30min-checklist.md.

## Live Incremental Save Protocol (NEW 2026-06-29) ⭐

> **왜 이 방식이 필수인가**:
> - 회의를 진행하면서 결정/논의가 누락되면 회고 시 복원 불가
> - Phase가 길어지면 (예: 30분+) 끝나고 한 번에 쓰면 가독성 ↓ + 누락 ↑
> - **GitHub에 중간 저장 → 회의 도중 외부 검증 가능** (aiprofit이 다른 곳에서 봐도 즉시 인덱싱)
> - 망각 방지가 1순위 — 회의 끝나고 4파일 만드는 건 비효율

### 📦 5단계 중간 저장 (Step 0~4)

#### Step 0 — 회의 시작 (최초 안건 입력 시)

```bash
# 1. 폴더 + 빈 4파일 즉시 생성
MEETING_DIR="/home/ubuntu/meeting-notes/YYYY/MM/DD/HHMM_topic-slug"
mkdir -p "$MEETING_DIR"
cat > "$MEETING_DIR/agenda.md" <<EOF
---
tags: ["meeting-notes", "..."]
date: YYYY-MM-DD
time: "HH:MM-HH:MM KST"
participants: [aiprofit, 채니봇, plannerbot]
title: {회의 제목}
status: in-progress
---
# {회의 제목}
EOF

# 4개 빈 파일 생성 (구조만, 내용은 phase 끝마다 채움)
for f in discussion decisions next_steps; do
  touch "$MEETING_DIR/$f.md"
done

# 2. INDEX.md에 등록 (in-progress marker)
echo "→ README.md 1줄 추가 (in-progress 회의로 표시)"
```

**critical**: 회의 시작 1분 이내에 폴더 + 빈 4파일을 만들어야 함. 안건이 들어오는 즉시.

#### Step 1 — 각 Phase 끝날 때마다

```bash
# Discussion.md Phase N 추가
echo "## Phase N: {제목} ({시간})" >> "$MEETING_DIR/discussion.md"
echo "..." >> "$MEETING_DIR/discussion.md"

# 결정 났으면 decisions.md에도
echo "## Phase N 결정" >> "$MEETING_DIR/decisions.md"
echo "- ..." >> "$MEETING_DIR/decisions.md"
```

#### Step 2 — 모든 Phase 끝날 때 (다음 단계 합의 시)

```bash
# next_steps.md 작성
cat > "$MEETING_DIR/next_steps.md" <<EOF
# 다음 단계
- ...
EOF
```

#### Step 3 — 회의 종료 시 (모든 봇 sign-off)

```bash
# status: done
sed -i 's/status: in-progress/status: done/' "$MEETING_DIR/agenda.md"

# git commit + push (자동으로 일관성 유지)
cd /home/ubuntu/meeting-notes
git add -A
git commit -m "Meeting HHMM_topic-slug: {한줄 요약}"
git push origin main

# 하루 README.md에도 등록 (이미 인덱스 위라면 commit 안 함)
```

#### Step 4 — 회의 도중 예상 못 한 인터럽트 (Discord 끊김 등)

**현재까지 저장된 내용 모두 GitHub에 push**:
```bash
git add -A && git commit -m "Meeting HHMM_topic-slug: in-progress snapshot" && git push
```

이렇게 하면 회의가 중간에 끊겨도 외부 백업 보장.

### ⚙️ 자동화 헬퍼 (필수)

**모든 회의에서 사용 — aiprofit이 망각 방지를 위해 강제 (2026-06-29)**.

스크립트 위치: `~/.hermes/scripts/meeting_incremental_save.sh`

```bash
# 기본 — 오늘 회의 auto-detect (가장 최근 YYYY/MM/DD)
~/.hermes/scripts/meeting_incremental_save.sh 0900_wiki-knowledge-search-onboarding

# 명시적 날짜 (auto-detect이 다른 날짜 잡았을 때 강제 지정)
~/.hermes/scripts/meeting_incremental_save.sh 2026-06-29 0900_wiki-knowledge-search-onboarding

# 커스텀 commit 메시지 (긴급 push 또는 특별 메모)
~/.hermes/scripts/meeting_incremental_save.sh 2026-06-29 1200_topic-slug "Phase 3 결정 — Neo4j 확정, push 긴급"
```

**출력 예시** (실제 2026-06-29):
```
📦 Meeting incremental save
   폴더: /home/ubuntu/meeting-notes/2026/06/29/0900_wiki-knowledge-search-onboarding
   phases: 1 / decisions: 0 / next_steps: yes / status: unknown
   msg: Meeting 0900_wiki-knowledge-search-onboarding: incremental snapshot (phases=1, decisions=0, next_steps=yes, status=unknown)

[main bb52a0b] Meeting 0900_wiki-knowledge-search-onboarding: incremental snapshot (...)
 1 file changed, 1 insertion(+)

✅ commit 완료. push 진행...
To https://github.com/mybotagent/meeting-notes.git
   4f01a9d..bb52a0b  main -> main

✅ push 완료. 회의 진행 안전.
```

**스크립트 동작**:
- 회의 폴더 안의 `phases=`, `decisions=`, `next_steps=`, `status=` 자동 카운트
- 변경 없으면 push 스킵 (안전)
- 변경 있으면 `git add -A` → commit → push 자동
- 빈 파일 / 0 match 상태에서도 안전
- 0개 회의 폴더일 때 사용 가능한 슬러그 목록 표시

**aiprofit 워크플로우에 통합된 사용 시점**:
- 회의 시작 후 첫 phase 끝 → 1차 save
- 각 phase 끝 → save
- 다음 단계 합의 → save
- 회의 종료 시 `sed -i 's/in-progress/done/' agenda.md` → 최종 save (status done 마킹)

스크립트 자체는 70줄 내외 bash — `references/shell-script-bug-fixes.md`에 작성 중 발견한 4개 함정 기록.

### 📋 Incremental Save 트리거 (aiprofit이 신경 쓸 시점)

| 트리거 | 액션 |
|--------|------|
| 회의 시작 / 안건 입력 | Step 0 — 폴더 + 빈 4파일 |
| Phase 1 끝 | Step 1 — discussion.md 갱신 |
| Phase 2 끝 | Step 1 — discussion.md 갱신 + decisions.md 갱신 |
| ... | 반복 |
| 다음 단계 합의 | Step 2 — next_steps.md |
| 회의 종료 | Step 3 — status: done + commit + push |
| 인터럽트 / 끊김 | Step 4 — 강제 push |

### 🔥 핵심 원칙

1. **회의 시작 즉시 폴더 만들어**. 안건 들어오는 순간부터 문서화 시작.
2. **각 Phase 끝마다 commit**. 메모리가 아닌 git log로 추적.
3. **짧아도 commit**. 5KB도 commit. 외부 백업이 우선.
4. **인터럽트 시 push**. 회의 도중이면 지금까지 저장분이라도 push.
5. **회고 시 verification**: 회의 끝나면 aiprofit이 "충분히 토론?" 물어봄. 정직하게 답변.

### ❌ Forbidden (절대 금지)

- 회의 끝나고 한 번에 4파일 일괄 작성 (incremental 위반)
- incremental 안 하고 회의 내용 손실 (가장 흔한 fail)
- commit 안 한 채로 회의 진행 (외부 백업 없음)
- status: done 전에 회의 종료 (명시적 sign-off 없이 끝내기)

## Pitfalls

- **Git push를 잊지 마라.** 회의록이 로컬에만 있으면 의미 없음. push까지가 완료.
- **INDEX.md 업데이트를 잊지 마라.** meeting-notes/INDEX.md에 새 회의록 항목 추가 필요.
- **Linear 상태 잘못 설정 금지.** 신규 태스크는 Todo, 취소는 Canceled (Done이 아님).
- **Kanban 태스크만 만들고 Linear 생략 금지.** 항상 쌍으로 업데이트.
- **DESIGN.md 없이 구현 시작 금지.** aiprofit이 명시적으로 요구한 패턴. "documentation first" 설계 원칙.
- **한글/영문 혼용 금지.** 회의록은 aiprofit이 한국어 사용자이므로 **전체 한국어로 작성.** 단, 기술 용어(Neo4j, GraphRAG 등)는 원어 유지.
- **Topic 분리 누락 금지.** 같은 날짜라도 다른 회시면 `HHMM_topic-slug/` 폴더로. **시간 prefix 없는 폴더명 절대 금지**.
- **Waiting mode에서 @mention 금지.** aiprofit 신호 대기 / 다른 봇 답변 대기 / 승인 대기 시 절대 @mention. 짧은 상태 보고 1줄 + 대기 선언으로 끝낼 것.
- **Verification 요청 시 rubber-stamp 금지.** "전부 합의" 식 답변 금지. Open Questions 섹션을 정직하게 채워서 정직한 답변. 미합의 영역은 다음 회의 agenda로.
- **ROI 정직 평가 필수.** 사용자가 "이게 진짜 가치 있나?" 물으면 시스템 코드 분석해서 진짜 토큰/시간 영향 정량적으로 답할 것. rubber-stamp "좋다 좋다" 답변 금지. 참고: `references/roi-honest-evaluation.md`
- **4-파일 구조 누락 금지.** `agenda.md` / `discussion.md` / `decisions.md` / `next_steps.md` 4개 모두 작성. `next_steps.md` 빠뜨리지 마라 (aiprofit 명시 요구).
- **incremental_save.sh 4대 함정** (작성 중 2026-06-29 발견 — `references/shell-script-bug-fixes.md` 참조):
  1. `set -e` + `grep -c`의 exit 1 (no-match) → 스크립트 조기 종료. 해결: `set +e` 또는 `|| true`로 명시적 처리.
  2. `$(grep -c ... || echo 0)` 패턴 → grep가 0만 출력 + echo 0도 출력 = "0\n0" multi-line. 해결: `[ -s file ]` 가드 + `${VAR:-0}`.
  3. `find ... -printf '%T@ %p\n'` 대신 그냥 `-type d` → TS/DIR 파싱 실패. 해결: `-printf` 명시.
  4. `[ "$TS" -gt "$LATEST_TS" ]` 정수 비교 + float TS → "integer expression expected" 에러. 해결: `awk "BEGIN {exit !($TS > $LATEST_TS)}"`.
  5. `find ... -path '*/.git' -prune` → `(.git` 매칭이 일부 shell에서 작동 안 함. 해결: `case "$DIR" in *".git"*) continue ;; esac`.
  6. .git/objects/ 안의 pack 파일 ts가 실제 회의 폴더 ts보다 클 수 있음 → "오늘 폴더" 잘못 선택. 해결: `case`로 .git 스킵 + REL regex `^[0-9]{4}/[0-9]{2}/[0-9]{2}$`으로 확실히 YYYY/MM/DD만 매치.
- **🚪 Convergence Theater (분석·합의 머신 위험, 2026-07-02 aiprofit 직설)** — 회의 안건이 합의·분석으로만 끝나는 패턴 (디자인·아키텍처·워크플로우 회의에서 가장 흔함). 4-파일 push 후 implementation 단계로 안 넘어감. aiprofit 명시 비판: "우리는 분석·합의 머신이지, 실행 머신이 아님". **해결**: 회의 종료 시 무조건 1개라도 작은 validate 실행 (5-10분) — query.py 1회, shell script 1회, git push 1회 확인. 결과 부정이어도 **negative result로 영속화**. 그게 진짜 회의 성공. See `execution-discipline` skill and Critical Rule 7.
