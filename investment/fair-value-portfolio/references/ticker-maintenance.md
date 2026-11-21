# Ticker Maintenance Guide (관심종목 추가/제거)

> **현행**: `data/watchlist.json` 하나만 수정하면 됨. 5개 파일 시대는 끝남.
> 단, **소비자 코드가 하드코딩 사전을 가지고 있으면 끝나지 않은 것** — 추가 절차는 §2 참조.

## 1. watchlist.json — 유일한 데이터 소스

**위치**: `~/trade-pipeline/data/watchlist.json`

```json
{
  "stocks": [
    {"ticker": "NVDA", "name": "엔비디아", "market": "US", "sector": "AI Infrastructure"},
    ...
  ],
  "sector_base": {
    "Technology": 22, "Semiconductors": 18, ...
  }
}
```

**추가**: 단순히 배열에 새 객체 push
```json
{"ticker": "ANET", "name": "아리스타네트웍스", "market": "US", "sector": "Technology"}
```

**제거**: 해당 객체를 배열에서 삭제

### 종목 추가 5단계 (반드시 순서대로)

#### 1단계 — 티커 실재 검증
등록 전에 yfinance로 조회한다. 404면 등록 금지.

```bash
python3 -c "
import yfinance as yf
for t in ['APPL','AAPL']:
    try: print(t, yf.Ticker(t).info.get('longName'))
    except Exception as e: print(t, 'ERR', type(e).__name__, e)"
```

- `HTTP Error 404: Quote not found for symbol: XXX` → 존재하지 않는 심볼
- 사용자가 실수로 오타를 낸 경우 (예: `APPL` → `AAPL`) **추측 등록 금지**. "실제 심볼은 AAPL이며 이미 보유 중입니다"를 보고하고 등록하지 않는다.
- 검증 통과 시 참고값도 같이 뽑아둔다 (PE/PBR/ROE) — §6 검증 단계에서 적정가 대조에 쓴다.

#### 2단계 — 중복 확인
요청 목록과 watchlist를 교차 비교한다. 이미 있는 종목은 재추가하지 않는다.

```bash
python3 -c "
import json
d = json.load(open('~/trade-pipeline/data/watchlist.json'))
have = {s['ticker'] for s in d['stocks']}
print('기존:', sorted(have))"
```

보고 형식: "LIN/KO/WM/CB 신규, LLY·AAPL은 이미 보유 중, APPL은 존재하지 않는 티커" — 사용자가 무엇이 실제로 반영됐는지 한눈에 파악 가능하게.

#### 3단계 — sector_base 이중 동기화
새 섹터를 쓸 경우 **양쪽 모두**에 넣는다.

| 위치 | 키 | 역할 |
|:--|:--|:--|
| `data/watchlist.json` → `sector_base` | 섹터명 → base PER | watchlist가 읽는 기준 |
| `langgraph/src/fair_value.py` → `SECTOR_BASE` | 섹터명 → base PER | fair_value 계산 기준 |
| `scripts/finviz_screener.py` → 섹터 기준 dict | 섹터명 → base PER | 스크리너 계산 기준 |

한쪽만 넣으면 그 섹터의 종목은 `sector_base.get(sector, DEFAULT)`로 폴백되어 **조용히 틀린 적정PER**로 계산된다. 에러가 나지 않으므로 눈에 안 띈다.

#### 4단계 — 하드코딩 이름→티커 사전 제거
새 종목이 name→ticker 하드코딩 사전을 쓰는 소비자에게서 누락된다.

```bash
grep -rn 'NAME_TO_TICKER\s*=\s*{' ~/trade-pipeline/{scripts,langgraph}/ --include=*.py | grep -v __pycache__
grep -rn 'NAME_MAP\s*=\s*{' ~/trade-pipeline/{scripts,langgraph}/ --include=*.py | grep -v __pycache__
```

교체 패턴 — 중앙 로더(`scripts/stocks_config.py`)가 watchlist.json을 읽어 역방향 매핑을 생성:

```python
# stocks_config.py
NAME_TO_TICKER = {v["name"]: yahoo_ticker(t) for t, v in ALL_STOCKS.items()}
```

```python
# 소비 측 (paper_tracker.py / collect_consensus.py 등)
try:
    from stocks_config import NAME_TO_TICKER as _WATCH_NAME_TO_TICKER
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from stocks_config import NAME_TO_TICKER as _WATCH_NAME_TO_TICKER

# watchlist에 없는 종목 / 과거 명칭만 남는다
NAME_ALIASES = {"HD현대일렉트릭": "267260.KS", "HPE": "HPE", "구글": "GOOGL"}
NAME_TO_TICKER = {**_WATCH_NAME_TO_TICKER, **NAME_ALIASES}
```

주의:
- **소비자가 여러 곳에 흩어져 있으면 전부 교체**한다. 하나만 고치면 나머지가 조용히 누락된다 (fair_value.py / collect_consensus.py / paper_tracker.py / collect_recent_targets.py 등).
- alias는 watchlist 밖 종목·과거 명칭 **만** 남긴다. watchlist에 있는 종목명을 alias로 다시 선언하면 sync가 두 곳으로 갈라진다.
- 기존 사전이 이미 watchlist와 어긋나 있었을 수 있다 (예: `샌디스크→WDC`인데 watchlist는 `SNDK`). 교체 시 그대로 두면 과거 성과 데이터 해석이 바뀐다 — alias 설계 필요.

#### 5단계 — suffix 중복 확인
ticker에 이미 `.KS`가 들어있는데 `yahoo_suffix`도 `.KS`면 `267260.KS.KS`로 터진다.

