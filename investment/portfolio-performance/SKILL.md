---
name: portfolio-performance
description: Daily paper portfolio performance monitoring — reads portfolio allocation snapshots (logs/portfolio/), calculates cumulative return / MDD / Sharpe, generates per-stock holdings breakdown with reasoning, produces HTML dashboard with Chart.js visuals, Vercel/GitHub Pages 배포
---

# Portfolio Performance Tracker (Paper Trading)

> **철학**: 포트폴리오 비중 결정이 끝난 후, 실제로 그 결정이 얼마나 수익을 냈는지 정량 측정.
> 실행 중인 `fair-value-portfolio`의 출력물(logs/portfolio/)을 읽어 성과를 추적하고 대시보드로 시각화.

## 개요

| 모듈 | 역할 |
|:-----|:------|
| `scripts/paper_tracker.py` | 일일 포트폴리오 JSON → 성과 계산 → CSV/JSON 저장 |
| `scripts/fix_portfolio_weights.py` | 일일 파이프라인 — 전 종목 2% 감지 시 macro 기반 비중 자동 복원 |
| `scripts/pipeline_healthcheck.py` | 전체 파이프라인 6종 검증 (파일/JSON/CSV/참조/Vercel) |
| `scripts/compute_portfolio_target.py` | 매크로 추천 → 보유종목 실제 비중 매핑 |
| `data/portfolio_dashboard.html` | Chart.js 기반 모바일-퍼스트 대시보드 |
| `data/paper_tracker_daily.csv` | 일일 수익률 시계열 |
| `data/paper_tracker_holdings.csv` | 날짜×종목별 보유현황 + 배분 사유 + **등급(grade)** + **해자점수(moat_score)** |
| `data/paper_tracker_market.csv` | 날짜별 시장 분위기 (regime, 현금비중, 요약, **뉴스**) |
| `data/paper_tracker_metrics.json` | 종합 성과 지표 |

## 데이터 흐름

```
logs/portfolio/YYYY-MM-DD.json (29+개 스냅샷)
        ↓
paper_tracker.py
        ├── yfinance로 과거 가격 백필 (price_cache.json)
        ├── 일일 가중수익률 계산 (전일비중 × 당일 수익률)
        ├── 종목별 상세 (stock_return, contrib, reason)
        └── 시장 분위기 추출 (regime, cash_reason)
        ↓
paper_tracker_daily.csv       ← 시계열
paper_tracker_holdings.csv    ← 종목별 상세
paper_tracker_market.csv      ← 시장 분위기
paper_tracker_metrics.json    ← 종합 지표
        ↓
portfolio_dashboard.html      ← Chart.js 대시보드 (Vercel/GitHub Pages)
```

## 성과 지표

| 지표 | 산식 | 설명 |
|:-----|:-----|:------|
| 누적수익률 | `Π(1+r_i) - 1` | **0% 기준** (100%→100.79%가 아니라 0%→+0.79%) |
| 연율화수익률 | `(1+C)^(252/N) - 1` | 트레이딩일수 252일 기준 |
| MDD | `min((V_t - Peak)/Peak)` | 최대 낙폭, cum multiplier 기준 |
| Sharpe Ratio | `(R_avg - Rf) / σ_R × √252` | 무위험 3% 가정 |
| 일일 변동성 | 일일수익률 표준편차 | σ(일일수익률) |

## 실행

```bash
cd ~/trade-pipeline
python3 scripts/paper_tracker.py
```

출력: `data/paper_tracker_daily.csv` + `holdings.csv` + `market.csv` + `metrics.json`

## 대시보드 기능

| 기능 | 설명 |
|:-----|:------|
| 메트릭 카드 | 누적수익률/MDD/Sharpe/변동성 등 8개 카드 |
| 누적수익률 vs S&P 500 | **다크 카드** 위 코랄(Portfolio) + 초록 점선(S&P 500) 오버레이 |
| 일일수익률 차트 | Bar chart, 초록=상승/빨강=하락 |
| 누적수익률 + MDD 통합 | **동일 차트, 좌/우 이중 축** — 같은 날짜축에서 비교 |
| 어코디언 테이블 | **이벤트 위임**(`data-idx` + `closest('.tr')`), onclick❌ |
| 시장 분위기 바 | Regime 배지 + 현금비중 + 시장 요약 |
| 페이지네이션 | ◀ [30일 윈도우] ▶ |
| 모바일 퍼스트 | Claude 디자인 시스템 (cream canvas, coral accent, serif header, dark navy cards) |

### ⚠️ 중요: 어코디언 토글 구현 (2026-07-17)

