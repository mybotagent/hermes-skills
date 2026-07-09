# FRED+yfinance 매크로 전략 데이터 통합

## 개요
매일 18:35 Phase 0.5에서 `fetch_macro_strategy()`를 호출하여 FRED 경제 데이터 + yfinance 자산 가격을 수집, `macro_context.json["macro_strategy"]`에 저장.

## 실행 흐름
```
collect_macro_context.py (Phase 0.5)
  └─ fetch_macro_strategy()
       └─ subprocess.run([HERMES_VENV_PYTHON, src/macro_strategy_report.py])
            ├─ FRED API (CPI, Sahm Rule, Fed Rate, HY Spread, M2) ← Hermes venv pandas_datareader
            ├─ yfinance (SPY, TLT, GLD, DXY, WTI, KOSPI, USDKRW)
            ├─ Macro Regime 판단 (CPI+Sahm 기반 6 Regime)
            └─ Alpha-Flip 전략 시그널
       ↓
  macro_context.json["macro_strategy"] = 결과 dict
       ↓
  LangGraph Agent → macro_strategy.CPI_YoY / macro_strategy.Sahm_Rule / ...
```

## pandas_datareader 호환성 문제
- `pandas_datareader`는 **pandas 3.x와 호환되지 않음**
- `~/trading-agents-nuri/venv/`에는 pandas 3.0.3 설치됨 → 직접 import 불가
- **해결**: Hermes Agent venv (`~/.hermes/hermes-agent/venv/`)의 python3를 subprocess로 실행
  - Hermes venv에는 pandas 2.x + pandas_datareader 호환 버전 설치됨
  - 코드: `src/utils/macro_strategy.py`의 `fetch_macro_strategy()`

## macro_context.json 구조 (macro_strategy 필드)
```json
{
  "macro_strategy": {
    "date": "2026-06-06",
    "macro_regime": "Overheat",
    "alpha_flip_signal": "Risk-On (Bullish)",
    "indicators": {
      "CPI_YoY": "3.4%",
      "Sahm_Rule": "0.10",
      "Fed_Funds_Rate": "3.63%",
      "M2_YoY": "3.9%",
      "HY_Spread": "2.7%",
      "WTI_Price": "$90.5",
      "DXY": "100.1",
      "USDKRW": "1559",
      "SPY_Price": "$738",
      "KOSPI": "8161"
    },
    "source": "fred_yfinance"
  }
}
```

## Fallback
FRED API 실패 시 yfinance 자산 가격만으로 기본 dict 구성 (`source: "yfinance_fallback"`)
- Regime, Alpha-Flip, CPI 등은 없음
- SPY, WTI, DXY, USDKRW, KOSPI만 포함
