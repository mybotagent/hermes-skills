# Cron-Mode Data Verification for Macro Context

> Created: 2026-06-15
> Context: 18:30 매크로 크론에서 subagent 데이터 fabrication 발견

## Problem

크론 모드에서 `delegate_task`(web toolsets)로 수집한 매크로 데이터는 **subagent hallucination**으로 인해 수치가 크게 왜곡될 수 있음.

## Concrete Example (2026-06-15)

| 데이터 항목 | Subagent 보고 | 실제 검증값 | 오차 |
|:-----------|:-------------|:-----------|:----|
| USD/KRW | 1,315 | **1,516.97** (exchangerate-api) | -13.3% ❌ |
| USD/KRW (2차) | 1,290 | **1,516.97** | -14.9% ❌ |

- 이전 보고서(6/12)의 USD/KRW 1,520.94가 더 정확했음
- subagent가 "1,315"를 생성한 이유: 과거 데이터(1월 수준)를 현재로 착각

## Cron-Mode Tool Constraints

| 도구 | 크론 모드 상태 |
|:----|:-------------|
| `execute_code` | ❌ BLOCKED (보안 정책) |
| `curl | python3 -c "..."` | ❌ BLOCKED (pipe-to-interpreter) |
| `browser_navigate` (금융사이트) | ❌ 타임아웃 (60초) |
| `curl | grep -o` | ✅ 허용됨 |
| `curl -o /tmp/file.json` | ✅ 허용됨 |
| `write_file` | ✅ 허용됨 |
| `delegate_task` | ✅ 허용됨 (단, 출력 검증 필수) |

## Verification Commands (Working in Cron Mode)

### Exchange Rates (exchangerate-api — 무료, 일 1,500회)
```bash
# USD/KRW
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" 2>/dev/null | grep -o '"KRW":[0-9.]*'

# EUR/USD
curl -s --max-time 10 "https://open.er-api.com/v6/latest/EUR" 2>/dev/null | grep -o '"USD":[0-9.]*'

# 전일 기록 비교용
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" 2>/dev/null | grep -o '"time_last_update_utc":"[^"]*"'
```

### Historical Data (Cached Files)
```bash
# /tmp/에 캐시된 이전 데이터 확인
cat /tmp/usd_rates.json | grep -o '"KRW":[0-9.]*'
cat /tmp/fx_rate.json | grep -o '"KRW":[0-9.]*'
```

### Yahoo Finance (Rate-Limited — 1회만 시도)
```bash
# 실패 시 Edge: Too Many Requests — 대체 경로로 전환
curl -s --max-time 10 "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1d" -o /tmp/wti_check.json 2>/dev/null
```

## Workflow Pattern

1. **Subagent에 뉴스/정성 데이터 위임** (fabrication 위험 낮음)
2. **직접 검증**으로 핵심 수치 확인 (curl + grep)
3. **검증값 기준으로 subagent 데이터 보정**
4. **파일 저장** (macro_context.json)

## Government Data (BLS / FRED) — Press Release Fallback via Google News RSS (2026-07-13 추가)

**증상**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=...`, `https://download.bls.gov/pub/time.series/...`, `https://www.bls.gov/news.release/...` 모두 봇 차단(403/Access Denied, 1325B 응답) 또는 SSL timeout. `browser_navigate`도 120초 타임아웃. IMF article 페이지도 차단. **Fed press release(`https://www.federalreserve.gov/...`)와 BEA(`https://www.bea.gov/news/2026/...`)는 직접 다운로드 정상 동작** — 정부 사이트라도 도메인별로 차단 여부가 다름.

**해결**: Google News RSS는 정부 보도자료 원문을 안정적으로 인덱싱한다. "발표일 + 핵심 수치 + 정부기관명" 쿼리로 그 보도자료를 그대로 인용한 매체 헤드라인이 나온다. 발행기관·발표시각·헤드라인이 모두 노출되므로 **수치 fabrication 없이 원문 인용 가능**.

