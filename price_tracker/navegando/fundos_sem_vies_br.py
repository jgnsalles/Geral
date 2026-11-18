"""Navegando Brasil sem viés de seleção, passo 2 (fundos): troca os 30 fundos escolhidos à mão (2014/2018) por uma regra point-in-time.
Regra (fixada antes de olhar retornos): em cada ano Y, entram os fundos de ações (classe "Ações" no cadastro da CVM, em qualquer época)
que não são FIC, nem indexados, nem previdência, nem exclusivos, cujo gestor no fim de Y-1 estava entre as 100 maiores gestoras do mês
(a regra das gestoras) e com PL ≥ R$ 100 mi no último dia útil de Y-1 (Informe Diário). O fundo fica na conta do ano até a última cota:
os que encerram no meio do ano contam até encerrar (sem viés de sobrevivência). Média mensal com peso igual entre os fundos vivos no mês.
Saídas (em price_tracker/navegando/): fundos_regra_br.csv (um fundo por linha) e fundos_regra_ano_br.csv (um ano por linha).
Uso: python3 fundos_sem_vies_br.py <pasta cvm> <carteiras_sv.json> <serie_mensal.csv dos 30> <ibov.csv>"""
import sys, os, re, zipfile, json, unicodedata, subprocess
import pandas as pd, numpy as np
RAW, JS, S30, IBOV = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(RAW, 'infd'); os.makedirs(CACHE, exist_ok=True)
PL_MIN = 100e6
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]
IDX = re.compile(r'IBOVESPA|\bIBOV\b|IBRX|\bIBX\b|INDICE|INDEX|INDEXAD|PASSIV|\bETF\b|\bSMLL\b|\bIDIV\b|\bMSCI\b|S&P|\bSP ?500\b|NASDAQ|\bPIBB\b')
ACT = re.compile(r'ATIV[OA]|ACTIVE|ALPHA|PLUS')
BAD = re.compile(r'\bFIC\b|COTAS|PREV|\bFIFE\b|VGBL|PGBL|PREVIDEN')

# ---------- cadastro: quem é fundo de ações elegível
z = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
rd = lambda n: pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str)
hc = rd('cad_fi_hist_classe.csv'); hf = rd('cad_fi_hist_fic.csv'); hx = rd('cad_fi_hist_exclusivo.csv')
cad = pd.read_csv(os.path.join(RAW, 'cad_fi.csv'), sep=';', encoding='latin1', dtype=str)
zr = zipfile.ZipFile(os.path.join(RAW, 'registro_fundo_classe.zip'))
rc = pd.read_csv(zr.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str)
fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if isinstance(c, str) and len(c) == 14 else c
rc['CNPJ_FUNDO'] = rc.CNPJ_Classe.str.zfill(14).map(fmt)
eq = set(hc[hc.CLASSE == 'Ações'].CNPJ_FUNDO) | set(cad[cad.CLASSE == 'Ações'].CNPJ_FUNDO) | set(rc[rc.Classificacao.fillna('').str.startswith('Aç')].CNPJ_FUNDO)
fic = set(hf[hf.iloc[:, -1].astype(str).str.upper().eq('S') | hf.astype(str).apply(lambda r: 'S' in r.values[2:], axis=1)].CNPJ_FUNDO) if len(hf) else set()
fic |= set(cad[cad.FUNDO_COTAS == 'S'].CNPJ_FUNDO)
exc = set(cad[cad.FUNDO_EXCLUSIVO == 'S'].CNPJ_FUNDO) | set(rc[rc.Exclusivo.fillna('').str.upper().str.startswith('S')].CNPJ_FUNDO)
exc |= set(hx[hx.astype(str).apply(lambda r: 'S' in r.values[2:], axis=1)].CNPJ_FUNDO) if len(hx) else set()
nome = pd.concat([rc.set_index('CNPJ_FUNDO').Denominacao_Social, cad.set_index('CNPJ_FUNDO').DENOM_SOCIAL])
nome = nome[~nome.index.duplicated(keep='last')]
cancel = pd.to_datetime(cad.set_index('CNPJ_FUNDO').DT_CANCEL, errors='coerce')
cancel = cancel[~cancel.index.duplicated(keep='last')]
def eleg(f):
    n = deacc(nome.get(f, ''))
    if f not in eq or f in fic or f in exc or BAD.search(n): return False
    return not (IDX.search(n) and not ACT.search(n))
