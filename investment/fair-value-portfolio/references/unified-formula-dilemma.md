# Unified Formula Dilemma — Cycle Caps vs One Formula

> 문서화일: 2026-06-03
> 컨텍스트: 너구리가 "예외 처리(cycle cap 20/11)는 바람직하지 않다. 하나의 공식으로 해결해야 한다"고 지적

## 문제: 하나의 공식으로는 동시 정밀 커버 불가

Cycle cap(US 20, KR 11)을 제거하고 `ROE/RF` 기반 PBR multiplier로 대체 시도했지만 실패.

**원인**: 종목별로 필요한 fair_pe가 근본적으로 다름:

| 종목 | 필요 fair_pe | 현재 fair_pe | 괴리 |
|:----|:-----------:|:-----------:|:----:|
| MU | ~20 | 35 | -15 |
| 삼성전자 | ~11 | 28 | -17 |
| NVDA | ~20 (Needham $270) | 35 | -15 |
| MSFT | ~39 (Wells Fargo $650) | 29 | +10 |

MSFT는 fair_pe를 29→39로 높여야 하고, MU는 35→20으로 낮춰야 함. 동일 gp/rp/dd 공식으로 불가능.

## 시도: RF 기반 PBR 리디자인의 한계

PBR multiplier를 `ROE/9` → `ROE/RF`로 변경, RF=6.5 최적화, cycle cap 제거:

```
평균 오차: 36~38% (cycle cap 유지 시 14~15%)
```

RF 변경만으로 cycle cap을 대체할 수 없었음. 이유:
- PBR part는 BPS에 비례 → BPS가 작은 고PBR 기업(NVDA, AAPL)에는 영향 미미
- BPS가 큰 기업(현대차 PBR 1.6)에는 이미 적정
- 고PBR 기업(NVDA 34, AAPL 43)은 BPS가 너무 작아 PBR multiplier가 아무리 높아도 T1에 영향 없음

## 근본 제약: NVDA 구조적 한계

NVDA: PBR 34.4, ROE 114%, BPS $6.48
- PBR part = $6.48 × (114/RF) × 25% → RF=9면 $20, RF=6.5면 $28
- T1 기여도: 5~8% 불과
- **PBR part로는 NVDA를 조정할 수 없음** — BPS가 너무 작아서

NVDA를 analyst target $270에 맞추려면 fair_pe 자체를 35→20으로 낮춰야 함.
근데 fair_pe 공식은 `base(22) + gp(12,캡) + rp(5,캡) = 39 → 35(캡)`.
gp/rp 캡을 낮추면 MSFT, DELL, TSM 등도 같이 영향받음.

## 최종 결론 (2026-06-03)

너구리와의 논의 끝에 **현행 유지**(cycle cap US 20/KR 11)로 결정:

1. **Cycle cap은 "예외 처리"가 아니라 FPE 기반 특성 분류**: FPE<12인 기업은 peak-cycle earnings 상태. 하나의 공식(`if FPE < 12`)이 모든 종목에 동일 적용되므로 특별 규칙 아님.
2. **PBR 절대 제거 금지**: `BPS × (ROE/9)`는 자본 효율성의 핵심 측정. 제거 시 ROE 반영 불가.
3. **모델 고유 시각 인정**: NVDA $372 vs analyst $270은 모델의 고유 판단. 강제로 끼워맞추지 않음.
4. **RF 기반 PBR 리디자인 거부**: cycle cap 제거 + ROE/RF 시도는 평균오차 36%로 실패.

### 최종 정확도 (21종목)

| 구분 | 개수 | 종목 |
|:----|:---:|:----|
| 🎯 ±10% 이내 | 8 | DELL, LLY, CLS, 삼성전자, SK하이닉스, MU(Susquehanna), MSFT, STX |
| ✅ ±10~25% | 5 | SNDK, GOOGL, TSM, AVGO, STX |
| ⚠️ ±25~50% 모델 시각 | 5 | NVDA(+38%), AAPL(-36%), LRCX(-37%), AMD(-45%), LITE(-50%) |
| ➖ 미확인 | 3 | 현대차, HD현대일렉, 삼성전기 (KR analyst target 미확보)

| 접근법 | 장점 | 단점 | 최종 판단 |
|:------|:----|:----|:---------|
| **현행 유지** (cycle cap 20/11) | 메모리 4종목 정밀 일치 | 예외 처리 존재 | ✅ **채택** (FPE 기반 = 특성 분류, 예외 아님) |
| **cycle cap 제거 + gp/rp 재설계** | 하나의 공식 | 36%+ 평균 오차 | ❌ 실패 |
| **fair_pe 공식 자체 재설계** | 근본 해결 가능 | FPE 통합 미해결 | ⏳ 미결 |
| **NVDA 등 메가캡 별도 처리** | 실용적 | 특별 규칙 추가 | ❌ 거부 (너구리)

## 관찰: FPE를 공식에 통합하는 아이디어

Cycle cap이 하는 일: FPE가 낮은 기업(cyclical peak)에 fair_pe 감소.
이걸 cap 없이 공식에 넣으려면 fair_pe 자체가 FPE에 반응해야 함.

```
sustainability = min(FPE / 12, 1.0)
fair_pe_adjusted = fair_pe × sustainability
```

- MU: FPE=10.1 → 0.84 → fair_pe=35×0.84=29.4 (여전히 높음)
- 삼성: FPE=6.5 → 0.54 → fair_pe=28×0.54=15.2 (좋음)
- NVDA: FPE=17.6 → 1.0 → fair_pe=35 (유지)

MU(29.4)와 삼성(15.2)의 괴리가 여전히 큼 → 단순 sustainability factor로는 부족.

**미결**: FPE 기반 discount를 공식에 자연스럽게 통합하는 방법은 아직 발견되지 않음.
