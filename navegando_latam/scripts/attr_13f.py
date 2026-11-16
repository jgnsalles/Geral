# 13F: posições e attribution das gestoras focadas em LatAm (só a parte listada nos EUA: ADRs e ações americanas).
# Retorno da carteira 13F entre dois trimestres = soma de peso no trimestre anterior × variação do preço (valor ÷ quantidade,
# mediana entre todos os gestores do 13F), sem dividendos; desdobramentos corrigidos pela razão de quantidades.
# Referência: iShares Latin America 40 ETF (ILF), mesma conta de preço.
import pandas as pd, numpy as np, glob, json, os, re
from fractions import Fraction
W = '/home/user/work/latam'
EXCL = (r'VANGUARD|BLACKROCK|ISHARES|STATE STREET|SSGA|DIMENSIONAL|GEODE|NORTHERN TRUST|SCHWAB|INVESCO|LEGAL & GENERAL|PARAMETRIC|RUSSELL INV|\bETFS?\b|INDEX|'
        r'CITADEL|JANE STREET|SUSQUEHANNA|OPTIVER|\bIMC\b|VIRTU|HUDSON RIVER|FLOW TRADERS|TWO SIGMA SECURITIES|'
        r'MORGAN STANLEY|GOLDMAN|JPMORGAN|J\.P\. MORGAN|UBS |BANK OF AMERICA|BARCLAYS|CITIGROUP|WELLS FARGO|ROYAL BANK|BNP|SOCIETE GENERALE|CREDIT SUISSE|DEUTSCHE BANK|NOMURA|HSBC|SANTANDER|ITAU|BRADESCO|SCOTIA|BMO|TORONTO DOMINION|JEFFERIES|RAYMOND JAMES|LPL FINANCIAL|AMERIPRISE|'
        r'\bBANKS?\b|\bBANCO\b|TRUST CO|TRUIST|ENVESTNET|SYNOVUS|PINNACLE FINANCIAL|FINANCIAL CORP|EXANE|TIDAL INV|MIRAE ASSET|ALLEN HOLDING|RENAISSANCE TECH|'
        r'RETIREMENT|PENSION|TEACHERS|NORGES|SOVEREIGN|PUBLIC EMPLOYEES|STATE OF |TREASURER|COMMONWEALTH|CENTRAL BANK|BANCO CENTRAL|BNDES|MIZUHO|SUMITOMO|MITSUBISHI')
PED = r'MONEDA|FOURTH SAIL|INCA INVEST|GQG'
# 1ª passada: escolhe as gestoras pelo resumo (todas as entregas 13F), sem carregar as carteiras
S = pd.concat([pd.read_pickle(f)['sum'] for f in sorted(glob.glob(W + '/f13/*.pkl'))])
S['per'] = pd.to_datetime(S.PERIODOFREPORT, format='%d-%b-%Y', errors='coerce')
S = S.sort_values('tot').drop_duplicates(['CIK', 'per'], keep='last').sort_values('per')
SEL = set()
for cik, s in S.groupby('CIK'):
    nm = str(s.FILINGMANAGER_NAME.iloc[-1]).upper()
    if re.search(EXCL, nm): continue
    sh = s.latv / s.tot
    if re.search(PED, nm) or sh.max() >= 0.5 or (s.latv.tail(8).median() >= 300e6 and sh.tail(8).median() >= 0.02): SEL.add(cik)
print('pré-seleção', len(SEL))
H, PX, QS = [], [], []
for f in sorted(glob.glob(W + '/f13/*.pkl')):
    d = pd.read_pickle(f); H.append(d['h'][d['h'].CIK.isin(SEL)]); PX.append(d['px'])
    q = d['qs']; QS.append(q[q.CUSIP.isin(set(H[-1].CUSIP))]); del d, q
