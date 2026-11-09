"""Segunda rodada da Fase 2: recupera tickers renomeados (ticker novo) e empresas com preco no Yahoo mas sem CIK (busca pelo nome)."""
import sys, time, json, gzip, pathlib, re
import pandas as pd, requests, yfinance as yf
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from fetch_pit import compact  # noqa: E402
from extend_universe import cik_for, UA  # noqa: E402
from pit_universe import RENAMES, SAME_COMPANY  # noqa: E402

D = ROOT / 'data'


def cik_by_name(name):
    if not name: return None, None
    q = re.sub(r'[,.]|\b(Inc|Corp|Corporation|Company|Co|Ltd|plc|Holdings|Group|The)\b', ' ', name).strip()
    r = requests.get('https://efts.sec.gov/LATEST/search-index', params={'keysTyped': q}, headers=UA, timeout=30)
    hits = r.json().get('hits', {}).get('hits', [])
    return (int(hits[0]['_id']), hits[0]['_source'].get('entity')) if hits else (None, None)


def fetch(cik, tk):
    sub = requests.get(f'https://data.sec.gov/submissions/CIK{cik:010d}.json', headers=UA, timeout=60).json(); time.sleep(0.12)
    sic = int(sub.get('sic') or 0)
    f = D / 'pit' / f'{tk}.json.gz'
    if not f.exists():
        resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json', headers=UA, timeout=90); time.sleep(0.12)
        if resp.status_code == 200:
            with gzip.open(f, 'wt') as g: json.dump(compact(resp.json()['facts']), g)
    return sub.get('name'), sic, f.exists()


def main():
    u = pd.read_csv(D / 'universe.csv'); x = pd.read_csv(D / 'universe_pit_extra.csv')
    have = set(u.ticker) | set(x[x.sec_ok & x.price_from.notna()].ticker)
    rows = []
    # (1) tickers novos de empresas renomeadas
    for old in sorted(SAME_COMPANY):
        new = RENAMES[old].replace('.', '-')
        if new in have or new in [r['ticker'] for r in rows]: continue
        cik, _ = cik_for(new); time.sleep(0.12)
        if cik:
            name, sic, ok = fetch(cik, new)
            rows.append(dict(ticker=new, hist_ticker=old, cik=cik, sec_name=name, sic=sic, sec_ok=ok))
    # (2) com preco no Yahoo, sem CIK: busca pelo nome
    cand = x[x.price_from.notna() & ~x.sec_ok]
    for t in cand.ticker:
        try:
            name = yf.Ticker(t).info.get('longName')
        except Exception:
            name = None
        cik, ent = cik_by_name(name); time.sleep(0.2)
        if cik:
            nm, sic, ok = fetch(cik, t)
            rows.append(dict(ticker=t, hist_ticker=t, cik=cik, sec_name=nm, sic=sic, sec_ok=ok, yahoo_name=name))
        print(t, name, '->', ent, flush=True)
    y = pd.DataFrame(rows)
    y['fin'] = y.sic.between(6000, 6499) | (y.sic.between(6700, 6799) & (y.sic != 6798))
    tks = [t for t in y.ticker if t not in set(x.ticker) or True]
    df = yf.download(tks, start='2005-01-01', end='2026-11-08', auto_adjust=False, actions=True, progress=False, threads=True)
    for field in ('Close', 'Adj Close', 'Dividends', 'Stock Splits'):
        old = pd.read_csv(D / f"prices_pit_{field.replace(' ', '_').lower()}.csv.gz", index_col=0, parse_dates=True)
        p = df[field]; p = p.loc[:, ~p.columns.duplicated()]
        old = old.drop(columns=[c for c in p.columns if c in old.columns]).join(p, how='outer')
        old.to_csv(D / f"prices_pit_{field.replace(' ', '_').lower()}.csv.gz")
    first = df['Close'].apply(lambda s: s.first_valid_index())
    y['price_from'] = y.ticker.map(first); y['price_to'] = y.ticker.map(df['Close'].apply(lambda s: s.last_valid_index()))
    x = pd.concat([x[~x.ticker.isin(y.ticker)], y], ignore_index=True)
    x.to_csv(D / 'universe_pit_extra.csv', index=False)
    print('recuperados:', int((y.sec_ok & y.price_from.notna()).sum()), 'de', len(y))


if __name__ == '__main__':
    main()
