# Recency-Weighted Target Price Calibration (tradingAgents Architecture)

## Data Flow

```
yfinance info (targetMeanPrice / Median / High / Low / n_analysts)
  + yfinance recommendations (monthly buy/hold/sell counts)
  + Google News RSS (recent analyst actions, 30일, 3 queries per ticker)
  ↓
collect_recent_targets.py
  ├── Multi-tier Source Registry (A=3, B=1, C=0.5)
  ├── src_yfinance_targets()        — yfinance consensus targets
  ├── src_web_analyst_targets()     — Google News RSS로 개별 analyst 리포트 수집 (v2)
  ├── _extract_target_price()       — $/₩ 추출 + market cap filter + price sanity
  ├── _extract_firm()               — 40+ analyst firm matching
  ├── weighted_synthesis()          ← lib/conflict.py 패턴
  └── per-source references (firm, date, value, url, action)
  ↓
recent_targets.json
  ↓
collect_consensus.py (calibration_factor 적용)
  ├── targetMeanPrice × calibration_factor
  ├── original_mean 필드 보존
  └── references[3] 추가 (source, url, date)
  ↓
portfolio_dashboard.html (표시)
  ├── 목표주가 옆 ×calibration_factor 배지
  └── ⚙️ 보정: original → calibrated 줄
```

## Key Files

| 파일 | 역할 |
|:-----|:------|
| `scripts/collect_recent_targets.py` | 수집 + 합성 + calibration (v2: web search) |
| `data/recent_targets.json` | 출력 (14 tickers) |
| `consensus_data.json` | 기존 targetMeanPrice + calibration 반영 |

## v2: Web Search for Individual Analyst Targets

`collect_recent_targets.py` v2는 yfinance 집계값 외에도 **웹서치로 개별 애널리스트 리포트**를 수집한다.

### 검색 방식

US ticker 기준 3개 검색어로 Google News RSS 검색:
1. `"{ticker} {name} analyst price target upgrade downgrade"`
2. `"{ticker} stock analyst rating target"`
3. `"{ticker} analyst upgrade downgrade target price"`

Each ticker → 3 queries → RSS items → analyst report 추출.

### Target Price 추출 (`_extract_target_price`)

```python
# $XXX or $XXX.XX
re.finditer(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', text)
# ₩XXX or ₩XXX,XXX  
re.finditer(r'₩(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', text)
```

**Sanity validation**:
- `$1` 미만 skip
- $X 뒤 `B/T/M` 문자 → market cap으로 간주 skip ($319B, $1.3T 등)
- `current_price * 0.5` ~ `current_price * 5.0` 범위 외 skip

### Analyst Firm 추출 (`_extract_firm`)

40+ analyst firm dictionary에서 title/snippet 매칭:
- Goldman Sachs, Morgan Stanley, JPMorgan, Citi, UBS, KeyBanc, Piper Sandler...
- KB투자증권, 미래에셋, 신한금융투자, 삼성증권, NH투자증권...
- Fallback: colon/dash 이전 문자열 추출

### Per-Source `action` field

각 analyst source는 `action` 필드 보유:
- `upgrade` — raised/increase/upgrade 키워드
- `downgrade` — cut/lower/downgrade 키워드
- `initiate` — start/initiate 키워드
- `""` — 중립/기타

### Search Statistics

`search_stats` 객체:
```json
{
  "queries": 3,
  "total_results": 48,
  "analyst_sources": 10
}
```

### 종목당 Source 수 (2026-07-17 기준)

| 종목 | 총 sources | web analyst reports |
|:----|:---------:|:------------------:|
| MU, NVDA, MSFT, STX, WDC, HPE | 15 | **10** ✅ |
| AVGO, CLS | 11 | **6** ✅ |
| SK하이닉스 | 10 | **5** ✅ |
| 삼성전자 | 6 | 1 |
| 삼성전기 | 6 | 1 |
| LG이노텍, 현대차, 기아 | 5 | **0** ❌ |

### Known Limitation: Korean Tickers

한국주(LG이노텍·현대차·기아·에이피알)는 영문 Google News RSS에서 애널리스트 리포트가 검색되지 않음.
- `005930.KS`(삼성전자)는 영문 coverage 일부 존재
- 해결 방안: 한국어 검색어 + Naver News RSS 별도 구현 필요
- Fallback: yfinance targetMeanPrice/Median 만으로 weighted target 계산

## Weighted Synthesis (tradingAgents lib/conflict.py)

```python
def synthesize(sources):
    numeric = [s for s in sources if s.get('value') and s['type'] in (
        'target_mean', 'target_median', 'target_high', 'target_low',
        'analyst_report')]  # v2: individual analyst reports included
    ...
```

**v2 변경**: `analyst_report` 타입도 weighted 합성에 포함 (Tier A, weight 3.0)

**Confidence 기준 (v2)**:
- n_analyst_sources >= 3 → high
- n_analyst_sources >= 1 or Tier B present → medium
- otherwise → low

## Per-Source Reference Format

```json
{
  "firm": "JPMorgan",
  "date": "2026-06-25",
  "value": 1540.0,
  "tier": "A",
  "weight": 0.83,
  "type": "analyst_report",
  "action": "",
  "ref": "JPMorgan raises Micron stock price target to $1,540 on contracts - Investing.com",
  "url": "https://news.google.com/rss/articles/...",
  "days_old": 22
}
```

### v2 Type 확장

| type | 설명 | Tier |
|:-----|:-----|:----:|
| target_mean | yfinance consensus mean | B |
| target_median | yfinance consensus median | B |
| target_high | yfinance highest estimate | C |
| target_low | yfinance lowest estimate | C |
| sentiment_delta | buy ratio change (월간) | B |
| **analyst_report** | **개별 analyst target (v2 신규)** | **A** |
| analyst_news | analyst mention (target price 없음) | C |

## Calibration Factor

```
calibration_factor = weighted_synthesis_target / existing_targetMeanPrice
```

- ×1.0 = 정확히 일치
- ×1.02 = weighted가 2% 높음 (consensus보다 낙관적)
- ×0.98 = weighted가 2% 낮음 (consensus보다 비관적)

## Pitfalls

### 1. 🔴 RSS 날짜 파싱 — timezone suffix 제거
Google News RSS는 `"Thu, 09 Jul 2026 13:47:11 GMT"` 형식 반환.
`datetime.strptime()`은 GMT/UTC/EST/PST 같은 timezone suffix를 처리 못 함 → ValueError.
**해결**: 파싱 전 `clean_pub`에서 `[" GMT"," UTC"," EST"," EDT"," PST"," PDT"]` suffix 제거.

### 2. 🔴 Market cap vs Target price 구분
"AVGO Stock Headed For $319B Market Cap Wipeout" → `$319`가 target처럼 추출됨.
**해결**: `$` 다음 문자에 `B/T/M` 있으면 market cap으로 간주 skip.

### 3. 🔴 Analyst firm name dictionary 유지보수
`ANALYST_FIRMS` 리스트에 있는 firm name만 인식. 새로운 analyst firm이 등장하면 업데이트 필요.
Firm 이름은 긴 순으로 정렬하여 짧은 이름(예: "Citi" vs "Citigroup")이 먼저 매칭되지 않도록 `sorted(key=len, reverse=True)`.

### 4. 🔴 KR ticker web search limitation
한국주는 English Google News RSS에서 analyst coverage 거의 없음.
종목 수 15개 중 4개(LG이노텍·현대차·기아·에이피알)는 web source 0개.
→ web source 0개여도 yfinance baseline은 유지, calibration factor = 1.0.
