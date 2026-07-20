---
name: daily-task-suggestion
description: "매일 07:00 KST 오늘의 할 일 제안 — kanban 태스크 생성, GitHub Issue 연동. 주식/트레이딩 관련 제안 금지"
version: 1.2.0
author: aiprofit
platforms: [linux]
metadata:
  hermes:
    tags: [daily, task, suggestion, kanban, planning]
    related_skills: [kanban-orchestrator]
---

# Daily Task Suggestion

> **실행:** 매일 07:00 KST, cron + kanban 기반
> **목적:** 회사 운영/Wiki/프로젝트 관련 오늘의 할 일을 kanban task로 제안
> **⚠️ 주식/트레이딩/포트폴리오 관련 제안 절대 금지**

## 🚫 제외 항목 (절대 제안 금지)
- 주식 분석, PER/PBR, 밸류에이션, 적정주가
- 포트폴리오 리밸런싱, 매수/매도
- 트레이딩 파이프라인, LangGraph 관련
- 매크로/경제 리포트
- Fear & Greed, Finviz 스크리너
- daily-survey, 수면 설문

이 모든 것은 별도 cron pipeline에서 처리됨.

## ✅ 포함 항목
- Wiki 페이지 신규/업데이트 제안
- SOP 문서 정리
- Kanban backlog 정리
- 프로젝트/코드 리팩토링
- 문서화, 가이드 작성
- 인프라 점검
- 기타 운영/개선 작업

## ⚠️ 중요: Cron 모드 vs 대화형 모드

이 스킬은 보통 07:00 KST cron job으로 실행됨. Cron 모드에서는:
- **사용자 부재** — 질문/확인 불가. 모든 결정은 직접 내려야 함.
- **최종 응답이 자동 전송** — send_message() 호출 금지. 리포트 내용을 그대로 최종 응답으로 출력.
- **반복 cron job** — 기본적으로 매일 실행. Idempotency key를 사용해 중복 태스크 방지 고려.
- **SILENT 처리** — 진짜 할 일이 없으면 "[SILENT]"만 출력 (전송 억제). 내용과 함께 사용 금지.

## 실행 흐름

### 1. 맥락 수집

다음 정보를 읽어서 오늘의 컨텍스트 파악:

#### 1a. 최근 Wiki 변경사항
- `logs/index.md` (wiki 루트의 logs/index.md, `wiki/logs/index.md` 아님)
- 또는 `logs/2026/YYYY-MM-*.md` 파일들을 읽어 최근 변경 파악
- wiki 루트의 `README.md` 도 같이 확인 (현재 INDEX 역할)

#### 1b. Kanban 현황
- `hermes kanban list --json` → 현재 열린 태스크 확인
- 진행 중이거나 블록된 태스크 파악
- **중복 태스크 탐지**: 동일한 title을 가진 todo/ready 태스크가 여러 개인지 확인 (예: 'Wiki lint 13건' 13개 중복). 중복 발견 시 backlog cleanup 태스크 제안.
- **스테일 auto 태스크 탐지**: daily-repo-orchestrator가 생성한 P0 ready 태스크 중 7일 이상 지난 것이 쌓여 있는지 확인. 대부분 false positive이므로 일괄 archive 제안.

#### 1c. Git 현황
- `git log --oneline -10` in wiki 디렉토리 → 최근 활동

### 2. 태스크 제안 선정

2~4개의 구체적인 태스크를 선정. 주식/트레이딩 제외 절대 준수.

### 3. Kanban 태스크 생성 (실제 CLI 명령어)

> **⚠️ Pitfall: `--assignee`를 알 수 없는 이름으로 설정하면 exit code 2와 함께 empty output이 반환됨. 에러 메시지도 없어 디버깅 어려움. 생성 시 assignee를 지정하지 말고, unassigned 상태로 생성할 것.**
>
> **⚠️ Cron 모드 파이프 차단: `| jq`, `| python3 -c` 등 파이프-to-인터프리터 패턴은 cron 모드에서 Tirith 보안 검사에 차단됨. 해결책: JSON을 임시 파일로 저장한 뒤 `read_file`로 읽거나, `python3 -c`로 미리 저장된 파일을 읽는 방식 사용.**

```bash
# 1. 부모 태스크 생성 → 임시 파일로 ID 캡처 (cron-safe: | jq 대신 임시 파일 사용)
hermes kanban create "daily-suggestions-$(date +%Y%m%d)" \
  --body "Daily task suggestions. 하위 태스크 참조." \
  --priority 1 \
  --idempotency-key "daily-suggestions-$(date +%Y%m%d)" \
  --json > /tmp/daily_suggest_parent.json
# ID 확인: read_file("/tmp/daily_suggest_parent.json") 후 .id 추출

# 2. 각 자식 태스크 생성 (--parent 플래그: 단수, 반복 가능)
hermes kanban create "Wiki README 업데이트: ..." \
  --priority 1 \
  --parent "$PARENT_ID" \
  --body "구체적인 실행 방법과 배경 설명 포함"

hermes kanban create "Log index 업데이트: ..." \
  --priority 2 \
  --parent "$PARENT_ID" \
  --body "..."
```

**중요:**
- `--parent` (단수) — 반복해서 여러 parent 지정 가능. `--parents` 아님.
- `--json` 플래그를 사용해 출력 캡처 (parent task ID를 얻거나 결과 확인)
- `--idempotency-key`로 중복 생성 방지 가능 (cron 재실행 대비)
- 자식 태스크는 생성 시 `todo` → parent 완료 시 `ready`로 자동 승격됨

### 4. 완료 처리 및 리포트 (Cron → 자동 전송)

```bash
hermes kanban complete "$PARENT_ID" \
  --summary "오늘의 추천 태스크 N개 생성" \
  --metadata '{"task_count":N,"tasks":["title1","title2","title3"],"date":"YYYY-MM-DD"}'
```

**주의:**
- `--summary`와 `--metadata`는 parent complete에만 사용. 자식 태스크는 complete하지 않음 (dispatcher가 처리).
- `--json` 플래그 없음 (exit code 0으로 성공 확인)
- Cron 모드: 최종 응답이 리포트 내용. 아래 형식 그대로 출력하면 자동 전송됨.

### 5. 리포트 형식 (최종 응답)

cron의 최종 응답으로 아래 형식을 그대로 출력:
```
📋 오늘의 추천 태스크 (07:00)

1. [태스크 제목] (우선순위)  ← kanban 태스크
2. [태스크 제목] (우선순위)
3. [태스크 제목] (우선순위)

🔗 kanban list로 확인: hermes kanban list
```

## ⚠️ 알려진 Pitfalls

| 문제 | 원인 | 해결 |
|:-----|:-----|:-----|
| `--assignee default` → exit 2 + empty output | 해당 assignee 미존재 | assignee 지정 없이 생성 (unassigned) |
| `--parents` 옵션 없음 | CLI는 `--parent` (단수, 반복가능) | `--parent` 플래그 반복 사용 |
| kanban create 실패 시 stderr 없음 | CLI 버그 특성 | `--json` 출력 비거나 exit 2면 assignee 의심 |
| 자식 태스크가 `ready` 상태로 보임 | parent 완료 시 `todo→ready` 승격 | 정상 동작 |
| `| jq` / `| python3 -c` 파이프 차단 (cron 모드) | Tirith 보안 검사가 파이프-to-인터프리터 차단 | JSON을 임시 파일로 저장 후 read_file()로 읽기 |
| README.md가 INDEX.md 역할 | AGENTS.md는 index.md 요구하나 실제로는 README.md가 catalog | README.md 확인 후 index.md 생성 고려
