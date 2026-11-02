---
name: llm-investment-agent-architecture
description: "LLM 기반 투자 판단 보조 에이전트 시스템 설계 방법론 — LangGraph, 데이터 소스 선정, 매크로 리포트, 포트폴리오 포워드 테스팅, 비용 최적화, 운영 체크리스트"
---

# LLM Investment Agent Architecture Design

> TradingAgents 논문(2412.20138) 기반, 너구리 가치투자 철학(PER75:PBR25)에 최적화된 LLM 투자 에이전트 설계 방법론.

## 🎯 적용 대상

- LLM Multi-Agent 기반 투자 판단 보조 시스템
- 가치투자 중심 (PER/PBR 기반, 데이트레이딩 X)
- 월 예산 3만원 이하 초경량 시스템
- LangGraph Fork-Join 패턴 활용

---

## 🧠 철학 (Override — 항상 우선)

```
1. 단순할수록 유지보수하기 쉽고 신뢰할 수 있다.
2. 정보의 최신성과 정확성이 전부다.
3. 모든 이벤트에 LLM을 호출하지 않는다 (Strategic Silence).
4. 유료 데이터는 절대 사용하지 않는다.
5. 비용은 추정이 아니라 실제 축적값을 추적한다.
```

---

## 🏛️ 표준 아키텍처 (10개 노드, 4개 레이어)

```
HOOK LAYER (LLM 0회)
  ├─ Source & Freshness Check
  ├─ **Midpoint Gap Filter** (30%↑, 상위 10종목) ← 🆕
  └─ Fair-Value Snapshot

### Midpoint Gap Filter 규칙

Bull/Bear/Decision Maker(LLM) 진입 전, 전체 종목을 30% 기준으로 선별한다.

```python
midpoint_gap = ((Model_T1 + Analyst_Target) / 2 / 현재가 - 1) × 100
if midpoint_gap >= 30:  # 상위 10종목만 통과
    candidates.append(ticker)
```

- **계산**: Model T1과 Analyst Target의 산술평균 → 괴리율
- **기준**: 30% 이상 & 상위 10종목
- **Analyst 미존재**: Model T1 단독 사용

ANALYSIS LAYER (LangGraph 병렬 구간)
  ├─ Context + Analysis (V3)
  ├─ Bull Researcher (V3)     ← Parallel
  ├─ Bear Researcher (V3)     ← Parallel
  └─ Decision Maker (R1)      ← Join

VERIFICATION LAYER (LLM 0회)
  ├─ Risk Check
  ├─ Hypothesis Store
  └─ Post-mortem Log

MACRO/NEWS LAYER (Phase 0.5 — LLM 0회, API 호출만)
  └─ **collect_macro_context.py**
       ├─ Finnhub API로 종목별 뉴스 3건 수집 (US ticker만)
       ├─ 최신 매크로 리포트 파일 읽기
       └─ data/macro_context.json 저장

PHASE 3 LAYER (LLM 1회, 포트폴리오 할당)
  └─ **portfolio_allocation.py**
       ├─ Regime 기반 현금 비중 결정
       ├─ Gap+Moat 기반 종목별 비중 산정
       └─ logs/portfolio/YYYY-MM-DD.json 저장

VALIDATION LAYER (LLM 0회, 결정 검증)
  └─ **decision_validator.py**
       ├─ logs/decisions/ 모든 JSON 읽기
       ├─ US ticker: yfinance / KR ticker: yfinance .KS
       ├─ 결정가 vs 현재가 비교 → 수익률 측정
       └─ logs/validation/YYYY-MM-DD.json + .md 저장

FEEDBACK LAYER (월 1회, DeepSeek V4 Flash)
  └─ **monthly_performance_review.py**
       ├─ 지난달 결정 + 포트폴리오 + 검증 데이터 통합
       ├─ DeepSeek LLM 분석 (5개 섹션)
       ├─ logs/monthly_review/YYYY-MM.md 저장
       ├─ Discord 전송
       └─ mybotagent/trading-agents-nuri-feedback 저장소
```

---

## 🕐 크론 및 Pipeline 통합 — Phase 독립 실행 + 저장된 데이터 체인

### 문제: 기존 스크립트는 stdout만 출력, 파일 저장 없음

`fair_value.py`와 `analyst_target_collector.py`는 **모두 print()로만 출력하고 파일을 저장하지 않는다.**
Hermes cron은 stdout을 받아 Discord 메시지로 전송한 후 **데이터를 폐기**한다.
→ LangGraph 파이프라인이 읽을 JSON 파일이 **존재하지 않는다.**

### 해결: 독립 실행 가능한 Phase들 (저장된 데이터 체인)

각 Phase는 독립적으로 실행 가능하며, 저장된 JSON 파일로만 연결된다. 기존 cron은 건드리지 않고 pipeline이 **독립적으로 데이터를 재수집**한다:

```
Phase 0  (capture_and_save.py)       → daily_snapshot.json 저장
Phase 0.5 (collect_macro_context.py)  → macro_context.json 저장 (Finnhub 뉴스)
Phase 1  (midpoint_filter.py)         → filtered_top10.json 저장
Phase 2  (run_phase2.py)              → filtered + macro 읽어서 LangGraph 분석
```

