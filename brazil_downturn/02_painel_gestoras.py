"""Brazil Downturn, passo 2: fundo -> gestora na data -> painel mensal por gestora.

Fundos elegíveis para medir fluxo: classe Ações (ou long biased), sem FIC (flag ou nome), sem exclusivo, sem previdência e sem
indexado. Os masters recebem o fluxo líquido dos feeders (FIC), então somar só os não-FIC evita dupla contagem.
Gestora na data: cad_fi_hist_gestor (reserva: registro RCVM 175 a partir de out/2023, depois cad_fi), agrupada pela raiz do CNPJ
e pelos CNPJs irmãos (mb) do carteiras.json do Navegando Brasil.
Universo de gestoras: as que estiveram entre as 100 maiores gestoras ativas de ações em algum mês (regra point-in-time do Navegando Brasil);
cada gestora-mês carrega a flag top100_prev (estava no top 100 no mês anterior) para análises sem viés.
Também sai a série de índices (Ibovespa e SMLL) a partir dos fundos indexados mais antigos e líquidos, e o CDI do BCB.
Uso: python3 02_painel_gestoras.py <raw> <painel_fundos.pkl> <carteiras.json> <cdi_m.json> <saida_dir>
"""
import sys, os, re, json, zipfile, unicodedata
import pandas as pd, numpy as np

RAW, PF, CJ, CDI, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if isinstance(c, str) and len(c) == 14 else c
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]

# ---------------- cadastro
z = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
rd = lambda n: pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str)
hf, hx, hn, hc = rd('cad_fi_hist_fic.csv'), rd('cad_fi_hist_exclusivo.csv'), rd('cad_fi_hist_denom_social.csv'), rd('cad_fi_hist_classe.csv')
cad = pd.read_csv(os.path.join(RAW, 'cad_fi.csv'), sep=';', encoding='latin1', dtype=str)
zr = zipfile.ZipFile(os.path.join(RAW, 'registro_fundo_classe.zip'))
rc = pd.read_csv(zr.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str)
rc['CNPJ_FUNDO'] = rc.CNPJ_Classe.str.zfill(14).map(fmt)

P = pd.read_pickle(PF)
F = pd.DataFrame({'CNPJ_FUNDO': P.CNPJ_FUNDO.unique()})
nm = pd.concat([hn.sort_values('DT_INI_DENOM_SOCIAL' if 'DT_INI_DENOM_SOCIAL' in hn else 'DT_REG')[['CNPJ_FUNDO', 'DENOM_SOCIAL']],
                cad[['CNPJ_FUNDO', 'DENOM_SOCIAL']], rc[['CNPJ_FUNDO', 'Denominacao_Social']].rename(columns={'Denominacao_Social': 'DENOM_SOCIAL'})])
allnames = nm.groupby('CNPJ_FUNDO').DENOM_SOCIAL.apply(lambda s: ' | '.join(sorted(set(map(deacc, s.dropna())))))
lastname = nm.dropna().drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').DENOM_SOCIAL
F['nome'] = F.CNPJ_FUNDO.map(lastname).fillna('')
F['nomes'] = F.CNPJ_FUNDO.map(allnames).fillna('')
fic = set(hf[hf.FUNDO_COTAS == 'S'].CNPJ_FUNDO) | set(cad[cad.FUNDO_COTAS == 'S'].CNPJ_FUNDO)
exc = set(hx[hx.FUNDO_EXCLUSIVO == 'S'].CNPJ_FUNDO) | set(cad[cad.FUNDO_EXCLUSIVO == 'S'].CNPJ_FUNDO) | \
      set(rc[rc.Exclusivo.fillna('').str.upper().str.startswith('S')].CNPJ_FUNDO)
