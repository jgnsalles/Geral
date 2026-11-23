"""Brazil Downturn, passo 3: macro × performance nos fluxos das gestoras de ações, e quem capta na seca.
Uso: python3 03_analise.py <out do passo 2> <carteiras.json> <gestoras_fr.json> <saida.json>
"""
import sys, os, re, json
import pandas as pd, numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

OUT, CJ, FRJ, SAIDA = sys.argv[1:5]
PLMIN = 30e6
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]
GM = pd.read_pickle(os.path.join(OUT, 'gestora_mes.pkl'))
# Opportunity fica fora: a maior parte do PL em ações são veículos patrimoniais (OPP I, Lógica, SLQ) e em 2023 dois fundos novos
# receberam R$ 21 bi de fora do perímetro, o que não é decisão de alocação do mercado.
EXCL = {'01608570'}
GM = GM[~GM.gid.isin(EXCL)]
if os.environ.get('FLOW') == 'rep':   # robustez: captação - resgate reportados
    GM['flow'] = GM.flow_rep
IX = pd.read_csv(os.path.join(OUT, 'indices.csv'), index_col=0)
MK = pd.read_csv(os.path.join(OUT, 'mercado_mes.csv'), index_col=0)
d = json.load(open(CJ)); M = d['meses']; G = [g for g in d['gestoras'] if g['id'] != '00000000']

# ---------------- universo point-in-time: top 100 no mês anterior (meses com CDA em sigilo usam a última lista completa, abr/2026)
LASTFULL = '2026-04'
top = {}
for g in G:
    for a, b in g.get('tp', []):
        for i in range(a, b + 1): top.setdefault(M[i], set()).add(g['id'])
def univ(ym):
    p = str(pd.Period(ym, 'M') - 1)
    return top.get(min(p, LASTFULL), set())
GM = GM.sort_values(['gid', 'ym']).reset_index(drop=True)
GM['univ'] = [g in univ(y) for g, y in zip(GM.gid, GM.ym)]
GM = GM.join(IX[['ibov', 'cdi']], on='ym')

# ---------------- variáveis da gestora (todas conhecidas no fim de t-1)
GM['per'] = pd.PeriodIndex(GM.ym, freq='M')
GM['gap'] = GM.groupby('gid').per.diff().map(lambda x: getattr(x, 'n', 99))
GM['fr'] = GM.flow / GM.pl_ant
def roll(s, n, f, minp):
    return s.groupby(GM.gid).transform(lambda x: f(x.rolling(n, min_periods=minp)))
lr = np.log1p(GM.r.clip(-0.9)); li = np.log1p(GM.ibov)
GM['ex12'] = np.expm1(roll(lr, 12, lambda r: r.sum(), 10)) - np.expm1(roll(li.where(GM.r.notna()), 12, lambda r: r.sum(), 10))
GM['ex36'] = (roll(lr - li, 36, lambda r: r.mean(), 24)) * 12
GM['vol36'] = roll(GM.r, 36, lambda r: r.std(), 24) * np.sqrt(12)
cov = (GM.r * GM.ibov); m_r = roll(GM.r, 36, lambda r: r.mean(), 24); m_i = roll(GM.ibov.where(GM.r.notna()), 36, lambda r: r.mean(), 24)
GM['beta36'] = (roll(cov, 36, lambda r: r.mean(), 24) - m_r * m_i) / (roll(GM.ibov.where(GM.r.notna()) ** 2, 36, lambda r: r.mean(), 24) - m_i ** 2)
GM['te36'] = roll(GM.r - GM.ibov, 36, lambda r: r.std(), 24) * np.sqrt(12)
first = GM[GM.pl > 0].groupby('gid').per.min()
GM['idade'] = (GM.per - GM.gid.map(first)).map(lambda x: getattr(x, 'n', np.nan)) / 12
for c in ['pl_lb', 'pl_small', 'pl_div', 'pl_ext']:
    GM[c.replace('pl_', 'sh_')] = (GM[c] / GM.pl).clip(0, 1)
