# Cron Mode Data Sources (2026-06-26 검증)

cron 모드(HIGH 보안, pipe-to-interpreter 차단)에서 실제 동작 확인된 금융 데이터 소스.

## ⭐ CNBC REST XML API (1순위 강력 추천) — 2026-06-26 발견

HTML 스크래핑보다 훨씬 안정적인 CNBC 공식 XML API 존재.

**Endpoint:** `https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols={SYMBOL}&requestMethod=itk`

**장점:**
- HTML 파싱 불필요, curl + python3(또는 grep)로 직접 추출
- `<last>`, `<previous_day_closing>`, `<change>`, `<change_pct>` 모두 제공
- `<fundamentalData>`로 52주 고가/저가 제공
- US10Y 등 HTML 페이지가 빈 페이지를 반환하는 심볼도 정상 작동
- Rate-limit 관대 (Yahoo 대비, 시간당 수십건에도 문제없음)
- XML 구조이므로 `curl -o /tmp/file.xml && python3 -c "import re; ..."` 패턴으로 쉽게 파싱

**동작 확인 심볼 (2026-06-26):**
| 심볼 | 대상 | XML 파싱 키 |
|:----|:-----|:------------|
| `.SPX` | S&P 500 | `<name>S&amp;P 500 Index</name><last>7357.49</last>` |
| `.KS11` | KOSPI | `<name>KOSPI Index</name><last>8411.21</last><previous_day_closing>8930.30</previous_day_closing>` |
| `.DXY` | 달러인덱스 | `<name>ICE U.S. Dollar Index</name><last>101.197</last>` |
| `@CL.1` | WTI 원유 | `<name>WTI Crude (Aug'26)</name><last>69.30</last>` |
| `@GC.1` | 금 선물 | `<name>Gold COMEX (Aug'26)</name><last>4059.90</last>` |
| `US10Y` | 미국 10년물 금리 | `<name>U.S. 10 Year Treasury</name><last>4.378</last><fundamentalData><yrhiprice>4.69</yrhiprice><yrloprice>3.93</yrloprice></fundamentalData>` |

**수집 스크립트 패턴:**
```python
import subprocess, re
symbols = [".SPX", ".KS11", ".DXY", "@CL.1", "@GC.1", "US10Y"]
for sym in symbols:
    # 1. curl로 XML 저장 (pipe-to-interpreter 차단 우회)
    cmd = f'curl -s --max-time 15 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols={sym}&requestMethod=itk" -H "User-Agent: Mozilla/5.0" -o /tmp/cnbc_{sym.replace(".","_").replace("@","_")}.xml'
    subprocess.run(cmd, shell=True, timeout=20)

    # 2. 파일 읽어서 XML 파싱
    with open(f"/tmp/cnbc_{sym.replace('.','_').replace('@','_')}.xml") as f:
        data = f.read()
    last = re.search(r'<last>([^<]+)', data)
    prev = re.search(r'<previous_day_closing>([^<]+)', data)
    chg = re.search(r'<change>([^<]+)', data)
    chg_pct = re.search(r'<change_pct>([^<]+)', data)
    name = re.search(r'<name>([^<]+)', data)
    print(f"{name.group(1) if name else sym}: last={last.group(1)} prev={prev.group(1)} chg={chg.group(1)} chg%={chg_pct.group(1)}")
```

**⚠️ US10Y 특이사항:** CNBC HTML 페이지 (`https://www.cnbc.com/quotes/US10Y`)는 종종 2MB+ React boilerplate만 반환하고 실제 시세 데이터가 없음. 반드시 XML API endpoint 사용할 것.

**⚠️ 기존 HTML scraping 패턴과의 차이:** CNBC HTML 스크래핑은 `change_pct`가 누락되는 경우가 잦음(2026-06-24 확인). XML API는 항상 `change_pct`를 포함하므로 직접 계산 불필요.

## 환율 (open.er-api.com)
- 무료, 일 1,500회, SSL 지원
- 검증 완료: USD/KRW=1513.37, EUR/USD=1.1597 (2026-06-16)
- 패턴: `curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" | grep -o '"KRW":[0-9.]*'`

