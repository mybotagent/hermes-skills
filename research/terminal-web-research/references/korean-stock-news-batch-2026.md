# Korean Stock News Batch Collector — Proven Pattern
# Tested: 2026-09-21, 6 tickers, Google News RSS hl=ko/gl=KR/ceid=KR:ko
#
# Usage:
#   python3 /tmp/kr_news_final.py  # outputs to stdout; save: > /tmp/kr_news.json
#
# Cron-safe: writes script file first, invokes via terminal() — no pipe-to-interpreter.
#
# ⚠️ Ticker codes — VERIFIED 2026-09-21 against user's actual portfolio codes:
#   삼성전자       005930  (KOSPI)
#   SK하이닉스     000660  (KOSPI)
#   삼성전기       009150  (KOSPI)
#   현대차         005380  (KOSPI)
#   에이피알       352820  (KOSDAQ) ← was 052220 in older batch files — ALWAYS re-verify
#   HD현대일렉     054050  (KOSPI)  ← was 267260 in older batch files — ALWAYS re-verify
# KRX codes change; company re-listings happen. Never assume a pre-verified code is still valid.

import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import re
import json
from html import unescape

# === CONFIGURE YOUR TARGETS HERE ===
TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("009150", "삼성전기"),
    ("005380", "현대차"),
    ("352820", "에이피알"),
    ("054050", "HD현대일렉"),
]
# ==================================

def fetch_rss(query, hl="ko", gl="KR", ceid="KR:ko"):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    return ET.fromstring(urllib.request.urlopen(req, timeout=15).read())

def strip_google_suffix(title):
    return unescape(re.sub(r'\s*-\s*Google\s*뉴스\s*$', '', title))

def extract_article_url(item):
    """Extract the best available article URL from RSS item."""
    desc_el = item.find("description")
    if desc_el is not None and desc_el.text:
        for pat in [
            r'href="(https://news\.naver\.com[^"]+)"',
            r'https://news\.naver\.com/\S+',
            r'https://n\.news\.naver\.com/article/\d+/\d+',
        ]:
            m = re.search(pat, desc_el.text)
            if m:
                return m.group(1) if m.group(1).startswith('http') else f"https://news.naver.com{m.group(1)}"
    link_el = item.find("link")
    if link_el is not None and link_el.text:
        return link_el.text
    return ""

def format_date(pub_date):
    if not pub_date:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date)
        return dt.strftime("%Y년 %m월 %d일 %H:%M")
    except:
        return pub_date

results = {}
for code, name in TARGETS:
    seen = set()
    items = []
    queries = [f"{name}+2026년+9월+21일", f"{name}+{code}"]

    for q in queries:
        try:
            root = fetch_rss(q)
            for item in root.findall(".//item")[:15]:
                title_el = item.find("title")
                if title_el is None or not title_el.text:
                    continue
                t = strip_google_suffix(title_el.text)
                if t in seen or "Google 뉴스" in t:
                    continue
                seen.add(t)

                src_el = item.find("source")
                pub_el = item.find("pubDate")

                items.append({
                    "title": t,
                    "source": src_el.text if src_el is not None else "",
                    "pubDate": format_date(pub_el.text if pub_el is not None else ""),
                    "url": extract_article_url(item),
                })
        except Exception as e:
            items.append({"title": f"[ERROR]: {str(e)}", "source": "", "pubDate": "", "url": ""})

    # Dedupe by title
    seen2 = set()
    deduped = []
    for it in items:
        if it["title"] not in seen2:
            seen2.add(it["title"])
            deduped.append(it)

    results[name] = {"code": code, "items": deduped[:5]}

# Save JSON
with open('/tmp/kr_stock_news_latest.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print markdown
print("# 한국 증시 뉴스 | 2026년 9월 21일 (월)\n")
for name, data in results.items():
    print(f"\n## {name} ({data['code']})\n")
    for i, item in enumerate(data["items"], 1):
        print(f"**{i}. {item['title']}**")
        print(f"- 출처: {item['source']} | {item['pubDate']}")
        if item["url"]:
            print(f"- URL: {item['url']}")
        print()
print("---\n*출처: Google 뉴스 RSS (hl=ko, gl=KR) | 2026년 9월 21일 수집*")