lagc = ['ex12', 'ex36', 'vol36', 'beta36', 'te36', 'sh_lb', 'sh_small', 'sh_div', 'sh_ext', 'pl', 'nf']
for c in lagc:
    GM[c + '_l'] = GM.groupby('gid')[c].shift()
    GM.loc[GM.gap != 1, c + '_l'] = np.nan

# ---------------- carteira (CDA consolidada do Navegando): concentração, nº de ações, exterior, "consenso"
H = []
for g in G:
    p = g['p'] if isinstance(g['p'], dict) else {}
    for tk, v in p.items():
        s0, vals = v[0], v[1]
        for k, x in enumerate(vals):
            if x: H.append((g['id'], s0 + k, tk, x))
H = pd.DataFrame(H, columns=['gid', 'i', 'tk', 'v']); H['ym'] = H.i.map(lambda i: M[i])
pop = H.groupby(['ym', 'tk']).gid.nunique().rename('ng').reset_index()
pop['rk'] = pop.groupby('ym').ng.rank(ascending=False, method='first')
H = H.merge(pop[['ym', 'tk', 'rk']], on=['ym', 'tk'])
H['w'] = H.v / H.groupby(['gid', 'ym']).v.transform('sum')
HS = H.groupby(['gid', 'ym']).apply(lambda x: pd.Series({
    'n_acoes': int((x.w >= 0.005).sum()), 'top10': x.w.nlargest(10).sum(), 'hhi': (x.w ** 2).sum(),
    'ext_cart': x.w[x.tk.str.contains(r'\.')].sum(), 'consenso': x.w[x.rk <= 20].sum()})).reset_index()
HS['per'] = pd.PeriodIndex(HS.ym, freq='M')
GM = pd.merge_asof(GM.sort_values('per').assign(per_l=GM.per - 1).sort_values('per_l'),
                   HS.rename(columns={'per': 'per_l'}).drop(columns='ym').sort_values('per_l'), on='per_l', by='gid',
                   direction='backward', tolerance=pd.Period('2006-01', 'M') - pd.Period('2005-01', 'M') if False else None)
# (merge_asof com Period não aceita tolerância; limita a 12 meses abaixo)
HS_last = HS.groupby('gid').per.apply(set)
GM = GM.sort_values(['gid', 'ym']).reset_index(drop=True)

# ---------------- Formulário de Referência: base de clientes e remuneração (ano y vale para y+1)
fr = json.load(open(FRJ))
r2g = {}
for g in G:
    for r in ({g['id']} | ({root8(x[1]) for x in g['mb']} if not g.get('rb') else set())): r2g.setdefault(r, g['id'])
FR = []
for x in fr['gestoras']:
    gid = r2g.get(root8(x['cnpj']))
    if not gid: continue
    for y, v in x['y'].items():
        ac = v.get('ac') or []
        tot = sum(a or 0 for a in ac)
        if tot <= 0: continue
        sh = [(a or 0) / tot for a in ac]
        rm = v.get('r') or [None] * 5
        FR.append(dict(gid=gid, ano=int(y) + 1, cli_pf=sh[0], cli_fundos=sh[9], cli_inst=sh[3] + sh[4] + sh[5] + sh[6], cli_nres=sh[10],
                       cli_pj=sh[1] + sh[2], perf_fee=(rm[1] / 100 if rm and rm[1] is not None else np.nan), func=v.get('e'),
                       aum_total=v.get('a')))
FR = pd.DataFrame(FR).groupby(['gid', 'ano']).mean(numeric_only=True).reset_index()
GM['ano'] = GM.ym.str[:4].astype(int)
GM = GM.merge(FR, on=['gid', 'ano'], how='left')

