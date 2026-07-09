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
