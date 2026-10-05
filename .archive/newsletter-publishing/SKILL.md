---
name: newsletter-publishing
description: "Daily/recurring newsletter publishing pipeline — 매일 1호 push하는 워크플로우 (단일 GitHub 레포 + Karpathy 5-layer + cadence/thesis 누적). aiprofit가 매일 1회 publish하는 뉴스레터(솔로프리너/기획/테크 트렌드)에 사용. 기존 wiki-save와 다름 — wiki-save는 단발 텍스트를 카테고리별 레포로 라우팅, 이 스킬은 '한 개 주제 = 한 호 = 한 commit' 반복 cadence에 특화."
version: 0.1.0
author: aiprofit
platforms: [linux, macos]
metadata:
  hermes:
    tags: [newsletter, publishing, cadence, solopreneur, daily-issue, github, wiki]
    related_skills: [wiki-save, wiki-architecture, meeting-documentation]
---

# Newsletter Publishing — 매일 1호 Push 워크플로우 (v0.1)

> aiprofit가 매일 1호 발행하는 뉴스레터 워크플로우. 단일 GitHub 레포에 Karpathy 5-layer 구조로 누적.
> 기존 `wiki-save`와 차이: wiki-save는 "텍스트 입력 → 카테고리 매칭 → 단발 저장". 이 스킬은 "**반복 cadence + 단일 영구 레포 + 이슈 단위 commit + 누적 thesis**".

## 🎯 트리거 패턴

사용자가 다음 중 하나를 말할 때 발동:
1. "매일 뉴스레터 1호 발행" / "오늘 호 push"
2. "newsletter-wiki에 새 호 추가"
3. "솔로프리너/기획/테크 트렌드 리서치 → 새 레포"
4. 특정 카테고리(techno-trends, strategy, solopreneur)로 본문 작성 + push

## 📐 단일 공식 (aiprofit 원칙 준수)

```
매일 1호 = 1 commit = 1 issue page = 1 raw 발췌 묶음
```

예외/조건문 없음. 5단계 단일 공식만 사용.

## 🏗️ 레포 구조 (신설 시)

```
newsletter-wiki/                 ← 단일 영구 레포 (private)
├── AGENTS.md                    ← 도메인 특화 운영 규칙
├── SCHEMA.md                    ← 태그/타입/lint 규칙
├── index.md                     ← 카탈로그 (1호 = 1줄)
│
├── newsletter/                  ← 본문 (이슈 페이지)
│   ├── 01-2026/                 ← 연도별
│   │   ├── techno-trends/       ← 카테고리
│   │   │   └── 2026-07-01-coding-agent-ecosystem.md
│   │   ├── strategy/
│   │   └── solopreneur/
│   ├── cadence.md               ← 발행 캘린더, 다음 호 후보 3개
│   └── thesis-stack.md          ← 누적 운영 원칙 (단일공식 누적)
│
├── raw/01-newsletter/YYYY-MM/   ← 불변 발췌 (URL + 본문)
│
└── logs/YYYY/                   ← YYYY-MM-DD-HHMM.md 발행 로그
```

**디렉토리 카테고리** (사용자별 다를 수 있으나 기본 3개):
- `techno-trends` — 기술 동향
- `strategy` — 기획/Product
- `solopreneur` — 1인 회사 운영

## 🚀 신규 레포 셋업 (1회성, 세션당 1번)

### Step 1: gh 토큰 활성화 (이미 세팅돼 있으면 생략)
```bash
TOKEN=$(head -1 ~/.git-credentials | sed 's|https://||;s|@github.com.*||' | cut -d: -f2-)
export GH_TOKEN="$TOKEN" GH_HOST=github.com
gh auth status  # → "Logged in to github.com account mybotagent" 확인
```

> **Pitfall**: `gh auth login` 직접 호출 시 인터랙티브 모드 필요 → `~/.git-credentials`에서 토큰 추출 + `GH_TOKEN` 환경변수 방식이 비대화형. 평소엔 gh가 credential helper로 자동 처리하는데 가끔 미인증 상태일 때만 위 export.

