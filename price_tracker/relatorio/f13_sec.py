"""Ramo D: lê os Form 13F Data Sets da SEC (todos os declarantes, inclusive os que fecharam depois) e salva, por trimestre:
 - resumo de TODOS os declarantes (cik, nome, período, nº de posições, valor, peso das 10 maiores) -> data_13f_sec/filers.csv.gz
 - posições (peso >= 0,1%) dos candidatos a gestor ativo (20 a 400 posições, 10 maiores >= 25%) -> data_13f_sec/pos_<período>.csv.gz
Baixa um zip por vez e apaga. Uso: python3 relatorio/f13_sec.py"""
import io, re, sys, time, zipfile, pathlib, urllib.request
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; OUT = ROOT / 'data_13f_sec'; OUT.mkdir(exist_ok=True)
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}
BASE = 'https://www.sec.gov'


def get(url):
    for k in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
        except Exception as e:
            time.sleep(5 * (k + 1)); err = e
    raise err


page = get(BASE + '/data-research/sec-markets-data/form-13f-data-sets').decode('utf-8', 'ignore')
links = sorted(set(re.findall(r'href="(/files/[^"]*form13f\.zip)"', page)))
def key(u):
    m = re.search(r'(\d{4})q(\d)_form13f', u)
    if m: return (int(m.group(1)), (int(m.group(2)) - 1) * 3 + 1)
    m = re.search(r'01([a-z]{3})(\d{4})-', u)
    return (int(m.group(2)), ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].index(m.group(1)) + 1)
links = [u for u in links if key(u) >= (2016, 4)]
print(len(links), 'zips')
done = OUT / 'feitos.txt'; seen = set(done.read_text().split()) if done.exists() else set()
filers_all = []
for u in sorted(links, key=key):
    tag = u.split('/')[-1].replace('_form13f.zip', '')
    if tag in seen: continue
    z = zipfile.ZipFile(io.BytesIO(get(BASE + u)))
    rd = lambda n, cols: pd.read_csv(z.open(n), sep='\t', usecols=cols, dtype=str, quoting=3, on_bad_lines='skip')
    sub = rd('SUBMISSION.tsv', ['ACCESSION_NUMBER', 'FILING_DATE', 'SUBMISSIONTYPE', 'CIK', 'PERIODOFREPORT'])
    sub = sub[sub.SUBMISSIONTYPE == '13F-HR']
    cov = rd('COVERPAGE.tsv', ['ACCESSION_NUMBER', 'FILINGMANAGER_NAME', 'REPORTTYPE', 'ISAMENDMENT'])
    cov = cov[cov.REPORTTYPE.isin(['13F HOLDINGS REPORT', '13F COMBINATION REPORT'])]
    s = sub.merge(cov, on='ACCESSION_NUMBER')
    s['fd'] = pd.to_datetime(s.FILING_DATE, format='%d-%b-%Y'); s['per'] = pd.to_datetime(s.PERIODOFREPORT, format='%d-%b-%Y')
    it = rd('INFOTABLE.tsv', ['ACCESSION_NUMBER', 'NAMEOFISSUER', 'CUSIP', 'VALUE', 'SSHPRNAMT', 'SSHPRNAMTTYPE', 'PUTCALL'])
    it = it[it.ACCESSION_NUMBER.isin(set(s.ACCESSION_NUMBER)) & it.PUTCALL.isna() & (it.SSHPRNAMTTYPE == 'SH')]
    it['v'] = pd.to_numeric(it.VALUE, errors='coerce'); it['sh'] = pd.to_numeric(it.SSHPRNAMT, errors='coerce')
    it['CUSIP'] = it.CUSIP.str.strip().str.upper().str.zfill(9)
    it = it[it.v > 0]
    # unidade: até 02/01/2023 em milhares; depois em dólares
    fd = s.set_index('ACCESSION_NUMBER').fd
    it['v'] = np.where(it.ACCESSION_NUMBER.map(fd) < pd.Timestamp('2023-01-03'), it.v * 1000, it.v)
    # corrige declarante que errou a unidade: preço implícito ~1000x (ou 1/1000) da mediana do mesmo CUSIP
    it['px'] = it.v / it.sh.where(it.sh > 0)
    med = it.groupby('CUSIP').px.transform('median')
    ratio = (it.px / med).groupby(it.ACCESSION_NUMBER).median()
    fix = np.where(ratio > 300, 1 / 1000, np.where(ratio < 1 / 300, 1000, 1.0))
    it['v'] = it.v * it.ACCESSION_NUMBER.map(pd.Series(fix, index=ratio.index)).fillna(1)
    h = it.groupby(['ACCESSION_NUMBER', 'CUSIP']).agg(v=('v', 'sum'), nome=('NAMEOFISSUER', 'first')).reset_index()
    tot = h.groupby('ACCESSION_NUMBER').v.sum(); npos = h.groupby('ACCESSION_NUMBER').size()
    top10 = h.sort_values('v', ascending=False).groupby('ACCESSION_NUMBER').head(10).groupby('ACCESSION_NUMBER').v.sum() / tot
    s = s.set_index('ACCESSION_NUMBER'); s['tot'] = tot; s['npos'] = npos; s['top10'] = top10; s['fix'] = pd.Series(fix, index=ratio.index)
    s = s.dropna(subset=['tot']).reset_index()
    # um relatório por (CIK, período): o último arquivado
    s = s.sort_values('fd').drop_duplicates(['CIK', 'per'], keep='last')
    filers_all.append(s[['ACCESSION_NUMBER', 'CIK', 'FILINGMANAGER_NAME', 'per', 'fd', 'tot', 'npos', 'top10', 'fix']])
    cand = s[(s.npos.between(20, 400)) & (s.top10 >= .25)]
    h = h[h.ACCESSION_NUMBER.isin(set(cand.ACCESSION_NUMBER))].copy()
    h['w'] = h.v / h.ACCESSION_NUMBER.map(tot)
    h = h[h.w >= .001].merge(cand[['ACCESSION_NUMBER', 'CIK', 'per', 'fd']], on='ACCESSION_NUMBER')
    h.to_csv(OUT / f'pos_{tag}.csv.gz', index=False)
    pd.concat(filers_all).to_csv(OUT / f'filers_{tag}.csv.gz', index=False); filers_all = []
    seen.add(tag); done.write_text('\n'.join(sorted(seen)))
    print(tag, len(s), 'declarantes', len(cand), 'candidatos', len(h), 'posições', flush=True)
    del z, it, h
    time.sleep(1)
