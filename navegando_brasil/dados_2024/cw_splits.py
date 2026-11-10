# Corrige desdobramentos/grupamentos nas quantidades das carteiras reconstruídas (base = quantidade mais recente).
# Detecta, por emissor e mês, a razão mediana q(m)/q(m-1) entre as gestoras que tinham a ação nos dois meses;
# quando quase todas mudam pela mesma razão "redonda" e o valor da posição não acompanha, é evento societário.
import json, sys, numpy as np
from fractions import Fraction
IN, OUT, A = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(IN)); M = d['meses']; G = d['gestoras']; i0 = M.index(A)
def series(g, r):
    e = g['p'].get(r)
    if not e: return {}
    return {g['o'] + e[0] + k: (e[1][k], e[2][k]) for k in range(len(e[1]))}
roots = sorted({r for g in G for r in g['p']})
CAND = sorted({Fraction(n, m) for n in range(1, 41) for m in range(1, 41)})
SIMPLE = sorted({Fraction(n, m) for n in range(1, 11) for m in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 30, 40, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 30, 40, 50, 100)})
ev = []
for r in roots:
    S = [(g, series(g, r)) for g in G if r in g['p']]
    for i in range(i0 + 1, len(M)):
        qr, vr = [], []
        for g, s in S:
            a, b = s.get(i - 1), s.get(i)
            if not a or not b or a[1] <= 0 or b[1] <= 0: continue
            ta = g['t'][i - 1 - g['o']] if 0 <= i - 1 - g['o'] < len(g['t']) else None; tb = g['t'][i - g['o']] if 0 <= i - g['o'] < len(g['t']) else None
            if not ta or not tb or not a[0] or not b[0]: continue
            qr.append(b[1] / a[1]); vr.append((b[0] * tb) / (a[0] * ta))
        if len(qr) < 2: continue
        q = float(np.median(qr))
        if abs(np.log(q)) < 0.04: continue
        f = min(CAND, key=lambda c: abs(np.log(q / float(c))))
        big = not (0.77 < q < 1.3)
        fs = min(SIMPLE, key=lambda c: abs(np.log(q / float(c))))
        share = np.mean([abs(np.log(x / float(f))) < (0.05 if big else 0.01) for x in qr])
        if big and abs(np.log(q / float(fs))) < 0.03 and np.mean([abs(np.log(x / float(fs))) < 0.03 for x in qr]) >= 0.3:
            f, share = fs, 1.0
        # desdobramento/grupamento: a maioria muda pela mesma razão; bonificação pequena: quase todas, com folga de 1%
        if not big and len(qr) >= 10:
            mid = np.mean([abs(np.log(x / q)) < 0.005 for x in qr])    # muitas gestoras com exatamente a razão mediana
            if mid >= 0.25: f, share = Fraction(q).limit_denominator(100), 1.0
        few_ok = len(qr) >= 5 or (big and f in SIMPLE and abs(np.log(float(f))) >= np.log(2))
        if few_ok and (share >= (0.6 if big else 0.8)) and (big or len(qr) >= 4) and abs(np.log(float(np.median(vr)))) < 0.4:
            ev.append((r, M[i], str(f), round(q, 3), len(qr), round(share, 2)))
print('eventos', len(ev)); [print(x) for x in ev]
# aplica: quantidades antes do evento (só a partir de A) passam para a base nova
for r, ym, f, *_ in ev:
    i = M.index(ym); f = float(Fraction(f))
    for g in G:
        e = g['p'].get(r)
        if not e: continue
        for k in range(len(e[2])):
            m = g['o'] + e[0] + k
            if i0 <= m < i and e[2][k] > 0: e[2][k] = int(round(e[2][k] * f))
d['base_q'] = A   # quantidades antes deste mês estão em outra base (json antigo): não comparar através dele
json.dump(d, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
# saltos remanescentes (mediana entre ≥10 gestoras fora de 0,8–1,25)
def ser2(g, r):
    e = g['p'].get(r); return {} if not e else {g['o'] + e[0] + k: e[2][k] for k in range(len(e[2]))}
for i in range(i0 + 1, len(M)):
    rs = {}
    for g in G:
        for r in g['p']:
            s_ = ser2(g, r); a, b = s_.get(i - 1, 0), s_.get(i, 0)
            if a > 0 and b > 0: rs.setdefault(r, []).append(b / a)
    bad = [(r, round(float(np.median(v)), 3), len(v)) for r, v in rs.items() if len(v) >= 10 and not 0.8 < np.median(v) < 1.25]
    if bad: print(M[i], bad)
