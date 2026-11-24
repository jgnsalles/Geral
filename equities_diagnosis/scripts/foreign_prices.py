"""Preço mensal em R$ de ações estrangeiras = mediana entre fundos de valor de mercado ÷ quantidade (bloco 7 da CDA).
Retorno de preço (sem dividendos). Também a cota dos fundos offshore da Fourth Sail (via fundos da Tordesilhas).
Uso: python3 foreign_prices.py <foreign.pkl> <saida_dir>"""
import sys, os, json
import pandas as pd, numpy as np
FP, OUT = sys.argv[1:3]
X = pd.read_pickle(FP)
X = X[(X.qt > 0) & (X.v > 0)].copy()
X['cod'] = X.cod.fillna('').str.strip().str.upper()
eq = X[X.tpa.isin(['Outros', 'Ação ordinária', 'Ação preferencial', 'Depository Receipt no Exterior(DR)']) & ~X.cod.isin(['', 'FUNDO OFF', 'OFFSHORE'])].copy()
eq['px'] = eq.v / eq.qt
P = eq.groupby(['ym', 'cod']).px.median().unstack()
R = P.pct_change(fill_method=None)
per = pd.PeriodIndex(P.index, freq='M').astype('int64')
R[pd.Series(per, index=P.index).diff().fillna(1).values != 1] = np.nan
R = R.mask((R > 2) | (R < -0.85))
R.columns = ['X:' + c for c in R.columns]
R.to_pickle(os.path.join(OUT, 'ret_ext.pkl'))
nm = eq.groupby('cod').emissor.agg(lambda s: s.value_counts().index[0] if s.notna().any() else '')
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
