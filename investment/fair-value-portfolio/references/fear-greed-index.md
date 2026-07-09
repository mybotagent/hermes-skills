# CNN Fear & Greed Index 수집 및 리포트 통합

## 개요
CNN Fear & Greed Index는 7개 시장 지표(주가 모멘텀, 주가 강도, 주가 폭, 풋/콜 비율, 변동성, 안전자산 수요, 정크본드 수요)를 종합한 투자심리 지표. 0~100 범위.

## 데이터 소스
- **URL**: `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`
- **공식 페이지**: `https://edition.cnn.com/markets/fear-and-greed`
- **무료**: API 키 불필요 (HTTP 헤더 기반 봇 탐지 우회만 필요)

## 봇 탐지 우회 (중요)
CNN API는 `User-Agent`가 없거나 기본 Python `urllib` UA면 **HTTP 418 "I'm a teapot"** 반환.
필수 헤더:
```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
    "Origin": "https://www.cnn.com",
    "Accept": "application/json, text/plain, */*",
}
```

## 스크립트
**위치**: `langgraph/src/utils/fear_greed.py`
**실행**:
```bash
# 리포트 출력 (08:10 크론용)
cd ~/trade-pipeline && python3 langgraph/src/utils/fear_greed.py --report

# 파이프라인용 (score|rating|prev_close|prev_1w|prev_1m|timestamp)
cd ~/trade-pipeline && python3 langgraph/src/utils/fear_greed.py
```

## 출력 예시
```
😨 **CNN Fear & Greed Index: 33.4 (FEAR)**
   공포 — 투자심리 위축, 신중한 접근 필요
   전일: 40.1 | 1주전: 56.1 | 1개월전: 67.3
   → 전일대비 6.7p 하락 (공포 심화 📉)
```

## 등급 기준 (0~100)
| 범위 | 등급 | 이모지 | 해석 |
|:----:|:----|:-----:|:-----|
| 0~25 | Extreme Fear | 🔴 | 극단적 공포 — 패닉, 과매도 구간 |
| 25~45 | Fear | 😨 | 공포 — 투자심리 위축 |
| 45~55 | Neutral | 😐 | 중립 — 방향성 탐색 |
| 55~75 | Greed | 😊 | 탐욕 — 시장 낙관, 과열 관찰 |
| 75~100 | Extreme Greed | 🟢 | 극단적 탐욕 — 버블 위험, 차익실현 고려 |

## API 응답 구조 (핵심 필드만)
```json
{
  "fear_and_greed": {
    "score": 33.43,
    "rating": "fear",
    "previous_close": 40.11,
    "previous_1_week": 56.06,
    "previous_1_month": 67.29,
    "previous_1_year": 63.43,
    "timestamp": "2026-06-09T21:59:25+00:00"
  },
  "fear_and_greed_historical": { /* 일별 시계열 */ },
  "market_momentum_sp500": { /* S&P 모멘텀 */ },
  "stock_price_strength": { /* NYSE 상승/하락 종목 비율 */ },
  "stock_price_breadth": { /* 시장 넓이 */ },
  "put_call_ratio": { /* 풋/콜 비율 */ },
  "market_volatility_vix": { /* VIX */ },
  "safe_haven_demand": { /* 안전자산 수요 */ },
  "junk_bond_demand": { /* 정크본드 수요 */ }
}
```

## 파이프라인 통합
- **적용 리포트**: 08:10 오전 브리핑 (크론 `6297df83d4f3`)
- **수집 시점**: 실행 순서 3번 — fair_value/analyst_target 후, 리포트 작성 전
- **출력 위치**: 08:10 리포트 섹션 1번 (가장 상단)
- **아직 미통합**: 18:00 US 브리핑, 18:30 매크로 리포트, 18:35 LangGraph Phase 0.5
