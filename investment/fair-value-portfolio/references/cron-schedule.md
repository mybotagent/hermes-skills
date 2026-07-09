# Cron Schedule (Snapshot: 2026-06-08)

9개 크론, 평일(월~금) 기준. 주말 OFF. **모든 LLM prompt 크론으로 전환 완료** (no_agent script 사용 금지).

| # | 시간 | 작업 | 유형 | 실행 경로 | job_id | 주말 |
|:-:|:----:|:-----|:----:|:---------|:------:|:----:|
| 1 | 04:00 | 📚 Wiki 동기화 + 메모리 정리 | LLM prompt | - | 64adaa1d6b0e | OFF |
| 2 | 08:00 | 📅 구글 캘린더 일정 요약 | Skill | google-workspace | 2f553ea20e27 | OFF |
| 3 | 08:10 | 📊 포트폴리오 + 한국/미국 브리핑 | Skill + LLM prompt | `~/trade-pipeline/langgraph/src/analyst_target_collector.py` + `fair_value.py` | 6297df83d4f3 | OFF |
| 4 | 08:30(월) | 📅 주간 계획 알림 | Skill | google-workspace | 47f701ea2755 | 월 only |
| 5 | **18:00** | **🇺🇸 미국 증시 브리핑** | **Skill + LLM prompt** | `~/trade-pipeline/langgraph/src/fair_value.py` | **2916cc9c2ceb** | **OFF** |
| 6 | **18:30** | **🌍 매크로 전략 리포트** | **LLM prompt** | web_search + LLM | **b96583fa9d27** | **OFF** |
| 7 | **18:35** | **🧠 LangGraph 파이프라인** | **LLM prompt** | `cd ~/trade-pipeline && python3 langgraph/pipeline.py` → **5개 메시지 분할 전송** | **afebf6cb0ab1** | **OFF** |
| 8 | 08:00(1일) | 📈 월간 전략 리포트 | LLM prompt | `cd ~/trade-pipeline && python3 langgraph/src/macro_strategy_report.py` | d3080e6f3789 | OFF |
| 9 | 08:10(1일) | 📈 월간 성과 검증 리포트 | LLM prompt | `cd ~/trade-pipeline && python3 langgraph/src/monthly_performance_review.py` | 18510b01362d | OFF |

## 크론 역할 구분

- **08:10 (스킬)**: 한국장 개장 전, analyst_target_collector.py + fair_value.py 실행 → Discord 브리핑
- **18:00 (스킬)**: 미국장 개장 전, 동일 스크립트 재실행 → Discord 브리핑 (한국/미국 가격 차이 반영)
- **18:30 (LLM)**: web_search로 글로벌 매크로 데이터 수집 → 리포트 → macro_context.json 저장
- **18:35 (no_agent)**: pipeline.py 실행 → 저장된 stdout + macro_context.json 읽어서 LangGraph 분석

## 데이터 흐름

```
08:10 ─── fair_value_stdout.txt + analyst_stdout.txt (저장)
18:00 ─── fair_value_stdout.txt + analyst_stdout.txt (갱신)
18:30 ─── macro_context.json (저장)
           ↓
18:35 ─── pipeline.py
           ├─ Phase 0: 저장된 stdout 파일 읽기 → daily_snapshot.json
           ├─ Phase 0.5: macro_context.json 읽기
           ├─ Phase 1: midpoint gap filter (인라인) → filtered_top10.json
           ├─ Phase 2: LangGraph → logs/decisions/
           └─ Phase 3: portfolio allocation → logs/portfolio/
```

## 이전 크론 ID (변경 이력)

제거된 크론:
- `b5bbf669cd51` (old 18:00 US 브리핑) → `2916cc9c2ceb`로 대체 (repo 경로 변경)
- `e69746446a65` (old 18:30 매크로, 18:00 통합으로 잘못 변경됨) → `b96583fa9d27`로 대체
- `62e57fc30547` (old 18:35 파이프라인) → `afebf6cb0ab1`로 대체 (repo 경로 변경)

## 주의

- **절대 기존 크론을 함부로 제거하지 말 것**: 08:10=한국, 18:00=미국, 18:30=매크로, 18:35=파이프라인은 각각 다른 목적의 별개 작업
- 크론 제거/변경 전: `cronjob action=list` → 사용자 승인
