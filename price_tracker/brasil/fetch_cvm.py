"""Baixa as DFPs (2010+) da CVM e guarda so as contas necessarias, com data de entrega por versao (point-in-time).
Saidas: data/cvm_docs.csv.gz (CD_CVM, DT_REFER, VERSAO, DT_RECEB) e data/cvm_facts.csv.gz (contas)."""
import io, re, zipfile, pathlib, requests
import pandas as pd

UA = {'User-Agent': 'PriceTracker-Research/1.0'}
D = pathlib.Path(__file__).parent / 'data'
BASE = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{}.zip'
KEEP = {'DRE': r'^3\.\d\d(\.0[1-2])?$|^3\.99\.0[12]\.\d\d$', 'BPA': r'^1(\.\d\d){0,2}$', 'BPP': r'^2(\.\d\d){0,2}$'}
COLS = ['CD_CVM', 'DT_REFER', 'VERSAO', 'CD_CONTA', 'DS_CONTA', 'VL_CONTA', 'ESCALA_MOEDA']

def main():
    docs, facts = [], []
    for y in range(2010, 2027):
        r = requests.get(BASE.format(y), headers=UA, timeout=300); r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        rd = lambda n: pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype={'CD_CVM': str, 'CD_CONTA': str})
        docs.append(rd(f'dfp_cia_aberta_{y}.csv')[['CD_CVM', 'DT_REFER', 'VERSAO', 'DT_RECEB']])
        for st, pat in KEEP.items():
            for grp in ('con', 'ind'):
                n = f'dfp_cia_aberta_{st}_{grp}_{y}.csv'
                if n not in z.namelist(): continue
                x = rd(n)
                x = x[(x.ORDEM_EXERC == 'ÚLTIMO') & x.CD_CONTA.str.match(pat)][COLS].copy()
                x['ST'], x['GRP'] = st, grp
                facts.append(x)
        print(y, sum(len(f) for f in facts), flush=True)
    pd.concat(docs).to_csv(D / 'cvm_docs.csv.gz', index=False)
    pd.concat(facts).to_csv(D / 'cvm_facts.csv.gz', index=False)

if __name__ == '__main__':
    main()
