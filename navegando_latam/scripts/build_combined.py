# Visão combinada por empresa: junta AFPs do Peru (SBS), fundos LatAm dos EUA (N-PORT), gestoras LatAm (13F) e o total dos fundos dos EUA.
# Liga a mesma empresa entre as bases por ISIN, CUSIP (9 e 6 primeiros dígitos = emissor) e, em último caso, pelo nome normalizado.
import json, re, glob, unicodedata, numpy as np, pandas as pd
W = '/home/user/work/latam'
pe = json.load(open(W + '/pe_attr.json')); us = json.load(open(W + '/us_attr.json')); f13 = json.load(open(W + '/f13_attr.json'))
L = json.load(open(W + '/latam.json')); agg = L['us']; SET = json.load(open(W + '/setores.json'))
pen = pd.read_pickle(W + '/pen.pkl')
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'\b(S\.?A\.?B?\.?( DE C\.?V\.?)?|S\.?A\.?A\.?|SA|SAB|SAA|DE CV|CV|INC|LTD|LTDA|LIMITED|PLC|CORP|CORPORATION|CO|COMPANY|HOLDINGS?|HLDGS|GROUP|GRUPO|ADR|ADS|SPONSORED|SP|PN|ON|PREF|PFD|CLASS [A-Z]|CL [A-Z]|N ?V|THE|DE|DEL|LA|EL|Y|E|AND)\b', ' ', s)
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', s)).strip()
# ---------- nós e identificadores
nodes = {}   # chave -> (nome, tokens)
CUSIPC = {'US', 'CA', 'BM', 'KY', 'VG', 'PA', 'LU', 'NL', 'GB', 'JE', 'IE', 'CW', 'BS'}   # ISINs cujo código interno é CUSIP/CINS
def toks(ids, extra=(), pais=None):
    t = set(extra)
    for x in ids:
        x = str(x).upper()
        if len(x) == 12 and re.match(r'^[A-Z]{2}[A-Z0-9]{9}\d$', x):
            if pais and x[:2] not in CUSIPC and x[:2] != pais: continue          # ISIN de outro país: erro de cadastro, ignora
            t.add('i:' + x)
            if x[:2] in CUSIPC: t.add('c:' + x[2:11]); t.add('c6:' + x[2:8])
        elif len(x) == 9: t.add('c:' + x); t.add('c6:' + x[:6])
    return t
for e, ids in pe.get('ids', {}).items(): nodes['pe:' + e] = (e, toks(ids, pais='PE'))
for e, v in us['emp'].items(): nodes['us:' + e] = (v[0], toks(us.get('ids', {}).get(e, []), pais=v[1]))
for e, v in f13['emp'].items(): nodes['f13:' + e] = (v[0], toks(f13.get('ids', {}).get(e, []), ['c6:' + e]))
for e, v in agg['emp'].items(): nodes['agg:' + e] = (v['nome'], toks(agg.get('ids', {}).get(e, []), pais=v.get('pais')))
CL = L['cl']
for f in CL['f']:
    for t in f['p']:
        nodes.setdefault('cl:' + t, (CL['emissores'].get(t, t), set()))
GEN = {'BANCO', 'BANK', 'GRUPO', 'FINANCIERO', 'CAPITAL', 'ENERGIA', 'INVESTMENTS', 'MINERA', 'INDUSTRIAS', 'CORPORACION', 'COMPANIA', 'CIA', 'EMPRESAS', 'FUND', 'TRUST', 'ETF', 'ISHARES'}
for k, (n, t) in nodes.items():
    nn = norm(n)
    if len(nn) >= 6 and nn not in GEN and not k.startswith('f13:'): t.add('n:' + nn)
    if k.startswith('cl:') and len(nn) >= 4: t.add('n:' + nn); t.add('n:' + ' '.join(nn.split()[:2]))
    if k.startswith(('agg:', 'us:')) and (us['emp'].get(k[3:], [0, ''])[1] == 'CL' or agg['emp'].get(k[4:], {}).get('pais') == 'CL'): t.add('n:' + ' '.join(nn.split()[:2]))
