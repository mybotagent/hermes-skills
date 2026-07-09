# Multi-Agent LLM Architecture (v3 — Simplified)

> **v3 업데이트 (2026-06-06)**: Bull/Bear 분리 제거, Critic 제거, SNS 제거, 유료 API 금지.
> **원칙**: 단순할수록 유지보수하기 쉽고 신뢰할 수 있다.

---

## 1. 개요

fair_value_v3 정량 분석 위에 LLM 레이어를 얹어 매수/매도/홀드 결정을 보조하는 시스템.
TradingAgents 논문([arXiv:2412.20138](https://arxiv.org/abs/2412.20138))에서 영감을 받았으나,
**가치투자 철학 + 단순성 + 무료 데이터만**에 맞게 재설계.

**GitHub**: `mybotagent/trading-agents-nuri`

---

## 2. 데이터 소스 — 무료 데이터만

| 소스 | 비용 | 신뢰도 |
|:----|:----:|:-----:|
| yfinance (주가/PER/FPE/PBR/ROE/EPS) | 무료 | ⭐⭐⭐⭐⭐ |
| yfinance analyst upgrades_downgrades | 무료 | ⭐⭐⭐⭐ |
| **Finnhub (뉴스, Insider, SEC Filing)** | **무료 (일 300회)** | **⭐⭐⭐⭐** |
| 네이버 증권 (한국주 PBR) | 무료 | ⭐⭐⭐⭐ |
| SEC EDGAR (10-K/10-Q/8-K) | 무료 | ⭐⭐⭐⭐⭐ |
| **Bloomberg/Reuters 등 유료 API** | ❌ 유료 | 사용 금지 |
| **SNS/Reddit/X/포럼** | ❌ 노이즈 | 사용 금지 |

> **원칙**: 유료 데이터 절대 사용하지 않음. SNS/포럼 데이터 절대 사용하지 않음.
> 현재 cron에서 수집하는 데이터 + Finnhub 무료 티어(일 300회)로 충분함.

---

## 3. 아키텍처 (3개 레이어, 9개 노드)

```
HOOK LAYER (LLM 0회)
  ├─ Source & Freshness Check (룰)  ← 출처 검증 + 최신성 + 중복 방어
  └─ Fair-Value Snapshot (데이터)    ← fair_value_v3 재사용

ANALYSIS LAYER (DeepSeek — 2회 호출)
  ├─ Context + Analysis (V3, ~2원)  ← 정보 요약 + 영향 분석 (Finnhub 뉴스/Insider 포함)
  └─ Decision Maker (R1, ~4원)      ← PER75:PBR25 기반 매매 결정

VERIFICATION + LOGGING (LLM 0회)
  ├─ Risk Check (룰)                 ← 15% 상한, AbsVal D+ 체크
  ├─ Hypothesis Store (DB)           ← 결정을 가설로 저장 → 3개월 후 검증
  ├─ Post-mortem Log (파일)          ← Raw Data + CoT 저장
  └─ Cost Monitor (계산)             ← 실제 토큰 기반 누적 비용 추적
```

**LangGraph**: 현재 구조는 순차 파이프라인으로 Python 함수 체인으로도 충분함.
LangGraph는 병렬 실행/조건부 분기가 필요할 때만 도입.

---

## 4. Source & Freshness Check (가장 중요한 노드)

```python
# 무료 실시간 데이터 소스만 허용
ALLOWED_SOURCES = {
    # 공통
    "yfinance_price":     {"trust": "HIGH",   "freshness": timedelta(minutes=5)},
    "yfinance_pe":        {"trust": "HIGH",   "freshness": timedelta(hours=24)},
    "yfinance_analyst":   {"trust": "HIGH",   "freshness": timedelta(days=30)},
    "cron_macro_brief":   {"trust": "MEDIUM", "freshness": timedelta(hours=12)},

    # Finnhub (무료, 일 300회, 실시간)
    "finnhub_news":       {"trust": "HIGH",   "freshness": timedelta(minutes=15)},
    "finnhub_insider":    {"trust": "HIGH",   "freshness": timedelta(days=7)},
    "finnhub_filing":     {"trust": "HIGHEST","freshness": timedelta(hours=48)},

    # 한국주 전용
    "naver_kr_stock":     {"trust": "HIGH",   "freshness": timedelta(hours=24)},

    # SEC (무료 공시)
    "sec_edgar":          {"trust": "HIGHEST","freshness": timedelta(hours=72)},
}

def check(self, event):
    if event.source not in ALLOWED_SOURCES:
        return REJECT(f"사용하지 않는 소스: {event.source}")

    max_age = ALLOWED_SOURCES[event.source]["freshness"]
    age = datetime.now() - event.timestamp
    if age > max_age:
        return REJECT(f"데이터 만료: {age}")

    if self.is_duplicate_within_15min(event):
        return SKIP("15분 내 재진입 → 스킵")

    return PASS(ALLOWED_SOURCES[event.source]["trust"])
```

**데이터 출처 목록에 없는 입력은 모두 폐기된다.**
SNS, 포럼, 유료 API는 아예 목록에 없으므로 자동 차단.

---

## 5. Context + Analysis (V3) Prompt

Finnhub 뉴스 + Insider 데이터를 Context에 포함:

```
System: 당신은 가치투자 분석가입니다.
PER75:PBR25 단일공식을 사용합니다.
**현재 보유한 데이터만으로 판단합니다. 외부 정보를 추가로 찾지 않습니다.**

User: 다음 데이터를 분석해주세요.

[Fair-Value Data]
- Ticker: {ticker}
- Current Price: ${price}
- Fair PE: {fair_pe}
- T0 Gap: {t0_gap}%
- T1 Gap: {t1_gap}%
- Analyst Target: ${target} ({firm}, {days_ago}일 전)
- Sector: {sector}

[Recent News - Finnhub]
{최근 24시간 뉴스 헤드라인 3~5개}

[Insider Activity - Finnhub]
{최근 30일 Insider 매수/매도 내역}

[Market Context]
{cron 브리핑 요약}

분석 (3문장):
1. 현재 밸류에이션 상태는? (Fair-Value 기준)
2. 뉴스/Insider가 밸류에이션을 지지하거나 위협하는가?
3. 정보의 최신성과 신뢰도는 충분한가?
```

---

## 6. Decision Maker (R1) — PER75:PBR25 적용

```
System: 당신은 PER75:PBR25 단일공식을 따르는 가치투자자입니다.
- 적정PER 밖 종목은 절대 매수하지 않습니다.
- 정보의 신뢰도와 최신성을 항상 확인합니다.
- 확실하지 않으면 HOLD입니다.

Output format:
Decision: BUY / SELL / HOLD
Rationale: (2문장)
Confidence: HIGH / MEDIUM / LOW
```

---

## 7. Hypothesis Store (자기 검증)

```python
def save_hypothesis(decision):
    """Trader의 결정을 '가설'로 저장, 3개월 후 검증"""
    hypothesis = {
        "id": generate_id(),
        "action": decision.action,          # BUY/SELL/HOLD
        "price_at_decision": decision.price,
        "target_price": decision.target,
        "rationale": decision.rationale,    # CoT
        "data_sources": decision.sources,   # 사용한 데이터 출처 목록
        "verify_at": now + timedelta(days=90),
        "status": "pending",
    }
    db.save(hypothesis)
    return hypothesis.id

def verify_hypotheses():
    """3개월 후 실제 주가와 비교 → 시스템 정확도 산출 (백테스트 대체)"""
    for h in db.query("status='pending' AND verify_at <= today"):
        current_price = get_price(h.ticker)
        actual_return = (current_price - h.price_at_decision) / h.price_at_decision
        h.actual_return = actual_return
        h.status = "correct" if actual_return > 0 else "wrong"
```

---

## 8. Cost Monitor (실제 토큰 기반)

```python
def log_cost(node, model, tokens_in, tokens_out):
    """실제 사용된 토큰으로 비용 계산"""
    PRICING = {"V3": (0.27, 1.10), "R1": (0.55, 2.19)}
    in_price, out_price = PRICING[model]
    cost = (tokens_in * in_price + tokens_out * out_price) / 1_000_000
    cost_krw = cost * 1450  # 환율 반영

    # 누적
    daily_total[node] += cost_krw
    monthly_total += cost_krw

    # 임계치 체크
    if monthly_total > 25000:
        alert("월 비용 25,000원 초과, 분석 빈도 감소")
    if monthly_total > 30000:
        halt("월 예산 30,000원 소진, 분석 중단")

    return cost_krw
```

> **중요**: 추정 토큰 수가 아닌 **실제 토큰 사용량**을 기록해야 함.

---

## 9. 비용 요약

| 노드 | 모델 | 1회 비용 | 월 8회 |
|:----|:----:|:--------:|:-----:|
| Source & Freshness Check | 룰 | 0원 | 0원 |
| Fair-Value Snapshot | 데이터 | 0원 | 0원 |
| Context + Analysis | V3 | ~2원 | ~16원 |
| Decision Maker | R1 | ~4원 | ~32원 |
| Risk Check | 룰 | 0원 | 0원 |
| Hypothesis Store | DB | 0원 | 0원 |
| Post-mortem Log | 파일 | 0원 | 0원 |
| Cost Monitor | 계산 | 0원 | 0원 |
| **합계** | | **~6원** | **~48원** |

---

## 10. v1 → v2 → v3 변화

| 항목 | v1 (초기) | v2 (과잉) | v3 (현행 ✅) |
|:----|:---------:|:---------:|:------------:|
| LLM 호출/Trigger | 4회 | 6회 | **2회** |
| Bull/Bear 분리 | 있음 | 있음 | **없음** |
| Critic Agent | 없음 | 있음 | **없음** |
| Fund Manager | 있음 | 있음 | **없음 (Risk가 대체)** |
| SNS 분석 | 없음 | 있었으나 제거 | **없음** |
| 유료 API | 없음 | 없음 | **없음 (사용 금지)** |
| 월 비용 | 74원 | 112원 | **48원** |

**사용자가 v3에서 직접 정리한 것**: "Bull/Bear 판단 researcher를 나눌 필요도 없으며, 과정 자체가 복잡할 필요는 없다. 유지보수하기가 어려워짐. 가장 중요한 정보의 최신성과 정확성에 기반해야 함."

---

## 11. 참조

- GitHub: `mybotagent/trading-agents-nuri`
  - `docs/03-final-architecture.md` — v3 상세
  - `docs/02-langgraph-assessment.md` — LangGraph 활용 판단
- TradingAgents 논문: [arXiv:2412.20138](https://arxiv.org/abs/2412.20138)
- TradingAgents GitHub: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)
- Finnhub API: https://finnhub.io/
