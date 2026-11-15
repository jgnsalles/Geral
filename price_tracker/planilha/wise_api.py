"""Puxa os dados da Price Tracker v3 pela API do Wisesheets (poucas requisições: até 100 tickers por chamada).
A chave fica no ambiente (o proxy injeta o cabeçalho). Saída: planilha/wise_dados.json. Uso: python3 planilha/wise_api.py"""
import json, time, pathlib, sys
import requests
HERE = pathlib.Path(__file__).parent; BASE = 'https://api.wisesheets.io/v1'
H = {'Authorization': 'Bearer ' + __import__('os').environ.get('WISESHEETS_API_KEY', 'proxy-injected')}
METRICS = ['operating_income', 'pretax_income', 'income_tax_expense', 'net_income', 'eps_diluted', 'property_plant_equipment_net',
           'operating_lease_right_of_use_assets', 'goodwill', 'intangible_assets', 'long_term_investments', 'total_current_assets',
           'cash_and_cash_equivalents', 'short_term_investments', 'total_current_liabilities', 'short_term_debt', 'total_debt',
           'total_lease_obligations', 'total_stockholders_equity', 'minority_interest', 'capital_expenditures', 'depreciation_and_amortization',
           'acquisitions_net', 'income_from_equity_method_investments', 'dividends_per_share']
CALLS = 0


def get(path, params=None, tries=4):
    global CALLS
    for k in range(tries):
        r = requests.get(BASE + path, params=params, headers=H, timeout=120); CALLS += 1
        if r.status_code == 429: time.sleep(20 * (k + 1)); continue
        if r.status_code >= 500: time.sleep(5 * (k + 1)); continue
        return r
    return r


def main():
    tickers = json.load(open(HERE / 'tickers.json'))
    us = [t for t in tickers if '.' not in t and not t[0].isdigit()]  # a API cobre empresas da SEC
    out = {'fin': {}, 'price': {}, 'profile': {}}
    cache = HERE / 'wise_perfis.json'; prof = json.load(open(cache)) if cache.exists() else {}
    for i in range(0, len(us), 100):
        ch = us[i:i + 100]
        r = get('/financials/', {'tickers': ','.join(ch), 'metrics': ','.join(METRICS), 'period': 'last5y', 'frequency': 'annual', 'layout': 'long', 'include': 'none'})
        js = r.json(); print('financials', i, r.status_code, js.get('meta', {}).get('returned'), 'sem dados:', js.get('meta', {}).get('noData'), flush=True)
        for row in js.get('data', []):
            t = row['ticker']; out['fin'].setdefault(t, {}).setdefault(str(row['fiscalYear']), {})[row['metric']] = float(row['value']) if row.get('value') not in (None, '') else None
            out['fin'][t]['_name'] = row.get('companyName')
    for i in range(0, len(us), 25):
        ch = us[i:i + 25]
        r = get('/prices/live', {'tickers': ','.join(ch), 'fields': 'name,price,marketCap,sharesOutstanding,eps,pe'})
        js = r.json()
        for row in js.get('data', js if isinstance(js, list) else []):
            out['price'][row.get('ticker') or row.get('symbol')] = row
        print('prices', i, r.status_code, flush=True)
    for t in us:
        if t in prof: continue
        r = get(f'/companies/{t}')
        if r.status_code == 200:
            d = r.json(); d = d.get('data', d); prof[t] = {'sic': d.get('sic'), 'sicDescription': d.get('sicDescription'), 'name': d.get('name')}
        else: prof[t] = None
        time.sleep(0.35)
    json.dump(prof, open(cache, 'w'))
    out['profile'] = prof; out['tickers'] = tickers
    json.dump(out, open(HERE / 'wise_dados.json', 'w'))
    print('ok: requisicoes', CALLS, 'empresas com financeiros', len(out['fin']), 'precos', len(out['price']), 'perfis', sum(1 for v in prof.values() if v))


if __name__ == '__main__':
    main()
