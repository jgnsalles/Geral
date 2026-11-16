# Peru: posições e attribution por fundo de AFP (carteira de ações locais), mensal.
# Preço de cada ISIN = valor ÷ quantidade somados entre os fundos; retorno = variação do preço (sem dividendos),
# corrigindo desdobramentos/grupamentos pela razão de quantidades entre os fundos.
# Contribuição = peso no fim do mês anterior × retorno no mês. Referência: carteira de ações locais de todas as AFPs somadas.
import pandas as pd, numpy as np, json
from fractions import Fraction
W = '/home/user/work/latam'
A = pd.read_pickle(W + '/pe_acoes.pkl'); T = pd.read_pickle(W + '/pe_totais.pkl')
A['v'] = pd.to_numeric(A.v, errors='coerce'); A['q'] = pd.to_numeric(A.q, errors='coerce'); A = A[(A.v > 0)].copy(); A['f'] = A.afp + A.fundo
import unicodedata, re as _re
def _canon(n):
    n = unicodedata.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode().upper()
    n = _re.sub(r'\(.*?\)|\(.*$', '', n)
    n = _re.sub(r'\b(S\.?\s?A\.?\s?A\.?|S\.?\s?A\.?|INC\.?|PLC|CORP\.?|LTD\.?)\b', ' ', n)
    return _re.sub(r'[^A-Z0-9 ]', ' ', _re.sub(r'\s+', ' ', n)).split().__str__()
A['_k'] = A.emissor.map(_canon)
_nm = A.sort_values('ym').groupby('_k').emissor.last()
A['emissor'] = A._k.map(_nm)
_ALIAS = {'HOCHSCHILD': 'HOCHSCHILD MINING PLC', 'Intercorp FS': 'Intercorp Financial Services Inc.', 'PACASMAYO S.A.A': 'CEMENTOS PACASMAYO S.A.A.', 'G & M S.A': 'AENZA S.A.A. (antes GRANA & MONTERO S.A.A.)'}
A['emissor'] = A.emissor.replace(_ALIAS)
last = A.sort_values('ym').groupby('isin').agg(emissor=('emissor', 'last'), setor=('setor', 'last'))
M = sorted(A.ym.unique()); mi = {m: i for i, m in enumerate(M)}; NM = len(M)
SIMPLE = sorted({Fraction(a, b) for a in range(1, 11) for b in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 50, 100)})
V = A.pivot_table(index=['f', 'isin'], columns='ym', values='v', aggfunc='sum').reindex(columns=M)          # miles de soles
Q = A.pivot_table(index=['f', 'isin'], columns='ym', values='q', aggfunc='sum').reindex(columns=M)
px = (V.groupby(level='isin').sum(min_count=1) * 1e3) / Q.groupby(level='isin').sum(min_count=1)
ret = pd.DataFrame(np.nan, index=px.index, columns=M); fac = pd.DataFrame(1.0, index=px.index, columns=M)
nsplit = 0
for isin in px.index:
    for j in range(1, NM):
        a, b = px.at[isin, M[j - 1]], px.at[isin, M[j]]
        if not (a > 0 and b > 0): continue
        ratio = b / a
        qq = (Q.xs(isin, level='isin')[M[j]] / Q.xs(isin, level='isin')[M[j - 1]]).replace([np.inf, -np.inf], np.nan).dropna()
        qq = qq[qq > 0]
        if len(qq) and abs(np.log(ratio)) > np.log(1.6):
            qm = float(qq.median()); f = min(SIMPLE, key=lambda c: abs(np.log(qm / float(c))))
            if abs(np.log(qm / float(f))) < 0.03 and abs(np.log(float(f))) > np.log(1.25) and abs(np.log(ratio * float(f))) < abs(np.log(ratio)):
                fac.at[isin, M[j]] = float(f); ratio *= float(f); nsplit += 1
        ret.at[isin, M[j]] = min(max(ratio - 1, -0.8), 3)
