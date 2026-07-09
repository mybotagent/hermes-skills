# Sector Mapping Audit (2026-06-18)

## Trigger
사용자가 BWXT의 적정PER가 비현실적으로 낮다고 지적 → 조사 결과 Industrial(15) → Technology(22)로 재분류.
이후 전 종목에 대해 watchlist sector vs yfinance sector systematic audit 수행.

## Methodology

### Step 1: Collect yfinance sector for all stocks
```python
import yfinance as yf, json

wl = json.load(open('data/watchlist.json'))
for s in wl['stocks']:
    info = yf.Ticker(s['ticker']).info
    s['yf_sector'] = info.get('sector', 'N/A')
    s['yf_de'] = info.get('debtToEquity')
    s['yf_roe'] = info.get('returnOnEquity')
    s['yf_target'] = info.get('targetMeanPrice')
```

### Step 2: Compare with watchlist sector
For each stock, check if `sector` in watchlist matches the sector the code actually uses:
```python
code_sector = TICKER_SECTOR.get(ticker, yf_sector)
```

### Step 3: Filter by practical impact
Ask: would changing the sector base change the fair PER enough to matter?
- If cyclical cap (FPE<12) overrides the base → no impact
- If 35 cap overrides → no impact  
- If base difference is small (1~2) → minor
- Only fix when base difference ≥ 3 AND no cap overrides

### Step 4: Add TICKER_SECTOR override
Only fix via `TICKER_SECTOR` dict in `fair_value.py`. Never change SECTOR_BASE values.

## Results

### Fixed (3 TICKER_SECTOR overrides added)

| Ticker | Watchlist Sector | yfinance Sector | New Override | Impact |
|--------|:---------------:|:--------------:|:-----------:|:------:|
| BWXT | Industrial (15) | Industrials (15) | **Technology (22)** | 적정PER 21.6→28.6, T1 gap -50.8%→-37.4% |
| MSFT | Software (25) | Technology (22) | **Software (25)** | 적정PER 29.1→32.1, T1 gap +27.5%→+38.9%, analyst 오차 -10.6%→-2.5% |
| 005380.KS (현대차) | Auto (7) | Consumer Cyclical (15) | **Auto (7)** | 적정PER 14.4→6.4, T1 gap +3.1%→-45.0% |

### Skipped (cap overrides, no practical difference)

| Ticker | Watchlist | yfinance | Reason Skipped |
|--------|:--------:|:--------:|:-------------|
| MU | Semiconductors (18) | Technology (22) | US cyclical cap 20 overrides |
| TSM | Semiconductors (18) | Technology (22) | 35 cap reached either way |
| 000660.KS (SK하이닉스) | Semiconductors (18) | Technology (22) | KR cyclical cap 11 overrides |
| 278470.KQ (에이피알) | Consumer Cyclical (15) | N/A→fallback 15 | Same base either way |

### Current TICKER_SECTOR (2026-06-18)
```python
TICKER_SECTOR = {
    'AVGO': 'AI Infrastructure',
    'NVDA': 'AI Infrastructure',
    'LITE': 'Optical Communications',
    'AAPL': 'Consumer Electronics Premium',
    'AMD': 'CPU/GPU',
    'INTC': 'CPU/GPU',
    'LRCX': 'Semiconductor Equipment',
    'TER': 'Semiconductor Equipment',
    'HPE': 'Hardware',
    'BWXT': 'Technology',
    'MSFT': 'Software',
    '005380.KS': 'Auto',
    '009150.KS': 'MLCC',
}
```

## Key Lesson
When a stock's T1 gap looks wrong or analyst-model discrepancy is abnormally large:
1. First check if yfinance sector matches the intended sector
2. Check D/E penalty, ROE premium, growth premium individually
3. Only then consider adding conditional caps
4. Always fix via TICKER_SECTOR, never change SECTOR_BASE
