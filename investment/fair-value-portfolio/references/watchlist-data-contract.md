# watchlist.json — 데이터 계약 (Data Contract)

## 위치
`~/trading-agents-nuri/data/watchlist.json`

## 구조
```json
{
  "stocks": [
    {"ticker": "NVDA", "name": "엔비디아", "market": "US", "sector": "AI Infrastructure"},
    {"ticker": "005930.KS", "name": "삼성전자", "market": "KR", "sector": "Technology"},
    ...
  ],
  "sector_base": {
    "Technology": 22, "Semiconductors": 18, ...
  }
}
```

## Consumer (읽는 파일)
| 파일 | 변수 | 용도 |
|:----|:----|:----|
| `src/fair_value.py` | `STOCKS` | 25종목 yfinance 분석 |
| `pipeline.py` | `NAME_TO_TICKER`, `KR_TICKERS` | 종목명→티커 변환, 한국주 판별 |
| `src/collect_macro_context.py` | `NAME_TO_TICKER`, `KR_TICKERS` | 뉴스 수집용 |
| `src/analyst_target_collector.py` | `KR_TICKERS`, `US_TICKERS` | analyst target 수집 |
| `src/agents/decision_validator.py` | `TICKER_MAP` | 결정 검증 |

## 변경 규칙
1. watchlist.json만 수정하면 5개 파일 모두 자동 반영
2. 종목 추가 시: `ticker`, `name`, `market`, `sector` 4개 필드 필수
3. sector_base는 fair_value.py의 SECTOR_BASE와 동기화 유지
4. 변경 후 `git commit -m "watchlist: ..." && git push`
