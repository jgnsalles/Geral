"""ESBOCO (nao altera o consolidado): Opportunity of Lifetime a partir de ROIC 12% e dividida em subclasses.
 - ROIC alto >= 12% (era 20%); ROIC medio 10%-12% (corte baixo mantido em 10%); demais regras da versao atual.
 - OoL High Returns: OoL com ROIC > 30%.  OoL High Growth: OoL com crescimento do EPS (mediana 5 anos) > 30%.
   Quem tem os dois entra nas duas.  OoL Base: OoL sem nenhum dos dois.
Uso: python3 backtest/esboco_ool_split.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

ROIC_HI, ROIC_LO, HR, HG = 0.12, 0.10, 0.30, 0.30
EXCLUDE = [a for a in sys.argv[1:]]  # ex.: python3 backtest/esboco_ool_split.py NVDA
TAG = '' if not EXCLUDE else '_sem_' + '_'.join(EXCLUDE)
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def cagr_between(nav, a, b):
    s = nav.loc[a:b].dropna(); yrs = (s.index[-1] - s.index[0]).days / 365.25
    return (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    base = cb.classify(cls[cls.date.isin(dates)].copy(), False, False, False)  # g 7%, WACC 8,5% (fair PE independe dos cortes)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': ROIC_HI, 'Roic_Lo': ROIC_LO})
    try:
        c = engine.classify(base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore'))
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(c.code.isna(), None, c.category)
    c = c[~c.ticker.isin(EXCLUDE)]  # empresas excluidas de todas as carteiras (inclusive do universo)
    ool = c.cat == 'Opportunity of Lifetime'
    hr, hg = ool & (c.roic > HR), ool & (c.growth > HG)
    groups = {
        'OoL Base': ool & ~hr & ~hg,
        'OoL High Returns (ROIC > 30%)': hr,
        'OoL High Growth (EPS > 30%)': hg,
        'OoL High Returns + High Growth (as duas)': hr & hg,
        'Opportunity of Lifetime (todas, corte 12%)': ool,
        'Good Companies, Great Returns (ROIC médio 10–12%)': c.cat == 'Good Companies, Great Returns',
    }
    for cat in ['Excellent but Fair', 'Good but Margin of Safety Required', 'Interesting but Requires Attention', 'Do not Waste Time']:
        groups[cat] = c.cat == cat
    univ = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat.notna()].groupby('date')}, adj, dates)[0]
    uq = univ.resample('QE').last().pct_change().dropna()
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    rows, navs = [], {}
    for name, m in groups.items():
        hold = {d: g.ticker.tolist() for d, g in c[m].groupby('date')}
        nav, net, _, n = run_portfolio(hold, adj, dates)
        q = nav.resample('QE').last().pct_change().dropna(); e = (q - uq.reindex(q.index)).dropna()
        t = e.mean() / e.std() * np.sqrt(len(e)) if e.std() > 0 else np.nan
        s = stats(nav)
        rows.append((name, s['CAGR'], e.mean() * 4, t, s['Vol'], s['MaxDD'], n, sum(1 for d in dates[:-1] if not hold.get(d)),
                     cagr_between(nav, '2012', '2019'), cagr_between(nav, '2020', '2026'), c[m].ticker.nunique()))
        navs[name] = nav
    out = [f'# Esboço: Opportunity of Lifetime a partir de ROIC 12%, com subclasses High Returns e High Growth (EUA){" — sem " + ", ".join(EXCLUDE) if EXCLUDE else ""}\n',
           '> ⚠️ **ROIC:** esboço; não altera o consolidado. ROIC da rodada 2; ROIC alto ≥ 12%, médio 10–12%; demais regras atuais '
           '(g 7%, WACC 8,5%, Growth 15%/6%, zGrowth 2,93, zROIC 0,7, retorno 20%/8%).\n',
           f'Universo EW: {pc(stats(univ)["CAGR"])} a.a. · S&P 500 (SPY): {pc(stats(spy)["CAGR"])} a.a. · 2012–2026.\n',
           '| Carteira | CAGR | vs Universo | t | Vol | Max DD | Ações (média) | Trim. vazios | 2012–19 | 2020–26 | Empresas distintas |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    out += [f'| {r[0]} | {pc(r[1])} | {sg(r[2])} | {nm(r[3])} | {pc(r[4])} | {pc(r[5])} | {nm(r[6])} | {r[7]} | {pc(r[8])} | {pc(r[9])} | {r[10]} |' for r in rows]
    # empresas
    last = c.date.max()
    for name, m in [('OoL High Returns (ROIC > 30%)', hr), ('OoL High Growth (EPS > 30%)', hg)]:
        x = c[m]
        cur = x[x.date == last].sort_values('roic' if 'Returns' in name else 'growth', ascending=False)
        out += ['', f'## {name}\n', f'**Na última carteira ({last:%d/%m/%Y}):** {len(cur)} empresas\n',
                '| Ticker | Empresa | Setor | ROIC | Growth (mediana 5 anos) | Retorno esperado |', '|---|---|---|---|---|---|']
        out += [f'| {r.ticker} | {u["name"].get(r.ticker)} | {u.sector.get(r.ticker)} | {pc(r.roic)} | {pc(r.growth)} | {pc(r.ret)} |' for r in cur.itertuples()]
        hist = x.groupby('ticker').agg(trim=('date', 'size'), roic=('roic', 'median'), growth=('growth', 'median'), primeiro=('date', 'min'), ultimo=('date', 'max'))
        hist = hist.sort_values('trim', ascending=False)
        out += ['', f'**Histórico (2012–2026):** {len(hist)} empresas passaram pela subclasse. As 30 mais frequentes:\n',
                '| Ticker | Empresa | Trimestres | ROIC (mediana) | Growth (mediana) | Período |', '|---|---|---|---|---|---|']
        out += [f'| {t} | {u["name"].get(t)} | {r.trim} | {pc(r.roic)} | {pc(r.growth)} | {r.primeiro.year}–{r.ultimo.year} |' for t, r in hist.head(30).iterrows()]
    (ROOT / f'esboco_ool_split{TAG}.md').write_text('\n'.join(out))
    # grafico
    fig, ax = plt.subplots(figsize=(11, 6), dpi=140)
    sty = {'OoL Base': ('#1f6feb', '-', 2.4), 'OoL High Returns (ROIC > 30%)': ('#2da44e', '-', 2.0), 'OoL High Growth (EPS > 30%)': ('#8250df', '-', 2.0),
           'Opportunity of Lifetime (todas, corte 12%)': ('#0a3069', ':', 1.6), 'Good Companies, Great Returns (ROIC médio 10–12%)': ('#e8590c', '-', 2.0)}
    for k, (col, ls, lw) in sty.items():
        s = (navs[k] - 1) * 100
        ax.plot(s.index, s, color=col, ls=ls, lw=lw, label=f'{k} (' + f'{s.iloc[-1]:+,.0f}%'.replace(',', '.') + ')')
    for k, s0, col in (('Universo EW', univ, '#57606a'), ('S&P 500 / SPY', spy, '#000000')):
        s = (s0 - 1) * 100
        ax.plot(s.index, s, color=col, ls='--', lw=1.5, label=f'{k} (' + f'{s.iloc[-1]:+,.0f}%'.replace(',', '.') + ')')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Esboço: OoL a partir de ROIC 12% e subclasses (retorno total acumulado, 2012–2026)' + (f' — sem {", ".join(EXCLUDE)}' if EXCLUDE else ''), fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / f'esboco_ool_split{TAG}.png'); plt.close(fig)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
