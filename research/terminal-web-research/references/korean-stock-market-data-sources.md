# Korean Stock Market Data Sources (2026-10-08)

## Verified Working: Naver Finance siseJson API

**Endpoint**: `https://api.finance.naver.com/siseJson.naver`

Individual Korean stocks return **daily OHLCV data** (open/high/low/close/volume) with foreign ownership ratio:

```
GET ?symbol=005930&requestType=1&startTime=20261001&endTime=20261008&timeframe=day
→ [["날짜","시가","고가","저가","종가","거래량","외국인소진율"],
   ["20261001", 266500, 276000, 264500, 274500, 13741073, 46.41],
   ["20261002", 273500, 277000, 271500, 276000, 11501250, 46.41], ...]
```

**KOSPI index** (`symbol=001`): Returns garbled/numeric-salvageable data — NOT the index value. **Use Yahoo Finance `^KS11` chart API** for KOSPI index (but note: Yahoo Finance KOSPI returns 429 Too Many Requests frequently).

**KOSPI constituent stocks** (verified working 2026-10-08):
| Code | Name | Example |
|------|------|---------|
| 005930 | 삼성전자 | `symbol=005930` |
| 000660 | SK하이닉스 | `symbol=000660` |
| 009150 | 삼성전기 | `symbol=009150` |
| 005380 | 현대차 | `symbol=005380` |
| 352820 | 에이피알 | `symbol=352820` |
| 054050 | HD현대일렉 | `symbol=054050` |

**Python usage** (cron-safe — no pipe-to-interpreter):
```python
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

code = '005930'
url = f'https://api.finance.naver.com/siseJson.naver?symbol={code}&requestType=1&startTime=20261001&endTime=20261008&timeframe=day'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
    raw = r.read().decode('utf-8', errors='ignore')
data = json.loads(raw.replace('\n','').replace('\t',''))
for row in data[1:]:
    date, open_, high, low, close, volume, foreign_ratio = row
    print(f'{date}: close={close}')
```

## Sources That DON'T Work for Korean Stocks (2026-10-08 confirmed)

| Source | Attempt | Result |
|--------|---------|--------|
| Yahoo Finance `^KS11` chart API | `query1/2.finance.yahoo.com/v8/finance/chart/%5EKS11` | **HTTP 429** Too Many Requests |
| Naver Finance KOSPI index | `symbol=001` | Garbled numeric-salvageable, not actual index value |
| CNBC KOSPI quote | `cnbc.com/quotes/KOSPI` | **HTTP 404** Not Found |
| Investing.com Korea | `kr.investing.com/equities/...` | **HTTP 403** Forbidden |
| Naver News (finance.naver.com) | `item/news.naver?code=XXXXX` | **JS-rendered**, no news items in curl |

## Global Macro Data Sources (Verified)

| Indicator | Source | URL | Notes |
|-----------|--------|-----|-------|
| **S&P 500** | CNBC quote | `cnbc.com/quotes/SPX` | Returns `regularMarketPrice` in page HTML |
| **Nasdaq Composite** | NASDAQ API | `api.nasdaq.com/api/quote/COMP/info?assetclass=index` | Returns JSON with `lastSalePrice`, `netChange`, `percentageChange` |
| **USD/KRW, USD/JPY, EUR** | exchangerate-api | `open.er-api.com/v6/latest/USD` | Reliable, returns all rates in one call |
| **USD/KRW** (backup) | exchangerate-api | `api.exchangerate-api.com/v4/latest/USD` | Also works |
| **DXY approximation** | Via EUR rate | `open.er-api.com/v6/latest/EUR` | DXY ≈ 1/EUR × 100 |
| **Gold** | CNBC | `cnbc.com/quotes/XAUUSD` | **HTTP 404** — try metal specific symbols |
| **WTI Crude** | CNBC | `cnbc.com/quotes/WTIC` | **HTTP 404** — commodities page has WTI in meta keywords but not parseable |
| **WTI Crude (backup)** | EIA API | `api.eia.gov/v2/petroleum/pri/spt/data/` | **HTTP 401** without API key; `DEMO_KEY` returns 404 |
| **10Y US Treasury** | FRED | `fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10` | **HTTP timeout** — FRED is unreliable from this environment |
| **VIX** | CNBC | `cnbc.com/quotes/VIX` | Returns 404; try `^VIX` via Yahoo Finance |

## Google News RSS for Korean Stock News (Working Pattern)

Google News RSS returns items with dates for Korean queries, but **titles may be stripped** in the `<title>` CDATA field — the title appears only inside `<description>` HTML. Workaround: parse `description` field, extract title from the anchor tag inside it.

**Verified working (2026-10-08)** — description contains real headline:
```
<description>
  <a href="...">SK하이닉스, 솔리다임 美상장 주관은행 선정</a>&nbsp;&nbsp;<font color="#6f6f6f">서울경제</font>
</description>
```

**Extraction pattern** (Python):
```python
import re
for item in root.findall('.//item'):
    desc = item.find('description')
    if desc is not None and desc.text:
        # Extract title from <a href="...">HEADLINE</a>
        m = re.search(r'<a[^>]+>([^<]+)</a>', desc.text)
        title = m.group(1) if m else ''
        # Source from <font color="#6f6f6f">SOURCE</font>
        src_m = re.search(r'color="#6f6f6f">([^<]+)</font>', desc.text)
        source = src_m.group(1) if src_m else ''
```

## Lessons from 2026-10-08 Session

1. **Yahoo Finance Korean stocks/indices all return HTTP 429** — rate limiting is aggressive. Do not rely on Yahoo Finance for Korean market data.
2. **Naver Finance siseJson API is the reliable source** for individual Korean stock OHLCV. Use this as primary.
3. **FRED is completely inaccessible** (timeout) from this environment — 10Y Treasury, WTI, DXY, VIX all fail via FRED.
4. **CNBC works for S&P500 and Nasdaq index**, but not for WTI, DXY, or 10Y Treasury directly.
5. **exchange-rate APIs (er-api.com, exchangerate-api.com) are reliable** for currency data.
6. **Google News RSS for Korean queries** — items are returned but title extraction requires parsing `description` HTML, not `<title>`.
7. ** CNBC `WTIC` symbol 404s** — the WTI contract on CNBC may be delisted/renamed.
