---
name: public-portfolio-content
description: "Public-facing portfolio/reveal deck content conventions — Korean/bot-name/closing-slide removal, link hygiene, readability, and github.io deployment pitfalls. Use when editing content that ships to a public URL (GitHub Pages, portfolio sites, public docs)."
version: 1.0.0
author: 채니봇
platforms: [linux, macos]
metadata:
  hermes:
    tags: [portfolio, github-pages, public, content, readability, korean, conventions]
    related_skills: [wiki-save, hermes-agent]
---

# Public Portfolio Content Conventions

> **Public URL = public contract.** Everything shipped to `mybotagent.github.io/*` (or any public repo) must pass these conventions. Private wiki content has different rules — this skill is for **public surface area only**.

## 🎯 When to Use

Trigger keywords:
- "깃헙페이지", "github.io", "github pages"
- "포트폴리오", "deck", "슬라이드"
- "공개", "public"
- "채니봇 빼고", "한글 빼고" (deck-specific)

Or any edit to files under `mybotagent.github.io/hermes-architecture-deck/` or other `*.github.io` repos.

## 📋 Hard Rules (Public Surface)

### 1. ❌ NO Korean text in public decks

- Public portfolio = global audience. Default = English.
- **예외**: 한국어 전용 채널/사이트에만 게시 시 한국어 OK.
- **자동 처리**: 한국어 섹션 발견 시 영어로 번역 + 발췌 출처 명시.
- **Why**: 한국어 모국어 화자가 아닌 방문자에게 noise. Bilingual navigation is worse than monolingual.

### 2. ❌ NO bot/agent names (채니봇, hermes-bot, etc.)

- User-facing portfolio = user's voice, not the agent's.
- **자동 처리**: "채니봇", "봇", agent persona 모두 제거.
- **예외**: "Built with [agent name]" footer 정도는 OK (attribution은 명시 OK).

### 3. ❌ NO closing slides ("끝", "Q&A", "Thanks for watching")

- Decks should end on substantive content, not ceremonial slides.
- **이유**: Ceremonial final slides add noise without information. Last slide = final takeaway or asset table.

### 4. ❌ NO redundant external links

- "← Portfolio" / "hermes-wiki" / "meeting-notes" 모든 페이지 끝에 반복 → 불필요.
- **허용**: 페이지 본문에서 의미 있는 자산 참조 (e.g., assets table의 wiki link)
- **금지**: 메타 navigation 링크 반복 (이미 navigation bar가 처리)

### 5. ✅ Full sentences, not fragments

- **Bad**: "전체 아키텍처 흐름도" (3 단어)
- **Good**: "End-to-End Architecture Flow" (5 단어, 명확)
- 단편 → 풀 문장으로. 가독성↑, 검색 가능성↑.

## 🔧 GitHub Pages Deployment Pitfalls (2026-07-03)

### Pages CDN Stuck — the most common issue

**증상**: `git push` 성공했지만 live URL은 옛 버전 (`last-modified` stale). `age` 0+ 분인데 변화 없음.

**진단 단계**:

```bash
# 1. Live last-modified 확인
curl -sI https://mybotagent.github.io/<repo>/<path> | grep -iE "last-modified|age|content-length"

# 2. 모든 페이지가 동일 last-modified면 빌드 stuck
for page in /decks/<a>/index.html /decks/<b>/index.html /index.html; do
  curl -sI "https://mybotagent.github.io/<repo>$page" | grep -i last-modified
done

# 3. GitHub Status 확인 (incident 있는지)
curl -s https://www.githubstatus.com/api/v2/summary.json | grep -A1 Pages
```

**해결 단계 (사용자 측 가능)**:

```bash
# Step A: 빈 commit으로 강제 트리거 (가끔 작동)
git commit --allow-empty -m "chore: trigger Pages rebuild"
git push

# Step B: GitHub API rebuild (더 강력)
TOKEN=$(grep "mybotagent:" ~/.git-credentials | sed 's|https://mybotagent:||; s|@github.com||')
curl -s -X POST -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/mybotagent/<repo>/pages/builds"

# 상태 추적
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/mybotagent/<repo>/pages/builds/latest" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('status:', d.get('status'), 'duration:', d.get('duration'),'ms')"
```

