# Cron Macro Validation Pattern (2026-07-15)

## Purpose

Reusable pattern for scheduled macro/market reports when the runtime must collect data autonomously and the final artifact must be auditable. This is a condensed operational reference, not a transcript.

## Source hierarchy

1. Official/primary APIs first: BLS Public Data API, Federal Reserve pages/releases, CNBC quote XML for market prices, Naver Polling for Korean equities, open.er-api for USD/KRW.
2. Google News RSS only for qualitative context and as a discovery/fallback layer when direct article/search tooling is unavailable.
3. Never let a news headline or subagent-generated number overwrite a directly verified value.

## Verified endpoints and interpretation

### BLS

- CPI index: `https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0?startyear=2025&endyear=2026`
- Unemployment: `LNS14000000`
- Total nonfarm employment: `CES0000000001`
- The CPI API returns an index, not a YoY percentage. Calculate `current_month_index / prior_year_same_month_index - 1`, then label the result as calculated from BLS index values.
- Employment series may be preliminary; preserve the BLS preliminary footnote.

### CNBC XML

Use `https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols=SYMBOL&requestMethod=itk`.
Extract `last`, `previous_day_closing`, `change`, and `change_pct`. Recalculate `(last - previous_day_closing) / previous_day_closing * 100` when both closes are available.

If `last == previous_day_closing` but `change` is non-zero, treat the record as internally inconsistent: retain the level, do not infer a daily percentage, and write a caveat. This occurred for the S&P 500 response in the session.

### USD/KRW

Use `https://open.er-api.com/v6/latest/USD`; retain the provider timestamp. Do not mix a stale cached FX value with same-day market prices without labeling the timing difference.

### Korean stocks

Use one Naver Polling request per six-digit code:
`https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:005930`

Decode as EUC-KR, then verify `cd` and `nm` before accepting `nv`, `pcv`, `cv`, and `cr`. A multi-code query may return an empty `datas` list; fall back to individual requests rather than treating that as a no-data market result. Use the regular close fields for the report, not after-market fields. Verify that the sign of `cr` agrees with `(nv-pcv)/pcv*100`.

## News collection

Use Google News RSS with URL-encoded Korean queries and `hl=ko&gl=KR&ceid=KR:ko`. For each requested ticker, run at least two query variants, deduplicate by title/source, and retain the RSS title, publisher, publication time, redirect URL, and a clearly qualified qualitative summary. If company-specific coverage is thin, report sector context explicitly; never invent a company headline.

For macro statistics, prefer government/central-bank release headlines. A news result is corroboration or qualitative context, not a replacement for an official numeric API response.

## Cron-safe scripting pitfall

Do not encode multiline Python as a shell string containing literal `\\n` characters passed to `python3 -c`; the shell/JSON layer can preserve the backslash and cause `SyntaxError: unexpected character after line continuation character`. For any loop, formatter, validation step, or JSON transformation:

1. Save a stdlib-only script with `skill_manage(action='write_file', file_path='scripts/...')` or the runtime file-writing tool.
2. Run it separately with `python3 /path/to/script.py`.
3. Cache raw API responses before parsing when practical.

This also avoids pipe-to-interpreter and heredoc scanner problems and makes the collection reproducible.

## Artifact and validation contract

- Build the report only after direct numeric verification completes.
- Save atomically to both active pipeline paths when legacy consumers may still exist: `~/trading-agents-nuri/data/macro_context.json` and `~/trade-pipeline/data/macro_context.json`.
- Validate JSON parsing, report length, required keys, news count, regime, and byte-for-byte equality of the two copies.
- Include `data_quality` metadata: numeric sources, RSS fallback status, stale/carry-forward fields, source disagreements, and anomaly handling.
- If KOSPI/KOSDAQ or another index moves beyond the anomaly threshold, double-check through a second representation and rebuild the narrative around the event rather than merely inserting the number in a table.
