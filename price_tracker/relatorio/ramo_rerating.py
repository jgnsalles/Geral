"""Ramo de análise (2026-11-16, pré-registrado no PROTOCOLO): o sell-side/a mediana preveem o crescimento? setores de crescimento estável,
"ROIC alto descontado" (desconto ao P/E justo) e PEG. S&P 500 point-in-time, ROIC triangulado.
Saída: relatorio/dados_rerating.json (+ tabela padrão em relatorio/rerating_tabela.md). Uso: python3 relatorio/ramo_rerating.py"""
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
OUT = {}

# ---------------- painel com o futuro (como em attrib.py) ----------------
p = c.copy(); p['qi'] = p.date.map(iq)
key = p.set_index(['qi', 'ticker'])
for h in (4, 12):
    f = key[['eps', 'pe']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'{x}_{h}' for x in f.columns]
    p = p.join(f, on=['qi', 'ticker'])
    tr = [A.at[D[iq[d] + h], t] / A.at[d, t] if iq[d] + h < len(D) and t in A and A.at[d, t] > 0 else np.nan for d, t in zip(p.date, p.ticker)]
    p[f'lt_{h}'] = np.log(np.array(tr, dtype=float))
    ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
    p[f'le_{h}'] = np.where(ok, np.log(p[f'eps_{h}'] / p.eps), np.nan)
    p[f'lp_{h}'] = np.where(ok, np.log(p[f'pe_{h}'] / p.pe), np.nan)
    p[f'ld_{h}'] = p[f'lt_{h}'] - p[f'le_{h}'] - p[f'lp_{h}']
    p[f'R{h}'] = np.expm1(p[f'le_{h}'] * 4 / h)          # crescimento anual realizado do EPS
ann = lambda x, h: np.expm1(x * 4 / h)

# grupo: subindústria com >= 5 empresas na data, senão setor
sz = p.groupby(['date', 'industry']).ticker.transform('size')
p['grupo'] = np.where(sz >= 5, p.industry, p.sector)
p['azg'] = p.zgrowth.abs()
GY = ['gy1', 'gy2', 'gy3', 'gy4', 'gy5']

# ---------------- A2: preditores ingênuos do crescimento ----------------
p['pr_med'] = p.growth
p['pr_mean'] = p[GY].mean(axis=1)
p['pr_last'] = p.gy5
p['pr_set'] = p.groupby(['date', 'grupo']).growth.transform('median')
p['pr_zero'] = 0.0; p['pr_8'] = .08
PRED = [('pr_med', 'Mediana de 5 anos (o nosso)'), ('pr_mean', 'Média de 5 anos'), ('pr_last', 'Último ano'), ('pr_set', 'Mediana do setor'),
        ('pr_zero', 'Zero (lucro não cresce)'), ('pr_8', 'Constante de 8%')]
a2 = {}
for h in (4, 12):
    x = p.dropna(subset=[f'R{h}', 'growth']).copy()
    rows = []
    for col, lab in PRED:
        y = x.dropna(subset=[col])
        err = (y[f'R{h}'] - y[col])
        ics = [st.spearmanr(g[col], g[f'R{h}'])[0] for _, g in y.groupby('date') if len(g) > 30 and g[col].nunique() > 5]
        rows.append(dict(nome=lab, ic=float(np.nanmean(ics)) if ics else None, mae=float(err.abs().median()), vies=float(err.median()),
                         n=int(len(y))))
    a2[str(h)] = rows
OUT['a2'] = a2
# viés por quinto do previsto (o "volta à média"): previsto x realizado
q = p.dropna(subset=['R12', 'growth']).copy()
q['qq'] = q.groupby('date').growth.transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False))
OUT['a2_quint'] = q.groupby('qq').agg(prev=('growth', 'median'), real=('R12', 'median')).round(4).values.tolist()

