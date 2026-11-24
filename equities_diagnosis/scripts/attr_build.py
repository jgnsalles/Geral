"""Attribution mensal por gestora: peso de cada emissor no fim do mês anterior (CDA dos fundos usados na performance)
× retorno total do mês (B3). O resto do retorno bruto dos fundos vira "outros" (caixa, operações no mês, posições em sigilo
ou sem preço); a diferença entre o retorno líquido (cotista) e o bruto vira "taxas".
Uso: python3 attr_build.py <E_sel.pkl> <holdings.pkl> <cda_pl.pkl> <ret.pkl> <perf.json> <nomes.json> <saida.json>"""
import sys, json
import pandas as pd, numpy as np
EP, HP, PLP, RP, PJ, NJ, OUT = sys.argv[1:8]
E = pd.read_pickle(EP); H = pd.read_pickle(HP); CP = pd.read_pickle(PLP); R = pd.read_pickle(RP)
PF = json.load(open(PJ)); NM = json.load(open(NJ))
M = PF['meses']; MI = {m: i for i, m in enumerate(M)}
prev = {m: str(pd.Period(m, 'M') - 1) for m in M}
H['tk'] = H.tk.str.strip().str.upper()
H = H[H.v > 0]
H['root'] = H.tk.where(H.tk.str.startswith('X:'), H.tk.str[:4])
# trocas de código (mesma empresa): raiz antiga -> nova
import os as _os
_tm = _os.environ.get('TMAP')
REN = json.load(open(_tm))['rename'] if _tm and _os.path.exists(_tm) else {}
def ren(r):
    seen = set()
    while r in REN and r not in seen: seen.add(r); r = REN[r]
    return r
H['root'] = H.root.map(ren)
# retorno de cada ticker no mês
Rl = R.stack().rename('ret').reset_index(); Rl.columns = ['ym', 'tk', 'ret']
# carteiras extras (fundos investidos via cotas) e ligações fundo -> fundo, se existirem
import os
X_H, X_P, X_L = os.environ.get('XH'), os.environ.get('XP'), os.environ.get('XL')
if X_H and os.path.exists(X_H):
    H2 = pd.read_pickle(X_H); H2['tk'] = H2.tk.str.strip().str.upper(); H2 = H2[H2.v > 0]; H2['root'] = H2.tk.where(H2.tk.str.startswith('X:'), H2.tk.str[:4]).map(ren)
    H = pd.concat([H, H2], ignore_index=True)
if X_P and os.path.exists(X_P):
    CP = pd.concat([CP, pd.read_pickle(X_P)]).drop_duplicates(['CNPJ_FUNDO', 'ym'], keep='first')
# peso de cada ticker em cada fundo no fim do mês (sobre o PL da CDA)
CP = CP.set_index(['CNPJ_FUNDO', 'ym'])
Hv = H.groupby(['CNPJ_FUNDO', 'ym', 'tk', 'root']).v.sum().reset_index()
Hv = Hv.merge(CP.pl.rename('plc').reset_index(), on=['CNPJ_FUNDO', 'ym'], how='left')
Hv = Hv[Hv.plc > 0]; Hv['w'] = Hv.v / Hv.plc
Hv = Hv[['CNPJ_FUNDO', 'ym', 'tk', 'root', 'w']]
# look-through: cotas de outro fundo (ex.: fundo que investe no master) viram as ações desse fundo, na proporção
if X_L and os.path.exists(X_L):
    Lk = pd.read_pickle(X_L).merge(CP.pl.rename('plf').reset_index(), on=['CNPJ_FUNDO', 'ym'])
    Lk = Lk[Lk.plf > 0]; Lk['s'] = Lk.v / Lk.plf; Lk = Lk[(Lk.s > 0.005) & (Lk.s <= 1.5) & (Lk.cota != Lk.CNPJ_FUNDO)]
    LT = Lk[['CNPJ_FUNDO', 'ym', 'cota', 's']].merge(Hv.rename(columns={'CNPJ_FUNDO': 'cota'}), on=['cota', 'ym'])
    LT['w'] = LT.s * LT.w
    Hv = pd.concat([Hv, LT[['CNPJ_FUNDO', 'ym', 'tk', 'root', 'w']]]).groupby(['CNPJ_FUNDO', 'ym', 'tk', 'root']).w.sum().reset_index()
    print('posições vindas de look-through:', len(LT))
