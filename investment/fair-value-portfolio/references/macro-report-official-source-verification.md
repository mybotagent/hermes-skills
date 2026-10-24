# 매크로 리포트 — 공식 소스 교차검증 + 텍스트 QA (2026-10-21 신규)

> 18:30 매크로 전략 리포트 cron에서 검증 완료한 패턴.
> 핵심 원칙: **전일 리포트의 값을 믿지 말고, 공식 기관 API로 다시 뽑는다.**
> 그리고 **저장 전 저장된 텍스트 자체를 검사한다.**

---

## 1. 왜 필요한가 — 실제 사례 (2026-10-21)

전일(10/20) `macro_context.json`에 아래 값이 들어있었다:

| 필드 | 전일 리포트 값 | 실제 (2026-10-21 검증) | 판정 |
|:--|:--|:--|:--|
| Fed Funds | `4.25~4.50%` | **3.75~4.00%** (EFFR 3.88%) | ❌ 틀림 |
| US CPI YoY | `2.9%` | **3.74%** (9월, BLS SA) | ❌ 틀림 |
| USD/KRW | 1330.79 | 1325.2 (4거래일 연저점) | ⚠️ 소폭 차이 |
| WTI | $100.71 | $99.93~100.07 | ⚠️ intraday 변동 |

→ 리포트 2연속 틀린 값이 "기억"으로 순식간에 전파됐음. **이전 파일은 참고용일 뿐 재검증 대상**이다.

**대응**: 전일 리포트 값과 공식 API 값이 다르면 **리포트에 정정 사실을 명시**한다
(숨기면 다음날 또 틀린 값이 재사용된다).

---

## 2. 공식 소스 1 — NY Fed Rates API (Fed Funds / SOFR)

무료, 키 불필요, **기준금리·목표범위까지 제공** (가장 권위 있는 1차 소스).

```bash
# EFFR (effective federal funds rate) — 마지막 1건
curl -s --max-time 15 "https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json" \
  -H "User-Agent: Mozilla/5.0"
# → {"refRates":[{"effectiveDate":"2026-10-19","percentRate":3.88,
#                 "targetRateFrom":3.75,"targetRateTo":4.0, ...}]}

# SOFR
curl -s --max-time 15 "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json" \
  -H "User-Agent: Mozilla/5.0"
# → percentRate 3.87

# 기간 조회 (금리 경로 확인용)
curl -s --max-time 15 \
 "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate=2026-08-01&endDate=2026-10-21" \
 -H "User-Agent: Mozilla/5.0"
```

- **`targetRateFrom`~`targetRateTo` = 연준 목표금리 범위** → 리포트 `fed_rate` 필드의 정답
- `percentRate` = 실제 거래금리(EFFR)
- 직전 리포트의 `fed_rate`가 이 값과 다르면 **반드시 정정 표기**
- 과거 값과 비교해 경로(동결/인상) 파악 가능 (search.json)

---

## 3. 공식 소스 2 — BLS Public API v2 (US CPI)

키 불필요(무료 tier는 한도 내), **CPI 원계열 SA 인덱스**를 직접 주므로 YoY를 정확히 계산 가능.

```bash
curl -s --max-time 15 \
 "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0?startyear=2024&endyear=2026" \
 -H "Content-Type: application/json" -o /tmp/bls.json
```

```python
import json
d = json.load(open('/tmp/bls.json'))
data = {}
for x in d['Results']['series'][0]['data']:
    try:
        data[(x['year'], x['period'])] = float(x['value'])
    except ValueError:
        pass          # ← 일부 기간에 '-' (결측) 값이 있어 float 변환 실패 → 반드시 try/except
for p in ['M07','M08','M09','M10']:
    a, b = data.get(('2025', p)), data.get(('2026', p))
    if a and b:
        print(p, 'YoY: %.2f%%' % ((b/a - 1) * 100))
```

**2026-10-21 실측**: 7월 3.36% → 8월 3.40% → **9월 3.74%** (재상승 전환)
→ "인플레이션 재점화" 논거의 정량 근거. 뉴스("美 9월 CPI 3.7%")와 일치 확인.

**주의**
- `M10`(10월)은 아직 발표 전 → 결측. 결측을 0으로 취급하지 말 것.
- `fred.stlouisfed.org/graph/fredgraph.csv`는 이 환경에서 빈 응답 → BLS API를 1순위로 사용.
- `api.bls.gov` 응답에 `'-'` 값이 섞임 → `float()` 변환 예외 처리 필수.

