"""Testa definicoes candidatas de ROIC contra os valores anuais do Wisesheets (dados SEC)."""
import json, glob, numpy as np, pandas as pd
w = pd.read_csv('data/wise_snapshot.csv').drop_duplicates('ticker').set_index('ticker')
YEARS = [2019, 2021, 2022, 2023, 2024, 2025]

def series(d, k):
    x = d['data'].get(k)
    return {} if not x else {pd.Timestamp(e).year if pd.Timestamp(e).month > 3 else pd.Timestamp(e).year - 1: v
                             for e, v in x['values'].items()}

def roic_defs(d):
    oi, pt, tx, ni = (series(d, k) for k in ('op_income', 'pretax', 'tax', 'net_income'))
    a, cl, eq, dbt, cash = (series(d, k) for k in ('assets', 'cur_liab', 'equity', 'lt_debt', 'cash'))
    out = {}
    for y in YEARS:
        try:
            t = min(max(tx[y] / pt[y], 0), 0.5) if pt.get(y) else 0.21
        except KeyError:
            t = 0.21
        nopat = oi[y] * (1 - t) if y in oi else np.nan
        g = lambda s, yy=y: s.get(yy, np.nan)
        avg = lambda s: np.nanmean([g(s, y), g(s, y - 1)])
        out[y] = {
            'A_nopat/(E+D)': nopat / (g(eq) + g(dbt)),
            'B_nopat/(E+D-C)': nopat / (g(eq) + g(dbt) - g(cash)),
            'C_nopat/(TA-CL)': nopat / (g(a) - g(cl)),
            'D_nopat/avg(TA-CL)': nopat / (avg(a) - avg(cl)),
            'E_ni/(E+D)': g(ni) / (g(eq) + g(dbt)),
            'F_ebit/(TA-CL)': g(oi) / (g(a) - g(cl)),
        }
    return out

rows = []
for f in glob.glob('data/raw/edgar/*/*.json'):
    d = json.load(open(f)); tk = d['ticker']
    if tk not in w.index: continue
    for y, defs in roic_defs(d).items():
        wv = w.loc[tk, f'roic{y}']
        try: wv = float(wv)
        except: continue
        for k, v in defs.items():
            rows.append((tk, y, k, v, wv))
df = pd.DataFrame(rows, columns=['ticker', 'year', 'defn', 'py', 'wise']).replace([np.inf, -np.inf], np.nan).dropna()
df['err'] = (df.py - df.wise).abs()
print(df.groupby('defn').err.agg(['median', 'mean', lambda s: (s < 0.02).mean(), 'count']).rename(columns={'<lambda_0>': '%<2pp'}))
df.to_csv('data/roic_calib.csv', index=False)