IDX = re.compile(r'IBOVESPA|\bIBOV\b|IBRX|\bIBX\b|INDICE|INDEX|INDEXAD|PASSIV|\bETF\b|\bSMLL\b|\bIDIV\b|\bMSCI\b|S&P|\bSP ?500\b|NASDAQ|\bPIBB\b')
ACT = re.compile(r'ATIV[OA]|ACTIVE|ALPHA|PLUS')
FICN = re.compile(r'\bFIC\b|\bFICFI|\bFIC-|COTAS|\bFOF\b|FUNDO DE FUNDOS')
PREV = re.compile(r'PREV|\bFIFE\b|\bFIE\b|VGBL|PGBL')
LB = re.compile(r'LONG ?BIAS|\bL\.?B\.?\b')
F['fic'] = F.CNPJ_FUNDO.isin(fic) | F.nomes.str.contains(FICN)
F['exclusivo'] = F.CNPJ_FUNDO.isin(exc)
F['prev'] = F.nomes.str.contains(PREV)
F['indexado'] = F.nomes.str.contains(IDX) & ~F.nomes.str.contains(ACT)
anb = rc.drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').Classificacao_Anbima
anb = anb.combine_first(cad.drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').CLASSE_ANBIMA)
F['anbima'] = F.CNPJ_FUNDO.map(anb).fillna('')
cls = pd.concat([hc[['CNPJ_FUNDO', 'CLASSE']], cad[['CNPJ_FUNDO', 'CLASSE']]]).dropna().drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').CLASSE
F['classe'] = F.CNPJ_FUNDO.map(cls).fillna('')
F['long_biased'] = F.nomes.str.contains(LB) | F.anbima.str.contains('L/S - Direcional') | F.classe.eq('Multimercado')
F['small'] = F.nomes.str.contains(r'SMALL|MICRO|\bSMID\b|MID ?CAP') | F.anbima.str.contains('Small')
F['divid'] = F.nomes.str.contains(r'DIVIDEND|RENDA') | F.anbima.str.contains('Dividend')
F['exterior'] = F.nomes.str.contains(r'EXTERIOR|GLOBAL|\bIE\b|OFFSHORE|INTERNACIONAL|WORLD|USA|AMERICA') | F.anbima.str.contains('Exterior')
F['eleg'] = ~(F.fic | F.exclusivo | F.prev | F.indexado)
print(F[['fic', 'exclusivo', 'prev', 'indexado', 'eleg', 'long_biased', 'small', 'divid', 'exterior']].sum().to_string(), flush=True)

# ---------------- gestor na data (vetorizado por intervalos)
h = rd('cad_fi_hist_gestor.csv')
h = h[h.PF_PJ_GESTOR == 'PJ'][['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'GESTOR', 'DT_INI_GESTOR', 'DT_FIM_GESTOR']].copy()
h['ini'] = pd.to_datetime(h.DT_INI_GESTOR, errors='coerce'); h['fim'] = pd.to_datetime(h.DT_FIM_GESTOR, errors='coerce').fillna(pd.Timestamp('2100-01-01'))
rf = pd.read_csv(zr.open('registro_fundo.csv'), sep=';', encoding='latin1', dtype=str)
rf['g'] = rf.CPF_CNPJ_Gestor.fillna('').str.zfill(14).map(fmt)
rcx = rc.merge(rf[['ID_Registro_Fundo', 'g']], on='ID_Registro_Fundo')
REG = pd.concat([rcx[['CNPJ_FUNDO', 'g']], rf.assign(CNPJ_FUNDO=rf.CNPJ_Fundo.str.zfill(14).map(fmt))[['CNPJ_FUNDO', 'g']]]).drop_duplicates('CNPJ_FUNDO').set_index('CNPJ_FUNDO').g
CADG = cad[cad.PF_PJ_GESTOR == 'PJ'].drop_duplicates('CNPJ_FUNDO', keep='last').set_index('CNPJ_FUNDO').CPF_CNPJ_GESTOR

P = P.merge(F[['CNPJ_FUNDO', 'indexado', 'prev', 'long_biased', 'small', 'divid', 'exterior']], on='CNPJ_FUNDO')
P['d'] = pd.to_datetime(P.ym + '-15')

# FIC e exclusivo NA DATA (um fundo que virou feeder depois de anos como master conta como master até a troca)
def on_date(tab, flag_col, ini, fim, val='S'):
    t = tab[['CNPJ_FUNDO', flag_col, ini, fim]].copy()
    t['a'] = pd.to_datetime(t[ini], errors='coerce').fillna(pd.Timestamp('1900-01-01'))
    t['b'] = pd.to_datetime(t[fim], errors='coerce').fillna(pd.Timestamp('2100-01-01'))
    x = P[['CNPJ_FUNDO', 'ym', 'd']].merge(t, on='CNPJ_FUNDO')
    x = x[(x.d >= x.a) & (x.d < x.b)].sort_values('a').drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
    has = set(t.CNPJ_FUNDO)
    s = pd.Series((x[flag_col] == val).values, index=pd.MultiIndex.from_frame(x[['CNPJ_FUNDO', 'ym']]))
    return s, has
key = pd.MultiIndex.from_frame(P[['CNPJ_FUNDO', 'ym']])
s_fic, has_fic = on_date(hf, 'FUNDO_COTAS', 'DT_INI_ST_COTAS', 'DT_FIM_ST_COTAS')
s_exc, has_exc = on_date(hx, 'FUNDO_EXCLUSIVO', 'DT_INI_ST_EXCLUSIVO', 'DT_FIM_ST_EXCLUSIVO')
hn2 = hn.copy(); hn2['fn'] = hn2.DENOM_SOCIAL.map(deacc).str.contains(FICN).map({True: 'S', False: 'N'})
s_nm, has_nm = on_date(hn2, 'fn', 'DT_INI_DENOM_SOCIAL', 'DT_FIM_DENOM_SOCIAL')
fic_static = F.set_index('CNPJ_FUNDO').fic; exc_static = F.set_index('CNPJ_FUNDO').exclusivo
P['fic'] = np.where(P.CNPJ_FUNDO.isin(has_fic), s_fic.reindex(key).fillna(False).values, P.CNPJ_FUNDO.map(fic_static).values)
P['fic'] = P.fic.astype(bool) | np.where(P.CNPJ_FUNDO.isin(has_nm), s_nm.reindex(key).fillna(False).values, False).astype(bool)
P['exclusivo'] = np.where(P.CNPJ_FUNDO.isin(has_exc), s_exc.reindex(key).fillna(False).values, P.CNPJ_FUNDO.map(exc_static).values).astype(bool)
P['eleg'] = ~(P.fic | P.exclusivo | P.prev | P.indexado)
print('fundo-mês elegível:', round(P.eleg.mean(), 3), '| fic na data:', round(P.fic.mean(), 3), '| exclusivo na data:', round(P.exclusivo.mean(), 3), flush=True)
m = P[['CNPJ_FUNDO', 'ym', 'd']].merge(h[['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'ini', 'fim']], on='CNPJ_FUNDO', how='left')
m = m[(m.d >= m.ini) & (m.d <= m.fim)].sort_values('ini').drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
P = P.merge(m[['CNPJ_FUNDO', 'ym', 'CPF_CNPJ_GESTOR']], on=['CNPJ_FUNDO', 'ym'], how='left')
late = P.CPF_CNPJ_GESTOR.isna() & (P.ym >= '2023-10')
P.loc[late, 'CPF_CNPJ_GESTOR'] = P.loc[late, 'CNPJ_FUNDO'].map(REG)
for src in (CADG, REG):
    na = P.CPF_CNPJ_GESTOR.isna(); P.loc[na, 'CPF_CNPJ_GESTOR'] = P.loc[na, 'CNPJ_FUNDO'].map(src)
P['r8'] = P.CPF_CNPJ_GESTOR.map(root8)
print('fundo-mês sem gestor:', round(P.CPF_CNPJ_GESTOR.isna().mean(), 4), flush=True)

# ---------------- gestoras do Navegando (regra)
d = json.load(open(CJ)); M = d['meses']; G = [g for g in d['gestoras'] if g['id'] != '00000000']
r2g, gname, top = {}, {}, set()
for g in G:
    roots = {g['id']} | ({root8(x[1]) for x in g['mb']} if not g.get('rb') else set())
    for r in roots: r2g.setdefault(r, g['id'])
    gname[g['id']] = g['n']
    for a, b in g.get('tp', []):
        for i in range(a, b + 1): top.add((g['id'], M[i]))
P['gid'] = P.r8.map(r2g)

# ---------------- retornos e fluxos por fundo
P = P.sort_values(['CNPJ_FUNDO', 'ym'])
P['pl_ant'] = P.groupby('CNPJ_FUNDO').pl.shift()
P['ym_ant'] = P.groupby('CNPJ_FUNDO').ym.shift()
P['r'] = P.groupby('CNPJ_FUNDO').q.pct_change()
consec = (pd.PeriodIndex(P.ym, freq='M') - pd.PeriodIndex(P.ym_ant.fillna(P.ym), freq='M')).map(lambda x: getattr(x, 'n', 0)) == 1
P.loc[~consec, ['r', 'pl_ant']] = np.nan
P.loc[(P.r < -0.6) | (P.r > 1.0), 'r'] = np.nan
P['flow'] = P.cap.fillna(0) - P.res.fillna(0)
# fluxo implícito (ΔPL - retorno), para conferência e para meses sem captação/resgate reportados
P['flow_impl'] = P.pl - P.pl_ant * (1 + P.r)
P.to_pickle(os.path.join(OUT, 'fundo_mes.pkl'))
F.to_csv(os.path.join(OUT, 'fundos_meta.csv'), index=False)

# ---------------- índices: fundos indexados de maior PL médio com série longa
def index_series(pat):
    c = F[F.indexado & F.nomes.str.contains(pat) & ~F.fic & ~F.prev].CNPJ_FUNDO
    x = P[P.CNPJ_FUNDO.isin(c) & P.r.notna()]
    piv = x.pivot(index='ym', columns='CNPJ_FUNDO', values='r')
    w = x.pivot(index='ym', columns='CNPJ_FUNDO', values='pl_ant')
    piv = piv.where(w > 50e6)
    # mediana entre os fundos indexados vivos no mês (robusta a erros de cota)
    return piv.median(axis=1), piv.notna().sum(axis=1)
ib, nib = index_series(r'IBOVESPA|\bIBOV\b')
sm, nsm = index_series(r'SMALL|SMLL')
cdi = pd.DataFrame(json.load(open(CDI)))
cdi['ym'] = pd.to_datetime(cdi.data, dayfirst=True).dt.strftime('%Y-%m'); cdi = cdi.set_index('ym').valor.astype(float) / 100
IX = pd.DataFrame({'ibov': ib, 'n_ibov': nib, 'smll': sm, 'n_smll': nsm}).join(cdi.rename('cdi'), how='outer').sort_index()
IX.to_csv(os.path.join(OUT, 'indices.csv'))
print(IX.loc['2005-01':].describe().round(4).to_string(), flush=True)

# ---------------- painel gestora-mês (só fundos elegíveis)
# ---------------- fluxo híbrido por fundo-mês
# continua elegível (t-1 e t): captação - resgate reportados.
# fundo novo (primeira linha no Informe): entra o PL, líquido das saídas por mudança de status da mesma gestora em t-1..t+1
#   (migração de master: o antigo vira FIC e o novo nasce com a carteira; isso não é dinheiro novo).
# mudança de status (FIC <-> master, troca de gestor, exclusivo): não é fluxo.
P = P.sort_values(['CNPJ_FUNDO', 'ym'])
P['first'] = ~P.CNPJ_FUNDO.duplicated()
cons = P.pl_ant.notna() | (P.ym_ant.notna() & (P.ym_ant.map(lambda y: str(pd.Period(y, 'M') + 1) if isinstance(y, str) else '') == P.ym))
P['eleg_ant'] = P.groupby('CNPJ_FUNDO').eleg.shift().astype('boolean').fillna(False).astype(bool) & cons
P['gid_ant'] = P.groupby('CNPJ_FUNDO').gid.shift()
P['cont'] = P.eleg & P.eleg_ant & (P.gid == P.gid_ant)
P['new_in'] = np.where(P.eleg & P['first'], P.pl.fillna(0), 0.0)
# saída por status: era elegível na gestora g em t-1 e em t não é (ou mudou de gestora)
P['st_out'] = np.where(P.eleg_ant & (~P.eleg | (P.gid != P.gid_ant)), (P.pl_ant * (1 + P.r.fillna(0))).fillna(0), 0.0)
P['idade_f'] = P.groupby('CNPJ_FUNDO').cumcount()
young = P.cont & (P.idade_f <= 6) & (P.flow > 0)
P['young_in'] = np.where(young, P.flow, 0.0)            # entradas de fundo recém-criado: podem ser a carteira do master antigo
P['flow_h'] = np.where(P.cont & ~young, P.flow, 0.0)
P['new_in'] = P.new_in + P.young_in
ev = P.groupby(['gid_ant', 'ym']).st_out.sum().rename('so').reset_index().rename(columns={'gid_ant': 'gid'})
ni = P.groupby(['gid', 'ym']).new_in.sum().rename('ni').reset_index()
evm = ni.merge(ev, on=['gid', 'ym'], how='outer').fillna(0).sort_values(['gid', 'ym'])
evm['per'] = pd.PeriodIndex(evm.ym, freq='M')
so = evm.set_index(['gid', 'per']).so
def win(g, p):
    return sum(so.get((g, p + k), 0.0) for k in (-1, 0, 1))
evm['so_win'] = [win(g, p) for g, p in zip(evm.gid, evm.per)]
evm['new_net'] = (evm.ni - evm.so_win).clip(lower=0)
# não reutiliza a mesma saída em dois meses: aloca a entrada líquida proporcionalmente
P.to_pickle(os.path.join(OUT, 'fundo_mes.pkl'))
E = P[P.eleg]
def agg(x):
    ok = x.r.notna() & x.pl_ant.gt(0)
    w = x.pl_ant.where(ok)
    return pd.Series({'pl': x.pl.sum(), 'pl_ant': x.pl_ant.sum(), 'flow': x.flow.sum(), 'flow_impl': x.flow_impl.sum(), 'flow_h': x.flow_h.sum(),
                      'cap': x.cap.sum(), 'res': x.res.sum(), 'r': (x.r * w).sum() / w.sum() if w.sum() > 0 else np.nan,
                      'nf': x.CNPJ_FUNDO.nunique(), 'cot': x.cot.sum(),
                      'pl_lb': x.pl[x.long_biased].sum(), 'pl_small': x.pl[x.small].sum(), 'pl_div': x.pl[x.divid].sum(), 'pl_ext': x.pl[x.exterior].sum()})
GM = E[E.gid.notna()].groupby(['gid', 'ym']).apply(agg).reset_index()
# grade mensal completa por gestora (mês sem fundo elegível = PL zero, para capturar a saída total)
allm = [str(p) for p in pd.period_range(P.ym.min(), P.ym.max(), freq='M')]
grid = []
for g, x in GM.groupby('gid'):
    a, b = allm.index(x.ym.min()), min(allm.index(x.ym.max()) + 1, len(allm) - 1)
    grid += [(g, m) for m in allm[a:b + 1]]
GM = pd.DataFrame(grid, columns=['gid', 'ym']).merge(GM, on=['gid', 'ym'], how='left')
GM[['pl', 'flow', 'flow_h', 'cap', 'res', 'nf', 'cot', 'pl_lb', 'pl_small', 'pl_div', 'pl_ext']] = GM[['pl', 'flow', 'flow_h', 'cap', 'res', 'nf', 'cot', 'pl_lb', 'pl_small', 'pl_div', 'pl_ext']].fillna(0)
GM['flow_rep'] = GM.flow                       # captação - resgate de todos os fundos elegíveis (conferência)
GM['pl_ant'] = GM.groupby('gid').pl.shift()
GM['flow_impl'] = GM.pl - GM.pl_ant * (1 + GM.r.fillna(0))   # ΔPL da casa - retorno (conferência)
GM = GM.merge(evm[['gid', 'ym', 'ni', 'so_win', 'new_net']], on=['gid', 'ym'], how='left')
GM[['ni', 'so_win', 'new_net']] = GM[['ni', 'so_win', 'new_net']].fillna(0)
GM['flow'] = GM.flow_h + GM.new_net            # medida principal (híbrida)
GM['nome'] = GM.gid.map(gname)
GM['top100'] = [(g, y) in top for g, y in zip(GM.gid, GM.ym)]
prev = {(g, str(pd.Period(y, 'M') + 1)) for g, y in top}
GM['top100_prev'] = [(g, y) in prev for g, y in zip(GM.gid, GM.ym)]
GM.to_pickle(os.path.join(OUT, 'gestora_mes.pkl'))

# mercado: todos os fundos elegíveis (inclui bancos e gestoras fora da regra) e só as gestoras da regra
MK = E.groupby('ym').agg(pl=('pl', 'sum'), flow_rep=('flow', 'sum'), flow_h=('flow_h', 'sum'), cap=('cap', 'sum'), res=('res', 'sum'), nf=('CNPJ_FUNDO', 'nunique'))
MK['r'] = E[E.r.notna() & E.pl_ant.gt(0)].groupby('ym').apply(lambda x: (x.r * x.pl_ant).sum() / x.pl_ant.sum())
MK['pl_ant'] = MK.pl.shift(); MK['flow'] = MK.pl - MK.pl_ant * (1 + MK.r)
RG = GM[GM.top100_prev].groupby('ym').agg(pl=('pl', 'sum'), pl_ant=('pl_ant', 'sum'), flow=('flow', 'sum'), ng=('gid', 'nunique'))
MK.join(RG, rsuffix='_regra').to_csv(os.path.join(OUT, 'mercado_mes.csv'))
print('gestora-mês:', len(GM), '| gestoras:', GM.gid.nunique(), '| na regra (t-1):', int(GM.top100_prev.sum()))