# ---------- união
par = {k: k for k in nodes}
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
by = {}
for k, (n, t) in nodes.items():
    for tk in t:
        if tk.startswith('c6:') and not k.startswith('f13:'):     # emissor (6 dígitos) só liga com o 13F, que agrupa por emissor
            tk = 'c6f:' + tk[3:]
        by.setdefault(tk, []).append(k)
for k in nodes:
    if k.startswith('f13:'): by.setdefault('c6f:' + k[4:], []).append(k)
for tk, ks in by.items():
    if tk.startswith('c6:'): continue
    for a in ks[1:]:
        ra, rb = find(ks[0]), find(a)
        if ra != rb: par[rb] = ra
groups = {}
for k in nodes: groups.setdefault(find(k), []).append(k)
# ---------- nome, setor, país de cada empresa
def title(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = s.title() if s.isupper() or s.islower() else s
    s = re.sub(r'\s+(S\.?\s?A\.?\s?A?\.?|Saa|Sab|S\.A\.B\.|Sa|A|B|L)$', '', s).strip()
    return re.sub(r'\bDe\b', 'de', re.sub(r'\bDo\b', 'do', s))
emp = {}; cid_of = {}
def slug(s): return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip('-')[:40] or 'x'
used = set()
for root, ks in groups.items():
    pri = sorted(ks, key=lambda k: ['agg', 'us', 'pe', 'f13', 'cl'].index(k.split(':')[0]))
    nome = title(nodes[pri[0]][0])
    setor = 'Outros'
    for k in pri:
        b, e = k.split(':', 1); s = SET.get(b, {}).get(e) if b != 'cl' else None
        if s and s != 'Outros': setor = s; break
    pais = None
    for k in pri:
        b, e = k.split(':', 1)
        if b == 'agg': pais = agg['emp'][e].get('pais'); break
        if b == 'us': pais = us['emp'][e][1]; break
        if b == 'pe': pais = 'PE'
        if b == 'cl': pais = 'CL'
    cid = slug(nome); i = 2
    while cid in used: cid = slug(nome) + '-' + str(i); i += 1
    used.add(cid)
    emp[cid] = {'n': nome, 's': setor, 'p': pais or '', 'k': ks}
    for k in ks: cid_of[k] = cid
# ---------- gestores (carteiras por data) e valores em US$
G = {}
AFPN = {'HA': 'AFP Habitat', 'IN': 'AFP Integra', 'PR': 'Prima AFP', 'RI': 'Profuturo AFP'}
M_ = pe['meses']
for a, nm_ in AFPN.items():
    fs = [d for f, d in pe['fundos'].items() if f.startswith(a)]
    S_ = [sum((d['S'][j] or 0) for d in fs) for j in range(len(M_))]
    pp_ = {}
    for d in fs:
        for e, v in d['p'].items():
            c = cid_of.get('pe:' + e)
            if not c: continue
            acc = pp_.setdefault(c, [0.0] * len(M_))
            for j in range(len(M_)): acc[j] += (v[0][j] or 0) / 1e4 * (d['S'][j] or 0)
    G['pe-' + a] = {'n': nm_, 'b': 'pe', 'dates': M_, 'p': {c: [None if not S_[j] else round(x[j] / S_[j] * 1e4) for j in range(len(M_))] for c, x in pp_.items()},
                    'usd': [None if not S_[j] else S_[j] / pen.get(m, np.nan) for j, m in enumerate(M_)], 'sub': 'Peru · fundos de pensão'}
for sid, d in us['fundos'].items():
    G['us-' + sid] = {'n': d['nome'], 'b': 'us', 'dates': d['datas'], 'p': {cid_of['us:' + e]: v[0] for e, v in d['p'].items() if 'us:' + e in cid_of}, 'usd': d['NA'], 'sub': d['reg']}
for cik, d in f13['fundos'].items():
    G['f13-' + cik] = {'n': d['nome'], 'b': 'f13', 'dates': d['datas'], 'p': {cid_of['f13:' + e]: v[0] for e, v in d['p'].items() if 'f13:' + e in cid_of}, 'usd': d['TOT'], 'sub': d.get('pais', '')}
clp = pd.read_pickle(W + '/clp.pkl'); mcl = CL['mes'][:4] + '-' + CL['mes'][4:6]
agf = {}
for f in CL['f']:
    a = agf.setdefault(f['agf'], {})
    for t, (v, w) in f['p'].items():
        c = cid_of.get('cl:' + t)
        if c: a[c] = a.get(c, 0) + v
for a, pos in agf.items():
    tot = sum(pos.values())
    G['cl-' + re.sub(r'[^a-z0-9]+', '-', a.lower())] = {'n': a.title() + ' (fundos mútuos)', 'b': 'cl', 'dates': [mcl], 'p': {c: [round(v / tot * 1e4)] for c, v in pos.items()},
        'usd': [tot * 1e3 / clp.get(mcl, np.nan)], 'sub': 'Chile · fundos mútuos'}
# soma por empresa quando dois títulos da mesma gestora caem na mesma empresa
for g in G.values():
    pp = {}
    for c, w in g['p'].items():
        cur = pp.get(c)
        pp[c] = w if cur is None else [(a or 0) + (b or 0) if (a is not None or b is not None) else None for a, b in zip(cur, w)]
    g['p'] = pp
P = lambda m: pd.Period(m, 'M')
NOW = max(g['dates'][-1] for g in G.values())
def idx_at(g, m, back=5):
    """índice da última carteira do gestor até o mês m (no máximo `back` meses antes)."""
    best = None
    for j, d in enumerate(g['dates']):
        if d <= m and (P(m) - P(d)).n <= back: best = j
    return best
CUR = {}
for gid, g in G.items():
    j = len(g['dates']) - 1
    if (P(NOW) - P(g['dates'][j])).n > 9: continue
    target = str(P(g['dates'][j]) - 12); jp = None
    for k, d in enumerate(g['dates']):
        if abs((P(d) - P(target)).n) <= 3 and (jp is None or abs((P(d) - P(target)).n) < abs((P(g['dates'][jp]) - P(target)).n)): jp = k
    CUR[gid] = (j, jp)
H = {c: [] for c in emp}
for gid, (j, jp) in CUR.items():
    g = G[gid]
    cids = set(g['p'])
    for c in cids:
        w = g['p'][c]; wn = (w[j] or 0) / 1e4; wp = None if jp is None else (w[jp] or 0) / 1e4
        if wn <= 0 and not wp: continue
        H[c].append([gid, round(wn, 5), None if wp is None else round(wp, 5), round(wn * (g['usd'][j] or 0), 2)])
# histórico trimestral: nº de gestores com posição e valor somado (US$ mi)
Q = [str(p) for p in pd.period_range('2016-03', NOW, freq='3M')]
QS = {c: [[0, 0.0] for _ in Q] for c in emp}
for gid, g in G.items():
    js = [idx_at(g, q) for q in Q]
    for c, w in g['p'].items():
        for qi, j in enumerate(js):
            if j is None: continue
            x = (w[j] or 0) / 1e4
            if x > 0: QS[c][qi][0] += 1; QS[c][qi][1] += x * (g['usd'][j] or 0)
# total dos fundos dos EUA (todos, inclusive índice): valor e fluxo do último trimestre
AG = {}
ti = len(agg['tris']) - 1
for r, es in agg['g'].items():
    for e, (v, f) in es.items():
        c = cid_of.get('agg:' + e)
        if not c: continue
        a = AG.setdefault(c, [0.0, 0.0, 0, [0.0] * len(agg['tris'])])
        if v[ti]: a[0] += v[ti]; a[2] += 1
        if f[ti]: a[1] += f[ti]
        for k, x in enumerate(v): a[3][k] += x or 0
# ---------- índice de preço em US$ por empresa (N-PORT; Peru: preço em soles convertido)
MES = [str(p) for p in pd.period_range('2016-01', NOW, freq='M')]
px = {}
rows = []
for f in sorted(glob.glob(W + '/np2/*.pkl')):
    x = pd.read_pickle(f)[['isin', 'ISSUER_CUSIP', 'REPORT_DATE', 'usd', 'BALANCE']]
    x = x[(x.usd > 0) & (x.BALANCE > 0)]
    x['ym'] = pd.to_datetime(x.REPORT_DATE, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
    x['tok'] = np.where(x['isin'].fillna('').str.len() == 12, 'i:' + x['isin'].fillna('').str.upper(), 'c:' + x.ISSUER_CUSIP.fillna('').str.upper())
    x['px'] = x.usd / x.BALANCE
    rows.append(x[['tok', 'ym', 'px']])
X = pd.concat(rows).groupby(['tok', 'ym']).px.median()
tok2c = {}
for k, (n, t) in nodes.items():
    for tk in t:
        if tk.startswith(('i:', 'c:')): tok2c.setdefault(tk, cid_of[k])
cnt = X.groupby(level=0).size()
best = {}
for tk, n in cnt.items():
    c = tok2c.get(tk)
    if c and n > best.get(c, ('', 0))[1]: best[c] = (tk, n)
SIMPLE = [2, 3, 4, 5, 10, 15, 20, 25, 50, 100]
def index_from(s):
    s = s.reindex(MES)
    r = s / s.ffill().shift(1) - 1
    r = r.where(s.notna())
    for m in r.index[r.abs() > 0.45]:          # desdobramento/grupamento provável
        q = 1 + r[m]
        for f in SIMPLE:
            for g_ in (f, 1 / f):
                if abs(np.log(q * g_)) < 0.15: r[m] = q * g_ - 1
    idx = (1 + r.fillna(0)).cumprod().where(s.ffill().notna())
    return idx
for c, (tk, n) in best.items():
    px[c] = index_from(X.loc[tk])
# Peru: preço em soles (valor ÷ quantidade das AFPs) convertido para US$
A = pd.read_pickle(W + '/pe_acoes.pkl'); A['v'] = pd.to_numeric(A.v, errors='coerce'); A['q'] = pd.to_numeric(A.q, errors='coerce')
pp = (A.groupby(['isin', 'ym']).v.sum() * 1e3 / A.groupby(['isin', 'ym']).q.sum()).dropna()
for isin, s in pp.groupby(level=0):
    c = tok2c.get('i:' + isin)
    if not c or c in px: continue
    s = s.droplevel(0); s = s / pen.reindex(s.index)
    px[c] = index_from(s.dropna())
# ---------- saída: só empresas com algum detentor (atual ou histórico) ou no total dos fundos dos EUA
out = {'map': {k: v for k, v in cid_of.items() if not k.startswith('agg:')}, 'now': NOW, 'q': Q, 'mes': MES, 'tris': agg['tris'], 'g': {}, 'e': {}}
for gid, g in G.items():
    j = len(g['dates']) - 1
    out['g'][gid] = {'n': g['n'], 'b': g['b'], 'sub': g.get('sub', ''), 'last': g['dates'][j], 'usd': round(g['usd'][j] or 0, 1), 'cur': gid in CUR}
for c, e in emp.items():
    hist = QS[c]
    if not H[c] and not any(h[0] for h in hist) and c not in AG: continue
    ix = px.get(c)
    out['e'][c] = {'n': e['n'], 's': e['s'], 'p': e['p'], 'h': H[c],
                   'qn': [h[0] for h in hist], 'qv': [round(h[1], 1) for h in hist],
                   'ag': None if c not in AG else [round(AG[c][0], 1), round(AG[c][1], 1), AG[c][2], [round(x, 1) for x in AG[c][3]]],
                   'px': None if ix is None else [None if pd.isna(v) else round(float(v), 4) for v in ix]}
json.dump(out, open(W + '/comb.json', 'w'), ensure_ascii=False, separators=(',', ':'))
import os
print('empresas', len(out['e']), 'gestores', len(out['g']), 'atuais', len(CUR), 'agora', NOW, os.path.getsize(W + '/comb.json') // 1024, 'KB')
top = sorted(out['e'].items(), key=lambda kv: -len(kv[1]['h']))[:20]
for c, e in top: print(f"{e['n'][:34]:34} {e['s'][:18]:18} {e['p']:3} detentores={len(e['h']):3} bases={sorted(set(h[0].split('-')[0] for h in e['h']))} px={'sim' if e['px'] else 'não'}")
