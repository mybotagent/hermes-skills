# 최신 개별 Analyst Target 수집 방법

> 생성: 2026-06-03 | 목적: stale consensus 평균 대신 최신 개별 analyst target 사용

## 배경

`yfinance.info['targetMeanPrice']`는 consensus 평균으로 weeks~months stale.
2026-06-02 MU 증례: strong_buy 추천에 mean target $726 vs 실제 Susquehanna $1,750(5/29)

## US 종목 — upgrades_downgrades

```python
s = yf.Ticker(ticker)
ud = s.upgrades_downgrades
if ud is not None and not ud.empty:
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    recent = ud[ud.index >= cutoff]
    if recent.empty:
        recent = ud.head(5)
    latest_target = recent.iloc[0]['currentPriceTarget']
    latest_firm = recent.iloc[0]['Firm']
    latest_date = recent.index[0].strftime('%m/%d')
```

### 30일 window 검증

```python
all_targets = recent['currentPriceTarget'].tolist()
high_30d = max(all_targets)
low_30d = min(all_targets)
avg_30d = sum(all_targets) / len(all_targets)

if abs(latest_target / avg_30d - 1) > 0.30:
    confidence = 'MEDIUM'
if (high_30d / low_30d - 1) > 1.0:
    confidence = 'MEDIUM'
```

## KR 종목

yfinance upgrades_downgrades 미지원 (HTTP 404).
- **삼성전자**: ₩500,000 (너구리 제공)
- **SK하이닉스**: ₩4,000,000 (너구리 제공)
- **기타**: 네이버 증권 컨센서스 (fallback)

## 신뢰도 기준

| 신뢰도 | 조건 | 대응 |
|:-----:|:-----|:-----|
| HIGH | 가격범위 0.3~5x + 30일 평균 ±30% + range 폭 <100% | 그대로 사용 |
| MEDIUM | 조건 중 1~2개 위반 | 사용하되 리포트 주의 표기 |
| LOW | 가격범위 위반 또는 다수 조건 위반 | 30일 평균으로 대체 |

## 관련 스크립트

```bash
./hermes-agent/venv/bin/python3 scripts/analyst_target_collector.py
```
