# RSS News Extraction — Reference

> Detailed extraction patterns and ready-to-use script template for Google News RSS parsing.
> Used by the `terminal-web-research` skill (section 7: RSS/XML Parsing for News Research).

## Quick-Start: One-Shot Extraction

Copy this into a `terminal()` call to get headlines for any topic:

```bash
curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://news.google.com/rss/search?q=YOUR_SEARCH_HERE&hl=en-US&gl=US&ceid=US:en" \
  -o /tmp/_rss.xml 2>&1 && python3 -c "
import xml.etree.ElementTree as ET, re
for item in ET.parse('/tmp/_rss.xml').findall('.//item')[:10]:
    t = (item.find('title').text or 'N/A').replace('<![CDATA[', '').replace(']]>', '')
    s = (item.find('source').text if item.find('source') is not None else '') or ''
    d = (item.find('pubDate').text or '') or ''
    print(f'  [{s}] {t}')
    print(f'    {d}')
"
```

## Full Extraction Script (Multi-Topic)

Save this as a Python script (`/tmp/rss_extract.py`) for repeated use:

```python
#!/usr/bin/env python3
"""Google News RSS extractor — run multiple searches and collect results."""
import xml.etree.ElementTree as ET
import json, sys, os, re
from datetime import datetime
from html import unescape

SEARCHES = [
    # (label, url_encoded_query, max_items)
    ("macro-fed", "Federal+Reserve+interest+rate+inflation", 8),
    ("semi-ai", "semiconductor+AI+chip+NVIDIA+export+controls", 8),
    ("market", "S%26P+500+Nasdaq+stock+market+treasury+yield", 8),
    ("geopolitics", "US+China+trade+tariff+geopolitics", 8),
]

def fetch_rss(label, query, max_items=8):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    tmp = f"/tmp/_rss_{label}.xml"
    os.system(f'curl -sL -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" "{url}" -o {tmp}')
    
    results = []
    try:
        tree = ET.parse(tmp)
        for item in tree.findall('.//item')[:max_items]:
            title = item.find('title')
            source = item.find('source')
            pubdate = item.find('pubDate')
            desc = item.find('description')
            
            title_text = unescape(title.text or '') if title is not None else ''
            # Skip Google News self-references
            if 'Google News' in title_text or ' - Google News' in title_text:
                continue
                
            results.append({
                'title': title_text,
                'source': source.text if source is not None else '',
                'date': pubdate.text if pubdate is not None else '',
                'snippet': unescape(re.sub(r'<[^>]+>', '', desc.text or '')[:200]),
            })
    except Exception as e:
        print(f"  ERROR parsing {label}: {e}", file=sys.stderr)
    
    return results

def main():
    all_results = {}
    for label, query, max_items in SEARCHES:
        print(f"Fetching: {label}...", file=sys.stderr)
        all_results[label] = fetch_rss(label, query, max_items)
        print(f"  -> {len(all_results[label])} items", file=sys.stderr)
    
    # Output JSON for automated processing
    print(json.dumps(all_results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
```

Usage:
```bash
python3 /tmp/rss_extract.py > /tmp/all_news.json
```

## Common Search Queries by Domain

### Macro Economy
```
Federal+Reserve+interest+rate+decision+2026
ECB+inflation+interest+rate+decision+2026
Bank+of+Japan+BOJ+rate+decision+yen
US+GDP+ISM+manufacturing+PMI+2026
US+employment+payrolls+nonfarm+2026
10+year+Treasury+yield+bond+market+2026
DXY+dollar+index+USD+trend+2026
CPI+inflation+consumer+prices+2026
```

### Semiconductors / AI
```
semiconductor+AI+chip+NVIDIA+AMD+stock+2026
BIS+export+controls+chip+semiconductor+2026
HBM+DDR5+memory+pricing+SK+Hynix+NVIDIA
AI+Capex+spending+data+center+2026
Broadcom+AVGO+Qualcomm+QCOM+earnings+2026
NVDA+Rubin+Vera+platform+memory+HBM
Philadelphia+semiconductor+index+SOX+2026
semiconductor+selloff+correction+2026
```

### Geopolitics
```
US+China+trade+tariffs+semiconductor+2026
Iran+Strait+of+Hormuz+oil+2026
Taiwan+TSMC+chip+supply+chain+2026
rare+earth+mineral+export+controls+2026
```

### Korea / Asia Markets
```
KOSPI+Korea+stock+market+foreign+selloff+2026
Samsung+Electronics+SK+Hynix+stock+2026
USD+KRW+exchange+rate+won+2026
COMPUTEX+2026+semiconductor+expo
```

## Pitfalls

1. **CDATA sections**: Some `<title>` content is wrapped in `<![CDATA[...]]>` — strip it with `replace('<![CDATA[', '').replace(']]>', '')`.
2. **HTML entities**: `&amp;`, `&#x27;`, `&quot;` in titles — use Python's `html.unescape()` before display.
3. **Google News self-references**: First 1-2 items are always `"{query} - Google News"` and `"Google News"` — filter them out.
4. **Description field**: Can contain raw HTML — always strip tags with `re.sub(r'<[^>]+>', '', desc)` before reading.
5. **Date format**: `pubDate` is RFC 2822 (`Fri, 05 Jun 2026 12:31:00 GMT`). Use `datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z')` for structured parsing.
6. **Empty results**: If a query returns 0 real items, broaden the search or switch to a different domain/source.
7. **Bot detection**: Rare with Google News RSS but if you get a CAPTCHA page instead of XML, add a 1-2 second delay between requests and reduce concurrent terminals.
