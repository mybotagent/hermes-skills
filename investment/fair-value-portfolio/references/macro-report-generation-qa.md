# 매크로 리포트 생성·저장 QA 워크플로우 (2026-10-27 검증)

18:30 매크로 크론에서 **리포트 본문 생성 → 정량값 교차검증 → 저장 → dual-save → QA**까지의
검증된 순서와 그때 발견된 함정들. 본문은 `SKILL.md` Pitfall 69가 요약하고, 여기가 세부 절차다.

---

## 0. 전체 순서 (이 순서로 지킬 것)

```
1. 데이터 수집 (urllib 스크립트 파일 → terminal 실행)   ← scripts/ 참고
2. 정량값 교차검증 (공식 소스 재조회)                    ← 섹션 1
3. 뉴스 URL 자동 매핑 (제목 정규화 매칭)                ← 섹션 2
4. 리포트 본문 작성 (단일 생성 스크립트 .py)             ← 섹션 3
5. 본문 QA (CJK + 로마자 혼입 + 정량값 일치)             ← 섹션 4
6. 저장 + dual-save + md5/timestamp 대조                 ← 섹션 5
```

**핵심 원칙**: 본문 QA(5)는 **3번에서 4번 사이에** 넣는다. 저장 후 QA하면 손상 토큰을
"저장 → 발견 → 스크립트 패치 → 재저장"로 여러 번 반복하게 된다 (2026-10-27 실제로 8회 반복).

---

## 1. 정량값 교차검증 — CNBC quote-html-webservice (신규 발견)

기존 `references/cnbc-xml-naver-polling-workflow.md`의 XML 엔드포인트와 별개로,
**HTML quote 엔드포인트가 지수·지수期货·금리를 한 번에 커버**한다. 2026-10-27 실측 검증됨.

```python
import urllib.request, re, time
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def cnbc(sym):
    url = ("https://quote.cnbc.com/quote-html-webservice/quote.htm"
           f"?symbols={sym}&requestMethod=itk")
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    x = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    def g(k):
        m = re.search(r'<%s>([^<]+)</%s>' % (k, k), x)
        return m.group(1) if m else None
    return sym, g('last'), g('previous_day_closing'), g('change'), g('change_pct'), g('last_time')
```

**2026-10-27 실측 결과 (13:00 KST 전후)**:

| 심볼 | last | change_pct | note |
|:--|--:|--:|:--|
| `.KS11` | 5638.34 | 3.09 | 코스피 확정 종가 |
| `.KQ11` | 743.83 | 2.29 | 코스닥 확정 종가 |
| `.SPX` | 7676.77 | 0.696 | 10/26 종가 |
| `.IXIC` | 26169.381 | 0.825 | 10/26 종가 |
| `.DJI` | 52361.58 | 0.28 | 10/26 종가 |
| `.VIX` | 18.32 | -0.381 | |
| `.DXY` | 102.253 | 0.29 | |
| `US10Y` | 4.986 | 0.00 | 미 10년물 |
| `US30Y` | 5.304 | -0.0508 | 미 30년물 |
| `@CL.1` | 102.25 | 0.48 | WTI 선물 |
| `@LCO.1` | 116.06 | 0.22 | 브렌트 선물 |
| `@GC.1` | 4007.70 | -0.76 | 금 선물 |

심볼당 1초 sleep 권장. `previous_day_closing`이 함께 나오므로 전일 대비 직접 계산 가능.

### 값이 어긋나면 — 양쪽 다 고쳐야 한다 (실수 패턴)

2026-10-27, 파이프라인이 모아온 값과 CNBC 재조회 값이 미세하게 달랐다:

| 지표 | 파이프라인 값 | CNBC 재조회 | 처리 |
|:--|--:|--:|:--|
| DXY | 102.247 (+0.28%) | 102.253 (+0.29%) | 갱신 |
| WTI | $102.38 (+0.61%) | $102.25 (+0.48%) | 갱신 |
| US10Y | 4.991% | 4.986% | 갱신 |
| VIX | 18.33 | 18.32 | 갱신 |
| 금 | $4,006.30 | $4,007.70 | 갱신 |
| 브렌트 | $116.27 | $116.06 | 갱신 |

