"""Todas as ligações fundo -> fundo investido (bloco 2 da CDA), todos os fundos. Uso: all_links.py <pasta cda> <saida.pkl>"""
import sys, os, glob, zipfile
import pandas as pd
CDA, OUT = sys.argv[1:3]; rows = []
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if 'BLC_2' not in n: continue
        for d in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3, chunksize=1_000_000):
            d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO', 'CNPJ_FUNDO_CLASSE_COTA': 'COTA', 'CNPJ_FUNDO_COTA': 'COTA'})
            x = pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.DT_COMPTC.str[:7], 'cota': d.COTA,
                              'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}).dropna()
            rows.append(x.groupby(['CNPJ_FUNDO', 'ym', 'cota']).v.sum().reset_index())
    print('ok', os.path.basename(z), flush=True)
L = pd.concat(rows).groupby(['CNPJ_FUNDO', 'ym', 'cota']).v.sum().reset_index()
L.to_pickle(OUT); print(L.shape)
