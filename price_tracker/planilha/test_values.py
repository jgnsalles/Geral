"""Valores de teste (SEC) no formato dos campos do Wisesheets, para validar as fórmulas da V3 sem o add-in."""
import sys, json, pathlib
import numpy as np, pandas as pd
sys.path[:0] = ['backtest', '.']
from backtest import load_pit, asof, D
from roic3 import load_pit2
import benchmarks as bm
t = pd.Timestamp('2026-11-01'); ANO = 2025
tick = [x for x in json.load(open('planilha/tickers.json')) if (D / 'pit' / f'{x}.json.gz').exists()]
pr = bm.load_prices(); close = pr['close']; divs = pr['dividends'].fillna(0)
u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
out = {}
for tk in tick:
    p = load_pit(tk); p2 = load_pit2(tk); s = {k: asof(v, t)[0] for k, v in {**p, **p2}.items()}
    g = lambda k, y: s[k][y][0] if s.get(k) and y in s[k] else None
    v = {}
    for k in range(-1, 7):
        y = ANO - k
        v[f'opinc{k}'] = g('op_income', y); v[f'pretax{k}'] = g('pretax', y); v[f'tax{k}'] = g('tax', y); v[f'ni{k}'] = g('net_income', y); v[f'eps{k}'] = g('eps_diluted', y)
        ppe = [x for x in (g('ppe', y), g('ppe_og', y)) if x is not None]; v[f'ppe{k}'] = max(ppe) if ppe else None
        v[f'gw{k}'] = g('goodwill', y)
        it = g('intang_tot', y)
        if it is None and (g('intang_fin', y) is not None or g('intang_indef', y) is not None): it = (g('intang_fin', y) or 0) + (g('intang_indef', y) or 0)
        v[f'intang{k}'] = it if it is not None else g('intangibles', y)
        v[f'ltinv{k}'] = g('lt_inv', y); v[f'tca{k}'] = g('assets_cur', y); v[f'cash{k}'] = g('cash', y); v[f'stinv{k}'] = g('st_inv', y); v[f'tcl{k}'] = g('cur_liab', y)
        v[f'std{k}'] = g('debt_cur', y)
        ld = g('ltd_tot', y); v[f'debt{k}'] = (ld + (g('st_borr', y) or 0)) if ld is not None else ((g('lt_debt', y) or 0) + (g('debt_cur', y) or 0))
        ll = g('lease_liab', y)
        if ll is None and (g('lease_liab_cur', y) is not None or g('lease_liab_nc', y) is not None): ll = (g('lease_liab_cur', y) or 0) + (g('lease_liab_nc', y) or 0)
        v[f'lease{k}'] = ll; v[f'eq{k}'] = g('equity', y); v[f'mino{k}'] = g('minority', y); v[f'rou{k}'] = g('rou', y); v[f'eqi{k}'] = g('eq_income', y)
        cx = g('capex', y); v[f'capex{k}'] = -cx if cx is not None else None; v[f'da{k}'] = g('da', y)
        aq = g('acq', y); v[f'acq{k}'] = -aq if aq is not None else None
    if tk not in close: continue
    pz = close[tk].dropna(); price = float(pz.iloc[-1])
    v['preco'] = price; v['nome'] = str(u.name.get(tk, tk)); v['setor'] = {'Financials': 'Financial Services'}.get(u.sector.get(tk), str(u.sector.get(tk))); v['ind'] = str(u.industry.get(tk, ''))
    sh = (v['ni0'] / v['eps0']) if v.get('ni0') and v.get('eps0') else None; v['mcap'] = price * sh if sh and sh > 0 else None
    dv = divs[tk] if tk in divs else pd.Series(dtype=float); v['dy'] = float(dv[dv.index > pz.index[-1] - pd.Timedelta(days=365)].sum() / price) if len(dv) else 0.0
    out[tk] = {a: (None if b is None or (isinstance(b, float) and not np.isfinite(b)) else b) for a, b in v.items()}
json.dump({'tickers': list(out), 'data': out}, open('planilha/teste.json', 'w')); print(len(out))