### 실행 방법

```bash
# 전체 파이프라인
cd ~/trading-agents-nuri-langgraph && venv/bin/python3 pipeline.py

# 개별 Phase
venv/bin/python3 pipeline.py --phase 0    # Phase 0만
venv/bin/python3 pipeline.py --phase 05   # Phase 0.5만
venv/bin/python3 pipeline.py --phase 1    # Phase 1만
venv/bin/python3 run_phase2.py            # Phase 2만 (독립 실행 파일)
```

### 실행 순서 (저장된 데이터 의존성)

```bash
# 올바른 순서
1. pipeline.py --phase 0    → daily_snapshot.json 생성
2. pipeline.py --phase 05   → macro_context.json 생성
3. pipeline.py --phase 1    → filtered_top10.json 생성 (daily_snapshot 의존)
4. run_phase2.py            → LangGraph 분석 (filtered + macro 의존)
```

### Phase 0.5 상세 (Macro Context + News)

```python
# collect_macro_context.py — Finnhub API로 종목별 뉴스 3건 수집
# 1. filtered_top10.json 읽기
# 2. Finnhub API로 종목별 뉴스 3건 수집 (US ticker: NVDA→3건, AVGO→3건, MU→1건)
#    - 한국주(KR ticker): Finnhub 미지원 → placeholder
#    - Finnhub rate limit(429): 빈 리스트 반환, 파이프라인 계속
# 3. data/macro_context.json에 저장
# 4. LangGraph Phase 2에서 읽어서 Context 프롬프트에 주입
```

### 실제 비용 (2026-06-06 테스트, 7종목 Finnhub + LangGraph)

| 실행 | 비용 | 비고 |
|:----|:----:|:-----|
| 1차 (기본 pipeline) | 146원 | 뉴스 없음 |
| 2차 (뉴스 포함) | 222원 | Finnhub 7종목 + V3 28회 + R1 7회 |
| 3차 (뉴스 포함) | 258원 | Context 크기 증가 |
| **예상 월간** | ~1,600원 | 일 1회 × 22영업일 |

### 전체 타임라인 (KST) — 최종

```
04:00 📚 새벽 wiki 동기화 + 메모리 정리   (매일, 64adaa)
06:00 🗑️ 데이터 Clean up (US 장 마감 후)  (매일, 38f08c, no_agent)
      - fair_value_stdout.txt, analyst_stdout.txt 삭제
      - daily_snapshot.json, filtered_top10.json, macro_context.json 삭제
      - stocks/ 종목별 리포트 삭제 (히스토리 로그는 보존)
      - 08:10 크론이 새 데이터 생성 → 문제 없음
08:00 📅 구글 캘린더 일정 요약            (매일, 2f553e)
08:10 📊 오전 포트폴리오 + KR/US 브리핑  (평일, 6297df)
08:30(월) 📆 주간 계획                    (월, 47f701)
18:00 🇺🇸 미국 증시 브리핑               (평일, b5bbf6)
18:30 🌍 매크로 전략 리포트              (매일, e69746)
      → macro_context.json 저장 (시장 해석 + 수치 + 글로벌뉴스)
18:35 🧠 LangGraph 파이프라인            (평일, 62e57f, no_agent)
      → run_pipeline.sh → 사전 데이터 읽기 → LangGraph 분석 → 리포트 전송
매월1일 📈 월간 전략 리포트              (1일, d3080e)
```

### 저장 규칙: Daily Storage → Clean up at 06:00

| 파일 | 위치 | 갱신 | Clean up |
|:----|:-----|:----|:---------|
| daily_snapshot.json | `~/trading-agents-nuri-scripts/data/` | Phase 0 실행 시 덮어씀 | 06:00 KST 삭제 |
| macro_context.json | 동일 | Phase 0.5 실행 시 덮어씀 | 06:00 KST 삭제 |
| filtered_top10.json | 동일 | Phase 1 실행 시 덮어씀 | 06:00 KST 삭제 |
| fair_value_stdout.txt | 동일 | 08:10/18:00 크론이 덮어씀 | 06:00 KST 삭제 |
| analyst_stdout.txt | 동일 | 08:10/18:00 크론이 덮어씀 | 06:00 KST 삭제 |
| logs/decisions/`*.md/*.json` | `~/trading-agents-nuri-langgraph/logs/` | Phase 2 실행 시 추가 | **보존** (히스토리) |
| logs/decisions/stocks/`*.md` | 동일 | Phase 2 실행 시 저장 | 06:00 KST 삭제 |

**Clean up 스크립트**: `~/trading-agents-nuri-scripts/src/cleanup_daily_data.py` (cp to `~/.hermes/scripts/`)
- 이유: US 장 마감 후(16:00 ET = 05:00~06:00 KST) 모든 중간 데이터 정리
- 08:10 크론이 새 데이터 생성 → clean up 해도 문제 없음

---

### 📦 데이터 소스 선정 기준