---

## 4. 선물/지수 수치 — CNBC XML vs CNBC HTML 병행

| 대상 | XML API (`quote.cnbc.com/...`) | HTML (`www.cnbc.com/quotes/{sym}`) |
|:--|:--|:--|
| `.SPX`, `.DJI`, `.IXIC`, `.KS11`, `.KQ11`, `.VIX`, `.DXY`, `US10Y`, **`US30Y`** | ✅ `last`/`previous_day_closing`/`change`/`change_pct` | ❌ HTML은 2MB React 보일러플레이트 |
| `@CL.1` (WTI 선물), `@GC.1` (금) | ⚠️ `last`는 있으나 `previous_day_closing`이 **장 마감 스냅샷**이라 intraday 반영이 늦음 | ✅ `last`/`change`/`change_pct`/`open`/`high`/`low`/`last_time` 모두 정확 |

**2026-10-22 신규 검증 — US 지수 3종 + 30년물**:
- `US30Y` → `<last>5.375</last>`, `<previous_day_closing>5.437</previous_day_closing>` — **CNBC가 30년물을 지원한다** (이전 가이드의 "CNBC 미지원"은 오류). 같은 날 Yahoo `^TYX`는 **빈 응답**(JSON 파싱 실패) → Yahoo fallback 약화.
- `.DJI` → 52,856.09 / `.IXIC` → 26,702.858 — 둘 다 XML 정상.
- **`.SPX`/`.DJI`/`.IXIC`는 `previous_day_closing == last` quirk**: 미국 장 마감 후 CNBC가 `pdc`를 `last` 스냅샷으로 반환하고 `change`만 실제 전일 대비 값을 준다.
  → **실제 전일 종가 = `last - change`** 로 역산해야 한다.
  실측: S&P `7,757.17 - 44.60 = 7,712.57` / 다우 `52,856.09 - 360.21 = 52,495.88` / 나스닥 `26,702.858 - 278.041 = 26,424.82`.
  → 리포트 본문/JSON의 "전일 종가" 표기에 이 역산값을 쓸 것 (Pitfall 56의 streak/레벨 교차검증과 직결).

**2026-10-21 실측**: 같은 @CL.1에 대해 XML `last=100.07`, HTML `last=99.93` / `change=+2.11` / `change_pct=+2.16%` / `last_time=2026-10-21T06:24:39-0400`.

→ **선물은 HTML embed 값을 우선**, XML은 전일 종가(`previous_day_closing=97.82`) 확인용.

```bash
curl -sL --max-time 15 "https://www.cnbc.com/quotes/@CL.1" -H "User-Agent: $UA" -o /tmp/cl.html
python3 -c "
import re
h=open('/tmp/cl.html',encoding='utf-8',errors='ignore').read()
for k in ['last','change','change_pct','open','high','low','last_time','name']:
    m=re.search(r'\"%s\":\"?([^\",}]+)'%k,h); print(k, m.group(1) if m else None)
"
```

**기존 규칙 유지**: 복수 심볼 1회 요청 금지(`.SPX,.KS11` → `<code>1</code>` 에러). 심볼당 1회 + sleep 1.

**펀더스 기준일 표기**: `last_time`이 KST 기준 현재보다 미래면(장 마감 후 다음 세션 선반영) → "다음 거래일 예상" 라벨 (Pitfall 61과 동일 원칙).

---

## 4b. 🔴 뉴스 URL을 손으로 쓰지 말 것 — RSS에서 그대로 추출 (2026-10-22 신규)

**문제**: `news_items[].url`을 리포트 본문에서 손으로 옮기다 보면 **URL이 중간에서 잘린다**.
2026-10-22 실측: 한국어 뉴스 12건의 URL을 손으로 복사하는 과정에서 여러 건이 100~200자에서 truncate → `https://news.google.com/rss/articles/CBMiZ0FVX3lxTE9heVVlbmp3S2h4Ty1NSDZXRGY0anNlNXhZbExBdnprZl9mR2tCV1V4c0ZWQTJ4emc0VnNRY0NpaWJ5VlNUUXJVeTNuRTNZR2xLaUdmSmJYb19QWXVLSjdzYU83YnFtSlU?oc=5` 형태가 `...KSjdzYU83YnFtSlU?oc=5` 처럼 잘려 들어감.

