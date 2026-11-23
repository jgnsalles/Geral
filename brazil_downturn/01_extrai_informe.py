"""Brazil Downturn, passo 1: Informe Diário da CVM -> painel mensal por fundo (2005-01 a 2026-10).

Universo amplo (o filtro fino fica no passo 2): todo fundo que em algum momento foi da classe "Ações"
(cad_fi_hist_classe, cad_fi, registro_classe RCVM 175) ou cujo nome indica long biased.
Por fundo e mês: PL e cota do último dia, PL do primeiro dia, soma de captações e resgates, cotistas.
Uso: python3 01_extrai_informe.py <pasta raw com cad_fi*.zip/csv, registro_fundo_classe.zip e infd/*.zip> <saida.pkl>
"""
import sys, os, re, glob, zipfile, unicodedata
import pandas as pd, numpy as np

RAW, OUT = sys.argv[1:3]
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if isinstance(c, str) and len(c) == 14 else c

z = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
rd = lambda n: pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str)
hc = rd('cad_fi_hist_classe.csv'); hn = rd('cad_fi_hist_denom_social.csv')
cad = pd.read_csv(os.path.join(RAW, 'cad_fi.csv'), sep=';', encoding='latin1', dtype=str)
zr = zipfile.ZipFile(os.path.join(RAW, 'registro_fundo_classe.zip'))
rc = pd.read_csv(zr.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str)
rc['CNPJ_FUNDO'] = rc.CNPJ_Classe.str.zfill(14).map(fmt)

eq = set(hc[hc.CLASSE == 'Ações'].CNPJ_FUNDO) | set(cad[cad.CLASSE == 'Ações'].CNPJ_FUNDO)
eq |= set(rc[rc.Classificacao.fillna('').str.startswith('Aç')].CNPJ_FUNDO)
eq |= set(rc[rc.Classificacao_Anbima.fillna('').str.contains('Ações|L/S - Direcional')].CNPJ_FUNDO)
LB = re.compile(r'LONG ?BIAS|\bL\.?B\.?\b|LONG ONLY')
names = pd.concat([hn[['CNPJ_FUNDO', 'DENOM_SOCIAL']], cad[['CNPJ_FUNDO', 'DENOM_SOCIAL']],
                   rc[['CNPJ_FUNDO', 'Denominacao_Social']].rename(columns={'Denominacao_Social': 'DENOM_SOCIAL'})])
lb = set(names[names.DENOM_SOCIAL.map(deacc).str.contains(LB)].CNPJ_FUNDO)
U = eq | lb
print('fundos no universo amplo:', len(U), '| ações:', len(eq), '| long biased pelo nome:', len(lb - eq), flush=True)


def monthly(df):
    df = df.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
    if 'ID_SUBCLASSE' in df.columns:
        df = df[df.ID_SUBCLASSE.isna()]
    df = df[df.CNPJ_FUNDO.isin(U)]
    if df.empty:
        return None
    for c in ['VL_QUOTA', 'VL_PATRIM_LIQ', 'CAPTC_DIA', 'RESG_DIA', 'NR_COTST']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.sort_values(['CNPJ_FUNDO', 'DT_COMPTC']).drop_duplicates(['CNPJ_FUNDO', 'DT_COMPTC'], keep='last')
    df['ym'] = df.DT_COMPTC.str[:7]
    g = df.groupby(['CNPJ_FUNDO', 'ym'])
    return pd.DataFrame({'dt': g.DT_COMPTC.last(), 'q': g.VL_QUOTA.last(), 'pl': g.VL_PATRIM_LIQ.last(),
                         'pl0': g.VL_PATRIM_LIQ.first(), 'cap': g.CAPTC_DIA.sum(), 'res': g.RESG_DIA.sum(),
                         'cot': g.NR_COTST.last(), 'nd': g.size()}).reset_index()


parts = []
for f in sorted(glob.glob(os.path.join(RAW, 'infd', 'inf_diario_fi_*.zip'))):
    with zipfile.ZipFile(f) as zf:
        for n in zf.namelist():
            chunks = []
            for c in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, chunksize=2_000_000):
                c = c.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
                if 'ID_SUBCLASSE' in c.columns:
                    c = c[c.ID_SUBCLASSE.isna()]
                chunks.append(c[c.CNPJ_FUNDO.isin(U)])
            m = monthly(pd.concat(chunks)) if chunks else None
            if m is not None:
                parts.append(m)
    print('ok', os.path.basename(f), flush=True)
P = pd.concat(parts).sort_values(['CNPJ_FUNDO', 'ym']).drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
P.to_pickle(OUT)
print('linhas', len(P), 'fundos', P.CNPJ_FUNDO.nunique(), 'meses', P.ym.min(), P.ym.max())