### 허용 (무료 + 실시간 + 신뢰 가능)
| 소스 | 용도 | 제한 | 비고 |
|:----|:-----|:----:|:-----|
| **yfinance** | 주가, PER, FPE, PBR, ROE, EPS, Analyst, **US/KR 현재가** | rate limit | 15~20분 지연 인지. 한국주는 .KS suffix |
| **Finnhub** | 뉴스, Insider, SEC Filing (미국주 전용) | 일 300회 무료 | 한국주 미지원 |
| **SEC EDGAR (sec-edgar-mcp)** | 10-K, 10-Q, 8-K 공시 | 무료, MCP 서버 | 미국주만 |
| **네이버 증권 홈페이지** | 한국주 PBR 직접 스크래핑 ⭐ | 무료 | `fair_value.py` 110~120줄 |
| **네이버 컨센서스** | 한국주 Analyst Target (참고용) **← 결정 검증기 아님** | 무료 | `analyst_target_collector.py` 85~109줄, `item/coinfo.naver` 스크래핑 |
| **네이버 증권 리서치** | 한국주 최근 리포트 목록 | 무료 | `get_kr_recent_reports()` |
| **네이버 뉴스** | 한국주 뉴스 수집 | 무료 | cron + Hermes Agent web |
| **너구리 제공 Target** | 한국주 Analyst Target (1순위) | 수동 업데이트 | 삼전 ₩500K, SK하닉 ₩4M |

> **한국주 데이터**: 네이버 증권(PBR) + 네이버 뉴스 + 너구리 Analyst + 네이버 컨센서스 + 네이버 리서치로 완전 커버.  
> **Naver scraping은 `analyst_target_collector.py`에서 analyst target 수집용으로만 사용. `decision_validator.py`는 yfinance로 US/KR 모두 처리.**
> "취약"이라고 표현하지 말 것. 가치투자(PER+PBR)에 충분한 수준.

### 금지
| 소스 | 사유 |
|:----|:-----|
| Bloomberg/Reuters API | ❌ 유료 |
| 뉴스 API 구독 | ❌ 유료 |
| SNS/Reddit/X | ❌ 신뢰도 낮음, 노이즈 |
| Finviz | ❌ 15~20분 지연 데이터 |

---

## ⚡ LangGraph 활용 패턴 — Fork-Join만 사용

### 필요한 경우: Bull/Bear 병렬 Debate

```python
# Fork: Context → Bull, Bear 병렬 분기
builder.add_edge("context_analysis", "bull_researcher")
builder.add_edge("context_analysis", "bear_researcher")

# Join: Bull + Bear → Decision (둘 다 끝날 때까지 기다림)
builder.add_edge("bull_researcher", "decision_maker")
builder.add_edge("bear_researcher", "decision_maker")
```

### 사용하지 않는 LangGraph 기능
- ❌ Multi-round Debate (n rounds) — 1회로 충분
- ❌ Human-in-the-loop — 자동화가 목적
- ❌ 복잡한 State 분기 — 단순 선형이면 Python 함수로 충분
- ❌ Persistence (checkpoint) — 로그 파일로 대체

### 판단 기준
```
병렬 Fork-Join 필요? → LangGraph 사용
순차 실행?           → Python 함수 체인 (LangGraph 불필요)
```

---

## 💰 비용 최적화 원칙

1. **Strategic Silence**: Hook Layer에서 노이즈 즉시 폐기 (LLM 0회)
2. **Bull/Bear는 V3 사용** (R1 불필요 — 간단한 근거 제시)
3. **Decision Maker만 R1 사용** (깊은 추론 필요)
4. **실제 토큰 로깅**: 실행 시마다 input_tokens, output_tokens 기록
5. **월 30,000원 하드 리밋**: 초과 시 전체 분석 중단

### 예상 비용 (주 2회, 8회/월)
| 구성 | 비용 | 실제(POC 7종목) | 비고 |
|:----|:----:|:---------------:|:-----|
| V3 3회 (Context + Bull + Bear) | ~48원 | ~67원 | 종목 수에 비례 |
| R1 1회 (Decision Maker) | ~32원 | ~79원 | Context 크기에 비례 |
| **합계** | **~80원/월** | **~146원/회** | 7종목 기준, 10종목 시 ~200원 예상 |

---

## 📋 Prompt 설계 원칙

1. **Bull/Bear 3문장 강제** — 출력 토큰 최소화
   - 각 문장에 **구체적 % 수치** 반드시 포함 (예: "적정PER 대비 39.4% 고평가")
   - 1문장: PER/PBR 수치 기반 저평가/고평가 근거 (괴리율 %)
   - 2문장: Forward EPS 현실화 시 기대 수익률 또는 하방 위험
   - 3문장: 뉴스/매크로가 해당 관점을 지지하는 요소
2. **Decision Maker는 Bull/Bear 중 선택** — 새로운 분석 금지
3. **"PER75:PBR25 단일공식" 시스템 프롬프트에 고정 포함**
4. **출처 명시 강제** — "무슨 데이터로 이 결론을 내렸는가?"
5. **HOLD 결정 시에도 구체적 수치로 근거 설명** — "Rule 1 때문"만 하지 않고 PER 수치와 괴리율 함께 제시
6. **Context 프롬프트에 매크로 + 뉴스 + 시장 해석 섹션 포함**:
   ```
   🌍 매크로 리포트 (시장 해석 포함):
   {macro_summary}

   📊 핵심 매크로 데이터:
   {key_macro_data}

   🎯 시장 해석 (18:30 크론 리포트):
   {market_interpretation}

   📰 종목 뉴스:
   {news_text}
   ```
