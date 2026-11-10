# Retornos mensais com dividendos, dez/2023 em diante (segue prices.py / prices_fix.py do repo gestoras).
# Fonte principal: Yahoo Finance (adjclose). Ações que mudaram de código: o Yahoo guarda a série no código novo.
# Sem Yahoo: COTAHIST da B3 (fechamento bruto, com correção de desdobramento pela quantidade dos fundos).
import pandas as pd, numpy as np, json, os, sys
W = '/home/user/work'; Y = '/home/user/raw/yahoo'
H = pd.read_pickle(W + '/holdings.pkl')
old = pd.concat([pd.read_csv(W + '/old/posicoes_1.csv'), pd.read_csv(W + '/old/posicoes_2.csv')])
RENAME = json.load(open(W + '/rename.json'))
b = pd.read_pickle(W + '/b3_daily.pkl'); b['ym'] = b.dt.str[:4] + '-' + b.dt.str[4:6]
b3 = b.sort_values('dt').groupby(['tk', 'ym']).tail(1).set_index(['tk', 'ym']).close.unstack(0)
b3.to_pickle(W + '/b3_monthly.pkl')
pd.Series(b.sort_values('dt').groupby('tk').nome.last()).to_pickle(W + '/names.pkl')
def yser(t):
    for s in [t] + ([RENAME[t]] if t in RENAME else []):
        f = f'{Y}/{s}.json'
        if not os.path.exists(f): continue
        try: j = json.load(open(f))['chart']['result'][0]
        except Exception: continue
        if not j or 'timestamp' not in j: continue
        adj = j['indicators'].get('adjclose', [{}])[0].get('adjclose')
        if not adj: continue
        a = pd.Series(adj, index=pd.to_datetime(j['timestamp'], unit='s')).dropna()
        if len(a) < 5: continue
        return a.groupby(a.index.strftime('%Y-%m')).last()
    return None
known = set(b3.columns)
tks = sorted(set(H.tk) | set(old.tk))
months = sorted(b3.index)
months = [m for m in months if m >= '2023-11']
yh = {}
for t in tks:
    s = yser(t)
    if s is not None: yh[t] = s
yh = pd.DataFrame(yh).reindex(months)
br = b3.reindex(months).pct_change(fill_method=None)
yr = yh.pct_change(fill_method=None)
# último mês do Yahoo pode ser parcial (mês corrente): descartado depois pelo corte da série
q = H[H.sign > 0].groupby(['tk', 'ym', 'id']).q.sum().unstack('id')
ret = pd.DataFrame(index=months, columns=tks, dtype=float); src = pd.DataFrame('', index=months, columns=tks)
for t in tks:
    r = br[t] if t in br else pd.Series(np.nan, index=months)
    if t in q.index.get_level_values(0):
        g = q.loc[t].reindex(months); k = (g / g.shift(1)).median(axis=1)
        split = (k.round(2).sub(1).abs() > 0.3) & (((1 + r) * k - 1).abs() < 0.25) & (r.abs() > 0.3)
        r = r.where(~split, (1 + r) * k - 1)
    if t in yr:
        ret[t] = yr[t].where(yr[t].notna(), r); src[t] = np.where(yr[t].notna(), 'Y', np.where(r.notna(), 'B', ''))
    else:
        ret[t] = r; src[t] = np.where(r.notna(), 'B', '')
F = [2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100, 200]; F = F + [1 / x for x in F]
for t in ret.columns:
    for ym in ret.index[(src[t] == 'B') & ((ret[t] > 1.0) | (ret[t] < -0.6))]:
        ratio = 1 + ret.at[ym, t]; best = min(F, key=lambda k: abs(np.log(ratio / k)))
        ret.at[ym, t] = ratio / best - 1 if abs(np.log(ratio / best)) < 0.25 else np.nan
ret = ret.clip(-0.9, 3)

