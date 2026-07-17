# Paper Portfolio Performance Tracking

로그된 portfolio snapshot + yfinance 가격 데이터로 포트폴리오 성과를 추적·시각화.

## 데이터 소스

- **Snapshot**: `logs/portfolio/YYYY-MM-DD.json` (Phase 3 할당 결과, 일일 저장)
- **가격**: yfinance 백필 (캐시: `data/paper_price_cache.json`)
- **성과**: `data/paper_tracker_daily.csv` + `data/paper_tracker_metrics.json`

## 핵심 스크립트

`scripts/paper_tracker.py` (단독 실행)

## 실행

```bash
cd ~/trade-pipeline && python3 scripts/paper_tracker.py
```

## 계산 방법론

### 일일 포트폴리오 수익률

```
daily_return = sum(weight_i × (price_t_i / price_t-1_i - 1)) + cash_ratio × 0
```

### 누적 수익률

```
cum_ret = Π(1 + daily_return_i) - 1
```

### MDD

```
peak = max(prev_peak, cum_ret_i)
dd_i = (cum_ret_i - peak) / peak
MDD = min(dd_i)
```

### Sharpe Ratio

```
daily_rfr = 0.03 / 252
sharpe = (mean(daily_returns) - daily_rfr) / std(daily_returns) × sqrt(252)
```

## HTML 대시보드

`data/portfolio_dashboard.html` — Chart.js 다크 테마.

### 실행

```bash
cd ~/trade-pipeline/data && python3 -m http.server 9292 --bind 0.0.0.0
→ http://<host>:9292/portfolio_dashboard.html
```

## 데이터 흐름

```
logs/portfolio/*.json → paper_tracker.py (yfinance 백필 + 수익률 계산)
  → paper_tracker_daily.csv + paper_tracker_metrics.json
  → portfolio_dashboard.html (Chart.js 대시보드)
```

## 주의사항

- 한국주 당일 nan → 해당 종목만 스킵
- 최소 5일치 snapshot 필요 (28일+ 권장)
- `set -euo pipefail` 스크립트는 `|| echo "실패"` + `exit 0` 필요
