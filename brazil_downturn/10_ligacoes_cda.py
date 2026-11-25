"""Brazil Downturn, passo 10: ligações fundo -> fundo, mês a mês (CDA, bloco 2 = cotas de fundos), jan/2019 a out/2026.
Guarda só ligações em que quem investe (A) e o fundo investido (B) estão no painel de fundos do passo 1.
Lê as duas versões das colunas (CNPJ_FUNDO / CNPJ_FUNDO_CLASSE e CNPJ_FUNDO_COTA / CNPJ_FUNDO_CLASSE_COTA).
A posição em sigilo (arquivo CONFID) não identifica o fundo investido e não entra.
Uso: python3 10_ligacoes_cda.py <pasta cda> <fundo_mes.pkl> <saida.pkl>
"""
import sys, os, glob, zipfile
import pandas as pd

CDA, FM, OUT = sys.argv[1:4]
U = set(pd.read_pickle(FM).CNPJ_FUNDO.unique())
REN = {'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO', 'CNPJ_FUNDO_CLASSE_COTA': 'CNPJ_FUNDO_COTA'}
rows = []
for f in sorted(glob.glob(os.path.join(CDA, 'cda_fi_*.zip'))):
    z = zipfile.ZipFile(f)
    for n in [n for n in z.namelist() if 'BLC_2' in n]:
        for c in pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str, chunksize=1_000_000, quoting=3, on_bad_lines='skip'):
            c = c.rename(columns=REN)
            if 'ID_SUBCLASSE' in c.columns: c = c[c.ID_SUBCLASSE.isna() | (c.ID_SUBCLASSE == '')]
            c = c[c.CNPJ_FUNDO.isin(U) & c.CNPJ_FUNDO_COTA.isin(U) & (c.CNPJ_FUNDO != c.CNPJ_FUNDO_COTA)]
            if len(c):
                c['ym'] = c.DT_COMPTC.str[:7]
                c['v'] = pd.to_numeric(c.VL_MERC_POS_FINAL, errors='coerce')
                rows.append(c[['CNPJ_FUNDO', 'CNPJ_FUNDO_COTA', 'ym', 'v']])
    print(os.path.basename(f), sum(len(r) for r in rows), flush=True)
L = pd.concat(rows).groupby(['CNPJ_FUNDO', 'CNPJ_FUNDO_COTA', 'ym'], as_index=False).v.sum()
L.to_pickle(OUT)
print('ligações:', len(L), '| meses:', L.ym.nunique(), L.ym.min(), L.ym.max())
print(L.groupby('ym').size().to_string())
