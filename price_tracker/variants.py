"""Testa variantes do modelo hibrido para Growth, zGrowth e Retorno e mede a aderencia ao Wisesheets.
Uso: python3 variants.py 2026-11-09"""
import sys, json, pathlib
import numpy as np, pandas as pd
import engine, hybrid
from compare import wise_baseline

TH = engine.TH


def letter(d, v):
    if pd.isna(v): return None
    if d == 'growth': return 'H' if v > TH['Growth_Hi'] else 'O' if v >= TH['Growth_Lo'] else 'L'
    if d == 'zgrowth': return 'O' if v < TH['zGrowth'] else 'P'
    if d == 'ret': return 'G' if v > TH['Return_Hi'] else 'O' if v >= TH['Return_Lo'] else 'B'


def score(d, w, h):
    lw, lh = w.map(lambda v: letter(d, v)), h.map(lambda v: letter(d, v))
    ok = lw.notna() & lh.notna()
    rho = pd.concat([w, h], axis=1).replace([np.inf, -np.inf], np.nan).dropna().corr('spearman').iloc[0, 1]
    return f'letra igual {(lw == lh)[ok].mean():.0%} | spearman {rho:.2f} | n={ok.sum()}'


def sec_eps_growth(day, tk, last_fy, n=6):
    f = pathlib.Path(f'data/raw/edgar/{day}/{tk}.json')
    if not f.exists(): return []
    s = hybrid.edgar_series(json.loads(f.read_text()), 'eps_diluted')
    yrs = [last_fy - n + i for i in range(n + 1)]
    return [hybrid.ratio(s.get(b), s.get(a)) for a, b in zip(yrs, yrs[1:])]


def main(day):
    w = wise_baseline().set_index('row')
    h = pd.read_csv(f'data/hybrid_{day}.csv').set_index('row')
    h = h[h.price.notna()]
    w = w.loc[h.index]
    print(f'linhas com dados Yahoo: {len(h)}\n')

    print('== GROWTH')
    v = {
        'G1 atual (2 hist + 2 proj)': h.growth,
        'G2 so projetado (f0,f1)': h[['f0', 'f1']].apply(lambda r: engine.growth_metric(list(r)), axis=1),
        'G3 so f1': h.f1,
    }
    for k, s in v.items(): print(f'{k:32s}', score('growth', w.growth, s))

    print('\n== zGROWTH')
    last = h.a_0  # apenas para alinhar
    zg = {
        'Z1 atual (4 pontos mistos)': h.zgrowth,
        'Z2 so projetado (f0,f1)': h[['f0', 'f1']].apply(lambda r: engine.cv(list(r), engine.growth_metric(list(r))), axis=1),
        'Z3 normalizados (h2*,f0,f1)': h[['h2', 'f0', 'f1']].apply(lambda r: engine.cv(list(r), engine.growth_metric(list(r))), axis=1),
    }
    hist6 = []
    for row, r in h.iterrows():
        g6 = [x for x in sec_eps_growth(day, r.ticker, int(r.name and 0) or 2025) if np.isfinite(x)]
        g = g6 + [r.f0, r.f1]
        hist6.append(engine.cv(g, engine.growth_metric(g)) if len(g6) >= 4 else np.nan)
    zg['Z4 SEC 6 anos + 2 proj'] = pd.Series(hist6, index=h.index)
    for k, s in zg.items(): print(f'{k:32s}', score('zgrowth', w.zgrowth, s))

    print('\n== RETORNO')
    eps2 = h.eps_1 * (1 + h.f1)
    r1 = h.ret
    fair1 = (h.fair_pe * h.eps_1 / h.price) - 1 + h.dy
    const1 = h.f1 + h.dy
    r2 = (fair1 + const1) / 2
    # mesmo P/E justo do Wise (isola o efeito do EPS/preco)
    fair_w = np.sqrt((w.fair_pe * eps2 / h.price).clip(lower=0)) - 1 + h.dy
    r3 = (fair_w + h.ret_const) / 2
    for k, s in {'R1 atual (2 anos, EPS+2 extrapolado)': r1, 'R2 horizonte 1 ano': r2,
                 'R3 = R1 com P/E justo do Wise': r3}.items():
        print(f'{k:36s}', score('ret', w.ret, s))

    print('\n== componentes do retorno')
    print('P/E justo        ', score('ret', w.fair_pe, h.fair_pe).split('|')[1])
    print('ret_fair (AE)    ', score('ret', w.ret_fair, h.ret_fair))
    print('ret_const (AF)   ', score('ret', w.ret_const, h.ret_const))


if __name__ == '__main__':
    main(sys.argv[1])
