"""Variantes pre-registradas (2026-11-11): crescimento do Brasil sem 2021 (A) e sem 2020-2021 (B). Regra congelada no resto.
Saida: brasil/sem2021.md. Uso: python3 brasil/sem2021.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT))
import backtest_br as bb  # noqa: E402
import oos_congelado as oc  # noqa: E402
import engine, top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
D = ROOT / 'data'
OOL, GCGR = oc.OOL, oc.GCGR


def build_classes(excl, path):
    if path.exists(): return pd.read_csv(path, parse_dates=['date'])
    bb.EXCL = set(excl)
    u = pd.read_csv(D / 'universe.csv')
    fund = pd.read_csv(D / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund = {c: g for c, g in fund.groupby('CD_CVM')}
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    close, vol = read('close'), read('volume'); divs, splits = read('dividends').fillna(0), read('stock_splits').fillna(0)
    c = bb.classify_all(u, fund, close, vol, divs, splits, bb.rebalance_dates(close)); c.to_csv(path, index=False); bb.EXCL = {2021}
    return c


def frozen(c, idx, fund, start):
    c = c[c.date >= start].copy()
    r = c.roic.clip(upper=1.0); c['fair_pe'] = np.where(r > 0, (1 - c.g / r) / (oc.WACC - c.g), np.nan)
    base = c.fair_pe * c.eps * (1 + c.growth) ** 2 / c.price
    c['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + c.dy; c['ret_const'] = c.growth + c.dy
    both = c.ret_fair.notna() & c.ret_const.notna(); c['ret'] = np.where(both, (c.ret_fair + c.ret_const) / 2, c.growth)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': 0.12, 'Roic_Lo': 0.10, 'zRoic': 0.7})
    try: n = engine.classify(c.assign(zroic=0.0))
    finally: engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(n.code.isna(), None, n.category)
    tk = c.ticker.map(idx.ticker)
    c['ok'] = ~(c.ticker.map(idx.Setor_Atividade).isin(oc.CYC_SECTORS) | tk.isin(oc.CYC_TICKERS) | tk.isin(oc.APPAREL))
    sh = {}
    for (t, fy), g in c.groupby(['ticker', 'last_fy']):
        ff = fund[(fund.CD_CVM == idx.Codigo_CVM.get(t)) & (fund.fy == fy)]
        ni = ff.sort_values('DT_RECEB').ni.iloc[-1] if len(ff) else np.nan
        e = g.eps.iloc[-1]; sh[(t, fy)] = ni / e if pd.notna(ni) and e and abs(e) > 1e-6 and np.sign(ni) == np.sign(e) else np.nan
    c['sh'] = [sh.get((t, y)) for t, y in zip(c.ticker, c.last_fy)]; c['sh'] = c.groupby('ticker').sh.transform(lambda s: s.ffill().bfill())
    c['mcap'] = (c.price * c.sh).where(lambda s: s > 0); c['mcap'] = c.mcap.fillna(c.groupby('date').mcap.transform('median'))
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    return c


def main():
    u = pd.read_csv(D / 'universe.csv'); idx = u.set_index('yf')
    fund = pd.read_csv(D / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    V = {'Regra atual (5 anos, com 2021)': pd.read_csv(D / 'classes_pit_com2021.csv', parse_dates=['date']),
         'A: sem 2021': build_classes([2021], D / 'classes_pit_sem2021.csv'),
         'B: sem 2020 e 2021': build_classes([2020, 2021], D / 'classes_pit_sem2020_2021.csv')}
    base = V['Regra atual (5 anos, com 2021)']; cov = base.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    dates = sorted(d for d in base.date.unique() if d >= start)
    navs, nn, today = {}, {}, {}
    for k, raw in V.items():
        c = frozen(raw, idx, fund, start)
        ool = c[(c.cat == OOL) & c.ok]
        navs[(k, 'OoL novo (raiz)')] = run_weighted({d: pd.Series(np.sqrt(g.mcap.values), index=g.ticker) for d, g in ool.groupby('date')}, adj, dates)
        nn[(k, 'OoL novo (raiz)')] = ool.groupby('date').size().mean()
        el = c[c.ok & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4) & c.cat.notna()]
        ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in el.groupby('date')])
        navs[(k, 'Top 20 (raiz, teto 10%)')] = run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in ch.groupby('date')}, adj, dates)
        nn[(k, 'Top 20 (raiz, teto 10%)')] = ch.groupby('date').size().mean()
        last = c[c.date == c.date.max()]
        today[k] = (last, set(last[(last.cat == OOL) & last.ok].ticker))
        print(k, flush=True)
    s = adj['BOVA11.SA'].loc[dates[0]:dates[-1]].dropna(); IB = s / s.iloc[0]; MI = IB.resample('ME').last(); SI = stats(IB)['CAGR']
    def win(nav, y):
        M = nav.resample('ME').last(); a = M / M.shift(12 * y); b = (MI / MI.shift(12 * y)).reindex(a.index); k = a.notna() & b.notna()
        return (a[k] > b[k]).mean()
    pc = lambda v: f'{v:.1%}'.replace('.', ',')
    out = ['# Brasil: crescimento sem a recuperação pós-COVID (variantes pré-registradas em 2026-11-11)\n',
           '> ⚠️ **O ROIC pode estar errado** (no Brasil é o ROIC clássico; financeiras usam ROE).\n',
           f'Período {pd.Timestamp(dates[0]):%m/%Y} a {pd.Timestamp(dates[-1]):%m/%Y}, em reais, trimestral, sem custos. Regra congelada no resto.\n',
           '| Crescimento | Carteira | Ações (média) | Retorno anual | vs Ibovespa | Pior queda | Janelas 3a > Ibov | Janelas 5a > Ibov |', '|---|---|---|---|---|---|---|---|']
    for (k, p), nav in navs.items():
        st = stats(nav)
        out.append(f"| {k} | {p} | {nn[(k, p)]:.0f} | **{pc(st['CAGR'])}** | {f'{(st['CAGR'] - SI) * 100:+.1f}'.replace('.', ',')} | {pc(st['MaxDD'])} | {win(nav, 3):.0%} | {win(nav, 5):.0%} |")
    out.append(f"| Ibovespa (BOVA11) | — | — | **{pc(SI)}** | — | {pc(stats(IB)['MaxDD'])} | — | — |")
    b0, s0 = today['Regra atual (5 anos, com 2021)']
    nm = lambda t: idx.ticker.get(t, t)
    out += ['', f'## OoL de hoje ({pd.Timestamp(b0.date.max()):%m/%Y}): quem muda\n', '| Crescimento | Ações na OoL | Saem | Entram |', '|---|---|---|---|']
    for k, (l, s_) in today.items():
        out.append(f"| {k} | {len(s_)} | {', '.join(sorted(map(nm, s0 - s_))) or '—'} | {', '.join(sorted(map(nm, s_ - s0))) or '—'} |")
    g = pd.DataFrame({k: l.set_index('ticker').growth for k, (l, _) in today.items()})
    g = g[g.index.isin(set().union(*[s_ for _, s_ in today.values()]))].sort_values('Regra atual (5 anos, com 2021)', ascending=False)
    out += ['', '## Crescimento do lucro usado pelo modelo, hoje (OoL em qualquer versão)\n', '| Ação | ' + ' | '.join(g.columns) + ' |', '|---|' + '---|' * len(g.columns)]
    for t, r in g.iterrows():
        out.append(f'| {nm(t)} | ' + ' | '.join('—' if pd.isna(v) else f'{v:.0%}' for v in r) + ' |')
    (ROOT / 'sem2021.md').write_text('\n'.join(out)); print('\n'.join(out))


if __name__ == '__main__':
    main()
