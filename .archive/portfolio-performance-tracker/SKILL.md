---
name: portfolio-performance-tracker
description: Daily paper portfolio performance monitoring — reads portfolio allocation snapshots (logs/portfolio/), calculates cumulative return / MDD / Sharpe, generates per-stock holdings breakdown with reasoning, produces HTML dashboard with Chart.js visuals
---

# Portfolio Performance Tracker (Paper Trading)

> **철학**: 포트폴리오 비중 결정이 끝난 후, **실제로 그 결정이 얼마나 수익을 냈는지** 정량 측정.  
> 실행 중인 `fair-value-portfolio`의 출력물(logs/portfolio/)을 읽어 성과를 추적하고 대시보드로 시각화.

## 개요

| 모듈 | 역할 |
|:-----|:------|
| `scripts/paper_tracker.py` | 일일 포트폴리오 JSON → 성과 계산 → CSV/JSON 저장 |
| `data/portfolio_dashboard.html` | Chart.js 기반 모바일-퍼스트 대시보드 |
| `data/paper_tracker_daily.csv` | 일일 수익률 시계열 |
| `data/paper_tracker_holdings.csv` | 날짜×종목별 보유현황 + 배분 사유 |
| `data/paper_tracker_metrics.json` | 종합 성과 지표 |

## 데이터 흐름

```
logs/portfolio/YYYY-MM-DD.json (29+개 스냅샷)
        ↓
paper_tracker.py
        ├── yfinance로 과거 가격 백필 (price_cache.json)
        ├── 일일 가중수익률 계산 (전일비중 × 당일수익률)
        └── 종목별 상세 (stock_return, contrib, reason)
        ↓
paper_tracker_daily.csv       ← 시계열
paper_tracker_holdings.csv    ← 종목별 상세
paper_tracker_metrics.json    ← 종합 지표
        ↓
portfolio_dashboard.html      ← Chart.js 대시보드
```

## 성과 지표

| 지표 | 산식 | 설명 |
|:-----|:-----|:------|
| 누적수익률 | `Π(1+r_i) - 1` | **0% 기준** (100%→100.79%가 아니라 0%→+0.79%) |
| 연율화수익률 | `(1+C)^(252/N) - 1` | 트레이딩일수 252일 기준 |
| MDD | `min((V_t - Peak)/Peak)` | 최대 낙폭, peak-to-trough |
| Sharpe Ratio | `(R_avg - Rf) / σ_R × √252` | 무위험 3% 가정 |
| 일일 변동성 | 일일수익률 표준편차 | σ(일일수익률) |

## ⚠️ 핵심 구현 규칙 (Pitfalls)

### 1. 🔴 누적수익률 = 0% 기준
- **net return = cumReturn - 1** — 절대 100% 기준으로 표시 금지
- 사용자 교정: "누적수익률을 100%가 시작이 아니라 0이 기준이어야함"
- 차트: `(d.cumReturn - 1) * 100`, 테이블도 동일

### 2. 🔴 MDD = 누적 multiplier 기준
- MDD는 raw cumulative multiplier(`cumReturn`)로 계산
- NOT the net return (`cumReturn - 1`)
- 공식: `(v - peak) / peak` (v = cumReturn multiplier)

### 3. 🔴 현금 항목 처리
- 현금은 `paper_tracker_holdings.csv`에 포함 (비중 표시용)
- 현금 수익률 = 0%, 기여도 = 0%
- reason = "시장 리스크 헷지"

### 4. 🔴 CSV reason 컬럼 — 콤마 포함 가능
- reason 필드에 콤마(,)가 포함될 수 있음
- JS 파싱 시 `cols.slice(8).join(',')` 사용
- Python CSV writer는 `csv.writer` 자동 quote 처리

### 5. 🔴 yfinance 한국주 가격 nan 처리
- `is_valid_price()` 함수로 None/nan 체크
- nan인 종목은 해당일 계산에서 제외 (valid_stocks 0이면 0% 반환)
- 캐시에서 nan 제거: `if v is None or (isinstance(v,float) and v != v): del cache[key][date]`

### 6. 🔴 모바일 퍼스트 UI
- `maximum-scale=1.0, user-scalable=no` — 줌 방지
- CSS Grid: 모바일 2열 → 태블릿+ 4열
- 차트 높이: 모바일 200px → 데스크톱 280px
- 테이블: `overflow-x:auto` + `-webkit-overflow-scrolling:touch`
- 카드: `tap: scale(0.97)` 피드백
- 종목별 상세: **어코디언 패턴** (날짜 행 클릭 → 상세 펼침)

## 🚀 배포

| 방식 | 명령어 / URL |
|:-----|:-------------|
| **로컬 HTTP** | `cd ~/trade-pipeline/data && python3 -m http.server 9292 --bind 0.0.0.0` |
| **GitHub Pages** | `https://mybotagent.github.io/hermes-paper-portfolio/` (repo: `mybotagent/hermes-paper-portfolio`) |
| **Vercel** | GitHub repo 연결 → 자동 배포 (Vercel MCP으로 연결 가능) |

### Vercel MCP 설정
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  vercel:
    command: npx
    args: ["-y", "@anthropic/mcp-vercel"]
    env:
      VERCEL_TOKEN: "vcp_..."
```

## 실행

```bash
cd ~/trade-pipeline
python3 scripts/paper_tracker.py
```

출력: `data/paper_tracker_daily.csv`, `data/paper_tracker_holdings.csv`, `data/paper_tracker_metrics.json`

## 크론 자동화 (선택)

매일 장 마감 후:
1. `paper_tracker.py` 실행 → CSV/JSON 갱신
2. GitHub push → Vercel/GitHub Pages 자동 재배포

## 📎 관련 스킬

- **`fair-value-portfolio`**: 포트폴리오 비중 결정 (Phase 3) — 이 스킬의 input을 생성
- **`stock-rating-system`**: 종목 등급 평가 — 보유 종목에 대한 정성 평가 참조

## 참고 파일

- `references/performance-metrics-formula.md` — 지표 산식 상세
