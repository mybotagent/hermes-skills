# 한국 주식 재무 데이터 추출

## 네이버 JSON API (권장, 2026-06-07)

yfinance로 한국 주식 가격을 조회할 수 있지만, **네이버 API가 더 정확하고 실시간**이다.

### 엔드포인트
```
GET https://api.finance.naver.com/service/itemSummary.nhn?itemcode={code}
Headers: Referer: https://finance.naver.com/
```

### 응답 형식
```json
{
  "now": 329000,         // 현재가 (원)
  "diff": -22500,        // 전일대비
  "rate": -6.4,          // 등락률 (%)
  "high": 343000,        // 고가
  "low": 325000,         // 저가
  "quant": 31299200,     // 거래량
  "marketSum": 1923425662, // 시가총액 (억?)
  "per": 26.59,
  "eps": 12372.0,
  "pbr": 4.58
}
```

### 코드 예시
```python
import http.client, json

conn = http.client.HTTPSConnection("api.finance.naver.com", timeout=10)
conn.request("GET", f"/service/itemSummary.nhn?itemcode=005930",
             headers={"Referer": "https://finance.naver.com/"})
resp = conn.getresponse()
data = json.loads(resp.read())
now = float(data["now"])  # 삼성전자 현재가 (₩329,000)
per = data.get("per")
pbr = data.get("pbr")
```

### 장점
- **실시간** (yfinance는 15~20분 지연)
- **표준 라이브러리만 필요** (http.client, json) — 추가 설치 불필요
- **언제나 동작** (네이버 금융 접속 차단 없음)
- **PER/PBR 동시 제공** — 별도 계산 불필요

### ⚠️ Naver Polling `cr` 부호 함정 (2026-07-17 발견)

**`polling.finance.naver.com/api/realtime`**의 `cr`(등락률) 필드는 **항상 절대값(양수)**.
`nv`(현재가)와 `pcv`(전일종가)를 비교해 부호를 직접 계산해야 함.

```python
# BAD — cr을 그대로 사용하면 부호가 항상 양수
cr = float(item['cr'])  # → 8.77 (절대값!)

# GOOD — nv-pcv로 부호 계산
nv = int(item['nv'])
pcv = int(item['pcv'])
sign = 1 if nv >= pcv else -1
cr_signed = round(float(item['cr']) * sign, 2)  # → -8.77
```

**권장**: `cd ~/trade-pipeline && python3 scripts/fetch_kr_stocks.py` 사용
— watchlist.json을 단일 진실 공급원으로 읽고, 부호까지 정확하게 계산.

### 종목 코드 검증 (Naver 응답 nm 교차 체크)

watchlist.json에 등록된 ticker 코드가 Naver Polling에서 의도한 회사를 가리키는지
반드시 `nm`(회사명) 필드로 교차 검증할 것. 잘못된 코드를 사용하면 전혀 다른 회사의
가격으로 분석이 이루어지는 silent corruption 발생.

```bash
python3 -c "
import json, urllib.request
url = 'https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:267260'
raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})).read()
item = json.loads(raw.decode('euc-kr', errors='ignore'))['result']['areas'][0]['datas'][0]
print(f'Naver says: {item[\"nm\"]}')  # 예: 'HD현대일렉트릭' vs watchlist 'HD현대일렉' → OK (부분 일치)
"
```

**실제 사례 (2026-07-17)**: `fetch_kr_stocks.py`에 `298040` (효성중공업, HD현대일렉 아님)으로
하드코딩되어 있어 **전혀 다른 회사의 가격**으로 수집됨. v2에서 watchlist.json을
단일 소스로 읽도록 수정하여 재발 방지. watchlist에 종목 추가 시 반드시 Naver `nm` 교차 검증 필요.

### 단점
- 한국 주식만 지원 (005930 형식, .KS/.KQ)
- Referer 헤더 필수 (없으면 빈 응답)
- 분/주봉 데이터 없음 (현재가만)

## yfinance 재무제표 계산 (fallback)

네이버 API로 현재가를 얻은 후, yfinance로 추가 재무 정보가 필요할 때:

```python
import yfinance as yf
stock = yf.Ticker('005930.KS')
info = stock.info
# price는 네이버 API 사용, yfinance는 재무제표용으로만
```

## 네이버 HTML 스크래핑 (deprecated, 레거시)

이전 방식 (`fair_value_v3.py` 초기 버전):
```bash
curl -s "https://finance.naver.com/item/main.naver?code=005930" \
  -H "User-Agent: Mozilla/5.0"
```
HTML 파싱이 필요한 경우에만 사용. **JSON API가 더 간단하고 안정적이므로 우선 사용할 것.**

## 데이터 출처 정책 (2026-06-07 확정)

| 데이터 | 🇰🇷 한국 | 🇺🇸 미국 |
|:-------|:--------|:--------|
| **현재가** | 네이버 API (`itemSummary.nhn`) | yfinance |
| **PER/PBR** | 네이버 API (JSON 내 필드) | yfinance info |
| **재무제표** | yfinance (KOSPI/KOSDAQ) | yfinance |
| **Analyst Target** | 너구리 제공 | Finnhub API |
| **뉴스** | 네이버 뉴스 (cron) | Finnhub API |