7. **Context 분석 6문장 (Bull/Bear/Risk도 6문장 이상)**:
   - 1: PER 괴리율 % 평가
   - 2: Forward PER 기반 EPS 증가 현실성
   - 3: 시장 해석(Key Driver/Regime) 중 해당 종목에 직접적 영향 주는 요소
   - 4: 매크로 데이터(금리/고용/물가) 중 해당 종목 영향 지표
   - 5: 뉴스 중 가장 중요한 이슈 1개 인용
   - 6: 종합 의견
8. **Rationale 4문장 (Decision Maker)**:
   - ① PER 수치 괴리율 (%)
   - ② 중간값 괴리율 의미
   - ③ 시장 해석(Key Driver/Regime) 근거
   - ④ 매크로/뉴스 중 가장 중요한 근거 1개
9. **Bull/Bear 6문장 (2문장 × 3근거)**: PER 수치 + 매크로/시장 해석 + 뉴스

---

## 📝 Post-mortem 로깅 (필수, 백테스트 대체)

백테스트를 할 수 없는 LLM 시스템에서 **과정의 타당성**을 기록하는 것이 최선.

```
logs/{date}/{ticker}/full_log.json
├── raw_data: 원본 데이터 (타임스탬프, 출처)
├── processing: Context + Bull + Bear + Decision (CoT)
├── hypothesis: 예측 저장 → 3개월 후 검증
└── cost: 노드별 토큰/비용
```

### Hypothesis Store (자기 검증)
```python
hypothesis = {
    "action": "BUY",
    "price": 220.0,
    "target": 250.0,
    "rationale": "T1괴리율 38%",
    "verify_at": "3개월 후",
    "status": "pending"  # → correct / wrong
}
```

---

## 🌍 Daily Macro Strategy Report (매크로 전략 리포트)

> **통합**: 이 섹션은 `macro-strategy-report` 스킬의 내용을 흡수했습니다.
> **실행**: 매일 18:30 KST cron (job_id: e69746). 미국 증시 브리핑(18:00) 후 추가 리포트.

### 🧠 사용자 선호 (반드시 준수)

1. **투자 영향도 순 정리**: Priority 1 → 5 순. 맨 아래 Priority Matrix 요약 표로 마감.
2. **데이터의 최신성과 정확성 최우선**: 24~48시간 내 데이터. 출처 꼬리표 명시 ([Reuters 6/5]). 가상 데이터 절대 금지.
3. **BUY/CAUTION 신호 명확히 구분**: Orbit T0/T1 괴리율 + FPER 분석 기반. FPER 5~10 종목은 하방 레버리지 경고 필수.
4. **추정 불가 영역은 '데이터 미비'로 명시**: 억지 결론 금지. Counter-factual 확률은 데이터 기반으로만.
5. **크론잡 등록/수정은 무조건 사용자 승인** — 동의 없이 등록 금지.
6. **기존 크론잡 절대 수정 금지, 추가만 가능**.

### 📋 리포트 구조 (6개 섹션)

#### 1. Executive Summary
- **Key Driver 1가지**와 파급력 요약. 세 가지 미만 핵심 축(Axis)으로 구조화.

#### 2. Current Macro State
표: 지표명 | 수치 | 방향성(⬆️➡️⬇️) | 해석 | 출처

#### 3. Causal Linkage
[원인 → 전파 경로 → 결과] 메커니즘. 각 주제마다 ```` 인과 체인. 포트폴리오 25종목별 Direct/Indirect Impact.

#### 4. Counter-factual Analysis
2~3개 반대 시나리오. 각 시나리오: Trigger | 3개월 내 전파 경로 | 포트폴리오 영향 | 확률(%) | 데이터 미비

#### 5. Structural Implications (6~12개월)
✅ 예측 가능 변화 / ⚠️ 데이터 미비로 추정 불가 (명시 후 유보)

#### 6. Priority Matrix (맨 아래)
| 순위 | 이슈 | 영향 종목 | 방향성(🟢/🟡/🔴) | 신뢰도(高/中) |

### 🔍 Source Hierarchy

| 순위 | 출처 유형 | 예시 |
|:---:|:---------|:----|
| **1순위** | 공식 기관 | IMF, BIS, World Bank, Fed, ECB, BOJ |
| **2순위** | 공식 싱크탱크 | CFR, CSIS, Peterson Institute |
| **3순위** | 경제 외신 | Reuters, Bloomberg, CNBC, WSJ, FT |
| **❌ 배제** | 추측/커뮤니티/차트 | Reddit, X/Twitter, Seeking Alpha 코멘트 |

### 📡 데이터 수집 (cron 환경 fallback)

**방법 A (Preferred)**: 개별 툴로 직접 검색 (`web_search`, `browser_navigate`)

**방법 B (Fallback — cron 환경)**: Google News RSS → curl + grep
```bash
curl -s "https://news.google.com/rss/search?q=KEYWORD&hl=en-US&gl=US&ceid=US:en" \
  | grep -oP '<title>.*?</title>' | head -20
```
XML 파싱: Python `xml.etree.ElementTree` 사용 (stdlib, 의존성 없음).

