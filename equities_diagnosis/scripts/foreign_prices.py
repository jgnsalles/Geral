"""Preço mensal em R$ de ações estrangeiras = mediana entre fundos de valor de mercado ÷ quantidade (bloco 7 da CDA).
Retorno de preço (sem dividendos). Também a cota dos fundos offshore da Fourth Sail (via fundos da Tordesilhas).
Uso: python3 foreign_prices.py <foreign.pkl> <saida_dir>"""
import sys, os, json
import pandas as pd, numpy as np
FP, OUT = sys.argv[1:3]
X = pd.read_pickle(FP)
X = X[(X.qt > 0) & (X.v > 0)].copy()
X['cod'] = X.cod.fillna('').str.strip().str.upper()
# o mesmo ativo aparece com o código escrito de jeitos diferentes entre fundos ("ITAUCL CI", "ITAUCL C", "WALMEX* MM"):
# fica só a primeira palavra, sem asterisco
ALIAS = {'BOLSA': 'BOLSAA'}
def norm(c):
    if c in ('', 'FUNDO OFF', 'OFFSHORE'): return c
    t = c.split()[0].replace('*', '')
    return ALIAS.get(t, t)
X['cod'] = X.cod.map(norm)
eq = X[X.tpa.isin(['Outros', 'Ação ordinária', 'Ação preferencial', 'Depository Receipt no Exterior(DR)']) & ~X.cod.isin(['', 'FUNDO OFF', 'OFFSHORE'])].copy()
eq = eq[~eq.cod.str.match(r'^[0-9]+$') & (eq.cod.str.len() >= 1)]   # código só com números = não é ticker
# cotas de fundos declaradas como ação (ex.: código 'SQ' = fundo offshore da Squadra, não a Square)
FUNDRE = r"(FUND|FUNDO|\bFDO\b|CLASS|\bCL [A-Z]\b|\bLP\b|L\.P\.|SICAV|PORTFOLIO|LONG ONLY|MASTER|FEEDER|OFFSHORE|SQUADRA|ATMOS|DYNAMO|SHP |\bETF\b|ISHARES)"
eq = eq[~(eq.emissor.fillna('') + ' ' + eq.ds.fillna('')).str.upper().str.contains(FUNDRE)]
eq['px'] = eq.v / eq.qt
# retorno dentro de cada fundo (a unidade da quantidade é a mesma no fundo); mediana entre fundos
f = eq.groupby(['CNPJ_FUNDO', 'cod', 'ym']).agg(v=('v', 'sum'), qt=('qt', 'sum')).reset_index()
f['px'] = f.v / f.qt
f = f.sort_values(['CNPJ_FUNDO', 'cod', 'ym'])
f['t'] = pd.PeriodIndex(f.ym, freq='M').astype('int64')
g = f.groupby(['CNPJ_FUNDO', 'cod'])
f['r'] = g.px.pct_change(); f['dt'] = g.t.diff()
f = f[(f.dt == 1) & f.r.notna() & (f.r.abs() < 0.6)]
R = f.groupby(['ym', 'cod']).r.median().unstack().sort_index()
R.columns = ['X:' + c for c in R.columns]
R.to_pickle(os.path.join(OUT, 'ret_ext.pkl'))
NAMES = {'AC': 'ARCA CONTINENTAL', 'AGUAS/A': 'AGUAS ANDINAS', 'ANDINAB': 'EMBOTELLADORA ANDINA', 'KOF': 'COCA-COLA FEMSA', 'WALMEX': 'WALMART DE MEXICO',
         'BSMX': 'BANCO SANTANDER MEXICO', 'ITAUCL': 'BANCO ITAU CHILE', 'MELI': 'MERCADOLIBRE', 'NU': 'NU HOLDINGS', 'XP': 'XP INC', 'GFNORTEO': 'GRUPO FINANCIERO BANORTE',
         'BOLSAA': 'BOLSA MEXICANA DE VALORES', 'VESTA': 'CORP INMOBILIARIA VESTA', 'Q': 'QUALITAS CONTROLADORA', 'RA': 'REGIONAL SAB'}
def best(s):
    v = s.dropna(); v = v[~v.str.upper().isin(['OFFSHORE', ''])]
    return v.value_counts().index[0] if len(v) else ''
nm = eq.groupby('cod').emissor.agg(best)
for k, v in NAMES.items(): nm[k] = v
json.dump({'X:' + k: v for k, v in nm.items()}, open(os.path.join(OUT, 'nomes_ext.json'), 'w'), ensure_ascii=False)
print('ações estrangeiras com preço:', R.shape[1])
# Fourth Sail: cota de cada série dos fundos offshore, retorno mensal mediano entre séries (sem side pockets)
fs = X[X.emissor.fillna('').str.upper().str.contains('FOURTH SAIL|FOURTH SHORT|FS DISC')].copy()
fs['nav'] = fs.v / fs.qt
fs['fam'] = np.where(fs.emissor.str.upper().str.contains('DISC'), 'Discovery', 'Long Short')
fs = fs[~fs.emissor.str.upper().str.contains('SIDE POCKET')]
fs = fs.groupby(['fam', 'emissor', 'ym']).nav.median().reset_index().sort_values(['emissor', 'ym'])
fs['r'] = fs.groupby('emissor').nav.pct_change()
fs['gap'] = pd.PeriodIndex(fs.ym, freq='M').astype('int64'); fs['gap'] = fs.groupby('emissor').gap.diff()
fs = fs[(fs.gap == 1) & fs.r.notna() & (fs.r.abs() < 0.6)]
S = fs.groupby(['fam', 'ym']).r.median().unstack(0)
S.to_pickle(os.path.join(OUT, 'fourth_sail.pkl'))
print(S.describe().round(4)); print(S.index.min(), S.index.max())
