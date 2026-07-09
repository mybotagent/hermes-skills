# Naver Polling API — Yahoo Finance 완전 차단 시 한국 개별주 fallback

**발견일**: 2026-07-09 18:32 KST (cron `b96583fa9d27` 18:30 매크로 리포트 실행 중)
**상태**: ✅ 6종목 검증 완료, 즉시 사용 가능
**트리거**: Yahoo Finance `query1`/`query2` 모두 429 "Too Many Requests" (심볼 무관)

---

## 1. 문제 정의 (2026-07-09 갱신)

**이전 self-healing-cron SKILL.md 가정 (7/7)**:
- Yahoo Finance는 **심볼별 차등 차단** — US 지수/선물만 429, 한국 개별주 `.KS` 는 정상
- "한국 개별주 가격이 필요하면 Yahoo chart API가 유일한 옵션"

**7/9 검증 결과 (6종목, 양쪽 query)**:
- `query1.finance.yahoo.com` → 전부 429
- `query2.finance.yahoo.com` → 전부 429
- 5초 sleep 재시도 / User-Agent 교체 / referer 추가 → **전부 무효**
- 7/7 시점 검증과 정반대 — Yahoo는 **시간 단위로 정책 변경**

**결과**: cron 모드에서 한국 개별주 가격 수집이 **완전 불가능**한 상태.

---

## 2. Naver Polling API — 유일한 fallback

### 2.1 Endpoint

```
https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{6자리코드}
```

- `{6자리코드}` = KRX 6자리 (Yahoo의 `.KS` 접미사 ❌)
- 예: `005930`, `000660`, `009150`, `005380`, `278470`, `267270`

### 2.2 호출 (cron 모드, 7/9 검증)

```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
curl -sL --max-time 12 "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:005930" \
  -H "User-Agent: $UA" -o /tmp/naver_005930.raw
```

**반드시 `curl -o /tmp/...` 로 파일 저장** — `curl | python3` 같은 pipe는 cron 모드에서 차단됨.

### 2.3 ⚠️ EUC-KR 인코딩 (가장 흔한 함정)

응답 바이트는 **EUC-KR**. `json.loads()` 직접 호출 시:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc7 in position 119: invalid continuation byte
```

**해결 (1줄)**:
```python
raw = open('/tmp/naver_005930.raw', 'rb').read()
d = json.loads(raw.decode('euc-kr', errors='ignore'))
```

`errors='ignore'` 필수 — 일부 종목명 바이트가 깨질 수 있지만 핵심 필드(nv, cv, cr, pcv)는 모두 영문 key라 영향 없음.

### 2.4 응답 구조 (삼성전자 7/9 응답 예시)

```json
{
  "resultCode": "success",
  "result": {
    "pollingInterval": 7000,
    "areas": [{
      "name": "SERVICE_ITEM",
      "datas": [{
        "cd": "005930",
        "nm": "삼성전자",
        "sv": "277500",
        "nv": 278000,
        "cv": 500,
        "cr": 0.18,
        "rf": "2",
        "mt": "1",
        "ms": "CLOSE",
        "tyn": "N",
        "pcv": 277500,
        "ov": 288500,
        "hv": 291500,
        "lv": 267500,
        "ul": 360500,
        "ll": 194500,
        "aq": 28796159,
        "keps": 6605,
        "eps": 12372,
        "bps": 71907.25952,
        "cnsEps": 46664,
        "dv": 1668.00000
      }]
    }]
  }
}
```

### 2.5 핵심 필드 (EUC-KR 인코딩된 영문 key)

| key | 의미 | 예시 (삼성전자 7/9 종가) |
|:----|:----|:---------------------|
| `cd` | 종목코드 | `005930` |
| `nm` | 종목명 | `삼성전자` (EUC-KR 바이트) |
| `nv` | **현재가 (정수)** | 278000 |
| `cv` | **전일비 (정수, +/− 부호)** | 500 |
| `cr` | **전일비율 (%, 부호 포함)** | 0.18 |
| `pcv` | **전일종가** | 277500 |
| `ov` | 시가 | 288500 |
| `hv` | 고가 | 291500 |
| `lv` | 저가 | 267500 |
| `ul` / `ll` | 상한가 / 하한가 | 360500 / 194500 |
| `aq` | 누적거래량 | 28796159 |
| `ms` | 거래상태 | `CLOSE` / `OPEN` / `PREOPEN` |
| `keps` | 추정 EPS | 6605 |
| `eps` | EPS | 12372 |
| `bps` | BPS | 71907.25952 |
| `cnsEps` | 컨센서스 EPS | 46664 |
| `dv` | 배당금 | 1668.00000 |

> `sv`는 `pcv`(전일종가)와 동일한 값. `nv`만 현재가. `cv`/`cr`은 `nv - pcv` / `(nv-pcv)/pcv*100` 자동 계산.

### 2.6 파싱 + 매크로 리포트용 dict 변환

```python
import json