올바른 패턴 — 이벤트 위임:
```javascript
document.getElementById('tb').onclick = function(e) {
  const row = e.target.closest('.tr');
  if (!row) return;
  const idx = row.dataset.idx;
  const det = document.getElementById('d' + idx);
  if (!det) return;
  row.classList.toggle('open');
  det.classList.toggle('show');
};
```

HTML 생성 — `data-idx` 속성 사용, onclick❌:
```javascript
html += '<tr class="tr" data-idx="' + idx + '">...' + detail;
```

틀린 패턴 (onclick + querySelector — ReferenceError 위험):
```javascript
// ❌ 이렇게 하지 말것
// '<tr onclick="t('+idx+')">'
// querySelector('.tr[onclick="t('+i+')"]')  ← 브라우저 호환성 문제
```

## 배포

| 방식 | 설명 |
|:-----|:------|
| **Vercel** (선호) | GitHub repo 연결 → 자동 배포. Vercel MCP으로도 연결 가능 |
| **GitHub Pages** | `https://mybotagent.github.io/hermes-paper-portfolio/` |
| **로컬 HTTP** | `cd ~/trade-pipeline/data && python3 -m http.server 9292 --bind 0.0.0.0` |

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

### GitHub 레포
- `mybotagent/hermes-paper-portfolio`
- `index.html` (대시보드) + CSV/JSON 데이터 파일들
- push만 하면 Vercel/GitHub Pages 자동 재배포

## 🏛️ Macro Regime Dashboard (2026-07-17 v2)

**스크립트**: `scripts/generate_macro_dashboard.py` (JSON/CSV) + `scripts/generate_macro_plots.py` (PNG)

사용자의 매트플롯립 매크로 전략 코드를 대시보드용으로 포팅. v2는 연속 Risk Score 기반으로 개선.

### v2 핵심 변경사항

- **CPI 3%/5% 하드 경계** → **연속 Risk Score (0~100)** (CPI z-score 35% + Sahm 25% + HY 25% + VIX 15%)
- **12개 세부 할당** → **5단계 연속 글라이드 할당**
- **MA(10) + WTI $80 크로스오버** → **Risk Score > 50 OR (5MA 하향 + VIX > 25)**
- **백테스트**: CAGR 12.0% vs SPY 11.1%, MDD -44.7% vs -50.8%, Sharpe 0.92 vs 0.78
- **v1 대비 MDD가 2배 이상 커졌지만 out-of-sample 신뢰도 훨씬 높음**

### 데이터 소스

| 소스 | 지표 | API |
|:-----|:-----|:----|
| FRED | CPI YoY, Fed Rate, Sahm Rule, HY Spread, M2 YoY | pandas_datareader |
| yfinance | SPY, DXY, WTI, TLT, GLD, XLE, KOSPI, USD/KRW, VIX | yfinance |
| CNN (Fallback: VIX) | Fear & Greed Index | requests / yfinance |

### 출력물

| 파일 | 스크립트 | 내용 |
|:-----|:---------|:------|
| `data/macro_dashboard_data.json` | `generate_macro_dashboard.py` | 현황 (regime, risk_score, signal, CPI, Sahm, Fed, WTI, DXY, USD/KRW, M2, HY, VIX, F&G, CAGR/MDD/Sharpe, recommendation) |
| `data/macro_regime_history.csv` | `generate_macro_dashboard.py` | 시계열 (date, spy_cum, strat_cum, regime, risk_score, signal, cpi, fed, sahm, wti, dxy, usdkrw, hy, vix) |
| `data/macro_plots/plot_0~7.png` | `generate_macro_plots.py` | Matplotlib PNG 8개 패널 |
| `data/macro_plots/full.png` | `generate_macro_plots.py` | 통합 8패널 |

### 실행

```bash
cd ~/trade-pipeline && python3 scripts/generate_macro_dashboard.py
cd ~/trade-pipeline && python3 scripts/generate_macro_plots.py
```

## 대시보드 JS: try/catch 전략

```javascript
async function main(){ try{
  // 모든 메인 로직
}catch(e){ document.querySelector('.header').innerHTML += '<p>Error</p>'; }}
```

- await 포함 메인 로직: 하나의 try/catch로 감싸기
- 개별 피처(SP500, Macro, F&G): 내부 try/catch로 분리 → 하나 실패해도 나머지 정상

## ⚠️ 함정 및 사용자 선호 (Pitfalls)

### 1. 🔴 누적수익률 = 0% 기준
- **net return = cumReturn - 1** — 절대 100% 기준 표시 금지
- 사용자: "누적수익률을 100%가 시작이 아니라 0이 기준이어야함"
- 차트: `(d.cumReturn - 1) * 100`, 테이블도 동일

