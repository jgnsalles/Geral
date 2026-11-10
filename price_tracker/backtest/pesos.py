"""Quebrando o equal weight. Para cada classe, tres ponderacoes rebalanceadas a cada trimestre:
  base = peso igual (atual);
  cenario 1 = valor de mercado, como o S&P 500 (peso = valor de mercado / soma da classe);
  cenario 2 = retorno esperado do modelo (peso = retorno esperado / soma dos retornos esperados da classe).
Valor de mercado point-in-time = preco x acoes; acoes = lucro liquido / EPS diluido do ultimo exercicio arquivado
(sem lucro valido, usa as acoes da ultima data em que deu para calcular; sem nenhuma, a mediana da classe).
ETFs nao mudam. Universo point-in-time, ROIC oficial corrigido, sem custos (como as demais curvas).
Saidas: backtest/pesos.md, backtest/pesos.png. Uso: python3 backtest/pesos.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from backtest import load_pit, asof, stats  # noqa: E402


DUAL = {'GOOG': 'GOOGL', 'FOX': 'FOXA', 'NWS': 'NWSA', 'UA': 'UAA', 'BRK-A': 'BRK-B', 'DISCK': 'DISCA', 'LEN-B': 'LEN'}


def run_weighted(weights, adj, dates):
    """weights: {data: Series(ticker -> peso)}; NAV diario rebalanceado nas datas."""
    v, out = 1.0, []
    for i, d in enumerate(dates[:-1]):
        nxt = dates[i + 1]; seg = adj.loc[d:nxt]
        w = weights.get(d, pd.Series(dtype=float))
        w = w[[t for t in w.index if t in adj and np.isfinite(adj.at[d, t])]]
        if w.empty or w.sum() <= 0:
            path = pd.Series(1.0, index=seg.index)
        else:
            w = w / w.sum(); rel = seg[w.index].ffill().div(seg[w.index].iloc[0]); path = (rel * w).sum(axis=1)
        p = v * path; out.append(p.iloc[:-1] if i < len(dates) - 2 else p); v = p.iloc[-1]
    return pd.concat(out)


def shares(rows):
    """acoes = lucro liquido / EPS (base de acoes de hoje, igual ao preco ajustado por desdobramentos)."""
    cache, sh = {}, {}
    for r in rows.itertuples():
        if r.ticker not in cache: cache[r.ticker] = load_pit(r.ticker)
        ni, _ = asof(cache[r.ticker].get('net_income', []), r.date)
        y = int(r.last_fy); n_ = ni[y][0] if y in ni else np.nan
        s = n_ / r.eps if np.isfinite(n_) and r.eps and abs(r.eps) > 0.01 and np.sign(n_) == np.sign(r.eps) else np.nan
        sh[(r.date, r.ticker)] = s
    s = pd.Series(sh)
    s = s.groupby(level=1).transform(lambda x: x.sort_index(level=0).ffill().bfill())
    return s


def main():
    f, dates = bm.base_data()
    adj = bm.load_prices()['adj_close']
    old = bm.vp.classify(f, 'orig', 'B'); new = bm.classify_new(f); hn = bm.holdings_new(new)
    H = {'OoL antigo': (old, old.cat == bm.OOL), 'GCGR antigo': (old, old.cat == bm.GCGR)}
    H.update({k: (new, m) for k, m in hn.items()})
    allrows = pd.concat([c[m][['date', 'ticker', 'eps', 'last_fy', 'price']] for c, m in H.values()]).drop_duplicates(['date', 'ticker'])
    sh = shares(allrows)
    navs, n, dts, _ = bm.load_benchmarks()
    S = stats(navs['S&P 500'])['CAGR']; Ms = navs['S&P 500'].resample('ME').last()
    pc = lambda x: f'{x:.1%}'.replace('.', ',')
    pp = lambda x: f'{x * 100:+.1f}'.replace('.', ',') + ' p.p.'
    res, curves, conc = [], {}, []
    for k, (c, m) in H.items():
        x = c[m].copy()
        x['mcap'] = [x_p * sh.get((d, t), np.nan) for d, t, x_p in zip(x.date, x.ticker, x.price)]
        x['mcap'] = x.mcap.where(x.mcap > 0); x['mcap'] = x.mcap.fillna(x.groupby('date').mcap.transform('median'))
        # duas classes de acao da mesma empresa (ex.: GOOG e GOOGL): lucro / EPS da a empresa inteira em cada uma; divide entre as classes presentes
        x['firm'] = x.ticker.map(lambda t: DUAL.get(t, t)); x['mcap'] = x.mcap / x.groupby(['date', 'firm']).ticker.transform('size')
        W = {'Peso igual (base)': {d: pd.Series(1.0, index=g.ticker) for d, g in x.groupby('date')},
             'Cenário 1: valor de mercado': {d: pd.Series(g.mcap.values, index=g.ticker) for d, g in x.groupby('date')},
             'Cenário 2: retorno esperado': {d: pd.Series(g.ret.clip(lower=0).values, index=g.ticker) for d, g in x.groupby('date')}}
        r = {'Carteira': k}
        for wn, w in W.items():
            nav = run_weighted(w, adj, dates); st = stats(nav); Mn = nav.resample('ME').last()
            r[wn] = (st['CAGR'], st['MaxDD'], ((Mn / Mn.shift(60)) > (Ms / Ms.shift(60))).dropna().mean())
            curves[(k, wn)] = nav
            mx = np.median([s.max() / s.sum() for s in w.values() if s.sum() > 0])
            top5 = np.median([s.nlargest(5).sum() / s.sum() for s in w.values() if s.sum() > 0])
            conc.append((k, wn, mx, top5))
        res.append(r)
    out = ['# Quebrando o peso igual: valor de mercado e retorno esperado (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** o retorno esperado do cenário 2 depende do ROIC (via P/E justo); qualquer erro nele muda os pesos.\n',
           '**Base** = peso igual. **Cenário 1** = peso pelo valor de mercado, como o S&P 500 (valor de mercado = preço × ações; ações = lucro líquido ÷ EPS do '
           'último balanço). **Cenário 2** = peso pelo retorno esperado do modelo (retorno esperado da ação ÷ soma da classe). Rebalanceamento trimestral, '
           'sem custos. ETFs não mudam. Empresas com duas classes de ação (GOOG/GOOGL etc.) têm o valor de mercado dividido entre as classes.\n',
           f'Referências: S&P 500 {pc(S)} a.a.; S&P 500 equal weight {pc(stats(navs["S&P 500 equal weight"])["CAGR"])} a.a.\n',
           '## Retorno anual e ganho/perda contra o peso igual\n',
           '| Carteira | Peso igual (base) | Cenário 1: valor de mercado | Ganho/perda | Cenário 2: retorno esperado | Ganho/perda |', '|---|---|---|---|---|---|']
    for r in res:
        b, c1, c2 = r['Peso igual (base)'], r['Cenário 1: valor de mercado'], r['Cenário 2: retorno esperado']
        out.append(f"| {r['Carteira']} | {pc(b[0])} | {pc(c1[0])} | **{pp(c1[0] - b[0])}** | {pc(c2[0])} | **{pp(c2[0] - b[0])}** |")
    out += ['', '## Pior queda e janelas de 5 anos acima do S&P\n', '| Carteira | Base: pior queda | C1: pior queda | C2: pior queda | Base: janelas 5a | C1: janelas 5a | C2: janelas 5a |',
            '|---|---|---|---|---|---|---|']
    for r in res:
        b, c1, c2 = r['Peso igual (base)'], r['Cenário 1: valor de mercado'], r['Cenário 2: retorno esperado']
        out.append(f"| {r['Carteira']} | {pc(b[1])} | {pc(c1[1])} | {pc(c2[1])} | {b[2]:.0%} | {c1[2]:.0%} | {c2[2]:.0%} |")
    out += ['', '## Concentração (mediana dos trimestres)\n', '| Carteira | Ponderação | Maior peso | 5 maiores pesos |', '|---|---|---|---|']
    for k, wn, mx, t5 in conc:
        out.append(f'| {k} | {wn} | {mx:.0%} | {t5:.0%} |')
    out += ['', '## Comparativos obrigatórios (peso igual)\n'] + bm.bench_table(navs, n)
    (ROOT / 'pesos.md').write_text('\n'.join(out)); print('\n'.join(out))
    plot = {k: navs[k] for k in ('S&P 500', 'S&P 500 equal weight')}
    for k in ('OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)'):
        for wn, tag in (('Peso igual (base)', 'peso igual'), ('Cenário 1: valor de mercado', 'valor de mercado'), ('Cenário 2: retorno esperado', 'retorno esperado')):
            plot[f'{k} — {tag}'] = curves[(k, wn)]
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, axs = plt.subplots(2, 2, figsize=(15, 10), dpi=130)
    for ax, k in zip(axs.ravel(), ('OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)')):
        for nm, col, ls in (('S&P 500', '#000', '--'), ('S&P 500 equal weight', '#8c959f', ':')):
            ax.plot(navs[nm].index, (navs[nm] - 1) * 100, color=col, ls=ls, lw=1.5, label=f'{nm} ({pc(stats(navs[nm])["CAGR"])})')
        for wn, col in (('Peso igual (base)', '#1f6feb'), ('Cenário 1: valor de mercado', '#2da44e'), ('Cenário 2: retorno esperado', '#cf222e')):
            s = curves[(k, wn)]; ax.plot(s.index, (s - 1) * 100, color=col, lw=2, label=f'{wn} ({pc(stats(s)["CAGR"])})')
        ax.set_title(k, fontsize=10); ax.grid(alpha=.3); ax.legend(fontsize=7, loc='upper left')
        ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.')))
    fig.suptitle('Peso igual × valor de mercado × retorno esperado — retorno total acumulado', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .97)); fig.savefig(ROOT / 'pesos.png'); plt.close(fig)


if __name__ == '__main__':
    main()
