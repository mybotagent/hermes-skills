# Verified Macro Data Collection Scripts (updated 2026-10-13)

Cron-safe, stdlib-only Python scripts for global macro data collection. All use `write_file` + `terminal()` pattern — no `execute_code`, no pipe-to-interpreter.

## Source Priority (this cron environment, verified 2026-10-13)

| Data | Primary Source | Fallback | Notes |
|:-----|:--------------|:---------|:------|
| Exchange rates (USD/KRW, JPY, EUR) | exchangerate-api.com `v4/latest/USD` | — | Reliable, no auth ✅ |
| S&P 500 | Yahoo Finance `query2` chart API (`^GSPC`) | macro_context.json prior | ✅ |
| KOSPI | Yahoo Finance `query2` chart API (`^KS11`) | macro_context.json prior | ✅ confirmed 6035.35 on 2026-10-13 |
| Nasdaq | Yahoo Finance `query2` chart API (`^IXIC`) | macro_context.json prior | ✅ confirmed 27245.90 on 2026-10-13 |
| 10Y Treasury yield | Yahoo Finance `query2` chart API (`^TNX`) | macro_context.json prior | ⚠️ works but stale sometimes |
| **WTI Crude** | **EIA API `v2/petroleum/pri/spt/`** | Yahoo Finance `CL=F` | **EIA primary — Yahoo `CL=F` returned stale ~$77.6 vs EIA $96.24 (2026-10-13)** |
| DXY | exchangerate-derived estimate | macro_context.json prior | Yahoo `UUP` ETF ≠ DXY; formula gives ~17000 (nonsense). Use "추정" label. |
| Fed Funds Rate | macro_context.json prior | — | FRED times out in cron (30s). Never use FRED as primary. |

> **WTI: EIA primary (2026-10-13 critical fix)** — Yahoo Finance `CL=F` returned stale ~$77.6 while EIA returned fresh $96.24 for 2026-10-06. Always prefer EIA as primary for WTI.
> **DXY**: Yahoo Finance `UUP` ETF price (~28.xx) is NOT the DXY index. The exchangerate-formula `(EUR^-0.576)*(JPY^-0.119)*(GBP^-0.481)*10000` produces ~17000 (nonsense). Label as "추정" and use prior value from macro_context.json.
> **FRED CSV always times out** in this cron environment (30s timeout). Never use as primary or fallback.

## Script 1: Core Macro Data (exchange rates + Yahoo Finance)

File: `/tmp/macro_yf.py`

```python
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = {}

# 1. Exchange rates - exchangerate-api (reliable)
try:
    req = urllib.request.Request(
        'https://api.exchangerate-api.com/v4/latest/USD',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        d = json.loads(r.read())
    results['usdkrw'] = round(d['rates'].get('KRW', 0), 2)
    results['usdjpy'] = round(d['rates'].get('JPY', 0), 2)
    results['eurusd'] = round(d['rates'].get('EUR', 0), 4)
except Exception as e:
    results['exchange_error'] = str(e)

# 2. S&P 500 via Yahoo Finance chart API
try:
    req = urllib.request.Request(
        'https://query2.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=5m&range=1d',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data['chart']['result'][0]['meta']
    results['sp500'] = str(meta.get('regularMarketPrice', 'N/A'))
except Exception as e:
    results['sp500_error'] = str(e)

# 3. US 10Y Treasury via Yahoo Finance
try:
    req = urllib.request.Request(
        'https://query2.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=5m&range=1d',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data['chart']['result'][0]['meta']
    results['us_10yr_yield'] = str(meta.get('regularMarketPrice', 'N/A'))
except Exception as e:
    results['yield_error'] = str(e)

# 4. KOSPI via Yahoo Finance chart API
try:
    req = urllib.request.Request(
        'https://query2.finance.yahoo.com/v8/finance/chart/%5EKS11?interval=5m&range=1d',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data['chart']['result'][0]['meta']
    results['kospi'] = str(meta.get('regularMarketPrice', 'N/A'))
except Exception as e:
    results['kospi_error'] = str(e)

# 5. Nasdaq via Yahoo Finance chart API
try:
    req = urllib.request.Request(
        'https://query2.finance.yahoo.com/v8/finance/chart/%5EIXIC?interval=5m&range=1d',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data['chart']['result'][0]['meta']
    results['nasdaq'] = str(meta.get('regularMarketPrice', 'N/A'))
except Exception as e:
    results['nasdaq_error'] = str(e)

print(json.dumps(results, indent=2))
```

