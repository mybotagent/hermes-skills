# Recency-Weighted Target Price Calibration

> tradingAgents `lib/recency.py` + `lib/conflict.py` 아키텍처 기반.
> 스크립트: `collect_recent_targets.py` → `recent_targets.json` → `collect_consensus.py`에서 calibration 적용.

## Architecture (tradingAgents 패턴)

### 1. Source Registry
각 source는 독립적, tier + weight + reference 보유:

| Source | Tier | Weight Base | Type | 데이터 |
|:-------|:----:|:----------:|:----:|:------|
| Yahoo Finance Consensus | B | 1.0 | target_mean | targetMeanPrice + numberOfAnalystOpinions |
| Yahoo Finance Median | B | 0.8 | target_median | targetMedianPrice (mean과 다를 때) |
| Analyst Sentiment Trend | B | 0.5 | sentiment_delta | recommendation trends 월별 buy ratio 변화 |
| Analyst High Estimate | C | 0.3 | target_high | targetHighPrice (낙관 시나리오) |
| Analyst Low Estimate | C | 0.3 | target_low | targetLowPrice (비관 시나리오) |
| Individual Analyst Web (v2) | **A** | 3.0 | analyst_report | Google News RSS → 추출된 개별 analyst target (firm + target price + date) |
| Web News (RSS) | C | 0.1~1.0 | news_mention | Google News RSS 최근 30일 analyst 액션 (target price 없음) |

### 2. Recency Budgets (tradingAgents `lib/recency.py`)

| Data Type | Budget (days) |
|:----------|:------------:|
| target_price | 14 |
| recommendation | 30 |
| web_news | 7 |

### 3. Recency Weighting
```
weight = tier_weight_base × recency_weight
- recency_weight: 0~1 (days_old / budget 비율 기반, max 0.1)
- web_news: max(0.1, 1.0 - days_old/30)
```

### 4. Synthesis (tradingAgents `lib/conflict.py` `weighted_synthesis`)
```
weighted_target = Σ(value_i × weight_i) / Σ(weight_i)
```

### 5. Calibration Factor
```
calibration_factor = weighted_target / existing_targetMeanPrice
- ×1.0 = 정확히 일치
- >1.0 = weighted target이 기존보다 높음 (상향 신호)
- <1.0 = weighted target이 기존보다 낮음 (하향 신호)
```

## Output: `data/recent_targets.json`

```json
{
  "date": "2026-07-17",
  "tickers": {
    "MU": {
      "current_price": 904.28,
      "recommendation": {"score": 1.42, "label": "Strong Buy", "n_analysts": 42},
      "sources": [
        {"firm": "Yahoo Finance Consensus", "date": "2026-07-17",
         "value": 1489.57, "tier": "B", "weight": 1.0,
         "ref": "Yahoo Finance Consensus (42 analysts)",
         "url": "https://finance.yahoo.com/quote/MU/"},
        {"firm": "Analyst Sentiment Trend", "date": "2026-07-17",
         "value": 0.02, "tier": "B", "weight": 0.5,
         "ref": "Buy ratio 85% (전월 83%) — 유지"}
      ],
      "synthesis": {"weighted_target": 1482.72, "confidence": "high", "n_sources": 3},
      "existing_target": "1,489.57",
      "calibration_factor": 0.9954,
      "references": [
        {"type": "target_mean", "ref": "Yahoo Finance Consensus (42 analysts)",
         "url": "https://finance.yahoo.com/quote/MU/", "value": 1489.57}
      ]
    }
  }
}
```

## Pipeline Integration

```bash
# 1. Recent targets 수집 (tradingAgents multi-source)
python3 scripts/collect_recent_targets.py
# → data/recent_targets.json

# 2. Consensus 수집 (calibration 포함)
python3 scripts/collect_consensus.py
# → collect_recent_targets.py의 calibration_factor 적용
# → data/consensus_data.json
```

### v2: Web Search for Individual Analyst Targets (2026-07-17)

`collect_recent_targets.py` v2는 yfinance 집계값 외에도 Google News RSS로 **개별 애널리스트 리포트**를 수집한다.