**투자 카테고리별 RSS 검색 패턴**은 `references/rss-feed-patterns.md` 참조:
1순위: 반도체·AI (HBM/DDR5, AI CapEx, 반도체 매도)
2순위: 통화정책 (Fed, 고용/물가, ECB/BOJ)
3순위: 지정학 (미중 갈등, 이란/중동)
4순위: 한국 시장 (KOSPI, 원/달러, COMPUTEX)

**⚠️ Pitfall**: `delegate_task`로 뉴스 수집 금지 — 서브 에이전트가 검색을 설명만 하고 실행 안 함. 직접 `terminal()` 호출.
**⚠️ Pitfall**: Google News RSS에 한글 검색어는 HTTP 400. 항상 영문 키워드 사용.

### 🎯 투자 판단 프레임워크 (Orbit T0/T1 연동)

`fair-value-portfolio`의 T0/T1 괴리율 + FPER 데이터를 매크로 리포트에 연계:

#### T0 vs T1 갭 분석

| 패턴 | T0 괴리율 | T1 괴리율 | 해석 | 판단 |
|:----|:--------:|:--------:|:-----|:----:|
| **메모리 트랩** | -56~-71% | +59~+94% | 현재가 2~3배 비쌈. FPER 5~10 기반 EPS 폭발 가정 | 🔴 하방 레버리지 > 상방 |
| **AI Core 적정** | -12~-29% | +18~+70% | T0 적정가 근접, T1 구조적 성장. PE/FPE 1.5~2.5 건강 | 🟢 매수/관심 |
| **Non-AI 정체** | ±20% | ±15% | 고평가도 저평가도 아님 | 🟢 안전자산 |
| **장비주 고PER** | -55~-62% | -32% | PER 60~75, FPER도 높아 개선 중 | 🔴 멀티플 부담 |

#### Analyst-Model 갭

| 갭 | 의미 | 신뢰도 |
|:--:|:----|:-----:|
| Analyst ≈ Model (±10%) | 일치 = fair value 신뢰도 높음 | 🟢 HIGH |
| Model > Analyst (+15~50%) | Model 낙관적. 성장성 높게 평가 | 🟡 검증 필요 |
| Model < Analyst (-10~25%) | Model 보수적. 과대낙관 경계 | 🟢 타당 |

#### 종합 판단 기준

| 조건 | 판단 |
|:----|:----:|
| T1 ≥ +20% + FPER ≥ 12 + T0 ≥ -30% | 🟢 **매수** |
| T1 ≥ +50% + FPER < 12 + T0 ≤ -50% | 🔴 **경계 (FPER 트랩)** |
| T1 ≥ +50% + FPER < 12 + Analyst ≈ Model | 🟡 **조건부 관심** |
| T1 < 0~+15% + T0 ±20% 내 | 🟢 **안전주/방어** |
| T1 ≥ +100% + 마진 10% 미만 | 🟡 **투기적** |

### 💾 JSON 저장 형식 (Pipeline 연동 → macro_context.json)

리포트가 Discord로 전송되기 **전에** 아래 JSON 저장:
```json
{
  "timestamp": "2026-06-06T18:30:00+09:00",
  "date": "2026-06-06",
  "macro_report_summary": "리포트 전문 (3000자 이상)",
  "key_macro_data": {"fed_rate": "4.25~4.50%", "dxy": "104.2", ...},
  "market_interpretation": {"key_driver": "...", "regime": "Goldilocks", ...},
  "news_items": [{"title": "...", "source": "Reuters", "impact": "high", ...}]
}
```

**Flow**: `18:30 크론 → macro_context.json 저장 → collect_macro_context.py (Finnhub 뉴스 추가) → LangGraph Phase 2 → 종목별 분석`

**포트폴리오 25종목**: NVDA, AVGO, LITE, MU, LRCX, STX, SNDK, TSM, AMD, INTC, CLS, TER, MRVL, HPE, GOOGL, AAPL, MSFT, DELL, LLY + 삼성전자, SK하이닉스, 삼성전기, 현대차, HD현대일렉, 에이피알

> 자세한 RSS 검색 URL 패턴: `references/rss-feed-patterns.md`

---

## 📊 Portfolio Forward Testing Framework

> **통합**: 이 섹션은 `portfolio-forward-testing` 스킬의 내용을 흡수했습니다.

### Trigger 조건
- 파이프라인 실행 후 (18:35 cron)
- 매월 1일 (월간 검증)
- 사용자가 "포워드 테스팅", "포트폴리오 기록", "검증", "피드백" 언급

### 1. 결정 검증 — Decision Validator (매일 자동)

```bash
cd ~/trade-pipeline && python3 langgraph/src/agents/decision_validator.py
```

- **US ticker**: yfinance 현재가 조회
- **KR ticker (.KS)**: 네이버 API(`api.finance.naver.com/service/itemSummary.nhn`) 조회
- 결정 시점 가격 vs 현재가 비교 → 수익률 측정
- `logs/validation/YYYY-MM-DD.json` + `.md` 저장

**주의**: 모든 결정이 같은 날짜면 수익률 0.00% (정상). 최소 1영업일 필요.

