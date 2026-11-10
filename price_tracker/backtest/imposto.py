"""Estrategias com imposto de 15% sobre o ganho de capital realizado nas vendas (vida real de pessoa fisica).
ETFs (S&P 500 e S&P 500 equal weight) ficam sem imposto: o fundo nao paga IR nas trocas internas.
Regras da simulacao:
  - Em cada rebalanceamento trimestral, venda total (saiu da classe) ou parcial (volta ao peso igual) realiza ganho ou perda
    pelo custo medio da posicao. Compras aumentam o custo medio.
  - IR = 15% x (ganhos - perdas do trimestre - prejuizo acumulado a compensar), pago na hora com dinheiro da propria carteira.
    Prejuizo sem uso fica acumulado para compensar ganhos futuros.
  - Dividendos reinvestidos sem imposto (o preco ajustado ja os inclui) e sem custo de corretagem, como nas demais curvas.
  - Coluna "vendendo tudo no fim": paga 15% sobre o ganho ainda nao realizado no ultimo dia (inclusive nos ETFs, para comparar).
Saidas: backtest/imposto.md, backtest/imposto.png. Uso: python3 backtest/imposto.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from backtest import stats  # noqa: E402

RATE = 0.15


def run_tax(holdings, adj, dates, rate=RATE):
    """NAV diario com IR sobre ganho realizado. Devolve (nav, ir_pago_total, ganho_nao_realizado_final, prejuizo_a_compensar_final)."""
    val, basis, carry, paid = {}, {}, 0.0, 0.0
    navs = []
    total = 1.0
    for i, d in enumerate(dates[:-1]):
        nxt = dates[i + 1]
        tks = [t for t in holdings.get(d, []) if t in adj and np.isfinite(adj.at[d, t])]
        V = sum(val.values()) + (total if not val else 0.0)
        cash = total if not val else 0.0
        target = V / len(tks) if tks else 0.0
        for _ in range(2):  # o IR reduz o valor a reinvestir; duas passadas bastam
            gains = 0.0
            for t, v in val.items():
                b = basis[t]
                if t not in tks: gains += v - b
                elif v > target: gains += (v - target) * (1 - b / v) if v > 0 else 0.0
            net = gains + carry
            tax = rate * net if net > 0 else 0.0
            target = (V - tax) / len(tks) if tks else 0.0
        new_val, new_basis = {}, {}
        for t in tks:
            v, b = val.get(t, 0.0), basis.get(t, 0.0)
            if v > target and v > 0: new_basis[t] = b * target / v
            else: new_basis[t] = b + (target - v)
            new_val[t] = target
        carry = net if net < 0 else 0.0
        paid += tax
        if not tks:  # sem acoes: fica em caixa
            total = V - tax; val, basis = {}, {}
            seg = adj.loc[d:nxt]; path = pd.Series(total, index=seg.index)
        else:
            val, basis = new_val, new_basis
            seg = adj.loc[d:nxt, tks].ffill()
            rel = seg.div(seg.iloc[0])
            path = (rel * pd.Series(val)).sum(axis=1)
            last = rel.iloc[-1]
            val = {t: val[t] * last[t] for t in tks}
            total = sum(val.values())
        navs.append(path.iloc[:-1] if i < len(dates) - 2 else path)
    unreal = sum(v - basis[t] for t, v in val.items()) if val else 0.0
    return pd.concat(navs), paid, unreal, carry


def main():
    f, dates = bm.base_data()
    adj = bm.load_prices()['adj_close']
    old = bm.vp.classify(f, 'orig', 'B'); new = bm.classify_new(f); hn = bm.holdings_new(new)
    H = {'OoL antigo': (old, old.cat == bm.OOL), 'GCGR antigo': (old, old.cat == bm.GCGR)}
    H.update({k: (new, m) for k, m in hn.items()})
    navs, n, dts, _ = bm.load_benchmarks()
    rows, taxed = [], {}
    for k, (c, m) in H.items():
        hold = {d: g.ticker.tolist() for d, g in c[m].groupby('date')}
        nav_t, paid, unreal, carry = run_tax(hold, adj, dates)
        taxed[k] = nav_t
        end = nav_t.iloc[-1]; liq = end - RATE * max(unreal + carry, 0)
        rows.append((k, navs[k], nav_t, paid, liq))
    yrs = (dates[-1] - dates[0]).days / 365.25
    cg = lambda x: x ** (1 / yrs) - 1
    pc = lambda x: f'{x:.1%}'.replace('.', ',')
    out = ['# Estratégias com 15% de imposto sobre o ganho de capital (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** as classes dependem do ROIC oficial (corrigido em 2026-11-10); o imposto não muda isso.\n',
           '**Regras:** a cada rebalanceamento trimestral, toda venda (ação que saiu da classe ou redução para voltar ao peso igual) realiza ganho ou perda '
           'pelo custo médio. IR = 15% do ganho líquido do trimestre, já compensando perdas (prejuízo sem uso fica guardado para compensar depois), pago na hora '
           'com dinheiro da carteira. Os ETFs (S&P 500 e equal weight) **não mudam**: o fundo não paga IR nas trocas internas. Dividendos reinvestidos sem imposto, '
           'sem corretagem, como nas demais curvas. "Vendendo tudo no fim" = paga também 15% sobre o ganho ainda não realizado no último dia; nos ETFs, '
           'isso é o único imposto.\n',
           '| Carteira | Sem imposto: retorno anual | **Com IR nas vendas: retorno anual** | Custo do IR (p.p. a.a.) | IR pago (% do capital inicial) | '
           'Vendendo tudo no fim: retorno anual | Retorno total com IR (sem vender no fim) |', '|---|---|---|---|---|---|---|']
    for b in ('S&P 500', 'S&P 500 equal weight'):
        s = navs[b]; e_ = s.iloc[-1]
        out.append(f'| {b} | {pc(stats(s)["CAGR"])} | {pc(stats(s)["CAGR"])} (ETF, sem IR interno) | 0,0 | 0% | {pc(cg(e_ - RATE * (e_ - 1)))} | {pc(e_ - 1)} |')
    for k, g, t, paid, liq in rows:
        a, b_ = stats(g)['CAGR'], stats(t)['CAGR']
        bold = '**' if k in ('OoL novo', 'GCGR novo') else ''
        out.append(f'| {bold}{k}{bold} | {pc(a)} | **{pc(b_)}** | {(b_ - a) * 100:+.1f}'.replace('.', ',') + f' | {paid:.0%} | {pc(cg(liq))} | {pc(t.iloc[-1] - 1)} |')
    S = stats(navs['S&P 500'])['CAGR']
    out += ['', '### Contra o S&P 500 (diferença de retorno anual)\n', '| Carteira | Sem imposto | Com IR nas vendas | Vendendo tudo no fim (ETF também paga) |', '|---|---|---|---|']
    s_liq = cg(navs['S&P 500'].iloc[-1] - RATE * (navs['S&P 500'].iloc[-1] - 1))
    for k, g, t, paid, liq in rows:
        fp = lambda x: f'{x * 100:+.1f}'.replace('.', ',') + ' p.p.'
        out.append(f"| {k} | {fp(stats(g)['CAGR'] - S)} | {fp(stats(t)['CAGR'] - S)} | {fp(cg(liq) - s_liq)} |")
    (ROOT / 'imposto.md').write_text('\n'.join(out)); print('\n'.join(out))
    plot = {k: v for k, v in navs.items() if k in ('S&P 500', 'S&P 500 equal weight')}
    for k, g, t, *_ in rows: plot[f'{k} (com IR)'] = t
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    for k, s in plot.items():
        base = k.replace(' (com IR)', '')
        col, ls, lw = bm.STYLE.get(base, ('#000', '-', 1.5))
        ax.plot(s.index, (s - 1) * 100, color=col, ls=ls, lw=lw, label=f'{k} (' + pc(stats(s)['CAGR']) + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Estratégias com 15% de IR sobre ganho realizado nas vendas × ETFs (sem IR interno) — retorno total acumulado', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'imposto.png'); plt.close(fig)


if __name__ == '__main__':
    main()
