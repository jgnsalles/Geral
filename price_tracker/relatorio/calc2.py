"""8 estrategias em qualquer universo (S&P 500 PIT ou medias/pequenas). Pre-registro de 2026-11-15. Saidas: relatorio/dados2_<base>.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path.insert(0, str(P)); sys.path.insert(0, str(P / 'backtest')); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import validation_portfolios as vp  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted, DUAL  # noqa: E402
from backtest import stats, D  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402
from validation_factors import factors  # noqa: E402
import calc  # noqa: E402

NAMES = dict(calc.NAMES, n2t20='Excepcionais completadas até 20', n2dca='Excepcionais sem nunca vender')
OOL = bm.OOL


def cap_w(g, mx=.10):
    return top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), mx)


def dd_firm(x):
    return x.assign(firm=x.ticker.map(lambda t: DUAL.get(t, t))).sort_values('mcap', ascending=False).drop_duplicates(['date', 'firm'])


def weights(c):
    """c: date, ticker, cat, excluded, util, fin, roic, growth, pe, ret, mcap."""
    W = {}
    q = c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna()]
    el = dd_firm(q[q.pe >= 4])
    W['top20'] = {d: cap_w(g.sort_values(['ret', 'roic'], ascending=False).head(20)) for d, g in el.groupby('date')}
    ool = dd_firm(c[(c['cat'] == OOL) & ~c.excluded])
    W['hroic'] = {d: pd.Series(1 / len(g), index=g.ticker) for d, g in ool[ool.roic > .30].groupby('date')}
    W['hgrowth'] = {d: pd.Series(1 / len(g), index=g.ticker) for d, g in ool[ool.growth > .30].groupby('date')}
    y = c[~c.fin & ~c.util & ~c.excluded & c.pe.notna() & (c.pe > 0) & c.roic.notna() & c.growth.notna() & c.mcap.notna()].copy()
    y['score'] = y.groupby('date').roic.rank(ascending=False) + y.groupby('date').growth.rank(ascending=False) + y.groupby('date').pe.rank()
    y = y.assign(firm=y.ticker.map(lambda t: DUAL.get(t, t))).sort_values('score').drop_duplicates(['date', 'firm'])
    W['magicg'] = {d: cap_w(g.head(20)) for d, g in y.groupby('date')}
    qd = dd_firm(q)
    W['n1'] = {d: (lambda s: s / s.sum())(pd.Series(np.sqrt(g.mcap.values), index=g.ticker)) for d, g in qd.groupby('date')}
    ex = qd[(qd.roic > .30) & (qd.growth > .30)]
    W['n2'] = {d: (lambda s: s / s.sum())(pd.Series(np.sqrt(g.mcap.values), index=g.ticker)) for d, g in ex.groupby('date')}
    qd = qd.assign(score=np.minimum(qd.roic / .30, qd.growth / .30))
    W['n2t20'] = {d: cap_w(g.sort_values(['score', 'roic'], ascending=False).head(20)) for d, g in qd.groupby('date')}
    W['_n2names'] = {d: list(g.ticker) for d, g in ex.groupby('date')}
    return W


def dca(names, adj, dates):
    """Aporte de 1 por trimestre dividido igualmente entre `names[d]`; nunca vende. Devolve (nav ponderado no tempo, valor, aportes, compras/ano)."""
    sh, units, flows, vals, navs, buys, seen = {}, 0.0, [], [], [], 0, set()
    idx = adj.loc[dates[0]:dates[-1]].index
    px = adj.loc[idx].ffill()
    contrib = {d: names.get(d, []) for d in dates[:-1]}
    nav_p, val_p = [], []
    for t in idx:
        v = sum(n * px.at[t, k] for k, n in sh.items() if np.isfinite(px.at[t, k]))
        price = v / units if units > 0 else 1.0
        if t in contrib and contrib[t]:
            ok = [k for k in contrib[t] if k in px and np.isfinite(px.at[t, k])]
            if ok:
                for k in ok:
                    sh[k] = sh.get(k, 0.0) + (1.0 / len(ok)) / px.at[t, k]
                    if k not in seen: buys += 1; seen.add(k)
                units += 1.0 / price; flows.append((t, 1.0)); v += 1.0
        nav_p.append(v / units if units > 0 else 1.0); val_p.append(v)
    nav = pd.Series(nav_p, index=idx); val = pd.Series(val_p, index=idx)
    yrs = (idx[-1] - idx[0]).days / 365.25
    return nav[nav.index >= flows[0][0]] if flows else nav, val, flows, buys / yrs


def irr(flows, final_value, end):
    cf = [(t, -a) for t, a in flows] + [(end, final_value)]
    t0 = cf[0][0]
    f = lambda r: sum(a / (1 + r) ** ((t - t0).days / 365.25) for t, a in cf)
    lo, hi = -0.9, 3.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0: lo = mid
        else: hi = mid
    return mid


def run(c, adj, dates, ref, rf, nm, desc_extra=''):
    W = weights(c); out = {'names': NAMES, 'strat': {}}
    navs = {}
    for k in ['top20', 'hroic', 'hgrowth', 'magicg', 'n1', 'n2', 'n2t20']:
        nav = run_weighted(W[k], adj, dates); navs[k] = nav
        mt = calc.metrics(nav, ref, rf); mt['cagr_tax'] = stats(tax_weighted(W[k], adj, dates))['CAGR']; mt.update(calc.turnover(W[k]))
        cb = calc.contrib(W[k], adj, dates, nav)
        last = max(W[k]); wl = W[k][last].sort_values(ascending=False)
        mt.update(top_contrib=[[t, nm(t), float(v)] for t, v in cb.head(8).items()], top5_share=float(cb.head(5).sum() / cb.sum()) if cb.sum() else None,
                  today=[[t, nm(t), float(w)] for t, w in wl.items()], today_date=str(pd.Timestamp(last).date()))
        out['strat'][k] = mt; print(k, round(mt['cagr'], 4), flush=True)
    # nunca vender
    nav, val, flows, bpy = dca(W['_n2names'], adj, dates); navs['n2dca'] = nav
    mt = calc.metrics(nav, ref, rf); mt.update(cagr_tax=None, trades=bpy, turnover=0.0, hold_mean=None, hold_median=None, one_q=0.0,
                                               n_mean=float(np.mean([(len([1 for k_ in val.index if False]) or 0)]) ), eff_n=None, top_w=None, top5_w=None)
    end = val.index[-1]; V = val.iloc[-1]; cost = sum(a for _, a in flows)
    mt['irr'] = irr(flows, V, end); mt['irr_tax'] = irr(flows, V - .15 * max(V - cost, 0), end); mt['multiple'] = V / cost
    out['strat']['n2dca'] = mt
    # aportes iguais no S&P/IWM (ref) e na Top 20 sem vender
    def dca_ref(series):
        units = 0.0; s = series.reindex(val.index).ffill()
        for t, a in flows: units += a / s.loc[t]
        Vr = units * s.iloc[-1]; return irr(flows, Vr, end), irr(flows, Vr - .15 * max(Vr - cost, 0), end), Vr / cost
    t20n = {d: list(w.index) for d, w in W['top20'].items()}
    _, v20, f20, _ = dca(t20n, adj, dates); V20 = v20.iloc[-1]
    out['dca'] = {'ref': dca_ref(ref), 'top20': (irr(f20, V20, end), irr(f20, V20 - .15 * max(V20 - cost, 0), end), V20 / cost),
                  'n2': (mt['irr'], mt['irr_tax'], mt['multiple']), 'n_aportes': len(flows)}
    M = pd.DataFrame({NAMES[k]: v.resample('ME').last() for k, v in navs.items()})
    out['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(x) else round(float(x), 5) for x in M[k] / M[k].dropna().iloc[0]] for k in M}}
    out['n_names_today'] = {k: len(W[k][max(W[k])]) for k in W if not k.startswith('_')}
    out['n2_count'] = float(np.mean([len(v) for v in W['_n2names'].values()]))
    return out, navs


def sp500():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']; c = bm.classify_new(f)
    sec, _ = bm.sector_maps(); c['util'] = c.ticker.map(sec) == 'Utilities'
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    need = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15)].copy(); need['mcap'] = top_n.mcap_us(need, need)
    c = c.merge(need[['date', 'ticker', 'mcap']], on=['date', 'ticker'], how='left')
    mf = pd.read_csv(D / 'magic_features.csv', parse_dates=['date'])[['date', 'ticker', 'mcap']].rename(columns={'mcap': 'mcap_m'})
    c = c.merge(mf, on=['date', 'ticker'], how='left'); c['mcap'] = c.mcap.fillna(c.mcap_m)
    bnav, _, _, _ = bm.load_benchmarks()
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    nm = lambda t: str(u.name.get(t, u.name.get(DUAL.get(t, t), t)))
    out, navs = run(c, adj, dates, bnav['S&P 500'], factors()['RF'], nm)
    out['refname'] = 'S&P 500'; out['ref_cagr'] = stats(bnav['S&P 500'])['CAGR']
    (ROOT / 'dados2_sp.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else float(o)))


def midsmall():
    import backtest_ms as ms
    c, adj, dates, u = pd.read_pickle(P / 'mundo' / 'cache' / 'backtest_ms.pkl')
    mc = c[['date', 'ticker', 'mcap', 'cyc', 'app']].copy()
    feat = c.drop(columns=['g', 'fair_pe', 'ret_fair', 'ret_const', 'ret', 'code', 'category', 'order', 'cat', 'pe', 'mcap'])
    n = vp.classify(feat.assign(zroic=0.0), 'sketch', 'B')  # classes novas: sem zROIC
    n = n.merge(mc, on=['date', 'ticker'], suffixes=('', '_m'))
    sic = u.drop_duplicates('ticker').set_index('ticker').sic
    n['util'] = pd.to_numeric(n.ticker.map(sic), errors='coerce').between(4900, 4999)
    n['excluded'] = n.cyc | n.app; n['pe'] = n.price / n.eps.where(n.eps > 0)
    d0 = sorted(n.date.unique()); dates = [pd.Timestamp(d) for d in d0]
    import yfinance as yf
    rf = factors()['RF']
    iwm = adj['IWM'].loc[dates[0]:dates[-1]].dropna(); iwm = iwm / iwm.iloc[0]
    nmap = u.drop_duplicates('ticker').set_index('ticker').name
    out, navs = run(n, adj, dates, iwm, rf, lambda t: str(nmap.get(t, t)).title())
    out['refname'] = 'Russell 2000 (IWM)'; out['ref_cagr'] = stats(iwm)['CAGR']
    for t, lab in (('IWM', 'Russell 2000 (IWM)'), ('IJR', 'S&P SmallCap 600 (IJR)'), ('IJH', 'S&P MidCap 400 (IJH)'), ('SPY', 'S&P 500 (SPY)')):
        s = adj[t].loc[dates[0]:dates[-1]].dropna(); s = s / s.iloc[0]
        out.setdefault('bench', {})[lab] = dict(cagr=stats(s)['CAGR'], maxdd=stats(s)['MaxDD'], vol=stats(s)['Vol'], w3=bm.windows(s, iwm, 3)[0], w5=bm.windows(s, iwm, 5)[0], w10=bm.windows(s, iwm, 10)[0])
        out['nav']['series'][lab] = [round(float(x), 5) for x in (s.resample('ME').last() / s.resample('ME').last().iloc[0]).reindex(pd.to_datetime(out['nav']['dates'])).values]
    uni = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in n.groupby('date')}, adj, dates)
    out['bench']['Universo médias e pequenas (peso igual)'] = dict(cagr=stats(uni)['CAGR'], maxdd=stats(uni)['MaxDD'], vol=stats(uni)['Vol'], w3=bm.windows(uni, iwm, 3)[0], w5=bm.windows(uni, iwm, 5)[0], w10=bm.windows(uni, iwm, 10)[0])
    out['universe_n'] = float(n.groupby('date').size().median()); out['period'] = [str(dates[0].date()), str(dates[-1].date())]
    (ROOT / 'dados2_ms.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else float(o)))


if __name__ == '__main__':
    (sp500 if sys.argv[1] == 'sp' else midsmall)()
