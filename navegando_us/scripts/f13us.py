# 13F (SEC) para o Navegando US: carteira completa (ações, sem opções) das gestoras de gestoras.txt + preço de mercado por CUSIP.
# Uso: python f13us.py <zip> <saída .pkl>
import zipfile, sys, pandas as pd, numpy as np
Z, OUT = sys.argv[1:3]
CIKS = {l.split('|')[0] for l in open('/home/user/work/us/gestoras.txt') if l.strip()}
z = zipfile.ZipFile(Z)
rd = lambda n, cols=None, ch=False: pd.read_csv(z.open([x for x in z.namelist() if x.upper().endswith(n)][0]), sep='\t', dtype=str, quoting=3, on_bad_lines='skip', usecols=cols, chunksize=1000000 if ch else None, encoding='latin1')
C = rd('COVERPAGE.TSV', ['ACCESSION_NUMBER', 'ISAMENDMENT', 'AMENDMENTTYPE', 'FILINGMANAGER_NAME', 'REPORTTYPE'])
S = rd('SUBMISSION.TSV', ['ACCESSION_NUMBER', 'FILING_DATE', 'CIK', 'PERIODOFREPORT'])
C = C.merge(S, on='ACCESSION_NUMBER')
C = C[C.REPORTTYPE.fillna('').str.upper().str.contains('HOLDINGS|COMBINATION') & ~((C.ISAMENDMENT == 'Y') & (C.AMENDMENTTYPE.fillna('').str.upper().str.startswith('NEW')))]
C['fd'] = pd.to_datetime(C.FILING_DATE, format='%d-%b-%Y', errors='coerce')
C['mult'] = np.where(C.fd < '2023-01-03', 1000.0, 1.0)
C = C.sort_values('fd').drop_duplicates(['CIK', 'PERIODOFREPORT'], keep='last')
mult = C.set_index('ACCESSION_NUMBER').mult; per = C.set_index('ACCESSION_NUMBER').PERIODOFREPORT
keep = set(C[C.CIK.isin(CIKS)].ACCESSION_NUMBER)
H = []; PX = []
for c in rd('INFOTABLE.TSV', ['ACCESSION_NUMBER', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'VALUE', 'SSHPRNAMT', 'SSHPRNAMTTYPE', 'PUTCALL'], True):
    c = c[c.ACCESSION_NUMBER.isin(mult.index) & c.PUTCALL.isna() & (c.SSHPRNAMTTYPE == 'SH')].copy()
    c['v'] = pd.to_numeric(c.VALUE, errors='coerce') * c.ACCESSION_NUMBER.map(mult); c['q'] = pd.to_numeric(c.SSHPRNAMT, errors='coerce')
    c = c[(c.v > 0) & (c.q > 0)]; c['CUSIP'] = c.CUSIP.str.upper()
    PX.append(pd.DataFrame({'CUSIP': c.CUSIP.values, 'per': c.ACCESSION_NUMBER.map(per).values, 'px': (c.v / c.q).values}))
    H.append(c[c.ACCESSION_NUMBER.isin(keep)][['ACCESSION_NUMBER', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'v', 'q']])
H = pd.concat(H); PX = pd.concat(PX)
PX = PX[PX.CUSIP.isin(set(H.CUSIP))].groupby(['CUSIP', 'per']).px.agg(['median', 'size']).reset_index()
H = H.merge(C[['ACCESSION_NUMBER', 'CIK', 'FILINGMANAGER_NAME', 'PERIODOFREPORT']], on='ACCESSION_NUMBER')
pd.to_pickle({'h': H, 'px': PX}, OUT)
print(OUT, 'gestoras', H.CIK.nunique(), 'linhas', len(H), 'períodos', sorted(H.PERIODOFREPORT.unique())[-2:])
