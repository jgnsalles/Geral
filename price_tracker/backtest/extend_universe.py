"""Fase 2: amplia o universo com todas as empresas que passaram pelo S&P 500 desde 2012 (composicao historica publica).
Para cada ticker fora do universo atual: CIK e setor (SIC) na SEC, balancos (companyfacts) e precos no Yahoo quando existirem.
Saidas: backtest/data/universe_pit.csv, backtest/data/pit/<ticker>.json.gz (novos), backtest/data/prices_pit_<campo>.csv.gz
Uso: python3 backtest/extend_universe.py"""
import sys, time, json, gzip, pathlib, re
import pandas as pd, requests, yfinance as yf
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from fetch_pit import compact  # noqa: E402

D = ROOT / 'data'
UA = {'User-Agent': 'PriceTracker-Research/1.0'}


def cik_for(tk):
    r = requests.get('https://efts.sec.gov/LATEST/search-index', params={'keysTyped': tk}, headers=UA, timeout=30)
    for h in r.json().get('hits', {}).get('hits', []):
        ent = h['_source'].get('entity', '')
        m = re.search(r'\(([^)]*)\)\s*$', ent)
        if m and tk.upper() in [x.strip().upper() for x in m.group(1).split(',')]:
            return int(h['_id']), ent
    return None, None


def main():
    h = pd.read_csv(D / 'pit_membership/sp500_hist.csv', parse_dates=['date'])
    h = h[h.date >= '2011-12-01']
    allt = sorted({t for l in h.tickers.str.split(',') for t in l})
    u = pd.read_csv(D / 'universe.csv')
    have = set(u.ticker)
    norm = lambda t: t.replace('.', '-')
    todo = [t for t in allt if norm(t) not in have]
    print('tickers a tentar:', len(todo), flush=True)
    rows = []
    for i, t in enumerate(todo):
        yt = norm(t)
        r = {'ticker': yt, 'hist_ticker': t, 'cik': None, 'sec_name': None, 'sic': None, 'fin': False, 'sec_ok': False}
        try:
            cik, ent = cik_for(t); time.sleep(0.12)
            if cik:
                sub = requests.get(f'https://data.sec.gov/submissions/CIK{cik:010d}.json', headers=UA, timeout=60).json(); time.sleep(0.12)
                sic = int(sub.get('sic') or 0)
                r.update(cik=cik, sec_name=sub.get('name'), sic=sic, fin=(6000 <= sic <= 6499) or (6700 <= sic <= 6799 and sic != 6798))
                f = D / 'pit' / f'{yt}.json.gz'
                if not f.exists():
                    resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json', headers=UA, timeout=90); time.sleep(0.12)
                    if resp.status_code == 200:
                        with gzip.open(f, 'wt') as g: json.dump(compact(resp.json()['facts']), g)
                r['sec_ok'] = f.exists()
        except Exception as e:
            print(t, 'erro SEC', repr(e)[:80])
        rows.append(r)
        if i % 40 == 0: print(i, t, flush=True)
    x = pd.DataFrame(rows)
    # precos (Yahoo so tem quem ainda negocia)
    tks = x.ticker.tolist()
    frames = [yf.download(tks[i:i + 100], start='2005-01-01', end='2026-11-08', auto_adjust=False, actions=True, progress=False, threads=True)
              for i in range(0, len(tks), 100)]
    df = pd.concat(frames, axis=1)
    for field in ('Close', 'Adj Close', 'Dividends', 'Stock Splits'):
        p = df[field]; p = p.loc[:, ~p.columns.duplicated()]
        p.to_csv(D / f"prices_pit_{field.replace(' ', '_').lower()}.csv.gz")
    first = df['Close'].apply(lambda s: s.first_valid_index())
    last = df['Close'].apply(lambda s: s.last_valid_index())
    x['price_from'] = x.ticker.map(first); x['price_to'] = x.ticker.map(last)
    x.to_csv(D / 'universe_pit_extra.csv', index=False)
    print('com SEC:', int(x.sec_ok.sum()), '| com preco:', int(x.price_from.notna().sum()), '| com os dois:', int((x.sec_ok & x.price_from.notna()).sum()))


if __name__ == '__main__':
    main()
