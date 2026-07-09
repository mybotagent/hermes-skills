---
name: wiki-save
description: "슬래시 명령어처럼 텍스트를 2중 레이어 LLM Wiki에 저장 — GitHub 레포(Layer 1) + LLM Wiki 패턴(Layer 2, operational/research 타입 분리) + 자동 신규 레포 생성"
version: 2.3.0
author: aiprofit
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, save, ingest, knowledge, routing, github, summarize, sources]
    related_skills: [wiki-architecture, llm-wiki]
---

# Wiki Save — 2중 레이어 LLM Wiki 저장 시스템 (v2)

> Karpathy LLM Wiki + GitHub 레포 분류 체계를 결합한 2중 레이어 저장 방식
> **Layer 1**: GitHub 저장소(주제별 분류) → **Layer 2**: Karpathy INDEX.md 패턴
> **동적 분류**: 기존 레포와 매칭 → 없으면 새 레포 생성

## 🎯 동작 방식

사용자가 텍스트 자료를 보내면:

### Step 1: 기존 레포 카탈로그 로드
`~/.hermes/wiki/infra/gh-token.md`와 GitHub API로 모든 기존 private 레포 목록 로드
→ 각 레포의 이름과 description에서 **카테고리 시그니처**(주제 키워드)를 추출

> **⚠️ 세션 내 연속 저장 최적화**: 같은 세션에서 직전에 특정 레포로 저장했고, 새 입력이 명백히 같은 주제(동일 키워드 50%+ 중복)면 분류 생략하고 직전 레포로 바로 저장. 예: Claude Code 페이지 5개를 잇달아 저장할 때 매번 분류하지 않고 같은 repo로 라우팅.

### Step 2: 텍스트 분류 (Layer 1)
입력 텍스트를 분석해 가장 유사한 기존 카테고리 탐색:
- **매칭 성공** (유사도 60%+) → 해당 레포에 저장
- **매칭 실패** (기존 레포와 겹치는 카테고리 없음) → **새 private GitHub 레포 생성** → 저장
- **모호함** (40~60%) → 사용자에게 질문

### Step 3: 저장 (Layer 2)
해당 레포 내에서 LLM Wiki 패턴으로 파일 생성/업데이트

### Step 4: INDEX.md + 카탈로그 동기화
- 레포 내 INDEX.md 업데이트
- 새 레포 생성 시 `gh-token.md`의 레포 목록 업데이트
- `hermes-wiki` INDEX.md의 Repo Map 업데이트

### Step 5: 로그 기록 + 결과 보고

## 📋 Layer 0: 기존 레포 카탈로그 (동적 로드 기준)

### 레포 목록 (총 13개, 2026-06-05 기준)

| 저장소 | GitHub | 카테고리 시그니처 | 로컬 경로 |
|:-------|:-------|:----------------|:---------|
| **hermes-wiki** | mybotagent/hermes-wiki | 공유 지식/INDEX — 방법론, 인프라, 설정, 사람, 일반 | `~/.hermes/wiki/` |
| **hermes-wiki-portfolio** | mybotagent/hermes-wiki-portfolio | ⚠️ ARCHIVED → `trade-pipeline/docs/portfolio-wiki/` | N/A |
| **trade-pipeline** | mybotagent/trade-pipeline | 주식/증시 — 트레이딩 파이프라인, LangGraph, 밸류에이션, 크론 | `~/trade-pipeline/` |
| **hermes-wiki-schedule** | mybotagent/hermes-wiki-schedule | 일정/캘린더 — 경제지표, 약속 | `~/.hermes/thread-wikis/hermes-wiki-schedule/` |
| **hermes-wiki-claude-code** | mybotagent/hermes-wiki-claude-code | Claude Code — CLI 명령어, 기능, 워크플로우 | `~/.hermes/hermes-wiki-claude-code/` 🆕 |
| **hermes-wiki-codex** | mybotagent/hermes-wiki-codex | Codex CLI (OpenAI) — 기능, 명령어, Goal, Steering, Plan Mode | `~/.hermes/hermes-wiki-codex/` 🆕 |
| **hermes-wiki-super** 🆕 | mybotagent/hermes-wiki-super | Super repo — 모든 wiki 레포 submodule로 모음. Obsidian 동기화용 | GitHub only |
| **hermes-logs** | mybotagent/hermes-logs | 변경 로그 — 타임스탬프 히스토리 | submodule in hermes-wiki |
| **stock-analysis-toolkit** | mybotagent/stock-analysis-toolkit | 주식 분석 스크립트 — 적정주가, 매크로 | submodule in hermes-wiki |
| **harness-engineering-wiki** | mybotagent/harness-engineering-wiki | Harness Engineering 강의 | `~/.hermes/harness-engineering-wiki/` |
| **hermes-slash-commands** | mybotagent/hermes-slash-commands | 슬래시 명령어 문서 | — |
| **subagents-library** | mybotagent/subagents-library | Sub-agent 패턴/프레임워크 카탈로그 | `~/.hermes/wiki/subagents-library/` |
| **claude-skill-library** | mybotagent/claude-skill-library | AI Agent 스킬 카탈로그 | submodule in hermes-wiki |
| **ai-job-analysis** | mybotagent/ai-job-analysis | AI Agent 직업 분석 | — |

