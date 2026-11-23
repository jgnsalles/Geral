"""Ramo N: CARTEIRA DE CONSENSO (pré-registrada no PROTOCOLO, 2026-11-23). Usa o estado salvo por filho.py. Saída: relatorio/dados_filho_consenso.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm, calc, calc2, backtest_8 as b8, backtest_bear as bb, robustez as rz  # noqa: E402
from validation_factors import factors  # noqa: E402
from filho import sub_cagr, CUT  # noqa: E402

c, V, navs0 = pd.read_pickle(P / 'mundo' / 'cache' / 'filho_state.pkl')
bn, nn, dates, adj = bm.load_benchmarks()
rf = factors()['RF']; spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; F = rz.fwd4(c, adj, dates)
W8 = b8.weights(c)
S = {'Top 20': V['Top 20 (aplicada: ≥ US$ 20 bi)'], 'Especiais': V['Especiais (aplicada: peso × nota)'], 'JG+G': W8['magicg'],
     'Excepcionais': V['Excepcionais (atual)'], 'High ROIC': W8['hroic'], 'High Growth': W8['hgrowth'], 'OoL': W8['ool']}
key = c.set_index(['date', 'ticker'])
cnt = {}
for d in sorted(set().union(*[set(w) for w in S.values()])):
    s = pd.Series(0, dtype=int)
    for w in S.values():
        if d in w: s = s.add(pd.Series(1, index=w[d].index.unique()), fill_value=0)
    cnt[d] = s.astype(int)
Wc, We = {}, {}
for d, s in cnt.items():
    df = pd.DataFrame({'ticker': s.index, 'n': s.values})
    k = key.loc[d] if d in key.index.get_level_values(0) else None
    if k is None: continue
    df = df.join(k[['ret', 'roic', 'mcap', 'sector']], on='ticker').dropna(subset=['mcap'])
    df = df.sort_values(['n', 'ret', 'roic'], ascending=False).head(20).reset_index(drop=True)
    if len(df) == 0: continue
    Wc[d] = bb.cap_sector(df); We[d] = pd.Series(1 / len(df), index=df.ticker.values)
CANDS = {'Consenso (raiz do valor, teto 10%)': Wc, 'Consenso (peso igual)': We, **{k: S[k] for k in ('Top 20', 'Especiais', 'Excepcionais')}}
D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill'); Q = A.shift(-1) / A - 1


def contrib(W):
    t = {}
    for d, w in W.items():
        if d not in Q.index: continue
        r = Q.loc[d].reindex(w.index).fillna(0)
        for k, v in (w * r).items(): t[k] = t.get(k, 0) + v
    return pd.Series(t).sort_values(ascending=False)


def drop(W, names):
    return {d: (w.drop([x for x in names if x in w.index]) / w.drop([x for x in names if x in w.index]).sum()) for d, w in W.items() if len(w.drop([x for x in names if x in w.index]))}


res = {}; navs = dict(bn)
for k, W in CANDS.items():
    m, nav = rz.metr(W, adj, dates, spy, rf, F); navs[k] = nav; nn[k] = m['n']
    m['c_a'] = sub_cagr(nav, nav.index[0], CUT); m['c_b'] = sub_cagr(nav, CUT, nav.index[-1])
    top3 = list(contrib(W).index[:3]); m['top3'] = top3
    m['sem_nvda'] = rz.metr(drop(W, ['NVDA']), adj, dates, spy, rf, F)[0]['cagr']
    m['sem_top3'] = rz.metr(drop(W, top3), adj, dates, spy, rf, F)[0]['cagr']
    tv = calc.turnover(W); m['giro'] = tv
    res[k] = m
    print(f"{k:38s} {m['cagr']:.3f} dd {m['maxdd']:.3f} w3 {m['w3']:.3f} w5 {m['w5']:.3f} w10 {m['w10']:.3f} a {m['c_a']:.3f} b {m['c_b']:.3f} "
          f"semNVDA {m['sem_nvda']:.3f} semTop3 {m['sem_top3']:.3f} {top3} giro {tv}", flush=True)
# retorno de 4 trimestres por faixa de sobreposição (média e mediana; contagem de posições), entre as ações que estão em ≥ 1 estratégia
rows = []
for d, s in cnt.items():
    if d not in F: continue
    f = F[d].reindex(s.index)
    rows += [(min(n, 4), x) for n, x in zip(s.values, f.values) if pd.notna(x)]
fx = pd.DataFrame(rows, columns=['n', 'f'])
faixa = {int(n): dict(obs=int(len(g)), media=float(g.f.mean()), mediana=float(g.f.median()), queda30=float((g.f <= -.3).mean()), perde=float((g.f < -.1).mean()))
         for n, g in fx.groupby('n')}
print('faixas', {k: (v['obs'], round(v['media'], 3), round(v['mediana'], 3), round(v['queda30'], 3)) for k, v in faixa.items()})
print('\n'.join(bm.bench_table(navs, nn)))
json.dump(dict(res=res, faixa=faixa, tabela=bm.bench_table(navs, nn)), open(ROOT / 'dados_filho_consenso.json', 'w'), ensure_ascii=False,
          default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v)))
