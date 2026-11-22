"""Ramo N (2026-11-22): combinações estilo Simons, anti-pânico e o "filho" (Buffett + Simons + Greenblatt). Pré-registro no PROTOCOLO.
S&P 500 point-in-time, crescimento histórico, ROIC triangulado. Saída: relatorio/dados_filho.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc2  # noqa: E402
import backtest_8 as b8, backtest_bear as bb  # noqa: E402
import robustez as rz, robustez2 as r2, robustez3 as r3  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

CUT = pd.Timestamp('2018-12-31')
SIG = ['s_roic', 's_spread', 's_esc', 's_gcred', 's_ret', 's_size', 's_stab', 's_nota']


def prep(c, adj, dates):
    c = c.copy()
    D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill'); m12 = A / A.shift(4) - 1
    c['m12'] = [m12.at[d, t] if t in m12.columns else np.nan for d, t in zip(c.date, c.ticker)]
    c['spread'] = c.roic - c.groupby(['date', 'industry']).roic.transform('median')
    c = c.sort_values(['ticker', 'date'])
    c['pe_med_prev'] = c.groupby('ticker').pe.transform(lambda s: s.where(s > 0).expanding().mean().shift(1))
    raw = {'s_roic': c.roic, 's_spread': c.spread, 's_esc': c.esc, 's_gcred': c.growth.clip(upper=.35), 's_ret': c.ret,
           's_size': np.log(c.mcap), 's_stab': -c.zgrowth, 's_nota': c.nota, 's_mom': c.m12}
    for k, v in raw.items():
        c[k] = v.groupby(c.date).rank(pct=True)
    return c.sort_index()


def elig_top(c):
    return c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.pe >= 4) & (c.mcap >= 20e9)]


def elig_esp(c):
    return c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.ret > .20) & c.bear_ok]


def pick(q, key, pri=False, wmult=None, n=20):
    q = calc2.dd_firm(q).copy(); q['_k'] = key.reindex(q.index).fillna(-9)
    if pri: q['_p'] = ((q.roic > .30) & (q.growth > .30)).astype(int)
    else: q['_p'] = 0
    if wmult is not None: q['mcap'] = q.mcap * wmult.reindex(q.index).fillna(1) ** 2
    out = {}
    for d, g in q.groupby('date'):
        g = g.sort_values(['_p', '_k'], ascending=False); keep, cnt = [], {}
        for r in g.itertuples():
            s = r.sector if isinstance(r.sector, str) else '?'
            if cnt.get(s, 0) < 8: keep.append(r.Index); cnt[s] = cnt.get(s, 0) + 1
            if len(keep) == n: break
        out[d] = bb.cap_sector(g.loc[keep])
    return out


def sub_cagr(nav, a, b):
    s = nav.loc[a:b]
    return float((s.iloc[-1] / s.iloc[0]) ** (365.25 / (s.index[-1] - s.index[0]).days) - 1)


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries()); c = bb.add_bear(c); c['esc'] = r2.escadinha(c); c = r3.nota(c)
    c = prep(c, adj, dates)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; F = rz.fwd4(c, adj, dates)
    c['fwd'] = [F[d].get(t) if d in F else np.nan for d, t in zip(c.date, c.ticker)]
    # pesos SW: IC medido só na descoberta, entre as elegíveis da Top 20
    et = elig_top(c); disc = et[(et.date <= CUT) & et.fwd.notna()]
    ic = {s: float(np.nanmean([g[s].corr(g.fwd, method='spearman') for _, g in disc.groupby('date') if len(g) >= 10])) for s in SIG + ['s_mom']}
    wsw = {s: max(ic[s], 0) for s in SIG}; tot = sum(wsw.values()) or 1; wsw = {s: v / tot for s, v in wsw.items()}
    c['S0'] = c[SIG].mean(axis=1)
    c['Sp'] = c[SIG + ['s_mom']].mean(axis=1)
    c['Sm'] = (c[SIG].sum(axis=1) + (1 - c.s_mom)) / (len(SIG) + 1)
    c['SW'] = sum(c[s] * w for s, w in wsw.items())
    c['r_ret'] = c.s_ret
    # pânico
    P1 = c.m12 < -.30; P2 = (c.m12 < -.25) & (c.gy5 > 0); P3 = (c.pe < c.pe_med_prev) & (c.m12 < 0)
    nota_w = c.nota
    base_top = lambda cc: pick(elig_top(cc), cc.ret)
    base_esp = lambda cc: pick(elig_esp(cc), 1.5 * cc.roic + cc.growth, pri=True, wmult=cc.nota)
    base_exc = lambda cc: r3.exc(cc)
    V = {'Top 20 (aplicada: ≥ US$ 20 bi)': base_top(c), 'Especiais (aplicada: peso × nota)': base_esp(c), 'Excepcionais (atual)': base_exc(c)}
    for s in ('S0', 'Sp', 'Sm', 'SW'):
        V[f'Top 20 · ordem {s}'] = pick(elig_top(c), c[s])
        V[f'Especiais · ordem {s}'] = pick(elig_esp(c), c[s], pri=True, wmult=nota_w)
    V['Top 20 · mistura ret/S0'] = pick(elig_top(c), .5 * c.r_ret + .5 * c.S0)
    V['Especiais · mistura ret/S0'] = pick(elig_esp(c), .5 * c.r_ret + .5 * c.S0, pri=True, wmult=nota_w)
    V['Top 20 · peso S0'] = pick(elig_top(c), c.ret, wmult=.5 + c.S0)
    V['Especiais · peso S0'] = pick(elig_esp(c), 1.5 * c.roic + c.growth, pri=True, wmult=nota_w * (.5 + c.S0))
    medret = elig_top(c).groupby('date').ret.transform('median')
    g1 = (c.esc >= 60) & (c.ret >= medret.reindex(c.index))
    g2 = (c.esc >= 60) & (c.spread > 0) & (c.mcap >= 20e9)
    V['Top 20 · G1 escadinha + desconto'] = pick(elig_top(c)[g1.reindex(elig_top(c).index).fillna(False)], c.ret)
    V['Top 20 · G2 escadinha + ROIC>indústria + tamanho'] = pick(elig_top(c)[g2.reindex(elig_top(c).index).fillna(False)], c.ret)
    V['Top 20 · G3 ret + nota'] = pick(elig_top(c), c.r_ret + c.s_nota)
    V['Especiais · G1'] = pick(elig_esp(c)[g1.reindex(elig_esp(c).index).fillna(False)], 1.5 * c.roic + c.growth, pri=True, wmult=nota_w)
    V['Especiais · G3 ret + nota'] = pick(elig_esp(c), c.r_ret + c.s_nota, pri=True, wmult=nota_w)
    for nm, mask in (('P1', P1), ('P2', P2), ('P3', P3)):
        cx = c.copy(); cx.loc[mask.fillna(False), 'excluded'] = True
        V[f'Top 20 · sem pânico {nm}'] = base_top(cx); V[f'Especiais · sem pânico {nm}'] = base_esp(cx); V[f'Excepcionais · sem pânico {nm}'] = base_exc(cx)
    c['FILHO'] = c[['s_ret', 's_spread', 's_esc', 's_nota']].mean(axis=1)
    V['Filho'] = pick(elig_top(c), c.FILHO, wmult=nota_w)
    res, navs = {}, {}
    for k, W in V.items():
        m, nav = rz.metr(W, adj, dates, spy, rf, F); navs[k] = nav
        m['c_a'] = sub_cagr(nav, nav.index[0], CUT); m['c_b'] = sub_cagr(nav, CUT, nav.index[-1])
        res[k] = m
        print(f'{k:55s} {m["cagr"]:.3f} dd {m["maxdd"]:.3f} w3 {m["w3"]:.3f} a {m["c_a"]:.3f} b {m["c_b"]:.3f} sev {m["sev"]:.3f}', flush=True)
    out = dict(res=res, ic=ic, wsw=wsw, spy=dict(c_a=sub_cagr(spy, spy.index[0], CUT), c_b=sub_cagr(spy, CUT, spy.index[-1]), cagr=float(stats(spy)['CAGR'])))
    pathlib.Path(ROOT / '_filho_state.pkl').write_bytes(b'')  # marcador
    pd.to_pickle((c, V, navs), ROOT.parent / 'mundo' / 'cache' / 'filho_state.pkl')
    (ROOT / 'dados_filho.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    print('ic', {k: round(v, 3) for k, v in ic.items()}); print('wsw', {k: round(v, 3) for k, v in wsw.items()})


if __name__ == '__main__':
    main()
