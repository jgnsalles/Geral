"""Retorno total mensal por ticker: fechamento B3 + proventos em dinheiro + desdobramento/grupamento/bonificação.
Índice diário: I_t = I_{t-1} * (P_t * m_t + D_t) / P_{t-1}, com m_t = multiplicador de ações e D_t = proventos por ação
cuja data-com foi o pregão anterior. Retorno do mês = I(fim do mês) / I(fim do mês anterior) - 1.
Uso: python3 b3_returns.py <precos.pkl> <pasta eventos> <holdings.pkl> <saida.pkl>"""
import sys, os, json, glob, math
import pandas as pd, numpy as np
PX, EV, HP, OUT = sys.argv[1:5]
B = pd.read_pickle(PX).sort_values(['tk', 'dt'])
H = pd.read_pickle(HP); H['tk'] = H.tk.str.strip().str.upper()
isin = H.dropna(subset=['isin']).groupby('tk').isin.agg(lambda s: s.value_counts().index[0])
CLS = {'3': 'ON', '4': 'PN', '5': 'PNA', '6': 'PNB', '7': 'PNC', '8': 'PND', '11': 'UNT'}
num = lambda s: float(str(s).replace('.', '').replace(',', '.')) if s not in (None, '') else np.nan
dt = lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce')
EVS = {}
for f in glob.glob(os.path.join(EV, '*.json')):
    d = json.load(open(f)); EVS[d['code']] = d
log = {'div_ok': 0, 'div_bad_price': 0, 'split_ok': 0, 'split_skip': 0}
out = {}
for tk, g in B.groupby('tk'):
    g = g.set_index('dt').close
    g = g[~g.index.duplicated()]
    days = g.index
    code, cls = tk[:4], CLS.get(tk[4:])
    ev = EVS.get(code, {'cash': [], 'stock': []})
    D = pd.Series(0.0, index=days); Mu = pd.Series(1.0, index=days)
    nxt = lambda d: days[days.searchsorted(d, side='right')] if days.searchsorted(d, side='right') < len(days) else None
    # proventos em dinheiro
    for x in ev['cash']:
        if cls is None or x.get('typeStock') != cls:
            continue
        dc = dt(x.get('lastDatePriorEx')); v = num(x.get('valueCash')); q = num(x.get('quotedPerShares')) or 1
        if pd.isna(dc) or not np.isfinite(v):
            continue
        ex = nxt(dc)
        if ex is None:
            continue
        pref = g[:dc]
        if pref.empty:
            continue
        p0 = pref.iloc[-1]; pb3 = num(x.get('closingPricePriorExDate'))
        if np.isfinite(pb3) and pb3 > 0 and abs(math.log(p0 / (pb3 / q))) > 0.2:   # cotação não bate: outro emissor ou outra unidade
            log['div_bad_price'] += 1; continue
        if v / q / p0 > 0.5:
            continue
        D[ex] += v / q; log['div_ok'] += 1
    # eventos com ações: confere o multiplicador pela cotação antes e depois
    my_isin = isin.get(tk); seen = set()
    for x in ev['stock']:
        kx = (x.get('label'), x.get('factor'), x.get('lastDatePrior'), x.get('isinCode') if my_isin else None)
        if kx in seen: continue
        seen.add(kx)
        lab = x.get('label', '')
        if lab not in ('DESDOBRAMENTO', 'GRUPAMENTO', 'BONIFICACAO'):
            continue
        if my_isin and x.get('isinCode') and x['isinCode'] != my_isin:
            continue
        dc = dt(x.get('lastDatePrior')); f = num(x.get('factor'))
        if pd.isna(dc) or not np.isfinite(f) or f <= 0:
            continue
        ex = nxt(dc); pref = g[:dc]
        if ex is None or pref.empty:
            continue
        ratio = g[ex] / pref.iloc[-1]          # ~ 1/m
        cands = [1 + f / 100, f, 1 / f, f / 100]
        m = min(cands, key=lambda c: abs(math.log(ratio * c)))
        if abs(math.log(ratio * m)) < 0.3:
            Mu[ex] *= m; log['split_ok'] += 1
        else:
            log['split_skip'] += 1
    # saltos de um pregão para outro sem evento registrado: fator redondo = grupamento (alta >= 4x, tolerância 15%)
    # ou desdobramento (queda <= 1/4, tolerância 3%); quedas reais de um dia (ex.: Americanas jan/23) ficam
    FF = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 20, 25, 30, 40, 50, 60, 75, 80, 100, 150, 200, 250, 500, 1000]
    pv = g.values
    for k in range(1, len(pv)):
        if Mu.iloc[k] != 1.0 or not (pv[k - 1] > 0) or D.iloc[k] > 0: continue
        q = pv[k] / pv[k - 1]
        if not (q > 0): continue
        if q >= 50 or q <= 0.02:  # mudança de cotação (lote de mil -> unidade) ou evento enorme: neutraliza o dia
            Mu.iloc[k] = 1 / q; log['quote_change'] = log.get('quote_change', 0) + 1; continue
        if q >= 4:
            f = min(FF, key=lambda f: abs(math.log(q / f)))
            if abs(math.log(q / f)) < 0.15: Mu.iloc[k] = 1 / f; log['split_infer_up'] = log.get('split_infer_up', 0) + 1
        elif q <= 0.25:
            f = min(FF, key=lambda f: abs(math.log(q * f)))
            if abs(math.log(q * f)) < 0.03: Mu.iloc[k] = f; log['split_infer_dn'] = log.get('split_infer_dn', 0) + 1
    # índice de retorno total
    p = g.values; idx = np.ones(len(p))
    for k in range(1, len(p)):
        idx[k] = idx[k - 1] * (p[k] * Mu.iloc[k] + D.iloc[k]) / p[k - 1]
    s = pd.Series(idx, index=days)
    me = s.groupby(days.strftime('%Y-%m')).last()
    # mês sem negócio no fim: não inventa retorno
    last_day = pd.Series(days, index=days).groupby(days.strftime('%Y-%m')).last()
    r = me.pct_change()
    gap = (pd.PeriodIndex(me.index, freq='M').astype('int64').to_series(index=me.index).diff() != 1)
    r[gap] = np.nan
    out[tk] = r