### 2. 🔴 MDD = 누적 multiplier 기준
- MDD는 `cumReturn` (multiplier)로 계산, NOT `cumReturn - 1`
- 공식: `(v - peak) / peak` (v = cumReturn multiplier)

### 3. 🔴 시장 분위기 우선 표시 (2026-07-17)
- **종목 배분 사유에서 gap×moat 부분을 표시하지 말 것**
- 대신 `—` 뒤의 시장 해석/증시 상황만 표시
- JS: `reason.replace(/^.*?[—–-]\s*/, '')`
- Python: `re.sub(r'^.*?[—–-]\s*', '', reason)`
- 각 날짜 상세 상단에 Regime 배지 + 현금비중 + 시장 요약 먼저 표시
- `cash_reason`에서 Alpha-Flip 계산식 제거하고 순수 시장 상황만 추출

### 4. 🔴 현금 항목 처리
- 현금은 `holdings.csv`에 포함 (비중 표시용), 수익률=0%, reason="시장 리스크 헷지"
- CSV에 `reason` 컬럼 반드시 포함 (KeyError 방지)

### 5. 🔴 CSV reason — 콤마 포함 가능
- JS 파싱: `cols.slice(8).join(',')` — split(',') 후 나머지 전부 join
- Python은 `csv.writer` 자동 quote 처리

### 6. 🔴 yfinance 한국주 가격 nan 처리
- `is_valid_price()` 함수로 None/nan 체크
- nan인 종목은 해당일 계산 제외, valid_stocks=0이면 0% 반환
- 캐시 정리: `if v is None or (isinstance(v,float) and v != v): del cache[key][date]`

### 7. 🔴 데이터 긴 값 폰트 축소
- MDD 구간, 기간, 변동성 → `.val.sm` 클래스
- 모바일 13px / 데스크톱 15px (기본: 22/26px)

### 8. 🔴 페이지네이션 — 30일 윈도우
- 테이블/차트는 30일 단위로 표시, ◀ ▶ 화살표로 이동
- 페이지 상태: `page` (0-indexed), `pageSize = 30`
- 상단 메트릭 카드는 전체 기간 기준 유지

### 9. 🔴 모바일 퍼스트 UI
- `maximum-scale=1.0, user-scalable=no` — 줌 방지
- Grid: 모바일 2열 → 600px+ 4열
- 차트 높이: 모바일 200px → 데스크톱 280px
- 테이블: `overflow-x:auto` + `-webkit-overflow-scrolling:touch`
- 카드 터치 피드백: `card:active { transform: scale(0.97) }`
- 어두운 테마: `--bg: #06060f`, `--card: #0e0e1e`, accent `#6c5ce7`

### 16. 🔴 Claude 디자인 시스템 (2026-07-17)

사용자가 **Claude.com warm cream 디자인**을 요청함. 적용 규칙:

| 토큰 | 값 | 용도 |
|:-----|:---:|:------|
| `--canvas` | #faf9f5 | 페이지 배경 (크림, 절대 pure white 금지) |
| `--surface-card` | #efe9de | 카드 배경 (캔버스보다 한 단계 진한 크림) |
| `--surface-dark` | #181715 | 다크 카드 (SP500 차트, 네이비) |
| `--primary` | #cc785c | 코랄 — 포인트 컬러 (누적수익률 라인, 강조) |
| `--ink` | #141413 | 본문 텍스트 (웜 다크, 완전 검정 금지) |
| `--muted` | #6c6a64 | 보조 텍스트 |
| `--green` | #5db872 | 성공/상승 |
| `--red` | #c64545 | 에러/하락 |

- **서체**: 헤드라인 = `EB Garamond` (serif, weight 400, 음수 자간) / 본문 = `Inter` (sans)
- **모서리**: 카드 12px, 버튼 6px, 배지 pill
- **여백**: 카드 내부 24px, 섹션 40px
- **계층**: 색상 블록 기반 (그림자 최소화) — cream → cream-card → dark → cream → coral → dark 순으로 교차

Chart.js 적용 예:
```javascript
// 다크 카드 (SP500 비교 차트) — 다크 텍스트
scales: { x: { ticks: { color: '#a09d96' } }, y: { ticks: { color: '#a09d96' } } }
// 크림 카드 (일일수익률, MDD) — 크림 텍스트
scales: { x: { ticks: { color: '#8e8b82' } }, y: { ticks: { color: '#8e8b82' } } }
```

### 17. 🔴 S&P 500 비교 — 조건부 렌더링

