# Paper Portfolio Tracker (v1.2 — 2026-07-17)

일일 포트폴리오 스냅샷(`logs/portfolio/*.json`) + yfinance 가격 데이터 기반 페이퍼 트레이딩 성과 분석 시스템.

## 데이터 소스

- **포트폴리오 스냅샷**: `~/trade-pipeline/logs/portfolio/YYYY-MM-DD.json`
  - Phase 3 `portfolio_allocation.py`가 매일 18:35 생성
  - 각 종목의 `name`, `weight`, `decision`, `reason`, `moat_score` + `cash_ratio`
- **가격 데이터**: yfinance 백필 (캐시: `data/paper_price_cache.json`)
- **성과 지표**: `data/paper_tracker_metrics.json`
- **일일 수익률**: `data/paper_tracker_daily.csv`
- **종목별 상세**: `data/paper_tracker_holdings.csv`
- **시장 분위기**: `data/paper_tracker_market.csv`
- **S&P 500 비교**: `data/paper_tracker_sp500.csv`

## 스크립트

```bash
cd ~/trade-pipeline && python3 scripts/paper_tracker.py
```

### 산출 지표

| 지표 | 의미 | 계산 |
|:-----|:-----|:-----|
| 누적수익률(전체) | 시작일~현재 총 수익률 | `Π(1 + r_i) - 1` |
| 연율화수익률 | 연간 환산 수익률 | `(1+R)^(252/n) - 1` |
| 최근 N개월 수익률 | N개월 구간 수익률 | 최근 N×22일 누적 |
| MDD | 최대 낙폭 | `min((V_i - Peak)/Peak)` |
| Sharpe Ratio | 위험 대비 수익률 | `(avg_r - rfr) / σ_r × √252` |
| 일일 변동성 | 일일 수익률 표준편차 | `σ(일일수익률)` |

### 데이터 계약

- 가격 cache는 `data/paper_price_cache.json`에 저장 (재실행 시 yfinance 재호출 방지)
- 2200 chars 메모리 cap 영향 없음 (파일 기반)
- 한국주 `.KS` ticker는 yfinance로 조회 가능 (watchlist 설정 기준)
- **당일 가격 누락**: paper_tracker는 전일 종가 기준 수익률. 당일 데이터는 다음날 yfinance 갱신 시 반영.
- **yfinance nan 방어**: `is_valid_price()` 함수로 None/nan 필터링 (`v is None or v != v`)

## CSV 파일 구조

### paper_tracker_daily.csv
```
date,daily_return,cumulative_return
2026-06-08,0.000000,1.000000
```
- `daily_return`: 일일 수익률 (decimal). 0.0079 = +0.79%
- `cumulative_return`: 누적 멀티플라이어. 1.0079 = +0.79% (대시보드에서 `(v-1)*100`으로 변환)

### paper_tracker_holdings.csv
```
date,stock,ticker,weight_pct,stock_return_pct,contrib_pct,price_prev,price_curr,reason
```
- `weight_pct`: 포트폴리오 내 비중 (%)
- `stock_return_pct`: 해당 종목 일일 수익률 (%)
- `contrib_pct`: 포트폴리오 전체 기여도 = weight × stock_return (%)
- `reason`: portfolio JSON의 stock.reason 원문 (gap×moat 포함)

### paper_tracker_market.csv
```
date,regime,cash_ratio,market_summary
```
- `regime`: 매크로 국면 (Overheat/Stagflation/Severe_Inflation 등)
- `cash_ratio`: 현금 비중
- `market_summary`: cash_reason의 Regime/Alpha-Flip 계산식 제거한 시장 설명

### paper_tracker_sp500.csv
```
date,portfolio_return,sp500_return
```
- `portfolio_return`: 포트폴리오 누적 멀티플라이어
- `sp500_return`: S&P 500 누적 수익률 (baseline=0부터). 0.018174 = +1.82%
- SPY 티커 사용, yfinance `Close` 가격 기반

## Vercel MCP 설정

```yaml
# config.yaml
mcp_servers:
  vercel:
    command: npx
    args: ['-y', '@anthropic/mcp-vercel']
    env:
      VERCEL_TOKEN: "<사용자 토큰>"
```

게이트웨이 재시작 후 `mcp_vercel_*` 도구 활성화.

## 자동 업데이트 워크플로 (제안)

18:35 파이프라인 완료 후:
1. `python3 scripts/paper_tracker.py` 실행
2. `data/paper_tracker_*.{csv,json}` 갱신
3. GitHub push → Vercel/GitHub Pages 자동 반영

## 대시보드 UI 핵심 규칙 (2026-07-16 ~ 07-17 확정)

### 누적수익률 차트
- **Y축은 반드시 0%에서 시작**할 것. 100%에서 시작 금지.
- 공식: `(cumReturn - 1) * 100` (순수익), `cumReturn * 100` 아님
- **S&P 500도 동일 baseline(0%)** 에서 시작하도록 `(price/baseline - 1) * 100` 계산

### S&P 500 비교
- SPY 티커 사용 (^GSPC 아님)
- 누적수익률 차트에 **노란색 점선(borderDash:[4,3])** 오버레이
- **fetch 실패해도 포트폴리오 차트는 정상 표시** — 반드시 try/catch로 감쌀 것
- **data 선언 후에 SP500 fetch할 것** — `spCum = data.map(...)`가 `data`보다 먼저 실행되면 ReferenceError
- **리팩토링 시 old code 완전 제거 확인** — SP500 로직을 try/catch로 옮길 때 아래 남은 spCsv 참조 코드를 삭제하지 않으면 ReferenceError로 전체 화면 먹통
- 범례: Portfolio(초록 실선 `#00d4aa`), S&P 500(노랑 점선 `#ffd93d`)

