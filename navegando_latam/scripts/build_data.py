# Junta as bases da LatAm num JSON compacto para a página.
import pandas as pd, numpy as np, json, glob, os, re
W = '/home/user/work/latam'
out = {'gerado_em': pd.Timestamp.now().strftime('%d/%m/%Y')}

# ---------- Peru: AFPs (SBS), mensal ----------
A = pd.read_pickle(W + '/pe_acoes.pkl')
A = A[A.v > 0]
import unicodedata, re as _re
def _canon(n):
    n = unicodedata.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode().upper()
    n = _re.sub(r'\(.*?\)|\(.*$', '', n)
    n = _re.sub(r'\b(S\.?\s?A\.?\s?A\.?|S\.?\s?A\.?|INC\.?|PLC|CORP\.?|LTD\.?)\b', ' ', n)
    return _re.sub(r'[^A-Z0-9 ]', ' ', _re.sub(r'\s+', ' ', n)).split().__str__()
A['_k'] = A.emissor.map(_canon)
_nm = A.sort_values('ym').groupby('_k').emissor.last()
A['emissor'] = A._k.map(_nm)
_ALIAS = {'HOCHSCHILD': 'HOCHSCHILD MINING PLC', 'Intercorp FS': 'Intercorp Financial Services Inc.', 'PACASMAYO S.A.A': 'CEMENTOS PACASMAYO S.A.A.', 'G & M S.A': 'AENZA S.A.A. (antes GRANA & MONTERO S.A.A.)'}
A['emissor'] = A.emissor.replace(_ALIAS)
last = A.sort_values('ym').groupby('isin').agg(emissor=('emissor', 'last'), setor=('setor', 'last'))
A = A.drop(columns=['emissor', 'setor']).join(last, on='isin')
AFP = {'HA': 'Habitat', 'IN': 'Integra', 'PR': 'Prima', 'RI': 'Profuturo'}
months = sorted(A.ym.unique())
g = A.groupby(['afp', 'emissor', 'ym']).agg(v=('v', 'sum'), q=('q', 'sum')).reset_index()
pe = {'meses': months, 'afps': AFP, 'emissores': {}, 'p': {}}
for e, d in last.groupby('emissor'): pe['emissores'][e] = {'setor': d.setor.iloc[-1], 'isins': sorted(d.index)}
mi = {m: k for k, m in enumerate(months)}
for (a, e), d in g.groupby(['afp', 'emissor']):
    v = [None] * len(months); q = [None] * len(months)
    for r in d.itertuples(): v[mi[r.ym]] = round(r.v / 1e3, 3); q[mi[r.ym]] = None if pd.isna(r.q) else int(r.q)   # v em S/ milhões
    pe['p'].setdefault(a, {})[e] = [v, q]
out['pe'] = pe

# ---------- EUA: N-PORT, fundos americanos em ações da LatAm, por trimestre de entrega ----------
rows = []
for f in sorted(glob.glob(W + '/np2/*.pkl')):
    q = os.path.basename(f)[:-4]; H = pd.read_pickle(f)
    H['rd'] = pd.to_datetime(H.REPORT_DATE, format='%d-%b-%Y', errors='coerce')
    H = H.sort_values(['SERIES_ID', 'rd', 'FILING_DATE'])
    lastacc = H.groupby('SERIES_ID').ACCESSION_NUMBER.last()          # última carteira de cada fundo no trimestre
    H = H[H.ACCESSION_NUMBER.isin(set(lastacc))]
    H['tri'] = q; rows.append(H)
N = pd.concat(rows)
N = N[~N.ISSUER_NAME.str.upper().str.contains('CARNIVAL', na=False)]
N['key'] = N['isin'].fillna('').where(N['isin'].fillna('') != '', N.ISSUER_CUSIP.fillna('') + '|' + N.ISSUER_NAME.str.upper().str[:30])
nm = N.sort_values('tri').groupby('key').agg(nome=('ISSUER_NAME', 'last'), pais=('INVESTMENT_COUNTRY', 'last'), tk=('ticker', 'last'))
# empresa: LEI do emissor (junta ON/PN/ADR); sem LEI, nome normalizado
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'\b(S\.?A\.?B?\.?( DE C\.?V\.?)?|SA|SAB|DE CV|INC|LTD|ADR|SPONSORED|CORP|PN|ON|PREF|PFD|CLASS [A-Z]|CL [A-Z])\b|[-,./]', ' ', str(s).upper())).strip()[:40]
nm['n2'] = nm.nome.map(norm)
lei = N[N.ISSUER_LEI.str.len().eq(20)].groupby('key').ISSUER_LEI.agg(lambda x: x.mode().iloc[0])
nm['emp'] = lei.reindex(nm.index).fillna(nm.n2)
N = N.join(nm[['emp']], on='key')
wt = N.groupby(['emp', 'key']).usd.sum().reset_index().join(nm[['n2', 'pais', 'tk']], on='key')
best = wt.sort_values('usd').groupby('emp').last()
# fluxo por título (ações do mesmo título são comparáveis) e depois somado por empresa
PAS = r'INDEX|ETF|MSCI|FTSE|S&P|RUSSELL|TOTAL (INTERNATIONAL|WORLD)|ISHARES|SPDR|VANGUARD (TOTAL|EMERGING|FTSE|DEVELOPED)|PASSIVE|DIMENSIONAL|DFA |AVANTIS'
N['REGISTRANT_NAME'] = np.where((N.SERIES_NAME.fillna('') + ' ' + N.REGISTRANT_NAME.fillna('')).str.upper().str.contains(PAS, regex=True), N.REGISTRANT_NAME + ' · índice', N.REGISTRANT_NAME)
K = N.groupby(['REGISTRANT_NAME', 'emp', 'key', 'tri']).agg(usd=('usd', 'sum'), sh=('BALANCE', 'sum')).reset_index()
tris = sorted(N.tri.unique()); ti = {t: k for k, t in enumerate(tris)}
# fluxo por fundo e título: desdobramento/grupamento quando a quantidade muda por uma fração redonda e o valor não acompanha
from fractions import Fraction
SIMPLE = sorted({Fraction(a, b) for a in range(1, 11) for b in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 50, 100)})
KS = N.groupby(['SERIES_ID', 'REGISTRANT_NAME', 'emp', 'key', 'tri']).agg(usd=('usd', 'sum'), sh=('BALANCE', 'sum')).reset_index()
fl = []; nsplit = 0
for (sid, r, e, k), d in KS.groupby(['SERIES_ID', 'REGISTRANT_NAME', 'emp', 'key']):
    d = d.set_index('tri')
    for t in tris[1:]:
        p_ = tris[ti[t] - 1]; a_ = d.loc[p_] if p_ in d.index else None; b_ = d.loc[t] if t in d.index else None
        if a_ is None and b_ is None: continue
        if a_ is None: f_ = b_.usd
        elif b_ is None: f_ = -a_.usd
        elif b_.sh > 0 and a_.sh > 0 and b_.usd > 0 and a_.usd > 0:
            q = b_.sh / a_.sh; vr = b_.usd / a_.usd; fac = 1.0
            if abs(np.log(q)) > np.log(1.25):
                fs = min(SIMPLE, key=lambda c: abs(np.log(q / float(c))))
                if abs(np.log(q / float(fs))) < 0.03 and abs(np.log(vr)) < abs(np.log(float(fs))) / 2: fac = float(fs); nsplit += 1
            f_ = (b_.sh - a_.sh * fac) * b_.usd / b_.sh
        else: f_ = 0
        fl.append((r, e, t, f_))