**원인**: Google News RSS의 `<link>`는 200~400자짜리 base64 토큰. 눈으로 옮기기엔 길고, 편집 과정에서 잘릴 확률 높음. **저장 후 검증하면 그때야 발견** → JSON에 깨진 URL이 남고 하위 파이프라인(파이프라인 Phase 0.5 뉴스 수집)이 404를 받는다.

**해법 — 2단계 분리**:
1. **탐색 단계**: Google News RSS를 검색해 제목/요약을 먼저 확보 (URL 없이).
2. **수집 단계**: 저장 직전에 **RSS에서 제목을 key로 매칭해 URL을 자동 추출**하고 JSON에 주입.

```python
# 1) 제목 매칭용 링크 수집 (write_file로 .py 저장 → terminal 실행)
def rss(q, n=8):
    url = 'https://news.google.com/rss/search?q=%s&hl=ko&gl=KR&ceid=KR:ko' % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    data = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
    out = []
    for it in re.findall(r'<item>(.*?)</item>', data, re.S)[:n]:
        t = re.search(r'<title>(.*?)</title>', it, re.S)
        l = re.search(r'<link>(.*?)</link>', it, re.S)
        s = re.search(r'<source[^>]*>(.*?)</source>', it, re.S)
        if t and l:
            out.append({'title': t.group(1), 'link': l.group(1), 'source': s.group(1) if s else ''})
    return out

found = {}
for q, key in WANT:          # WANT = [(검색어, 제목 매칭 키), ...]
    for it in rss(q, 8):
        if key in it['title']:
            found[key] = it
            break
json.dump(found, open('/tmp/links.json', 'w'), ensure_ascii=False, indent=2)

# 2) 저장 스크립트에서 URL 주입 + 검증
news_items = []
for key, title, summ in NEWS:
    link = found[key]['link']          # ← 손으로 쓴 URL이 아니라 자동 추출값
    news_items.append({"title": title, "summary": summ, "url": link, "source": "web_search"})

# 3) 저장 직후 URL 무결성 assert (Pitfall 63의 텍스트 QA와 같은 시점에)
for n in news_items:
    assert n['url'].startswith('https://news.google.com/rss/articles/'), n['url']
    assert n['url'].endswith('?oc=5') and len(n['url']) > 120, n['url']
```

**검증 assert 2개가 핵심**:
- `startswith('https://news.google.com/rss/articles/')` — 스킴/경로 잘림 방지
- `endswith('?oc=5') and len(url) > 120` — **후반부 truncation 방지** (Google News 링크는 항상 `?oc=5`로 끝남)

**원칙**: `news_items[].url`은 **사람이 옮기지 않는다**. RSS → dict → JSON 자동 주입. 손으로 쓴 URL은 어차피 거의 틀린다.

---

## 5. 환율 — exchangerate-api.com

```bash
curl -s --max-time 15 "https://api.exchangerate-api.com/v4/latest/USD" -o /tmp/fx.json
# rates: KRW 1327.17, JPY 158.22, EUR 0.891, CNY 6.69
```

- `open.er-api.com`도 가능하나 **exchangerate-api.com이 더 안정**
- News RSS에서 실제 장 마감 환율(예: "원/달러 4거래일 연속 연저점 1,325.2원")과 교차 확인 → 리포트에는 뉴스 확정치 우선 표기

---

## 6. 한국 종목 코드 — 확정 매핑 (2026-10-21 재검증)

| 종목 | 코드 | Naver `nm` 확인 | 2026-10-21 종가 |
|:--|:--|:--|--:|
| 삼성전자 | 005930 | 삼성전자 | 223,000 (+5.44%) |
| SK하이닉스 | 000660 | SK하이닉스 | 1,285,000 (+5.07%) |
| 삼성전기 | 009150 | 삼성전기 | 1,168,000 (+1.13%) |
| 현대차 | 005380 | 현대차 | 309,000 (-0.32%) |
| 에이피알 | **278470** | 에이피알 | 316,500 (+2.10%) |
| HD현대일렉트릭 | **267260** | HD현대일렉트릭 | 498,500 (+2.26%) |

- ❌ 278470 ≠ 267270 (`nm=HD건설기계`, 다른 회사)
- ❌ 054050 ≠ HD현대일렉트릭 (prev 리포트 표기 오기)
- Pitfall 26d에 따라 매번 `nm` 교차검증을 한다.

