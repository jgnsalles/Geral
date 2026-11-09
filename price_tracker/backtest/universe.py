"""Monta o universo do backtest: S&P 500 atual (Wikipedia) + as acoes da planilha com arquivamento na SEC.
Saida: backtest/data/universe.csv (ticker Yahoo, CIK, financeira?, origem)."""
import io, json, glob, pathlib
import pandas as pd, requests
import sys; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from engine import HEALTH_INSURERS  # noqa: E402

UA = {'User-Agent': 'PriceTracker-Research/1.0'}
OUT = pathlib.Path(__file__).parent / 'data'

def main():
    OUT.mkdir(exist_ok=True)
    r = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=UA, timeout=30)
    sp = pd.read_html(io.StringIO(r.text))[0]
    sp = pd.DataFrame({'ticker': sp.Symbol.str.replace('.', '-', regex=False), 'cik': sp.CIK.astype(int),
                       'fin': sp['GICS Sector'].eq('Financials'), 'name': sp.Security, 'src': 'sp500'})
    w = pd.read_csv(pathlib.Path(__file__).parent.parent / 'data/wise_snapshot.csv').drop_duplicates('ticker')
    rows = []
    for f in glob.glob(str(pathlib.Path(__file__).parent.parent / 'data/raw/edgar/*/*.json')):
        d = json.load(open(f))
        tk = d['ticker']
        s = w[w.ticker == tk]
        rows.append({'ticker': tk, 'cik': int(d['cik']), 'fin': bool((s.sector == 'Financial Services').any()),
                     'name': s.name.iloc[0] if len(s) else tk, 'src': 'planilha'})
    pl = pd.DataFrame(rows)
    u = pd.concat([pl, sp[~sp.ticker.isin(pl.ticker)]], ignore_index=True)
    u['src'] = u.apply(lambda r: 'ambos' if r.src == 'planilha' and r.ticker in set(sp.ticker) else r.src, axis=1)
    u.loc[u.ticker.isin(HEALTH_INSURERS), 'fin'] = True  # seguradoras de saude: ROE (decisao do usuario 2026-11-10)
    u = u.drop_duplicates('cik')  # classes de acao duplicadas (GOOG/GOOGL, FOX/FOXA...) ficam com a primeira
    u.to_csv(OUT / 'universe.csv', index=False)
    print(len(u), u.src.value_counts().to_dict(), 'financeiras', int(u.fin.sum()))

if __name__ == '__main__':
    main()
