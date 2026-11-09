"""Varre um criterio de corte (EUA, versao atual) e mede Opportunity of Lifetime e Good Companies, Great Returns.
Uso: python3 backtest/criteria_sweep.py <criterio>   criterio em: zroic, growth, zgrowth, ret"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

SPEC = {  # chave do engine.TH, valores, valor atual, rotulo, formato
    'zroic': ('zRoic', np.round(np.arange(0.20, 2.0001, 0.05), 2), 0.7, 'Corte de zROIC', lambda v: f'{v:.2f}'.replace('.', ',')),
    'growth': ('Growth_Hi', np.round(np.arange(0.065, 0.4001, 0.005), 3), 0.15, 'Corte alto de Growth (mediana de 5 anos do EPS)', lambda v: f'{v:.1%}'.replace('.', ',')),
    'zgrowth': ('zGrowth', np.round(np.arange(0.3, 5.0001, 0.1), 1), 2.93, 'Corte de zGrowth', lambda v: f'{v:.1f}'.replace('.', ',')),
    'ret': ('Return_Hi', np.round(np.arange(0.10, 0.5001, 0.01), 2), 0.20, 'Corte alto de retorno esperado', lambda v: f'{v:.0%}'),
}
pc = lambda x: f'{x:.1%}'.replace('.', ',')
sg = lambda x: f'{x:+.1%}'.replace('.', ',')
nm = lambda x: f'{x:.1f}'.replace('.', ',')


def main(crit):
    key, vals, current, label, fmt = SPEC[crit]
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    base = cb.classify(cls[cls.date.isin(dates)].copy(), False, False, False)
    univ = run_portfolio({d: g.ticker.tolist() for d, g in base[base.cat.notna()].groupby('date')}, adj, dates)[0]
    uq = univ.resample('QE').last().pct_change().dropna()
    rows = []
    for v in vals:
        saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93}); engine.TH[key] = float(v)
        try:
            c = engine.classify(base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore'))
        finally:
            engine.TH.clear(); engine.TH.update(saved)
        c['cat'] = np.where(c.code.isna(), None, c.category)
        r = {'valor': float(v)}
        for k, cat in (('ool', cb.OOL), ('gcgr', cb.GCGR)):
            hold = {d: g.ticker.tolist() for d, g in c[c.cat == cat].groupby('date')}
            nav, _, _, n = run_portfolio(hold, adj, dates)
            q = nav.resample('QE').last().pct_change().dropna(); e = (q - uq.reindex(q.index)).dropna()
            r.update({f'{k}_cagr': stats(nav)['CAGR'], f'{k}_ex': e.mean() * 4, f'{k}_t': e.mean() / e.std() * np.sqrt(len(e)) if e.std() > 0 else np.nan,
                      f'{k}_n': n, f'{k}_vazios': sum(1 for d in dates[:-1] if not hold.get(d))})
        rows.append(r); print(crit, v, flush=True)
    df = pd.DataFrame(rows); df.to_csv(D / f'sweep_{crit}.csv', index=False)
    out = [f'# Varredura: {label} (EUA, 2012–2026)\n',
           f'> ⚠️ **ROIC:** demais critérios na versão atual (ROIC 20%/10%, zROIC 0,7, Growth 15%/6%, zGrowth 2,93, retorno 20%/8%). Valor atual deste critério: {fmt(current)}.\n',
           f'Universo EW: {pc(stats(univ)["CAGR"])} a.a.\n',
           '| Valor | OoL CAGR | OoL vs Universo | OoL t | OoL ações | OoL trim. vazios | GCGR CAGR | GCGR vs Universo | GCGR t | GCGR ações |', '|---|---|---|---|---|---|---|---|---|---|']
    out += [f"| {fmt(r.valor)} | {pc(r.ool_cagr)} | {sg(r.ool_ex)} | {nm(r.ool_t)} | {nm(r.ool_n)} | {int(r.ool_vazios)} | {pc(r.gcgr_cagr)} | {sg(r.gcgr_ex)} | {nm(r.gcgr_t)} | {nm(r.gcgr_n)} |"
            for _, r in df.iterrows()]
    (ROOT / f'sweep_{crit}.md').write_text('\n'.join(out))
    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
    x = df.valor * (100 if crit in ('growth', 'ret') else 1)
    w = (x.iloc[1] - x.iloc[0]) * 0.8
    ax2 = ax.twinx(); ax2.bar(x, df.ool_n, width=w, color='#1f6feb', alpha=0.12); ax2.set_ylabel('Ações em OoL (média, barras)', color='#1f6feb')
    ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
    ax.plot(x, df.ool_cagr * 100, 'o-', color='#1f6feb', lw=2.0, ms=3, label='Opportunity of Lifetime')
    ax.plot(x, df.gcgr_cagr * 100, 'o-', color='#e8590c', lw=2.0, ms=3, label='Good Companies, Great Returns')
    ax.axhline(stats(univ)['CAGR'] * 100, color='#57606a', ls='--', lw=1.4, label='Universo EW (contraprova)')
    ax.axvline(current * (100 if crit in ('growth', 'ret') else 1), color='#8c959f', ls=':', lw=1.4, label=f'Corte atual ({fmt(current)})')
    ax.set_xlabel(label); ax.set_ylabel('Retorno anual (CAGR)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    if crit in ('growth', 'ret'): ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.grid(alpha=.3); ax.legend(fontsize=8, loc='best'); ax.set_title(f'Retorno anual por {label.lower()} (2012–2026)', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / f'sweep_{crit}.png'); plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1])
