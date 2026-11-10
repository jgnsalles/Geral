# Atualiza carteiras.json (Carteiras das Gestoras) com a CDA mais nova da CVM.
# Reconstrói, por gestora (CNPJs do gestor + mb), o total em ações divulgado (t, R$ mil), o total em sigilo (c, R$ mil)
# e por emissor o peso (×1e4) e a quantidade. Calibrado contra o próprio carteiras.json em meses já completos.
# Uso: python cw_update.py <json entrada> <json saída> <primeiro mês a reconstruir AAAA-MM> <último mês> [meses de conferência...]
import pandas as pd, numpy as np, zipfile, json, sys, re, datetime
IN, OUT, A, B = sys.argv[1:5]; CHK = sys.argv[5:]
RAW = '/home/user/raw'
d = json.load(open(IN)); M = d['meses']; E = d['emissores']; G = d['gestoras']
EQ = ['Ações', 'Ações e outros TVM cedidos em empréstimo', 'Certificado ou recibo de depósito de valores mobiliários', 'Brazilian Depository Receipt - BDR']
EXT = 'Investimento no Exterior'
fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}'
# ---- fundo/classe -> gestor (registro CVM 175; classes canceladas só aparecem no registro do fundo)
z = zipfile.ZipFile(RAW + '/cad/registro.zip')
rf = pd.read_csv(z.open('registro_fundo.csv'), sep=';', encoding='latin1', dtype=str)
rc = pd.read_csv(z.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str).merge(rf[['ID_Registro_Fundo', 'CPF_CNPJ_Gestor']], on='ID_Registro_Fundo')
rc['cnpj'] = rc.CNPJ_Classe.str.zfill(14)
rf2 = rf.assign(cnpj=rf.CNPJ_Fundo.str.zfill(14))[['cnpj', 'CPF_CNPJ_Gestor']]
fg = pd.concat([rc[['cnpj', 'CPF_CNPJ_Gestor']], rf2[~rf2.cnpj.isin(set(rc.cnpj))]]).dropna()
fg = dict(zip(fg.cnpj.map(fmt), fg.CPF_CNPJ_Gestor.str.zfill(14).map(fmt)))
g_of = {}
for g in G:
    for c in {g['cnpj']} | {x[1] for x in g['mb']}: g_of[c] = g['id']
fund_g = {f: g_of[c] for f, c in fg.items() if c in g_of}
# ---- código -> emissor
tk2r = {}
for r, v in E.items():
    for t in (v[1] or '').split(): tk2r.setdefault(t, r)
old2r = {}
for r, v in E.items():
    for o in (v[2] or '').split(): old2r.setdefault(o, r)
b3 = pd.read_pickle('/home/user/work/b3_daily.pkl'); b3n = b3.sort_values('dt').groupby('tk').nome.last()
new_em = {}
def root_br(tk, ds):
    tk = str(tk or '').strip().upper()
    if not re.match(r'^[A-Z0-9]{4}\d{1,2}[A-Z]?$', tk):
        return None
    if tk in tk2r: return tk2r[tk]
    r4 = tk[:4]
    if r4 in E:
        E[r4][1] = (E[r4][1] + ' ' + tk).strip(); tk2r[tk] = r4; return r4
    if r4 in old2r:
        r = old2r[r4]; E[r][1] = (E[r][1] + ' ' + tk).strip(); tk2r[tk] = r; return r
    E[r4] = [str(b3n.get(tk, ds or r4)).strip(), tk, '']; tk2r[tk] = r4; new_em[r4] = E[r4][0]; return r4
CC = {'USA': 'US', 'HKG': 'HK', 'JPN': 'JP', 'DEU': 'GR', 'CAN': 'CN', 'BEL': 'BB', 'GBR': 'LN', 'FRA': 'FP', 'NLD': 'NA', 'CHE': 'SW', 'CHN': 'CH', 'KOR': 'KS', 'TWN': 'TT', 'ESP': 'SM', 'ITA': 'IM', 'MEX': 'MM', 'ARG': 'AR', 'CHL': 'CI', 'PER': 'PE', 'COL': 'CB', 'IND': 'IN', 'DNK': 'DC', 'SWE': 'SS', 'NOR': 'NO', 'IRL': 'ID', 'AUS': 'AU'}
def root_ext(row):
    if row.TP_ATIVO in ('Depository Receipt no Exterior(DR)', 'Ação ordinária', 'Ação preferencial'):
        c = str(row.CD_ATIVO_BV_MERC or '').strip().upper()
        m = re.match(r'^([A-Z0-9.\-/]{1,10})(?:\s+([A-Z]{2}))?(?:\s+EQUITY)?$', c)
        if m and not c.isdigit():
            k = m.group(1).replace('/', '.') + '.' + (m.group(2) or CC.get(str(row.CD_PAIS), 'US'))
            if k not in E: E[k] = [str(row.EMISSOR or k).strip(), k, '']; new_em[k] = E[k][0]
            return k
    return 'EXT.FUNDOS'
