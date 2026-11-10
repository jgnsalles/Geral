"""Gera os arquivos do painel interativo: NAV mensal (9 comparativos x 3 ponderacoes) e posicoes trimestrais com pesos e retornos.
Saidas: backtest/dash/navs.csv, backtest/dash/posicoes.csv. Uso: python3 backtest/dash_data.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, shares, DUAL  # noqa: E402
from backtest import D  # noqa: E402

OUT = ROOT / 'dash'; OUT.mkdir(exist_ok=True)
f, dates = bm.base_data()
adj = bm.load_prices()['adj_close']
old = bm.vp.classify(f, 'orig', 'B'); new = bm.classify_new(f); hn = bm.holdings_new(new)
NAME = {'OoL antigo': 'OoL antigo', 'GCGR antigo': 'GCGR antigo', 'OoL novo': 'OoL novo', 'GCGR novo': 'GCGR novo',
        'OoL High ROIC (novo)': 'OoL High ROIC', 'OoL High Growth (novo)': 'OoL High Growth', 'Cyclicals': 'Cyclicals'}
H = {'OoL antigo': (old, old.cat == bm.OOL), 'GCGR antigo': (old, old.cat == bm.GCGR)}
H.update({k: (new, m) for k, m in hn.items()})
sh = shares(pd.concat([c[m][['date', 'ticker', 'eps', 'last_fy', 'price']] for c, m in H.values()]).drop_duplicates(['date', 'ticker']))
sec, ind = bm.sector_maps()
u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
xe = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
nm = lambda t: u.name.get(t) if t in u.index else str(xe.sec_name.get(t, t)).title()
px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
spyq = fwd['SPY']
navs, pos = {}, []
for k, (c, m) in H.items():
    x = c[m].copy()
    x['mcap'] = [p * sh.get((d, t), np.nan) for d, t, p in zip(x.date, x.ticker, x.price)]
    x['mcap'] = x.mcap.where(x.mcap > 0); x['mcap'] = x.mcap.fillna(x.groupby('date').mcap.transform('median'))
    x['firm'] = x.ticker.map(lambda t: DUAL.get(t, t)); x['mcap'] = x.mcap / x.groupby(['date', 'firm']).ticker.transform('size')
    x = x[[t in adj and np.isfinite(adj.at[d, t]) for d, t in zip(x.date, x.ticker)]]
    x['w_ew'] = 1 / x.groupby('date').ticker.transform('size')
    x['w_raiz'] = np.sqrt(x.mcap) / x.groupby('date').mcap.transform(lambda s: np.sqrt(s).sum())
    x['w_mv'] = x.mcap / x.groupby('date').mcap.transform('sum')
    for col, lab in (('w_ew', 'Peso igual'), ('w_raiz', 'Raiz do valor de mercado'), ('w_mv', 'Valor de mercado')):
        navs[f'{NAME[k]}|{lab}'] = run_weighted({d: pd.Series(g[col].values, index=g.ticker) for d, g in x.groupby('date')}, adj, dates)
    x['r'] = [fwd.at[d, t] if d < dates[-1] else np.nan for d, t in zip(x.date, x.ticker)]
    R = x[[f'ry{i}' for i in range(1, 7)]]
    extra = {f'roic_{i}': R[f'ry{i}'].round(4) for i in range(1, 7)}
    extra.update({'ano_fiscal': x.last_fy.astype(int), 'roic_mediana': R.median(axis=1).round(4), 'roic_modelo': x.roic.round(4),
                  'eps': x.eps.round(2), 'cresc_eps': x.growth.round(4), 'g': x.g.round(4),
                  'pl': (x.price / x.eps.where(x.eps > 0)).round(1), 'pe_justo': x.fair_pe.round(1), 'ret_esperado': x.ret.round(4)})
    pos.append(pd.DataFrame({'trimestre': x.date.dt.strftime('%Y-%m-%d'), 'classe': NAME[k], 'ticker': x.ticker, 'empresa': x.ticker.map(nm),
                             'setor': x.ticker.map(sec).fillna(''), 'subsetor': x.ticker.map(ind).fillna(''),
                             'w_ew': x.w_ew.round(6), 'w_raiz': x.w_raiz.round(6), 'w_mv': x.w_mv.round(6),
                             'retorno': x.r.round(6), 'sp500': x.date.map(spyq).round(6), **extra}))
    print(k, flush=True)
for b, lab in (('SPY', 'S&P 500'), ('RSP', 'S&P 500 equal weight')):
    s = adj[b].loc[dates[0]:dates[-1]]; navs[lab] = s / s.iloc[0]
N = pd.DataFrame(navs).ffill()
M = N.resample('ME').last(); M.loc[N.index[0]] = 1.0; M = M.sort_index(); M.index.name = 'mes'
long = M.reset_index().melt(id_vars='mes', var_name='serie', value_name='nav')
long['mes'] = long.mes.dt.strftime('%Y-%m-%d'); long['nav'] = long.nav.round(6)
long.to_csv(OUT / 'navs.csv', index=False)
P = pd.concat(pos); P.to_csv(OUT / 'posicoes.csv', index=False)
print(len(long), len(P), (OUT / 'navs.csv').stat().st_size, (OUT / 'posicoes.csv').stat().st_size)
