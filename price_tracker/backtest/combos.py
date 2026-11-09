"""8 combinacoes de 3 ajustes (EUA, cenario-base da rodada 2, zGrowth 2,93):
  A) g maximo +1 p.p. (7% -> 8%; financeiras 6,5% -> 7,5%) e WACC +1 p.p. (8,5% -> 9,5%); pisos de g inalterados
  B) corte alto de ROIC 20% -> 16%
  C) corte de zROIC 0,7 -> 0,8
Saidas: backtest/combos.md, backtest/combos_ool.png, backtest/combos_gcgr.png
Uso: python3 backtest/combos.py"""
import sys, itertools, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
CLASSES = [OOL, GCGR, 'Excellent but Fair', 'Good but Margin of Safety Required', 'Cheap Slow Compounder', 'Interesting but Requires Attention',
           'Cheap but Aggressive', 'Expensive for what you get', 'Investable but Not Good', 'Expensive', 'Do not Waste Time']
FLAW = {0: 'Growth médio', 1: 'Growth instável', 2: 'ROIC médio', 3: 'ROIC instável'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')
n2 = lambda x: f'{x:.2f}'.replace('.', ',')


def name(a, b, c):
    parts = [p for p, on in (('g/WACC +1', a), ('ROIC 16%', b), ('zROIC 0,8', c)) if on]
    return 'Base (atual)' if not parts else ' + '.join(parts)


def g_rank(x, gmax):
    out = pd.Series(np.nan, index=x.index)
    for fin, top, floor in ((False, gmax, 0.035), (True, gmax - 0.005, 0.03)):
        m = x.fin == fin
        r = x.loc[m, 'growth'].dropna().to_numpy()
        rk = x.loc[m, 'growth'].apply(lambda v: np.nan if pd.isna(v) else 1 + (r > v).sum())
        out[m] = top - (rk - 1) * (top - floor) / (len(r) - 1)
    return out


def classify(cls, a, b, c):
    gmax, wacc = (0.08, 0.095) if a else (0.07, 0.085)
    parts = []
    for d, x in cls.groupby('date'):
        x = x.copy(); x['g'] = g_rank(x, gmax)
        x['fair_pe'] = np.where(x.roic > 0, (1 - x.g / x.roic) / (wacc - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    x = pd.concat(parts)
    saved = dict(engine.TH)
    engine.TH['zGrowth'] = 2.93
    if b: engine.TH['Roic_Hi'] = 0.16
    if c: engine.TH['zRoic'] = 0.8
    try:
        out = engine.classify(x.drop(columns=[k for k in x.columns if k.startswith('cat_')], errors='ignore'))
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    out['cat'] = np.where(out.code.isna(), None, out.category)
    return out


def pos_perf(x, univ):
    if x.empty: return dict(n=0)
    ex = x.rq - x.date.map(univ)
    q = ex.groupby(x.date).mean()
    t = q.mean() / q.std() * np.sqrt(len(q)) if len(q) > 2 and q.std() > 0 else np.nan
    return dict(n=len(x), emp=x.ticker.nunique(), ret=x.rq.mean() * 4, ex=ex.mean() * 4, t=t)


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)].copy()
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill(); fwd = px.shift(-1) / px - 1
    cls['rq'] = [fwd.at[d, t] for d, t in zip(cls.date, cls.ticker)]
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    combos = list(itertools.product([False, True], repeat=3))
    navs, summary, details = {OOL: {}, GCGR: {}}, [], []
    for a, b, c in combos:
        nmc = name(a, b, c)
        x = classify(cls, a, b, c)
        univ_pos = x[x.cat.notna() & (x.date < dates[-1])].groupby('date').rq.mean()
        univ = run_portfolio({d: g.ticker.tolist() for d, g in x[x.cat.notna()].groupby('date')}, adj, dates)[0]
        uq = univ.resample('QE').last().pct_change().dropna()
        cl_rows = []
        for cat in CLASSES:
            hold = {d: g.ticker.tolist() for d, g in x[x.cat == cat].groupby('date')}
            nav, _, _, n = run_portfolio(hold, adj, dates)
            q = nav.resample('QE').last().pct_change().dropna(); e = (q - uq.reindex(q.index)).dropna()
            t = e.mean() / e.std() * np.sqrt(len(e)) if e.std() > 0 else np.nan
            s = stats(nav)
            s1 = (nav.loc['2012':'2019'].iloc[-1] / nav.loc['2012':'2019'].iloc[0]) ** (1 / ((nav.loc['2012':'2019'].index[-1] - nav.loc['2012':'2019'].index[0]).days / 365.25)) - 1
            s2 = (nav.loc['2020':].iloc[-1] / nav.loc['2020':].iloc[0]) ** (1 / ((nav.loc['2020':].index[-1] - nav.loc['2020':].index[0]).days / 365.25)) - 1
            cl_rows.append((cat, s['CAGR'], e.mean() * 4, t, s['MaxDD'], n, s1, s2))
            if cat in navs: navs[cat][nmc] = nav
        summary.append((nmc, {r[0]: r for r in cl_rows}, stats(univ)['CAGR']))
        # desqualificacoes
        xo = x[(x.cat == OOL) & (x.date < dates[-1])]; xg = x[(x.cat == GCGR) & (x.date < dates[-1])].copy()
        roic_hi = 0.16 if b else 0.20; zr = 0.8 if c else 0.7
        xg['flaw'] = xg.code.map(lambda s: next((i for i in range(4) if s[i] != 'HOGNG'[i]), None))
        sec = [f'## {nmc}\n', f'Parâmetros: g máx {"8%" if a else "7%"}, WACC {"9,5%" if a else "8,5%"}, ROIC alto {pc(roic_hi)}, zROIC {n2(zr)}. '
               f'Universo EW: {pc(stats(univ)["CAGR"])} a.a.\n',
               '### Todas as classes\n', '| Classe | CAGR | vs Universo | t | Max DD | Ações (média) | 2012–19 | 2020–26 |', '|---|---|---|---|---|---|---|---|']
        sec += [f'| {r[0]} | {pc(r[1])} | {sg(r[2])} | {nm(r[3])} | {pc(r[4])} | {nm(r[5])} | {pc(r[6])} | {pc(r[7])} |' for r in cl_rows]
        po = pos_perf(xo, univ_pos)
        sec += ['', '### Good Companies, Great Returns por motivo de desqualificação (posições)\n',
                '| Grupo | Posições | Empresas | % de GCGR | Retorno a.a. | vs Universo | t |', '|---|---|---|---|---|---|---|',
                f"| *Opportunity of Lifetime (referência)* | {po['n']} | {po['emp']} | — | {pc(po['ret'])} | {sg(po['ex'])} | {nm(po['t'])} |"]
        sub = []
        for k in range(4):
            gk = xg[xg.flaw == k]; p = pos_perf(gk, univ_pos)
            if p['n'] == 0: sec.append(f'| {FLAW[k]} | 0 | | | | | |'); continue
            sec.append(f"| {FLAW[k]} | {p['n']} | {p['emp']} | {pc(len(gk) / len(xg))} | {pc(p['ret'])} | **{sg(p['ex'])}** | {nm(p['t'])} |")
            # faixas dentro do motivo
            var, nb, lab = {0: ('growth', 3, 'Growth'), 1: ('zgrowth', 3, 'zGrowth'), 2: ('roic', 3, 'ROIC'), 3: ('zroic', 5, 'zROIC')}[k]
            try:
                bins = pd.qcut(gk[var], nb, duplicates='drop')
            except ValueError:
                continue
            rows = []
            for iv, gg in gk.groupby(bins, observed=True):
                q = pos_perf(gg, univ_pos)
                f = (lambda v: pc(v)) if var in ('growth', 'roic') else n2
                rows.append(f"| {f(iv.left)}–{f(iv.right)} | {q['n']} | {q['emp']} | {pc(q['ret'])} | **{sg(q['ex'])}** | {nm(q['t'])} |")
            sub += [f'**{FLAW[k]}: por faixa de {lab}**\n', f'| Faixa de {lab} | Posições | Empresas | Retorno a.a. | vs Universo | t |', '|---|---|---|---|---|---|'] + rows + ['']
        pg = pos_perf(xg, univ_pos)
        sec += [f"| **Good Companies, Great Returns (total)** | {pg['n']} | {pg['emp']} | 100% | {pc(pg['ret'])} | {sg(pg['ex'])} | {nm(pg['t'])} |", '',
                '### Dentro de cada motivo: desempenho por faixa\n'] + sub
        details += sec
        print(nmc, flush=True)

    # graficos
    for cat, fn in ((OOL, 'combos_ool.png'), (GCGR, 'combos_gcgr.png')):
        fig, ax = plt.subplots(figsize=(11, 6), dpi=140)
        cmap = plt.cm.tab10.colors
        for i, (k, nav) in enumerate(navs[cat].items()):
            s = (nav - 1) * 100
            ax.plot(s.index, s, color=cmap[i], lw=2.6 if k == 'Base (atual)' else 1.5,
                    label=f'{k} ({s.iloc[-1]:+,.0f}%)'.replace(',', '.'))
        s = (spy - 1) * 100
        ax.plot(s.index, s, color='black', ls='--', lw=1.8, label=f'S&P 500 / SPY ({s.iloc[-1]:+,.0f}%)'.replace(',', '.'))
        ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.')))
        ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
        ax.set_title(f'{cat}: 8 combinações de ajustes × S&P 500 (retorno total acumulado, 2012–2026)', fontsize=10)
        fig.tight_layout(); fig.savefig(ROOT / fn); plt.close(fig)

    head = ['# 8 combinações: g/WACC +1 p.p. × ROIC alto 16% × zROIC 0,8 (EUA)\n',
            '> ⚠️ **ROIC:** dois dos três ajustes mexem em cortes de ROIC; ROIC da rodada 2 (capital operacional quando patrimônio ≤ 0).\n',
            'Backtest point-in-time 2012–2026, equal weight, rebalanceamento trimestral, corte de zGrowth 2,93. S&P 500 (SPY): '
            f'{pc(stats(spy)["CAGR"])} a.a.\n', '## Resumo\n',
            '| Combinação | OoL CAGR | OoL vs Universo (t) | OoL ações | GCGR CAGR | GCGR vs Universo (t) | GCGR ações | Universo EW |', '|---|---|---|---|---|---|---|---|']
    for nmc, rows, ucagr in summary:
        o, g = rows[OOL], rows[GCGR]
        head.append(f'| {nmc} | {pc(o[1])} | {sg(o[2])} ({nm(o[3])}) | {nm(o[5])} | {pc(g[1])} | {sg(g[2])} ({nm(g[3])}) | {nm(g[5])} | {pc(ucagr)} |')
    (ROOT / 'combos.md').write_text('\n'.join(head + [''] + details))
    print('\n'.join(head))


if __name__ == '__main__':
    main()