H = pd.concat(H); PX = pd.concat(PX); QS = pd.concat(QS)
for x in (H, PX, QS): x['per'] = pd.to_datetime(x.PERIODOFREPORT, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
H = H[~(H.TITLEOFCLASS.fillna('') + ' ' + H.NAMEOFISSUER.fillna('')).str.upper().str.contains(r'\bNOTE|\bBOND|\bMTN\b|144A|\bDEB|\bCONV|SR NT|\bNTS\b|%', regex=True)]   # só ações
H = H.sort_values('per').drop_duplicates(['CIK', 'per', 'CUSIP', 'TITLEOFCLASS', 'v', 'q'])
# 1 entrega por gestora e trimestre (a de maior carteira, caso haja duplicata entre arquivos)
best = H.groupby(['CIK', 'per', 'ACCESSION_NUMBER']).tot.first().reset_index().sort_values('tot').drop_duplicates(['CIK', 'per'], keep='last')
H = H[H.ACCESSION_NUMBER.isin(set(best.ACCESSION_NUMBER))]
PX = PX.groupby(['CUSIP', 'per']).px.median()
QS = QS.groupby(['CUSIP', 'per', 'CIK']).q.sum()
NAO_LATAM = ['143658', '191216', '54150E', '70450Y', '816851', '962879', 'G1466R', 'G2004J']   # empresas fora da região marcadas por engano (ex.: BDRs) e títulos de dívida
LAT = {c for c in open(W + '/latam_cusips.txt').read().split() if c[:6] not in NAO_LATAM}
H['latv'] = H.ACCESSION_NUMBER.map(H[H.CUSIP.str.upper().isin(LAT)].groupby('ACCESSION_NUMBER').v.sum()).fillna(0)
CPAIS = pd.read_pickle(W + '/cusip_pais.pkl')
SIMPLE = sorted({Fraction(a, b) for a in range(1, 11) for b in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 50, 100)})
def sret(c, a, b):
    pa, pb = PX.get((c, a)), PX.get((c, b))
    if pa is None or pb is None or not (pa > 0 and pb > 0): return np.nan
    ratio = pb / pa
    if abs(np.log(ratio)) > np.log(1.6):
        try:
            qq = (QS.loc[(c, b)] / QS.loc[(c, a)]).dropna(); qq = qq[qq > 0]
            if len(qq):
                qm = float(qq.median()); f = min(SIMPLE, key=lambda z: abs(np.log(qm / float(z))))
                if abs(np.log(qm / float(f))) < 0.03 and abs(np.log(float(f))) > np.log(1.25) and abs(np.log(ratio * float(f))) < abs(np.log(ratio)): ratio *= float(f)
        except KeyError: pass
    return min(max(ratio - 1, -0.8), 3)
