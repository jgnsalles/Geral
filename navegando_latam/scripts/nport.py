# N-PORT (SEC): ações de empresas da América Latina nas carteiras dos fundos registrados nos EUA.
# Uso: python nport.py <zip trimestral> <saída .pkl>
import zipfile, sys, pandas as pd
Z, OUT = sys.argv[1], sys.argv[2]
LAT = {'BR', 'MX', 'CL', 'PE', 'CO', 'AR', 'UY', 'PA'}
z = zipfile.ZipFile(Z)
def rd(n, cols=None, chunks=False):
    return pd.read_csv(z.open(n), sep='\t', dtype=str, quoting=3, on_bad_lines='skip', usecols=cols, chunksize=500000 if chunks else None)
H = []
for c in rd('FUND_REPORTED_HOLDING.tsv', ['ACCESSION_NUMBER', 'HOLDING_ID', 'ISSUER_NAME', 'ISSUER_LEI', 'ISSUER_TITLE', 'ISSUER_CUSIP', 'BALANCE', 'UNIT', 'CURRENCY_VALUE', 'EXCHANGE_RATE', 'PERCENTAGE', 'PAYOFF_PROFILE', 'ASSET_CAT', 'INVESTMENT_COUNTRY'], True):
    c = c[c.INVESTMENT_COUNTRY.isin(LAT) & (c.ASSET_CAT == 'EC') & (c.PAYOFF_PROFILE != 'Short')]
    H.append(c)
H = pd.concat(H)
ids = set(H.HOLDING_ID)
I = []
for c in rd('IDENTIFIERS.tsv', ['HOLDING_ID', 'IDENTIFIER_ISIN', 'IDENTIFIER_TICKER'], True):
    I.append(c[c.HOLDING_ID.isin(ids)])
I = pd.concat(I).groupby('HOLDING_ID').agg(isin=('IDENTIFIER_ISIN', 'first'), ticker=('IDENTIFIER_TICKER', 'first'))
H = H.join(I, on='HOLDING_ID')
S = rd('SUBMISSION.tsv', ['ACCESSION_NUMBER', 'REPORT_DATE', 'FILING_DATE', 'IS_LAST_FILING'])
R = rd('REGISTRANT.tsv', ['ACCESSION_NUMBER', 'REGISTRANT_NAME', 'CIK'])
F = rd('FUND_REPORTED_INFO.tsv', ['ACCESSION_NUMBER', 'SERIES_NAME', 'SERIES_ID', 'TOTAL_ASSETS', 'NET_ASSETS'])
H = H.merge(S, on='ACCESSION_NUMBER', how='left').merge(R, on='ACCESSION_NUMBER', how='left').merge(F, on='ACCESSION_NUMBER', how='left')
for c in ['BALANCE', 'CURRENCY_VALUE', 'EXCHANGE_RATE', 'PERCENTAGE', 'NET_ASSETS', 'TOTAL_ASSETS']: H[c] = pd.to_numeric(H[c], errors='coerce')
H['usd'] = H.PERCENTAGE / 100 * H.NET_ASSETS            # valor em US$ (PERCENTAGE = % do patrimônio)
H.to_pickle(OUT)
print(len(H), H.REPORT_DATE.str[:7].value_counts().sort_index().tail(6).to_dict(), round(H.usd.sum() / 1e9, 1), 'US$ bi')
print(H.groupby('INVESTMENT_COUNTRY').usd.sum().div(1e9).round(1).sort_values(ascending=False).to_dict())
