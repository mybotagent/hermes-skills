# Cron Testing: bg-review Limitation

> 크론을 수동 테스트할 때 `cronjob action='run'`이 실패하는 이유와 올바른 방법

## 증상

```
cronjob(action='run', job_id='6297df83d4f3')
→ {"success": true, ...last_status: "ok"}
```

크론이 실행된 것처럼 보이지만 `last_run_at`이 갱신되지 않고, Discord로 결과도 안 옴.

## 원인

`cronjob action='run'`이 생성하는 **bg-review 세션**은 다음과 같은 툴 제한이 있음:

| 툴 | bg-review 허용 여부 | 이유 |
|:---|:------------------:|:-----|
| `memory` | ✅ 허용 | 세션 정보 저장 |
| `skill_view` / `skills_list` | ✅ 허용 | 스킬 로드 |
| `terminal` | ❌ **차단** | 실제 실행 차단 |
| `patch` / `write_file` | ❌ **차단** | 파일 수정 차단 |
| `web_search` / `browser_*` | ❌ **차단** | 웹 접근 차단 |

실제 크론(스케줄에 의해 자동 실행)은 정상적인 LLM 세션에서 실행되므로 모든 툴 사용 가능.

## 올바른 테스트 방법

### 방법 1: 직접 terminal() 호출 (권장)

```python
# Phase별 순차 실행
terminal('cd ~/trade-pipeline && python3 langgraph/src/analyst_target_collector.py > data/analyst_stdout.txt')
terminal('cd ~/trade-pipeline && python3 langgraph/src/fair_value.py > data/fair_value_stdout.txt')
terminal('cd ~/trade-pipeline && python3 langgraph/pipeline.py')
```

**왜 순차 실행이 필수인가?**
- `data/analyst_stdout.txt` → Phase 0이 읽음
- `data/fair_value_stdout.txt` → Phase 0이 읽음  
- `data/daily_snapshot.json` → Phase 1이 읽음
- `data/filtered_top10.json` → Phase 2가 읽음
- `macro_context.json` → Phase 0.5가 생성 → Phase 2/3이 읽음

이 파일 체인이 깨지면 Phase 2/3이 데이터 없이 실행됨.

### 방법 2: 각 Phase 독립 실행

```bash
python3 langgraph/pipeline.py --phase 0    # stdout → daily_snapshot.json
python3 langgraph/pipeline.py --phase 05   # Finnhub + FRED 수집
python3 langgraph/pipeline.py --phase 1    # T1-gap 필터
python3 langgraph/pipeline.py --phase 2    # LangGraph
python3 langgraph/pipeline.py --phase 3    # 포트폴리오 비중
```

## 크론 자동 실행 확인

테스트는 위 방법으로 하고, 실제 자동 실행은 평일 스케줄에 맡길 것:

| 크론 | 시간 | 테스트 명령어 |
|:-----|:----|:-------------|
| 08:10 포트폴리오 | `10 8 * * 1-5` | `cd ~/trade-pipeline && python3 langgraph/src/analyst_target_collector.py && python3 langgraph/src/fair_value.py` |
| 18:00 US 브리핑 | `0 18 * * 1-5` | `cd ~/trade-pipeline && python3 langgraph/src/fair_value.py` |
| 18:30 매크로 | `30 18 * * 1-5` | LLM web_search (cron prompt에 의존) |
| 18:35 LangGraph | `35 18 * * 1-5` | `cd ~/trade-pipeline && python3 langgraph/pipeline.py` |

## 관련 이슈

- Hermes Agent bg-review 제한: 의도된 설계 (리뷰 모드는 읽기 전용)
- 우회 불가능 — 크론 자체의 문제가 아니라 bg-review 컨텍스트의 제한
- 평일 자동 실행 시에는 정상 작동 확인됨
