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
