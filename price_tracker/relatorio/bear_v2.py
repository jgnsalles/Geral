"""Ramo L (2026-11-22, pré-registrado no PROTOCOLO): bear v2 pela indústria e regra de venda.
1) reclassifica os perdedores do ramo K pela lente "crescimento previsto muito acima da indústria, não entregue";
2) testa sinais (gap de crescimento/múltiplo vs indústria, bear v2 mediana e p70) em descoberta 2012–18 e confirmação 2019–26;
3) se algum passar, testa nas 8 seleções; testa à parte a regra de venda (EPS < 80% da trajetória prevista na entrada).
Saída: relatorio/dados_bear_v2.json. Uso: python3 relatorio/bear_v2.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import benchmarks as bm  # noqa: E402
import calc  # noqa: E402
import backtest_8 as b8  # noqa: E402
import perdedores as pk  # noqa: E402
from backtest_bear import add_bear, especiais_nova, metrics_all, NAMES, KEYS  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from validation_factors import factors  # noqa: E402
from ciclicos import cyclical_industries  # noqa: E402

CUT = pd.Timestamp('2018-12-31'); WACC = 0.085
med = lambda x: None if x.dropna().empty else float(x.median())


def industry_stats(c):
    c = c.copy()
    n = c.groupby(['date', 'industry']).ticker.transform('count')
    c['grp'] = np.where(n >= 5, c.industry.astype(str), 'S:' + c.sector.astype(str))
    gb = c.groupby(['date', 'grp'])
    c['g_med'] = gb.growth.transform('median'); c['g_p70'] = gb.growth.transform(lambda s: s.quantile(.7))
    pe = c.pe.where(c.pe > 0)
    c['pe_med'] = pe.groupby([c.date, c.grp]).transform('median'); c['pe_p70'] = pe.groupby([c.date, c.grp]).transform(lambda s: s.quantile(.7))
    c['gap_g'] = c.growth - c.g_med; c['gap_pe'] = c.pe / c.pe_med
    for tag, gcol, pcol in (('med', 'g_med', 'pe_med'), ('p70', 'g_p70', 'pe_p70')):
        gbear = np.minimum(c.growth, np.maximum(c[gcol].fillna(0.06), 0.06))
        r = c.roic.clip(upper=1.0)
        fpe = np.where((r > 0) & (gbear < WACC - 0.005), (1 - gbear / r) / (WACC - gbear), np.nan)
        mult = np.minimum(c.pe, np.nanmax(np.vstack([c[pcol].values, fpe]), axis=0))
        base = mult / c.pe * (1 + gbear) ** 2
        c[f'rb2_{tag}'] = np.where((c.pe > 0) & (base > 0), np.sqrt(np.clip(base, 0, None)) - 1 + c.dy.fillna(0), np.nan)
    return c


def sig_eval(U, mask_fn):
    out = {}
    for per, m in (('desc', U.d0 <= CUT), ('conf', U.d0 > CUT)):
        u = U[m]; f = mask_fn(u).fillna(False).astype(bool); base = u.loser.mean()
        prec = u.loser[f].mean() if f.any() else np.nan
        out[per] = dict(n=int(len(u)), marcados=float(f.mean()), base=float(base), prec=float(prec) if np.isfinite(prec) else None,
                        lift=float(prec / base) if f.any() and base > 0 else None, rec_perd=float(f[u.loser].mean()) if u.loser.any() else None,
                        rec_venc=float(f[u.win].mean()) if u.win.any() else None, tir_m=med(u.tir[f]), tir_nm=med(u.tir[~f]),
                        venc_cortados=[[r.t, str(r.d0.date()), round(float(r.tir), 3)] for r in u[f & u.win].sort_values('tir', ascending=False).head(6).itertuples()])
    ok = lambda x: (x['lift'] or 0) >= 1.5 and x['tir_m'] is not None and x['tir_nm'] is not None and x['tir_nm'] - x['tir_m'] >= 0.10 and \
        (x['rec_perd'] or 0) >= 1.5 * max(x['rec_venc'] or 0, 1e-9)
    out['passa'] = bool(ok(out['desc']) and ok(out['conf']))
    return out


def sell_rule(Wk, c, D):
    """vende quando o EPS do último exercício < 80% da trajetória prevista na entrada; não volta enquanto seguir selecionada sem interrupção"""
    key = c.set_index(['date', 'ticker'])[['eps', 'growth']]
    entry, banned, out = {}, set(), {}
    prev = set()
    for d in sorted(Wk):
        w = Wk[d]; cur = set(w.index)
        for t in list(entry):
            if t not in cur: entry.pop(t); banned.discard(t)
        for t in cur - set(entry):
            if (d, t) in key.index:
                e, g = key.loc[(d, t)]
                entry[t] = (d, e, g)
        drop = []
        for t in cur:
            if t in banned: drop.append(t); continue
            if t in entry and (d, t) in key.index:
                d0, e0, g0 = entry[t]; yrs = (d - d0).days / 365.25
                e = key.loc[(d, t)].eps
                if yrs >= 0.9 and pd.notna(e0) and e0 > 0 and pd.notna(g0) and pd.notna(e) and e < 0.8 * e0 * (1 + max(g0, -0.5)) ** yrs:
                    banned.add(t); drop.append(t)
        keep = w.drop(drop)
        out[d] = keep / keep.sum() if len(keep) else w
    return out


def main():
    rf = factors()['RF']
    c, adj, dates = b8.build(bm.ROIC_FILE, cyclical_industries())
    c = add_bear(c); D = pd.DatetimeIndex(dates); A = adj.reindex(D, method='ffill')
    c, pk.SIG = pk.signals(c, A, D)
    c = industry_stats(c)
    W = pk.weights_all(c)
    E = pk.episodes(W, c, A, D)
    key = c.set_index(['date', 'ticker'])
    for col in ('g_med', 'pe_med', 'gap_g', 'gap_pe', 'rb2_med', 'rb2_p70', 'g_p70', 'pe_p70'):
        E[col] = [key.at[(d, t), col] if (d, t) in key.index else np.nan for d, t in zip(E.d0, E.t)]
    E['loser'] = E.tir < -0.10; E['win'] = E.tir > 0.30
    ok = E.pe1.notna() & (E.pe0 > 0) & (E.pe1 > 0) & (E.eps0 > 0) & (E.eps1 > 0)
    E['eps_cagr'] = np.where(ok, (E.eps1 / E.eps0) ** (4 / E.q) - 1, np.nan)
    L = E[E.loser].copy(); L['tipo_k'] = L.apply(pk.kind, axis=1)

    def tipo_l(r):
        acima = pd.notna(r.gap_g) and r.gap_g > 0.15 and pd.notna(r.gap_pe) and r.gap_pe > 1.3
        nao_ent = pd.notna(r.eps_cagr) and pd.notna(r.g0) and r.eps_cagr < r.g0 - 0.10
        if r.tipo_k.startswith('Queda curta'): return 'Queda curta (≤ 1 trimestre)'
        if acima and nao_ent: return 'Crescimento não entregue, precificada acima da indústria'
        if nao_ent: return 'Crescimento não entregue (preço normal)'
        return 'Outros (múltiplo/evento com crescimento entregue)'
    L['tipo_l'] = L.apply(tipo_l, axis=1)
    Lu = L.sort_values('R').drop_duplicates(['t', 'd0'])
    cruz = pd.crosstab(Lu.tipo_k, Lu.tipo_l).to_dict()
    mult_k = Lu[Lu.tipo_k == 'Múltiplo comprimiu (lucro ok)']
    reclass = dict(tipos_l=Lu.tipo_l.value_counts().to_dict(), cruz=cruz,
                   mult_era_nao_entregue=float((mult_k.tipo_l == 'Crescimento não entregue, precificada acima da indústria').mean()) if len(mult_k) else None,
                   n_mult=int(len(mult_k)))
    worst = [[r.t, NAMES.get(r.cart, pk.NAMES.get(r.cart, r.cart)), str(r.d0.date()), str(r.d1.date()), float(r.R), float(r.tir),
              *[None if pd.isna(v) else float(v) for v in (r.g0, r.g_med, r.gap_g, r.pe0, r.pe_med, r.gap_pe, r.pe1, r.eps_cagr, r.roic0, r.roic1, r.rb2_med)],
              r.tipo_l] for r in Lu.head(20).itertuples()]
    # perfil: perdedores × vencedores × demais
    E['grupo'] = np.where(E.loser, 'Perdedores', np.where(E.win, 'Grandes vencedores', 'Demais'))
    prof = {g: dict(n=int(len(x)), g0=med(x.g0), g_med=med(x.g_med), gap_g=med(x.gap_g), pe0=med(x.pe0), pe_med=med(x.pe_med), gap_pe=med(x.gap_pe),
                    eps_cagr=med(x.eps_cagr), entregue_menos_10=float((x.eps_cagr < x.g0 - 0.10).sum() / max(1, x.eps_cagr.notna().sum())),
                    rb2_med=med(x.rb2_med)) for g, x in E.groupby('grupo')}
    # sinais (a)(b)(c): parâmetro escolhido na descoberta
    U = E.sort_values('tir').drop_duplicates(['t', 'd0'])
    cand = {}
    for X in (0.10, 0.20, 0.30): cand[f'(a) gap de crescimento > {int(X*100)} p.p.'] = ('a1', lambda u, X=X: u.gap_g > X)
    for Y in (1.5, 2.0, 3.0): cand[f'(a) P/L > {Y:g}× a indústria'] = ('a2', lambda u, Y=Y: u.gap_pe > Y)
    for X in (0.10, 0.20, 0.30):
        for Y in (1.5, 2.0, 3.0): cand[f'(a) gap g > {int(X*100)} p.p. E P/L > {Y:g}× indústria'] = ('a3', lambda u, X=X, Y=Y: (u.gap_g > X) & (u.gap_pe > Y))
    for cut in (-0.10, 0.0):
        cand[f'(b) bear v2 (mediana) ≤ {int(cut*100)}%'] = ('b', lambda u, cut=cut: u.rb2_med <= cut)
        cand[f'(c) bear v2 (p70) ≤ {int(cut*100)}%'] = ('c', lambda u, cut=cut: u.rb2_p70 <= cut)
    res_all = {k: sig_eval(U, f) for k, (fam, f) in cand.items()}
    chosen = {}
    for fam in ('a1', 'a2', 'a3', 'b', 'c'):
        ks = [k for k, (fm, _) in cand.items() if fm == fam]
        best = max(ks, key=lambda k: res_all[k]['desc']['lift'] or 0)
        chosen[fam] = best
    sinais = [dict(sinal=chosen[f], **res_all[chosen[f]]) for f in chosen]
    passed = [s['sinal'] for s in sinais if s['passa']]
    print('reclass', reclass['tipos_l'], 'mult->', reclass['mult_era_nao_entregue'])
    for s in sinais: print(s['sinal'], s['passa'], {p: (round(s[p]['lift'] or 0, 2), round(s[p]['rec_perd'] or 0, 2), round(s[p]['rec_venc'] or 0, 2)) for p in ('desc', 'conf')})
    # carteiras: atual, bear antigo e (se passar) o sinal aprovado; regra de venda à parte
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    Fw = A.shift(-4) / A - 1

    def queda30(Wx):
        v = [Fw.at[d, t] for k in KEYS for d, w in Wx[k].items() if d in Fw.index for t in w.index if t in Fw.columns and np.isfinite(Fw.at[d, t])]
        return float(np.mean(np.array(v) <= -0.30)) if v else None

    def queda30_k(Wk):
        v = [Fw.at[d, t] for d, w in Wk.items() if d in Fw.index for t in w.index if t in Fw.columns and np.isfinite(Fw.at[d, t])]
        return float(np.mean(np.array(v) <= -0.30)) if v else None

    def build_W(cx):
        W0 = b8.weights(cx); W0['n2t20'] = especiais_nova(cx)
        return W0
    c_now = c.copy(); c_now['bear_ok'] = True                       # versão atual (sem bear)
    variants = {'Atual (sem filtro)': c_now}
    c_old = c.copy(); c_old.loc[~c_old.bear_ok, 'excluded'] = True; variants['Bear antigo'] = c_old
    for s in passed:
        fam, f = cand[s]; cx = c_now.copy(); m = f(cx).fillna(False).astype(bool); cx.loc[m, 'excluded'] = True; cx.loc[m, 'bear_ok'] = False
        variants[s] = cx
    port = {}
    for vn, cx in variants.items():
        Wx = build_W(cx)
        if vn == 'Atual (sem filtro)': Wnow = Wx
        res, _ = metrics_all(Wx, cx, adj, dates, spy, rf, False)
        for k in KEYS: res[k]['queda30'] = queda30_k(Wx[k])
        port[vn] = res
        print(vn, {k: round(v['cagr'], 4) for k, v in res.items()}, flush=True)
    # regra de venda sobre a versão atual
    Ws = {k: sell_rule(Wnow[k], c_now, D) for k in KEYS}
    res, _ = metrics_all(Ws, c_now, adj, dates, spy, rf, False)
    for k in KEYS: res[k]['queda30'] = queda30_k(Ws[k])
    port['Regra de venda (EPS < 80% da trajetória)'] = res
    print('venda', {k: round(v['cagr'], 4) for k, v in res.items()}, flush=True)
    # robustez da regra de venda e da atual: sem as 3 maiores (pelo ranking da atual) e sem NVIDIA
    rob = {}
    for vn, maker in (('Atual (sem filtro)', lambda cx: build_W(cx)), ('Regra de venda (EPS < 80% da trajetória)', lambda cx: {k: sell_rule(v, cx, D) for k, v in build_W(cx).items() if k in KEYS})):
        rob[vn] = {}
        for lab, ts in (('sem NVIDIA', ['NVDA']), ('sem NVDA, AVGO, META', ['NVDA', 'AVGO', 'META'])):
            cx = c_now[~c_now.ticker.isin(ts)].copy(); Wx = maker(cx)
            rob[vn][lab] = {k: float(stats(run_weighted(Wx[k], adj, dates))['CAGR']) for k in ('top20c', 'n2t20', 'ool', 'hroic')}
    def adopt(vn):
        a, b = port[vn], port['Atual (sem filtro)']
        n = sum(1 for k in KEYS if a[k]['cagr'] >= b[k]['cagr'] - 1e-9 and (a[k]['queda30'] or 0) < (b[k]['queda30'] or 0))
        return n
    adot = {vn: adopt(vn) for vn in port if vn != 'Atual (sem filtro)'}
    navs_b, _, _, _ = bm.load_benchmarks()
    out = dict(reclass=reclass, worst=worst, prof=prof, sinais=sinais, todos={k: {p: v[p] for p in ('desc', 'conf')} | {'passa': v['passa']} for k, v in res_all.items()},
               aprovados=passed, port=port, rob=rob, adot=adot, names=NAMES,
               bench9={k: float(stats(v)['CAGR']) for k, v in navs_b.items()},
               win9={k: [bm.windows(v, navs_b['S&P 500'], y)[0] for y in (3, 5, 10)] for k, v in navs_b.items()},
               periodo=[str(D[0].date()), str(D[-1].date())])
    (ROOT / 'dados_bear_v2.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
    print('adoção (seleções com retorno ≥ e menos quedas):', adot)


if __name__ == '__main__':
    main()
