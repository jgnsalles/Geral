"""Coleta demonstrativos anuais (10-K/20-F/40-F) via API XBRL da SEC (data.sec.gov) e salva um resumo por ticker.
Uso: python3 fetch_edgar.py data/wise_snapshot.csv [YYYY-MM-DD]"""
import sys, json, time, datetime as dt, pathlib, re
import pandas as pd, requests

UA = {'User-Agent': 'PriceTracker-Research/1.0'}
CONCEPTS = {
    'op_income': ['OperatingIncomeLoss', 'ProfitLossFromOperatingActivities'],
    'pretax': ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
               'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments',
               'ProfitLossBeforeTax'],
    'tax': ['IncomeTaxExpenseBenefit', 'IncomeTaxExpenseContinuingOperations'],
    'net_income': ['NetIncomeLoss', 'ProfitLossAttributableToOwnersOfParent', 'ProfitLoss'],
    'eps_diluted': ['EarningsPerShareDiluted', 'DilutedEarningsLossPerShare'],
    'assets': ['Assets'],
    'cur_liab': ['LiabilitiesCurrent', 'CurrentLiabilities'],
    'equity': ['StockholdersEquity', 'EquityAttributableToOwnersOfParent',
               'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'lt_debt': ['LongTermDebt', 'LongTermDebtNoncurrent', 'NoncurrentPortionOfNoncurrentBorrowings'],
    'cash': ['CashAndCashEquivalentsAtCarryingValue', 'CashAndCashEquivalents'],
}
FORMS = {'10-K', '10-K/A', '20-F', '20-F/A', '40-F', '40-F/A'}

def cik_for(tk):
    q = tk.split('.')[0]
    r = requests.get('https://efts.sec.gov/LATEST/search-index', params={'keysTyped': q}, headers=UA, timeout=30)
    for h in r.json().get('hits', {}).get('hits', []):
        ent = h['_source'].get('entity', '')
        m = re.search(r'\(([^)]*)\)\s*$', ent)
        if m and q.upper() in [x.strip().upper() for x in m.group(1).split(',')]:
            return h['_id'].zfill(10)
    return None

def annual(facts, names):
    """Escolhe o primeiro conceito disponivel; devolve {ano_fiscal_fim: valor} usando o ultimo arquivamento."""
    for tax in ('us-gaap', 'ifrs-full'):
        for n in names:
            node = facts.get(tax, {}).get(n)
            if not node: continue
            for unit, vals in node['units'].items():
                out = {}
                for x in vals:
                    if x.get('form') not in FORMS: continue
                    if 'start' in x:
                        days = (pd.Timestamp(x['end']) - pd.Timestamp(x['start'])).days
                        if not 350 <= days <= 380: continue
                    key = x['end']
                    if key not in out or x['filed'] > out[key][1]:
                        out[key] = (x['val'], x['filed'])
                if out:
                    return {'concept': f'{tax}:{n}', 'unit': unit, 'values': {k: v[0] for k, v in sorted(out.items())}}
    return None

def main(src, day=None):
    day = day or dt.date.today().isoformat()
    out = pathlib.Path('data/raw/edgar') / day
    out.mkdir(parents=True, exist_ok=True)
    tickers = pd.read_csv(src).ticker.tolist()
    for tk in tickers:
        f = out / f'{tk}.json'
        if f.exists(): continue
        if '.' in tk and not tk.endswith('.TO'):
            continue  # listagem fora dos EUA: sem arquivamento na SEC
        try:
            cik = cik_for(tk); time.sleep(0.15)
            if not cik:
                print(tk, 'sem CIK'); continue
            r = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json', headers=UA, timeout=60)
            if r.status_code != 200:
                print(tk, 'http', r.status_code); continue
            facts = r.json()['facts']
            res = {'ticker': tk, 'cik': cik, 'data': {k: annual(facts, v) for k, v in CONCEPTS.items()}}
            f.write_text(json.dumps(res, indent=1))
        except Exception as e:
            print(tk, 'erro', repr(e)[:120])
        time.sleep(0.15)
    print('ok', len(list(out.glob('*.json'))))

if __name__ == '__main__':
    main(*sys.argv[1:])
