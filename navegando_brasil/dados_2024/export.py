# Junta jan/2024+ aos CSVs do dashboard (segue export_ds.py do repo gestoras).
import pandas as pd, numpy as np, json, re, os
W = '/home/user/work'; O = W + '/out'; os.makedirs(O, exist_ok=True)
OLD = W + '/old'
S = pd.read_pickle(W + '/serie.pkl'); P = pd.read_pickle(W + '/pos.pkl')
ret = pd.read_pickle(W + '/ret.pkl'); b3 = pd.read_pickle(W + '/b3_monthly.pkl'); names = pd.read_pickle(W + '/names.pkl'); ib = pd.read_pickle(W + '/ibov.pkl')
RENAME = json.load(open(W + '/rename.json'))
END = S.ym.max()
# ---- serie_mensal
S2 = S.copy(); S2['PL_mi'] = (S2.PL / 1e6).round(1)
for c in ['ret_fundo', 'ret_ibov', 'exp_long', 'exp_short', 'ret_acoes_contrib']: S2[c] = S2[c].round(5)
S2 = S2.sort_values(['id', 'ym'])
prevPL = S2.groupby('id').PL.shift(1); prevM = S2.groupby('id').master.shift(1)
S2['fluxo_mi'] = ((S2.PL - prevPL * (1 + S2.ret_fundo)) / 1e6).where((S2.master == prevM) & S2.ret_fundo.notna()).round(1)
cols = ['id', 'ym', 'PL_mi', 'ret_fundo', 'ret_ibov', 'exp_long', 'exp_short', 'n_acoes', 'ret_acoes_contrib', 'fluxo_mi']
so = pd.read_csv(OLD + '/serie_mensal.csv')
sm = pd.concat([so, S2[S2.ym >= '2024-01'][cols]]).sort_values(['id', 'ym'])
sm.to_csv(O + '/serie_mensal.csv', index=False)
# ---- agrupamento por empresa: mantém os representantes antigos; códigos novos de empresas renomeadas apontam para o antigo
po = pd.concat([pd.read_csv(OLD + '/posicoes_1.csv'), pd.read_csv(OLD + '/posicoes_2.csv')])
ALIAS = {'KROT': 'COGN', 'BVMF': 'B3SA', 'RUMO': 'RAIL', 'ESTC': 'YDUQ', 'VVAR': 'VIIA', 'NATU': 'NTCO', 'ABRE': 'SEDU', 'GOAU': 'GOAU',
         'AXIA': 'ELET', 'EMBJ': 'EMBR', 'MOTV': 'CCRO', 'ISAE': 'TRPL', 'AZZA': 'ARZZ', 'MBRF': 'MRFG', 'BRAV': 'RRRP', 'RIAA': 'GUAR', 'AUAU': 'PETZ', 'WIZC': 'WIZS', 'BRST': 'BRIT'}
def root(t):
    if re.match(r'^[A-Z][A-Z0-9]{3}\d{1,2}[FB]$', t): t = t[:-1]  # fracionário (ENGI11F), recibo (AMER3B)
    return ALIAS.get(t[:4], t[:4]) if re.match(r'^[A-Z][A-Z0-9]{3}\d{1,2}$', t) else t
oldrep = {}
for t in sorted(po.tk.unique()): oldrep.setdefault(root(t), t)
held = P.assign(a=P.peso.abs()).groupby('tk').a.sum()
rep = {}
for t in held.index:
    r0 = root(t)
    if r0 in oldrep: continue
    if r0 not in rep or held[t] > held[rep[r0]]: rep[r0] = t
