# Analyst Target Only Policy

> 사용자 교정 (2026-06-07): "내 의견 넣지 말고 애널리스트 목표주가 의견만 사용해"

## 핵심 규칙

1. **절대 금지**: `KR_KNOWN_TARGETS` 같은 하드코딩된 개인 target 값
2. **절대 금지**: 너구리/사용자 제공 값을 `latest_target`으로 사용
3. **절대 금지**: 개인 의견 vs 컨센서스 비교 출력 ("너구리제공 vs Naver X% 차이")

## KR 종목 = 네이버 컨센서스 스크래핑 (유일)

| 종목 | 네이버 컨센서스 | 이전 (너구리) | 비고 |
|:-----|:---------------:|:-------------:|:-----|
| 삼성전자 | ₩426,250 | ~~₩500,000~~ | 컨센서스가 더 보수적 |
| SK하이닉스 | ₩2,707,917 | ~~₩4,000,000~~ | 큰 차이 — analyst 의견 채택 |
| 현대차 | ₩775,385 | 없음 | ✅ |
| HD현대일렉 | ₩1,468,571 | 없음 | ✅ |
| 삼성전기 | ₩1,679,600 | 없음 | ✅ |
| 에이피알 | ₩508,421 | 없음 | ✅ |

## 구현 상세

```python
def get_kr_targets():
    results = {}
    for code, name in KR_TICKERS.items():
        consensus = get_kr_naver_consensus(code.replace('.KS','').replace('.KQ',''))
        if consensus:
            item['latest_target'] = consensus
            item['source'] = '네이버컨센서스'
        else:
            item['latest_target'] = None
            item['source'] = '데이터없음'
```

## 스크래핑 방식

- **URL**: `https://finance.naver.com/item/coinfo.naver?code=005930`
- **인코딩**: `euc-kr`
- **Referer 헤더 필수** (없으면 차단)
- **목표가 추출**: `<em>426,250</em>` → 정규식 매치
- **함수**: `get_kr_naver_consensus(code)` in `analyst_target_collector.py`
