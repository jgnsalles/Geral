"""Brazil Downturn, passo 6: fluxo por tipo de investidor final, por gestora e trimestre (2019T2 a 2026T3), e todas as análises por tipo.

Posição de cada tipo k na gestora g no fim do trimestre q (H_k,g,q):
  - nos fundos de ações elegíveis da gestora (masters, sem FIC/exclusivo/previdência/indexado): PL x % do tipo no Perfil Mensal;
  - a parte detida por fundos (FI/clube + "outro", que até 2020 recebia fundos) é aberta pela CDA (bloco de cotas de fundos):
      feeders da própria gestora -> atravessa até o investidor final pelo Perfil Mensal do feeder;
      fundos de outras casas -> "alocadores" (FoFs de plataformas, bancos, multimercados, family offices).
Fluxo do tipo = H_q - H_(q-1) x (1 + retorno da gestora no trimestre). Todos os tipos ganham o mesmo retorno (mesma cota).
Uso: python3 06_passivo.py <raw> <out> <carteiras.json> <ust10.csv> <saida.json>
"""
import sys, os, re, json, zipfile
import pandas as pd, numpy as np
import statsmodels.formula.api as smf

RAW, OUT, CJ, UST, SAIDA = sys.argv[1:6]
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]
fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if isinstance(c, str) and len(c) == 14 else c
GRP = {'private': ['PF_PB'], 'varejo': ['PF_VAREJO'], 'plataformas': ['DISTRIB'], 'previdencia': ['EAPC', 'SEGUR', 'CAPITALIZ'],
       'pensao': ['EFPC', 'RPPS'], 'estrangeiro': ['INVNR'], 'empresas': ['PJ_NAO_FINANC_PB', 'PJ_NAO_FINANC_VAREJO', 'BANCO', 'CORRETORA_DISTRIB', 'PJ_FINANC']}
FUND = ['FI_CLUBE', 'OUTRO']
TYPES = list(GRP) + ['wealth', 'alocadores']
NOMES = {'total': 'Todos', 'private': 'PF private', 'varejo': 'PF varejo direto', 'plataformas': 'Plataformas (conta e ordem)',
         'wealth': 'Wealth (private banks e family offices, via fundo)', 'alocadores': 'FoFs e gestoras de terceiros', 'previdencia': 'Previdência aberta', 'pensao': 'Fundos de pensão e RPPS',
         'estrangeiro': 'Estrangeiro', 'empresas': 'Empresas e bancos'}
# até 2026-09. De abr/2026 em diante a CDA ainda está parcialmente em sigilo (cotas de fundos -18% em jun, -35% em set):
# nesses trimestres, fundo cuja lista de cotistas-fundo veio incompleta usa a de mar/2026 (BASEQ), com o Perfil Mensal atual de cada cotista.
QM = [f'{y}-{m:02d}' for y in range(2019, 2027) for m in (3, 6, 9, 12) if f'{y}-{m:02d}' <= '2026-09']
BASEQ, EST_Q = '2026-03', ['2026-06', '2026-09']

# ---------------- dados
P = pd.read_pickle(os.path.join(OUT, 'fundo_mes.pkl'))
PF = pd.read_pickle(os.path.join(OUT, 'perfil.pkl')).sort_values(['CNPJ_FUNDO', 'ym'])
PC = pd.read_pickle(os.path.join(OUT, 'perfil_cotistas.pkl'))
B = pd.read_pickle(os.path.join(OUT, 'cotistas_fundos.pkl'))
S = pd.read_pickle(os.path.join(OUT, 'amostra_mes.pkl'))       # amostra do passo 3 (universo, atributos, Opportunity fora)
GM = pd.read_pickle(os.path.join(OUT, 'gestora_mes.pkl'))
IX = pd.read_csv(os.path.join(OUT, 'indices.csv'), index_col=0)
TIPCOLS = [c for c in PF.columns if c not in ('CNPJ_FUNDO', 'ym')]

def norm(df):
    s = df[TIPCOLS].sum(axis=1).replace(0, np.nan)
    df[TIPCOLS] = df[TIPCOLS].div(s, axis=0)
    return df
# perfil do fundo no fim do trimestre (ou até 2 meses antes)
PF = PF[PF.ym >= '2019-01']
grid = pd.MultiIndex.from_product([PF.CNPJ_FUNDO.unique(), [str(p) for p in pd.period_range('2019-01', '2026-10', freq='M')]], names=['CNPJ_FUNDO', 'ym'])
PFg = PF.set_index(['CNPJ_FUNDO', 'ym']).reindex(grid).groupby(level=0).ffill(limit=2).reset_index()
PFq = norm(PFg[PFg.ym.isin(QM)].dropna(subset=TIPCOLS, how='all').copy())
PC = norm(PC.copy())