# Proventos (Fundamentus) somados nos meses só com B3, como em divadj.py / prices_fix.py
import requests, re, time
D = b[['tk', 'dt', 'close']].copy(); D['dt'] = pd.to_datetime(D.dt, format='%Y%m%d')
need = [t for t in ret.columns if (src[t].loc['2024-01':] == 'B').any()]
divs = []
for t in need:
    f = f'/home/user/raw/fund/{t}.html'
    if not os.path.exists(f):
        r = requests.get('https://www.fundamentus.com.br/proventos.php', params=dict(papel=t, tipo=2), headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        open(f, 'wb').write(r.content); time.sleep(0.3)
    s = open(f, encoding='latin1').read()
    for d, v, tp, qq in re.findall(r'<td>(\d\d/\d\d/\d{4})</td>\s*<td>([\d.,]+)</td>\s*<td>([^<]+)</td>\s*<td>[^<]*</td>\s*<td>(\d+)</td>', s):
        divs.append((t, pd.to_datetime(d, format='%d/%m/%Y'), float(v.replace('.', '').replace(',', '.')) / int(qq)))
dv = pd.DataFrame(divs, columns=['tk', 'dt', 'val']); dv = dv[dv.dt >= '2023-12-01']
out = []
for t, g in dv.groupby('tk'):
    px = D[D.tk == t].sort_values('dt')
    if px.empty: continue
    mm = pd.merge_asof(g.sort_values('dt'), px[['dt', 'close']], on='dt', direction='backward'); mm['y'] = mm.val / mm.close; out.append(mm)
nD = 0
if out:
    dv = pd.concat(out); dv = dv[dv.y.between(0, 0.25)]; dv['ym'] = dv.dt.dt.strftime('%Y-%m')
    dy = dv.groupby(['ym', 'tk']).y.sum().unstack()
    for t in dy.columns:
        d = dy[t].reindex(ret.index).fillna(0); m = (src[t] == 'B') & ret[t].notna() & (d > 0)
        ret.loc[m, t] = (1 + ret.loc[m, t]) * (1 + d[m]) - 1; src.loc[m, t] = 'BD'; nD += int(m.sum())
print('meses com proventos somados (B3+Fundamentus):', nD)
# Sem cotação em bolsa (ex.: Compass PASS5/PASS6): preço implícito na CDA (valor ÷ quantidade, mediana dos fundos)
hp = H[(H.sign > 0) & (H.q > 0)].assign(px=lambda d: d.v / d.q).groupby(['ym', 'tk']).px.median().unstack().reindex(months)
nC = 0
for t in hp.columns:
    if t not in ret: continue
    rr = hp[t].pct_change(fill_method=None); m = ret[t].isna() & rr.notna() & (rr.abs() < 0.6)
    ret.loc[m, t] = rr[m]; src.loc[m, t] = 'C'; nC += int(m.sum())
print('meses com preço implícito da CDA:', nC)
ret.to_pickle(W + '/ret.pkl'); src.to_pickle(W + '/retsrc.pkl')
# Ibovespa (fechamento de fim de mês, Yahoo ^BVSP)
j = json.load(open(Y + '/^BVSP.json'))['chart']['result'][0]
ib = pd.Series(j['indicators']['quote'][0]['close'], index=pd.to_datetime(j['timestamp'], unit='s')).dropna()
ib = ib.groupby(ib.index.strftime('%Y-%m')).last(); ib.to_pickle(W + '/ibov.pkl')
held = H[(H.ym >= '2024-01')].assign(a=H.w.abs()).groupby('tk').a.sum()
cov = src.loc['2024-01':]
print('tickers', len(tks), 'yahoo', len(yh.columns))
print('peso mantido sem retorno no mês:')
miss = []
for (t, ym), a in H[(H.ym >= '2024-01')].assign(a=H.w.abs()).groupby(['tk', 'ym']).a.sum().items():
    if ym in ret.index and t in ret and np.isnan(ret.at[ym, t]): miss.append((t, ym, a))
mm = pd.DataFrame(miss, columns=['tk', 'ym', 'a'])
print(mm.groupby('tk').a.agg(['sum', 'size']).sort_values('sum', ascending=False).head(30).to_string())
print('fonte B3 (sem dividendos):', cov.isin(['B','BD']).sum().sum(), 'Yahoo:', (cov == 'Y').sum().sum())