### 카테고리 시그니처 (분류 키워드)

```
hermes-wiki:           ["방법론", "분석법", "인프라", "설정", "config", "cron", "token", "스킬", "사람", "프로필", "일반", "코드"]
hermes-wiki-portfolio: ["트레이딩", "파이프라인", "LangGraph", "크론"]  # ⚠️ ARCHIVED — trade-pipeline 참조
trade-pipeline:        ["주식", "증시", "종목", "PER", "PBR", "EPS", "밸류에이션", "적정주가", "포트폴리오", "매크로", "시장", "NVDA", "삼성전자", "SK하이닉스", "LangGraph", "파이프라인", "트레이딩"]
hermes-wiki-schedule:  ["일정", "캘린더", "약속", "경제지표", "CPI", "PCE", "FOMC", "고용", "NFP", "ISM", "회의"]
hermes-wiki-super:     ["super repo", "서브모듈", "submodule", "Obsidian 동기화", "모든 레포"]
hermes-logs:           ["로그", "변경이력", "히스토리", "changelog"]  # 직접 저장 대상 아님
stock-analysis-toolkit:["스크립트", "분석코드", "fair_value", "orbits"]
harness-engineering-wiki: ["Harness", "harness engineering", "CI/CD", "delivery", "엔지니어링"]
hermes-slash-commands:  ["슬래시", "slash", "명령어", "command", "hermes 명령어"]
subagents-library:     ["subagent", "sub-agent", "에이전트 패턴", "멀티에이전트", "agent framework"]
claude-skill-library:  ["스킬", "skill catalog", "CLI 스킬", "프롬프트"]
ai-job-analysis:       ["직업", "채용", "AI Agent 직업", "블루오션", "취업"]
hermes-wiki-claude-code: ["Claude Code", "Claude", "명령어", "CLI", "명령어", "코드 리뷰", "워크플로우", "자동화", "개발자 도구", "agent"]
hermes-wiki-codex: ["Codex", "코덱스", "OpenAI", "Goal", "Steering", "Plan Mode", "Worktree", "Fork", "골", "스티어링", "플랜 모드"]
```

### 분류 알고리즘

1. 입력 텍스트에서 키워드 추출 (명사/주제어 중심)
2. 각 레포의 카테고리 시그니처와 매칭 점수 계산
3. **최고 점수 레포 선택**
   - 점수 ≥ 60% → 해당 레포로 확정
   - 점수 40~60% → 사용자에게 "이 내용은 [레포A]와 [레포B] 중 어디에 저장할까요?"
   - 점수 < 40% (모든 레포) → **새 레포 생성 필요** → 사용자에게 확인 후 생성

