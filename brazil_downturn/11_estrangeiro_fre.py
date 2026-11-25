"""Brazil Downturn, passo 11: o estrangeiro pelo Formulário de Referência (FRE), ano a ano (dez/2017 a dez/2025).
Os fundos da CVM só mostram o não residente que compra cota de fundo brasileiro. O FRE traz o patrimônio de cada gestora por tipo
de cliente, inclusive "investidores não residentes", que cobre os fundos offshore e mandatos de fora. É uma foto de 31/dez, da casa inteira.
Casa de ações: PL em fundos de ações na CVM (dezembro, sem dupla contagem) >= 40% do patrimônio doméstico do FRE (AUM - não residentes).
Assim o dinheiro estrangeiro da casa é, na prática, dinheiro em ações. Anos com erro de unidade (AUM 5x acima ou abaixo do ano anterior) saem.
Fluxo estimado do ano = posição no fim - posição no fim do ano anterior x (1 + retorno líquido da gestora no ano, fundos de ações da CVM).
Uso: python3 11_estrangeiro_fre.py <out> <carteiras.json> <gestoras_fr.json> <usdbrl.json> <ust10.csv> <saida.json>
"""
import sys, os, re, json
import pandas as pd, numpy as np
import statsmodels.formula.api as smf

OUT, CJ, FRJ, FXJ, UST, SAIDA = sys.argv[1:7]
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]
GM = pd.read_pickle(os.path.join(OUT, 'gestora_mes.pkl'))
S = pd.read_pickle(os.path.join(OUT, 'amostra_mes.pkl'))
IX = pd.read_csv(os.path.join(OUT, 'indices.csv'), index_col=0)
d = json.load(open(CJ)); r2g = {}
for g in d['gestoras']:
    for r in ({g['id']} | ({root8(x[1]) for x in g['mb']} if not g.get('rb') else set())): r2g.setdefault(r, g['id'])
gname = {g['id']: g['n'] for g in d['gestoras']}
fr = json.load(open(FRJ))
rows = []
for x in fr['gestoras']:
    gid = r2g.get(root8(x['cnpj']))
    if not gid: continue
    for y, v in x['y'].items():
        ac = v.get('ac') or [None] * 12; ic = v.get('ic') or [None] * 12
        rows.append(dict(gid=gid, y=int(y), a=v.get('a') or 0, nres=ac[10] or 0, n_nres=ic[10] or 0, it=v.get('it') or 0))
F = pd.DataFrame(rows).groupby(['gid', 'y']).sum().reset_index()      # gestoras com mais de um CNPJ: soma
F = F[F.a > 0].sort_values(['gid', 'y'])
F['a_ant'] = F.groupby('gid').a.shift(); F['y_ant'] = F.groupby('gid').y.shift()
erro = (F.a_ant > 0) & ((F.a / F.a_ant > 5) | (F.a / F.a_ant < 0.2))
print('gestora-anos com erro de unidade (fora):', int(erro.sum()))
F = F[~erro].copy()
# PL em ações na CVM em dezembro e retorno líquido no ano
GM['y'] = GM.ym.str[:4].astype(int)
dez = GM[GM.ym.str.endswith('-12')][['gid', 'y', 'pl']].rename(columns={'pl': 'pl_cvm'})
ret = GM.groupby(['gid', 'y']).r.apply(lambda s: np.prod(1 + s.fillna(0)) - 1 if s.notna().sum() >= 10 else np.nan).rename('r_ano').reset_index()
F = F.merge(dez, on=['gid', 'y'], how='left').merge(ret, on=['gid', 'y'], how='left')
F['dom'] = F.a - F.nres
F['eq_share'] = F.pl_cvm / F.dom.replace(0, np.nan)
F['casa_acoes'] = F.eq_share >= 0.4
F = F.sort_values(['gid', 'y'])
for c in ['nres', 'dom', 'n_nres', 'it', 'casa_acoes']:
    F[c + '_ant'] = F.groupby('gid')[c].shift()
