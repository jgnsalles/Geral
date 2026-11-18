"""Navegando LatAm: as maiores gestoras 13F de LatAm ex-Brasil em CADA trimestre (ranking refeito em cada data), contra a lista do artefato.
Lê (sem alterar) os 13F de todos os declarantes extraídos pelo ramo D (relatorio/data_13f_sec/pos_*.csv.gz: gestores ativos, 20 a 400 posições,
10 maiores >= 25%) e a lista de empresas LatAm do próprio artefato (D.f13.emp: CUSIP de 6 dígitos -> [nome, LatAm ex-Brasil?]).
Regra: valor em empresas LatAm ex-Brasil listadas nos EUA, com pelo menos 3 empresas; as 100 maiores de cada trimestre.
Uso: python3 latam_13f_top.py <D.json do artefato> <pasta data_13f_sec> <saida.csv>"""
import sys, json, glob, os
import pandas as pd
DJ, DIR, OUT = sys.argv[1:4]
D = json.load(open(DJ)); emp = {k: v for k, v in D['f13']['emp'].items() if v[1]}
orig = set(D['f13']['fundos'])
rows = []
for f in sorted(glob.glob(os.path.join(DIR, 'pos_*.csv.gz'))):
    p = pd.read_csv(f, dtype={'CUSIP': str, 'CIK': str})
    p['c6'] = p.CUSIP.str[:6].str.upper(); x = p[p.c6.isin(emp)]
    if not len(x): continue
    g = x.groupby(['CIK', 'per']).agg(lat=('v', 'sum'), n=('c6', 'nunique'), nome=('nome', 'size')).reset_index()
    fl = pd.read_csv(f.replace('pos_', 'filers_'), dtype={'CIK': str})[['CIK', 'FILINGMANAGER_NAME', 'tot']].drop_duplicates('CIK')
    g = g.merge(fl, on='CIK', how='left'); g = g[g.n >= 3]
    g['rk'] = g.lat.rank(ascending=False, method='first'); g['q'] = os.path.basename(f)[4:10]
    g['cik10'] = g.CIK.str.zfill(10); g['no_artefato'] = g.cik10.isin(orig)
    rows.append(g)
R = pd.concat(rows); top = R[R.rk <= 100]
cov = top.groupby('q').apply(lambda x: pd.Series({'gestoras_top': len(x), 'do_artefato': int(x.no_artefato.sum()),
                                                   'lat_bi': round(R[R.q == x.name].lat.sum() / 1e9, 1),
                                                   'cobertura_artefato': round(R[(R.q == x.name) & R.no_artefato].lat.sum() / R[R.q == x.name].lat.sum(), 3),
                                                   'cobertura_top100_mais_artefato': round(R[(R.q == x.name) & (R.no_artefato | (R.rk <= 100))].lat.sum() / R[R.q == x.name].lat.sum(), 3)}), include_groups=False)
top.to_csv(OUT, index=False)
print(cov.to_string())
fora = top[~top.no_artefato].groupby('FILINGMANAGER_NAME').agg(trimestres=('q', 'size'), pico_lat_mi=('lat', lambda v: round(v.max() / 1e6))).sort_values('pico_lat_mi', ascending=False)
print(fora.head(25).to_string()); print('gestoras fora do artefato que estiveram no top 100:', len(fora))
