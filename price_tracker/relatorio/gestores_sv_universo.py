"""Ramo D, parte 1: gestores point-in-time sem viés (todos os 13F da SEC) e contagem de gestores por emissor (CUSIP de 6 dígitos).
Entrada: relatorio/data_13f_sec/ (f13_sec.py), relatorio/data_13f/posicoes.csv.gz (Navegando US) e a meta dos fundos do artefato (CIKs).
Saídas (pequenas, versionadas): data_gestores_sv/contagem.csv.gz (período, cusip6, n250, nnav, nrob, valor), data_gestores_sv/gestores_250.csv.gz,
relatorio/top100_ativos_por_trimestre.csv, data_gestores_sv/cusip_map.csv. Uso: python3 relatorio/gestores_sv_universo.py <fundos_meta.json>"""
import sys, re, json, time, glob, pathlib
import numpy as np, pandas as pd, requests
ROOT = pathlib.Path(__file__).parent; S = ROOT / 'data_13f_sec'; O = ROOT / 'data_gestores_sv'; O.mkdir(exist_ok=True)
meta = json.load(open(sys.argv[1]))
NAV_CIK = {int(c) for f in meta.values() for c in (f.get('ciks') or []) if str(c).strip().isdigit()}
EXCL = re.compile(r'VANGUARD|BLACKROCK|STATE STREET|GEODE|NORTHERN TRUST|FMR\b|FIDELITY MANAGEMENT TRUST|JPMORGAN|J\.P\. MORGAN|GOLDMAN|MORGAN STANLEY|'
                  r'BANK OF AMERICA|MERRILL|WELLS FARGO|\bUBS\b|CREDIT SUISSE|DEUTSCHE|BARCLAYS|BNP|CITIGROUP|CITIBANK|ROYAL BANK|\bRBC\b|TORONTO.DOMINION|'
                  r'\bTD\b|BANK OF MONTREAL|\bBMO\b|NOMURA|MIZUHO|MITSUBISHI|SUMITOMO|NORGES|CANADA PENSION|\bCPP\b|PUBLIC EMPLOYEES|TEACHERS|RETIREMENT SYSTEM|'
                  r'PENSION|\bBANK\b|BANCORP|BANCO|TRUST CO|TRUST COMPANY|INSURANCE|ASSURANCE|LIFE |MUTUAL OF|SOVEREIGN|INVESTMENT CORP OF|GIC |TEMASEK|'
                  r'ABU DHABI|KUWAIT|SAUDI|QATAR|CHARLES SCHWAB|EDWARD JONES|RAYMOND JAMES|LPL FINANCIAL|AMERIPRISE|STIFEL|JANNEY|BAIRD|'
                  r'DIMENSIONAL|INVESCO|NUVEEN|TIAA|PRINCIPAL FINANCIAL|PRUDENTIAL|METLIFE|ALLIANZ|AXA |AMUNDI|LEGAL & GENERAL|SCHRODER|ABERDEEN|'
                  r'FRANKLIN RESOURCES|T\. ROWE|CAPITAL RESEARCH|CAPITAL WORLD|CAPITAL INTERNATIONAL|WELLINGTON MANAGEMENT|MANULIFE|SUN LIFE|'
                  r'RENAISSANCE TECH|TWO SIGMA|CITADEL|SUSQUEHANNA|JANE STREET|D\. E\. SHAW|DE SHAW|AQR|MILLENNIUM|HUDSON RIVER|VIRTU|TOWER RESEARCH|'
                  r'MARSHALL WACE|BALYASNY|POINT72|QUBE|WOLVERINE|OPTIVER|IMC |FLOW TRADERS|XTX|ARROWSTREET|ACADIAN|MAN GROUP|WORLD QUANT|WORLDQUANT', re.I)