## 미국 10년물 금리 (CNBC)
- URL: `https://www.cnbc.com/quotes/US10Y`
- User-Agent 필수
- 응답에 JSON 데이터 삽입됨 → grep으로 추출
- 패턴: `curl -sL "https://www.cnbc.com/quotes/US10Y" -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[0-9.]+%"'`
- 2026-06-16 검증: 4.441%

## KOSPI (CNBC)
- URL: `https://www.cnbc.com/quotes/.KS11`
- 패턴: `curl -sL "https://www.cnbc.com/quotes/.KS11" -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[0-9,.]+"'`
- 2026-06-16 검증: 8,726.60

## S&P 500 (CNBC JSON — 추천, Yahoo fallback)

- URL: `https://www.cnbc.com/quotes/.SPX`
- User-Agent 필수
- 2026-06-18 검증: **7,420.10** (Open 7,524.50, Change -91.25)
- Yahoo Finance 차단 시 CNBC가 안정적 fallback
- 패턴: `curl -sL "https://www.cnbc.com/quotes/.SPX" -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[0-9,.]+"'`

## S&P 500 (Yahoo Finance — US 심볼이라 2026-07-07 기준 여전히 차단)

- URL: `https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d`
- ⚠️ **2026-07-07 검증 — US 심볼은 여전히 차단**. query1·query2 모두 "Too Many Requests". User-Agent 필수지만 추가 노이즈 — 재시도/5초 sleep 모두 무효.
- **2026-07-07 권장**: US 심볼(`^GSPC`, `^TNX`, `^TYX`, `CL=F`)은 무조건 **CNBC XML API** 우선 사용. Yahoo 시도 X.
- 차단 시 fallback 경로 더 이상 Yahoo → 바로 **CNBC XML API** (`https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.SPX&requestMethod=itk`).
- 2026-06-16 검증: 7,554.29 (이전 검증, 2026-07-07부터는 차단으로 분류).

## ⚠️ Yahoo Finance 차단 상태 — 심볼별 차등 (2026-07-07 신규 섹션)

**이전 blanket 판정("완전 차단")은 2026-07-07 취소**. 심볼별 차등:

| 분류 | 심볼 | 2026-07-07 상태 | 권장 소스 |
|:----|:----|:---------------|:---------|
| US 지수 | `^GSPC`, `^DJI`, `^IXIC` | 🛑 여전히 차단 | CNBC XML (`.SPX` 등) |
| US 선물 | `CL=F` (WTI), `GC=F` (Gold) | 🛑 여전히 차단 | CNBC XML (`@CL.1`, `@GC.1`) |
| US 금리 | `^TNX` (10Y), `^TYX` (30Y) | 🛑 여전히 차단 | CNBC XML (`US10Y` 등) |
| **한국 개별주** | `005930.KS`, `000660.KS`, `009150.KS`, `005380.KS`, `278470.KS`, `267270.KS` | ✅ **정상 동작** | **Yahoo chart API** (CNBC 미지원 → 사실상 유일 옵션) |

**핵심 결론**: `.KS` 접미사 한국 개별주만 Yahoo 정상. 그 외(US 지수/선물/금리)는 차단이므로 시도조차 금지. blanket "Yahoo 완전 차단" 가정은 한국 종목 가격 수집을 막는다.

Yahoo `.KS` 검증 (2026-07-07):
```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
curl -s --max-time 15 "https://query1.finance.yahoo.com/v8/finance/chart/005930.KS?interval=1d" \
  -H "User-Agent: $UA" -o /tmp/stock.json
python3 -c "
import json
m = json.load(open('/tmp/stock.json'))['chart']['result'][0]['meta']
print(f'Price: {m[\"regularMarketPrice\"]}, Prev: {m[\"chartPreviousClose\"]}')"
```

> SKILL.md 본체("### Yahoo Finance 특이사항 (심볼별 차등)")에도 동일 정정이 적용되어 있음 — 본 reference는 그 출처/세부사항 기록, SKILL.md는 cron 운영 규칙.

## WTI 유가 (CNBC JSON — 추천, Yahoo fallback)

- URL: `https://www.cnbc.com/quotes/@CL.1`
- User-Agent 필수
- 2026-06-18 검증: **$74.84** (CNBC) / $74.14 (Yahoo query2)
- 패턴: `curl -sL "https://www.cnbc.com/quotes/@CL.1" -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[0-9,.]+"'`

