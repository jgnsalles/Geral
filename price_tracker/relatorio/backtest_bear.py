"""Ramo J (2026-11-22): filtro do cenário bear (retorno_bear > −10%) e Especiais nova (prioridade ROIC > 30% e g > 30%, completa por 1,5·ROIC + g).
S&P 500 point-in-time, trimestral, crescimento histórico (mediana 5a), ROIC triangulado com as regras de 22/11. Antes × depois nas 8 seleções do Painel.
Saída: relatorio/dados_bear.json. Uso: python3 relatorio/backtest_bear.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc, calc2  # noqa: E402
import backtest_8 as b8  # noqa: E402
from pesos import run_weighted  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

OOL = bm.OOL
NAMES = {'top20c': 'Top 20 (máx. 8 por setor)', 'ool': 'Opportunity of Lifetime', 'n2': 'Excepcionais', 'n2t20': 'Especiais',
         'hroic': 'High ROIC', 'gcgr': 'Good Companies, Great Returns', 'magicg': 'JG+G', 'hgrowth': 'High Growth'}
KEYS = list(NAMES)


def add_bear(c):
    c = c.copy()
    p70 = c.groupby(['date', 'industry']).growth.transform(lambda s: s.quantile(.7))
    g = c.growth
    c['g_bear'] = np.minimum(g, np.maximum.reduce([p70.fillna(-9), 0.7 * g, pd.Series(0.06, index=c.index)]))
    mult = np.minimum(0.8 * c.fair_pe, c.pe)
    base = mult / c.pe * (1 + c.g_bear) ** 2           # = múltiplo_bear·EPS·(1+g)²/preço
    c['ret_bear'] = np.where((base > 0) & c.fair_pe.notna() & c.pe.notna(), np.sqrt(base.clip(lower=0)) - 1 + c.dy.fillna(0), np.nan)
    c['bear_ok'] = c.ret_bear > -0.10
    return c


def cap_sector(g, mx=.10, smx=.40):
    """raiz do valor de mercado com teto por ação e por setor (water-filling iterativo)"""
    w = pd.Series(np.sqrt(g.mcap.values), index=g.ticker.values); sec = pd.Series(g.sector.fillna('?').values, index=g.ticker.values)
    w = w / w.sum()
    for _ in range(60):
        changed = False
        ss = w.groupby(sec).sum()
        for s, v in ss.items():
            if v > smx + 1e-9:
                m = sec == s; w[m] *= smx / v; changed = True
        over = w > mx + 1e-9
        if over.any(): w[over] = mx; changed = True
        tot = w.sum()
        if abs(tot - 1) < 1e-9 and not changed: break
        free = (w < mx - 1e-9) & (~sec.map(w.groupby(sec).sum() >= smx - 1e-9))
        if not free.any(): w = w / w.sum(); break
        w[free] += (1 - tot) * w[free] / w[free].sum()
    return w / w.sum()


def especiais_nova(c):
    q = c[~c.excluded & c['cat'].notna() & (c.roic >= .12) & (c.growth >= .15) & c.mcap.notna() & (c.ret > .20) & c.bear_ok]
    q = calc2.dd_firm(q).copy()
    q['pri'] = ((q.roic > .30) & (q.growth > .30)).astype(int); q['nota'] = 1.5 * q.roic + q.growth
    out = {}
    for d, g in q.groupby('date'):
        g = g.sort_values(['pri', 'nota'], ascending=False); keep, cnt = [], {}
        for r in g.itertuples():
            s = r.sector if isinstance(r.sector, str) else '?'
            if cnt.get(s, 0) < 8: keep.append(r.Index); cnt[s] = cnt.get(s, 0) + 1
            if len(keep) == 20: break
        out[d] = cap_sector(g.loc[keep])
    return out


def weights_after(c):
    cb = c.copy()
    W0 = b8.weights(c)                                   # GCGR e JG+G sem filtro
    cb.loc[~cb.bear_ok, 'excluded'] = True               # barradas saem da qualidade (Top 20, Excepcionais) e da OoL
    W1 = b8.weights(cb)
    W = {k: W1[k] for k in ('top20c', 'ool', 'n2', 'hroic', 'hgrowth')}
    W['gcgr'], W['magicg'] = W0['gcgr'], W0['magicg']
    W['n2t20'] = especiais_nova(c)
    return W


def metrics_all(W, c, adj, dates, spy, rf, deep):
    res, cbs = {}, {}
    for k in KEYS:
        nav = run_weighted(W[k], adj, dates); m = calc.metrics(nav, spy, rf)
        r = dict(cagr=m['cagr'], vol=m['vol'], maxdd=m['maxdd'], sharpe=m['sharpe'], w3=m['w3'], w5=m['w5'], w10=m['w10'], w3min=m['w3min'],
                 n_mean=float(np.mean([len(w) for w in W[k].values()])), cagr_tax=stats(tax_weighted(W[k], adj, dates))['CAGR'])
        if deep:
            cb = calc.contrib(W[k], adj, dates, nav); cbs[k] = cb
            r['best5'] = [[t, float(v)] for t, v in cb.head(5).items()]; r['worst5'] = [[t, float(v)] for t, v in cb.tail(5).items()]
            r['decomp'] = b8.decomp(W[k], c, adj, dates)
        res[k] = r
    return res, cbs


def fwd_ret(adj, dates):
    D_ = pd.DatetimeIndex(dates); A = adj.reindex(D_, method='ffill')
    return (A.shift(-4) / A - 1)                         # retorno total do ano seguinte


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries())
    c = add_bear(c)
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    Wb = b8.weights(c); Wa = weights_after(c)
    before, cb_b = metrics_all(Wb, c, adj, dates, spy, rf, True)
    after, cb_a = metrics_all(Wa, c, adj, dates, spy, rf, True)
    print('antes', {k: round(v['cagr'], 4) for k, v in before.items()}); print('depois', {k: round(v['cagr'], 4) for k, v in after.items()}, flush=True)
    # robustez (depois): tirar ações do universo inteiro
    rob = {}
    for k in KEYS:
        cb = cb_a[k]; sets = {'sem a maior': list(cb.index[:1]), 'sem as 3 maiores': list(cb.index[:3]), 'sem as 3 piores': list(cb.index[-3:]), 'sem NVIDIA': ['NVDA']}
        rob[k] = {lab: [float(stats(run_weighted(weights_after(c[~c.ticker.isin(ts)])[k], adj, dates))['CAGR']), ts] for lab, ts in sets.items()}
        print(k, {a: round(b[0], 4) for a, b in rob[k].items()}, flush=True)
    rob_b = {k: float(stats(run_weighted(b8.weights(c[c.ticker != 'NVDA'])[k], adj, dates))['CAGR']) for k in KEYS}
    # quantas o filtro tira, perdedores evitados × vencedores perdidos (ano seguinte), quedas fortes
    F = fwd_ret(adj, dates); nm = calc2.sp_data()[4] if False else None
    cand = c[~c.excluded & (c['cat'] == OOL)]
    rem = cand.groupby('date').apply(lambda g: (~g.bear_ok).mean(), include_groups=False)
    filt = {}
    for k in ('top20c', 'ool', 'n2t20', 'n2', 'hroic', 'hgrowth'):
        out_rows, in_b, in_a = [], [], []
        for d in Wb[k]:
            if d not in F.index: continue
            sb, sa = set(Wb[k][d].index), set(Wa[k].get(d, pd.Series(dtype=float)).index)
            for t in sb - sa:
                v = F.at[d, t] if t in F.columns else np.nan
                if np.isfinite(v): out_rows.append((str(pd.Timestamp(d).date()), t, float(v)))
            in_b += [F.at[d, t] for t in sb if t in F.columns and np.isfinite(F.at[d, t])]
            in_a += [F.at[d, t] for t in sa if t in F.columns and np.isfinite(F.at[d, t])]
        o = pd.DataFrame(out_rows, columns=['d', 't', 'r'])
        filt[k] = dict(n_sai=float(len(o) / max(1, len(Wb[k]))), r_med_saidas=float(o.r.median()) if len(o) else None,
                       r_med_mantidas=float(np.median(in_a)) if in_a else None,
                       queda30_antes=float(np.mean(np.array(in_b) <= -0.30)) if in_b else None, queda30_depois=float(np.mean(np.array(in_a) <= -0.30)) if in_a else None,
                       evitados=o.nsmallest(8, 'r').values.tolist(), perdidos=o.nlargest(8, 'r').values.tolist(),
                       pct_saidas_queda30=float((o.r <= -0.30).mean()) if len(o) else None, pct_saidas_alta50=float((o.r >= 0.50).mean()) if len(o) else None)
    navs_b, _, _, _ = bm.load_benchmarks()
    bench9 = {k: float(stats(v)['CAGR']) for k, v in navs_b.items()}
    win9 = {k: [bm.windows(v, navs_b['S&P 500'], y)[0] for y in (3, 5, 10)] for k, v in navs_b.items()}
    out = dict(names=NAMES, before=before, after=after, rob=rob, rob_b_nvda=rob_b, filt=filt, oo_rem=float(rem.mean()), bench9=bench9, win9=win9,
               periodo=[str(dates[0].date()), str(dates[-1].date())], bear_pct_fail=float((~c.bear_ok).mean()))
    (ROOT / 'dados_bear.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    print('ok')


if __name__ == '__main__':
    main()