print('desdobramentos tratados (fundo × título × trimestre):', nsplit)
FL = pd.DataFrame(fl, columns=['REGISTRANT_NAME', 'emp', 'tri', 'flow']).groupby(['tri', 'REGISTRANT_NAME', 'emp']).flow.sum()
G = K.groupby(['tri', 'REGISTRANT_NAME', 'emp']).usd.sum().to_frame().join(FL, how='outer').reset_index()
us = {'tris': tris, 'emp': {}, 'g': {}}
us['ids'] = {e: sorted(set(d['isin'].dropna().str.upper()) | set(d.ISSUER_CUSIP.dropna().str.upper()) - {'000000000', '999999999', 'N/A'}) for e, d in N.groupby('emp')}
for e, r_ in best.iterrows(): us['emp'][e] = {'pais': r_.pais, 'nome': r_.n2, 'tk': r_.tk if isinstance(r_.tk, str) else ''}
tot_reg = G.groupby('REGISTRANT_NAME').usd.sum()
keep = set(tot_reg[tot_reg >= 5e6].index)                                # gestoras com ≥ US$ 5 mi somados
for (r, e), d in G[G.REGISTRANT_NAME.isin(keep)].groupby(['REGISTRANT_NAME', 'emp']):
    v = [None] * len(tris); f = [None] * len(tris)
    for x in d.itertuples():
        if pd.notna(x.usd): v[ti[x.tri]] = round(x.usd / 1e6, 2)
        if pd.notna(x.flow): f[ti[x.tri]] = round(x.flow / 1e6, 2)
    if max(z or 0 for z in v) < 0.05 and max(abs(z or 0) for z in f) < 0.05: continue
    us['g'].setdefault(r, {})[e] = [v, f]
us['emp'] = {k: v for k, v in us['emp'].items() if any(k in m for m in us['g'].values())}
out['us'] = us
print('EUA', tris, len(us['g']), 'gestoras', len(us['emp']), 'empresas')

# ---------- Chile: fondos mutuos (CMF), último trimestre ----------
C = pd.read_excel('/home/user/raw/latam/cl/cart.xlsx', sheet_name='datos')
fund_tot = C.groupby('fo_run').val_cierr.sum()
E = C[C.descripcion_tipoinst.isin(['ACCIONES DE SOCIEDADES ANONIMAS ABIERTAS'])].copy()
E['w'] = E.val_cierr / E.fo_run.map(fund_tot)
cl = {'mes': str(int(C.fecha_mes.iloc[0])), 'f': []}
for (agf, fr, fn, fam), d in E.groupby(['nombre_agf', 'fo_run', 'nombre_fondo', 'familia_estudios']):
    cl['f'].append({'agf': agf, 'n': fn, 'fam': fam, 'tot': round(float(fund_tot[fr]), 2), 'p': {r.nemotecnico: [round(float(r.val_cierr), 3), round(float(r.w), 5)] for r in d.itertuples()}})
emis = E.groupby('nemotecnico').nombre_emisor.last().to_dict()
cl['emissores'] = emis
out['cl'] = cl
out['fpe'] = json.load(open(W + '/pe_attr.json'))
out['fus'] = json.load(open(W + '/us_attr.json'))
out['f13'] = json.load(open(W + '/f13_attr.json')) if os.path.exists(W + '/f13_attr.json') else {'fundos': {}, 'emp': {}}
out['setores'] = json.load(open(W + '/setores.json')) if os.path.exists(W + '/setores.json') else {}
json.dump(out, open(W + '/latam.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', os.path.getsize(W + '/latam.json') // 1024, 'KB')
