# Macro Context Data Contract

> **Last updated: 2026-07-02 (was 2026-06-07)**
> ⚠️ **이 문서 초안(2026-06-07) 이후 실제 출력이 evolve했습니다.** 본 문서에 기재된 키 외에 실제 JSON에 ~20개 추가 키가 존재합니다. 신규 consumer 작성 시 본 문서만 믿지 말고 **반드시 `python3 -c "import json; print(json.load(open('data/macro_context.json')).keys())"` 로 직접 키 확인**하세요.

## Producer: 18:30 매크로 크론 (b96583fa9d27) — LLM 매크로 리포트
### Output: `data/macro_context.json` (양쪽 디렉토리에 저장: `~/trading-agents-nuri/` + `~/trade-pipeline/`)

```json
{
  "timestamp": "ISO datetime (KST, e.g. 2026-07-02T19:30:00+09:00)",
  "date": "YYYY-MM-DD",
  "collection_note": "Verified via CNBC XML API + open.er-api.com (no subagent hallucination risk). Data timestamp: ... KST.",
  "macro_report_summary": "string (~3000~6000자, Executive Summary/Current State/Causal Linkage/Counter-factual/Structural Implications/Priority Matrix 6섹션 리포트 전문)",
  "key_macro_data": {
    "fed_rate": "string (e.g. '4.25~4.50% (Warsh regime, hawkish, 6/17 FOMC 동결)')",
    "us_10y_yield": "string (⚠️ 2026-06-30부터 us10y → us_10y_yield 키명 변경)",
    "dxy": "string",
    "wti": "string",
    "usdkrw": "string",
    "usd_jpy": "string (2026-06-30부터 추가)",
    "usd_cny": "string (2026-06-30부터 추가)",
    "sp500": "string (2026-06-30부터 추가 — 전일 마감값)",
    "kospi": "string (2026-06-30부터 추가)",
    "kospi_prev_close": "string (전일 종가, change_pct 계산 검증용)",
    "kospi_intraday": "string (시가→종가 메모)",
    "kosdaq": "string (2026-06-30부터 추가)",
    "vix": "string (2026-06-29부터 정상 수집 — 이전에는 'N/A'였음)",
    "gold": "string (2026-06-30부터 추가)",
    "may_cpi_yoy": "string (⚠️ cpi_yoy → may_cpi_yoy로 변경)",
    "fed_chair": "string (2026-06-18부터 'Kevin Warsh (hawkish)')"
  },
  "market_interpretation": {
    "key_driver": "string (트리거 이벤트 명시)",
    "market_sentiment": "risk-on|risk-off|neutral (한국어 추가 가능: '강한 Risk-off (한국 한정 패닉)')",
    "regime": "Goldilocks|Overheat|Slowdown|Stagflation|Severe_Inflation|Deflation (2026-06-08부터 6개로 확장)",
    "impact_analysis": "string (6종목별 인과관계)",
    "divergence_note": "string (2026-06-24부터 — 글로벌 vs 한국 괴리)",
    "oil_iran_dynamics": "string (2026-06-30부터 — 호르무즈 시나리오 분기)",
    "fx_dynamics": "string (2026-06-30부터 — 환율 메커니즘)",
    "leverage_note": "string (2026-07-02부터 — 레버리지 ETF 노트, 이벤트 발생 시)"
  },
  "news_items": [
    {
      "title": "string (Google News RSS 제목)",
      "url": "string (Google News 리다이렉트 URL)",
      "pubDate": "ISO datetime KST ('%Y-%m-%d %H:%M KST' 포맷)",
      "source": "string (언론사, e.g. '경향신문 (Google News RSS)')",
      "search_query": "string (어떤 쿼리로 수집했는지 — 2026-06-30부터 dedupe용 추가)",
      "category": "string (선택 — 'stock'|'macro'|'oil'|'fed' 등)",
      "ticker": "string (선택 — 종목 뉴스인 경우 한글명)"
    }
  ]
}
```

## Consumers

### 1. pipeline.py Phase 0.5
```python
mc.get("key_macro_data", {})       # korrect
mc.get("market_interpretation", {})  # korrect
mc.get("news_items", [])            # korrect
```

