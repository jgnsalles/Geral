# 13F: posições e attribution das gestoras focadas em LatAm (só a parte listada nos EUA: ADRs e ações americanas).
# Retorno da carteira 13F entre dois trimestres = soma de peso no trimestre anterior × variação do preço (valor ÷ quantidade,
# mediana entre todos os gestores do 13F), sem dividendos; desdobramentos corrigidos pela razão de quantidades.
# Referência: iShares Latin America 40 ETF (ILF), mesma conta de preço.
import pandas as pd, numpy as np, glob, json, os, re
from fractions import Fraction
W = '/home/user/work/latam'
H, PX, QS = [], [], []
for f in sorted(glob.glob(W + '/f13/*.pkl')):
    d = pd.read_pickle(f); H.append(d['h']); PX.append(d['px']); QS.append(d['qs'])
H = pd.concat(H); PX = pd.concat(PX); QS = pd.concat(QS)
for x in (H, PX, QS): x['per'] = pd.to_datetime(x.PERIODOFREPORT, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
H = H[~(H.TITLEOFCLASS.fillna('') + ' ' + H.NAMEOFISSUER.fillna('')).str.upper().str.contains(r'\bNOTE|\bBOND|\bMTN\b|144A|\bDEB|\bCONV|SR NT|\bNTS\b|%', regex=True)]   # só ações
H = H.sort_values('per').drop_duplicates(['CIK', 'per', 'CUSIP', 'TITLEOFCLASS', 'v', 'q'])
# 1 entrega por gestora e trimestre (a de maior carteira, caso haja duplicata entre arquivos)
best = H.groupby(['CIK', 'per', 'ACCESSION_NUMBER']).tot.first().reset_index().sort_values('tot').drop_duplicates(['CIK', 'per'], keep='last')
H = H[H.ACCESSION_NUMBER.isin(set(best.ACCESSION_NUMBER))]
PX = PX.groupby(['CUSIP', 'per']).px.median()
QS = QS.groupby(['CUSIP', 'per', 'CIK']).q.sum()
LAT = set(open(W + '/latam_cusips.txt').read().split())
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
    if sh.max() < 0.5 and not re.search(r'MONEDA|FOURTH SAIL|INCA INVEST', h.FILINGMANAGER_NAME.iloc[-1].upper()): continue   # ≥ 50% em LatAm, ou gestora pedida
    name = h.sort_values('per').FILINGMANAGER_NAME.iloc[-1]
    tot = h.groupby('per').tot.first().reindex(pers); latv = h.groupby('per').latv.first().reindex(pers)
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
    # divisão por país da parte latino-americana; fora: gestoras sediadas no Brasil e carteiras ≥ 70% Brasil
    hl = h[h.CUSIP.str.upper().isin(LAT)].assign(pais=lambda d: d.CUSIP.str.upper().map(CPAIS))
    mixp = hl.groupby(['per', 'pais']).v.sum().unstack().fillna(0)
    mixp = mixp.div(mixp.sum(axis=1), axis=0)
    br = float(mixp.get('BR', pd.Series(0, index=mixp.index)).median()) if len(mixp) else 0
    if h.FILINGMANAGER_STATEORCOUNTRY.iloc[-1] == 'D5' or br >= 0.7: continue
    nlat = hl.groupby('per').emp.nunique().median() if len(hl) else 0
    shm = float((h.groupby('per').latv.first() / h.groupby('per').tot.first()).median())
    pedida = bool(re.search(r'MONEDA|FOURTH SAIL|INCA INVEST', h.FILINGMANAGER_NAME.iloc[-1].upper()))
    if not pedida and (nlat < 5 or shm < 0.5): continue           # foco em LatAm: ≥ 5 empresas da região e metade da carteira, na mediana
    mix = mixp.iloc[-1].sort_values(ascending=False) if len(mixp) else pd.Series(dtype=float)
    out['fundos'][cik] = {'nome': name, 'pais': h.FILINGMANAGER_STATEORCOUNTRY.iloc[-1], 'datas': pers, 'R': [None if x is None else round(x, 5) for x in R],
                          'REF': [None if x is None else round(x, 5) for x in REF], 'COV': COV, 'TOT': [round(x / 1e6, 1) for x in tot],
                          'LAT': [round(float(a / b), 3) for a, b in zip(latv, tot)], 'mix': [[k, round(float(v), 3)] for k, v in mix.items() if v >= 0.03], 'p': p}
json.dump(out, open(W + '/f13_attr.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for cik, f in sorted(out['fundos'].items(), key=lambda z: -z[1]['TOT'][-1]):
    r = [x for x in f['R'] if x is not None]
    print(f"{f['nome'][:42]:42} {f['datas'][0]}..{f['datas'][-1]} n={len(f['datas']):2} US${f['TOT'][-1]:7.0f}mi LatAm {f['LAT'][-1]:.0%} acum {np.prod([1 + x for x in r]) - 1:+.2f}")
print('ok', len(out['fundos']), os.path.getsize(W + '/f13_attr.json') // 1024, 'KB')
