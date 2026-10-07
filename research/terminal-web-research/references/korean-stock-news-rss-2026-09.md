# Korean Stock News via Google News RSS (2026-09-25)

## Verified Working Pattern

```python
import urllib.request
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET
import html, re

def fetch_korean_stock_news(query, lang='ko', country='KR', limit=3):
    """Fetch Korean stock news via Google News RSS.
    
    Returns list of dicts: {title, url (Google News deep-link), source, pubDate}
    """
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={lang}&gl={country}&ceid={country}:{lang}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        xml_data = resp.read()
    root = ET.fromstring(xml_data)
    items = root.findall('.//item')
    results = []
    for item in items[:limit]:
        title = html.unescape(item.findtext('title', ''))
        link = item.findtext('link', '')
        desc_html = item.findtext('description', '')
        # Extract source name: <font color="#6f6f6f">source_name</font>
        src_match = re.search(r'<font color="#6f6f6f">([^<]+)</font>', desc_html)
        source = src_match.group(1) if src_match else 'Google News'
        pub = item.findtext('pubDate', '')
        results.append({'title': title, 'url': link, 'source': source, 'pubDate': pub})
    return results

# Usage
for ticker, query in [('005930', '삼성전자 005930'), ('000660', 'SK하이닉스 000660')]:
    print(f'=== {ticker} ===')
    for i, a in enumerate(fetch_korean_stock_news(query)):
        print(f"  [{i+1}] {a['title']}")
        print(f"      Source: {a['source']} ({a['pubDate']})")
        print(f"      URL: {a['url']}")
```

## Key Learnings (2026-09-25)

1. **URL encoding is mandatory** with `urllib.request.urlopen()` — spaces cause `InvalidURL` unless `urllib.parse.quote()` is used first.

2. **`link` field in RSS items is a Google News deep-link, NOT the original article URL** — attempting to `urlopen()` it just returns the Google URL with different query params. Do NOT try to resolve it to the original source; instead extract source name from the `description` field's `<font color="#6f6f6f">` tag.

3. **`description` HTML structure** (confirmed format):
   ```html
   <a href="https://news.google.com/rss/articles/..." target="_blank"> headline text </a>&nbsp;&nbsp;<font color="#6f6f6f">source_name</font>
   ```

4. **`search.naver.com` is JS-rendered** — do not use. The `<a class="news_tit">` elements are in the static HTML but the news list content is populated by JS. Use Google News RSS instead.

5. **Korean query params**: `hl=ko&gl=KR&ceid=KR:ko` returns Korean-language domestic press results.

## Batch Per-Ticker Script (2026-10-06)

For macro reports covering 6 Korean tickers, use a reusable batch script that collects news for all tickers in one run:

```python
# /tmp/kr_news_collect.py — reusable, cron-safe (no pipe-to-interpreter)
import xml.etree.ElementTree as ET, json, urllib.request, urllib.parse, re
from html import unescape

TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("009150", "삼성전기"),
    ("005380", "현대차"),
    ("352820", "에이피알"),
    ("054050", "HD현대일렉"),
]

def fetch_rss(query, hl="ko", gl="KR", ceid="KR:ko"):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return ET.fromstring(r.read())

results = {}
for code, name in TARGETS:
    seen = set()
    items = []
    for q in [f"{name}+2026년+10월", f"{name}+{code}"]:
        root = fetch_rss(q)
        for item in root.findall(".//item")[:10]:
            t_el = item.find("title")
            t = unescape(t_el.text) if t_el is not None and t_el.text else ""
            t = re.sub(r"\s*-\s*Google\s*뉴스\s*$", "", t).strip()
            if not t or t in seen or "Google 뉴스" in t:
                continue
            seen.add(t)
            src = item.find("source")
            pub = item.find("pubDate")
            desc_el = item.find("description")
            desc_src = ""
            if desc_el is not None and desc_el.text:
                m = re.search(r'<font color="#6f6f6f">([^<]+)</font>', desc_el.text)
                if m:
                    desc_src = m.group(1)
            items.append({
                "title": t,
                "source": src.text if src is not None else (desc_src or ""),
                "pubDate": pub.text if pub is not None else "",
            })
    results[code] = items[:5]

print(json.dumps(results, ensure_ascii=False, indent=2))
```

Cron-safe invocation:
```bash
python3 /tmp/kr_news_collect.py > /tmp/kr_news_2026-10-06.json
```

**Key patterns demonstrated:**
- Multi-query per ticker (`name+2026년+10월` + `name+ticker`) for breadth
- `seen = set()` deduplication across query variants
- Strip `" - Google 뉴스"` suffix with regex: `r"\s*-\s*Google\s*뉴스\s*$"`
- Fallback source from `description` HTML when `<source>` element is empty
- `urllib.parse.quote()` always — spaces in Korean queries cause `InvalidURL`

## Verified 2026-10-06 News Data (sample output)

```json
{
  "005930": [
    {"title": "경찰, '장인회사 계약 논란' 삼성전자 노조ectable 수상 착수", "source": "뉴스핌", "pubDate": "Tue, 06 Oct 2026 06:10:00 GMT"},
    {"title": "삼성전기, 글로벌 기업과 2천900억 AI 서버용 MLCC 공급계약", "source": "연합뉴스", "pubDate": "Tue, 06 Oct 2026 02:46:56 GMT"}
  ],
  "009150": [
    {"title": "삼성전기, 글로벌 기업과 2천900억 AI 서버용 MLCC 공급계약 체결", "source": "연합뉴스", "pubDate": "Tue, 06 Oct 2026 02:46:56 GMT"},
    {"title": "삼성전기, 2,856억원 규모 공급계약에 5% 급등", "source": "CEO경제신문", "pubDate": "Tue, 06 Oct 2026 03:10:20 GMT"}
  ],
  "000660": [
    {"title": "넥스틴, SK하이닉스와 254억원 규모 공급계약", "source": "데이터투자", "pubDate": "Tue, 06 Oct 2026 02:14:22 GMT"}
  ]
}
```

## Alternative: Naver News direct articles (when available)

If a Google News headline links to a Naver News article (`n.news.naver.com/article/{oid}/{aid}`), the article body IS server-rendered and curl-accessible:

```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://n.news.naver.com/article/001/0016191550?sid=104" -o /tmp/article.html
# Extract body: look for id="newsct_body"
grep -A 250 'newsct_body' /tmp/article.html | sed 's/<[^>]*>/ /g' | head -c 2000
```

This works for Naver News ( 연합뉴스, 매일경제, etc.) but NOT for the direct outlet sites (yna.co.kr/view/, etnews.com) which are JS-rendered.