# soma das posições acima de 100% do PL (master + look-through duplicados, alavancagem) é reescalada para 100%
_tot = Hv.groupby(['CNPJ_FUNDO', 'ym']).w.transform('sum')
Hv['w'] = np.where(_tot > 1.0, Hv.w / _tot, Hv.w)
cv = Hv.groupby(['CNPJ_FUNDO', 'ym']).w.sum()
conf = (CP.conf.fillna(0) / CP.pl).rename('cw').reset_index()
# fundo-mês t usa a carteira de t-1; se t-1 estiver em sigilo (cobertura < 50%), usa a última carteira revelada (>= 70%) até 6 meses antes
E = E[E.ym.isin(MI)].copy(); E['yp'] = E.ym.map(prev)
E['a'] = E.pl_ant / E.groupby(['gid', 'ym']).pl_ant.transform('sum')
cvd = cv.to_dict()
def src(f, yp):
    if cvd.get((f, yp), 0) >= 0.5: return yp, False
    per = pd.Period(yp, 'M')
    for k in range(1, 7):
        y2 = str(per - k)
        if cvd.get((f, y2), 0) >= 0.7: return y2, True
    return yp, False
sr = [src(f, y) for f, y in zip(E.CNPJ_FUNDO, E.yp)]
E['ys'] = [x[0] for x in sr]; E['est'] = [x[1] for x in sr]
print('fundo-mês com carteira estimada pela última revelada:', int(E.est.sum()))
X = E[['gid', 'CNPJ_FUNDO', 'ym', 'ys', 'a']].merge(Hv.rename(columns={'ym': 'ys'}), on=['CNPJ_FUNDO', 'ys'])
X['wa'] = X.a * X.w
X = X.merge(Rl, on=['ym', 'tk'], how='left')
X['c'] = X.wa * X.ret
# agregados por gestora-mês
G = E.groupby(['gid', 'ym']).apply(lambda d: pd.Series({'rg': (d.r * d.pl_ant).sum() / d.pl_ant.sum()}), include_groups=False)
cov = X.groupby(['gid', 'ym']).wa.sum().rename('cov')
nop = X[X.ret.isna()].groupby(['gid', 'ym']).wa.sum().rename('nop')
cf = E.merge(conf.rename(columns={'ym': 'yp'}), on=['CNPJ_FUNDO', 'yp'], how='left')
cf.loc[cf.est, 'cw'] = 0
cf = (cf.a * cf.cw.fillna(0)).groupby([cf.gid, cf.ym]).sum().rename('conf')
est = E[E.est].groupby(['gid', 'ym']).a.sum().rename('est')
G = G.join(cov).join(nop).join(cf).join(est).fillna({'cov': 0, 'nop': 0, 'conf': 0, 'est': 0})
P = X[X.ret.notna()].groupby(['gid', 'ym', 'root']).agg(w=('wa', 'sum'), c=('c', 'sum')).reset_index()
roots = sorted(P.root.unique()); RI = {r: k for k, r in enumerate(roots)}
# empresas de fora do Brasil: posições no exterior (X:) ou BDRs (códigos 31-35, 39)
_tpx = H.assign(fx=H.tk.str.startswith('X:') | H.tk.str.match(r'^[A-Z0-9]{4}(3[1-5]|39)$') | H.tp.fillna('').str.contains('Depository|Exterior'))
FXR = set(_tpx[_tpx.fx].root)
I = lambda v: int(round(v * 1e6)) if np.isfinite(v) else 0
out = {'meses': M, 'roots': roots, 'names': [NM.get(r, r) for r in roots], 'fx': [k for k, r in enumerate(roots) if r in FXR], 'g': {}}
for gid, gg in G.groupby(level=0):
    gg = gg.droplevel(0)
    o, last = MI[gg.index.min()], MI[gg.index.max()]
    pg = P[P.gid == gid]
    byM = {ym: d for ym, d in pg.groupby('ym')}
    rec = {'o': o, 'rg': [], 'cov': [], 'nop': [], 'conf': [], 'est': [], 'p': []}
    for i in range(o, last + 1):
        ym = M[i]
        if ym in gg.index:
            row = gg.loc[ym]
            rec['rg'].append(I(row['rg'])); rec['cov'].append(I(row['cov'])); rec['nop'].append(I(row['nop'])); rec['conf'].append(I(row['conf'])); rec['est'].append(I(row['est']))
            d = byM.get(ym)
            rec['p'].append([] if d is None else [[RI[r], I(w), I(c)] for r, w, c in zip(d.root, d.w, d.c) if abs(w) >= 5e-5])
        else:
            for k in ('rg', 'cov', 'nop', 'conf', 'est'): rec[k].append(None)
            rec['p'].append([])
    out['g'][gid] = rec
json.dump(out, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
# conferência: quanto do retorno bruto as ações explicam
S = P.groupby(['gid', 'ym']).c.sum().rename('sc')
C = G.join(S).dropna()
C = C[C['cov'] > 0.7]
print('gestora-meses com cobertura > 70%:', len(C), '| correlação ações x bruto:', round(C.sc.corr(C.rg), 3),
      '| resíduo médio mensal (p.p.):', round((C.rg - C.sc).mean() * 100, 2), '| desvio:', round((C.rg - C.sc).std() * 100, 2))
print('emissores:', len(roots), 'gestoras:', len(out['g']))