### 시장 분위기 표시
- 각 날짜 확장 영역 상단: **Regime 배지** + **시장 요약** 텍스트
- 개별 종목 reason에서 `gap XX% × moat Y/10 — ` 접두사 제거. `—` 이후 시장 맥락만 표시
  - 정규식: `x.reason.replace(/^.*?[—–-]\s*/, '')` (em dash, en dash, hyphen 모두 대응)
- reason 55자 truncation + title attr tooltip
- 시장 데이터 출처: portfolio JSON의 `regime` + `cash_reason` 필드

### 홀딩스 상세 (어코디언)
- 행 클릭/탭 → 종목별 breakdown 펼쳐짐
- 컬럼: 종목 | 비중(%) | 수익률(%) | 기여도(%) | 사유
- 현금도 별도 "종목"으로 표시 (수익률 0%, 사유 "시장 리스크 헷지")
- **사유 컬럼은 사용자 요구로 gap×moat 대신 시장 상황만 표시** (2026-07-17 교정)
- 사유 데이터: portfolio JSON의 stock.reason 필드에서 `gap XX% × moat Y/10` 부분 제거

### 페이지네이션
- **최근 30일** 기본 표시
- ◀ ▶ 화살표로 이전 구간 이동
- `page` state 변수, `pageSize = 30`
- `window.toggle(i)` 함수로 어코디언 열기/닫기

### 메트릭 카드
- 긴 텍스트(MDD 구간, 기간, 변동성) → `sm` 클래스 (13px/15px)
- 짧은 숫자(누적수익률, Sharpe, MDD) → 기본 22px/26px
- CSS: `.card .val.sm { font-size:13px; line-height:1.4; }`

### 모바일 대응
- 2열 그리드(모바일) / 4열(데스크톱) via `@media(min-width:600px)`
- 차트 높이: 200px(모바일) / 280px(데스크톱)
- 카드 tap 피드백: `scale(0.97)`
- 테이블 가로 스크롤 지원
- CSS 커스텀 프로퍼티 기반 다크 테마

## 함정

1. **한국주 2026-07-16 yfinance nan**: yfinance가 당일 장 마감 후에도 `nan` 반환 가능. `is_valid_price()` 함수로 필터링 필요.
2. **경량 데이터 + 그래프 = CSV+JSON만**: 대시보드는 정적 HTML+Chart.js. 서버사이드 로직 없음 → 데이터 파일만 갱신하면 자동 반영.
3. **Vercel MCP 재시작 필요**: `config.yaml` 수정 후 gateway 재시작해야 MCP 도구 활성화.
4. **현재 시점 가격 누락 (당일)**: paper_tracker는 전일 종가 기준 수익률. 당일 데이터는 다음날 yfinance 갱신 시 반영.
5. **🔴 SP500 코드 리팩토링 시 old code 잔여 (2026-07-17 경험)**: try/catch로 SP500 fetch를 이동할 때 `spCsv.trim().split('\n')` 참조 코드가 아래에 그대로 남으면 ReferenceError로 전체 main() 함수 중단 → 차트/테이블 모두 빈 화면. **수정 후 반드시 `grep -c "spCsv" portfolio_dashboard.html`로 1회만 참조되는지 확인.**
6. **🔴 data 선언 전 SP500 fetch (2026-07-17 경험)**: `const data = ...`보다 `spCum = data.map(...)`가 먼저 실행되면 ReferenceError. SP500 처리는 반드시 data 변수 선언 이후에 배치.
7. **파일 권한 (2026-07-17 경험)**: `portfolio_dashboard.html`이 `-rw-------`(600)이면 HTTP 서버가 읽지 못할 수 있음. `chmod 644` 권장.
8. **🔴 main() 지역변수를 render()가 접근 (2026-07-17 경험)**: `render()` 함수가 `main()`의 `const H = {}`, `const MK = {}`에 접근하면 ReferenceError: `H is not defined`. **`H`와 `MK`는 반드시 전역으로 선언** (`let page = 0, PGS = 30, ALL = [], H = {}, MK = {};`), main() 내부에서는 `H = {};`, `MK = {};`로 재할당만 할 것 (`const H = {};` 금지).
9. **🔴 다중 patch 누적 시 코드 중복 (2026-07-17 경험)**: 여러 번 patch/edit하면 old code가 완전히 제거되지 않고 그대로 남을 수 있음. 특히 try/catch 리팩토링 시 기존 참조 코드가 블록 밖에 잔존 → ReferenceError. **수정 후 반드시 `grep -c`로 중복/잔여 확인.**

## 2026-07-17 검증 결과

| 지표 | 값 |
|:-----|:---:|
| 분석 기간 | 2026-06-08 ~ 2026-07-16 (28일) |
| 누적수익률 | +0.79% |
| 연율화 수익률 | 7.38% |
| 최근 1개월 | -0.62% |
| MDD | -12.96% (6/22~7/13) |
| Sharpe Ratio | 0.31 |
| 일일 변동성 | 2.80% |
