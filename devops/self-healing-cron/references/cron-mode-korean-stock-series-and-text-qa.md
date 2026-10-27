# 한국 개별주 일별 시계열 + 텍스트 오염 QA (cron 모드)

**발견일**: 2026-10-26 18:40 KST (cron `b96583fa9d27` 18:30 매크로 리포트 실행 중)
**상태**: ✅ 검증 완료 (삼성전자·SK하이닉스·삼성전기·현대차·에이피알·HD현대일렉트릭 6종목)
**목적**: (1) 종가/주간수익률/외국인 소진율을权威하게 수집 (2) 저장된 한국어 리포트의 CJK 혼입 오염 탐지

---

## 1. 🚨 가장 중요한 교훈 — Polling API는 장중/종가 구분을 못 한다

2026-10-26 15:33 KST (장 마감 직후) 실측:

| 종목 | Polling API (`ms='OPEN'`) | siseJson (확정 종가) | 차이 |
|:--|:--|:--|:--|
| 삼성전자 | 214,000 / `cr=+0.70` | 214,000 / **+0.23%** | 변화율 **3배 차이** |
| HD현대일렉트릭 | 445,000 / `cr=+5.32` | 444,000 / **-4.82%** | **방향까지 반대** |

**원인**: Polling API의 `cr`(전일비율)은 실시간 스냅샷 기준이라, `ms='OPEN'` 상태에서는
장중/직전 스냅샷과 확정 종가가 섞인다. `pcv`도 실시간 기준이라 어긋난다.

**규칙 (HARD)**:
- **종가·일변동률·주간수익률 → 반드시 `siseJson`** (확정 종가)
- **Polling API는 실시간 스냅샷(盘中 모멘텀) 용도**에만 사용
- `ms == 'CLOSE'`인 경우에만 Polling 값과 siseJson이 일치
- 리포트에 "종가"를 쓸 때는 Polling 값을 쓰지 말 것 → 방향/크기 오류 propagates

---

## 2. Naver 일별 시계열 API — siseJson (권장, 1순위)

### Endpoint
```
https://api.finance.naver.com/siseJson.naver?symbol={6자리}&requestType=1&startTime=YYYYMMDD&endTime=YYYYMMDD&timeframe=day
```

### 필수 헤더
```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
curl -sL --max-time 12 "https://api.finance.naver.com/siseJson.naver?symbol=005930&requestType=1&startTime=20261013&endTime=20261026&timeframe=day" \
  -H "User-Agent: $UA" \
  -H "Referer: https://finance.naver.com/item/sise_day.naver?code=005930" \
  -o /tmp/sise_005930.txt
```
- `Referer` 없으면 빈 응답 → **가장 흔한 함정**
- 응답 인코딩 **EUC-KR**

### 응답 형식
```json
[['날짜','시가','고가','저가','종가','거래량','외국인소진율'],
 ["20261026", 213500, 216000, 211500, 214000, 11190302, 46.11],
 ["20261023", 206000, 215500, 203500, 213500, 16145972, 46.11]]
```
(헤더 행은 문자열 배열, 데이터 행은 정수/실수 배열)

### 파싱 (write_file로 저장 후 실행 — pipe-to-interpreter 차단 회피)
```python
import urllib.request, re, json, time
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
CODES = {'삼성전자':'005930','SK하이닉스':'000660','삼성전기':'009150',
         '현대차':'005380','에이피알':'278470','HD현대일렉트릭':'267260'}

def fetch_series(code):
    url = (f'https://api.finance.naver.com/siseJson.naver?symbol={code}&requestType=1'
           f'&startTime=20261013&endTime=20261026&timeframe=day')
    req = urllib.request.Request(
        url, headers={'User-Agent': UA,
                      'Referer': f'https://finance.naver.com/item/sise_day.naver?code={code}'})
    txt = urllib.request.urlopen(req, timeout=12).read().decode('euc-kr', errors='ignore')
    rows = []
    for m in re.finditer(r'\["(\d{8})",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\]', txt):
        rows.append({'date': m.group(1), 'open': int(m.group(2)), 'high': int(m.group(3)),
                     'low': int(m.group(4)), 'close': int(m.group(5)),
                     'vol': int(m.group(6)), 'foreign_retention': float(m.group(7))})
    return rows

out = {}
for nm, c in CODES.items():
    try:
        rows = fetch_series(c)
        last, prev, first = rows[-1], rows[-2], rows[0]
        out[nm] = {
            'code': c,
            'close': last['close'],
            'prev_close': prev['close'],
            'chg_pct': round((last['close'] - prev['close']) / prev['close'] * 100, 2),
            'week_pct': round((last['close'] - first['close']) / first['close'] * 100, 2),
            'foreign_retention': last['foreign_retention'],   # 외국인 소진율(%)
            'series': [(r['date'], r['close']) for r in rows],
        }
    except Exception as e:
        out[nm] = {'code': c, 'error': str(e)}
    time.sleep(0.4)
print(json.dumps(out, ensure_ascii=False, indent=1))
```

