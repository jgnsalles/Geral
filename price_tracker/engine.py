"""Motor deterministico: replica a logica da aba Formula (Growth, zGrowth, ROIC, zROIC, g, P/E justo, retorno, classe)."""
import json, pathlib
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).parent
TABLE = pd.read_csv(HERE / 'data/class_table.csv')
TH = json.loads((HERE / 'data/thresholds.json').read_text())
WACC = 0.085
LOOKUP = {''.join(r[['growth', 'zgrowth', 'roic', 'zroic', 'ret']]): r['category'] for _, r in TABLE.iterrows()}
ORDER = dict(zip(TABLE.category, TABLE.order))

def growth_metric(g):
    """T = media(mediana(g), media(g), media(dois ultimos)) -- AGGREGATE(12/1) ignorando erros."""
    ok = lambda v: [x for x in v if x is not None and np.isfinite(x)]
    allg, last2 = ok(g), ok(list(g)[-2:])  # ultimos dois *slots*, como AGGREGATE(1,2,R:S)
    if not allg: return np.nan
    return float(np.mean([np.median(allg), np.mean(allg), np.mean(last2) if last2 else np.nan]))

def cv(values, mean):
    v = [x for x in values if x is not None and np.isfinite(x)]
    if len(v) < 2 or not np.isfinite(mean) or mean == 0: return np.nan
    return float(np.std(v) / mean)  # STDEV.P

def roic_metric(series):
    v = [x for x in series if x is not None and np.isfinite(x)]
    if not v: return np.nan
    return float(np.mean([np.mean(v[-3:]), np.mean(v)]))

def rank_g(growth, top=0.07):
    """U = top - (RANK.EQ desc - 1) * 3.5% / (N - 1). Excel: bloco geral (linhas 6-206) com top 7%;
    bloco de financeiras (211-233) ranqueado entre si com top 6,5%."""
    r = growth.dropna().to_numpy()
    rk = growth.apply(lambda x: np.nan if pd.isna(x) else 1 + (r > x).sum())
    return top - (rk - 1) * 0.035 / (len(r) - 1)

def block_g(df, col='growth'):
    """Aplica rank_g por bloco (coluna 'fin': True para financeiras), ranqueando pela coluna `col`."""
    out = pd.Series(np.nan, index=df.index)
    for fin, top in ((False, 0.07), (True, 0.065)):
        m = df['fin'] == fin
        if m.any(): out[m] = rank_g(df.loc[m, col], top)
    return out

def fair_pe(g, roic):
    return (1 - g / roic) / (WACC - g)

def code(row):
    G, zG, R, zR, Ret = row['growth'], row['zgrowth'], row['roic'], row['zroic'], row['ret']
    if any(pd.isna(x) for x in (G, zG, R, zR, Ret)): return None
    c = ('H' if G > TH['Growth_Hi'] else 'O' if G >= TH['Growth_Lo'] else 'L')
    c += ('O' if zG < TH['zGrowth'] else 'P')
    c += ('G' if R > TH['Roic_Hi'] else 'O' if R >= TH['Roic_Lo'] else 'L')
    c += ('N' if zR < TH['zRoic'] else 'U')
    c += ('G' if Ret > TH['Return_Hi'] else 'O' if Ret >= TH['Return_Lo'] else 'B')
    return c

def classify(df):
    df = df.copy()
    df['code'] = df.apply(code, axis=1)
    df['category'] = df['code'].map(LOOKUP).fillna('Do not Waste Time')
    df['order'] = df['category'].map(ORDER).fillna(11).astype(int)
    return df
