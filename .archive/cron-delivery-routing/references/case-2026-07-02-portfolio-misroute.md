# Case: 2026-07-02 — Portfolio silently misrouted to calendar thread

## Symptom
User (aiprofit, Discord thread `#주식-증시` `1510404235915694170`) reported: **"추천 포트폴리오와 비중 자체는 안알려 주네?"**

The 18:35 LangGraph cron had just run successfully. User saw a header/posting in the thread but no weights were delivered.

## Root cause
Cron `afebf6cb0ab1` (LangGraph Pipeline, schedule `35 18 * * 1-5`) had:
```
Deliver: discord:1510397804139515945:1520640537995247698
```
- Channel = HomeID ✅
- Thread = `1520640537995247698` = **#일정 (calendar thread)** ❌

The cron NAME says "포트폴리오" (portfolio) but the DELIVER pointed to the calendar thread. Result: full 1059-line report (with Phase 3 weights table at the end) was generated and delivered successfully — to the calendar thread, where the user never looked.

## This is Mode B (silent success)
- Cron `last_status=ok`
- Cron `last_delivery_error=null`
- All 5 phases ran: Fair Value load → Macro → T1 Gap → LangGraph (HOLD×10) → Portfolio allocation
- Output saved to `~/trade-pipeline/logs/full_report_20260702_1839.md` AND `~/trade-pipeline/logs/portfolio/2026-07-02.json` (with full weights)
- Discord delivery to wrong thread = **silent failure from the user's perspective**

## Diagnostic path that worked
1. User mentioned missing portfolio in #주식-증시
2. Checked `hermes cron list` → saw `afebf6cb0ab1` Deliver pointed to `1520640537995247698`
3. Cross-referenced thread ID against memory: `#일정(1520640537995247698)=캘린더`
4. Confirmed misroute (Mode B) — cron was running fine but to the wrong channel

## Recovery performed
1. `hermes cron update afebf6cb0ab1 deliver='discord:1510397804139515945:1510404235915694170'`
2. Manually reposted today's portfolio content (with weights table) to `#주식-증시` so user got the missing report
3. User-level memory entry added/extended with this Mode B lesson

## Lessons
- **Mode B is silent** — no error in cron logs, no `last_delivery_error`, runs `ok`. Only the user notices.
- **Cron name vs deliver thread should be intuitive**: a "portfolio" cron should NOT deliver to a calendar thread.
- **Recovery is two-part**: (1) fix the deliver for forward runs, (2) repost today's content because past reports are already lost to the user.
- **Pre-flight validation is non-existent**: Hermes scheduler doesn't validate that `deliver` thread topic matches cron name. Agents must do this manually.

## Prevention (recommended)
- Audit script `scripts/audit_cron_deliver.sh` runs each cron
- Pre-flight checklist in `cron-delivery-routing` SKILL.md
- For periodic review, run `hermes cron list | grep Deliver:` once per week
