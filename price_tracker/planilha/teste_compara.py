"""Compara a V3 recalculada (teste_igualdade.py) com o Python, ação por ação. Uso: python3 planilha/teste_compara.py <v3.xlsx> <out.xlsx>"""
import sys, json
import numpy as np, pandas as pd, openpyxl
sys.path[:0] = ['backtest', '.']
import roic3, engine
from backtest import load_pit, features
t = pd.Timestamp('2026-11-01')
cols = json.load(open(sys.argv[1] + '.cols.json')); O = cols['O']
ws = openpyxl.load_workbook(sys.argv[2], data_only=True)['Formula']
T = json.load(open('planilha/teste.json'))['data']
HEALTH = {'UNH', 'ELV', 'CNC', 'HUM', 'MOH', 'CI'}
num = lambda x: float(x) if isinstance(x, (int, float)) else np.nan
rows = []
for a, b in ((6, 206), (211, 233)):
    for r in range(a, b + 1):
        tk = ws[f'B{r}'].value
        if tk not in T: continue
        fin = T[tk]['setor'] == 'Financial Services' or tk in HEALTH
        pit = load_pit(tk)
        f = features(pit, t, fin, pd.Series(dtype=float, index=pd.DatetimeIndex([])))
        tri = np.nan
        if not fin:
            res = roic3.one((tk, False, [t])); tri = res[0]['roic_tri'] if res else np.nan
        roic_py = (f['roic'] if f else np.nan) if fin else tri
        g_xl = num(ws[f'U{r}'].value); dy = T[tk]['dy']
        gr = f['growth'] if f else np.nan; eps = f['eps'] if f else np.nan; price = T[tk]['preco']
        fp = (1 - g_xl / min(roic_py, 1)) / (0.085 - g_xl) if roic_py and roic_py > 0 else np.nan
        base = fp * eps * (1 + gr) ** 2 / price if np.isfinite(fp) else np.nan
        rf = np.sqrt(base) - 1 + dy if np.isfinite(base) and base > 0 else np.nan
        rc = gr + dy
        ret = (rf + rc) / 2 if np.isfinite(rf) and np.isfinite(rc) else gr
        rows.append(dict(tk=tk, fin=fin, g_py=gr, g_xl=num(ws[f'AO{r}'].value), zg_py=f['zgrowth'] if f else np.nan, zg_xl=num(ws[f'AP{r}'].value),
                         roic_py=roic_py, roic_xl=num(ws[f'{O["ROIC (usado)"]}{r}'].value), ret_py=ret, ret_xl=num(ws[f'AG{r}'].value),
                         pe_py=price / eps if eps else np.nan, pe_xl=num(ws[f'M{r}'].value), cls=ws[f'AM{r}'].value, top=ws[f'{O["Top 20"]}{r}'].value,
                         w=ws[f'{O["Peso Top 20"]}{r}'].value))
d = pd.DataFrame(rows)
for k in ('g', 'zg', 'roic', 'ret', 'pe'):
    x, y = d[f'{k}_py'], d[f'{k}_xl']; both = x.notna() & y.notna()
    diff = (x - y).abs()
    print(f'{k:5s} ambos={both.sum():3d}  só py={(x.notna() & y.isna()).sum():3d}  só xl={(x.isna() & y.notna()).sum():3d}  '
          f'iguais(<0,1pp)={(diff[both] < 1e-3).mean():.0%}  dif mediana={diff[both].median():.5f}')
d.to_csv('planilha/teste_compara.csv', index=False)
bad = d[(d.roic_py - d.roic_xl).abs() > 1e-3]
print(bad[['tk', 'fin', 'roic_py', 'roic_xl']].head(20).to_string())
print(d[d.top.notna()][['tk', 'top', 'w', 'ret_xl', 'roic_xl', 'g_xl']].sort_values('top').to_string())
