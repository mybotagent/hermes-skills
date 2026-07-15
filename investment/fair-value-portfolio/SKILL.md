---
name: fair-value-portfolio
description: 적정 PER 기반 포트폴리오 밸류에이션 분석 + 글로벌 시장 뉴스 통합 일일 리포트
---

# Fair Value Portfolio Analysis (적정 PER 기반 방법론)

> **핵심 철학**: "기업이 실제로 얼마나 버는지(EPS+ROE)와 자본을 얼마나 효율적으로 쓰는지(PBR)" — 가치투자 원칙 기반.
> 모든 상세 지식은 `~/.hermes/wiki/analysis/orbit-valuation.md`에 구조화되어 있음.

## 🧠 사용자 선호 (반드시 준수)

### 포트폴리오 비중 = t1_gap × Moat 점수 곱셈식 (2026-06-08 v2)
- 사용자: "Gap과 해자만 활용" → "LLM이 추정하기"
- **규칙**: `가중값 = max(0, t1_gap) × moat_점수` → `기본_비중 = (가중값 / 총_가중값) × (100% - 현금비중)`
- **Moat 점수는 LLM이 종목 데이터로 1~10 추정**: 해자 요소(특허·독점, 네트워크효과, 전환비용, 브랜드파워, 규제장벽) 기준
  - 9~10: 독점적 지위 (NVDA, MSFT, GOOGL)
  - 7~8: 강한 시장지위
  - 5~6: 차별화 보통
  - 3~4: 차별화 약함
  - 1~2: 진입장벽 없음
- **오직 gap + moat 두 가지 요소만 사용** — PER상태/성장성/현금흐름 등 다른 요소 반영 금지
- **SELL 판정 종목**: 비중 = 2% (계산에서 제외)
- **상한 15%, 하한 2%** — **무조건 고정 후 재분배**, 15% 초과 절대 불가
- Analyst Target과의 평균(midpoint) 사용 금지 — 순수 Model T1 적정가만 사용
- 구현: `src/agents/portfolio_allocation.py` PROMPT 규칙 2번 (수식 + moat 추정 루브릭 포함)
- **변경 이력**: midpoint_gap(T1+Target) → t1_gap 단독 → **t1_gap × moat (LLM 추정)** (2026-06-08 v2)
- **📌 근거(reason) 필드는 반드시 시장해석 기반으로 — 순수 계산식 금지 (2026-06-16 교정)**
  - COLUMN 근거에는 `gap XX% × moat Y/10` 수치를 포함하되, **매크로·뉴스 맥락 1문장을 반드시 추가**할 것
  - 포트폴리오 프롬프트(prompt line 77)에서 reason 템플릿을 `"시장해석 기반 근거 (gap XX% × moat Y/10) — 뉴스/매크로 맥락 1문장"`으로 강제
  - 사용자 교정: "근거가 시장해석과 다름" → 순수 gap×moat 계산식만 출력해서 시장 맥락이 반영 안 됨
  - 출력 시 reason truncation 60자 (기존 40자→60자로 확대) — 35→55자 칸 너비

### 리포트 출력 형식 (2026-06-08 전환)
- 리포트는 **T1 괴리율(t1_gap) 30%↑ 상위 10종목**만 간단한 표로 출력.
- **T1 괴리율(t1_gap) 단독 사용** — Analyst Target 혼합 금지 (2026-06-08 교정).
- Analyst Target이 30일 내 없는 종목은 Model T1 단독값 유지 (별도 처리 불필요).
- 출력 컬럼: 순위·종목·현재가·Model T1·Analyst Target·T1괴리율.

### 리포트 종목 간 간격 (2026-06-06 교정)
- **종목 사이에 반드시 2줄 간격(빈 줄 2개)** 을 둘 것.
- 사용자: "종목사이에 두줄 띄워쓰기 해줘 왜 붙어서 오는지 모르겠네"
- 구현: `report.py generate_report()`에서 각 stock_report 뒤에 `lines.append("")`를 **2회** 호출.
- 마크다운에서 빈 줄 1개는 시각적 간격이 거의 없으므로 반드시 2개여야 Discord에서 가독성 확보.

### 주말 크론 OFF (2026-06-06 확정)
- **모든 크론은 주말(토/일)에 실행하지 않는다** — 사용자: "주말에는 크론 안돌게 하자"
- 월~금(평일)만 실행: `1-5` 사용 (cron 표현식 `* * * * 1-5`)
- 예외 없음. 주말에 AI 분석/리포트가 필요해도 크론으로 보내지 말고 사용자에게 수동 요청.
- 해당 크론: 04:00 Wiki, 08:00 Calendar, 08:10 Portfolio, 18:00 US, 18:30 Macro, 18:35 Pipeline
- 이미 `1-5`가 아닌 크론: 주간계획(월 only), 월간전략(1일 only) — 수정 불필요.

### 데이터 Clean up 규칙 (2026-06-06 철회)
- **별도 cleanup 크론 없음.** 중간 데이터(`data/*.txt`, `data/*.json`)는 다음날 08:10/18:00 크론이 덮어쓰므로 삭제 불필요.
- `logs/decisions/stocks/`의 종목별 리포트는 **히스토리로 보존** (삭제 금지).
- 사용자가 cleanup 크론 등록을 질문했으나 철회함. 사용자: "랭그래프 상세 분석 리포트 지우면 안되는 거 아님?"

### 사용자 탐색 패턴 (2026-06-08)
- **반복/실험적 탐색** 선호. 한 번에 완벽한 답 금지.
- 패턴: 빠르게 결과 보여주기 → 피드백 받기 → 조건 변경.
- "analyst만" → "T1만" → "중간값" → "30%↑" → "Analyst-T1 갭 작은 것만" → **t1_gap 단독** 식으로 진화.
- "필터링 하자" / "하지 말자" 같은 지시가 여러 번 오면, 최종 방향 확인 후 고정.
- 2026-06-08 최종: midpoint_gap 폐기, **t1_gap 단독 사용** 확정.
### 문서화 선호 (2026-06-06)

- **아키텍처 다이어그램은 Markdown 텍스트 전용**: 별도 HTML/SVG 파일 금지.
- 한국주 데이터는 실제 코드 기반으로 작성: `fair_value.py` 110~120줄 네이버 스크래핑, `analyst_target_collector.py` 85~109줄 네이버 컨센서스 확인 후 기재. "취약하다" 같은 주관적 표현 금지.
- 크론 시간은 **cron식 포함** 분 단위 정밀도. "08:00"이 아니라 "`10 8 * * 1-5`".
- 실행 타임라인: "18:00 통합 크론 Step 1(스크립트) → Step 2(매크로) → Step 3(pipeline)". 모든 Phase는 pipeline.py 하나로 처리.
- **모든 코드는 단일 GitHub 레포**: `mybotagent/trade-pipeline`. **symlink 금지 (2026-06-07 교정)** — `~/.hermes/scripts/`는 cron wrapper `.sh`만 보관. Python 스크립트는 스킬 프롬프트에서 `~/trade-pipeline/langgraph/src/...` 절대경로로 직접 호출.



2. **적정PER 내 투자 우선**: PER이 적정 범위를 벗어난 종목(고PER)은 모멘텀이 아무리 좋아도 리스크 명시 필수.

3. **PBR 절대 제거 금지 (2026-06-03 재확인)**: PBR은 ROE와 함께 자본 효율성을 측정하는 핵심. BPS x ROE/9 공식 유지.

4. **ROE는 기업의 실제 수익력의 핵심 (2026-06-03)**: ROE가 높은 기업은 그만한 자본 수익성을 가진 것. ROE 상한(캡) 두지 않음. ROE는 PER part(rp)와 PBR part(ROE/9) 양쪽에서 자연 반영.

5. **Analyst target에 강제로 끼워맞추지 말 것 (2026-06-03)**: 모델은 EPS·ROE·BPS라는 hard data 기반 고유 시각을 가짐. NVDA $372 vs Needham $270은 모델 고유 판단으로 인정. Analyst target과 차이는 모델의 보수적/낙관적 편향으로 해석.

6. **최신 개별 analyst target 사용, stale consensus 평균 금지 (2026-06-03 교정)**: yfinance `targetMeanPrice`는 consensus 평균으로 weeks~months stale. US는 `stock.upgrades_downgrades.iloc[0]`의 최신 target 사용. KR은 너구리 제공 target 사용. **(참조: `references/latest-analyst-targets.md`)**.

7. **모든 종목 동일 공식 — 예외 처리 최소화 (2026-06-03)**: 종목별/업종별 하드코딩 금지. 특성 기반 조건(FPE<12 같은)만 허용. TICKER_SECTOR 같은 매핑은 yfinance의 부정확한 sector 분류를 보정하는 것이므로 예외가 아닌 데이터 보정.

7b. **비현실적 괴리율 → TICKER_SECTOR 우선, 추가 cap 금지 (2026-06-11 교정)**: 괴리율이 비현실적으로 크면 FPE 사이클 cap 같은 조건문을 추가하기 전에 **TICKER_SECTOR 재분류**부터 확인할 것. HPE 사례: yfinance `Technology(base 22)` → 적정가 $112(+125%) → `Hardware(base 18)`로 재분류만으로 $100(+108%)로 적정화. 사용자가 FPE 12.0 기준 사이클 cap 조건문은 거절("no"). 원칙: 데이터 보정 우선, 조건문 추가는 최후 수단. 기존 cap(FPE<12→US 20/KR 11)으로 충분.

8. **"기업이 실제로 얼마나 버는지"만 고려 (2026-06-03)**: 브랜드, 모멘텀, 생태계 등 정성적 요소는 모델에서 제외. EPS(수익력) + ROE(자본효율성)가 전부.

9. **Analyst 추정 불신**: yfinance forwardPE/targetPrice는 analyst 컨센서스 기반 — 평균 25~35% 과대 낙관 가능. 리포트 인용 시 출처 명시.

10. **Forward EPS 기준**: 1년 적정가는 반드시 Forward EPS (Price / FPER). Trailing EPS 사용 금지.

11. **현금 불가산**: 순현금 per share 적정가에 불가산. 순수 PER/PBR 배수 기반.

12. **Wiki-First 지식 관리**: 설정/스크립트 질문은 `~/.hermes/wiki/` 확인.

## 개요
섹터별 적정 PER과 PBR 밴드를 결합한 Orbit 방법론으로 22개 관심 종목 평가.
PER 밴드 + PBR 밴드 내 주가 위치 추적 → 현재 적정가(T0)와 1년 후 적정가(T1) 괴리율 산출.

- 출처 명시 강제
- **API 키는 절대 코드에 저장 금지**: `.env` → `.gitignore` → `python-dotenv` → `os.getenv()`
- **리포트는 Discord 전송용 포맷**: Midpoint Filter 표 + 종목별 Bull/Bear/Risk + 결정 근거 통합

## 🔍 Finviz Screener — 신규 종목 발굴 (2026-06-23 신규)

Finviz 기반 가속 성장주 스크리너. watchlist 외부 신규 후보 발굴 용도.
적정가 계산은 포함하지 않음 — 기존 `fair_value.py` 수정 금지.

### 실행
```bash
cd ~/trade-pipeline && python3 scripts/finviz_screener.py
```

### 필터 조건
| 조건 | 값 |
|:----|:---|
| P/E | Under 50 |
| ROE | Over +15% |
| D/E | Under 1 |
| EPS growththis year | Over 15% |
| EPS growthnext year | Over 15% |
| Market Cap | +Mid (over $2bln) |

### 가속 조건
- **FPE < PE**: Forward P/E가 Trailing보다 낮아야 함
- 보너스: `FPE < PE/2` → 초강세 후보

### 정렬 기준
- **가속도 = EPS Next Y(%) - EPS This Y(%)**
- 양수 = 내년 성장이 올해보다 가속
- 내림차순 정렬, 상위 30 출력

### 편입/퇴출 규칙
- **편입**: 사용자(너구리) 승인 필요만
- **퇴출**: gap_T1 < -50% 자동 제거 (watchlist)
- 적정가는 기존 fair_value.py 그대로 (수정 금지)

### 주의
- ROE Financial screener 소수 반환(0.21→21%) → median<5면 ×100
- Finviz 무료 rate limit 있음
- 한국주 미커버

**참조**: `references/finviz-screener.md`

## 📚 방법론 발전 (Evolution)