# ---------------- amostra
S = GM[GM.univ & (GM.pl_ant >= PLMIN) & (GM.gap == 1) & (GM.ym >= '2006-01')].copy()
lo, hi = S.fr.quantile([0.01, 0.99]); S['frw'] = S.fr.clip(lo, hi)
for c in ['ex12_l', 'ex36_l', 'pl_l', 'vol36_l', 'beta36_l', 'te36_l']:
    S[c.replace('_l', '_rk')] = S.groupby('ym')[c].rank(pct=True)
print('amostra gestora-mês:', len(S), 'gestoras:', S.gid.nunique(), flush=True)
R = {}

# ================= A. O ciclo: fluxo agregado × mercado × juros
A = S.groupby('ym').agg(flow=('flow', 'sum'), pl_ant=('pl_ant', 'sum'), ng=('gid', 'nunique'), ex12_med=('ex12_l', 'median'),
                        bateu=('ex12_l', lambda x: (x > 0).mean()))
A = A.join(IX[['ibov', 'cdi']]).join(MK[['flow', 'pl_ant']].rename(columns={'flow': 'flow_mkt', 'pl_ant': 'pl_mkt'}))
A['fr'] = A.flow / A.pl_ant; A['fr_mkt'] = A.flow_mkt / A.pl_mkt
A['fr12'] = A.flow.rolling(12).sum() / A.pl_ant.shift(11)
A['ibov12'] = np.expm1(np.log1p(A.ibov).rolling(12).sum())
A['cdi12'] = np.expm1(np.log1p(A.cdi).rolling(12).sum())
A['cdi_aa'] = (1 + A.cdi) ** 12 - 1
A['dcdi12'] = A.cdi_aa - A.cdi_aa.shift(12)
A['ibov_cdi12'] = A.ibov12 - A.cdi12
A['ibov12_l'] = A.ibov12.shift(1); A['ibov_cdi12_l'] = A.ibov_cdi12.shift(1); A['cdi_aa_l'] = A.cdi_aa.shift(1); A['dcdi12_l'] = A.dcdi12.shift(1)
A['ex12_med_l'] = A.ex12_med  # já é a mediana do ex12 defasado
A['f3'] = A.flow.rolling(3).sum() / A.pl_ant.shift(2)
# regressões mensais do fluxo agregado (HAC 12)
def ols(y, X, df, hac=12):
    x = df[[y] + X].dropna(); m = sm.OLS(x[y], sm.add_constant(x[X])).fit(cov_type='HAC', cov_kwds={'maxlags': hac})
    return dict(n=int(m.nobs), r2=round(m.rsquared, 3), coef={k: round(v, 4) for k, v in m.params.items()}, t={k: round(v, 2) for k, v in m.tvalues.items()})
R['agg_reg'] = {
    'mercado': ols('fr', ['ibov12_l'], A),
    'juros': ols('fr', ['cdi_aa_l', 'dcdi12_l'], A),
    'alpha_industria': ols('fr', ['ex12_med_l'], A),
    'tudo': ols('fr', ['ibov12_l', 'cdi_aa_l', 'dcdi12_l', 'ex12_med_l'], A),
}
# anual
S['y'] = S.ym.str[:4]
Y = S.groupby('y').agg(flow=('flow', 'sum'), ng=('gid', 'nunique'))
pl_dez = S[S.ym.str.endswith('-01')].groupby('y').pl_ant.sum()
Y['pl0'] = pl_dez; Y['fr'] = Y.flow / Y.pl0
Y['ibov'] = A.groupby(A.index.str[:4]).ibov.apply(lambda x: np.prod(1 + x) - 1)
Y['cdi'] = A.groupby(A.index.str[:4]).cdi.apply(lambda x: np.prod(1 + x) - 1)
Y['cdi_fim'] = A.groupby(A.index.str[:4]).cdi_aa.last()
Y['ex_med'] = S[S.ym.str.endswith('-12') | (S.ym == S.ym.max())].groupby('y').ex12_l.median()  # aprox.
Y['pos'] = S.groupby(['y', 'gid']).flow.sum().gt(0).groupby('y').mean()
Y['fr_mkt'] = MK.groupby(MK.index.str[:4]).flow.sum() / MK[MK.index.str.endswith('-01')].groupby(MK[MK.index.str.endswith('-01')].index.str[:4]).pl_ant.sum()
Y['dcdi'] = Y.cdi_fim - Y.cdi_fim.shift()
Y['ibov_l'] = Y.ibov.shift()
yy = Y.loc['2006':'2025']
R['agg_anual'] = {k: ols('fr', v, yy, hac=1) for k, v in {'ibov_ano': ['ibov'], 'ibov_ano_anterior': ['ibov_l'], 'juros': ['dcdi', 'cdi'], 'juros_ibov': ['dcdi', 'cdi', 'ibov'], 'alpha_mediano': ['ex_med']}.items()}
R['anos'] = Y.reset_index().replace({np.nan: None}).to_dict('records')

