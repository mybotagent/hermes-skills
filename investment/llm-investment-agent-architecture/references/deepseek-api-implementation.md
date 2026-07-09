# DeepSeek API Implementation Reference

> LangGraph Bull/Bear/Risk → Decision 파이프라인의 DeepSeek V3/R1 연동 구현 패턴.
> `trading-agents-nuri-langgraph` POC (2026-06-06) 기준.

## API 키는 이미 .env에 있음 — 탐색 금지
- `~/trading-agents-nuri-langgraph/.env`에 DeepSeek + Finnhub 키 저장 완료
- 검증: `cd ~/trading-agents-nuri-langgraph && cat .env`

## 🔌 DeepSeek API 호출 (httpx)

두 가지 모델 사용:

| 모델 | 식별자 | 용도 | Temperature |
|:-----|:-------|:-----|:-----------:|
| V3 | `deepseek-chat` | 정보 분석/요약 (Context, Bull, Bear, Risk) | 0.3 |
| R1 | `deepseek-reasoner` | 최종 결정 (Decision Maker) | 0.1 |

```python
import httpx

def _call(messages, model, temperature=0.3):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": 1024}
    with httpx.Client(timeout=60.0) as client:
        resp = client.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    track_cost(model, data["usage"]["prompt_tokens"], data["usage"]["completion_tokens"])
    return data["choices"][0]["message"]["content"].strip()
```

## 🧠 Agent 구현 패턴 (5개, V2 — 매크로 + 뉴스 포함)

### Context + Analysis (V3) — macro + news passing
```python
def analyze_context(state):
    macro = state.get("macro_context", {})
    macro_summary = macro.get("summary", "제공되지 않음")
    news = macro.get("news", "최신 뉴스 데이터 없음")
    
    prompt = CONTEXT_PROMPT.format(
        ticker=state["ticker"], price=state["price"],
        fair_pe=state["fair_pe"], midpoint=state["midpoint"],
        midpoint_gap=state["midpoint_gap"], t1_price=state["t1_price"],
        t1_gap=state["t1_gap"], target=state.get("analyst_target", "N/A"),
        current_pe=state["current_pe"], forward_pe=state["forward_pe"],
        macro=macro_summary, news=news,
    )
    result = call_v3(prompt, "당신은 PER75:PBR25 단일공식을 따르는 가치투자 애널리스트입니다.")
    return {"context_analysis": result}
```

### Decision Maker (R1) — HOLD에도 정성적 근거 포함
```python
def make_decision(state):
    prompt = DECISION_PROMPT.format(
        ticker=state["ticker"], price=state["price"],
        midpoint=state["midpoint"], midpoint_gap=state["midpoint_gap"],
        fair_pe=state["fair_pe"], current_pe=state["current_pe"],
        context=state["context_analysis"],
        bull=state["bull_case"], bear=state["bear_case"], risk=state["risk_case"],
    )
    result = call_r1(prompt, "당신은 PER75:PBR25 단일공식을 따르는 가치투자자입니다.")
    
    decision, rationale, confidence = "HOLD", result, "LOW"
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("Decision:") or line.startswith("**Decision:**"):
            val = line.split(":", 1)[-1].strip().upper().replace("**", "")
            if val in ("BUY", "SELL", "HOLD"): decision = val
        elif line.startswith("Confidence:") or line.startswith("**Confidence:**"):
            val = line.split(":", 1)[-1].strip().upper().replace("**", "")
            if val in ("HIGH", "MEDIUM", "LOW"): confidence = val
        elif line.startswith("Rationale:") or line.startswith("**Rationale:**"):
            rationale = line.split(":", 1)[-1].strip()
    
    # HOLD여도 Rule 1만 말하지 말고 구체적 수치 포함
    if decision == "HOLD" and ("Rule" in rationale[:50] or "규칙" in rationale[:50]):
        pe_ratio, fair_pe, gap = state["current_pe"], state["fair_pe"], state.get("midpoint_gap", 0)
        rationale = f"현재 PER {pe_ratio}이(가) 적정PER {fair_pe}을(를) 초과하여 Rule 1 적용. 중간값 괴리율 {gap}%는 저평가 신호이나 PER 조건이 우선하므로 HOLD."
    
    return {"decision": decision, "rationale": rationale[:400], "confidence": confidence}
```

## 📊 Cost Tracker (실제 토큰 기반)

```python
COST_V3_INPUT = 0.27      # $/1M tokens
COST_V3_OUTPUT = 1.10
COST_R1_INPUT = 0.55
COST_R1_OUTPUT = 2.19

# cost_log.jsonl에 append → get_daily_cost(), get_monthly_cost() 조회
```

## 🏃 독립 실행: run_phase2.py

Phase 2(LangGraph 분석)만 독립적으로 실행. 저장된 데이터 파일만 읽음:

```bash
cd ~/trading-agents-nuri-langgraph && venv/bin/python3 run_phase2.py
```

내부 동작:
1. `data/filtered_top10.json` 읽기 (필수, 없으면 종료)
2. `data/macro_context.json` 읽기 (선택, 없으면 뉴스/매크로 없이 진행)
3. `src.graph.run_batch()`로 LangGraph Fork-Join 분석
4. 리포트 생성 + `logs/decisions/`에 저장
5. 표준 출력으로 Discord 전송용 리포트 출력

## 🚀 전체 파이프라인 실행

```bash
# 전체
cd ~/trading-agents-nuri-langgraph && venv/bin/python3 pipeline.py

# 개별 Phase
venv/bin/python3 pipeline.py --phase 0    # 데이터 캡처
venv/bin/python3 pipeline.py --phase 05   # Finnhub 뉴스 수집
venv/bin/python3 pipeline.py --phase 1    # Midpoint 필터
venv/bin/python3 run_phase2.py            # LangGraph 분석
```

## ⚠️ 함정

- **Decision Maker(R1)는 실행마다 BUY/HOLD가 미묘하게 달라짐** — NVDA가 BUY였다가 HOLD로 바뀌는 현상 발생
  - 원인: R1 추론 편차. Rule 1(적정PER)은 강력하게 지켜지지만, Rule 2(Bull > Bear 비교)는 LLM 판단이라 변동 있음
  - 해결: Decision Maker 프롬프트에 구체적 Rule 설명 추가 (v2에서 개선됨)
- **Finnhub 뉴스 포함 시 Context 토큰 증가 → 비용 1.5~2배 상승** (146원 → 258원)
- **R1 출력 파싱은 Decision/Rationale/Confidence 순서 보장 안 됨** — 모든 줄을 순회하며 파싱
