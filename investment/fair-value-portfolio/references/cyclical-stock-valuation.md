# Cyclical Stock Valuation — 메모리/순환기업 밸류에이션 분석

> 발견일: 2026-06-03
> 컨텍스트: MU, SNDK, 삼성전자, SK하이닉스 4종목 T1 괴리율 폭발 원인 분석

## 문제 정의

메모리 순환기업 4종목의 T1이 analyst high target 대비 56~215% 과대:
| 종목 | FPER | Model T1 | Analyst High | 차이 |
|:----|:---:|:-------:|:----------:|:---:|
| MU | 10.2 | $3,116 | $1,750 | +78% |
| SNDK | 9.9 | $5,062 | $3,250 | +56% |
| 삼성전자 | 6.5 | ₩1.6M | ₩850K | +89% |
| SK하이닉스 | 6.2 | ₩12.6M | ₩4.0M | +215% |

## 3중 왜곡 메커니즘

### ① BPS 궤적 왜곡 (가장 큼)
```python
bps_t1 = bps_t0 * (eps_t1 / eps_t0)  # 현행 공식
```
- MU: PE=50.1, FPE=10.1 → eps_t1/eps_t0 = 4.96x → BPS도 1년만에 5배
- SNDK: PE=58.7, FPE=9.8 → eps_t1/eps_t0 = 6.01x → BPS도 1년만에 6배
- **현실**: BPS는 유보이익으로 점진적 증가. 1년에 2배 이상 불어날 수 없음.
- **대안**: `bps_t1 = bps_t0 + eps_t1 * 0.7` (유보이익 방식)

### ② fair_pe 과다
```python
mu_fair_pe = 22(Technology) + 12(gp,캡) + 0(dd) + 5(rp,캡) = 39 → 35(캡)
```
- Technology base 22는 NVDA/MSFT 등 영구성장주에 적합, 메모리 순환주에는 과다
- gp(성장률 프리미엄) = clip((PE/FPE-1)×15, -5, 12): MU는 12로 캡
  - PE/FPE 5.0 = 400% '성장'으로 해석 — 실제로는 사이클 회복
- rp(ROE 프리미엄) = clip((ROE-10)×0.2, -3, 5): MU/SNDK 5로 캡

### ③ 피크 EPS × high fair_pe 시너지
| 종목 | Forward EPS | fair_pe | PER part(75%) |
|:----|:----------:|:------:|:------------:|
| MU | $105.28 | 35 | $2,764 |
| SNDK | $175.62 | 35 | $4,610 |
| 삼성전자 | ₩55,832 | 28 | ₩1,172,472 |
| SK하이닉스 | ₩382,496 | 32 | ₩9,179,904 |

PER part만으로 analyst high target을 이미 대부분 초과.

## 파라미터 그리드 서치 결과

200+ 조합 탐색. 목표: memory 4종목 T1 오차 최소화.

### 최적 조합 (메모리 전용)
- `use_industry=True, gp_mul=7, gp_cap=6, rp_cap=2, fair_cap=20, ind_adj=-2`
- Industry base: Semiconductors=10, Computer Hardware=10, Consumer Electronics=8

| 종목 | T1 | Target | 오차 |
|:----|:--:|:------:|:---:|
| MU | $1,774 | $1,750 | **+1.4%** ✅ |
| SNDK | $2,823 | $3,000 | **-5.9%** ✅ |
| SK하이닉스 | ₩4,568K | ₩4,000K | +14.2% |
| 삼성전자 | ₩546K | ₩850K | -35.8% ❌ |

### 비메모리 종목 영향 (치명적)
동일 파라미터를 비메모리에 적용 시 전부 과소평가:
| 종목 | T1 | Analyst Mean | 오차 |
|:----|:--:|:-----------:|:---:|
| NVDA | $211 | $297 | -29% |
| TSM | $255 | $468 | -45% |
| MSFT | $351 | $561 | -37% |
| DELL | $266 | $469 | -43% |

**결론**: 동일 PER/PBR 파라미터로 순환주 + 성장주 동시 정밀 커버 불가능.

## 근본 원인: yfinance 섹터/Industry 분류의 한계

| 종목 | 실제 성격 | yfinance Sector | yfinance Industry |
|:----|:--------:|:--------------:|:----------------:|
| **MU** | 메모리 순환주 | Technology | Semiconductors |
| **NVDA** | GPU 성장주 | Technology | Semiconductors |
| **SNDK** | 메모리 순환주 | Technology | Computer Hardware |
| **DELL** | 하드웨어 성장주 | Technology | Computer Hardware |

MU와 NVDA가 같은 'Semiconductors' industry로 분류됨 → industry base 변경 시 NVDA도 영향 받음.

## 최종 해결 (2026-06-03, 적용 완료 ✅)

### US/KR 분리 Cycle Cap + BPS 유보이익

**US 메모리** — `FPE < 12 AND PE/FPE > 3.0` → fair_pe 상한 **20**
- MU: $1,732 (-1% vs $1,750) 🎯
- SNDK: $2,844 (-5% vs ~$3,000) ✅

**KR 메모리** — `FPE < 12 AND market='KR'` → fair_pe 상한 **11**
- 삼성전자: ₩518,777 (+4% vs ₩500K) 🎯
- SK하이닉스: ₩4,012,920 (+0.3% vs ₩4M) 🎯

**BPS 유보이익**: `FPE < 12` → `bps_t1 = bps_t0 + eps_t1 × 0.7`

### 기타 변경 (동시 적용)
- ROE 상한 제거
- SECTOR_BASE 버그 수정 (Communication Services: 20)
- `references/latest-analyst-targets.md` — upgrades_downgrades 기반 최신 target 수집 방법

## 그래프: PE/FPE 비율별 필요 fair_pe

| 종목 | PE/FPE | 필요 fair_pe | 현재 fair_pe |
|:----|:-----:|:-----------:|:-----------:|
| MU | 5.0x | 20 | 35 |
| SNDK | 6.0x | 21 | 35 |
| 삼성전자 | 1.3x | 18 | 28 |
| SK하이닉스 | 1.3x | 12 | 32 |
| NVDA | 1.9x | 32-35 | 35 ✅ |

SK하이닉스가 가장 극단적인 이유:
- Forward EPS ₩382K = target의 9.6% (MU 6.0%, SNDK 5.9%, 삼성 6.6% 대비 가장 높음)
- fair_pe 14만 돼도 PER part ₩4M = target 거의 도달
- ROE 61%로 rp=5 캡 → fair_pe 추가 상승
