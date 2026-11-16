# Portfolio Dashboard Design (2026-07-17)

## Claude.com Design System (2026-07-17)

> 사용자가 Claude.com의 warm cream 디자인을 요청하여 적용.
> 기존 dark-purple 테마(#06060f/#6c5ce7) → Claude 톤(#faf9f5/#cc785c)으로 전환.

### Color Palette
```css
--canvas: #faf9f5;          /* 크림 캔버스 (순수 흰색 금지) */
--surface-card: #efe9de;    /* 카드 배경 (한 단계 진한 크림) */
--surface-dark: #181715;    /* 다크 네이비 (SP500 차트, footer 용) */
--surface-dark-soft: #1f1e1b;
--surface-dark-elevated: #252320;
--ink: #141413;             /* 본문 (웜 다크, 완전 검정 금지) */
--body: #3d3d3a;            /* 부본문 */
--muted: #6c6a64;           /* 보조 텍스트 */
--muted-soft: #8e8b82;      /* 캡션 */
--primary: #cc785c;         /* 코랄 — 시그니처 포인트 컬러 */
--primary-active: #a9583e;  /* 코랄 호버 */
--hairline: #e6dfd8;        /* 1px 테두리 (크림 표면) */
--green: #5db872;           /* 성공/상승 */
--red: #c64545;             /* 에러/하락 */
--warning: #d4a017;         /* 경고 */
--on-dark: #faf9f5;         /* 다크 표면 위 텍스트 */
--on-dark-soft: #a09d96;    /* 다크 표면 위 보조 텍스트 */
```

### Typography

| 용도 | 서체 | Weight | 자간 | 크기 |
|:-----|:-----|:------:|:----:|:----:|
| 헤드라인 | **EB Garamond** (serif) | 400 | -1px | 40px |
| 메트릭 값 | **EB Garamond** (serif) | 400 | -0.5px | 24~28px |
| 본문 | **Inter** (sans) | 400 | 0 | 14~16px |
| 레이블/버튼 | **Inter** (sans) | 500 | 0.8px | 10~14px |

### Layout

- Max content width: ~1200px centered
- Section padding: 40px (metrics grid), 16px (charts), 48px (table section)
- Card padding: 24px
- Border radius: 12px (cards), 6px (buttons), pill (badges)
- Grid: 2열(mobile) / 4열(tablet+) metrics, 1열(mobile) / 2열(tablet+) charts

### Chart.js Config

#### 다크 카드 (SP500 비교 — `chart-card-dark`)
```javascript
scales: {
  x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#a09d96', font: {size:10} } },
  y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { callback: v=>v+'%', color: '#a09d96', font: {size:10} } }
}
plugins: { legend: { display: true, labels: { color: '#a09d96', font: {size:10}, usePointStyle: true, padding: 12, boxWidth: 12 } } }
```

#### 크림 카드 (일일수익률, MDD — `chart-card`)
```javascript
scales: {
  x: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: '#8e8b82', font: {size:10} } },
  y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v=>v+'%', color: '#8e8b82', font: {size:10} } }
}
```

### Component States

| 컴포넌트 | 클래스 | 설명 |
|:---------|:-------|:------|
| 다크 카드 | `chart-card-dark` | `background: var(--surface-dark)`, `grid-column: 1/-1` |
| 크림 카드 | `chart-card` | `background: var(--surface-card)`, `border-radius: 12px` |
| 메트릭 그리드 | `metrics-grid` | `gap: 1px`, 모바일 2열 / 600px+ 4열 |
| 페이지 버튼 | `paginate .btn` | `background: var(--canvas)`, `border: 1px solid var(--hairline)` |
| 시장 분위기 | `mood-bar` | Regime 배지(`rgba(204,120,92,0.08)` 배경, `#cc785c` 텍스트) |
| 어코디언 | `tr` + `detail-row` | 이벤트 위임(`data-idx` + `closest`) |

### 차트 구성 (3개)

1. **누적수익률 vs S&P 500** — 다크 카드, 코랄(#cc785c) Portfolio + 초록(#5db872) 점선 S&P 500
2. **일일수익률** — 크림 카드, 막대(초록#5db872 / 빨강#c64545)
3. **누적수익률 + MDD** — 크림 카드, 이중 Y축: 좌=코랄 누적수익률, 우=파랑(#4a8fe0) MDD
