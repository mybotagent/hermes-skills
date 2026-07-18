# Naver Polling `cr` (등락률) 부호 반전 버그

> 발견일: 2026-07-17
> 상태: ✅ `fetch_kr_stocks.py`로 해결됨

## 문제

오전 포트폴리오 브리핑(08:10 KST)에서 한국주 등락률 부호가 반전됨.
예: 삼성전자 실제 -8.77% → 브리핑에 **+8.77%**로 표시

## 원인

`polling.finance.naver.com/api/realtime` API의 `cr`(등락률) 필드는
**항상 절대값(양수)** 이다. 부호를 제공하지 않는다.

```json
// Naver Polling 응답 예 (005930)
{
  "nv": 255000,    // 현재가
  "pcv": 279500,   // 전일종가
  "cr": 8.77       // ⚠️ 항상 양수! 실제는 -8.77%
}
```

## 해결

1. `fetch_kr_stocks.py`를 반드시 사용할 것 (절대 raw API 직접 호출 금지)
2. 이 스크립트는 `nv - pcv`로 부호를 직접 계산함

```bash
cd ~/trade-pipeline && python3 scripts/fetch_kr_stocks.py
```

## Single Source of Truth (SSoT)

- `fetch_kr_stocks.py`는 `data/watchlist.json`에서 종목 코드를 읽음
- 하드코딩된 코드 목록 금지 (이전 버그: 298040 = 효성중공업, HD현대일렉 아님)
- 정확한 코드: 267260 = HD현대일렉트릭

## 검증

Naver 응답의 `nm`(회사명) 필드로 코드 정확성 검증:
```python
nm_naver = item.get('nm', '')
if nm_naver and nm_naver != expected_name:
    # 코드가 잘못되었음을 자동 감지
```