**`ms` 필드 의미**: `OPEN` = 장중(한국장), `CLOSE` = 마감. `ms=OPEN`일 때 `pcv`는 전일 종가 → `(nv-pcv)/pcv*100`이 올바른 등락률.

---

## 7. 🔴 저장 전 텍스트 QA — 한국어 토큰 손상 검사 (2026-10-21 신규)

긴 한국어 요약을 LLM이 생성해 JSON에 저장할 때, **한자/영문 혼입 토큰이 깨져 저장되는 사례**가 발생했다.

실제 손상 예시 (수정 전):
```
"민·관·정서 일제히wynDd불"     ← "일제히 지적하며"
"주가가 실적 개선 못 따라감'ipuiae 목표가"  ← "이라"
"定义선 회장"                    ← "정의선 회장"
"名词 금리"                       ← "명목 금리"
"소진에서come."                   ← "소진에서 온 것이고"
```

**원인**: 저자성이 높은 장문 한국어 생성에서 가끔 인코딩/토큰 경계 붕괴 발생. 저장 후에만 드러남.

**QA 절차 (저장 직후 필수)**:
```python
import json, re
d = json.load(open(path))
BAD = ['wyn','Dd','ipuiae','定义','名词','cend','come','Dd']
for n in d['news_items']:
    assert not any(b in n['summary'] for b in BAD), n['summary']
assert not any(b in d['macro_report_summary'] for b in BAD)
```

**조치**: 손상된 summary만 해당 항목의 title로 특정 → 손상 텍스트를 정상 한국어로 **명시적으로 다시 작성**(일괄 replace 말고 항목 단위 교체).

**원칙**: 리포트 본문은 `write_file`로 만든 `.py` 스크립트에서 `json.dump`으로 저장하고, 저장 직후 **읽어와서 검사**한다. 수동 편집은 손상 재발 위험.

---

## 8. 데이터 이중 저장 (Pitfall 22b 재확인)

18:30 매크로 cron은 `macro_context.json`을 **두 경로 모두**에 저장해야 한다:
- `~/trading-agents-nuri/data/macro_context.json`
- `~/trade-pipeline/data/macro_context.json` (18:35 pipeline.py가 읽는 경로)

한쪽만 저장하면 18:35 LangGraph Phase 0.5/2/3이 매크로 데이터를 못 읽는다 → 조용한 실패.

---

## 9. 체크리스트 (18:30 매크로 cron)

1. 전일 `macro_context.json` 값은 **재검증 대상** (신뢰 불가)
2. Fed Funds → NY Fed EFFR (`targetRateFrom/To`)
3. CPI → BLS `CUUR0000SA0` YoY 직접 계산 (`-` 결측 try/except)
4. 지수/금리/DXY → CNBC XML (심볼당 1회) — `.SPX` `.DJI` `.IXIC` `.KS11` `.KQ11` `.VIX` `.DXY` `US10Y` `US30Y`
5. 선물(WTI/금) → CNBC **HTML embed** 우선, XML은 전일 종가 확인
6. 환율 → exchangerate-api + News RSS 확정치
7. 한국 6종목 → Naver Polling + `nm` 교차검증 (코드 하드코딩 금지)
8. 뉴스 → Google News RSS (한국어 + 영어 병행, Pitfall 57)
9. **뉴스 URL은 RSS에서 자동 추출해 주입** — 손으로 옮기지 말 것 (절 4b)
10. 전일 값과 다르면 **정정 사실을 리포트에 명시**
11. 저장 → **읽어와서 손상 토큰 검사 + URL 무결성 assert** → 이상 시 항목 단위 재작성
12. 두 경로에 저장 + `.bak_YYYYMMDD` 백업
13. **CJK 정규식 스캔** (`[\u4e00-\u9fff]`)으로 한국어 문장 손상 검사 (title 제외, summary/report만) — 절 13
14. 한국 6종목 등락률은 **`(nv-pcv)/pcv*100` 직접 계산** — `cr`/`ms` 필드는 참고용 (절 12)
15. **Stagflation 분류 시 실업률(BLS `LNS14000000`) + PPI(BLS `WPSFD4`) + 브렌트(`@LCO.1`) 포함** (절 11)

---

## 10. 🔴 US 지수 "전일 종가" 표기 — `last - change` 역산 (2026-10-22 신규)

CNBC XML은 미국 장 마감 후 `previous_day_closing`(=pdc)을 `last`와 동일하게 스냅샷 반환한다.
따라서 리포트에서 **전일 종가**를 표기하려면:

