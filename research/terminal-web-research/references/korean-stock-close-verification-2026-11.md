# 한국 종목 종가·지수 검증 패턴 (2026-11-05 실측)

> 목적: 일일 매크로/리포트 크론에서 **종가·등락률·주간수익률**을 확정할 때
> "어느 소스를 신뢰할 것인가"를 즉시 결정하기 위한 검증 패턴.
> 이전 문서(`korean-stock-market-data-sources.md`)에는 KOSPI/KOSDAQ을 Yahoo로만
> 얻는다고 적혀 있었으나 **2026-11-05에 Naver siseJson이 지수도 지원함을 확인** → 아래가 1순위.

## 1. Naver siseJson = 한국 개별주 + 지수 모두 1순위 (2026-11-05 확인)

```bash
# 개별주
curl -sL --max-time 15 \
 "https://api.finance.naver.com/siseJson.naver?symbol=005930&requestType=1&startTime=20261020&endTime=20261105&timeframe=day" \
 -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36" \
 -H "Referer: https://finance.naver.com/item/sise_day.naver?code=005930" \
 -o /tmp/sise.raw

# 지수도 같은 엔드포인트 (symbol=KOSPI / KOSDAQ) → 2026-11-05 실측 정상 동작
curl -sL --max-time 15 \
 "https://api.finance.naver.com/siseJson.naver?symbol=KOSPI&requestType=1&startTime=20261026&endTime=20261105&timeframe=day" \
 -H "User-Agent: Mozilla/5.0" -o /tmp/kospi.raw
```

필수 조건 3가지:
1. `Referer: https://finance.naver.com/item/sise_day.naver?code=<CODE>` 헤더 (없으면 빈 응답)
2. EUC-KR 인코딩 → `raw.decode('euc-kr', errors='ignore')`
3. `symbol=KOSPI` / `symbol=KOSDAQ` (문자열) — 숫자 `001`은 여전히 garbled

2026-11-05 실측:
```
KOSPI  rows 9 → 20261103 5648.79 / 20261104 5683.80 / 20261105 5383.80 → -5.28%
KOSDAQ rows 9 → 704.39 / 714.95 / 678.41 → -5.11%
```

> ⚠️ 이전 reference의 "KOSPI는 Yahoo `^KS11` (429) 뿐" 기록은 **부분적으로 폐기**.
> Yahoo는 여전히 429지만, siseJson이 KOSPI/KOSDAQ을 직접 준다 → Yahoo 의존 불필요.

## 2. 🚨 정규식 파싱 실패 — `rows 0` 함정 (가장 자주 나는 오류)

**실패 패턴(무조건 `rows 0`):**
```python
# ❌ 날짜가 JSON 문자열("20261105")일 때 + 공백/개행이 들어올 때 매칭 실패
re.findall(r'\[(\d{8}),([\d,\.]+),([\d,\.]+),([\d,\.]+),([\d,\.]+),(\d+),([\d\.]+)\]', txt)
```

**작동 패턴 (공백·따옴표·선택 소수부 허용):**
```python
rows = re.findall(
    r'\[\s*"?(\d{8})"?\s*,\s*([\d\.]+)\s*,\s*([\d\.]+)\s*,\s*([\d\.]+)\s*,'
    r'\s*([\d\.]+)\s*,\s*(\d+)\s*,\s*([\d\.]+)\s*\]', txt)
parsed = [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), int(r[5]), float(r[6]))
          for r in rows]
```
→ 행: `["20261105", 213000, 213500, 199800, 202500, 24263949, 46.06]`
  = 날짜, 시가, 고가, 저가, **종가**, 거래량, 외국인소진율

**디버그 규칙**: `rows == 0`이면 파싱 버그로 단정하지 말고 **원문 1KB를 먼저 출력**:
```bash
wc -c /tmp/sise.raw && head -c 400 /tmp/sise.raw | iconv -f euc-kr -t utf-8
```
원문이 정상인데 rows가 0이면 → 정규식 문제.

## 3. 주간수익률 기준일 — "5거래일 전"을 실제로 계산

`p[-1]`(오늘) `p[-2]`(전일)만으로는 주간수익률이 안 나온다.
기준 종가를 **명시적 날짜**로 잡아야 재현 가능하다:

```python
base_row = [x for x in p if x[0] == '20261029']   # 정확히 5거래일 전 날짜
base = base_row[0][4] if base_row else p[-6][4]
week_pct = (p[-1][4] - base) / base * 100
```
기준 날짜를 **리포트에 함께 적어라**(예: "주간 -12.15%(10/29 종가 230,500 기준)").
지나치게 느슨한 `p[-6]` fallback은 달력 공백(공휴일)에 어긋난다.

## 4. 하한가 도달 판정 — 라운딩 규칙 주의

