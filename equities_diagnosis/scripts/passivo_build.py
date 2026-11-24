"""Passivo por tipo de cotista.
1) Mensal (2019+): Perfil Mensal da CVM, % do PL de cada fundo por tipo de cotista, nos fundos da base líquida da performance
   (FICs da gestora e fundos diretos), ponderado pelo PL do fundo no mês. Também % do PL do maior cotista e nº de cotistas.
2) Anual (2016–2025): Formulário de Referência da gestora (todos os produtos), AUM por classe de cliente.
Uso: python3 passivo_build.py <E_net.pkl> <pasta perfil> <gestoras_perf.json> <html Gestoras CVM> <saida.json>"""
import sys, os, re, json, glob, zipfile, io
import pandas as pd, numpy as np
EN, PD, GJ, FRH, OUT = sys.argv[1:6]
E = pd.read_pickle(EN)
keep = set(E.CNPJ_FUNDO)
CAT = [  # (rótulo, colunas)
    ('PF varejo', ['PF_VAREJO']), ('PF private', ['PF_PB']),
    ('Plataformas (conta e ordem)', ['DISTRIB']),
    ('Fundos e clubes', ['FI_CLUBE']),
    ('Previdência', ['EAPC', 'EFPC', 'ENTID_PREVID_COMPL']), ('RPPS', ['RPPS']),
    ('Seguradoras', ['SEGUR', 'CAPITALIZ']),
    ('PJ não financeira', ['PJ_NAO_FINANC_VAREJO', 'PJ_NAO_FINANC_PB']),
    ('Bancos e financeiras', ['BANCO', 'CORRETORA_DISTRIB', 'PJ_FINANC']),
    ('Estrangeiros', ['INVNR']), ('Outros', ['OUTRO'])]
NRC = ['PF_VAREJO', 'PF_PB', 'DISTRIB', 'FI_CLUBE', 'EAPC', 'EFPC', 'ENTID_PREVID_COMPL', 'RPPS', 'SEGUR', 'CAPITALIZ',
       'PJ_NAO_FINANC_VAREJO', 'PJ_NAO_FINANC_PB', 'BANCO', 'CORRETORA_DISTRIB', 'PJ_FINANC', 'INVNR', 'OUTRO']
parts = []
def take(f):
    d = pd.read_csv(f, sep=';', encoding='latin1', dtype=str, on_bad_lines='skip', quoting=3)
    d = d.rename(columns={'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO'})
    d = d[d.CNPJ_FUNDO.isin(keep)]
    if d.empty: return
    x = pd.DataFrame({'CNPJ_FUNDO': d.CNPJ_FUNDO, 'ym': d.DT_COMPTC.str[:7]})
    num = lambda c: pd.to_numeric(d.get(c, pd.Series(index=d.index, dtype=str)).str.replace(',', '.'), errors='coerce')
    for c in NRC:
        x['p_' + c] = num('PR_PL_COTST_' + c); x['n_' + c] = num('NR_COTST_' + c)
    x['maior'] = num('PR_PATRIM_LIQ_MAIOR_COTST')
    parts.append(x)
for f in sorted(glob.glob(os.path.join(PD, '*.csv'))):
    take(f); print('ok', os.path.basename(f), flush=True)
for z in sorted(glob.glob(os.path.join(PD, '*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if n.endswith('.csv'): take(zf.open(n))
    print('ok', os.path.basename(z), flush=True)
X = pd.concat(parts).drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last')
X = X.merge(E[['CNPJ_FUNDO', 'ym', 'gid', 'pl']], on=['CNPJ_FUNDO', 'ym'])
# percentuais podem vir em 0–100 ou 0–1: normaliza pela soma do fundo
pc = ['p_' + c for c in NRC]
s = X[pc].sum(axis=1)
X = X[s > 0.5]
X[pc] = X[pc].div(X[pc].sum(axis=1), axis=0)
mx = X.maior.where(X.maior <= 1, X.maior / 100)
X['maior'] = mx
X['ncot'] = X[['n_' + c for c in NRC]].sum(axis=1)
M = sorted(X.ym.unique()); MI = {m: i for i, m in enumerate(M)}
out = {'meses': M, 'cats': [c for c, _ in CAT], 'g': {}, 'fr': {}}
for gid, d in X.groupby('gid'):
    w = d.pl / d.groupby('ym').pl.transform('sum')
    rows = []
    agg = {}
    for c, cols in CAT:
        agg[c] = (d[['p_' + k for k in cols]].sum(axis=1) * w).groupby(d.ym).sum()
    mai = (d.maior.fillna(0) * w).groupby(d.ym).sum()
    nc = d.groupby('ym').ncot.sum(); plm = d.groupby('ym').pl.sum(); nf = d.groupby('ym').CNPJ_FUNDO.nunique()
    o = MI[d.ym.min()]; last = MI[d.ym.max()]
    rec = {'o': o, 'p': [], 'maior': [], 'ncot': [], 'pl': [], 'nf': []}
    for i in range(o, last + 1):
        ym = M[i]
        if ym in plm.index:
            rec['p'].append([int(round(agg[c].get(ym, 0) * 1e4)) for c, _ in CAT])
            rec['maior'].append(int(round(mai.get(ym, 0) * 1e4))); rec['ncot'].append(int(nc.get(ym, 0)))
            rec['pl'].append(round(float(plm[ym]) / 1e6, 1)); rec['nf'].append(int(nf[ym]))
        else:
            for k in ('p', 'maior', 'ncot', 'pl', 'nf'): rec[k].append(None)
    out['g'][gid] = rec
print('gestoras com passivo mensal:', len(out['g']), M[0], M[-1])
# Formulário de Referência (anual, gestora inteira) a partir do painel Gestoras CVM
h = open(FRH, encoding='utf-8').read()
D = json.loads(re.search(r'<script id="data" type="application/json">(\{.*?\})</script>', h, re.S).group(1))
G = json.load(open(GJ))
r2g = {}
for g in G:
    for r in {g['id']} | {re.sub(r'\D', '', x[1])[:8] for x in g['mb']}: r2g.setdefault(r, g['id'])
out['fr_classes'] = D['classes']
for x in D['gestoras']:
    gid = r2g.get(re.sub(r'\D', '', x['cnpj'])[:8])
    if not gid: continue
    for y, v in x['y'].items():
        ac = v.get('ac'); ic = v.get('ic')
        if not ac or not any(a for a in ac if a): continue
        cur = out['fr'].setdefault(gid, {})
        prev = cur.get(y)
        a = [int(round((q or 0) / 1e6)) for q in ac]; n = [int(q or 0) for q in (ic or [0] * len(ac))]
        if prev:  # soma CNPJs irmãos
            a = [p + q for p, q in zip(prev['a'], a)]; n = [p + q for p, q in zip(prev['n'], n)]
        cur[y] = {'a': a, 'n': n}
print('gestoras com FR:', len(out['fr']))
json.dump(out, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print('bytes', os.path.getsize(OUT))