def fetch_naver_price(ticker: str) -> dict:
    """Naver Polling API에서 한국 주식 현재가 + 전일비 수집 (EUC-KR 디코딩)."""
    raw = open(f'/tmp/naver_{ticker}.raw', 'rb').read()
    d = json.loads(raw.decode('euc-kr', errors='ignore'))
    data = d['result']['areas'][0]['datas'][0]
    return {
        'code': data['cd'],
        'price': int(data['nv']),
        'prev_close': int(data['pcv']),
        'change': int(data['cv']),
        'change_pct': float(data['cr']),
        'open': int(data['ov']),
        'high': int(data['hv']),
        'low': int(data['lv']),
        'volume': int(data['aq']),
        'session': data['ms'],  # 'CLOSE' / 'OPEN' / 'PREOPEN'
        'eps': data.get('eps'),
        'bps': data.get('bps'),
    }

# 6종목 일괄 수집
TICKERS = ['005930', '000660', '009150', '005380', '278470', '267270']
for t in TICKERS:
    info = fetch_naver_price(t)
    print(f"{info['code']}: {info['price']:,} ({info['change']:+,}, {info['change_pct']:+.2f}%)")
```

### 2.7 6종목 검증 출력 (2026-07-09 18:32 KST)

```
005930: 278,000 (+500, +0.18%)
000660: 2,186,000 (+110,000, +5.30%)
009150: 1,493,000 (+14,000, +0.95%)
005380: 445,500 (-17,000, -3.68%)
278470: 365,500 (-20,000, -5.19%)
267270: 121,200 (-4,100, -3.27%)
```

---

## 3. 알려진 제약 + 함정

### 3.1 제약

| 제약 | 영향 | 대안 |
|:----|:-----|:----|
| **한국 종목만** (KRX 6자리) | US 종목 불가 | CNBC / Yahoo(풀리면) / Finnhub |
| **`polling.finance.naver.com` DNS 의존** | 해외 망에서 차단 가능 | 한국 VPS에서는 안정, `curl -I` 로 사전 확인 |
| **EUC-KR 인코딩** | `json.loads()` 직접 실패 | `raw.decode('euc-kr', errors='ignore')` 1줄 |
| **장 마감 후 1~2분 지연** | `ms='CLOSE'` 후 1~2분간 직전 값 유지 | yfinance도 동일 (15~20분 지연) |
| **`nv`/`cv`는 정규장 기준** | 시간외 거래는 다른 필드 (`nxtOverMarketPriceInfo`) | 정규장 분석은 무관 |

### 3.2 함정

1. **EUC-KR 디코딩 누락** → `UnicodeDecodeError`. **가장 흔한 함정.**
2. **빈 응답 / DNS 실패** → `json.loads('')` → `JSONDecodeError`. `try/except` 필수.
3. **`.KS` 접미사 사용** → Naver는 KRX 6자리만 받음. Yahoo의 `.KS` 자동 변환 안 함.
4. **rate limit** → 명시된 limit 없음 (관대). 안전하게 종목당 sleep 0.3초.
5. **장 시작 전 (`PREOPEN`)** → `pcv`는 직전 종가, `nv`는 시가 전 예상가일 수 있음. `change_pct` 해석 주의.
6. **정수 vs float** → `nv`/`cv`/`pcv`는 int지만 JSON에서 float로 파싱될 수 있음. `int()` 캐스팅 권장.

### 3.3 다중 종목 루프 패턴 (안전)

```bash
# ① curl 호출 (bash, sleep 0.3초)
for t in 005930 000660 009150 005380 278470 267270; do
  curl -sL --max-time 12 "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:$t" \
    -H "User-Agent: $UA" -o /tmp/naver_$t.raw
  sleep 0.3
