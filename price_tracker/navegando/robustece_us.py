"""Navegando US robustecido, passo 2: acrescenta ao artefato os 100 maiores gestores ativos de cada trimestre que não estão na lista original
(todos os 13F da SEC, inclusive quem fechou), com selo e seletor "100 maiores de cada trimestre + lista original" / "só a lista original".
Uso: python3 -I navegando/robustece_us.py <index.html> <us_added_pos.csv.gz> <top100.csv> <saida.html>"""
import sys, re, gzip, base64, json
import numpy as np, pandas as pd
IDX, POS, TOP, OUT = sys.argv[1:5]
s = open(IDX, encoding='utf-8').read()
m = re.search(r'(<script id="nbd" type="text/plain">)(.*?)(</script>)', s, re.S)
d = json.loads(gzip.decompress(base64.b64decode(m.group(2).strip())))
G, C = d['f13'], d['comb']; Q = C['q']; qi = {q: i for i, q in enumerate(Q)}; nq = len(Q)
REF = next(iter(G['fundos'].values()))['REF']
P = pd.read_csv(POS, dtype={'CUSIP': str}); P = P[P.trimestre.isin(qi)]
P['cu'] = P.CUSIP.str[:6]
T = pd.read_csv(TOP); T = T[~T.no_navegando_us]
names = T.sort_values('trimestre').groupby('cik').nome.last()
GID = lambda c: f'sec-{int(c)}'
added = 0; holders_now = {}
for cik, g in P.groupby('cik'):
    tot = g.groupby('trimestre').v.sum()
    mem = sorted(tot.index, key=qi.get)
    w9 = {(q, c9): (v / tot[q], (v / sh if sh and sh > 0 else None)) for q, c9, v, sh in zip(g.trimestre, g.CUSIP, g.v, g.sh)}
    W6 = g.groupby(['trimestre', 'cu']).v.sum().div(g.groupby('trimestre').v.sum(), level=0)
    R, COV, TOTl, N = [None] * nq, [None] * nq, [None] * nq, [None] * nq
    contrib = {}
    for q in mem:
        j = qi[q]; TOTl[j] = round(float(tot[q]) / 1e6, 1); N[j] = int(g[g.trimestre == q].cu.nunique())
        if j == 0 or Q[j - 1] not in tot.index: continue
        qp = Q[j - 1]; cov = 0.0; rs = []
        for (qq, c9), (w0, p0) in w9.items():
            if qq != qp: continue
            x = w9.get((q, c9))
            if p0 and x and x[1]:
                r = x[1] / p0 - 1
                if -0.95 < r < 10: cov += w0; rs.append((c9[:6], w0 * r))
        if cov > 0.3:
            R[j] = round(sum(v for _, v in rs) / cov, 5); COV[j] = round(cov, 3)
            for cu, v in rs: contrib[(cu, j)] = contrib.get((cu, j), 0) + v / cov
    keep = sorted({cu for (q, cu), w in W6.items() if w >= .002})
    p = {}
    for cu in keep:
        ws = [None] * nq; cs = [None] * nq
        for q in mem:
            w = W6.get((q, cu))
            if w is not None and w >= .002: ws[qi[q]] = int(round(w * 1e4 * 100)) / 100 if False else int(round(w * 1e4))
        for j in range(nq):
            if (cu, j) in contrib: cs[j] = int(round(contrib[(cu, j)] * 1e6))
        p[cu] = [ws, cs]
        if cu not in G['emp']:
            nm_ = g[g.cu == cu].nome.iloc[0]; G['emp'][cu] = [str(nm_).title()]
    last = mem[-1]; lw = W6.loc[last] if last in W6.index.get_level_values(0) else pd.Series(dtype=float)
    mix = {}
    for cu, w in lw.items():
        pais = (G['fc'].get(cu) or ['EUA'])[0] or 'EUA'; mix[pais] = mix.get(pais, 0) + w
    gid = GID(cik)
    G['fundos'][gid] = dict(nome=str(names.get(cik, gid)), tipo='longo', ciks=[f'{int(cik):010d}'], datas=Q, R=R, REF=REF, COV=COV, TOT=TOTl, N=N, p=p,
                            mix=sorted([[k, round(v, 3)] for k, v in mix.items()], key=lambda z: -z[1]), pais='longo', rb=True)
    cur = last == Q[-1]
    C['g']['f13-' + gid] = dict(n=str(names.get(cik, gid)), b='f13', sub='Long-only', last=last, usd=TOTl[qi[last]], cur=bool(cur), rb=True)
    # empresas: número e valor de gestores por trimestre; detentores atuais
    for (q, cu), w in W6.items():
        if w < .002: continue
        key = C['map'].get('f13:' + cu)
        if not key or key not in C['e']: continue
        e = C['e'][key]; j = qi[q]
        e['qn'][j] = (e['qn'][j] or 0) + 1
        if e.get('qv') is not None: e['qv'][j] = round((e['qv'][j] or 0) + w * tot[q] / 1e6, 1)
    if cur:
        jp = nq - 5; qp = Q[jp]
        for cu in set(W6.loc[last].index) | (set(W6.loc[qp].index) if qp in W6.index.get_level_values(0) else set()):
            key = C['map'].get('f13:' + cu)
            if not key or key not in C['e']: continue
            wn = float(W6.get((last, cu), 0)); wp = W6.get((qp, cu)) if qp in tot.index else None
            if wn < .002 and (wp is None or wp < .002): continue
            C['e'][key]['h'].append(['f13-' + gid, round(wn if wn >= .002 else 0.0, 4), None if wp is None else round(float(wp) if wp >= .002 else 0.0, 4),
                                    round(wn * tot[last] / 1e6, 1) if wn >= .002 else 0.0])
    added += 1
