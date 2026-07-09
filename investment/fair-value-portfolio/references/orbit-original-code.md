# Orbit 원본 코드 구조 (듄토드 제공)

> 듄토드가 2026-06-02 세션에서 직접 제공한 Python 코드 기반.

## 데이터 흐름

```
final_top (데이터프레임)
  ├── PE_num / FPE_num → Growth_Rate / Target_PER
  ├── PBR_num / ROE_num → BPS / PBR 성분
  ├── DE_num → W_Growth 조건
  └── EPS_NY_num / EPS_5Y_num → EPS/BPS 타임라인
```

## EPS/BPS 궤적 계산

```python
# EPS 타임라인
EPS_T0  = Price / PE_num
EPS_Tm5 = EPS_T0 / (1 + 0.15 * 5)      # 역산: 연 15% 성장 가정
EPS_T1  = Price / FPE_num               # Forward EPS
EPS_T2  = EPS_T1 * (1 + EPS_NY_num/100) # Next Year 성장 반영
EPS_T5  = EPS_T1 * (1 + EPS_5Y_num*0.8/100 * 4)  # 5Y 성장 × 80% 보수적

# BPS 타임라인  
BPS_T0  = Price / PBR_num
BPS_Tm5 = BPS_T0 / (1 + 0.10 * 5)      # 연 10% 성장 가정
BPS_T1  = BPS_T0 * (EPS_T1 / EPS_T0)    # EPS 비율로 BPS 추정
BPS_T2  = BPS_T1 * (1 + EPS_NY_num/100)
BPS_T5  = BPS_T1 * (1 + EPS_5Y_num*0.8/100 * 4)
```

## 핵심 공식

```python
Growth_Rate = (PE_num / FPE_num) - 1
Expert_Target_PER = (Growth_Rate * 100 * 1.2).clip(15, 35)

# W_Growth: 이분법적 가중치
W_Growth = 0.7 if (DE_num < 0.5 AND Growth_Rate > 0.2) else 0.4

# Orbit 적정가 (타임라인별)
fair_pts = [
    (EPS_t * Expert_Target_PER * W_Growth) +
    (BPS_t * (ROE_num / 9) * (1 - W_Growth))
    for EPS_t, BPS_t in zip(eps_timeline, bps_timeline)
]
```

## 보조 적정가 (참고용)

```python
# DCF 기반
FCF_Yield = 1 / PFCF_num  # P/FCF의 역수
DCF_Fair = Price * (1 + (FCF_Yield + EPS_NY_growth/100) * 0.5)

# Macro 기반  
Macro_Rate = 0.085  # WACC
RF_Rate = 0.045     # 무위험 수익률
Macro_Fair = Price * (1.1 - Macro_Rate)
```

## 그래프 구성

- **상단 (= PER 기반)**: EPS 타임라인 × PE 배수 밴드 (+15~-15) + Orbit 라인
- **하단 (= PBR 기반)**: BPS 타임라인 × PB 배수 밴드 + Orbit 라인
- **마커**: 현재가(검정), Orbit 적정가(분홍 ★), DCF 적정가(주황 ★), Macro Safe(빨강 ★)

## timeout_ms

- Orbit 라인: 5개 시점(T-5, T0, T1, T2, T5) 연결한 마젠타 궤적
- 배수 밴드: PE/PBR ±5, ±10, ±15 단위 점선
- 각 밴드 끝에 배수값 텍스트 표시

## 주의: 코드 내 미정의 변수

아래 변수는 `final_top` 데이터프레임에서 가져오는 것으로 추정:
- `PFCF_num`, `EPS_NY_num`, `EPS_5Y_num`
- `Fair_Value` (별도 계산된 적정가)
- `DE_num` (yfinance debtToEquity 가공값 — raw %인지 ratio인지 불확실)