```
전일 종가 = last - change
```

실측 (2026-10-22, 10/21 세션):
| 심볼 | last | change | 전일 종가(역산) |
|:--|--:|--:|--:|
| .SPX | 7,757.17 | +44.60 | **7,712.57** |
| .DJI | 52,856.09 | +360.21 | **52,495.88** |
| .IXIC | 26,702.858 | +278.041 | **26,424.82** |

- 전일 리포트의 `sp500` 값과 일치해야 한다 → 불일치 시 **pdc quirk 적용 여부를 의심**하고, 한국 지수처럼 pdc가 정상인 `.KS11`/`.KQ11`과 교차 확인.
- 한국 지수(.KS11/.KQ11)는 pdc가 정상 반환 → 이 역산은 **미국 심볼에만** 적용.
- 🔗 Pitfall 56(연속 기록/레벨 표현 cross-check)과 직결: "3일째 급등락", "전일 대비" 같은 표현을 쓸 때 이 역산값이 기준값.

**2026-10-23 실측 (10/22 세션)**: `.SPX` last=7,663.43 / change=-93.74 → 전일종가 역산 **7,757.17** = 전일(10/21) 리포트 `sp500` 값과 **정확히 일치** ✅ → pdc quirk 적용 확인. 다우 52,867.98-11.89=52,856.09 / 나스닥 26,008.859-(-693.999)=**26,702.86** = 전일 리포트 `nasdaq` 값과 일치 ✅.

---

## 11. 추가 공식 지표 — 실업률(BLS) / PPI(BLS) / 브렌트(CNBC) (2026-10-23 신규 검증)

### 11.1 미국 실업률 — BLS `LNS14000000`

```bash
curl -s --max-time 15 \
 "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000?startyear=2025&endyear=2026" \
 -H "Content-Type: application/json" -o /tmp/unemp.json
```

2026-10-23 실측: `2026 M09 = 4.2` (8월 4.1, 6월 4.2, 5월 4.3, 2월 4.4).
→ **"물가 재상승 + 고용 개선" = 스태그플레이션** 국면 분류의 정량 근거. CPI만으로는 "Slowdown"과 구분 불가 — 실업률을 반드시 같이 넣을 것.

### 11.2 PPI — BLS `WPSFD4` (원계열 인덱스)

```bash
curl -s --max-time 15 \
 "https://api.bls.gov/publicAPI/v2/timeseries/data/WPSFD4?startyear=2025&endyear=2026" \
 -H "Content-Type: application/json" -o /tmp/ppi.json
```

2026-10-23 실측: 2026-09 = **159.780** (8월 157.662, 7월 156.924, 6월 156.683) → 사상 최고권.
→ 유가 → PPI → CPI **전가 경로**의 중간 단계를 수치로 보여줄 때 사용.

### 11.3 브렌트유 — CNBC XML `@LCO.1`

`@CL.1`(WTI)만 쓰면 브렌트-아비텍 스프레드를 놓친다. `@LCO.1`이 정상 지원됨.

```bash
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=@LCO.1&requestMethod=itk" \
  -H "User-Agent: $UA"
# 2026-10-23 실측: <last>114.35</last> <previous_day_closing>113.17</previous_day_closing> <change>1.18</change> <change_pct>1.04</change_pct>
```

→ WTI $101 / 브렌트 $114 = 스프레드 $13 → 중동·러시아 공급 premium가 계속 걸려 있다는 근거.

### 11.4 환율 — `open.er-api.com`도 정상 (2026-10-23 재확인)

`api.exchangerate-api.com`과 **둘 다** 정상 동작. 2026-10-23 `open.er-api.com/v6/latest/USD` → KRW **1324.953768**, JPY 156.92, EUR 0.8915.
→ 한 소스만 믿지 말고, News RSS의 "원/달러 N거래일 연속 연저점" 확정치와 교차 확인.

---

## 12. 🔴 Naver Polling `cr` 부호·`ms` 필드 신뢰 불가 (2026-10-23 신규 검증)

### 12.1 `cr` 부호가 두 번의 호출에서 달라졌다

같은 시각(18:30 KST) **동일 URL**을 두 번 호출했을 때:

| 호출 | 종목 | nv | pcv | cv | cr |
|:--|:--|--:|--:|--:|--:|
| 1회차 | HD현대일렉트릭 | 467,000 | 490,000 | — | **+4.69** (❌ 부호 반대) |
| 2회차 | HD현대일렉트릭 | 467,000 | 490,000 | 23,000 | **-4.69** (✅) |

