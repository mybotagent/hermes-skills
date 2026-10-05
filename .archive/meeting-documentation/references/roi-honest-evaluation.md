---
tags: [roi, honest-evaluation, value-verification, skeptic, "이게-진짜-필요한가"]
---

# ROI Honest Evaluation — "이게 진짜 가치 있나?"

> aiprofit의 **가치 검증 선행** 워크플로우. 사용자가 "이게 진짜 가치 있나?", "토큰 줄여줄까?", "방해만 될까?" 물을 때 정직하게 답하는 패턴. SHO-24 (Skill Dynamic Selection Phase ②) 사례 기반.

## When to Use

- 사용자가 "이거 진짜 필요한가?" / "가치 있어?" / "ROI 있어?" 물을 때
- 새 기능/시스템 도입 제안 후 사용자가 의심할 때
- "작업 시간 줄여줄까 vs 방해만 될까" 양면 평가 요청
- 자기(Bot)가 이전에 추천한 것에 대해 사용자가 의심할 때

## Core Principle (aiprofit 명시 요구)

> **"가치 검증 선행 — 실행 전 진짜 필요성 평가"**

rubber-stamp "좋다 좋다" 답변은 **신뢰 하락**. 사용자가 진짜 답을 원함. 시스템 코드를 직접 분석해서 정량 데이터로 답할 것.

## Evaluation Pattern (4 Steps)

### Step 1 — 가설 vs 실제 시스템 분석

사용자/내가 제안한 가설:
> "50개 스킬 다 로드돼서 토큰 낭비"

시스템 코드 직접 분석:
```python
# prompt_builder.py: build_skills_system_prompt() 보니까
# Tier 1: system prompt 시작 시 → 이름 + 1줄 description만 inject (~3-5KB)
# Tier 2: LLM이 skill_view() 호출 시 → 풀 SKILL.md 로드 (필요한 것만)
```

**핵심 발견**: 가설 자체가 틀린 경우가 많음. 시스템이 이미 lazy loading 구현.

### Step 2 — 정량 비교

| 항목 | 현재 시스템 | 새 시스템 pretend | 차이 |
|------|-------------|------------------|------|
| 매 세션 시작 | ~3-5KB | ~3-5KB | 0% |
| 풀 SKILL.md | LLM 요청 시만 | 동일 | 0% |
| **총 토큰** | 0% 변화 | - | **거의 없음** |

### Step 3 — 약간 도움 vs 근본 ROI 분리

**약간 도움 (low-value)**:
- analyze의 컨텍스트 분석 → discoverability ↑
- switch의 unload hint → 명시성
- 코드 추가 100줄 → 유지보수 부담

**근본 ROI 없음**:
- 가설이 틀렸음 (50개 다 로드된다는 전제)
- 토큰/시간 변화 ≈ 0
- 다른 곳에 시간 쓰는 게 나음

### Step 4 — 정직한 권고

```
❌ "좋다 좋다, 진행합시다" (rubber-stamp) — 신뢰 하락
✅ "이 가설은 시스템 코드 분석 결과 틀렸습니다. ROI 낮습니다. 다른 곳에 시간 쓰자" (정직)
```

## Real Example: SHO-24 (Skill Dynamic Selection Phase ②)

### 사용자 질문
> "지금 이 방식이 토큰소모를 줄이거나 시간을 줄여줄까 아니면 오히려 더 방해만 될까?"

### 분석

**시스템 코드** (`prompt_builder.py`):
```python
def build_skills_system_prompt(available_tools=None, available_toolsets=None) -> str:
    # ...
    skills_by_category: dict[str, list[tuple[str, str]]] = {}
    # 이름 + description만 inject
    for entry in snapshot.get("skills", []):
        skills_by_category.setdefault(category, []).append(
            (frontmatter_name, entry.get("description", ""))
        )
```

**핵심**: Tier 1 (system prompt) = **description만**, Tier 2 (skill_view 호출) = **풀 SKILL.md**.

### 정량 결과

| 항목 | 현재 | Phase ② |
|------|------|---------|
| Tier 1 토큰 | 3-5KB | 3-5KB (동일) |
| Tier 2 호출 | 필요한 것만 | 동일한 lazy 호출 |
| **총 토큰** | 0% 변화 | - |
| 50개 SKILL.md 크기 | 1.4MB | 1.4MB |
| **매 세션 풀 로드** | **하지 않음** | - |

**결론**: "50개 다 로드"는 가설 자체가 틀림.

### 정직 권고

| 옵션 | 추천 | 이유 |
|------|------|------|
| A. SHO-24 Cancel | ⭐ | 진짜 ROI 없음 |
| B. 축소 (analyze만) | ⭐⭐ | 15분, 약간 가치 |
| C. 그대로 진행 | ❌ | 30-60분 낭비 |
| **D. skill description 품질 개선** | ⭐⭐⭐ | 진짜 병목 |

