# N-PORT: fundos dos EUA focados em América Latina (≥ 50% do patrimônio em ações da região).
# Salva, por trimestre: carteira completa desses fundos, retorno mensal das cotas e fluxos.
# Uso: python nport_fundos.py <zip trimestral> <saída .pkl>
import zipfile, sys, pandas as pd, numpy as np
Z, OUT = sys.argv[1], sys.argv[2]
LAT = {'BR', 'MX', 'CL', 'PE', 'CO', 'AR', 'UY', 'PA'}
z = zipfile.ZipFile(Z)
def rd(n, cols=None, chunks=False):
    return pd.read_csv(z.open(n), sep='\t', dtype=str, quoting=3, on_bad_lines='skip', usecols=cols, chunksize=500000 if chunks else None)
HC = ['ACCESSION_NUMBER', 'HOLDING_ID', 'ISSUER_NAME', 'ISSUER_LEI', 'ISSUER_TITLE', 'ISSUER_CUSIP', 'BALANCE', 'UNIT', 'CURRENCY_CODE', 'CURRENCY_VALUE', 'PERCENTAGE', 'PAYOFF_PROFILE', 'ASSET_CAT', 'ISSUER_TYPE', 'INVESTMENT_COUNTRY']
lat = {}
for c in rd('FUND_REPORTED_HOLDING.tsv', ['ACCESSION_NUMBER', 'PERCENTAGE', 'ASSET_CAT', 'INVESTMENT_COUNTRY', 'PAYOFF_PROFILE'], True):
    c = c[c.INVESTMENT_COUNTRY.isin(LAT) & c.ASSET_CAT.isin(['EC', 'EP']) & (c.PAYOFF_PROFILE != 'Short')]
    for a, v in pd.to_numeric(c.PERCENTAGE, errors='coerce').groupby(c.ACCESSION_NUMBER).sum().items(): lat[a] = lat.get(a, 0) + v
sel = {a for a, v in lat.items() if v >= 50}
H = pd.concat([c[c.ACCESSION_NUMBER.isin(sel)] for c in rd('FUND_REPORTED_HOLDING.tsv', HC, True)])
ids = set(H.HOLDING_ID)
I = pd.concat([c[c.HOLDING_ID.isin(ids)] for c in rd('IDENTIFIERS.tsv', ['HOLDING_ID', 'IDENTIFIER_ISIN', 'IDENTIFIER_TICKER'], True)])
I = I.groupby('HOLDING_ID').agg(isin=('IDENTIFIER_ISIN', 'first'), ticker=('IDENTIFIER_TICKER', 'first'))
H = H.join(I, on='HOLDING_ID')
for c in ['BALANCE', 'CURRENCY_VALUE', 'PERCENTAGE']: H[c] = pd.to_numeric(H[c], errors='coerce')
S = rd('SUBMISSION.tsv', ['ACCESSION_NUMBER', 'REPORT_DATE', 'FILING_DATE'])
R = rd('REGISTRANT.tsv', ['ACCESSION_NUMBER', 'REGISTRANT_NAME'])
F = rd('FUND_REPORTED_INFO.tsv', ['ACCESSION_NUMBER', 'SERIES_NAME', 'SERIES_ID', 'NET_ASSETS'] + [f'{k}_MON{m}' for k in ('SALES_FLOW', 'REINVESTMENT_FLOW', 'REDEMPTION_FLOW') for m in (1, 2, 3)])
T = rd('MONTHLY_TOTAL_RETURN.tsv', ['ACCESSION_NUMBER', 'CLASS_ID', 'MONTHLY_TOTAL_RETURN1', 'MONTHLY_TOTAL_RETURN2', 'MONTHLY_TOTAL_RETURN3'])
for c in T.columns[2:]: T[c] = pd.to_numeric(T[c], errors='coerce')
T = T.groupby('ACCESSION_NUMBER')[list(T.columns[2:])].median()      # mediana entre as classes de cotas
INFO = F.merge(S, on='ACCESSION_NUMBER').merge(R, on='ACCESSION_NUMBER', how='left').join(T, on='ACCESSION_NUMBER')
INFO['lat_pct'] = INFO.ACCESSION_NUMBER.map(lat).fillna(0)
INFO = INFO[INFO.lat_pct >= 50]
pd.to_pickle({'h': H.merge(S, on='ACCESSION_NUMBER'), 'info': INFO}, OUT)
print(OUT, 'fundos', INFO.SERIES_ID.nunique(), 'carteiras', len(INFO), 'posições', len(H))
