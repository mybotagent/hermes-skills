# Macro Strategy v2 Evaluation (2026-07-17)

## v1 (Original) → Overfitting Analysis

v1 strategy provided by user's Python code. Backtest results (1995~2026, 379 months):

| Metric | SPY | Strategy v1 | Assessment |
|:-------|:---:|:-----------:|:-----------|
| CAGR | 11.1% | 14.7% | +3.6%p — plausible |
| MDD | -50.8% | -19.4% | **2.6x improvement — SUSPICIOUS** |
| Sharpe | 0.78 | 1.17 | +0.39 — high but not impossible |

### Red Flags Identified

1. **CPI hard cutoffs (3.0%, 5.0%)**: No economic reason these exact values work for 30 years
2. **WTI $80 threshold**: Specific to 2022 oil spike
3. **12 allocation paths**: SPY 70%+GLD 30% vs XLE 60%+DXY 40% — too many parameters
4. **2008/2020/2022 perfect avoidance**: MA10 crossover timing too precise

## v2 (Improved) — Risk Score Approach

### Changes

| Component | v1 (removed) | v2 (current) |
|:----------|:-------------|:-------------|
| CPI regime | 3%/5% hard boundary | Risk Score (0~100 continuous) |
| Weights | none | CPI 35% + Sahm 25% + HY 25% + VIX 15% |
| Allocation | 12 discrete cases | 5-tier glide (continuous) |
| Alpha-Flip | MA10 + WTI $80 | Risk Score > 50 OR (5MA↓ + VIX>25) |
| Fee | 0.15% | 0% (no switching cost) |

### Risk Score Formula

```python
CPI_z = (CPI_YoY - 10yr_rolling_mean) / 10yr_rolling_std
Sahm_Score = min(Sahm_Rule, 1.0) * 100
HY_Score = min(max((HY_Spread - 3) / 5, 0), 1) * 100
VIX_Score = min(max((VIX - 15) / 20, 0), 1) * 100

Risk_Score = CPI_z * 0.35 + Sahm_Score * 0.25 + HY_Score * 0.25 + VIX_Score * 0.15
```

### Glide Allocation

| Risk Score | Allocation | Label |
|:----------:|:-----------|:------|
| 0~20 | SPY 100% | 공격 |
| 20~40 | SPY 70~100% + TLT 0~20% + GLD 0~10% | 안정 |
| 40~60 | SPY 40~70% + TLT 20% + GLD 10~20% + DXY 0~20% | 중립 |
| 60~80 | TLT 20~40% + DXY 30% + GLD 20% + SPY 0~10% + CASH 0~20% | 방어 |
| 80~100 | DXY 40% + GLD 30% + CASH 30% | 초방어 |

### Results (1995~2026)

| Metric | SPY | v2 | Meaning |
|:-------|:---:|:--:|:--------|
| CAGR | 11.1% | 12.0% | +0.9%p — modest but real |
| MDD | -50.8% | -44.7% | -6.1%p — realistic improvement |
| Sharpe | 0.78 | 0.92 | +0.14 — better risk-adjusted |

**v2 intentionally trades higher MDD (-44.7% vs -19.4%) for realistic out-of-sample behavior.**

## Pipeline Design (Deterministic)

```
paper_tracker.py → CSV/JSON (portfolio performance)
generate_macro_dashboard.py → JSON + CSV (macro data + recommendation)
generate_macro_plots.py → PNG (matplotlib charts)
compute_portfolio_target.py → JSON (macro rec → holdings mapping)
    ↓
paper_tracker_daily.sh (no_agent cron) → git push → Vercel auto-deploy
```

**Rule**: No LLM in data pipeline. All scripts are deterministic Python.
**Dashboard**: Static HTML reads JSON/CSV/PNG files at load time.
**Vercel**: GitHub push triggers auto-deploy. API-based deploy has SSO issues.

## Current Status (2026-07-01)

| Field | Value |
|:------|:------|
| Regime | Goldilocks |
| Risk Score | 3.0/100 |
| Signal | 상승장 (Risk-On) |
| Recommendation | SPY 100% |
| CPI YoY | 3.2% |
| Sahm Rule | 0.07 |
| Fed Rate | 3.6% |
| WTI | $78.9 |
| VIX | 16.7 |
| Fear & Greed | Neutral (50) |

All risk indicators are benign. Strategy recommends full equity allocation.