**Status 의미**:
- `queued` → 대기열 (정상)
- `building` → 빌드 중 (보통 1~3분)
- `built` → 완료 (live 반영)
- `errored` → 빌드 실패. `error.message` 확인. 보통 .nojekyll 또는 Jekyll 호환 문제.
- **1분+ `building` 0ms = stuck** → GitHub 인프라 incident 가능

### 🚨 GitHub Incident 시 — 사용자 알림

`https://www.githubstatus.com/api/v2/summary.json`:
- `Pages: degraded_performance` 또는 `partial_outage`이면 incident 진행 중
- `Incidents` 배열에 "Incident with Pages" 보고 있으면 공식 incident

**사용자에게 보고할 메시지 포맷**:
```
⚠️ GitHub Pages incident 진행 중 (출처: githubstatus.com)
- Push는 성공했지만 live CDN은 옛 버전 유지
- 5분~1시간 내 자동 반영 예정
- 강제 rebuild API도 동일 증상
- 사용자 측에서 더 할 수 있는 것 없음
```

### 검증 — "정말 push 됐나"?

**Private repo → raw.githubusercontent.com 404는 정상**. 올바른 검증:

```bash
# 1. ls-remote (commit hash 일치)
git ls-remote origin main
# 로컬 commit과 일치하면 push 성공

# 2. GitHub API (실제 파일 메타)
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/mybotagent/<repo>/contents/<path>" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('sha:', d['sha'][:10], 'size:', d['size'])"
```

로컬 file size + GitHub API size + ls-remote commit hash — 3가지 모두 일치해야 진짜 push 성공.

## 🎨 Readability Checklist (Content Edit 시)

각 섹션/슬라이드마다:

- [ ] 풀 문장 (단편 X)
- [ ] 자연스러운 영어 (직역 X)
- [ ] 표/리스트 적절히 사용 (텍스트 wall X)
- [ ] 핵심 메트릭은 굵게 또는 코드 (`<code>`)
- [ ] 섹션 헤더는 결과/목적 (e.g., "Validated End-to-End" not "Test Results")

## ⚠️ Pitfalls

### ❌ 자기 스타일로 새로 짓기 (2026-07-03 Pitfall)
- 사용자가 "github.io에서 메모리 관리 deck 정리해줘" → **첫 시도에서 6단계 단일공식 임의 작성** → 사용자 정정
- ✅ 항상 Pitfall 11.5 (`wiki-save`) 처럼 **기존 자료/공식문서 토대로** 발췌 모드

### ❌ Push 후 변화 없음 = "내가 뭔가 잘못했나" 가정 (잘못된 결론)
- 보통 **GitHub 인프라 incident**. 사용자 탓 아님.
- ✅ 진단 단계 1~3 (curl headers + status API) 먼저 실행

### ❌ Closing slide 추가 (습관)
- "끝. Push & validate." 같은 슬라이드 → **즉시 제거**
- 마지막 슬라이드 = 자산/참조/요약 표

## 📚 Examples

### 2026-07-03 메모리 관리 deck (mybotagent.github.io/hermes-architecture-deck/decks/memory-pipeline/)

**Before (사용자 정정 트리거)**:
- 슬라이드 8개, 마지막 "끝. Push & validate." + 채니봇/Portfolio/meeting-notes 링크
- 다수 한글 섹션 (전체 아키텍처 흐름도, 왜 이 4-Layer인가, 실제 작동 결과 등)
- 단편적 문장 (전체 / 왜 / 실제)

**After**:
- 슬라이드 7개, 마지막은 "Open Workstreams" (substantive)
- 100% 영어
- 풀 문장 + 자연스러운 헤더
- 채니봇/Portfolio/meeting-notes 메타 링크 제거
- 자산 테이블은 의미 있는 wiki link만 유지

**GitHub Pages 반영**:
- 3번 push 시도 후 정상 반영 안 됨
- GitHub API rebuild + 빈 commit 시도
- **원인**: GitHub 측 Pages incident (githubstatus.com 확인)
- **해결**: incident 종료 대기 (사용자 통보, 더 할 수 있는 것 없음)

## 🔗 Related

- `wiki-save` §Pitfall 11.5 — "기존 자료 토대로" 신호 (임의 작성 금지)
- `hermes-agent` (번들) — 공식 GitHub Pages 셋업 문서
- `architecture/hermes-architecture-deck` — 예시 프로젝트