print('desdobramentos corrigidos', nsplit)
ret.index.name = 'isin'
NOMES = {'HA': 'Habitat', 'IN': 'Integra', 'PR': 'Prima', 'RI': 'Profuturo'}
TIPO = {'00': 'Fondo 0 (protección de capital)', '01': 'Fondo 1 (conservador)', '02': 'Fondo 2 (mixto)', '03': 'Fondo 3 (crecimiento)'}
TT = T.assign(f=T.afp + T.fundo).pivot_table(index='f', columns='ym', values='tot', aggfunc='sum').reindex(columns=M)
def attr(Vf, Qf):
    """Vf, Qf: DataFrames isin × mês da carteira; devolve séries por mês e por emissor."""
    S = Vf.sum(min_count=1)                                    # carteira de ações locais
    w = Vf.div(S, axis=1)
    r = ret.reindex(index=Vf.index)
    c = w.shift(1, axis=1) * r.fillna(0)                       # contribuição (fração da carteira de ações)
    c = c.where(w.shift(1, axis=1).notna())
    R = c.sum(min_count=1)
    # compras e vendas: Δ quantidade (corrigida por desdobramento) × preço, em % da carteira de ações
    pq = Qf.shift(1, axis=1) * fac.reindex(index=Qf.index).reindex(columns=M)
    tr = ((Qf.fillna(0) - pq.fillna(0)) * px.reindex(index=Qf.index) / 1e3).div(S, axis=1)
    tr = tr.where(Qf.notna() | pq.notna())
    return S, w, c, R, tr
emis = last.emissor.to_dict()
def by_emissor(df): return df.groupby(df.index.map(emis)).sum(min_count=1)
out = {'meses': M, 'fundos': {}, 'emissores': {e: last[last.emissor == e].setor.iloc[-1] for e in last.emissor.unique()}}
out['ids'] = {e: sorted(set(last[last.emissor == e].index)) for e in last.emissor.unique()}
# referência: todas as AFPs somadas
Vall = V.groupby(level='isin').sum(min_count=1); Qall = Q.groupby(level='isin').sum(min_count=1)
Sb, wb, cb, Rb, _ = attr(Vall, Qall)
out['ref'] = {'R': [None if pd.isna(x) else round(float(x), 5) for x in Rb]}
r6 = lambda s, k=5: [None if pd.isna(x) else round(float(x), k) for x in s]
for f in sorted(V.index.get_level_values(0).unique()):
    Vf = V.xs(f, level='f'); Qf = Q.xs(f, level='f')
    S, w, c, R, tr = attr(Vf, Qf)
    we, ce, te = by_emissor(w), by_emissor(c), by_emissor(tr)
    tot = TT.loc[f] if f in TT.index else pd.Series(np.nan, index=M)
    P = {}
    for e in we.index:
        if we.loc[e].max(skipna=True) < 0.0005 and ce.loc[e].abs().max(skipna=True) < 0.00005: continue
        P[e] = [[None if pd.isna(x) else int(round(x * 1e4)) for x in we.loc[e]], [None if pd.isna(x) else int(round(x * 1e6)) for x in ce.loc[e]], [None if pd.isna(x) or abs(x) < 0.0005 else int(round(x * 1e4)) for x in te.loc[e]]]
    out['fundos'][f] = {'nome': NOMES[f[:2]] + ' · ' + TIPO[f[2:]], 'afp': NOMES[f[:2]], 'tipo': f[2:], 'S': r6(S / 1e3, 1), 'tot': r6(tot / 1e3, 1), 'R': r6(R), 'p': P}
json.dump(out, open(W + '/pe_attr.json', 'w'), ensure_ascii=False, separators=(',', ':'))
# conferência
for f in ['HA03', 'PR02']:
    R = pd.Series(out['fundos'][f]['R'], index=M).dropna(); print(f, 'acumulado', round(float((1 + R).prod() - 1), 3), 'ref', round(float((1 + pd.Series(out['ref']['R'], index=M).dropna()).prod() - 1), 3))
import os; print('ok', os.path.getsize(W + '/pe_attr.json') // 1024, 'KB')
