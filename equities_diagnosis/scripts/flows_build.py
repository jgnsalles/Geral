"""Captação líquida mensal por gestora (R$ mi), nos mesmos fundos da performance líquida.
Fundos brasileiros: captação − resgate do Informe Diário no mês. Fundos LatAm (E_la): PL − PL anterior × (1 + retorno).
Uso: flows_build.py <E_net.pkl> <fundo_mes.pkl> <E_la.pkl> <perf.json> <saida.json>"""
import sys, json
import pandas as pd
EN, FM, EL, PJ, OUT = sys.argv[1:6]
M = json.load(open(PJ))['meses']; MI = {m: i for i, m in enumerate(M)}
E = pd.read_pickle(EN)[['CNPJ_FUNDO', 'ym', 'gid']]
F = pd.read_pickle(FM)[['CNPJ_FUNDO', 'ym', 'flow']]
X = E.merge(F, on=['CNPJ_FUNDO', 'ym'], how='left')
L = pd.read_pickle(EL); L = L[L.pl_ant > 0]
L['flow'] = L.pl - L.pl_ant * (1 + L.r)
X = pd.concat([X[['gid', 'ym', 'flow']], L[['gid', 'ym', 'flow']]])
X = X[X.ym.isin(MI)].groupby(['gid', 'ym']).flow.sum() / 1e6
out = {}
for gid, s in X.groupby(level=0):
    s = s.droplevel(0); ix = sorted(MI[m] for m in s.index); o = ix[0]
    v = [None] * (ix[-1] - o + 1)
    for m, f in s.items(): v[MI[m] - o] = round(float(f), 1)
    out[gid] = {'o': o, 'f': v}
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('gestoras', len(out), 'meses até', M[max(v['o'] + len(v['f']) - 1 for v in out.values())])