### Step 2: 레포 생성
```bash
gh repo create mybotagent/newsletter-wiki \
  --private \
  --description 'Solopreneur Daily Newsletter Wiki — techno-trends/strategy/solopreneur (YYYY-MM~)' \
  --add-readme
# → https://github.com/mybotagent/newsletter-wiki
```

### Step 3: 클론 + 디렉토리 + 베이스 파일 작성 (병렬 실행)

```bash
cd /tmp && git clone https://github.com/mybotagent/newsletter-wiki.git
cd newsletter-wiki
git config user.email 'aiprofit@hermes.local'
git config user.name 'aiprofit'
mkdir -p raw/01-newsletter/2026-07 \
         newsletter/01-2026/techno-trends \
         newsletter/01-2026/strategy \
         newsletter/01-2026/solopreneur \
         logs/2026
```

5개 베이스 파일 동시 작성 (write_file 병렬):
- `AGENTS.md` — 도메인 규칙 (5-layer Karpathy)
- `SCHEMA.md` — 태그/타입/lint
- `index.md` — 카탈로그 placeholder
- `newsletter/cadence.md` — 발행 캘린더 + 다음 호 후보 3개
- `newsletter/thesis-stack.md` — 누적 원칙

### Step 4: 1차 commit
```bash
git add -A && git commit -m 'newsletter-wiki initial: 5-layer structure, AGENTS/SCHEMA/index/cadence/thesis-stack (issue 001 placeholder)'
```

> **push는 본문까지 더한 후 한 번에!** 본문이 없는 placeholder commit은 리뷰/공유 시 noise. 1차 commit은 local에 두고 push는 마지막.

## ✍️ 본문 작성 (매 호 반복)

### Step 1: 주제 확정 (사용자 명시 또는 cadence.md 후보에서)
- 카테고리 선택: techno-trends / strategy / solopreneur
- 제목 + URL: `newsletter/01-YYYY/<category>/YYYY-MM-DD-<slug>.md`

### Step 2: 본문 구조 (단일 공식)

```markdown
---
type: issue
issue_no: N
date: YYYY-MM-DD
category: techno-trends | strategy | solopreneur
title: "한 줄 요약 (한국어 + 영문 병기)"
tags: [카테고리, 엔터티, ...]
entities: [claude-code, codex, ...]
confidence: high | medium | low
related: [newsletter/cadence.md]
---

# Issue N — 제목

## Executive Summary (5개 불릿, 각 1줄 + 출처 URL)
## 1. [섹션]
## 2. [섹션]
## 3. 솔로프리너 시사점 (3~5 인사이트)
## 4. 매크로/원인 분석
## 5. 출처 통합 목록
## 6. 다음 호 hook
```

### Step 3: raw 발췌 저장 (본문보다 먼저)
- 각 source = 1개 외부 URL 발췌
- 형식: `raw/01-newsletter/YYYY-MM/<medium>-<slug>.md`
- frontmatter: `source_url, ingested, type, medium, date_published, tags`
- ⚠️ raw 파일은 불변 (수정 금지)

### Step 4: index.md + cadence.md + thesis-stack.md 업데이트
- `index.md` 본문 표에 1줄 추가
- `cadence.md` 발행 이력 + 다음 호 후보 3개 회전
- `thesis-stack.md` (선택) — 단일공식 누적 추가

### Step 5: logs + commit + push
```bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
cat > "logs/$TIMESTAMP.md" <<EOF
# [$TIMESTAMP] Newsletter Issue N: <slug>
## Summary
## Changes
EOF

git add -A
git commit -m "newsletter issue N: <slug> (<category>, +<N>raw)"
git push origin main
```

## 🔀 병렬화 패턴 (subagent 활용)

본문 리서치는 delegate_task로 background dispatch + 메인 에이전트는 base skeleton을 먼저 commit:

```
[병렬 1] subagent: 웹 리서치 + raw 발췌 + 본문 초안 작성 (5~10분)
[병렬 2] main: AGENTS/SCHEMA/index/cadence/thesis-stack 작성 + 1차 commit
       → subagent 결과 도착 시 본문/raw/추가 commit + push
```

**근거**: autonomous 모드("알아서 작업해주고")일 때 시간 낭비 금지. 메인이 빈손으로 subagent를 기다리지 않고 즉시 commit 가능한 skeleton을 만든다.

