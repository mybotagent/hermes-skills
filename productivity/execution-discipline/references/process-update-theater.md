# Process-Update Theater (2026-07-17)

> **Signal**: User points out a problem → agent fixes the OUTPUT/DISPLAY → user re-corrects:  
> "결과를 업데이트하지 말고 과정을 업데이트해" (Don't update the result, update the PROCESS)

## The Anti-Pattern

When user reports an issue (wrong date, stale data, missing market holiday, broken chart):
1. Agent patches the **display layer** (HTML, message text, note field)
2. User re-reads and says: "That's cosmetic. Fix how the data is **generated**."
3. Agent then realizes the root cause is in the **pipeline/process layer**.

## Examples

| User issue | Display-only fix (WRONG) | Process fix (RIGHT) |
|------------|------------------------|---------------------|
| "오늘 국장 휴장인데 브리핑 없음" | Add "오늘은 휴장입니다" note to dashboard | Add `market_calendar.py` module; update `collect_briefings.py` to auto-detect holidays; update pipeline scripts to use the calendar |
| "브리핑 시간이 23:00 KST로 나와요" | Hardcode "08:22 KST" in JS | Fix `collect_stock_briefings.sh` to extract timestamp from cron filename; fix `collect_briefings.py` to parse it |
| "브리핑이 안올라옴" | Add "오늘 브리핑이 아직 생성되지 않았습니다" | Fix cron timing (08:15→08:50), add holiday detection |
| "데이터 날짜가 틀림" | Add date warning to display | Fix the data-generation script's date handling |

## Detection Rule

The agent has fallen into process-update theater when:

- The **fix lives in `data/portfolio_dashboard.html`** (or any display-layer file) but the root cause is in a **`scripts/*.py` or `~/.hermes/scripts/*.sh`** pipeline file
- User's next question is about the same problem in a different view/format
- The commit message contains "fix: display/show/note for X" instead of "fix: pipeline logic for X"

## Recovery

1. **Stop editing the display file.** Identify the data-generation script.
2. Trace the data pipeline: find the earliest script in the chain that can solve the problem.
3. Fix the script at the **earliest** point in the chain.
4. Verify: the display automatically shows the corrected data without any display-layer patch.

## Root Cause

Display-layer patching is **faster to verify** (reload browser → see result). Process-layer patching requires running the pipeline, checking intermediate files, then reloading the browser. The agent optimizes for time-to-show-result instead of time-to-correct-result.
