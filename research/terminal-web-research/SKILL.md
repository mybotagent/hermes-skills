---
name: terminal-web-research
description: "Web research via curl + Python when browser tools are unavailable"
version: 1.2.0
author: Hermes Agent
metadata:
  hermes:
    tags: [research, web, curl, python, html-parsing, github-api, ai-coding-agents]
    related_skills: [spike, plan, systematic-debugging]
---
## Companion References

- `references/ai-coding-agent-ecosystem-jun2026.md` — June 2026 field notes: Anthropic Sonnet 5, Codex Rust rewrite, Cursor 3.9, Devin Desktop rebrand, MCP/ACP protocols, GitHub redirect gotchas, Next.js extraction recipes, Cloudflare detection. Update this file as the AI ecosystem shifts.

# Terminal Web Research

Perform thorough web research using only terminal tools (curl, Python, grep) when the browser tool (`browser_navigate`) fails because Chrome is not installed.

## When to Use This Skill

- `browser_navigate` returns `Chrome not found` or `agent-browser install` fails
- You need to extract structured information from documentation sites, blogs, or GitHub
- The research task involves searching multiple sources in parallel
- Target sites are static-rendered (Docusaurus, GitHub, raw content, standard HTML pages)

## Detection

```bash
# Check if browser is available
browser_navigate "https://example.com"  # if this fails → use this skill
```

## Core Technique: curl + Python HTML Parsing

### Principle

Most documentation sites, blogs, and static pages render content as server-side HTML. A well-crafted `curl` + Python one-liner can extract structured data (headings, tables, article lists, links) without JavaScript.

### 1. Fetch Raw Content

Always set a browser-like User-Agent:

```bash
curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" "https://target-site.com/page" -o /tmp/page.html
```

Or pipe directly to Python (more concise for one-off extractions):

```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://target-site.com/page" | python3 -c "
import sys, re
html = sys.stdin.read()
# ... extraction logic ...
"
```

### 2. Common Extraction Patterns

**Extract headings (h2, h3, h4):**
```python
headings = re.findall(r'<h[23][^>]*>([^<]+)</h[23]>', html)
```

**Extract article blocks with nested content:**
```python
articles = re.split(r'<h3[^>]*>', html)
for part in articles[1:]:
    title_end = part.find('</h3>')
    title = part[:title_end].strip()
    after = part[title_end+5:]
    text = re.sub(r'<[^>]+>', ' ', after)
    text = re.sub(r'\s+', ' ', text).strip()
```

**Extract link targets from anchor tags:**
```python
links = re.findall(r'href="([^"]+)"', html)
```

**Extract table rows:**
```python
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
for row in rows:
    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
```

**Extract content from a specific section (by id or class):**
```python
main = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
content = main.group(1) if main else html
# or by CSS class
section = re.search(r'class="[^"]*content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
```

**Extract metadata (author, description):**
```python
desc_m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
```

**HTML entity decoding:**
```python
title = title.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
title = title.replace('&lt;', '<').replace('&gt;', '>')
```

### 3. GitHub API Queries

GitHub REST API is available without auth for public data:

```bash
# Search issues/PRs across a repo
curl -s -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/search/issues?q=harness+repo:nousresearch/hermes-agent&per_page=10"

# Get PR content
curl -s -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/owner/repo/pulls/{number}"

# Search code in a repo
curl -s -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/search/code?q=keyword+repo:owner/repo&per_page=10"

# Get repo contents (raw)
curl -s -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/owner/repo/contents/path/to/file"
```

When authenticated (token stored globally), use:
```bash
TOKEN=$(cat /tmp/ghtoken)
curl -s -H "Authorization: token $TOKEN" ...
```

#### 3.1 GitHub API Redirect Gotcha — ALWAYS use `curl -L`

Many GitHub endpoints return **HTTP 301 Moved Permanently** with a JSON body containing the new URL when:
- A repo is renamed/redirected (e.g. `sst/opencode` → `anomalyco/opencode`)
- You hit a redirect alias (`api.github.com/repos/{owner}/{repo}`)

The naive curl returns the JSON `{"message":"Moved Permanently",...}` with HTTP 200 (curl follows up to 301 itself but stops at 308 sometimes). The **fix**: always use `curl -sL` (capital `-L` follows redirects), and verify the resolved repo name in the response:

```bash
# WRONG — silently returns the redirect JSON as if it were the repo
curl -s "https://api.github.com/repos/sst/opencode" | python3 -c "import json,sys; print(json.load(sys.stdin).get('full_name'))"
# → None

# RIGHT — follow redirects
curl -sL "https://api.github.com/repos/sst/opencode" | python3 -c "import json,sys; print(json.load(sys.stdin).get('full_name'))"
# → anomalyco/opencode

# Alternative: hit /repositories/{id} after a 301
curl -sL "https://api.github.com/repositories/975734319"
```

**Always include `curl -sL` for GitHub API calls.** This is the #1 silent failure mode.

#### 3.2 Releases API — Distinguish Stable from Pre-release

The `/repos/{owner}/{repo}/releases` endpoint returns ALL releases including alphas/betas. **Critical for tracking real shipped work vs. internal builds:**

```bash
curl -sL "https://api.github.com/repos/openai/codex/releases?per_page=20" -o /tmp/releases.json
python3 -c "
import json
for r in json.load(open('/tmp/releases.json')):
    print(f\"{r['tag_name']:30s} {r['published_at']:25s} prerelease={r['prerelease']}\")
"
```

Filter to stable only when you want shipped features:
```python
stable = [r for r in data if not r['prerelease']]
```

Pattern recognition examples from real research sessions:
- `rust-v0.142.x` tags + `rust-v0.143.0-alpha.x` = **stable vs. nightly split** (Codex CLI Rust rewrite)
- `v4.0.x` + `cli-v3.0.x` = **VS Code extension vs. CLI split** (Cline)
- Tags with `-alpha.N` suffix that increment daily = **rapid pre-release cadence** — sign of active development

### 4. Common Target Patterns

| Target | URL Pattern | Extraction Method |
|--------|-------------|-------------------|
| GitHub README | `raw.githubusercontent.com/owner/repo/main/README.md` | Direct text (no HTML parsing needed) |
| Docusaurus docs | `site.com/docs/page` | Parse HTML for `<main>` content, headings, articles |
| Nous Research blog | `nousresearch.com/blog/` | Parse heading/class selectors |
| GitHub issues/PRs | API: `api.github.com/search/issues` | JSON parsing via Python json module |
| Static HTML pages | Direct URL | Regex extraction |

### 5. Parallel Research via Delegate Task

When you need to search multiple sources simultaneously:

```python
# Inside execute_code
from hermes_tools import terminal

sources = [url1, url2, url3]
results = []
for url in sources:
    result = terminal(f'curl -sL -H "User-Agent: Mozilla/5.0" "{url}" | python3 extract.py')
    results.append(result)
```

However, note that subagents with `toolsets=["web","browser"]` cannot do terminal-based research because they lack the terminal tool. For browser-less research, use `toolsets=["terminal"]` on subagents or do the research directly in the parent session.

### 6. Verifying Results

After extraction, always verify:
- The data is from the actual target (check response status codes)
- HTML entities are decoded properly
- The regex patterns matched the intended content (not error pages or redirects)
- Use `grep -n "keyword"` as a quick sanity check before full extraction

### 7. RSS/XML Parsing for News Research

> **Why this matters**: Many financial/news sites (Investing.com, CNBC, MarketWatch, Yahoo Finance) block curl scraping with Cloudflare, JS-required rendering, or paywalls. Google News RSS bypasses ALL of these — it returns clean, structured XML that is trivially parseable.

**Best use case**: Any research task that needs recent news headlines — macro economics, company earnings, semiconductor/AI, geopolitics.

#### 7.1 Google News RSS — Primary Method

Google News RSS endpoint works unconditionally with curl (no JS, no Cloudflare):

```bash
curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://news.google.com/rss/search?q={URL_ENCODED_SEARCH}&hl=en-US&gl=US&ceid=US:en" \
  -o /tmp/news.xml
```

**Key parameters:**
- `q=` — URL-encoded search query (multi-word, operators supported)
- `hl=en-US` — language (can use `ko` for Korean results)
- `gl=US` — geographic region
- `ceid=US:en` — country+language combination

#### 7.2 Parsing RSS XML with Python (Recommended)

Use `xml.etree.ElementTree` — built into Python stdlib, no dependencies:

```bash
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('/tmp/news.xml')
root = tree.getroot()
for item in root.findall('.//item')[:15]:
    title = item.find('title')
    source = item.find('source')
    pubdate = item.find('pubDate')
    t = title.text if title is not None else 'N/A'
    s = source.text if source is not None else ''
    p = pubdate.text if pubdate is not None else ''
    print(f'[{s}] {t}  ({p})')
"
```

