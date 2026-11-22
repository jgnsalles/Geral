"""Ramo K (2026-11-22): diagnóstico dos episódios perdedores (TIR < −10% a.a.) e teste de sinais para evitá-los (pré-registrado no PROTOCOLO).
Carteiras: Top 20 (máx. 8/setor), Especiais nova, OoL, High ROIC, High Growth, Excepcionais, JG+G. S&P 500 PIT, crescimento histórico.
Saída: relatorio/dados_perdedores.json. Uso: python3 relatorio/perdedores.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc, calc2  # noqa: E402
import backtest_8 as b8  # noqa: E402
from backtest_bear import add_bear, especiais_nova  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

NAMES = {'top20c': 'Top 20', 'n2t20': 'Especiais', 'ool': 'OoL', 'hroic': 'High ROIC', 'hgrowth': 'High Growth', 'n2': 'Excepcionais', 'magicg': 'JG+G'}
CUT = pd.Timestamp('2018-12-31')


def weights_all(c):
    W = b8.weights(c); W['n2t20'] = especiais_nova(c)
    return {k: W[k] for k in NAMES}


def signals(c, A, D):
    c = c.copy(); iq = {d: i for i, d in enumerate(D)}
    p70 = c.groupby(['date', 'industry']).growth.transform(lambda s: s.quantile(.7))
    g = c.growth
    gb50 = np.minimum(g, np.maximum.reduce([p70.fillna(-9), 0.5 * g, pd.Series(0.06, index=c.index)]))
    mult = np.minimum(0.8 * c.fair_pe, c.pe); base = mult / c.pe * (1 + gb50) ** 2
    c['ret_bear50'] = np.where((base > 0) & c.fair_pe.notna() & c.pe.notna(), np.sqrt(base.clip(lower=0)) - 1 + c.dy.fillna(0), np.nan)
    pe80 = c.groupby(['date', 'industry']).pe.transform(lambda s: s.quantile(.8))
    gsec = c.groupby(['date', 'sector']).growth.transform('median')
    mom = []
    for d, t in zip(c.date, c.ticker):
        i = iq.get(d)
        if i is None or i < 4 or t not in A: mom.append(np.nan); continue
        a0, a1 = A.at[D[i - 4], t], A.at[d, t]; mom.append(a1 / a0 - 1 if a0 > 0 else np.nan)
    c['mom12'] = mom
    S = {'Bear atual ≤ −10%': c.ret_bear <= -0.10,
         'Bear com piso de 50% ≤ −10%': c.ret_bear50 <= -0.10,
         'P/L > 1,5× o P/E justo': c.pe > 1.5 * c.fair_pe,
         'P/L acima do p80 da indústria': c.pe > pe80,
         'Crescimento > 2× a mediana do setor': c.growth > 2 * gsec.clip(lower=0.01),
         'ROIC do último ano caiu > 20%': c.ry6 < 0.8 * c[['ry4', 'ry5']].mean(axis=1),
         'EPS do último ano caiu': c.gy5 < 0,
         'Alta de 12 meses > 80%': c.mom12 > 0.80,
         'zGrowth > 1,5': c.zgrowth > 1.5}
    for k, v in S.items(): c['S:' + k] = v.fillna(False).astype(bool)
    return c, list(S)


def episodes(W, c, A, D):
    iq = {d: i for i, d in enumerate(D)}; key = c.set_index(['date', 'ticker'])
    rows = []
    for k, Wk in W.items():
        held = {}
        for d, w in Wk.items():
            for t in w.index: held.setdefault(t, []).append(iq[pd.Timestamp(d)])
        for t, idx in held.items():
            idx = sorted(set(idx)); runs, s = [], idx[0]
            for a, b in zip(idx, idx[1:] + [None]):
                if b is None or b != a + 1: runs.append((s, a)); s = b
            for i0, i1 in runs:
                ie = min(i1 + 1, len(D) - 1)
                if ie <= i0 or t not in A: continue
                p0 = A[t].iloc[:i0 + 1].dropna(); pe_ = A[t].iloc[:ie + 1].dropna()
                if not len(p0) or not len(pe_): continue
                a0, a1 = A.at[D[i0], t], pe_.iloc[-1]
                if not (a0 > 0): continue
                R = a1 / a0 - 1; yrs = (ie - i0) / 4; tir = (1 + R) ** (1 / yrs) - 1 if R > -1 else -1.0
                e0 = key.loc[(D[i0], t)] if (D[i0], t) in key.index else None
                e1 = key.loc[(D[ie], t)] if (D[ie], t) in key.index else None
                if e0 is None: continue
                r = dict(cart=k, t=t, d0=D[i0], d1=D[ie], q=ie - i0, R=R, tir=tir, sector=e0.sector, industry=e0.industry, mcap=e0.mcap,
                         pe0=e0.pe, fpe0=e0.fair_pe, roic0=e0.roic, g0=e0.growth, zg0=e0.zgrowth, zroic0=e0.zroic, ret0=e0.ret, rb0=e0.ret_bear,
                         rb50=e0.ret_bear50, mom12=e0.mom12, eps0=e0.eps, cyc=bool(e0.cyclical) if 'cyclical' in e0 else False)
                for s in SIG: r['S:' + s] = bool(e0['S:' + s])
                if e1 is not None: r.update(pe1=e1.pe, roic1=e1.roic, eps1=e1.eps)
                i2 = i0 + 8
                if i2 < len(D) and (D[i2], t) in key.index: r['roic2y'] = key.loc[(D[i2], t)].roic; r['eps2y'] = key.loc[(D[i2], t)].eps
                rows.append(r)
    return pd.DataFrame(rows)


def kind(r):
    if r.q <= 1: return 'Queda curta (≤ 1 trimestre)'
    eps_ok = pd.notna(r.get('eps1')) and pd.notna(r.eps0) and r.eps0 > 0
    if not eps_ok: return 'Lucro virou prejuízo / sem dado'
    ch = r.eps1 / r.eps0
    if ch < 0.9:
        if pd.notna(r.zroic0) and r.zroic0 > 0.4: return 'Ciclo disfarçado (lucro caiu, ROIC instável antes)'
        if pd.notna(r.get('roic1')) and pd.notna(r.roic0) and r.roic1 < 0.7 * r.roic0: return 'ROIC caiu (vantagem enfraqueceu)'
        return 'Lucro caiu (crescimento não veio)'
    e2 = r.get('eps2y')
    if pd.notna(e2) and e2 < 0.9 * r.eps0: return 'Múltiplo caiu antes, lucro caiu depois (mercado antecipou)'
    return 'Múltiplo comprimiu (lucro ok)'


def main():
    global SIG
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries())
    c = add_bear(c); D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill')
    c, SIG = signals(c, A, D)
    W = weights_all(c)
    E = episodes(W, c, A, D)
    E['loser'] = E.tir < -0.10; E['win'] = E.tir > 0.30
    E['grupo'] = np.where(E.loser, 'Perdedores', np.where(E.win, 'Grandes vencedores', 'Demais'))
    ok = E.pe1.notna() & (E.pe0 > 0) & (E.pe1 > 0) & (E.eps0 > 0) & (E.eps1 > 0)
    E['le'] = np.where(ok, np.log(E.eps1 / E.eps0), np.nan); E['lp'] = np.where(ok, np.log(E.pe1 / E.pe0), np.nan)
    E['lt'] = np.log1p(E.R.clip(lower=-0.99)); E['ld'] = E['lt'] - E['le'] - E['lp']
    E['eps_cagr'] = np.where(ok, (E.eps1 / E.eps0) ** (4 / E.q) - 1, np.nan)
    E['disc0'] = np.log(E.fpe0 / E.pe0)
    okf = (E.eps0 > 0) & E.eps2y.notna() & (E.eps2y > 0)
    E['eps2y_cagr'] = np.where(okf, (E.eps2y / E.eps0) ** 0.5 - 1, np.nan)
    L = E[E.loser].copy(); L['tipo'] = L.apply(kind, axis=1)
    med = lambda x: None if x.dropna().empty else float(x.median())
    prof = {}
    for gname, g in E.groupby('grupo'):
        prof[gname] = dict(n=int(len(g)), q_med=med(g.q), tir_med=med(g.tir), R_med=med(g.R), pe0=med(g.pe0), pe1=med(g.pe1), fpe0=med(g.fpe0),
                           disc0=med(g.disc0), roic0=med(g.roic0), roic1=med(g.roic1), roic2y=med(g.roic2y), g0=med(g.g0), eps_cagr=med(g.eps_cagr), eps2y_cagr=med(g.eps2y_cagr), eps2y_queda=float(((g.eps2y < 0.9 * g.eps0) & (g.eps0 > 0)).sum() / max(1, ((g.eps0 > 0) & g.eps2y.notna()).sum())),
                           zg0=med(g.zg0), zroic0=med(g.zroic0), mom12=med(g.mom12), rb0=med(g.rb0), ret0=med(g.ret0), mcap=med(g.mcap),
                           le=med(g['le']), lp=med(g['lp']), ld=med(g['ld']), cyc=float(g.cyc.mean()))
    por_cart = {NAMES[k]: dict(n=int(len(g)), perd=float(g.loser.mean()), tir_med=med(g.tir), perd_curto=float((g.loser & (g.q <= 1)).sum() / max(1, g.loser.sum())))
                for k, g in E.groupby('cart')}
    tipos = L.tipo.value_counts().to_dict()
    tipo_ex = {tp: [[r.t, str(r.d0.date()), str(r.d1.date()), float(r.tir), float(r.R), NAMES[r.cart]] for r in g.sort_values('R').head(6).itertuples()]
               for tp, g in L.groupby('tipo')}
    tipo_prof = {tp: dict(n=int(len(g)), R_med=med(g.R), le=med(g['le']), lp=med(g['lp']), roic0=med(g.roic0), roic1=med(g.roic1), pe0=med(g.pe0), pe1=med(g.pe1))
                 for tp, g in L.groupby('tipo')}
    setor = L.sector.value_counts(normalize=True).head(8).round(3).to_dict(); setor_all = E.sector.value_counts(normalize=True).round(3).to_dict()
    ano = L.groupby(L.d0.dt.year).size().to_dict(); ano_all = E.groupby(E.d0.dt.year).size().to_dict()
    # sinais: episódios únicos por ação × data de entrada
    U = E.sort_values('tir').drop_duplicates(['t', 'd0'])
    sig = []
    for s in SIG:
        row = dict(sinal=s)
        for per, m in (('desc', U.d0 <= CUT), ('conf', U.d0 > CUT)):
            u = U[m]; f = u['S:' + s]; base = u.loser.mean()
            prec = u.loser[f].mean() if f.any() else np.nan
            row[per] = dict(n=int(len(u)), marcados=float(f.mean()), base=float(base), prec=float(prec) if np.isfinite(prec) else None,
                            lift=float(prec / base) if f.any() and base > 0 else None, rec_perd=float(f[u.loser].mean()) if u.loser.any() else None,
                            rec_venc=float(f[u.win].mean()) if u.win.any() else None, tir_m=med(u.tir[f]), tir_nm=med(u.tir[~f]))
        def ok_(x): return (x['lift'] or 0) >= 1.5 and x['tir_m'] is not None and x['tir_nm'] is not None and x['tir_nm'] - x['tir_m'] >= 0.10 and \
            (x['rec_perd'] or 0) >= 1.5 * max(x['rec_venc'] or 0, 1e-9)
        row['passa'] = bool(ok_(row['desc']) and ok_(row['conf']))
        sig.append(row)
    passed = [r['sinal'] for r in sig if r['passa']]
    # teste nas carteiras: só os sinais aprovados (pré-registro)
    teste = {}
    if passed:
        spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
        def mt(Wx):
            out = {}
            for k in ('top20c', 'n2t20', 'ool'):
                nav = run_weighted(Wx[k], adj, dates); m = calc.metrics(nav, spy, rf)
                out[NAMES[k]] = dict(cagr=m['cagr'], vol=m['vol'], maxdd=m['maxdd'], sharpe=m['sharpe'], w3=m['w3'], w5=m['w5'], w10=m['w10'], w3min=m['w3min'])
            return out
        teste['antes'] = mt(W)
        for s in passed:
            cx = c.copy(); cx.loc[cx['S:' + s], 'excluded'] = True; cx.loc[cx['S:' + s], 'bear_ok'] = False
            teste[s] = mt(weights_all(cx))
        navs_b, _, _, _ = bm.load_benchmarks()
        teste['bench9'] = {k: float(stats(v)['CAGR']) for k, v in navs_b.items()}
        teste['win9'] = {k: [bm.windows(v, navs_b['S&P 500'], y)[0] for y in (3, 5, 10)] for k, v in navs_b.items()}
    worst = [[r.t, NAMES[r.cart], str(r.d0.date()), str(r.d1.date()), int(r.q), float(r.R), float(r.tir), r.tipo,
              None if pd.isna(r.pe0) else float(r.pe0), None if pd.isna(r.pe1) else float(r.pe1),
              None if pd.isna(r.roic0) else float(r.roic0), None if pd.isna(r.roic1) else float(r.roic1),
              None if pd.isna(r.g0) else float(r.g0), None if pd.isna(r.eps_cagr) else float(r.eps_cagr)]
             for r in L.sort_values('R').drop_duplicates(['t', 'd0']).head(25).itertuples()]
    out = dict(n_ep=int(len(E)), n_perd=int(E.loser.sum()), n_perd_unicos=int(L.drop_duplicates(['t', 'd0']).shape[0]), pct_perd=float(E.loser.mean()),
               pct_perd_curto=float((L.q <= 1).mean()), prof=prof, por_cart=por_cart, tipos=tipos, tipo_ex=tipo_ex, tipo_prof=tipo_prof,
               setor=setor, setor_all=setor_all, ano={int(k): int(v) for k, v in ano.items()}, ano_all={int(k): int(v) for k, v in ano_all.items()},
               sinais=sig, aprovados=passed, teste=teste, worst=worst, periodo=[str(D[0].date()), str(D[-1].date())])
    (ROOT / 'dados_perdedores.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
    print(json.dumps({k: out[k] for k in ('n_ep', 'n_perd', 'n_perd_unicos', 'pct_perd', 'pct_perd_curto', 'tipos', 'aprovados')}, ensure_ascii=False))
    print(json.dumps(prof, ensure_ascii=False, default=float)[:2500])
    for r in sig: print(r['sinal'], r['passa'], {p: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r[p].items()} for p in ('desc', 'conf')})


if __name__ == '__main__':
    SIG = []
    main()