R = pd.DataFrame(out).sort_index()
# saltos sem evento da B3: só descarta o que parece erro, não quebra real.
#  (a) vai e volta: salto grande seguido do movimento contrário no mês seguinte
#  (b) razão muito próxima de um fator redondo de desdobramento/grupamento (±3%) = evento não registrado
import math
F = [2, 3, 4, 5, 8, 10, 20, 25, 50, 100, 200, 1000]; F = F + [1 / x for x in F]
big = (R > 1.5) | (R < -0.75)
nxt = R.shift(-1)
rev = big & ((np.log1p(R.clip(lower=-0.999)) + np.log1p(nxt.clip(lower=-0.999))).abs() < 0.3)
rnd = big & (1 + R).apply(lambda col: col.map(lambda v: (not np.isnan(v)) and v > 0 and min(abs(math.log(v / f)) for f in F) < 0.03))
bad = rev | rnd
print('meses grandes:', int(big.sum().sum()), '| descartados (vai e volta):', int(rev.sum().sum()), '| (fator redondo):', int((rnd & ~rev).sum().sum()), '| mantidos como reais:', int((big & ~bad).sum().sum()))
R = R.mask(bad)
R.to_pickle(OUT); print(R.shape, log)
V = B.assign(ym=B.dt.dt.strftime('%Y-%m')).groupby(['ym', 'tk']).vol.sum().unstack()
V.to_pickle(OUT.replace('.pkl', '_vol.pkl'))
LT = B.groupby('tk').dt.max().dt.strftime('%Y-%m'); LT.to_pickle(OUT.replace('.pkl', '_last.pkl'))