### 새 레포 생성 조건
- 기존 10개 레포 중 어디에도 40% 이상 매칭되지 않는 완전히 새로운 주제
- 예: 갑자기 "요리 레시피" → 새 레포 `hermes-wiki-cooking` 생성
- 예: 갑자기 "운동/헬스" → 새 레포 `hermes-wiki-fitness` 생성

## 🆕 새 레포 생성 절차

새 레포가 필요할 때:

### 1. GitHub API로 private 레포 생성

```bash
# 토큰 읽기
TOKEN=$(sed 's/.*://' ~/.git-credentials | sed 's/@.*//')

# 새 레포 생성
curl -s -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{
    "name": "hermes-wiki-<topic>",
    "description": "<topic> wiki — Karpathy-style LLM Wiki",
    "private": true
  }'
```

`ghp_` 토큰은 `repo` scope로 private 레포 생성 가능. 단, `delete_repo` scope는 별도 필요.

### 2. 로컬에 클론 + LLM Wiki 구조 초기화

```bash
cd ~/.hermes
git clone https://github.com/mybotagent/hermes-wiki-<topic>.git

cd hermes-wiki-<topic>
echo "# <Topic> Wiki" > README.md
cat > index.md << 'EOF'
# <Topic> Wiki Index

> Content catalog
> Last updated: $(date +%Y-%m-%d)

## Pages
<!-- Alphabetical -->
EOF
mkdir -p analysis references

git add -A && git commit -m "init: <topic> wiki (Karpathy LLM Wiki pattern)"
git branch -m master main 2>/dev/null
git push -u origin main
```

### 3. 카탈로그 업데이트
- `~/.hermes/wiki/infra/gh-token.md` → 레포 목록에 새 레포 추가
- `~/.hermes/wiki/index.md` → Repo Map에 추가
- `~/.hermes/wiki/AGENTS.md` → 필요한 경우 라우팅 규칙 업데이트
- Memory에 새 레포 경로 저장

### 4. 저장
새로 생성된 레포에 텍스트를 LLM Wiki 패턴으로 저장

### 5. 로그 기록
hermes-logs에 레포 생성 + 첫 저장 로그 기록

## 📄 Layer 2: LLM Wiki 패턴 (레포 내부 구조)

콘텐츠 유형에 따라 두 가지 저장 경로:

| 유형 | 대상 디렉토리 | frontmatter | 예시 |
|:-----|:-------------|:------------|:-----|
| **Operational** (free-form) | `infra/`, `analysis/`, `code/`, `people/` 등 | `tags:`, `related:` | 서버 설정, 크론, 분석법 |
| **Research** (typed) | `research/entities/`, `research/concepts/`, `research/comparisons/` | `type:`, `title:`, `created:`, `updated:`, `tags:`, `sources:`, `confidence:` | 기술 분석, 논문 요약, 비교 |

### 필수 단계

#### ① 콘텐츠 유형 판별
- **Research 콘텐츠** (외부 기술/논문/제품/개념) → `research/` 타입 페이지로 저장
- **Operational 콘텐츠** (시스템 설정/분석법/코드) → 기존 디렉토리에 free-form 저장
- 모호하면 사용자에게 질문

#### ② 기존 내용 확인
```
1. 대상 저장소의 INDEX.md 또는 index.md 읽기
2. search_files로 기존에 같은 주제 페이지가 있는지 확인
3. 있으면 업데이트, 없으면 새로 생성
```

#### ③ Research 콘텐츠: 타입 결정
Research 콘텐츠일 경우 적절한 페이지 타입 선택:
- **Entity**: 단일 주체 (사람/조직/제품/기술) → `research/entities/`
- **Concept**: 추상 개념/프레임워크/이론 → `research/concepts/`
- **Comparison**: A vs B 체계적 비교 → `research/comparisons/`
- [SCHEMA.md](SCHEMA.md) page thresholds 참고

### ④ Raw Source 보존 (STEP ① — wiki 페이지보다 먼저!)

> **⛔ 절대 잊지 말 것**: wiki 페이지를 만들기 **전에**, 사용자가 보낸 **원본 텍스트를 그대로 raw source로 먼저 저장**하라.
> raw 저장을 건너뛰고 wiki 페이지만 만들면 사용자가 "원본 그대로 저장됐어?"라고 확인할 수 없음.