### 2. 포트폴리오 비중 산식 (v2 — t1_gap × moat)

```
보정_gap = max(0, t1_gap)
moat_점수 = LLM 추정 (1~10)
가중값 = 보정_gap × moat_점수
기본_비중 = (가중값 / Σ가중값_all) × (1 - cash_ratio)
비중 = clamp(기본_비중, 2%, 15%)
```

**변경 이력**: 2026-06-07 mid_gap 기반 → 06-08 v1 t1_gap 단독 → **06-08 v2 t1_gap × moat_score 곱셈식**

### 3. 현금 비중 (Macro Regime + Alpha-Flip + 뉴스 심각성)

| Regime | Base | +AlphaBearish(+5%p) | +AlphaBullish(-5%p) |
|:------:|:----:|:-------------------:|:------------------:|
| Goldilocks | 5% | 10% | 0% |
| Overheat | 15% | 20% | 10% |
| Slowdown | 25% | 30% | 20% |
| Stagflation | 40% | 45% | 35% |
| Severe_Inflation | 30% | 35% | 25% |
| Deflation | 10% | 15% | 5% |

극단적 이벤트 시 LLM이 **+10~20%p 추가 가능** (Broadcom 쇼크, 전쟁, 원화 급락 등), 최대 50%. `cash_reason` 필드에 근거 명시.

### 4. 결정 평가 기준

| Pipeline 판단 | 실제 결과 | Score |
|:-------------:|:---------:|:-----:|
| BUY | 주가 상승 | +2 |
| BUY | 주가 하락 | -1 |
| SELL | 주가 하락 | +2 |
| SELL | 주가 상승 | -1 |
| HOLD | ±5% 유지 | +1 |
| HOLD | >5% 상승 | 0 |
| HOLD | >5% 하락 | +1 |

**월간 Accuracy = ΣScore / ΣMaxScore × 100**

### 5. 월간 검증 — Monthly Performance Review (매월 1일 08:10 KST)

```bash
cd ~/trade-pipeline && python3 langgraph/src/monthly_performance_review.py
```

1. Decision Summary — BUY/SELL/HOLD 건수
2. Portfolio — Regime 분포, 평균 현금비중
3. **Decisions Validated** — `logs/validation/` 수익률 + 정확도
4. Weight Distribution — 상위 5개 종목
5. Cost Summary — 월 비용 (예산 30,000원 대비 %)
6. Improvement Suggestions — DeepSeek LLM 분석

**결정 검증 통합**: `collect_validation()` 함수로 `logs/validation/` 최신 JSON 읽기 → LLM 프롬프트에 섹션 자동 추가.

### 6. 예산 관리
- **월 한도**: 30,000원
- **90% 초과 경고**: 누적 27,000원
- **100% 도달**: 일부 분석 skip

### ⚠️ Forward Testing Pitfalls

**🟡 결정 평가는 최소 1영업일 간격 필요** — 같은 날 데이터는 수익률 0.00%.

**🟡 한국 주식 통화 표시 주의** — `decision_validator.py`의 `TICKER_MAP`은 yfinance 심볼 (.KS) 사용. `format_report()`에서 한국 종목은 `currency = "KRW"` 오버라이드.

**🟡 Naver API vs yfinance 데이터 소스 라우팅**:
- KR ticker 목표주가: `analyst_target_collector.py`의 `get_kr_naver_consensus(code)` — coinfo 페이지 스크래핑, euc-kr 인코딩, Referer 헤더 필요
- US ticker 목표주가: yfinance `upgrades_downgrades` (30일 window)
- KR ticker 현재가 (validator): yfinance `.KS` suffix
- US ticker 현재가 (validator): yfinance 일반 ticker

**⚠️ 데이터 누적**: 최소 2주(14일) 이상 누적 후 월간 검증 의미 있음.

**⚠️ migration 경로**: 구 `trading-agents-nuri-*` 레포 → `~/trade-pipeline/` 통합 완료. 자세한 디렉토리 구조 및 크론 경로는 `references/trade-pipeline-migration.md` 참조.

---

## 🔄 설계 프로세스 (요청 시)

1. 데이터 소스 확정 (무료만, 출처별 freshness 정의)
2. Hook Layer 설계 (Source & Freshness Check)
3. Analysis Layer 설계 (Context → Bull∥Bear → Decision)
4. Prompt 작성 (각 노드별, 3문장 제한)
5. 비용 산정 (실제 토큰 기반)
6. Post-mortem Log + Hypothesis Store 설계
7. Cost Monitor + 임계치 설정

---

## 🔗 관련 스킬

- **`fair-value-portfolio`**: 정량 밸류에이션 데이터 제공 (`fair_value.py`).
  - 이 스킬로 설계한 아키텍처의 Hook Layer가 `fair_value.py`의 출력을 입력으로 사용
  - `fair_value.py`의 T1괴리율, Sector Base, Analyst Target을 Context + Analysis 노드에 전달
- **`stock-rating-system`**: S+~F 정성 평가 (위험 체크용).

## ⚠️ 함정 및 주의사항 (Pitfalls)