REP = {t: oldrep.get(root(t)) or rep[root(t)] for t in held.index}
json.dump(REP, open(W + '/rep.json', 'w'))
Pn = P.assign(tk=P.tk.map(REP).fillna(P.tk))
Pn = Pn.groupby(['id', 'ym', 'tk'], as_index=False).agg(peso=('peso', 'sum'), contrib=('contrib', lambda x: x.sum(min_count=1)), trade_pct_pl=('trade_pct_pl', lambda x: x.sum(min_count=1)))
P2 = Pn[['id', 'ym', 'tk']].copy(); P2['peso'] = Pn.peso.round(5); P2['contrib'] = Pn.contrib.round(6); P2['compra_venda_pct_pl'] = Pn.trade_pct_pl.round(5)
P2 = P2[P2.ym >= '2024-01']
allp = pd.concat([po, P2]).sort_values(['id', 'ym', 'tk'])
allp[allp.id <= 17].to_csv(O + '/posicoes_1.csv', index=False); allp[allp.id > 17].to_csv(O + '/posicoes_2.csv', index=False)
# ---- precos: retorno da empresa = média dos códigos ponderada pelo peso agregado nos fundos no mês anterior
months = [m for m in sorted(S.ym.unique())]          # 2023-12 .. END
tks = sorted(set(allp.tk.unique()))
W_t = P.assign(a=P.peso.abs()).groupby(['ym', 'tk']).a.sum().unstack().reindex(months).shift(1)
r = pd.DataFrame(index=months, columns=tks, dtype=float)
for rp in tks:
    members = [t for t, v in REP.items() if v == rp and t in ret.columns] or ([rp] if rp in ret.columns else [])
    if not members: continue
    R_ = ret.reindex(index=months, columns=members); w = W_t.reindex(columns=members).fillna(0).where(R_.notna(), 0)
    w = w.where(w.sum(axis=1) > 0, R_.notna().astype(float))
    r[rp] = (R_.fillna(0) * w).sum(axis=1) / w.sum(axis=1).replace(0, np.nan)
r = r.loc['2024-01':]
pro = pd.read_csv(OLD + '/precos.csv')
last_idx = pro.dropna(subset=['indice_ret_total']).sort_values('ym').groupby('tk').indice_ret_total.last()
idx = (1 + r.fillna(0)).cumprod() * pd.Series({t: last_idx.get(t, 100.0) for t in r.columns})
idx = idx.where(r.notna())
pxcols = {t: (t if t in b3.columns else RENAME.get(t)) for t in tks}
pr = pd.DataFrame({t: (b3[c] if c in b3.columns else np.nan) for t, c in pxcols.items()}).reindex(r.index)
# preço B3 do código novo quando o antigo deixou de negociar (ex.: ELET3 -> AXIA3)
for t, c in RENAME.items():
    if t in pr and c in b3.columns: pr[t] = b3[t].reindex(r.index).fillna(b3[c].reindex(r.index)) if t in b3.columns else b3[c].reindex(r.index)
L = pd.DataFrame({'ret_total': r.stack(future_stack=True).round(5), 'indice_ret_total': idx.stack(future_stack=True).round(2), 'preco_b3': pr.stack(future_stack=True).round(2)}).dropna(how='all').reset_index()
L.columns = ['ym', 'tk', 'ret_total', 'indice_ret_total', 'preco_b3']
L = L[L.ret_total.notna() | L.tk.isin(set(P2.tk))]
pd.concat([pro, L]).sort_values(['ym', 'tk']).to_csv(O + '/precos.csv', index=False)
# ---- acoes: novas empresas
ao = pd.read_csv(OLD + '/acoes.csv')
setor_by_root = {root(t): (s, ss) for t, s, ss in zip(ao.tk, ao.setor, ao.subsetor)}
MAN = json.load(open(W + '/setores_novos.json')) if os.path.exists(W + '/setores_novos.json') else {}
new = [t for t in tks if t not in set(ao.tk)]
rows = []
for t in new:
    s = MAN.get(t[:4]) or setor_by_root.get(root(t)) or ('Outros/não classificado', '')
    rows.append(dict(tk=t, empresa=names.get(t, names.get(t[:-1], '')), setor=s[0], subsetor=s[1]))
an = pd.concat([ao, pd.DataFrame(rows)]).sort_values('tk')
an.to_csv(O + '/acoes.csv', index=False)
# ---- ibov
io = pd.read_csv(OLD + '/ibov.csv')
ni = pd.DataFrame({'ym': ib.index, 'pontos': ib.round(0).astype(int).values}); ni = ni[(ni.ym >= '2024-01') & (ni.ym <= END)]
pd.concat([io, ni]).to_csv(O + '/ibov.csv', index=False)
for f in ['fundos', 'encerrados']: pd.read_csv(OLD + f'/{f}.csv').to_csv(O + f'/{f}.csv', index=False)
print('END', END, 'novas empresas', len(new))
print(pd.DataFrame(rows).assign(w=lambda d: d.tk.map(P2.assign(a=P2.peso.abs()).groupby('tk').a.sum())).sort_values('w', ascending=False).to_string())
[print(f, os.path.getsize(O + '/' + f) // 1024, 'KB') for f in sorted(os.listdir(O))]
