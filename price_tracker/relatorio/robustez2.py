"""Ramo M, parte 2: escadinha (filtro), Pequenas que compõem, Ótima em pânico. Saída: relatorio/dados_robustez2.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc2  # noqa: E402
import backtest_8 as b8, backtest_bear as bb  # noqa: E402
import robustez as rz  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

GY = rz.GY


def escadinha(c):
    R = c[GY]; n = R.notna().sum(axis=1); up = (R > 0).sum(axis=1)
    run = np.zeros(len(c)); best = np.zeros(len(c))
    for g in GY:
        pos = (c[g] > 0).to_numpy(); run = np.where(pos, run + 1, 0); best = np.maximum(best, run)
    med = R.median(axis=1); cv = R.std(axis=1, ddof=0) / med
    s = 40 * up / n + 20 * best / n + 20 * (R.min(axis=1) > -0.10) + 20 * np.maximum(0, 1 - np.minimum(1, cv / 1.5))
    return s.where((n >= 4) & (med > 0), 0).where(n >= 4)


def pequenas(c):
    m = (~c.excluded) & c.mcap.between(2e9, 30e9) & (c.roic >= .20) & (c.esc >= 70) & (c.growth >= .12) & (c.pe > 0) & (c.pe <= 1.3 * c.fair_pe)
    q = calc2.dd_firm(c[m & c.ret.notna()]); out = {}
    for d, g in q.groupby('date'):
        out[d] = bb.cap_sector(g.sort_values('ret', ascending=False).head(20))
    return out


def panico(c, adj, dates):
    D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill'); m12 = A / A.shift(4) - 1
    c = c.copy(); c['m12'] = [m12.at[d, t] if t in m12 and d in m12.index else np.nan for d, t in zip(c.date, c.ticker)]
    m = (~c.excluded) & (c.roic >= .15) & (c.esc >= 60) & (c.m12 <= -0.25) & (c.gy5 > 0)
    q = calc2.dd_firm(c[m]); out = {}
    for d, g in q.groupby('date'):
        g = g.sort_values('m12').head(20); out[d] = pd.Series(1 / len(g), index=g.ticker.values)
    return out


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries()); c = bb.add_bear(c); c['esc'] = escadinha(c)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; F = rz.fwd4(c, adj, dates)
    e60 = c.esc >= 60
    V = {'Top 20 (atual)': rz.top20(c), 'Top 20 · escadinha ≥ 60': rz.top20(c, e60), 'Especiais (atual)': rz.especiais(c),
         'Especiais · escadinha ≥ 60': rz.especiais(c, e60), 'Pequenas que compõem': pequenas(c), 'Ótima em pânico': panico(c, adj, dates)}
    res = {}
    for k, W in V.items():
        if not W: res[k] = None; continue
        res[k], _ = rz.metr(W, adj, dates, spy, rf, F)
        print(k, {a: (round(float(b), 3) if isinstance(b, (float, np.floating)) else b) for a, b in res[k].items() if a in ('cagr', 'maxdd', 'w3', 'w5', 'sev', 'n')}, flush=True)
    cx = c[c.ticker != 'NVDA']
    for k, fn in (('Pequenas que compõem', lambda: pequenas(cx)), ('Ótima em pânico', lambda: panico(cx, adj, dates))):
        if res.get(k): res[k]['nv_sem_nvda'] = float(stats(run_weighted(fn(), adj, dates))['CAGR'])
    (ROOT / 'dados_robustez2.json').write_text(json.dumps(res, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    print('ok')


if __name__ == '__main__':
    main()
