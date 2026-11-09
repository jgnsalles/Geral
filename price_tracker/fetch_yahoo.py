"""Coleta dados do Yahoo (yfinance) e congela um snapshot bruto por ticker em data/raw/yahoo/<data>/.
Uso: python3 fetch_yahoo.py data/wise_snapshot.csv [YYYY-MM-DD]"""
import sys, json, time, datetime as dt, math, pathlib
import pandas as pd, yfinance as yf

INC = ['Diluted EPS', 'Basic EPS', 'EBIT', 'Operating Income', 'Pretax Income', 'Tax Provision',
       'Tax Rate For Calcs', 'Net Income', 'Total Revenue', 'Diluted Average Shares']
BS = ['Invested Capital', 'Total Debt', 'Stockholders Equity', 'Total Equity Gross Minority Interest',
      'Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Total Assets',
      'Current Liabilities', 'Goodwill And Other Intangible Assets', 'Ordinary Shares Number']
INFO = ['currentPrice', 'regularMarketPrice', 'currency', 'financialCurrency', 'trailingEps', 'forwardEps',
        'dividendYield', 'trailingAnnualDividendYield', 'lastFiscalYearEnd', 'nextFiscalYearEnd',
        'mostRecentQuarter', 'sector', 'industry', 'quoteType', 'trailingPE', 'forwardPE']

def clean(v):
    if v is None: return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return v

def frame(df, keys):
    if df is None or df.empty: return {}
    out = {}
    for k in keys:
        if k in df.index:
            out[k] = {str(c.date()): clean(v) for c, v in df.loc[k].items()}
    return out

def fetch(tk):
    t = yf.Ticker(tk)
    d = {'ticker': tk}
    info = t.info or {}
    d['info'] = {k: clean(info.get(k)) for k in INFO}
    ee = t.earnings_estimate
    d['earnings_estimate'] = {} if ee is None else {p: {c: clean(v) for c, v in row.items()} for p, row in ee.iterrows()}
    d['income'] = frame(t.income_stmt, INC)
    d['balance'] = frame(t.balance_sheet, BS)
    div = t.dividends
    d['dividends_12m'] = None
    if div is not None and len(div):
        cut = div.index.max() - pd.Timedelta(days=365)
        d['dividends_by_year'] = {str(y): float(v) for y, v in div.groupby(div.index.year).sum().items()}
    return d

def main(src, day=None):
    day = day or dt.date.today().isoformat()
    out = pathlib.Path('data/raw/yahoo') / day
    out.mkdir(parents=True, exist_ok=True)
    tickers = pd.read_csv(src).ticker.tolist()
    for i, tk in enumerate(tickers):
        f = out / f'{tk}.json'
        if f.exists(): continue
        for attempt in range(3):
            try:
                f.write_text(json.dumps(fetch(tk), indent=1, default=str))
                break
            except Exception as e:
                print(tk, 'erro', attempt, repr(e)[:120]); time.sleep(5 * (attempt + 1))
        time.sleep(0.4)
        if i % 20 == 0: print(i, tk, flush=True)
    print('ok', len(list(out.glob('*.json'))))

if __name__ == '__main__':
    main(*sys.argv[1:])
