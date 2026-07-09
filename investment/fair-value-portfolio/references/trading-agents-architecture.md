# TradingAgents 기반 LLM Agent Layer — 최종 v3.2

**소속 스킬**: `fair-value-portfolio` (Phase 6)
**GitHub**: `mybotagent/trading-agents-nuri`
**기준 논문**: TradingAgents (arXiv:2412.20138, `langgraph>=0.4.8` 사용 확인)

---

## 아키텍처 결정 이력

| 버전 | LLM 호출 | 노드 | 월 비용 | 설명 |
|:----|:--------:|:----:|:------:|:-----|
| v1 | 4회 | 6 | 74원 | TradingAgents 거의 그대로 |
| v2 | 6회 | 14 | 112원 | 과잉 설계 (Critic+SNS) |
| v3 | 2회 | 9 | 48원 | 너무 단순화 (Bull/Bear 제거) |
| v3.2 | 5회(V3×4+R1) | 5 | ~96원 | **✅ 최종: Bull+Bear+Risk + 논문 패턴** |

## 원칙: 기존 시스템 변경 금지

신규 Agent Layer는 기존 cron/fair_value_v3를 **절대 변경하지 않는다.**
기존 시스템의 **출력물(JSON, 텍스트)만 읽어서** Bull/Bear/Risk Debate을 추가한다.

## 최종 아키텍처

```
기존 시스템 (변경 없음)              신규 파이프라인 (추가)
─────────────────────────           ─────────────────────────
fair_value_v3 (매일) ────→ JSON ──┐
cron Analyst Target ────→ JSON ──┤
cron 브리핑 (08/18시) ──→ Text ──┤
                                  ├── Context → Bull∥Bear∥Risk → Facilitator
네이버 증권 (한국주) ──→ JSON ──┤
Finnhub 뉴스 (미국주) ──→ JSON ──┘
```

## LangGraph 패턴 (논문 동일 3가지)

```
1. Structured Report (State) → AgentState TypedDict
2. Natural Language Debate (Node) → 각 Agent가 State 읽고 의견 작성
3. Single StateGraph → add_node/add_edge로 Fork-Join 제어

논문:   Analyst(4) → Researcher(2) → Trader → Risk(3) → Fund Manager
우리:   Context(1) → Bull(1)∥Bear(1)∥Risk(1) → Facilitator(1)
                     ↑ Fork (병렬)              ↑ Join
```

## Agent 역할

| Agent | 모델 | 내용 |
|:------|:----|:------|
| **Context** | V3 | fair_value_v3 + Finnhub 뉴스 + Insider + Macro Briefing(cron) → 3문장 분석 |
| **Bull** | V3 | "PER75:PBR25 기준 살 이유 3가지" (3문장) |
| **Bear** | V3 | "PER75:PBR25 기준 사면 안 되는 이유 3가지" (3문장) |
| **Risk** | V3 | 포지션 리스크 + 변동성 + 정보 불확실성 (3문장, 논문 3명→1명 통합) |
| **Facilitator** | R1 | 3개 의견 종합 → PER75:PBR25 최종 결정. 논문의 Facilitator+Trader+FundManager 통합 |

## 데이터 소스 정책

| 분류 | 허용 | 금지 |
|:-----|:-----|:-----|
| **미국주** | yfinance (15~20분 지연), Finnhub (무료, 일300회), sec-edgar-mcp | 유료 API (Bloomberg/Reuters) |
| **한국주** | **네이버 증권 홈페이지**, **네이버 뉴스** (cron+Hermes Agent), Analyst Target(cron, 너구리 제공) | yfinance, Finnhub |
| **공통** | cron 거시경제 브리핑, SEC EDGAR | SNS/Reddit/X |

## 비용 (DeepSeek API, 추정치)

| 구분 | 1회 | 월 8회 |
|:----|:---:|:------:|
| V3×4 (Context+Bull+Bear+Risk) | ~8원 | ~64원 |
| R1×1 (Facilitator) | ~4원 | ~32원 |
| **합계** | **~12원** | **~96원** |
| 예산 30,000원 대비 | 0.04% | 0.32% |

> ⚠️ DeepSeek 가격표 기반 추정. 실제 비용은 실행 후 Cost Monitor 측정 필요.
> n rounds debate으로 확장해도 예산 내 (3R=168원/월=0.56%).

## 한국주 vs 미국주 전체 데이터 흐름

```
[미국주] yfinance → fair_value_v3 → JSON
        Finnhub → 뉴스/Insider/SEC Filing
        cron → Macro Briefing
                ↓
        Context (V3): fair_value + 뉴스 + Macro
                ↓
        Bull(V3)∥Bear(V3)∥Risk(V3) → Facilitator(R1) → BUY/SELL/HOLD

[한국주] 네이버 증권 홈페이지 → fair_value_v3 → JSON
        네이버 뉴스 (cron) → 뉴스
        cron → Analyst Target + Macro Briefing
                ↓
        동일한 LangGraph 파이프라인 (Context→Bull∥Bear∥Risk→Facilitator)
```
