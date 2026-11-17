# Entregas 13F-HR mais recentes (ainda fora dos arquivos trimestrais da SEC), direto do EDGAR, para as gestoras de gestoras.txt.
# Uso: python edgar_q.py 2026-09-30 <saída .pkl>
import sys, json, time, re, requests, pandas as pd, numpy as np, xml.etree.ElementTree as ET
PER, OUT = sys.argv[1:3]
S = requests.Session(); S.headers['User-Agent'] = 'Navegando-Research/1.0 research@example.org'
def get(u):
    for k in range(4):
        r = S.get(u, timeout=60); time.sleep(0.15)
        if r.status_code == 200: return r
        time.sleep(2 + 3 * k)
    return None
CIKS = sorted({l.split('|')[0] for l in open('/home/user/work/us/gestoras.txt') if l.strip()})
rows = []; got = []
for cik in CIKS:
    r = get(f'https://data.sec.gov/submissions/CIK{cik}.json')
    if r is None: continue
    j = r.json(); f = j['filings']['recent']; nm = j.get('name', '')
    cand = [(f['filingDate'][k], f['accessionNumber'][k]) for k in range(len(f['form'])) if f['form'][k] == '13F-HR' and f['reportDate'][k] == PER]
    if not cand: continue
    fd, acc = sorted(cand)[-1]
    idx = get(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/index.json')
    if idx is None: continue
    xs = [it['name'] for it in idx.json()['directory']['item'] if it['name'].lower().endswith('.xml') and 'primary_doc' not in it['name'].lower()]
    if not xs: continue
    x = get(f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/{xs[0]}')
    if x is None: continue
    t = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', x.text); t = re.sub(r'\s[\w-]+:[\w-]+="[^"]*"', '', t); t = re.sub(r'<(\/?)\w+:', r'<\1', t)
    try: root = ET.fromstring(t.encode())
    except ET.ParseError as e: print('xml', cik, e); continue
    n0 = len(rows)
    for it in root.iter('infoTable'):
        g = lambda p: (it.findtext(p) or '').strip()
        if g('putCall') or g('shrsOrPrnAmt/sshPrnamtType') != 'SH': continue
        try: v = float(g('value')); q = float(g('shrsOrPrnAmt/sshPrnamt'))
        except ValueError: continue
        if v > 0 and q > 0: rows.append([acc, g('nameOfIssuer'), g('titleOfClass'), g('cusip').upper(), v, q, cik, nm, pd.Timestamp(PER).strftime('%d-%b-%Y').upper()])
    got.append((cik, nm[:30], fd, len(rows) - n0))
H = pd.DataFrame(rows, columns=['ACCESSION_NUMBER', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'v', 'q', 'CIK', 'FILINGMANAGER_NAME', 'PERIODOFREPORT'])
PX = H.assign(px=H.v / H.q).groupby('CUSIP').px.agg(['median', 'size']).reset_index().assign(per=H.PERIODOFREPORT.iloc[0])
pd.to_pickle({'h': H, 'px': PX}, OUT)
print('gestoras', len(got), 'linhas', len(H)); print(got[:10])
