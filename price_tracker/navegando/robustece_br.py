"""Navegando Brasil robustecido, passo 2: junta ao carteiras.json as gestoras que estavam entre as 100 MAIORES de cada mês e faltavam.
Regra (fixada antes de olhar qualquer retorno): em cada mês, ranking refeito com o patrimônio em ações daquele mês (t + c, CDA da CVM,
todos os fundos, gestor na data), só gestoras ativas: fora fundos indexados (pelo nome), fundos de fundos (só ação direta conta) e
gestoras de bancos, seguradoras, previdência, fundações e corretoras (pelo nome). A gestora adicionada só aparece nos meses em que
estava entre as 100 maiores (uma que cresceu depois não entra nos períodos antigos; uma que fechou entra enquanto era grande).
Uso: python3 robustece_br.py <agg> <carteiras.json> <saida.json> <cobertura.csv>"""
import sys, json, glob, os, re, unicodedata, datetime
import pandas as pd, numpy as np
AGG, IN, OUT, COV = sys.argv[1:5]
N_TOP = 100
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
BANK = re.compile(r'\bBANCO\b|\bBB\b|BRADESCO|\bBRAM\b|ITAU|UNIBANCO|\bCAIXA\b|SANTANDER|SAFRA|\bBTG\b|\bXP\b|VOTORANTIM|\bBNP\b|CREDIT SUISSE|MORGAN|HSBC|\bCITI|'
                  r'SICREDI|SICOOB|BANCOOB|BANRISUL|BANESTES|DAYCOVAL|ABC BRASIL|\bMODAL\b|BNDES|\bBRB\b|MERCANTIL|\bPINE\b|\bDTVM\b|CORRETORA|DISTRIBUIDORA|'
                  r'PREVIDENCIA|SEGURADORA|SEGUROS|BRASILPREV|ICATU|SULAMERICA|PORTO SEGURO|MAPFRE|ZURICH|\bPETROS\b|\bPREVI\b|FUNCEF|VALIA|SISTEL|FUNDACAO|'
                  r'BLACKROCK|VANGUARD|STATE STREET|BANK|\bUBS\b|KINEA|JULIUS|PICTET|\bBNY\b|MELLON|DEUTSCHE|SCHRODER|ALLIANZ|AMUNDI|INTRAG|\bBEM\b|OLIVEIRA TRUST|VORTX|REAG\b|PLANNER')
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]

tot = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob(os.path.join(AGG, 'tot_*.pkl')))])
hold = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob(os.path.join(AGG, 'hold_*.pkl')))])
names = pd.read_pickle(os.path.join(AGG, 'gestor_nomes.pkl')).set_index('CPF_CNPJ_GESTOR').GESTOR
tot['r8'] = tot.g.map(root8); hold['r8'] = hold.g.map(root8)
d = json.load(open(IN)); M = d['meses']; G = d['gestoras']; E = d['emissores']
tot = tot[tot.ym.isin(M)]; hold = hold[hold.ym.isin(M)]
exist = {}
for g in G:
    exist[g['id']] = g['id']
    for x in g['mb']: exist[root8(x[1])] = g['id']
# nome da raiz = nome do CNPJ com mais ações
big = tot.groupby(['r8', 'g']).t.sum().reset_index().sort_values('t').drop_duplicates('r8', keep='last').set_index('r8').g
rname = {r: str(names.get(c, c)) for r, c in big.items()}
T = tot.groupby(['r8', 'ym'])[['t', 'c']].sum().reset_index()
T['bank'] = T.r8.map(lambda r: bool(BANK.search(deacc(rname.get(r, '')))))
# dado ruim: mês com patrimônio > 8× a mediana móvel (±6 meses) da própria gestora sai do ranking e da página
T = T.sort_values(['r8', 'ym'])
T['med'] = T.groupby('r8').t.transform(lambda x: x.rolling(13, center=True, min_periods=3).median())
T['bad'] = T.t > 8 * T.med
# participação de controle / family office: maior posição > 50% da carteira de ações no mês (mesma régua da seleção dos 30 fundos)
hx = hold.groupby(['r8', 'ym', 'key']).v.sum().groupby(['r8', 'ym']).max().rename('vmax')
T = T.merge(hx, left_on=['r8', 'ym'], right_index=True, how='left')
T['conc'] = (T.vmax / T.t) > 0.5
T['orig'] = T.r8.isin(exist)
el = T[(~T.bank & ~T.bad & ~T.conc) | T.orig].copy(); el['tc'] = el.t + el.c
el['rk'] = el.groupby('ym').tc.rank(ascending=False, method='first')
top = el[el.rk <= N_TOP]
add_months = top[~top.orig].groupby('r8').ym.apply(set).to_dict()
# cobertura (só gestoras elegíveis: ativas, sem bancos)
cov = []
for ym, x in el.groupby('ym'):
    tt = x.tc.sum(); o = x[x.orig].tc.sum(); n = x[(x.orig) | ((x.rk <= N_TOP))].tc.sum()
    cov.append(dict(ym=ym, total_bi=round(tt / 1e9, 1), orig=round(o / tt, 3) if tt else None, robust=round(n / tt, 3) if tt else None,
                    adicionadas=int(((x.rk <= N_TOP) & ~x.orig).sum()), originais_no_top=int(((x.rk <= N_TOP) & x.orig).sum())))
