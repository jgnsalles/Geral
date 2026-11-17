# Navegando US: posições, retorno e attribution das gestoras de gestoras.txt (13F, carteira completa listada nos EUA, sem opções).
# Retorno entre trimestres = soma de peso no trimestre anterior × variação do preço (valor ÷ quantidade, mediana entre todos os gestores do 13F),
# sem dividendos; desdobramentos corrigidos pela razão de quantidades; referência: SPDR S&P 500 ETF (SPY), mesma conta.
import pandas as pd, numpy as np, glob, json, re, os
from fractions import Fraction
W = '/home/user/work/us'
GL = [l.strip().split('|') for l in open(W + '/gestoras.txt') if l.strip()]
NOME = {c: n for c, n, t in GL}; TIPO = {n: t for c, n, t in GL}
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
H, PX = [], []
for f in sorted(glob.glob(W + '/f13/*.pkl')):
    d = pd.read_pickle(f); H.append(d['h']); PX.append(d['px'])
H = pd.concat(H, ignore_index=True); PX = pd.concat(PX, ignore_index=True)
H['per'] = pd.to_datetime(H.PERIODOFREPORT, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
PX['per'] = pd.to_datetime(PX.per, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
PX = PX.groupby(['CUSIP', 'per']).apply(lambda x: np.average(x['median'], weights=x['size'])) if False else PX.sort_values('size').groupby(['CUSIP', 'per'])['median'].last()
# só ações (sem títulos de dívida)
H = H[~(H.TITLEOFCLASS.fillna('') + ' ' + H.NAMEOFISSUER.fillna('')).str.upper().str.contains(r'\bNOTE|\bBOND|\bMTN\b|144A|\bDEB\b|\bCONV|SR NT|\bNTS\b|%', regex=True)]
# unidade trocada (US$ × US$ mil) linha a linha, pelo preço de mercado
r = (H.v / H.q) / pd.Series(list(zip(H.CUSIP, H.per)), index=H.index).map(PX)
H['v'] = H.v * np.where(r > 300, 1 / 1000, np.where(r < 1 / 300, 1000, 1.0))
print('linhas corrigidas', int(((r > 300) | (r < 1 / 300)).sum()), 'de', len(H))
H['g'] = H.CIK.map(NOME).map(slug)
# CNPJs da mesma gestora: por trimestre, fica a entrega maior
tt = H.groupby(['g', 'per', 'CIK']).v.sum().reset_index().sort_values('v').drop_duplicates(['g', 'per'], keep='last')
H = H.merge(tt[['g', 'per', 'CIK']], on=['g', 'per', 'CIK'])
H = H.drop_duplicates(['g', 'per', 'CUSIP', 'TITLEOFCLASS', 'v', 'q'])
H['emp'] = H.CUSIP.str[:6]
QS = H.groupby(['CUSIP', 'per', 'g']).q.sum()
SIMPLE = sorted({Fraction(a, b) for a in range(1, 11) for b in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 30, 40, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 30, 40, 50, 100)})
def sret(c, a, b):
    pa, pb = PX.get((c, a)), PX.get((c, b))
    if pa is None or pb is None or not (pa > 0 and pb > 0): return np.nan
    ratio = pb / pa
    if abs(np.log(ratio)) > np.log(1.6):
        try:
            qq = (QS.loc[(c, b)] / QS.loc[(c, a)]).dropna(); qq = qq[qq > 0]
            if len(qq):
                qm = float(qq.median()); f = min(SIMPLE, key=lambda z: abs(np.log(qm / float(z))))
                if abs(np.log(qm / float(f))) < 0.15 and abs(np.log(float(f))) > np.log(1.25) and abs(np.log(ratio * float(f))) < abs(np.log(ratio)) - 0.3: ratio *= float(f)
        except KeyError: pass
    return min(max(ratio - 1, -0.9), 4)
REFC = '78462F103'
nm = H.sort_values('per').groupby('emp').NAMEOFISSUER.last()
out = {'fundos': {}, 'emp': {}, 'ids': {}}
usadas = set()
for gid, h in H.groupby('g'):
    pers = sorted(h.per.unique())
    if len(pers) < 2: continue
    nome = NOME[h.CIK.iloc[-1]]
    tot = h.groupby('per').v.sum().reindex(pers)
    w = h.groupby(['emp', 'per']).v.sum().unstack().reindex(columns=pers).div(tot, axis=1)
    hc = h.groupby(['CUSIP', 'emp', 'per']).v.sum().unstack().reindex(columns=pers).div(tot, axis=1)
    C = {e: [None] * len(pers) for e in w.index}; R = [None] * len(pers); REF = [None] * len(pers); COV = [None] * len(pers)
    for j in range(1, len(pers)):
        a, b = pers[j - 1], pers[j]
        if (pd.Period(b) - pd.Period(a)).n > 6: continue
        s = cv = 0.0
        for (c, e), w0 in hc[a].dropna().items():
            x = sret(c, a, b)
            if np.isnan(x): continue
            C[e][j] = (C[e][j] or 0) + w0 * x; s += w0 * x; cv += w0
        R[j] = s / cv if cv > 0.5 else None; COV[j] = round(cv, 3)
        x = sret(REFC, a, b); REF[j] = None if np.isnan(x) else x
    p = {}
    for e in w.index:
        wv = [None if pd.isna(x) else int(round(x * 1e4)) for x in w.loc[e]]
        cv_ = [None if x is None else int(round(x * 1e6)) for x in C[e]]
        if max(abs(v or 0) for v in wv) < 20 and max(abs(v or 0) for v in cv_) < 300: continue     # posições < 0,2% (e sem efeito) ficam fora
        p[e] = [wv, cv_]; usadas.add(e)
    out['fundos'][gid] = {'nome': nome, 'tipo': TIPO[nome], 'ciks': sorted(h.CIK.unique()), 'datas': pers, 'R': [None if x is None else round(x, 5) for x in R],
                          'REF': [None if x is None else round(x, 5) for x in REF], 'COV': COV, 'TOT': [round(x / 1e6, 1) for x in tot], 'N': [int(x) for x in h.groupby('per').emp.nunique().reindex(pers)], 'p': p}
out['emp'] = {e: [str(nm.get(e, e)).title()] for e in usadas}
# índice de preço por empresa (trimestral, encadeado pelo CUSIP mais usado; desdobramentos corrigidos)
ALLP = sorted(H.per.unique()); rep = H[H.emp.isin(usadas)].groupby(['emp', 'CUSIP']).size().reset_index().sort_values(0).drop_duplicates('emp', keep='last').set_index('emp').CUSIP
pxo = {}
for e, c in rep.items():
    idx, cur, st = {}, None, False
    for a, b in zip(ALLP[:-1], ALLP[1:]):
        if not st:
            if PX.get((c, a)) is not None: st = True; cur = 1.0; idx[a] = 1.0
            else: continue
        x = sret(c, a, b)
        if np.isnan(x): continue
        cur *= 1 + x; idx[b] = round(cur, 4)
    if len(idx) >= 2: pxo[e] = idx
out['px'] = pxo
out['ids'] = {e: sorted(set(d.CUSIP)) for e, d in H[H.emp.isin(usadas)].groupby('emp')}
json.dump(out, open(W + '/us_attr.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for gid, f in sorted(out['fundos'].items(), key=lambda z: -z[1]['TOT'][-1]):
    r_ = [x for x in f['R'] if x is not None]; rf = [x for x, y in zip(f['REF'], f['R']) if y is not None and x is not None]
    print(f"{f['nome'][:32]:32} {f['datas'][0]}..{f['datas'][-1]} n={len(f['datas']):2} US${f['TOT'][-1]/1e3:8.1f}bi pos={len(f['p']):4} acum {np.prod([1+x for x in r_])-1:+7.2f} SPY {np.prod([1+x for x in rf])-1:+6.2f}")
print('ok', len(out['fundos']), 'empresas', len(usadas), os.path.getsize(W + '/us_attr.json') // 1024, 'KB')