### 2. context.py (`src/agents/context.py`)
```python
mc = state["macro_context"]
mk = mc.get("key_macro_data", {})     # ← was: mc.get("market", {})  (BUG!)
mi = mc.get("market_interpretation", {})
# key_driver: mi.get("key_driver", "N/A")
# dxy:        mk.get("dxy", "N/A")
# usdkrw:     mk.get("usdkrw", "N/A")
# tnx:        mk.get("us_10y_yield", "N/A")  # ⚠️ 2026-06-30 키명 us10y → us_10y_yield로 변경됨
# vix:        mk.get("vix", "N/A")           # 2026-06-29부터 정상 수집
# gold:       mk.get("gold", "N/A")          # 2026-06-30부터 추가
# kospi:      mk.get("kospi", "N/A")         # 2026-06-30부터 (매크로 리포트 한정)
# events:     news_items titles with medium/high impact
# risks:      news_items titles with high impact only
```

### 3. risk.py (`src/agents/risk.py`)
```python
mk = mc.get("key_macro_data", {})
# ⚠️ 키명 검증: 실제 출력은 us_10y_yield (2026-06-30부터)
# vix:    mk.get("vix", "N/A")        # 정상 수집됨
# dxy:    mk.get("dxy", "N/A")
# tnx:    mk.get("us_10y_yield", "N/A")  # ⚠️ 변경됨
# usdkrw: mk.get("usdkrw", "N/A")
# gold:   mk.get("gold", "N/A")
```

### 4. report.py (`src/report.py`)
```python
mk = mc.get("key_macro_data", {})     # ← same bug fixed
mi = mc.get("market_interpretation", {})
# metrics: fed_rate, us_10y_yield, dxy, wti, usdkrw (2026-06-30 이후)
#          + vix, gold, kospi, kosdaq, sp500 (2026-06-30+ 부터)
# key_driver: mi.get("key_driver", "")
# regime:     mi.get("regime", "")
# divergence: mi.get("divergence_note", "")  # 2026-06-24 신규
# oil_iran:   mi.get("oil_iran_dynamics", "")  # 2026-06-30 신규
# events:     news_items titles with medium/high impact
# risks:      news_items titles with high impact only
```

### 5. portfolio_allocation.py (`src/agents/portfolio_allocation.py`) ✅
```python
# CORRECT - reads the right keys:
interp = macro_ctx.get("market_interpretation", {})
key_data = macro_ctx.get("key_macro_data", {})
report = macro_ctx.get("macro_report_summary", "")
```

## Common Bugs (실제 발생 사례, 2026-06-07 ~ 07-02)

| 버그 | 발생 파일 | 원인 | 결과 | 상태 |
|:----|:---------|:-----|:-----|:----|
| `mc.get("market", {})` | context.py L12, risk.py L6 | 존재하지 않는 키 `market` 사용 | 모든 매크로 값 "N/A" | ✅ FIXED |
| `mc.get("events", [])` | context.py L13 | `events` 키 없음 | 항상 빈 리스트 | ✅ FIXED |
| `mc.get("risks", [])` | context.py L14 | `risks` 키 없음 | 항상 빈 리스트 | ✅ FIXED |
| `mk.get("tnx")` | report.py L20 (구버전) | 실제 키: `us10y` | 10Y 값 항상 None | ✅ FIXED |
| `mk.get("vix")` | context.py L25 (구버전) | "VIX 수집 안 함 - N/A" 가정 | 항상 "N/A" | ✅ FIXED (2026-06-29부터 vix 정상 수집) |
| `mk.get("gold")` | report.py L22 (구버전) | "Gold 수집 안 함" 가정 | 항상 None | ✅ FIXED (2026-06-30부터 gold 추가) |
| `mk.get("us10y")` | 모든 consumer (구버전) | 2026-06-30 키명 us10y → us_10y_yield 변경 | 10Y 값 None | ⚠️ 2026-07-02 확인 (이전 코드 위험) |
| `mk.get("cpi_yoy")` | 모든 consumer (구버전) | 2026-06-30 키명 cpi_yoy → may_cpi_yoy 변경 | CPI 값 None | ⚠️ 2026-07-02 확인 (이전 코드 위험) |
| `mk.get("fed_chair")` 등 신규 키 미사용 | 모든 consumer | 2026-06-18+ 신규 키 10+개 | 추가 정보 미활용 | ⚠️ cron v3 영향 적음 |
| `mi.get("divergence_note")` 등 신규 해석 필드 미사용 | 모든 consumer | 2026-06-24+ market_interpretation에 4개 필드 추가 | 추가 컨텍스트 미활용 | ⚠️ cron v3 영향 적음 |

## 검증 방법
새 Phase를 추가하거나 데이터 구조를 변경했으면 실제 JSON 출력 파일을 읽어 키 목록을 확인:
```bash
python3 -c "import json; print(json.load(open('data/macro_context.json')).keys())"
python3 -c "import json; d=json.load(open('data/macro_context.json')); print(d.get('key_macro_data',{}).keys())"
```
