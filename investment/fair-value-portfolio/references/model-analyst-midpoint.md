# Model T1 vs Analyst Target 중간값 절충 기법

> ⛔ **DEPRECATED (2026-06-08)**: 2026-06-08 사용자 결정으로 `t1_gap`이 `midpoint_gap`을 대체했습니다.
> Phase 1 필터와 Phase 3 비중 결정 모두 **순수 T1 괴리율(T1_gap)** 을 사용합니다.
> Analyst Target은 리포트 표시용으로만 유지 — 필터링/비중 결정에 미사용.
> 상세: `references/t1-gap-vs-midpoint.md`

> **목적**: Model T1(fair_value_v3 계산)과 Analyst Target(시장 컨센서스)의 차이를 절충하여 신뢰도 높은 목표가 산출. (2026-06-07까지 사용, 현재는 대체됨)

## 계산식

```python
if analyst_target_exists and analyst_target > 0:
    midpoint = (model_t1_price + analyst_target_price) / 2
    midpoint_gap = (midpoint / current_price - 1) * 100
else:
    # 30일 내 Analyst Target 없으면 Model T1 단독 사용
    midpoint = model_t1_price
    midpoint_gap = t1_gap
```

## 판단 기준

| Analyst 동의도 | Model-Target 갭 | midpoint_gap | 판단 |
|:-------------|:--------------:|:------------:|:----|
| ✅ 거의 일치 | ±5% 미만 | 30%↑ | 신뢰도 HIGH — 적극 매수 검토 |
| ✅ 양호 | ±5~20% | 30%↑ | 신뢰도 MEDIUM — Analyst도 동의 |
| ⚠️ 갭 큼 | ±20%↑ | 30%↑ | 신뢰도 LOW — Model 독자 판단, 추가 확인 필요 |
| ❌ Analyst 없음 | N/A | (T1 gap) | Model 단독 판단, 보수적 접근 |

## 구현

- `trading-agents-nuri/src/midpoint_filter.py` — Phase 1: 24종목 → 필터 → 상위 10종목
- `trading-agents-nuri/src/capture_and_save.py` — Phase 0: 기존 스크립트 stdout 캡처 → JSON

## NAME_TO_TICKER 매핑 (midpoint_filter.py 사용)

fair_value_v3.py의 한글/영문 종목명을 analyst_target_collector.py의 ticker 키와 매칭:

```python
NAME_TO_TICKER = {
    # US
    "엔비디아": "NVDA", "마이크론": "MU", "램리서치": "LRCX",
    "시게이트": "STX", "샌디스크": "SNDK", "TSMC": "TSM",
    "AMD": "AMD", "테라다인": "TER", "브로드컴": "AVGO",
    "루멘텀": "LITE", "마블테크": "MRVL", "HPE": "HPE",
    "Celestica": "CLS", "알파벳": "GOOGL", "애플": "AAPL",
    "마이크로소프트": "MSFT", "델": "DELL", "일라이릴리": "LLY",
    # KR
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS",
    "삼성전기": "009150.KS", "현대차": "005380.KS",
    "에이피알": "278470.KQ", "HD현대일렉": "267260.KS",
}
```

> **주의**: fair_value_v3.py의 종목명 출력 형식이 변경되면 이 매핑도 함께 업데이트 필요.

## 참고

- Analyst Target이 없어도 Model T1이 높으면 통과 가능 (예: HPE, Analyst 없음 but T1 +128%)
- 단, Analyst 없는 종목은 Decision Maker(R1)에서 "Analyst 부재 = 신뢰도 LOW"로 가중치 부여 필요