### Phase 1: Orbit PER/PBR Band (원본, deprecated)
- PER 배수 밴드 + 궤적 추정 → Orbit 적정가
- **순환논리 함정 발견 (by user)**: Target_PER = (PE/FPE-1) × 100 × 1.2
  - 이미 비싼 주식(PER 높음) × 실적 급증(FPER 낮음) → Growth_Rate 폭발 → Target_PER 35 → "매수"
  - 합리적 가격 주식(PER 적정) × 안정 성장 → Growth_Rate 10~15% → Target_PER 15~18 → "매도"

### Phase 2: 적정 PER 기반 (sector-based, 2026-05-31)
- 섹터 기준 PER 베이스 + 성장률 프리미엄 + 부채 디스카운트 + ROE 프리미엄
- 순수 PER만, PBR 미반영. Trailing EPS 사용 (틀림).

### Phase 3: Orbit v2 — PER+PBR 혼합 (2026-06-02 오전)
- Phase 2 섹터 PER + Orbit PER&PBR 밴드 결합. Forward EPS 사용.
- 동적 W_Growth 시도했다가 **고정 혼합비**로 전환.

### Phase 4: 고정 혼합비 75:25 (2026-06-02 저녁)
- `W_PER = 0.75 (PER75%:PBR25%)` — 고정, 예외 없음
- EPS 하드코딩 캡 금지 (너구리 교정). raw forward EPS 사용.
- 네이버 PBR 수집. yfinance analyst mean staleness 발견.
- **참조**: `references/orbit-original-code.md`

### Phase 5: US/KR 분리 사이클 cap + 업종 세분화 (2026-06-03, 현행 ✅)
- **US 메모리**: `FPE < 12 AND PE/FPE > 3.0` → fair_pe 상한 **20**
- **KR 메모리**: `FPE < 12 AND market='KR'` → fair_pe 상한 **11**
- BPS 유보이익 방식: `FPE < 12` → `bps_t1 = bps_t0 + eps_t1 × 0.7`
- ROE 상한 제거
- **업종 세분화** (TICKER_SECTOR 매핑)
- **Analyst Target 자동수집**: `upgrades_downgrades` 30일 window 최신 target
- 최종 정확도: **23.1%** 평균 절대 오차

### Phase 6: Multi-Agent LLM Layer — V4 프롬프트 + 시장 해석 연동 ✅ (2026-06-06)

### Phase 6.1: V4.5 — Truncation 제거 → LLM 요약으로 전환 (2026-06-08 v2)

**핵심 사용자 선호 — 반드시 준수:**

1. **절대 하드 Truncation 금지**: `bull[:200]`, `bear[:200]` 같은 문자수 슬라이싱 금지. 대신 LLM으로 3~5줄 요약 후 전달. (portfolio_allocation.py `summarize_stock()` 함수)
2. **Phase 3 포트폴리오 비중**: `build_stock_summary()`가 raw text 대신 LLM 요약을 Phase 3 프롬프트에 전달
3. **Phase 2 리포트/종목별 전송**은 여전히 전문(full text) 저장 및 Discord 전송

3. **종목 간 2줄 간격**: 각 종목 리포트 사이에 반드시 빈 줄 2개를 넣을 것. 사용자: "종목사이에 두줄 띄워쓰기 해줘 왜 붙어서 오는지 모르겠네"

4. **시장 해석(Interpretation) 필수**: 단순 수치 나열 금지. Key Driver/Regime/Impact를 Bull/Bear/Risk/Decision에 인용해야 한다. 사용자: "매크로 리포트도 단순 수치가 아니라 시장 해석을 보내주도록"

5. **정량적 수치 인용 강제**: 모든 Agent(Context/Bull/Bear/Risk)는 `{current_pe} vs {fair_pe} = X% 차이` 같은 구체적 %를 포함해야 한다. "고평가됨" 금지 — "현재 PER 28.5는 적정 22.0 대비 29.5% 고평가"

**per-stock delivery 구현 (report.py v4):**
```python
# report.py 핵심 함수
generate_stock_report(r, idx)  → 1개 종목 전체 리포트 (truncation 없음)
generate_stock_sections(results) → 종목별 분할 리스트
save_stock_reports(results, dir) → 개별 .md 파일 저장

# pipeline.py 호출
from src.report import save_stock_reports
stock_dir = os.path.join(LOGS_DIR, "stocks")
stock_paths = save_stock_reports(p2["results"], p2["cost"], stock_dir)
# 이후 Hermes Agent가 각 파일 읽어 send_message로 개별 전송
```