KRX 하한가 = `round(prev_close * 0.85, -1)` (100원 단위 반올림).
2026-11-05 삼성전기: 전일 1,119,000 → `round(951150, -1)` = **951,000** → 종가 951,000 = **하한가 마감**.
→ 종가 == 하한가면 "하한가 마감"을 명시해야 함 (리포트의 임팩트 서술에 직접 반영).

## 5. 🚨 Naver Polling `cr` 부호가 뒤집힐 수 있다 (2026-11-05 실측)

```
polling 원자료 (삼성전자): 203000 218000 6.88 OPEN None
siseJson 확정 종가       : 202,500 (전일 221,500 → -8.58%)
```
Polling은 **장중 스냅샷**이고 `cr` 필드의 부호/기준이 확정 종가와 어긋난다
(상승으로 표시되었으나 실제로는 -8.58% 하락).
**HARD RULE (기존 문서와 동일, 증강):**
- 종가·등락률·주간수익률 → **siseJson만**
- Polling `cr`은 **방향 확인용으로 절대 사용 금지**, 뉴스 방향과 충돌하면 siseJson으로 재확인
- Polling `ms` 필드가 `CLOSE`일 때만 두 소스가 수렴

## 6. Stooq는 이제 JS PoW 게이트 (2026-11-05)

`https://stooq.com/q/d/l/?s=cl.f&i=d` 응답이 CSV가 아니라
`<noscript>This site requires JavaScript to verify your browser</noscript>` +
SHA-256 proof-of-work `<script>` 을 반환함.
→ 원유/금/지수 히스토리가 필요하면 **CNBC XML(지수·금리) + CNBC HTML embed(선물)** 로 대체.
Stooq를 기다리는 반복 재시도는 예산 낭비.

## 7. 선물은 CNBC HTML embed 우선 (기존 원칙 재확인)

2026-11-05 실측:
| 심볼 | XML `last` | HTML embed `last` | HTML `last_time` |
|:--|--:|--:|:--|
| `@CL.1` (WTI) | 88.69 | 88.63 | 2026-11-05T05:31:05-0500 |
| `@CL.2` (WTI 2월) | 87.53 | 87.53 | — |
| `@LCO.1` (Brent) | 96.16 | 96.07 | 2026-11-05T11:31:33+0100 |
| `@GC.1` (금) | 4,133.60 | 4,134.20 | 2026-11-05T05:31:34-0500 |

HTML embed 정규식: `"last":"..."`, `"change":"..."`, `"change_pct":"..."`, `"last_time":"..."`.
`last_time`이 KST 현재보다 미래면 → **"다음 거래일 예상" 라벨** (다음날로 넘어간 값임).

## 8. 🚨 "하루 급락"과 "전일 급락"을 분리 — 유가 서사 혼동 사례

2026-11-05 현장:
- 뉴스: "국제유가 8% 넘게 급락" (11/4 미국 세션 기준, WTI 8.29% 하락, 이란전 종식 기대)
- CNBC 현재값: `@CL.1` 88.63 / **+0.58%** (11/5亚洲세션 반등)

→ 리포트에 "오늘 유가 급락"으로 쓰면 **현재가와 모순**.
**규칙**: 유가 방향성은 ① 뉴스(직전 세션 events) ② 현재가(오늘 방향) ③ `previous_day_closing` 을
**분리해서** 각각 명시. "전일 -8.29% 급락 → 오늘 +0.58% 반등"처럼 양쪽을 함께 기술.

## 9. 🚨 최종 산출물은 검증이 끝난 뒤에만 저장 (작업 순서 규칙)

2026-11-05 실제 사고: 초안 수치(폴링 기반 종목 등락률, "오늘 유가 8% 하락" 서사)로
`macro_context.json`을 **먼저 저장** → 이후 siseJson 검증에서 값이 전부 달라짐
(삼성전자 -8.35% → -8.58%, 삼성전기 -14.48% → -15.01%, HD현대일렉트릭 -9.88% → -10.21%).
**저장 파일은 18:35 파이프라인이 즉시 읽으므로, 검증 전 저장 = 오염 전파.**

**강제 순서**:
```
1. 데이터 수집 (개별/지수/선물/뉴스 모두)
2. 원자료 → 파싱 → /tmp/*.json 로 캐시
3. 교차 검증 (2개 소스 비교, siseJson vs Polling, CNBC vs 뉴스)
4. 검증된 값으로 리포트 본문 작성
5. 본문 QA (CJK/한영혼합/숫자 재확인)
6. → 그 다음에 두 경로 저장 + timestamp assert + cp
7. Discord 전송 (본문이 확정된 뒤)
```
"일단 저장해 두고 나중에 고치기"는 파이프라인이 18:35에 읽으므로 **금지**.
