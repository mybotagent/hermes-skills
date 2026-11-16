#!/usr/bin/env python3
"""
Paper Portfolio Performance Tracker
- Reads logs/portfolio/*.json daily snapshots
- Fetches yfinance prices for all tracked stocks
- Calculates: cumulative return (total/1m/3m/6m/1y), MDD, Sharpe
- Outputs: CSV (daily, holdings, market) + JSON metrics
- Dashboard: portfolio_dashboard.html
"""
import json, os, sys, csv, re
from datetime import datetime, date, timedelta
try: import yfinance as yf
except ImportError: print("❌ yfinance not installed"); sys.exit(1)
try: import numpy as np
except ImportError: print("❌ numpy not installed"); sys.exit(1)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_DIR = os.path.join(PROJECT_DIR, "logs", "portfolio")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data")
NAME_TO_TICKER = {
    "엔비디아":"NVDA","마이크론":"MU","샌디스크":"WDC","시게이트":"STX",
    "브로드컴":"AVGO","HPE":"HPE","델":"DELL","AMD":"AMD","인텔":"INTC",
    "MSFT":"MSFT","구글":"GOOGL","애플":"AAPL","TSMC":"TSM","LRCX":"LRCX",
    "LITE":"LITE","CLS":"CLS","BWXT":"BWXT","일라이릴리":"LLY","SNDK":"WDC",
    "마이크로소프트":"MSFT","알파벳":"GOOGL","Celestica":"CLS",
    "삼성전자":"005930.KS","SK하이닉스":"000660.KS","삼성전기":"009150.KS",
    "LG이노텍":"011070.KS","현대차":"005380.KS","에이피알":"278470.KQ","기아":"000270.KS",
}
PRICE_CACHE_PATH = os.path.join(OUTPUT_DIR, "paper_price_cache.json")

def load_price_cache():
    if os.path.exists(PRICE_CACHE_PATH):
        with open(PRICE_CACHE_PATH) as f: return json.load(f)
    return {}
def save_price_cache(cache):
    with open(PRICE_CACHE_PATH, "w") as f: json.dump(cache, f, indent=2)
def load_all_portfolios():
    files = sorted(os.listdir(PORTFOLIO_DIR))
    portfolios = []
    for fname in files:
        if not fname.endswith(".json"): continue
        with open(os.path.join(PORTFOLIO_DIR, fname)) as f: portfolios.append(json.load(f))
    return portfolios
def extract_stocks_from_portfolios(portfolios):
    stocks = set()
    for p in portfolios:
        for s in p.get("stocks", []): stocks.add(s["name"])
    return sorted(stocks)
def portfolio_dates(portfolios):
    return sorted(set(p.get("date","") for p in portfolios if p.get("date")))
def is_valid_price(v):
    if v is None: return False
    try: return not (v != v)
    except: return False
def fetch_daily_prices(tickers, start_date, end_date, cache):
    tickers_to_fetch = [t for t in tickers if t not in cache]
    if not tickers_to_fetch: return cache
    for t in tickers_to_fetch:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty: continue
            prices = {}
            for idx, row in hist.iterrows():
                prices[idx.strftime("%Y-%m-%d")] = round(float(row["Close"]), 2)
            cache[t] = prices
        except Exception as e:
            print(f"  ⚠️  {t}: {str(e)[:60]}")
    save_price_cache(cache)
    return cache

def calc_daily_returns(portfolios, price_cache):
    all_dates = portfolio_dates(portfolios)
    if len(all_dates) < 2: return [], []
    date_to_portfolio = {p.get("date"): p for p in portfolios if p.get("date")}
    daily_returns, holdings_detail = [], []
    for i in range(1, len(all_dates)):
        d_prev, d_curr = all_dates[i-1], all_dates[i]
        p_curr = date_to_portfolio.get(d_curr)
        if not p_curr: daily_returns.append((d_curr, 0.0)); continue
        stocks = p_curr.get("stocks", [])
        cash_ratio = float(p_curr.get("cash_ratio","0%").replace("%","")) / 100
        total_return, valid_stocks = 0.0, 0
        day_holdings = []
        for s in stocks:
            name, weight_str = s["name"], s["weight"]
            weight = float(weight_str.replace("%","")) / 100
            ticker = NAME_TO_TICKER.get(name)
            if not ticker: continue
            prices = price_cache.get(ticker, {})
            if not isinstance(prices, dict): continue
            p_prev, p_curr_p = prices.get(d_prev), prices.get(d_curr)
            if is_valid_price(p_prev) and is_valid_price(p_curr_p) and p_prev > 0:
                stock_return = (p_curr_p / p_prev) - 1
                contrib = weight * stock_return
                total_return += contrib; valid_stocks += 1
                day_holdings.append({"date":d_curr,"stock":name,"ticker":ticker,
                    "weight_pct":f"{weight*100:.1f}","stock_return_pct":f"{stock_return*100:.2f}",
                    "contrib_pct":f"{contrib*100:.2f}","price_prev":f"{p_prev:.0f}",
                    "price_curr":f"{p_curr_p:.0f}","reason":s.get("reason","")})
        total_return += cash_ratio * 0.0
        if cash_ratio > 0:
            day_holdings.append({"date":d_curr,"stock":"현금","ticker":"CASH",
                "weight_pct":f"{cash_ratio*100:.1f}","stock_return_pct":"0.00",
                "contrib_pct":"0.00","price_prev":"-","price_curr":"-",
                "reason":"시장 리스크 헷지"})
        daily_returns.append((d_curr, total_return if valid_stocks > 0 else 0.0))
        holdings_detail.extend(day_holdings)
    return daily_returns, holdings_detail