cons = F.groupby('gid').y.shift() == F.y - 1
F.loc[~cons, ['nres_ant', 'dom_ant', 'n_nres_ant', 'it_ant', 'casa_acoes_ant']] = np.nan
F['f_nres'] = F.nres - F.nres_ant * (1 + F.r_ano)
F['f_dom'] = F.dom - F.dom_ant * (1 + F.r_ano)
F['nome'] = F.gid.map(gname)
# universo: casa de ações no ano anterior e no ano (para o fluxo) e gestora do universo point-in-time em janeiro
U = S[S.ym.str.endswith('-01')][['gid', 'ym', 'ex12_l', 'ex36_l', 'vol36_l', 'beta36_l', 'te36_l', 'idade', 'top10', 'n_acoes', 'consenso', 'sh_lb_l', 'pl_ant']].copy()
U['y'] = U.ym.str[:4].astype(int)
A = F.merge(U.drop(columns='ym'), on=['gid', 'y'], how='inner')
nivel = A[A.casa_acoes.fillna(False).astype(bool)].copy()                         # foto do ano
fluxo = A[A.casa_acoes.fillna(False).astype(bool) & A.casa_acoes_ant.fillna(False).astype(bool) & A.r_ano.notna()].copy()
print('casas de ações (gestora-ano):', len(nivel), '| com fluxo:', len(fluxo), '| anos', sorted(nivel.y.unique()))

# ---------------- mercado por ano
ib, cdi = IX.ibov, IX.cdi
fx = pd.DataFrame(json.load(open(FXJ))); fx['ym'] = pd.to_datetime(fx.data, dayfirst=True).dt.strftime('%Y-%m'); fx = fx.set_index('ym').valor.astype(float)
ust = pd.read_csv(UST); ust.columns = ['d', 'v']; ust['v'] = pd.to_numeric(ust.v, errors='coerce'); ust = ust.dropna(); ust = ust.groupby(ust.d.str[:7]).v.last() / 100
MK = {}
for y in range(2017, 2026):
    a, b = f'{y}-01', f'{y}-12'
    ibv = float(np.prod(1 + ib.loc[a:b]) - 1); dfx = fx.get(b) / fx.get(f'{y - 1}-12') - 1
    MK[y] = dict(ibov=ibv, ibov_usd=(1 + ibv) / (1 + dfx) - 1, usdbrl=dfx, cdi=(1 + cdi.get(b)) ** 12 - 1,
                 dcdi=(1 + cdi.get(b)) ** 12 - (1 + cdi.get(f'{y - 1}-12')) ** 12, ust=ust.get(b), dust=ust.get(b) - ust.get(f'{y - 1}-12'))
# ---------------- agregado por ano
AG = []
for y in sorted(nivel.y.unique()):
    n = nivel[nivel.y == y]; fl = fluxo[fluxo.y == y]
    r = dict(y=int(y), casas=int(len(n)), casas_com=int((n.nres > 0).sum()), nres_bi=n.nres.sum() / 1e9, dom_bi=n.dom.sum() / 1e9, pl_cvm_bi=n.pl_cvm.sum() / 1e9,
             sh=n.nres.sum() / n.a.sum(), n_inv=int(n.n_nres.sum()),
             tk_mi=(n.nres.sum() / max(1, n.n_nres.sum())) / 1e6, tk_dom_mil=(n.dom.sum() / max(1, (n.it - n.n_nres).sum())) / 1e3,
             top5=float(n.nres.nlargest(5).sum() / n.nres.sum()) if n.nres.sum() > 0 else None)
    if len(fl):
        r.update(f_nres_bi=fl.f_nres.sum() / 1e9, fr_nres=fl.f_nres.sum() / fl.nres_ant.sum() if fl.nres_ant.sum() > 0 else None,
                 f_dom_bi=fl.f_dom.sum() / 1e9, fr_dom=fl.f_dom.sum() / fl.dom_ant.sum(), n_fluxo=int(len(fl)),
                 pos_nres=float((fl[fl.nres_ant > 50e6].f_nres > 0).mean()))
    r.update(MK.get(int(y), {}))
    AG.append(r)
AG = pd.DataFrame(AG)
print(AG.round(3).to_string())
yy = AG.dropna(subset=['fr_nres'])
drv = {}
for k in ['ibov', 'ibov_usd', 'usdbrl', 'cdi', 'dcdi', 'ust', 'dust']:
    drv[k] = dict(est=round(float(yy.fr_nres.corr(yy[k])), 2), dom=round(float(yy.fr_dom.corr(yy[k])), 2), n=int(len(yy)))
print('correlação anual (estrangeiro, doméstico):', drv)
# regimes (anos)
REGS = {'ibov_usd': ('Ibovespa em dólar no ano', lambda r: r.ibov_usd > 0), 'ibov': ('Ibovespa em reais no ano', lambda r: r.ibov > 0), 'usdbrl': ('Dólar no ano', lambda r: r.usdbrl > 0), 'selic': ('Selic no ano', lambda r: r.dcdi > 0.0025),
        'ust': ('Treasury 10a no ano', lambda r: r.dust > 0)}
