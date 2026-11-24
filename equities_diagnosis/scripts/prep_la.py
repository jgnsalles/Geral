"""Prepara o attribution dos fundos LatAm com carteira na CVM (Onyx LatAm e o fundo brasileiro da Apo):
fundo-mês, posições no exterior (bloco 7) no formato das posições locais, e junta retornos B3 + exterior.
Uso: python3 prep_la.py <scratch>"""
import sys, os, json
import pandas as pd
S = sys.argv[1]; j = lambda *p: os.path.join(S, *p)
FUNDS = {'30.181.837/0001-45': '15555653', '41.333.289/0001-48': '34008584'}
P = pd.read_pickle(j('out', 'fundo_mes.pkl'))
E = P[P.CNPJ_FUNDO.isin(FUNDS) & P.r.notna() & P.pl_ant.gt(0)][['CNPJ_FUNDO', 'ym', 'pl', 'pl_ant', 'r']].copy()
E['gid'] = E.CNPJ_FUNDO.map(FUNDS)
Esel = pd.read_pickle(j('E_sel.pkl'))
pd.concat([Esel, E[Esel.columns]], ignore_index=True).to_pickle(j('E_all.pkl'))
X = pd.read_pickle(j('emp', 'foreign.pkl'))
X = X[X.CNPJ_FUNDO.isin(FUNDS) & X.tpa.isin(['Outros', 'Ação ordinária', 'Ação preferencial', 'Depository Receipt no Exterior(DR)']) & (X.v > 0)].copy()
X['cod'] = X.cod.fillna('').str.strip().str.upper(); X = X[~X.cod.isin(['', 'FUNDO OFF', 'OFFSHORE'])]
X['cod'] = X.cod.map(lambda c: {'BOLSA': 'BOLSAA'}.get(c.split()[0].replace('*', ''), c.split()[0].replace('*', '')))
Hb = pd.read_pickle(j('attr', 'la', 'holdings.pkl'))
Hf = pd.DataFrame({'CNPJ_FUNDO': X.CNPJ_FUNDO, 'ym': X.ym, 'tp': 'Investimento no Exterior', 'tk': 'X:' + X.cod, 'isin': None, 'ds': X.emissor, 'qt': X.qt, 'v': X.v})
pd.concat([Hb, Hf], ignore_index=True).to_pickle(j('attr', 'la', 'holdings_all.pkl'))
R1 = pd.read_pickle(j('attr', 'ret.pkl')); R2 = pd.read_pickle(j('emp', 'ret.pkl')); R3 = pd.read_pickle(j('emp', 'ret_ext.pkl'))
R = pd.concat([R2, R1[[c for c in R1.columns if c not in R2.columns]], R3], axis=1).sort_index()
R.to_pickle(j('attr', 'ret_all.pkl'))
nm = json.load(open(j('attr', 'nomes.json'))); nm.update(json.load(open(j('emp', 'nomes_ext.json'))))
json.dump(nm, open(j('attr', 'nomes_all.json'), 'w'), ensure_ascii=False)
print('E_la', len(E), E.groupby('gid').ym.agg(['min', 'max']).to_dict(), '| posições exterior', len(Hf), '| retornos', R.shape)
