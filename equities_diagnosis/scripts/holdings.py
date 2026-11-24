"""Posições em ações (longas) por fundo e mês, a partir dos blocos 4 e 8 e do PL da CDA, mais o valor confidencial.
Saída: holdings.pkl (fundo, ym, ticker, isin, qt, valor) e cda_pl.pkl (fundo, ym, pl, confidencial).
Uso: python3 holdings.py <pasta cda> <fundos.txt> <saida_dir>"""
import sys, os, glob, zipfile, re
import pandas as pd
CDA, FL, OUT = sys.argv[1:4]
keep = set(open(FL).read().split()); H = []; PL = []; CF = []
LONG = re.compile(r'^(Ações|Ações e outros TVM cedidos|Brazilian Depository|Certificado ou recibo de depósito|Ações e outros TVM cedidos em empréstimo)')
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        kind = 'h' if re.search(r'BLC_4', n) else 'pl' if re.search(r'_PL_|fi_PL', n) else 'cf' if 'CONFID' in n else None
        if not kind: continue
        for d in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3, chunksize=1_000_000):
            d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'}); d = d[d.CNPJ_FUNDO.isin(keep)]
            if d.empty: continue
            d['ym'] = d.DT_COMPTC.str[:7]
            if kind == 'pl':
                PL.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.ym, 'pl': pd.to_numeric(d.VL_PATRIM_LIQ, errors='coerce')}))
            elif kind == 'cf':
                CF.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.ym, 'tp': d.TP_APLIC, 'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}))
            else:
                d = d[d.TP_APLIC.fillna('').str.match(LONG)]
                H.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.ym, 'tp': d.TP_APLIC, 'tk': d.get('CD_ATIVO'), 'isin': d.get('CD_ISIN'),
                                       'ds': d.get('DS_ATIVO'), 'qt': pd.to_numeric(d.QT_POS_FINAL, errors='coerce'),
                                       'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}))
    print('ok', os.path.basename(z), flush=True)
H = pd.concat(H); H.to_pickle(os.path.join(OUT, 'holdings.pkl'))
P = pd.concat(PL).groupby(['CNPJ_FUNDO', 'ym']).pl.last().reset_index()
C = pd.concat(CF).groupby(['CNPJ_FUNDO', 'ym']).v.sum().rename('conf').reset_index()
P.merge(C, how='left', on=['CNPJ_FUNDO', 'ym']).to_pickle(os.path.join(OUT, 'cda_pl.pkl'))
print(H.shape, H.tk.notna().mean())
