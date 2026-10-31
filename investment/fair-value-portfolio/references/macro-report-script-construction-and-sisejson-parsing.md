# 매크로 리포트 — 저장 스크립트 구성 안전성 + siseJson 헤더 행 파싱 (2026-10-30 신규)

**출현**: 18:30 매크로 전략 리포트 cron (`b96583fa9d27`) 실행 세션 (2026-10-30 금요일)

---

## 1. 🚨 저장 스크립트에 리포트 본문을 통째로 embed 하지 말 것

### 증상

리포트 본문(~3,900자) + JSON 구조를 **하나의 `.py` 파일의 긴 문자열 리터럴**로 작성하자
LLM이 생성 중 **퇴화(degeneration)** — 무의미한 문자열이 수천 자 반복 출력됨:

```python
# 실제로 생성된 손상 (요약)
"impact_analysis": "('_ "_ "_ "_ "_ "_ "_ "_ ... "  # 수천 자 meaningless 반복
"... summary": "영업이익 1,606 Recreation management로 사상 최대인데도 ..."
```

→ Python SyntaxError(`closing parenthesis ')' does not match opening parenthesis '{'`)로 **스크립트 자체가 죽음**.

### 원인

- LLM이 수천 자 단일 문자열 리터럴을 한 번에 생성하면 **토큰 붕괴(degeneration)** 위험
- 특히 `"""..."""` 삼중따옴표 + 한글 + 화살표(`->`) + 백슬래시 조합에서 빈도 상승
- 파일이 길어질수록 뒤쪽 품질이 급락 (앞부분은 정상, 뒤에서부터 오염)

### 해법 — 본문을 별도 파일로 분리

```python
# STEP 1: write_file()로 리포트 본문만 별도 .md/.txt 에 저장 ( degeneration 위험 격리 )
#         /tmp/macro_body_20261030.md
# STEP 2: 저장 스크립트는 파일을 읽기만 한다
body = open('/tmp/macro_body_20261030.md', encoding='utf-8').read().strip()
assert len(body) > 2500, f'본문 너무 짧음: {len(body)}'
assert not re.search(r'[\u4e00-\u9fff]', body), '본문 CJK 혼입'
```

- 긴 산문을 **`.py`가 아니라 `.md`**에 담으면: (1) degeneration 위험이 텍스트 파일로 격리됨
  (2) syntax error 원천 차단 (3) 본문 수정이 제자리에서 가능
- 짧은 필드(`key_driver`, `impact_analysis`)는 `.py`에 두어도 무방 — 단 500자 이내로 제한

### 추가 안전장치 — 실행 전 assert + 중단

```python
for label, txt in (('summary', body), ('impact', impact)):
    bad = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', txt)
    if bad:
        for m in re.finditer(r'[\u4e00-\u9fff\u3400-\u4dbf]+', txt):
            print('CJK', label, repr(txt[max(0, m.start()-40):m.end()+40]))
        raise SystemExit('CJK contamination in ' + label)
```

→ 오염 시 **저장 전에 중단** (Pitfall 70의 "저장 전 QA" 원칙과 동일).
근본 재작성이 필요하므로 자동 replace가 아니라 **항목 단위 재작성** (Pitfall 63/67 규정).

---

## 2. 🚨 siseJson 헤더 행 — `split(',')` 파싱이 죽는다

### 증상

```python
raw = open('/tmp/n_005930.raw','rb').read().decode('euc-kr', errors='ignore')
rows = re.findall(r'\[([^\]]+)\]', raw)
for r in rows:
    p = [x.strip().strip('"') for x in r.split(',')]
    if len(p) >= 7:
        parsed.append((p[0], int(p[4]), p[6]))
# → ValueError: invalid literal for int() with base 10: "'醫媛'"
```

### 원인

응답 **첫 줄이 헤더 행**이라 `int()` 변환 대상이 문자열이 됨:

```
[['날짜', '시가', '고가', '저가', '종가', '거래량', '외국인소진율'],
```

- EUC-KR 디코딩 시 `날짜`가 한자 bytecode로 깨져 `醫媛`처럼 보임 (UTF-8로 읽으면 정상)
- `len(p) >= 7` 조건이 헤더 행도 통과시킴 (헤더도 7개 필드)

### 해법 — 날짜로 앵커된 엄격한 정규식

```python
pat = re.compile(
    r'\["(\d{8})",\s*([\d,]+),\s*([\d,]+),\s*([\d,]+),\s*([\d,]+),\s*([\d,]+),\s*([\d.]+)\]'
)
parsed = [(m[0], int(m[4].replace(',', '')), float(m[6])) for m in pat.findall(raw)]
```

