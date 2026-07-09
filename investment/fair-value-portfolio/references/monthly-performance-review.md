# Monthly Performance Review

## Overview
매월 1일 08:10 KST 실행. 지난달 LangGraph 결정 데이터 + 포트폴리오 할당 데이터를 DeepSeek V4 Flash로 분석.

## Data Sources
- `logs/decisions/YYYYMM*.json` — timestamp, results[].decision/confidence/mid_gap/fair_pe/current_pe, cost_summary
- `logs/portfolio/YYYY-MM*.json` — date, regime, cash_ratio, stocks[].name/decision/weight

## Collection Logic (`collect_decisions`)
1. 현재 날짜 기준 `get_last_month_range()`로 지난달 범위 계산
2. `logs/decisions/`에서 `YYYYMM` prefix 매칭 → JSON 파싱
3. 각 파일의 `results[]`에서 decision/confidence/mid_gap 추출
4. `cost_summary`에서 "이번달: X$ (Y원)" 파싱 (마지막 파일만 사용 — 이미 월 누적값)
5. 종목별 평균 괴리율 계산

## Collection Logic (`collect_portfolios`)
1. `logs/portfolio/`에서 날짜 범위 매칭
2. 각 파일의 regime, cash_ratio, stocks[] 추출

## LLM Prompt Structure
1. 결정 현황 (총 실행/결정, BUY/SELL/HOLD 분포)
2. 종목별 결정 요약 (decision count + 평균 괴리율)
3. 포트폴리오 할당 이력 (날짜별 Regime/현금/비중)
4. 비용 (월 총 비용, 예산 대비 %)
5. 분석 요청 (결정 패턴, 포트폴리오 평가, 방법론 개선)

## Cost
- DeepSeek V4 Flash: ~500 input + ~1000 output tokens = ~$0.03
- 1회/월 = ~45원

## Storage & Feedback Loop

### 저장 경로
- **리포트 파일**: `trading-agents-nuri-langgraph/logs/monthly_review/YYYY-MM.md`
- **원천 데이터**: `logs/decisions/YYYYMM*.json` (지난달), `logs/portfolio/YYYY-MM*.json`

### 피드백 레포
- **GitHub**: `mybotagent/trading-agents-nuri-feedback` (private, 2026-06-07 생성)
- **README**: 분석 항목 설명 + 개선 제안 라이프사이클 포함
- **개선 제안 흐름**: 리포트 생성 → GitHub Issue 등록 → 검토 → 구현 → 효과 검증 (순환)

### 결정 검증(Validation) 통합 (2026-06-07 추가)

`monthly_performance_review.py`의 `main()` 함수가 `collect_validation(month_label)`로 `logs/validation/` 최신 JSON을 읽음.

**통합 내용**:
- `build_prompt()`에 validation 데이터 섹션 추가 (Section 5: 결정 검증 결과)
  - 검증 대상 총 건수, BUY 정확도(%), BUY 평균 수익률, HOLD 관찰 수익률
  - 종목별 현재 상태 (결정 + 수익률)
- 리포트 헤더에 검증 요약 표시
- LLM 프롬프트 순서 변경: 1~4(기존) → 5(검증) → 6(분석 요청)

**검증 데이터 출처**: `decision_validator.py`가 생성한 `logs/validation/YYYY-MM-DD.json`
- `summary.accuracy_pct` — BUY 정확도
- `summary.avg_buy_return` — BUY 평균 수익률  
- `summary.avg_hold_return` — HOLD 관찰 수익률
- `ticker_latest.{name}.decision/return_pct` — 종목별 현황

## Caveats
- `__file__` 기반 경로 계산 → no_agent 실행 시 `~/.hermes/scripts/` 기준. LANGGRAPH_DIR = `/home/ubuntu/trading-agents-nuri-langgraph`.
- `.env` 파일에서 DEEPSEEK_API_KEY 로드 (python-dotenv, LANGGRAPH_DIR/.env)
- dotenv + httpx 패키지는 `venv/`에만 설치 → 실행 시 venv Python 사용 필수 (shell wrapper)