EQ = {f for f in eq if eleg(f)}
print('fundos de ações elegíveis no cadastro (qualquer época):', len(EQ), flush=True)

# ---------- gestor na data (mesma função do cda_gestoras.py)
src = open(os.path.join(HERE, 'cda_gestoras.py')).read()
ns = {'pd': pd, 'np': np, 'os': os, 'zipfile': zipfile, 're': re, 'RAW': RAW, 'OUT': CACHE}
exec(src[src.index('def gestor_map'):src.index('def read(')], ns)
gestor_on = ns['gestor_on']

# ---------- universo das gestoras (a regra, por mês): raiz de CNPJ -> meses
d = json.load(open(JS)); M = d['meses']; G = d['gestoras']
top = {}
for g in G:
    r8s = {g['id']} if g.get('rb') else {root8(x[1]) for x in g['mb']} | {g['id']}
    for a, b in g.get('tp', []):
        for i in range(a, b + 1):
            top.setdefault(M[i], set()).update(r8s)
gname = {}
for g in G:
    for r in ({g['id']} if g.get('rb') else {root8(x[1]) for x in g['mb']} | {g['id']}): gname[r] = g['n']

# ---------- Informe Diário: cota e PL de fim de mês dos fundos elegíveis (cache por arquivo)
def url(tag):
    base = 'https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/'
    return base + ('HIST/' if len(tag) == 4 else '') + f'inf_diario_fi_{tag}.zip'
tags = [str(y) for y in range(2011, 2021)] + [f'{y}{m:02d}' for y in range(2021, 2027) for m in range(1, 13) if f'{y}{m:02d}' <= '202610']
parts = []
for t in tags:
    pk = os.path.join(CACHE, f'm_{t}.pkl')
    if not os.path.exists(pk):
        zp = os.path.join(CACHE, f'{t}.zip')
        r = subprocess.run(['curl', '-sf', '-A', 'Mozilla/5.0 (research)', '-o', zp, url(t)])
        if r.returncode: print('sem arquivo', t, flush=True); continue
        out = []
        with zipfile.ZipFile(zp) as zf:
            for n in zf.namelist():
                for c in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, chunksize=1_000_000):
                    c = c.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
                    if 'ID_SUBCLASSE' in c.columns: c = c[c.ID_SUBCLASSE.isna()]
                    c = c[c.CNPJ_FUNDO.isin(EQ)][['CNPJ_FUNDO', 'DT_COMPTC', 'VL_QUOTA', 'VL_PATRIM_LIQ']]
                    out.append(c)
        os.remove(zp)
        x = pd.concat(out); x['ym'] = x.DT_COMPTC.str[:7]
        x = x.sort_values('DT_COMPTC').drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
        x['q'] = pd.to_numeric(x.VL_QUOTA, errors='coerce'); x['pl'] = pd.to_numeric(x.VL_PATRIM_LIQ, errors='coerce')
        x[['CNPJ_FUNDO', 'ym', 'DT_COMPTC', 'q', 'pl']].to_pickle(pk)
        print('ok', t, len(x), flush=True)
    parts.append(pd.read_pickle(pk))
Q = pd.concat(parts).sort_values(['CNPJ_FUNDO', 'ym']).drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
Q['r'] = Q.groupby('CNPJ_FUNDO').q.pct_change()
Q.loc[(Q.r < -0.6) | (Q.r > 1.0), 'r'] = np.nan          # erro de cota
last_m = Q[Q.q.notna()].groupby('CNPJ_FUNDO').ym.max()
LAST = Q.ym.max()
CUT = str(pd.Period(LAST, 'M') - 3)   # sem cota há mais de 3 meses = encerrado