# ---------------- B1: previsibilidade por grupo ----------------
x = p.dropna(subset=['R12', 'growth']).copy()
grp = []
for (d, g_), y in x.groupby(['date', 'grupo']):
    if len(y) < 5: continue
    ic = st.spearmanr(y.growth, y.R12)[0] if y.growth.nunique() > 2 else np.nan
    grp.append((d, g_, ic, len(y)))
G = pd.DataFrame(grp, columns=['date', 'grupo', 'ic', 'n'])
z = p.groupby(['date', 'grupo']).agg(azg=('azg', 'median'), n_all=('ticker', 'size')).reset_index()
yr = p.melt(id_vars=['date', 'grupo'], value_vars=GY).dropna()
yr['ok'] = yr.value.between(0, .25)
band = yr.groupby(['date', 'grupo']).ok.mean().rename('faixa').reset_index()
G = G.merge(z, on=['date', 'grupo'], how='left').merge(band, on=['date', 'grupo'], how='left')
G['per'] = np.where(G.date <= pd.Timestamp('2018-12-31'), 'a', 'b')
summ = G.groupby('grupo').agg(ic=('ic', 'mean'), azg=('azg', 'median'), faixa=('faixa', 'mean'), datas=('date', 'count'), n=('n', 'median'))
per = G.groupby(['grupo', 'per']).ic.mean().unstack()
summ = summ.join(per).rename(columns={'a': 'ic_a', 'b': 'ic_b'})
summ = summ[summ.datas >= 12].sort_values('ic', ascending=False)
OUT['b1_grupos'] = [dict(grupo=k, **{c_: (None if pd.isna(v) else float(v)) for c_, v in r.items()}) for k, r in summ.iterrows()]
ok = summ.dropna(subset=['ic_a', 'ic_b'])
OUT['b1_persist'] = dict(corr_ic=float(st.spearmanr(ok.ic_a, ok.ic_b)[0]), n=int(len(ok)))
# a régua ex-ante (|zGrowth| mediano do grupo na data) separa onde o passado prevê melhor?
x2 = G.dropna(subset=['azg', 'ic']).copy()
x2['terco'] = x2.groupby('date').azg.transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=['estável', 'médio', 'instável']))
OUT['b1_terco'] = x2.groupby('terco', observed=True).agg(ic=('ic', 'mean'), azg=('azg', 'median')).round(4).reset_index().values.tolist()
# erro do preditor (mediana própria) nos setores estáveis x demais, empresa a empresa
p = p.merge(z[['date', 'grupo', 'azg']].rename(columns={'azg': 'g_azg'}), on=['date', 'grupo'], how='left')
p['terco_g'] = p.groupby('date').g_azg.transform(lambda s: pd.qcut(s.rank(method='dense'), 3, labels=False, duplicates='drop'))
p['set_estavel'] = p.terco_g == 0
p['emp_estavel'] = (p.azg < .5) & p.growth.between(.05, .30)
e = p.dropna(subset=['R12', 'growth'])
OUT['b1_erro'] = {lab: dict(mae=float((g.R12 - g.growth).abs().median()), ic=float(np.nanmean([st.spearmanr(y.growth, y.R12)[0] for _, y in g.groupby('date') if len(y) > 15])),
                            real_med=float(g.R12.median()), prev_med=float(g.growth.median()))
                  for lab, g in (('Setores estáveis', e[e.set_estavel]), ('Demais setores', e[~e.set_estavel]), ('Empresas estáveis', e[e.emp_estavel]),
                                 ('Demais empresas', e[~e.emp_estavel]))}
# robustez: previsibilidade passada do grupo (previsto há 3 anos x realizado até a data)
Gp = G[['date', 'grupo', 'ic']].copy(); Gp['date'] = Gp.date.map(lambda d: D[iq[d] + 12] if iq[d] + 12 < len(D) else pd.NaT)
p = p.merge(Gp.dropna().rename(columns={'ic': 'ic_passado'}), on=['date', 'grupo'], how='left')
p['set_previs'] = p.groupby('date').ic_passado.transform(lambda s: s >= s.quantile(2 / 3) if s.notna().sum() > 10 else pd.Series(False, index=s.index))