LBL = {'ibov_usd': ('Ibovespa em dólar subiu', 'Ibovespa em dólar caiu'), 'ibov': ('Ibovespa subiu', 'Ibovespa caiu'), 'usdbrl': ('Real se desvalorizou', 'Real se valorizou'), 'selic': ('Selic subiu', 'Selic caiu ou parada'), 'ust': ('Treasury subiu', 'Treasury caiu')}
reg = {}
for k, (nm, fn) in REGS.items():
    m = yy.apply(fn, axis=1)
    reg[k] = dict(nome=nm, rot=LBL[k], alta=dict(anos=[int(v) for v in yy[m].y], est=float(yy[m].f_nres_bi.mean()) if m.any() else None, dom=float(yy[m].f_dom_bi.mean()) if m.any() else None,
                                                  fr_est=float(yy[m].fr_nres.mean()) if m.any() else None, fr_dom=float(yy[m].fr_dom.mean()) if m.any() else None),
                  baixa=dict(anos=[int(v) for v in yy[~m].y], est=float(yy[~m].f_nres_bi.mean()) if (~m).any() else None, dom=float(yy[~m].f_dom_bi.mean()) if (~m).any() else None,
                             fr_est=float(yy[~m].fr_nres.mean()) if (~m).any() else None, fr_dom=float(yy[~m].fr_dom.mean()) if (~m).any() else None))
# ---------------- quem recebe, perfil 0-100, alpha 1a x 3a
ATTR = {'ex12_l': 'Alpha 12 meses', 'ex36_l': 'Alpha 36 meses (ao ano)', 'pl_ant': 'Tamanho (PL em ações)', 'top10': 'Concentração (peso das 10 maiores)',
        'n_acoes': 'Nº de ações na carteira', 'beta36_l': 'Beta 36m', 'vol36_l': 'Volatilidade 36m', 'te36_l': 'Tracking error 36m', 'idade': 'Idade da gestora',
        'sh_lb_l': '% do PL em long biased', 'consenso': 'Peso nas 20 ações mais detidas', 'dep': 'Peso do estrangeiro no patrimônio'}
nivel['dep'] = nivel.nres / nivel.a
fluxo['dep'] = fluxo.nres_ant / (fluxo.nres_ant + fluxo.dom_ant)
for D in (nivel, fluxo):
    for c in ATTR: D[c + '_rk'] = D.groupby('y')[c].rank(pct=True) * 100
def perfil(D, mask):
    out = {}
    for c in ATTR:
        x = D.dropna(subset=[c + '_rk'])
        dq = x.groupby('y').apply(lambda z: z[mask.loc[z.index]][c + '_rk'].mean() - z[~mask.loc[z.index]][c + '_rk'].mean()).dropna()
        t = dq.mean() / (dq.std() / np.sqrt(len(dq))) if len(dq) > 2 and dq.std() > 0 else None
        out[c] = dict(w=round(x[mask.loc[x.index]][c + '_rk'].mean(), 1), l=round(x[~mask.loc[x.index]][c + '_rk'].mean(), 1), t=None if t is None or not np.isfinite(t) else round(t, 2),
                      same=int((np.sign(dq) == np.sign(dq.mean())).sum()), ny=int(len(dq)))
    return out
tem = nivel.nres > 0
PERF_TEM = perfil(nivel, tem)                                                  # quem tem estrangeiro x quem não tem
fx_ = fluxo[(fluxo.nres_ant > 20e6) | (fluxo.f_nres.abs() > 20e6)].copy()
rec = fx_.f_nres > 0
PERF_REC = perfil(fx_, rec)                                                    # quem recebeu x quem perdeu
fx_['ibov_y'] = fx_.y.map(lambda y: MK[int(y)]['ibov_usd'])                    # mercado ruim para o estrangeiro: Ibovespa em dólar negativo
PERF_REC_RUIM = perfil(fx_[fx_.ibov_y < 0], rec[fx_.ibov_y < 0]) if (fx_.ibov_y < 0).sum() > 20 else None
# sensibilidade (painel com efeito de ano, erro por gestora): estrangeiro x doméstico
def sens(D, k):
    x = D[(D[k + '_ant'] > 20e6)].copy(); x['yv'] = x['f_' + k] / x[k + '_ant']
    lo, hi = x.yv.quantile([.03, .97]); x['yv'] = x.yv.clip(lo, hi) * 100
    x['a12'] = x.ex12_l_rk / 100 - .5; x['a36'] = x.ex36_l_rk / 100 - .5; x['ls'] = np.log(x.pl_ant)
    x = x.dropna(subset=['yv', 'a12', 'a36', 'ls'])
    m = smf.ols('yv ~ a12 + a36 + ls + C(y)', x).fit(cov_type='cluster', cov_kwds={'groups': x.gid.astype('category').cat.codes})
    return dict(a12=dict(b=round(m.params.a12, 1), t=round(m.tvalues.a12, 2)), a36=dict(b=round(m.params.a36, 1), t=round(m.tvalues.a36, 2)), n=int(m.nobs))
