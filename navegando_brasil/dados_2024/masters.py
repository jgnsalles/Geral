# Masters e posições dos 30 fundos, dez/2023 em diante (segue holdings.py do repo gestoras).
import pandas as pd, numpy as np, json
W = '/home/user/work'
RT = json.load(open(W + '/roots.json'))
pos = pd.concat([pd.read_pickle(W + '/hist_pos.pkl'), pd.read_pickle(W + '/hist_pos8.pkl')], ignore_index=True)
pl = pd.read_pickle(W + '/hist_pl.pkl'); cot = pd.read_pickle(W + '/hist_cot.pkl')
for d in (pos, pl, cot): d['ym'] = d.DT_COMPTC.str[:7]
pos['v'] = pd.to_numeric(pos.VL_MERC_POS_FINAL, errors='coerce').fillna(0); pos['q'] = pd.to_numeric(pos.QT_POS_FINAL, errors='coerce').fillna(0)
LONG = ['Ações', 'Ações e outros TVM cedidos em empréstimo', 'Certificado ou recibo de depósito de valores mobiliários', 'Compras a termo a receber']
SHORT = ['Obrigações por ações e outros TVM recebidos em empréstimo', 'Vendas a termo a receber']
e = pos[pos.TP_APLIC.isin(LONG + SHORT)].copy()
e['sign'] = np.where(e.TP_APLIC.isin(SHORT), -1, 1); e['v'] *= e.sign; e['q'] *= e.sign
e['tk'] = e.CD_ATIVO.fillna('').str.strip().str.upper(); e = e[e.tk != '']
eqv = e[e.sign > 0].groupby(['CNPJ_FUNDO', 'ym']).v.sum()
pl['PL'] = pd.to_numeric(pl.VL_PATRIM_LIQ, errors='coerce'); pl = pl.drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='last').set_index(['CNPJ_FUNDO', 'ym']).PL
cot = cot.groupby(['CNPJ_FUNDO', 'ym', 'CNPJ_FUNDO_COTA']).v.sum().reset_index()
cot['w'] = cot.v / [pl.get((a, b), np.nan) for a, b in zip(cot.CNPJ_FUNDO, cot.ym)]
months = sorted(pos.ym.unique())
ROOTS = {int(i): set(r['masters']) for i, r in RT.items()}
ALLR = set().union(*ROOTS.values())
masters = []
for i, r in RT.items():
    i = int(i); mem = set(r['masters']) | set(r['feeders'])
    for m in months:
        c = cot[(cot.ym == m) & (cot.w >= 0.5)]
        cand = set(mem)
        for _ in range(3): cand |= set(c[c.CNPJ_FUNDO.isin(cand)].CNPJ_FUNDO_COTA)
        cand -= (ALLR - ROOTS[i])
        ev = {f: eqv.get((f, m), 0) for f in cand}
        best = max(ev, key=ev.get) if ev else None
        if not best or ev[best] <= 0: continue
        masters.append(dict(id=i, ym=m, master=best, eq=ev[best], PL=pl.get((best, m), np.nan)))
mst = pd.DataFrame(masters)
H = e.merge(mst[['id', 'ym', 'master', 'PL']], left_on=['CNPJ_FUNDO', 'ym'], right_on=['master', 'ym'])
H = H.groupby(['id', 'ym', 'master', 'tk', 'sign'], as_index=False).agg(q=('q', 'sum'), v=('v', 'sum'), PL=('PL', 'first'), isin=('CD_ISIN', 'first'), ds=('DS_ATIVO', 'first'))
H['w'] = H.v / H.PL
H.to_pickle(W + '/holdings.pkl'); mst.to_pickle(W + '/masters.pkl')
pd.set_option('display.width', 250)
print(len(H), H.tk.nunique())
print(mst.groupby('id').agg(n=('ym', 'size'), first=('ym', 'min'), last=('ym', 'max'), nmasters=('master', 'nunique')).to_string())
print(mst.groupby('ym').size().to_string())