```yaml
# raw/source-file.md
---
source_url: aiprofit wiki-save (Discord)
ingested: YYYY-MM-DD
---
(원본 텍스트 그대로 — 가공/요약 금지)
```

**규칙:** raw source 저장은 wiki 페이지 작성보다 **먼저** 실행. 예외: 사용자가 명시적으로 "요약해줘"라고 한 경우.

### ⑤ 위키 페이지 생성 — "상세 설명 우선"

**사용자 선호 (2026-06-04 확인):** 각 개념/항목마다 **상세한 설명**을 포함할 것.

각 개념은 최소한 다음을 포함:
- **개념 정의** (무엇인가?)
- **동작 메커니즘** (어떻게 동작하는가?) — 단계별 설명
- **일반 vs 고급 비교표** (무엇과 어떻게 다른가?)
- **활용 예시** (실제 Copy-Paste 가능한 프롬프트/명령어)
- **차별점** (왜 이게 중요한가?)

**Bad vs Good:**
```
❌ Bad: "Goal은 집착적인 실행 모드입니다" (1줄)
✅ Good: "Goal: 턴 제한 없이 며칠/몇 시간도 실행. 
실패 시 대체 경로 탐색. 메타 프롬프팅 필수. 
일반 채팅 vs Goal 5개 항목 비교표 포함"
```

### ⑥ 원본 vs 위키 검증 (필수!)

wiki 페이지 생성 후, **원본 raw source와 비교하여 모든 핵심 포인트가 반영되었는지 검증**할 것.

```markdown
| 원본 항목 | 위키 반영 | 상태 |
|:---------|:---------|:----:|
| 개념 A 설명 | Section 2에 반영 | ✅ |
| 개념 B 설명 | 누락됨 | ❌ → 수정 필요 |
| 사용자 교정사항 | Section 5에 반영 | ✅ |
```

**문제 발견 시:** 즉시 wiki 페이지 수정 후 재검증.

### ⑦ 파일 생성/업데이트
- 파일명: `lowercase-hyphen-names.md` (영문), `한글-파일명.md` (한글 가능)
- YAML frontmatter 포함:

  **Operational (free-form):**
  ```yaml
  ---
  title: 페이지 제목
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  tags: [분류 태그]
  sources: [raw/source-file.md]
  related: [관련 페이지 경로]
  ---
  ```

  **Research (typed) — [SCHEMA.md](SCHEMA.md) 준수:**
  ```yaml
  ---
  type: entity | concept | comparison
  title: 페이지 제목
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  tags: [research, <type>, ...]
  sources: [raw/소스파일.md]
  confidence: high | medium | low
  related: [research/entities/related.md]
  ---
  ```
- 내용은 Karpathy 원칙: **Non-obvious knowledge only**
  - ❌ 설치 가이드, CLI 기초, 구글 1페이지에 나오는 일반 정보
  - ✅ 고유 분석법, 환경 특화 정보, 발견한 패턴/함정, 의사결정 기록
- 1~5KB, 핵심만 요약

### ⑧ INDEX.md 업데이트
- 새 페이지를 INDEX.md의 적절한 섹션에 추가 (알파벳/가나다순)
- 기존 페이지 업데이트 시 내용만 변경, INDEX.md 링크는 그대로
- **INDEX.md에 추가하지 않으면 페이지가 존재하지 않는 것과 같음**

### ⑨ 변경 로그 기록
```bash
cd ~/.hermes/wiki
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
cat > "logs/$TIMESTAMP.md" << LOGEOF
# [$(date '+%Y-%m-%d %H:%M')] Wiki Save: short-title

## Summary
무엇을 저장했고 왜 저장했는지

## Changes
- [저장소명] path/to/file.md — 생성/업데이트 (설명)
LOGEOF

git add -A && git commit -m "wiki-save: short description"
git push
```

