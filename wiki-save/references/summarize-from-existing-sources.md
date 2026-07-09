---
title: 기존 자료/공식문서 기반 발췌 패턴
created: 2026-07-03
updated: 2026-07-03
tags: [wiki-save, summarize, sources, pattern, pitfall]
related: [SKILL.md §11.5, references/worked-example-claude-code-repo.md]
---

# 기존 자료/공식문서 기반 발췌 패턴

> **용도**: 사용자가 "기존 [자료/공식문서] 토대로/기반으로/가져와서" 같은 신호를 줬을 때의 반응 절차.
> SKILL.md §11.5에서 발췌. 이 문서는 상세 절차 + 검증 체크리스트 + 사례.

## 트리거 패턴 (한국어/영어)

| 한국어 | 영어 | 의미 |
|:-------|:-----|:-----|
| "기존 [OO] 토대로" | "based on existing [X]" | 1차 출처 = 기존 자료 |
| "[공식문서/도큐먼트] 기반/으로" | "from the official docs" | 외부 공식 출처 우선 |
| "[OO] 문서/위키 기반으로" | "using the [X] wiki" | 기존 wiki 페이지 우선 |
| "~에서 가져와서" | "quote from ~" / "cite ~" | 발췌 + 출처 명시 |
| "[OO] 활용법/매뉴얼 정리해서 github에" | "summarize [X] docs to github" | 발췌 + 구조화 |

## 반응 프로토콜 (5단계)

### Step 1: 1차 출처 식별

```
사용자: "헤르메스 활용법 정리해서 github에 올려서 정리해줄래?"
       + (이어서) "기존 헤르메스 공식문서를 토대로 알려줘"

1차 출처 후보:
  A. 외부 공식문서 (URL) — 사용자가 명시한 경우
  B. 기존 위키 페이지 (wiki INDEX.md 검색)
  C. 스킬 (예: hermes-agent skill이 공식문서 요약본)
  D. 사용자 제공 본문 (raw source로 저장)
```

**판단 기준**:
- "공식문서/도큐먼트" 명시 → A, C 우선
- "기존 위키/문서" 명시 → B, C 우선
- 둘 다 → A + B + C 모두 활용 (이번 케이스)

### Step 2: 자료 수집

```bash
# A. 외부 URL fetch
curl -fsSL <URL> -o /tmp/source.md

# B. 기존 위키 페이지 검색
cd ~/.hermes/wiki
search_files(pattern="헤르메스", target="content", path=".")
cat index.md

# C. 스킬 로드
skill_view(name="hermes-agent")

# D. (해당 시) raw/에 사용자 원본 저장
mkdir -p raw/<topic>
```

### Step 3: 발췌 + 구조화 (작성 단계)

**DO**:
- 기존 자료의 구조와 문구를 가능한 한 보존
- 핵심 정의/메커니즘은 원문 인용 (출처 명시)
- 페이지 상단에 **출처 명시 박스**:
  ```markdown
  > **이 문서는 [N]가지 1차 소스만 토대로 작성됐습니다:**
  > 1. [소스 1 — URL 또는 wiki 경로]
  > 2. [소스 2]
  >
  > 개인 의견·해석은 최소화했고, 공식 출처 링크를 그대로 보존합니다.
  ```
- 페이지 하단에 **🔗 1차 출처 (Single Source of Truth)** 섹션
- 각 페이지마다 `sources: [...]` frontmatter 명시
- 큰 표/리스트는 발췌 후 wiki INDEX 형식에 맞게 단순화

**DON'T**:
- ❌ 자기 임의 스타일(단일공식, 5-stage verify 등)로 새 구조 발명
- ❌ 원문에 없는 예제/해석 추가 (사용자가 명시 요청 시만)
- ❌ 출처 없이 "일반적으로 알려진" 식의 작성
- ❌ "제가 정리한 결론" 같은 1인칭 의견 (출처 인용이 아닌 경우)

### Step 4: 검증 체크리스트 (validate)

작성 후 반드시 점검:

- [ ] 모든 페이지 상단에 "출처 명시 박스" 있음?
- [ ] 각 페이지 frontmatter `sources: [...]` 채워짐?
- [ ] 페이지 하단에 "🔗 1차 출처" 섹션 있음?
- [ ] 외부 URL 인용 시 정확한 URL인지 (404 검증 안 함, 공식 URL만)?
- [ ] wiki 페이지 경로 인용 시 실제 존재하는지 (`read_file` 확인)?
- [ ] INDEX.md에 새 페이지 추가?
- [ ] git commit + push + `git ls-remote` 검증?

### Step 5: 보고

```
✅ 발췌 + GitHub 업로드 완료

📂 저장소: <repo-name>
🔗 1차 출처:
   1. <URL 또는 wiki path 1>
   2. <URL 또는 wiki path 2>
📄 작성: <page 1>, <page 2>, ...
🔍 검증: git ls-remote hash 일치 ✅
```

## 실제 사례 (2026-07-03)

### Pitfall

```
사용자: "헤르메스를 잘 활용하는 방법에 대해서 정리해서 github에 올려서 정리해줄래?"

에이전트 반응 (❌ 잘못):
- 5-stage verify로 자기 스타일 단일공식 발명
- "요청→단일공식→실행→검증→위키화→개선" 6단계 사이클 작성
- 기존 hermes-vs-chatbot.md, hermes-memory-pipeline.md, 공식문서 무시
- 새 페이지 5개 (README, 01~05) 생성

사용자 정정: "아니.. 기존 헤르메스 공식문서를 토대로 알려줘"

에이전트 수정 (✅ 옳음):
- 즉시 잘못된 파일 rm -rf
- 1차 출처 식별:
  1. hermes-agent skill (Nous 공식문서 발췌본)
  2. 기존 위키 4종 (hermes-vs-chatbot, hybrid-ai-stack, hermes-memory-pipeline, ssot)
- 새 페이지 10개 (README + 9개 문서) 재작성
- 각 페이지 상단 출처 박스, 하단 1차 출처 섹션
- INDEX.md 업데이트 + git commit/push + ls-remote 검증

결과: commit `4ddaf8c` push 성공, aiprofit 만족
```

### Lessons Learned

1. **"정리" + "기존/공식/토대로/기반"** 조합 감지 시 → 자동 발췌 모드 (자기 스타일 OFF)
2. **출처 명시는 모든 페이지에** (상단 박스 + 하단 섹션 + frontmatter sources)
3. **기존 자료 우선 + 자기 해석 최소화** — 발췌가가 아니라 큐레이터
4. **정정 신호 = 즉시 폐기 + 재시작** (이미 만든 파일 보존하려 하지 말 것)
5. **검증은 측정 가능 신호로** (`git ls-remote`, `read_file`, `search_files`)

## 연관

- SKILL.md §11.5 — 메인 함정 정의
- `references/worked-example-claude-code-repo.md` — 다른 발췌 패턴 사례
- §8 (이미지/파일 첨부) — 같은 모호 표현 처리 패턴 (텍스트 요청)

## Anti-patterns (절대 하지 말 것)

```
❌ "공식문서 기반이지만 제 스타일로 재구성했어요" → 1차 출처 무시
❌ "공식문서 + 제 해석을 더해서" → 제 해석 = 1차 출처가 아님
❌ "공식문서에 없는 부분은 제가 추가했어요" (사용자 명시 X) → 임의 작성
❌ "요약하자면 ~" 식의 자기 결론 → 출처 인용이 아닌 1인칭
```

**원칙**: 사용자가 "기존 자료/공식문서 기반" 신호를 줬다면, **에이전트는 큐레이터이지 저자가 아닙니다.**