- `"(\d{8})"` 앵커 → **헤더 행은 매칭 자체가 안 됨** (EUC-KR 손상 무관)
- `[\d,]+` → 거래량/가격에 천단위 쉼표가 포함된 응답도 처리 (2026-10-30 응답은 쉼표 없었지만 안전망)
- 그룹: 날짜, 시가, 고가, 저가, **종가(4번)**, 거래량, **외국인소진율(6번)**

### 10일 창으로 주간수익률까지 한 번에

```python
# startTime=YYYYMMDD (11 trading days inclusive)
url = (f'https://api.finance.naver.com/siseJson.naver?symbol={code}'
       f'&requestType=1&startTime=20261019&endTime=20261030&timeframe=day')
```
- `Referer: https://finance.naver.com/item/sise_day.naver?code={코드}` **필수** (없으면 빈 응답)
- 첫 행 종가 vs 마지막 행 종가 → **주간수익률**
- 마지막-1행 종가 vs 마지막 행 종가 → **일변동률** (Polling `cr` 대신 확정값, Pitfall 66)
- 마지막 행 7번째 필드 → **외국인소진율**

2026-10-30 실측 (6종목 전부 정상):

| 종목 | 종가 | 일변동 | 주간 | 외국인 |
|:--|--:|--:|--:|--:|
| 삼성전자 | 221,000 | -4.12% | -1.12% | 46.17% |
| SK하이닉스 | 1,393,000 | -8.11% | +6.83% | 48.72% |
| 삼성전기 | 1,171,000 | -8.66% | -4.02% | 36.45% |
| 현대차 | 278,000 | -4.79% | -14.33% | 24.14% |
| 에이피알 | 254,500 | -9.91% | -22.76% | 39.43% |
| HD현대일렉트릭 | 419,500 | -4.66% | -20.40% | 33.50% |

---

## 3. 시장 이벤트 1차 원인 — 종목명이 아닌 "사건명" 쿼리 필수

6종목 뉴스만 수집하면 **매크로 드라이버(예: 알파벳 AI 투자 충격)를 놓친다**.
2026-10-30 실제 드라이버는 `SK하이닉스/삼성전자` 뉴스가 아니라 **구글 모회사** 뉴스였음.

추가 필수 쿼리 (사건명 기반):

```python
EXTRA_QUERIES = [
    '알파벳 구글 AI', '나스닥 AI주', '코스피 급락',
    '서킷브레이커', '연준 12월 인상', '유가 급등',
]
```

- `코스피 급락` → 지수 레벨 이벤트 확인
- `알파벳 구글 AI` →半导体로 전이되는 **1차 원인** 확인
- `서킷브레이커` → 시장 이벤트 에스컬레이션 판단 (기존 escalation 패턴)
- 언어 혼용: `美`/한자 표기가 실제 헤드라인에 실려 오므로 `美 연준` → `미국 연준`처럼 **정정 매핑** 후 사용 (Pitfall 70)

---

## 4. dual-save + 바이트 동일성 assert (Pitfall 22b/65 재확인)

```python
p1 = '/home/ubuntu/trading-agents-nuri/data/macro_context.json'
p2 = '/home/ubuntu/trade-pipeline/data/macro_context.json'
shutil.copy2(p1, p1 + '.bak_20261030')     # 전일 백업
with open(p1, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
shutil.copy2(p1, p2)                        # pipeline.py가 읽는 경로

d1 = json.load(open(p1)); d2 = json.load(open(p2))
assert d1 == d2, 'FILES DIFFER'
assert d1['timestamp'] == d2['timestamp']
assert not re.search(r'[\u4e00-\u9fff]', d1['macro_report_summary'])
assert len(d1['macro_report_summary']) > 2500
```

- `timestamp` 만 비교가 아니라 **`d1 == d2` 전체 동등성** + 바이트 동일성까지 확인
- `json.dump(..., ensure_ascii=False)` — `True`면 한자가 `\uXXXX`로 escaping되어 한국어 검증이 무의미해짐

---

## 5. 변경 이력

- **2026-10-30 (v1)**: 최초 작성. 저장 스크립트에 긴 문자열 embed 시 LLM degeneration → 본문 분리(.md) 패턴,
  siseJson 헤더 행 파싱 실패(严격 정규식 앵커로 해결), 10일 창으로 일변동/주간/외국인소진율 1회 수집,
  사건명 쿼리(알파벳/코스피/서킷브레이커) 필수 추가, dual-save 전체 동등성 assert.