# ================= B. Decomposição: maré (ano) × alpha (gestora)
# B1 anual: fluxo do ano / PL de dez do ano anterior, gestoras no universo em janeiro
Yg = S.groupby(['y', 'gid']).agg(flow=('flow', 'sum'), n=('ym', 'size')).reset_index()
start = S[S.ym.str.endswith('-01')][['y', 'gid', 'pl_ant', 'ex12_l', 'ex36_l', 'vol36_l', 'beta36_l', 'te36_l', 'idade',
                                     'sh_lb_l', 'sh_small_l', 'sh_div_l', 'sh_ext_l', 'n_acoes', 'top10', 'consenso', 'ext_cart',
                                     'cli_pf', 'cli_fundos', 'cli_inst', 'cli_nres', 'perf_fee', 'func', 'aum_total', 'nome']]
Yg = Yg.merge(start, on=['y', 'gid'])
Yg['fry'] = Yg.flow / Yg.pl_ant
lo, hi = Yg.fry.quantile([0.02, 0.98]); Yg['fryw'] = Yg.fry.clip(lo, hi)
# retorno do ano seguinte e do próprio ano
ret = S.groupby(['y', 'gid']).apply(lambda x: pd.Series({'ret': np.prod(1 + x.r.fillna(0)) - 1, 'ib': np.prod(1 + x.ibov) - 1, 'nm': x.r.notna().sum()})).reset_index()
ret['exy'] = ret.ret - ret.ib
Yg = Yg.merge(ret[['y', 'gid', 'exy', 'nm']], on=['y', 'gid'], how='left')
nxt = ret.assign(y=(ret.y.astype(int) - 1).astype(str))[['y', 'gid', 'exy']].rename(columns={'exy': 'exy_next'})
Yg = Yg.merge(nxt, on=['y', 'gid'], how='left')
nflow = Yg[['y', 'gid', 'fryw']].assign(y=(Yg.y.astype(int) - 1).astype(str)).rename(columns={'fryw': 'fry_next'})
Yg = Yg.merge(nflow, on=['y', 'gid'], how='left')
Yg['size_rk'] = Yg.groupby('y').pl_ant.rank(pct=True)
for c in ['ex12_l', 'ex36_l', 'vol36_l', 'beta36_l', 'te36_l', 'idade', 'n_acoes', 'top10', 'consenso', 'cli_pf', 'cli_fundos', 'cli_inst', 'perf_fee', 'sh_lb_l', 'exy']:
    Yg[c + '_rk'] = Yg.groupby('y')[c].rank(pct=True)
Yg = Yg[Yg.y.astype(int).between(2006, 2026)]
Yd = Yg.dropna(subset=['fryw', 'ex12_l_rk']).copy()
def r2(f, df):
    return smf.ols(f, df).fit().rsquared
