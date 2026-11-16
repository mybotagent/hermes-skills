# Consensus Collection — tradingAgents Multi-Source Architecture

> Applied 2026-07-17. Source inspiration: `sh-ai-x/tradingAgents` (tier system + recency + conflict + multi-source synthesis).

## Architecture

```python
raw = SourceRegistry.fetch_all(ticker)   # 모든 source 독립적 fetch
stock = synthesize(name, raw)             # tier-weight + conflict + confidence
```

## Source Registry Pattern

`@SourceRegistry.register(name, tier, desc)` 데코레이터로 새 소스 추가:

```python
@SourceRegistry.register("yfinance", "B", "Yahoo Finance (Refinitiv consensus)")
def src_yfinance(ticker, name, today): ...

@SourceRegistry.register("fdr", "B", "FinanceDataReader (KRX price)")
def src_fdr(ticker, name, today): ...

@SourceRegistry.register("finnhub", "B", "Finnhub recommendation trends")
def src_finnhub(ticker, name, today): ...
```

새 소스 추가: `@SourceRegistry.register("fmp", "A", "Financial Modeling Prep")` + fetch 함수만 작성.

## Data Sources & Tiers (Current)

| Source | Tier | Provides | Notes |
|--------|:----:|----------|-------|
| `yfinance.earnings_estimate` | B | EPS avg/low/high/growth/n_analysts 4개 기간 | 모든 종목 |
| `yfinance.revenue_estimate` | B | Revenue avg/low/high/growth 4개 기간 | 모든 종목 |
| `yfinance.info` | B | Target price, forward PE, PEG, recommendation | 모든 종목 |
| `yfinance.calendar` | B | Next earnings date + EPS/rev estimate range | 모든 종목 |
| `FinanceDataReader` | B | 한국주 현재가 (5일 fallback) | `.KS`/`.KQ` 티커 |
| `finnhub.recommendation_trends` | B | 추천 breakdown 보강 | Free tier 제한적 |

### FDR Weekend Fallback (2026-07-17 fix)

```python
for offset in [0, 1, 2, 3, 4]:
    d = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
    df = fdr.DataReader(code, d, d)
    if not df.empty and float(df["Close"].iloc[-1]) > 0:
        return {"price": ..., "source_detail": f"KRX:{code} asof {d}"}
```

## Output Schema (per stock)

```json
{
  "sources": ["yfinance(eps)", "yfinance(rev)", "FinanceDataReader(price)"],
  "source_details": {
    "yfinance": {"tier": "B", "weight": 1.0},
    "fdr": {"tier": "B", "weight": 1.0}
  },
  "forward_estimates": {
    "eps": {
      "tier": "B", "confidence": "high", "n_analysts": 31,
      "periods": {
        "upcoming_quarter": {"avg": "31.33", "growth": "933.96%"},
        "next_quarter": {"avg": "34.87"},
        "current_fy": {"avg": "73.37"},
        "next_fy": {"avg": "150.47"}
      }
    },
    "revenue": {"tier": "B", "periods": {}},
    "target": {"mean": "1,489.57", "upside": "74.6%", "tier": "B"},
    "recommendation": {"label": "Strong Buy", "score": "1.42", "color": "#5db872"},
    "valuation": {"current_price": "853.20", "forward_pe": "5.67"},
    "next_earnings": {"date": "2026-09-24", "is_future": true, "days_until": 69},
    "confidence": {
      "level": "high", "tier": "B (Aggregator)",
      "n_analysts_avg": 36, "total_sources": 3
    }
  }
}
```

**모든 데이터는 `forward_estimates` 아래**. `periods` 키 = `upcoming_quarter` / `next_quarter` / `current_fy` / `next_fy`.

## Confidence Model (tier-first)

```
Confidence = Tier_Base + Analyst_Mod + Source_Mod + Recency_Mod
```

| 요소 | 가중치 | 기준 (Tier-B) |
|:-----|:------:|:--------------|
| **Tier Base** | ⭐ 기본 | B=1.0, A=3.0, C=0.0 |
| **Analyst count** (보조) | +0.3 | ≥30명 |
| | +0.15 | ≥15명 |
| | 0 | ≥5명 |
| | -0.2 | <5명 |
| **Multi-source** (2+) | +0.1 | 2 sources 이상 |
| **Recency stale** | -0.2 | 14일 초과 |
| **High threshold** | ≥ 1.4 | 🔵 high |
| **Medium threshold** | ≥ 0.8 | 🟡 medium |

### Examples (2026-07-17)

| Stock | Analysts | Sources | Score | Level | Reasoning |
|:------|:--------:|:-------:|:-----:|:------|:----------|
| 삼성전자 | 33명 | **2** | 1.4 | 🔵 high | tier-B + 2 sources = multi-source bonus |
| 마이크론 | 36명 | 1 | 1.3 | 🟡 medium | single source cap |
| 엔비디아 | 50명 | 1 | 1.3 | 🟡 medium | single source limit |
| LG이노텍 | 25명 | **2** | 1.25 | 🟡 medium | 2 sources but analyst <30 |

## Forward-Only Guarantee

- `0q` = upcoming fiscal quarter (모두 미래, next earnings date 기준)
- `+1q` = 차기분기
- `0y` = 금년도
- `+1y` = 내년도
- **trailingEps** = 컨세서스 미포함 (참고용만)
- `is_future` 플래그로 검증

## Pipeline Position

```bash
collect_consensus.py  # step 4 of 9 in paper_tracker_daily.sh
```

## Pitfalls

- **한국주 EPS 분석가 수 적음** (7~9명) → 구조적 한계
- **Finnhub**: free tier = recommendation_trends only (EPS/Rev 403)
- **Dashboard 접근**: `forward_estimates.eps.periods.upcoming_quarter.avg` 구조
