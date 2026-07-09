# Trade-Pipeline Migration (2026-06-08)

## 배경
모든 트레이딩 관련 코드를 단일 레포 `mybotagent/trade-pipeline`으로 통합. 구 `trading-agents-nuri-*` 레포 5개는 모두 GitHub ARCHIVED 처리 및 로컬 삭제.

## 작업 디렉토리
```bash
~/trade-pipeline/          # 유일한 작업 디렉토리
  ├── langgraph/           # Python 소스 코드
  │   ├── pipeline.py      # 메인 파이프라인 (Phase 0→0.5→1→2→3)
  │   └── src/             # 모듈
  │       ├── agents/      # LangGraph agents
  │       ├── utils/       # deepseek.py, macro_strategy.py
  │       ├── fair_value.py
  │       ├── collect_macro_context.py
  │       ├── macro_strategy_report.py
  │       └── ...
  ├── data/                # 생성 데이터 (daily)
  ├── logs/                # 히스토리
  └── .env                 # API keys (DATA_DIR=/home/ubuntu/trade-pipeline/data)
```

## PATH 주의
- `langgraph/` 서브디렉토리 때문에 `os.path.dirname()` 계산이 한 레벨 더 깊음
- `load_dotenv()`가 `.env`를 찾으려면 `os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` = `trade-pipeline/`
- `sys.path.insert()`에도 `langgraph/` 디렉토리를 추가해야 `from src.xxx import` 가능

## 크론 경로 (모든 cron: `~/trade-pipeline`)
- 08:10: `cd ~/trade-pipeline && python3 langgraph/src/analyst_target_collector.py && python3 langgraph/src/fair_value.py`
- 18:00: `cd ~/trade-pipeline && python3 langgraph/src/fair_value.py`
- 18:35: `cd ~/trade-pipeline && python3 langgraph/pipeline.py`
- 월 1일: `cd ~/trade-pipeline && python3 langgraph/src/monthly_performance_review.py`
- 월 1일: `cd ~/trade-pipeline && python3 langgraph/src/macro_strategy_report.py`

## ARCHIVED 레포 (GitHub 읽기전용)
| 레포 | 내용 |
|------|------|
| `mybotagent/trading-agents-nuri` | 구 멀티 에이전트 시스템 |
| `mybotagent/trading-agents-nuri-cron` | 구 크론 스크립트 |
| `mybotagent/trading-agents-nuri-feedback` | 구 피드백 루프 |
| `mybotagent/trading-agents-nuri-langgraph` | 구 LangGraph 파이프라인 |
| `mybotagent/trading-agents-nuri-scripts` | 구 파이프라인 스크립트 |

## 변경 이력
- 2026-06-07: `~/trading-agents-nuri/` → 단일 통합 레포
- 2026-06-08: `~/trading-agents-nuri/` → `~/trade-pipeline/` 이전. 구 레포 5개 ARCHIVED + 로컬 삭제. 모든 크론 경로 업데이트.
