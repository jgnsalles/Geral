"""EUA: empresas que cairam de OoL para GCGR por ROIC instavel (zROIC >= 0,7).
5 faixas de zROIC (mesmo numero de posicoes) e, em cada faixa, ROIC medio dos ultimos 2 anos acima/abaixo da media dos 6 anos.
Uso: python3 backtest/zroic_unstable.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import diag_two_countries as dg  # noqa: E402
from backtest import load_pit, asof  # noqa: E402
from zroic_breakdown import perf, row  # noqa: E402

pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')


def roic_series(pit, t, fin, last):
    s = {k: asof(pit[k], t)[0] for k in ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income')}
    g = lambda k, y: s[k][y][0] if y in s[k] else None
    out = []
    for y in range(last - 5, last + 1):
        if fin:
            ni, eq = g('net_income', y), g('equity', y)
            out.append(ni / eq if ni is not None and eq and eq > 0 else np.nan); continue
        oi, eq = g('op_income', y), g('equity', y)
        if oi is None or eq is None: out.append(np.nan); continue
        pt, tx = g('pretax', y), g('tax', y)
        tr = min(max(tx / pt, 0), 0.5) if pt and tx is not None and pt > 0 else 0.21
        ic = eq + (g('lt_debt', y) or 0.0) - (g('cash', y) or 0.0)
        out.append(oi * (1 - tr) / ic if ic > 0 else np.nan)
    return out


def main():
    c, adj = dg.us(); c = dg.enrich(c, adj)
    univ = c[c.cat.notna()].groupby('date').rq.mean()
    g = c[c.cat == dg.GCGR].copy()
    g = g[g.code.map(lambda s: next((i for i in range(4) if s[i] != 'HOGNG'[i]), None)) == 3]  # ROIC instavel
    pits = {}
    l2, l6 = [], []
    for d, t, fin, last in zip(g.date, g.ticker, g.fin, g.last_fy):
        pits.setdefault(t, load_pit(t))
        r = roic_series(pits[t], d, bool(fin), int(last))
        v = [x for x in r if np.isfinite(x)]
        l2.append(np.nanmean(r[-2:]) if np.isfinite(r[-2:]).any() else np.nan)
        l6.append(np.mean(v) if v else np.nan)
    g['roic_2a'], g['roic_6a'] = l2, l6
    g['acima'] = g.roic_2a > g.roic_6a
    g['faixa'] = pd.qcut(g.zroic, 5)
    hdr = ['| Faixa de zROIC | Posições | Empresas | Retorno a.a. | vs Universo | t | % negativas | ROIC (mediana) | ROIC marginal (mediana) |',
           '|---|---|---|---|---|---|---|---|---|']
    lab = lambda iv: f'{iv.left:.2f}–{iv.right:.2f}'.replace('.', ',')
    out = ['# EUA: excluídas de OoL por ROIC instável (zROIC ≥ 0,7)\n',
           '> ⚠️ **ROIC:** grupo pequeno; problemas de dado no ROIC pesam mais aqui.\n',
           f'{len(g)} posições, {g.ticker.nunique()} empresas. Faixas com o mesmo número de posições. '
           '"ROIC 2 anos" = média dos dois últimos exercícios; "média 6 anos" = média da janela do modelo (só exercícios já arquivados na data).\n',
           '## 1. Cinco faixas de zROIC\n'] + hdr
    out.append(row('**Todas**', perf(g, univ)))
    for iv, x in g.groupby('faixa', observed=True):
        out.append(row(lab(iv), perf(x, univ)))
    out += ['', '## 2. Cinco faixas × ROIC dos últimos 2 anos acima ou abaixo da média de 6 anos\n',
            '| Faixa de zROIC | Acima: posições | Acima: retorno a.a. | Acima: vs Universo | Abaixo: posições | Abaixo: retorno a.a. | Abaixo: vs Universo |',
            '|---|---|---|---|---|---|---|']
    for iv, x in list(g.groupby('faixa', observed=True)) + [('Todas', g)]:
        a, b = perf(x[x.acima], univ), perf(x[~x.acima], univ)
        f = lambda p, k: '—' if p.get('n', 0) == 0 else (pc(p[k]) if k == 'ret' else f"**{p[k]:+.1%}**".replace('.', ','))
        name = lab(iv) if iv != 'Todas' else '**Todas**'
        out.append(f"| {name} | {a.get('n', 0)} | {f(a, 'ret')} | {f(a, 'ex')} | {b.get('n', 0)} | {f(b, 'ret')} | {f(b, 'ex')} |")
    out += ['', '## Empresas do grupo\n', '| Ticker | Empresa | Posições | zROIC (mediana) | ROIC 2 anos (mediana) | Média 6 anos (mediana) | Retorno médio a.a. |', '|---|---|---|---|---|---|---|']
    u = pd.read_csv(ROOT / 'data/universe.csv').set_index('ticker')
    t = g.groupby('ticker').agg(n=('rq', 'size'), z=('zroic', 'median'), r2=('roic_2a', 'median'), r6=('roic_6a', 'median'), ret=('rq', 'mean')).sort_values('n', ascending=False)
    out += [f"| {k} | {u['name'].get(k)} | {int(r.n)} | {f'{r.z:.2f}'.replace('.', ',')} | {pc(r.r2)} | {pc(r.r6)} | {pc(r.ret * 4)} |" for k, r in t.iterrows()]
    (ROOT / 'zroic_unstable.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
