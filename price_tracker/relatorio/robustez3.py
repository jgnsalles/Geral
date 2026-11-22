"""Ramo M, parte 3: "Nota de boa empresa" (framework v4.2) no backtest: filtro (N1), ordem (N2) e peso (N3) em Top 20, Especiais e Excepcionais.
Saída: relatorio/dados_robustez3.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc2  # noqa: E402
import backtest_8 as b8, backtest_bear as bb  # noqa: E402
import robustez as rz, robustez2 as r2  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

WACC = .085
RY = ['ry1', 'ry2', 'ry3', 'ry4', 'ry5', 'ry6']


def nota(c):
    c = c.copy()
    med_ind = c.groupby(['date', 'industry']).roic.transform('median')
    spread = c.roic - med_ind
    pct = spread.groupby(c.date).rank(pct=True)
    c1 = 1 + 4 * pct
    c1 = np.where((c.roic < WACC + .10) | (c.roic < 1.5 * med_ind), np.minimum(c1, 3), c1)
    m = c.roic_marg; ro = c.roic
    c2 = np.select([m.isna(), (m >= .8 * ro) & (m >= WACC), m >= .5 * ro, m >= WACC, m >= 0], [3, 5, 4, 3, 2], 1)
    pe = c.pe; r1 = np.minimum(ro.clip(lower=1e-6), 1)
    gimp = (WACC * pe - 1) / (pe - 1 / r1)
    pista = np.minimum(c.growth, .15) - gimp
    c3 = np.select([pe.isna() | c.growth.isna(), pe < 1 / r1, pista >= .05, pista >= .02, pista >= 0, pista >= -.03], [3, 5, 5, 4, 3, 2], 1)
    R = c[RY]; n = R.notna().sum(axis=1)
    allv = lambda th: (R.ge(th) | R.isna()).all(axis=1) & (n >= 3)
    c4 = np.select([allv(.20) & (R.min(axis=1) >= .7 * R.mean(axis=1)), allv(.15), allv(WACC), (R >= WACC).sum(axis=1) > n / 2], [5, 4, 3, 2], 1)
    noloss = (c[rz.GY] > -0.25).all(axis=1)
    c6 = 1 + (c.esc >= 70).astype(int) + (c.mcap >= 10e9).astype(int) + (~c.cyclical.astype(bool)).astype(int) + noloss.astype(int)
    c['n1'], c['n2'], c['n3'], c['n4'], c['n6'] = c1, c2, c3, c4, c6
    c['nota'] = c[['n1', 'n2', 'n3', 'n4', 'n6']].mean(axis=1)
    return c


def top20_order(c):
    cc = c.copy(); cc['ret'] = cc.ret + .05 * (cc.nota - 3); return rz.top20(cc)


def esp(c, mode=None):
    q = c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.ret > .20) & c.bear_ok]
    if mode == 'filtro': q = q[q.nota >= 3.5]
    q = calc2.dd_firm(q).copy()
    q['pri'] = ((q.roic > .30) & (q.growth > .30)).astype(int); q['sc'] = 1.5 * q.roic + q.growth + (.3 * (q.nota - 3) if mode == 'ordem' else 0)
    if mode == 'peso': q['mcap'] = q.mcap * q.nota ** 2
    out = {}
    for d, g in q.groupby('date'):
        g = g.sort_values(['pri', 'sc'], ascending=False); keep, cnt = [], {}
        for r in g.itertuples():
            s = r.sector if isinstance(r.sector, str) else '?'
            if cnt.get(s, 0) < 8: keep.append(r.Index); cnt[s] = cnt.get(s, 0) + 1
            if len(keep) == 20: break
        out[d] = bb.cap_sector(g.loc[keep])
    return out


def exc(c, mode=None):
    q = c[~c.excluded & c['cat'].notna() & (c.roic > .30) & (c.growth > .30) & c.mcap.notna()]
    if mode == 'filtro': q = q[q.nota >= 3.5]
    q = calc2.dd_firm(q); out = {}
    for d, g in q.groupby('date'):
        w = np.sqrt(g.mcap.values) * (g.nota.values if mode == 'peso' else 1)
        out[d] = pd.Series(w / w.sum(), index=g.ticker.values)
    return out


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries()); c = bb.add_bear(c); c['esc'] = r2.escadinha(c); c = nota(c)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; F = rz.fwd4(c, adj, dates)
    cw = c.copy(); cw['mcap'] = cw.mcap * cw.nota ** 2
    V = {'Top 20 (atual)': rz.top20(c), 'Top 20 · N1 filtro ≥ 3,5': rz.top20(c, c.nota >= 3.5), 'Top 20 · N2 ordem': top20_order(c), 'Top 20 · N3 peso': rz.top20(cw),
         'Especiais (atual)': esp(c), 'Especiais · N1 filtro': esp(c, 'filtro'), 'Especiais · N2 ordem': esp(c, 'ordem'), 'Especiais · N3 peso': esp(c, 'peso'),
         'Excepcionais (atual)': exc(c), 'Excepcionais · N1 filtro': exc(c, 'filtro'), 'Excepcionais · N3 peso': exc(c, 'peso')}
    res = {}
    for k, W in V.items():
        res[k], _ = rz.metr(W, adj, dates, spy, rf, F)
        dl = [d for d in W if len(W[d])]
        res[k]['nota_media'] = float(np.nanmean([np.average(c.set_index(['date', 'ticker']).nota.reindex([(d, t) for t in W[d].index]).fillna(3), weights=W[d].values) for d in dl]))
        print(k, {a: (round(float(b), 3) if isinstance(b, (float, np.floating)) else b) for a, b in res[k].items() if a in ('cagr', 'maxdd', 'w3', 'w5', 'sev', 'n', 'nota_media')}, flush=True)
    (ROOT / 'dados_robustez3.json').write_text(json.dumps(res, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    print('ok')


if __name__ == '__main__':
    main()