### 얻는 값
| 값 | 용도 |
|:--|:--|
| 확정 종가 | 리포트 "종가" |
| 일변동률 (직전 거래일 대비) | Priority Matrix |
| **주간수익률** (기간 첫 거래일 대비) | "주간 -8.55%" 등 추세 지표 |
| **외국인 소진율 (`foreign_retention`)** | 외국인 수급 추세 — 지수 방향의 선행 설명 |
| 시가/고가/저가/거래량 | 변동성·유동성 판단 |

### 2026-10-26 실측 (기준: 전일 10/23 종가)
| 종목 | 코드 | 종가 | 일변동 | 주간 | 외국인소진율 |
|:--|:--|--:|--:|--:|--:|
| 삼성전자 | 005930 | 214,000 | +0.23% | -8.55% | 46.11 |
| SK하이닉스 | 000660 | 1,291,000 | +2.22% | -11.33% | 48.69 |
| 삼성전기 | 009150 | 1,119,000 | +0.72% | -18.97% | 36.36 |
| 현대차 | 005380 | 288,500 | -1.54% | -7.38% | 24.09 |
| 에이피알 | 278470 | 279,000 | -1.24% | -2.28% | 39.10 |
| HD현대일렉트릭 | 267260 | 444,000 | -4.82% | -20.57% | 33.45 |

> ⚠️ **주간수익률 계산 기준 주의**: `rows[0]`은 조회 시작일의 거래일 종가. 시작일을 바꾸면
> "주간" 수치가 달라진다 → 리포트에는 기준 기간을 명시하거나, 항상 직전 N거래일로 고정.

---

## 3. Naver 차트 API (`api.stock.naver.com`) — 보조, 사용 시 함정 2개

```
https://api.stock.naver.com/chart/domestic/item/{code}?periodType=day&rangeType=days&startDateTime=YYYYMMDDHHMM&endDateTime=YYYYMMDDHHMM
```
- 헤더: `User-Agent` + `Referer: https://m.stock.naver.com/`
- 응답 키는 **`priceInfos`** (가 아님, `priceBlocks`로 접근하면 KeyError)
- `startDateTime` 포맷은 **콜론 없이** `202610190000` — 콜론 넣으면 날짜 범위가 무시되고
  최근 ~3개월치 전체가 반환됨
- 각 row: `localDate`, `openPrice`, `highPrice`, `lowPrice`, `closePrice`,
  `accumulatedTradingVolume`, `foreignRetentionRate`
- **우선순위**: siseJson이 더 단순·신뢰 높음. 이 API는 캔들 OHLCV가 필요할 때만.

---

## 4. Bloomberg Terminal 대용 — CNBC XML 추가 심볼

