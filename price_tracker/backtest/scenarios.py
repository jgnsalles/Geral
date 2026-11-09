"""6 cenarios: g maximo 7% ou 6% x ROIC usado no P/E justo (original, marginal de 5 anos, media dos dois).
- g: ranking pela mediana do crescimento de 5 anos; geral de g_max ate 3,5%; financeiras de g_max - 0,5 p.p. ate 3%.
- ROIC alternativo entra so no P/E justo (1 - g/ROIC)/(8,5% - g). Criterios de qualidade (ROIC > 20%, zROIC) seguem com o original.
- ROIC marginal = (NOPAT_t - NOPAT_t-5) / (IC_t - IC_t-5); sem crescimento de capital investido -> usa o original.
Uso: python3 backtest/scenarios.py"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

CUTS = {'2,93': 2.93, '0,9': 0.9}
GMAX = [0.07, 0.06]
ROICS = {'original': 'Original', 'marg': 'Marginal 5a', 'media': 'Média'}
SHOW = ['Opportunity of Lifetime', 'Good Companies, Great Returns', 'Excellent but Fair', 'Interesting but Requires Attention',
        'Good but Margin of Safety Required', 'Expensive', 'Do not Waste Time']
pc = lambda x: f'{x:.1%}'.replace('.', ',')
sg = lambda x: f'{x:+.1%}'.replace('.', ',')


def g_rank(x, gmax):
    out = pd.Series(np.nan, index=x.index)
    for fin, top, floor in ((False, gmax, 0.035), (True, gmax - 0.005, 0.03)):
        m = x.fin == fin
        r = x.loc[m, 'growth'].dropna().to_numpy()
        rk = x.loc[m, 'growth'].apply(lambda v: np.nan if pd.isna(v) else 1 + (r > v).sum())
        out[m] = top - (rk - 1) * (top - floor) / (len(r) - 1)
    return out


def classify(cls, gmax, rv, cut):
    x = cls.copy()
    marg = x.roic_marg.where(x.roic_marg.notna(), x.roic)          # sem delta de capital: original
    roic_pe = {'original': x.roic, 'marg': marg, 'media': (x.roic + marg) / 2}[rv]
    parts = []
    for d, y in x.assign(roic_pe=roic_pe).groupby('date'):
        y = y.copy()
        y['g'] = g_rank(y, gmax)
        y['fair_pe'] = np.where(y.roic_pe > 0, engine.fair_pe(y.g, y.roic_pe), np.nan)
        base = y.fair_pe * y.eps * (1 + y.growth) ** 2 / y.price
        y['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + y.dy
        both = y.ret_fair.notna() & y.ret_const.notna()
        y['ret'] = np.where(both, (y.ret_fair + y.ret_const) / 2, y.growth)
        parts.append(y)
    y = pd.concat(parts)
    saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
    try:
        c = engine.classify(y.drop(columns=[k for k in y.columns if k.startswith('cat_')], errors='ignore'))
    finally:
        engine.TH['zGrowth'] = saved
    y['cat'] = np.where(c.code.isna(), None, c.category)
    return y


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)]
    valid = cls.roic_marg.notna()
    lines = ['# 6 cenários: g máximo × ROIC no P/E justo\n',
             '> ⚠️ **ROIC:** o ROIC alternativo entra só no P/E justo; a definição de capital investido e os cortes 20%/10% continuam pendentes.\n',
             f'ROIC marginal de 5 anos disponível em {valid.mean():.0%} das observações; no resto (capital investido não cresceu ou sem 5 anos) usa o original. '
             f'Mediana do ROIC original {cls.roic.median():.1%} e do marginal {cls.roic_marg.median():.1%}.\n'.replace('.', ',', 0),
             'Cada célula: CAGR (excesso a.a. sobre o Universo EW; t) · ações em média.\n']
    for cname, cut in CUTS.items():
        res = {}
        univ = None
        for gmax in GMAX:
            for rv in ROICS:
                x = classify(cls, gmax, rv, cut)
                if univ is None:
                    univ = run_portfolio({d: g.ticker.tolist() for d, g in x[x.cat.notna()].groupby('date')}, adj, dates)[0]
                    uq = univ.resample('QE').last().pct_change().dropna()
                for cat in SHOW:
                    nav, _, _, n = run_portfolio({d: g.ticker.tolist() for d, g in x[x.cat == cat].groupby('date')}, adj, dates)
                    q = nav.resample('QE').last().pct_change().dropna()
                    ex = (q - uq.reindex(q.index)).dropna()
                    res[(gmax, rv, cat)] = (stats(nav)['CAGR'], ex.mean() * 4, ex.mean() / ex.std() * np.sqrt(len(ex)), n)
                print(cname, gmax, rv, flush=True)
        cols = [(gm, rv) for gm in GMAX for rv in ROICS]
        lines += [f'## Corte zGrowth {cname} (Universo EW: {pc(stats(univ)["CAGR"])} a.a.)\n',
                  '| Classe | ' + ' | '.join(f'g {int(gm * 100)}% · {ROICS[rv]}' for gm, rv in cols) + ' |',
                  '|---|' + '---|' * len(cols)]
        for cat in SHOW:
            cells = []
            for gm, rv in cols:
                c, e, t, n = res[(gm, rv, cat)]
                cells.append(f'{pc(c)} ({sg(e)}; t={t:.1f}) · {n:.0f}'.replace('t=', 't=').replace('.', ',', 0))
            lines.append(f'| {cat} | ' + ' | '.join(cells) + ' |')
        lines.append('')
    (ROOT / 'scenarios.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
