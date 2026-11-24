"""Série mensal de retorno total por empresa (raiz de 4 letras), usando no mês a classe mais negociada nos 12 meses
anteriores. Empresas que saíram da bolsa (falência, fechamento de capital, incorporação) ficam com a série até o último pregão.
Uso: python3 emp_build.py <ret.pkl> <nomes.json> <tags.json> <pasta eventos> <perf.json> <saida.json>"""
import sys, os, json, glob
import pandas as pd, numpy as np
RP, NJ, TJ, EV, PJ, OUT = sys.argv[1:7]
R = pd.read_pickle(RP); V = pd.read_pickle(RP.replace('.pkl', '_vol.pkl')); LT = pd.read_pickle(RP.replace('.pkl', '_last.pkl'))
M = json.load(open(PJ))['meses']; MI = {m: i for i, m in enumerate(M)}
R = R.reindex(M); V = V.reindex(M).fillna(0)
NM = json.load(open(NJ)); TG = json.load(open(TJ))
for f in glob.glob(os.path.join(EV, '*.json')):
    d = json.load(open(f))
    if d.get('tradingName') and d['code'] not in NM: NM[d['code']] = d['tradingName']
VA = pd.read_pickle(os.path.join(os.path.dirname(os.path.abspath(OUT)), 'vol_anual.pkl'))
esp = VA.drop_duplicates('tk', keep='last').set_index('tk').espec
fund = {t for t, e in esp.items() if str(e).startswith(('CI', 'ETF', 'DRN', 'BDR'))}
R = R[[c for c in R.columns if c not in fund and not any(w in str(NM.get(c[:4], '')).upper() for w in ('ISHARES', ' ETF', 'FUNDO', 'IT NOW', 'TREND '))]]
TM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(OUT)), 'tickermap.json')))
REN = TM['rename']
def ren(r):
    seen = set()
    while r in REN and r not in seen: seen.add(r); r = REN[r]
    return r
rootof = {c: ren(c[:4]) for c in R.columns}
roots = sorted(set(rootof.values()))
V12 = V.rolling(12, min_periods=1).sum().shift(1).fillna(V)   # volume dos 12 meses anteriores
last_all = M[-1]
out = {'meses': M, 'e': {}}
for r in roots:
    cols = [c for c in R.columns if rootof[c] == r]
    rr = R[cols]; vv = V12[cols]
    vw = vv.where(rr.notna()).fillna(-1)                   # classe mais líquida com retorno no mês
    pick = vw.idxmax(axis=1).where(vw.max(axis=1) >= 0)
    ser = pd.Series([rr.at[m, t] if isinstance(t, str) else np.nan for m, t in zip(M, pick)], index=M)
    vol = V[cols].sum(axis=1)
    if ser.notna().sum() < 3: continue
    o = MI[ser.first_valid_index()]; lastm = max(LT.get(c, '0000') for c in cols)
    li = MI.get(lastm, len(M) - 1); li = min(li, MI[ser.last_valid_index()] if ser.last_valid_index() else li)
    tk_last = pick.dropna().iloc[-1] if pick.notna().any() else cols[0]
    out['e'][r] = {'n': NM.get(r, r), 'tk': tk_last, 'o': o,
                   'r': [None if not np.isfinite(v) else int(round(v * 1e6)) for v in ser.iloc[o:li + 1]],
                   'v': [int(round(x / 1e6)) for x in vol.iloc[o:li + 1]],   # R$ mi negociados no mês
                   'dl': lastm < '2026-09',                                   # saiu da bolsa
                   'ib': any(c in TG['ibov'] for c in cols), 'sm': any(c in TG['smll'] for c in cols), 'h': r in TG['held']}
print('empresas:', len(out['e']), '| fora da bolsa:', sum(x['dl'] for x in out['e'].values()))
json.dump(out, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print('bytes', os.path.getsize(OUT))