- `paper_tracker_sp500.csv` fetch는 try/catch로 감싸기
- 실패 시 `spCum = null` → 차트 dataset에 `...(spCum ? [{...}] : [])`로 조건부 추가
- 데이터 로드 시점: 반드시 `data` 변수 선언 **이후**
- 증상(틀린 순서): `ReferenceError: Cannot access 'data' before initialization`
- catch되면 spCum=null, 차트는 Portfolio 단독 표시

### 18. 🔴 누적수익률 + MDD 통합 차트

동일 캔버스, 이중 Y축 — **색상 구분: 누적수익률=코랄(#cc785c), MDD=파랑(#4a8fe0)**:
```javascript
new Chart(canvas, { type: 'line', data: {
  datasets: [
    { data: cum, borderColor: '#cc785c', backgroundColor: 'rgba(204,120,92,.08)', yAxisID: 'y' },
    { data: ddown, borderColor: '#4a8fe0', backgroundColor: 'rgba(74,143,224,.12)', yAxisID: 'y1' }
  ]
}, options: {
  plugins: { legend: { display: true, labels: { color: '#8e8b82', font: {size:10}, usePointStyle: true, padding: 12, boxWidth: 12 } } },
  scales: {
    x: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { maxTicksLimit: 8, color: '#8e8b82', font: {size:10} } },
    y: { position: 'left', grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v=>v+'%', color: '#cc785c', font: {size:9} } },
    y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: v=>v+'%', color: '#4a8fe0', font: {size:9} } }
  }
}});
```
- MDD는 **reverse: false** (당연히 음수, 자연스럽게 아래로)
- 2026-07-17 사용자 피드백: 빨강(#c64545) → 파랑(#4a8fe0)으로 변경 — 누적수익률(코랄)과 더 확실한 구분
- 범례 활성화 (`legend.display: true`)
- paper_tracker.py의 `NAME_TO_TICKER`에 매핑 추가 필요
- yfinance 데이터 없으면 자동 skip (0% 반영)

### 11. 🔴 JavaScript: H, MK 변수는 전역 scope
- `H` (holdings), `MK` (market)는 `render()` 함수에서 접근하므로 전역 변수여야 함
- `let page = 0, PGS = 30, ALL = [], H = {}, MK = {};` — main() 바깥에서 선언
- main() 내부에서는 `H = {};` (const ❌, let/재할당 ✅)
- 반대로 ALL도 이미 전역이지만 main()에서 `const ALL`로 재선언하면 ReferenceError 나므로 주의
- 증상: **차트/테이블 모두 빈 화면** — ReferenceError로 main() 전체 중단

### 12. 🔴 JavaScript: SP500 데이터 로드 시점
- `spCum = data.map(...)`는 **`data` 변수 선언 이후에 실행**해야 함
- try/catch로 감싸서 fetch 실패 → `spCum = null` → 차트에서 `...(spCum ? [{...}] : [])`로 조건부 렌더링
- 데이터 파일이 없어도 dashboard는 정상 작동해야 함
- 증상: `ReferenceError: Cannot access 'data' before initialization` (catch되면 spCum=null로 fallback)

### 13. 🔴 Vercel: 커밋 이메일 매칭
- Vercel 배포 시 HEAD 커밋의 author email이 GitHub 계정에 등록된 이메일과 일치해야 함
- `aiprofit@users.noreply.github.com` 같은 noreply 이메일 사용 금지
- 해결:
  ```bash
  cd repo
  git config user.email "your-actual-email@gmail.com"
  git config user.name "mybotagent"
  git commit --amend --reset-author --no-edit
  # 또는 모든 커밋 한 번에 수정:
  git filter-branch -f --env-filter '
    OLD_EMAIL="old@email.com"
    export GIT_AUTHOR_NAME="mybotagent" GIT_AUTHOR_EMAIL="new@email.com"
    export GIT_COMMITTER_NAME="mybotagent" GIT_COMMITTER_EMAIL="new@email.com"
  ' -- --branches --tags
  git push --force-with-lease
  ```
- Vercel 차단 메시지: `"The deployment was blocked because the commit email could not be matched"`

### 14. 🔴 Private repo + GitHub Pages
- GitHub Pages는 **public repo만 무료 지원**
- private 전환 시 Pages 자동 비활성화 → deploy workflow에서 404 에러
- 해결: Vercel만 사용 (private repo 배포 지원)
- GitHub Pages 관련 workflow 파일은 `.github/workflows/`에서 삭제

### 15. 🔴 S&P 500 비교 — 선택적 로드
- `paper_tracker_sp500.csv`를 fetch하되, 실패해도 dashboard 정상 작동
- JS 패턴:
  ```javascript
  let spCum = null;
  try {
    const spCsv = await fetch('paper_tracker_sp500.csv?t='+Date.now()).text();
    // ... parse
    spCum = data.map(d => spMap[d.date] !== undefined ? +(spMap[d.date]*100).toFixed(2) : 0);
  } catch(e) { console.log('SP500 unavailable:', e.message); }
  ```
- 차트 dataset: `...(spCum ? [{ data:spCum, ... }] : [])`

### 20. 🔴 종목별 reason — 정성적 분석 우선 표시 (2026-07-17)

**사용자 교정 이력**:
1. 초기: `y.rs` (raw gap×moat 계산식) 표시 → "사유 각종목마다 적도록"
2. "gap 말고..." → 정성적 분석만 표시하도록 변경
3. "사유는 정량 분석이 아닌 정성적인 분석" → 확정

**최종 패턴** — 각 종목의 reason 필드에서 `—` 뒤 정성적 분석만 추출:
```javascript
const q = y.rs || '';
const m = q.match(/[—–-]\s*(.+)/);
const qual = m ? m[1].slice(0, 45) : '';
```

**별도 컬럼으로 분리** (사용자 요청):
- **근거** 컬럼: `y.rs.slice(0, 22)` — gap×moat 계산식 요약
- **사유** 컬럼: `qual` — `—` 뒤 정성적 분석 (45자 제한)
- 시장 상황 (MK.tx)은 날짜 상단 mood-bar에 표시 (모든 종목 공통)

**paper_tracker.py** — reason 저장 시 reason 전체를 CSV에 포함 (truncation 금지):
```python
s.get("reason", "")  # full reason: "gap XX% × moat Y/10 — qualitative text"
```

### 21. 🔴 가로 화면 힌트 — 모바일 전용 표시
- 헤더 아래 `💡 가로 화면에 최적화 — 핸드폰을 눕혀서 보세요` 문구
- CSS: `.landscape-hint { display:none; font-size:11px; color:var(--muted-soft); margin-top:6px; }`
- 모바일에서만 표시: `@media(max-width:600px){ .landscape-hint { display:block; } }`
- 차트(300px)와 테이블이 가로 방향에서 더 잘 보이므로 UX 가이드

### 22. 🔴🔴 리팩토링 시 old code 잔여 — Refactoring Residue (2026-07-17)

**증상**: Dashboard가 빈 화면(ReferenceError). 모든 차트+테이블 미표시.

**원인**: SP500 fetch를 try/catch로 리팩토링하면서 `const spCsv = await fetch(...)`를 try 블록 안으로 이동했으나, 아래에 `spCsv.trim().split()`을 참조하는 **옛날 코드가 삭제되지 않고 잔여**. `spCsv`가 스코프 밖이라 ReferenceError 발생.

**방지**: 리팩토링 후 반드시 grep으로 변수 참조 확인:
```bash
grep -c "spCsv\|참조할변수명" portfolio_dashboard.html
```
참조 횟수가 예상보다 많으면 old code 잔여 의심.

**재발 방지 패턴**:
1. 리팩토링 전: 옮길 코드 블록에 주석 `// OLD-BLOCK` 표시
2. 리팩토링 후: `grep "OLD-BLOCK\|spCsv" file.html` → 0이어야 함
3. 새 기능 추가 시 try/catch로 감싼 새 블록과 기존 코드를 분리하지 말고 **전체 교체**

### 23. 🔴 등급 배지 + 뉴스 표시 (2026-07-17)

**holdings CSV** — 새로운 컬럼:
- `c[9]` = grade (durable_compounder / high_quality / constructive / fragile / low_conviction)
- `c[10]` = moat_score (1~10)

**JS 파싱**:
```javascript
H[dt].push({
  s:c[1], w:parseFloat(c[3]), r:parseFloat(c[4]), rb:parseFloat(c[5]),
  rs:c.slice(8).join(',')||'', gr:c[9]||'', ms:c[10]||''
});
```

**등급 배지 렌더링** — 종목명 옆 작은 태그:
```javascript
const gb = gr ? ' <span style="font-size:9px;background:rgba(204,120,92,.1);color:var(--primary);padding:1px 5px;border-radius:3px">'+gr.slice(0,12)+'</span>' : '';
return '<td style="font-weight:500">'+y.s+gb+'</td>...';
```

**market CSV** — 새로운 5열 `news` (파이프 구분, 최대 3개):
```javascript
MK[c[0]] = { rg:c[1], ca:c[2], tx:..., nw:c[4]||'' };
// 렌더링
const nws = mk.nw ? mk.nw.split('|').filter(x=>x.trim()).slice(0,3)
  .map(n => '<div style="font-size:10px;color:var(--muted-soft)">📰 '+n.trim().slice(0,70)+'</div>')
  .join('') : '';
```

### 24. 🔴 Multi-Factor Quality Scoring (tradingAgents 영감, 2026-07-17)

5개 Quality Factor로 등급 산출 (0~100점):
| 항목 | 가중치 | 평가 내용 |
|:-----|:-----:|:---------|
| Reliability (신뢰도) | 25% | 출처 품질, 데이터 신선도 |
| Economic Moat (해자) | 25% | 특허·독점, 네트워크효과 |
| Structural Stability | 15% | 부채비율, 시장지위 |
| Growth Quality | 20% | ROE 추세, 이익률 |
| Risk-Adjusted | 15% | 변동성, 경쟁 리스크 |

등급 체계: durable_compounder(85+) / high_quality(70-84) / constructive(55-69) / fragile(40-54) / low_conviction(0-39)

Phase 3 프롬프트에 포함된 내용. 포트폴리오 JSON의 `quality_scores.grade`와 `moat_score`로 전달.
LLM이 5개 항목 개별 점수 + 종합 점수 + grade를 출력. 등급 표시는 dashboard JS에서.

## 📎 관련 스킬
- **`fair-value-portfolio`**: 포트폴리오 비중 결정 (Phase 3) — 이 스킬의 input 생성
- **`stock-rating-system`**: 종목 등급 평가 — 보유 종목 정성 평가 참조

## 참고 파일
- `references/performance-metrics-formula.md` — 지표 산식 상세
- `references/dashboard-design.md` — 디자인 토큰, 레이아웃, 차트 설정
- `references/macro-regime-dashboard.md` — Macro Regime 분석 + 차트 + beforeDraw Plugin + 지표 차트 6종 + Fear & Greed

## ⚠️ 함정 추가 (2026-07-17)

### 25. 🔴 CSV 해상도 불일치 — Macro Regime 차트
`macro_regime_history.csv`(월별)와 포트폴리오 데이터(일별) 길이 불일치로 차트 전체 실패.
**해결**: pfLookup으로 포트폴리오 데이터를 CSV 날짜에 가장 가까운 값으로 매핑.
**방지**: 데이터 해상도 차이 확인 후 매핑 필수.

### 26. 🔴🔴 hex→rgba 변환 실패
`c.color.replace(')', ',.15)')` — hex(#cc785c)는 ')'가 없어 실패.
**해결**: 명시적 rgba 값 하드코딩. 동적 변환 금지.

### 32. 🔴🔴 복잡한 다중패널 시각화 → matplotlib PNG (2026-07-17)

**규칙**: 로그 스케일, 배경색 세그먼트, 이중 축, 해칭이 포함된 차트는 **Chart.js로 재구현하지 말고 matplotlib PNG로 표시**.

Chart.js는 단순 line/bar 차트(포폴 일일수익률, 누적, MDD)에만 사용. 매크로 전략 차트(1995~전체, 8패널, Regime 배경색)는 반드시 PNG.

**생성**:
```bash
cd ~/trade-pipeline && python3 scripts/generate_macro_plots.py
```

**표시**: `<img src="macro_plots/plot_N.png" style="width:100%;height:auto" loading="lazy">`

### 33. 🔴🔴 JS 문법 검증 (patch 후 필수) (2026-07-17)

**증상**: patch 툴로 catch 블록 교체 시 이스케이프 문제로 `}</catch(e)` 생성. 브라우저에서 모든 JS 중단.

**방지**: 매 patch 후 다음 스크립트로 검증:
```bash
python3 -c "
import re
txt = open('portfolio_dashboard.html').read()
m = re.search(r'<script>(.*?)</script>', txt, re.DOTALL)
js = m.group(1)
print('Parens:', js.count('(') - js.count(')'))
print('Braces:', js.count('{') - js.count('}'))
print('Broken:</catch:', '</catch' in js)
print('Broken:</script:', '</script' in js)
"
```

**허용 범위**: parens/braces diff는 0이어야 함. `</catch`나 `</script` 문자열이 있으면 무조건 수정 필요.

### 34. 🔴 두 개의 JSON 파일 혼동 (2026-07-17)

Dashboard는 `macro_dashboard_data.json`만 읽음. `macro_plots_status.json`은 별도.

**방지**: recommendation 같은 UX 필드는 **반드시** `generate_macro_dashboard.py`에 추가. `generate_macro_plots.py`에도 동일 로직 복제 필요. import로 공유하지 말고 복제할 것.

### 35. 🔴 전략 추천 표시 — insertAdjacentHTML 위치 (2026-07-17)

```javascript
var msEl = document.getElementById('macroSection');
if(msEl) msEl.insertAdjacentHTML('afterend', recHtml);
```

- `id="macroSection"`이 HTML에 정의되어 있어야 함
- recommendation이 `macro_dashboard_data.json`에 있어야 함
- Asset별 배지 색상: SPY=코랄, GLD=골드, TLT=초록, DXY=회색, CASH=파랑

### 36. 🔴 오버피팅 진단 프레임워크 (2026-07-17)

매크로 전략이나 포트폴리오 할당 규칙의 신뢰도를 평가할 때:

| 진단 항목 | 의심 신호 | 대응 |
|:---------|:----------|:------|
| MDD 개선 | SPY -50% → 전략 -19% (3배 개선) | 2008/2020/2022를 완벽히 피한 것 → overfitting |
| 하드 경계값 | CPI 3.0%/5.0%, WTI $80 | 해당 값으로 과거 데이터 분할이 자연스러운지 검증 |
| 세부 케이스 수 | 12개 이상 분기 할당 | 3~5개로 단순화 가능한지 확인 |
| 세부 비율 | SPY 70%+GLD 30% vs 60%+40% | 정수 10% 단위로 반올림해도 성능 유지? |
| Out-of-sample | 전체 기간 단일 백테스트 | 70% train / 30% test 분할 시 성능 유지? |

**질문**: "오버피팅이야?" → 위 표 기준으로 구체적 증거와 함께 답변. 단순 "네/아니오" 금지.

### 37. 🔴 macro recommendation → 포트폴리오 매핑 (2026-07-17)

**스크립트**: `scripts/compute_portfolio_target.py`

매핑 규칙 (Strategy v2 recommendation dict):

| 매크로 키 | 매핑 대상 |
|:----------|:----------|
| SPY X% | 포트폴리오 보유 주식 X% (현금 제외, 상대 비중 유지) |
| GLD X% | GLD ETF X% |
| TLT X% | TLT ETF X% |
| DXY X% | USD (달러) X% |
| CASH X% | 현금 X% |

SPY 매핑 계산: `target = stock_weight / stock_total * SPY_pct`

출력: `data/portfolio_target.json` → target_allocation[]

### 38. 🔴 확정적 데이터 파이프라인 (2026-07-17)

모든 데이터 생성 = shell script(no_agent). LLM 개입 없음. Dashboard는 파일만 읽음.

paper_tracker_daily.sh 실행 순서:
```bash
python3 scripts/paper_tracker.py           # 포트폴리오 성과
python3 scripts/generate_macro_dashboard.py # 매크로 데이터
python3 scripts/generate_macro_plots.py     # PNG 플롯
python3 scripts/compute_portfolio_target.py # 추천→포트폴리오 매핑
git push                                    # 데이터만 push → Vercel 자동 배포
```

금지: Chart.js로 복잡한 다중패널 차트 재구현 (→ matplotlib PNG). LLM을 데이터 생성에 개입.

### 39. 🔴 v1→v2 전략 마이그레이션 (2026-07-17)

| 항목 | v1 (제거) | v2 (현재) |
|:-----|:----------|:----------|
| Regime | CPI hard cutoff (3%/5%) | Risk Score 연속 (CPI z-score) |
| Signal | MA(10) + WTI $80 | Risk Score > 50 OR (5MA + VIX > 25) |
| 할당 | 12개 케이스 (과적합) | 5단계 글라이드 |
| 수수료 | 0.15% per switch | 없음 (연속 전환) |
| 예상 MDD | -19.4% (의심) | -44.7% (현실적) |

**주의**: `generate_macro_dashboard.py`와 `generate_macro_plots.py`는 strategy 로직이 동일해야 함. 한쪽만 업데이트하면 안 됨.

### 40. 🔬 Pipeline Health Check (2026-07-17)

**스크립트**: `scripts/pipeline_healthcheck.py`

전체 파이프라인의 상태를 자동 검증하는 health check. 매일 `paper_tracker_daily.sh` 마지막에 자동 실행.

**검사 항목**:
1. 모든 데이터 파일 존재 + 신선도 (10개, 각각 max_age_hours 검증)
2. JSON 유효성 + 필수 키 존재
3. CSV 헤더 + 행 수 검증
4. 대시보드 HTML 참조 15개 경로 일치 검증
5. portfolio_target.json 표시 코드 존재 확인
6. Vercel 배포 데이터 vs 로컬 일치 검증

**실행**: `cd ~/trade-pipeline && python3 scripts/pipeline_healthcheck.py`

**paper_tracker_daily.sh 통합**: `python3 "$SCRIPT_DIR/pipeline_healthcheck.py" 2>&1 | tail -6`

### 42. 🔴 JSON 숫자/문자열 타입 일치 — JS `.toFixed()` 호출 (2026-07-17)

**문제**: `generate_macro_dashboard.py`에서 `sahm_rule`을 f-string(`f"{latest['Sahm_Rule']:.2f}"`)으로 출력 → **문자열 `'0.07'`**. 대시보드 JS가 `mj.sahm_rule.toFixed(2)` 호출 → TypeError → `try/catch`가 전체 매크로 패널 먹통 → "Data loading..." 영구 표시.

**해결**:
```python
# ❌ 문자열 — JS .toFixed() TypeError
"sahm_rule": f"{latest['Sahm_Rule']:.2f}",
# ✅ 숫자 — .toFixed(2) 정상 동작
"sahm_rule": round(latest['Sahm_Rule'], 2),
```

**교훈**: 대시보드 JS가 `.toFixed()`, `.toLocaleString()` 등 Number 메서드를 호출하는 키는 반드시 Python에서 숫자형(int/float)으로 출력할 것.
- `f"{val:.1f}%"` 같이 '%'나 '$' 접미사가 붙는 값은 문자열이어도 OK (JS에서 텍스트로만 표시)
- `.toFixed()`를 호출하는 키는 반드시 raw number

**발견 방법**: Vercel 데이터 확인:
```bash
python3 -c "import json; d=json.load(open('/tmp/macro_dashboard_data.json')); print({k:type(v).__name__ for k,v in d.items() if isinstance(v,str) and k!='desc'})"
```

### 44. 🔴 포트폴리오 비중 자동 복원 (2026-07-17)

**문제**: LLM이 극단적 이벤트(KOSPI 폭락 등)에 과민반응 → 전 종목 최소 2% + 현금 40%.

**해결**: `scripts/fix_portfolio_weights.py`가 일일 파이프라인에서 실행:
1. 최신 portfolio JSON에서 전 종목 2% 감지
2. 최근 정상 템플릿(2026-07-01 기준)의 비중 복원
3. Macro Goldilocks(Risk-On) → 현금 10%, SPY 100% 추천 기준으로 주식 90% 분배
4. `paper_tracker.py` 재실행 → CSV/JSON 재생성

**트리거**: `paper_tracker_daily.sh`에서 `generate_macro_dashboard.py` 이후 자동 실행.

### 45. 🔴 애널리스트 컨세서스 데이터 수집 (2026-07-17)

**스크립트**: `scripts/collect_consensus.py`

일일 파이프라인 4번째 단계로 편입 (generate_macro_plots.py 직후, fix_portfolio_weights.py 직전). yfinance의 `earnings_estimate`, `revenue_estimate`, `info`, `calendar` API를 사용해 각 종목의 다음 분기/다음 해 EPS, 매출, 애널리스트 목표가, 추천 의견을 수집.

**수집 항목 (종목별)**:
- 현재가 / 목표가 (mean/high/low) / 상승여력
- 애널리스트 추천 (Strong Buy~Sell, 점수, 분석가 수)
- 다음 분기 / 다음 해 EPS 컨세서스
- 다음 분기 / 다음 해 매출 컨세서스
- Fwd P/E / PEG Ratio / 매출성장률 / EPS성장률
- 다음 실적 발표일 + EPS/매출 예상 범위

**Python 핵심 패턴**:
```python
t = yf.Ticker(ticker)
info = t.info or {}
ee = t.earnings_estimate      # DataFrame: index=[0q,+1q,0y,+1y], columns=[avg,low,high,yearAgoEps,...]
re = t.revenue_estimate        # DataFrame: index=[0q,+1q,0y,+1y], columns=[avg,low,high,...]
cal = t.calendar or {}         # dict: Earnings Date, Earnings Average, Revenue Average, etc.
```

**에러 처리**: 각 종목별 try/except. 하나가 실패해도 나머지 정상 진행. 네트워크 타임아웃(30s)만 주의.

**출력**: `data/consensus_data.json` (Vercel push 대상, `.gitignore` 우회하여 `-f add`)

**대시보드 표시**: `fetch('consensus_data.json')` → try/catch → 각 종목 4열 그리드: 종목명+등급 | 현재가/목표가/상승여력 | Fwd P/E | 다음분기 EPS / 다음해 EPS | 매출 | 실적일.

**수집 대상**: MU, HPE, 005930.KS(삼성전자), 000660.KS(SK하이닉스), MSFT, NVDA, AVGO, STX, 011070.KS(LG이노텍), WDC