Yd['lsize'] = np.log(Yd.pl_ant)
dec = {
    'so_ano (maré)': r2('fryw ~ C(y)', Yd),
    'so_alpha12 (rank)': r2('fryw ~ ex12_l_rk + I(ex12_l_rk**2)', Yd),
    'so_alpha12_e_ano_corrente': r2('fryw ~ ex12_l_rk + I(ex12_l_rk**2) + exy_rk', Yd.dropna(subset=['exy_rk'])),
    'ano + alpha12': r2('fryw ~ C(y) + ex12_l_rk + I(ex12_l_rk**2)', Yd),
    'ano + alpha12 + alpha do ano': r2('fryw ~ C(y) + ex12_l_rk + I(ex12_l_rk**2) + exy_rk', Yd.dropna(subset=['exy_rk'])),
    'ano + alpha + tamanho': r2('fryw ~ C(y) + ex12_l_rk + I(ex12_l_rk**2) + exy_rk + lsize', Yd.dropna(subset=['exy_rk'])),
}
Yd36 = Yd.dropna(subset=['ex36_l_rk', 'exy_rk'])
dec['ano + alpha12 + alpha36 + alpha do ano (amostra 36m)'] = r2('fryw ~ C(y) + ex12_l_rk + I(ex12_l_rk**2) + ex36_l_rk + exy_rk', Yd36)
dec['ano (amostra 36m)'] = r2('fryw ~ C(y)', Yd36)
dec['alphas (amostra 36m)'] = r2('fryw ~ ex12_l_rk + I(ex12_l_rk**2) + ex36_l_rk + exy_rk', Yd36)
R['decomp_anual'] = {k: round(v, 3) for k, v in dec.items()}
R['decomp_n'] = dict(obs=len(Yd), gestoras=int(Yd.gid.nunique()), anos=int(Yd.y.nunique()))

# Dólar: quanto do fluxo total em R$ é "maré" (fluxo médio do ano × PL) vs "relativo"
Yd['tide'] = Yd.groupby('y').flow.transform('sum') / Yd.groupby('y').pl_ant.transform('sum') * Yd.pl_ant
Yd['rel'] = Yd.flow - Yd.tide
R['dolar'] = dict(var_tide=float(Yd.tide.var()), var_rel=float(Yd.rel.var()),
                  share_tide=float(Yd.tide.var() / (Yd.tide.var() + Yd.rel.var())),
                  abs_tide=float(Yd.tide.abs().sum() / (Yd.tide.abs().sum() + Yd.rel.abs().sum())))

# B2: fluxo-performance por quintil de alpha 12m (início do ano), em anos de seca × cheia
Yd['q'] = Yd.groupby('y').ex12_l.transform(lambda x: pd.qcut(x.rank(method='first'), 5, labels=False) + 1)
regime = {y: ('seca' if fr < 0 else ('cheia' if fr > 0.10 else 'morno')) for y, fr in Y.fr.items()}
Yd['regime'] = Yd.y.map(regime)
qt = Yd.groupby(['regime', 'q']).agg(fr_med=('fryw', 'median'), fr_mean=('fryw', 'mean'), pos=('flow', lambda x: (x > 0).mean()), n=('gid', 'size')).reset_index()
R['quintis'] = qt.round(4).to_dict('records')
qt2 = Yd.assign(qy=Yd.groupby('y').exy.transform(lambda x: pd.qcut(x.rank(method='first'), 5, labels=False) + 1)).groupby(['regime', 'qy']).agg(
    fr_med=('fryw', 'median'), pos=('flow', lambda x: (x > 0).mean()), n=('gid', 'size')).reset_index()
R['quintis_ano'] = qt2.round(4).to_dict('records')
R['regime'] = regime

# B3: Fama-MacBeth mensal: fluxo do mês ~ alpha 12m (rank), alpha 36m, tamanho, vol — inclinações por regime
S['lsize'] = np.log(S.pl_ant)
reg12 = A.fr12.shift(1)  # fluxo agregado dos 12 meses até t-1
S['reg'] = S.ym.map(lambda y: 'seca' if reg12.get(y, np.nan) < 0 else ('cheia' if reg12.get(y, np.nan) > 0.10 else 'morno'))
fm = []
for ym, x in S.dropna(subset=['frw', 'ex12_rk', 'lsize']).groupby('ym'):
    if len(x) < 30: continue
    m = smf.ols('frw ~ ex12_rk + lsize', x).fit()
    fm.append(dict(ym=ym, reg=x.reg.iloc[0], **{k: v for k, v in m.params.items()}))
