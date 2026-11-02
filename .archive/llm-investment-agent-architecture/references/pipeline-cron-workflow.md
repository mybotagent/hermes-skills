# Pipeline Cron Workflow

## 등록된 크론 목록 (2026-06-06 기준)

| 시간(KST) | 작업 | job_id | 형식 | 설명 |
|:---------:|:-----|:------|:----:|:-----|
| 04:00 | 📚 Wiki 동기화 | 64adaa | LLM | 변경사항 없으면 [SILENT] |
| 06:00 | 🗑️ 데이터 Clean up | 38f08c | no_agent | US 장 마감 후 중간 데이터 삭제 |
| 08:00 | 📅 캘린더 | 2f553e | LLM | Google Calendar 요약 |
| 08:10 | 📊 포트폴리오 | 6297df | LLM(fair-value) | fair_value + analyst 실행 → stdout 파일 저장 |
| 08:30(월) | 📆 주간계획 | 47f701 | LLM | 주간 일정 요약 |
| 18:00 | 🇺🇸 US 브리핑 | b5bbf6 | LLM(fair-value) | fair_value + analyst 실행 → stdout 파일 저장 |
| 18:30 | 🌍 매크로 | e69746 | LLM | macro_context.json 저장 + Discord 전송 |
| 18:35 | 🧠 파이프라인 | 62e57f | no_agent (run_pipeline.sh) | LangGraph 분석 → Discord 전송 |
| 매월1일 08:00 | 📈 전략 | d3080e | no_agent (monthly) | 월간 매크로 전략 리포트 |

## Clean up 상세 (06:00 KST)

**스크립트**: `~/.hermes/scripts/cleanup_daily_data.py`

삭제 대상:
- `data/fair_value_stdout.txt` (08:10 재생성)
- `data/analyst_stdout.txt` (08:10 재생성)
- `data/daily_snapshot.json` (Phase 0 재생성)
- `data/filtered_top10.json` (Phase 1 재생성)
- `data/macro_context.json` (18:30 재생성)
- `data/macro_context.txt` (레거시)
- `logs/decisions/stocks/*.md` (종목별 리포트)

**보존**: `logs/decisions/*.md`, `logs/decisions/*.json` (히스토리)

## 파이프라인 상세 (18:35 KST, 평일)

**스크립트**: `~/.hermes/scripts/run_pipeline.sh`
```bash
cd /home/ubuntu/trading-agents-nuri-langgraph
source venv/bin/activate
python3 pipeline.py 2>&1
```

**출력 형식**: `report.py` — 종목별 전체 분석 (Bull/Bear/Risk/Rationale truncation 금지)
- 종목 간 2줄 간격
- 각 종목: 밸류에이션 → 종합분석(6문장) → Bull(6문장) → Bear(6문장) → Risk(4문장) → Rationale(4문장)
- 저장 파일: `logs/decisions/full_report_*.md` (통합) + `logs/decisions/stocks/*.md` (종목별)

**비용**: ~$0.36/회 (7종목 × 5 DeepSeek 호출)
**월간**: ~$7.92 (22일 기준)

## 종목별 리포트 파일 (분할 전송용)

`logs/decisions/stocks/YYYYMMDD_HHMM_{종목명}.md` 에 저장.
각 파일은 `send_message`로 개별 Discord 전송 가능.
