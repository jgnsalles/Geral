"""Brazil Downturn, passo 8: série trimestral longa do fluxo total (2006T1–2026T3, mesma medida da parte 1) e regimes por trimestre,
gravada no JSON da parte 2 (chave serie_longa). Uso: python3 08_serie_longa.py <out> <ust10.csv> <passivo.json>"""
import sys, os, json
import pandas as pd, numpy as np
OUT, UST, PJ = sys.argv[1:4]
S = pd.read_pickle(os.path.join(OUT, 'amostra_mes.pkl')); IX = pd.read_csv(os.path.join(OUT, 'indices.csv'), index_col=0)
ust = pd.read_csv(UST); ust.columns = ['d', 'v']; ust['v'] = pd.to_numeric(ust.v, errors='coerce'); ust = ust.dropna(); ust = ust.groupby(ust.d.str[:7]).v.last() / 100
S['q'] = pd.PeriodIndex(S.ym, freq='M').asfreq('Q').astype(str); S['m0'] = S.groupby(['gid', 'q']).ym.transform('min')
g = S.groupby('q').apply(lambda x: pd.Series({'f': x.flow.sum(), 'b': x[x.ym == x.m0].pl_ant.sum(), 'pos': (x.groupby('gid').flow.sum() > 0).mean(), 'h': x[x.ym == x.ym.max()].pl.sum()}))
rows = []
for q, r in g.iterrows():
    if q > '2026Q3': continue
    p = pd.Period(q, 'Q'); m0 = str(p.asfreq('M', 'start')); m1 = min(str(p.asfreq('M', 'end')), IX.index.max()); mp = str(pd.Period(m0, 'M') - 1); m12 = str(pd.Period(m1, 'M') - 11)
    ib, cd = IX.ibov, IX.cdi; aa = lambda y: (1 + cd.get(y, np.nan)) ** 12 - 1; fr = r.f / r.b
    d = dict(q=q, fr=fr, f=r.f / 1e9, h=r.h / 1e9, pos=r.pos, ibov_q=float(np.prod(1 + ib.loc[m0:m1]) - 1), ibov_12=float(np.prod(1 + ib.loc[m12:m1]) - 1),
             cdi=aa(m1), dcdi_q=aa(m1) - aa(mp), ust=ust.get(m1), dust_q=ust.get(m1, np.nan) - ust.get(mp, np.nan))
    d['st_ibov_q'] = 'alta' if d['ibov_q'] > 0 else 'baixa'; d['st_ibov_12'] = 'alta' if d['ibov_12'] > 0 else 'baixa'
    d['st_selic'] = 'alta' if d['dcdi_q'] > 0.0025 else 'baixa'; d['st_ust'] = 'alta' if (d['dust_q'] or 0) > 0 else 'baixa'; d['st_fluxo'] = 'alta' if fr > 0 else 'baixa'
    rows.append({k: (None if isinstance(v, float) and np.isnan(v) else (round(v, 5) if isinstance(v, float) else v)) for k, v in d.items()})
P = json.load(open(PJ)); P['serie_longa'] = rows; json.dump(P, open(PJ, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(rows), rows[0]['q'], rows[-1]['q'])
