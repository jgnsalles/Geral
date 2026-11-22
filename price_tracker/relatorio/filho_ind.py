"""Ramo N: tabela simples por indústria (posições das 3 carteiras aplicadas) e efeito de excluir. Saída: relatorio/dados_filho_ind.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm, robustez as rz, filho as fh, robustez3 as r3  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
c, V, navs = pd.read_pickle(P / 'mundo' / 'cache' / 'filho_state.pkl')
adj = bm.load_prices()['adj_close']; dates = sorted(c.date.unique())
rows = []
for k in ('Top 20 (aplicada: ≥ US$ 20 bi)', 'Especiais (aplicada: peso × nota)', 'Excepcionais (atual)'):
    for d, w in V[k].items():
        for t in w.index: rows.append((d, t))
pos = pd.DataFrame(rows, columns=['date', 'ticker']).drop_duplicates().merge(c[['date', 'ticker', 'industry', 'fwd']], on=['date', 'ticker'], how='left').dropna(subset=['fwd'])
base_l, base_s = (pos.fwd < -.10).mean(), (pos.fwd <= -.30).mean()
ind = pos.groupby('industry').agg(n=('fwd', 'size'), perd=('fwd', lambda s: (s < -.10).mean()), queda=('fwd', lambda s: (s <= -.30).mean()), med=('fwd', 'median'), media=('fwd', 'mean'))
ind = ind[ind.n >= 25].sort_values('queda', ascending=False)
bt = lambda cc: fh.pick(fh.elig_top(cc), cc.ret); be = lambda cc: fh.pick(fh.elig_esp(cc), 1.5 * cc.roic + cc.growth, pri=True, wmult=cc.nota)
b0 = (float(stats(run_weighted(bt(c), adj, dates))['CAGR']), float(stats(run_weighted(be(c), adj, dates))['CAGR']))
eff = {}
for i in list(ind.index[:6]) + [x for x in ('Biotechnology', 'Semiconductors', 'Application Software') if x in ind.index and x not in ind.index[:6]]:
    cx = c.copy(); cx.loc[cx.industry == i, 'excluded'] = True
    eff[i] = (float(stats(run_weighted(bt(cx), adj, dates))['CAGR']) - b0[0], float(stats(run_weighted(be(cx), adj, dates))['CAGR']) - b0[1])
    print(i, [round(x * 100, 2) for x in eff[i]], flush=True)
out = dict(base=dict(perd=float(base_l), queda=float(base_s), n=int(len(pos))), ind=ind.reset_index().round(4).to_dict('records'), eff=eff)
(ROOT / 'dados_filho_ind.json').write_text(json.dumps(out, ensure_ascii=False, default=float))
print('base', round(base_l, 3), round(base_s, 3), len(pos)); print(ind.round(3).to_string())
