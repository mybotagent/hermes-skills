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

## Alternative: Naver News direct articles (when available)

If a Google News headline links to a Naver News article (`n.news.naver.com/article/{oid}/{aid}`), the article body IS server-rendered and curl-accessible:

```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://n.news.naver.com/article/001/0016191550?sid=104" -o /tmp/article.html
# Extract body: look for id="newsct_body"
grep -A 250 'newsct_body' /tmp/article.html | sed 's/<[^>]*>/ /g' | head -c 2000
```

This works for Naver News ( 연합뉴스, 매일경제, etc.) but NOT for the direct outlet sites (yna.co.kr/view/, etnews.com) which are JS-rendered.
