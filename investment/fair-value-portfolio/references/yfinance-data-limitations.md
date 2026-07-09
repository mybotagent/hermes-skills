# yfinance 데이터 한계

## 지연 시간
yfinance는 **실시간 데이터를 제공하지 않는다.** Yahoo Finance 무료 사용자는 15~20분 지연된 데이터를 받는다. 실시간 데이터는 Yahoo Finance Premium(유료)에서만 가능.

| 데이터 종류 | 실제 지연 | Freshness Check 기준 |
|:----------|:--------:|:-------------------:|
| 현재가 (regularMarketPrice) | **15~20분** | 30분 (5분→30분 조정) |
| 일봉 (close, 마감가) | **지연 없음** (장 마감 후 확정) | 24시간 |
| PER / FPE / PBR | **분기 단위 갱신** | 24시간 |
| ROE / EPS | **분기 단위 갱신** | 24시간 |

## Analyst Target
yfinance `targetMeanPrice`는 consensus 평균으로 weeks~months stale. **절대 단독 사용 금지.**

| 문제 | 설명 |
|:----|:------|
| **Consensus 평균** | 수십 개 Analyst의 평균 = 개별 최신 정보가 아님 |
| **Stale 데이터** | weeks~months 구닥다리 평균 |
| **대안** | `upgrades_downgrades` 30일 window 최신 target 사용 (cron 08:00 수집) |

## 가치투자 영향
가치투자(월 2~4회 거래)에게 20분 지연은 **무시할 수준.** 하루 단위로 판단하는 투자 스타일에는 전혀 영향 없음.

**참조**: `references/latest-analyst-targets.md`
