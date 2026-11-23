"""Brazil Downturn, passo 4: Perfil Mensal da CVM (jan/2019 a out/2026) -> % do PL por tipo de cotista, fundo-mês.
Só os fundos do painel do passo 1 (classe Ações ou long biased, qualquer status). Fica a última versão entregue de cada fundo-mês.
Uso: python3 04_extrai_perfil.py <pasta com perfil_mensal_fi_*.csv> <fundo_mes.pkl do passo 2> <saida.pkl>
"""
import sys, glob, os
import pandas as pd, numpy as np

DIR, FM, OUT = sys.argv[1:4]
U = set(pd.read_pickle(FM).CNPJ_FUNDO.unique())
TIP = ['PF_PB', 'PF_VAREJO', 'PJ_NAO_FINANC_PB', 'PJ_NAO_FINANC_VAREJO', 'BANCO', 'CORRETORA_DISTRIB', 'PJ_FINANC', 'INVNR',
       'EAPC', 'EFPC', 'RPPS', 'SEGUR', 'CAPITALIZ', 'FI_CLUBE', 'DISTRIB', 'OUTRO']
cols = ['PR_PL_COTST_' + t for t in TIP]
parts = []
for f in sorted(glob.glob(os.path.join(DIR, 'perfil_mensal_fi_*.csv'))):
    h = pd.read_csv(f, sep=';', encoding='latin1', nrows=0).columns
    c = 'CNPJ_FUNDO_CLASSE' if 'CNPJ_FUNDO_CLASSE' in h else 'CNPJ_FUNDO'
    use = [c, 'DT_COMPTC'] + (['VERSAO'] if 'VERSAO' in h else []) + cols
    x = pd.read_csv(f, sep=';', encoding='latin1', dtype=str, usecols=use, on_bad_lines='skip').rename(columns={c: 'CNPJ_FUNDO'})
    x = x[x.CNPJ_FUNDO.isin(U)]
    for k in cols:
        x[k] = pd.to_numeric(x[k].str.replace(',', '.'), errors='coerce')
    x['ym'] = x.DT_COMPTC.str[:7]
    x['v'] = pd.to_numeric(x.get('VERSAO', 0), errors='coerce').fillna(0)
    x = x.sort_values('v').drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
    parts.append(x[['CNPJ_FUNDO', 'ym'] + cols])
    print(os.path.basename(f), len(x), flush=True)
X = pd.concat(parts).drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
X.columns = ['CNPJ_FUNDO', 'ym'] + TIP
s = X[TIP].sum(axis=1)
print('soma dos % (quantis):', s.quantile([.01, .05, .5, .95, .99]).round(1).to_dict())
X.to_pickle(OUT)