```bash
python3 -c "
import json
d = json.load(open('~/trade-pipeline/data/watchlist.json'))
for s in d['stocks']:
    t, suf = s['ticker'], s.get('yahoo_suffix','')
    if suf and t.endswith(suf): print('중복:', t, suf)"
```

- `yahoo_suffix`는 **ticker에 접미사가 없을 때만** 채운다. `267260.KS`면 `yahoo_suffix: ""`.
- 소비 코드(`stocks_config.yahoo_ticker()`)에도 방어 로직을 넣는다:
  ```python
  def yahoo_ticker(ticker: str) -> str:
      suffix = ALL_STOCKS.get(ticker, {}).get("yahoo_suffix", "")
      if not suffix: return ticker
      if ticker.endswith(suffix): return ticker   # 중복 방지
      return ticker + suffix
  ```

### 섹터 규칙
- 섹터는 `sector_base`에 정의된 값만 사용
- yfinance 섹터가 틀렸으면 적절한 `sector_base` 값으로 수동 지정
- 새 섹터 필요시 §1 3단계대로 3곳에 항목 추가 (base PER 참고: tech 22, semi equip 22, industrial 15, energy 10)

### 변경 후
```bash
cd ~/trade-pipeline && git add -A && git commit -m "watchlist: add/remove ..." && git push
```
→ **git push 필수** (사용자 추적을 위해)

⚠️ `data/watchlist.json`은 `.gitignore`(`data/*.json`)로 git 추적에서 제외된다. 로컬 단일 진실이며 서버/다른 환경에 자동 반영되지 않는다. 그래서:
- 코드 측 변경(`stocks_config.py`, `fair_value.py`, 소비 스크립트)은 커밋·push 대상.
- watchlist.json 자체는 커밋되지 않으므로, 공유가 필요하면 저장소 정책 확인 후 `git add -f` 여부를 사용자에게 물을 것 — 임의로 강제 추가하지 않는다.

## 6. 검증 (수정 후 반드시 실제 실행)

```bash
# ① 로더 — 종목 수 & suffix 조합 확인
cd ~/trade-pipeline/scripts && python3 -c "
import stocks_config as sc
print('종목 수:', len(sc.ALL_STOCKS))
for t in ['267260.KS','005930.KS','LIN']: print(t, '→', sc.yahoo_ticker(t))
print({n: sc.NAME_TO_TICKER.get(n) for n in ['린드','삼성전자','LG이노텍']})"

# ② 밸류에이션 — 신규 종목이 적정가 표에 뜨는가
cd ~/trade-pipeline && python3 langgraph/src/fair_value.py

# ③ 소비 스크립트 — 정상 동작 & 누락 없음
cd ~/trade-pipeline && python3 scripts/collect_consensus.py
cd ~/trade-pipeline && python3 scripts/paper_tracker.py
```

- 모든 티커가 정상 출력되는지 확인
- **신규 종목이 섹터·적정PER·T1 목표가와 함께 표에 나타나는지** 확인 (미노출 = 매핑 누락)
- 섹터가 의도대로 반영되었는지 적정PER 컬럼 확인
- 신규 종목은 analyst target 유무도 확인 (US는 Finnhub/upgrades_downgrades 자동)

## 2. 데이터 품질 엣지 케이스

### SPCX (SpaceX) — 비상장 기업
- SPCX는 yfinance에 데이터가 있지만 **SpaceX는 아직 상장 전** (pre-IPO)
- fair_value 실행 시 `⚠️ 데이터 불충분` 출력 — 정상 동작, 제거 불필요
- yfinance가 SPAC/쉘 컴퍼니 정보를 잘못 매핑한 케이스

### KLA analyst target $2,250 vs 실제 주가 $249
- 가끔 upgrades_downgrades에서 analyst target이 단위 오류(10배)로 수집됨
- KLA 사례: Wolfe Research/Barclays target $2,250 (주가 $249의 9배) → 데이터 오류
- **대응**: fair_value.py output에서 오차율 > 80%면 데이터 오류 의심하고 리포트에 주석

### 데이터 불충분 종목 (INTC 패턴)
- INTC는 yfinance FPE/Forward EPS 누락으로 `⚠️ 데이터 불충분`
- 제거하지 않고 watchlist에 유지 (yfinance 데이터가 복구될 수 있음)
- fair_value.py 출력에만 표시, pipeline LangGraph에서는 자동 제외

### ADR 티커 suffix 혼동
- `SKHY` (SK hynix USD ADR) vs `SKHYY` (404), `005930.KS` (KR본주) vs `005930` — 이들 혼동은 silent corruption이다.
- 검증은 §1 1단계 yfinance 404 체크로 잡힌다.

### 패치 후 JSON 전체 재검증 (인접 값 손상 방지)
JSON 배열을 텍스트 patch로 편집하면 **옆 항목이 실수로 손상**된다 (예: `SKHY` → `SKHYY`). 패치가 성공했다고 종료하지 말고, 파일 전체를 재검증한다.

```bash
python3 -c "
import json, yfinance as yf
d = json.load(open('~/trade-pipeline/data/watchlist.json'))
bad = []
for s in d['stocks']:
    t = s['ticker']
    try: yf.Ticker(t).info.get('longName')
    except Exception: bad.append(t)
print('총', len(d['stocks']), '종목 / 404:', bad)"
```

- 404가 나온 ticker가 **패치 전에는 정상**이었다면 패치가 값을 망가뜨린 것이다 → 즉시 원복.
- JSON 파싱 에러가 나면 trailing comma / 중괄호 불일치 → §1 5단계 표에서 구조 확인.

### yfinance `.history()` 빈 결과
- 티커가 살아있어도 `.history(start=..., end=...)` 구간에 데이터가 없으면 빈 DataFrame이 돌아온다. 정상 종목이면 100행 이상 나오는 것을 확인.