# ---------------- B3: carteiras ----------------
print('valor de mercado...', flush=True)
need = p[~p.excluded & (p.roic >= .12) & p.pe.gt(0)].copy()
need['mcap2'] = top_n.mcap_us(need, need)
p = p.merge(need[['date', 'ticker', 'mcap2']], on=['date', 'ticker'], how='left'); p['mcap'] = p.mcap.fillna(p.mcap2)
p['gap'] = np.where((p.fair_pe > 0) & (p.pe > 0), np.log(p.fair_pe / p.pe), np.nan)
p['peg'] = np.where((p.pe > 0) & (p.growth > 0), p.pe / (p.growth * 100), np.nan)
base = p[~p.excluded & (p.roic >= .12) & p.gap.notna() & p.mcap.notna()]
qual = p[~p.excluded & p['cat'].notna() & (p.roic >= .12) & (p.growth >= .15) & p.mcap.notna()]


def pick(df, sort, asc, n=20):
    df = calc2.dd_firm(df)
    return {d: g.sort_values(sort, ascending=asc).head(n) for d, g in df.groupby('date')}


SEL = {
    'ROIC alto descontado': pick(base, ['gap', 'roic'], [False, False]),
    'Descontado, setores estáveis': pick(base[base.set_estavel], ['gap', 'roic'], [False, False]),
    'Descontado, empresas estáveis': pick(base[base.emp_estavel], ['gap', 'roic'], [False, False]),
    'Descontado, setores previsíveis (robustez)': pick(base[base.set_previs], ['gap', 'roic'], [False, False]),
    'Top 20, setores estáveis': pick(qual[(qual.pe >= 4) & qual.set_estavel], ['ret', 'roic'], [False, False]),
    'PEG (contraste)': pick(qual[qual.peg.notna()], ['peg', 'roic'], [True, False]),
}
Wn = {k: {d: calc2.cap_w(g) for d, g in v.items()} for k, v in SEL.items()}
We = {k: {d: pd.Series(1 / len(g), index=g.ticker) for d, g in v.items()} for k, v in SEL.items()}
navs9, n9, _, _ = bm.load_benchmarks()
navs = dict(navs9)
navs['Top 20 (OoL)'] = run_weighted(W['top20'], adj, dates); navs['JG+G'] = run_weighted(W['magicg'], adj, dates)
nn = dict(n9); nn['Top 20 (OoL)'] = 20; nn['JG+G'] = 20
for k in SEL:
    navs[k] = run_weighted(Wn[k], adj, dates); nn[k] = float(np.mean([len(g) for g in SEL[k].values()]))
    navs[k + ' (peso igual)'] = run_weighted(We[k], adj, dates); nn[k + ' (peso igual)'] = nn[k]
R = navs['S&P 500']
tab = {}
for k, s in navs.items():
    s = s.dropna(); stt = stats(s); w = {y: bm.windows(s, R, y) for y in (3, 5, 10)}
    tab[k] = dict(cagr=stt['CAGR'], vol=stt['Vol'], dd=stt['MaxDD'], n=nn.get(k), w3=w[3][0], w5=w[5][0], w10=w[10][0], p3=w[3][1], p5=w[5][1])
