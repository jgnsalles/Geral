"""Criterios de estabilidade (ROIC e crescimento): variantes e ausencia do criterio.
Universo point-in-time, ROIC oficial, estrutura do esboco (OoL a partir de ROIC 12%, ROIC medio 10-12%).
Saidas: backtest/stability_tests.md, backtest/stability_tests.png
Uso: python3 backtest/stability_tests.py"""
import sys, itertools, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
RY = [f'ry{i}' for i in range(1, 7)]; GY = [f'gy{i}' for i in range(1, 6)]
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
n1 = lambda x: '—' if pd.isna(x) else f'{x:.0f}'


def roic_rules(x):
    r = x[RY]; n = r.notna().sum(axis=1)
    med = r.median(axis=1); q75, q25 = r.quantile(.75, axis=1), r.quantile(.25, axis=1)
    last2 = r[['ry5', 'ry6']].mean(axis=1)
    return {
        'R0 atual (zROIC < 0,7)': x.zroic < 0.7,
        'R1 sem critério': pd.Series(True, index=x.index),
        'R2 zROIC < 1,0': x.zroic < 1.0,
        'R3 zROIC < 1,5': x.zroic < 1.5,
        'R4 ROIC ≥ 8,5% em todos os anos menos 1': ((r >= 0.085).sum(axis=1) >= n - 1) & (n >= 4),
        'R5 ROIC nunca negativo': (r.min(axis=1) > 0) & (n >= 4),
        'R6 dispersão robusta (IQR ÷ mediana < 0,7)': ((q75 - q25) / med < 0.7) & (med > 0),
        'R7 zROIC < 0,7 ou 2 últimos anos ≥ mediana': (x.zroic < 0.7) | (last2 >= med),
    }