fm = pd.DataFrame(fm)
def fmsum(df):
    return {k: dict(coef=round(df[k].mean(), 5), t=round(df[k].mean() / df[k].std() * np.sqrt(len(df)) / np.sqrt(6), 2)) for k in ['ex12_rk', 'lsize']} | {'meses': len(df)}
R['fm'] = {'todos': fmsum(fm), **{r: fmsum(g) for r, g in fm.groupby('reg')}}
fm['y'] = fm.ym.str[:4]
R['fm_ano'] = fm.groupby('y').ex12_rk.mean().round(5).to_dict()

# ================= C. Quem capta na seca
sec = [y for y, r in regime.items() if r == 'seca' and int(y) >= 2006]
che = [y for y, r in regime.items() if r == 'cheia' and int(y) >= 2006]
R['anos_seca'] = sec; R['anos_cheia'] = che
feat = {'size_rk': 'Tamanho (rank)', 'ex12_l_rk': 'Alpha 12m antes (rank)', 'ex36_l_rk': 'Alpha 36m antes (rank)',
        'vol36_l_rk': 'Volatilidade 36m (rank)', 'beta36_l_rk': 'Beta 36m (rank)', 'te36_l_rk': 'Tracking error 36m (rank)',
        'idade_rk': 'Idade (rank)', 'n_acoes_rk': 'Nº de ações (rank)', 'top10_rk': 'Concentração top 10 (rank)',
        'consenso_rk': 'Peso nas 20 ações mais detidas (rank)', 'sh_lb_l_rk': '% em fundos long biased (rank)',
        'cli_pf_rk': '% clientes pessoa física (rank)', 'cli_fundos_rk': '% clientes fundos/alocadores (rank)',
        'cli_inst_rk': '% clientes institucionais (rank)', 'perf_fee_rk': '% receita de performance (rank)'}
def profile(years, label):
    x = Yd[Yd.y.isin(years)].copy()
    x['win'] = x.flow > 0
    x['topq'] = x.groupby('y').fryw.rank(pct=True) > 0.75
    out = []
    for f, nmf in feat.items():
        xx = x.dropna(subset=[f])
        w, l = xx[xx.win][f], xx[~xx.win][f]
        # diferença de médias com erro padrão por ano (cluster simples)
        dif = w.mean() - l.mean()
        byy = xx.groupby('y').apply(lambda z: z[z.win][f].mean() - z[~z.win][f].mean()).dropna()
        se = byy.std() / np.sqrt(len(byy)) if len(byy) > 1 else np.nan
        out.append(dict(var=f, nome=nmf, win=round(w.mean(), 3), lose=round(l.mean(), 3), dif=round(dif, 3),
                        t=round(byy.mean() / se, 2) if se and se > 0 else None, anos_mesmo_sinal=int((np.sign(byy) == np.sign(dif)).sum()), anos=int(len(byy)),
                        n=int(len(xx))))
    return dict(label=label, n=int(len(x)), n_win=int(x.win.sum()), pct_win=round(x.win.mean(), 3), tab=out)
R['perfil_seca'] = profile(sec, 'seca'); R['perfil_cheia'] = profile(che, 'cheia')
# logit multivariado (seca), ranks centrados
from statsmodels.discrete.discrete_model import Logit
def logit(years, cols):
    x = Yd[Yd.y.isin(years)].dropna(subset=cols).copy(); x['win'] = (x.flow > 0).astype(int)
    X = pd.concat([x[cols] - 0.5, pd.get_dummies(x.y, prefix='a', drop_first=True, dtype=float)], axis=1)
    m = Logit(x.win, sm.add_constant(X)).fit(disp=0, cov_type='cluster', cov_kwds={'groups': x.gid.astype('category').cat.codes})
    return dict(n=int(m.nobs), pseudo_r2=round(m.prsquared, 3), coef={c: round(m.params[c], 3) for c in cols}, t={c: round(m.tvalues[c], 2) for c in cols})
