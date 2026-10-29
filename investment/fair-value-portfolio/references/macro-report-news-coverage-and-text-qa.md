# 매크로 리포트 — 뉴스 종목 커버리지 보장 + 텍스트 오염 사전 QA (2026-10-28 신규)

**출현**: 18:30 매크로 전략 리포트 cron (`b96583fa9d27`) 실행 세션
**문제 2건**: ① 종목 뉴스 편중 ② 한국어 텍스트 CJK 혼입이 **저장 후**而非 저장 전에 발견

---

## 1. 🚨 뉴스 수집 — 종목별 커버리지 보장 (per-ticker quota + 날짜 창 확장)

### 증상 (실측)

`news_items`를 "종목명 + 주가" 같은 범용 쿼리로 수집했더니 **반도체에 쏠렸다**:

```
Counter({'삼성전자': 3, 'SK하이닉스': 3, '삼성전기': 3, ...})   # 32건 중 3종목이 9건
```

- 삼성전자·SK하이닉스·삼성전기 쿼리는 검색 결과가 서로 겹친다 (같은 "3분기 실적·주가 급등" 기사 재사용)
- 특히 **에이피알·현대차**는 최신 기사가 거의 없어 27~28일 창에서 **0건** → 필수 6종목 중 2종목 누락

### 해결: (a) 종목별 최대 건수 (b) 날짜 창 종목별 확장

```python
queries = [
    ("삼성전자", "삼성전자 주가 실적"),
    ("SK하이닉스", "SK하이닉스 주가 실적"),
    ("삼성전기", "삼성전기 주가 실적"),
    ("현대차", "현대차 주가 실적 목표주가"),
    ("에이피알", "에이피알 주가"),
    ("에이피알", "에이피알 실적 공시"),     # ← 같은 종목 2개 쿼리 = 폴백
    ("HD현대일렉트릭", "HD현대일렉트릭 주가 목표주가"),
    ...
]

for name, q in queries:
    got = 0
    for it in fetch(q):
        # (b) 저빈도 종목은 날짜 창을 넓힌다
        min_day = "26 Oct 2026" if name in ("현대차", "에이피알") else "27 Oct 2026"
        if min_day not in it["pub"] and "28 Oct 2026" not in it["pub"]:
            continue
        key = it["title"][:35]
        if key in seen:            # (a) 중복 제목 제거
            continue
        seen.add(key)
        news_items.append({...})
        got += 1
        if got >= 3:               # (a) 종목당 최대 3건
            break
```

### 규칙

1. **종목당 최대 3건 하드캡** — 쿼리 12개를 돌려도 한 종목이 12건을 독식하지 않게.
2. **저빈도 종목 날짜 창 확장** — 27~28일(48h) 창이 0건이면 **26일로 넓히고**, 그래도 0건이면 **쿼리를 2개로 분리**(예: "에이피알 주가" + "에이피알 실적 공시").
3. **저장 후 커버리지 assert** (아래 3절).
4. 중복 제거 키 = 정규화 제목 35자 prefix (`title[:35]`). 35자보다 짧게 잡으면 서로 다른 기사가 합쳐진다.

### 2026-10-28 최종 결과 (검증 통과)

```
Counter({'에이피알': 4, '삼성전자': 3, 'SK하이닉스': 3, '삼성전기': 3,
         'HD현대일렉트릭': 3, '시장': 3, '앤트로픽': 3, '연준': 3, '환율': 3,
         '현대차': 2, '유가': 2})
→ 6개 관심종목 전부 커버 ✅
```

---

## 2. 🚨 한국어 텍스트 오염 — **저장 스크립트 소스**를 먼저 스캔

### 기존 규칙의 공백

Pitfall 63/67은 **저장된 JSON**을 검사했다. 그런데 오염은 LLM이 **저장 스크립트(.py)의 summary 문자열**에서 이미 발생해 있다.
즉 저장→검사→패치→재저장을 반복하면 8회 이상 재실행된다.

### 정답 순서: 소스 스캔 → 수정 → 실행 → 저장 후 검증

```bash
# 저장 스크립트(.py) 자체에 CJK가 있는지 먼저 검사
python3 -c "
import re
s=open('/tmp/build_macro.py',encoding='utf-8').read()
for m in re.finditer(r'[一-鿿]+',s):
    print(repr(s[max(0,m.start()-45):m.end()+45]))
"
```

### 2026-10-28 실제 오염 (LLM 생성 산문, 인코딩 붕괴 아님)

| 오염 | 올바른 한국어 |
|:--|:--|
| `지수层面 크나` | `지수 수준으로는 크며` |
| `원자재·환수 입계비용` | `원자재·환수 등 내재 비용` |
| `실적으로跟进했다` | `실적으로 동반 상승했다` |
| `메모리厂商의 가격 결정력` | `메모리 제조업체의 가격 결정력` |
| `반도체，给你 물가 대비` | `반도체 대형주에 물가 대비` |
| `비(非) 반도체` | `비반도체` |

