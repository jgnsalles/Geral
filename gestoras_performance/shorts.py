"""Exposição vendida por fundo e mês, a partir da CDA: futuro de Ibovespa vendido (nocional) e ações tomadas emprestadas (vendidas).
Uso: python3 shorts.py <pasta cda> <ibov_pontos.json {ym: pontos}> <fundos.txt CNPJs> <saida.pkl>"""
import sys, os, glob, zipfile, json, re
import pandas as pd
CDA, IBJ, FL, OUT = sys.argv[1:5]
IBP = json.load(open(IBJ)); keep = set(open(FL).read().split())
rows = []
for z in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if not re.search(r'BLC_[48]|_PL_|cda_fi_PL', n): continue
        d = pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3)
        d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
        d = d[d.CNPJ_FUNDO.isin(keep)]
        if d.empty: continue
        d['ym'] = d.DT_COMPTC.str[:7]
        if 'VL_PATRIM_LIQ' in d:
            rows.append(d.assign(kind='pl', v=pd.to_numeric(d.VL_PATRIM_LIQ, errors='coerce'))[['CNPJ_FUNDO', 'ym', 'kind', 'v']]); continue
        code = (d.get('CD_ATIVO', pd.Series('', index=d.index)).fillna('') + ' ' + d.get('DS_ATIVO', pd.Series('', index=d.index)).fillna('')).str.upper()
        qt = pd.to_numeric(d.QT_POS_FINAL, errors='coerce').abs(); vl = pd.to_numeric(d.VL_MERC_POS_FINAL, errors='coerce').abs()
        fut = d.TP_APLIC.fillna('').str.contains('Futuro - Posi..es vendidas') & code.str.contains(r'\bIND|\bWIN|IBOV|FUT IND')
        mult = code.str.contains('WIN').map({True: 0.2, False: 1.0})
        pts = d.ym.map(IBP).astype(float)
        a = d[fut].assign(kind='idx', v=(qt * mult * pts)[fut])
        stk = d.TP_APLIC.fillna('').str.startswith('Obriga') & d.TP_APLIC.fillna('').str.contains('empr')
        b = d[stk].assign(kind='stk', v=vl[stk])
        rows += [a[['CNPJ_FUNDO', 'ym', 'kind', 'v']], b[['CNPJ_FUNDO', 'ym', 'kind', 'v']]]
    print('ok', os.path.basename(z), flush=True)
R = pd.concat(rows).groupby(['CNPJ_FUNDO', 'ym', 'kind']).v.sum().unstack('kind').reset_index()
R.to_pickle(OUT); print(R.shape)