> **참고**: thread-wikis(portfolio, schedule)는 별도 GitHub 레포이므로 해당 디렉토리에서 별도 git push 필요
> **참고**: harness-engineering-wiki, subagents-library 등 외부 레포도 동일한 git 커밋/푸시 필요

## 💬 사용법 (Discord)

### 호출 방식

사용자가 다음 패턴 중 하나로 요청하면 이 스킬이 활성화됩니다:

1. **"이거 wiki에 저장해줘: [텍스트]"**
2. **"저장: [텍스트]"**
3. **"wiki: [텍스트]"**
4. **"/wiki-save [텍스트]"** — 슬래시 명령어 스타일
5. **"다음 내용을 wiki에 저장해줘:" + [텍스트]**
6. **텍스트만 보내고 "wiki 저장" 요청**

텍스트가 너무 길면(2000자 이상):
- 요약해서 저장할지
- 파일로 저장할지 (write_file)
물어볼 것

### 응답 형식

#### CASE A: 기존 레포에 저장
```
✅ Wiki 저장 완료

📂 Layer 1: hermes-wiki-portfolio (기존 레포)
📄 Layer 2: watchlist/nvda-analysis.md
📑 INDEX.md 업데이트 ✅
📝 logs/2026-06-04-1200.md 기록
```

#### CASE B: 새 레포 생성 + 저장
```
✅ Wiki 저장 완료 + 🆕 새 레포 생성!

📂 Layer 1: hermes-wiki-cooking (신규)
   → github.com/mybotagent/hermes-wiki-cooking
📄 Layer 2: recipes/korean-bbq-sauce.md
📑 INDEX.md + gh-token.md + Repo Map 업데이트 ✅
📝 logs/2026-06-04-1200.md 기록
🧠 Memory 업데이트 완료
```

## ⚠️ 함정 및 주의사항

### 0. 🔴 Submodule push 시 detached HEAD (logs 서브모듈 등)

hermes-wiki 내 `logs/` (hermes-logs 서브모듈)는 **detached HEAD** 상태가 기본 — `.gitmodules`가 특정 commit hash를 잠가두기 때문. 일반 `git push origin main`은 **실패** (`src refspec main does not match any`).

**해결 (force 없음):**
```bash
cd <repo>/<submodule>
git push origin HEAD:refs/heads/main
# → [new branch] HEAD -> main 가능
```

**주의:**
- `--force` 또는 `--force-with-lease` 사용 금지 (위험, 다른 사람 commit 손실)
- hermes-wiki 메인 push는 **submodule push 완료 후** 별도 commit 필요 (submodule ref hash 갱신)
- 순서: submodule push → 메인에서 `git add logs` → 메인 commit + push

### 0.5. 🔴 Private repo 검증 — raw.githubusercontent.com 404

wiki repo는 모두 private. push 직후 `curl raw.githubusercontent.com/...` 하면 **404** (anonymous 404 정책). 

