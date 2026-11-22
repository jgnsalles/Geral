"""Ramo M (2026-11-22): robustez. R1 piso de valor de mercado, R2 consistência histórica, R3 Compounders redondos, R4 Quase lá → entra,
R5 indústrias perigosas. S&P 500 point-in-time, crescimento histórico, ROIC triangulado. Saída: relatorio/dados_robustez.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc, calc2  # noqa: E402
import backtest_8 as b8  # noqa: E402
import backtest_bear as bb  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

GY = ['gy1', 'gy2', 'gy3', 'gy4', 'gy5']


def top20(c, extra=None):
    q = c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.pe >= 4)]
    if extra is not None: q = q[extra.loc[q.index]]
    el = calc2.dd_firm(q); out = {}
    for d, g in el.groupby('date'):
        g = g.sort_values(['ret', 'roic'], ascending=False); keep, cnt = [], {}
        for r in g.itertuples():
            s = r.sector if isinstance(r.sector, str) else '?'
            if cnt.get(s, 0) < 8: keep.append(r.Index); cnt[s] = cnt.get(s, 0) + 1
            if len(keep) == 20: break
        out[d] = bb.cap_sector(g.loc[keep])
    return out


def especiais(c, extra=None):
    cc = c if extra is None else c[extra]
    return bb.especiais_nova(cc)


def compounders(c, need_ret=None, pe_cap=True, n=25, spy_fill=False):
    m = (~c.excluded) & (c.mcap >= 50e9) & (c.roic >= .20) & c.growth.between(.08, .35) & (c.npos >= 4) & (c.zgrowth <= 1.0)
    if pe_cap: m &= (c.pe <= 1.3 * c.fair_pe) & (c.pe > 0)
    if need_ret is not None: m &= c.ret >= need_ret
    q = calc2.dd_firm(c[m & c.ret.notna()]); out = {}
    for d in sorted(c.date.unique()):
        g = q[q.date == d].sort_values('ret', ascending=False).head(n)
        if spy_fill:
            if len(g) == 0: out[d] = pd.Series({'SPY': 1.0}); continue
            w = bb.cap_sector(g) if len(g) >= 5 else pd.Series(1 / len(g), index=g.ticker.values)
            k = min(1.0, len(g) / 5); out[d] = pd.concat([w * k, pd.Series({'SPY': 1 - k})]) if k < 1 else w
        elif len(g): out[d] = bb.cap_sector(g)
    return out


def fwd4(c, adj, dates):
    D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill'); r = {}
    for i, d in enumerate(D[:-4]):
        r[d] = A.iloc[i + 4] / A.iloc[i] - 1
    return r


def metr(W, adj, dates, spy, rf, F):
    nav = run_weighted(W, adj, dates); m = calc.metrics(nav, spy, rf); tv = calc.turnover(W)
    sev = [];
    for d, w in W.items():
        if d in F:
            x = F[d].reindex(w.index); sev += list(x.dropna() <= -0.30)
    return dict(cagr=m['cagr'], vol=m['vol'], maxdd=m['maxdd'], sharpe=m['sharpe'], w3=m['w3'], w5=m['w5'], w10=m['w10'], w3min=m['w3min'],
                trades=tv['trades'], n=float(np.mean([len(w) for w in W.values()])), sev=float(np.mean(sev)) if sev else None,
                mcap_med=None), nav


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries())
    c = bb.add_bear(c)
    c['npos'] = (c[GY] > 0).sum(axis=1).where(c[GY].notna().sum(axis=1) >= 4)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    F = fwd4(c, adj, dates)
    cons = (c.npos >= 4) & (c.zgrowth <= 1.0)
    V = {'Top 20 (atual)': top20(c), 'Top 20 · ≥ US$ 20 bi': top20(c, c.mcap >= 20e9), 'Top 20 · ≥ US$ 50 bi': top20(c, c.mcap >= 50e9),
         'Top 20 · consistência': top20(c, cons),
         'Especiais (atual)': especiais(c), 'Especiais · ≥ US$ 20 bi': especiais(c, c.mcap >= 20e9), 'Especiais · ≥ US$ 50 bi': especiais(c, c.mcap >= 50e9),
         'Especiais · consistência': especiais(c, cons),
         'Compounders redondos': compounders(c), 'Quase lá → entra (ret ≥ 20%)': compounders(c, need_ret=.20, pe_cap=False, spy_fill=True)}
    res, navs = {}, {}
    for k, W in V.items():
        if not W: res[k] = None; continue
        res[k], navs[k] = metr(W, adj, dates, spy, rf, F)
        res[k]['nv_sem_nvda'] = None
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in res[k].items() if a in ('cagr', 'maxdd', 'w3', 'sev', 'n', 'trades')}, flush=True)
    # sem NVIDIA nas principais
    cx = c[c.ticker != 'NVDA']
    for k, fn in (('Top 20 (atual)', lambda: top20(cx)), ('Top 20 · ≥ US$ 50 bi', lambda: top20(cx, cx.mcap >= 50e9)),
                  ('Especiais (atual)', lambda: especiais(cx)), ('Especiais · ≥ US$ 50 bi', lambda: especiais(cx, cx.mcap >= 50e9)),
                  ('Compounders redondos', lambda: compounders(cx))):
        res[k]['nv_sem_nvda'] = float(stats(run_weighted(fn(), adj, dates))['CAGR'])
    # R5 indústrias: posições das carteiras principais (Top 20, Especiais, OoL, High ROIC, Excepcionais)
    W8 = b8.weights(c); allW = {**{k: W8[k] for k in ('top20c', 'ool', 'hroic', 'n2')}, 'esp': V['Especiais (atual)']}
    rows = []
    for k, Wk in allW.items():
        for d, w in Wk.items():
            if d not in F: continue
            x = F[d]
            for t in w.index:
                v = x.get(t)
                if v is not None and np.isfinite(v): rows.append((d, t, v))
    pos = pd.DataFrame(rows, columns=['date', 'ticker', 'r']).drop_duplicates(['date', 'ticker'])
    pos = pos.merge(c[['date', 'ticker', 'industry', 'sector']], on=['date', 'ticker'], how='left')
    pos['sev'] = pos.r <= -0.30; pos['per'] = np.where(pos.date <= pd.Timestamp('2018-12-31'), 'a', 'b')
    base = pos.groupby('per').sev.mean()
    ind = pos.groupby('industry').agg(n=('sev', 'size'), sev=('sev', 'mean'), med=('r', 'median'))
    per = pos.groupby(['industry', 'per']).sev.mean().unstack()
    ind['lift_a'] = per['a'] / base['a']; ind['lift_b'] = per['b'] / base['b']
    ind = ind[ind.n >= 30].sort_values('sev', ascending=False)
    danger = list(ind[(ind.lift_a >= 1.5) & (ind.lift_b >= 1.5)].index)
    custo = {}
    for i in list(ind.index[:6]) + ['Biotechnology']:
        if i in custo: continue
        cx = c.copy(); cx.loc[cx.industry == i, 'excluded'] = True
        custo[i] = {'Top 20': float(stats(run_weighted(top20(cx), adj, dates))['CAGR']), 'Especiais': float(stats(run_weighted(especiais(cx), adj, dates))['CAGR'])}
    bio = pos[pos.industry == 'Biotechnology']
    # 9 comparativos
    navs_b, _, _, _ = bm.load_benchmarks()
    bench9 = {k: [float(stats(v)['CAGR'])] + [bm.windows(v, navs_b['S&P 500'], y)[0] for y in (3, 5, 10)] for k, v in navs_b.items()}
    M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()}); sp = spy.resample('ME').last()
    nav_out = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(x) else round(float(x), 4) for x in M[k] / M[k].dropna().iloc[0]] for k in M}}
    nav_out['series']['S&P 500'] = [round(float(x), 4) for x in (sp / sp.iloc[0]).reindex(M.index).ffill()]
    # quem está hoje nos compounders (última data)
    dl = max(c.date); cl = compounders(c).get(dl, pd.Series(dtype=float))
    out = dict(res=res, ind=ind.reset_index().round(4).to_dict('records'), base_sev={k: float(v) for k, v in base.items()}, danger=danger, custo=custo,
               bio=dict(n=int(len(bio)), sev=float(bio.sev.mean()) if len(bio) else None, med=float(bio.r.median()) if len(bio) else None),
               bench9=bench9, nav=nav_out, comp_hoje=[[t, float(w)] for t, w in cl.items()], periodo=[str(dates[0].date()), str(dates[-1].date())])
    (ROOT / 'dados_robustez.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
    print('perigosas', danger); print(ind.head(10).to_string()); print('custo', custo); print('bio', out['bio']); print('comp hoje', out['comp_hoje'])


if __name__ == '__main__':
    main()
