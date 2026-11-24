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
    my_isin = isin.get(tk)
    for x in ev['stock']:
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
# saltos impossíveis sem evento explicado: descarta o mês
bad = (R > 1.5) | (R < -0.75)
print('meses descartados por salto:', int(bad.sum().sum()))
R = R.mask(bad)
R.to_pickle(OUT); print(R.shape, log)
