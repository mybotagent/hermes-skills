# Capture Pipeline: stdout → JSON → Midpoint Filter → LangGraph

> **현행 아키텍처 (2026-06-06 v3)**

기존 cron 스크립트(`fair_value.py`, `analyst_target_collector.py`)는 **print()로만 출력**한다.
**더 이상 subprocess로 재실행하지 않는다** — 대신 크론 프롬프트 내에서 stdout을 파일로 저장한다.

## 데이터 흐름 (3-Stage Pipeline)

```
┌─ 08:10 / 18:00 크론 ─────────────────────────────────────┐
│ fair-value-portfolio 스킬 로드                              │
│ → fair_value.py > data/fair_value_stdout.txt              │
│ → analyst_target_collector.py > data/analyst_stdout.txt   │
│ → Hermes stdout → Discord (원본 유지)                      │
└───────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─ 18:30 크론 ─────────────────────────────────────────────┐
│ 🌍 매크로 전략 리포트 (LLM 기반)                           │
│ → web_search로 지난 24~48시간 글로벌 이슈 수집              │
│ → 리포트 생성 + 시장 해석(key_driver/regime/impact)         │
│ → JSON 저장: data/macro_context.json                      │
│   {macro_report_summary, market_interpretation,           │
│    key_macro_data, news_items}                            │
│ → Hermes stdout → Discord (원본 유지)                      │
└───────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─ Pipeline (18:35 수동 / cron 미등록) ────────────────────┐
│ Phase 0: capture_and_save.py                             │
│   → fair_value_stdout.txt + analyst_stdout.txt 읽기       │
│   → data/daily_snapshot.json 저장                         │
│                                                          │
│ Phase 0.5: collect_macro_context.py                      │
│   → macro_context.json 읽기 (18:30 크론이 저장한 것)       │
│   → Finnhub API로 필터 통과 종목 뉴스 3건씩 수집           │
│   → 기존 macro_context.json에 stocks[] 필드 추가           │
│   → data/macro_context.json 덮어쓰기 (정보 보존+확장)      │
│                                                          │
│ Phase 1: midpoint_filter.py                              │
│   → daily_snapshot.json → 중간값 괴리율 계산               │
│   → 괴리율 ≥ 30% 상위 10종목 → data/filtered_top10.json   │
│                                                          │
│ Phase 2: LangGraph Pipeline (7~10종목)                   │
│   → filtered_top10.json + macro_context.json 읽기         │
│   → 각 종목별 Context→Bull∥Bear∥Risk→Decision Maker      │
│   → 리포트 저장 + Discord 전송                            │
└───────────────────────────────────────────────────────────┘
```

## macro_context.json 구조 (18:30 크론 → Phase 0.5)

```json
{
  "timestamp": "2026-06-06T18:30:00+09:00",
  "date": "2026-06-06",

  "macro_report_summary": "리포트 전문 (Executive Summary + Current Macro State + Causal Linkage + Counter-factual + Structural Implications + Priority Matrix)",

  "key_macro_data": {
    "fed_rate": "4.25~4.50%",
    "ecb_rate": "2.00%",
    "boj_rate": "0.50%",
    "dxy": "104.2",
    "usdkrw": "1320",
    "us10y": "4.45%",
    "wti": "68.5",
    "cpi_yoy": "2.7%",
    "nonfarm": "+172K"
  },

  "market_interpretation": {
    "key_driver": "트리플 악재 — 칩 수출통제 강화 + 고용 쇼크 + 반도체 업종 매도",
    "market_sentiment": "risk-off",
    "regime": "Overheat / Slowdown / Goldilocks 등",
    "impact_analysis": "포트폴리오 종목군별 인과관계 설명"
  },

  "news_items": [
    {"title": "제목", "source": "Reuters", "impact": "high", "summary": "...", "affected_tickers": ["NVDA", "MU"]}
  ],

  "stocks": [
    {"name": "엔비디아", "ticker": "NVDA", "news": [{"title": "...", "summary": "...", "url": "..."}]}
  ]
}
```

**세 필드의 차이점:**
| 필드 | 내용 | 용도 |
|:-----|:-----|:-----|
| `macro_report_summary` | 전체 리포트 텍스트 (∼3000자) | Context agent에 raw 리포트로 전달 |
| `market_interpretation` | 구조화된 시장 해석 (key_driver/regime/impact) | Bull/Bear/Risk/Decision에 구조화된 정보로 전달 |
| `key_macro_data` | 숫자 데이터만 (fed_rate, dxy 등) | Bull/Bear 정량적 인용 |

## 데이터 주의사항

1. **macro_context.txt로 저장 금지**: 반드시 JSON(`macro_context.json`)으로 저장. 이유: `collect_macro_context.py`가 Finnhub 뉴스를 추가할 때 JSON 읽기/쓰기가 편리함. txt 파일을 따로 만들면 두 파일 간 동기화 문제 발생.

2. **시장 해석 필수**: 18:30 크론은 단순 수치 나열 금지. `market_interpretation.key_driver`, `market_interpretation.regime`, `market_interpretation.impact_analysis`를 반드시 포함해야 함. 이 필드들이 LangGraph Bull/Bear/Decision에 직접 인용됨.

3. **일간 저장/폐기**: `data/` 디렉토리에 하루치만 보관. 다음날 06:00 KST Cleanup 크론이 삭제 → 08:10/18:00 크론이 새 데이터로 생성.

4. **Cleanup 상세 (06:00 KST 평일)**:

4. **Cleanup 상세 (06:00 KST 평일)**: `cleanup_daily_data.py`가 실행. 삭제 대상: `fair_value_stdout.txt`, `analyst_stdout.txt`, `daily_snapshot.json`, `filtered_top10.json`, `macro_context.json`, `logs/decisions/stocks/*`. 보존: `logs/decisions/*.md`, `logs/decisions/*.json` (히스토리).

5. **매크로 리포트 없는 경우**: 18:30 크론 미실행 시 Phase 0.5는 `macro_report_summary=""`, `market_interpretation={}` 상태로 저장. LangGraph는 이 경우 매크로/뉴스 없이 PER 데이터만으로 분석.