**올바른 검증:**
```bash
git ls-remote origin main
# 출력 예: 271e57109fc106077dddd2edc04cc72f2e7a6081	refs/heads/main
```
커밋 hash가 로컬 commit과 일치하면 push 성공. GitHub UI (https://github.com/mybotagent/<repo>/commit/<hash>) 에서 직접 확인 가능.

### 1. 🔴 SKILL.md 파일 권한 (600 → 644)
`skill_manage`나 `write_file`로 SKILL.md를 생성하면 `-rw-------` (600) 권한으로 생성됨.
Hermes 게이트웨이(`/skill` 명령어)는 600 파일을 읽지 못해 "Unknown skill" 오류 발생.

**반드시 생성 직후 권한 변경:**
```bash
chmod 644 ~/.hermes/skills/<skill-name>/SKILL.md
```

**확인:** `ls -la ~/.hermes/skills/<skill-name>/` → `-rw-r--r--` (644) 여야 함.
**위험:** 권한을 잊으면 `/reload-skills`에도 잡히지 않고 `/skill` autocomplete에도 안 나타남.

### 2. 🟢 연속 저장 최적화 (세션 내)
같은 세션에서 직전 저장한 레포와 새 입력의 주제가 50%+ 일치하면:
- **분류 단계 생략** → 직전 레포로 바로 저장
- **이유**: 사용자가 "이 외에도 ... 추가해줘" 패턴으로 연속 저장 요청하는 경우가 많음
- **주의**: 완전히 다른 주제면 분류를 생략하지 말 것

### 3. 🟡 분류 모호 시 추측 금지
분류가 50% 미만으로 확실하면 사용자에게 물어볼 것.

### 4. 🟡 Git Push 충돌 처리 (rejected)

`hermes-wiki`는 여러 세션/크론이 동시에 push할 수 있어 **rejected 오류**가 자주 발생.

```bash
# 에러: ! [rejected] main -> main (fetch first)
# 해결:
git pull --rebase origin main && git push
```

**규칙:**
- `git push` 실패 시 → 즉시 `git pull --rebase origin main && git push`
- 절대 `git push -f` (force push) 금지 — 다른 사람의 커밋 날아감
- rebase 충돌 발생 시: 충돌 해결 후 `git rebase --continue && git push`

### 5. 🔴 Git Push 누락 금지
- `hermes-wiki`는 `logs/` submodule 포함. `git add -A` 시 logs/ 변경도 포함
- thread-wikis(portfolio, schedule)는 별도 레포 → 해당 디렉토리에서 별도 commit/push
- hermes-wiki 변경 후 `git push origin main` 확인

### 6. 🔴 INDEX.md 누락 금지
파일만 생성하고 INDEX.md에 추가하지 않으면 고아 페이지. INDEX.md 업데이트 필수.

### 7. 🟡 하위 디렉토리 선택
`hermes-wiki`에서는:

**Operational:**
- `analysis/`, `infra/`, `watchlist/`, `people/`, `code/`, `architecture/`, `solopreneur/`, `repos/`

**Research:**
- `research/entities/` — 단일 주체 (entity)
- `research/concepts/` — 추상 개념 (concept)
- `research/comparisons/` — 비교 분석 (comparison)

중 가장 적합한 디렉토리 선택.

### 8. 🟡 이미지/파일 첨부 시 텍스트 요청
이미지나 파일이 첨부되었는데 텍스트 추출이 불가능하면, 내용을 추측/저장하지 말고 사용자에게 **텍스트로 다시 보내달라고 요청**할 것.

### 9. 🟡 같은 내용 중복 저장 금지
저장 전 `search_files`로 같은 내용이 이미 있는지 확인. 중복 시 "이미 [페이지]에 비슷한 내용이 있습니다. 업데이트할까요?" 질문.

### 10. 🟢 반복 제출 = 놓친 신호
사용자가 **같은 내용을 여러 번 반복해서 보내면**:
1. ❌ "이미 저장되었습니다" dismiss 금지
2. ✅ raw source 저장 여부 먼저 확인
3. ✅ wiki 페이지가 원본을 정확히 반영했는지 검증
4. ✅ 빠진 내용 즉시 수정
5. ✅ "빠진 부분이 있나요?" 질문

**반복 제출 = 내가 뭔가 놓쳤다는 신호.** 절대 무시하지 말 것.

### 11. 🔴 사용자 교정 즉시 반영
사용자가 wiki 페이지 내용을 교정하면:
1. **지금 당장** wiki 페이지에 반영
2. `updated` 날짜 갱신 + git commit + push
3. "수정 완료" 확인 전달

**"다음에 수정" 금지.** 지금 하지 않으면 영원히 안 함.

### 11.5. 🔴 "기존 자료/공식문서 토대로" 신호 — 임의 작성 금지

사용자가 다음 패턴으로 요청하면 **자기 스타일로 새로 짓지 말고** 지정된 1차 출처를 인용/구조화하라:

| 트리거 패턴 (한국어) | 트리거 패턴 (영어) | 의미 |
|:--------------------|:------------------|:-----|
| "기존 [자료/문서] 토대로" | "based on existing [docs]" | 1차 출처 = 기존 자료 |
| "[공식문서/도큐먼트] 기반" | "from the official docs" | 외부 공식 출처 우선 |
| "[OO] 문서/위키 기반으로" | "using the [X] wiki" | 기존 wiki 페이지 우선 |
| "~에서 가져와서" / "~를 인용해서" | "quote from ~" / "cite ~" | 발췌 + 출처 명시 |

**반응 프로토콜 (3단계)**:

1. **1차 출처 식별**
   - 사용자가 명시한 자료 (예: "헤르메스 공식문서" → `~/.hermes/skills/autonomous-ai-agents/hermes-agent/SKILL.md` + URL `hermes-agent.nousresearch.com/docs`)
   - 기존 wiki 페이지 (예: `architecture/hermes-vs-chatbot.md`, `hermes-memory-pipeline.md`)
   - 둘 다 가능

2. **읽기 → 발췌 → 인용 구조화**
   - ❌ 자기 임의 스타일/단일공식/예제 만들어내기
   - ✅ 기존 자료의 구조와 문구 보존, 출처 링크를 페이지 상단에 명시
   - ✅ 페이지 하단에 "🔗 1차 출처 (Single Source of Truth)" 섹션 필수

3. **출처 명시 형식 (모든 페이지 상단)**

   ```markdown
   > **이 문서는 [N]가지 1차 소스만 토대로 작성됐습니다:**
   > 1. [소스 1 — URL 또는 wiki 경로]
   > 2. [소스 2]
   >
   > 개인 의견·해석은 최소화했고, 공식 출처 링크를 그대로 보존합니다.
   ```

**Bad vs Good (Pitfall 2026-07-03, aiprofit 정정)**:

```
❌ Bad: 사용자가 "헤르메스 활용법 정리해서 github에" + "기존 공식문서 기반으로"
       → 단일공식 제 스타일로 6단계 사이클(요청→해석→실행→위키화→개선) 새로 발명
       → 기존 hermes-vs-chatbot.md, hermes-memory-pipeline.md, 공식문서 무시
       → 사용자: "아니.. 기존 헤르메스 공식문서를 토대로 알려줘" ← 정정

✅ Good: 즉시 작업 폐기 (rm -rf)
       → 1차 출처 식별:
          1. hermes-agent skill (공식문서)
          2. 기존 위키 4종 (hermes-vs-chatbot, hybrid-ai-stack, hermes-memory-pipeline, ssot)
       → 각 페이지 상단에 "출처: 공식문서 + 기존 위키" 명시
       → 구조화만 (인덱스, 목차, 출처 섹션), 본문은 발췌
       → INDEX.md 업데이트 + git push 검증 (git ls-remote)
```

**왜 함정이 반복되는가**:
- 사용자가 "정리해서"라고만 하면 자기 스타일로 작성하는 게 기본 반응
- "기존 자료/공식문서 기반"이 추가되면 발췌 모드로 전환해야 함
- 둘 다 한국어 모호 표현이라 같은 문장에 들어오면 놓치기 쉬움
- 해결: "정리" + "기존/공식/토대로/기반" 조합 감지 시 → 자동 발췌 모드

**연관**:
- `references/summarize-from-existing-sources.md` — 발췌 패턴 상세 절차 + 검증 체크리스트

12. 🔴 **미팅/회의록은 meeting-documentation skill 사용 (이 스킬 아님)**

사용자가 "미팅/회의/회의록/meeting notes" 키워드로 github 저장 요청 시 — **이 스킬을 절대 사용하지 마세요.**

| 사용자 키워드 | 올바른 스킬 | 올바른 레포 |
|:-------------|:-----------|:----------|
| 미팅 / 회의 / 회의록 / meeting notes / 3자회의 | **`meeting-documentation`** | `mybotagent/meeting-notes` (~/meeting-notes/) |
| 위키 / wiki / 지식 / 분석 / 리서치 저장 | wiki-save (이 스킬) | `mybotagent/hermes-wiki` 등 매칭 레포 |
| 노트 / 메모 / Obsidian | obsidian | ~/Documents/Obsidian Vault/ |
| Linear 이슈 생성 | linear | Linear workspace |
| Kanban 태스크 생성 | kanban-orchestrator | ~/.hermes/kanban.db |

**Pitfall (2026-07-01)**: aiprofit "현재 미팅안을 정리해서 github에올려줘 기존 스킬을이용해서" 요청 시 → ❌ wiki-save 잘못 로드 → 즉시 정정 ("기존 미팅 관련된 거 저장하는 스킬 있을거임 / 미팅 레포애"). meeting-documentation 로드 후 `~/meeting-notes/2026/07/01/2015_topic-slug/` 5파일 구조 (agenda/discussion/decisions/next_steps/DESIGN) + git push 성공.

**규칙**: "미팅" 또는 "회의" 키워드 감지 시 → **무조건 meeting-documentation 먼저 확인**. wiki-save 트리거("위키/wiki/지식 저장")와 명확히 구분. 두 스킬 모두 "텍스트 → GitHub" 패턴이라 한국어 모호 표현("정리해서 올려")이 둘 다 트리거 가능하므로 키워드 우선.

**이유 (왜 함정이 반복되는가)**:
- 두 스킬 모두 한국어 사용자, "정리해서 github에" 패턴
- wiki-save가 카테고리 매칭 시도 시 회의록도 일반 텍스트로 인식할 위험
- 해결: 키워드 기반 분기. "미팅/회의" 명시 → meeting-documentation 1순위 고정.

## 🔄 Memory Tool → Wiki Sync (별도 watcher, 2026-07-02 합의)

`wiki-save`의 분류/저장 자동화 패턴을 memory tool 직접 push에 적용. 별도 구현은 `~/.hermes/scripts/memory_sync.sh` (영속: `mybotagent/hermes-pipeline-scripts`).

### 사용법
```bash
~/.hermes/scripts/memory_sync.sh "TITLE" "BODY"
# → raw + page 2건 저장 + git commit + push + (옵션) Neo4j reindex
```

### 패턴: Karpathy raw + page 동시 저장
- raw: `~/.hermes/wiki/raw/sync/<TS>-<slug>.md` (불변 원본)
- page: `~/.hermes/wiki/architecture/memory-snapshots/<TS>-<slug>.md` (영속 페이지)
- 두 파일 동시 저장 → 위키 패턴 일치

### Heredoc injection-safe pattern
```bash
{
  cat <<EOF
---
title: $TITLE
created: $DATE
tags: [memory-sync, snapshot]
sources: [raw/sync/$TS-$SLUG.md]
related: [../hermes-memory-pipeline.md]
---

# $TITLE

EOF
  printf '%s\n' "$BODY"      # ← 사용자 입력은 printf safe
  cat <<'FOOTER'              # ← 정적 텍스트는 single-quoted

## Provenance
- Manual watcher (memory_sync.sh)
FOOTER
} > "$SLOT_DIR/$TS-$SLUG.md"
```

**왜?**
- `<<EOF` (unquoted) → `$USER_INPUT` evaluate → shell injection 위험
- `printf '%s' "$VAR"` → quoted, escape, no expansion
- `<<'EOF'` → 정적 텍스트 (변수 확장 X)

### Trigger 정책
- **사용자 명시 trigger** (단일공식 철학 — 자동 cron 시 의도 추측 위험)
- `0 20 * * *` cron = `wiki_reindex.sh`만 (12초, sync only)
- `memory_sync.sh` 자동 cron은 **OFF**

### 5-Stage Verify 적용
- why: memory tool 2,200자 한계 → 영속 layer로 push
- what: raw + page 동시 저장 + commit + push
- whether: wiki-save 분류와 정합성 (raw + page 일관)
- what: audit pack에서 printf safe + env var override 적용
- how: atomic commit (한 entry = 한 commit)
- validate: `git ls-remote` + `bash -n` syntax OK + mirror `~/.hermes/scripts/` sync

### 후속
- trigger 자동화는 별도 회의 (cron auto 위험)
- 자동 압축 OFF (단일공식 위반, 90% 알림만 — `memory_alert.sh`)

---

## 📚 참고