## ⚠️ Pitfalls (실전 검증)

### 1. 🔴 subagent가 잘못된 카테고리에 라우팅 가능
delegate_task 컨텍스트에 **반드시** 카테고리/디렉토리 명시:
```
context에 포함: "본문은 /tmp/newsletter-wiki/newsletter/01-2026/techno-trends/2026-07-01-coding-agent-ecosystem.md 위치에 작성하라. raw/01-newsletter/2026-07/ 하위에 발췌 저장."
```

### 2. 🟡 gh CLI --add-readme vs 빈 레포
`--add-readme`로 생성 시 자동으로 commit된 README가 있음. AGENTS.md를 루트로 쓰려면 README 삭제 필요 (`rm README.md`).

### 3. 🟡 main 브랜치 default
GitHub 2020+ default = main. `git branch -m master main`은 옛날 절차. 그냥 clone 후 main에서 작업.

### 4. 🔴 1차 commit을 main에 직접 push
subagent를 기다리는 동안 base skeleton을 main에 1차 commit하는 건 OK (placeholder 명시 시). 단 push는 본문 합쳐서 한 번에.

### 5. 🟡 private 레포 검증
`curl raw.githubusercontent.com/...` → 404 (anonymous). 검증은 `git ls-remote origin main` + GitHub UI (https://github.com/mybotagent/newsletter-wiki/commit/<hash>).

### 5.5. 🆕 Stage ⑥ Validate — GitHub API bytes check (2026-07-03)
5-stage verify의 마지막 단계. `git push` 성공 ≠ 실제 파일 존재. **반드시 실행**:

```bash
# 1) local 파일 사이즈 확인
ls -la newsletter/01-2026/<category>/<file>.md

# 2) GitHub API tree 실재 확인 (private repo는 raw.githubusercontent 404)
gh api repos/mybotagent/<repo>/contents/newsletter/01-2026/<category> \
  --jq '.[] | {name, path, size}'

# 3) 사이즈 비교 — 같으면 push 성공, 다르면 재시도
```

**Pitfall**: subagent가 "push 완료" 자가 보고해도 parent 세션에서 직접 검증. `git ls-remote`만으론 ref 업데이트만 확인하고 파일 존재는 보장 못 함. `gh api .../contents/<path>`만이 bytes-level ground truth.

### 6. 🟢 cadence.md / thesis-stack.md는 별도 단일공식 운영 메타
- `cadence.md` = 매일 1호 cadence (시간표 + 후보 3개)
- `thesis-stack.md` = 누적 단일 공식 (예: 주식 PER75:PBR25과 같은 형태로 본 뉴스레터에서도 누적)

### 7. 🆕 subagent 600s timeout fallback (2026-07-03)
`delegate_task(goal=research, role='leaf')`가 자주 600s timeout. **대응 패턴**:

1. **probe partial work** (1s):
   ```bash
   find /tmp -maxdepth 4 -type f \( -name '*.md' -o -name '*<topic>*' \) | head -20
   ```
2. **partial 있음** → 통합 + gap 명시
3. **partial 없음** → main 세션에서 직접 리서치로 전환 (위 Stage ③의 직접 curl 패턴 사용)
4. **재 dispatch는 피하기** — 동일 goal은 같은 600s 천장 또 hit. prompt 좁히거나 직접 모드.

**Trigger**: dispatch가 URL 30+ browse/summarize 작업일 때 timeout 위험 ↑. 직접 curl 5~10개 병렬이 더 빠를 수 있음.

## 🔗 Related

- `wiki-save` — 단발 텍스트 저장. 본 스킬은 **반복 cadence** 특화.
- `wiki-architecture` — Karpathy 5-layer 스키마 본체. 본 스킬은 newsletter 도메인 특화 적용.
- `meeting-documentation` — 회의록 (별도 class). 본 스킬과 트리거 분리.

## 📚 References

- `references/first-issue-template.md` — 1호 발행 템플릿 (commit msg, skeleton)
- `references/research-delegation-prompt.md` — subagent에게 보내는 리서치 프롬프트 템플릿