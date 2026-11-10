"""Baixa (1) companyfacts da SEC (point-in-time, mesmo formato do backtest dos EUA) e (2) precos do Yahoo das empresas estrangeiras
listadas em bolsa americana (20-F/40-F). Uso: python3 estrangeiras/fetch.py"""
import sys, json, gzip, time, pathlib
import pandas as pd, requests
ROOT = pathlib.Path(__file__).parent; D = ROOT / 'data'
sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT.parent))
from fetch_pit import compact  # noqa: E402
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}

def main():
    u = pd.read_csv(D / 'fpi_info.csv')
    u = u[u.tickers.notna() & ~u.exchanges.fillna('').str.contains('OTC')].copy()
    u['ticker'] = u.tickers.str.split(',').str[0].str.replace('.', '-', regex=False)
    u.to_csv(D / 'universe.csv', index=False)
    (D / 'pit').mkdir(exist_ok=True)
    for i, r in enumerate(u.itertuples()):
        f = D / 'pit' / f'{r.ticker}.json.gz'
        if f.exists(): continue
        for a in range(3):
            try:
                resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(r.cik):010d}.json', headers=UA, timeout=90)
                if resp.status_code == 404: break
                resp.raise_for_status()
                with gzip.open(f, 'wt') as g: json.dump(compact(resp.json()['facts']), g)
                break
            except Exception as e:
                time.sleep(3 * (a + 1))
        time.sleep(0.12)
        if i % 200 == 0: print('sec', i, flush=True)
    import yfinance as yf
    tk = sorted(set(u.ticker)) + ['SPY', 'EFA', 'ACWX', 'EEM', 'VXUS']
    px = yf.download(tk, start='2009-06-01', auto_adjust=False, progress=False, group_by='column', threads=True)
    for col, name in (('Close', 'close'), ('Adj Close', 'adj_close'), ('Volume', 'volume')):
        px[col].to_csv(D / f'prices_{name}.csv.gz')
    act = yf.Tickers(' '.join(tk))
    sp = {}
    for t in tk:
        try:
            s = act.tickers[t].splits
            if len(s): sp[t] = s
        except Exception: pass
    pd.DataFrame(sp).to_csv(D / 'prices_splits.csv.gz')
    print('ok', len(list((D / 'pit').glob('*.gz'))), px['Close'].shape)

if __name__ == '__main__':
    main()
