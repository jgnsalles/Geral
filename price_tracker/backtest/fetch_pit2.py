"""Conceitos extras para o ROIC triangulado (2026-11-14): arrendamentos, investimentos, minoritarios, divida detalhada, capex, depreciacao,
aquisicoes, equivalencia patrimonial, intangiveis de vida indefinida, imobilizado de oleo e gas, aplicacoes de curto prazo.
Saida: backtest/data/pit2/<ticker>.json.gz (mesmo formato do pit). Uso: python3 backtest/fetch_pit2.py"""
import sys, json, gzip, time, pathlib
import pandas as pd, requests
D = pathlib.Path(__file__).parent / 'data'
UA = {'User-Agent': 'PriceTracker-Research research@pricetracker-research.org'}
FORMS = {'10-K', '10-K/A', '20-F', '20-F/A', '40-F', '40-F/A'}
CONCEPTS = {
    'ppe_og': ['OilAndGasPropertySuccessfulEffortMethodNet', 'OilAndGasPropertyFullCostMethodNet'],
    'intang_indef': ['IndefiniteLivedIntangibleAssetsExcludingGoodwill', 'IndefiniteLivedLicenseAgreements', 'IndefiniteLivedFranchiseRights', 'IndefiniteLivedTrademarks'],
    'intang_fin': ['FiniteLivedIntangibleAssetsNet'],
    'intang_tot': ['IntangibleAssetsNetExcludingGoodwill'],
    'intang_incl_gw': ['IntangibleAssetsNetIncludingGoodwill'],
    'st_inv': ['ShortTermInvestments', 'MarketableSecuritiesCurrent', 'AvailableForSaleSecuritiesDebtSecuritiesCurrent', 'AvailableForSaleSecuritiesCurrent'],
    'lt_inv': ['LongTermInvestments', 'EquityMethodInvestments', 'MarketableSecuritiesNoncurrent', 'AvailableForSaleSecuritiesDebtSecuritiesNoncurrent'],
    'eq_method': ['EquityMethodInvestments'],
    'rou': ['OperatingLeaseRightOfUseAsset'],
    'lease_liab': ['OperatingLeaseLiability'],
    'lease_liab_cur': ['OperatingLeaseLiabilityCurrent'],
    'lease_liab_nc': ['OperatingLeaseLiabilityNoncurrent'],
    'lease_rate': ['OperatingLeaseWeightedAverageDiscountRatePercent'],
    'fl_y1': ['OperatingLeasesFutureMinimumPaymentsDueCurrent'], 'fl_y2': ['OperatingLeasesFutureMinimumPaymentsDueInTwoYears'],
    'fl_y3': ['OperatingLeasesFutureMinimumPaymentsDueInThreeYears'], 'fl_y4': ['OperatingLeasesFutureMinimumPaymentsDueInFourYears'],
    'fl_y5': ['OperatingLeasesFutureMinimumPaymentsDueInFiveYears'], 'fl_after': ['OperatingLeasesFutureMinimumPaymentsDueThereafter'],
    'minority': ['MinorityInterest'],
    'ltd_tot': ['LongTermDebt', 'DebtLongtermAndShorttermCombinedAmount'],
    'ltd_nc': ['LongTermDebtNoncurrent', 'LongTermDebtAndCapitalLeaseObligations'],
    'ltd_cur': ['LongTermDebtCurrent', 'LongTermDebtAndCapitalLeaseObligationsCurrent'],
    'st_borr': ['ShortTermBorrowings', 'CommercialPaper'],
    'capex': ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets'],
    'da': ['DepreciationDepletionAndAmortization', 'DepreciationAndAmortization', 'DepreciationAmortizationAndAccretionNet'],
    'acq': ['PaymentsToAcquireBusinessesNetOfCashAcquired'],
    'eq_income': ['IncomeLossFromEquityMethodInvestments'],
    'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
}


def compact(facts):
    out = {}
    for key, names in CONCEPTS.items():
        cands = []
        for n in names:
            node = facts.get('us-gaap', {}).get(n)
            if not node: continue
            for unit, vals in node['units'].items():
                rows = []
                for x in vals:
                    if x.get('form') not in FORMS: continue
                    if 'start' in x:
                        days = (pd.Timestamp(x['end']) - pd.Timestamp(x['start'])).days
                        if not 350 <= days <= 380: continue
                    rows.append([x['end'], x['val'], x['filed']])
                if rows: cands.append({'concept': f'us-gaap:{n}', 'unit': unit, 'rows': rows})
        out[key] = cands
    return out


def main():
    u = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'cik']], pd.read_csv(D / 'universe_pit_extra.csv')[['ticker', 'cik']]]).dropna().drop_duplicates('ticker')
    have = {p.name.split('.json')[0] for p in (D / 'pit').glob('*.json.gz')}
    u = u[u.ticker.isin(have)]
    (D / 'pit2').mkdir(exist_ok=True)
    for i, r in enumerate(u.itertuples()):
        f = D / 'pit2' / f'{r.ticker}.json.gz'
        if f.exists(): continue
        for attempt in range(4):
            try:
                resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(r.cik):010d}.json', headers=UA, timeout=90)
                if resp.status_code == 404: print(r.ticker, '404'); break
                resp.raise_for_status()
                with gzip.open(f, 'wt') as g: json.dump(compact(resp.json()['facts']), g)
                break
            except Exception as e:
                print(r.ticker, 'erro', repr(e)[:100], flush=True); time.sleep(3 * (attempt + 1))
        time.sleep(0.15)
        if i % 50 == 0: print(i, r.ticker, flush=True)
    print('ok', len(list((D / 'pit2').glob('*.gz'))), 'de', len(u))


if __name__ == '__main__':
    main()
