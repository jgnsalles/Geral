"""Baixa companyfacts da SEC e guarda, por conceito, TODOS os fatos anuais com data de arquivamento (point-in-time).
Saida: backtest/data/pit/<ticker>.json.gz"""
import sys, json, gzip, time, pathlib
import pandas as pd, requests
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from fetch_edgar import CONCEPTS, FORMS

UA = {'User-Agent': 'PriceTracker-Research/1.0'}
D = pathlib.Path(__file__).parent / 'data'

def compact(facts):
    out = {}
    for key, names in CONCEPTS.items():
        cands = []
        for tax in ('us-gaap', 'ifrs-full'):
            for n in names:
                node = facts.get(tax, {}).get(n)
                if not node: continue
                for unit, vals in node['units'].items():
                    rows = []
                    for x in vals:
                        if x.get('form') not in FORMS: continue
                        if 'start' in x:
                            days = (pd.Timestamp(x['end']) - pd.Timestamp(x['start'])).days
                            if not 350 <= days <= 380: continue
                        rows.append([x['end'], x['val'], x['filed']])
                    if rows: cands.append({'concept': f'{tax}:{n}', 'unit': unit, 'rows': rows})
        out[key] = cands
    return out

def main():
    u = pd.read_csv(D / 'universe.csv')
    (D / 'pit').mkdir(exist_ok=True)
    for i, r in u.iterrows():
        f = D / 'pit' / f'{r.ticker}.json.gz'
        if f.exists(): continue
        for attempt in range(3):
            try:
                resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(r.cik):010d}.json', headers=UA, timeout=90)
                if resp.status_code == 404: print(r.ticker, '404'); break
                resp.raise_for_status()
                with gzip.open(f, 'wt') as g:
                    json.dump(compact(resp.json()['facts']), g)
                break
            except Exception as e:
                print(r.ticker, 'erro', repr(e)[:100]); time.sleep(3 * (attempt + 1))
        time.sleep(0.12)
        if i % 50 == 0: print(i, r.ticker, flush=True)
    print('ok', len(list((D / 'pit').glob('*.gz'))))

if __name__ == '__main__':
    main()
