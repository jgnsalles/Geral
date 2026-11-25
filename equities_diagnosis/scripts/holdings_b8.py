"""Ações, BDRs e units que aparecem no bloco 8 da CDA ("demais ativos"), no mesmo formato de holdings.py.
O ticker vem de DS_ATIVO (ex.: "BBSE/BBSE3/BRBBSEACNOR5", "CIEL3", "AÇÕES À VISTA - CIEL 3") ou do ISIN.
Uso: python3 holdings_b8.py <pasta cda> <fundos.txt> <saida.pkl>"""
import sys, os, glob, zipfile, re
import pandas as pd
CDA, FL, OUT = sys.argv[1:4]
keep = set(open(FL).read().split()); H = []
TP = re.compile(r'^(Ações|Brazilian Depository|Certificado ou recibo de depósito|Ações e outros TVM cedidos)')
TK = re.compile(r'\b([A-Z][A-Z0-9]{3}(?:3|4|5|6|7|8|11|31|32|33|34|35|39))\b')
ISIN = re.compile(r'\b(BR[A-Z0-9]{4}[A-Z0-9]{6})\b')
def tick(ds):
    s = re.sub(r'([A-Z]{4})\s+(\d{1,2})\b', r'\1\2', str(ds or '').upper())
    m = TK.search(s)
    return m.group(1) if m else None
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if 'BLC_8' not in n: continue
        for d in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3, chunksize=1_000_000):
            d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'}); d = d[d.CNPJ_FUNDO.isin(keep)]
            d = d[d.TP_APLIC.fillna('').str.match(TP)]
            if d.empty: continue
            ds = d.DS_ATIVO.fillna('')
            H.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.DT_COMPTC.str[:7], 'tp': d.TP_APLIC, 'tk': ds.map(tick),
                                   'isin': ds.str.extract(ISIN, expand=False), 'ds': ds,
                                   'qt': pd.to_numeric(d.QT_POS_FINAL, errors='coerce'), 'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}))
    print('ok', os.path.basename(z), flush=True)
H = pd.concat(H, ignore_index=True)
print('linhas', len(H), 'sem ticker', round(H.tk.isna().mean(), 3), 'valor sem ticker', round(H.v[H.tk.isna()].sum() / H.v.sum(), 3))
H.to_pickle(OUT)
