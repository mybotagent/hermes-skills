#!/usr/bin/env python3
"""
fetch_kr_stocks.py — 네이버 Polling API에서 한국 주식 데이터 수집
등락률(cr)의 부호를 nv-pcv로 직접 계산하여 정확한 ±값 출력.

SINGLE SOURCE OF TRUTH: data/watchlist.json (KR 종목 목록)
경고: Naver Polling `cr` 필드는 항상 절대값(양수). 
      부호는 반드시 nv - pcv로 직접 계산해야 함.
      절대 cr 필드를 그대로 사용 금지!

Usage:
    python3 scripts/fetch_kr_stocks.py
    python3 scripts/fetch_kr_stocks.py --json
"""
import json, urllib.request, sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
WATCH_PATH = os.path.join(PROJECT_DIR, "data", "watchlist.json")


def load_kr_tickers() -> list[dict]:
    """watchlist.json에서 KR 종목 로드 (단일 진실 공급원)"""
    with open(WATCH_PATH, encoding="utf-8") as f:
        watch = json.load(f)
    kr_stocks = []
    for s in watch.get("stocks", []):
        market = s.get("market", "")
        ticker = s.get("ticker", "")
        if market == "KR" or ".KS" in ticker:
            code = ticker.replace(".KS", "").replace(".KQ", "")
            kr_stocks.append({
                "code": code,
                "ticker": ticker,
                "name": s.get("name", ticker),
                "sector": s.get("sector", ""),
            })
    return kr_stocks


def fetch_kr_prices() -> list[dict]:
    """네이버 Polling API 호출 → 각 종목 현재가·전일종가·등락률(±) 반환"""
    stocks = load_kr_tickers()
    results = []
    for s in stocks:
        code = s["code"]
        try:
            url = f'https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw = urllib.request.urlopen(req, timeout=10).read()
            data = json.loads(raw.decode('euc-kr', errors='ignore'))
            item = data['result']['areas'][0]['datas'][0]

            nm_naver = item.get('nm', '')
            nv = int(item['nv'])
            pcv = int(item['pcv'])
            cr_abs = float(item['cr'])  # ⚠️ 항상 양수!
            diff = nv - pcv
            sign = 1 if diff >= 0 else -1
            cr_signed = round(cr_abs * sign, 2)

            result_item = {
                "code": code,
                "ticker": s["ticker"],
                "name": s["name"],
                "naver_name": nm_naver,
                "current": nv,
                "prev_close": pcv,
                "change": diff,
                "change_pct": cr_signed,
                "change_display": f"{diff:+,d}",
                "change_pct_display": f"{cr_signed:+.2f}%",
            }

            if nm_naver and nm_naver != s["name"]:
                warn = f"⚠️ Naver name mismatch: {s['name']} → Naver says '{nm_naver}'"
                result_item["name_warning"] = warn

            results.append(result_item)
        except Exception as e:
            results.append({
                "code": code,
                "ticker": s["ticker"],
                "name": s["name"],
                "error": str(e),
            })
    return results


if __name__ == "__main__":
    data = fetch_kr_prices()
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{'종목':14s} {'현재가':>10s} {'전일종가':>10s} {'전일비':>10s} {'등락률':>10s} {'비고':>10s}")
        print("-" * 65)
        for r in data:
            if "error" in r:
                print(f"{r['name']:14s} {'Error: ' + r['error']}")
            else:
                warn = r.get("name_warning", "")
                print(f"{r['name']:14s} {r['current']:>10,d} {r['prev_close']:>10,d} {r['change_display']:>10s} {r['change_pct_display']:>10s} {warn:>10s}")
