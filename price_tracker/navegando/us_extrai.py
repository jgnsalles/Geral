"""Navegando US robustecido, passo 1: posições (com quantidade) dos 100 maiores gestores ativos de cada trimestre que não estão na lista original.
Fontes: SEC Form 13F Data Sets (até jun/2026) e, para set/2026, os 13F-HR de cada gestor no EDGAR. Saída: navegando/us_added_pos.csv.gz
Uso: python3 navegando/us_extrai.py"""
import io, re, time, zipfile, pathlib, urllib.request, json
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; R = ROOT.parent / 'relatorio'
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}
def get(url):
    for k in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
        except Exception as e: err = e; time.sleep(4 * (k + 1))
    raise err
T = pd.read_csv(R / 'top100_ativos_por_trimestre.csv')
T = T[~T.no_navegando_us]
F = pd.concat([pd.read_csv(f) for f in sorted((R / 'data_13f_sec').glob('filers_*.csv.gz'))])
F['per'] = pd.to_datetime(F.per).dt.strftime('%Y-%m'); F['lim'] = pd.to_datetime(F.per) + pd.offsets.QuarterEnd(1)
F = F.sort_values('fd').drop_duplicates(['CIK', 'per'], keep='last')
need = T.merge(F, left_on=['cik', 'trimestre'], right_on=['CIK', 'per'])[['ACCESSION_NUMBER', 'cik', 'trimestre', 'fix']]
acc = set(need.ACCESSION_NUMBER); fixm = need.set_index('ACCESSION_NUMBER').fix.fillna(1)
fdm = F.set_index('ACCESSION_NUMBER').fd
print('acessos', len(acc), flush=True)
page = get('https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets').decode('utf-8', 'ignore')
links = sorted(set(re.findall(r'href="(/files/[^"]*form13f\.zip)"', page)))
def key(u):
    m = re.search(r'(\d{4})q(\d)_form13f', u)
    if m: return (int(m.group(1)), (int(m.group(2)) - 1) * 3 + 1)
    m = re.search(r'01([a-z]{3})(\d{4})-', u)
    return (int(m.group(2)), ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].index(m.group(1)) + 1)
out = []
for u in [x for x in links if key(x) >= (2016, 4)]:
    z = zipfile.ZipFile(io.BytesIO(get('https://www.sec.gov' + u))); nmap = {x.split('/')[-1].upper(): x for x in z.namelist()}
    it = pd.read_csv(z.open(nmap['INFOTABLE.TSV']), sep='\t', usecols=['ACCESSION_NUMBER', 'NAMEOFISSUER', 'CUSIP', 'VALUE', 'SSHPRNAMT', 'SSHPRNAMTTYPE', 'PUTCALL'], dtype=str, quoting=3, on_bad_lines='skip')
    it = it[it.ACCESSION_NUMBER.isin(acc) & it.PUTCALL.isna() & (it.SSHPRNAMTTYPE == 'SH')].copy()
    if len(it): out.append(it.drop(columns=['SSHPRNAMTTYPE', 'PUTCALL']))
    print(u.split('/')[-1], len(it), flush=True); time.sleep(1)
P = pd.concat(out)
P['v'] = pd.to_numeric(P.VALUE, errors='coerce'); P['sh'] = pd.to_numeric(P.SSHPRNAMT, errors='coerce')
P['v'] = np.where(P.ACCESSION_NUMBER.map(fdm).astype(str) < '2023-01-03', P.v * 1000, P.v) * P.ACCESSION_NUMBER.map(fixm).fillna(1)
P['CUSIP'] = P.CUSIP.str.strip().str.upper().str.zfill(9)
P = P.groupby(['ACCESSION_NUMBER', 'CUSIP']).agg(v=('v', 'sum'), sh=('sh', 'sum'), nome=('NAMEOFISSUER', 'first')).reset_index()
P = P.merge(need[['ACCESSION_NUMBER', 'cik', 'trimestre']], on='ACCESSION_NUMBER')
# set/2026: 13F-HR de cada gestor que estava entre os 100 em jun/2026
last = T[T.trimestre == T.trimestre.max()]
rows = []
for cik in last.cik:
    try:
        sub = json.loads(get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'))['filings']['recent']
        ix = [i for i, (f, r) in enumerate(zip(sub['form'], sub['reportDate'])) if f == '13F-HR' and r == '2026-09-30']
        if not ix: continue
        a = sub['accessionNumber'][ix[0]]; idx = json.loads(get(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a.replace("-", "")}/index.json'))
        xs = [x['name'] for x in idx['directory']['item'] if x['name'].lower().endswith('.xml') and 'primary_doc' not in x['name'].lower()]
        if not xs: continue
        xml = get(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a.replace("-", "")}/{xs[0]}').decode('utf-8', 'ignore')
        xml = re.sub(r'<(/?)[A-Za-z0-9]+:', r'<\1', xml)
        for blk in re.findall(r'<infoTable>(.*?)</infoTable>', xml, re.S):
            g = lambda t: (re.search(rf'<{t}>(.*?)</{t}>', blk, re.S) or [None, None])[1]
            if g('putCall') or (g('sshPrnamtType') or 'SH').strip() != 'SH': continue
            rows.append(dict(ACCESSION_NUMBER=a, CUSIP=g('cusip').strip().upper().zfill(9), v=float(g('value')), sh=float(g('sshPrnamt')), nome=g('nameOfIssuer'), cik=cik, trimestre='2026-09'))
        time.sleep(.3)
    except Exception as e:
        print('edgar', cik, repr(e)[:80])
if rows:
    Q = pd.DataFrame(rows).groupby(['ACCESSION_NUMBER', 'CUSIP', 'cik', 'trimestre']).agg(v=('v', 'sum'), sh=('sh', 'sum'), nome=('nome', 'first')).reset_index()
    P = pd.concat([P, Q], ignore_index=True)
P.to_csv(ROOT / 'us_added_pos.csv.gz', index=False)
print('ok', len(P), P.groupby('trimestre').cik.nunique().tail(3).to_dict())
