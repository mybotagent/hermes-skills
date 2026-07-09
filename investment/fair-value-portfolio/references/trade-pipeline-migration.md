# 2026-06-08: trade-pipeline 완전 이전 (최종 통합)

## 변경사항
- **ACTIVE REPO**: `mybotagent/trade-pipeline` → `~/trade-pipeline/` (유일 활성)
- **구조**: `langgraph/`에 모든 Python 소스 (`langgraph/pipeline.py`, `langgraph/src/...`)
- **PATH 주의**: `os.path.dirname` depth가 3~4로 증가 (langgraph/ 서브디렉토리 때문)

## GitHub 아카이브 (전체 7개, 전부 ARCHIVED + 로컬 삭제 완료)

| 구 레포 | 아카이브일 | trade-pipeline 내 위치 |
|:--------|:--------:|:---------------------|
| `trading-agents-nuri` | 2026-06-07 | 전체 통합 |
| `trading-agents-nuri-cron` | 2026-06-07 | `langgraph/src/` |
| `trading-agents-nuri-langgraph` | 2026-06-07 | `langgraph/` |
| `trading-agents-nuri-scripts` | 2026-06-07 | `langgraph/pipeline.py` (인라인) |
| `trading-agents-nuri-feedback` | 2026-06-07 | `logs/monthly_review/` |
| `portfolio-feedback` | 2026-06-08 | `logs/monthly_review/` |
| `hermes-wiki-portfolio` | 2026-06-08 | `docs/portfolio-wiki/` |

## docs/ 이전
TradingAgents 논문 분석 문서 6개 → `trade-pipeline/docs/trading-agents-paper/`
Portfolio wiki 문서 3개 → `trade-pipeline/docs/portfolio-wiki/`

## 크론 경로 업데이트
모든 cron prompt의 `cd ~/trading-agents-nuri` → `cd ~/trade-pipeline` + `langgraph/` prefix
08:10 / 18:00 크론 프롬프트 수정 완료 (2026-06-08)

## archive/ 삭제
`archive/` 디렉토리 (orbit 알고리즘 v2~v11, 29개 파일, 4,404줄) — 코드 참조 0건 확인 후 삭제 완료.
