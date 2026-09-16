# CNBC XML + Naver Polling API — 검증된 데이터 소스 (2026-09-10)

> Created: 2026-09-10
> Context: 18:30 매크로 크론에서 CNBC XML API + Naver Polling이 subagent보다 안정적임을 실증

## 검증된 소스 (모두 cron 모드 동작 확인)

### CNBC XML REST API — US 글로벌 지표 (1순위)

**Base URL**: `https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols={SYMBOL}&requestMethod=itk`

**⚠️ 중요 규칙**
- 심볼당 **1회 호출 + sleep 1초** — 다중 심볼(`,` 구분) 요청 시 `<code>1</code>` 에러
- 반드시 개별 호출 루프 사용

**검증된 심볼** (2026-09-10):
```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# WTI 유가
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=@CL.1&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# S&P 500
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.SPX&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# DXY 달러인덱스
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.DXY&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# US 10년물 금리
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=US10Y&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# KOSPI
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.KS11&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# KOSDAQ
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.KQ11&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# VIX
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=.VIX&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'

# 금값 (Gold)
curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=@GC.1&requestMethod=itk" \
  -H "User-Agent: $UA" | grep -oP '<last>[^<]+</last>|<change_pct>[^<]+</change_pct>'
```

**응답 필드** (`<last>`, `<change_pct>`, `<change>`, `<previous_day_closing>` 전부 사용 가능)

---

### open.er-api.com — USD/KRW 환율 (1순위)

```bash
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" -o /tmp/usd.json
grep -o '"KRW":[0-9.]*' /tmp/usd.json
# → "KRW":1339.004703
```

---

### Naver Polling API — 한국 6종목 실시간 시세 (1순위)

**⚠️ 6자리 KRX 코드** (.KS/.KQ suffix 없음), **EUC-KR 디코딩 필수**

**검증된 6종목** (2026-09-10):
| 종목 | 코드 | Naver nm |
|:-----|:-----|:---------|
| 삼성전자 | 005930 | 삼성전자 |
| SK하이닉스 | 000660 | SK하이닉스 |
| 삼성전기 | 009150 | 삼성전기 |
| 현대차 | 005380 | 현대차 |
| 에이피알 | 278470 | 에이피알 |
| HD현대일렉트릭 | 267260 | HD현대일렉트릭 |

```bash
UA="Mozilla/5.0"
for code in 005930 000660 009150 005380 278470 267260; do
  curl -sL --max-time 12 "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:$code" \
    -H "User-Agent: $UA" -o /tmp/naver_$code.raw
  python3 -c "
import json
raw=open('/tmp/naver_$code.raw','rb').read()
d=json.loads(raw.decode('euc-kr',errors='ignore'))
data=d['result']['areas'][0]['datas'][0]
print(f'$code: price={data[\"nv\"]:,} prev={data[\"pcv\"]:,} change={data[\"cv\"]:+,} ({data[\"cr\"]:+.2f}%)')
"
done
```

**응답 필드**:
| key | 의미 | 예시 |
|:----|:-----|:-----|
| `nv` | 현재가 | 269000 |
| `cv` | 전일비 (부호포함) | -500 |
| `cr` | 전일비율 (%, 부호포함 문자열) | "-0.19" |
| `pcv` | 전일종가 | 269500 |

**⚠️ `cr` 필드는 문자열 절대값** — 반드시 `nv - pcv`로 부호 계산

**⚠️ HD현대일렉트릭 코드 혼동 주의**:
- `267260` = HD현대일렉트릭 (전력기기, 시총 30조+) ✅
- `267270` = HD건설기계 (건설중장비, 시총 1.2조) ❌

---

## Cron 모드 실행 패턴 (2026-09-10 확인)

```bash
# 1단계: 글로벌 지표 (CNBC XML, 순차 호출)
UA="Mozilla/5.0"
for sym in @CL.1 .SPX .DXY US10Y .KS11 .KQ11 .VIX @GC.1; do
  curl -sL --max-time 12 "https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=$sym&requestMethod=itk" \
    -H "User-Agent: $UA" -o /tmp/cnbc_$(echo $sym | tr '.@' '_').xml
  sleep 1
done

# 2단계: 환율 (open.er-api)
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" -o /tmp/usd.json

# 3단계: 한국 6종목 (Naver Polling, 병렬 불가 — 순차)
for code in 005930 000660 009150 005380 278470 267260; do
  curl -sL --max-time 12 "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:$code" \
    -H "User-Agent: $UA" -o /tmp/naver_$code.raw
done

# 4단계: Python으로 파싱 + JSON 조립
python3 -c "... (파싱 로직) ..."
```

---

## 저장 위치

- `~/trading-agents-nuri/data/macro_context.json` (GitHub 백업용)
- 두 레포 모두 업데이트: `cp ~/trading-agents-nuri/data/macro_context.json ~/trade-pipeline/data/macro_context.json`

---

## Subagent 사용 제한

**뉴스는 subagent에게 위임 가능** (정성 데이터, fabrication 위험 낮음).
**정량 수치(환율, 금리, 유가, 지수, 주가)는 반드시 위 API 직접 수집** — subagent hallucination 위험 높음 (실제 사례: USD/KRW 1,315 보고 → 실제 1,516.97, -13.3% 오차).
