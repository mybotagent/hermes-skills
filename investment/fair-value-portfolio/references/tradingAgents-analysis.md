# tradingAgents — Strategy Enhancement Analysis

> 검토일: 2026-07-17
> 출처: https://github.com/sh-ai-x/tradingAgents
> 비교 대상: 현재 fair-value-portfolio 시스템

## 1. Evidence Tier System (출처 계층)

tradingAgents는 모든 출처를 **Tier A/B/C**로 분류하고 **7일 신선도**를 강제:

| Tier | 기준 | 예시 |
|:----:|:-----|:-----|
| A | SEC filing, 정부 발표, 기업 IR | SEC EDGAR, Naver 공시 |
| B | 신뢰할 수 있는 2차 출처 | yfinance, Finnhub, analyst upgrade |
| C | 블로그, 뉴스, 커뮤니티 | 일반 기사, Seeking Alpha |

**핵심 규칙**:
- Tier-A 간 10%↑ disagreement → **평균 금지**, bracket 표시
- 7일 초과 source → drop (Tier-A도 advisory로만)
- 결측은 "not found"로 보고, 절대 추정 금지

**우리 적용 방안**: LLM 추정값(gap×moat)을 Tier C로 명시. SEC/Naver filing 기반 데이터만 Tier A.

## 2. Quality Factor Scoring (정성 평가 체계화)

tradingAgents는 5가지 Quality Factor를 **0~100 점수 + 등급**:

| Factor | Weight | 평가 내용 |
|:-------|:------:|:----------|
| Reliability | 25 | 출처 품질, 독립성, 신선도, 일관성 |
| Economic Moat | 20 | 해자 요소 (우리의 moat 점수와 동일) |
| Structural Stability | 20 | 재무 구조, 부채, 현금흐름 안정성 |
| Growth Quality | 20 | 성장의 질(일회성 vs 구조적) |
| Risk-Adjusted | 15 | 리스크 대비 수익 잠재력 |

**등급 체계**: durable_compounder(85+) / high_quality_cyclical(70-84) / constructive_but_volatile(55-69) / fragile_opportunity(40-54) / low_conviction(0-39)

**우리 적용 방안**: 현재 `moat 1~10` 단일 점수를 **5-factor 종합 점수**로 확장. 각 factor에 LLM reasoning trace + cited_evidence 포함.

## 3. Bear/Base/Bull Scenario (시나리오 기반 전망)

tradingAgents는 6개월 전망을 **3개 시나리오 + 확률(합=1.0)**:
```json
{
  "bear": {"price": 80, "prob": 0.2},
  "base": {"price": 110, "prob": 0.5},
  "bull": {"price": 150, "prob": 0.3}
}
```

**Return/Risk ratio** = probability-weighted upside / probability-weighted downside

**우리 적용 방안**: T1 단일 적정가 대신 시나리오별 목표가 + 확률을 LLM이 추정. return/risk ratio로 비중 결정에 활용.

## 4. Research Guidance (행동 레이블)

BUY/HOLD/SELL 대신 **다음 조사 행동**을 제안:
- `prioritize_deeper_due_diligence`
- `watch_for_pullback_or_confirmation`
- `monitor_key_risk_before_action`
- `avoid_new_commitment_until_evidence_improves`

**우리 적용 방안**: BUY/SELL 결정에 **research confidence** 레이블 병기. "BUY (high confidence, evidence: 7일 내 SEC filing)"

## 5. Doctor Validation (자체 검증)

실행 후 bundle을 **schema/coverage/일관성** 감사:
- Schema 검증, citation 형식, tier 검사
- 완료/부분/중단 → 상태를 **투명하게 보고**
- Deep doctor: cross-output 일관성

**우리 적용 방안**: pipeline.py 마지막 Phase 4로 doctor 추가.

## 6. 적용 우선순위 제안

| 순위 | 항목 | 난이도 | 기대효과 |
|:----:|:-----|:-----:|:-------:|
| 1 | Bear/Base/Bull 시나리오 + 확률 | 중 | 상 |
| 2 | Return/Risk ratio 계산 | 중 | 상 |
| 3 | Moat 점수 다차원화 (0-100, 5 factor) | 하 | 중 |
| 4 | Doctor 검증 Phase 4 | 하 | 중 |
| 5 | 출처 Tier 표시 + 신선도 검증 | 중 | 중 |
| 6 | Research confidence 레이블 | 하 | 중 |

> 1+2번만 도입해도 S&P 500 대비 언더퍼폼 원인을 사전 감지 가능.
> 예: "NVDA bear scenario 확률 40% → return/risk ratio 0.8x → 비중 축소"