2026-10-26 신규 검증:
| 심볼 | 대상 | 실측 |
|:--|:--|:--|
| `@LCO.1` | **ICE Brent Crude (Dec'26)** | last 115.08 / pdc 116.72 / change_pct -1.41% |
| `@GC.1` | Gold COMEX (Dec'26) | last 4,030.10 / pdc 4,007.90 / +0.55% |

- 브렌트도 **XML API가 정상 지원** (`@LCO.1`) — 이전에 "CNBC는 Brent 미지원"으로 기록한 내용이 있으면 폐기.
- 선물은 기존 규칙 그대로: **HTML embed 우선**(intraday 반영), XML은 전일종가 확인용.
  - 10/26 실측 @CL.1: XML `last=101.24 / pdc=103.27` vs HTML `last=101.35 / change=-1.92 / -1.86%`
    → HTML 값이 실시간, XML `pdc`가 전일 종가
- `@LCO.1` XML의 `last_time`은 `+0100` (영국 시간) → KST 변환 주의.

---

## 5. 🚨 BLS period 키는 `M09` 형식 — `'09'`로 조회하면 KeyError

BLS Public API v2 응답의 `period` 값은 **`"M09"`** (문자 M 접두). `"09"`로 dict를 인덱싱하면
`KeyError('2026','09')` → YoY 계산이 조용히 실패하거나 NameError로 튕긴다.

```python
d = json.load(open('/tmp/bls.json'))
m = {(r['year'], r['period']): r['value']
     for r in d['Results']['series'][0]['data']}

def yoy(year, month):          # month: 'M09' 등
    cur = float(m[(str(year), month)])
    prev = float(m[(str(year - 1), month)])
    return round((cur / prev - 1) * 100, 2)

yoy(2026, 'M07')   # 3.36
yoy(2026, 'M08')   # 3.40
yoy(2026, 'M09')   # 3.74
```
- 결측값 `'-'`이 섞임 → `float()` 변환은 try/except 필수
- 헤더 행/메타데이터 혼재 → `d['Results']['series'][0]['data']`만 사용

---

## 6. 🧪 저장된 한국어 리포트 텍스트 오염 QA (CJK 혼입)

LLM이 긴 한국어 리포트를 생성하면 **중국어/일본어 토큰이 섞여 저장**되는 사례가 반복됨.
2026-10-26 실제 발생 (한 번에 5개 이상):
`ELP`(思考 잔재), `投기`(投机), `累`(累计), `本月`, `回落`, `widgets`, `Kombini`,
`交易`, `头上的`, `ELP(ELP)는` 등.

### 탐지 (한글 리포트에 CJK 한자 → 무조건 오염)
```python
import re
s = d['macro_report_summary']
cjk = re.findall(r'[一-鿿]', s)      # 漢字 유니코드 범위
print(len(cjk))                      # 0 이 아니면 오염
for m in re.finditer(r'[一-鿿]+', s):
    print(repr(s[max(0, m.start()-40):m.end()+40]))
```
- `[一-鿿]` = CJK 통합 한자. 한국어 한글은 `[가-힣]`이므로 겹치지 않음.
- **정규식 `[가-힣]`로 검색하면 조용히 통과한다** → 반드시 한자 범위로 검사.
- 기존의 고정 BAD 토큰 리스트(`['wyn','Dd','ipuiae','定义','名词',...]`)는
  **무작위 문자열일 뿐이라 매번 다른 오염을 못 잡는다** → CJK 범위 검사가 본체.

### 수정 원칙
1. **일괄 replace ❌** → 다른 문맥을 망가뜨림 (예: `投机` → `투기` 치환 시
   `가장 커투기적` 처럼 띄어쓰기가 깨진 문자열 생성 → 또 다른 결함)
2. **항목 단위 재작성** — 문장 전체를 정상 한국어로 다시 쓰는 것이 가장 안전
3. 수정 스크립트는 `write_file`로 별도 .py 저장 후 실행 (heredoc + 이모지/특수문자 차단 회피)
4. 저장 → **재로드 → 검증** 순서로 반복 (저장 직후 검증 아니면 옛 값이 남음)

### 최종 검증 루프 (저장 스크립트에 내장)
```python
a = json.load(open(SRC, encoding='utf-8'))
b = json.load(open(DST, encoding='utf-8'))
assert a['timestamp'] == b['timestamp']
assert len(re.findall(r'[一-鿿]', a['macro_report_summary'])) == 0
for n in a['news_items']:
    assert n['title'] and n['summary'] and n['url']
```
→ 두 저장 경로(trading-agents-nuri / trade-pipeline) timestamp 일치 확인까지 자동화.

---

## 7. 이 reference의 우선순위 요약

| 목적 | 1순위 소스 | 2순위 |
|:--|:--|:--|
| 한국개별주 종가/등락률 | **Naver siseJson** | Polling(실시간 전용) |
| 주간수익률 | Naver siseJson | Polling ❌ |
| 외국인 소진율 | Naver siseJson | Naver chart API `foreignRetentionRate` |
| 글로벌 지수/금리 | CNBC XML | — |
| 원유/금 선물 | CNBC HTML embed | CNBC XML(전일종가 확인용) |
| CPI YoY | BLS API (`M09` 형식) | — |
| 환율 | open.er-api.com | — |

## 8. 변경 이력

- **2026-10-26 (v1)**: 최초 작성. siseJson 일별시계열 API 발견·검증(6종목),
  Polling vs 확정종가 불일치 함정 문서화, CNBC `@LCO.1` 브렌트 XML 검증,
  BLS `M09` period 형식 명시, CJK 혼입 QA 정규화.
