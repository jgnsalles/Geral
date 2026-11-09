"""Varre o corte alto de ROIC (20% -> 12%, passo 0,5 p.p.) e mede Opportunity of Lifetime e Good Companies, Great Returns.
Demais parametros da versao atual (g 7%, WACC 8,5%, zROIC 0,7, ROIC baixo 10%, zGrowth 2,93). Uso: python3 backtest/roic_sweep.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

CUTS = [round(0.20 - 0.005 * i, 3) for i in range(17)]
if len(sys.argv) > 2:  # ex.: python3 backtest/roic_sweep.py 0.50 0.10
    hi, lo = float(sys.argv[1]), float(sys.argv[2])
    CUTS = [round(hi - 0.005 * i, 3) for i in range(int(round((hi - lo) / 0.005)) + 1)]
TAG = '' if len(sys.argv) <= 2 else f'_{int(round(float(sys.argv[1]) * 100))}_{int(round(float(sys.argv[2]) * 100))}'
pc = lambda x: f'{x:.1%}'.replace('.', ',')
sg = lambda x: f'{x:+.1%}'.replace('.', ',')
nm = lambda x: f'{x:.1f}'.replace('.', ',')


def main():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)].copy()
    base = cb.classify(cls, False, False, False)  # fair PE e retorno nao dependem do corte de ROIC
    univ = run_portfolio({d: g.ticker.tolist() for d, g in base[base.cat.notna()].groupby('date')}, adj, dates)[0]
    uq = univ.resample('QE').last().pct_change().dropna()
    rows = []
    for cut in CUTS:
        saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': cut})
        try:
            c = engine.classify(base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore'))
        finally:
            engine.TH.clear(); engine.TH.update(saved)
        c['cat'] = np.where(c.code.isna(), None, c.category)
        r = {'cut': cut}
        for k, cat in (('ool', cb.OOL), ('gcgr', cb.GCGR)):
            nav, _, _, n = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat == cat].groupby('date')}, adj, dates)
            q = nav.resample('QE').last().pct_change().dropna(); e = (q - uq.reindex(q.index)).dropna()
            r.update({f'{k}_cagr': stats(nav)['CAGR'], f'{k}_ex': e.mean() * 4, f'{k}_t': e.mean() / e.std() * np.sqrt(len(e)),
                      f'{k}_n': n, f'{k}_dd': stats(nav)['MaxDD']})
        rows.append(r); print(cut, flush=True)
    df = pd.DataFrame(rows); df.to_csv(D / f'roic_sweep{TAG}.csv', index=False)
    out = ['# Varredura do corte alto de ROIC (EUA, 2012–2026)\n',
           '> ⚠️ **ROIC:** ROIC da rodada 2; corte baixo fixo em 10%; zROIC 0,7; g 7%; WACC 8,5%; zGrowth 2,93.\n',
           f'Universo EW: {pc(stats(univ)["CAGR"])} a.a. · S&P 500 (SPY): {pc(stats(adj["SPY"].loc[dates[0]:dates[-1]] / adj["SPY"].loc[dates[0]])["CAGR"])} a.a.\n',
           '| Corte de ROIC | OoL CAGR | OoL vs Universo | OoL t | OoL ações | GCGR CAGR | GCGR vs Universo | GCGR t | GCGR ações | OoL − GCGR |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for _, r in df.iterrows():
        out.append(f"| {pc(r.cut)} | {pc(r.ool_cagr)} | {sg(r.ool_ex)} | {nm(r.ool_t)} | {nm(r.ool_n)} | {pc(r.gcgr_cagr)} | {sg(r.gcgr_ex)} | {nm(r.gcgr_t)} | {nm(r.gcgr_n)} | {sg(r.ool_cagr - r.gcgr_cagr)} |")
    (ROOT / f'roic_sweep{TAG}.md').write_text('\n'.join(out))
    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
    x = df.cut * 100
    ax.plot(x, df.ool_cagr * 100, 'o-', color='#1f6feb', lw=2.0, ms=3, label='Opportunity of Lifetime')
    ax.plot(x, df.gcgr_cagr * 100, 'o-', color='#e8590c', lw=2.0, ms=3, label='Good Companies, Great Returns')
    ax.axvline(20, color='#8c959f', ls=':', lw=1.2, label='Corte atual (20%)')
    ax.axhline(stats(univ)['CAGR'] * 100, color='#57606a', ls='--', lw=1.4, label='Universo EW (contraprova)')
    ax.invert_xaxis(); ax.set_xlabel('Corte alto de ROIC (%)'); ax.set_ylabel('Retorno anual (CAGR)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%')); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.1f}%'.replace('.', ',')))
    ax.grid(alpha=.3); ax.legend(fontsize=9); ax.set_title('Retorno anual por corte alto de ROIC (2012–2026)', fontsize=10)
    ax2 = ax.twinx(); ax2.bar(x, df.ool_n, width=0.4, color='#1f6feb', alpha=0.12); ax2.set_ylabel('Ações em OoL (média, barras)', color='#1f6feb')
    fig.tight_layout(); fig.savefig(ROOT / f'roic_sweep{TAG}.png'); plt.close(fig)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
