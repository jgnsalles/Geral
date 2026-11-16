"""Compara a V3 nova recalculada com o Python (mesmos dados). Uso: python3 planilha/teste_v3novo_compara.py <v3.xlsx> <recalculado.xlsx>"""
import sys, json
import numpy as np, pandas as pd, openpyxl
sys.path[:0] = ['backtest', '.']
import roic3, top_n
from backtest import load_pit, features
t = pd.Timestamp('2026-11-01')
cols = json.load(open(sys.argv[1] + '.cols.json')); CC, R0, R1 = cols['CC'], cols['R0'], cols['R1']
wb = openpyxl.load_workbook(sys.argv[2], data_only=True); a, c = wb['Ações'], wb['Cálculo']
T = json.load(open('planilha/teste.json'))['data']
num = lambda v: v if isinstance(v, (int, float)) and not isinstance(v, bool) else np.nan
rows = []
for r in range(R0, R1 + 1):
    tk = a[f'A{r}'].value
    if tk not in T: continue
    fin = T[tk]['setor'] == 'Financial Services' or tk in {'UNH', 'ELV', 'CNC', 'HUM', 'MOH', 'CI'}
    f = features(load_pit(tk), t, fin, pd.Series(dtype=float, index=pd.DatetimeIndex([])))
    tri = np.nan
    if not fin:
        res = roic3.one((tk, False, [t])); tri = res[0]['roic_tri'] if res else np.nan
    rows.append(dict(tk=tk, fin=fin, g_py=f['growth'] if f else np.nan, g_xl=num(a[f'H{r}'].value), roic_py=(f['roic'] if f else np.nan) if fin else tri,
                     roic_xl=num(a[f'I{r}'].value), flag=a[f'N{r}'].value))
d = pd.DataFrame(rows)
for k in ('g', 'roic'):
    x, y = d[f'{k}_py'], d[f'{k}_xl']; b = x.notna() & y.notna(); df = (x - y).abs()[b]
    print(f'{k}: n={b.sum()} iguais(<0,1pp)={(df < 1e-3).mean():.0%} até 2pp={(df < .02).mean():.0%} dif mediana={df.median()*100:.2f}pp  corr de ordem={x[b].corr(y[b], method="spearman"):.3f}  só py={(x.notna()&y.isna()).sum()} só xl={(x.isna()&y.notna()).sum()}')
nf = d[~d.fin]; b = nf.roic_py.notna() & nf.roic_xl.notna()
print('mesmo lado de 12%:', ((nf.roic_py[b] >= .12) == (nf.roic_xl[b] >= .12)).mean())
d['dif'] = (d.roic_py - d.roic_xl).abs(); print(d.sort_values('dif', ascending=False).head(12)[['tk', 'fin', 'roic_py', 'roic_xl']].to_string())
print(d.flag.value_counts().head(8))
