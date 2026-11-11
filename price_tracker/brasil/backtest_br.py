"""Backtest point-in-time do metodo 2 no Brasil (dados da CVM + precos do Yahoo), em reais.
Ajustes pedidos pelo usuario: WACC 12%; g de 9% (maior crescimento) a 4% (menor); financeiras de 8,5% a 3,5%.
Cortes de classe iguais aos dos EUA. Crescimento pela mediana de 5 anos do lucro dos controladores.
Uso: python3 brasil/backtest_br.py"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest'))
import engine  # noqa: E402
from backtest import run_portfolio, stats  # noqa: E402

D = ROOT / 'data'
WACC, GMAX, GMIN, FIN_SHIFT = 0.12, 0.09, 0.04, 0.005
N_HIST, STALE_DAYS, MIN_ADTV = 5, 550, 2e6
CUTS = {'zg2.93': 2.93, 'zg0.9': 0.9}
START = '2011-01-01'
BENCH = ['BOVA11.SA', 'SMAL11.SA']
EXCL = set()  # anos cujo crescimento (ano y sobre y-1) fica fora da mediana; vazio = regra original


def ratio(a, b):
    return a / b - 1 if pd.notna(a) and pd.notna(b) and b > 0 else np.nan


def split_after(sp, d):
    s = sp[sp.index > d]
    return float(np.prod(s.values)) if len(s) else 1.0


def features(f, t, r, sp):
    """f: fundamentos de uma empresa (todas as versoes). So usa versoes entregues ate t."""
    k = f[f.DT_RECEB <= t]
    if k.empty: return None
    k = k.sort_values(['DT_REFER', 'VERSAO']).groupby('DT_REFER').tail(1)
    k = k.assign(fy=k.DT_REFER.dt.year).drop_duplicates('fy', keep='last').set_index('fy')
    last = k.index.max()
    if (t - k.loc[last, 'DT_REFER']).days > STALE_DAYS: return None
    ni = k.ni
    rates = [ratio(ni.get(y), ni.get(y - 1)) for y in range(last - N_HIST + 1, last + 1) if y not in EXCL]
    ok = [x for x in rates if np.isfinite(x)]
    growth = float(np.median(ok)) if len(ok) >= min((N_HIST + 1) // 2, len(rates)) and ok else np.nan
    zgrowth = engine.cv(rates, growth) if np.isfinite(growth) else np.nan
    roics = []
    for y in range(last - 5, last + 1):
        if y not in k.index: roics.append(np.nan); continue
        x = k.loc[y]
        if r.fin:
            roics.append(x.ni / x.equity if pd.notna(x.ni) and x.equity > 0 else np.nan); continue
        if pd.isna(x.ebit) or pd.isna(x.equity): roics.append(np.nan); continue
        tr = min(max(-x.tax / x.pretax, 0), 0.5) if pd.notna(x.tax) and pd.notna(x.pretax) and x.pretax > 0 else 0.34
        ic = engine.invested_capital(x.equity, x.debt, x.cash, x.get('ppe'), x.get('ac'), x.get('cl'), x.get('debt_cur'))[0]
        roics.append(x.ebit * (1 - tr) / ic if ic > 0 else np.nan)
    roic = engine.roic_metric(roics); zroic = engine.cv(roics, roic)
    x = k.loc[last]
    on, pn = x.eps_on, x.eps_pn if pd.notna(x.eps_pn) else x.eps_on
    tk = r.ticker
    if tk.endswith('11') and pd.notna(r.unit_on): eps = r.unit_on * on + r.unit_pn * pn
    elif tk[-1] in '3': eps = on
    else: eps = pn
    eps = eps / split_after(sp, x.DT_RECEB) if pd.notna(eps) else np.nan
    return dict(growth=growth, zgrowth=zgrowth, roic=roic, zroic=zroic, eps=eps, last_fy=last, n_rates=len(ok))


def rebalance_dates(px):
    out = []
    for q in pd.date_range(START, px.index.max(), freq='QS'):
        prev = px.index[px.index < q]
        if len(prev): out.append(prev[-1])
    return out


def g_rank(x):
    out = pd.Series(np.nan, index=x.index)
    for fin, top, floor in ((False, GMAX, GMIN), (True, GMAX - FIN_SHIFT, GMIN - FIN_SHIFT)):
        m = x.fin == fin
        rr = x.loc[m, 'growth'].dropna().to_numpy()
        if len(rr) < 2: continue
        rk = x.loc[m, 'growth'].apply(lambda v: np.nan if pd.isna(v) else 1 + (rr > v).sum())
        out[m] = top - (rk - 1) * (top - floor) / (len(rr) - 1)
    return out


def classify_all(u, fund, close, vol, divs, splits, dates):
    tv = (close * vol).rolling(63, min_periods=20).median()
    rows = []
    for d in dates:
        for r in u.itertuples():
            f = fund.get(r.Codigo_CVM)
            if f is None or r.yf not in close: continue
            p = close.at[d, r.yf]
            if not np.isfinite(p) or p <= 0 or not (tv.at[d, r.yf] >= MIN_ADTV): continue
            sp = splits[r.yf]; sp = sp[sp > 0]
            ft = features(f, d, r, sp)
            if ft is None: continue
            pe = p / ft['eps'] if ft['eps'] and ft['eps'] > 0 else np.nan
            if pd.notna(pe) and not 1 <= pe <= 300: ft['eps'] = np.nan  # LPA inconsistente com o preco: descarta para valuation
            dv = divs[r.yf]
            dy = dv[(dv.index > d - pd.Timedelta(days=730)) & (dv.index <= d)].sum() / 2 / p
            rows.append(dict(date=d, ticker=r.yf, fin=r.fin, price=p, dy=dy, **ft))
        print(d.date(), sum(1 for x in rows if x['date'] == d), flush=True)
    df = pd.DataFrame(rows)
    out = []
    for d, x in df.groupby('date'):
        x = x.copy()
        x['g'] = g_rank(x)
        x['fair_pe'] = np.where(x.roic > 0, (1 - x.g / x.roic) / (WACC - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        for name, cut in CUTS.items():
            saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
            try:
                c = engine.classify(x)
            finally:
                engine.TH['zGrowth'] = saved
            x[f'cat_{name}'] = np.where(c.code.isna(), None, c.category)
        out.append(x)
    return pd.concat(out, ignore_index=True)


def main():
    u = pd.read_csv(D / 'universe.csv')
    fund = pd.read_csv(D / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB'])
    fund = {c: g for c, g in fund.groupby('CD_CVM')}
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    close, adj, vol = read('close'), read('adj_close'), read('volume')
    divs, splits = read('dividends').fillna(0), read('stock_splits').fillna(0)
    dates = rebalance_dates(close)
    cache = D / 'classes_pit.csv'
    if cache.exists():
        cls = pd.read_csv(cache, parse_dates=['date'])
    else:
        cls = classify_all(u, fund, close, vol, divs, splits, dates)
        cls.to_csv(cache, index=False)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 60].index.min()  # comeca quando ha pelo menos 60 empresas classificadas
    dates = [d for d in dates if d >= start]
    print('inicio:', start.date(), '| trimestres:', len(dates) - 1, '| classificadas por data (mediana):', int(cov[cov.index >= start].median()))
    for name in CUTS:
        c = cls[cls.date >= start]
        navs, rows = {}, []
        groups = {cat: {d: g.ticker.tolist() for d, g in c[c[f'cat_{name}'] == cat].groupby('date')} for cat in c[f'cat_{name}'].dropna().unique()}
        groups['Universo EW'] = {d: g.ticker.tolist() for d, g in c[c[f'cat_{name}'].notna()].groupby('date')}
        for pname, hold in groups.items():
            nav, net, to, n = run_portfolio(hold, adj, dates)
            navs[pname] = nav
            rows.append(dict(Carteira=pname, **stats(nav), **{'CAGR liq.': stats(net)['CAGR']}, Giro=to, **{'N medio': n},
                             **{'Trim. vazios': sum(1 for d in dates[:-1] if not hold.get(d))}))
        for b in BENCH:
            nb = adj[b].loc[dates[0]:dates[-1]].dropna(); nb = nb / nb.iloc[0]
            navs[b] = nb
            rows.append(dict(Carteira=b.replace('.SA', ''), **stats(nb), **{'CAGR liq.': stats(nb)['CAGR']}, Giro=0, **{'N medio': np.nan}, **{'Trim. vazios': 0}))
        pd.DataFrame(navs).to_csv(D / f'nav_{name}.csv')
        st = pd.DataFrame(rows); st.to_csv(D / f'stats_{name}.csv', index=False)
        print('\n==', name); print(st.sort_values('CAGR', ascending=False).to_string(index=False, float_format=lambda v: f'{v:.3f}'))


if __name__ == '__main__':
    main()