OUT['carteiras'] = tab
(ROOT / 'rerating_tabela.md').write_text('\n'.join(bm.bench_table(navs, nn)))
M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()})
show = ['S&P 500', 'Top 20 (OoL)', 'JG+G', 'ROIC alto descontado', 'Descontado, setores estáveis', 'Descontado, empresas estáveis', 'PEG (contraste)']
OUT['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(v) else round(float(v), 4) for v in M[k] / M[k].dropna().iloc[0]] for k in show}}

# decomposição (EPS, re-rating, dividendos) e o re-rating previsto x realizado
dec = {}
for k, sel in list(SEL.items()) + [('Top 20 (OoL)', None), ('JG+G', None)]:
    if sel is None:
        rows = [(pd.Timestamp(d), t, w) for d, ws in (W['top20'] if k.startswith('Top 20') else W['magicg']).items() for t, w in ws.items()]
    else:
        rows = [(d, t, w) for d, ws in Wn[k].items() for t, w in ws.items()]
    hh = pd.DataFrame(rows, columns=['date', 'ticker', 'w']).merge(p, on=['date', 'ticker'], how='left')
    out = {}
    for h in (4, 12):
        y = hh.dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
        g = y.groupby('date').apply(lambda z_: pd.Series({c_: np.average(z_[c_], weights=z_.w) for c_ in (f'le_{h}', f'lp_{h}', f'ld_{h}', f'lt_{h}', 'gap')}), include_groups=False).mean()
        out[str(h)] = dict(eps=ann(g[f'le_{h}'], h), rr=ann(g[f'lp_{h}'], h), div=ann(g[f'ld_{h}'], h), tot=ann(g[f'lt_{h}'], h), gap=float(g['gap']))
    dec[k] = out
uu = p.dropna(subset=['le_12', 'lp_12', 'lt_12'])
u = uu.groupby('date')[['le_12', 'lp_12', 'ld_12', 'lt_12']].mean().mean()
dec['Universo'] = {'12': dict(eps=ann(u.le_12, 12), rr=ann(u.lp_12, 12), div=ann(u.ld_12, 12), tot=ann(u.lt_12, 12), gap=float(uu.gap.median()))}
OUT['decomp'] = dec

# sem NVIDIA: a melhor das novas
new = [k for k in SEL]
best = max(new, key=lambda k: tab[k]['cagr'])
sel_nv = {d: g[g.ticker != 'NVDA'] for d, g in SEL[best].items()}
src = {'ROIC alto descontado': base, 'Descontado, setores estáveis': base[base.set_estavel], 'Descontado, empresas estáveis': base[base.emp_estavel],
       'Descontado, setores previsíveis (robustez)': base[base.set_previs], 'Top 20, setores estáveis': qual[(qual.pe >= 4) & qual.set_estavel], 'PEG (contraste)': qual[qual.peg.notna()]}[best]
srt = (['peg', 'roic'], [True, False]) if best == 'PEG (contraste)' else ((['ret', 'roic'], [False, False]) if best.startswith('Top 20') else (['gap', 'roic'], [False, False]))
sel_nv = pick(src[src.ticker != 'NVDA'], *srt)
nav_nv = run_weighted({d: calc2.cap_w(g) for d, g in sel_nv.items()}, adj, dates)
OUT['sem_nvda'] = dict(carteira=best, com=tab[best]['cagr'], sem=stats(nav_nv.dropna())['CAGR'], w3_sem=bm.windows(nav_nv, R, 3)[0])
# composição de hoje da melhor e da ROIC alto descontado
last = max(SEL['ROIC alto descontado'])
OUT['hoje'] = {k: [[t, nm(t), float(w)] for t, w in Wn[k][last].sort_values(ascending=False).items()] for k in ('ROIC alto descontado', 'Descontado, setores estáveis', 'Descontado, empresas estáveis')}
OUT['hoje_data'] = str(pd.Timestamp(last).date())
OUT['setores_estaveis_hoje'] = sorted(p[(p.date == last) & p.set_estavel].grupo.unique().tolist())
(ROOT / 'dados_rerating.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
for k in ['S&P 500', 'Top 20 (OoL)', 'JG+G'] + new:
    t = tab[k]; print(f"{k:45s} {t['cagr']:.1%} vol {t['vol']:.1%} dd {t['dd']:.1%} w3 {t['w3']:.0%} w5 {t['w5']:.0%} w10 {t['w10']:.0%}  EW {tab.get(k + ' (peso igual)', {}).get('cagr', np.nan):.1%}")
print(json.dumps({k: OUT[k] for k in ('a2', 'b1_persist', 'b1_terco', 'b1_erro', 'sem_nvda')}, ensure_ascii=False, default=str)[:4000])