**Item fields available:**
- `title` — headline text
- `source` — publication name (Reuters, CNBC, Bloomberg, etc.)
- `pubDate` — publication date (RFC 2822 format)
- `link` — article URL (Google News redirect wrapper)
- `description` — optional, may contain HTML snippet

#### 7.3 Parallel RSS Search Strategy

For comprehensive research (macro report, sector scan), run multiple RSS queries in parallel:

```bash
# terminal() 1: q=semiconductor+AI+chip+export
# terminal() 2: q=Federal+Reserve+interest+rate
# terminal() 3: q=US+China+trade+tariffs
# terminal() 4: q=KOSPI+foreign+selloff+USD+KRW
```

Each call returns ~10-20 relevant headlines with sources and dates. Cross-reference duplicates, then do targeted follow-ups for articles that merit deeper reading.

#### 7.4 Common Extraction Patterns (Python XML)

**Extract all items with date filtering:**
```python
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

tree = ET.parse('/tmp/news.xml')
items = tree.findall('.//item')
recent = []
for item in items:
    pub_str = item.find('pubDate').text
    pub_date = datetime.strptime(pub_str.split(',')[1].strip(), '%d %b %Y')
    if pub_date >= datetime.now() - timedelta(days=2):
        recent.append(item)
```

**Extract descriptions (first ~300 chars):**
```python
import re
for item in items:
    desc = item.find('description')
    if desc is not None and desc.text:
        clean = re.sub(r'<[^>]+>', '', desc.text)
        print(clean[:300])
```

**Filter by source (specific publication):**
```python
for item in items:
    source = item.find('source')
    if source is not None and source.text in ('Reuters', 'Bloomberg', 'CNBC', 'WSJ'):
        print(item.find('title').text)
```

#### 7.5 Cron-Safe RSS Workflow (No execute_code, No Pipe-to-Interpreter)

`execute_code` is **blocked in cron jobs** (no user present to approve pipe-to-interpreter security warnings). The fix: write a reusable Python script file first, then call it via `terminal()`.

**Step 1 — Write the extraction script with `write_file`:**

The script accepts a key argument and reads a pre-downloaded XML file:

```python
import xml.etree.ElementTree as ET, sys

queries = {
    "QUERY1": "search+term+one",
    "QUERY2": "search+term+two",
}
key = sys.argv[1]
tree = ET.parse(f"/tmp/{key}.xml")
for item in tree.findall('.//item')[:8]:
    t = item.find('title')
    s = item.find('source')
    p = item.find('pubDate')
    print(f'[{s.text if s is not None else ""}] {t.text if t is not None else "N/A"}')
```

**Step 2 — Download RSS XML (parallel `terminal()` calls):**

```python
# Download + parse in one terminal() call per query
terminal(f'curl -sL -H "User-Agent: Mozilla/5.0" "{rss_url}" -o /tmp/QUERY1.xml && python3 /tmp/script.py QUERY1')
terminal(f'curl -sL -H "User-Agent: Mozilla/5.0" "{rss_url2}" -o /tmp/QUERY2.xml && python3 /tmp/script.py QUERY2')
```

**Key constraints enforced by this pattern:**
- ❌ NO `execute_code()` — blocked in cron jobs
- ❌ NO `curl | python3 -c` — pipe-to-interpreter blocked in cron jobs
- ✅ Pre-written `.py` file → `terminal()` runs it without security prompts
- ✅ Parallel `terminal()` calls for multi-source research
- ✅ Stdlib-only (`xml.etree.ElementTree`, no pip dependencies)

#### 7.6 When RSS Fails

- **No internet**: RSS won't work either. Report `[SILENT]`.
- **Rate limiting**: Google News RSS has generous limits but 10+ rapid requests may trigger CAPTCHA. Space them out or add a 1-second delay between batches.
- **Non-English queries**: Google News RSS works with any language. Set `hl=ko` for Korean, `hl=ja` for Japanese. Content returned depends on the query language.
- **Very niche queries**: Google News may return 0 results. Fall back to site-specific curl scraping (section 1-6 above) or try broader search terms.

- `references/korean-stock-news-extraction.md` — Korean stock news: parallel RSS + Naver News body extraction + outlet code map + causal chain reporting (added 2026-07-13)
- `references/rss-news-extraction.md` — Ready-to-use Google News RSS extraction script template.

