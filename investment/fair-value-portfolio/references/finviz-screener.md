# Finviz Screener Reference (2026-06-23)

## 스크립트
- **경로**: `~/trade-pipeline/scripts/finviz_screener.py`
- **실행**: `cd ~/trade-pipeline && python3 scripts/finviz_screener.py`
- **설치 의존성**: `~/.hermes/hermes-agent/venv/bin/python3 -m pip install finvizfinance`

## 자동퇴출 (auto_expel)
- **경로**: `~/trade-pipeline/scripts/auto_expel.py`
- **실행**: `cd ~/trade-pipeline && python3 scripts/auto_expel.py`
- **동작**: `data/daily_snapshot.json` 읽어 gap_T1 < -50% 종목 watchlist에서 제거
- **이름 매핑**: `daily_snapshot.json`의 `name`(한글명) → `watchlist.json`의 `name` → `ticker`
- **2026-06-23 실행**: 삼성전기(-64.9%), GEV(-66.9%) 제거 (37→35)

## 크론
- **job_id**: `d92ed6044d32`
- **이름**: 주간 스크리너 + 자동퇴출
- **스케줄**: `0 6 * * 1` (매주 월 06:00 UTC+8 = 07:00 KST)
- **방식**: no_agent script (`weekly_screener.sh` → auto_expel + finviz_screener 순차 실행)
- **전송**: origin (현재 채널로 자동 전송)

## 설계 결정

### 왜 적정가를 포함하지 않았나?
사용자 지시: "적저가 구하는건 기존거 활용해 코드 변형하지 말고"
→ 스크리너는 발굴만. 편입 후보가 나오면 watchlist에 추가하고 기존 fair_value.py로 평가.
**핵심 규칙**: 기존 fair_value.py 절대 수정 금지 — 수정 없이 재사용만.
편입은 사용자(너구리) 허락 시에만.

### 가속 조건의 의미
사용자: "물렸을때 미래성장성을 보고 안심하기 위함"
→ FPE < PE = 실적이 가속 중이라는 신호. PER이 높아도 FPE가 낮으면 내년 EPS 급증 예상.
편입 검토 시 이 조건 확인하고 안심.

### EPS 가속도 = Next Y% - This Y%
사용자: "다음분기랑 다음해 gap차이로 sorting"
- EPS This Y (올해 EPS 성장률) — "EPS next Q" 개념
- EPS Next Y (내년 EPS 성장률)
- 가속도(+) = 내년이 올해보다 더 빠르게 성장 → 가장 관심있는 후보
- Sort: 가속도 내림차순 (상위 30 표시)

## 데이터 소스
- **Valuation screener columns**: Ticker, Market Cap, P/E, Forward P/E, PEG, P/S, P/B, EPS This Y, EPS Next Y, EPS Past 5Y, EPS Next 5Y, Price, Change, Volume
- **Financial screener columns**: Ticker, ROE, Debt/Eq, ROA, ROIC, Gross M, Oper M, Profit M
- **ROE 변환**: Financial screener ROE는 소수(0.2133=21.33%). `merged['ROE_raw'].median() < 5`면 ×100

## 테스트 결과 (2026-06-23)
- 49종목 필터 통과 → 46종목 가속조건 통과 (94%)
- 가속도 상위: TBBK(+16.4%), BTG(+15.6%), FSLR(+11.5%)
- 초강세(FPE<PE/2): BTG, YOU, TOST, HMY, ONON, SGHC, STLD, CENX
- MSFT도 포함 (PE 21.9 → FPE 18.9, ROE 34%)
