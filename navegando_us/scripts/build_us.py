# Navegando US: junta posições (us_attr.json) e classificação (classe.json) no formato do app (mesmo do Navegando LatAm, só a base 13F).
import json, gzip, base64, pathlib, datetime, pandas as pd, numpy as np, re
W = pathlib.Path('/home/user/work/us')
A = json.load(open(W / 'us_attr.json')); FC = json.load(open(W / 'classe.json'))
P = lambda m: pd.Period(m, 'M')
cid = lambda e: 'u' + e
G = {}
for gid, f in A['fundos'].items():
    G['f13-' + gid] = {'n': f['nome'], 'b': 'f13', 'dates': f['datas'], 'p': {cid(e): v[0] for e, v in f['p'].items()}, 'usd': f['TOT'],
                       'sub': 'Hedge fund ou ativista' if f['tipo'] == 'hedge' else 'Long-only'}
NOW = max(g['dates'][-1] for g in G.values())
def idx_at(g, m, back=5):
    best = None
    for j, d in enumerate(g['dates']):
        if d <= m and (P(m) - P(d)).n <= back: best = j
    return best
CUR = {}
for gid, g in G.items():
    j = len(g['dates']) - 1
    if (P(NOW) - P(g['dates'][j])).n > 9: continue
    target = P(g['dates'][j]) - 12; jp = None
    for k, d in enumerate(g['dates']):
        if abs((P(d) - target).n) <= 3 and (jp is None or abs((P(d) - target).n) < abs((P(g['dates'][jp]) - target).n)): jp = k
    CUR[gid] = (j, jp)
SMALL = {'Of', 'And', 'The', 'De', 'Du', 'For', 'In', 'On'}
def nice(s):
    s = re.sub(r'\s*[-–]\s*Class [A-Z]\b|\bCl(ass)? [A-Z]\b|\b(Common Stock|Cmn|Cap Stk|Ord|Shs|Sponsored|Spons|Adr|Ads|New|Del|/[A-Z]{2}/?)\b|\(The\)', ' ', s, flags=re.I)
    s = re.sub(r'\s+Com$', '', re.sub(r'\s+', ' ', s)).strip(' ,.-/'); s = re.sub(r'^Amazon Com\b', 'Amazon.com', s, flags=re.I)
    if s.isupper() or s.islower(): s = ' '.join(w.capitalize() if w.upper() not in ('ETF', 'ADR', 'LLC', 'PLC', 'NV', 'SA', 'AG', 'SE', 'LP') else w.upper() for w in s.split())
    s = ' '.join(w if k == 0 or w not in SMALL else w.lower() for k, w in enumerate(s.split()))
    return {'Amazon Inc': 'Amazon.com', 'Booking Inc': 'Booking Holdings'}.get(s, s)
def fcx(e): x = FC.get(e, ['Outros', 'Outros', '', '']); return x + ['', ''][len(x) - 2:] if len(x) < 4 else x
emp = {cid(e): {'n': nice(fcx(e)[2] or v[0]), 't': fcx(e)[3], 's': fcx(e)[1], 'p': fcx(e)[0]} for e, v in A['emp'].items()}
H = {c: [] for c in emp}
for gid, (j, jp) in CUR.items():
    g = G[gid]
    for c, w in g['p'].items():
        wn = (w[j] or 0) / 1e4; wp = None if jp is None else (w[jp] or 0) / 1e4
        if wn <= 0 and not wp: continue
        H[c].append([gid, round(wn, 5), None if wp is None else round(wp, 5), round(wn * (g['usd'][j] or 0), 2)])
Q = [str(p) for p in pd.period_range('2016-03', NOW, freq='3M')]
QS = {c: [[0, 0.0] for _ in Q] for c in emp}
for gid, g in G.items():
    js = [idx_at(g, q) for q in Q]
    for c, w in g['p'].items():
        for qi, j in enumerate(js):
            if j is None: continue
            x = (w[j] or 0) / 1e4
            if x > 0: QS[c][qi][0] += 1; QS[c][qi][1] += x * (g['usd'][j] or 0)
MES = [str(p) for p in pd.period_range('2016-01', NOW, freq='M')]
def pxm(d):
    out, cur = [], None
    for m in MES:
        if m in d: cur = d[m]
        out.append(cur)
    return out
comb = {'map': {'f13:' + e: cid(e) for e in A['emp']}, 'now': NOW, 'q': Q, 'mes': MES, 'tris': [], 'g': {}, 'e': {}}
for gid, g in G.items():
    j = len(g['dates']) - 1
    comb['g'][gid] = {'n': g['n'], 'b': 'f13', 'sub': g['sub'], 'last': g['dates'][j], 'usd': round(g['usd'][j] or 0, 1), 'cur': gid in CUR}
for c, e in emp.items():
    if e['s'] == 'Fundos e ETFs' or e['p'] == 'ETFs': continue
    if not H[c] and not any(h[0] for h in QS[c]): continue
    d = A['px'].get(c[1:])
    comb['e'][c] = {'n': e['n'], 't': e['t'], 's': e['s'], 'p': e['p'], 'h': H[c], 'qn': [h[0] for h in QS[c]], 'qv': [round(h[1], 1) for h in QS[c]], 'ag': None, 'px': pxm(d) if d else None}
# gestoras: países da carteira (último trimestre), tipo
for gid, f in A['fundos'].items():
    mx = {}
    for e, (wv, _) in f['p'].items():
        w = (wv[-1] or 0) / 1e4
        if w > 0: k = FC.get(e, ['Outros'])[0]; mx[k] = mx.get(k, 0) + w
    tt = sum(mx.values()) or 1
    f['mix'] = [[k, round(v / tt, 3)] for k, v in sorted(mx.items(), key=lambda kv: -kv[1]) if v / tt >= 0.02]
    f['pais'] = f['tipo']
f13 = {'fundos': A['fundos'], 'emp': {e: [emp[cid(e)]['n']] for e in A['emp']}, 'fc': FC}
D = {'gerado_em': datetime.date.today().strftime('%d/%m/%Y'), 'comb': comb, 'fpe': {'fundos': {}, 'meses': [], 'ref': {'R': []}}, 'fus': {'fundos': {}}, 'f13': f13}
raw = json.dumps(D, ensure_ascii=False, separators=(',', ':')).encode()
b64 = base64.b64encode(gzip.compress(raw, 9, mtime=0)).decode()
html = (W / 'src/app.html').read_text().replace('{{DATA}}', b64)
out = pathlib.Path('/tmp/claude-0/-home-user-Geral/fcac98de-4843-5238-88c1-7d682acd2098/scratchpad/us/index.html'); out.parent.mkdir(exist_ok=True); out.write_text(html)
print('empresas', len(comb['e']), 'gestoras', len(G), 'atuais', len(CUR), 'agora', NOW, '·', len(raw) // 1024, 'KB de dados;', len(html) // 1024, 'KB de página')