**교정 대상은 `key_macro_data` JSON 블록과 `macro_report_summary` 본문 양쪽이다.**
본문에만 갱신하면 JSON과 리포트가 서로 다른 수치를 말하게 된다 (2026-10-27 실제로 4곳 스윕 필요).
`grep`으로 잔여 구버전 값이 0건인지 확인하고 나서 저장한다.

```bash
grep -n "102.247\|4.991\|18.33\|116.27\|4,006.30" /tmp/save_macro.py   # 0건이어야 함
```

---

## 2. 뉴스 URL 자동 매핑 — 제목 정규화 매칭

RSS 제목 문자열이 리포트에 쓰일 제목과 **정확히 다를 수 있다** (플랫폼 접미사 `- 연합뉴스`,
특수문자, 말줄임). 단순 `in` 매칭은 실패한다. **정규화 후 다중 토큰 부분 매칭**을 쓴다.

```python
import re
def norm(s):
    return re.sub(r'[\s’‘\'"…·]', '', s)   # 공백·구분기호 제거

def find(flat, *subs):
    for r in flat:
        t = norm(r['title'])
        if all(norm(s) in t for s in subs):
            return r
    return None
```

사용 예: `find(flat, '코스피, 3% 반등해 5,638.34 마감', '코스닥도 2.3% 올라')`,
`find(flat, 'SK하이닉스내일3분기실적공개')` (공백 제거 후 비교).

**매칭 실패 처리**: `find`가 None이면 **임의 URL을 넣지 말고** 저장 스크립트에서 assert로 막는다.

```python
for i, k in enumerate(KEY_ORDER):
    u = URLMAP.get(k)
    assert u and u.get('url'), ('URL 매핑 누락', k)   # 실패 시 여기서 중단
    news_items[i]['url'] = u['url']
    news_items[i]['source'] = u['source']
```

타이틀도 매칭 결과에서 **정규화하지 말고 그대로** 가져올 것이 아니라, 원하는 표시형으로
명시적으로 지정한다 (RSS 제목이 "…- 폴리뉴스 Polinews" 통을 포함하므로).

---

## 3. 본문은 단일 생성 스크립트에서 만든다

- 리포트 본문 + `news_items` + `key_macro_data` + `market_interpretation`을 **하나의 `.py`**에서
  `json.dump`으로 저장. 손으로 JSON 편집 금지.
- 본문 문자열이 길면 Python 소스 안에서 triple-quoted string으로 둔다.
- **보안 스캐너 제약**: heredoc에 특수문자/이모지가 들어가면 차단되므로
  `write_file()`로 `/tmp/save_macro.py` 저장 → `terminal("python3 /tmp/save_macro.py")`.

---

## 4. 본문 QA — 2계열 스캔 (저장 전!)

Pitfall 63/67의 BAD 토큰 리스트만으로는 부족하다. 2026-10-27에 실제로 통과한 손상 유형:

| 유형 | 실제 손상 예시 | 검출 방법 |
|:--|:--|:--|
| CJK 한자 혼입 | `进入한 국면`, `金리 경로`, `集中매수`, `定义`, `名词` | `re.compile(r'[\u4e00-\u9fff]')` |
| **로마자 혼입** | `money를 끌어당겼다`, `wells put 반등`, `today's rally`, `hawkish surprise`, `defenses`, `transistor`, `catalysts`, `S/W 라이선스` | 라틴 문자 단어 목록 + 금지 단어 리스트 |

**로마자 혼입 검출 실무**:
1. 생성 스크립트 소스를 라인 단위로 훑어 **영문 단어가 들어간 한국어 문장**을 육안 확인.
2. 다음 성어가 자연어에서 자주 오염된다: `money`, `well`, `put`, `today`, `hawkish`, `surprise`,
   `defense`, `transistor`, `catalyst`, `rally`, `leader`, `S/W`, `CNY`, `US`.
