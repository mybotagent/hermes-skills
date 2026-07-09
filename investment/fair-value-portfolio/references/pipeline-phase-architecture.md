# Pipeline Phase Architecture (2026-06-07)

## 크론 → 파이프라인 실행 순서 (저녁 타임라인)

```
18:00 🇺🇸 US 브리핑 스킬 (LLM)
  ├─ fair_value.py 실행 → data/fair_value_stdout.txt 저장
  ├─ analyst_target_collector.py 실행 → data/analyst_stdout.txt 저장
  └─ 브리핑 리포트 Discord 전송

18:30 🌍 매크로 리포트 크론 (LLM)
  ├─ web_search: 글로벌 매크로 데이터 수집
  ├─ web_search: 한국주 6종목 뉴스 수집
  ├─ 리포트 작성 + Discord 전송
  └─ data/macro_context.json 저장
       ├─ macro_report_summary (리포트 전문)
       ├─ key_macro_data (Fed rate, DXY, WTI, CPI 등)
       ├─ market_interpretation (key_driver, regime, impact_analysis)
       └─ news_items (글로벌 뉴스)

18:35 🧠 LangGraph 파이프라인 (no_agent, ~/.hermes/scripts/run_pipeline.sh)
  └─ python3 pipeline.py
       ├─ Phase 0: stdout 파일 읽기 → daily_snapshot.json
       │   (subprocess 재실행하지 않음 — 저장된 파일만 파싱)
       ├─ Phase 0.5: macro_context.json 읽기 + Finnhub US뉴스 수집 → 저장
       ├─ Phase 1: Midpoint Filter → filtered_top10.json (상위 7종목)
       ├─ Phase 2: LangGraph 5회 LLM 호출 (Context→Bull∥Bear∥Risk→Facilitator)
       │           → logs/decisions/stocks/*.md + logs/decisions/YYYY-MM-DD.json
       └─ Phase 3: 포트폴리오 비중 → logs/portfolio/YYYY-MM-DD.json
```

## 중요: 크론 wrapper 스크립트 경로 검증

- `~/.hermes/scripts/run_pipeline.sh` → `cd /home/ubuntu/trading-agents-nuri`
- `~/.hermes/scripts/run_monthly_review.sh` → `cd /home/ubuntu/trading-agents-nuri`
- **절대 `trading-agents-nuri-langgraph` 또는 `trading-agents-nuri-scripts` 사용 금지** (구 레포)
- 확인: `cat /home/ubuntu/.hermes/scripts/run_*.sh`

## 데이터 파일 체인 (하루치만 보관, 다음날 덮어씀)

| 파일 | 생성자 | 소비자 | 보존 |
|:----|:------|:------|:----:|
| `data/fair_value_stdout.txt` | 08:10/18:00 스킬 | pipeline Phase 0 | 덮어씀 |
| `data/analyst_stdout.txt` | 08:10/18:00 스킬 | pipeline Phase 0 | 덮어씀 |
| `data/macro_context.json` | 18:30 LLM + Phase 0.5 | pipeline Phase 2 | 덮어씀 |
| `data/daily_snapshot.json` | pipeline Phase 0 | Phase 1 | 덮어씀 |
| `data/filtered_top10.json` | pipeline Phase 1 | Phase 2 | 덮어씀 |
| `logs/decisions/YYYY-MM-DD.json` | pipeline Phase 2 | 보존 (히스토리) | 영구 |
| `logs/portfolio/YYYY-MM-DD.json` | pipeline Phase 3 | 월간 리뷰 | 영구 |
| `logs/validation/YYYY-MM-DD.json` | decision_validator | 월간 리뷰 | 영구 |
| `logs/monthly_review/YYYY-MM.md` | monthly_performance_review | 피드백 | 영구 |
