"""Backtest das 8 seleções do Painel com as regras de 2026-11-22 (seguros multilinha e distribuidoras de saúde não são cíclicos;
ROIC: marginal sozinho só sem dado de ativo/passivo). S&P 500 point-in-time, trimestral, crescimento HISTÓRICO (a regra testada).
Compara com a versão anterior das regras. Saída: relatorio/dados_8.json. Uso: python3 relatorio/backtest_8.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
import calc, calc2  # noqa: E402
from pesos import run_weighted, DUAL  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402
from backtest import stats, D  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

OOL, GCGR = bm.OOL, bm.GCGR
NAMES = {'top20c': 'Top 20 (máx. 8 por setor)', 'top20': 'Top 20 (sem limite)', 'ool': 'Opportunity of Lifetime', 'n2': 'Excepcionais',
         'n2t20': 'Especiais', 'hroic': 'High ROIC', 'gcgr': 'Good Companies, Great Returns', 'magicg': 'JG+G', 'hgrowth': 'High Growth'}
KEYS = list(NAMES)


def build(roic_file, cyc):
    f, dates = bm.base_data(roic=roic_file); adj = bm.load_prices()['adj_close']; c = bm.classify_new(f, cyc=cyc)
    sec, _ = bm.sector_maps(); c['util'] = c.ticker.map(sec) == 'Utilities'
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    need = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15)].copy(); need['mcap'] = top_n.mcap_us(need, need)
    c = c.merge(need[['date', 'ticker', 'mcap']], on=['date', 'ticker'], how='left')
    mf = pd.read_csv(D / 'magic_features.csv', parse_dates=['date'])[['date', 'ticker', 'mcap']].rename(columns={'mcap': 'mcap_m'})
    c = c.merge(mf, on=['date', 'ticker'], how='left'); c['in_mf'] = c.mcap_m.notna(); c['mcap'] = c.mcap.fillna(c.mcap_m)
    return c, adj, dates


def weights(c):
    W = calc2.weights(c)
    q = c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.pe >= 4)]
    el = calc2.dd_firm(q)
    out = {}
    for d, g in el.groupby('date'):
        g = g.sort_values(['ret', 'roic'], ascending=False); keep, cnt = [], {}
        for r in g.itertuples():
            s = r.sector if isinstance(r.sector, str) else '?'
            if cnt.get(s, 0) < 8: keep.append(r.Index); cnt[s] = cnt.get(s, 0) + 1
            if len(keep) == 20: break
        out[d] = calc2.cap_w(g.loc[keep])
    W['top20c'] = out
    for k, cat in (('ool', OOL), ('gcgr', GCGR)):
        x = calc2.dd_firm(c[(c['cat'] == cat) & ~c.excluded])
        W[k] = {d: pd.Series(1 / len(g), index=g.ticker) for d, g in x.groupby('date')}
    return W


def decomp(W, c, adj, dates, h=12):
    """retorno anual das posições em 3 anos: EPS, re-rating e dividendos (log, ponderado pelo peso)"""
    D_ = pd.DatetimeIndex(dates); iq = {d: i for i, d in enumerate(D_)}
    A = adj.reindex(D_, method='ffill'); key = c.set_index(['date', 'ticker'])[['eps', 'pe']]
    rows = []
    for d, w in W.items():
        i = iq.get(pd.Timestamp(d))
        if i is None or i + h >= len(D_): continue
        d1 = D_[i + h]
        for t, x in w.items():
            if (d, t) not in key.index or (d1, t) not in key.index or t not in A: continue
            e0, p0 = key.loc[(d, t)]; e1, p1 = key.loc[(d1, t)]
            a0, a1 = A.at[d, t], A.at[d1, t]
            if not (e0 > 0 and e1 > 0 and p0 > 0 and p1 > 0 and a0 > 0 and np.isfinite(a1)): continue
            lt = np.log(a1 / a0); le = np.log(e1 / e0); lp = np.log(p1 / p0)
            rows.append((d, x, le, lp, lt - le - lp, lt))
    if not rows: return None
    z = pd.DataFrame(rows, columns=['d', 'w', 'le', 'lp', 'ld', 'lt'])
    g = z.groupby('d').apply(lambda y: pd.Series({k: np.average(y[k], weights=y.w) for k in ('le', 'lp', 'ld', 'lt')}), include_groups=False).mean()
    return {k: float(np.expm1(g[k] * 4 / h)) for k in ('le', 'lp', 'ld', 'lt')}


def run_all(c, adj, dates, spy, rf, deep=True):
    W = weights(c); res, navs = {}, {}
    sec = c.drop_duplicates('ticker').set_index('ticker').sector
    for k in KEYS:
        nav = run_weighted(W[k], adj, dates); navs[k] = nav
        m = calc.metrics(nav, spy, rf); tv = calc.turnover(W[k])
        r = dict(cagr=m['cagr'], vol=m['vol'], maxdd=m['maxdd'], sharpe=m['sharpe'], w3=m['w3'], w5=m['w5'], w10=m['w10'], w3min=m['w3min'],
                 behind=m['behind_months'], beat_m=m['beat_m'], trades=tv['trades'], n_mean=float(np.mean([len(w) for w in W[k].values()])),
                 top_w=float(np.mean([w.max() for w in W[k].values() if len(w)])))
        if deep:
            r['cagr_tax'] = stats(tax_weighted(W[k], adj, dates))['CAGR']
            cb = calc.contrib(W[k], adj, dates, nav)
            r['best5'] = [[t, float(v)] for t, v in cb.head(5).items()]; r['worst5'] = [[t, float(v)] for t, v in cb.tail(5).items()]
            bysec = cb.groupby(cb.index.map(lambda t: sec.get(t, '?'))).sum().sort_values(ascending=False)
            r['sector'] = [[s, float(v), float(v / cb.sum())] for s, v in bysec.items()]
            r['decomp'] = decomp(W[k], c, adj, dates)
            r['_cb'] = cb
        res[k] = r
    return res, navs, W


def main():
    rf = factors()['RF']
    cyc_new = cyclical_industries()
    cyc_old = set(cyc_new) | {'Multi-line Insurance', 'Health Care Distributors'}
    # antes: ROIC e cíclicos antigos
    c0, adj, dates = build('roic3_antes_20261122.csv', cyc_old)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    old, _, _ = run_all(c0, adj, dates, spy, rf, deep=False)
    print('antes', {k: round(v['cagr'], 4) for k, v in old.items()}, flush=True)
    c, adj, dates = build(bm.ROIC_FILE, cyc_new)
    new, navs, W = run_all(c, adj, dates, spy, rf)
    print('depois', {k: round(v['cagr'], 4) for k, v in new.items()}, flush=True)
    # robustez de concentração: tirar a(s) ação(ões) do universo inteiro
    rob, cache = {}, {}
    for k in KEYS:
        cb = new[k].pop('_cb')
        sets = {'sem a maior': list(cb.index[:1]), 'sem as 3 maiores': list(cb.index[:3]), 'sem a pior': list(cb.index[-1:]),
                'sem as 3 piores': list(cb.index[-3:]), 'sem NVIDIA': ['NVDA']}
        rob[k] = {}
        for lab, ts in sets.items():
            fk = frozenset(ts)
            if fk not in cache: cache[fk] = weights(c[~c.ticker.isin(ts)])
            Wx = cache[fk]
            rob[k][lab] = [float(stats(run_weighted(Wx[k], adj, dates))['CAGR']), ts]
        print(k, {a: round(b[0], 4) for a, b in rob[k].items()}, flush=True)
    for k in KEYS: new[k].pop('_cb', None)
    # correlação, sobreposição e quem foi a melhor em janelas de 3 anos
    M = pd.DataFrame({NAMES[k]: navs[k].resample('ME').last() for k in KEYS})
    corr = M.pct_change().corr().round(3)
    ov = {}
    for a in KEYS:
        for b in KEYS:
            if a >= b: continue
            vals = [len(set(W[a][d].index) & set(W[b][d].index)) / max(1, len(set(W[a][d].index) | set(W[b][d].index))) for d in W[a] if d in W[b]]
            ov[f'{NAMES[a]} × {NAMES[b]}'] = float(np.mean(vals)) if vals else None
    r3 = (M / M.shift(36)) ** (1 / 3)
    best = r3.dropna().idxmax(axis=1).value_counts(normalize=True).round(3).to_dict()
    sp = spy.resample('ME').last()
    bench = {'S&P 500': calc.metrics(spy, spy, rf)['cagr'], 'S&P 500 equal weight': stats((lambda s: s / s.iloc[0])(adj['RSP'].loc[dates[0]:dates[-1]].dropna()))['CAGR']}
    navs_b, nb, _, _ = bm.load_benchmarks()
    bench9 = {k: float(stats(v)['CAGR']) for k, v in navs_b.items()}
    win9 = {k: [bm.windows(v, navs_b['S&P 500'], y)[0] for y in (3, 5, 10)] for k, v in navs_b.items()}
    nav_out = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(x) else round(float(x), 4) for x in M[k] / M[k].dropna().iloc[0]] for k in M}}
    nav_out['series']['S&P 500'] = [round(float(x), 4) for x in (sp / sp.iloc[0]).reindex(M.index).ffill()]
    out = dict(names=NAMES, new=new, old=old, rob=rob, corr={'labels': list(corr.columns), 'm': corr.values.tolist()}, overlap=ov, best3=best,
               bench=bench, bench9=bench9, win9=win9, nav=nav_out, periodo=[str(dates[0].date()), str(dates[-1].date())])
    (ROOT / 'dados_8.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    print('ok')


if __name__ == '__main__':
    main()
