# PE/FPE Ratio vs Model Accuracy Analysis

> 발견일: 2026-06-02 (초기) / 2026-06-03 (갱신: cycle cap 20 + BPS retained)
> 컨텍스트: Orbit v2 PER+PBR 혼합 모델의 T1과 analyst target 비교

## 핵심 발견 1: PE/FPE 비율 구간별 정확도

PER+PBR 혼합 모델(고정 PER75%:PBR25%, cycle cap 20)의 T1 적정가는 **PE/FPE 비율**에 따라 analyst target 대비 정확도가 결정됨.

### 🟢 PE/FPE 1.5~2.5 (최적 구간, ±20%)
- Forward EPS가 trailing보다 50~150% 높음 (적절한 성장 기대)
- PBR anchor가 과도하지도, 너무 약하지도 않음
- 해당 종목: NVDA(1.94), TSM(1.67), DELL(2.29), LLY(1.58), CLS(1.82)

### 🔺 PE/FPE > 3.0 (과대추정 구간, cycle cap 20 적용 시 개선됨)
- **v2026-06-03 대응**: 사이클리컬 fair_pe 상한 20 으로 과대추정 완화
  - MU: $1,732 (-1% vs high $1,750) 🎯
  - SNDK: $2,844 (-12.5% vs high $3,250) ✅
- 단, KR 주식(삼전/하이닉스)은 trailingPE가 재무제표 기준(PE 40~50)이라 PE/FPE가 크지만, market='KR' 조건으로 cycle cap 적용됨
- **여전히 과대**: SK하이닉스(FPER 6.2) — Forward EPS 자체가 너무 커서 cap으로 해결 불가

### 🔻 PE/FPE < 1.5 (과소추정 구간)
- Analyst들은 브랜드, 모트 등 정성 요소를 higher multiple로 반영
- **대응**: 저성장 고모트 기업(AAPL, MSFT, GOOGL)은 PBR anchor 과도 가능성 인지

## 핵심 발견 2: yfinance Analyst Mean Target Staleness

| 종목 | 추천등급 | 현재가 | Mean Target | 문제 |
|:----|:-------:|:-----:|:----------:|:----:|
| MU | strong_buy (1.48) | $1,064 | **$726** | 강력매수인데 32% 하락 target? |
| SNDK | buy (1.55) | $1,716 | **$1,609** | 매수인데 현재가보다 낮음? |
| 삼성전자 | strong_buy (1.38, 37명) | ₩360,500 | **₩397,803** | strong_buy인데 +10%뿐? FPER 6.5→ implied PER 7.1x |

- **원인**: 주가 급등 후 analyst target 업데이트가 yfinance에 미반영
- **대응**: `targetHighPrice`가 mean보다 현재 시장 상황에 더 가까울 수 있음

## Model T1 vs Analyst Target 전체 비교 (v2026-06-03)

| 종목 | Model T1 | Mean Target | High Target | vs Mean | vs High |
|:----|:--------:|:----------:|:----------:|:------:|:-------:|
| **MU** | **$1,732** | $726 (stale) | $1,750 | — | **-1.0% ✅** |
| **SNDK** | **$2,844** | $1,609 (stale) | $3,250 | — | **-12.5% ✅** |
| **삼성전자** | **₩895,648** | ₩397,803 (stale) | ₩850,000 | — | **+5.4% ✅** |
| SK하이닉스 | ₩6,593,421 | ₩2,076,603 | ₩4,000,000 | — | **+64.8% ❌** |
| NVDA | $372 | $297 | $500 | **+25.4%** | -25.6% |
| TSM | $523 | $468 | $600 | **+11.8% ✅** | -12.8% |
| MSFT | $482 | $561 | $870 | **-14.0% ✅** | -44.6% |
| GOOGL | $336 | $430 | $515 | **-21.8%** | -34.7% |
| DELL | $534 | $469 | $700 | **+13.7% ✅** | -23.7% |
| CLS | $443 | $441 | $550 | **+0.3% 🎯** | -19.5% |
| LLY | $1,189 | $1,215 | $1,500 | **-2.2% 🎯** | -20.7% |
| AVGO | $543 | $486 | $630 | **+11.8% ✅** | -13.8% |

## 현행 최적 파라미터 (v2026-06-03)

```python
# fair_value_v3.py
w_per = 0.75                   # PER 75% : PBR 25% (고정)
# ROE 상한 없음 — raw 값 그대로 사용 (너구리 원칙)
# 사이클리컬 fair_pe 상한 20
if fpe < 12 and ((pe/fpe) > 3.0 or market == 'KR'):
    fair_pe = min(fair_pe, 20)
# BPS 유보이익 (FPE < 12):
bps_t1 = bps_t0 + eps_t1 * 0.7
# SECTOR_BASE: 'Communication Services': 20 추가 (GOOGL 키 버그 수정)
```