def month(ym):
    m = ym.replace('-', ''); z = zipfile.ZipFile(f'{RAW}/cvm/cda_fi_{m}.zip')
    rd = lambda k: pd.concat([pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str, quoting=3, on_bad_lines='skip') for n in z.namelist() if k in n and 'fie' not in n] or [pd.DataFrame()])
    b4 = rd('BLC_4'); b7 = rd('BLC_7'); cf = rd('_CONFID_')
    rows = []
    if len(b4):
        x = b4[b4.TP_APLIC.isin(EQ)].copy(); x['g'] = x.CNPJ_FUNDO_CLASSE.map(fund_g); x = x[x.g.notna()]
        x['r'] = [root_br(t, ds) for t, ds in zip(x.CD_ATIVO, x.DS_ATIVO)]
        rows.append(x[['g', 'r', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']])
    if len(b7):
        x = b7[b7.TP_APLIC == EXT].copy(); x['g'] = x.CNPJ_FUNDO_CLASSE.map(fund_g); x = x[x.g.notna()]
        x['r'] = [root_ext(rw) for rw in x.itertuples()]
        rows.append(x[['g', 'r', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']])
    X = pd.concat(rows); X['v'] = pd.to_numeric(X.VL_MERC_POS_FINAL, errors='coerce').fillna(0); X['q'] = pd.to_numeric(X.QT_POS_FINAL, errors='coerce').fillna(0)
    X = X[X.v > 0]
    t = X.groupby('g').v.sum() / 1e3
    sem = X[X.r.isna()].groupby('g').v.sum() / 1e3          # sem código: entra no total, sem emissor (como no json)
    P = X[X.r.notna()].groupby(['g', 'r'])[['v', 'q']].sum()
    c = pd.Series(dtype=float)
    if len(cf):
        y = cf[cf.TP_APLIC.isin(EQ + [EXT])].copy(); y['g'] = y.CNPJ_FUNDO_CLASSE.map(fund_g); y = y[y.g.notna()]
        y['v'] = pd.to_numeric(y.VL_MERC_POS_FINAL, errors='coerce').fillna(0); c = y.groupby('g').v.sum() / 1e3
    return t, c, P
# ---- p[r] = [início relativo a g.o, pesos×1e4, quantidades]  <->  dict mês->(w,q)
def dec(g):
    out = {}
    for r, (s, w, q) in g['p'].items():
        out[r] = {g['o'] + s + k: (w[k], q[k]) for k in range(len(w))}
    return out
def enc(g, pm):
    p = {}
    for r, mm in pm.items():
        ks = [k for k, (w, q) in mm.items() if w or q]
        if not ks: continue
        a, b = min(ks), max(ks) + 1
        p[r] = [a - g['o'], [mm.get(k, (0, 0))[0] for k in range(a, b)], [mm.get(k, (0, 0))[1] for k in range(a, b)]]
    g['p'] = p
# ---- conferência
for ym in CHK:
    i = M.index(ym); t, c, P = month(ym); ok = tot = 0; errs = []
    for g in G:
        k = i - g['o']
        if not (0 <= k < len(g['t'])) or g['t'][k] is None: continue
        tj = g['t'][k]; tn = t.get(g['id'], 0); tot += tj
        if abs(tn / tj - 1) < 0.05: ok += tj
        else: errs.append((g['n'], tj, round(tn), round(tn / tj - 1, 3)))
    print(ym, 'valor das gestoras a menos de 5% do json:', round(ok / tot, 3), sorted(errs, key=lambda z: -z[1])[:8])
# ---- reconstrução
months = [m for m in pd.period_range(A, B, freq='M').strftime('%Y-%m')]
for m in months:
    if m not in M: M.append(m)
NM = len(M)
cache = {m: month(m) for m in months}
for g in G:
    pm = dec(g); T = list(g['t']); C = list(g['c'])
    need = M.index(months[-1]) - g['o'] + 1
    T += [None] * (need - len(T)); C += [0] * (need - len(C))
    for m in months:
        i = M.index(m); k = i - g['o']
        if k < 0: continue
        t, c, P = cache[m]
        for r in pm: pm[r].pop(i, None)
        tv = t.get(g['id']); cv = c.get(g['id'], 0)
        T[k] = int(round(tv)) if tv else (0 if cv else None); C[k] = int(round(cv))
        if tv and g['id'] in P.index.get_level_values(0):
            for r, (v, q) in P.loc[g['id']].iterrows():
                w = int(round(v / 1e3 / tv * 1e4))
                if w > 0 or q > 0: pm.setdefault(r, {})[i] = (w, int(round(q)))
    while T and T[-1] is None: T.pop(); C.pop()
    g['t'] = T; g['c'] = C[:len(T)]; enc(g, pm)
d['meses'] = M; d['emissores'] = E
d['gerado_em'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
json.dump(d, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
for m in months:
    i = M.index(m); T_ = C_ = n = 0
    for g in G:
        k = i - g['o']
        if 0 <= k < len(g['t']) and g['t'][k] is not None: T_ += g['t'][k]; C_ += g['c'][k]; n += 1
    print(m, 'gestoras', n, 'revelado R$ bi', round(T_ / 1e6, 1), 'sigilo R$ bi', round(C_ / 1e6, 1), 'cobertura', round(T_ / (T_ + C_), 3) if T_ + C_ else None)
print('emissores novos', len(new_em), list(new_em.items())[:40])
