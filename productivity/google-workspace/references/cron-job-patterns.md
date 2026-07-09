# Automated Google Calendar Cron Job Patterns

Trigger a cron job daily/weekly to query Google Calendar and deliver formatted summaries. Each cron job loads the `google-workspace` skill so it can use `google_api.py`.

## Common Patterns

### 1. Daily Morning Summary (8:00 AM)

Delivers today's calendar events to the user each morning.

```bash
# Create via cronjob tool:
# schedule: "0 8 * * *"
# skills: ["google-workspace"]
# prompt: >
#   오늘의 구글 캘린더 일정을 확인하고
#   시간순으로 정리해서 요약해줘.
#   일정이 없으면 "오늘은 등록된 일정이 없습니다"라고 알려줘.
```

### 2. Weekly Preview (Monday 8:30 AM)

Delivers Mon-Sun event overview at start of week.

```bash
# schedule: "30 8 * * 1"
# skills: ["google-workspace"]
# prompt: >
#   이번 주(월~일) 구글 캘린더 전체 일정을
#   날짜별, 시간순으로 정리해서 요약해줘.
#   총 일정 개수도 보여줘.
```

### 3. Midday Reminder (12:00 PM)

Checks remaining afternoon events.

```bash
# schedule: "0 12 * * *"
# skills: ["google-workspace"]
# prompt: >
#   오늘 구글 캘린더 일정 중에서
#   남은 오후 일정이 있는지 확인해서 알려줘.
#   없으면 "오늘 오후 일정은 없습니다"라고 알려줘.
```

### 4. Evening Review (9:00 PM)

Summarizes what happened today and previews tomorrow.

```bash
# schedule: "0 21 * * *"
# skills: ["google-workspace"]
# prompt: >
#   오늘 완료된 일정과
#   내일 예정된 일정을 확인해서 알려줘.
```

## Key Points

- **`deliver`**: Omit (defaults to origin channel / current thread) to auto-deliver back to the scheduling thread. Set `deliver="all"` to fan out to all connected home channels.
- **Discord thread delivery**: To send schedule summaries to a specific Discord thread, use `deliver="discord:CHANNEL_ID:THREAD_ID"`. This is used when users create a dedicated schedule-management thread (e.g., `#일정관리`) as the permanent home for all schedule-related cron outputs. Common pattern: update existing cron jobs (daily summary, weekly preview) after the thread is created so new runs land in the right place.
- **`skills`**: Always include `["google-workspace"]` so the cron agent has Calendar access. The agent will load the skill and can use `$GAPI calendar list ...` commands.
- **Timezones**: Queries default to UTC. Use explicit KST offsets (`--start 2026-06-01T00:00:00+09:00`) if events were created in Korean time.
- **Scope limit**: If the OAuth token only has `calendar` scope (not Gmail/Drive/etc.), the cron agents will work fine for calendar-only jobs — the partial scope warning is harmless.

## Pitfalls

- **Full-day events show as date-only** (`"start": "2026-06-04"`) — don't expect a time component; they span from midnight to midnight.
- **google_api.py calendar list** may miss events if the time range is too narrow or in the wrong timezone. When debugging, fall back to a raw Google API call with a wider window, or use Python's `googleapiclient` directly.
- **Cron job prompts must be self-contained** — they run in a fresh session with zero conversation history. Include all instructions inline.
- **Token auto-refresh works** for cron jobs using OAuth — the Google OAuth token at `~/.hermes/google_token.json` refreshes automatically as long as the refresh token is still valid.
- **Service Account**: If using a service account (`~/.hermes/google_service_account.json`), no token refresh is needed — the key is valid indefinitely unless rotated or deleted. The service account accesses the user's shared calendar (email stored in `~/.hermes/google_calendar_user.txt`). Calendar cron jobs work identically either way — the skill's `google_api.py` handles auth transparently.
