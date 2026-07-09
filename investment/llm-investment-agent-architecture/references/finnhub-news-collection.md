# Finnhub News Collection for Investment Pipeline

## API Key Verification
```bash
# Profile 확인
curl -s "https://finnhub.io/api/v1/stock/profile2?symbol=AAPL&token=$FINNHUB_API_KEY"

# News 확인 (7일 window)
curl -s "https://finnhub.io/api/v1/company-news?symbol=NVDA&from=2026-05-30&to=2026-06-06&token=$FINNHUB_API_KEY"
```

## Free Tier Limits
- **Daily limit**: 300 calls/day
- Usage for 16 US tickers: ~23 calls/day

## Implementation: Phase 0.5 (collect_macro_context.py)

### Data Flow (독립 실행)
```
Phase 1 output (filtered_top10.json)
  → collect_macro_context.py (Phase 0.5, 독립 실행 가능)
    → Finnhub API (US tickers only) — 3 news articles per ticker
    → Save data/macro_context.json
  → run_phase2.py (Phase 2, 독립 실행)
    → Reads macro_context.json
    → Injects into graph.py: macro_context={"summary": ..., "news": ...}
    → context.py passes to prompts.py CONTEXT_PROMPT
```

### 실행 방법
```bash
# 독립 실행 (Phase 0.5)
cd ~/trading-agents-nuri-langgraph && venv/bin/python3 pipeline.py --phase 05

# 또는 pipeline.py 전체 실행 시 자동 포함
venv/bin/python3 pipeline.py
```

### Per-ticker Test Results (2026-06-06)
| Ticker | News Count | Notes |
|:------|:----------:|:------|
| NVDA | 3 | Finnhub full result |
| AVGO | 3 | Finnhub full result |
| MU | 1 | Finnhub |
| SNDK | 1 | Finnhub |
| HPE | 0 | No recent news in window |
| 005930.KS | 1 | KR placeholder |
| 000660.KS | 1 | KR placeholder |

### Error Handling
- Finnhub rate limit (HTTP 429): returns empty list, pipeline continues
- API key missing (empty env): returns placeholder message, pipeline continues
- No macro report file: `macro_report_summary = ""`, pipeline continues

## Enhanced Prompt Templates (V2 — with News + Macro)

### Context + Analysis (V3) — macro + news sections
```python
CONTEXT_PROMPT = """
🌍 매크로 컨텍스트:
{macro}

📰 종목 뉴스:
{news}

분석 내용 (5문장 이내, 구체적 수치 기반):
1. 현재 PER vs 적정PER 평가 (구체적 괴리율 수치 사용)
2. Forward EPS 기반 실적 개선 전망의 현실성
3. 매크로/뉴스가 밸류에이션에 미치는 영향
4. 정보 신뢰도 및 데이터 한계점
5. 종합 의견"""
```

### Bull Researcher (V3) — 구체적 수치 강제
```python
BULL_PROMPT = """
다음 기준으로 매수 근거를 구체적 수치와 함께 3문장으로 제시:
1. PER/PBR 수치 기반 저평가 근거 (구체적 괴리율 %)
2. Forward EPS가 현실화될 경우 기대 수익률
3. 뉴스/매크로가 Bull 관점을 지지하는 요소
각 근거에 괴리율 %와 가격 수치를 반드시 포함하세요."""
```

### Decision Maker (R1) — HOLD에도 구체적 근거
```python
DECISION_PROMPT = """
Rule 1: 현재 PER > 적정PER이면 → HOLD (Bull/Bear 근거와 무관)
  이유: PER75:PBR25 공식에서 PER 비중 75% — 현재 PER이 적정 범위 밖이면 어떤 호재도 매수 정당화 불가

Rationale: (HOLD인 경우에도 구체적 수치로 근거 설명. "Rule 1 때문"만 말고 PER 수치와 괴리율 함께 제시)"""
```

## Implementation: context.py (macro_context 주입)

```python
def analyze_context(state: dict) -> dict:
    macro = state.get("macro_context", {})
    macro_summary = macro.get("summary", "제공되지 않음")
    news = macro.get("news", "최신 뉴스 데이터 없음")
    
    prompt = CONTEXT_PROMPT.format(
        ticker=state["ticker"], price=state["price"],
        fair_pe=state["fair_pe"], midpoint=state["midpoint"],
        macro=macro_summary,  # ← 매크로 리포트 요약
        news=news,            # ← Finnhub 뉴스
    )
    ...
```

## Implementation: graph.py (매크로 컨텍스트 매칭)

```python
def run_single(stock: dict, macro_context: dict = None) -> dict:
    stock_news = []
    macro_summary = ""
    if macro_context:
        macro_summary = macro_context.get("macro_report_summary", "")
        for s in macro_context.get("stocks", []):
            if s.get("name") == stock["name"]:
                stock_news = s.get("news", [])
                break
    
    news_text = ""
    for n in stock_news[:3]:
        news_text += f"- {n['title']}: {n['summary'][:200]}\n"
    
    news_context = news_text[:800] if news_text else "최신 뉴스 데이터 없음"
    
    state = AgentState(
        ...
        macro_context={"summary": macro_summary[:1500], "news": news_context},
        ...
    )
```

## Caveats
- Finnhub does NOT support Korean stocks (KR tickers)
- News content truncated to 200 chars per article (prompt budget)
- HPE returned 0 news — may happen for smaller tickers on weekends
- Total cost impact of news: ~+36원/pipeline run (longer prompts = more tokens)
