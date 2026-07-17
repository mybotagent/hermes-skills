# Moat 점수 LLM 추정 루브릭 (2026-07-17 v3 — Multi-Factor Quality Scoring)

**변경 이력**: 
- v1 (2026-06-06): stock-rating-system 스킬의 Moat 가중치 35% 기반 점수
- v2 (2026-06-08): 사용자 "Gap과 해자만 활용" + "LLM이 추정하기" → 단일 moat 1~10 점수
- **v3 (2026-07-17)**: tradingAgents 영감 — **5개 Quality Factor** 종합 점수로 moat 도출

## 개요

기존 단일 moat 점수(1~10)는 평가 차원이 부족해 엔비디아 12.6% 최대 비중에도 기여도 -0.04% 같은 문제 발생.
tradingAgents의 Evidence-backed Quality Scoring을 차용하여 5개 항목 종합 평가로 업그레이드.

## 평가 항목 (각 0~100점)

| # | 항목 | 가중치 | 평가 내용 |
|:-:|:-----|:-----:|:---------|
| ① | **Reliability** (신뢰도) | 25% | 출처 품질(Tier A/B/C), 데이터 신선도(7일 이내?), 정보 일관성 |
| ② | **Economic Moat** (해자) | 25% | 특허·독점, 네트워크효과, 전환비용, 브랜드파워, 규제장벽 |
| ③ | **Structural Stability** (구조적 안정성) | 15% | 부채비율, 영업현금흐름, 시장지위 변동성 |
| ④ | **Growth Quality** (성장 질) | 20% | 매출 성장 지속성, ROE 추세, 이익률 방향성 |
| ⑤ | **Risk-Adjusted** (리스크 대비) | 15% | 변동성, 경쟁 리스크, 규제 리스크, 지정학 리스크 |

```
종합_점수 = ①×0.25 + ②×0.25 + ③×0.15 + ④×0.20 + ⑤×0.15
```

## 종합 점수 → Moat 점수 변환

| 종합 점수 | 등급 | Moat 점수 | 의미 |
|:--------:|:----|:---------:|:-----|
| 85~100 | durable_compounder | 9~10 | 독점적 지위 (MSFT, GOOGL) |
| 70~84 | high_quality | 7~8 | 강한 시장지위 (NVDA, AVGO — 2026-07-17 하향) |
| 55~69 | constructive | 5~6 | 차별화 보통 |
| 40~54 | fragile | 3~4 | 차별화 약함, 경쟁 심함 |
| 0~39 | low_conviction | 1~2 | 진입장벽 없음, 적자 |

## LLM 추정 방식

Phase 3 (`portfolio_allocation.py`)에서:
1. `build_stock_summary()` → LangGraph 결과를 LLM 요약
2. Phase 3 프롬프트에서 5개 항목 평가
3. 종합 점수 계산 → moat 점수 변환
4. `quality_scores` 객체에 각 항목 점수 + composite + grade 저장

## 실행 결과 예시 (v3 기대)

| 종목 | 신뢰도 | 해자 | 안정성 | 성장 | 리스크 | 종합 | 등급 | moat |
|:-----|:----:|:---:|:-----:|:---:|:----:|:---:|:----:|:----:|
| MSFT | 95 | 95 | 90 | 85 | 85 | 91 | durable | 10 |
| NVDA | 80 | 85 | 70 | 75 | 65 | **77** | high_quality | **8** |
| AVGO | 75 | 80 | 65 | 70 | 60 | **71** | high_quality | **8** |
| SK하이닉스 | 70 | 75 | 65 | 80 | 60 | 71 | high_quality | 8 |
| 삼성전자 | 70 | 70 | 70 | 60 | 65 | 67 | constructive | 6 |
| HPE | 60 | 45 | 55 | 50 | 55 | 52 | fragile | **4** |
| LG이노텍 | 50 | 35 | 45 | 40 | 45 | 42 | fragile | **3** |

## 수식

```
가중값 = max(0, t1_gap) × moat_점수
기본_비중 = (가중값 / 총_가중값) × (100% - 현금비중)
```

## Bear/Base/Bull 시나리오 (2026-07-17 신규)

각 종목의 6개월 전망:
```
Bull (낙관):    상방 케이스 목표가 + 확률 (%)
Base (기준):    가장 가능성 높은 케이스 + 확률 (%)
Bear (비관):    하방 케이스 목표가 + 확률 (%)
(확률 합계 = 100%)
return/risk ratio = weighted_upside / weighted_downside_risk
```

## 주의사항

- 5개 항목 점수는 LLM 판단이므로 실행마다 편차 발생 가능
- Reliability 항목은 출처 정보가 불충분하면 보수적으로 평가 (50점 이하)
- Risk-Adjusted 항목에서 엔비디아 등 고변동성 종목은 감점
- 저승률 종목(승률<30%)은 moat 점수를 자동 1~2점 하향
- 15% 상한 절대 불가 — 초과 시 무조건 15%로 재분배