done

# ② Python 파싱 (write_file로 저장 후 실행)
python3 /tmp/parse_naver.py
```

`parse_naver.py`:
```python
import json
TICKERS = ['005930', '000660', '009150', '005380', '278470', '267270']
out = {}
for t in TICKERS:
    try:
        raw = open(f'/tmp/naver_{t}.raw', 'rb').read()
        d = json.loads(raw.decode('euc-kr', errors='ignore'))
        data = d['result']['areas'][0]['datas'][0]
        out[t] = {
            'price': int(data['nv']),
            'prev_close': int(data['pcv']),
            'change': int(data['cv']),
            'change_pct': float(data['cr']),
        }
    except Exception as e:
        out[t] = {'error': str(e)}
print(json.dumps(out, indent=2, ensure_ascii=False))
```

---

## 4. 매크로 리포트 통합 예시 (2026-07-09 실제 사용)

`b96583fa9d27` 18:30 매크로 리포트 크론에서:
1. CNBC XML API → KOSPI / KOSDAQ / S&P / DXY / WTI / Gold / 10Y / VIX (글로벌 지표)
2. `open.er-api.com` → USD/KRW, EUR/USD
3. Google News RSS → 22건 뉴스 헤드라인
4. **Naver Polling API → 6종목 가격·등락률 (이 reference로 추가)**

기존 `macro_context.json` 구조에 `stock_data_6` 필드 추가:
```json
{
  "key_macro_data": {"fed_rate": "4.25~4.50%", "kospi": "7291.91", ...},
  "stock_data_6": {
    "삼성전자": {"code": "005930", "price": 278000, "prev": 277500, "change": 500, "change_pct": 0.18},
    "SK하이닉스": {"code": "000660", "price": 2186000, "prev": 2076000, "change": 110000, "change_pct": 5.30}
  }
}
```

→ LangGraph 파이프라인이 이 필드를 읽어 종목별 분석에 활용.

---

## 5. 향후 Yahoo 회복 감시 패턴 (선택)

Yahoo가 다시 풀리는지 매주 확인하고 싶을 때 (read-only probe):

```bash
# 7/9 기준 모두 429 — 풀리면 200 OK로 바뀜
for sym in 005930.KS 000660.KS; do
  status=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" \
    -H "User-Agent: $UA" "https://query1.finance.yahoo.com/v8/finance/chart/$sym?interval=1d")
  echo "$sym: $status"
done
```

- 200 OK → Yahoo 복구 → Naver fallback 우선순위 낮춤
- 429 → 계속 차단 → Naver 사용

---

## 6. 관련 레퍼런스

- `SKILL.md` 본문 — "🚨 Yahoo Finance 완전 차단" 섹션, "Naver Polling API" 섹션, "한국 개별주" 데이터 소스 행
- `fair-value-portfolio` 스킬 — Korean stock 데이터 (Pitfall 8, 18), Naver 우선 정책
- `references/cron-mode-data-sources.md` — 다른 글로벌 데이터 소스

## 7. 변경 이력

- **2026-07-09 (v1)**: 최초 발견 + 6종목 검증. Yahoo 완전 차단 확인 후 Naver Polling API로 즉시 우회.
