"""Setores (subsetores GICS) ciclicos, definidos pelo historico completo do ROIC, por SETOR e nao por empresa.
Regua (so fundamentos, sem olhar retorno de acao):
  - queda media: media das quedas ano a ano do ROIC (subidas contam zero) / ROIC medio, em todo o historico da empresa;
  - colapsos: numero de episodios em que o ROIC caiu a metade ou menos do maior valor dos 3 anos anteriores.
  Subsetor = mediana das suas empresas (empresas com ROIC medio <= 0 ficam fora da mediana).
  CICLICO se queda media >= 2 x a dos setores defensivos (consumo basico + utilidades) E mediana de colapsos >= 2.
Saida: backtest/data/ciclicos.csv. Uso: python3 backtest/ciclicos.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import D  # noqa: E402

# rotulos do Yahoo (algumas empresas da planilha) -> subsetor GICS equivalente
CANON = {'Auto - Manufacturers': 'Automobile Manufacturers', 'Medical - Healthcare Plans': 'Managed Health Care', 'Software - Application': 'Application Software',
         'Software - Infrastructure': 'Systems Software', 'Banks - Regional': 'Regional Banks', 'Insurance - Property & Casualty': 'Property & Casualty Insurance',
         'Industrial - Distribution': 'Trading Companies & Distributors', 'Industrial - Machinery': 'Industrial Machinery & Supplies & Components',
         'Industrial Machinery': 'Industrial Machinery & Supplies & Components', 'Drug Manufacturers - General': 'Pharmaceuticals',
         'Medical - Pharmaceuticals': 'Pharmaceuticals', 'Hardware, Equipment & Parts': 'Electronic Components', 'Specialty Retail': 'Other Specialty Retail',
         'Residential Construction': 'Homebuilding', 'Medical - Diagnostics & Research': 'Life Sciences Tools & Services',
         'Medical - Care Facilities': 'Health Care Facilities', 'Household & Personal Products': 'Household Products',
         'Waste Management': 'Environmental & Facilities Services', 'Broadline Retail (lojas de departamento)': 'Department Stores',
         'Software - Infrastructure ': 'Systems Software', 'Packaging & Containers': 'Metal, Glass & Plastic Containers'}
# subsetores com uma empresa so: decididos no nivel de industria GICS (um nivel acima), juntando os irmaos
GROUPS = {'Media': {'Advertising', 'Publishing', 'Cable & Satellite', 'Broadcasting'},
          'Entertainment': {'Movies & Entertainment', 'Interactive Home Entertainment'},
          'Specialty Retail': {'Computer & Electronics Retail', 'Homefurnishing Retail', 'Other Specialty Retail', 'Apparel Retail', 'Home Improvement Retail', 'Automotive Retail'},
          'Household Durables': {'Consumer Electronics', 'Home Furnishings', 'Household Appliances', 'Homebuilding', 'Housewares & Specialties'},
          'Textiles, Apparel & Luxury Goods': {'Footwear', 'Apparel, Accessories & Luxury Goods', 'Textiles'},
          'Automobiles': {'Motorcycle Manufacturers', 'Automobile Manufacturers'},
          'Diversified Consumer Services': {'Education & Training Services', 'Specialized Consumer Services'},
          'Consumer Staples Distribution & Retail': {'Food Distributors', 'Food Retail', 'Consumer Staples Merchandise Retail', 'Drug Retail'},
          'Energy Equipment & Services': {'Oil & Gas Drilling', 'Oil & Gas Equipment & Services'},
          'Financial Services': {'Multi-Sector Holdings', 'Transaction & Payment Processing Services', 'Diversified Financial Services'},
          'Insurance': {'Reinsurance', 'Property & Casualty Insurance', 'Life & Health Insurance', 'Multi-line Insurance', 'Insurance Brokers'},
          'Machinery': {'Agricultural & Farm Machinery', 'Construction Machinery & Heavy Transportation Equipment', 'Industrial Machinery & Supplies & Components'},
          'Professional Services': {'Data Processing & Outsourced Services', 'Research & Consulting Services', 'Human Resource & Employment Services'},
          'Electrical Equipment': {'Heavy Electrical Equipment', 'Electrical Components & Equipment'},
          'Commercial Services & Supplies': {'Security & Protection Services', 'Specialty Business Services', 'Environmental & Facilities Services', 'Diversified Support Services'},
          'Electronic Equipment, Instruments & Components': {'Technology Distributors', 'Electronic Components', 'Electronic Manufacturing Services', 'Electronic Equipment & Instruments'},
          'Metals & Mining': {'Copper', 'Steel', 'Gold', 'Aluminum', 'Diversified Metals & Mining'},
          'Containers & Packaging': {'Metal, Glass & Plastic Containers', 'Paper & Plastic Packaging Products & Materials'},
          'Specialized REITs': {'Other Specialized REITs', 'Timber REITs', 'Data Center REITs', 'Self-Storage REITs', 'Telecom Tower REITs'}}
SUB2GROUP = {sub: g for g, subs in GROUPS.items() for sub in subs}
DEFENSIVE_SECTORS = {'Consumer Staples', 'Utilities'}
# Decisao do usuario (2026-11-10, opcao B): passam na regua, mas o ROIC oscila por motivos que nao sao ciclo
# (pandemia, saida de prejuizo, vencimento de patente); voltam para a OoL/GCGR. Escolha feita olhando o retorno de 2012-2026.
NOT_CYCLICAL = {'Hotels, Resorts & Cruise Lines', 'Movies & Entertainment', 'Biotechnology', 'Automobile Manufacturers', 'Diversified Chemicals'}
MULT, MIN_COLLAPSES = 2.0, 2


def canon(ind):
    return CANON.get(ind, ind) if isinstance(ind, str) else ind


def company_metrics(s):
    rows = []
    for tk, g in s.groupby('ticker'):
        r = g.set_index('fy').roic.sort_index()
        if len(r) < 8: continue
        d = np.diff(r.values)[np.diff(r.index.values) == 1]
        if len(d) < 7: continue
        mu = r.mean()
        col, prev = 0, False
        for i in range(3, len(r)):
            pk = r.iloc[i - 3:i].max(); c = pk > 0 and r.iloc[i] <= 0.5 * pk
            if c and not prev: col += 1
            prev = c
        rows.append(dict(ticker=tk, anos=len(r), y0=int(r.index.min()), roic_med=mu,
                         queda=(np.abs(np.clip(d, None, 0)).mean() / mu) if mu > 0 else np.nan,
                         var_total=(np.abs(d).mean() / mu) if mu > 0 else np.nan, colapsos=col))
    return pd.DataFrame(rows).set_index('ticker')


def build():
    import benchmarks as bm
    s = pd.read_csv(D / 'roic_series.csv')
    sec, ind = bm.sector_maps()
    e = company_metrics(s)
    e['sector'] = e.index.map(sec); e['industry'] = e.index.map(lambda t: canon(ind(t)))
    e = e[e.industry.notna()]
    v = e[e.queda.notna()]
    S = v.groupby(['sector', 'industry']).agg(empresas=('queda', 'size'), queda=('queda', 'median'), var_total=('var_total', 'median'),
                                              colapsos=('colapsos', 'median'), anos=('anos', 'median')).reset_index()
    ref = v[v.sector.isin(DEFENSIVE_SECTORS)].queda.median()
    cut = MULT * ref
    S['nivel'] = 'subsetor'
    for i, r in S[S.empresas < 2].iterrows():
        g = SUB2GROUP.get(r.industry)
        pool = v[v.industry.isin(GROUPS[g])] if g else v.iloc[0:0]
        if len(pool) >= 2:
            S.loc[i, ['queda', 'colapsos', 'empresas']] = [pool.queda.median(), pool.colapsos.median(), len(pool)]
            S.loc[i, 'nivel'] = f'indústria GICS: {g}'
        else:
            S.loc[i, 'nivel'] = 'uma empresa só (sem evidência suficiente)'
    S['ciclico'] = (S.queda >= cut) & (S.colapsos >= MIN_COLLAPSES) & (S.empresas >= 2)
    S.attrs.update(ref=ref, cut=cut)
    S.to_csv(D / 'ciclicos.csv', index=False)
    e.to_csv(D / 'ciclicos_empresas.csv')
    return S, e, ref, cut


def cyclical_industries():
    p = D / 'ciclicos.csv'
    if not p.exists(): build()
    S = pd.read_csv(p)
    return set(S[S.ciclico].industry) - NOT_CYCLICAL


if __name__ == '__main__':
    S, e, ref, cut = build()
    print(f'referencia defensiva {ref:.3f} corte {cut:.3f}')
    print(S[S.ciclico].sort_values('queda', ascending=False).to_string())
