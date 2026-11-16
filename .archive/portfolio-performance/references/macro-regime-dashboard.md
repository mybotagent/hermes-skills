# Macro Regime Dashboard Reference

## Overview

The `generate_macro_dashboard.py` (v2) script implements a **continuous Risk Score (0~100)** based macro strategy, replacing the original hard CPI-cutoff regime classification. The `generate_macro_plots.py` script generates matplotlib PNG images for dashboard display.

## Risk Score (0~100) — v2 Core

| Component | Weight | Calculation |
|:----------|:------:|:------------|
| CPI z-score (10yr rolling) | 35% | `clip((CPI - mean_120m) / std_120m, 0, 3) / 3 * 100` |
| Sahm Rule | 25% | `clip(Sahm, 0, 1.0) * 100` |
| HY Spread | 25% | `clip((HY - 3) / 5, 0, 1) * 100` |
| VIX | 15% | `clip((VIX - 15) / 20, 0, 1) * 100` |

**Formula**: `Risk_Score = CPI_z_score * 0.35 + Sahm_Score * 0.25 + HY_Score * 0.25 + VIX_Score * 0.15`

### Display Regimes (from Risk Score)

| Regime | Risk Score | Color |
|:-------|:----------:|:------|
| Goldilocks | 0~15 | rgba(93,184,114,.25) |
| Slowdown | 15~30 | rgba(108,106,100,.20) |
| Overheat | 30~50 | rgba(212,160,23,.25) |
| Stagflation | 50~65 | rgba(198,69,69,.25) |
| Severe_Inflation | 65~80 | rgba(220,80,140,.20) |
| Deflation | 80~100 | rgba(74,143,224,.20) |

These are **display only** — actual allocation uses the continuous Risk Score.

## Glide Allocation (Continuous)

```python
def glide_allocation(risk):
    if risk < 20:    return {'SPY': 1.0}
    elif risk < 40:  return {'SPY': 0.7-0.3w, 'TLT': 0.2w, 'GLD': 0.1w}
    elif risk < 60:  return {'SPY': 0.4-0.3w, 'TLT': 0.2, 'GLD': 0.1+0.1w, 'DXY': 0.2w}
    elif risk < 80:  return {'TLT': 0.4-0.2w, 'DXY': 0.3, 'GLD': 0.2, 'SPY': 0.1-0.1w, 'CASH': 0.2w}
    else:            return {'DXY': 0.4, 'GLD': 0.3, 'CASH': 0.3}
```

No fees (dynamic allocation absorbs transitions naturally).

## Signal (Risk-On / Risk-Off)

Signal = 1 (Risk-Off) when:
- Risk Score > 50 (severe conditions), OR
- SPY < 5-month MA AND VIX > 25 (tactical break)

## Output Files

| File | Script | Usage |
|:-----|:-------|:------|
| `macro_dashboard_data.json` | `generate_macro_dashboard.py` | Status panel + recommendation |
| `macro_regime_history.csv` | `generate_macro_dashboard.py` | Monthly time series |
| `macro_plots/plot_N.png` | `generate_macro_plots.py` | Matplotlib PNG images (8 panels) |
| `macro_plots/full.png` | `generate_macro_plots.py` | Combined 8-panel figure |

## Matplotlib PNG Rules

**Rule**: Complex multi-panel visualizations (log scale, regime background segments, twin axes, hatching) -> ALWAYS use matplotlib PNG, never Chart.js.

### Dashboard HTML pattern:
```html
<img src="macro_plots/plot_0.png" style="width:100%;height:auto;border-radius:8px" loading="lazy">
```

### Matplotlib setup required:
```python
import matplotlib
matplotlib.use('Agg')  # MUST be before pyplot import
import matplotlib.pyplot as plt
fig.patch.set_facecolor('#faf9f5')  # cream canvas
plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#faf9f5')
```

## Strategy Recommendation Display

Recommendation computed in `generate_macro_dashboard.py`, stored in `macro_dashboard_data.json.recommendation`.

Dashboard JS: read `mj.recommendation`, render asset badges with color-coded pills. Insert after `#macroSection` via `insertAdjacentHTML('afterend', html)`.

### Asset color mapping:
| Asset | Color |
|:------|:------|
| SPY | #cc785c (coral) |
| GLD | #d4a017 (gold) |
| TLT | #5db872 (green) |
| DXY | #a09d96 (gray) |
| CASH | #4a8fe0 (blue) |

## v1 Strategy (Deprecated — replaced by v2)

Original used: hard CPI cutoffs (3%/5%) + WTI $80 threshold + MA(10) crossover + 12 allocation buckets.
v2 improvement: CAGR 12.0% vs SPY 11.1%, MDD -44.7% vs -50.8%, Sharpe 0.92 vs 0.78.

## Gotchas

1. **Date resolution**: CSV=MONTHLY, portfolio=DAILY. Use pfLookup mapping.
2. **Hex->rgba**: NEVER dynamically replace. Hardcode values.
3. **Two JSON files**: `macro_dashboard_data.json` (dashboard reads this) != `macro_plots_status.json`. Add recommendation to BOTH or only to `macro_dashboard_data.json`.
4. **Duplicate strategy logic**: `generate_macro_dashboard.py` and `generate_macro_plots.py` must have identical regime/allocation/signal logic. Simplicity over DRY.
5. **'}</catch' bug**: Patching catch blocks can corrupt syntax. Verify with parens/braces count after each patch.
6. **beforeDraw guard**: Always check `if (!chartArea) return;` — can be null during resize.
7. **CNN API**: Sometimes 403. Always have VIX fallback ready.