### 🔴 크론 등록 전 항상 사용자 승인 — 무단 등록 금지 (2026-06-06 교정)
- 새 cron을 생각나자마자 바로 등록하지 말 것
- **반드시 사용자에게 먼저 제안/확인 후 등록** — "해줄까?" 형태로 물어볼 것
- 사용자가 "해줘봐"라고 하면 그때 등록
- "크론 등록 우선 하지말고" 같은 지시가 오면 즉시 중단하고 취소
- 이유: 사용자는 크론 등록 전에 코드 검토, 시간 확인, 테스트 등을 원할 수 있음
- 새 cron 등록 전 `cronjob(action='list')`로 전체 일정 확인 필수
- 같은 시간에 두 개의 cron이 등록되면 **먼저 실행된 하나가 에러**날 수 있음
- **6/6 사례**: 📅 캘린더(08:00) + 📊 포트폴리오(08:00) 동시 등록 → 포트폴리오 `last_status: error`
- 해결: 10분 간격으로 분리 (08:00 → 08:10)
- **규칙**: 같은 분에 2개 이상 cron 등록 금지. 최소 5~10분 간격 유지.

### 🔴 "기존 작업 그대로 두고 추가" — cron은 절대 수정 금지
- 새 cron은 항상 **추가(additive)** 로만 등록. 기존 cron의 시간/내용 변경 금지.
- 이유: 사용자는 각 cron의 시각적 일관성(08:00=아침, 18:00=저녁)에 익숙함
- 예외: 시간 충돌 감지 시에만 기존 cron 시간을 최소 조정 (10분 단위)
- **6/6 사례**: 사용자가 "__기존작업은 그대로 두고 추가작업임__"이라고 명시적으로 지시

### 🔴 새벽 wiki 동기화 cron 패턴
- 사용자가 "__나 잠자는 시간에__" wiki 정리 요청 → **04:00 KST**가 최적 (23:00~07:00 중 중간)
- 작업 내용: git add/commit/push/pull (hermes-wiki, hermes-wiki-claude-code, hermes-wiki-codex) + 메모리 정리
- SILENT 규칙: 변경사항 없으면 `[SILENT]` 출력 (잠자는 시간 알림 차단)
- job_id: 64adaa1d6b0e

### 🔴 API 키 탐색 시간 낭비 금지 — 이미 .env에 저장되어 있음 (2026-06-06 교정)
- DeepSeek API key, Finnhub API key는 이미 `~/trading-agents-nuri-langgraph/.env`에 저장되어 있음
- 절대 search_files/grep으로 키를 찾으려고 시간 낭비하지 말 것
- 키가 유효한지 확인하는 가장 빠른 방법: pipeline.py 실행해보기
- 6/6 사례: 사용자가 왜이렇게 해매냐고 지적 — .env에 이미 key 있었음

### 🔴 매크로 리포트는 크론(web_search)로 생성 — 스크립트가 아님
- `macro_strategy_report.py`는 월 1회 FRED 데이터 기반 리포트 (매월 1일 실행)
- 매일 18:30 KST에 생성되는 매크로 리포트는 cron e69746446a65가 web_search로 수집하는 것
- pipeline Phase 0.5(collect_macro_context.py)는 Finnhub 뉴스만 수집. 매크로 리포트 통합은 추후 크론 출력 저장 시 별도 추가 필요

### 🔴 기존 크론을 건드리지 말고 capture_and_save로 독립 재실행
- 기존 cron(08:10, 18:00)은 fair_value.py 실행 → Discord 출력
- pipeline Phase 0(capture_and_save.py)는 fair_value.py를 독립적으로 다시 실행해서 데이터 캡처
- 기존 cron과 pipeline은 완전 독립 — 각자 fair_value.py를 별도로 실행
- 이유: 기존 cron 수정 금지 원칙 + pipeline이 원하는 시간에 자유롭게 실행 가능
- **적용 대상**: DeepSeek API key, Finnhub API key, 그 외 모든 서드파티 키

### 🔴 전체 파이프라인은 `pipeline.py` 하나로 실행 (Phase 0→1→2)
- Phase 0 (`capture_and_save.py`) + Phase 1 (`midpoint_filter.py`) + Phase 2 (LangGraph)를 순차 실행
- `pipeline.py`가 stdout 캡처 → Midpoint 계산 → LangGraph 분석 → 통합 리포트 생성까지 한 번에 처리
- 위치: `~/trading-agents-nuri-langgraph/pipeline.py`
- 실행: `cd ~/trading-agents-nuri-langgraph && source venv/bin/activate && python3 pipeline.py`
- **크론 자동 실행**: `run_pipeline.sh` (no_agent=true, 18:35 KST 평일, job_id: 62e57fc30547)

### 🔴 리포트 출력 규칙 — 종목 간 2줄 간격, truncation 금지 (2026-06-06 교정)
- **절대 truncation 금지**: Bull/Bear/Risk/Rationale 모든 내용을 전체 출력할 것
  - `report.py`에서 `bull_case[:200]`, `bear_case[:200]`, `risk_case[:200]` 금지
  - `graph.py`에서 `macro_summary[:2000]`, `interp_text[:1000]` 금지
  - `context[:200]`, `rationale[:250]` 금지
  - 사용자 요청: "전부 보이는 버전을 원해" — LLM이 생성한 분석 전문을 보존
