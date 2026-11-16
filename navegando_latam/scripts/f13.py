# 13F (SEC): gestoras focadas em América Latina (≥ 40% da carteira 13F em empresas da região) + lista de gestoras pedidas.
# Uso: python f13.py <zip> <saída .pkl> <arquivo com CUSIPs da LatAm>
import zipfile, sys, pandas as pd, numpy as np
Z, OUT, CUS = sys.argv[1:4]
LAT = set(open(CUS).read().split())
WATCH = r'MONEDA|FOURTH SAIL|INCA INVEST|ONYX|LATAM|LATIN AMERICA|COMPASS GROUP|LARRAIN|ANDINA|CREDICORP'
z = zipfile.ZipFile(Z)
rd = lambda n, cols=None, ch=False: pd.read_csv(z.open([x for x in z.namelist() if x.upper().endswith(n)][0]), sep='\t', dtype=str, quoting=3, on_bad_lines='skip', usecols=cols, chunksize=1000000 if ch else None, encoding='latin1')
C = rd('COVERPAGE.TSV', ['ACCESSION_NUMBER', 'REPORTCALENDARORQUARTER', 'ISAMENDMENT', 'AMENDMENTTYPE', 'FILINGMANAGER_NAME', 'FILINGMANAGER_STATEORCOUNTRY', 'REPORTTYPE'])
S = rd('SUBMISSION.TSV', ['ACCESSION_NUMBER', 'FILING_DATE', 'SUBMISSIONTYPE', 'CIK', 'PERIODOFREPORT'])
C = C.merge(S, on='ACCESSION_NUMBER')
C = C[C.REPORTTYPE.fillna('').str.contains('HOLDINGS') & ~((C.ISAMENDMENT == 'Y') & (C.AMENDMENTTYPE.fillna('').str.upper().str.startswith('NEW')))]
C['fd'] = pd.to_datetime(C.FILING_DATE, format='%d-%b-%Y', errors='coerce')
C['mult'] = np.where(C.fd < '2023-01-03', 1000.0, 1.0)       # antes de 2023 o valor vinha em US$ mil
C = C.sort_values('fd').drop_duplicates(['CIK', 'PERIODOFREPORT'], keep='last')
acc = set(C.ACCESSION_NUMBER); mult = C.set_index('ACCESSION_NUMBER').mult
H = []; PX = []
for c in rd('INFOTABLE.TSV', ['ACCESSION_NUMBER', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'VALUE', 'SSHPRNAMT', 'SSHPRNAMTTYPE', 'PUTCALL'], True):
    c = c[c.ACCESSION_NUMBER.isin(acc) & c.PUTCALL.isna() & (c.SSHPRNAMTTYPE == 'SH')].copy()
    c['v'] = pd.to_numeric(c.VALUE, errors='coerce') * c.ACCESSION_NUMBER.map(mult); c['q'] = pd.to_numeric(c.SSHPRNAMT, errors='coerce')
    c = c[(c.v > 0) & (c.q > 0)]
    H.append(c[['ACCESSION_NUMBER', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'v', 'q']])
H = pd.concat(H)
H['lat'] = H.CUSIP.str.upper().isin(LAT)
tot = H.groupby('ACCESSION_NUMBER').v.sum(); latv = H[H.lat].groupby('ACCESSION_NUMBER').v.sum().reindex(tot.index).fillna(0)
C = C.set_index('ACCESSION_NUMBER'); C['tot'] = tot; C['latv'] = latv; C = C[C.tot.notna()]
keep = C[((C.latv / C.tot >= 0.4) & (C.latv >= 20e6)) | C.FILINGMANAGER_NAME.fillna('').str.upper().str.contains(WATCH, regex=True)].index
K = H[H.ACCESSION_NUMBER.isin(set(keep))].merge(C[['CIK', 'FILINGMANAGER_NAME', 'PERIODOFREPORT', 'tot', 'latv', 'FILINGMANAGER_STATEORCOUNTRY']], left_on='ACCESSION_NUMBER', right_index=True)
# preço por CUSIP no trimestre: mediana de valor ÷ quantidade entre todos os gestores
cus = set(K.CUSIP)
P = H[H.CUSIP.isin(cus)].merge(C[['PERIODOFREPORT']], left_on='ACCESSION_NUMBER', right_index=True)
P['px'] = P.v / P.q
px = P.groupby(['CUSIP', 'PERIODOFREPORT']).px.median().reset_index()
qs = P.groupby(['CUSIP', 'PERIODOFREPORT', 'ACCESSION_NUMBER']).q.sum().reset_index().merge(C[['CIK']], left_on='ACCESSION_NUMBER', right_index=True)
pd.to_pickle({'h': K, 'px': px, 'qs': qs[['CUSIP', 'PERIODOFREPORT', 'CIK', 'q']]}, OUT)
print(OUT, 'gestoras', K.CIK.nunique(), 'períodos', sorted(K.PERIODOFREPORT.unique())[-2:], sorted(K.FILINGMANAGER_NAME.unique())[:12])