TradingAgents 논문([arXiv:2412.20138](https://arxiv.org/abs/2412.20138)) 기반 멀티 에이전트 의사결정 레이어.\n**⚠️ 기존 시스템(fair_value/cron)을 변경하지 않는다 — 출력물만 읽어서 추가 분석.**

**V4 업데이트 (2026-06-06):** Context/Bull/Bear/Risk/Decision 프롬프트에 **시장 해석(market_interpretation)** 포함
- 18:00 통합 크론의 `market_interpretation.key_driver`, `market_interpretation.regime`, `market_interpretation.impact_analysis`가 각 Agent에 전달됨
- Context agent: 6문장 (기존 5문장 → 시장 해석 인용 추가)
- Bull/Bear agent: "매크로/시장 해석 중 Bull/Bear 관점을 지지하는 요소 인용 — Regime(국면), Key Driver"
- Risk agent: "시장 해석(Key Driver/Regime)과 매크로 지표의 특정 수치를 인용하여 영향 평가"
- Decision agent: Rationale 4문장 (기존 3문장 → 시장 해석 근거 1문장 추가)

**최종 아키텍처: LangGraph StateGraph, 논문과 동일한 3가지 패턴**
```
① Structured Report (State) — AgentState TypedDict
② Natural Language Debate — Bull+Bear+Risk가 State 읽고 의견 작성
③ Single StateGraph — add_node/add_edge로 Fork-Join 제어

Context(V3) → Bull(V3)∥Bear(V3)∥Risk(V3) → Facilitator(R1)
               ↑ 3-way parallel fork          ↑ join
```

| Agent | 역할 | 모델 | 설명 |
|:------|:----|:----|:------|
| Context | Analyst Report | V4 | fair_value + 뉴스 + 매크로 수치 + **시장 해석(Key Driver/Regime)** | 6문장 |
| Bull | 매수 측면 | V4 | "PER75:PBR25 기준 살 이유 3가지" + **시장 해석 인용** |
| Bear | 매도/회피 측면 | V4 | "PER75:PBR25 기준 사면 안 되는 이유 3가지" + **시장 해석 인용** |
| Risk | 리스크 평가 | V4 | 포지션/변동성/정보 불확실성 + **시장 해석(Key Driver/Regime) 인용** |
| Facilitator | 최종 결정 | R1 | 3개 의견 종합 → PER75:PBR25로 BUY/SELL/HOLD. Rationale 4문장 (PER 수치 + 중간값 괴리율 + 시장 해석 근거 + 매크로/뉴스 근거) |

**데이터 소스 구분**:
| 항목 | 미국주 (16종목) | 한국주 (6종목) |
|:----|:-------------:|:-------------:|
| 주가/재무 | yfinance (15~20분 지연) | **네이버 증권 홈페이지** |
| Analyst Target | Finnhub/cron (30일 window) | **네이버 컨센서스 스크래핑** (coinfo.naver, analyst 의견만) |
| 뉴스 | **Finnhub** (실시간) | **네이버 뉴스** (cron+Hermes Agent) |
| Insider | Finnhub | 해당 없음 |
| SEC Filing | sec-edgar-mcp | 해당 없음 |
| 거시경제 | **cron 08:00/18:00 브리핑** | **cron 08:00 브리핑** |
| **매크로 전략** (CPI·Fed·WTI·지정학) | **cron 18:30 + Phase 0.5** (공통, 전 종목) — `macro_context.json`에 시장 해석 + FRED 데이터 포함 저장 | **cron 18:30 + Phase 0.5** (공통, 전 종목) |
| **FRED 거시경제** (CPI, Sahm, Fed Rate, HY, M2) | **Phase 0.5** → `fetch_macro_strategy()` → Hermes venv로 `macro_strategy_report.py` 실행 → `macro_context.json["macro_strategy"]` | **Phase 0.5** 동일 |
| **시장 해석** (Key Driver/Regime/Impact) | **cron 18:00 통합** → `market_interpretation` 필드 → Bull/Bear/Risk/Decision에 직접 인용 | **cron 18:00 통합** 동일 |
| **Fear & Greed Index** (CNN) | **cron 08:10 오전 브리핑** — `fear_greed.py --report` → 리포트 상단 | **cron 08:10 오전 브리핑** — US 센티먼트 지표로만 사용 **(참조: `references/fear-greed-index.md`)** |

**비용 (추정치)**: V3 4회(~8원) + R1 1회(~4원) = **~12원/Trigger, 월 8회 ~96원** (예산 30,000원의 0.32%)
> 정확한 비용은 실행 후 Cost Monitor 측정 필요.

**LangGraph GitHub**: [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) (langgraph>=0.4.8)  
**우리 GitHub**: [mybotagent/trade-pipeline](https://github.com/mybotagent/trade-pipeline)

---

## ⚠️ 함정 및 주의사항 (Pitfalls)

### 1. 🟡 기존 시스템 변경 금지 (2026-06-06)
- 신규 Agent Layer는 **기존 cron/fair_value를 절대 변경하지 않는다**
- 기존 시스템의 **출력물(JSON, 텍스트)만 읽어서** 추가 분석
- "기존 방식을 변경하면 안 되는 거야? 기존 방식 + 추가되는 파이프라인" — 사용자 교정

### 2. 🔴 Forward EPS 과대낙관
- FPER 6~10 → Forward EPS 3~7배 → T1 폭발
- **대응**: 사이클 cap 20/11 + BPS 유보이익

### 3. 🔴 PBR 데이터 오류 / 결측
- STX PBR 440: BPS $2 수준으로 자연 감쇠
- 한국주: 네이버 스크래핑 → 실패 시 EPS_T0 × 5

### 4. 🔴 ROE 극단값 (상한 없음)
- STX ROE 1788% → BPS $2 + PBR 25% weight → 자연 감쇠
- SK하이닉스 ROE 61% → BPS × (61/9) = 정당

### 5. ⚠️ 순수 PER만 사용 금지

### 6. 🔴 최신 개별 analyst target vs stale consensus (중요)
- `targetMeanPrice`는 **절대 단독 사용 금지** (stale)
- `upgrades_downgrades`에서 **30일 최신 target** 확인
- KR: upgrades_downgrades 미지원 → **네이버 컨센서스 스크래핑** (`finance.naver.com/item/coinfo.naver`) — analyst 의견만 사용, 개인 의견/하드코딩 금지

### 7. 🔴 논문 분석 시: GitHub 코드를 먼저 확인할 것 (2026-06-06 교정)
- TradingAgents 논문 본문은 LangGraph를 언급하지 않지만, 실제 코드는 `langgraph>=0.4.8` 사용
- 학술 논문은 **방법론(methodology)**만 설명하고 구현 디테일은 GitHub에 담는 것이 관행
- `llm.call()` 같은 코드는 LangChain/LangGraph의 `invoke()`일 가능성 높음

### 8. 🔴 데이터 소스 정책 (2026-06-06 확정)
- **유료 데이터 API (Bloomberg, Reuters 등) 절대 사용 금지**
- **SNS/Reddit/X/포럼 데이터 절대 사용 금지**
- **한국주는 네이버가 유일**: 한국주 데이터는 **네이버 증권 홈페이지**(주가/PER/PBR) + **네이버 뉴스**(cron+Hermes Agent) + **네이버 컨센서스**(analyst target, coinfo.naver 스크래핑). yfinance 사용 자제.
- **미국주는 yfinance + Finnhub**: yfinance(15~20분 지연 인지), Finnhub(무료 티어 일 300회, 미국주 전용)
- **SEC EDGAR**: `sec-edgar-mcp` MCP 서버 (무료 공시, 미국주 해당)
- **거시경제**: 기존 cron 08:00/18:00 브리핑 Context에 포함

### 9. 🔴 멀티 에이전트 아키텍처 설계 원칙 (2026-06-06 v3 최종)
- **단순할수록 좋다**: Bull/Bear/Risk 3명 1라운드면 충분. 논문처럼 n rounds+Facilitator+Risk 3명 Debate은 오버엔지니어링.
- **LangGraph는 필요할 때만**: Bull∥Bear∥Risk Fork-Join + 조건부 분기에만 사용. 순차 로직은 Python.
- **LangGraph 부정하지 말 것**: 사용자가 LangGraph를 원하면 쓰는 방향으로 설계할 것. "필요 없다"고 단정하지 말고 "어디에 쓰면 좋을까"로 접근.
- **비용은 추정치임을 명시**: DeepSeek 가격표 기준 추정. 실제 비용은 실행 후 Cost Monitor 측정 필요.

### 10. 🔴 비용 추정은 실제 토큰 카운팅 기반으로 해야 함
- 추정 Input/Output 토큰 수는 실제와 다를 수 있음
- 실행마다 실제 input_tokens, output_tokens 기록 필요
- 모든 비용 표시는 "추정치" 표기 필수

### 11. 🔴 yfinance 데이터 지연
- yfinance는 **실시간이 아니다**. 모든 가격 데이터는 15~20분 지연.
- 가치투자(월 2~4회 거래)에게는 영향 없지만, Freshness Check 기준은 30분으로 조정 필요.
- 한국주는 yfinance보다 **네이버 증권 홈페이지**가 더 정확할 수 있음.

**크론 출력물 재활용 — 저장된 stdout 파일만 읽기, subprocess 재실행 금지 (2026-06-07 간소화)
`fair_value.py`와 `analyst_target_collector.py`는 **print()로만 출력하고 파일을 저장하지 않는다.**
- **초기 해결**: subprocess로 재실행 → stdout 파싱 → JSON 저장 (capture_and_save.py v1)
- **❌ 사용자 교정**: "새로 만들지 말고 기존 크론에서 저장하게 해"
- **✅ 최종 해결**: 기존 Hermes cron 프롬프트에 **파일 저장 단계 추가**:
  ```
  # 크론 프롬프트 내부 (Discord 출력 전 실행)
  ./hermes-agent/venv/bin/python3 scripts/fair_value_v3.py > /path/to/data/fair_value_stdout.txt
  ./hermes-agent/venv/bin/python3 scripts/analyst_target_collector.py > /path/to/data/analyst_stdout.txt
  ```
- Phase 0은 pipeline.py에 인라인으로 직접 구현됨 (`read_fair_value_stdout()` + `read_analyst_stdout()`) — 별도 capture_and_save.py 스크립트 아님
- **midpoint_filter.py도 pipeline.py에 인라인 통합** — 별도 스크립트 아님 (이전의 `/root/` 하드코딩 + `captured_snapshot.json` 버그 해결)
- 18:00 통합 크론(LLM)이 리포트 전문을 `macro_context.json`에 저장 → pipeline.py가 직접 읽음
- **macro_context.json 구조 (v3) — 시장 해석 포함**:
  ```json
  {
    "macro_report_summary": "리포트 전문 (∼3000자)",
    "key_macro_data": {"fed_rate": "4.25~4.50%", "dxy": "104.2", ...},
    "market_interpretation": {
      "key_driver": "트리플 악재",
      "market_sentiment": "risk-off",
      "regime": "Overheat",
      "impact_analysis": "종목군별 인과관계 설명"
    },
    "news_items": [...]
  }
  ```
- **❗ 'macro_context.txt'로 저장하지 말 것**: 반드시 JSON 형식(`macro_context.json`)으로 저장. 이유: `collect_macro_context.py`가 Finnhub 뉴스를 추가할 때 JSON 읽기/쓰기가 편리함. txt 파일을 따로 만들면 두 파일 간 동기화 문제 발생.
- **시장 해석 필수 세 필드**: `market_interpretation.key_driver`, `market_interpretation.regime`, `market_interpretation.impact_analysis`를 18:00 통합 크론이 반드시 포함해야 함. 이 필드들이 LangGraph Bull/Bear/Decision에 직접 인용되어 디베이트의 정량적 근거로 사용됨. 단순 수치 나열 금지.
- **일간 저장/폐기 규칙**: `data/` 디렉토리에 하루치만 보관. 다음날 08:10/18:00 통합 크론이 새 데이터로 덮어씀.

### 14. 🔴 크론 시간 충돌: 08:00 중복 등록 금지 (2026-06-06 교정)
- **08:00**에 📅 구글 캘린더와 📊 포트폴리오가 동시 등록되어 충돌
- 해결: 포트폴리오를 **08:10**(`10 8 * * 1-5`)으로 지연
- 새 크론 등록 시 반드시 `cronjob action=list`로 기존 시간표 확인 후 중복 회피

### 16. 🔴 설계 먼저, 구현은 나중에 — 절대 급하게 만들지 말 것 (2026-06-06 신규)
- 사용자 교정 (여러 번): "급하게 만들지 말라고", "우선 구현을 위한 설계 부터해"
- **올바른 순서**: 설계 문서 작성 → 사용자 검토 → 승인 후 구현
- 잘못된 예: forward testing system을 사용자 요청 받자마자 바로 코드+크론+위키까지 만들어버림
- 올바른 예: "이런 설계 어떤가요?" → 사용자 피드백 → 수정 → 승인 → 구현
- **코드 한 줄도 먼저 만들지 말 것.** 설계 문서를 사용자에게 먼저 보여주고 승인받아야 함.

### 17. 🔴 기존 구현 활용 — 새로 만들기 전에 이미 있는 것부터 확인 (2026-06-06 신규)
- 사용자 교정: "기존에 구현한거장ㅎ아" (이미 구현된 게 있는데 왜 새로 만드냐)
- 새 기능을 추가하기 전에 **logs/decisions/*.json**, **pipeline.py 출력물**, **기존 크론 출력** 등 이미 저장되는 데이터를 먼저 확인할 것.
- 파이프라인은 이미 `timestamp`, `results[].decision`, `results[].confidence`, `cost_summary` 등 forward testing에 필요한 모든 데이터를 JSON으로 저장하고 있음.
- "새로 만들어야겠다"는 생각이 들면 **일단 stop**. 이미 저장되는 데이터로 해결 가능한지 먼저 검토.
- **금지**: 파이프라인/POC가 잘 도는 것만 확인하고 바로 cron 등록
- **사용자 교정**: "cron 등록 우선 하지말고" — 등록하기 전에 먼저 수동 테스트로 전체 흐름 검증
- **올바른 순서**:
  1. 구현 → 수동 테스트 (`venv/bin/python3 pipeline.py --phase 0`)
  2. 각 phase 독립 실행 검증
  3. 데이터 파일 저장 확인
  4. **사용자 승인 후** cron 등록
- 각 Phase는 독립 실행 가능해야 함 (`pipeline.py --phase 0/05/1/2`)
- 데이터는 파일 체인으로 전달: `fair_value_stdout.txt` → `daily_snapshot.json` → `filtered_top10.json` → LangGraph
- 중복 실행 금지: 18:00 크론이 stdout 저장하면 pipeline은 재실행하지 않고 읽기만

### 18. 🔴 한국 주식 데이터 수집: Naver는 analyst_target_collector 전용 (2026-06-07 교정)
- 사용자: "한국 주식은 네이버 증권에서 스크랩하기로 했음" → **단, Naver 스크래핑은 analyst_target_collector에서만 수행**
- **decision_validator.py는 Naver API 사용 금지** — yfinance만 사용 (validator는 단순 가격 비교, Analyst target 불필요)
- `analyst_target_collector.py`: Naver `coinfo.naver?code=005930` 페이지 스크래핑
  - Referer 헤더 필수: `headers={"Referer": "https://finance.naver.com/"}` (안 보내면 빈 응답)
  - 삼성전자 컨센서스 예: `get_kr_naver_consensus("005930")` → ₩426,250
- 참조: `references/korean-stock-data.md`

### 20. 🔴 하나의 GitHub 레포로 통합 — symlink 금지 (2026-06-07 교정, 2026-06-07 symlink 금지 추가)
- 사용자: "모든 코드를 한 레포로 통합" + "새 레포로 이전" + "심볼릭 링크 걸지 말고 새레포에서 모두 처리해"
**통합 GitHub**: [mybotagent/trade-pipeline](https://github.com/mybotagent/trade-pipeline) → `~/trade-pipeline/`  
**Python 모듈**: `langgraph/src/` 서브디렉토리  
**경로 주의**: `langgraph/` 서브디렉토리 때문에 `os.path.dirname` 계산이 depth=3~4로 깊음 — `langgraph/src/` 안의 파일은 두 단계(`..`, `..`) 올라가야 `~/trade-pipeline/`에 도달.

| 구분 | 이전 (삭제됨) | 현재 |
|:----|:-------------|:-----|
| 레포 | `trading-agents-nuri`, `trading-agents-nuri-cron`, `trading-agents-nuri-langgraph`, `trading-agents-nuri-scripts`, `trading-agents-nuri-feedback`, `portfolio-feedback`, `hermes-wiki-portfolio` (전부 ARCHIVED + GitHub 삭제 완료) | `mybotagent/trade-pipeline` (유일) |
| 경로 | `~/trading-agents-nuri/` | `~/trade-pipeline/` |
| 심볼릭 링크 | `~/.hermes/scripts/fair_value.py` → symlink | 없음 — cron prompt가 `~/trade-pipeline/langgraph/src/` 직접 호출 |
| 크론 스크립트 | no_agent script 크론 | LLM prompt 크론 (terminal 명령어로 직접 실행) |
**매 세션 종료 시 git push 필수**: `cd ~/trade-pipeline && git add -A && git commit -m "요약" && git push`
- **구조**: `pipeline.py` + `src/fair_value.py` + `src/analyst_target_collector.py` + `src/agents/*.py` + `src/*.py` = 한 레포
- **예외**: `trading-agents-nuri-feedback`(피드백 저장소)는 별도 유지 — 월간 리뷰 산출물 저장용이므로 분리
- **symlink 금지**: `~/.hermes/scripts/`의 심볼릭 링크 제거. 08:10/18:00 스킬 크론은 프롬프트에서 `~/trade-pipeline/langgraph/src/` 절대경로 직접 호출.
  ```diff
  - ~/.hermes/scripts/fair_value.py → symlink
  + 08:10 스킬 프롬프트: `cd ~/trade-pipeline && python3 langgraph/src/fair_value.py > data/fair_value_stdout.txt`
  ```
- **cron wrapper 없음**: `~/.hermes/scripts/` 완전히 비움 (2026-06-07). no_agent script 크론 3개를 LLM prompt로 전환.
- **크론 실행 방식**: 모든 파이프라인/검증/전략 크론은 LLM prompt로 실행되며, prompt에 `cd ~/trade-pipeline && python3 langgraph/pipeline.py`가 포함됨.
- **중요**: 새 코드를 추가할 때도 반드시 이 단일 레포 내에 추가. 별도 레포/scripts 디렉토리 생성 금지.
- 구 레포(trading-agents-nuri, portfolio-feedback, hermes-wiki-portfolio 등 7개)는 **전부 GitHub ARCHIVED + 로컬 삭제 완료** (2026-06-07).

symlink 제거 작업 순서 (2026-06-07 시점 완료 ✅):
1. `~/.hermes/scripts/fair_value.py` → symlink 제거 (파일 삭제)
2. `~/.hermes/scripts/fair_value_v3.py` → symlink 제거
3. `~/.hermes/scripts/analyst_target_collector.py` → symlink 제거
4. 08:10 스킬 크론 프롬프트 수정: symlink 경로 → `~/trade-pipeline/langgraph/src/...` 절대경로\n5. 18:00 스킬 크론 프롬프트 수정: 동일

**컨텍스트 체이닝 (2026-06-07 간소화, FRED 데이터 포함)**: 네 cron 출력이 순차적으로 LangGraph 파이프라인의 Context 입력으로 들어감
  ```08:10 → fair_value + Analyst Target + 시장 브리핑
    18:00 → 🇺🇸 미국 증시 브리핑 (fair_value 재실행)
    18:30 → 🌍 매크로 전략 리포트 (macro_context.json 저장)
         ├─ macro_report_summary → Context agent (raw 리포트)
         ├─ market_interpretation → Bull/Bear/Risk/Decision (구조화된 시장 해석)
         └─ key_macro_data → Bull/Bear (정량적 수치 인용)
           ↓
    18:35 → pipeline.py: Phase 0.5에서 FRED+pandas_datareader 데이터 수집
           ├─ fetch_macro_strategy() 호출 (Hermes venv subprocess)
           ├─ macro_strategy.macro_regime (Overheat/Goldilocks/...)
           ├─ macro_strategy.indicators.CPI_YoY / Sahm_Rule / Fed_Funds_Rate
           └─ macro_strategy.alpha_flip_signal (Risk-On/Off)
           ↓ macro_context.json["macro_strategy"] 저장
    18:35 → Phase 2 LangGraph: Context/Bull/Bear/Risk/Decision이
           macro_strategy.* 인용하여 리포트에 반영
    ```

---

## 분석 방법론 (Phase 5 현행 ✅)

> **핵심**: PER 밴드(earnings trajectory) + PBR 밴드(book value trajectory) 결합.
> 항상 PER+PBR 혼합, 절대 순수 PER만 사용 금지.
> 현금(Net Cash) 적정가에 불가산.

### 0. 업종 분류 (SECTOR_BASE + watchlist.json sector 필드)

```python
SECTOR_BASE = {
    'Technology': 22, 'Semiconductors': 18, 'Software': 25,
    'Healthcare': 18, 'Consumer Cyclical': 15, 'Financial': 12,
    'Communication': 20, 'Communication Services': 20,
    'Auto': 7, 'Consumer Defensive': 18, 'Hardware': 18,
    'Industrial': 15, 'Energy': 10,
    'AI Infrastructure': 25,             # AVGO, NVDA
    'Optical Communications': 25,        # LITE (광통신)
    'Consumer Electronics Premium': 28,  # AAPL (브랜드)
    'CPU/GPU': 22,                       # AMD, INTC
    'Semiconductor Equipment': 22,       # LRCX
    'MLCC': 18,                          # 삼성전기
}

# ⚠️ 2026-07-02 변경: TICKER_SECTOR 하드코딩 dict 제거
# sector = watchlist.json의 `sector` 필드에서 직접 가져옴 (단일 진실)
# fair_value.py 변경:
STOCKS = [(s["ticker"], s["name"], s["market"], s["sector"]) for s in WATCH["stocks"]]
for ticker, name, market, sector in STOCKS:
    # sector는 watchlist.json에서 이미 로드됨 — yfinance sector 미사용
    ...

# 효과: 18개 → 33개 종목 분석 (config 18 → watchlist 33으로 확장)
# 단일소스 원칙: 종목 추가/변경 = watchlist.json 1곳만 수정
# see Pitfall 26 — "관심종목은 한파일에서만 관리" 사용자 원칙
```

**이전 (deprecated)** — TICKER_SECTOR dict 패턴 (2026-06-03 ~ 2026-07-01):
```python
TICKER_SECTOR = {  # ❌ deprecated 2026-07-02
    'AVGO': 'AI Infrastructure',
    'NVDA': 'AI Infrastructure',
    ...
}
sector = info.get('sector', 'Technology')
sector = TICKER_SECTOR.get(ticker, sector)
```

### 1. EPS / BPS 궤적
```python
EPS_T0 = Price / PE                    # Current (trailing)
EPS_T1 = Price / FPE                   # Forward 1Y (raw)

BPS_T0 = Price / PBR if PBR else EPS_T0 * 5
# 한국주: 네이버 증권 스크래핑 → 실패 시 EPS_T0 × 5

# BPS_T1: 사이클리컬(FPE<12)은 유보이익, 일반은 EPS 비율
if FPE < 12:
    BPS_T1 = BPS_T0 + EPS_T1 * 0.7      # 유보이익 (30% 배당/자사주)
else:
    BPS_T1 = BPS_T0 * (EPS_T1 / EPS_T0)
```

### 2. 적정 PER

```python
fair_pe = sector_base + gp + dd + rp
fair_pe = clip(fair_pe, 5, 35)

# 사이클리컬 discount
if FPE < 12:
    if market == 'KR':
        fair_pe = min(fair_pe, 11)   # KR 메모리
    elif (PE/FPE) > 3.0:
        fair_pe = min(fair_pe, 20)   # US 메모리
```
- gp = clip((PE/FPE-1) × 15, -5, 12)
- dd = -3 if DE>150% else -1 if DE>100% else 0
- rp = clip((ROE%-10) × 0.2, -3, 5) — **ROE 상한 없음**

### 3. 가중치 — 모든 종목 동일
```
w_per = 0.75   # PER 75%
w_pbr = 0.25   # PBR 25%
```

### 4. Orbit 적정가
```python
Fair_T0 = EPS_T0 × fair_pe × 0.75 + BPS_T0 × (ROE%/9) × 0.25
Fair_T1 = EPS_T1 × fair_pe × 0.75 + BPS_T1 × (ROE%/9) × 0.25
Gap_T0 = (Fair_T0 / Price - 1) × 100
Gap_T1 = (Fair_T1 / Price - 1) × 100
```

---

### Phase 7: T1 Gap Filter — LLM 분석 대상 선별 (2026-06-08: midpoint_gap → t1_gap 전환)

LangGraph Bull/Bear/Decision Maker(LLM 4회)를 실행하기 전, **25종목 중 T1 괴리율 30%↑ 상위 10종목만 선별**.

```python
# Phase 1 (pipeline.py 인라인) — t1_gap 기준
results.sort(key=lambda r: r["t1_gap"], reverse=True)
top10 = [r for r in results if r["t1_gap"] >= 30][:10]
```

- **변경**: Phase 7은 과거 `midpoint_gap`(T1+Target 중간값)을 사용했으나, 2026-06-08 사용자 지시로 `t1_gap`(순수 Model T1 적정가)으로 전환.
- Analyst Target은 리포트 표시용으로만 사용 (필터링/비중 결정에서 배제)
- 출력: T1 Gap Filter 표 (순위·종목·현재가·T1·Target·T1괴리율)

---

### Phase 8: Portfolio Allocation (Phase 3) — LLM 포트폴리오 비중 구성 ✅ (2026-06-07 ~ 06-08 v3)

LangGraph 결정(Phase 2) + 매크로 리포트를 DeepSeek V4 Flash 1회에 전달하여 포트폴리오 비중 구성.

**실행 위치**: `src/agents/portfolio_allocation.py`
**호출 시점**: `pipeline.py` `main()`에서 Phase 2 직후

**Context 준비 — LLM 요약 레이어** (2026-06-08 신규):
- `build_stock_summary()`에서 **raw LangGraph 결과를 직접 전달하지 않음**
- 대신 `summarize_stock(r)` 함수가 각 종목의 context_analysis + bull_case + bear_case + risk_case + rationale를 **DeepSeek V3 1회 호출로 3~5줄 요약**
- 요약 프롬프트: "Extract only: (1) Moat indicators (2) Key growth driver (3) Key risk (4) Decision rationale. Output 3~5 bullet lines in Korean."
- 사용자 교정 이력: "자르면 안된다고 했는데" → "자르지말고 주요 정보만 llm으로 요약해서"
- **원칙**: 절대 `[:200]` 같은 하드 truncation 사용 금지. 대신 LLM으로 핵심 추출.
- 비용: 7종목 × DeepSeek V3 1회 ≈ 소폭 증가 (월 예산 30,000원 내 충분)

**Input**: 
- 7종목 결과 (decision, confidence, t1_gap, Bull/Bear/Risk LLM 요약)
- macro_context (regime, key_macro_data, market_interpretation)

**Output**: `logs/portfolio/YYYY-MM-DD.json`
```json
{
  "date": "2026-06-08",
  "regime": "Slowdown",
  "cash_ratio": "30%",
  "cash_reason": "Regime Slowdown 기준 25% + Alpha-Flip Bearish +5%p = 30%",
  "stocks": [
    {
      "name": "HPE",
      "decision": "HOLD",
      "weight": "2%",
      "reason": "시장해석 기반 근거 (gap 128.5% × moat 3/10) — 경쟁 심화로 해자 낮음, AI 서버 수요는 견조",
      "moat_score": "3",
      "moat_reason": "서버 경쟁 심함, 차별화 약함"
    }
  ],
  "expected_return": "-5~0%",
  "key_risks": ["반도체 AI CapEx 둔화"]
}
```

**비중 결정 공식** (2026-06-08 v2): 
```
moat_점수 = LLM이 종목 데이터로 추정 (1~10, 해자 기준 루브릭 사용)
가중값 = max(0, t1_gap) x moat_점수
기본_비중 = (가중값 / 총_가중값) x (100% - 현금비중)
```
- **오직 gap + moat 두 가지 요소만 사용**. PER상태/성장성/현금흐름 등 다른 요소 반영 금지.
- SELL=2% 고정, 상한 15%/하한 2% 무조건 적용. 초과 시 재분배 (2026-06-08 상한 위반 경험: LLM이 19% 출력 → 강제 15% 재분배)
- `cash_reason` 필드에 현금비중 결정 근거 포함

**현금 비중 규칙 — 유연한 조정** (2026-06-08 수정):
- Before: 하드코딩 (Slowdown=25% 고정, Alpha-Flip ±5%p만 허용)
- After: Regime 기본값 + Alpha-Flip 보정 + 뉴스/매크로 심각성 반영
  - Regime 기본: Goldilocks 5% / Overheat 15% / Slowdown 25% / Stagflation 40%
  - Alpha-Flip: Bearish +5%p, Bullish -5%p
  - 추가 조정: 극단적 이벤트(전쟁, 반도체 쇼크, 유가 급등 등) 시 +10~20%p 추가 가능
  - 최대 현금 50%까지 가능
  - cash_reason에 구체적 근거 명시 (예: "Slowdown 25% + AlphaBearish +5%p + Broadcom쇼크 +10%p = 40%")

**Phase 3 컨텍스트 — Finnhub + FRED 데이터 포함** (2026-06-08 수정):
- Before: build_macro_summary()가 macro_report_summary + market_interpretation[:200]만 전달 → Finnhub 뉴스와 FRED 전략 누락
- After: 모든 필드 포함:
  - macro_report_summary (전문) + market_interpretation (전문) + key_macro_data (전문)
  - stocks[i].news[].title — Finnhub 종목별 뉴스 헤드라인
  - macro_strategy — FRED 지표 (CPI, Fed, 유가, Sahm) + Regime + AlphaFlip
- **2026-06-08 v2: t1_gap x moat(LLM 추정) — 두 요소 조합**
- **2026-06-08 v3: 현금 비중 유연화 + LLM 요약 레이어 + Phase 3 데이터 플로우 수정**

**Phase 3 컨텍스트 — Finnhub + FRED 데이터 포함** (2026-06-08 수정):
- Before (bug): build_macro_summary()가 일부 필드만 전달 → Finnhub stocks[i].news와 FRED macro_strategy 완전 누락
- After: 모든 필드 전문(full text) 전달 — stocks[i].news[].title + macro_strategy 지표 포함
- 사용자 교정: "Finnhub이랑 fed 왜안됨?" → build_macro_summary()가 `macro_ctx.get("stocks", [])`와 `macro_ctx.get("macro_strategy", {})`를 추출하지 않아 누락

**collect_macro_context.py subprocess import 고정**
- 증상: pipeline.py --phase 3에서 subprocess 실행 시 ModuleNotFoundError: No module named 'src'
- 원인: subprocess는 새 Python 프로세스 — src/가 경로에 없음
- 해결: 스크립트 내부에 sys.path.insert(0, PROJECT_DIR) 추가
- 참조: Pitfall 30 (2026-06-07: -m 플래그 권장) — subprocess에서는 불가능하므로 자체 경로 추가

**Phase 3 → Discord 전송: 5개 메시지 분할** (2026-06-08)

LangGraph 크론(18:35, job_id: afebf6cb0ab1)이 pipeline.py 실행 후 각 Phase 결과를 **5개 개별 메시지**로 Discord 전송:

| # | Phase | 전송 내용 |
|:-:|:------|:---------|
| 1 | Phase 0 | fair_value 종목별 T0/T1 적정가·괴리율 + Analyst Target |
| 2 | Phase 0.5 | Key Driver, Regime, FRED 전략, Finnhub 뉴스 헤드라인 |
| 3 | Phase 1 | T1 Gap Filter 표 (통과/탈락, 괴리율 순위) |
| 4 | Phase 2 | LangGraph 종목별 결정·신뢰도·Bull/Bear/Risk 요약 |
| 5 | Phase 3 | 포트폴리오 표 + 현금근거 + 기대수익 + 리스크 |

- 각 Phase 구분선 `─────` 포함, 1500자 초과 시 분할
- 실패 Phase는 원인 명시 후 다음 Phase 진행
- 마지막에 소요시간 + API 비용 추가
- 크론 프롬프트는 `afebf6cb0ab1` 참조

**변경 이력**: 
- 2026-06-07: midpoint_gap 기반 (T1+Target 평균)
- 2026-06-08 v1: t1_gap 기반 (gap 단독, Moat 금지)
- **2026-06-08 v2: t1_gap × moat(LLM 추정) — 두 요소 조합**
- **2026-06-08 v3: 현금 비중 유연화 + LLM 요약 레이어 + Phase 3 데이터 플로우 수정**
- **2026-06-08 v4: Discord 분할 전송 (5개 메시지)**
- **2026-06-16 v5: reason 필드 시장해석 기반으로 전환** — 순수 gap×moat 계산식 → 매크로/뉴스 맥락 1문장 포함
- **2026-06-16 v5: reason 출력 truncation 60자·칸 너비 55자로 확대**

**Phase 3 컨텍스트 — Finnhub + FRED 데이터 포함** (2026-06-08 수정):
- Before (bug): build_macro_summary()가 일부 필드만 전달 → Finnhub stocks[i].news와 FRED macro_strategy 완전 누락
- After: 모든 필드 전문(full text) 전달 — stocks[i].news[].title + macro_strategy 지표 포함
- 사용자 교정: "Finnhub이랑 fed 왜안됨?" → build_macro_summary()가 `macro_ctx.get("stocks", [])`와 `macro_ctx.get("macro_strategy", {})`를 추출하지 않아 누락

**collect_macro_context.py subprocess import 고정**

---

### Phase 9: Monthly Performance Review — 월간 성과 검증 리포트 ✅ (2026-06-07)

매월 1일, 지난달 전체 결정 데이터 집계 → LLM 분석 리포트 생성.

**실행 위치**: `src/monthly_performance_review.py`
**크론**: `10 8 1 * *` (job_id: `18510b01362d`), **LLM prompt** (script 필드 없음)
**저장**: `logs/monthly_review/YYYY-MM.md`
**비용**: DeepSeek V4 Flash 1회 ≈ $0.03 (45원/월)

**리포트 항목**: 결정 패턴 분석, 포트폴리오 평가, 방법론 개선 제안
**상세**: `references/monthly-performance-review.md`

### Phase 10: Decision Validation Engine — 결정 추적 및 검증 ✅ (2026-06-07)

과거 모든 결정 로그(`logs/decisions/*.json`)를 읽어 결정 시점 가격 vs 현재 가격을 비교, 파이프라인 성과를 정량 측정.

**실행 위치**: `src/agents/decision_validator.py` (trading-agents-nuri-langgraph)
**저장**: `logs/validation/YYYY-MM-DD.json` + `.md`
**트리거**: 매 실행 시 자동 갱신, 또는 독립 실행

**작동 방식**:
1. 77개+ 결정 로그 읽기 (종목별 중복 제거)
2. **현재가 조회**: 전 종목 yfinance (한국 .KS 포함)
3. 결정가 vs 현재가 수익률 계산
4. BUY: 가격 상승=Win / HOLD: 중립 관찰 / SELL: 가격 하락=Win
5. 중복 제거 리포트

**TICKER_MAP** (한글명 → ticker 변환):
- SNDK (샌디스크) — **WDC 아님** (사용자 교정: WDC→SNDK)
- 한국(.KS) 종목: yfinance로 조회 (가격 및 통화 비교용)

**월간 리뷰 통합**: `monthly_performance_review.py`가 `collect_validation()` 함수로 검증 데이터 읽음 → LLM 프롬프트에 검증 결과(정확도, 수익률) 포함 → 리포트에 표시

**상세**: `references/decision-validation.md`

### Phase 11: Analyst Target Only Policy — 개인 의견 배제 ✅ (2026-06-07)

### 🔴 데이터 계약(Data Contract) 검증 — producer/consumer JSON 키 일치 확인 (2026-06-07 신규)

다중 Phase 파이프라인에서 가장 빈번한 버그 유형은 **A Phase가 저장한 JSON의 키 구조와 B Phase가 읽는 키 구조의 불일치**다.
- **증상**: 실행 시 에러가 나지 않고 조용히 모든 값이 "N/A"로 떨어짐
- **방지**: 새 Phase 추가 시 실제 JSON 출력 파일을 읽어 키 목록을 확인
- **중요**: `macro_context`처럼 여러 consumer가 공유하는 파일은 모든 consumer의 `.get()` 키를 반드시 대조
- **참조**: `references/macro-context-data-contract.md`
- 사용자 교정: "내 의견 넣지 말고 애널리스트 목표주가 의견만 사용해"
- `KR_KNOWN_TARGETS` 하드코딩 제거, 컨센서스만 사용
- **참조**: `references/analyst-target-only-policy.md`

### Phase 11: Feedback Loop — logs/monthly_review/ 로 통합 ✅ (2026-06-07)

**저장소**: `logs/monthly_review/` (trade-pipeline 내), `docs/portfolio-wiki/`
**흐름**: 월간 리포트 → 분석 → trade-pipeline README/docs 업데이트

**전체 피드백 루프**:
```
결정 → logs/decisions/ → decision_validator → logs/validation/ 
  → monthly_performance_review → logs/monthly_review/ 
    → docs/portfolio-wiki/ + README 업데이트
      → 개선 → pipeline 변경 → 결정 (순환)
```
> 과거 `mybotagent/portfolio-feedback` 및 `mybotagent/trading-agents-nuri-feedback` 레포는 trade-pipeline으로 통합 후 ARCHIVED 처리됨.

### 📊 최종 정확도 (2026-06-03, 22개 종목)

| 등급 | 기준 | 수 |
|:---:|:----|:-:|
| 🎯 | ±10% | **5** |
| ✅ | ±10~25% | **6** |
| ⚠️ | ±25~50% | **6** |
| ❌ | ≥50% | **3** |

---

## 실행 스크립트 (2026-06-08 → trade-pipeline/)

**통합 레포**: `mybotagent/trade-pipeline` → `~/trade-pipeline/`  
**Python 모듈**: `langgraph/src/` 아래

### 메인 밸류에이션 분석
```bash
cd ~/trade-pipeline && python3 langgraph/src/fair_value.py
```

### Analyst Target 수집 + 검증
```bash
cd ~/trade-pipeline && python3 langgraph/src/analyst_target_collector.py
```

### 전체 파이프라인 실행
```bash
cd ~/trade-pipeline && python3 langgraph/pipeline.py
```

### 단계별 실행
```bash
cd ~/trade-pipeline && python3 langgraph/pipeline.py --phase 0
cd ~/trade-pipeline && python3 langgraph/pipeline.py --phase 1
cd ~/trade-pipeline && python3 langgraph/pipeline.py --phase 2
cd ~/trade-pipeline && python3 langgraph/pipeline.py --phase 3
```

> ⚠️ fair_value_v3.py는 fair_value.py의 심볼릭 링크였음 (2026-06-07 symlink 제거 완료). 현재는 08:10(스킬) + 18:00(US 스킬)에서 하루 2회 실행. pipeline.py Phase 0은 subprocess 재실행하지 않고 저장된 stdout 파일만 읽음.

### 크론 실행 순서 (매일 08:00 / 18:00 KST)
1. `analyst_target_collector.py` → 최신 target 수집 + 검증
2. `fair_value.py` → 분석

## 크론 일정 (2026-06-23 최종, 10개)
| 시간 (KST) | 작업 | job_id | 주말 |
|:----------:|:----|:------:|:----:|
| 04:00 (평일) | 📚 새벽 wiki 동기화 + 메모리 정리 | 64adaa1d6b0e | OFF |
| 07:00 (월) | 🔍 주간 스크리너 + 자동퇴출 | d92ed6044d32 | 월 only |
| 08:00 (평일) | 📅 구글 캘린더 일정 요약 | 2f553ea20e27 | OFF |
| 08:10 (평일) | 📊 오전 포트폴리오 + 한국/미국 브리핑 | 6297df83d4f3 | OFF |
| 08:30 (월) | 📅 주간 계획 알림 | 47f701ea2755 | 월 only |
| 08:00 (매월 1일) | 📈 월간 전략 리포트 — LLM prompt (Hermes venv 실행) | d3080e6f3789 | OFF |
| **08:10 (매월 1일)** | **📈 월간 성과 검증 리포트 — LLM prompt** | **18510b01362d** | **OFF** |
| 18:00 (평일) | 🇺🇸 미국 증시 브리핑 | 2916cc9c2ceb | OFF |
| 18:30 (평일) | 🌍 매크로 전략 리포트 | b96583fa9d27 | OFF |
| **18:35 (평일)** | **🧠 LangGraph 파이프라인 — LLM prompt** | **afebf6cb0ab1** | **OFF** |

> ⚠️ 주말(토/일) 모든 크론 OFF. `1-5` = 평일만 실행.
>
> **18:35 LangGraph 파이프라인**이 pipeline.py를 실행. 18:00 US 스킬 크론과 18:30 매크로 LLM 크론이 데이터 생성 후 pipeline이 읽음.
>
> ❗ 크론을 변경할 때는 절대 기존 크론을 함부로 제거하지 말 것. 각 크론의 목적(한국 오전/미국 오후/매크로/파이프라인)을 반드시 이해한 후에만 수정. 사용자 교정: "오전에는 한국 증시 오후에는 미국 증시 브리핑인데? 왜 지움?"

---

## 🔗 관련 스킬
- **`stock-rating-system`**: S+~F 정성 평가.
- **`macro-strategy-report`**: 🌍 글로벌 매크로 전략 리포트 (18:30 KST 일일).

## 📎 참고 파일
- `references/latest-analyst-targets.md` — 최신 개별 target 수집
- `references/ticker-maintenance.md` — 관심종목 추가/제거
- `references/watchlist-data-contract.md` — watchlist.json 구조와 종목 관리
- **`references/fred-macro-strategy.md`** — FRED+yfinance 매크로 데이터 Phase 0.5 통합
- **`references/cron-mode-data-verification.md`** — subagent 데이터 검증 + 정부 데이터(BLS/FRED/IMF) 직접 차단 시 Google News RSS press-release fallback 패턴 (2026-07-13 추가)
- `references/orbit-original-code.md` — Orbit 원본 코드
- `references/trading-agents-architecture.md` — TradingAgents 기반 LLM Agent Layer (v3.2 최종)
- `references/dynamic-analysis-depth.md` — 데이터 품질 기반 조건부 분기 설계
- `references/systematic-parameter-tuning.md` — 파라미터 튜닝
- `references/pe-fpe-ratio-analysis.md` — PE/FPE 분석
- `references/korean-stock-data.md` — 한국주 데이터 처리 (네이버 증권 스크래핑, 네이버 뉴스, 너구리 target)
- `references/unified-formula-dilemma.md` — cycle cap vs one formula
- `references/ai-infrastructure-sector.md` — AI Infrastructure 정의
- `references/paper-code-verification.md` — 논문 GitHub 코드 검증 패턴
- `references/yfinance-data-limitations.md` — yfinance 15~20분 지연 분석
- `references/model-analyst-midpoint.md` — Model T1 vs Analyst Target 중간값 절충 기법 + NAME_TO_TICKER 매핑
- `references/capture-pipeline.md` — stdout 캡처 레이어 (data/daily_snapshot.json → filtered_top10.json → macro_context.json 통합)
- `references/pipeline-phase-architecture.md` — Pipeline Phase 구성, 독립 실행 명령어, 파일 체인
- **`references/prompt-engineering-v4.md`** — V4 프롬프트 전체 + 시장 해석 인용 규칙 (2026-06-06 신규)
- **`references/per-stock-delivery.md`** — 종목별 분할 Discord 전송 + truncation 제거 규칙 (2026-06-06 신규)
- **`references/macro-context-data-contract.md`** — macro_context.json 필드별 producer/consumer 매핑 + 자주 발생하는 데이터 키 불일치 실수 (2026-06-07 신규)\n- **`references/news-collection-architecture.md`** — Finnhub(US)+Naver(KR) 뉴스 수집 아키텍처 (2026-06-07 신규)
- **`references/cron-schedule.md`** — 크론 전체 일정 snapshot + 데이터 흐름 + 변경 이력 (2026-06-07 신규)
- **`references/discord-pipeline-delivery.md`** — LangGraph 크론 Discord 5분할 전송 규칙 (2026-06-08)
- **`references/cron-testing-bg-review.md`** — 크론 수동 테스트 시 bg-review 툴 제한 및 우회 방법 (2026-06-07 신규)
- **`references/t1-gap-vs-midpoint.md`** — T1 괴리율 전환 사유 및 변경 내역 (2026-06-08)
- **`references/fear-greed-index.md`** — CNN Fear & Greed Index API, 봇 우회 방법, 스크립트, 08:10 크론 통합 (2026-06-10 신규)
- **`references/moat-estimation-rubric.md`** — Moat 점수 LLM 추정 루브릭 + 실행 사례 (2026-06-08 신규)

### 34. 🔴 Phase 3 컨텍스트 누락 — Finnhub 뉴스와 FRED 데이터가 포트폴리오 비중 결정에 안 들어감 (2026-06-08 신규)
- `build_macro_summary()`가 `macro_ctx`의 모든 필드를 추출하지 않음
- 증상: `market_interpretation[key][:200]`만 전달, `stocks[i].news`(Finnhub)와 `macro_strategy`(FRED) 누락
- 결과: Phase 3 LLM이 Finnhub 뉴스와 FRED 경제 지표를 보지 못함 → 현금 비중 결정이 뉴스/매크로 심각성 반영 못 함
- **해결**: `build_macro_summary()`에 `macro_ctx.get("stocks", [])` 순회 + `macro_ctx.get("macro_strategy", {})` 추출 로직 추가
- 참조: portfolio_allocation.py build_macro_summary() 함수 (2026-06-08 수정 완료)

### 35. 🔴 DeepSeek API 키 이중 관리 — .env + Hermes config.yaml (2026-06-08 신규)
- `deepseek.py`의 `call_v3()`/`call_r1()`은 `load_dotenv()`로 `.env` 파일에서 API 키 로드
- 문제: `.env` 파일이 실수로 덮어써지거나 `***` 값이 저장되면 API 호출 실패
- **증상**: `[API Error 401] Authentication Fails, Your api key: **** API is invalid`
- **해결**: `deepseek.py`에 Hermes config.yaml fallback 추가
  ```python
  # .env 키가 없거나 ***면 Hermes config.yaml에서 fallback
  if not API_KEY or API_KEY.strip() == "***":
      config_path = os.path.expanduser("~/.hermes/config.yaml")
      if os.path.exists(config_path):
          with open(config_path, "r") as f:
              cfg = yaml.safe_load(f) or {}
          key = cfg.get("providers", {}).get("deepseek", {}).get("api_key", "")
          if key and key.strip() != "***":
              API_KEY = key
  ```
- **주의**: `yaml` 패키지 import 필요 (`import yaml`)
- `.env` 파일 신규 생성 시 `DEEPSEEK_API_KEY=`를 비워두거나 `DEEPSEEK_API_KEY=***`로 둬도 Hermes config fallback이 자동 처리
- 월별 예산 관리와 무관 — Hermes config의 key는 Hermes provider 레벨에서 관리하는 키이므로 프로젝트별 추가 비용 발생 안 함

### 37. 🔴 langgraph/src/ 하위 경로 depth 계산 (2026-06-07 신규)
- `langgraph/src/` 아래 Python 파일(`fair_value.py`, `analyst_target_collector.py` 등)은
  `os.path.dirname(os.path.abspath(__file__))` depth가 3까지 필요함
- **공식**: `trade-pipeline/data/watchlist.json`에 접근하려면 `dirname × 2` 필요
  ```python
  # langgraph/src/analyst_target_collector.py  (정답)
  WATCHLIST_PATH = os.path.join(
      os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
      "data", "watchlist.json"
  )
  # → /home/ubuntu/trade-pipeline/data/watchlist.json ✅
  
  # langgraph/src/fair_value.py  (정답)
  PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  # → /home/ubuntu/trade-pipeline/ ✅
  ```
- **실수 패턴**: `".."` 하나만 넣으면 `langgraph/data/`로 잘못 향함
- **참조**: `references/path-depth-calculation.md`
- **검증**: `python3 -c "import os; print(os.path.dirname(os.path.dirname(os.path.abspath('FILE'))))"`

### 38. 🔴 Python 환경 불일치 — pip vs python3 (2026-06-07 신규)
- `which python3` → Hermes venv (Python 3.11), `pip` → system (Python 3.12) **mismatch**
- `pip install langgraph`로 설치해도 Hermes venv python3에서 `import langgraph` 실패
- **해결**:
  1. `~/.hermes/hermes-agent/venv/bin/python3 -m ensurepip --upgrade`
  2. `~/.hermes/hermes-agent/venv/bin/python3 -m pip install <package>`
- **증상 확인**: `python3 -c "import langgraph"` → 오류면 Hermes venv에 없음
- 파이프라인 실행 시 `python3 langgraph/pipeline.py`는 Hermes venv python3(3.11)을 사용하므로,
  필요한 패키지(langgraph, httpx, yfinance, python-dotenv, yaml 등)는 모두 Hermes venv에 설치되어 있어야 함

### 39. 🔴 .env 키 값 오염 — fallback 무력화 (2026-06-07 신규)
- `deepseek.py`는 `.env`의 `DEEPSEEK_API_KEY`가 `***`인지 검사하여 Hermes config.yaml fallback으로 전환
- **발견된 오염 패턴**: `DEEPSEEK_API_KEY=*** Finnhub API` — 키 값 뒤에 주석이 붙어서 `***` 검사 실패
- `.env`에서 `#` 없는 인라인 주석은 키 값의 일부로 인식됨
- **방지**: `.env`에서 여러 키를 한 줄에 넣지 말 것. 반드시 `#`으로 주석 분리.

- **참조**: `references/trade-pipeline-migration.md` (레포 이전 체크리스트)
- Before: `Slowdown=25%` 하드코딩, `Alpha-Flip ±5%p`만 허용 → 시장 쇼크 반영 불가
- After: Regime 기본값 + Alpha-Flip 보정 + **극단적 이벤트 추가 조정 (LLM 판단)**
  - Regime 기본: Goldilocks 5% / Overheat 15% / Slowdown 25% / Stagflation 40% / Severe_Inflation 30% / Deflation 10%
  - Alpha-Flip: Bearish +5%p, Bullish -5%p
  - 추가 조정: Broadcom 쇼크($1.3조 증발), 전쟁(유가 급등), 원화 급락 등 발생 시 **+10~20%p 추가 가능**
  - 최대 현금: **50%** (극단적 상황)
  - `cash_reason` 필드에 구체적 근거 명시 필수 (예: "Slowdown 25% + AlphaBearish 5% + Broadcom쇼크 10% = 40%")
- 참조: portfolio_allocation.py PROMPT 규칙 1번 (2026-06-08 수정 완료)
- 함정: LLM이 15% 상한을 위반하는 경우 발생 (실제 19% 출력 사례) → 프롬프트에 "**15% 초과 절대 불가**" 강조
- Phase 3 포트폴리오 비중 프롬프트에 LangGraph raw text를 직접 전달하지 말 것
- `build_stock_summary()`에서 `summarize_stock()` 함수로 각 종목의 분석 결과를 LLM 요약 후 전달
- `bull_case[:200]` 같은 하드 슬라이싱 금지 — 중요한 해자 정보가 200자 뒤에 있을 수 있음
- 사용자 교정 이력:
  1. 초기: truncation 200자로 bull/bear 전달
  2. "자르면 안된다고 했는데" → raw 전문 전달로 변경 (but token 과다)
  3. "자르지말고 주요 정보만 llm으로 요약해서" → **LLM 요약 레이어 도입** (최종 ✅)
- **Phase 2 → Phase 3 데이터 흐름**:
  ```
  LangGraph 결과 (raw 500~860자/종목)
    → summarize_stock() [DeepSeek V3 1회/종목]
      → 3~5줄 요약 (해자·성장동력·리스크·결정근거)
        → Phase 3 PROMPT {stock_results}
  ```

### 33. 🔴 사용자 탐색 패턴 변화 — 빠른 반복 + 점진적 조건 변경 (2026-06-08 신규)
- 사용자: 한 번에 완벽한 솔루션 대신, 빠르게 결과 보여주기 → 피드백 → 조건 변경 반복 선호
- 이번 세션 패턴:
  1. "비중에 내가 구한 gap이 중요한거 같은데" → gap 단독 비중
  2. "T1 이 더 정확하면 그것을 활용" → midpoint_gap → t1_gap
  3. "Gap과 해자만 활용" → gap × moat 두 요소 조합
  4. "LLM이 추정하기" → moat 점수 LLM 추정
  5. "자르지말고 주요 정보만 llm으로 요약해서" → LLM 요약 레이어
- **대응**: 코드를 작은 단위로 변경하고, 매번 사용자 피드백을 받은 후 다음 단계로 진행
- **금지**: 한 번에 모든 변경사항을 다 구현하고 "됐습니다" 하는 방식
- 사용자: "내 의견 넣지 말고 애널리스트 목표주가 의견만 사용해"
- **KR_KNOWN_TARGETS** 같은 하드코딩된 개인(target) 값 절대 금지
- KR 종목 analyst target: **네이버 컨센서스 스크래핑**만 사용 (`coinfo.naver` 페이지)
  - `get_kr_naver_consensus(code)` 함수 사용
  - 삼성전자 예: ₩426,250 (네이버 consensus 평균)
  - 컨센서스 실패 시 → `latest_target = None`, `source = '데이터없음'`
- US 종목 analyst target: **yfinance upgrades_downgrades** 30일 window 최신 개별 target
  - 컨센서스 평균(`targetMeanPrice`) 금지
- **절대 금지**: `KR_KNOWN_TARGETS = {'삼성전자': 500000}` 같은 하드코딩
- **절대 금지**: 너구리/사용자 제공 값을 `latest_target`으로 사용
- 비교 표시도 금지: "너구리제공 vs 네이버컨센서스 X% 차이" 같은 출력 제거, 단순히 컨센서스 값만 표시

### 22. 🔴 파이프라인 subprocess 재실행 금지 — 저장된 stdout만 읽기 (2026-06-07 교정)
- pipeline.py Phase 0은 **절대 subprocess로 fair_value.py/analyst_target_collector.py를 재실행하지 않는다**
- 대신 `data/fair_value_stdout.txt`와 `data/analyst_stdout.txt`를 직접 읽어 파싱
- 이유: 08:10(스킬)과 18:00(통합 크론 Step 1)에서 이미 스크립트를 실행해 stdout 파일을 저장함. pipeline에서 또 실행하면 **3중 실행**이 됨
- midpoint_filter.py도 pipeline.py에 인라인 통합 — 별도 스크립트 아님
- capture_and_save.py, capture_existing.py, midpoint_filter.py, portfolio_tracker.py는 모두 삭제됨
- **데이터 체인**: stdout 파일(.txt) → `read_fair_value_stdout()` → `daily_snapshot.json` → `run_phase1()` 인라인 필터 → `filtered_top10.json` → LangGraph

다중 Phase 파이프라인에서 가장 빈번한 버그 유형은 **A Phase가 저장한 JSON의 키 구조와 B Phase가 읽는 키 구조의 불일치**다.

### 22b. 🔴 macro_context.json 이중 저장 — trading-agents-nuri + trade-pipeline (2026-06-10 신규)

18:30 매크로 크론이 `macro_context.json`을 저장할 때 **두 경로 모두에 저장해야 함**:
- `~/trading-agents-nuri/data/macro_context.json` (과거 레포, 일부 스크립트가 참조)
- `~/trade-pipeline/data/macro_context.json` (현행 통합 레포, pipeline.py가 읽음)

**실수 패턴**: 한쪽만 저장하면 18:35 LangGraph 파이프라인(pipeline.py)이 macro_context.json을 읽지 못해 Phase 0.5/2/3에서 데이터 누락 발생.

**해결**: 리포트 생성 후 `cp`로 복사:
```bash
cp ~/trading-agents-nuri/data/macro_context.json ~/trade-pipeline/data/macro_context.json
```

### 🔴 Subagent 데이터 fabrication — 검증 필수 (2026-06-15 신규)

크론 모드에서 `delegate_task`(web toolsets)로 수집한 매크로 데이터는 **검증 없이 사용 금지**.

**2026-06-15 사례**: subagent가 USD/KRW를 1,315로 보고했으나,
직접 검증(`open.er-api.com`) 결과 1,516.97 — **200원 차이(+13%)**.
이는 매크로 리포트의 Key Driver 판단과 포트폴리오 비중 결정을 왜곡할 수 있음.

**규칙**:
1. Subagent는 뉴스/정성 데이터(제목·요약·URL) 수집에만 사용
2. 정량 수치(환율·금리·유가·S&P)는 반드시 직접 API 검증
3. 검증값과 subagent값 차이 5% 이상 → subagent값 폐기, 검증값 사용
4. 검증 자체 실패 시 → "데이터 수집 실패"로 보고, fabrication 데이터 저장 금지

**참조**: `references/cron-mode-data-verification.md` (검증 명령어·도구 제약 전체 목록)

### 🔴 크론에서 뉴스 수집: delegate_task 우회 패턴 (2026-06-10 신규)

18:30 매크로 크론(LLM prompt)에서 `web_search` 툴이 없거나, `execute_code`가 크론 모드에서 차단된 경우:

**올바른 패턴**: `delegate_task`에 `toolsets=['web','terminal']`을 넘겨 뉴스 리서치를 위임
```python
# 크론 내부에서 (LLM prompt로 실행 중)
delegate_task(
    goal="Search for latest news on these 6 Korean stocks and global macro...",
    context="Today is June 10, 2026...",
    toolsets=['web','terminal']
)
```

**작동 원리**: 
- Subagent는 `web` toolset을 통해 Google News RSS, 뉴스 사이트 검색 가능
- Subagent는 `terminal` toolset으로 curl/RSS 파싱 실행 가능
- Subagent는 `delegate_task`를 호출할 수 없으므로(leaf role) 무한 위험 없음
- 크론 모드의 제한(execute_code 차단, pipe-to-interpreter 차단)은 subagent에 적용되지 않음

**주의**: Subagent는 독립적인 컨텍스트에서 실행됨. 매크로 데이터(SPY, WTI, DXY 등)는 직접 `terminal()`로 수집한 후 subagent에는 뉴스만 위임할 것. subagent에 한국어로 요청하려면 context에 "한국어로 검색해"를 명시해야 함.

### 🔴 크론 함부로 제거 금지 — 각 크론의 목적을 반드시 이해할 것 (2026-06-07 교정)
- 사용자 교정: "기존 방식 왜 지움? 오전에는 한국 증시 오후에는 미국 증시 브리핑인데?"
- **08:10** = 한국 증시 오전 브리핑 (한국장 개장 전)
- **18:00** = 미국 증시 오후 브리핑 (미국장 개장 전)
- **18:30** = 글로벌 매크로 리포트 (web_search + LLM)
- **18:35** = LangGraph 파이프라인 (Python)
- 이 4개는 각각 다른 목적을 가진 **별개 작업**이다. 절대 하나로 통합하려 하지 말 것.
- 크론을 제거/변경하기 전에 반드시 `cronjob action=list`로 현재 상태를 사용자에게 먼저 보여주고 승인받을 것.
- 사용자 교정: "크론잡 리스트 부터 보여줘 잘 정리했는지 확인하게"
- 사용자에게 변경 사항을 설명할 때는 **현재 vs 변경 후 표**를 반드시 보여줄 것.

### 24. 🔴 fair_value_v3.py와 fair_value.py는 동일 파일 (symlink 제거 완료)
- fair_value_v3.py는 fair_value.py의 심볼릭 링크였음 (2026-06-07 삭제 완료).
- 하루 2회 실행: 08:10(스킬 크론) + 18:00(US 스킬 크론) — pipeline.py Phase 0은 subprocess 재실행하지 않음.

### 25. 🔴 레포 이전 후 cron wrapper 경로 확인 필수 (2026-06-07 신규)
**`~/.hermes/scripts/` 아래 cron wrapper 스크립트(.sh)** 의 경로가 새 레포를 가리키는지 반드시 확인할 것.
- 증상: `run_pipeline.sh`가 `cd /home/ubuntu/trading-agents-nuri-langgraph` (구 레포) → 존재하지 않음 → `set -e`로 즉시 실패
- 08:10/18:00 **스킬 크론**은 src/utils/deepseek.py 등 내부 경로가 상대 경로라서 새 레포에서 자동 동작
- 18:35/매월1일 **no_agent script 크론**은 `~/.hermes/scripts/*.sh`를 경유 → 절대 경로가 깨지면 크래시
- 수정 패턴:
  ```bash
  # BEFORE (broken)
  cd /home/ubuntu/trading-agents-nuri-langgraph
  
  # AFTER (fixed)
  cd /home/ubuntu/trading-agents-nuri
  ```
- **확인 명령어**: `ls -la /home/ubuntu/.hermes/scripts/run_*.sh` + 각 파일 내용 확인
- **강제 규칙**: 레포 이전/이름 변경 시 cron wrapper 스크립트의 cd 경로와 python3 경로를 항상 수정할 것.

### 25b. 🔴 cron script 경로 제약 해결: no_agent → LLM prompt 전환 (2026-06-07 교정)
- cron의 `script` 필드는 **절대경로를 지원하지 않음** — 오류: `Script path must be relative to ~/.hermes/scripts/`
- **1차 해결 (실패)**: `~/.hermes/scripts/wrapper.sh` → `exec /home/ubuntu/trading-agents-nuri/real_script.sh` 패턴
  - 사용자 교정: "모든 소스코드가 새레포에 있어야해. ~/.hermes/scripts/도 안됨"
- **✅ 최종 해결**: no_agent script 크론 3개를 **LLM prompt 크론**으로 전환
  - `afebf6cb0ab1` (18:35 LangGraph): prompt에 `cd ~/trade-pipeline && python3 langgraph/pipeline.py` 포함
  - `18510b01362d` (매월 1일 08:10): prompt에 `cd ~/trade-pipeline && python3 langgraph/src/monthly_performance_review.py` 포함
  - `d3080e6f3789` (매월 1일 08:00): prompt에 Hermes venv python3 실행 명령 포함
- **결과**: `~/.hermes/scripts/` 완전히 비움 (cron wrapper 0개)
- **단점**: LLM 호출 비용 소폭 증가 (크론 실행 시 terminal 명령어 생성에 1회 LLM 호출)
- **규칙**: 새 cron 등록 시 no_agent script 대신 prompt만 사용. script 필드 절대 사용 금지.

### 26. ✅ watchlist.json — **단일 종목 정보 파일 (절대 원칙)** (2026-06-07, 2026-07-02 강화)
- `data/watchlist.json` 모든 종목 정보를 단일 JSON으로 관리 — **사용자 명시 원칙: "관심종목은 한파일에서만 관리"**
- 다른 곳에 종목 정보 중복 저장 절대 금지 (config/stocks.json 류 중복 파일 생성 X)
- 읽기 전용 파일이 watchlist.json을 읽음:
  - `fair_value.py` → STOCKS, `collect_macro_context.py` → NAME_TO_TICKER+KR_TICKERS
  - `pipeline.py` → NAME_TO_TICKER+KR_TICKERS, `analyst_target_collector.py` → KR_TICKERS+US_TICKERS
  - `decision_validator.py` → TICKER_MAP
- **종목 추가/변경은 watchlist.json만 수정하면 됨**
- 상세: `references/watchlist-data-contract.md`
- **watchlist.json을 수정한 후 `git commit -m "watchlist: 종목 변경" && git push` 할 것**
- ⚠️ watchlist.json은 `.gitignore`에 의해 git 추적 제외 → cron/스크립트가 로컬에서 참조. 동기화 불요.

#### 26b. 🔴 수정 전 필수 진단: 중복 소스 grep (2026-07-02 신규)

사용자 원칙 위반의 대표 사례 — "관심종목 X 제외" 1건 처리 시 **3개 파일을 동시 수정**해서 사용자 지적받음.

**규칙**: 어떤 config/setting을 수정하기 전, **다음 4단계**를 항상 수행:

```bash
# ① 수정하려는 값(ticker/필드)이 어디 정의되어 있는지 전수 조사
grep -rln '"HPE"' ~/trade-pipeline/{config,data,langgraph,scripts}/ 2>/dev/null | grep -v __pycache__

# ② watchlist 외 별도 소스가 있으면 → 그 파일은 **단일소스 원칙 위반**이라 통합/삭제 대상
# (예: config/stocks.json은 watchlist의 중복 + 부가 필드 → 통합 후 삭제)

# ③ 사용자 보고: "watchlist.json 외 별도 소스 N개 발견, 통합/삭제 권장"
#    사용자가 "통합하라"고 하면 → 4단계 통합 절차 진행

# ④ 단일소스 원칙 준수 후 수정
```

**실수 패턴 (실제 사례)**:
- 사용자: "hpe 관심종목 제외하기"
- (X) `data/watchlist.json` + `config/stocks.json` + `langgraph/src/fair_value.py` 3곳 동시 수정
- (O) 단계 ① grep → config/stocks.json + fair_value.py TICKER_SECTOR 발견 → 사용자에게 보고 → "한파일에서만 관리, 불필요 파일 제거" → **config/stocks.json 삭제 + TICKER_SECTOR dict 제거 + watchlist.json에 모든 필드 흡수**

#### 26c. ✅ 중복 소스 통합 4단계 (2026-07-02 신규)

중복 config 파일을 단일소스(watchlist)로 통합할 때:

```
1단계: 필드 매핑 + 키 정규화
  - config의 KR ticker ('005930') ↔ watchlist ticker ('005930.KS') → suffix 정규화 매핑
  - config의 고유 필드 (pe_min/pe_max/currency/yahoo_suffix) 식별
  - watchlist에 없는 config 종목 식별 (데이터 손실 방지)

2단계: watchlist.json 확장
  - 모든 종목에 8개 필드 보장 (ticker/name/market/sector/pe_min/pe_max/currency/yahoo_suffix)
  - defaults (KR: 8/18/KRW/.KS / US: 10/30/USD/'')
  - config에 있으면 config 값 우선 적용

3단계: 통합 코드로 변경
  - 읽기 모듈 (e.g., stocks_config.py)이 watchlist.json을 직접 읽도록 변경
  - list → dict 변환 (호환성 유지)
  - API 표면 (ALL_STOCKS, US_TICKERS, KR_TICKERS 등) 시그니처 보존
  - 중복 소스 파일 삭제 + git rm

4단계: 회귀 검증
  - Python import test: `python3 -c "from stocks_config import ALL_STOCKS; print(len(ALL_STOCKS))"`
  - AST syntax check: `python3 -c "import ast; ast.parse(open('...').read())"`
  - 실제 파이프라인 dry-run: `python3 langgraph/src/fair_value.py` (전 종목 분석 확인)
  - 커밋 메시지에 diff 요약 명시 (lines added/removed)
```

**검증 출력 예** (2026-07-02):
```
stocks_config: 33개 US=27 KR=6 (source: data/watchlist.json)
fair_value.py: 33개 전체 분석 정상 (이전 18개 → 33개로 확장)
TICKER_SECTOR removed: OK
```
→ 이전 18개 → 33개로 늘어난 이유: watchlist 33개 전부 vs config 18개만 fair_value가 분석 → 통합 후 전체 분석.

#### 26d. 🔴 watchlist.json ticker 코드 자체 검증 — 수집 시점 cross-check (2026-07-14 신규)

Pitfall 26 / 26b / 26c는 "단일소스 + 중복 통합"의 정합성 문제였음. 별도 4번째 함정: **watchlist.json에 등록된 ticker 코드 자체가 사용자 의도와 다를 수 있음** — 등록 시점에는 검증되지 않은 채 통과된 stale 데이터.

**실제 사례 (2026-07-14)**: watchlist.json에 `에이피알` 종목이 `278280`으로 등록되어 있었으나, Naver Polling 조회 시 응답 `nm='천보'` (2차전지 부품 회사, 화장품 ODM인 에이피알이 아님). **정정 코드 = 278470** (`nm='에이피알'` 확인). 두 회사는 사업군·시총·변동성이 모두 다르므로 **분석 결과 자체가 잘못된 회사에 대해 산출**되는 silent corruption.

**방지 3단계** (수집 시점 1차 방어선):

1. **Naver Polling 1회 응답으로 종목명 cross-check** (모든 한국주 권장):
   ```bash
   python3 -c "
   import json, urllib.request
   raw = urllib.request.urlopen(urllib.request.Request(
     'https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:278280',
     headers={'User-Agent':'Mozilla/5.0'}), timeout=10).read()
   print(json.loads(raw.decode('euc-kr', errors='ignore'))['result']['areas'][0]['datas'][0]['nm'])"
   ```
   - 응답 `nm`이 watchlist의 `name`과 일치해야 통과
   - 불일치 시 → `grep -rn '<ticker>' data/watchlist.json` + 메모리/위키 cross-check

2. **Suffix 검증** (`.KS` vs `.KQ` 혼동 방지): 코스피 ↔ 코스닥 섞인 등록은 시가총액·유동성 등급 자체가 달라짐. watchlist의 `market` 필드와 Naver 응답 일치 확인.

3. **change_pct 부호 검증**: Naver Polling의 `cr` 필드는 부호 포함. 직접 계산 `(nv - pcv) / pcv * 100` 결과와 부호 일치 확인. cron 표 작성 시 부호 누락 실수 방지 (2026-07-14 삼성전기 사례: `cv=-29,000`을 표에서 `+29,000`으로 잘못 적을 위험).

**watchlist.json 정정 워크플로우** (Pitfall 26 단일소스 원칙 준수):
1. `data/watchlist.json`에서 해당 ticker 한 줄 확인
2. 사용자(너구리)에게 "watchlist에 등록된 `{ticker}`가 Naver 응답 기준 `{nm}`입니다. 정정 코드는 `{correct_ticker}` (`{correct_nm}`)입니다. 정정할까요?" 명시적 확인
3. 승인 시 → watchlist.json 1곳만 수정
4. `git commit -m "watchlist: {name} 코드 정정 {old} → {new}"` (선택, watchlist.json은 .gitignore 대상이지만 변경 이력은 보존 가능)

**왜 SKILL 본체 pitfall로 보존하나**: 단일소스 원칙은 코드 구조의 정합성 (Pitfall 26). 이 pitfall은 **데이터 무결성** — 등록 시점에 한 번 잡으면 이후 18:30 매크로 + 18:35 파이프라인 전체에 silent corruption 전파. references/cron-mode-data-verification.md의 Ticker Code Verification 섹션에 **상세 워크플로우 + 코드 예시** 기록. SKILL 본체는 **pitfall 신호등** 역할.

### 27. ⚠️ import os 누락 주의 (2026-06-07 신규)
- 하드코딩 STOCKS 리스트에서 watchlist.json 로드로 변경 시 `import os`와 `import json`이 필요
- 기존에 `import os`가 없던 파일(fair_value.py 등)에서 `os.path.join()`을 쓰면 NameError
- 수정: `fair_value.py` → `import os, json` 추가
- **리팩토링 시 import 체크리스트**: os, json, sys가 필요한 새 함수에서 빠지지 않았는지 확인

**증상**: 실행 시 에러가 나지 않고 조용히 모든 값이 "N/A"로 떨어짐. `mc.get("존재하지않는키", {})`는 `{}`를 반환할 뿐 예외가 아님.

**방지법**:
1. 새로운 Phase를 추가하거나 데이터 구조를 변경했으면 **실제 JSON 출력 파일을 읽어 키 목록을 확인**한다: `python3 -c "import json; print(json.load(open('path/to/file.json')).keys())"`
2. 각 consumer(소비자) 코드를 열어 **접근하는 모든 `.get()` 호출의 키 이름**이 JSON 키와 정확히 일치하는지 대조한다
3. 특히 `macro_context`처럼 여러 consumer(context.py, risk.py, report.py, portfolio_allocation.py)가 공유하는 파일은 반드시 모든 consumer를 확인한다
4. 키 불일치는 조용한 실패(silent failure)이므로, Phase 1-2 통합 테스트 전에 반드시 검증한다
5. **참조**: `references/macro-context-data-contract.md`

### 28. ⚠️ FRED 경제 데이터 수집: pandas_datareader 호환성 문제 (2026-06-07 신규)
- `pandas_datareader`는 pandas 3.x와 호환되지 않음 (`deprecate_kwarg` API 변경)
- **해결책**: `src/utils/macro_strategy.py`의 `fetch_macro_strategy()`가 Hermes Agent venv의 `python3`로 `src/macro_strategy_report.py`를 subprocess 실행
  ```python
  HERMES_PYTHON = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python3")
  result = subprocess.run([HERMES_PYTHON, MACRO_SCRIPT], capture_output=True, text=True, timeout=120)
  data = json.loads(result.stdout)
  ```
- Hermes Agent venv에는 구버전 pandas + pandas_datareader가 호환되어 정상 동작
- **Fallback**: FRED 실패 시 yfinance 자산 가격(SPY, WTI, DXY, USDKRW)만으로 기본 dict 구성

### 29. 🔴 cron wrapper 권한 누락 (2026-06-07 신규)
- 새 레포로 `.sh` 파일을 복사/이동한 후 **실행 권한이 없으면 Permission denied**
  ```bash
  # 증상
  $ bash ~/.hermes/scripts/run_pipeline.sh
  run_pipeline.sh: line 3: /home/ubuntu/trading-agents-nuri/run_pipeline.sh: Permission denied
  ```
- **해결**: `chmod +x ~/trade-pipeline/*.sh` (단, 현재는 cron wrapper 없음 — 모두 LLM prompt로 대체됨)
- **확인**: `ls -la ~/trade-pipeline/*.sh` → `-rwxr-xr-x` (755)인지 확인
- **규칙**: `.sh` 파일을 새 레포에 추가하거나 복사한 후 반드시 `git add` 전에 `chmod +x` 실행

### 31. 🔴 세션 종료 시 git push 누락 — 사용자 트래킹 불가 (2026-06-08 신규)
- 사용자: "잘하고 있는지 트레킹이 어려우니까 github 수시로 업데이트해"
- **규칙**: 모든 작업 세션 종료 시 `cd ~/trade-pipeline && git add -A && git commit -m "간결한 요약" && git push` 실행
- wiki/hermes-logs submodule도 함께 푸시할 것
- `.env`와 `data/*.json`은 .gitignore 대상이므로 push 안 됨 — 정상

### 30. ⚠️ src/ 모듈 import — 반드시 -m 플래그로 실행 (2026-06-07 신규)

### 31. 🔴 `.env` 키 오염 방지 — `***` 접두사 매칭으로 fallback

`.env` 파일에서 키 값 뒤에 주석이 붙으면 값 자체가 오염됨:
```bash
# BAD — 주석이 키 값에 포함됨
DEEPSEEK_API_KEY=*** Finnhub API
# 실제 값: "*** Finnhub API" (공백+주석까지 포함)
```

**대책:**
- `.env` 라인은 **키=값**만 쓰고 같은 줄에 주석 금지. 주석은 별도 줄에:
  ```bash
  # DeepSeek API key
  DEEPSEEK_API_KEY=***
  ```
- `deepseek.py`의 fallback 조건문은 `== "***"` 대신 `"***" in API_KEY` 사용:
  ```python
  if not API_KEY or "***" in API_KEY:
      # Hermes config.yaml fallback
  ```
- Finnhub 키도 동일한 패턴으로 오염 가능 — `.env` 포맷팅 항상 확인

### 40. 🔴 yfinance sector mismatch — watchlist 의도 vs yfinance 실제 sector 수시 점검

yfinance가 return하는 sector(generic)가 watchlist에 설정된 사용자 의도 sector와 다를 수 있음.

### 41. 🔴 스크리너에서 fair_value.py는 절대 수정 금지 (2026-06-23 신규)
- 사용자 지시: "적저가 구하는건 기존거 활용해 코드 변형하지 말고"
- **스크리너 = 발굴만**. 발견된 후보 사용자에게 보고 → 승인 → watchlist 편입
- 적정가 계산은 기존 fair_value.py가 watchlist 기반으로 처리
- `fair_value.py`에 스크리너 기능 추가하거나, 스크리너에 적정가 로직 중복 구현 금지
- 스크리닝 결과 후보의 적정가가 필요하면 watchlist에 추가 후 다음 pip라인 실행에서 자동 계산

yfinance가 return하는 sector(generic)가 watchlist에 설정된 사용자 의도 sector와 다를 수 있음.
코드는 `info.get('sector')`로 yfinance sector를 우선 읽고, `TICKER_SECTOR.get(ticker, sector)`로 오버라이드하므로
**TICKER_SECTOR에 없는 종목은 yfinance sector가 그대로 적용**되어 의도와 다른 base PER가 사용됨.

**발견 방법 (이번 세션에서 정립):**
```python
# 1. 모든 종목의 yfinance sector 수집
stocks = json.load(open('data/watchlist.json'))['stocks']
for s in stocks:
    info = yf.Ticker(s['ticker']).info
    yf_sector = info.get('sector', 'N/A')
    wl_sector = s['sector']
    
# 2. watchlist sector와 비교 — 다른 종목 식별
# 3. cyclical cap/상한 cap으로 base 차이가 무효화되는지 확인
# 4. 실질적 영향 있는 경우만 TICKER_SECTOR에 오버라이드 추가
```

**발견 사례 (2026-06-18):**
| 종목 | watchlist 의도 | yfinance 실제 | 문제 |
|:----|:------------:|:------------:|:----:|
| MSFT | Software (25) | Technology (22) | base 3 차이, 적정PER 29.1→32.1로 개선 |
| 현대차 | Auto (7) | Consumer Cyclical (15) | base 8 차이, 적정PER 14.4→6.4로 수정 |
| 에이피알 | Consumer Cyclical (15) | N/A (fallback 15) | 실제로는 동일, 불필요 |
| BWXT | Industrial (15→22) | Industrials (fallback 15) | 이미 수정 완료 (Technology 22) |

**미발견 사례 (base 차이가 cap에 의해 무효화됨, 수정 불필요):**
- MU (watchlist Semiconductors 18, yf Technology 22): cyclical cap 20으로 무효화
- TSM (watchlist Semiconductors 18, yf Technology 22): cap 35로 무효화
- SK하이닉스 (watchlist Semiconductors 18, yf Technology 22): KR cyclical cap 11로 무효화

**참조**: `references/sector-mapping-audit-20260618.md`

Python 패키지 `langgraph`와 로컬 `langgraph/` 디렉토리가 이름 충돌:
```python
# BAD — sys.path에 PROJECT_DIR만 추가하면 'from langgraph.graph import...'가
# 로컬 langgraph/ 디렉토리를 먼저 찾아서 ModuleNotFoundError 발생
sys.path.insert(0, PROJECT_DIR)

# GOOD — src/와 LANGGRAPH_DIR을 PROJECT_DIR보다 먼저 추가
LANGGRAPH_DIR = os.path.join(PROJECT_DIR, "langgraph")
sys.path.insert(0, os.path.join(LANGGRAPH_DIR, "src"))
sys.path.insert(0, LANGGRAPH_DIR)
```

### 33. 🔴 WATCHLIST_PATH depth 계산 — `langgraph/src/`에서 3단계

`langgraph/src/` 디렉토리 아래 파일에서 `data/watchlist.json` 경로 계산:
```python
# BAD — 1단계만 올라감 (langgraph/src/ → langgraph/data/)
WATCHLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", ...)

# GOOD — 3단계 올라감 (langgraph/src/analyst_target_collector.py → trade-pipeline/)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WATCHLIST_PATH = os.path.join(PROJECT_DIR, "data", "watchlist.json")
```

### 34. 🔴 데이터 수집 순차 실행 필수 — 중간 파일 덮어쓰기 방지

파이프라인 Phase 간 데이터 파일 체인이 있으므로 **절대 동시/병렬 실행 금지:**
```bash
# ✅ 올바른 순서
python3 langgraph/src/analyst_target_collector.py > data/analyst_stdout.txt
python3 langgraph/src/fair_value.py > data/fair_value_stdout.txt
python3 langgraph/pipeline.py

# ❌ 금지 — 동시 실행 시 data/analyst_stdout.txt 경쟁 상태
```
- `cronjob action='run'`은 bg-review에서 tool 제한(teminal 금지)으로 실제 테스트 불가.
- 테스트는 반드시 직접 `terminal()` 호출로 순차 실행할 것.
- `src/` 디렉토리 안의 스크립트를 직접 `python3 src/collect_macro_context.py`로 실행하면 `ModuleNotFoundError: No module named 'src'`
- **올바른 실행법**:
  ```bash
  cd ~/trade-pipeline
  python3 langgraph/src/collect_macro_context.py   # langgraph/src/ 내에서 python3 직접 실행
  ```
  또는
  ```bash
  cd ~/trade-pipeline && python3 -m langgraph.src.collect_macro_context   # ✅ -m 플래그
  ```
- `-m` 없이 실행하면 `src.utils.macro_strategy` 같은 `src.` 접두사 import를 찾지 못함
- 대안: `collect_macro_context.py`가 내부에서 `sys.path.insert(0, PROJECT_DIR)`로 경로 추가
- `pipeline.py`는 루트에 있어서 문제 없음 (`python3 langgraph/pipeline.py`로 실행)