# ---------- coortes anuais
ib = pd.read_csv(IBOV).set_index('ym').pontos; ibr = ib.pct_change()
s30 = pd.read_csv(S30)
rows, fund = [], {}
for Y in range(2012, int(LAST[:4]) + 1):
    m0 = f'{Y - 1}-12'
    base = Q[(Q.ym == m0) & (Q.pl >= PL_MIN)]
    if base.empty: continue
    gm = gestor_on(base.CNPJ_FUNDO, pd.Timestamp(f'{Y - 1}-12-28'))
    T = top.get(m0, set())
    coh = [f for f in base.CNPJ_FUNDO if gm.get(f) and root8(gm[f]) in T]
    yms = [f'{Y}-{m:02d}' for m in range(1, 13) if f'{Y}-{m:02d}' <= LAST]
    R = Q[Q.CNPJ_FUNDO.isin(coh) & Q.ym.isin(yms)].pivot(index='ym', columns='CNPJ_FUNDO', values='r').reindex(yms)
    ew = R.mean(axis=1)                                     # peso igual entre os vivos no mês
    alive_full = R.notna().sum() >= len(yms) - 1
    fr = (1 + R).prod(min_count=1) - 1
    died = [f for f in coh if last_m.get(f, m0) < yms[-1] and last_m.get(f, m0) < CUT]
    r30 = s30[s30.ym.isin(yms)].groupby('ym').ret_fundo.mean().reindex(yms)
    ri = ibr.reindex(yms)
    rows.append(dict(ano=Y, meses=len(yms), fundos=len(coh), gestoras=len({root8(gm[f]) for f in coh}), encerraram_no_ano=len(died),
                     ret_medio=float((1 + ew.fillna(0)).prod() - 1), ret_mediano_vivos=float(fr[alive_full].median()) if alive_full.any() else None,
                     pct_bateu_ibov=float((fr[alive_full] > (1 + ri).prod() - 1).mean()) if alive_full.any() else None,
                     ret_30_selecionados=float((1 + r30.fillna(0)).prod() - 1) if r30.notna().sum() == len(yms) else None, ibov=float((1 + ri.fillna(0)).prod() - 1)))
    for f in coh:
        x = fund.setdefault(f, dict(cnpj=f, fundo=str(nome.get(f, f)).title()[:60], gestora=gname.get(root8(gm[f]), ''), anos=[]))
        x['anos'].append(Y)
A = pd.DataFrame(rows)
F = []
for f, x in fund.items():
    lm = last_m.get(f); cn = cancel.get(f)
    dead = None
    if lm and lm < CUT: dead = int(lm[:4])
    elif pd.notna(cn) and cn.strftime('%Y-%m') <= LAST: dead = int(cn.year)
    rr = Q[(Q.CNPJ_FUNDO == f) & Q.ym.between(f'{min(x["anos"])}-01', f'{max(x["anos"])}-12')].r.dropna()
    nm = len(rr); cg = (1 + rr).prod() ** (12 / nm) - 1 if nm >= 12 else None
    F.append(dict(cnpj=f, fundo=x['fundo'], gestora=x['gestora'], de=min(x['anos']), ate=max(x['anos']), ultima_cota=lm, dead=dead,
                  ret_anual=round(cg, 4) if cg is not None else None))
F = pd.DataFrame(F).sort_values(['dead', 'ret_anual'], na_position='first')
F.to_csv(os.path.join(HERE, 'fundos_regra_br.csv'), index=False)
A.to_csv(os.path.join(HERE, 'fundos_regra_ano_br.csv'), index=False)
cum = lambda s: float(np.prod(1 + s) ** (1 / len(s)) - 1)
full = A[A.meses == 12]
print(A.round(3).to_string())
print('anualizado (anos completos): regra', round(cum(full.ret_medio), 4), '| 30 selecionados', round(cum(full.ret_30_selecionados), 4), '| Ibov', round(cum(full.ibov), 4))
print('fundos na regra (algum ano):', len(F), '| encerrados:', int(F.dead.notna().sum()))
