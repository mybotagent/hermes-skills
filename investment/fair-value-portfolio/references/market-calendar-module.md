# Market Calendar Module (2026-07-17)

## Purpose

`scripts/market_calendar.py` provides holiday-aware market status for the pipeline.
Single source of truth for US/KR market open/close times and holidays.

## Usage

```python
from scripts.market_calendar import market_status, is_holiday

# Check if today is a Korean holiday
hol, name = is_holiday(date(2026, 7, 17), 'kr')
# → (True, '제헌절')

# Get full market status
ms = market_status()
ms['kr']['status']       # '장중'|'장마감'|'휴장'
ms['kr']['holiday_name'] # '제헌절' or ''
ms['kr']['last_trading'] # '2026-07-16'
ms['us']['status']       # '장중'|'장마감'|'휴장'

# Find last trading day
last_trading_day('kr', date(2026, 7, 17))
# → 2026-07-16 (Thursday, since 7/17 is 제헌절)
```

## Holiday Lists

**KR (18 days)**: 신정, 설날(3일), 삼일절, 어린이날, 석가탄신일, 현충일, 제헌절, 광복절, 추석(2일), 한글날, 개천절, 성탄절, 연말, 임시공휴일

**US (10 days)**: New Year, MLK Day, Presidents Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, Christmas

## Consumers

| Script | What it uses | Since |
|--------|-------------|-------|
| `collect_briefings.py` | Holiday note when today_dir missing | 2026-07-17 |
| `portfolio_dashboard.html` (JS) | Inline holiday map for market status display | 2026-07-17 |
| `generate_macro_dashboard.py` | (Not yet) Date freshness indicator | TBD |
| `paper_tracker.py` | (Not yet) Last trading day for data cut | TBD |

## Cron Timing

The morning briefing collect cron (`7f8ba2820760`) was delayed from 08:15 → **08:50** because the briefing generation cron takes 08:10~08:22 to finish. Always ensure at least 30min buffer between generation and collection.

## JS Counterpart

The dashboard JS embeds a simplified holiday map inline since it runs in the browser:
```javascript
var krHolidays={'2026-01-01':'신정','2026-07-17':'제헌절',...};
var usHolidays={'2026-01-01':'New Year','2026-07-03':'Indep Day',...};
```
These MUST be kept in sync with the Python module when adding future years.
