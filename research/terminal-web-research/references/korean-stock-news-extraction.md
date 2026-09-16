# Korean Stock News Extraction — Reference

> Detailed playbook for collecting news about Korean listed stocks when:
> - `browser_navigate` fails (no Chromium) AND
> - The article body is JS-rendered on the source site's own page (yna.co.kr, etnews.com, v.daum.net, etc.) AND
> - You need 2-3 articles per ticker across multiple tickers in parallel
>
> Used by `terminal-web-research` §7.7–7.10.

## The Two-Layer Pipeline

Korean stock news has a **two-layer** reality:

| Layer | Sites | Render | Curl-friendly? |
|-------|------|--------|----------------|
| **Headline layer** | Google News RSS (`news.google.com/rss`) | server-rendered XML | ✅ Yes |
| **Body layer** | Naver News (`n.news.naver.com/article/...`) | server-rendered HTML | ✅ Yes |
| **Body layer (broken)** | Original outlets (`yna.co.kr/view/`, `etnews.com`, `v.daum.net`) | JS-rendered | ❌ No |

**Rule of thumb**: never try to scrape article bodies from the original outlet. Use Google News → find the Naver News URL → scrape Naver News.

## Quick-Start: 6-Ticker Korean News Batch

Save the batch script and run it via `terminal()` (cron-safe):

```python
# /tmp/kr_news_batch.py
import xml.etree.ElementTree as ET, json, urllib.request, urllib.parse, re, sys
from html import unescape
from datetime import datetime, timezone, timedelta

this_month = datetime.now().strftime("%Y년 %-m월")  # e.g. "2026년 9월"

TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("009150", "삼성전기"),
    ("005380", "현대차"),
    ("052220", "에이피알"),        # KOSDAQ — DO NOT use 278280 (wrong code!)
    ("267260", "HD현대일렉트릭"),  # NOT 267270 (HD건설기계)
]

def fetch_rss(q):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return ET.fromstring(urllib.request.urlopen(req, timeout=15).read())

def _parse(pub_str):
    # "Thu, 03 Sep 2026 10:21:00 GMT" → datetime
    return datetime.strptime(pub_str.split(",")[1].strip(), "%d %b %Y %H:%M:%S %Z")

results = {}
for code, name in TARGETS:
    seen, items = set(), []
    for q in [f"{name}+{this_month}", f"{name}+{code}"]:
        try:
            for it in fetch_rss(q).findall(".//item")[:10]:
                t = unescape(re.sub(r"\s*-\s*Google\s*뉴스\s*$", "",
                                    it.find("title").text or ""))
                if t in seen or "Google 뉴스" in t:
                    continue
                seen.add(t)
                src = it.find("source")
                pub = it.find("pubDate")
                items.append({
                    "ticker": code,
                    "title": t,
                    "source": src.text if src is not None else "",
                    "pubDate": pub.text if pub is not None else "",
                })
        except Exception as e:
            items.append({"ticker": code, "error": str(e)})
    results[code] = items[:5]

# Keep only items within last 36 hours KST
KST = timezone(timedelta(hours=9))
cutoff = datetime.now(KST) - timedelta(hours=36)
out = []
for code, items in results.items():
    fresh = [i for i in items if "pubDate" in i and _parse(i["pubDate"]) >= cutoff]
    out.extend(fresh or items[:2])  # fallback to any 2 if no same-day

print(json.dumps(out, ensure_ascii=False, indent=2))
```

```bash
python3 /tmp/kr_news_batch.py > /tmp/kr_news.json
```

## Body Extraction from Naver News

Once you have a Naver article URL (`n.news.naver.com/article/{oid}/{aid}`):

```bash
curl -sL -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0" \
  "https://n.news.naver.com/article/{oid}/{aid}" \
  -o /tmp/article.html

# Extract first ~3500 chars of body
grep -A 250 'newsct_body' /tmp/article.html \
  | sed -E 's/<[^>]+>/ /g; s/&nbsp;/ /g; s/[[:space:]]+/ /g' \
  | head -c 3500
```

### Why this works
- Naver News is a **different render path** than the original outlet
- The article body lives in `<div id="newsct_body">` and is server-rendered
- The other outlets (`yna.co.kr/view/`, `v.daum.net/v/`, `etnews.com/news/...`) return JS-stub pages or 500/404

### Verification

```bash
wc -c /tmp/article.html
# Real article: ~200KB+
# JS-stub: ~50KB
# 404 page: ~30KB
```

If you hit a JS-stub, try a different Naver URL from the same Google News RSS result list.

## Cross-Source Causal Chain Reporting

