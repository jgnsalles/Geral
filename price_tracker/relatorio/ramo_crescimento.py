"""Ramo A (2026-11-18, pedido do usuário): o crescimento é previsível?
 1. previsibilidade do crescimento do EPS sem cíclicos/vestuário (e sem financeiras)
 2. o g normalizado do P/E justo prevê o crescimento? R², fórmula, erro e viés (contra a mediana e a constante de 8%)
 3. receita: a passada prevê a futura? prevê o EPS? alavancagem operacional (EPS = a + b·receita)
 4. variantes pré-registradas (PROTOCOLO, 2026-11-18): o crescimento do P/E justo e do retorno esperado vindo de outro preditor
S&P 500 point-in-time, ROIC triangulado. Saída: relatorio/dados_crescimento.json.
Uso: python3 relatorio/ramo_crescimento.py [analise|carteiras]"""
import sys, json, pathlib
from multiprocessing import Pool
import numpy as np, pandas as pd
from scipy import stats as st
MODE = sys.argv[1] if len(sys.argv) > 1 else 'analise'; sys.argv = sys.argv[:1]
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import calc2, top_n  # noqa: E402
import benchmarks as bm  # noqa: E402
from backtest import asof  # noqa: E402
from roic3 import load_pit2  # noqa: E402

CACHE = ROOT / 'cache_receita.pkl'


def rev_one(args):
    tk, ds = args
    p2 = load_pit2(tk)
    if 'revenue' not in p2: return []
    out = []
    for t in ds:
        r = asof(p2['revenue'], t)[0]
        if not r: continue
        last = max(r); v = {y: r[y][0] for y in r}
        rates = []
        for y in range(last - 4, last + 1):
            a, b = v.get(y - 1), v.get(y)
            rates.append(b / a - 1 if a and b is not None and a > 0 else np.nan)
        ok = [x for x in rates if np.isfinite(x)]
        out.append(dict(date=t, ticker=tk, rev=v[last], rev_fy=last, rev_med=float(np.median(ok)) if len(ok) >= 3 else np.nan,
                        rev_last=rates[-1], rev_n=len(ok)))
    return out


c, adj, dates, ref, nm = calc2.sp_data()
D = pd.DatetimeIndex(dates); iq = {d: i for i, d in enumerate(D)}
if CACHE.exists():
    rv = pd.read_pickle(CACHE)
else:
    jobs = [(t, sorted(pd.Timestamp(x) for x in g.date.unique())) for t, g in c.groupby('ticker')]
    with Pool(4) as pool:
        res = pool.map(rev_one, jobs, chunksize=8)
    rv = pd.DataFrame([r for rr in res for r in rr]); rv.to_pickle(CACHE)
p = c.merge(rv, on=['date', 'ticker'], how='left')
p['qi'] = p.date.map(iq)
key = p.set_index(['qi', 'ticker'])
for h in (4, 12, 20):
    f = key[['eps', 'rev']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'{x}_{h}' for x in f.columns]
    p = p.join(f, on=['qi', 'ticker'])
    ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
    p[f'R{h}'] = np.where(ok, (p[f'eps_{h}'] / p.eps) ** (4 / h) - 1, np.nan)        # crescimento anual realizado do EPS
    okr = (p.rev > 0) & (p[f'rev_{h}'] > 0)
    p[f'V{h}'] = np.where(okr, (p[f'rev_{h}'] / p.rev) ** (4 / h) - 1, np.nan)      # crescimento anual realizado da receita
p['pr_med'] = p.growth; p['pr_g'] = p.g; p['pr_8'] = .08
p['pr_rmed'] = p.rev_med; p['pr_rlast'] = p.rev_last
AMOSTRAS = {'Todas': p.ticker.notna(), 'Sem cíclicas e vestuário': ~p.excluded, 'Sem cíclicas, vestuário e financeiras': ~p.excluded & ~p.fin}
CL = (-.5, 1.0)


