---
tags: [meeting-notes, restructure, hhmm-prefix, time-prefix, workflow]
---

# Restructure Existing Meeting Notes — HHMM_topic-slug 변환

> aiprofit이 2026-06-29에 "시간대-제목 형식으로" 명시 요구. 기존 단일 파일 (`2026-06-29-1230.md`) → 새 폴더 구조 (`2026/06/29/1230_topic-slug/agenda.md ...`)로 변환하는 표준 절차.

## When to Use

- 사용자가 "회의 GitHub에 올려" + "시간대-제목 형식으로" 요청
- 기존 회의록을 새 형식으로 마이그레이션 (06/28, 06/27 등 과거 회의)
- 한 날 여러 회의를 4-파일 표준으로 분리

## Procedure

### 1단계 — 회의 식별

기존 단일 파일 또는 topic 폴더에서 회의 단위 식별:
- `agenda.md` (있다면) — 원래 안건 + 논의 흐름에서 시간/주제 추출
- `discussion.md` (있다면) — Phase 1/2/3 분리 = 회의 N개 가능성
- git log `git log --format="%h %ai %s" -- YYYY/MM/DD/` — 첫 commit 시각 = 첫 회의 시작 추정
- README.md에 시간 정보 명시된 경우 활용

### 2단계 — 회의 분리

한 날이 5-15개 회의를 포함할 수 있음. 분리 기준:

| 신호 | 분리 단위 |
|------|----------|
| Phase 1, 2, 3 섹션 | 각 Phase = 1 회의 |
| 시간 정보 있음 ("00:10-00:30") | 해당 시간대 = 1 회의 |
| 안건이 명확히 다름 | 안건 단위 = 1 회의 |
| Linear 이슈 SHO-XX | 해당 이슈 = 1 회의 |

### 3단계 — 폴더명 결정

`HHMM_topic-slug` 형식:
- 시간 prefix: KST 24시간제 4자리
- 주제 slug: kebab-case, 핵심 키워드
- 예시: `0900_wiki-knowledge-search-onboarding`, `1930_linear-sho22-kanban-sync`

### 4단계 — 4-파일 작성

각 회의 폴더에 `agenda.md` / `discussion.md` / `decisions.md` / `next_steps.md` 4개 파일 작성.

**agenda.md 형식**:
```markdown
# 안건

원래 안건: [초기 안건]

## 실제 논의 흐름
1. ...
2. ...
```

**discussion.md 형식**:
```markdown
# 논의 내용

## Phase 1: [첫 번째 주제]
...

## Phase 2: [두 번째 주제 - 방향 전환 등]
...
```

**decisions.md 형식**:
```markdown
# 결정 사항

## ✅ 합의된 결정

### 1. 결정 제목
- **내용**: ...
- **근거**: ...
- **영향**: ...
```

**next_steps.md 형식**:
```markdown
# 다음 단계

- 다음 회의 시간_주제
- Linear SHO-XX
- Kanban 태스크 ID
```

### 5단계 — 하루 인덱스 README

`YYYY/MM/DD/README.md`에 그날 모든 회의 시간순 인덱스:

```markdown
# 2026-06-29 (월) 회의록

> **총 N개 회의** — 시간순으로 정렬

## 폴더 구조
`날짜/시간_토론주제/여러파일` 형식

```
2026/06/29/
├── README.md
├── HHMM_topic-1/
├── HHMM_topic-2/
└── ...
```

## 회의 목록
| 시작 | 제목 | 폴더 |
|------|------|------|
| 08:55 | Wiki 온보딩 | `0855_wiki-knowledge-search-onboarding/` |
| 12:30 | Phase 5 | `1230_phase5-operations-automation/` |

## 회의 의존성
```
HHMM-1
  └── HHMM-2
        └── HHMM-3
```

## 한 줄 요약
[3줄 이내]
```

### 6단계 — Git 작업

```bash
cd /home/ubuntu/meeting-notes

# 1. 기존 파일/폴더 정리
git rm YYYY/MM/DD/agenda.md 2>/dev/null
git rm YYYY/MM/DD/discussion.md 2>/dev/null
git rm YYYY/MM/DD/decisions.md 2>/dev/null
git rm YYYY/MM/DD/2026-MM-DD-HHMM.md 2>/dev/null

# 2. 새 폴더 파일들 추가
git add YYYY/MM/DD/

# 3. 커밋
git config user.email "hermes@mybotagent.com"
git config user.name "Hermes Agent"
git commit -m "Restructure MM/DD: N개 회의를 HHMM_topic-slug 폴더로 분리"

# 4. Push
git push origin main
```

## Pitfalls

- **시간 prefix 빠뜨리지 마라.** `HHMM_topic-slug` 형식 강제. `wiki-knowledge-search-onboarding/` 같은 prefix 없는 폴더는 절대 금지.
- **기존 단일 파일을 git rm 안 하면 두 가지 형식 공존** → git history에 남고 새 구조와 충돌. `git rm` 먼저.
- **4-파일 중 next_steps 빠뜨리기 쉬움.** `agenda` / `discussion` / `decisions` 3개만 만들고 끝내지 말고, `next_steps.md` 반드시 추가 (aiprofit 명시 요구).
- **README.md를 회의 폴더 안에 또 만들지 마라.** 하루 단위 README는 `YYYY/MM/DD/README.md` 한 곳에만. 회의 폴더 내 README는 의존성이 매우 복잡한 경우만.
- **시간이 불명확한 회의는?** git log 첫 commit 시각 + Phase 단위로 best estimate. 모호하면 "09:00 (추정)" 같이 명시.
- **24:00 넘기는 회의는?** 다음 날 날짜 폴더에 저장하되 시간 표기는 실제 시작 시간 (예: 23:57 시작 → `2357_topic/` 폴더는 06/28에).
- **재구성 후 새 회의 추가 시 동일 형식 유지.** "이미 12개 있는데 1개 더 추가"도 `HHMM_topic-slug/` 형식으로.

## Real Example: 2026-06-29

### Before (5 files):
```
2026/06/29/
├── agenda.md
├── decisions.md
├── discussion.md
├── DESIGN.md
├── PLAN.md
├── 2026-06-29-1230.md
├── 2026-06-29-1300.md
└── 2026-06-29-1315.md
```

### After (12 folders + 4 files each):
```
2026/06/29/
├── README.md
├── 0900_wiki-knowledge-search-onboarding/
│   ├── agenda.md
│   ├── discussion.md
│   ├── decisions.md
│   └── next_steps.md
├── 0930_wiki-knowledge-search-design/
├── 1100_neo4j-installation/
├── 1200_skill-plugin-v1/
├── 1230_phase5-operations-automation/
├── 1300_phase6-universal-kg/
├── 1315_full-reindex-12-repos/
├── 1400_ir-metrics-evaluation/
├── 1845_disk-cleanup-wiki-scalability/
├── 1930_linear-sho22-kanban-sync/
├── 2020_sho24-roi-ir-guide-push/
└── 2055_meeting-file-convention-update/
```

48개 파일 (12 × 4) + 1 인덱스 = 49개 파일.

## Migration Order

1. **06/29 (가장 최근, 12개 회의)** — 첫 마이그레이션
2. **06/28 (3개 회의)** — 두 번째
3. 다른 일자 — 사용자 추가 요청 시 진행

**왜 06/29 먼저?** 가장 많은 회의 + 가장 최근 = "기억 생생" 상태. 패턴 확립 후 06/28 적용.