**모두 LLM이 한국어 문장 안에 중국어 단어를 끼워 넣은 것** — 인코딩 문제 아님.
→ **항목 단위 정상 한국어 재작성**(일괄 replace 금지, 기존 Pitfall 67 규정 그대로).

### 뉴스 title의 CJK는 정상이지만 저장 시 제거 권장

RSS 제목에 실제 한자가 섞여 온다:

> `SK하이닉스 100兆 역대급 주주환원 추진에 주가도 방긋`  ← "100兆" (100조)

Pitfall 67은 title을 CJK 스캔에서 제외하도록 했지만, **Discord에 그대로 노출되면 혼입으로 보인다**.
→ **title·summary 저장 시 CJK/전각문자 제거 후 저장**:

```python
def clean(t):
    t = (t.replace("&#39;", "'").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&lt;", "<").replace("&gt;", ">"))
    t = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", "", t)   # 한자+전각
    return re.sub(r"\s+", " ", t).strip()
```

> 다만 **제목 의미가 바뀌지 않는 경우에만** 적용. 예: "SK하이닉스 100兆" → "SK하이닉스 100" (조는 단위만 소실, 의미 유지).

---

## 3. 저장 후 검증 — 커버리지 + 무결성 assert

```python
d1 = json.load(open(p1)); d2 = json.load(open(p2))
assert d1["timestamp"] == d2["timestamp"]
assert open(p1,'rb').read() == open(p2,'rb').read()      # byte-identical

# 6종목 커버리지
REQUIRED = {"삼성전자","SK하이닉스","삼성전기","현대차","에이피알","HD현대일렉트릭"}
have = {n["ticker"] for n in d1["news_items"]}
assert REQUIRED <= have, f"뉴스 누락: {REQUIRED - have}"

# CJK 0건
assert len(re.findall(r"[\u4e00-\u9fff]", d1["macro_report_summary"])) == 0
for n in d1["news_items"]:
    assert n["title"] and n["url"] and n["source"]
    assert len(re.findall(r"[\u4e00-\u9fff]", n["summary"])) == 0
```

---

## 4. 지수는 Naver siseJson / Polling 으로는 못 가져온다 (2026-10-28 실측)

| 소스 | KOSPI/KOSDAQ | 결과 |
|:--|:--|:--|
| Naver siseJson `symbol=KOSPI` | ❌ | `[]` — **빈 배열** (종목 코드만 지원) |
| Naver siseJson `symbol=KOSDAQ` | ❌ | `[]` |
| Naver Polling `query=SERVICE_ITEM:KOSPI` | ❌ | `datas: []` |
| Naver Polling `query=SERVICE_ITEM:KOSDAQ` | ❌ | `datas: []` |
| **CNBC XML `.KS11` / `.KQ11`** | ✅ | last / pdc / change / change_pct 정상 |

→ **지수는 CNBC XML만 사용.** 개별 종목만 Naver siseJson.

### siseJson 파싱 — `json.loads`는 실패한다

응답 첫 줄이 헤더 배열(깨진 EUC-KR 포함)이라 `json.loads`가
`Expecting value: line 2 column 4 (char 4)` 로 죽는다.

```python
# ❌ 실패
d = json.loads(raw.decode('euc-kr', errors='ignore'))

# ✅ 정규식만으로 데이터 행 추출
rows = re.findall(r'\["(\d{8})", *([\d.]+), *([\d.]+), *([\d.]+), *([\d.]+), *([\d.]+), *([\d.]+)\]', raw)
# → (날짜, 시가, 고가, 저가, 종가, 거래량, 외국인소진율)
```

`[\d.]+` 로 잡아야 한다 — 정수만 가정하면 거래량/소진율 파싱에서 놓친다.

---

## 5. 뉴스 URL 자동 추출 유지 (Pitfall 65 재확인)

손으로 URL을 옮기지 말 것. RSS에서 추출 → URL 그대로 JSON 주입 → 저장 시 assert:

```python
assert n["url"].startswith("https://news.google.com/rss/articles/"), n["url"]
assert n["url"].endswith("?oc=5") and len(n["url"]) > 120, n["url"]
```

2026-10-28: 32건 전부 통과 (저장 스크립트가 RSS에서 직접 추출).

---

## 6. 변경 이력

- **2026-10-28 (v1)**: 최초 작성. 뉴스 per-ticker quota(3건) + 저빈도 종목 날짜 창 확장(26일) 패턴,
  저장 스크립트 소스 사전 CJK 스캔, 뉴스 title CJK 제거(clean()), 지수 인덱스는 Naver 미지원 확인,
  siseJson `json.loads` 실패 → 정규식 파싱.
