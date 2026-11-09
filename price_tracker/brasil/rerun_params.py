"""Reclassifica o Brasil com os parametros dos EUA + 2,5 p.p. (diferencial de inflacao), igual para operacionais e financeiras.
Variante A: cortes de ROIC iguais aos dos EUA; variante B: cortes de ROIC tambem + 2,5 p.p.
Uso: python3 brasil/rerun_params.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import backtest_br as bb  # noqa: E402
from backtest import run_portfolio, stats  # noqa: E402

D = ROOT / 'data'
ADD = 0.025
bb.WACC, bb.GMAX, bb.GMIN, bb.FIN_SHIFT = 0.085 + ADD, 0.07 + ADD, 0.035 + ADD, 0.0
BASE_TH = dict(engine.TH)
VARIANTS = {'A (ROIC 20%/10%)': False, 'B (ROIC 22,5%/12,5%)': True}
SHOW = ['Opportunity of Lifetime', 'Good Companies, Great Returns', 'Excellent but Fair', 'Good but Margin of Safety Required',
        'Cheap Slow Compounder', 'Interesting but Requires Attention', 'Cheap but Aggressive', 'Expensive for what you get',
        'Investable but Not Good', 'Expensive', 'Do not Waste Time']
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date']).drop(columns=lambda c: c.startswith('cat_'), errors='ignore')
    cls = cls[[c for c in cls.columns if not c.startswith('cat_')]]
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    close = pd.read_csv(D / 'prices_close.csv.gz', index_col=0, parse_dates=True)
    parts = []
    for d, x in cls.groupby('date'):
        x = x.copy()
        x['g'] = bb.g_rank(x)
        x['fair_pe'] = np.where(x.roic > 0, (1 - x.g / x.roic) / (bb.WACC - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    x = pd.concat(parts)
    out = ['# Brasil: parâmetros dos EUA + 2,5 p.p.\n',
           '> ⚠️ **ROIC:** a variante B sobe também os cortes de ROIC; a definição de ROIC segue em revisão.\n',
           f'WACC {pc(bb.WACC)}; g {pc(bb.GMAX)} → {pc(bb.GMIN)} (operacionais e financeiras); crescimento 17,5%/8,5%; retorno 22,5%/10,5%.\n']
    for vname, roic_up in VARIANTS.items():
        for cut in (2.93, 0.9):
            engine.TH.clear(); engine.TH.update(BASE_TH)
            engine.TH.update({'Growth_Hi': 0.15 + ADD, 'Growth_Lo': 0.06 + ADD, 'Return_Hi': 0.20 + ADD, 'Return_Lo': 0.08 + ADD, 'zGrowth': cut})
            if roic_up: engine.TH.update({'Roic_Hi': 0.20 + ADD, 'Roic_Lo': 0.10 + ADD})
            c = engine.classify(x)
            c['cat'] = np.where(c.code.isna(), None, c.category)
            cov = c.groupby('date').cat.apply(lambda s: s.notna().sum())
            start = cov[cov >= 60].index.min()
            dates = [d for d in bb.rebalance_dates(close) if d >= start]
            c = c[c.date >= start]
            univ = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat.notna()].groupby('date')}, adj, dates)[0]
            uq = univ.resample('QE').last().pct_change().dropna()
            out += [f'## Variante {vname}, corte zGrowth {str(cut).replace(".", ",")} (início {start:%d/%m/%Y})\n',
                    '| Carteira | Retorno anual | vs Universo EW | t | Ações em média | Trimestres vazios |', '|---|---|---|---|---|---|']
            for cat in SHOW:
                hold = {d: g.ticker.tolist() for d, g in c[c.cat == cat].groupby('date')}
                nav, _, _, n = run_portfolio(hold, adj, dates)
                q = nav.resample('QE').last().pct_change().dropna(); ex = (q - uq.reindex(q.index)).dropna()
                t = ex.mean() / ex.std() * np.sqrt(len(ex)) if ex.std() > 0 else np.nan
                out.append(f'| {cat} | {pc(stats(nav)["CAGR"])} | {sg(ex.mean() * 4)} | {t:.1f} | {n:.1f} | {sum(1 for d in dates[:-1] if not hold.get(d))} |'.replace('.', ',', 0))
            out.append(f'| *Universo EW* | {pc(stats(univ)["CAGR"])} | | | {c[c.cat.notna()].groupby("date").size().mean():.0f} | |')
            for b in bb.BENCH:
                nb = adj[b].loc[dates[0]:dates[-1]].dropna()
                out.append(f'| *{b.replace(".SA", "")}* | {pc(stats(nb / nb.iloc[0])["CAGR"])} | | | | |')
            out.append('')
            print(vname, cut, flush=True)
    (ROOT / 'rerun_params.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
