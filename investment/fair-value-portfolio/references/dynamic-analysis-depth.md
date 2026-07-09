# Dynamic Analysis Depth — LangGraph 조건부 분기 (참조 설계)

**소속 스킬**: `fair-value-portfolio` (Phase 6, 향후 확장 옵션)
**현재 상태**: Bull+Bear+Risk 1라운드 고정. 이 구조는 **필요 시** 전환.

---

## 개요

데이터 품질(최신성, 출처 신뢰도, 정보량)에 따라 분석 깊이를 동적으로 변경.
LangGraph의 `add_conditional_edges()`가 없으면 Python if/elif/else 3중첩 + 재귀함수 필요.

## 4-way Quality Router

```python
def assess_quality(state):
    score = 0
    if source_age < 30:    score += 2   # 30분 이내
    elif source_age < 120: score += 1   # 2시간 이내
    if has_analyst_target: score += 1
    if news:               score += 1
    if insider:            score += 1

    if score >= 5: return "high"          # 풀 분석 (Context→Bull∥Bear→Decision)
    if score >= 3: return "medium"        # 빠른 분석 (Context→Quick Decision)
    if score >= 1: return "investigate"   # 조건부 Loop 가능
    return "low"                          # 분석 불필요
```

## LangGraph 조건부 분기 (전환 시)

```python
builder.add_conditional_edges("quality_check", quality_router, {
    "high": "context",
    "medium": "context",        # → quick_decision (Bull/Bear 생략)
    "investigate": "context",   # → Bear가 "추가 데이터 필요" → loop back
    "low": END
})

# INVESTIGATE 경로: 조건부 Loop
builder.add_conditional_edges("bear", needs_more_data_router, {
    "continue": "context",      # 추가 데이터 → 재분석
    "done": "decision"          # → 최종 결정
})
```

## 적용 시 비용

| 경로 | LLM 호출 | 1회 비용 |
|:-----|:--------:|:--------:|
| high | V3 4회 + R1 1회 | ~12원 |
| medium | V3 1회 + R1 1회 | ~6원 |
| investigate (1회) | V3 4회 + R1 1회 | ~12원 |
| investigate (2회) | V3 7회 + R1 1회 | ~18원 |
| low | 0회 | 0원 |

> **현재는 Bull+Bear+Risk 1라운드 고정 (high만 사용).**
> 위 구조는 추후 데이터 품질 변동이 심해지면 도입 검토.
