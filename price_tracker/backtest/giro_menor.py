"""Versao de giro menor pre-registrada (2026-11-14): fica na carteira enquanto estiver no top B (B = 30; 25 e 40 como sensibilidade).
Saida: backtest/giro_menor.md e .png. Uso: python3 backtest/giro_menor.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'mundo'))
import backtest_mundo as bmu  # noqa: E402
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402

RATE = 0.15


def select(el, B):
    held, W = [], {}
    for d, g in el.groupby('date'):
        g = g.sort_values(['ret', 'roic'], ascending=False).drop_duplicates('ticker').reset_index(drop=True)
        rank = {t: i + 1 for i, t in enumerate(g.ticker)}
        keep = [t for t in held if rank.get(t, 999) <= B]
        for t in g.ticker:
            if len(keep) >= 20: break
            if t not in keep: keep.append(t)
        held = keep
        m = g.set_index('ticker').mcap.reindex(keep)
        W[d] = top_n.cap(pd.Series(np.sqrt(m.values), index=keep), .10)
    return W


def tax_weighted(W, adj, dates, rate=RATE):
    """IR sobre ganho realizado com pesos-alvo (generaliza imposto.run_tax para pesos). Devolve nav."""
    val, basis, carry, total, navs = {}, {}, 0.0, 1.0, []
    for i, d in enumerate(dates[:-1]):
        nxt = dates[i + 1]
        w = W.get(d, pd.Series(dtype=float)); w = w[[t for t in w.index if t in adj and np.isfinite(adj.at[d, t])]]
        w = w / w.sum() if len(w) else w
        V = sum(val.values()) if val else total
        tgt = {t: V * w[t] for t in w.index}
        for _ in range(2):
            gains = 0.0
            for t, v in val.items():
                b = basis[t]; tg = tgt.get(t, 0.0)
                if v > tg and v > 0: gains += (v - tg) * (1 - b / v)
            net = gains + carry; tax = rate * net if net > 0 else 0.0
            tgt = {t: (V - tax) * w[t] for t in w.index}
        carry = net if net < 0 else 0.0
        nb = {}
        for t in w.index:
            v, b, tg = val.get(t, 0.0), basis.get(t, 0.0), tgt[t]
            nb[t] = b * tg / v if v > tg and v > 0 else b + (tg - v)
        if not len(w):
            total = V - tax; val, basis = {}, {}; seg = adj.loc[d:nxt]; path = pd.Series(total, index=seg.index)
        else:
            val, basis = dict(tgt), nb
            seg = adj.loc[d:nxt, list(w.index)].ffill(); rel = seg.div(seg.iloc[0])
            path = (rel * pd.Series(val)).sum(axis=1); last = rel.iloc[-1]
            val = {t: val[t] * last[t] for t in w.index}; total = sum(val.values())
        navs.append(path.iloc[:-1] if i < len(dates) - 2 else path)
    return pd.concat(navs)


def turnover(W):
    ds = sorted(W); tr, gi = [], []
    for a, b in zip(ds[:-1], ds[1:]):
        A, Bs = set(W[a].index), set(W[b].index); tr.append((b.year, len(Bs - A) + len(A - Bs)))
        dw = W[b].reindex(A | Bs, fill_value=0) - W[a].reindex(A | Bs, fill_value=0); gi.append((b.year, dw.abs().sum() / 2))
    t = pd.DataFrame(tr, columns=['y', 'n']).groupby('y').agg(n=('n', 'sum'), k=('n', 'size')); g = pd.DataFrame(gi, columns=['y', 'g']).groupby('y').g.sum()
    ok = t.k >= 4
    held = []
    for tk in set().union(*[set(w.index) for w in W.values()]):
        run = 0
        for d in ds:
            if tk in W[d].index: run += 1
            elif run: held.append(run); run = 0
        if run: held.append(run)
    return t.n[ok].mean(), g[ok].mean(), np.mean(held) * 3


def main():
    import yfinance as yf
    sp, adj_us, dates_us = bmu.us_sp()
    fx = yf.download('BRL=X', start='2010-01-01', progress=False, auto_adjust=True)['Close'].squeeze(); fx.index = pd.to_datetime(fx.index).tz_localize(None)
    br, _ = bmu.brasil(fx)
    adj_br = pd.read_csv(ROOT.parent / 'brasil' / 'data' / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    out = ['# Versão de giro menor: fica enquanto estiver no top 30 (pré-registrada em 2026-11-14)\n',
           '> ⚠️ **O ROIC pode estar errado** — ele define quem é elegível e a ordem do ranking (logo, quem fica e quem sai).\n',
           'Igual à candidata (20 ações, P/L ≥ 4, raiz do valor de mercado com teto de 10%, trimestral), mas a ação só sai se cair para fora do top B '
           'ou deixar de ser elegível. IR de 15% sobre ganho realizado (prejuízo compensa ganhos futuros), sem custos de corretagem.\n']
    US_navs = {}
    for lab, x, adj, curr, bench in (('EUA', sp, adj_us, 'dólares', ('SPY', 'S&P 500')), ('Brasil', br, adj_br, 'reais', ('BOVA11.SA', 'Ibovespa'))):
        el = x[x.elig.fillna(False).astype(bool) & x.ret.notna() & x.mcap.notna()]
        dates = sorted(el.date.unique()); dates = [pd.Timestamp(d) for d in dates]
        rows = []
        for B, nm in ((20, 'Candidata atual (sai do top 20)'), (25, 'Fica no top 25'), (30, 'Fica no top 30 (produto testado)'), (40, 'Fica no top 40')):
            W = select(el, B)
            nav = run_weighted(W, adj, dates); navt = tax_weighted(W, adj, dates)
            n, g, h = turnover(W)
            rows.append((nm, stats(nav)['CAGR'], stats(navt)['CAGR'], stats(nav)['MaxDD'], n, g, h))
            if lab == 'EUA': US_navs[nm] = nav
            print(lab, B, flush=True)
        s = adj[bench[0]].loc[dates[0]:dates[-1]].dropna(); sb = stats(s / s.iloc[0])['CAGR']
        out += [f'\n## {lab} ({dates[0]:%m/%Y}–{dates[-1]:%m/%Y}, em {curr}; {bench[1]} {pc(sb)} a.a. antes de IR)\n',
                '| Versão | Retorno anual antes do IR | Depois de 15% de IR | Custo do IR | Pior queda | Trades por ano | Giro de peso no ano | Tempo médio na carteira |',
                '|---|---|---|---|---|---|---|---|']
        out += [f'| {nm} | **{pc(a)}** | **{pc(b)}** | {(a - b) * 100:.1f}'.replace('.', ',') + ' p.p.' + f' | {pc(dd)} | {n:.0f} | {g:.0%} | {h:.0f} meses |' for nm, a, b, dd, n, g, h in rows]
    # comparativos obrigatorios (EUA)
    navs, nn, _, _ = bm.load_benchmarks()
    for k, v in US_navs.items():
        s = v.loc[navs['S&P 500'].index[0]:]; navs[k] = s / s.iloc[0]; nn[k] = 20
    out += ['\n## EUA: comparativos obrigatórios (antes do IR)\n'] + bm.bench_table(navs, nn)
    (ROOT / 'giro_menor.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or k in US_navs}, ROOT / 'giro_menor.png',
                  'EUA: candidata × versões de giro menor (top 25/30/40) × comparativos obrigatórios — antes do IR')


if __name__ == '__main__':
    main()
