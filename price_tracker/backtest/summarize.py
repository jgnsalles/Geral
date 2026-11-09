"""Gera tabelas (markdown) e graficos do backtest por classe. Uso: python3 backtest/summarize.py"""
import pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

D = pathlib.Path(__file__).parent / 'data'
OUT = pathlib.Path(__file__).parent
CLASSES = ['Opportunity of Lifetime', 'Good Companies, Great Returns', 'Excellent but Fair',
           'Good but Margin of Safety Required', 'Cheap Slow Compounder', 'Interesting but Requires Attention',
           'Cheap but Aggressive', 'Expensive for what you get', 'Investable but Not Good', 'Expensive', 'Do not Waste Time']
REF = ['Universo EW', 'SPY', 'QQQ', 'RSP']
pct = lambda x: f'{x:.1%}'.replace('.', ',') if pd.notna(x) else '—'
num = lambda x, n=1: f'{x:.{n}f}'.replace('.', ',') if pd.notna(x) else '—'


def cagr(s):
    s = s.dropna(); yrs = (s.index[-1] - s.index[0]).days / 365.25
    return (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1


def table(cut):
    nav = pd.read_csv(D / f'nav_{cut}.csv', index_col=0, parse_dates=True)
    st = pd.read_csv(D / f'stats_{cut}.csv').set_index('Carteira')
    q = nav.resample('QE').last().pct_change().dropna(how='all')
    lines = ['| Carteira | CAGR | CAGR liq. | Vol | Max DD | vs Universo EW | t | 2012–2019 | 2020–2026 | N médio | Trim. em caixa |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in CLASSES + REF:
        if c not in st.index: continue
        r = st.loc[c]
        if c in REF and c != 'Universo EW':
            ex = t = None
        else:
            e = (q[c] - q['Universo EW']).dropna(); ex = e.mean() * 4; t = e.mean() / e.std() * np.sqrt(len(e)) if c != 'Universo EW' else None
        name = f'**{c}**' if c in CLASSES else c + (' (contraprova)' if c == 'Universo EW' else '')
        lines.append(f"| {name} | {pct(r.CAGR)} | {pct(r['CAGR liq.'])} | {pct(r.Vol)} | {pct(r.MaxDD)} | "
                     f"{'—' if ex is None or c == 'Universo EW' else ('+' if ex > 0 else '') + pct(ex)} | {num(t) if t is not None else '—'} | "
                     f"{pct(cagr(nav[c].loc['2012':'2019']))} | {pct(cagr(nav[c].loc['2020':'2026']))} | "
                     f"{num(r['N medio'], 0)} | {int(r['Trim. vazios'])} |")
    return '\n'.join(lines)


def chart(cut):
    nav = pd.read_csv(D / f'nav_{cut}.csv', index_col=0, parse_dates=True)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), dpi=130, sharey=True)
    colors = plt.cm.tab10.colors
    groups = [CLASSES[:6], CLASSES[6:]]
    for ax, grp in zip(axes, groups):
        for i, c in enumerate(grp):
            lw = 2.8 if c == 'Opportunity of Lifetime' else 1.6
            ax.plot(nav.index, nav[c], color=colors[i], lw=lw, label=f'{c} ({nav[c].iloc[-1]:.1f}x)')
        for c, col in (('Universo EW', '#57606a'), ('SPY', '#000000'), ('QQQ', '#e377c2')):
            ax.plot(nav.index, nav[c], color=col, lw=1.6, ls='--', label=f'{c} ({nav[c].iloc[-1]:.1f}x)')
        ax.set_yscale('log'); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    axes[0].set_ylabel('Crescimento de 1 (escala log)')
    fig.suptitle(f'Uma carteira por classe: equal weight, rebalanceamento trimestral, 2012–2026 (corte zGrowth {cut[2:].replace(".", ",")})')
    fig.tight_layout(); fig.savefig(OUT / f'classes_{cut}.png'); plt.close(fig)


if __name__ == '__main__':
    for cut in ('zg2.93', 'zg0.9'):
        chart(cut)
        print(f'\n### Corte zGrowth {cut[2:]}\n'); print(table(cut))