When the user asks "why did KOSPI drop?", the workflow:

1. **Headlines** (parallel RSS):
   - `KOSPI+급락`
   - `반도체+매도`
   - `유가+급등`
   - `호르무즈+2026`
2. **Body extraction** — pick 3-4 articles from **different outlets** (MBN, KBS, 헤럴드경제, 매일경제, 뉴시스) → extract via Naver News → confirm causal chain
3. **Quote-in-source attribution** — only cite numbers/quotes that appear in the actual article body
4. **Cross-source verification** — if 3+ outlets independently report the same causal explanation, that's verified

## User Preferences Observed (2026-07-13)

| Preference | Meaning | Source |
|------------|---------|--------|
| **"정성 뉴스만 반환, 수치를 새로 생성하지 말라"** | Only qualitative news; never fabricate market numbers | Direct instruction |
| **Ticker code verification** | User explicitly flagged HD현대일렉트릭=267260 ≠ HD건설기계=267270, 에이피알=052220 (KOSDAQ) | Direct instruction |
| **Substitution on missing data** | If a ticker has no same-day article, say so explicitly and substitute most recent prior-day article (earnings, contract wins, sector context). **Never invent headlines.** | Inferred from task constraint |

## Korean News Site Reliability Map

| Outage class | Outlets affected | Fallback strategy |
|--------------|-----------------|-------------------|
| JS-rendered body | yna.co.kr, etnews.com, v.daum.net, chosun.com | Use Naver News |
| Paywall blocked | 일부 프리미엄 outlet | Naver News bypass |
| Search.naver.com capcha | Sometimes returns 403 after burst | Switch to Google News RSS |
| Rate limit | Google News RSS ~10+ rapid | Add `sleep 1` between batches |

## Pitfalls

1. **Ticker code confusion**: HD현대일렉트릭=**267260**, HD건설기계=267270 (different!). Always verify codes against KRX before running. The user will flag this explicitly.
2. **Samsung SDI cross-contamination**: When searching "삼성전자" (Samsung Electronics, 005930), Google News RSS returns many Samsung SDI (006400) results because the company name prefix is shared. Always de-dupe by checking if the article body actually mentions the target ticker/company. If "삼성SDI" appears in the headline near "삼성전자", it's Samsung SDI, not Samsung Electronics. Filter aggressively.
3. **Outlet ID guessing**: `oid` in Naver URLs = outlet code (001=연합뉴스, 023=조선일보, 009=매일경제, 011=서울경제, 015=한국경제, 016=헤럴드경제, 021=문화일보, 025=중앙일보, 028=한겨레, 032=경향신문, 038=한국일보, 052=YTN, 055=SBS, 056=JBpress, 057=MBN, 008=머니투데이, 014=파이낸셜뉴스, 018=이데일리, 020=동아일보, 029=디지털타임스, 030=전자신문, 031=아이뉴스24, 050=뉴시스, 119=데일리안). Don't guess — extract from Google News RSS first.
4. **Embedded quotes hidden by `&quot;`**: After HTML-stripping, quotes show as plain text. No special handling needed.
5. **Description vs content**: Google News `<description>` may have HTML. Always strip with `re.sub(r'<[^>]+>', '', desc)`.
6. **Naver article URL may 404**: Older articles get archived. Fallback to original outlet headline only (don't fabricate body).
7. **News head says "AMD rally" but body is about Samsung**: Headlines from Google News RSS can be off-topic from ticker. Always grep body for ticker name before citing.
8. **RSS `<description>` field has HTML entities and nested tags**: Even after stripping `<[^>]+>`, you get `&nbsp;` and `&amp;amp;` embedded in text. In Python, use `html.unescape()` after stripping tags: `re.sub(r'<[^>]+>', '', desc_text)` then `.replace('&nbsp;', ' ')` or chain `html.unescape()` from stdlib.
9. **Google News HTML scraping fails silently**: The `news.google.com/search?q=...` HTML page is a JS-rendered SPA — curl returns ~2.5MB of framework JavaScript with no article content. **Always prefer RSS** (`/rss/search?q=...`) over HTML scraping for news discovery. The RSS returns clean XML with titles, sources, and pubDates in one pass.
10. **Same-stock-name cross-pollution**: When company name is a common prefix (e.g. "삼성" = Samsung, "현대" = Hyundai), searches return unrelated companies in the same conglomerate group. "삼성SDI" results appear when searching "삼성전자". Use ticker-code query variant (`{name}+{code}`) as a second query to disambiguate. Combine results from name-query and code-query, de-dupe by title, then filter by content relevance.