pd.DataFrame(cov).to_csv(COV, index=False)

# ---- emissores: código B3 -> raiz do json (mesma lógica de cw_update.py)
tk2r, old2r = {}, {}
for r, v in E.items():
    for t in (v[1] or '').split(): tk2r.setdefault(t, r)
    for o in (v[2] or '').split(): old2r.setdefault(o, r)
def root_of(key, nm):
    if '.' in key or key == 'EXT.FUNDOS':
        if key not in E: E[key] = [nm or key, key, '']
        return key
    if not re.match(r'^[A-Z0-9]{4}\d{1,2}[A-Z]?$', key): return None
    if key in tk2r: return tk2r[key]
    r4 = key[:4]
    if r4 in E: E[r4][1] = (E[r4][1] + ' ' + key).strip(); tk2r[key] = r4; return r4
    if r4 in old2r: r = old2r[r4]; tk2r[key] = r; return r
    E[r4] = [str(nm or r4).strip(), key, '']; tk2r[key] = r4; return r4
keys = hold[['key', 'nm']].drop_duplicates('key')
kmap = {k: root_of(k, n) for k, n in zip(keys.key, keys.nm)}
hold['r'] = hold.key.map(kmap); hold = hold[hold.r.notna()]
H = hold.groupby(['r8', 'ym', 'r'])[['v', 'q']].sum().reset_index()
# ---- base das quantidades: fator q_json / q_CDA por emissor e mês, medido nas gestoras originais
mi = {m: i for i, m in enumerate(M)}
rows = []
for g in G:
    for r, (s, w, q) in g['p'].items():
        for k in range(len(q)):
            if q[k] > 0: rows.append((g['id'], M[g['o'] + s + k], r, q[k]))
J = pd.DataFrame(rows, columns=['gid', 'ym', 'r', 'qj'])
Ho = H[H.r8.isin(exist)].assign(gid=lambda x: x.r8.map(exist)).groupby(['gid', 'ym', 'r']).q.sum().reset_index()
F = J.merge(Ho, on=['gid', 'ym', 'r']); F = F[F.q > 0]; F['f'] = F.qj / F.q
fac = F.groupby(['r', 'ym']).f.median()
fac = fac.unstack('ym').reindex(columns=M).T.ffill().bfill().T.stack().rename('f') if len(fac) else fac
fac = fac.to_dict()
# ---- novas gestoras
nice = lambda s: re.sub(r'\s+', ' ', re.sub(r'\b(LTDA|S\.?/?A\.?|ME|EPP|EIRELI|GESTAO|GESTORA|ADMINISTRACAO|ADMINISTRADORA|DE|DOS|DA|DO|RECURSOS|INVESTIMENTOS?|ASSET|MANAGEMENT|PARTICIPACOES|CAPITAL)\b\.?', ' ', deacc(s))).strip().title() or s.title()
added = []
for r8, months in sorted(add_months.items()):
    ms = sorted(months, key=mi.get); o = mi[ms[0]]; last = mi[ms[-1]]
    tr = T[(T.r8 == r8)].set_index('ym')
    t_, c_ = [], []
    for i in range(o, last + 1):
        m = M[i]
        if m in months: t_.append(int(round(tr.t.get(m, 0) / 1e3))); c_.append(int(round(tr.c.get(m, 0) / 1e3)))
        else: t_.append(None); c_.append(0)
    pm = {}
    for x in H[H.r8 == r8].itertuples():
        if x.ym not in months: continue
        tv = tr.t.get(x.ym, 0) / 1e3
        if tv <= 0: continue
        w = int(round(x.v / 1e3 / tv * 1e4)); q = int(round(x.q * fac.get((x.r, x.ym), 1.0)))
        if w > 0 or q > 0: pm.setdefault(x.r, {})[mi[x.ym]] = (w, q)
    p = {}
    for r, mm in pm.items():
        a, b = min(mm), max(mm) + 1
        p[r] = [a - o, [mm.get(k, (0, 0))[0] for k in range(a, b)], [mm.get(k, (0, 0))[1] for k in range(a, b)]]
    full = rname.get(r8, r8); cn = big.get(r8, r8)
    added.append(dict(id=r8, n=nice(full)[:28], rs=full, cnpj=cn, mb=[], o=o, man=False, rb=1, t=t_, c=c_, p=p))
G.extend(added)
d['emissores'] = E; d['robustecida'] = dict(regra=f'{N_TOP} maiores gestoras ativas de cada mês (ranking refeito em cada mês)', adicionadas=len(added),
                                             gerado_em=datetime.datetime.now().strftime('%d/%m/%Y'))
json.dump(d, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
c = pd.DataFrame(cov)
print('adicionadas', len(added)); print(c.iloc[::24].to_string()); print(c.tail(3).to_string())
print('maiores adicionadas (pico R$ bi):', sorted(((max([x or 0 for x in g['t']]) / 1e6, g['n']) for g in added), reverse=True)[:25])
