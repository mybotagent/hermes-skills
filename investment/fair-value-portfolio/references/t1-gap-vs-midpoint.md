# T1 Gap vs Midpoint Gap — 2026-06-08 전환 사유

## 배경
2026-06-07까지 포트폴리오 비중과 Phase 1 필터는 **midpoint_gap** (T1 적정가 + Analyst Target의 중간값 괴리율)을 사용했다.

## 문제
- midpoint는 Analyst Target이 없거나 stale한 경우 T1 단독으로 fallback되어 일관성 부족
- Analyst Target 자체가 yfinance upgrades_downgrades의 30일 window 최신값 → 평균 25~35% 과대낙관 가능
- midpoint_gap을 계산할 때 `current_price`를 T1가격에서 역산: `current_price = fair_price / (1 + fair_gap/100)` — 반올림 오차 발생

## 사용자 결정
```
채니봇: "비중에 내가 구한 gap이 중요한거 같은데"
사용자: "T1 이 더 정확하면 그것을 활용"
```

## 전환 내역 (2026-06-08)

| 영역 | Before (midpoint_gap) | After (t1_gap) |
|:----|:---------------------|:---------------|
| Phase 1 정렬 | `midpoint_gap` 역순 | `t1_gap` 역순 |
| Phase 1 필터 | `midpoint_gap >= 30%` | `t1_gap >= 30%` |
| Phase 3 수식 | `보정_gap = midpoint_gap` | `보정_gap = t1_gap` |
| report.py | 중간값+중간괴리율 2줄 | T1 괴리율 1줄 통합 |
| 출력 컬럼 | 중간값/중간괴리율 | T1괴리율 |

## 장점
1. **순수 모델 판단** — Analyst Target의 왜곡/지연 영향 제거
2. **계산 단순화** — midpoint 계산 과정 생략, 오차 누적 감소
3. **일관된 기준** — Target 유무에 관계없이 모든 종목 동일 기준
4. **디버깅 용이** — T1 gap은 fair_value.py에서 직접 계산, 추적 간단

## 단점
1. Analyst Target 정보 활용 안 함 (30일 내 업데이트된 target 무시)
2. T1 적정가 자체가 부정확한 종목(데이터 부족)은 그대로 반영

## 유지보수
- `pipeline.py` Phase 1: `t1_gap`으로 정렬+필터
- `portfolio_allocation.py`: Prompt에 `t1_gap` 수식 포함
- `report.py`: T1 괴리율을 리포트에 직접 표시 (중간값 생략)
- Analyst Target은 리포트 표시용으로만 유지 (비중 결정 미사용)

## 추가 전환 (2026-06-08 v2): t1_gap → t1_gap × moat

Phase 3 비중 수식이 `t1_gap 단독`에서 `t1_gap × moat(LLM 추정)`으로 변경됨:
- `가중값 = max(0, t1_gap) × moat_점수`
- moat 점수는 LLM이 종목 데이터(context_analysis, bull/bear/risk, rationale)를 읽고 1~10 추정
- t1_gap이 여전히 핵심 입력이며 moat은 보조 가중치
- 이유: 사용자 "Gap과 해자만 활용" → "LLM이 추정하기"
- 상한 15%, 하한 2% — 절대 위반 불가
