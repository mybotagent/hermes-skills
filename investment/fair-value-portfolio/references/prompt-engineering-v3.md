# Prompt Engineering — 정량적 매크로/뉴스 분석 v3

## 배경 (2026-06-06)
초기 프롬프트는 Bull/Bear가 단순 3문장으로 "Rule 1에 따라 HOLD"만 반복. 
사용자 교정: "매크로/뉴스에 대한 정량적인 분석결과에 근거도 정확하게 리포트하도록 해야해"

## 해결: v3 프롬프트 패턴

### 핵심 변경
1. **Context 프롬프트**: {macro}와 {news}를 템플릿 변수로 직접 주입
2. **Bull/Bear/Risk**: 각 근거에 **구체적 수치(%)를 포함**하도록 강제
3. **Decision Maker**: HOLD여도 ①PER 수치 비교 ②중간값 괴리율 ③매크로/뉴스 근거를 정량 수치로 설명

### 템플릿 패턴

**Context 프롬프트**:
```
📊 밸류에이션 데이터: (PER/FPER/T1/중간값 수치 자동 삽입)
🌍 매크로 컨텍스트: {macro}  ← macro_context.json의 macro_report_summary
📰 종목 뉴스: {news}          ← Finnhub에서 수집한 최신 뉴스

분석 내용 (5문장, 각 문장에 구체적 수치 포함):
1. 현재 PER {current_pe} vs 적정PER {fair_pe} — 괴리율 몇 %인지
2. Forward PER {forward_pe} 기반 EPS 증가율 계산
3. 매크로 지표 중 어떤 것이 이 종목에 영향을 주는지 구체적으로 명시
4. 뉴스 중 가장 중요한 이슈 1개를 수치와 함께 인용
5. 종합 의견
```

**Bull/Bear 프롬프트**:
```
다음 3가지 근거를 각각 **구체적 수치(%)를 포함하여** 2문장씩 제시:
1. PER/PBR 수치 기반 — 괴리율 % 명시
2. 매크로 데이터 인용 (ISM/고용/금리 등 특정 수치)
3. 뉴스 인용 (구체적 내용과 출처)
각 근거에 반드시 괴리율 %와 매크로/뉴스 수치를 포함할 것.
```

**Decision Maker — Rationale 형식**:
```
Rationale: (3문장. HOLD여도 ①PER 수치(현재 X vs 적정 Y = Z% 차이)
②중간값 괴리율 W% 의미 ③매크로/뉴스 중 가장 중요한 근거 1개를 정량 수치로 설명)
```

### 결과 예시 (HPE, 2026-06-06)
```
💡 결정 근거:
1. 현재 PER 46.0은 적정PER 33.0 대비 39.4% 높아 매수 조건 불충족.
2. 중간값 괴리율 127.64%는 Forward PER 12.3 기반 실적 개선(274% EPS 증가)이 전제된 극단적 낙관치.
3. BIS HBM/AI 수출통제 확대는 HPE AI 서버 고객사 공급망의 20~30%에 규제 리스크.
```

### 파일 위치
- `~/trading-agents-nuri-langgraph/src/prompts.py` — 실제 프롬프트 템플릿
- `~/trading-agents-nuri-langgraph/src/agents/context.py` — Context Agent (macro/news 주입)
- `~/trading-agents-nuri-langgraph/src/agents/risk.py` — Risk Agent (forward_pe 포함)
- `~/trading-agents-nuri-langgraph/src/agents/decision.py` — Decision Maker (정량 근거 포맷)