base = ['size_rk', 'ex12_l_rk', 'ex36_l_rk', 'idade_rk', 'vol36_l_rk']
R['logit_seca'] = logit(sec, base); R['logit_cheia'] = logit(che, base)
R['logit_seca_estilo'] = logit(sec, base + ['top10_rk', 'consenso_rk', 'sh_lb_l_rk'])
R['logit_seca_cliente'] = logit([y for y in sec if int(y) >= 2017], ['size_rk', 'ex12_l_rk', 'ex36_l_rk', 'cli_pf_rk', 'cli_inst_rk', 'cli_fundos_rk', 'perf_fee_rk'])
R['logit_cheia_cliente'] = logit([y for y in che if int(y) >= 2017], ['size_rk', 'ex12_l_rk', 'ex36_l_rk', 'cli_pf_rk', 'cli_inst_rk', 'cli_fundos_rk', 'perf_fee_rk'])

# concentração dos ganhadores na seca e o que veio depois
cc = []
for y in sec + che:
    x = Yd[Yd.y == y]
    pos = x[x.flow > 0].sort_values('flow', ascending=False)
    cc.append(dict(y=y, regime=regime[y], n=len(x), n_pos=len(pos), cap_pos_bi=round(pos.flow.sum() / 1e9, 2), saida_neg_bi=round(x[x.flow < 0].flow.sum() / 1e9, 2),
                   top5_share=round(pos.flow.head(5).sum() / pos.flow.sum(), 3) if len(pos) else None,
                   top=[dict(nome=r.nome, flow_mi=round(r.flow / 1e6), fr=round(r.fry, 3), ex12=None if pd.isna(r.ex12_l) else round(r.ex12_l, 3),
                             size_rk=round(r.size_rk, 2), idade=None if pd.isna(r.idade) else round(r.idade, 1)) for r in pos.head(8).itertuples()]))
R['ganhadores'] = cc
x = Yd[Yd.y.isin(sec)].copy(); x['win'] = x.flow > 0
R['depois_seca'] = dict(
    exy_next_win=round(x[x.win].exy_next.median(), 4), exy_next_lose=round(x[~x.win].exy_next.median(), 4),
    exy_next_win_mean=round(x[x.win].exy_next.mean(), 4), exy_next_lose_mean=round(x[~x.win].exy_next.mean(), 4),
    fry_next_win=round(x[x.win].fry_next.median(), 4), fry_next_lose=round(x[~x.win].fry_next.median(), 4),
    exy_win=round(x[x.win].exy.median(), 4), exy_lose=round(x[~x.win].exy.median(), 4),
    bateu_next_win=round((x[x.win].exy_next > 0).mean(), 3), bateu_next_lose=round((x[~x.win].exy_next > 0).mean(), 3),
    n_win=int(x.win.sum()), n_lose=int((~x.win).sum()))
dd = x.groupby('y').apply(lambda z: z[z.win].exy_next.mean() - z[~z.win].exy_next.mean()).dropna()
R['depois_seca']['dif_media_anos'] = round(dd.mean(), 4); R['depois_seca']['t'] = round(dd.mean() / (dd.std() / np.sqrt(len(dd))), 2); R['depois_seca']['anos_pos'] = int((dd > 0).sum()); R['depois_seca']['anos'] = int(len(dd))
dd2 = x.groupby('y').apply(lambda z: z[z.win].fry_next.median() - z[~z.win].fry_next.median()).dropna()
R['depois_seca']['fry_anos_pos'] = int((dd2 > 0).sum())
x = Yd[Yd.y.isin(che)].copy(); x['win'] = x.fry > x.groupby('y').fry.transform('median')
R['depois_cheia'] = dict(exy_next_win=round(x[x.win].exy_next.median(), 4), exy_next_lose=round(x[~x.win].exy_next.median(), 4))