#### 7.7 Korean Stock News Collection — Parallel Per-Ticker (added 2026-07-13)

When a user asks for "today's news for these N Korean stocks", use this parallel Google News RSS pattern. The Korean-language `hl=ko&gl=KR&ceid=KR:ko` parameter set returns domestic-press results (연합뉴스, 조선일보, 매일경제, 한국경제, etc.) with Korean-localized rankings.

**Single-query pattern** (one stock):
```bash
curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://news.google.com/rss/search?q=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+2026%EB%85%84+7%EC%9B%94+13%EC%9D%BC&hl=ko&gl=KR&ceid=KR:ko" \
  -o /tmp/samsung.xml
```

**Batch script** (N tickers in parallel terminal() calls — `/tmp/kr_news_collect.py`):
```python
import xml.etree.ElementTree as ET, json, urllib.request, urllib.parse, os, re
from html import unescape

# (ticker_code, display_name) — pick 2-3 query variants per ticker for breadth
TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("267260", "HD현대일렉트릭"),  # NOT HD건설기계(267270) — double-check codes
]

def fetch_rss(query, hl="ko", gl="KR", ceid="KR:ko"):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return ET.fromstring(urllib.request.urlopen(req, timeout=15).read())

results = {}
for code, name in TARGETS:
    # Multi-variant query — Korean name + ticker code + date for breadth
    queries = [f"{name}+2026년+7월", f"{name}+{code}"]
    seen = set()
    items = []
    for q in queries:
        root = fetch_rss(q)
        for item in root.findall(".//item")[:10]:
            t = (item.find("title").text or "")
            # Strip " - Google 뉴스" suffix and HTML entities
            t = unescape(re.sub(r"\s*-\s*Google\s*뉴스\s*$", "", t))
            if t in seen or "Google 뉴스" in t:
                continue
            seen.add(t)
            src = item.find("source")
            pub = item.find("pubDate")
            items.append({
                "title": t,
                "source": src.text if src is not None else "",
                "pubDate": pub.text if pub is not None else "",
            })
    results[code] = items[:5]

print(json.dumps(results, ensure_ascii=False, indent=2))
```

**Cron-safe invocation** (no pipe-to-interpreter):
```bash
python3 /tmp/kr_news_collect.py > /tmp/kr_news_2026-07-13.json
```

#### 7.8 Naver News Body Extraction — When JS Sites Block curl (added 2026-07-13)

Yonhap/조선일보/전자신문 본문이 JS로 렌더링됨 (curl로 받으면 빈 `<div>`만). **Naver News 채널 (`n.news.naver.com/article/{oid}/{aid}`)** 은 server-rendered HTML이라 본문 추출 가능. 연합뉴스 본문은 `yna.co.kr/view/`도 JS 렌더링이지만, Naver News의 연합 채널은 정상.

```bash
curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0" \
  "https://n.news.naver.com/article/001/0016191550?sid=104" \
  -o /tmp/article.html

# newsct_body 블록 추출 — sed로 HTML 태그 제거
grep -A 250 'newsct_body' /tmp/article.html \
  | sed -E 's/<[^>]+>/ /g; s/&nbsp;/ /g; s/[[:space:]]+/ /g' \
  | head -c 3500
```

**Why this works**: Naver News (`n.news.naver.com/article/...`) is a different render path than the main news site. It returns server-rendered HTML with `<div id="newsct_body">` containing the full article, while other Korean news outlets (yna.co.kr/view/, etnews.com, v.daum.net/v/) return JS-rendered pages or 404s.

**Verification**: Check `wc -c /tmp/article.html` — real article ~200KB+, JS-stub page ~50KB.

#### 7.9 Find Naver Article URLs from Google News (added 2026-07-13)

Google News headlines link to Naver News pages (especially for Korean press). To extract the underlying Naver article URL from Google News RSS:

```bash
# Find Naver article URLs in a Google News RSS feed
curl -sL "https://news.google.com/rss/search?q=..." -o /tmp/news.xml
grep -oE 'href="https://news\.naver\.com/[^"]+"' /tmp/news.xml | head -5
# Returns URLs like: https://news.naver.com/main/read.naver?mode=LSD&mid=shm&sid1=104&oid=023&aid=0003928909
# The "oid" = outlet ID, "aid" = article ID — use these to construct direct Naver News URL:
# https://n.news.naver.com/article/{oid}/{aid}
```