REFC = '464287390'   # iShares Latin America 40 ETF
H['emp'] = H.CUSIP.str[:6]
nm = H.sort_values('per').groupby('emp').NAMEOFISSUER.last()
lat_emp = set(H[H.CUSIP.str.upper().isin(LAT)].emp)
out = {'fundos': {}, 'emp': {e: [n.title(), e in lat_emp] for e, n in nm.items()}}
out['ids'] = {e: sorted(set(d.CUSIP.str.upper())) for e, d in H.groupby('emp')}
for cik, h in H.groupby('CIK'):
    pers = sorted(h.per.unique())
    if len(pers) < 3: continue
    sh = (h.groupby('per').latv.first() / h.groupby('per').tot.first())
    NM = h.sort_values('per').FILINGMANAGER_NAME.iloc[-1].upper()
    if re.search(EXCL, NM): continue                                   # passivos, corretoras, bancos, previdência
    pedida = bool(re.search(PED, NM))
    lv = h.groupby('per').latv.first().sort_index().tail(8)
    foco = sh.max() >= 0.5
    forte = lv.median() >= 300e6 and float(sh.tail(8).median()) >= 0.02    # gestora ativa global/emergentes com posição relevante em LatAm
    if not (foco or forte or pedida): continue
    name = h.sort_values('per').FILINGMANAGER_NAME.iloc[-1]
    # divisão por país da parte latino-americana; fora: gestoras sediadas no Brasil e carteiras ≥ 70% Brasil
    hl = h[h.CUSIP.str.upper().isin(LAT)].assign(pais=lambda d: d.CUSIP.str.upper().map(CPAIS))
    mixp = hl.groupby(['per', 'pais']).v.sum().unstack().fillna(0)
    mixp = mixp.div(mixp.sum(axis=1), axis=0)
    br = float(mixp.get('BR', pd.Series(0, index=mixp.index)).median()) if len(mixp) else 0
    if h.FILINGMANAGER_STATEORCOUNTRY.iloc[-1] == 'D5' or (foco and not pedida and br >= 0.7): continue
    nlat = hl.groupby('per').emp.nunique().median() if len(hl) else 0
    shm = float((h.groupby('per').latv.first() / h.groupby('per').tot.first()).median())
    if foco and not pedida and not forte and (nlat < 5 or shm < 0.5): continue
    if not foco and not pedida and nlat < 5: continue           # foco em LatAm: ≥ 5 empresas da região e metade da carteira, na mediana
    tipo = 'latam' if (foco and float(sh.median()) >= 0.4) else 'global'
    latv0 = h.groupby('per').latv.first().reindex(pers); tot0 = h.groupby('per').tot.first().reindex(pers)
    if tipo == 'global':   # gestora global/emergentes: só a parcela LatAm (pesos e retorno sobre ela)
        h = h[h.CUSIP.str.upper().isin(LAT)].copy(); h['tot'] = h.latv
    tot = h.groupby('per').tot.first().reindex(pers); latv = latv0
    hv = h.groupby(['emp', 'per']).v.sum().unstack().reindex(columns=pers)
    w = hv.div(tot, axis=1)
    hc = h.groupby(['CUSIP', 'emp', 'per']).v.sum().unstack().reindex(columns=pers).div(tot, axis=1)
    C = {e: [None] * len(pers) for e in w.index}; R = [None] * len(pers); REF = [None] * len(pers); COV = [None] * len(pers)
    for j in range(1, len(pers)):
        a, b = pers[j - 1], pers[j]
        if (pd.Period(b) - pd.Period(a)).n > 6: continue
        s = 0.0; cv = 0.0
        for (c, e), w0 in hc[a].dropna().items():
            r = sret(c, a, b)
            if np.isnan(r): continue
            C[e][j] = (C[e][j] or 0) + w0 * r; s += w0 * r; cv += w0
        R[j] = s / cv if cv > 0.5 else None          # retorno da parte com preço nas duas datas
        COV[j] = round(cv, 3)
        rr = sret(REFC, a, b); REF[j] = None if np.isnan(rr) else rr
    p = {}
    for e in w.index:
        wv = [None if pd.isna(x) else int(round(x * 1e4)) for x in w.loc[e]]
        cv_ = [None if x is None else int(round(x * 1e6)) for x in C[e]]
        if max(abs(v or 0) for v in wv) < 10 and max(abs(v or 0) for v in cv_) < 100: continue
        p[e] = [wv, cv_]
    mix = mixp.iloc[-1].sort_values(ascending=False) if len(mixp) else pd.Series(dtype=float)
    out['fundos'][cik] = {'nome': name, 'pais': h.FILINGMANAGER_STATEORCOUNTRY.iloc[-1], 'datas': pers, 'R': [None if x is None else round(x, 5) for x in R],
                          'REF': [None if x is None else round(x, 5) for x in REF], 'COV': COV, 'TOT': [round(x / 1e6, 1) for x in tot0],
                          'LAT': [round(float(a / b), 3) for a, b in zip(latv0, tot0)], 'mix': [[k, round(float(v), 3)] for k, v in mix.items() if v >= 0.03], 'tipo': tipo, 'p': p}
usadas = {e for f in out['fundos'].values() for e in f['p']}
out['emp'] = {e: v for e, v in out['emp'].items() if e in usadas}; out['ids'] = {e: v for e, v in out['ids'].items() if e in usadas}
json.dump(out, open(W + '/f13_attr.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for cik, f in sorted(out['fundos'].items(), key=lambda z: -z[1]['TOT'][-1]):
    r = [x for x in f['R'] if x is not None]
    print(f"{f['nome'][:42]:42} {f['datas'][0]}..{f['datas'][-1]} n={len(f['datas']):2} US${f['TOT'][-1]:7.0f}mi LatAm {f['LAT'][-1]:.0%} acum {np.prod([1 + x for x in r]) - 1:+.2f}")
print('ok', len(out['fundos']), os.path.getsize(W + '/f13_attr.json') // 1024, 'KB')