## Script 2: WTI Crude Oil (EIA Primary)

File: `/tmp/wti_eia.py`

```python
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = {}

# WTI via EIA API (primary — verified 2026-10-13: Yahoo returned stale ~$77.6, EIA returned $96.24)
try:
    url = ('https://api.eia.gov/v2/petroleum/pri/spt/data/'
           '?api_key=DEMO_KEY&frequency=daily&data[0]=value'
           '&facets[product][]=EPCWTI'
           '&sort[0][column]=period&sort[0][direction]=desc&length=2')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        d = json.loads(r.read())
    for item in d.get('response', {}).get('data', []):
        results['wti'] = f"${item['value']}"
        results['wti_date'] = item['period']
        break
except Exception as e:
    results['wti_error'] = str(e)

print(json.dumps(results, indent=2))
```

**Fallback: Yahoo Finance `CL=F`** (only if EIA fails):

```python
# WTI via Yahoo Finance crude oil futures (CL=F) — FALLBACK ONLY
try:
    req = urllib.request.Request(
        'https://query2.finance.yahoo.com/v8/finance/chart/CL=F?interval=5m&range=1d',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data['chart']['result'][0]['meta']
    results['wti'] = f"${meta.get('regularMarketPrice', 'N/A')}"
    results['wti_source'] = 'yahoo_fallback'
except Exception as e:
    results['wti_error'] = str(e)
```

## Script 3: Korean Stock News Batch

File: `/tmp/kr_news_collect.py`

```python
import xml.etree.ElementTree as ET
import json
import urllib.request
import urllib.parse
import re
from html import unescape

TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("009150", "삼성전기"),
    ("005380", "현대차"),
    ("352820", "에이피알"),
    ("054050", "HD현대일렉"),
]

def fetch_rss(query, hl="ko", gl="KR", ceid="KR:ko"):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return ET.fromstring(r.read())

results = {}
for code, name in TARGETS:
    queries = [f"{name}+2026년+10월", f"{name}+{code}"]
    seen = set()
    items = []
    for q in queries:
        try:
            root = fetch_rss(q)
            for item in root.findall(".//item")[:8]:
                t_elem = item.find("title")
                t = unescape(t_elem.text) if t_elem is not None and t_elem.text else ""
                t = re.sub(r'\s*-\s*Google\s*뉴스\s*$', '', t)
                if not t or t in seen or "Google 뉴스" in t:
                    continue
                seen.add(t)
                src = item.find("source")
                pub = item.find("pubDate")
                items.append({
                    "title": t,
                    "source": src.text if src is not None else "",
                    "pubDate": pub.text if pub is not None else "",
                })
        except Exception as e:
            pass
    results[code] = {"name": name, "news": items[:4]}

print(json.dumps(results, ensure_ascii=False, indent=2))
```

## Invocation Pattern (cron-safe)

```bash
# Collect exchange rates + US markets + KOSPI + Nasdaq
python3 /tmp/macro_yf.py

# Collect WTI (EIA primary)
python3 /tmp/wti_eia.py

# Collect Korean stock news (all 6 tickers)
# Use delegate_task with tasks=[] for parallel news collection
# or write kr_news_collect.py to /tmp/ and run via terminal()
```

## Known Ticker Codes (verified 2026-10-13)

| Name | Code | Notes |
|:-----|:-----|:------|
| 삼성전자 | 005930 | |
| SK하이닉스 | 000660 | |
| 삼성전기 | 009150 | |
| 현대차 | 005380 | |
| 에이피알 | 352820 | |
| HD현대일렉 | 054050 | Was 267250 before re-listing |

> Always verify ticker codes against user input — KRX codes change, companies re-list.
