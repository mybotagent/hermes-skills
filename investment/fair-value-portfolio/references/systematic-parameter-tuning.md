# Systematic Parameter Tuning — Cycle Cap Optimization

> 문서화일: 2026-06-03 (최종)
> 컨텍스트: Phase 4→5 전환, 메모리 4종목 T1 정확도 최적화

## 1차 파라미터 서치 (2026-06-02): PER75:PBR25 + EPS 2.8x cap

6개 종목 기준 최적: 평균오차 16.5%
- MU $1,759 vs High $1,750 (+0.5% 🎯)

## 2차 파라미터 서치 (2026-06-03): 사이클 cap 도입

### 발견: BPS 궤적 공식 왜곡
- `bps_t1 = bps_t0 × (eps_t1/eps_t0)` — 순환기업에서 BPS가 1년만에 3~7배 폭등
- 삼성전자 실제 PE=46.9, FPE=6.5 → eps_t1/eps_t0 = 7.27x → BPS도 7.27배로 부풀려짐
- **해결**: BPS 유보이익 방식 `bps_t1 = bps_t0 + eps_t1 × 0.7`

### 발견: KR 주식 trailingPE 추정 문제
- yfinance가 KOSPI trailingPE 미제공 → FPE×1.3 추정 시 PE/FPE ≈ 1.3 고정
- 실제 재무제표 기준 PE는 46.9 (삼전) → PE/FPE = 7.2 → 완전히 다름
- **해결**: market='KR' 조건으로 KR 순환기업 별도 처리

### 발견: US와 KR 메모리 동일 cap 불가능
- MU Forward EPS $105 / target $1,750 = 6% 비율 → cap 20 필요
- 삼전 Forward EPS ₩55,833 / target ₩500K = 11.2% 비율 → cap 11 필요
- **해결**: US/KR 분리 cap (US 20, KR 11)

## 최종 파라미터 (Phase 5, 2026-06-03)

| 파라미터 | 값 | 근거 |
|:--------|:--:|:-----|
| W_PER | 0.75 | 고정, 예외 없음 (너구리 원칙) |
| US cycle cap | 20 | MU $1,732 (-1%), SNDK $2,844 (-5%) |
| KR cycle cap | 11 | 삼전 ₩519K (+3.8%), SK하이닉스 ₩4.01M (+0.3%) |
| BPS (FPE<12) | 유보이익 | bps_t1 = bps_t0 + eps_t1 × 0.7 |
| ROE 상한 | 없음 | 너구리 원칙 |
| EPS 하드코딩 캡 | 없음 | raw forward EPS 사용 |

## 최종 정확도 (2026-06-03, 최신 analyst target 기준)

| 종목 | Model T1 | Target | 오차 | 데이터 출처 |
|:----|:-------:|:------:|:---:|:---------:|
| MU | $1,732 | $1,750 | -1.0% 🎯 | Susquehanna 5/29 |
| SNDK | $2,844 | ~$3,000 | -5.2% ✅ | Susquehanna 5/29 |
| 삼성전자 | ₩518,777 | ₩500K | +3.8% 🎯 | 너구리 제공 |
| SK하이닉스 | ₩4,012,920 | ₩4M | +0.3% 🎯 | 너구리 제공 |
| DELL | $534 | $500 | +6.8% 🎯 | Goldman Sachs 6/1 |
| LLY | $1,189 | $1,251 | -5.0% 🎯 | BofA 5/26 |
| CLS | $443 | $460 | -3.7% 🎯 | Rothschild 5/1 |
| NVDA | $372 | $270 | +37.8% | 성장주 모델 한계 |
| GOOGL | $336 | $420 | -20.0% | PBR anchor 과잉 |
| LRCX | $229 | $365 | -37.3% | PBR anchor 과잉 |
| AAPL | $245 | $380 | -35.5% | PBR anchor 과잉 |