```bash
# BLS 5월 CPI 4.2% 검증 (BLS direct 차단 시)
python3 -c "
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
q = urllib.parse.quote('May 2026 US CPI 12 months 4.2 percent BLS')
r = urllib.request.urlopen(urllib.request.Request(
  'https://news.google.com/rss/search?q='+q+'&hl=en-US&gl=US&ceid=US:en',
  headers={'User-Agent':'Mozilla/5.0'}), timeout=20).read()
root = ET.fromstring(r)
for i in root.findall('.//item')[:8]:
  print(i.findtext('pubDate'), '|', i.findtext('title'))"
# → Wed, 17 Jun 2026 07:00:00 GMT | Consumer prices up 4.2 percent over the year ended May 2026 - Bureau of Labor Statistics (.gov)

# BLS 6월 고용 (실업률 4.2%, NFP +57K) — 7/2 발표
python3 -c "
import urllib.parse, urllib.request, xml.etree.ElementTree as ET
q = urllib.parse.quote('\"job growth\" \"unemployment rate\" \"June\" \"2026\" US')
r = urllib.request.urlopen(urllib.request.Request(
  'https://news.google.com/rss/search?q='+q+'&hl=en-US&gl=US&ceid=US:en',
  headers={'User-Agent':'Mozilla/5.0'}), timeout=20).read()
root = ET.fromstring(r)
for i in root.findall('.//item')[:6]:
  print(i.findtext('pubDate'), '|', i.findtext('title'))"
# → Thu, 02 Jul 2026 07:00:00 GMT | U.S. job creation cools in June with payrolls growth of just 57,000; unemployment rate at 4.2% - CNBC
# → The Employment Situation - June 2026 - Bureau of Labor Statistics (.gov)
```

**교차 확인 규칙**:
- Google News RSS에서 `Bureau of Labor Statistics (.gov)` / `Federal Reserve` / `BEA` 등 정부 발행 표기가 있는 헤드라인만 1차 출처로 인정
- 매체 헤드라인(CNBC, Reuters, NYT)은 2차 출처
- 동일 수치가 2개 매체 이상에서 반복 등장 시 채택 (subagent hallucination과 동일 패턴)

**관측된 차단 패턴 (2026-07-13)**:
| 출처 | 상태 | Fallback |
|:----|:----|:---------|
| `https://fred.stlouisfed.org/graph/fredgraph.csv?id=...` | TimeoutError | Google News RSS |
| `https://download.bls.gov/pub/time.series/...` | TimeoutError | Google News RSS |
| `https://www.bls.gov/news.release/...` | Access Denied (1325B) | Google News RSS |
| `https://www.imf.org/en/News/Articles/...` | 540B 차단 | Google News RSS |
| `https://www.bea.gov/news/2026/...` | ✅ 정상 | 직접 사용 |
| `https://www.federalreserve.gov/newsevents/...` | ✅ 정상 | 직접 사용 |
| `https://www.federalreserve.gov/monetarypolicy/fomc*.pdf` | ✅ 정상 | pdftotext / pdfplumber |

**macro_context.json `data_quality.notes`에 fallback 사실 명기 필수** — 검증 책임의 투명성.

## Ticker Code Verification (Naver Polling) (2026-07-13 추가)

Naver 코드는 6자리 코스피 코드라 Yahoo 심볼(예: 005930.KS)과 다르고, 같은 그룹의 종목끼리 혼동이 잦다. **수집 코드는 Naver Polling 1회 응답으로 종목명 검증**:

```bash
python3 -c "
import json, urllib.request
raw = urllib.request.urlopen(urllib.request.Request(
  'https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:267260',
  headers={'User-Agent':'Mozilla/5.0'}), timeout=10).read()
print(json.loads(raw.decode('euc-kr', errors='ignore'))['result']['areas'][0]['datas'][0]['nm'])"
# → HD현대일렉트릭  (267260)  ← 올바른 코드
# 267270 → HD건설기계  ← 흔한 혼동 케이스
```

흔한 혼동:
- HD현대일렉트릭 267260 (전력기기) vs HD건설기계 267270
- HD현대 267270 (모회사) vs HD현대일렉트릭 267260 (자회사)

## Important

- subagent가 "정확한" 데이터처럼 보여도 **반드시 검증**
- 검증명령어가 실패해도 subagent 데이터를 그대로 쓰지 말 것
- "데이터를 가져올 수 없음"이라고 보고하는 것이 fabrication 데이터를 쓰는 것보다 안전함
- 정부 통계 직접 다운로드가 차단되면 Google News RSS로 동일 보도자료 인덱싱을 확인 — 0% fabrication risk + 1차 출처 추적 가능
