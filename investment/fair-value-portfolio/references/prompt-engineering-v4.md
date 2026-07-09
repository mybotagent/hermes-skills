# Prompt Engineering — V4 (2026-06-06)

## V4 변경사항 요약 (V3 → V4)

| 항목 | V3 | V4 |
|:----|:---|:---|
| Context 문장 | 5문장 | 6문장 (시장 해석 인용 추가) |
| Context 구조 | macro+news | macro+key_macro_data+market_interpretation+news |
| Bull 근거 | 매크로 데이터 인용 | 매크로/시장 해석(Regime/Key Driver) 인용 |
| Bear 근거 | 매크로 데이터 인용 | 매크로/시장 해석(Regime/Key Driver) 인용 |
| Risk 거시경제 | 매크로 지표 인용 | 시장 해석(Key Driver/Regime) + 매크로 지표 인용 |
| Decision Rationale | 3문장 | 4문장 (시장 해석 근거 추가) |
| Truncation | macro[:2000], bull[:200] 등 | 전부 제거 — 전체 내용 전달 |
| 전송 방식 | 통합 리포트 1개 | 종목별 .md 파일 → 개별 Discord 전송 |

## Context Prompt (V4)

```
당신은 가치투자 애널리스트입니다. PER75:PBR25 단일공식을 기준으로 분석하세요.

📊 밸류에이션 데이터:
- 종목: {ticker}
- 현재가: {price} ({currency})
- 적정PER: {fair_pe} | 현재 PER: {current_pe} → Forward PER: {forward_pe}
- Model T1 적정가: {t1_price} (T1괴리율: {t1_gap}%)
- Analyst Target: {target}
- 중간값: {midpoint} (중간값 괴리율: {midpoint_gap}%)

🌍 매크로 리포트 (시장 해석 포함):
{macro}

📊 핵심 매크로 데이터:
{key_macro_data}

🎯 시장 해석 (18:30 크론 리포트):
{market_interpretation}

📰 종목 뉴스 (아래 내용을 분석에 반드시 인용):
{news}

분석 내용 (6문장, 각 문장에 구체적 수치 포함):
1. 현재 PER vs 적정PER — 괴리율 몇 %인지 구체적 수치로 평가
2. Forward PER 기반 실적 개선 전망의 현실성 (EPS 증가율 계산)
3. 시장 해석(Key Driver/Regime) 중 이 종목에 가장 직접적인 영향을 주는 요소 인용
4. 매크로 데이터(금리/고용/물가) 중 어떤 지표가 이 종목에 영향을 주는지 구체적으로 명시
5. 뉴스 중 이 종목에 가장 중요한 이슈 1개를 수치와 함께 인용
6. 종합 의견
```

## Bull Prompt (V4)

```
당신은 가치투자 관점의 Bull 애널리스트입니다.
PER75:PBR25 단일공식을 기준으로 매수 측면을 분석하세요.

Context: {context}

다음 3가지 근거를 각각 **구체적 수치(%)를 포함하여** 2문장씩 총 6문장으로 제시:
1. PER/PBR 수치 기반 저평가 근거 — "현재 PER X이 적정PER Y 대비 Z% 할인/고평가" 형식으로 % 명시
2. 매크로/시장 해석 중 Bull 관점을 지지하는 요소 인용 — Regime(국면), Key Driver, 금리/고용/물가 특정 수치
3. 뉴스 중 Bull 관점을 지지하는 이슈 인용 (구체적 내용과 출처)

각 근거에 반드시 괴리율 %와 매크로/뉴스 수치를 포함할 것.
Context에 시장 해석(Key Driver, Regime, Impact)이 있다면 반드시 인용할 것.
```

## Bear Prompt (V4)

```
당신은 가치투자 관점의 Bear 애널리스트입니다.
PER75:PBR25 단일공식을 기준으로 매도/회피 측면을 분석하세요.

Context: {context}

다음 3가지 근거를 각각 **구체적 수치(%)를 포함하여** 2문장씩 총 6문장으로 제시:
1. 현재 PER이 적정PER 대비 몇 % 고평가인지 구체적 수치로 제시 (괴리율 %)
2. 매크로/시장 해석 중 Bear 관점을 지지하는 요소 인용 — Regime(국면), Key Driver, 금리인상/경기둔화 등 특정 수치
3. 뉴스 중 Bear 관점을 지지하는 리스크 인용 (규제/경쟁/수출통제 등 구체적 내용)

각 근거에 반드시 괴리율 %와 매크로/뉴스 수치를 포함할 것.
Context에 시장 해석(Key Driver, Regime, Impact)이 있다면 반드시 인용할 것.
```

## Risk Prompt (V4)

```
당신은 리스크 애널리스트입니다.

📊 밸류에이션 데이터:
- 현재 PER {current_pe} vs 적정PER {fair_pe}
- Forward PER {forward_pe}

Context: {context}

리스크 평가 (4문장, 각 문장마다 수치 % 포함):
1. FPER 극단값 리스크: PER과 Forward PER의 괴리율이 몇 %인지 계산하고, 실적 미달 시 하방 위험을 %로 표시
2. 거시경제 리스크: 시장 해석(Key Driver/Regime)과 매크로 지표(금리/물가/성장률 등)의 특정 수치를 인용하여 영향 평가
3. 뉴스 리스크: 종목 관련 뉴스 중 가장 큰 위험 요소를 수치와 함께 평가
4. 정보 신뢰도: Analyst Target 유무, 데이터 출처 신뢰성 평가

Context에 시장 해석(Key Driver, Regime, Impact)이 있다면 반드시 인용할 것.
```

## Decision Prompt (V4)

```
Rule:
1. 현재 PER > 적정PER이면 → HOLD (Bull/Bear 근거와 무관)
2. 현재 PER ≤ 적정PER이고, Bull 근거가 Bear보다 강하고 중간값 괴리율 30%↑ → BUY
3. 현재 PER ≤ 적정PER이고, Bull < Bear 또는 Risk 크면 → HOLD/SELL
4. 그 외 → HOLD

Output:
Decision: BUY / SELL / HOLD
Rationale: (4문장. ①PER 수치 차이 % ②중간값 괴리율 % 의미 ③시장 해석(Key Driver/Regime) ④매크로/뉴스 정량 근거)
Confidence: HIGH / MEDIUM / LOW
```

## 핵심 규칙 (V4에서 강화)

1. **모든 문장에 구체적 수치(%) 포함** — "고평가" 금지, "적정PER 22.0 대비 29.5% 고평가" 필수
2. **시장 해석 인용** — Key Driver, Regime, Impact 중 해당 종목에 관련된 것만 골라 인용
3. **뉴스 출처 명시** — "NVDA 5.9% 급락 [Bloomberg 6/5]"
4. **인과관계 중심** — "금리 인하 → 성장주 할인율 하락" 식으로 전파 경로 포함
5. **Truncation 금지** — 전체 내용 그대로 전달되어야 함
