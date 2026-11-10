"""Baixa companyfacts (point-in-time), SIC e precos das empresas americanas listadas fora do universo ja coletado.
Uso: python3 midsmall/fetch.py"""
import sys, json, gzip, time, pathlib, shutil
import pandas as pd, requests
ROOT = pathlib.Path(__file__).parent; D = ROOT / 'data'
sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT.parent))
from fetch_pit import compact  # noqa: E402
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}
E = ROOT.parent / 'estrangeiras' / 'data'; B = ROOT.parent / 'backtest' / 'data'

def get(url):
    for a in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=90)
            if r.status_code == 404: return None
            r.raise_for_status(); return r.json()
        except Exception:
            time.sleep(3 * (a + 1))
    return None

def main():
    t = json.load(open(E / 'tickers.json')); T = pd.DataFrame(t['data'], columns=t['fields'])
    T = T[T.exchange.isin(['Nasdaq', 'NYSE'])]
    fpi = set(pd.read_csv(E / 'fpi_info.csv').cik)
    T = T[~T.cik.isin(fpi)].drop_duplicates('cik').copy(); T['ticker'] = T.ticker.str.replace('.', '-', regex=False)
    from concurrent.futures import ThreadPoolExecutor
    def one(r):
        f = D / 'pit' / f'{r.ticker}.json.gz'
        src = B / 'pit' / f'{r.ticker}.json.gz'
        if not f.exists():
            if src.exists(): shutil.copy(src, f)
            else:
                j = get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(r.cik):010d}.json'); time.sleep(0.6)
                if j:
                    with gzip.open(f, 'wt') as g: json.dump(compact(j['facts']), g)
        s = get(f'https://data.sec.gov/submissions/CIK{int(r.cik):010d}.json'); time.sleep(0.6)
        return dict(ticker=r.ticker, cik=r.cik, name=r.name, sic=(s or {}).get('sic'), sicdesc=(s or {}).get('sicDescription'))
    with ThreadPoolExecutor(5) as ex:
        info = list(ex.map(one, T.itertuples()))
    print('sec ok', flush=True)
    U = pd.DataFrame(info); U.to_csv(D / 'universe.csv', index=False)
    import yfinance as yf
    tk = sorted(set(U.ticker)) + ['SPY', 'IJH', 'IJR', 'IWM', 'MDY']
    parts = {k: [] for k in ('Close', 'Adj Close', 'Volume', 'Stock Splits', 'Dividends')}
    for i in range(0, len(tk), 400):
        px = yf.download(tk[i:i + 400], start='2009-06-01', auto_adjust=False, actions=True, progress=False, threads=True)
        for k in parts:
            if k in px.columns.get_level_values(0): parts[k].append(px[k])
        print('yahoo', i, flush=True)
    for k, n in (('Close', 'close'), ('Adj Close', 'adj_close'), ('Volume', 'volume'), ('Stock Splits', 'splits'), ('Dividends', 'dividends')):
        pd.concat(parts[k], axis=1).to_csv(D / f'prices_{n}.csv.gz')
    print('ok', len(list((D / 'pit').glob('*.gz'))))

if __name__ == '__main__':
    main()
