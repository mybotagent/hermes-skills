# Market Calendar — KR/US Holiday Detection

**Module**: `scripts/market_calendar.py`
**Purpose**: Single source of truth for Korean/US market holidays, open/closed detection, and last-trading-day calculation.

## How to use in pipeline scripts

```python
from market_calendar import market_status, is_holiday, last_trading_day

# Check if today is a Korean holiday
hol, name = is_holiday()  # defaults to 'kr'
# → (True, '제헌절') or (False, '')

# Get last trading day before today
ltd = last_trading_day('kr')
# → date(2026, 7, 16)  (Thursday, the previous trading day)

# Full market status dict
ms = market_status()
print(ms['kr']['open_status'])  # '휴장' / '⚡ 장중' / '장마감'
print(ms['kr']['holiday_name']) # '제헌절' or ''
print(ms['kr']['last_trading']) # '2026-07-16'
```

## Holiday lists (2026)

### 🇰🇷 Korea (18 holidays)
| Date | Holiday |
|:----|:--------|
| 2026-01-01 | 신정 |
| 2026-02-15~17 | 설날 |
| 2026-03-01 | 삼일절 |
| 2026-05-05 | 어린이날 |
| 2026-05-27 | 석가탄신일 |
| 2026-06-06 | 현충일 |
| **2026-07-17** | **제헌절** |
| 2026-08-14~18 | 광복절·추석 |
| 2026-09-07 | 한글날(대체) |
| 2026-10-03~09 | 개천절·한글날 |
| 2026-12-25 | 성탄절 |
| 2026-12-31 | 연말 |

### 🇺🇸 US (10 holidays)
| Date | Holiday |
|:----|:--------|
| 2026-01-01 | New Year's Day |
| 2026-01-19 | MLK Day |
| 2026-02-16 | Presidents' Day |
| 2026-04-03 | Good Friday |
| 2026-05-25 | Memorial Day |
| 2026-06-19 | Juneteenth |
| 2026-07-03 | Independence Day (obs.) |
| 2026-09-07 | Labor Day |
| 2026-11-26 | Thanksgiving |
| 2026-12-25 | Christmas |

## Dashboard integration

The `portfolio_dashboard.html` JS has an inline holiday map (must match Python module).

**JS logic** (per exchange):
```javascript
// US: 23:30~06:00 KST (Mon-Fri, excludes holidays)
var usOpen = !isWeekend && !isUsHoliday && (kstH>=23 || kstH<6);
// KR: 09:00~15:30 KST (Mon-Fri, excludes holidays)
var krOpen = !isWeekend && !isKrHoliday && kstH>=9 && kstH<15;
```

## Data freshness on holidays

When today is a holiday:
- `collect_briefings.py` shows `"🇰🇷 오늘(YYYY-MM-DD)은 {holiday_name}입니다. 마지막거래일({last_trading}) 브리핑을 참조하세요."`
- Dashboard status shows `🇰🇷 휴장(제헌절)`
- Pipeline scripts should use `last_trading_day()` for data reference dates

## Scripts that use market_calendar.py

| Script | What it does |
|:-------|:------------|
| `collect_briefings.py` | Shows holiday note when no briefing found |
| `portfolio_dashboard.html` | JS inline holiday map for US/KR status |
| (future) `paper_tracker.py` | Should use last_trading_day for holiday ref dates |

## 🔴 Pitfall: Naver Polling `cr` sign on holidays

The Naver Polling API `cr` field is always absolute (positive). On a holiday, the API still returns data from the last trading day. The sign must be computed from `nv - pcv`.

**Always use**: `cd ~/trade-pipeline && python3 scripts/fetch_kr_stocks.py`
**Never use**: raw `polling.finance.naver.com` curl/python calls.