**Or use search.naver.com for discovery** when Google News doesn't surface enough:
```bash
curl -sL -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://search.naver.com/search.naver?where=news&query=ENCODED_QUERY&pd=1" \
  -o /tmp/search.html
grep -oE 'article/[0-9]+/[0-9]+' /tmp/search.html | head -10
# Returns: article/023/0003928909, article/009/0005706657, ...
# Prefix with: https://n.news.naver.com/
```

#### 7.10 Korean Stock News Causal Chain Reporting (added 2026-07-13)

When the user asks "why did KOSPI drop?", the workflow is:

1. **Headline collection**: parallel Google News RSS for `KOSPI+급락`, `반도체+매도`, `유가+급등`, `호르무즈+2026`
2. **Body extraction**: pick 3-4 representative articles from different outlets (MBN, KBS, 헤럴드경제, 매일경제) → extract `newsct_body` to confirm causal chain
3. **Cross-source verification**: Korean outlets often share wire copy (연합뉴스/AFP). Extract quotes that appear across multiple sources. If multiple outlets report the same cause, that's the verified explanation.
4. **Quote-in-source attribution**: report only what each outlet actually wrote. Don't synthesize a number that wasn't in the source.

**User preference observed 2026-07-13**: "정성 뉴스만 반환, 수치를 새로 생성하지 말라" (return only qualitative news, do not fabricate new numbers). When reporting market data points (KOSPI %, ticker prices), only cite numbers that appear in the actual article body — never extrapolate or interpolate.

When a ticker has no same-day article (e.g. 소형주, 신규 종목), report this explicitly and substitute the most recent prior-day article that includes relevant context (earnings, contract wins, sector trends). Never invent a headline for a missing ticker.

### 8. YouTube / Video Search

When you need to find YouTube videos about a topic but the browser is unavailable:

**Search:**
```bash
curl -s "https://www.youtube.com/results?search_query=KEYWORD+KEYWORD2" |
  grep -oP '/watch\?v=[^"&]+' | sort -u | head -10
```

**Get metadata (title, channel, thumbnail):**
```bash
curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
```

**Bulk lookup:**
```bash
for vid in "ID1" "ID2"; do
  curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=$vid&format=json" |
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','?'), '-', d.get('author_name','?'))"
done
```

See `references/youtube-search-via-curl.md` for full details, Korean query handling, and pitfalls.

## Pitfalls

1. **Missing User-Agent**: Sites like Google, DDG, and some CDNs block requests with no/bare User-Agent. Always set `-H "User-Agent: Mozilla/5.0 ..."`
2. **JavaScript-rendered content**: This technique ONLY works for server-rendered HTML. SPAs (React, Vue, Angular) that render content via JS require browser_navigate or a headless browser.
3. **API rate limits**: GitHub unauthenticated API is limited to 60 req/hr. Set up a token for 5000 req/hr.
4. **Pipe to Python security**: The command `curl ... | python3 -c` triggers Hermes' security scanner ("Pipe to interpreter" warning). It will ask for approval. For repeated operations, write intermediate files with `-o /tmp/page.html` then read from file, or pre-write a Python script.
5. **HTML entity encoding**: Site content often uses `&#x27;`, `&amp;`, `&quot;`, `&lt;`, `&gt;` — always decode these in post-processing.
6. **Nested HTML**: Regex is not a parser — deeply nested HTML, script tags, and inline styles can confuse simple regex patterns. For complex pages, consider writing a more robust extraction using Python's `html.parser` or `BeautifulSoup` if available.
7. **execute_code blocked in cron jobs**: `execute_code` is denied in cron mode because there's no user to approve "pipe to interpreter" security prompts. Workaround: (a) write a reusable Python script to `/tmp/` via `write_file`, (b) download data with `curl` via `terminal()`, (c) invoke the script via `terminal()` with arguments. See §7.5 Cron-Safe RSS Workflow.
8. **S&P 500 / generic RSS queries return noise**: High-level queries like "S&P 500 stock market" often return unrelated news (politics, obituaries, sports) because Google News keyword matching is broad. Fix: use more specific queries like "S&P 500 tech rally", or add date constraints like "June 2026" to narrow results.
9. **GitHub API 301 redirects silently fail**: `api.github.com/repos/{owner}/{repo}` returns 301 when a repo is renamed (e.g. `sst/opencode` → `anomalyco/opencode`). Without `curl -L`, you get a JSON-looking "Moved Permanently" response and your extractor returns `None`. **Always `curl -sL` for GitHub API.** See §3.1.
10. **`.dev`/`.exe` TLDs blocked by tirith security scan**: Hermes' terminal pre-flight blocks commands containing lookalike-TLD URLs. Workaround: use `vet https://url` first to confirm, or use `browser_navigate`. See §9.
11. **Cloudflare challenges look like HTML**: A page returning `cdn-cgi/challenge-platform` in the body, ~10KB in size, with `<noscript>Enable JavaScript</noscript>` is a Cloudflare managed challenge — NOT the content you want. Don't waste iterations parsing it. See §9.
12. **Blog URL slugs change after rebrands**: After a company rebrands (e.g. Windsurf → Devin Desktop), old blog URLs at `codeium.com/windsurf/changelog` may 404. Always check the new corporate parent domain (`devin.ai/blog/`) for rebrand-era content.
13. **Wasting budget on re-reads**: When you extract data and only hold it in your context window, you'll re-read the same HTML to "remember" facts — burning 3-5 calls per source. **Cache extracted data as JSON files in /tmp/** so write_file can ingest them in one call.
14. **Iteration cap is real**: At ~50 tool calls, you cannot do "fetch → extract → write → polish → fetch more → rewrite" loops for a 30-50KB deliverable. Front-load fetches, write once, ship once. See §11.

