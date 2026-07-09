# Decision Validation Engine

**파일**: `trading-agents-nuri-langgraph/src/agents/decision_validator.py`
**실행**: `python3 src/agents/decision_validator.py` (langgraph venv)
**저장**: `logs/validation/YYYY-MM-DD.json` + `.md`
**비용**: $0 (네이버 API + yfinance, 무료)

## 핵심 로직

### 1. 데이터 로드
- `logs/decisions/*.json` 파일 스캔 (full_*, report_* 제외)
- 각 JSON의 `results[]`에서 ticker, decision, price 등 추출
- 중복 제거: 종목별 최신 결정만 리포트에 표시

### 2. 현재가 조회 (이중 채널)

| 시장 | API | 함수 | 특징 |
|:----|:----|:------|:------|
| 🇰🇷 한국(.KS) | 네이버 `itemSummary.nhn` | `get_korean_price()` | 실시간, JSON 응답 |
| 🇺🇸 미국(기타) | yfinance | `get_current_price()` | 15~20분 지연 |

#### 네이버 API (한국 주식)
```python
conn = http.client.HTTPSConnection("api.finance.naver.com", timeout=10)
conn.request("GET", f"/service/itemSummary.nhn?itemcode={code}",
             headers={"Referer": "https://finance.naver.com/"})
data = json.loads(conn.getresponse().read())
now = float(data["now"])  # e.g. 329000 (원)
```

**NAVER_CODE_MAP**: 한글명 → 네이버 숫자 코드 = yfinance Symbol
| 한글명 | 네이버 코드 | yfinance Symbol |
|:-------|:----------:|:---------------:|
| 삼성전자 | 005930 | 005930.KS |
| SK하이닉스 | 000660 | 000660.KS |
| 삼성전기 | 009150 | 009150.KS |

### 3. 결정 검증
| 결정 | 성공 조건 | 상태 |
|:----:|:---------|:-----|
| BUY | 현재가 > 결정가 | win/loss |
| HOLD | 중립 (관찰만) | hold_monitor |
| SELL | 현재가 < 결정가 | win/loss |

### 4. 리포트 생성 (중복 제거)
- **KRW_DISPLAY_NAMES** — 삼성전자/SK하이닉스/삼성전기 → `₩` 표시
- `fmt_price(329000, "KRW")` → `₩32.9만`
- 성능 지표: 정확도, 평균 BUY 수익률, 평균 HOLD 관찰 수익률
- 종목별 최신 결정만 표시 (11회 반복 방지)

## 통합 포인트
| 대상 | 방식 | 파일 |
|:-----|:-----|:-----|
| 월간 성과 검증 | `collect_validation()` → LLM Section 5 | `monthly_performance_review.py` |
| 독립 실행 | `python3 src/agents/decision_validator.py` | stdout 리포트 |

## 주의사항
- **네이버 API는 Referer 헤더 필수** — 없으면 빈 응답
- **의존성**: `pip install yfinance` (US 주식용). 네이버는 stdlib만 사용
- **데이터가 축적되어야 의미 있음**