SENS = dict(estrangeiro=sens(fluxo, 'nres'), domestico=sens(fluxo, 'dom'))
print('sensibilidade ao alpha (p.p. do fluxo do ano, pior -> melhor):', SENS)
# listas por ano
TOP = {}
for y, x in fluxo.groupby('y'):
    x = x[x.f_nres.abs() > 1e6]
    f = lambda z: [dict(nome=r.nome, f_mi=round(r.f_nres / 1e6), pos_mi=round(r.nres / 1e6), pct=None if not r.nres_ant else round(r.f_nres / r.nres_ant, 3),
                        n_inv=int(r.n_nres), a12=None if pd.isna(r.ex12_l) else round(r.ex12_l, 3)) for r in z.itertuples()]
    TOP[int(y)] = dict(rec=f(x.sort_values('f_nres', ascending=False).head(8)), saq=f(x.sort_values('f_nres').head(8)),
                       n_rec=int((x.f_nres > 0).sum()), n_saq=int((x.f_nres < 0).sum()), rec_bi=round(x.f_nres.clip(lower=0).sum() / 1e9, 2), saq_bi=round(x.f_nres.clip(upper=0).sum() / 1e9, 2))
MAIORES = {int(y): [dict(nome=r.nome, pos_mi=round(r.nres / 1e6), sh=round(r.nres / r.a, 3), n_inv=int(r.n_nres), tk_mi=round(r.nres / max(1, r.n_nres) / 1e6, 1))
                    for r in x.sort_values('nres', ascending=False).head(10).itertuples()] for y, x in nivel.groupby('y')}
# tamanho do cheque por investidor estrangeiro (gestoras com estrangeiro)
tk = nivel[nivel.n_nres > 0].assign(tk=lambda z: z.nres / z.n_nres)
TK = dict(mediana_mi=round(float(tk.tk.median() / 1e6), 1), p25=round(float(tk.tk.quantile(.25) / 1e6), 1), p75=round(float(tk.tk.quantile(.75) / 1e6), 1),
          inv_por_casa_mediana=float(tk.n_nres.median()))
print('cheque por investidor estrangeiro (R$ mi):', TK)
print('regimes:', json.dumps(reg, default=str))
out = dict(agregado=AG.round(5).replace({np.nan: None}).to_dict('records'), drivers=drv, regimes=reg, perfil_tem=PERF_TEM, perfil_rec=PERF_REC, perfil_rec_ruim=PERF_REC_RUIM,
           attr=ATTR, sens=SENS, tops=TOP, maiores=MAIORES, ticket=TK, n_nivel=int(len(nivel)), n_fluxo=int(len(fluxo)))
def _l(o):
    if isinstance(o, dict): return {str(k): _l(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_l(v) for v in o]
    if hasattr(o, 'item') and not isinstance(o, str): o = o.item()
    if isinstance(o, float) and not np.isfinite(o): return None
    return o
json.dump(_l(out), open(SAIDA, 'w'), ensure_ascii=False, separators=(',', ':'), allow_nan=False)
for nm, P in [('tem estrangeiro x não tem', PERF_TEM), ('recebeu x perdeu', PERF_REC), ('recebeu x perdeu (Ibov negativo no ano)', PERF_REC_RUIM)]:
    if P: print(nm); print(pd.DataFrame(P).T.to_string())
for y in sorted(TOP): print(y, TOP[y]['rec_bi'], TOP[y]['saq_bi'], [(r['nome'], r['f_mi']) for r in TOP[y]['rec'][:4]], [(r['nome'], r['f_mi']) for r in TOP[y]['saq'][:3]])
