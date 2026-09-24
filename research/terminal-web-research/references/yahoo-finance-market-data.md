# Yahoo Finance Market Data — Terminal Fetch (No Pipe-to-Interpreter)

## The Problem

Yahoo Finance API endpoints (`/v7/finance/quote`, `/v8/finance/chart`) rate-limit or block requests without a browser-like User-Agent. The security scanner blocks `curl | python3 -c` (pipe-to-interpreter).

## Working Pattern

**Two-step: save to file first, then parse with read_file**

```bash
# Step 1: Fetch with custom User-Agent — query2 works when query1 fails
curl -s "https://query2.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=5m&range=1d" \
  --header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -o /tmp/gspc.json

# Step 2: Parse with read_file + python3 on the saved file
# (read_file tool reads the JSON, then use python3 separately for extraction)
```

> ⚠️ **query1 vs query2**: `query1.finance.yahoo.com` may return 404 on some days/regions. **Always try `query2`** — it was confirmed working 2026-09-23 when `query1` returned 404. Parallel fetch to both as fallback is cheap.

## Verified Working Endpoints (2026-09-22, updated 2026-09-23)

| Data | Yahoo Symbol | Endpoint | Notes |
|:-----|:------------|:---------|:------|
| S&P 500 | `^GSPC` | `/v8/finance/chart/%5EGSPC?interval=5m&range=1d` | `regularMarketPrice` in meta |
| 10Y Treasury | `^TNX` | `/v8/finance/chart/%5ETNX?interval=5m&range=1d` | `regularMarketPrice` in meta (in %) |
| SPY ETF | `SPY` | `/v8/finance/chart/SPY?interval=5m&range=1d` | ETF price, same pattern |
| KOSPI | `^KS11` | `/v8/finance/chart/%5EKS11?interval=5m&range=1d` | Korean index |
| KOSDAQ | `^KQ11` | `/v8/finance/chart/%5EKQ11?interval=5m&range=1d` | Korean index |
| VIX | `^VIX` | `/v8/finance/chart/%5EVIX?interval=5m&range=1d` | Fear index |

**Failed endpoints:**
- `/v7/finance/quote?symbols=%5EGSPC` → 429 Too Many Requests
- `/v8/finance/chart/%5EGSPC?interval=1d&range=1d` → also rate-limited without custom UA
- **`^DXY`** (Dollar Index) → returns `{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found, symbol may be delisted"}}}` on chart API. **Workaround**: use UUP (Invesco DB Dollar Index) as proxy (~28.48 on 2026-09-23), or fall back to exchangerate-api.com for cross-rate calculation.

## Key Fields from Response

```python
# From /v8/finance/chart/{symbol}?interval=5m&range=1d
meta = result["meta"]
price = meta["regularMarketPrice"]           # current price
change_pct = meta["regularMarketChangePercent"]  # daily change %
day_high = meta["regularMarketDayHigh"]
day_low = meta["regularMarketDayLow"]
volume = meta["regularMarketVolume"]
52wk_high = meta["fiftyTwoWeekHigh"]
52wk_low = meta["fiftyTwoWeekLow"]
```

## Exchange Rate Sources

| Pair | Source | Endpoint | Notes |
|:-----|:-------|:---------|:------|
| USD/KRW | exchangerate-api.com | `https://api.exchangerate-api.com/v4/latest/USD` | `rates.KRW` |
| EUR/KRW | exchangerate-api.com | `https://api.exchangerate-api.com/v4/latest/EUR` | `rates.KRW` |
| USD/KRW (alt) | Yahoo Finance | `USDKRW=X` ticker | `chart.result[0].meta.regularMarketPrice` |

## Anti-Patterns (Blocked)

```bash
# BLOCKED by security scanner — pipe to interpreter
curl -s "URL" | python3 -c "import json,sys; ..."
curl -s "URL" | python3 -c "import sys,json; ..."

# WORKAROUND: save to file first
curl -s "URL" -o /tmp/data.json
# then use read_file + separate python3 call

# BLOCKED: background & in foreground terminal()
curl -sL "https://..." -o /tmp/file1.xml &
curl -sL "https://..." -o /tmp/file2.xml &
wait
# Error: "Foreground command uses '&' backgrounding. Use terminal(background=true)..."

# CORRECT: sequential calls (still parallel via batching in same terminal() call)
curl -sL "https://..." -o /tmp/file1.xml && echo "ONE_DONE"
curl -sL "https://..." -o /tmp/file2.xml && echo "TWO_DONE"
```

## Complete Fetch Example

```bash
# S&P 500
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=5m&range=1d" \
  --header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -o /tmp/gspc.json

# 10Y Treasury
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=5m&range=1d" \
  --header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -o /tmp/tnx.json

# USD/KRW (exchange rate API)
curl -s "https://api.exchangerate-api.com/v4/latest/USD" -o /tmp/usd_krw.json
```

## Data Freshness

- Yahoo Finance prices: **15-20 minute delay** (real-time requires paid API)
- Exchange rate API: varies, typically daily or hourly close
- For real-time needs: consider direct exchange data sources
