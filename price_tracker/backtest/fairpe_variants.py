"""Testa ajustes no P/E justo para nao dar peso excessivo a ROIC muito alto.
 A  original:        (1 - g/ROIC) / (WACC - g)
 B  ROIC normalizado: ROIC_n = mediana do universo na data + 50% * (ROIC - mediana)   (reversao a media, Fama-French/Mauboussin)
 C  dois estagios:   10 anos com g e ROIC da empresa; depois perpetuidade com RONIC = WACC (McKinsey, Valuation)
Tudo o mais igual ao backtest (metodo 2, point-in-time, equal weight, trimestral).
Uso: python3 backtest/fairpe_variants.py"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

W = engine.WACC
CUTS = {'2,93': 2.93, '0,9': 0.9}
OOL, GCGR, EF = 'Opportunity of Lifetime', 'Good Companies, Great Returns', 'Excellent but Fair'
SHOW = [OOL, GCGR, EF, 'Interesting but Requires Attention', 'Good but Margin of Safety Required', 'Expensive', 'Do not Waste Time']


def pe_original(g, roic):
    return engine.fair_pe(g, roic)


def pe_normalized(x):
    med = x.groupby('fin').roic.transform('median')
    return engine.fair_pe(x.g, med + 0.5 * (x.roic - med))


def pe_two_stage(g, roic, n=10):
    rr = (g / roic).clip(lower=0, upper=1)
    t = np.arange(1, n + 1)
    g_, rr_ = g.to_numpy()[:, None], rr.to_numpy()[:, None]
    stage1 = ((1 + g_) ** (t - 1) * (1 - rr_) / (1 + W) ** t).sum(axis=1)
    terminal = (1 + g.to_numpy()) ** n / W / (1 + W) ** n  # RONIC = WACC: crescimento nao cria valor
    out = stage1 + terminal
    return pd.Series(np.where(roic > 0, out, np.nan), index=g.index)


def classify(cls, variant, cut):
    out = []
    for d, x in cls.groupby('date'):
        x = x.copy()
        if variant == 'A': x['fair_pe'] = pe_original(x.g, x.roic)
        elif variant == 'B': x['fair_pe'] = pe_normalized(x)
        else: x['fair_pe'] = pe_two_stage(x.g, x.roic)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
        try:
            c = engine.classify(x.drop(columns=[k for k in x.columns if k.startswith('cat_')] + ['category', 'code'], errors='ignore'))
        finally:
            engine.TH['zGrowth'] = saved
        x['cat'] = np.where(c.code.isna(), None, c.category)
        out.append(x)
    return pd.concat(out)


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)]
    lines = ['# Ajuste do P/E justo para ROIC alto\n',
             '> ⚠️ **ROIC:** o ajuste trata o peso do ROIC no P/E justo; a definição do ROIC (capital investido, cortes 20%/10%) continua pendente.\n',
             'A = original; B = ROIC normalizado (50% do excedente sobre a mediana); C = dois estágios (10 anos, depois RONIC = WACC).\n']
    univ = None
    for cname, cut in CUTS.items():
        res, extra = {}, {}
        for v in 'ABC':
            x = classify(cls, v, cut)
            res[v] = {}
            for cat in SHOW:
                hold = {d: g.ticker.tolist() for d, g in x[x.cat == cat].groupby('date')}
                nav, _, _, n = run_portfolio(hold, adj, dates)
                res[v][cat] = (stats(nav), n, nav)
            if univ is None:
                hold = {d: g.ticker.tolist() for d, g in x[x.cat.notna()].groupby('date')}
                univ = run_portfolio(hold, adj, dates)[0]
            o = x[x.cat == OOL]; gg = x[x.cat == GCGR]
            extra[v] = dict(pe_paid_ool=(o.price / o.eps.where(o.eps > 0)).median(), fpe_ool=o.fair_pe.median(),
                            roic_ool=o.roic.median(), pe_paid_g=(gg.price / gg.eps.where(gg.eps > 0)).median(), fpe_g=gg.fair_pe.median(),
                            fpe_all=x.fair_pe.median(), fpe_p90=x.fair_pe.quantile(.9))
            if v == 'A': base_x = x
            else:
                m = base_x[base_x.cat == OOL][['date', 'ticker']].merge(x[['date', 'ticker', 'cat']], on=['date', 'ticker'])
                extra[v]['dest'] = m.cat.value_counts(normalize=True).head(4)
        uq = univ.resample('QE').last().pct_change().dropna()
        lines += [f'## Corte zGrowth {cname}\n', '### Retorno anual (CAGR) e excesso sobre o Universo EW (t)\n',
                  '| Classe | A original | B ROIC normalizado | C dois estágios | N médio (A / B / C) |', '|---|---|---|---|---|']
        for cat in SHOW:
            cells = []
            for v in 'ABC':
                s, n, nav = res[v][cat]
                q = nav.resample('QE').last().pct_change().dropna()
                ex = (q - uq.reindex(q.index)).dropna()
                t = ex.mean() / ex.std() * np.sqrt(len(ex))
                cells.append(f"{s['CAGR']:.1%} ({ex.mean() * 4:+.1%}; t={t:.1f})".replace('.', ','))
            ns = ' / '.join(f'{res[v][cat][1]:.0f}' for v in 'ABC')
            lines.append(f'| {cat} | ' + ' | '.join(cells) + f' | {ns} |')
        lines += [f"| Universo EW | {stats(univ)['CAGR']:.1%} | | | |".replace('.', ','), '']
        lines += ['### P/E justo × P/L pago (medianas)\n', '| | A | B | C |', '|---|---|---|---|']
        f1 = lambda k: ' | '.join(f'{extra[v][k]:.1f}'.replace('.', ',') for v in 'ABC')
        lines += [f'| P/E justo, universo (mediana) | {f1("fpe_all")} |', f'| P/E justo, universo (percentil 90) | {f1("fpe_p90")} |',
                  f'| Opportunity of Lifetime: P/E justo | {f1("fpe_ool")} |', f'| Opportunity of Lifetime: P/L pago | {f1("pe_paid_ool")} |',
                  f'| Good Companies, Great Returns: P/E justo | {f1("fpe_g")} |', f'| Good Companies, Great Returns: P/L pago | {f1("pe_paid_g")} |', '']
        for v in 'BC':
            d = ', '.join(f'{k} {p:.0%}' for k, p in extra[v]['dest'].items())
            lines.append(f'- Para onde vão as ações que eram Opportunity of Lifetime em A, na variante {v}: {d}')
        lines.append('')
        univ = None
    (ROOT / 'fairpe_variants.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
