"""Ramo B (2026-11-18, pré-registrado no PROTOCOLO): o universo das ações detidas pelos gestores do "Navegando US" (13F) tem mais crescimento do EPS?
Dentro dele, o re-rating via ROIC ("ROIC alto descontado") e a Top 20 rendem mais? S&P 500 point-in-time, ROIC triangulado, 2016-06 a 2026-09.
Entrada: relatorio/data_13f/posicoes.csv.gz (relatorio/extrai_13f.py). Saída: relatorio/dados_gestores.json e relatorio/gestores_tabela.md.
Uso: python3 relatorio/ramo_gestores.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
from scipy import stats as st
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import calc2, top_n  # noqa: E402
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, DUAL  # noqa: E402
from backtest import stats  # noqa: E402

c, adj, dates, ref, nm = calc2.sp_data()
W = calc2.weights(c)
D = pd.DatetimeIndex(dates); iq = {d: i for i, d in enumerate(D)}
A = adj.reindex(D, method='ffill')
D0 = pd.Timestamp('2016-06-30'); D0 = D[D >= D0][0]
DS = [d for d in dates if pd.Timestamp(d) >= D0]
OUT = {'periodo': [str(D0.date()), str(D[-1].date())]}
firm = lambda t: DUAL.get(t, t)

# ---------------- contagem de gestores (13F do trimestre anterior) ----------------
x = pd.read_csv(ROOT / 'data_13f' / 'posicoes.csv.gz').dropna(subset=['ticker'])
x['firm'] = x.ticker.map(firm)
cnt = x.groupby(['trimestre', 'firm']).gestor.nunique()
cnt_t = x.groupby(['trimestre', 'firm', 'tipo']).gestor.nunique().unstack(fill_value=0)
OUT['gestores'] = dict(n=int(x.gestor.nunique()), longo=int(x[x.tipo == 'longo'].gestor.nunique()), hedge=int(x[x.tipo == 'hedge'].gestor.nunique()),
                       trimestres=[x.trimestre.min(), x.trimestre.max()])


def prev_q(d):
    q = (pd.Timestamp(d) - pd.offsets.QuarterEnd(1))
    return f'{q.year}-{q.month:02d}'


p = c.copy(); p['qi'] = p.date.map(iq); p['firm'] = p.ticker.map(firm)
p['q13f'] = p.date.map(prev_q)
p['ng'] = [cnt.get((q, f), 0) for q, f in zip(p.q13f, p.firm)]
p['ng_longo'] = [cnt_t['longo'].get((q, f), 0) if (q, f) in cnt_t.index else 0 for q, f in zip(p.q13f, p.firm)]

# ---------------- painel com o futuro (como em attrib.py) ----------------
key = p.set_index(['qi', 'ticker'])
for h in (4, 12):
    f = key[['eps', 'pe']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'{v}_{h}' for v in f.columns]
    p = p.join(f, on=['qi', 'ticker'])
    tr = [A.at[D[iq[d] + h], t] / A.at[d, t] if iq[d] + h < len(D) and t in A and A.at[d, t] > 0 else np.nan for d, t in zip(p.date, p.ticker)]
    spy = {d: (A.at[D[iq[d] + h], 'SPY'] / A.at[d, 'SPY'] if iq[d] + h < len(D) else np.nan) for d in D}
    p[f'lt_{h}'] = np.log(np.array(tr, dtype=float))
    ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
    p[f'le_{h}'] = np.where(ok, np.log(p[f'eps_{h}'] / p.eps), np.nan)
    p[f'lp_{h}'] = np.where(ok, np.log(p[f'pe_{h}'] / p.pe), np.nan)
    p[f'ld_{h}'] = p[f'lt_{h}'] - p[f'le_{h}'] - p[f'lp_{h}']
    p[f'R{h}'] = np.expm1(p[f'le_{h}'] * 4 / h)
    p[f'RR{h}'] = np.expm1(p[f'lp_{h}'] * 4 / h)
    p[f'ex_{h}'] = (np.array(tr, dtype=float) / p.date.map(spy)) ** (4 / h) - 1
ann = lambda v, h: float(np.expm1(v * 4 / h))
pp = p[p.date >= D0].copy()

# ---------------- teste 1: a premissa ----------------
def ic(df, a, b, mn=30):
    v = [st.spearmanr(g[a], g[b])[0] for _, g in df.dropna(subset=[a, b]).groupby('date') if len(g) >= mn and g[a].nunique() > 2]
    v = np.array([u for u in v if np.isfinite(u)])
    return dict(ic=float(v.mean()), pos=float((v > 0).mean()), t=float(v.mean() / (v.std() / np.sqrt(len(v) / 4))), n=len(v)) if len(v) > 4 else None


prem = {}
for nmv, col in (('Crescimento do EPS em 1 ano', 'R4'), ('Crescimento do EPS em 3 anos (a.a.)', 'R12'), ('Re-rating em 1 ano', 'RR4'),
                 ('Re-rating em 3 anos (a.a.)', 'RR12'), ('Excesso sobre o S&P em 1 ano', 'ex_4'), ('Excesso sobre o S&P em 3 anos (a.a.)', 'ex_12')):
    prem[nmv] = dict(todos=ic(pp, 'ng', col), qualidade=ic(pp[~pp.excluded & (pp.roic >= .12)], 'ng', col, 20))
OUT['premissa_ic'] = prem
grp = {'0 gestores': pp.ng == 0, '1–2': pp.ng.between(1, 2), '3–4': pp.ng.between(3, 4), '5–9': pp.ng.between(5, 9), '10 ou mais': pp.ng >= 10}
med = {}
for k, m in grp.items():
    y = pp[m]
    med[k] = dict(n=float(y.groupby('date').size().mean()), R4=float(y.R4.median()), R12=float(y.R12.median()), RR4=float(y.RR4.median()), RR12=float(y.RR12.median()),
                  ex4=float(y.groupby('date').ex_4.mean().mean()), ex12=float(y.groupby('date').ex_12.mean().mean()), roic=float(y.roic.median()),
                  growth=float(y.growth.median()))
OUT['premissa_faixas'] = med
dec_u = {}
for k, m in (('≥ 5 gestores', pp.ng >= 5), ('≥ 3 gestores', pp.ng >= 3), ('< 3 gestores', pp.ng < 3), ('Todas', pp.ng >= 0)):
    y = pp[m].dropna(subset=['le_12', 'lp_12', 'lt_12'])
    g = y.groupby('date')[['le_12', 'lp_12', 'ld_12', 'lt_12']].mean().mean()
    dec_u[k] = dict(eps=ann(g.le_12, 12), rr=ann(g.lp_12, 12), div=ann(g.ld_12, 12), tot=ann(g.lt_12, 12))
OUT['premissa_decomp'] = dec_u
OUT['cobertura'] = {str(d.date()): [int((g.ng >= 3).sum()), int((g.ng >= 5).sum()), int(len(g))] for d, g in pp.groupby('date')}

# ---------------- teste 2: carteiras ----------------
print('valor de mercado...', flush=True)
need = pp[(pp.ng >= 1) | (~pp.excluded & (pp.roic >= .12))].copy()
need['mcap2'] = top_n.mcap_us(need, need)
pp = pp.merge(need[['date', 'ticker', 'mcap2']], on=['date', 'ticker'], how='left'); pp['mcap'] = pp.mcap.fillna(pp.mcap2)
pp['gap'] = np.where((pp.fair_pe > 0) & (pp.pe > 0), np.log(pp.fair_pe / pp.pe), np.nan)
base = pp[~pp.excluded & (pp.roic >= .12) & pp.gap.notna() & pp.mcap.notna()]
qual = pp[~pp.excluded & pp['cat'].notna() & (pp.roic >= .12) & (pp.growth >= .15) & pp.mcap.notna() & (pp.pe >= 4)]
held = pp[~pp.excluded & (pp.ng >= 1) & pp.mcap.notna()]


def pick(df, sort, asc, n=20):
    df = calc2.dd_firm(df)
    return {d: g.sort_values(sort, ascending=asc).head(n) for d, g in df.groupby('date')}


SEL = {
    'ROIC alto descontado (original)': pick(base, ['gap', 'roic'], [False, False]),
    'Top 20 (original)': pick(qual, ['ret', 'roic'], [False, False]),
    'ROIC alto descontado, ≥ 3 gestores': pick(base[base.ng >= 3], ['gap', 'roic'], [False, False]),
    'ROIC alto descontado, ≥ 5 gestores': pick(base[base.ng >= 5], ['gap', 'roic'], [False, False]),
    'Top 20, ≥ 3 gestores': pick(qual[qual.ng >= 3], ['ret', 'roic'], [False, False]),
    'Top 20, ≥ 5 gestores': pick(qual[qual.ng >= 5], ['ret', 'roic'], [False, False]),
    'As 20 mais detidas (controle)': pick(held, ['ng', 'mcap'], [False, False]),
}
NEW = [k for k in SEL if 'gestores' in k or 'detidas' in k]
Wn = {k: {d: calc2.cap_w(g) for d, g in v.items()} for k, v in SEL.items()}
We = {k: {d: pd.Series(1 / len(g), index=g.ticker) for d, g in v.items()} for k, v in SEL.items()}
navs9, n9, _, _ = bm.load_benchmarks()
rebase = lambda s: (s.loc[D0:] / s.loc[D0:].iloc[0])
navs = {k: rebase(v) for k, v in navs9.items()}
nn = dict(n9)
for k in SEL:
    navs[k] = run_weighted(Wn[k], adj, DS); nn[k] = float(np.mean([len(g) for g in SEL[k].values()]))
    navs[k + ' (peso igual)'] = run_weighted(We[k], adj, DS); nn[k + ' (peso igual)'] = nn[k]
R = navs['S&P 500']
tab = {}
for k, s in navs.items():
    s = s.dropna(); stt = stats(s); w = {y: bm.windows(s, R, y) for y in (3, 5, 10)}
    tab[k] = dict(cagr=stt['CAGR'], vol=stt['Vol'], dd=stt['MaxDD'], n=nn.get(k), w3=w[3][0], w5=w[5][0], w10=w[10][0], p3=w[3][1], p5=w[5][1])
OUT['carteiras'] = tab
(ROOT / 'gestores_tabela.md').write_text(f'Período: {D0.date()} a {D[-1].date()} (todas rebaseadas no início)\n\n' + '\n'.join(bm.bench_table(navs, nn)))
M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()})
show = ['S&P 500', 'Top 20 (original)', 'ROIC alto descontado (original)', 'ROIC alto descontado, ≥ 3 gestores', 'ROIC alto descontado, ≥ 5 gestores',
        'Top 20, ≥ 3 gestores', 'As 20 mais detidas (controle)']
OUT['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(v) else round(float(v), 4) for v in M[k] / M[k].dropna().iloc[0]] for k in show}}

# decomposição das carteiras (3 anos)
dec = {}
for k in SEL:
    rows = [(d, t, w) for d, ws in Wn[k].items() for t, w in ws.items()]
    hh = pd.DataFrame(rows, columns=['date', 'ticker', 'w']).merge(pp, on=['date', 'ticker'], how='left')
    out = {}
    for h in (4, 12):
        y = hh.dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
        g = y.groupby('date').apply(lambda z_: pd.Series({c_: np.average(z_[c_], weights=z_.w) for c_ in (f'le_{h}', f'lp_{h}', f'ld_{h}', f'lt_{h}', 'gap', 'ng')}), include_groups=False).mean()
        out[str(h)] = dict(eps=ann(g[f'le_{h}'], h), rr=ann(g[f'lp_{h}'], h), div=ann(g[f'ld_{h}'], h), tot=ann(g[f'lt_{h}'], h), gap=float(g['gap']), ng=float(g['ng']))
    dec[k] = out
OUT['decomp'] = dec
# sobreposição com a original
ov = {}
for k in ('ROIC alto descontado, ≥ 3 gestores', 'ROIC alto descontado, ≥ 5 gestores'):
    ov[k] = float(np.mean([len(set(SEL[k][d].ticker) & set(SEL['ROIC alto descontado (original)'][d].ticker)) / 20 for d in SEL[k] if d in SEL['ROIC alto descontado (original)']]))
OUT['sobreposicao'] = ov
# sem NVIDIA: a melhor das novas
best = max(NEW, key=lambda k: tab[k]['cagr'])
src = {'ROIC alto descontado, ≥ 3 gestores': (base[base.ng >= 3], ['gap', 'roic']), 'ROIC alto descontado, ≥ 5 gestores': (base[base.ng >= 5], ['gap', 'roic']),
       'Top 20, ≥ 3 gestores': (qual[qual.ng >= 3], ['ret', 'roic']), 'Top 20, ≥ 5 gestores': (qual[qual.ng >= 5], ['ret', 'roic']),
       'As 20 mais detidas (controle)': (held, ['ng', 'mcap'])}[best]
sel_nv = pick(src[0][src[0].ticker != 'NVDA'], src[1], [False, False])
nav_nv = run_weighted({d: calc2.cap_w(g) for d, g in sel_nv.items()}, adj, DS)
orig_nv = pick(base[base.ticker != 'NVDA'], ['gap', 'roic'], [False, False])
nav_onv = run_weighted({d: calc2.cap_w(g) for d, g in orig_nv.items()}, adj, DS)
OUT['sem_nvda'] = dict(carteira=best, com=tab[best]['cagr'], sem=stats(nav_nv.dropna())['CAGR'], original_com=tab['ROIC alto descontado (original)']['cagr'],
                       original_sem=stats(nav_onv.dropna())['CAGR'])
# a diferença contra a original é estatisticamente distinguível? (retornos trimestrais)
qd = pd.DatetimeIndex(DS)
qr = {k: navs[k].reindex(qd, method='ffill').pct_change().dropna() for k in SEL}
dif = {}
for a_, b_ in (('ROIC alto descontado, ≥ 3 gestores', 'ROIC alto descontado (original)'), ('ROIC alto descontado, ≥ 5 gestores', 'ROIC alto descontado (original)'),
               ('Top 20, ≥ 3 gestores', 'Top 20 (original)'), ('Top 20, ≥ 5 gestores', 'Top 20 (original)')):
    dd_ = (qr[a_] - qr[b_]).dropna()
    dif[a_] = dict(contra=b_, media_aa=float(dd_.mean() * 4), te=float(dd_.std() * 2), t=float(dd_.mean() / (dd_.std() / np.sqrt(len(dd_)))), melhor=float((dd_ > 0).mean()), n=len(dd_))
OUT['diferenca'] = dif
last = max(SEL['ROIC alto descontado, ≥ 3 gestores'])
OUT['hoje'] = {k: [[t, nm(t), float(w), int(SEL[k][last].set_index('ticker').ng.get(t, 0))] for t, w in Wn[k][last].sort_values(ascending=False).items()]
               for k in ('ROIC alto descontado, ≥ 3 gestores', 'ROIC alto descontado, ≥ 5 gestores', 'As 20 mais detidas (controle)')}
OUT['hoje_data'] = str(pd.Timestamp(last).date())
OUT['new'] = NEW
(ROOT / 'dados_gestores.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
for k in ['S&P 500', 'Top 20 (original)', 'ROIC alto descontado (original)'] + NEW:
    t = tab[k]; print(f"{k:42s} {t['cagr']:.1%} vol {t['vol']:.1%} dd {t['dd']:.1%} w3 {t['w3']:.0%} w5 {t['w5']:.0%} w10 {t['w10']:.0%}  EW {tab.get(k + ' (peso igual)', {}).get('cagr', np.nan):.1%}  n {nn.get(k, np.nan):.1f}")
print(json.dumps({k: OUT[k] for k in ('diferenca', 'sobreposicao', 'sem_nvda')}, ensure_ascii=False, default=str)[:5000])
