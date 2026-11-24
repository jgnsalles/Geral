"""Brazil Downturn, passo 7: número de cotistas pessoa física por fundo (Perfil Mensal), fim de trimestre 2019-03 a 2026-09.
PF private (NR_COTST_PF_PB), PF varejo direto (NR_COTST_PF_VAREJO) e conta e ordem (NR_COTST_DISTRIB, investidores finais das plataformas) e não residentes (NR_COTST_INVNR).
Fundos: os do painel do passo 1 e todos os fundos cotistas do passo 5.
Uso: python3 07_extrai_cotistas_pf.py <pasta perfil> <fundo_mes.pkl> <cotistas_fundos.pkl> <saida.pkl>
"""
import sys, os, glob
import pandas as pd

PERF, FM, CF, OUT = sys.argv[1:5]
U = set(pd.read_pickle(FM).CNPJ_FUNDO.unique()) | set(pd.read_pickle(CF).CNPJ_FUNDO.unique())
QM = {f'{y}-{m:02d}' for y in range(2019, 2027) for m in (3, 6, 9, 12) if f'{y}-{m:02d}' <= '2026-09'}
COLS = {'NR_COTST_PF_PB': 'n_private', 'NR_COTST_PF_VAREJO': 'n_varejo', 'NR_COTST_DISTRIB': 'n_plataformas', 'NR_COTST_INVNR': 'n_estrangeiro'}
parts = []
for f in sorted(glob.glob(os.path.join(PERF, 'perfil_mensal_fi_*.csv'))):
    b = os.path.basename(f); ym = b[17:21] + '-' + b[21:23]
    if ym not in QM: continue
    h = pd.read_csv(f, sep=';', encoding='latin1', nrows=0).columns
    c = 'CNPJ_FUNDO_CLASSE' if 'CNPJ_FUNDO_CLASSE' in h else 'CNPJ_FUNDO'
    x = pd.read_csv(f, sep=';', encoding='latin1', dtype=str, usecols=[c] + (['VERSAO'] if 'VERSAO' in h else []) + list(COLS), on_bad_lines='skip').rename(columns={c: 'CNPJ_FUNDO', **COLS})
    x = x[x.CNPJ_FUNDO.isin(U)].copy()
    for k in COLS.values(): x[k] = pd.to_numeric(x[k], errors='coerce')
    x['vv'] = pd.to_numeric(x.get('VERSAO', 0), errors='coerce').fillna(0)
    x = x.sort_values('vv').drop_duplicates('CNPJ_FUNDO', keep='last'); x['ym'] = ym
    parts.append(x[['CNPJ_FUNDO', 'ym'] + list(COLS.values())])
    print(b, len(x), flush=True)
X = pd.concat(parts); X.to_pickle(OUT)
print(X.groupby('ym')[list(COLS.values())].sum().iloc[::4].to_string())
