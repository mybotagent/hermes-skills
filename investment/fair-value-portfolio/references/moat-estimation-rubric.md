# Moat 점수 LLM 추정 루브릭 (2026-06-08 v2)

**변경 이력**: 
- v1 (2026-06-06): stock-rating-system 스킬의 Moat 가중치 35% 기반 점수
- v2 (2026-06-08): 사용자 "Gap과 해자만 활용" + "LLM이 추정하기" → 포트폴리오 비중 내에서 LLM이 직접 추정

## LLM 추정 방식

Phase 3 (`portfolio_allocation.py`)의 `summarize_stock()` 함수가 LangGraph 분석 결과 (context_analysis + bull/bear/risk_case + rationale)를 DeepSeek V3로 **3~5줄 요약**할 때, 요약에 해자 정보가 자연스럽게 포함됨.

이 요약 + 정량 데이터(t1_gap, PER, FwdPER)를 바탕으로 Phase 3 DeepSeek V4 Flash가 moat 점수 추정.

## 루브릭 (PROMPT에 포함)

```
해자 요소: 특허·독점, 네트워크효과, 전환비용, 브랜드파워, 규제장벽
9~10: ROE 30%↑ + 영업이익률 30%↑ + 독점적 지위 (NVDA, MSFT, GOOGL 등)
7~8:  ROE 15~30% + 이익률 15~30% + 강한 시장지위
5~6:  ROE 10~15% + 이익률 5~15% + 차별화 보통
3~4:  ROE 5~10% + 차별화 약함, 경쟁 심함
1~2:  ROE 0~5% or 적자, 진입장벽 없음
```

## 2026-06-08 실행 결과 예시

| 종목 | 해자 | 근거 |
|------|:---:|------|
| 엔비디아 | **10** | GPU 독점 + CUDA 생태계 |
| 브로드컴 | **9** | 네트워킹/VmWare 독점 |
| SK하이닉스 | **8** | HBM 선두 |
| 삼성전자 | **8** | 종합 반도체 |
| 마이크론 | **7** | HBM 경쟁력 |
| HPE | **5** | 서버 상품화, 차별화 약함 |
| 샌디스크 | **5** | NAND 상품화, 경쟁 심함 |

## 주의사항

- LLM이 bull/bear/risk text만 보고 추정하므로, context_analysis에 ROE나 이익률 정보가 부족하면 정확도 떨어짐
- Phase 2 LangGraph context agent가 충분한 재무 데이터 인용하도록 프롬프트 설계 중요
- 해자 점수는 정성 평가 — 동일 종목도 LLM 실행마다 1~2점 차이날 수 있음
- LLM이 15% 상한을 자주 위반하므로 프롬프트에 강조 필요 (2026-06-08 실행: 브로드컴 19%)

## 수식

```
가중값 = max(0, t1_gap) × moat_점수
기본_비중 = (가중값 / 총_가중값) × (100% - 현금비중)
```
