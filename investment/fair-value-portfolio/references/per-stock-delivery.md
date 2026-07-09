# Per-Stock Discord Delivery (종목별 분할 전송)

## Why (왜 필요한가)

2026-06-06 사용자 교정: "truncate가 아니라 요약을 해서 해야지 / 아니야 전부 보이는 버전을 원해 / 분할해서 종목별로 디스코드로 보내주도록"

**문제점:**
- 이전: `report.py`가 Bull/Bear/Risk를 200~250자로 truncation → 내용 손실
- 이전: 모든 종목을 하나의 긴 Discord 메시지로 전송 → 스크롤 압박, 종목별 검토 불편
- 이전: `graph.py`가 macro_summary를 2000자로 truncation → 시장 해석 내용 손실

## How (구현)

### 1. `report.py` (v4) — truncation 제거

```python
def generate_stock_report(r: dict, idx: int) -> str:
    """1개 종목의 전체 리포트 생성 (truncation 없음)"""
    # 모든 필드를 원본 그대로 표시
    context = r.get("context_analysis", "")       # 전체
    bull = r.get("bull_case", "")                  # 전체
    bear = r.get("bear_case", "")                  # 전체
    risk = r.get("risk_case", "")                  # 전체
    rationale = r.get("rationale", "")             # 전체
    # ... (이전: [:200], [:250] truncation)
```

### 2. `pipeline.py` — 종목별 파일 저장

```python
from src.report import save_stock_reports, save_report

# Phase 2 완료 후:
stock_dir = os.path.join(LOGS_DIR, "stocks")
stock_paths = save_stock_reports(results, cost, stock_dir)
# 저장 예: logs/decisions/stocks/20260606_1830_NVDA.md
#           logs/decisions/stocks/20260606_1830_MU.md
```

### 3. Discord 전송 (Hermes Agent)

파이프라인 완료 후, Hermes Agent가 각 파일을 읽어 send_message로 개별 전송:

```python
# Hermes Agent 측 (pipeline 외부)
stock_dir = "/home/ubuntu/trading-agents-nuri-langgraph/logs/decisions/stocks/"
for f in sorted(os.listdir(stock_dir)):
    if f.endswith(".md"):
        content = read_file(os.path.join(stock_dir, f))
        send_message(content)  # 각 종목을 개별 Discord 메시지로
```

## Per-Stock Report Format

각 종목 리포트는 다음 섹션을 포함, **종목 간 반드시 2줄 간격**:

```
**1️⃣ NVDA** — ⚪ HOLD 🔶
────────────────────────────────────────
📌 현재: $110 | 적정PER: 25.0 | 현재PER: 28.5
📌 T1: $135 | Target: $130
📌 중간값: $132 (**괴리율: +20.0%**)

📋 **종합 분석:**
(6문장: PER괴리율, FPER 의미, 시장 해석 인용, 매크로 데이터, 뉴스 인용, 종합)

🟢 **Bull 근거:**
(6문장: PER저평가 %, 시장해석 Bull, 뉴스 Bull)

🔴 **Bear 근거:**
(6문장: PER고평가 %, 시장해석 Bear, 뉴스 리스크)

⚠️ **Risk 평가:**
(4문장: FPER 리스크, 거시경제, 뉴스 리스크, 정보 신뢰도)

💡 **판단 근거:**
(4문장: PER수치, 중간값괴리율, 시장해석 근거, 매크로/뉴스 근거)
```

## graph.py — truncation 금지 규칙

```python
# graph.py run_single()
macro_context_part = {
    "summary": macro_summary,              # 전체 (이전: [:2000])
    "news": news_context,
    "market_interpretation": interp_text,  # 전체 (이전: [:1000])
    "key_macro_data": key_data_text,       # 전체 (이전: [:500])
}

# impact_analysis도 전체
if impact: interp_parts.append(f"🔗 Impact: {impact}")
# (이전: impact[:300])
```

### 4. report.py helper — `generate_stock_sections()`

`generate_stock_sections(results, cost_text)`는 Hermes Agent가 Discord로 보내기 편하도록 `[{"type": "header", "content": ...}, {"type": "stock", "content": ..., "name": ...}]` 형식의 리스트를 반환. 각 stock entry를 `send_message`로 개별 전송 가능.

### 5. import scope 주의 (pipeline.py)

`save_stock_reports`는 `run_phase2()` **내부에서** import해야 함 (`from src.report import save_stock_reports`). 이유: `run_phase2()`에서 `_sys.path.insert(0, PROJECT_DIR)`로 경로 설정한 후에 import해야 `from src.report`가 동작함. pipeline.py 최상단에서 import 시도하면 경로 미설정으로 `ModuleNotFoundError` 발생.

## 주의사항

1. **macro_summary가 매우 큰 경우** (10K+ 문자): DeepSeek V3 컨텍스트는 64K이므로 문제 없음. Bull/Bear Agent가 전체 macro 리포트를 읽고 관련 부분만 골라 인용.
2. **per-stock 파일 관리**: `logs/decisions/stocks/`는 하루치만 보관. 다음 실행 시 덮어씀.
3. **Discord 메시지 길이**: 각 종목 리포트가 4000자를 초과할 수 있음. DeepSeek V3 출력은 보통 1500~2500자이므로 문제 없지만, 만약 초과 시 2000자 단위로 분할 전송 필요.