def calc_metrics(daily_returns, risk_free_rate=0.03):
    if not daily_returns: return {"error":"수익률 데이터 없음"}
    returns = [r[1] for r in daily_returns]; dates = [r[0] for r in daily_returns]
    n_days, ann_factor = len(returns), 252
    cum_ret = 1.0; cum_returns = []
    for r in returns: cum_ret *= (1+r); cum_returns.append(cum_ret)
    total_cum = cum_ret - 1
    def recent_cum(n):
        if len(returns) >= n:
            sub = cum_returns[-n:-1]
            recent = sub[-1] if sub else 1.0
            return cum_returns[-1]/recent - 1 if recent > 0 else 0
        lc = 1.0
        for r in returns[-min(n, len(returns)):]: lc *= (1+r)
        return lc-1 if lc > 0 else 0
    peak = cum_returns[0]; mdd = 0.0; mdd_start=mdd_end=dates[0]; ct_start=dates[0]
    for i, v in enumerate(cum_returns):
        if v > peak: peak=v; ct_start=dates[i]
        dd = (v-peak)/peak if peak > 0 else 0
        if dd < mdd: mdd=dd; mdd_start=ct_start; mdd_end=dates[i]
    avg_dr = np.mean(returns); std_dr = np.std(returns, ddof=1)
    daily_rfr = risk_free_rate / ann_factor
    sharpe = (avg_dr - daily_rfr) / std_dr * np.sqrt(ann_factor) if std_dr > 0 else 0.0
    years = n_days / ann_factor; ann_ret = (cum_ret**(1/years))-1 if years > 0 else 0
    return {"기간":f"{dates[0]} ~ {dates[-1]} ({n_days}일)","시작일":dates[0],"종료일":dates[-1],
        "트레이딩일수":n_days,"누적수익률(전체)":f"{total_cum*100:.2f}%",
        "연율화수익률":f"{ann_ret*100:.2f}%","최근1개월수익률":f"{recent_cum(22)*100:.2f}%",
        "최근3개월수익률":f"{recent_cum(66)*100:.2f}%","최근6개월수익률":f"{recent_cum(132)*100:.2f}%",
        "최근12개월수익률":f"{recent_cum(252)*100:.2f}%","MDD":f"{mdd*100:.2f}%",
        "MDD_구간":f"{mdd_start} ~ {mdd_end}","Sharpe_Ratio":f"{sharpe:.2f}",
        "일일수익률_평균":f"{avg_dr*100:.4f}%","일일수익률_표준편차":f"{std_dr*100:.4f}%",
        "가정_무위험수익률":f"{risk_free_rate*100:.1f}%"}

def main():
    portfolios = load_all_portfolios(); print(f"  📂 {len(portfolios)}개 스냅샷")
    stocks = extract_stocks_from_portfolios(portfolios)
    tickers = [NAME_TO_TICKER[s] for s in stocks if NAME_TO_TICKER.get(s)]
    print(f"     {len(stocks)}개 종목, {len(tickers)}개 티커")
    all_dates = portfolio_dates(portfolios)
    if not all_dates: print("❌ 데이터 없음"); return
    start = all_dates[0]
    end = (datetime.strptime(all_dates[-1],"%Y-%m-%d")+timedelta(days=1)).strftime("%Y-%m-%d")
    cache = load_price_cache()
    cache = fetch_daily_prices(tickers, start, end, cache)
    daily_returns, holdings_detail = calc_daily_returns(portfolios, cache)
    print(f"     {len(daily_returns)}일, {len(holdings_detail)}건 홀딩스")
    if len(daily_returns) < 5: print("❌ 데이터 부족"); return
    metrics = calc_metrics(daily_returns)
    dates_list = [r[0] for r in daily_returns]; rets_list = [r[1] for r in daily_returns]
    cum = 1.0; cum_list = []
    for r in rets_list: cum *= (1+r); cum_list.append(cum)
    cf = lambda x: f"{x*100:.2f}%"
    date_table = list(zip(dates_list, [cf(r) for r in rets_list], [cf(c) for c in cum_list]))

    # CSV 저장
    csv_path = os.path.join(OUTPUT_DIR, "paper_tracker_daily.csv")
    with open(csv_path,"w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","daily_return","cumulative_return"])
        for d,r,c in zip(dates_list, rets_list, cum_list): w.writerow([d,f"{r:.6f}",f"{c:.6f}"])
    print(f"  💾 {csv_path}")
    metrics_path = os.path.join(OUTPUT_DIR, "paper_tracker_metrics.json")
    with open(metrics_path,"w") as f: json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  💾 {metrics_path}")
    h_csv = os.path.join(OUTPUT_DIR, "paper_tracker_holdings.csv")
    with open(h_csv,"w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","stock","ticker","weight_pct","stock_return_pct","contrib_pct","price_prev","price_curr","reason"])
        for h in holdings_detail: w.writerow([h["date"],h["stock"],h["ticker"],h["weight_pct"],h["stock_return_pct"],h["contrib_pct"],h["price_prev"],h["price_curr"],h["reason"]])
    print(f"  💾 {h_csv}")
    mkt_csv = os.path.join(OUTPUT_DIR, "paper_tracker_market.csv")
    dtp = {p.get("date"): p for p in portfolios if p.get("date")}
    with open(mkt_csv,"w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","regime","cash_ratio","market_summary"])
        seen = set()
        for d,_ in daily_returns:
            p = dtp.get(d)
            if p and d not in seen:
                seen.add(d)
                w.writerow([d, p.get("regime",""), p.get("cash_ratio","0%"), p.get("cash_reason","")[:150]])
    print(f"  💾 {mkt_csv}")
    print(f"\n  📊 누적: {metrics['누적수익률(전체)']} | MDD: {metrics['MDD']} | Sharpe: {metrics['Sharpe_Ratio']}")
if __name__ == "__main__":
    main()
