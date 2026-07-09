# Discord Pipeline Delivery — LangGraph 크론 5분할 전송

## 개요
18:35 LangGraph 파이프라인 크론(`afebf6cb0ab1`)이 pipeline.py 실행 후 각 Phase 결과를 5개 Discord 메시지로 분할 전송.

## 크론 프롬프트 핵심 규칙 (2026-06-08 수정)

### 실행 명령어
```bash
cd ~/trading-agents-nuri && python3 pipeline.py 2>&1
```

### 5개 메시지 분할 규칙

**Message 1 — Phase 0: 밸류에이션 데이터**
- fair_value stdout에서 파싱한 종목별 T0/T1 적정가, 괴리율, Analyst Target
- `daily_snapshot.json["fair_value"]` 데이터를 표로 정리
- 컬럼: 종목·현재가·PER·적정PER·T0(T0괴리율)→T1(T1괴리율)

**Message 2 — Phase 0.5: 매크로 컨텍스트**
- `macro_context.json`에서 추출:
  - `market_interpretation.key_driver` — 핵심 동인
  - `market_interpretation.regime` — 현재 국면
  - `market_interpretation.impact_analysis` — 영향 분석
  - `key_macro_data` — Fed, CPI, WTI, USDKRW 등
  - `macro_strategy` — FRED 지표 (CPI, Sahm, Fed Rate 등)
  - `stocks[].news[].title` — Finnhub 종목별 뉴스 헤드라인 요약
- 형태: Key Driver 1줄 + Regime + 지표 요약 + 뉴스 헤드라인 5~8개

**Message 3 — Phase 1: T1 Gap Filter**
- `filtered_top10.json` 기반
- 필터 조건: `t1_gap >= 30%`, 상위 10종목
- 통과/탈락 종목 표
- 컬럼: 순위·종목·현재가·T1·Target·T1괴리율

**Message 4 — Phase 2: LangGraph 분석 결과**
- LangGraph 결과 (Phase 2 output)에서 각 종목별:
  - 결정 (BUY/HOLD/SELL) + 신뢰도
  - Bull/Bear/Risk 요약 (LLM 요약된 내용)
- 종목별 3~5줄로 간결하게
- 총 분석 종목 수 + BUY/SELL/HOLD 분포

**Message 5 — Phase 3: 포트폴리오 비중**
- `logs/portfolio/YYYY-MM-DD.json` 기반
- 포트폴리오 표: 종목·결정·비중·해자점수·근거
- 현금비중 + 현금근거 (cash_reason)
- 기대수익 + 리스크 요약
- 총 소요시간 + DeepSeek API 비용

### 출력 규칙
- terminal 출력을 그대로 복사 금지 — 핵심 데이터만 가공
- 각 Phase 사이에 구분선 `─────` 추가
- 1500자 초과 시 추가 분할 전송
- Phase 실패 시: `❌ Phase N 실패: (원인)` 표시 후 다음 Phase 진행

## Before/After 비교

Before (1개 메시지):
```
🧠 LangGraph 파이프라인
Phase 0: ... (terminal 출력 전체)
Phase 1: ... (terminal 출력 전체)
Phase 3: ... (terminal 출력 전체)
→ 2000자 넘어서 잘림, 중요한 Phase 3가 안 보임
```

After (5개 메시지, 2026-06-08):
```
📊 Phase 0: 밸류에이션 데이터 (별도 메시지)
🌍 Phase 0.5: 매크로 컨텍스트 (별도 메시지)
🔬 Phase 1: T1 Gap Filter (별도 메시지)
🧠 Phase 2: LangGraph 분석 (별도 메시지)
📊 Phase 3: 포트폴리오 비중 (별도 메시지)
→ 각 Phase를 찾기 쉬움, 잘림 없음
```

## 관련 파일
- 크론: `afebf6cb0ab1` (LLM prompt)
- pipeline: `~/trading-agents-nuri/pipeline.py`
- Phase 3: `~/trading-agents-nuri/src/agents/portfolio_allocation.py`
