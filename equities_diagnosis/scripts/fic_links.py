"""Ligações FIC -> fundo investido, por mês, a partir do bloco 2 da CDA (cotas de fundos).
Saída: fundo, ym, fundo investido, valor de mercado.
Uso: python3 fic_links.py <pasta cda> <fundos.txt CNPJs dos FICs> <saida.pkl>"""
import sys, os, glob, zipfile, re
import pandas as pd
CDA, FL, OUT = sys.argv[1:4]
keep = set(open(FL).read().split()); rows = []
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if 'BLC_2' not in n: continue
        for d in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3, chunksize=1_000_000):
            d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO', 'CNPJ_FUNDO_CLASSE_COTA': 'COTA', 'CNPJ_FUNDO_COTA': 'COTA'})
            d = d[d.CNPJ_FUNDO.isin(keep)]
            if d.empty: continue
            rows.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.DT_COMPTC.str[:7], 'cota': d.COTA,
                                      'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}))
    print('ok', os.path.basename(z), flush=True)
L = pd.concat(rows).groupby(['CNPJ_FUNDO', 'ym', 'cota']).v.sum().reset_index()
L.to_pickle(OUT); print(L.shape, L.CNPJ_FUNDO.nunique())
