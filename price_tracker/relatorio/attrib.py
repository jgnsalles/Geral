"""Atribuição e calibração do modelo determinístico (S&P 500 point-in-time, ROIC triangulado), pedido de 2026-11-16.
6 carteiras: Top 20, OoL (novo), High ROIC, High Growth, Excepcionais, JG+G (Fórmula Mágica com crescimento: ROIC + crescimento do EPS + P/L). Passos:
 1. decomposição do retorno (crescimento do EPS, re-rating, dividendos) das posições, carteira x universo
 2. as previsões se confirmam? persistência do ROIC, do crescimento, convergência ao P/E justo, retorno esperado por decil
 3. o que explica o retorno: variáveis conhecidas na compra x surpresas (Fama-MacBeth)
 4. onde errou: piores/melhores contribuições e as grandes altas que ficaram de fora (e por quê)
 5. quanto vale o julgamento: veto oráculo x aleatório, curva de habilidade, sinais dentro das OoL (descoberta 2012-18, confirmação 2019-26)
Saída: relatorio/dados_attrib.json. Uso: python3 relatorio/attrib.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
from scipy import stats as st
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import calc2  # noqa: E402

rng = np.random.default_rng(7)
c, adj, dates, ref, nm = calc2.sp_data()
W = calc2.weights(c)
OOL = 'Opportunity of Lifetime'
ool = c[(c['cat'] == OOL) & ~c.excluded]
W['ool'] = {d: pd.Series(1 / len(g), index=g.ticker) for d, g in ool.groupby('date')}
PORTS = {'top20': 'Top 20', 'ool': 'OoL', 'hroic': 'High ROIC', 'hgrowth': 'High Growth', 'n2': 'Excepcionais', 'magicg': 'JG+G'}
D = pd.DatetimeIndex(dates); iq = {d: i for i, d in enumerate(D)}
A = adj.reindex(D, method='ffill')

# ---------------- painel com o futuro ----------------
p = c[['date', 'ticker', 'fin', 'price', 'eps', 'pe', 'roic', 'growth', 'ret', 'fair_pe', 'g', 'cat', 'excluded', 'sector', 'industry', 'mcap',
       'zgrowth', 'roic_marg', 'dy', 'ry4', 'ry5', 'ry6', 'ry1', 'ry2', 'ry3', 'gy5']].copy()
p['qi'] = p.date.map(iq)
key = p.set_index(['qi', 'ticker'])
for h in (4, 12, 20):
    f = key[['eps', 'pe', 'roic', 'price']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)])
    f.columns = [f'{x}_{h}' for x in f.columns]
    p = p.join(f, on=['qi', 'ticker'])
    tr = []
    for d, t in zip(p.date, p.ticker):
        i = iq[d]
        if i + h >= len(D) or t not in A: tr.append(np.nan); continue
        a0, a1 = A.at[d, t], A.at[D[i + h], t]
        tr.append(a1 / a0 if a0 > 0 and np.isfinite(a1) else np.nan)
    p[f'tr_{h}'] = tr
    spy = {d: (A.at[D[iq[d] + h], 'SPY'] / A.at[d, 'SPY'] if iq[d] + h < len(D) else np.nan) for d in D}
    p[f'spy_{h}'] = p.date.map(spy)
    p[f'lt_{h}'] = np.log(p[f'tr_{h}'])
    ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
    p[f'le_{h}'] = np.where(ok, np.log(p[f'eps_{h}'] / p.eps), np.nan)          # crescimento do EPS
    p[f'lp_{h}'] = np.where(ok, np.log(p[f'pe_{h}'] / p.pe), np.nan)            # re-rating
    p[f'ld_{h}'] = p[f'lt_{h}'] - p[f'le_{h}'] - p[f'lp_{h}']                    # dividendos e resíduo
    p[f'ex_{h}'] = (p[f'tr_{h}'] / p[f'spy_{h}']) ** (4 / h) - 1                  # excesso anual vs S&P
    p[f'cagr_{h}'] = p[f'tr_{h}'] ** (4 / h) - 1
ann = lambda x, h: np.expm1(x * 4 / h)
OUT = {'periodo': [str(D[0].date()), str(D[-1].date())], 'n_obs': int(len(p))}

# ---------------- 1. decomposição ----------------
def hold_panel(k):
    rows = []
    for d, w in W[k].items():
        for t, x in w.items(): rows.append((pd.Timestamp(d), t, x))
    h = pd.DataFrame(rows, columns=['date', 'ticker', 'w'])
    return h.merge(p, on=['date', 'ticker'], how='left')


H = {k: hold_panel(k) for k in PORTS}
dec = {}
for h in (4, 12):
    tab = []
    univ = p.dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
    u = univ.groupby('date')[[f'le_{h}', f'lp_{h}', f'ld_{h}', f'lt_{h}']].mean().mean()
    tab.append(dict(nome='Universo (S&P, peso igual)', eps=ann(u[f'le_{h}'], h), rr=ann(u[f'lp_{h}'], h), div=ann(u[f'ld_{h}'], h), tot=ann(u[f'lt_{h}'], h)))
    for k, nmk in PORTS.items():
        x = H[k].dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
        g = x.groupby('date').apply(lambda z: pd.Series({c_: np.average(z[c_], weights=z.w) for c_ in (f'le_{h}', f'lp_{h}', f'ld_{h}', f'lt_{h}')}), include_groups=False).mean()
        cov = 1 - len(x) / max(1, len(H[k]))
        tab.append(dict(nome=nmk, eps=ann(g[f'le_{h}'], h), rr=ann(g[f'lp_{h}'], h), div=ann(g[f'ld_{h}'], h), tot=ann(g[f'lt_{h}'], h), sem_dado=cov))
    dec[h] = tab
OUT['decomp'] = {str(h): v for h, v in dec.items()}

# ---------------- 2. previsões ----------------
nf = p[~p.fin]
def ic_by_date(df, a, b, min_n=20):
    v = [st.spearmanr(g[a], g[b])[0] for _, g in df.dropna(subset=[a, b]).groupby('date') if len(g) >= min_n]
    v = np.array(v); return dict(ic=float(np.mean(v)), pos=float((v > 0).mean()), n=len(v))

pers = {}
for h in (4, 12, 20):
    pers[str(h)] = ic_by_date(nf, 'roic', f'roic_{h}')
OUT['roic_pers'] = pers
B = [-np.inf, .12, .20, .30, np.inf]; BL = ['< 12%', '12–20%', '20–30%', '> 30%']
trans = {}
for h in (12, 20):
    x = nf.dropna(subset=['roic', f'roic_{h}'])
    m = pd.crosstab(pd.cut(x.roic, B, labels=BL), pd.cut(x[f'roic_{h}'], B, labels=BL), normalize='index')
    trans[str(h)] = m.round(4).values.tolist()
OUT['roic_trans'] = {'labels': BL, 'm': trans}
# ROIC das carteiras ao longo do tempo (mediana na compra x 1, 3, 5 anos depois)
rp = {}
for k, nmk in PORTS.items():
    x = H[k]
    rp[nmk] = [float(x.roic.median())] + [float(x[f'roic_{h}'].median()) for h in (4, 12, 20)] + [float((x['roic_12'] >= .12).mean() / x['roic_12'].notna().mean())]
xu = nf
rp['Universo'] = [float(xu.roic.median())] + [float(xu[f'roic_{h}'].median()) for h in (4, 12, 20)] + [float((xu['roic_12'] >= .12).mean() / xu['roic_12'].notna().mean())]
OUT['roic_port'] = rp

# crescimento: previsto x realizado
gr = {}
for h in (12, 20):
    x = p.dropna(subset=['growth', f'le_{h}']).copy(); x['real'] = ann(x[f'le_{h}'], h)
    ic = ic_by_date(x, 'growth', 'real')
    xc = x[(x.growth.between(-.5, 1)) & x.real.between(-.5, 1)]
    sl = st.linregress(xc.growth, xc.real)
    q = x.groupby(pd.qcut(x.growth, 5, labels=False, duplicates='drop')).agg(prev=('growth', 'median'), real=('real', 'median'))
    gr[str(h)] = dict(ic=ic, slope=float(sl.slope), quint=q.round(4).values.tolist())
    for k, nmk in PORTS.items():
        y = H[k].dropna(subset=['growth', f'le_{h}'])
        gr[str(h)][nmk] = [float(y.growth.median()), float(ann(y[f'le_{h}'], h).median())]
OUT['growth'] = gr

# re-rating: o P/L anda em direção ao P/E justo?
rr = {}
for h in (4, 12, 20):
    x = p[(p.pe > 0) & (p.fair_pe > 0)].dropna(subset=[f'lp_{h}']).copy()
    x['gap'] = np.log(x.fair_pe / x.pe); x = x[x.gap.between(-3, 3)]
    sl = [st.linregress(g.gap, g[f'lp_{h}']).slope for _, g in x.groupby('date') if len(g) > 30]
    hit = float((np.sign(x.gap) == np.sign(x[f'lp_{h}'])).mean())
    q = x.groupby(pd.qcut(x.gap, 5, labels=False)).agg(gap=('gap', 'median'), mov=(f'lp_{h}', 'median'))
    rr[str(h)] = dict(slope=float(np.mean(sl)), hit=hit, quint=[[float(a), float(b)] for a, b in q.values])
OUT['rerating'] = rr

# retorno esperado: decis e IC (universo e só as de qualidade)
qual = (~p.excluded) & (p.roic >= .12) & (p.growth >= .15) & p['cat'].notna()
er = {}
for h in (4, 12):
    x = p.dropna(subset=['ret', f'ex_{h}']).copy()
    x['dec'] = x.groupby('date').ret.transform(lambda s: pd.qcut(s.rank(method='first'), 10, labels=False))
    er[str(h)] = dict(dec=x.groupby('dec')[f'ex_{h}'].mean().round(4).tolist(), ic=ic_by_date(x, 'ret', f'ex_{h}'))
    xq = x[qual.loc[x.index]]
    er[str(h)]['ic_qual'] = {nmv: ic_by_date(xq, v, f'ex_{h}', 10) for nmv, v in (('Retorno esperado', 'ret'), ('ROIC', 'roic'), ('Crescimento', 'growth'),
                                                                              ('P/L (menor melhor)', 'pe'), ('Valor de mercado', 'mcap'))}
    er[str(h)]['ic_qual']['P/L (menor melhor)']['ic'] *= -1
    er[str(h)]['ic_qual']['P/L (menor melhor)']['pos'] = 1 - er[str(h)]['ic_qual']['P/L (menor melhor)']['pos']
    xq = xq.copy(); xq['qd'] = xq.groupby('date').ret.transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False) if len(s) >= 10 else np.nan)
    er[str(h)]['quint_qual'] = xq.groupby('qd')[f'ex_{h}'].mean().round(4).tolist()
OUT['exp_ret'] = er

# ---------------- 3. o que explica o retorno ----------------
z = lambda s: (s - s.mean()) / s.std()
OUT['fm'] = {}
for h in (4, 12):
    fm = {'ante': [], 'eps': [], 'roic': [], 'ambos': [], 'tudo': [], 'coef_ante': []}
    x = p[~p.fin & (p.eps > 0)].dropna(subset=[f'lt_{h}', 'roic', 'growth', 'pe', 'ret', f'le_{h}', f'roic_{h}']).copy()
    x['droic'] = x[f'roic_{h}'] - x.roic
    for d, g in x.groupby('date'):
        if len(g) < 60: continue
        y = g[f'lt_{h}'] - g[f'lt_{h}'].mean()
        Xa = [z(g.roic.clip(-1, 2)), z(g.growth.clip(-.5, 1.5)), z(np.log(g.pe.clip(1, 200))), z(g.ret.clip(-.5, 1.5))]
        Xe = [z(g[f'le_{h}'].clip(-3, 3))]; Xr = [z(g.droic.clip(-1, 1))]
        for k_, cols_ in (('ante', Xa), ('eps', Xe), ('roic', Xr), ('ambos', Xe + Xr), ('tudo', Xa + Xe + Xr)):
            X = np.column_stack([np.ones(len(g))] + cols_)
            b_, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ b_
            fm[k_].append(1 - res.var() / y.var())
            if k_ == 'ante': fm['coef_ante'].append(b_[1:])
    ca = np.array(fm['coef_ante'])
    OUT['fm'][str(h)] = dict(r2={k_: float(np.mean(v)) for k_, v in fm.items() if k_ != 'coef_ante'}, coef_ante=ca.mean(axis=0).round(4).tolist(),
                             t_ante=(ca.mean(axis=0) / (ca.std(axis=0) / np.sqrt(len(ca) / max(h, 1)))).round(2).tolist())
# variância do retorno de 1 e 3 anos: quanto vem do EPS, do re-rating e dos dividendos
vd = {}
for h in (4, 12, 20):
    xx = p.dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
    xx = xx[xx[f'lt_{h}'].between(-3, 3)]
    sh = {}
    for comp in ('le', 'lp', 'ld'):
        sh[comp] = float(np.mean([np.cov(g[f'{comp}_{h}'], g[f'lt_{h}'])[0, 1] / g[f'lt_{h}'].var() for _, g in xx.groupby('date') if len(g) > 30]))
    vd[str(h)] = sh
OUT['var_decomp'] = vd

# ---------------- 4. onde errou ----------------
qret = A.pct_change().shift(-1)  # retorno do trimestre seguinte
contrib = {}
for k in ('top20', 'ool', 'n2', 'magicg'):
    rows = []
    for d, w in W[k].items():
        d = pd.Timestamp(d)
        if d not in qret.index or d == D[-1]: continue
        for t, x in w.items():
            r = qret.at[d, t] if t in qret else np.nan
            rows.append((d, t, x, r))
    df = pd.DataFrame(rows, columns=['date', 'ticker', 'w', 'r'])
    df['c'] = df.w * df.r.fillna(0)
    g = df.groupby('ticker').agg(contrib=('c', 'sum'), tri=('date', 'count'), first=('date', 'min'), last=('date', 'max')).sort_values('contrib')
    def drv(t, a, b):
        i0, i1 = iq[a], min(iq[b] + 1, len(D) - 1)
        x0 = key.loc[(i0, t)] if (i0, t) in key.index else None; x1 = key.loc[(i1, t)] if (i1, t) in key.index else None
        if x0 is None or x1 is None: return dict(eps=None, rr=None, roic0=None, roic1=None)
        yrs = max((i1 - i0) / 4, .25)
        e = (x1.eps / x0.eps) ** (1 / yrs) - 1 if x0.eps > 0 and x1.eps > 0 else None
        r_ = (x1.pe / x0.pe) ** (1 / yrs) - 1 if x0.pe > 0 and x1.pe > 0 else None
        return dict(eps=e, rr=r_, roic0=float(x0.roic) if pd.notna(x0.roic) else None, roic1=float(x1.roic) if pd.notna(x1.roic) else None)
    sel = pd.concat([g.head(10), g.tail(10)])
    contrib[PORTS[k]] = [dict(t=t, nome=nm(t), contrib=float(r.contrib), tri=int(r.tri), de=str(r['first'].date()), ate=str(r['last'].date()), **drv(t, r['first'], r['last']))
                         for t, r in sel.iterrows()]
OUT['contrib'] = contrib

# as maiores altas que ficaram de fora: 10% melhores em 3 anos, em cada data
def reason(r):
    if pd.isna(r.roic) or pd.isna(r.growth) or pd.isna(r.ret): return 'Sem dados suficientes'
    if r.excluded: return 'Cíclica ou vestuário'
    if r.roic < .12: return 'ROIC < 12%'
    if r.growth < .15: return 'Crescimento < 15%'
    if not (r.pe >= 4): return 'Prejuízo ou P/L < 4'
    return 'Qualidade, mas fora das 20 de maior retorno esperado'

top20set = {(pd.Timestamp(d), t) for d, w in W['top20'].items() for t in w.index}
oolset = {(pd.Timestamp(d), t) for d, w in W['ool'].items() for t in w.index}
x = p.dropna(subset=['ex_12']).copy()
x['top'] = x.groupby('date').ex_12.transform(lambda s: s >= s.quantile(.9))
w10 = x[x.top].copy()
w10['in_t20'] = [(d, t) in top20set for d, t in zip(w10.date, w10.ticker)]
w10['in_ool'] = [(d, t) in oolset for d, t in zip(w10.date, w10.ticker)]
miss = w10[~w10.in_t20].copy(); miss['why'] = miss.apply(reason, axis=1)
OUT['misses'] = dict(pct_t20=float(w10.in_t20.mean()), pct_ool=float(w10.in_ool.mean()), base_t20=float(len(top20set) / len(x)),
                     why=miss.why.value_counts(normalize=True).round(4).to_dict())
# o que essas vencedoras tinham de diferente: ROIC e crescimento depois (realizado) x na data
miss['g_real'] = ann(miss.le_12, 12); miss['droic'] = miss.roic_12 - miss.roic
w10['g_real'] = ann(w10.le_12, 12)
OUT['misses']['por_motivo'] = {k: dict(n=int(len(g)), roic0=float(g.roic.median()), roic3=float(g.roic_12.median()), g0=float(g.growth.median()),
                                       g3=float(g.g_real.median()), ex=float(g.ex_12.median()))
                               for k, g in miss.groupby('why')}
# os nomes: maiores altas em 10 anos (set/2016 -> set/2026) entre membros na data, e se/por que ficaram de fora
d0 = D[iq[D[-1]] - 40]
x0 = p[p.date == d0].dropna(subset=['tr_20']).copy()
x0['tr10'] = [A.at[D[-1], t] / A.at[d0, t] if t in A and A.at[d0, t] > 0 else np.nan for t in x0.ticker]
x0 = x0.dropna(subset=['tr10']).sort_values('tr10', ascending=False).head(25)
names = []
for _, r in x0.iterrows():
    ever = {k: int(sum(r.ticker in W[k][dd].index for dd in W[k])) for k in ('top20', 'ool')}
    last = key.loc[(len(D) - 1, r.ticker)] if (len(D) - 1, r.ticker) in key.index else None
    names.append(dict(t=r.ticker, nome=nm(r.ticker), tr10=float(r.tr10), why=reason(r), roic0=float(r.roic) if pd.notna(r.roic) else None,
                      roic_hoje=float(last.roic) if last is not None and pd.notna(last.roic) else None, g0=float(r.growth) if pd.notna(r.growth) else None,
                      eps10=float((last.eps / r.eps) ** .1 - 1) if last is not None and r.eps > 0 and last.eps > 0 else None,
                      tri_t20=ever['top20'], tri_ool=ever['ool']))
OUT['misses']['nomes'] = names
OUT['misses']['data0'] = str(d0.date())

# ---------------- 5. quanto vale o julgamento ----------------
def port_ret(k, veto=None, keep=4):
    """veto(d, w) -> ações retiradas na data d; o veto vale por `keep` trimestres (julgamento sobre o ano seguinte).
    Retorno trimestral com peso renormalizado; sem preço no trimestre seguinte = 0."""
    out, hist = [], []
    for d in D[:-1]:
        w = W[k].get(d)
        if w is None or len(w) == 0: out.append(0.0); hist.append(set()); continue
        if veto is not None:
            hist.append(set(veto(d, w)))
            ban = set().union(*hist[-keep:])
            keepw = [t for t in w.index if t not in ban]
            if keepw: w = w[keepw] / w[keepw].sum()
        r = qret.loc[d, [t for t in w.index if t in qret]].reindex(w.index).fillna(0)
        out.append(float((w * r).sum()))
    return np.array(out)

cg = lambda r: float(np.prod(1 + r) ** (4 / len(r)) - 1)
fut = p.set_index(['qi', 'ticker'])[['roic', 'roic_4', 'roic_12', 'le_4', 'lp_4', 'lt_4', 'le_12', 'lp_12', 'lt_12']]
def oracle(col, frac=.2, noise=None, sims=1):
    def v(d, w):
        i = iq[d]; n = int(round(len(w) * frac))
        if n == 0: return []
        idx = [(i, t) for t in w.index]
        s = np.array([((fut.loc[j, 'roic_4'] - fut.loc[j, 'roic']) if col == 'droic' else (fut.loc[j, 'roic_12'] - fut.loc[j, 'roic']) if col == 'droic3' else fut.loc[j, col]) if j in fut.index else np.nan for j in idx], dtype=float)
        s = np.where(np.isfinite(s), s, np.nanmedian(s) if np.isfinite(s).any() else 0)
        if noise is not None:
            zs = (s - s.mean()) / (s.std() + 1e-12); rho = noise
            s = rho * zs + np.sqrt(max(1 - rho ** 2, 0)) * rng.standard_normal(len(s))
        return list(w.index[np.argsort(s)[:n]])
    return v

def rand_veto(frac=.2):
    def v(d, w):
        n = int(round(len(w) * frac)); return list(rng.choice(w.index, n, replace=False)) if n else []
    return v

orc = {}
for k in PORTS:
    base = cg(port_ret(k))
    o = dict(base=base)
    for col, lab in (('droic', 'ROIC em 1 ano'), ('droic3', 'ROIC em 3 anos'), ('le_4', 'EPS em 1 ano'), ('le_12', 'EPS em 3 anos'),
                     ('lp_4', 'Re-rating em 1 ano'), ('lt_4', 'Retorno total em 1 ano')):
        o[lab] = cg(port_ret(k, oracle(col))) - base
    o['Aleatório'] = float(np.mean([cg(port_ret(k, rand_veto())) for _ in range(30)])) - base
    orc[PORTS[k]] = o
OUT['oracle'] = orc
SKILL_COL = 'le_12'
skill = {}
for k in ('top20', 'ool', 'magicg'):
    base = cg(port_ret(k)); skill[PORTS[k]] = []
    for rho in (0, .1, .2, .3, .5, .7, 1.0):
        vals = [cg(port_ret(k, oracle(SKILL_COL, noise=rho))) - base for _ in range(1 if rho == 1 else 40)]
        skill[PORTS[k]].append([rho, float(np.mean(vals))])
OUT['skill'] = skill

# hipótese (não testada antes): ROIC alto com crescimento parado (o motivo nº 1 das vencedoras que ficaram de fora)
pz = {}
for lab, m in (('ROIC ≥ 20% e crescimento < 15%', (~p.excluded) & (p.roic >= .20) & (p.growth < .15) & (p.growth > -.5)),
               ('OoL', (p['cat'] == OOL) & ~p.excluded), ('Universo', p.roic.notna())):
    y = p[m]
    pz[lab] = {str(h): float(y.groupby('date')[f'ex_{h}'].mean().mean()) for h in (4, 12)}
    pz[lab]['n'] = float(y.groupby('date').size().mean())
OUT['pausa'] = pz

# sinais dentro das OoL: descoberta 2012-2018, confirmação 2019-2026
o = H['ool'].copy()
o['tend_roic'] = o.ry6 - o[['ry1', 'ry2', 'ry3']].mean(axis=1)
o['tend_g'] = o.gy5 - o.growth
o['gap_pe'] = np.log(o.fair_pe / o.pe)
o['lmcap'] = np.log(o.mcap)
o['marg_vs'] = o.roic_marg - o.roic
o['tech'] = (o.sector == 'Information Technology').astype(float)
SIG = {'ROIC': 'roic', 'Crescimento': 'growth', 'Retorno esperado': 'ret', 'P/L': 'pe', 'Desconto ao P/E justo': 'gap_pe', 'Instabilidade do crescimento (zGrowth)': 'zgrowth',
       'Tendência do ROIC (último ano vs 3 primeiros)': 'tend_roic', 'Aceleração do crescimento (último vs mediana)': 'tend_g', 'ROIC marginal vs ROIC': 'marg_vs',
       'Tamanho (valor de mercado)': 'lmcap', 'Dividend yield': 'dy', 'Tecnologia (setor)': 'tech'}
cut = pd.Timestamp('2018-12-31'); res = []
for lab, col in SIG.items():
    row = dict(sinal=lab)
    for per, msk in (('desc', o.date <= cut), ('conf', o.date > cut)):
        ics = [st.spearmanr(g[col], g.ex_4)[0] for _, g in o[msk].dropna(subset=[col, 'ex_4']).groupby('date') if len(g) >= 15 and g[col].nunique() >= 2]
        ics = np.array([v for v in ics if np.isfinite(v)])
        row[f'ic_{per}'] = float(ics.mean()) if len(ics) else None
        row[f't_{per}'] = float(ics.mean() / (ics.std() / np.sqrt(len(ics) / 4))) if len(ics) > 4 else None
        row[f'n_{per}'] = int(len(ics))
    res.append(row)
OUT['sinais'] = res
# quintis dos sinais que passaram (|t| descoberta > 2,9 Bonferroni 12 testes e mesmo sinal na confirmação com t > 1,5)
ok = [r for r in res if r['t_desc'] is not None and abs(r['t_desc']) > 2.9 and r['t_conf'] is not None and np.sign(r['t_conf']) == np.sign(r['t_desc']) and abs(r['t_conf']) > 1.5]
quint = {}
for r in (ok or sorted(res, key=lambda r: -abs(r['t_desc'] or 0))[:3]):
    col = SIG[r['sinal']]; y = o.dropna(subset=[col, 'ex_4']).copy()
    y['q'] = y.groupby('date')[col].transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False) if len(s) >= 15 else np.nan)
    quint[r['sinal']] = {per: y[m].groupby('q').ex_4.mean().round(4).tolist() for per, m in (('desc', y.date <= cut), ('conf', y.date > cut))}
OUT['sinais_ok'] = [r['sinal'] for r in ok]
OUT['sinais_quint'] = quint

(ROOT / 'dados_attrib.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
print(json.dumps({k: OUT[k] for k in ('decomp', 'roic_pers', 'roic_port', 'fm', 'var_decomp', 'oracle', 'skill', 'sinais_ok')}, ensure_ascii=False, indent=0, default=str)[:6000])