print('gestores acrescentados', added, '| atuais', sum(1 for g_ in C['g'].values() if g_.get('rb') and g_['cur']))
d['gerado_em'] = d.get('gerado_em')
b64 = base64.b64encode(gzip.compress(json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode(), 9, mtime=0)).decode()
s = s[:m.start(2)] + b64 + s[m.end(2):]
REP = [
    ("const SG = { base: 'f13', per: 36, tipo: 'all' };", "const SG = { base: 'f13', per: 36, tipo: 'all', lst: 'rb' };"),
    ("GBASE[g.b] = (GBASE[g.b] || 0) + 1;", "GBASE[g.b] = (GBASE[g.b] || 0) + 1; if (!g.rb) GB0[g.b] = (GB0[g.b] || 0) + 1;"),
    ("const hs = e.h.filter((h) => ST.base === 'all' || C.g[h[0]].b === ST.base);",
     "const hs = e.h.filter((h) => (ST.base === 'all' || C.g[h[0]].b === ST.base) && (SG.lst !== 'orig' || !C.g[h[0]].rb)); const GBX = SG.lst === 'orig' ? GB0 : GBASE;"),
    ("const pres = now.length / ((ST.base === 'all' ? Object.values(GBASE).reduce((a, b) => a + b, 0) : GBASE[ST.base]) || 1);",
     "const pres = now.length / ((ST.base === 'all' ? Object.values(GBX).reduce((a, b) => a + b, 0) : GBX[ST.base]) || 1);"),
    ("seg($('g-tipo'), [['all', 'Todas'], ['longo', 'Long-only'], ['hedge', 'Hedge funds e ativistas']], SG.tipo, (v) => { SG.tipo = v; renderGestores(); });",
     "seg($('g-tipo'), [['all', 'Todas'], ['longo', 'Long-only'], ['hedge', 'Hedge funds e ativistas']], SG.tipo, (v) => { SG.tipo = v; renderGestores(); });\n  seg($('g-lst'), [['rb', '100 maiores de cada trimestre + lista original'], ['orig', 'Só a lista original']], SG.lst, (v) => { SG.lst = v; renderGestores(); });"),
    ("const rows = GLIST(b).filter((id) => b !== 'f13' || (SG.tipo === 'all' || D.f13.fundos[id].tipo === SG.tipo))",
     "const rows = GLIST(b).filter((id) => b !== 'f13' || ((SG.tipo === 'all' || D.f13.fundos[id].tipo === SG.tipo) && (SG.lst !== 'orig' || !D.f13.fundos[id].rb)))"),
    ("sub: (f.tipo === 'hedge' ? 'Hedge fund ou ativista' : 'Long-only') + ' · 13F, ações listadas nos EUA', L: f.datas, ret: f.R, ref: f.REF",
     "sub: (f.tipo === 'hedge' ? 'Hedge fund ou ativista' : 'Long-only') + ' · 13F, ações listadas nos EUA' + (f.rb ? ' · acrescentado: entre os 100 maiores gestores ativos do trimestre' : ''), L: f.datas, ret: f.R, ref: f.REF"),
    ('<div class="seg" id="g-tipo"></div>', '<div class="seg" id="g-tipo"></div><div class="seg" id="g-lst"></div>'),
    ('<li><b>Presença:</b>', '<li><b>Lista robustecida:</b> além das cerca de 150 gestoras da lista original, entram os 100 maiores gestores ativos de cada trimestre que não estão nela, refeitos em cada data a partir de todos os 13F da SEC, inclusive de quem fechou depois (20 a 400 posições, as 10 maiores somando ao menos 25%; fora indexadores, bancos, corretoras, seguradoras, fundos de pensão, soberanos e fundações). Cada um só aparece nos trimestres em que estava entre os 100 maiores e leva o selo "acrescentado". O seletor em Gestores volta à lista original (vale também para a presença nas empresas). Classificados como long-only.</li>\n          <li><b>Presença:</b>'),
]
for a, b in REP:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
assert s.count('let GBASE = {};') == 1
s = s.replace('let GBASE = {};', 'let GBASE = {}, GB0 = {};')
open(OUT, 'w', encoding='utf-8').write(s); print('ok', len(s) // 1024, 'KB')