F = pd.concat([pd.read_csv(f, dtype={'CIK': int}) for f in sorted(S.glob('filers_*.csv.gz'))], ignore_index=True)
F['per'] = pd.to_datetime(F.per); F['fd'] = pd.to_datetime(F.fd)
F = F[F.per >= '2016-03-31']
F['lim'] = F.per + pd.offsets.QuarterEnd(1)          # o 13F do período p só vale para a carteira de p + 1 trimestre
F = F[F.fd <= F.lim].sort_values('fd').drop_duplicates(['CIK', 'per'], keep='last')
F['excl'] = F.FILINGMANAGER_NAME.fillna('').str.contains(EXCL)
F['ativo'] = F.npos.between(20, 400) & (F.top10 >= .25) & ~F.excl
F['in_nav'] = F.CIK.isin(NAV_CIK)
A = F[F.ativo].sort_values(['per', 'tot'], ascending=[True, False]).copy()
A['rank'] = A.groupby('per').cumcount() + 1
G250 = A[A['rank'] <= 250]
T100 = A[~A.in_nav].copy(); T100['rank2'] = T100.groupby('per').cumcount() + 1; T100 = T100[T100.rank2 <= 100]
G250[['per', 'CIK', 'FILINGMANAGER_NAME', 'tot', 'npos', 'top10', 'rank', 'in_nav']].to_csv(O / 'gestores_250.csv.gz', index=False)
top100 = A[A['rank'] <= 100][['per', 'CIK', 'FILINGMANAGER_NAME', 'tot', 'npos', 'top10', 'in_nav']].rename(columns={
    'per': 'trimestre', 'CIK': 'cik', 'FILINGMANAGER_NAME': 'nome', 'tot': 'valor_13f_usd', 'npos': 'n_posicoes', 'top10': 'peso_10_maiores', 'in_nav': 'no_navegando_us'})
top100['trimestre'] = top100.trimestre.dt.strftime('%Y-%m')
top100.to_csv(ROOT / 'top100_ativos_por_trimestre.csv', index=False)
print('validação: maiores gestores ativos (nomes) em 3 datas')
for p in ('2016-03-31', '2021-06-30', '2026-06-30'):
    x = A[A.per == p].head(25); print(p, '|', '; '.join(f"{n[:28]} ({v / 1e9:.0f}bi,{k})" for n, v, k in zip(x.FILINGMANAGER_NAME, x.tot, x.npos)))
print('excluídos por nome entre os 300 maiores com 20–400 posições (amostra):',
      F[F.npos.between(20, 400) & (F.top10 >= .25) & F.excl & (F.per == '2026-06-30')].sort_values('tot', ascending=False).FILINGMANAGER_NAME.head(25).tolist())
print('Navegando: CIKs', len(NAV_CIK), '| entre os 250 (média por trimestre):', G250.groupby('per').in_nav.sum().mean())

# posições dos selecionados
acc250 = set(G250.ACCESSION_NUMBER); acc100 = set(T100.ACCESSION_NUMBER)
P = []
for f in sorted(S.glob('pos_*.csv.gz')):
    x = pd.read_csv(f, dtype={'CUSIP': str}); x = x[x.ACCESSION_NUMBER.isin(acc250 | acc100) & (x.w >= .002)]
    P.append(x)
P = pd.concat(P, ignore_index=True); P['per'] = pd.to_datetime(P.per); P['cusip6'] = P.CUSIP.str[:6]
cnt250 = P[P.ACCESSION_NUMBER.isin(acc250)].groupby(['per', 'cusip6']).agg(n250=('CIK', 'nunique'), v250=('v', 'sum'))
cnt100 = P[P.ACCESSION_NUMBER.isin(acc100)].groupby(['per', 'cusip6']).CIK.nunique().rename('n100')
# Navegando (lista de hoje): posições do artefato, já >= 0,2%
nav = pd.read_csv(ROOT / 'data_13f' / 'posicoes.csv.gz', dtype={'cusip6': str})
nav['per'] = pd.to_datetime(nav.trimestre + '-01') + pd.offsets.MonthEnd(0)
cntnav = nav.groupby(['per', 'cusip6']).gestor.nunique().rename('nnav')
C = pd.concat([cnt250, cnt100, cntnav], axis=1).fillna(0).reset_index()
C['nrob'] = C.nnav + C.n100
C.to_csv(O / 'contagem.csv.gz', index=False)
print('contagem', C.shape, C.groupby('per').apply(lambda z: (z.n250 >= 5).sum(), include_groups=False).describe().round(0).to_dict())

