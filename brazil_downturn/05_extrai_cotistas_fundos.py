"""Brazil Downturn, passo 5: quem são os fundos cotistas dos fundos de ações (CDA, bloco 2 = cotas de fundos), fim de trimestre 2019-03 a 2026-09,
e o Perfil Mensal desses fundos cotistas (para atravessar feeders até o investidor final).
Uso: python3 05_extrai_cotistas_fundos.py <pasta cda> <pasta perfil> <fundo_mes.pkl> <saida_dir>
"""
import sys, os, glob, zipfile
import pandas as pd

CDA, PERF, FM, OUT = sys.argv[1:5]
U = set(pd.read_pickle(FM).CNPJ_FUNDO.unique())
QM = {f'{y}-{m:02d}' for y in range(2019, 2027) for m in (3, 6, 9, 12) if f'{y}-{m:02d}' <= '2026-09'}
REN = {'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO', 'CNPJ_FUNDO_CLASSE_COTA': 'CNPJ_FUNDO_COTA'}
rows = []
for f in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    z = zipfile.ZipFile(f)
    for n in [n for n in z.namelist() if 'BLC_2' in n]:
        for c in pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str, chunksize=1_000_000, quoting=3, on_bad_lines='skip'):
            c = c.rename(columns=REN)
            if 'ID_SUBCLASSE' in c.columns: c = c[c.ID_SUBCLASSE.isna() | (c.ID_SUBCLASSE == '')]
            c['ym'] = c.DT_COMPTC.str[:7]
            c = c[c.ym.isin(QM) & c.CNPJ_FUNDO_COTA.isin(U)]
            if len(c):
                c['v'] = pd.to_numeric(c.VL_MERC_POS_FINAL, errors='coerce')
                rows.append(c[['CNPJ_FUNDO', 'ym', 'CNPJ_FUNDO_COTA', 'v', 'EMISSOR_LIGADO']])
    print(os.path.basename(f), sum(len(r) for r in rows), flush=True)
B = pd.concat(rows).groupby(['CNPJ_FUNDO', 'ym', 'CNPJ_FUNDO_COTA'], as_index=False).agg(v=('v', 'sum'), lig=('EMISSOR_LIGADO', 'first'))
B.to_pickle(os.path.join(OUT, 'cotistas_fundos.pkl'))
H = set(B.CNPJ_FUNDO)
TIP = ['PF_PB', 'PF_VAREJO', 'PJ_NAO_FINANC_PB', 'PJ_NAO_FINANC_VAREJO', 'BANCO', 'CORRETORA_DISTRIB', 'PJ_FINANC', 'INVNR',
       'EAPC', 'EFPC', 'RPPS', 'SEGUR', 'CAPITALIZ', 'FI_CLUBE', 'DISTRIB', 'OUTRO']
cols = ['PR_PL_COTST_' + t for t in TIP]
parts = []
for f in sorted(glob.glob(os.path.join(PERF, 'perfil_mensal_fi_*.csv'))):
    ym = os.path.basename(f)[17:21] + '-' + os.path.basename(f)[21:23]
    if ym not in QM: continue
    h = pd.read_csv(f, sep=';', encoding='latin1', nrows=0).columns
    c = 'CNPJ_FUNDO_CLASSE' if 'CNPJ_FUNDO_CLASSE' in h else 'CNPJ_FUNDO'
    use = [c] + (['VERSAO'] if 'VERSAO' in h else []) + cols
    x = pd.read_csv(f, sep=';', encoding='latin1', dtype=str, usecols=use, on_bad_lines='skip').rename(columns={c: 'CNPJ_FUNDO'})
    x = x[x.CNPJ_FUNDO.isin(H)]
    for k in cols: x[k] = pd.to_numeric(x[k].str.replace(',', '.'), errors='coerce')
    x['vv'] = pd.to_numeric(x.get('VERSAO', 0), errors='coerce').fillna(0)
    x = x.sort_values('vv').drop_duplicates('CNPJ_FUNDO', keep='last'); x['ym'] = ym
    parts.append(x[['CNPJ_FUNDO', 'ym'] + cols])
X = pd.concat(parts); X.columns = ['CNPJ_FUNDO', 'ym'] + TIP
X.to_pickle(os.path.join(OUT, 'perfil_cotistas.pkl'))
print('fundos cotistas:', len(H), '| com perfil:', X.CNPJ_FUNDO.nunique())
