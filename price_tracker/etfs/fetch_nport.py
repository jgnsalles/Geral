"""Baixa a composicao dos ETFs (N-PORT da SEC) e mapeia CUSIP -> ticker (OpenFIGI). Saidas: etfs/data/holdings.csv, etfs/data/cusip_map.csv"""
import re, time, json, pathlib
import pandas as pd, requests
D = pathlib.Path(__file__).parent / 'data'; D.mkdir(exist_ok=True)
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}
SERIES = {'RSP': 'S000060812', 'QUAL': 'S000041444', 'SPHQ': 'S000003049', 'JQUA': 'S000059315', 'MTUM': 'S000040316', 'VLUE': 'S000040205',
          'USMV': 'S000031838', 'IWF': 'S000004346', 'IWD': 'S000004345', 'VUG': 'S000002842', 'VTV': 'S000002840', 'SPYG': 'S000006984',
          'IJH': 'S000004307', 'IJR': 'S000004313', 'MOAT': 'S000036713', 'SCHD': 'S000034163', 'COWZ': 'S000055466'}


def get(url, tries=4):
    for k in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 200: return r.text
        except Exception: pass
        time.sleep(2 * (k + 1))
    return None


def fetch():
    out = D / 'holdings.csv'
    rows = []
    for etf, sid in SERIES.items():
        atom = get(f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={sid}&type=NPORT-P&dateb=&owner=include&count=100&output=atom')
        if not atom: print(etf, 'sem lista'); continue
        fil = re.findall(r'<filing-date>([^<]*)</filing-date>.*?<filing-href>([^<]*)</filing-href>', atom, re.S)
        if not fil:
            hrefs = re.findall(r'<filing-href>([^<]*)', atom); dts = re.findall(r'<filing-date>([^<]*)', atom); fil = list(zip(dts, hrefs))
        for fdate, href in fil:
            base = href.rsplit('/', 1)[0]
            x = get(base + '/primary_doc.xml'); time.sleep(0.12)
            if not x: continue
            ser = re.search(r'<seriesId>([^<]*)', x)
            if ser and ser.group(1) != sid: continue  # arquivo de outra serie do mesmo trust
            end = re.search(r'<repPdDate>([^<]*)', x).group(1)
            for blk in re.findall(r'<invstOrSec>(.*?)</invstOrSec>', x, re.S):
                g = lambda tag: (re.search(f'<{tag}>([^<]*)', blk) or [None, None])[1]
                if g('assetCat') != 'EC': continue
                rows.append(dict(etf=etf, filed=fdate, end=end, cusip=g('cusip'), name=g('name'), pct=float(g('pctVal') or 0), val=float(g('valUSD') or 0)))
        print(etf, len(fil), 'arquivos', flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)


def figi():
    h = pd.read_csv(D / 'holdings.csv'); cus = sorted(set(h.cusip.dropna()) - {'N/A', '000000000'})
    mp = D / 'cusip_map.csv'; done = pd.read_csv(mp) if mp.exists() else pd.DataFrame(columns=['cusip', 'ticker'])
    todo = [c for c in cus if c not in set(done.cusip)]; out = []
    for i in range(0, len(todo), 10):
        b = todo[i:i + 10]
        try:
            r = requests.post('https://api.openfigi.com/v3/mapping', json=[{'idType': 'ID_CUSIP', 'idValue': c} for c in b], timeout=60)
            if r.status_code == 429: time.sleep(30); r = requests.post('https://api.openfigi.com/v3/mapping', json=[{'idType': 'ID_CUSIP', 'idValue': c} for c in b], timeout=60)
            for c, res in zip(b, r.json()):
                d = res.get('data') or []
                us = [x for x in d if x.get('exchCode') == 'US'] or d
                out.append(dict(cusip=c, ticker=us[0]['ticker'].replace('/', '-') if us else None))
        except Exception as e: print('erro figi', repr(e)[:80])
        time.sleep(2.6)
        if i % 500 == 0: print('figi', i, len(todo), flush=True)
    pd.concat([done, pd.DataFrame(out)]).to_csv(mp, index=False)


if __name__ == '__main__':
    import sys
    if 'figi' not in sys.argv: fetch()
    figi()
