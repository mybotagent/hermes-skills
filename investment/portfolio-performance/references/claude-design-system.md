# Claude.com Design System Reference

> 대시보드 디자인에 적용된 Anthropic Claude.com 디자인 시스템.
> 출처: 사용자가 제공한 Claude.com design spec + 실제 적용 결과.

## 철학

- **Warm cream canvas** (#faf9f5) — 절대 pure white 사용 금지. "크림"이 브랜드 차별화.
- **Coral accent** (#cc785c) — Anthropic 시그니처. CTA, 강조 라인, 포인트 컬러.
- **Dark navy surface** (#181715) — 코드 에디터, 다크 카드, 푸터.
- **서체 이중 구조**: Display = serif (EB Garamond, weight 400, 음수 tracking) / Body = sans (Inter)
- **색상 블록 기반 계층** (그림자 최소화) — cream → cream-card → dark → coral 순으로 교차

## 색상

| 토큰 | 값 | 용도 |
|:-----|:---:|:------|
| `--canvas` | #faf9f5 | 페이지 배경 |
| `--surface-card` | #efe9de | 카드 배경 |
| `--surface-dark` | #181715 | 다크 카드 |
| `--surface-dark-elevated` | #252320 | 다크 내부 카드 |
| `--ink` | #141413 | 본문/헤드라인 |
| `--body` | #3d3d3a | 본문 텍스트 |
| `--muted` | #6c6a64 | 보조 텍스트 |
| `--muted-soft` | #8e8b82 | 캡션, 저작권 |
| `--primary` | #cc785c | 코랄 — 포인트 |
| `--primary-active` | #a9583e | 코랄 hover |
| `--hairline` | #e6dfd8 | 1px 경계선 |
| `--green` | #5db872 | 성공/상승 |
| `--red` | #c64545 | 에러/하락 |
| `--warning` | #d4a017 | 경고 |
| `--on-dark` | #faf9f5 | 다크 위 텍스트 |
| `--on-dark-soft` | #a09d96 | 다크 위 보조 텍스트 |

## 서체

| 역할 | 폰트 | weight | 특징 |
|:-----|:-----|:------:|:-----|
| 헤드라인 | **EB Garamond** (serif) | 400 | 음수 letter-spacing (-0.3~-1.5px), bold 금지 |
| 본문 | **Inter** (sans) | 400~500 | Humanist sans, 절대 geometric 금지 |
| 코드 | JetBrains Mono | 400 | 코드 블록 |

**대체 폰트**: Copernicus/Tiempos Headline (유료) → Cormorant Garamond (오픈소스)
StyreneB (유료) → Inter (오픈소스)

## 모서리 (Border Radius)

| 토큰 | 값 | 용도 |
|:-----|:---:|:------|
| `rounded.md` | 8px | 버튼, 입력 |
| `rounded.lg` | 12px | 카드 |
| `rounded.xl` | 16px | 히어로 |
| `rounded.pill` | 9999px | 배지, 태그 |

## 여백

- 카드 내부 패딩: 24~32px
- 섹션 간격: 40px (모바일) / 96px (데스크톱, Claude 원칙)
- 버튼 높이: 40px

## 적용 규칙 (Do / Don't)

### Do
- 크림 캔버스에 배경 고정. pure white 금지.
- 헤드라인은 serif (EB Garamond), 본문은 sans (Inter).
- 코랄은 **희소하게** — CTA와 주요 강조에만.
- 다크 카드는 코드/SP500 비교 등 실제 제품 크롬 표시에 사용.
- 카드 배경은 크림 → 다크 교차 배치.

### Don't
- 차가운 회색/파랑 계열 사용 금지 (코랄이 유일한 브랜드 컬러).
- serif에 bold(700) 사용 금지 — 400 유지.
- Inter를 헤드라인에 사용 금지 — 반드시 serif.
- 모든 요소에 코랄 칠하지 말 것 — 희소성이 핵심.
- 그림자 과다 사용 금지 — 색상 블록이 깊이감을 만듦.

## Chart.js 적용 예

### 다크 카드 텍스트 (SP500 비교)
```javascript
scales: {
  x: { ticks: { color: '#a09d96' } },
  y: { ticks: { color: '#a09d96' } }
}
```

### 크림 카드 텍스트 (일일, MDD)
```javascript
scales: {
  x: { ticks: { color: '#8e8b82' } },
  y: { ticks: { color: '#8e8b82' } }
}
```

### 누적수익률 + MDD 통합 차트 — 이중 축
```javascript
datasets: [
  { data: cum, borderColor: '#cc785c', yAxisID: 'y' },     // 좌축: 코랄
  { data: ddown, borderColor: '#4a8fe0', yAxisID: 'y1' }   // 우축: 파랑
]
scales: {
  y:  { position: 'left',  ticks: { color: '#cc785c' } },
  y1: { position: 'right', ticks: { color: '#4a8fe0' }, grid: { drawOnChartArea: false } }
}
```
