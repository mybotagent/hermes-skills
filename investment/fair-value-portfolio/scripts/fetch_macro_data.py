#!/usr/bin/env python3
"""
fetch_macro_data.py — 검증된 실시간 매크로 데이터 수집기
경로: ~/trade-pipeline/scripts/fetch_macro_data.py
호출: python3 ~/trade-pipeline/scripts/fetch_macro_data.py

한국 증시 + 글로벌 핵심 지표를 수집합니다.
urllib 사용 — cron 모드에서 curl|bash 파이프 대신 사용 가능.
"""
import urllib.request, ssl, json, sys, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY_STR = NOW.strftime('%Y-%m-%d')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read().decode('utf-8', errors='ignore')

results = {
    'timestamp': NOW.isoformat(),
    'date': TODAY_STR,
    'fx': {},
    'us_stocks': {},
    'kr_stocks': {},
    'news_items': [],
    'errors': []
}

# ─── 환율 ───
try:
    d = json.loads(fetch('https://api.exchangerate-api.com/v4/latest/USD'))
    results['fx']['usdkrw'] = d['rates'].get('KRW')
    results['fx']['usdjpy'] = d['rates'].get('JPY')
    results['fx']['eurusd'] = round(1 / d['rates'].get('EUR'), 4)
except Exception as e:
    results['errors'].append(f'환율: {e}')

# ─── Yahoo Finance: 미국 증시 ───
us_tickers = {
    'sp500': '%5EGSPC',
    'nasdaq': '%5EIXIC',
    'vix': '%5EVIX',
    'tnx': '%5ETNX',       # 10년물 금리
    'gold': 'GC%3DF',
    'dxy': 'DXY',
}
for name, sym in us_tickers.items():
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d'
        d = json.loads(fetch(url))
        results['us_stocks'][name] = d['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        results['errors'].append(f'{name}: {e}')

# ─── Yahoo Finance: 한국 증시 ───
kr_tickers = {
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '000100': '삼성전기',
    '005380': '현대차',
    '051900': 'HD현대일렉',
}
for code, name in kr_tickers.items():
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.KS?interval=1d&range=2d'
        d = json.loads(fetch(url))
        results['kr_stocks'][name] = d['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        results['errors'].append(f'{name}: {e}')

# ─── KOSPI via query2 ───
try:
    url = 'https://query2.finance.yahoo.com/v8/finance/chart/%5EKS11?interval=1d&range=2d'
    d = json.loads(fetch(url))
    results['us_stocks']['kospi'] = d['chart']['result'][0]['meta']['regularMarketPrice']
except Exception as e:
    results['errors'].append(f'KOSPI: {e}')

# ─── WTI: Google News RSS에서 최신 수치 추적 ───
try:
    # Fortune WTI 기사
    q = 'WTI+crude+oil+price+September+2026'
    xml = fetch(f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en', timeout=20)
    root = ET.fromstring(xml)
    for item in root.findall('.//item')[:3]:
        title = item.findtext('title') or ''
        if 'WTI' in title or 'oil' in title.lower() or 'crude' in title.lower():
            results['fx']['wti_news_title'] = title
            results['fx']['wti_news_date'] = item.findtext('pubDate', '')
            break
except Exception as e:
    results['errors'].append(f'WTI news: {e}')

print(json.dumps(results, ensure_ascii=False, indent=2))