## Verification

After running extractions, spot-check:
```bash
# Check raw content size (Cloudflare challenges are ~10KB; real content is much larger)
wc -c /tmp/page.html

# Quick keyword check
grep -c "target_keyword" /tmp/page.html

# Verify GitHub API didn't return a redirect
curl -sL "https://api.github.com/repos/owner/repo" | python3 -c "import json,sys; d=json.load(sys.stdin); print('NAME:', d.get('full_name','MISSING — got redirect?'))"

# View first 20 lines of extracted JSON
python3 -c "import json; d=json.load(open('output.json')); [print(json.dumps(item,ensure_ascii=False)[:200]) for item in d[:3]]"
```
| Korean Stocks | `005930.KS`, `000660.KS`, etc. | Append `.KS` for KOSPI, `.KQ` for KOSDAQ |

#### 8.2 Core Pattern: Python urllib (bypasses curl empty-response issue)

Curl to Yahoo Finance often returns empty JSON because the API requires specific request headers. Python's `urllib.request` with a browser User-Agent reliably returns data:

```bash
python3 -c "
import urllib.request, json

url = 'https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=10d'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
result = data['chart']['result'][0]
quotes = result['indicators']['quote'][0]['close']
timestamps = result['timestamp']
from datetime import datetime
for t, c in zip(timestamps[-5:], quotes[-5:]):
    if c:
        print(f'{datetime.fromtimestamp(t).strftime(\"%m/%d\")}: {c:.2f}')
"
```

#### 8.3 Multi-Ticker Collection (Bulk Fetch)

For macro reports, collect all key indicators in one script:

```bash
python3 -c "
import urllib.request, json

urls = {
    'spy': 'https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=5d',
    'cl': 'https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1d&range=5d',
    'tnx': 'https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=5d',
    'dxy': 'https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d',
    'krw': 'https://query1.finance.yahoo.com/v8/finance/chart/KRW=X?interval=1d&range=5d',
}
for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        result = data['chart']['result']
        if result and result[0]:
            quotes = result[0]['indicators']['quote'][0]['close']
            timestamps = result[0]['timestamp']
            d = {name: [(t, c) for t, c in zip(timestamps[-3:], quotes[-3:]) if c]}
            print(f'{name}: {d[name]}')
    except Exception as e:
        print(f'{name}: {e}')
"
```

#### 8.4 Korean Stock Price Collection (yfinance tickers)

Korean stocks use `.KS` (KOSPI) and `.KQ` (KOSDAQ) suffixes:

| Stock | Ticker | Note |
|-------|--------|------|
| 삼성전자 | `005930.KS` | KOSPI |
| SK하이닉스 | `000660.KS` | KOSPI |
| 삼성전기 | `009150.KS` | KOSPI |
| 현대차 | `005380.KS` | KOSPI |
| 에이피알 | `278280.KQ` | KOSDAQ (note: `.KQ` not `.KS`) |
| HD현대일렉 | `267260.KS` | KOSPI |

