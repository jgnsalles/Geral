"""Fase 2 (nucleo): metricas point-in-time com o ROIC oficial para (a) membros do S&P 500 em cada data e (b) universo atual.
Saida: backtest/data/val_features.csv (uma linha por acao x data, com flags pit_member e cur_universe)
Uso: python3 backtest/validation_core.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import load_pit, features, rebalance_dates, D  # noqa: E402
from pit_universe import membership, at  # noqa: E402


def load_prices():
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    out = {}
    for n in ('close', 'adj_close', 'dividends', 'stock_splits'):
        a, b = read(n), read(f'pit_{n}')
        out[n] = a.join(b[[c for c in b.columns if c not in a.columns]], how='outer').sort_index()
    out['dividends'] = out['dividends'].fillna(0); out['stock_splits'] = out['stock_splits'].fillna(0)
    return out


def universe_table():
    u = pd.read_csv(D / 'universe.csv')[['ticker', 'fin']]
    x = pd.read_csv(D / 'universe_pit_extra.csv')
    x = x[x.sec_ok.astype(bool) & x.price_from.notna()][['ticker', 'fin']]
    t = pd.concat([u.assign(cur=True), x.assign(cur=False)]).drop_duplicates('ticker')
    t['fin'] = t.fin.astype(bool)
    return t


def main():
    px = load_prices()
    t = universe_table()
    have = set(t.ticker)
    mem, miss, miss_list = membership(have)
    dates = [d for d in rebalance_dates(px['close']) if d >= pd.Timestamp('2011-06-30')]
    pits = {}
    rows = []
    for d in dates:
        members = set(at(mem, d))
        todo = t[t.ticker.isin(members) | t.cur]
        for r in todo.itertuples():
            if r.ticker not in px['close'].columns: continue
            p = px['close'].at[d, r.ticker]
            if not np.isfinite(p) or p <= 0: continue
            if r.ticker not in pits: pits[r.ticker] = load_pit(r.ticker)
            pit = pits[r.ticker]
            if pit is None: continue
            sp = px['stock_splits'][r.ticker]; sp = sp[sp > 0]
            f = features(pit, d, r.fin, sp)
            if f is None: continue
            dv = px['dividends'][r.ticker]
            dy = dv[(dv.index > d - pd.Timedelta(days=730)) & (dv.index <= d)].sum() / 2 / p
            rows.append(dict(date=d, ticker=r.ticker, fin=r.fin, price=p, dy=dy, pit_member=r.ticker in members, cur_universe=bool(r.cur), **f))
        n = sum(1 for x in rows if x['date'] == d)
        print(d.date(), 'linhas', n, '| membros sem dados', miss[max(k for k in miss if k <= d)], flush=True)
    pd.DataFrame(rows).to_csv(D / 'val_features.csv', index=False)


if __name__ == '__main__':
    main()