def growth_rules(x):
    g = x[GY]
    return {'G0 atual (zGrowth < 2,93)': x.zgrowth < 2.93, 'G1 sem critério': pd.Series(True, index=x.index),
            'G2 no máx. 1 ano de queda de lucro em 5': (g < 0).sum(axis=1) <= 1}


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member]
    adj = load_prices()['adj_close']
    base = vp.classify(f, 'sketch', 'B')
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    base['rq'] = [fwd.at[d, t] for d, t in zip(base.date, base.ticker)]
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; Ms = spy.resample('ME').last()
    univ = run_portfolio({d: g.ticker.tolist() for d, g in base[base.cat.notna()].groupby('date')}, adj, dates)[0]
    uq = base[base.cat.notna() & (base.date < dates[-1])].groupby('date').rq.mean()
    rr, gr = roic_rules(base), growth_rules(base)
    rows = []
    for (rn, rm), (gn, gm) in itertools.product(rr.items(), gr.items()):
        x = base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore').copy()
        x['zroic'] = np.where(rm, 0.0, 9.0); x['zgrowth'] = np.where(gm, 0.0, 9.0)
        saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'zRoic': 0.7, **vp.PARAMS['sketch']})
        try:
            c = engine.classify(x)
        finally:
            engine.TH.clear(); engine.TH.update(saved)
        r = {'roic': rn, 'growth': gn}
        for k, cat in (('ool', OOL), ('gcgr', GCGR)):
            sel = c[c.category == cat]
            nav = run_portfolio({d: g.ticker.tolist() for d, g in sel.groupby('date')}, adj, dates)[0]
            Mn = nav.resample('ME').last(); w = ((Mn / Mn.shift(60)) > (Ms / Ms.shift(60))).dropna()
            pos = sel[sel.date < dates[-1]]
            r.update({f'{k}_cagr': stats(nav)['CAGR'], f'{k}_n': sel.groupby('date').size().mean(), f'{k}_w5': w.mean(),
                      f'{k}_pos': (pos.rq - pos.date.map(uq)).mean() * 4})
        rows.append(r); print(rn, gn, flush=True)
    df = pd.DataFrame(rows); df.to_csv(D / 'stability_tests.csv', index=False)
    S, U = stats(spy)['CAGR'], stats(univ)['CAGR']
    out = ['# Critérios de estabilidade: variantes e ausência do critério (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A). Estrutura do esboço: OoL a partir de ROIC 12%; ROIC médio 10–12%.\n',
           f'S&P 500 (SPY): {pc(S)} a.a. · Universo EW: {pc(U)} a.a. "Posições vs universo" = excesso médio por posição (ação × trimestre). '
           '"Janelas 5a > S&P" = % das janelas móveis de 5 anos em que a carteira bateu o S&P 500.\n',
           '| Critério de ROIC | Critério de crescimento | OoL: retorno a.a. | OoL vs S&P | OoL: posições vs universo | OoL: ações | OoL: janelas 5a > S&P | '
           'GCGR: retorno a.a. | GCGR vs S&P | GCGR: ações | OoL − GCGR |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for _, r in df.iterrows():
        out.append(f"| {r.roic} | {r.growth} | {pc(r.ool_cagr)} | {sg(r.ool_cagr - S)} | {sg(r.ool_pos)} | {n1(r.ool_n)} | {pc(r.ool_w5)} | "
                   f"{pc(r.gcgr_cagr)} | {sg(r.gcgr_cagr - S)} | {n1(r.gcgr_n)} | **{sg(r.ool_cagr - r.gcgr_cagr)}** |")
    # analise: barradas por zROIC, ultimos 2 anos vs mediana
    x = base.copy(); r = x[RY]; x['last2'] = r[['ry5', 'ry6']].mean(axis=1); x['med'] = r.median(axis=1)
    barred = x[(x.cat == GCGR) & (x.code.str[3] == 'U') & (x.date < dates[-1])]
    nm = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'name']],
                    pd.read_csv(D / 'universe_pit_extra.csv').rename(columns={'sec_name': 'name'})[['ticker', 'name']]]).drop_duplicates('ticker').set_index('ticker')['name']
    out += ['', '## Barradas por ROIC instável (zROIC ≥ 0,7): 2 últimos anos acima ou abaixo da mediana da janela\n',
            '| Grupo | Posições | Empresas | Retorno a.a. | vs Universo | % negativas | ROIC (mediana) | Exemplos (mais frequentes) |', '|---|---|---|---|---|---|---|---|']
    for lab, m in (('2 últimos anos ≥ mediana (melhorando)', barred.last2 >= barred.med), ('2 últimos anos < mediana (piorando)', barred.last2 < barred.med)):
        y = barred[m]; ex = (y.rq - y.date.map(uq)).mean() * 4
        top = ', '.join(f'{t} ({nm.get(t, t)})' for t in y.ticker.value_counts().head(8).index)
        out.append(f'| {lab} | {len(y)} | {y.ticker.nunique()} | {pc(y.rq.mean() * 4)} | **{sg(ex)}** | {pc((y.rq < 0).mean())} | {pc(y.roic.median())} | {top} |')
    (ROOT / 'stability_tests.md').write_text('\n'.join(out))
    # grafico
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=140)
    labels = list(rr); xs = np.arange(len(labels))
    for i, (gn, col) in enumerate(zip(gr, ['#1f6feb', '#2da44e', '#8250df'])):
        d = df[df.growth == gn].set_index('roic').reindex(labels)
        ax.bar(xs + (i - 1) * 0.27, d.ool_cagr * 100, width=0.27, color=col, label=f'OoL — {gn}')
        ax.scatter(xs + (i - 1) * 0.27, d.gcgr_cagr * 100, color='#e8590c', marker='D', s=18, zorder=3, label='GCGR' if i == 0 else None)
    ax.axhline(S * 100, color='black', ls='--', lw=1.4, label=f'S&P 500 ({pc(S)})'); ax.axhline(U * 100, color='#57606a', ls=':', lw=1.4, label=f'Universo EW ({pc(U)})')
    ax.set_xticks(xs); ax.set_xticklabels([l.split(' ', 1)[1] for l in labels], rotation=20, ha='right', fontsize=8)
    ax.set_ylim(min(df.ool_cagr.min(), df.gcgr_cagr.min(), U) * 100 - 1, max(df.ool_cagr.max(), df.gcgr_cagr.max(), S) * 100 + 1)
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%')); ax.grid(alpha=.3, axis='y'); ax.legend(fontsize=7, ncol=3)
    ax.set_title('Retorno anual da OoL (barras) e de GCGR (losangos) por critério de estabilidade — universo point-in-time', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'stability_tests.png'); plt.close(fig)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