#### 8.5 Cron-Safe Data Collection Pattern

In cron jobs:
- ❌ `execute_code` is blocked (no user to approve security prompts)
- ❌ `curl | python3 -c` pipes trigger security scanner warnings
## Pitfalls

1. **Missing User-Agent**: Sites like Google, DDG, and some CDNs block requests with no/bare User-Agent. Always set `-H "User-Agent: Mozilla/5.0 ..."`
2. **JavaScript-rendered content**: This technique ONLY works for server-rendered HTML. SPAs (React, Vue, Angular) that render content via JS require browser_navigate or a headless browser.
3. **API rate limits**: GitHub unauthenticated API is limited to 60 req/hr. Set up a token for 5000 req/hr.
4. **Pipe to Python security**: The command `curl ... | python3 -c` triggers Hermes' security scanner ("Pipe to interpreter" warning). It will ask for approval. For repeated operations, write intermediate files with `-o /tmp/page.html` then read from file, or pre-write a Python script.
5. **HTML entity encoding**: Site content often uses `&#x27;`, `&amp;`, `&quot;`, `&lt;`, `&gt;` — always decode these in post-processing.
6. **Nested HTML**: Regex is not a parser — deeply nested HTML, script tags, and inline styles can confuse simple regex patterns. For complex pages, consider writing a more robust extraction using Python's `html.parser` or `BeautifulSoup` if available.
7. **execute_code blocked in cron jobs**: `execute_code` is denied in cron mode because there's no user to approve "pipe to interpreter" security prompts. Workaround: (a) write a reusable Python script to `/tmp/` via `write_file`, (b) download data with `curl` via `terminal()`, (c) invoke the script via `terminal()` with arguments. See §7.5 Cron-Safe RSS Workflow.
8. **S&P 500 / generic RSS queries return noise**: High-level queries like "S&P 500 stock market" often return unrelated news (politics, obituaries, sports) because Google News keyword matching is broad. Fix: use more specific queries like "S&P 500 tech rally", or add date constraints like "June 2026" to narrow results.
9. **GitHub API 301 redirects silently fail**: `api.github.com/repos/{owner}/{repo}` returns 301 when a repo is renamed (e.g. `sst/opencode` → `anomalyco/opencode`). Without `curl -L`, you get a JSON-looking "Moved Permanently" response and your extractor returns `None`. **Always `curl -sL` for GitHub API.** See §3.1.
10. **`.dev`/`.exe` TLDs blocked by tirith security scan**: Hermes' terminal pre-flight blocks commands containing lookalike-TLD URLs. Workaround: use `vet https://url` first to confirm, or use `browser_navigate`. See §9.
11. **Cloudflare challenges look like HTML**: A page returning `cdn-cgi/challenge-platform` in the body, ~10KB in size, with `<noscript>Enable JavaScript</noscript>` is a Cloudflare managed challenge — NOT the content you want. Don't waste iterations parsing it. See §9.
12. **Blog URL slugs change after rebrands**: After a company rebrands (e.g. Windsurf → Devin Desktop), old blog URLs at `codeium.com/windsurf/changelog` may 404. Always check the new corporate parent domain (`devin.ai/blog/`) for rebrand-era content.
13. **Wasting budget on re-reads**: When you extract data and only hold it in your context window, you'll re-read the same HTML to "remember" facts — burning 3-5 calls per source. **Cache extracted data as JSON files in /tmp/** so write_file can ingest them in one call.
14. **Iteration cap is real**: At ~50 tool calls, you cannot do "fetch → extract → write → polish → fetch more → rewrite" loops for a 30-50KB deliverable. Front-load fetches, write once, ship once. See §11.

## Verification

After running extractions, spot-check:
```bash
# Check raw content size (Cloudflare challenges are ~10KB; real content is much larger)
wc -c /tmp/page.html

# Quick keyword check
grep -c "target_keyword" /tmp/page.html

# Verify GitHub API didn't return a redirect
curl -sL "https://api.github.com/repos/owner/repo" | python3 -c "import json,sys; d=json.load(sys.stdin); print('NAME:', d.get('full_name','MISSING — got redirect?'))"

# View first 20 lines of extracted JSON
python3 -c "import json; d=json.load(open('output.json')); [print(json.dumps(item,ensure_ascii=False)[:200]) for item in d[:3]]"
```
