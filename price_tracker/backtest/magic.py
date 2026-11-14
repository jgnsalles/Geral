"""Formula Magica de Greenblatt no S&P 500 point-in-time (pre-registrado em 2026-11-14). Saida: backtest/magic.md e .png"""
import sys, pathlib
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'etfs'))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import load_pit, asof, stats, D  # noqa: E402
from roic3 import load_pit2  # noqa: E402
from roic3_backtest import top20  # noqa: E402

KEYS = ('op_income', 'ppe', 'assets_cur', 'cur_liab', 'cash', 'debt_cur', 'lt_debt')


def feats(args):
    tk, dates = args
    p = load_pit(tk); p2 = load_pit2(tk); out = []
    if p is None: return out
    for t in dates:
        s = {k: asof(p.get(k, []), t)[0] for k in KEYS}; s.update({k: asof(p2.get(k, []), t)[0] for k in ('st_inv', 'ltd_tot', 'st_borr', 'minority')})
        if not s['op_income']: continue
        y = max(s['op_income']); g = lambda k: s[k][y][0] if s.get(k) and y in s[k] else None
        ebit, ac, cl, ppe = g('op_income'), g('assets_cur'), g('cur_liab'), g('ppe')
        cash = (g('cash') or 0) + (g('st_inv') or 0)
        debt = (g('ltd_tot') + (g('st_borr') or 0)) if g('ltd_tot') is not None else (g('lt_debt') or 0) + (g('debt_cur') or 0)
        cap = ((ac - cash) - (cl - (g('debt_cur') or 0)) + ppe) if None not in (ac, cl, ppe) else None
        out.append(dict(date=t, ticker=tk, ebit=ebit, cap=cap, net_debt=debt + (g('minority') or 0) - cash))
    return out


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    c = bm.classify_new(f)
    sec, _ = bm.sector_maps(); c['sector'] = c.ticker.map(sec)
    base = c[~c.fin & (c.sector != 'Utilities')][['date', 'ticker', 'price', 'eps', 'last_fy', 'sector']].copy()
    base['mcap'] = top_n.mcap_us(base, base)
    jobs = [(t, sorted(pd.Timestamp(d) for d in g.date.unique())) for t, g in base.groupby('ticker')]
    with Pool(4) as pool: res = pool.map(feats, jobs, chunksize=4)
    F = base.merge(pd.DataFrame([r for rr in res for r in rr]), on=['date', 'ticker'], how='inner')
    F['ev'] = F.mcap + F.net_debt
    F = F[(F.ev > 0) & (F.cap > 0) & F.ebit.notna()]
    F['roc'] = F.ebit / F.cap; F['ey'] = F.ebit / F.ev
    F['score'] = F.groupby('date').roc.rank(ascending=False) + F.groupby('date').ey.rank(ascending=False)
    F.to_csv(D / 'magic_features.csv', index=False)
    def W(n, wt='eq'):
        out = {}
        for d, g in F.groupby('date'):
            ch = g.sort_values('score').head(n)
            out[d] = pd.Series(1.0, index=ch.ticker) if wt == 'eq' else top_n.cap(pd.Series(np.sqrt(ch.mcap.values), index=ch.ticker), .10)
        return out
    navs, n, _, _ = bm.load_benchmarks()
    navs['Top 20 da estratégia (OoL, raiz)'] = top20(c, adj, dates); n['Top 20 da estratégia (OoL, raiz)'] = 20
    for lab, w in (('Fórmula Mágica — Top 20, peso igual, trimestral', W(20)), ('Fórmula Mágica — Top 30, peso igual, trimestral', W(30)),
                   ('Fórmula Mágica — Top 20, raiz com teto, trimestral', W(20, 'sqrt'))):
        navs[lab] = run_weighted(w, adj, dates); n[lab] = 20 if 'Top 20' in lab else 30
    w30 = W(30); ann = []
    for k in range(4):
        ds = [d for i, d in enumerate(dates) if i % 4 == k] + [dates[-1]]; ds = sorted(set(ds))
        nav = run_weighted({d: w30[d] for d in ds if d in w30}, adj, ds); ann.append(nav)
    t0 = max(a.index[0] for a in ann)
    navs['Fórmula Mágica — Top 30, troca anual (média de 4)'] = pd.concat([a.loc[t0:] / a.loc[t0:].iloc[0] for a in ann], axis=1).ffill().mean(axis=1); n['Fórmula Mágica — Top 30, troca anual (média de 4)'] = 30
    out = ['# Fórmula Mágica de Greenblatt × Opportunity of Lifetime (pré-registrado em 2026-11-14)\n',
           '> ⚠️ **O ROIC pode estar errado** — a Fórmula usa o retorno sobre capital tangível do Greenblatt (EBIT ÷ capital de giro + imobilizado), não o nosso triangulado.\n',
           f'S&P 500 point-in-time, {dates[0]:%m/%Y} a {dates[-1]:%m/%Y}, sem financeiras e utilities, sem custos nem impostos.\n',
           '## 1. Período todo (2011–2026)\n'] + bm.bench_table(navs, n)
    # periodo dos ETFs
    import yfinance as yf
    px = yf.download('SPYG', start='2019-06-01', progress=False, auto_adjust=True)['Close'].squeeze(); px.index = pd.to_datetime(px.index).tz_localize(None)
    E = pd.read_csv(ROOT.parent / 'etfs' / 'navs_etf.csv', index_col=0, parse_dates=True) if (ROOT.parent / 'etfs' / 'navs_etf.csv').exists() else None
    t1 = pd.Timestamp('2019-12-31'); t1 = max(d for d in navs['S&P 500'].index if d <= t1)
    sub = {k: (v.loc[t1:] / v.loc[t1:].iloc[0]) for k, v in navs.items()}
    s = px.loc[t1:dates[-1]].dropna(); sub['SPYG parado'] = s / s.iloc[0]
    if E is not None:
        for col in E.columns: x = E[col].loc[t1:].dropna(); sub[col] = x / x.iloc[0]
    out += ['', f'## 2. Período dos ETFs ({t1:%m/%Y}–{dates[-1]:%m/%Y})\n'] + bm.bench_table(sub, n)
    last = F[F.date == F.date.max()].sort_values('score').head(20)
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    out += ['', f'## 3. Fórmula Mágica hoje ({F.date.max():%m/%Y})\n', '| # | Ação | Empresa | Setor | Retorno sobre capital | Rendimento (EBIT/EV) |', '|---|---|---|---|---|---|']
    out += [f'| {i} | {r.ticker} | {str(u.name.get(r.ticker, r.ticker))[:28]} | {r.sector} | {r.roc:.0%} | {r.ey:.1%} |'.replace('.', ',', 0) for i, r in enumerate(last.itertuples(), 1)]
    (ROOT / 'magic.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or 'Fórmula' in k or k.startswith('Top 20')}, ROOT / 'magic.png',
                  'Fórmula Mágica de Greenblatt × Opportunity of Lifetime × comparativos obrigatórios (S&P 500, 2011–2026)')


if __name__ == '__main__':
    main()
