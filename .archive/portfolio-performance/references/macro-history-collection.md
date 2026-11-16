# Macro History Collection (2026-07-17)

> 대시보드 거시경제 차트용 데이터 수집. 기존 macro_strategy_report.py의 FRED 수집 방식 재사용.

## 스크립트
`scripts/collect_macro_history.py`

## 데이터 소스
1. **yfinance** (일별): ^GSPC, DX-Y.NYB, CL=F, ^TNX, USDKRW=X, ^VIX
2. **FRED (pandas_datareader)**: CPIAUCSL(CPI→YoY), FEDFUNDS, SAHMREALTIME, BAMLH0A0HYM2

## 출력
`data/macro_history.csv` — date, sp500, dxy, wti, tnx, usdkrw, vix, cpi_yoy, fed_rate, sahm_rule, hy_spread

## 대시보드 차트
- S&P 500 + DXY (다크 카드, 이중 축)
- WTI + USD/KRW (크림 카드, 이중 축)
- 10Y 금리 + VIX (크림 카드, 이중 축)
- CPI YoY + Fed Rate + Sahm Rule (다크 카드, 이중 축)

## 사용자 교정
- "기존의 거시경제 그래프 분석하는 거 있잖아 그거 사용하면 안될까?" → collect_macro_history.py는 **기존 macro_strategy_report.py의 FRED 수집 방식을 그대로 재사용**해야 함
- 새 pandas_datareader 호출을 처음부터 작성하지 말고, 기존 스크립트의 fetch 로직을 복사할 것
- Hermes venv python3 경로 확인 필요 (pandas_datareader 호환성)

## 크론 연동
paper_tracker_daily.sh 실행 전에 collect_macro_history.py 먼저 실행 권장.
```bash
cd ~/trade-pipeline && python3 scripts/collect_macro_history.py
```