3. 검사 대상은 **`macro_report_summary`와 `news_items[].summary`만**. `news_items[].title`은
   원문 그대로 ("美 금리 결정" 같은 정상 혼입 가능) → title은 스캔에서 제외.

```python
import re
CJK = re.compile(r'[\u4e00-\u9fff]')
bad = re.findall(CJK, summary)
assert not bad, bad[:10]
```

**조치**: 일괄 replace 금지. **항목 단위로 정상 한국어 재작성** 후 생성 스크립트에 반영하고
재실행한다. 2026-10-27에는 CJK 5건 + 로마자 혼입 4건을 항목 단위로 재작성해 통과시켰다.

**추가 검증**: 저장 후 `summary`에 포함된 핵심 수치가 `key_macro_data`와 일치하는지 grep/count로 확인.

```python
for k in ['102.253', '4.986', '102.25', '116.06', '4,007.70', '18.32', '5,638.34']:
    print(k, summary.count(k))
```

---

## 5. 저장 + dual-save + 무결성 대조 (한 스크립트에서)

Pitfall 22b/65의 dual-save를 **저장 스크립트 내부에서** 처리하면 QA가 한 번에 끝난다.

```python
import json, shutil, os
targets = [
    os.path.expanduser('~/trading-agents-nuri/data/macro_context.json'),
    os.path.expanduser('~/trade-pipeline/data/macro_context.json'),
]
for t in targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

# 이후 검증
a = json.load(open(targets[0], encoding='utf-8'))
b = json.load(open(targets[1], encoding='utf-8'))
assert a['timestamp'] == b['timestamp'], 'timestamp 불일치'
assert a == b, '두 파일 내용 불일치'
```

추가로 `md5sum` 두 경로를 비교하면 "내용 동일"이 눈으로 확인된다.

```bash
md5sum ~/trading-agents-nuri/data/macro_context.json ~/trade-pipeline/data/macro_context.json
# 두 줄의 해시가 같아야 함 (2026-10-27 실측: ddc454ccbe1f1d5edf0afbf13c505fe8)
```

**저장 QA 체크리스트 (같은 스크립트 말미에서 전부)**
- [ ] `json.load` 양쪽 성공
- [ ] `timestamp` 동일
- [ ] 본문 전체 동일 (md5)
- [ ] `key_macro_data` 필수 키 존재 (`fed_rate`, `dxy`, `wti`, `usdkrw`, `ten_year_yield`)
- [ ] `market_interpretation` 3필드 존재 (`key_driver`, `market_sentiment`, `regime`, `impact_analysis`)
- [ ] `news_items[].url`이 `https://news.google.com/rss/articles/`로 시작하고 `?oc=5`로 끝나며 길이 > 120
- [ ] `macro_report_summary` CJK 스캔 0건
- [ ] `summary` 내 핵심 수치가 `key_macro_data`와 일치

---

## 6. Discord 전송 — webhook을 못 찾으면 우회는 이것

2026-10-27: `~/trade-pipeline/.env`에는 `DEEPSEEK_API_KEY`, `FINNHUB_API_KEY`, `DATA_DIR`, `LOGS_DIR`만
있었고 Discord webhook URL은 어디에도 없었다. `~/.hermes/config.yaml`의 `discord:` 블록은
`require_mention` / `free_response_channels` / `allowed_channels`만 있고 webhook URL이 없다.

**대응**: 이 크론의 최종 응답 자체가 잡의 Discord 채널로 전달되므로, **리포트 전문을 최종 응답에
그대로 담아** 전송을 대신한다. webhook URL을 찾기 위해 `grep -r`을 홈 디렉터리 전체에 돌리면
시간 초과가 난다(2026-10-27 실측 60초 타임아웃) → `.env`, `config.yaml`, `*.py`, `*.sh`처럼
**후보 확장자로 한정해서** grep할 것.