# CUSIP de 9 dígitos mais comum por emissor, nome do emissor; tickers: Navegando (fc) -> OpenFIGI -> nome na SEC
need = set(C[(C.n250 >= 3) | (C.nrob >= 3)].cusip6)
c9 = P[P.cusip6.isin(need)].groupby(['cusip6', 'CUSIP']).v.sum().reset_index().sort_values('v', ascending=False).drop_duplicates('cusip6')
nm = P[P.cusip6.isin(need)].groupby('cusip6').nome.agg(lambda s: s.mode().iat[0] if len(s.mode()) else s.iat[0])
mp = c9.set_index('cusip6')[['CUSIP']].join(nm)
navtk = nav.dropna(subset=['ticker']).groupby('cusip6').ticker.agg(lambda s: s.mode().iat[0])
mp['ticker'] = mp.index.map(navtk); mp['fonte'] = np.where(mp.ticker.notna(), 'navegando', None)
mp['sectype'] = None; mp['exch'] = None
todo = [c for c in mp.index if pd.isna(mp.at[c, 'ticker'])] + list(mp.index[mp.ticker.notna()])   # OpenFIGI também para os do Navegando (tipo de papel)
hdr = {'Content-Type': 'application/json'}
for i in range(0, len(todo), 10):
    chunk = todo[i:i + 10]
    body = [{'idType': 'ID_CUSIP', 'idValue': mp.at[c, 'CUSIP'], 'exchCode': 'US'} for c in chunk]
    for k in range(4):
        r = requests.post('https://api.openfigi.com/v3/mapping', json=body, headers=hdr, timeout=60)
        if r.status_code == 429: time.sleep(20); continue
        break
    if r.status_code != 200: print('openfigi', r.status_code); time.sleep(5); continue
    for c, res in zip(chunk, r.json()):
        d = (res.get('data') or [None])[0]
        if not d: continue
        mp.at[c, 'sectype'] = d.get('securityType2') or d.get('securityType'); mp.at[c, 'exch'] = d.get('exchCode')
        if pd.isna(mp.at[c, 'ticker']) and d.get('ticker'):
            mp.at[c, 'ticker'] = d['ticker'].replace('/', '-').replace('.', '-'); mp.at[c, 'fonte'] = 'openfigi'
    time.sleep(2.6)    # sem chave: 25 requisições por minuto
# reserva por nome (SEC company_tickers.json)
ct = requests.get('https://www.sec.gov/files/company_tickers.json', headers={'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}, timeout=60).json()
norm = lambda s: re.sub(r'[^A-Z0-9 ]', '', str(s).upper()).replace(' INC', '').replace(' CORP', '').replace(' CO', '').replace(' LTD', '').replace(' PLC', '').strip()
byname = {norm(v['title']): v['ticker'].replace('.', '-') for v in ct.values()}
cur = {v['ticker'].replace('.', '-') for v in ct.values()}
for c in mp.index[mp.ticker.isna()]:
    t = byname.get(norm(mp.at[c, 'nome']))
    if t: mp.at[c, 'ticker'] = t; mp.at[c, 'fonte'] = 'nome_sec'
mp['listada_hoje'] = mp.ticker.isin(cur)
mp.reset_index().to_csv(O / 'cusip_map.csv', index=False)
print('mapa', len(mp), 'com ticker', mp.ticker.notna().mean().round(3), mp.fonte.value_counts().to_dict(), 'tipos', mp.sectype.value_counts().head(8).to_dict())
