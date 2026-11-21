# watchlist.json — 데이터 계약 (Data Contract)

## 위치
`~/trade-pipeline/data/watchlist.json`

(구 경로 `~/trading-agents-nuri/...` 는 더 이상 사용하지 않는다)

## 구조
```json
{
  "stocks": [
    {"ticker": "NVDA", "name": "엔비디아", "market": "US", "sector": "AI Infrastructure",
     "pe_min": 10, "pe_max": 30, "currency": "USD", "yahoo_suffix": ""},
    {"ticker": "005930.KS", "name": "삼성전자", "market": "KR", "sector": "Technology",
     "pe_min": 8, "pe_max": 18, "currency": "KRW", "yahoo_suffix": ""},
    ...
  ],
  "sector_base": {
    "Technology": 22, "Semiconductors": 18, "Basic Materials": 15, "Clean Energy": 25, ...
  }
}
```

## Consumer (읽는 파일)

| 파일 | 변수 | 용도 |
|:----|:----|:----|
| `scripts/stocks_config.py` | `ALL_STOCKS`, `US_TICKERS`, `KR_TICKERS`, `NAME_TO_TICKER`, `yahoo_ticker()` | 중앙 로더 — 다른 모듈은 여기서 import |
| `langgraph/src/fair_value.py` | `STOCKS`, `SECTOR_BASE` | 적정 PER 밸류에이션 |
| `scripts/collect_consensus.py` | `NAME_TO_TICKER` | 종목별 뉴스/컨센서스 수집 |
| `scripts/paper_tracker.py` | `NAME_TO_TICKER` | 페이퍼 포트폴리오 성과 추적 |
| `scripts/auto_expel.py` | watchlist 직접 로드 | `gap_T1 < -50%` 자동퇴출 |
| `langgraph/src/collect_macro_context.py` | `NAME_TO_TICKER`+`KR_TICKERS` | 매크로 수집 |
| `langgraph/src/analyst_target_collector.py` | `KR_TICKERS`+`US_TICKERS` | analyst target 수집 |
| `langgraph/src/agents/decision_validator.py` | `TICKER_MAP` | 결정 검증 |

**반드시 stocks_config.py를 통해 import 한다** — 각 모듈이 watchlist.json을 직접 파싱하거나 이름→티커 사전을 하드코딩하면 단일소스 원칙이 깨진다.

## 변경 규칙
1. watchlist.json만 수정하면 위 전 파일이 자동 반영됨
2. 종목 추가 시 8개 필드: `ticker`, `name`, `market`, `sector`, `pe_min`, `pe_max`, `currency`, `yahoo_suffix`
3. `sector_base`는 **watchlist.json**과 `fair_value.py`의 `SECTOR_BASE` 양쪽에 동기화 유지 (한쪽만 하면 조용히 기본값으로 폴백)
4. `yahoo_suffix`는 ticker에 이미 접미사가 있을 때 비워둔다 (`267260.KS` → `""`)
5. 종목 추가 절차 전체는 `references/ticker-maintenance.md` 참조 (검증 → 중복확인 → sector 동기화 → 하드코딩 사전 제거 → suffix 확인 → 실제 실행 검증)
6. `data/watchlist.json`은 `.gitignore`(`data/*.json`)로 git 추적 제외 — 로컬 단일 진실. 코드 측 변경만 커밋·push 대상.