# gestor de qualquer fundo na data (mesma regra do passo 2)
z = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
h = pd.read_csv(z.open('cad_fi_hist_gestor.csv'), sep=';', encoding='latin1', dtype=str)
h = h[h.PF_PJ_GESTOR == 'PJ'][['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'DT_INI_GESTOR', 'DT_FIM_GESTOR']].copy()
h['ini'] = pd.to_datetime(h.DT_INI_GESTOR, errors='coerce'); h['fim'] = pd.to_datetime(h.DT_FIM_GESTOR, errors='coerce').fillna(pd.Timestamp('2100-01-01'))
zr = zipfile.ZipFile(os.path.join(RAW, 'registro_fundo_classe.zip'))
rc = pd.read_csv(zr.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str); rc['CNPJ_FUNDO'] = rc.CNPJ_Classe.str.zfill(14).map(fmt)
rf = pd.read_csv(zr.open('registro_fundo.csv'), sep=';', encoding='latin1', dtype=str); rf['g'] = rf.CPF_CNPJ_Gestor.fillna('').str.zfill(14).map(fmt)
REG = pd.concat([rc.merge(rf[['ID_Registro_Fundo', 'g']], on='ID_Registro_Fundo')[['CNPJ_FUNDO', 'g']],
                 rf.assign(CNPJ_FUNDO=rf.CNPJ_Fundo.str.zfill(14).map(fmt))[['CNPJ_FUNDO', 'g']]]).drop_duplicates('CNPJ_FUNDO').set_index('CNPJ_FUNDO').g
cad = pd.read_csv(os.path.join(RAW, 'cad_fi.csv'), sep=';', encoding='latin1', dtype=str)
CADG = cad[cad.PF_PJ_GESTOR == 'PJ'].drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').CPF_CNPJ_GESTOR
hb = B[['CNPJ_FUNDO', 'ym']].drop_duplicates(); hb['d'] = pd.to_datetime(hb.ym + '-15')
m = hb.merge(h, on='CNPJ_FUNDO'); m = m[(m.d >= m.ini) & (m.d <= m.fim)].sort_values('ini').drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
hb = hb.merge(m[['CNPJ_FUNDO', 'ym', 'CPF_CNPJ_GESTOR']], on=['CNPJ_FUNDO', 'ym'], how='left')
late = hb.CPF_CNPJ_GESTOR.isna() & (hb.ym >= '2023-10'); hb.loc[late, 'CPF_CNPJ_GESTOR'] = hb.loc[late, 'CNPJ_FUNDO'].map(REG)
for src in (CADG, REG):
    na = hb.CPF_CNPJ_GESTOR.isna(); hb.loc[na, 'CPF_CNPJ_GESTOR'] = hb.loc[na, 'CNPJ_FUNDO'].map(src)
d = json.load(open(CJ)); r2g = {}
for g in d['gestoras']:
    for r in ({g['id']} | ({root8(x[1]) for x in g['mb']} if not g.get('rb') else set())): r2g.setdefault(r, g['id'])
hb['hr8'] = hb.CPF_CNPJ_GESTOR.map(root8); hb['hgid'] = hb.hr8.map(r2g)
B = B.merge(hb[['CNPJ_FUNDO', 'ym', 'hr8', 'hgid']], on=['CNPJ_FUNDO', 'ym'], how='left')

# ---------------- masters elegíveis das gestoras do universo, fim de trimestre
univ_g = set(S.gid)
# perímetro: todos os fundos de ações da gestora (qualquer status, sem indexados). Cada real é contado uma vez, no investidor final:
# a parte de um fundo detida por outro fundo da própria gestora que também está no perímetro fica para o nível do cotista.
M = P[~P.indexado & P.ym.isin(QM) & P.gid.isin(univ_g) & (P.pl > 0)][['CNPJ_FUNDO', 'ym', 'gid', 'r8', 'pl', 'eleg']].copy()
PSET = set(zip(M.CNPJ_FUNDO, M.ym))
M = M.merge(PFq, on=['CNPJ_FUNDO', 'ym'], how='left')
M['sem_perfil'] = M[TIPCOLS].isna().all(axis=1)
M[TIPCOLS] = M[TIPCOLS].fillna(0)
for k, cs in GRP.items(): M['d_' + k] = M.pl * M[cs].sum(axis=1)
M['F'] = M.pl * M[FUND].sum(axis=1)
M.loc[M.sem_perfil, 'F'] = 0; M['nao_ident'] = np.where(M.sem_perfil, M.pl, 0.0)
# cotistas-fundo: abertura recursiva até o investidor final.
# vetor de tipos de um fundo X = % não-fundo do X + % fundo do X repartido entre seus fundos cotistas (CDA):
#   cotista da mesma gestora -> abre o vetor dele (até 4 níveis); cotista de outra casa -> alocadores; sem cotista na CDA -> alocadores (sem_cda).
PER = pd.concat([PFq[['CNPJ_FUNDO', 'ym'] + TIPCOLS], PC[['CNPJ_FUNDO', 'ym'] + TIPCOLS]]).drop_duplicates(['CNPJ_FUNDO', 'ym']).set_index(['CNPJ_FUNDO', 'ym'])
PERd = {k: v for k, v in zip(PER.index, PER[TIPCOLS].to_numpy())}
TI = {c: i for i, c in enumerate(TIPCOLS)}
GI = {k: [TI[c] for c in cs] for k, cs in GRP.items()}
FI_ = [TI[c] for c in FUND]
B['hr8'] = B.hr8.fillna(''); B['hgid'] = B.hgid.fillna('')
HOLD, VT = {}, {}
for (inv, ym), x in B[B.CNPJ_FUNDO != B.CNPJ_FUNDO_COTA].groupby(['CNPJ_FUNDO_COTA', 'ym']):
    tot = x.v.sum()
    if tot > 0: HOLD[(inv, ym)] = list(zip(x.CNPJ_FUNDO, x.v / tot, x.hgid, x.hr8)); VT[(inv, ym)] = tot
# trimestres com CDA parcial: completa com a estrutura de mar/2026 quando o valor em cotas caiu mais de 30% contra mar/2026
_pl = P.set_index(['CNPJ_FUNDO', 'ym']).pl
n_fill = {}
for ym in EST_Q:
    for (inv, y0), hs in list(HOLD.items()):
        if y0 != BASEQ: continue
        v0, v1 = VT.get((inv, BASEQ), 0), VT.get((inv, ym), 0)
        g0, g1 = _pl.get((inv, BASEQ), np.nan), _pl.get((inv, ym), np.nan)
        esc = (g1 / g0) if (g0 and g0 > 0 and g1 == g1) else 1.0
        if v1 < 0.7 * v0 * esc:
            HOLD[(inv, ym)] = hs; n_fill[ym] = n_fill.get(ym, 0) + 1
print('fundos com cotistas-fundo de mar/2026 nos trimestres estimados:', n_fill)
OUTK = list(GRP) + ['wealth', 'alocadores', 'sem_cda', 'nao_ident']
# classificação do fundo cotista de outra casa pelo nome do gestor e do fundo
gn = pd.concat([rf.assign(r=rf.g.map(root8))[['r', 'Gestor']], cad.assign(r=cad.CPF_CNPJ_GESTOR.map(root8))[['r', 'GESTOR']].rename(columns={'GESTOR': 'Gestor'})]).dropna().drop_duplicates('r').set_index('r').Gestor
fnm = pd.concat([cad[['CNPJ_FUNDO', 'DENOM_SOCIAL']], rc[['CNPJ_FUNDO', 'Denominacao_Social']].rename(columns={'Denominacao_Social': 'DENOM_SOCIAL'})]).drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').DENOM_SOCIAL
import unicodedata
dea = lambda x: unicodedata.normalize('NFD', str(x or '')).encode('ascii', 'ignore').decode().upper()
R_PEN = re.compile(r'FUNDACAO|SEGURIDADE|PREVIDENCIA COMPLEMENTAR|\bPETROS\b|\bVALIA\b|FUNCEF|REAL GRANDEZA|ELETROS|\bPRECE\b|SISTEL|FORLUZ|\bRPPS\b|INSTITUTO DE PREVIDENCIA')
R_PRV = re.compile(r'\bPREV|\bFIE\b|VGBL|PGBL|ICATU|BRASILPREV|ZURICH|MAPFRE|SUL ?AMERICA|PORTO SEGURO|CAIXA VIDA|BRADESCO VIDA|SEGUR')
R_WM = re.compile(r'WEALTH|\bWM\b|PATRIM|PRIVATE|FAMILY|HEDGING|\bUBS\b|JULIUS|INTRAG|SAFRA|BRADESCO|SANTANDER|ITAU|BTG|BB GEST|BB DTVM|CAIXA|CITI|MORGAN|CREDIT SUISSE|PICTET|LOMBARD|ASSESSORIA|CONSULTORIA|ADVISORY|\bG5\b|BRAINVEST|PRAGMA|TABOACO|JAZZ|VITRA|TURIM|ALOCC|\bTAG\b|ATRIO|MANDATTO|ONE INVEST|AZIMUT|WHG|GOVERNANCE|BELVEDERE|MULTI FAMILY|GESTAO DE BENS|\bBNP|SCOTIA|\bXP\b|\bPF\b')
def extcat(h, hr):
    g, n = dea(gn.get(hr, '')), dea(fnm.get(h, ''))
    if R_PEN.search(g) or R_PEN.search(n): return 'pensao'
    if R_PRV.search(n) or R_PRV.search(g): return 'previdencia'
    if R_WM.search(g): return 'wealth'
    return 'alocadores'
ECAT = {}
def vec(cnpj, ym, gid, r8, depth, seen, mult=1.0):
    out = dict.fromkeys(OUTK, 0.0)
    s = PERd.get((cnpj, ym))
    if (s is None or np.isnan(s).all()) and ym in EST_Q: s = PERd.get((cnpj, BASEQ))
    if s is None or np.isnan(s).all():
        out['nao_ident'] = 1.0; return out
    s = np.nan_to_num(s)
    for k, ix in GI.items(): out[k] = float(s[ix].sum())
    fsh = float(s[FI_].sum())
    if fsh <= 0: return out
    hs = HOLD.get((cnpj, ym))
    if not hs or depth >= 4:
        out['sem_cda'] += fsh; return out
    for h, w, hg, hr in hs:
        if h in seen: out['sem_cda'] += fsh * w; continue
        if (hg and hg == gid) or (hr and hr == r8):
            if (h, ym) in PSET: continue          # contado no próprio cotista
            REC.add((gid, ym, h))
            sub = vec(h, ym, gid, r8, depth + 1, seen | {h}, mult * fsh * w)
            for k in OUTK: out[k] += fsh * w * sub[k]
        else:
            cat = ECAT.get((h, hr))
            if cat is None: cat = ECAT[(h, hr)] = extcat(h, hr)
            out[cat] += fsh * w
            EXTLOG.append((cnpj, ym, h, hr, cat, fsh * w * mult * CUR[0]))
    return out
EXTLOG, CUR, VV, REC = [], [0.0], [], set()
for c, y, g, r, pl in zip(M.CNPJ_FUNDO, M.ym, M.gid, M.r8, M.pl):
    CUR[0] = pl; VV.append(vec(c, y, g, r, 0, {c}))
EXT = pd.DataFrame(EXTLOG, columns=['inv', 'ym', 'holder', 'hr8', 'cat', 'v'])
print('externos por categoria (R$ bi, 2024-12):', (EXT[EXT.ym == '2024-12'].groupby('cat').v.sum() / 1e9).round(1).to_dict())
print((EXT[(EXT.ym == '2024-12') & (EXT.cat == 'alocadores')].groupby('hr8').v.sum().sort_values(ascending=False).head(15) / 1e9).round(2).rename(index=lambda r: str(gn.get(r, r))[:50]).to_string())
EXT.to_pickle(os.path.join(OUT, 'ext_holders.pkl'))
VV = pd.DataFrame(VV, index=M.index)
for k in OUTK: M[k] = M.pl * VV[k]
M['ext'] = M.alocadores + M.wealth
M['alocadores'] = M.alocadores + M.sem_cda
M['pl_el'] = np.where(M.eleg, M.pl, 0.0)
H = M.groupby(['gid', 'ym'])[TYPES + ['nao_ident', 'ext', 'sem_cda']].sum().join(M.groupby(['gid', 'ym']).pl_el.sum().rename('pl')).reset_index()
chk = H[TYPES + ['nao_ident']].sum(axis=1) / H.pl
# o não identificado (master sem Perfil Mensal) é rateado pela composição conhecida da própria gestora; sem nenhuma composição, fica fora
_id = H[TYPES].sum(axis=1)
H[TYPES] = H[TYPES].mul(((_id + H.nao_ident) / _id).where(_id > 0), axis=0)
H['pct_ident'] = _id / (_id + H.nao_ident)
print('fecha com o PL (mediana, p5, p95):', chk.median().round(3), chk.quantile(.05).round(3), chk.quantile(.95).round(3))
agg = H.groupby('ym')[TYPES + ['nao_ident', 'pl', 'sem_cda']].sum()
print('composição agregada (% do PL):'); print((agg[TYPES + ['nao_ident', 'sem_cda']].div(agg.pl, axis=0) * 100).round(1).iloc[::4].to_string())

# ---------------- fluxos trimestrais por tipo
GM['q'] = pd.PeriodIndex(GM.ym, freq='M').asfreq('Q').astype(str)
rq = GM[GM.ym >= '2019-01'].groupby(['gid', 'q']).r.apply(lambda x: np.prod(1 + x.fillna(0)) - 1).rename('rq').reset_index()
H['q'] = pd.PeriodIndex(H.ym, freq='M').asfreq('Q').astype(str)
H = H.sort_values(['gid', 'ym'])
H = H.merge(rq, on=['gid', 'q'], how='left')
H['qa'] = H.groupby('gid').q.shift()
H['cons'] = H.qa == (pd.PeriodIndex(H.q, freq='Q') - 1).astype(str)
for k in TYPES + ['pl']:
    H[k + '_ant'] = H.groupby('gid')[k].shift()
    H.loc[~H.cons, k + '_ant'] = np.nan
    H['f_' + k] = H[k] - H[k + '_ant'] * (1 + H.rq.fillna(0))
H['total'] = H[TYPES].sum(axis=1); H['total_ant'] = H[[k + '_ant' for k in TYPES]].sum(axis=1, min_count=1)
H['f_total'] = H[['f_' + k for k in TYPES]].sum(axis=1, min_count=1)
TT = ['total'] + TYPES
# universo no início do trimestre: gestora no S no primeiro mês do trimestre
qs = {q: str(pd.Period(q, 'Q').asfreq('M', 'start')) for q in H.q.unique()}
H['ym0'] = H.q.map(qs)
A = S[['gid', 'ym', 'ex12_l', 'ex36_l', 'vol36_l', 'beta36_l', 'te36_l', 'idade', 'sh_lb_l', 'n_acoes', 'top10', 'consenso', 'pl_ant', 'nome']].rename(columns={'ym': 'ym0', 'pl_ant': 'size0'})
Q = H.merge(A, on=['gid', 'ym0'], how='inner')
Q = Q[Q.total_ant.notna() & (Q.total_ant > 0)]
for k in TYPES: Q['dep_' + k] = Q[k + '_ant'] / Q.total_ant
ATTR = {'ex12_l': 'Alpha 12 meses', 'ex36_l': 'Alpha 36 meses (ao ano)', 'size0': 'Tamanho (PL em ações)', 'top10': 'Concentração (peso das 10 maiores)',
        'n_acoes': 'Nº de ações na carteira', 'beta36_l': 'Beta 36m', 'vol36_l': 'Volatilidade 36m', 'te36_l': 'Tracking error 36m',
        'idade': 'Idade da gestora', 'sh_lb_l': '% do PL em long biased', 'consenso': 'Peso nas 20 ações mais detidas', 'dep': 'Peso desse tipo no passivo'}
for c in [c for c in ATTR if c != 'dep']:
    Q[c + '_rk'] = Q.groupby('q')[c].rank(pct=True) * 100
for k in TYPES:
    Q['dep_' + k + '_rk'] = Q.groupby('q')['dep_' + k].rank(pct=True) * 100
Q['dep_total_rk'] = np.nan
print('gestora-trimestres:', len(Q), '| gestoras:', Q.gid.nunique(), '| trimestres:', Q.q.nunique())

# ---------------- regimes por trimestre
ib = IX.ibov; cdi = IX.cdi
ust = pd.read_csv(UST); ust.columns = ['d', 'v']; ust['v'] = pd.to_numeric(ust.v, errors='coerce'); ust = ust.dropna()
ust['ym'] = ust.d.str[:7]; ust = ust.groupby('ym').v.last() / 100
qlist = sorted(Q.q.unique())
def mprod(s, a, b): x = s.loc[a:b]; return float(np.prod(1 + x) - 1)
R = []
for q in qlist:
    p = pd.Period(q, 'Q'); m0 = str(p.asfreq('M', 'start')); m1 = str(p.asfreq('M', 'end'))
    m12 = str(pd.Period(m1, 'M') - 11); mprev = str(pd.Period(m0, 'M') - 1); m12p = str(pd.Period(m1, 'M') - 12)
    cdi_aa = lambda ym: (1 + cdi.get(ym, np.nan)) ** 12 - 1
    R.append(dict(q=q, ibov_q=mprod(ib, m0, m1), ibov_12=mprod(ib, m12, m1), cdi=cdi_aa(m1), dcdi_q=cdi_aa(m1) - cdi_aa(mprev), dcdi_12=cdi_aa(m1) - cdi_aa(m12p),
                  ust=ust.get(m1), dust_q=ust.get(m1) - ust.get(mprev), dust_12=ust.get(m1) - ust.get(m12p)))
RQ = pd.DataFrame(R).set_index('q')
ind = Q.groupby('q').apply(lambda x: x.f_total.sum() / x.total_ant.sum())
RQ['ind_flow'] = ind
REG = {'ibov_q': ('Ibovespa no trimestre', lambda r: 'alta' if r.ibov_q > 0 else 'baixa'),
       'ibov_12': ('Ibovespa em 12 meses', lambda r: 'alta' if r.ibov_12 > 0 else 'baixa'),
       'selic': ('Selic no trimestre', lambda r: 'alta' if r.dcdi_q > 0.0025 else 'baixa'),
       'ust': ('Treasury 10 anos no trimestre', lambda r: 'alta' if r.dust_q > 0 else 'baixa'),
       'fluxo': ('Fluxo da indústria no trimestre', lambda r: 'alta' if r.ind_flow > 0 else 'baixa')}
STATE_LBL = {'ibov_q': ('Ibov subiu', 'Ibov caiu'), 'ibov_12': ('Ibov 12m positivo', 'Ibov 12m negativo'), 'selic': ('Selic subindo', 'Selic caindo ou parada'),
             'ust': ('Treasury subindo', 'Treasury caindo'), 'fluxo': ('Indústria captando', 'Indústria resgatando')}
for k, (_, f) in REG.items(): RQ['st_' + k] = RQ.apply(f, axis=1)
Q = Q.join(RQ[['st_' + k for k in REG]], on='q')
out = dict(nomes=NOMES, tipos=TT, regimes={k: v[0] for k, v in REG.items()}, estados=STATE_LBL, attr=ATTR)
out['trimestres'] = RQ.reset_index().round(5).replace({np.nan: None}).to_dict('records')
out['n_estado'] = {k: RQ['st_' + k].value_counts().to_dict() for k in REG}

# ---------------- A. agregado por tipo: série, composição, investe/tira por estado, sensibilidade a CDI/Ibov/Treasury
ser = []
for q, x in Q.groupby('q'):
    r = dict(q=q)
    for k in TT:
        b = x[k + '_ant'].sum(); f = x['f_' + k]
        r[k] = dict(h=round(x[k].sum() / 1e9, 3), f=round(f.sum() / 1e9, 3), fr=round(f.sum() / b, 5) if b > 0 else None,
                    inv=round(f[f > 0].sum() / b, 5) if b > 0 else None, tira=round(f[f < 0].sum() / b, 5) if b > 0 else None,
                    pos=round((f > 0).mean(), 3))
    ser.append(r)
out['serie'] = ser
SQ = pd.DataFrame([{**{'q': s['q']}, **{k: s[k]['fr'] for k in TT}} for s in ser]).set_index('q')
SI = pd.DataFrame([{**{'q': s['q']}, **{k: s[k]['inv'] for k in TT}} for s in ser]).set_index('q')
ST = pd.DataFrame([{**{'q': s['q']}, **{k: s[k]['tira'] for k in TT}} for s in ser]).set_index('q')
est = {}
for rg in REG:
    est[rg] = {}
    for stt in ('alta', 'baixa'):
        qq = RQ.index[RQ['st_' + rg] == stt]
        x = Q[Q.q.isin(qq)]
        def pooled(k):
            b = x[k + '_ant'].sum(); f = x['f_' + k]
            return dict(fr=round(f.sum() / b, 5), inv=round(f[f > 0].sum() / b, 5), tira=round(f[f < 0].sum() / b, 5),
                        f_bi=round(f.sum() / 1e9, 2), inv_bi=round(f[f > 0].sum() / 1e9, 2), tira_bi=round(f[f < 0].sum() / 1e9, 2),
                        pos=round((f[x[k + '_ant'] >= 5e6] > 0).mean(), 3), n=int(len(qq)))
        est[rg][stt] = {k: pooled(k) for k in TT}
out['estados_agg'] = est
DRV = {'ibov_q': 'Ibovespa no trimestre', 'ibov_12': 'Ibovespa 12m', 'cdi': 'CDI (nível)', 'dcdi_12': 'Δ CDI 12m', 'ust': 'Treasury 10a (nível)', 'dust_12': 'Δ Treasury 12m', 'ind_alpha': 'Alpha mediano das gestoras'}
RQ['ind_alpha'] = Q.groupby('q').ex12_l.median()
drv = {}
for k in TT:
    drv[k] = {}
    for dv in DRV:
        x = pd.concat([SQ[k], RQ[dv]], axis=1).dropna(); r = x.iloc[:, 0].corr(x.iloc[:, 1]); n = len(x)
        drv[k][dv] = dict(r=round(r, 3), t=round(r * np.sqrt(n - 2) / np.sqrt(1 - r * r), 2), n=n)
out['drivers'] = drv; out['drivers_nome'] = DRV
# multivariada (CDI, ΔCDI, Ibov 12m, ΔUST 12m)
mv = {}
for k in TT:
    x = pd.concat([SQ[k].rename('y'), RQ[['cdi', 'dcdi_12', 'ibov_12', 'dust_12']]], axis=1).dropna()
    z = (x - x.mean()) / x.std()
    mm = smf.ols('y ~ cdi + dcdi_12 + ibov_12 + dust_12', z).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
    mv[k] = dict(r2=round(mm.rsquared, 3), coef={c: round(mm.params[c], 3) for c in ['cdi', 'dcdi_12', 'ibov_12', 'dust_12']}, t={c: round(mm.tvalues[c], 2) for c in ['cdi', 'dcdi_12', 'ibov_12', 'dust_12']})
out['drivers_mv'] = mv

# ---------------- B. sensibilidade ao alpha 1 ano x 3 anos, por tipo (painel com efeito de trimestre, erro por gestora)
def sens(k, df):
    x = df[(df[k + '_ant'] >= 10e6)].copy() if k != 'total' else df[df.total_ant >= 30e6].copy()
    x = x[x['f_' + k].notna()]
    if len(x) < 80: return None
    x['y'] = x['f_' + k] / x[k + '_ant']; lo, hi = x.y.quantile([.02, .98]); x['y'] = x.y.clip(lo, hi) * 100
    x['a12'] = x.ex12_l_rk / 100 - .5; x['a36'] = x.ex36_l_rk / 100 - .5; x['ls'] = np.log(x.size0)
    res = {}
    for nm, f in {'a12': 'y ~ a12 + ls + C(q)', 'a36': 'y ~ a36 + ls + C(q)', 'ambos': 'y ~ a12 + a36 + ls + C(q)'}.items():
        xx = x.dropna(subset=(['a12', 'a36'] if nm == 'ambos' else [nm]) + ['y', 'ls'])
        xx = xx[np.isfinite(xx.y) & np.isfinite(xx.ls)]
        mm = smf.ols(f, xx).fit(cov_type='cluster', cov_kwds={'groups': xx.gid.astype('category').cat.codes})
        res[nm] = {c: dict(b=round(mm.params[c], 3), t=round(mm.tvalues[c], 2)) for c in ['a12', 'a36', 'ls'] if c in mm.params}
        res[nm]['n'] = int(mm.nobs)
    return res
SENS = {k: {'todos': sens(k, Q)} for k in TT}
for rg in REG:
    for stt in ('alta', 'baixa'):
        for k in TT:
            SENS[k][f'{rg}:{stt}'] = sens(k, Q[Q['st_' + rg] == stt])
out['sens'] = SENS

# ---------------- C. perfil de quem recebe (0 a 100) e quintis de alpha, por tipo e estado
def expo(k, df):
    return df[(df[k + '_ant'] >= 5e6) | (df['f_' + k].abs() >= 5e6)] if k != 'total' else df
def perfil(k, df):
    x = expo(k, df).dropna(subset=['f_' + k]).copy(); x['win'] = x['f_' + k] > 0
    if x.win.sum() < 15 or (~x.win).sum() < 15: return None
    res = dict(n=int(len(x)), pct_win=round(x.win.mean(), 3), tab={})
    for a in ATTR:
        c = ('dep_' + k + '_rk') if a == 'dep' else a + '_rk'
        if a == 'dep' and k == 'total': continue
        xx = x.dropna(subset=[c])
        if len(xx) < 30: continue
        dq = xx.groupby('q').apply(lambda z: z[z.win][c].mean() - z[~z.win][c].mean()).dropna()
        t = dq.mean() / (dq.std() / np.sqrt(len(dq))) if len(dq) > 2 and dq.std() > 0 else None
        res['tab'][a] = dict(w=round(xx[xx.win][c].mean(), 1), l=round(xx[~xx.win][c].mean(), 1), t=None if t is None else round(t, 2),
                             same=int((np.sign(dq) == np.sign(dq.mean())).sum()), nq=int(len(dq)))
    return res
def quint(k, df):
    x = expo(k, df).dropna(subset=['f_' + k, 'ex12_l_rk']).copy()
    x = x[x[k + '_ant'] > 0]; x['y'] = x['f_' + k] / x[k + '_ant']
    out_ = {}
    for a in ('ex12_l_rk', 'ex36_l_rk'):
        xx = x.dropna(subset=[a]).copy(); xx['qq'] = (xx[a] / 20).clip(0, 4.999).astype(int) + 1
        out_[a[:4]] = [dict(q=int(qq), med=round(z.y.median(), 4), pos=round((z.y > 0).mean(), 3), n=int(len(z))) for qq, z in xx.groupby('qq')]
    return out_
def tops(k, df):
    x = df.dropna(subset=['f_' + k]).groupby('gid').agg(nome=('nome', 'last'), f=('f_' + k, 'sum'), a12=('ex12_l', 'mean'), nq=('q', 'nunique'), h=(k + '_ant', 'mean'))
    x = x[x.f.abs() > 0]
    fm = lambda z: [dict(nome=r.nome, f_mi=round(r.f / 1e6), a12=None if pd.isna(r.a12) else round(r.a12, 3), nq=int(r.nq), h_mi=None if pd.isna(r.h) else round(r.h / 1e6)) for r in z.itertuples()]
    return dict(rec=fm(x.sort_values('f', ascending=False).head(10)), saq=fm(x.sort_values('f').head(10)))
PERF, QUI, TOP = {}, {}, {}
for k in TT:
    PERF[k] = {'todos': perfil(k, Q)}; QUI[k] = {'todos': quint(k, Q)}; TOP[k] = {'todos': tops(k, Q)}
    for rg in REG:
        for stt in ('alta', 'baixa'):
            sub = Q[Q['st_' + rg] == stt]
            PERF[k][f'{rg}:{stt}'] = perfil(k, sub); QUI[k][f'{rg}:{stt}'] = quint(k, sub); TOP[k][f'{rg}:{stt}'] = tops(k, sub)
out['perfil'] = PERF; out['quintis'] = QUI; out['tops'] = TOP
# quem captou e quem sacou, trimestre a trimestre, por tipo
TQ = {}
for k in TT:
    TQ[k] = {}
    for q, x in Q.groupby('q'):
        x = x[x['f_' + k].notna() & ((x[k + '_ant'].fillna(0) >= 1e6) | (x['f_' + k].abs() >= 1e6))]
        if x.empty: continue
        def lst(z):
            return [dict(nome=r.nome, f_mi=round(getattr(r, 'f_' + k) / 1e6, 1), pct=None if not getattr(r, k + '_ant') else round(getattr(r, 'f_' + k) / getattr(r, k + '_ant'), 3),
                         a12=None if pd.isna(r.ex12_l) else round(r.ex12_l, 3), h_mi=round((getattr(r, k + '_ant') or 0) / 1e6)) for r in z.itertuples()]
        f = x['f_' + k]
        TQ[k][q] = dict(rec=lst(x[f > 0].sort_values('f_' + k, ascending=False).head(8)), saq=lst(x[f < 0].sort_values('f_' + k).head(8)),
                        n_rec=int((f > 0).sum()), n_saq=int((f < 0).sum()), rec_bi=round(f[f > 0].sum() / 1e9, 3), saq_bi=round(f[f < 0].sum() / 1e9, 3),
                        top3_rec=round(f[f > 0].nlargest(3).sum() / f[f > 0].sum(), 3) if (f > 0).any() else None)
out['tri'] = TQ
out['estimados'] = [str(pd.Period(m, 'M').asfreq('Q')) for m in EST_Q]

# ---------------- pessoa física: número de cotistas, posição média, cotistas novos x quem já estava, tamanho do cheque
NPF = pd.read_pickle(os.path.join(OUT, 'cotistas_pf.pkl')).sort_values(['CNPJ_FUNDO', 'ym'])
# limpeza: valor isolado > 5x os dois vizinhos (ou zero entre vizinhos > 1000) é erro de preenchimento -> média dos vizinhos
for c in ['n_private', 'n_varejo', 'n_plataformas', 'n_estrangeiro']:
    g = NPF.groupby('CNPJ_FUNDO')[c]; a, b = g.shift(1), g.shift(-1); v = NPF[c]
    nb = pd.concat([a, b], axis=1)
    spike = (v > 500) & (v > 5 * nb.max(axis=1).fillna(0))
    hole = (v == 0) & (nb.min(axis=1) > 1000)
    block = (v > 1000) & (v > 20 * g.transform('median'))   # bloco de trimestres com contagem errada (ex.: 19 -> 6.315 -> 100)
    bad = spike | hole | block
    NPF.loc[bad & ~block, c] = nb[bad & ~block].mean(axis=1).round()
    NPF[c] = NPF[c].astype(float); NPF.loc[block, c] = g.transform('median')[block].round()
    print('contagem corrigida', c, int(bad.sum()))
PFK = ['private', 'varejo', 'plataformas', 'estrangeiro']
cnt = M[['CNPJ_FUNDO', 'ym', 'gid']].merge(NPF, on=['CNPJ_FUNDO', 'ym'], how='left')
rec = pd.DataFrame(list(REC), columns=['gid', 'ym', 'CNPJ_FUNDO']).merge(NPF, on=['CNPJ_FUNDO', 'ym'], how='left')
NC = pd.concat([cnt, rec]).groupby(['gid', 'ym'])[['n_' + k for k in PFK]].sum().reset_index()
NC['q'] = pd.PeriodIndex(NC.ym, freq='M').asfreq('Q').astype(str)
Q = Q.merge(NC[['gid', 'q'] + ['n_' + k for k in PFK]], on=['gid', 'q'], how='left').sort_values(['gid', 'q'])
BANDS = [('pulverizado', 0, 50e3), ('medio', 50e3, 1e6), ('grande', 1e6, np.inf), ('existentes', 0, 0), ('inconsistente', 0, 0)]
pf = {}
for k in PFK:
    Q['n_' + k + '_ant'] = Q.groupby('gid')['n_' + k].shift(); Q.loc[Q.q != Q.groupby('gid').q.shift().map(lambda z: str(pd.Period(z, 'Q') + 1) if isinstance(z, str) else ''), 'n_' + k + '_ant'] = np.nan
    a0 = Q[k + '_ant'] / Q['n_' + k + '_ant'].replace(0, np.nan)
    dN = Q['n_' + k] - Q['n_' + k + '_ant']
    # contagem consistente: sem reclassificação de cotistas (número muda muito sem o dinheiro mudar);
    # relação nova (menos de 30 cotistas antes): o cheque é a posição do fim dividida pelos cotistas novos
    a1 = Q[k] / Q['n_' + k].replace(0, np.nan)
    rat = a1 / a0
    novo = Q['n_' + k + '_ant'].fillna(0) < 30
    # reclassificação = o número de cotistas muda mais de 3x e o dinheiro não acompanha (fica entre metade e o dobro)
    cr = Q['n_' + k] / Q['n_' + k + '_ant'].replace(0, np.nan)
    mr = Q[k] / (Q[k + '_ant'] * (1 + Q.rq.fillna(0))).replace(0, np.nan)
    recl = ((cr > 3) | (cr < 1 / 3)) & mr.between(0.5, 2)
    okc = (novo & (Q['n_' + k].fillna(0) > 0)) | (~novo & cr.notna() & ~recl)
    dN = dN.where(~novo, Q['n_' + k] - Q['n_' + k + '_ant'].fillna(0))
    dN = dN.where(okc)
    Q['okc_' + k] = okc
    ext = (dN * a0 * (1 + Q.rq.fillna(0)))
    ext = ext.where(~novo, Q['f_' + k])                      # relação nova: todo o dinheiro é de cotista novo
    Q['ext_' + k] = ext.where(okc)
    Q['int_' + k] = (Q['f_' + k] - Q['ext_' + k]).where(okc)
    Q['dN_' + k] = dN
    tk = Q['f_' + k] / dN
    # cheque da entrada: R$ por cotista novo líquido; entrada sem cotista novo = grande cheque (quem já estava aumentou)
    band = np.where(Q['f_' + k] <= 0, None, np.where(dN.isna(), 'inconsistente', np.where(dN <= 0, 'existentes', np.where(tk < 50e3, 'pulverizado', np.where(tk < 1e6, 'medio', 'grande')))))
    Q['band_' + k] = band
    rows = []
    for q, x in Q.groupby('q'):
        x2 = x[x['n_' + k].notna()]
        f = x2['f_' + k]
        r = dict(q=q, n=int(x2['n_' + k].sum()), h=round(x2[k].sum() / 1e9, 3), f=round(f.sum() / 1e9, 3),
                 ext=round(x2['ext_' + k].sum() / 1e9, 3), int=round(x2['int_' + k].sum() / 1e9, 3),
                 dN=int(x2['dN_' + k].sum()) if x2['dN_' + k].notna().any() else None)
        x3 = x2[x2['okc_' + k].fillna(False).astype(bool)]   # só contagem consistente
        r['pos_media_mil'] = round(x3[k].sum() / max(1, x3['n_' + k].sum()) / 1e3, 1)
        for b, _, _ in BANDS: r[b] = round(x2.loc[x2['band_' + k] == b, 'f_' + k].sum() / 1e9, 3)
        rows.append(r)
    st = {}
    for rg in REG:
        st[rg] = {}
        for stt in ('alta', 'baixa'):
            x = Q[(Q['st_' + rg] == stt) & Q['n_' + k].notna()]
            fpos = x['f_' + k].clip(lower=0).sum()
            st[rg][stt] = {b: round(x.loc[x['band_' + k] == b, 'f_' + k].sum() / fpos, 3) if fpos > 0 else None for b, _, _ in BANDS} | dict(
                ext_bi=round(x['ext_' + k].sum() / 1e9, 2), int_bi=round(x['int_' + k].sum() / 1e9, 2), f_bi=round(x['f_' + k].sum() / 1e9, 2), entrada_bi=round(fpos / 1e9, 2))
    x = Q[Q['n_' + k].notna()]; fpos = x['f_' + k].clip(lower=0).sum()
    st['todos'] = {b: round(x.loc[x['band_' + k] == b, 'f_' + k].sum() / fpos, 3) for b, _, _ in BANDS} | dict(
        ext_bi=round(x['ext_' + k].sum() / 1e9, 2), int_bi=round(x['int_' + k].sum() / 1e9, 2), f_bi=round(x['f_' + k].sum() / 1e9, 2), entrada_bi=round(fpos / 1e9, 2))
    # número de cotistas encadeado: variação só entre as mesmas gestoras de um trimestre para o outro (entrada e saída do universo não mexem)
    pv = Q.pivot_table(index='gid', columns='q', values='n_' + k, aggfunc='sum')
    qs = sorted(pv.columns); idx = {qs[0]: float(pv[qs[0]].sum())}
    for a_, b_ in zip(qs, qs[1:]):
        both = pv[a_].notna() & pv[b_].notna() & (pv[a_] > 0)
        idx[b_] = idx[a_] * (pv.loc[both, b_].sum() / pv.loc[both, a_].sum()) if both.any() else idx[a_]
    # posição média encadeada: mesma ideia, só gestoras presentes e com contagem consistente nos dois trimestres
    ok = Q[Q['okc_' + k].fillna(False).astype(bool) | Q['n_' + k + '_ant'].isna()]
    ph = ok.pivot_table(index='gid', columns='q', values=k, aggfunc='sum'); pn = ok.pivot_table(index='gid', columns='q', values='n_' + k, aggfunc='sum')
    q0 = qs[0]; a0_ = ph[q0].sum() / max(1, pn[q0].sum()); ida = {q0: a0_}
    for a_, b_ in zip(qs, qs[1:]):
        if a_ not in ph or b_ not in ph: ida[b_] = ida[a_]; continue
        both = ph[a_].notna() & ph[b_].notna() & (pn[a_] > 0) & (pn[b_] > 0)
        if both.any():
            r_ = (ph.loc[both, b_].sum() / pn.loc[both, b_].sum()) / (ph.loc[both, a_].sum() / pn.loc[both, a_].sum())
            ida[b_] = ida[a_] * r_
        else: ida[b_] = ida[a_]
    for r in rows:
        r['n_enc'] = round(idx.get(r['q'], np.nan)); r['pos_enc_mil'] = round(ida.get(r['q'], np.nan) / 1e3, 1)
    pf[k] = dict(serie=rows, estados=st)
    # tabela trimestral: acrescenta cotistas novos e R$ por cotista novo
    for q, d in out['tri'].get(k, {}).items():
        xq = Q[Q.q == q].set_index('nome')
        for lst in (d['rec'], d['saq']):
            for r in lst:
                if r['nome'] in xq.index:
                    z = xq.loc[r['nome']]; z = z.iloc[0] if isinstance(z, pd.DataFrame) else z
                    dn = z['dN_' + k]; r['dN'] = None if pd.isna(dn) else int(dn)
                    r['tk_mil'] = None if (pd.isna(dn) or dn <= 0 or r['f_mi'] <= 0) else round(r['f_mi'] * 1e3 / dn, 1)
                    r['band'] = z['band_' + k] if isinstance(z['band_' + k], str) else None
out['pf'] = pf
print('\npessoa física: entradas por tamanho do cheque (todos os trimestres) e cotistas novos x quem já estava (R$ bi):')
print(pd.DataFrame({k: pf[k]['estados']['todos'] for k in PFK}).to_string())
print(pd.DataFrame({k: {s2: pf[k]['estados']['ibov_12'][s2] for s2 in ('alta', 'baixa')} for k in PFK}).to_string())
print(pd.DataFrame([{**{'q': r['q']}, **{c: r[c] for c in ('n', 'pos_media_mil', 'f', 'ext', 'int')}} for r in pf['varejo']['serie']]).iloc[::3].to_string())
print(pd.DataFrame([{**{'q': r['q']}, **{c: r[c] for c in ('n', 'pos_media_mil', 'f', 'ext', 'int')}} for r in pf['private']['serie']]).iloc[::3].to_string())
print(pd.DataFrame([{**{'q': r['q']}, **{c: r[c] for c in ('n', 'pos_media_mil', 'f', 'ext', 'int')}} for r in pf['plataformas']['serie']]).iloc[::3].to_string())
def _limpa(o):   # JSON não aceita NaN/inf
    if isinstance(o, dict): return {k: _limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_limpa(v) for v in o]
    if hasattr(o, 'item') and not isinstance(o, str): o = o.item()
    if isinstance(o, float) and not np.isfinite(o): return None
    return o
json.dump(_limpa(out), open(SAIDA, 'w'), ensure_ascii=False, separators=(',', ':'), allow_nan=False, default=str)
Q.to_pickle(os.path.join(OUT, 'passivo_trimestre.pkl'))

# ---------------- resumo no terminal
print('\nfluxo médio por trimestre (% da posição do tipo) e investe/tira, por estado:')
for rg in REG:
    print('==', REG[rg][0], out['n_estado'][rg])
    print(pd.DataFrame({f'{stt}:{m}': {NOMES[k]: est[rg][stt][k][m] * 100 for k in TT} for stt in ('alta', 'baixa') for m in ('fr', 'inv', 'tira')}).round(2).to_string())
print('\ncorrelação do fluxo trimestral de cada tipo com:')
print(pd.DataFrame({DRV[dv]: {NOMES[k]: f"{drv[k][dv]['r']:+.2f} ({drv[k][dv]['t']:+.1f})" for k in TT} for dv in DRV}).to_string())
print('\nmultivariada padronizada (coef, t):')
print(pd.DataFrame({c: {NOMES[k]: f"{mv[k]['coef'][c]:+.2f} ({mv[k]['t'][c]:+.1f})" for k in TT} for c in ['cdi', 'dcdi_12', 'ibov_12', 'dust_12']} | {'R2': {NOMES[k]: mv[k]['r2'] for k in TT}}).to_string())
print('\nsensibilidade ao alpha (p.p. de fluxo no trimestre do pior ao melhor rank), modelo com os dois:')
print(pd.DataFrame({NOMES[k]: {'a12': SENS[k]['todos']['ambos']['a12']['b'], 't12': SENS[k]['todos']['ambos']['a12']['t'], 'a36': SENS[k]['todos']['ambos']['a36']['b'], 't36': SENS[k]['todos']['ambos']['a36']['t'], 'n': SENS[k]['todos']['ambos']['n']} for k in TT if SENS[k]['todos']}).T.to_string())
