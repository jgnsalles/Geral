"""Regra de picos no crescimento (pre-registrada em 2026-11-14)."""
import numpy as np

LIM = 1.5


def adjust(rates, years=None):
    """rates: variacoes anuais (antiga -> recente), nan quando indefinida. Devolve a lista ajustada (picos fundidos em variacao de 2 anos)."""
    r = list(rates); n = len(r); cand = []
    for i in range(n - 1):
        a, b = r[i], r[i + 1]
        if not (np.isfinite(a) and np.isfinite(b)) or 1 + a <= 0 or 1 + b <= 0: continue
        q = np.sqrt((1 + a) / (1 + b))  # lucro do ano i / media geometrica dos vizinhos
        if q >= LIM or q <= 1 / LIM: cand.append((abs(np.log(q)), i))
    used, merge = set(), {}
    for _, i in sorted(cand, reverse=True):
        if i in used or i + 1 in used: continue
        used |= {i, i + 1}; merge[i] = np.sqrt((1 + r[i]) * (1 + r[i + 1])) - 1
    out, lab, i = [], [], 0
    while i < n:
        if i in merge: out.append(merge[i]); lab.append(None); i += 2  # variacao fundida: nao pertence a um ano so
        else: out.append(r[i]); lab.append(years[i] if years else None); i += 1
    return (out, lab) if years else out