- 1회차 `cv`는 음수인데 `cr`은 **양수**로 반환 → **부호 불일치 버그 재현**
- Pitfall 50이 "cr은 항상 절대값"이라 한 것보다 나쁜 케이스: **cr에 부호가 있어도 그 부호가 틀릴 수 있다**
- **확정 규칙: `cr`은 절대 신뢰하지 말고 `(nv - pcv) / pcv * 100`을 직접 계산해 표기한다.** `cv`도 함께 출력해 교차 확인.

```python
chg = int(x['nv']) - int(x['pcv'])
pct = round(chg / int(x['pcv']) * 100, 2)
assert abs(pct - float(x['cr'])) < 0.2 or True   # cr이 틀릴 수 있으므로 assert 대신 참고로만
```

### 12.2 `ms` 필드도 신뢰 불가 — 장 마감 후에도 `OPEN`

2026-10-23 18:30 KST(한국장 마감 15:30 이후) 호출 → `ms='OPEN'` 반환.
실제 종가는 뉴스("[마감] 코스피, SK하이닉스 반등에 0.30% 상승…5550선")로 확인됨 → `nv`는 종가(5,550.30)였음.

- **Pitfall 26d / 절 6의 "`ms='OPEN'`이면 장중이라 `pcv`가 전일 종가" 설명만으로는 부족** — `ms`는 갱신이 늦다.
- **판단 기준은 시각으로 한다**: KST 15:30 이후면 `ms`와 무관하게 `nv`를 종가로 취급하고 `pcv`를 전일 종가로 간주. (KR 장중 = 09:00~15:30)
- `ms`는 참고용으로만, 판정에 사용하지 말 것.

---

## 13. 🔴 한국어 텍스트 손상 — CJK 문자 스캔으로 조기 검출 (2026-10-23 재발)

Pitfall 63의 `BAD` 토큰 리스트(`wyn`, `ipuiae`, `定义` …)는 **이미 손상된 케이스만** 커버한다.
2026-10-23 세션에서 **새로운 형태의 손상**이 발생:

```
"NY源于: 연준, 워시체제 첫 FOMC서 금리 또 동결"   ←源于 (중국어)
"물가 재상승背景下 11월 3.50% 최종 전망"          ←背景下
"내수주(현대차)·보조리了中国(HD현대일렉)"           ←中国
"-白的 국면: 물가 재상승"                          ←白的
"有一颗장관리 및 스페인 팝업"                      ←有一颗
```

→ **한국어 문장에 섞인 CJK(한자) 토큰**이 공통 징후. `BAD` 리스트에 없는 신형이므로 기존 검사를 통과함.

### 검증된 조기 검출 방법 — CJK 정규식 스캔

```python
import re
CJK = re.compile(r'[\u4e00-\u9fff]')
# 저장 스크립트 안에서 (저장 전에) 검사
bad_spans = [(m.start(), m.group(0))
             for m in CJK.finditer(summary) if not ALLOWED_KOREAN_NEIGHBOR]
```

실전 절차(2026-10-23 검증):
1. 저장 `.py` 스크립트 전체에 `re.findall(r'[\u4e00-\u9fff]', s)`로 **비-ASCII 문자 목록**을 뽑는다.
2. 한글(`가-힣`)·ASCII를 제외한 잔여 문자가 CJK면 → 손상 후보.
3. `grep -n`으로 해당 라인 특정 → **항목 단위로 정상 한국어 재작성** (일괄 replace 금지).
4. **주의**: 뉴스 제목에는 정상적으로 CJK가 섞일 수 있음 (예: "SK하이닉스, 솔리다임 **美**상장 중단", "美 금리 결정", "中동"). → **뉴스 title은 CJK 스캔에서 제외**, `summary`와 `macro_report_summary`만 검사.

###_BAD 리스트 확장 권장

```python
BAD = ['wyn','Dd','ipuiae','定义','名词','cend','come','olor',
       '源于','背景下','中国','美的','白的','中导','有景','词','颗','颗장']
```

→ **BAD 리스트는 사례가 늘어날수록 반드시 뒤따라붙는 형태이므로, CJK 정규식 스캔이 본문 검출의 주력이고 BAD 리스트는 2차 방어로 유지**할 것.