**진짜 권고 (사용자 철학과 정합)**:
- "단일공식 선호" — Phase ② 옵션 A/B/C → **Cancel or D (description 개선)**
- D가 가장 정직한 답 (가짜 옵션 3개 나열 대신 진짜 답 1개)

## Evaluation Checklist

평가할 때 다음 확인:

- [ ] **가설이 시스템 코드와 일치?** 코드 직접 읽기
- [ ] **정량 데이터로 비교?** 단정 ❌, 숫자 ✅
- [ ] **현재 동작 vs 제안 동작의 실제 차이?** "토큰 절감" 같은 모호한 말 ❌
- [ ] **유지보수 비용 포함?** 새 코드 = 새 버그
- [ ] **대안 제시?** "이거 안 한다면 뭐가 더 가치 있나?"
- [ ] **사용자 철학과 정합?** 단일공식/가치검증선행

## Failure Modes to Avoid

### ❌ Rubber-stamp 답변
```
Q: "이거 가치 있어?"
A: "네, 좋아 보입니다! 진행합시다." 
```
→ **이건 평가가 아니라 칭찬**. 신뢰 하락.

### ❌ 옵션 나열 답변
```
A: "Option A, B, C가 있습니다. 어느 걸로 할까요?"
```
→ **aiprofit이 정한 단일 공식 위반**. 1순위 + fallback 2개로 압축.

### ❌ 주관적 답변
```
A: "느낌적으로 좋아 보입니다."
```
→ **근거 없음**. 정량 데이터 / 코드 분석 필수.

### ❌ 포기 답변
```
A: "잘 모르겠습니다. 그냥 하죠."
```
→ **가치 검증 실패**. 시간을 더 들여서 진짜 답 찾기.

## Positive Pattern — 정직 권고

```
Q: "SHO-24 (Phase ②) 가치 있어?"

A: "코드 분석 결과 가설이 틀렸습니다. 시스템은 이미 2-tier lazy loading을 구현하고 있어.
   Tier 1 (system prompt)은 description만, Tier 2 (skill_view)는 풀 SKILL.md 호출 시만.
   Phase ② 추가 시 토큰 차이 ≈ 0%.

   진짜 병목은 skill description 품질입니다. 50개 중 일부는 description이 모호해서 LLM이 헤매는 거.
   description 개선이 ROI 10배 이상.

   권고: SHO-24 Cancel, 대신 skill inventory audit (description 품질 점검) 진행."
```

**이게 정직한 답변.** 가치 없으면 가치 없다고 말하기. 사용자는 그걸 원함.

## Skill Description Quality Audit (SHO-24 대안)

Phase ② 대신 권장하는 진짜 작업:

```bash
# 1. 모든 SKILL.md description 길이 확인
for f in ~/.hermes/skills/**/SKILL.md; do
    desc=$(awk '/^description:/,/^---$/' "$f" | head -3)
    length=$(echo -n "$desc" | wc -c)
    echo "$f: $length bytes"
done | sort -t: -k2 -n

# 2. description 짧은 것 (< 50자) 찾기 → 우선 개선 대상
# 3. LLM이 어떤 description을 보고 잘못된 skill을 선택하는지 로깅
# 4. description 길이 + 정확성 매트릭스 작성
```

## Memory + Skill Embedding

이 패턴을 발견하면:

1. **Memory**: "aiprofit — 가치 검증 선행 선호" (이미 있음)
2. **Skill**: `meeting-documentation`의 `references/roi-honest-evaluation.md` (이 파일)
3. **Workflow**: 사용자 평가 요청 시 **자동으로** 코드 분석 → 정량 비교 → 정직 권고

## Related Patterns

- **"기초부터 렙업"** (aiprofit 학습 선호) — 모르는 주제일 때 개념→구조→실전 순서
- **"단일공식"** (value investing) — 옵션 나열 ❌, 1순위 + 1 fallback
- **"OAuth 코드 만료 시 서비스 계정 우회"** (실용주의) — 가설보다 실제 동작
- **"GitHub API 검증 선호"** (검증 중시) — 주장보다 증거

## Pitfalls

- **"가치 있다" 평가가 어려운 일은?**: 그래도 정직하게 답해야 함. "ROI 측정 불가"는 rubber-stamp보다 낫지만, "이유는 X, Y" 같은 분석이 더 가치.
- **자기 추천에 대한 자기 평가**: 당연히 편향. 따라서 외부 검증 / 코드 분석 / 정량 데이터로 균형.
- **사용자 의중 추측**: "당연히 가치 있을 거라 생각하실 거야" — 추측 ❌. 사용자가 진짜로 물은 거니까 진짜로 답.
- **너무 자주 평가 요청하면 짜증**: 가끔은 그냥 진행도 OK. 사용자가 명시적으로 물을 때만.

## Final Note

> 정직한 답이 항상 옳다. 가치 없다면 가치 없다고 말하기. 그게 aiprofit이 신뢰하는 답.