def avalia(df, y, x):
    """pooled: realizado = a + b·preditor (os dois limitados a −50%..100%); IC = correlação de ordem média por trimestre"""
    z = df.dropna(subset=[y, x])
    err = z[y] - z[x]
    out = dict(n=int(len(z)), mae=float(err.abs().median()), vies=float(err.median()), real_med=float(z[y].median()), prev_med=float(z[x].median()))
    if z[x].nunique() > 5:
        yy, xx = z[y].clip(*CL), z[x].clip(*CL)
        sl = st.linregress(xx, yy)
        ics = [st.spearmanr(g[x], g[y])[0] for _, g in z.groupby('date') if len(g) > 30 and g[x].nunique() > 5]
        ics = np.array([v for v in ics if np.isfinite(v)])
        out.update(a=float(sl.intercept), b=float(sl.slope), r2=float(sl.rvalue ** 2), ic=float(ics.mean()), ic_pos=float((ics > 0).mean()),
                   ic_t=float(ics.mean() / (ics.std() / np.sqrt(max(len(ics) / 4, 1)))))
        # erro do preditor calibrado (a + b·x), para comparar só a informação
        out['mae_cal'] = float((yy - (sl.intercept + sl.slope * xx)).abs().median())
    return out


OUT = {'periodo': [str(D[0].date()), str(D[-1].date())]}
if MODE == 'analise':
    PRED = [('pr_med', 'Mediana de 5 anos do EPS (o nosso)'), ('pr_g', 'g normalizado do P/E justo'), ('pr_8', 'Constante de 8%'),
            ('pr_rmed', 'Mediana de 5 anos da receita'), ('pr_rlast', 'Receita do último ano')]
    eps = {}
    for am, m in AMOSTRAS.items():
        eps[am] = {str(h): {lab: avalia(p[m], f'R{h}', col) for col, lab in PRED} for h in (4, 12, 20)}
    OUT['eps'] = eps
    rev = {}
    for am, m in AMOSTRAS.items():
        rev[am] = {str(h): {lab: avalia(p[m], f'V{h}', col) for col, lab in (('pr_rmed', 'Mediana de 5 anos da receita'), ('pr_rlast', 'Receita do último ano'),
                                                                            ('pr_8', 'Constante de 8%'), ('pr_med', 'Mediana de 5 anos do EPS'))} for h in (4, 12, 20)}
    OUT['receita'] = rev
    lev = {}
    for am, m in AMOSTRAS.items():
        lev[am] = {str(h): avalia(p[m].assign(_v=p[m][f'V{h}']), f'R{h}', '_v') for h in (4, 12, 20)}
    OUT['alavancagem'] = lev
    # quintis do previsto x realizado (3 anos, sem cíclicos): EPS pela mediana do EPS, pela receita; receita pela receita
    q = p[~p.excluded].copy(); quint = {}
    for nm_, x, y in (('EPS pela mediana do EPS', 'pr_med', 'R12'), ('EPS pela mediana da receita', 'pr_rmed', 'R12'), ('Receita pela mediana da receita', 'pr_rmed', 'V12')):
        z = q.dropna(subset=[x, y]).copy()
        z['qq'] = z.groupby('date')[x].transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False))
        quint[nm_] = z.groupby('qq').agg(prev=(x, 'median'), real=(y, 'median')).round(4).values.tolist()
    OUT['quintis'] = quint
    # estabilidade: dispersão anual do crescimento (EPS x receita), mediana por empresa
    OUT['dispersao'] = dict(eps=float(p[~p.excluded].zgrowth.abs().median()),
                            rev_iqr=float(q.groupby('ticker').V4.std().median()), eps_iqr=float(q.groupby('ticker').R4.std().median()))
    (ROOT / 'dados_crescimento.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    for am in AMOSTRAS:
        print('==', am)
        for h in ('4', '12'):
            for lab, r in OUT['eps'][am][h].items():
                print(f"  EPS h={h:>2} {lab:38s} r2={r.get('r2', np.nan):.3f} a={r.get('a', np.nan):+.3f} b={r.get('b', np.nan):+.3f} ic={r.get('ic', np.nan):+.3f} t={r.get('ic_t', np.nan):+.1f} mae={r['mae']:.3f} mae_cal={r.get('mae_cal', np.nan):.3f} vies={r['vies']:+.3f} n={r['n']}")
            for lab, r in OUT['receita'][am][h].items():
                print(f"  REC h={h:>2} {lab:38s} r2={r.get('r2', np.nan):.3f} a={r.get('a', np.nan):+.3f} b={r.get('b', np.nan):+.3f} ic={r.get('ic', np.nan):+.3f} mae={r['mae']:.3f} vies={r['vies']:+.3f}")
            r = OUT['alavancagem'][am][h]; print(f"  ALAV h={h:>2} EPS = {r['a']:+.3f} + {r['b']:.2f}·receita  r2={r['r2']:.3f} ic={r['ic']:+.3f}")
    print(OUT['quintis'], OUT['dispersao'])

if MODE == 'carteiras':
    import combos as cb
    from pesos import run_weighted
    from backtest import stats
    OUT = json.loads((ROOT / 'dados_crescimento.json').read_text())
    adjp = adj
    A = adjp.reindex(D, method='ffill')
    # coeficientes da V1 estimados só em 2011-2018 (sem cíclicos e vestuário), aplicados a todas as datas
    tr_ = p[~p.excluded & (p.date <= pd.Timestamp('2018-12-31'))].dropna(subset=['R12', 'rev_med'])
    sl = st.linregress(tr_.rev_med.clip(*CL), tr_.R12.clip(*CL))
    A1, B1 = float(sl.intercept), float(sl.slope)
    OUT['v1_coef'] = dict(a=A1, b=B1, r2=float(sl.rvalue ** 2), n=int(len(tr_)))
    print(f'V1: EPS previsto = {A1:+.3f} + {B1:.3f}·receita (2011-2018, R² {sl.rvalue ** 2:.3f})')
    # valor de mercado para todas as candidatas (como em ramo_rerating)
    need = p[~p.excluded & (p.roic >= .12) & p.pe.gt(0)].copy()
    need['mcap2'] = top_n.mcap_us(need, need)
    p = p.merge(need[['date', 'ticker', 'mcap2']], on=['date', 'ticker'], how='left'); p['mcap'] = p.mcap.fillna(p.mcap2)

    def valuation(x, G, gfix=None):
        """P/E justo e retorno esperado como em validation_portfolios.classify, com o crescimento G no lugar da mediana do EPS"""
        out = []
        for d, y in x.assign(_G=G).groupby('date'):
            y = y.copy()
            if gfix is None:
                g = cb.g_rank(y.assign(growth=y._G), 0.07)
            else:
                g = pd.Series(np.where(y.fin, gfix - .005, gfix), index=y.index)
            r = y.roic.clip(upper=1.0)
            fpe = np.where(r > 0, (1 - g / r) / (0.085 - g), np.nan)
            base = fpe * y.eps * (1 + y._G) ** 2 / y.price
            rf = np.where(base > 0, np.sqrt(np.clip(base, 0, None)) - 1, np.nan) + y.dy
            rc = y._G + y.dy
            both = np.isfinite(rf) & rc.notna()
            y['v_fpe'] = fpe; y['v_ret'] = np.where(both, (rf + rc) / 2, y._G)
            y['v_gap'] = np.where((fpe > 0) & (y.pe > 0), np.log(np.where(fpe > 0, fpe, np.nan) / y.pe), np.nan)
            out.append(y)
        return pd.concat(out)

    G1 = (A1 + B1 * p.rev_med.clip(*CL))
    VAR = {'Registrada': valuation(p, p.growth), 'V1a receita no valuation': valuation(p, G1), 'V2 sem previsão de crescimento': valuation(p, pd.Series(.08, index=p.index), gfix=.0525)}
    VAR['V1b receita também no filtro'] = VAR['V1a receita no valuation']

    def pick(df, sort, n=20):
        df = calc2.dd_firm(df)
        return {d: g.sort_values(sort, ascending=False).head(n) for d, g in df.groupby('date')}

    SEL = {}
    for vk, x in VAR.items():
        x = x[~x.excluded & x.mcap.notna()]
        gfilt = (x.rev_med >= .10) if vk.startswith('V1b') else (x.growth >= .15)
        q = x[x['cat'].notna() & (x.roic >= .12) & gfilt & (x.pe >= 4) & x.v_ret.notna()]
        SEL[f'Top 20 · {vk}'] = pick(q, ['v_ret', 'roic'])
        b_ = x[(x.roic >= .12) & x.v_gap.notna() & ((x.rev_med >= .10) if vk.startswith('V1b') else True)]
        SEL[f'ROIC alto descontado · {vk}'] = pick(b_, ['v_gap', 'roic'])
    Wn = {k: {d: calc2.cap_w(g) for d, g in v.items()} for k, v in SEL.items()}
    navs9, n9, _, _ = bm.load_benchmarks()
    navs = dict(navs9); nn = dict(n9)
    for k in SEL:
        navs[k] = run_weighted(Wn[k], adjp, dates); nn[k] = float(np.mean([len(g) for g in SEL[k].values()]))
    R = navs['S&P 500']; tab = {}
    for k, s in navs.items():
        s = s.dropna(); stt = stats(s); w = {y: bm.windows(s, R, y) for y in (3, 5, 10)}
        tab[k] = dict(cagr=stt['CAGR'], vol=stt['Vol'], dd=stt['MaxDD'], n=nn.get(k), w3=w[3][0], w5=w[5][0], w10=w[10][0], p3=w[3][1], p5=w[5][1])
    OUT['carteiras'] = tab
    (ROOT / 'crescimento_tabela.md').write_text('\n'.join(bm.bench_table(navs, nn)))
    M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()})
    show = ['S&P 500'] + list(SEL)
    OUT['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(v) else round(float(v), 4) for v in M[k] / M[k].dropna().iloc[0]] for k in show}}
    # decomposição em 3 anos (EPS, re-rating, dividendos)
    for h in (4, 12):
        f = key[['pe']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'pe_{h}']
        p = p.join(f, on=['qi', 'ticker'])
        trr = [A.at[D[iq[d] + h], t] / A.at[d, t] if iq[d] + h < len(D) and t in A and A.at[d, t] > 0 else np.nan for d, t in zip(p.date, p.ticker)]
        p[f'lt_{h}'] = np.log(np.array(trr, dtype=float))
        ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
        p[f'le_{h}'] = np.where(ok, np.log(p[f'eps_{h}'] / p.eps), np.nan); p[f'lp_{h}'] = np.where(ok, np.log(p[f'pe_{h}'] / p.pe), np.nan)
        p[f'ld_{h}'] = p[f'lt_{h}'] - p[f'le_{h}'] - p[f'lp_{h}']
    ann = lambda x, h: np.expm1(x * 4 / h)
    dec = {}
    for k in SEL:
        rows = [(d, t, w) for d, ws in Wn[k].items() for t, w in ws.items()]
        hh = pd.DataFrame(rows, columns=['date', 'ticker', 'w']).merge(p[['date', 'ticker', 'le_12', 'lp_12', 'ld_12', 'lt_12', 'rev_med', 'R12', 'V12']], on=['date', 'ticker'], how='left')
        y = hh.dropna(subset=['le_12', 'lp_12', 'lt_12'])
        g = y.groupby('date').apply(lambda z_: pd.Series({c_: np.average(z_[c_], weights=z_.w) for c_ in ('le_12', 'lp_12', 'ld_12', 'lt_12')}), include_groups=False).mean()
        dec[k] = dict(eps=ann(g.le_12, 12), rr=ann(g.lp_12, 12), div=ann(g.ld_12, 12), tot=ann(g.lt_12, 12),
                      rev_prev=float(hh.rev_med.median()), rev_real=float(hh.V12.median()), eps_real=float(hh.R12.median()))
    OUT['decomp'] = dec
    best = max(SEL, key=lambda k: tab[k]['cagr'])
    vk = best.split(' · ')[1]; x = VAR[vk]; x = x[~x.excluded & x.mcap.notna() & (x.ticker != 'NVDA')]
    gfilt = (x.rev_med >= .10) if vk.startswith('V1b') else (x.growth >= .15)
    if best.startswith('Top 20'):
        snv = pick(x[x['cat'].notna() & (x.roic >= .12) & gfilt & (x.pe >= 4) & x.v_ret.notna()], ['v_ret', 'roic'])
    else:
        snv = pick(x[(x.roic >= .12) & x.v_gap.notna() & ((x.rev_med >= .10) if vk.startswith('V1b') else True)], ['v_gap', 'roic'])
    nv = run_weighted({d: calc2.cap_w(g) for d, g in snv.items()}, adjp, dates)
    OUT['sem_nvda'] = dict(carteira=best, com=tab[best]['cagr'], sem=stats(nv.dropna())['CAGR'], w3_sem=bm.windows(nv, R, 3)[0])
    last = max(SEL[best]); OUT['hoje'] = {k: [[t, nm(t), float(w)] for t, w in Wn[k][last].sort_values(ascending=False).items()] for k in (best,)}
    OUT['hoje_data'] = str(pd.Timestamp(last).date())
    (ROOT / 'dados_crescimento.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
    for k in ['S&P 500'] + list(SEL):
        t = tab[k]; print(f"{k:55s} {t['cagr']:.1%} vol {t['vol']:.1%} dd {t['dd']:.1%} w3 {t['w3']:.0%} w5 {t['w5']:.0%} w10 {t['w10']:.0%} n {t['n'] or 0:.1f}")
    print(json.dumps(OUT['decomp'], ensure_ascii=False)[:2500]); print(OUT['sem_nvda'])