# probabilidade de captar na seca por decil de tamanho e de alpha (para gráfico)
x = Yd[Yd.y.isin(sec)].copy(); x['win'] = x.flow > 0
x['ds'] = (x.size_rk * 5).clip(0, 4.999).astype(int); x['da'] = (x.ex12_l_rk * 5).clip(0, 4.999).astype(int)
R['grid_seca'] = x.groupby(['ds', 'da']).win.mean().round(3).reset_index().to_dict('records')
R['grid_seca_n'] = x.groupby(['ds', 'da']).size().reset_index().to_dict('records')
R['p_size'] = x.groupby('ds').win.mean().round(3).to_dict()
R['p_alpha'] = x.groupby('da').win.mean().round(3).to_dict()
y2 = Yd[Yd.y.isin(che)].copy(); y2['win'] = y2.flow > 0
y2['ds'] = (y2.size_rk * 5).clip(0, 4.999).astype(int); y2['da'] = (y2.ex12_l_rk * 5).clip(0, 4.999).astype(int)
R['p_size_cheia'] = y2.groupby('ds').win.mean().round(3).to_dict(); R['p_alpha_cheia'] = y2.groupby('da').win.mean().round(3).to_dict()

# série mensal para o gráfico do ciclo
A2 = A.loc['2006-01':, ['fr', 'fr12', 'fr_mkt', 'ibov12', 'cdi_aa', 'ibov_cdi12', 'ex12_med', 'bateu', 'ng']].copy()
A2['pl_bi'] = A.pl_ant / 1e9; A2['flow_bi'] = A.flow / 1e9
R['mensal'] = A2.reset_index().rename(columns={'index': 'ym'}).replace({np.nan: None}).round(5).to_dict('records')
# gestora-ano para tabela navegável
keep = ['y', 'nome', 'pl_ant', 'flow', 'fry', 'ex12_l', 'ex36_l', 'exy', 'exy_next', 'idade', 'size_rk', 'n_acoes', 'top10', 'cli_pf', 'cli_inst', 'cli_fundos']
R['gestora_ano'] = Yd[keep].round(4).replace({np.nan: None}).to_dict('records')
json.dump(R, open(SAIDA, 'w'), default=lambda o: o.item() if hasattr(o, 'item') else str(o), ensure_ascii=False)
Yd.to_pickle(os.path.join(OUT, 'gestora_ano.pkl')); S.to_pickle(os.path.join(OUT, 'amostra_mes.pkl'))
for k in ['agg_anual', 'agg_reg', 'decomp_anual', 'decomp_n', 'dolar', 'fm', 'anos_seca', 'anos_cheia', 'logit_seca', 'logit_cheia', 'logit_seca_estilo', 'logit_seca_cliente', 'logit_cheia_cliente', 'depois_seca', 'depois_cheia', 'p_size', 'p_alpha', 'p_size_cheia', 'p_alpha_cheia']:
    print(k, json.dumps(R[k], default=str, ensure_ascii=False))
print(pd.DataFrame(R['anos']).round(3).to_string())
for p in ['perfil_seca', 'perfil_cheia']:
    print(p, R[p]['n'], R[p]['pct_win']); print(pd.DataFrame(R[p]['tab']).to_string())
print(pd.DataFrame(R['quintis']).to_string()); print(pd.DataFrame(R['quintis_ano']).to_string())
for c in R['ganhadores']:
    print(c['y'], c['regime'], c['n_pos'], '/', c['n'], c['cap_pos_bi'], c['saida_neg_bi'], c['top5_share'], [(t['nome'], t['flow_mi']) for t in c['top'][:6]])
