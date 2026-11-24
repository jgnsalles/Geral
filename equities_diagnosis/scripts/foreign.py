"""Ativos no exterior (bloco 7 da CDA) de todos os fundos: código na bolsa de origem, quantidade e valor em R$ por mês.
Serve para (1) preço mensal em R$ de ações estrangeiras = mediana entre fundos de valor ÷ quantidade, (2) cota dos fundos
offshore da Fourth Sail, (3) posições no exterior dos fundos LatAm.
Uso: python3 foreign.py <pasta cda> <saida.pkl>"""
import sys, os, glob, zipfile
import pandas as pd
CDA, OUT = sys.argv[1:3]; rows = []
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if 'BLC_7' not in n: continue
        for d in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3, chunksize=1_000_000):
            d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
            g = lambda c: d[c] if c in d.columns else pd.Series(None, index=d.index, dtype=str)
            rows.append(pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.DT_COMPTC.str[:7], 'cod': g('CD_ATIVO_BV_MERC'), 'emissor': g('EMISSOR'),
                                      'ds': g('DS_ATIVO_EXTERIOR'), 'pais': g('PAIS'), 'bolsa': g('BV_MERC'), 'tp': g('TP_APLIC'), 'tpa': g('TP_ATIVO'),
                                      'qt': pd.to_numeric(d.QT_POS_FINAL, errors='coerce'), 'v': pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce')}))
    print('ok', os.path.basename(z), flush=True)
X = pd.concat(rows); X.to_pickle(OUT); print(X.shape, X.cod.notna().mean())