### 검색 방식
US ticker 기준 3개 검색어:
1. `"{ticker} {name} analyst price target upgrade downgrade"`
2. `"{ticker} stock analyst rating target"`
3. `"{ticker} analyst upgrade downgrade target price"`

### Target Price 추출 (`_extract_target_price`)
- `$XXX` / `₩XXX` 정규식 추출
- Market cap 필터: `$X` 뒤 `B/T/M` 문자 → skip ($319B 등)  
- Price sanity: `current_price * 0.5` ~ `current_price * 5.0` 범위 외 skip
- `re.finditer`로 모든 매치 검색 (기존 `re.search` 단일 매치 → `re.finditer` 다중 매치)

### Firm 추출 (`_extract_firm`)
- 50+ analyst firm dictionary (Goldman Sachs, Morgan Stanley, JP모건, 미래에셋, KB증권 등)
- Matching by longest substring first (sorted by len, reverse)
- Fallback: 콜론/대시 앞쪽 문자열

### Action Tracking
- upgrade / downgrade / initiate keyword detection
- `sources[].action` 필드에 저장

### 종목당 현황

| 종목 | 총 sources | web analyst reports |
|:----|:---------:|:------------------:|
| MU, NVDA, MSFT, STX, WDC, HPE | 15 | **10** ✅ |
| AVGO, CLS | 11 | **6** ✅ |
| SK하이닉스 | 10 | **5** ✅ |
| 삼성전자 | 6 | 1 |
| LG이노텍, 현대차, 기아 | 5 | **0** ❌ |

> **한국주 한계**: 영문 Google News RSS는 한국주(LG이노텍·현대차·기아) analyst coverage 거의 없음.
> web source 0개여도 yfinance baseline은 유지, calibration_factor = 1.0 (변화 없음).

## 실행: `scripts/collect_recent_targets.py`

```bash
cd ~/trade-pipeline && python3 scripts/collect_recent_targets.py
```

14개 포트폴리오 종목 각각에 대해:
1. yfinance target_mean/median/high/low + recommendation
2. yfinance recommendation trends (월별 buy ratio 변화)
3. **v2: Google News RSS 3개 검색어로 개별 analyst 리포트 수집 (Tier A, 5~10개/ticker)**
4. Weighted synthesis + calibration factor 출력 + per-source references (firm, date, value, url, action)

## Dashboard 표시

Consensus card에서 calibration factor 표시:
- 목표주가 옆 `×0.9954` 배지
- ⚙️ 보정 줄: `1,489.57 → 1,482.72`
- cal=1.0이면 표시 생략 (변화 없음)

## 주의사항

1. **yfinance targetMeanPrice는 aggregate — stale 위험**: 42명 analyst 평균이지만 개별 업데이트 시점 불명. Sentiment trend로 보완.
2. **upgrades_downgrades는 2012년 데이터**: yfinance의 개별 analyst track은 10년 이상 stale. 사용 불가.
3. **Web news RSS는 Tier C 참고용**: Google News RSS의 한국어 검색은 정확도 낮음. US주 위주로 동작.
4. **Calibration factor가 1.0에 근접하면 큰 의미 없음**: ±2% 이내는 노이즈, ±5% 이상일 때만 실질적 의미.
5. **한국주 targetMedianPrice는 yfinance에서 somsang**: 한국주(.KS)는 numberOfAnalystOpinions이 yfinance에서 제공되지 않을 수 있음.
6. **📌 RSS 날짜 파싱 — timezone suffix 제거 필수**: Google News RSS는 `"Thu, 09 Jul 2026 13:47:11 GMT"` 형식. `[" GMT"," UTC"," EST"," EDT"," PST"," PDT"]` 접미사 제거 후 `strptime()` 호출.
7. **📌 Market cap vs Target price 오인식 방지**: `$319B` → market cap으로 간주 skip (뒤에 B/T/M 문자 확인).
8. **📌 Analyst firm dictionary 유지보수**: 새 analyst firm 발견 시 `ANALYST_FIRMS` 리스트 업데이트 필요.
9. **📌 KR ticker web search limitation**: 한국주 4개(LG이노텍·현대차·기아·에이피알)는 web source 0개. calibration_factor = 1.0으로 fallback.
