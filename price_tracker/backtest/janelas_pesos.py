"""Janelas moveis (1, 3, 5, 8 e 10 anos, passo mensal) contra o S&P 500 para tres ponderacoes de cada classe:
peso igual, valor de mercado e raiz do valor de mercado. Universo point-in-time, ROIC oficial corrigido.
Saidas: backtest/janelas_pesos.md, backtest/janelas_pesos.png. Uso: python3 backtest/janelas_pesos.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, shares, DUAL  # noqa: E402
from backtest import stats  # noqa: E402

YRS = (1, 3, 5, 8, 10)
WN = ['Peso igual', 'Valor de mercado', 'Raiz do valor de mercado']


def main():
    f, dates = bm.base_data()
    adj = bm.load_prices()['adj_close']
    old = bm.vp.classify(f, 'orig', 'B'); new = bm.classify_new(f); hn = bm.holdings_new(new)
    H = {'OoL antigo': (old, old.cat == bm.OOL), 'GCGR antigo': (old, old.cat == bm.GCGR)}
    H.update({k: (new, m) for k, m in hn.items()})
    allrows = pd.concat([c[m][['date', 'ticker', 'eps', 'last_fy', 'price']] for c, m in H.values()]).drop_duplicates(['date', 'ticker'])
    sh = shares(allrows)
    navs, n, dts, _ = bm.load_benchmarks()
    curves = {}
    for k, (c, m) in H.items():
        x = c[m].copy()
        x['mcap'] = [p * sh.get((d, t), np.nan) for d, t, p in zip(x.date, x.ticker, x.price)]
        x['mcap'] = x.mcap.where(x.mcap > 0); x['mcap'] = x.mcap.fillna(x.groupby('date').mcap.transform('median'))
        x['firm'] = x.ticker.map(lambda t: DUAL.get(t, t)); x['mcap'] = x.mcap / x.groupby(['date', 'firm']).ticker.transform('size')
        W = {'Peso igual': lambda g: pd.Series(1.0, index=g.ticker), 'Valor de mercado': lambda g: pd.Series(g.mcap.values, index=g.ticker),
             'Raiz do valor de mercado': lambda g: pd.Series(np.sqrt(g.mcap.values), index=g.ticker)}
        for wn, fn in W.items():
            curves[(k, wn)] = run_weighted({d: fn(g) for d, g in x.groupby('date')}, adj, dates)
        print(k, flush=True)
    M = {kk: v.resample('ME').last() for kk, v in curves.items()}
    Ms = navs['S&P 500'].resample('ME').last(); Mr = navs['S&P 500 equal weight'].resample('ME').last()
    sg = lambda x: f'{x * 100:+.1f}'.replace('.', ',')
    out = ['# Janelas móveis contra o S&P 500: peso igual × valor de mercado × raiz do valor de mercado (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** as classes dependem do ROIC oficial (corrigido em 2026-11-10); a ponderação não usa o ROIC.\n',
           'Para cada janela (passo mensal), compara o retorno acumulado da carteira com o do S&P 500. As janelas se sobrepõem: a contagem mostra a '
           'experiência de quem entrou em cada mês. Cada célula: **% das janelas em que bateu o S&P** · excesso anual mediano (p.p.).\n',
           '**Referência:** S&P 500 equal weight contra o S&P 500: ' + '; '.join(
               f"{y}a {((Mr / Mr.shift(12 * y)) > (Ms / Ms.shift(12 * y)))[(Mr / Mr.shift(12 * y)).notna() & (Ms / Ms.shift(12 * y)).notna()].mean():.0%}" for y in YRS) + '.\n']
    hdr = '| Classe | Ponderação | Retorno anual | ' + ' | '.join(f'{y} ano{"s" if y > 1 else ""}' for y in YRS) + ' |'
    out += ['## Todas as classes\n', hdr, '|---|---|---|' + '---|' * len(YRS)]
    for k in H:
        for wn in WN:
            Mn = M[(k, wn)]; cells = []
            for y in YRS:
                a = (Mn / Mn.shift(12 * y)).dropna(); b = (Ms / Ms.shift(12 * y)).reindex(a.index)
                ex = a ** (1 / y) - b ** (1 / y)
                cells.append(f'**{(a > b).mean():.0%}** · {sg(ex.median())}')
            bold = '**' if wn != 'Peso igual' and k in ('OoL novo', 'GCGR novo') else ''
            out.append(f"| {k} | {wn} | {stats(curves[(k, wn)])['CAGR']:.1%} | ".replace('.', ',') + ' | '.join(cells) + ' |')
    out += ['', '## Comparativos obrigatórios (peso igual)\n'] + bm.bench_table(navs, n)
    (ROOT / 'janelas_pesos.md').write_text('\n'.join(out)); print('\n'.join(out))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(15, 9), dpi=130)
    col = {'Peso igual': '#1f6feb', 'Valor de mercado': '#2da44e', 'Raiz do valor de mercado': '#bf8700'}
    for ax, k in zip(axs.ravel(), ('OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)')):
        xs = np.arange(len(YRS))
        for i, wn in enumerate(WN):
            Mn = M[(k, wn)]
            v = [((Mn / Mn.shift(12 * y)).dropna() > (Ms / Ms.shift(12 * y)).reindex((Mn / Mn.shift(12 * y)).dropna().index)).mean() * 100 for y in YRS]
            ax.bar(xs + (i - 1) * .27, v, width=.27, color=col[wn], label=wn)
        vr = [((Mr / Mr.shift(12 * y)) > (Ms / Ms.shift(12 * y)))[(Mr / Mr.shift(12 * y)).notna() & (Ms / Ms.shift(12 * y)).notna()].mean() * 100 for y in YRS]
        ax.plot(xs, vr, color='#8c959f', marker='o', ls=':', label='S&P 500 equal weight')
        ax.axhline(50, color='black', lw=.8); ax.set_xticks(xs); ax.set_xticklabels([f'{y} ano{"s" if y > 1 else ""}' for y in YRS])
        ax.set_ylim(0, 105); ax.set_ylabel('% das janelas acima do S&P 500'); ax.set_title(k, fontsize=10); ax.grid(alpha=.3, axis='y'); ax.legend(fontsize=7)
    fig.suptitle('Janelas móveis: % das vezes em que a carteira bateu o S&P 500, por ponderação', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(ROOT / 'janelas_pesos.png'); plt.close(fig)


if __name__ == '__main__':
    main()