- **종목 간 2줄 간격 필수**: 각 종목 분석 사이에 빈 줄 2개 (`lines.append("")` × 2)
  - 이유: Discord에서 1줄은 시각적 구분이 안 됨. 사용자가 "종목사이에 두줄 띄워쓰기 해줘"라고 지적
- **종목별 개별 파일 저장**: `save_stock_reports()` → `logs/decisions/stocks/`에 각 종목별 .md 파일 저장
  - 파일명: `YYYYMMDD_HHMM_{종목명}.md` (예: `20260606_1807_NVDA.md`)
  - 이후 `send_message`로 개별 전송 가능
- **report.py 구조**: `generate_stock_report()` (1종목) + `generate_report()` (통합) + `generate_stock_sections()` (분할용) + `save_stock_reports()` (파일 저장)

### 🔴 리포트는 Discord 전송용 포맷으로 생성
- `report.py`가 Phase 1 (Midpoint Filter 표) + Phase 2 (종목별 Bull/Bear/Risk + 결정 근거) 통합 리포트 생성
- Discord `#주식-증시` 채널에 전송
- 포맷: 마크다운 + 이모지 (`🟢 BUY` / `🔴 SELL` / `⚪ HOLD`), 종목별 📌 밸류에이션 + 📈 Bull + 📉 Bear + ⚠️ Risk + 💡 결정 근거
- 저장: `logs/decisions/full_report_*.md`

### 🔴 Finnhub API Key 검증 (신규 등록 시)
```
# Profile 확인
curl -s "https://finnhub.io/api/v1/stock/profile2?symbol=AAPL&token=YOUR_KEY"
# News 확인 (7일 window)
curl -s "https://finnhub.io/api/v1/company-news?symbol=NVDA&from=2026-05-30&to=2026-06-06&token=YOUR_KEY"
```
무료 티어: 일 300회 (16종목 × 뉴스 1회 + Insider 주 2회 + SEC Filing 주 1회 = 약 23회 — 넉넉함)

### 🟡 기존 스크립트 이름 변경 시 주의
- `fair_value_v3.py` → `fair_value.py` 로 이름 변경 시 **심볼릭 링크** 생성 필요 (`fair_value_v3.py` → `fair_value.py`)
- 이유: 기존 cron이 `fair_value_v3.py`를 참조할 수 있음. cron이 깨지지 않도록 링크 유지

## 📎 참고 파일

- `references/paper-code-verification.md` — 논문 코드 구현 검증 가이드 (TradingAgents 사례)
- `references/deepseek-api-implementation.md` — **DeepSeek V3/R1 API 호출 구현 패턴 (+ httpx, cost tracking, response parsing, Finnhub key 검증)**
- `references/discord-report-delivery.md` — **Discord 리포트 전송: 채널 지정, 2000자 분할, 포맷 규칙, 문제 대응**
- `references/finnhub-news-collection.md` — **Finnhub 뉴스 수집 + 매크로 컨텍스트 + 향상된 프롬프트 템플릿 (Phase 0.5)**
|- `references/pipeline-cron-workflow.md` — **등록된 크론 전체 일정, Clean up, 파이프라인 실행 상세, 종목별 리포트 분할 전송**
|- `references/rss-feed-patterns.md` — **Google News RSS 검색 URL 패턴 (매크로 리포트 데이터 수집용, 투자 카테고리별)**
|- `references/forward-testing-wiki.md` — **Forward Testing 프레임워크 요약 (비중 산식, 평가 기준)**
|- `references/trade-pipeline-migration.md` — **Trade-Pipeline 마이그레이션 경로 (구 trading-agents-nuri → ~/trade-pipeline/)**
|- `references/data-visualization-preferences.md` — **matplotlib 차트 스타일: 다크 테마, 한글 폰트(WenQuanYi Zen Hei), 대형 폰트, 분할 전송 규칙**

---
- **비용은 추정하지 말고 실제 토큰 로깅으로 축적할 것**
- **Bull/Bear Debate 없이 단순 Context→Decision이면 LangGraph 불필요**
- **한국주는 Finnhub/SEC EDGAR 미지원 — 네이버 증권 의존**
- **Prompt에 "PER75:PBR25" 명시하지 않으면 LLM이 다른 기준으로 판단함**
- **Hypothesis Store 없이 LLM 결정만 내리면 나중에 복기 불가능**
- **아키텍처 다이어그램은 markdown 텍스트 하나로만 표현할 것** — 깔끔한 텍스트 박스(━━ 라인, ①~⑨ 번호) 사용. 별도 HTML/SVG 파일 금지. 사용자가 "왜 만듬"이라고 함.
- **Discord 리포트 전송 전 채널 목록 반드시 확인** (`send_message(action="list")`). 채널 ID 추측 금지. 사용자가 "안오는데?"라고 하면 바로 잘못된 채널로 보낸 것.
- **리포트 2000자 초과 시 종목별로 분할 전송** — 각 메시지 1800자 안전 임계치 유지, rate limit 방지 위해 0.5초 간격.
- **사용자는 요약보다 모든 상세 데이터를 원함** — Bull/Bear/Risk 분석 전부 포함.