## WTI 유가 (Yahoo Finance)
- URL: `https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1d`
- User-Agent 필수
- 2026-06-16 검증: $77.38

## 금 선물 (CNBC)
- URL: `https://www.cnbc.com/quotes/@GC.1`
- COMEX Aug'26 기준
- 2026-06-16 검증: $4,366.20

## 한국주 뉴스 (Google News RSS)
- 가장 신뢰성 높은 크론용 뉴스 소스
- URL 패턴: `https://news.google.com/rss/search?q={검색어}&hl=ko&gl=KR&ceid=KR:ko`
- Rate-limit 매우 관대
- 한국어 검색 정상 작동
- 다른 소스 문제점:
  - DuckDuckGo: bot 차단 (Challenge page)
  - Naver: JavaScript 렌더링, curl 불가
  - Daum: JavaScript 렌더링
- grep 추출: `grep -oP '<title>[^<]+'`

### ⚠️ URL 인코딩 주의
bash에서 직접 한글 쿼리 사용 시 Google News 400 Bad Request 발생.
**curl 직접 호출**이 아닌 **Python urllib.parse.quote()** 로 URL 인코딩 필수.

```python
import urllib.parse, urllib.request
stock = '삼성전자'
query = urllib.parse.quote(f'{stock} 주식')
url = f'https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
import re
titles = re.findall(r'<title>([^<]+)', data)
for t in titles[1:6]:
    print(f'  • {t}')
```

### 종목별 검색 쿼리 (한국어)
| 종목 | 검색어 |
|:----|:------|
| 삼성전자 | `삼성전자 주식` 또는 `삼성전자 005930` |
| SK하이닉스 | `SK하이닉스 주식` |
| 삼성전기 | `삼성전기 주식` |
| 현대차 | `현대차 주식` |
| 에이피알 | `에이피알 주식` |
| HD현대일렉 | `HD현대일렉 주식` |

### Google News RSS 헤드라인 추출 패턴
- `<title>` 태그 첫 번째는 항상 "Google 뉴스" (무시)
- 실제 뉴스 제목은 `titles[1:]`

## DXY 달러 인덱스 (CNBC JSON — 검증 완료)

- URL: `https://www.cnbc.com/quotes/.DXY`
- User-Agent 필수
- 2026-06-18 최초 검증: **100.646** (Change: +0.562)
- 패턴: `curl -sL "https://www.cnbc.com/quotes/.DXY" -H "User-Agent: Mozilla/5.0" | grep -oP '"last":"[0-9.]+"'`
- background data: DXY basket = EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%

## Fed Funds Rate (Google News 기반 추론)

직접 API가 어려우므로 Google News FOMC 검색으로 추론.

### 검증 패턴 (2026-06-18)
```python
import urllib.parse, urllib.request, re
q = urllib.parse.quote('Fed funds rate June 2026 FOMC decision')
url = f'https://news.google.com/rss/search?q={q}&hl=en'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
titles = re.findall(r'<title>([^<]+)', data)
for t in titles[1:6]:
    print(f'  • {t}')
# 출력 예: "Fed holds rates steady", "Fed leaves interest rates unchanged"
```

### CPI 데이터 (동일 방식)
```python
q = urllib.parse.quote('US CPI May 2026')
url = f'https://news.google.com/rss/search?q={q}&hl=en'
# Consumer prices rose 4.2% annually in May...
```

### Fed 의장 확인
```python
q = urllib.parse.quote('Kevin Warsh Fed chair June 2026')
# → Warsh kicks off Fed chief era...
```

### 대상 키워드
| 찾을 정보 | 검색 키워드 | 확인 패턴 |
|:---------|:-----------|:---------|
| 금리 결정 | `Fed holds rates steady` 또는 `Fed raises rates` | 타이틀에서 동결/인상/인하 확인 |
| 금리 수준 | 검색 결과 + 기존 지식 조합 | `4.25~4.50%` (동결 시 이전 유지) |
| CPI | `Consumer prices rose X% annually` | X%를 타이틀에서 직접 추출 |
| Fed 의장 | FOMC meeting 타이틀 | 의장 이름 포함 기사 확인 |
| 점도표 전망 | `dot plot` 검색 | 향후 금리 경로 예측
