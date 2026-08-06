# 네러티브 & 순환매 분석 프레임워크 (2026-08-06)

사용자 요구: "네러티브와 순환매도 고려해줘" / "모든 뉴스에 대해서" — PER 수치 단독 판단 금지, 시장 스토리 + 자금 흐름을 함께 봐야 함.

## 종목별 3요소 분석

| 요소 | 내용 | 수집 방법 |
|:-----|:-----|:---------|
| **네러티브** | 시장이 말하는 스토리 (불/곰) | Google News RSS 헤드라인 5건/종목 |
| **순환매** | 자금 유입/이탈 방향 | 최근 7~10일 주가 흐름 + 섹터 뉴스 |
| **가격·PER** | 현재가 + Fwd/Trailing P/E | CNBC quote API 또는 yfinance (rate-limit 주의) |

## Google News RSS 쿼리 패턴

```python
import urllib.request, urllib.parse, xml.etree.ElementTree as ET

def news(q, hl='en', gl='US', n=5):
    url = f'https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl={hl}&gl={gl}&ceid={gl}:{hl}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    root = ET.fromstring(resp.read().decode('utf-8', errors='replace'))
    return [(i.findtext('title',''), i.findtext('pubDate','')) for i in list(root.iter('item'))[:n]]
```

- **US 종목**: `f"{ticker} stock outlook 2026"` (영문, hl=en)
- **한국 종목**: `"삼성전자 주가 전망 2026"` (한글, hl=ko, gl=KR, ceid=KR:ko)
- 뉴스 사이트 직접 크롤링 금지 (403/404 차단됨) — RSS만 사용

## 가격/P/E API fallback 체인

1. yfinance `Ticker.info` — **rate-limit(429) 빨리 걸림** (여러 티커 연속 조회 시)
2. CNBC quote API — Yahoo 429 발생 시 대체로 안정적
   ```
   https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=SNDK&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json
   ```
3. stockanalysis.com API — 404로 실패 (사용 금지)

## 대량 종목 병렬 조사 (delegate_task 패턴)

30개+ 종목이면 **클러스터당 ≤6종목, 3개 배치**로 병렬 위임:

```
배치 1: 미국 반도체·메모리 (NVDA, AMD, AVGO, MU, TSM, MRVL, INTC, STX, WDC, SNDK, SKHYY)
배치 2: 장비·광학·빅테크 (LRCX, ASML, KLAC, TER, LITE, COHR, GOOGL, AAPL, MSFT, DELL, ANET, CLS)
배치 3: 한국주 + 기타 (삼성전자, 현대차, HD현대일렉, LG이노텍, LLY, SPCX, BE, BWXT, ALB)
```

- **배치당 종목 수 제한**: 9개+는 600초 타임아웃 위험 (실제 발생: 배치 3 타임아웃). 6개 이하 권장.
- 각 서브에이전트 context에: 기준일 명시 (예: "오늘은 2026-08-06"), 한국어 응답 요청, RSS-only 규칙, "각 종목 3~5줄 요약" 지시.
- 서브에이전트 결과는 self-report — **정량 수치는 직접 재검증** (기준일 표기 확인).
- 타임아웃 발생 배치는 **직접 조사로 대체** (RSS 3~4건/종목이면 충분).

## 2026-08-06 실제 분석 결과 요약 (참고용 기준치)

- SK하이닉스 Q2 2026: 영업이익 ₩60.5조 (+557% YoY, 사상 최대)지만 **컨센서스 미스** → 7/28 -14.7%, 7/29 -9.6% → 이후 +30% 반등 (월가 목표가 상향 쇄도)
- **메모리 3인방 (MU/SNDK/SKHYY) Fwd P/E 5~8x** = 사이클 정점 할인 (저평가 아님에 주의)
- **진짜 이탈은 장비주** (KLAC/LRCX/TER 고점 대비 -30~-37%)
- **순환매 수혜**: 전력 (HD현대일렉 +3.16%, 영업익률 27%), 원자력 (BWXT, BE), 실적 확정 AI 인프라 (ANET, COHR)
- **"셀 더 뉴스" 패턴**: 실적 서프라이즈 + 가이던스 약화 = 급락 (AAPL 시총 -$5,000억)

## 판정 원칙

1. 낮은 PER + 피크아웃 내러티브 → "관망" (매수는 2027 EPS 전망 상향 확인 후)
2. 순환매 이탈 중 → 비중 점검
3. 실적발표 후 급락 = 차익실현 국면 → 다음 분기 가이던스 확인 전 매수 금지
4. 모든 수치 표시에 **기준일** 명시 (Pitfall 52)
