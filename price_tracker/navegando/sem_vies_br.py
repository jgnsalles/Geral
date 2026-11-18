"""Navegando Brasil sem viés de seleção, passo 1 (gestoras): universo padrão = SÓ a regra (100 maiores gestoras ativas de ações de cada mês,
ranking refeito em cada mês, incluindo as que fecharam depois). A lista original de 158 (escolhida hoje) vira filtro opcional.
Mesma régua do robustece_br.py, agora aplicada também às originais: fora bancos/seguradoras/previdência/corretoras, meses com dado ruim
(> 8× a mediana móvel) e casas com uma ação > 50% da carteira (controle). Grava em cada gestora `tp` = faixas [início, fim] (índices de mês)
em que ela estava entre as 100 maiores. Uso: python3 sem_vies_br.py <agg> <carteiras_rb.json> <saida.json>"""
import sys, json, glob, os, re, unicodedata
import pandas as pd
AGG, IN, OUT = sys.argv[1:4]
N_TOP = 100
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
src = open(os.path.join(os.path.dirname(__file__), 'robustece_br.py')).read()
BANK = eval(re.search(r"BANK = (re\.compile\(.*?\))\nroot8", src, re.S).group(1))
root8 = lambda c: re.sub(r'\D', '', str(c))[:8]
tot = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob(os.path.join(AGG, 'tot_*.pkl')))])
hold = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob(os.path.join(AGG, 'hold_*.pkl')))])
names = pd.read_pickle(os.path.join(AGG, 'gestor_nomes.pkl')).set_index('CPF_CNPJ_GESTOR').GESTOR
d = json.load(open(IN)); M = d['meses']; G = d['gestoras']; mi = {m: i for i, m in enumerate(M)}
gid = {}
for g in G:
    gid.setdefault(g['id'], g['id'])
    if not g.get('rb'):
        for x in g['mb']: gid[root8(x[1])] = g['id']
tot = tot[tot.ym.isin(M)].copy(); hold = hold[hold.ym.isin(M)].copy()
tot['r8'] = tot.g.map(root8); hold['r8'] = hold.g.map(root8)
tot['k'] = tot.r8.map(lambda r: gid.get(r, r)); hold['k'] = hold.r8.map(lambda r: gid.get(r, r))
big = tot.groupby(['k', 'g']).t.sum().reset_index().sort_values('t').drop_duplicates('k', keep='last').set_index('k').g
T = tot.groupby(['k', 'ym'])[['t', 'c']].sum().reset_index()
T['bank'] = T.k.map(lambda k: bool(BANK.search(deacc(names.get(big.get(k), '')))))
T = T.sort_values(['k', 'ym'])
T['med'] = T.groupby('k').t.transform(lambda x: x.rolling(13, center=True, min_periods=3).median())
T['bad'] = T.t > 8 * T.med
vmax = hold.groupby(['k', 'ym', 'key']).v.sum().groupby(['k', 'ym']).max().rename('vmax')
T = T.merge(vmax, left_on=['k', 'ym'], right_index=True, how='left')
T['conc'] = (T.vmax / T.t) > 0.5
el = T[~T.bank & ~T.bad & ~T.conc].copy(); el['tc'] = el.t + el.c
el['rk'] = el.groupby('ym').tc.rank(ascending=False, method='first')
top = el[el.rk <= N_TOP]
inside = top.groupby('k').ym.apply(lambda s: sorted(mi[m] for m in s)).to_dict()
ids = {g['id'] for g in G}
act = T[(T.t + T.c) > 0].groupby('k').ym.max()
CUT = '2026-01'   # sem carteira de ações desde antes disto = encerrada (os últimos meses têm sigilo, por isso a folga)
n_orig_top, stats = 0, []
for g in G:
    ms = inside.get(g['id'], [])
    if g.get('rb'):   # adicionada: só onde ela tem dado
        have = {g['o'] + k for k, v in enumerate(g['t']) if v is not None}
        ms = [m for m in ms if m in have] or sorted(have)
    rng, s0 = [], None
    for a, b in zip(ms, ms[1:] + [None]):
        if s0 is None: s0 = a
        if b != a + 1: rng.append([s0, a]); s0 = None
    g['tp'] = rng
    lm = act.get(g['id'])
    if g.get('rb') is None and lm is None:
        lm = max([act.get(root8(x[1])) for x in g['mb'] if act.get(root8(x[1]))] or [None])
    g['dead'] = int(lm[:4]) if lm and lm < CUT else None
    g['fora'] = int(M[min(rng[-1][1] + 1, len(M) - 1)][:4]) if (rng and not g['dead'] and rng[-1][1] < len(M) - 1) else (None if rng else -1)
    if not g.get('rb') and ms: n_orig_top += 1
per = []
for m in M:
    i = mi[m]
    inn = [g for g in G if any(a <= i <= b for a, b in g['tp'])]
    per.append(dict(ym=m, regra=len(inn), originais_na_regra=sum(1 for g in inn if not g.get('rb')),
                    originais_fora=sum(1 for g in G if not g.get('rb') and g['o'] <= i < g['o'] + len(g['t']) and not any(a <= i <= b for a, b in g['tp']))))
missing = sorted(set(top.k) - ids)
d['sem_vies'] = dict(regra=f'{N_TOP} maiores gestoras ativas de ações de cada mês; a lista original é só filtro', originais_alguma_vez_na_regra=n_orig_top,
                     gestoras_da_regra_sem_pagina=len(missing))
json.dump(d, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
p = pd.DataFrame(per); p.to_csv(os.path.join(os.path.dirname(__file__), 'universo_regra_br.csv'), index=False)
print('encerradas (dead):', sum(1 for g in G if g['dead']), '| vivas fora do top 100 hoje:', sum(1 for g in G if g['fora'] and g['fora'] > 0))
print('originais que alguma vez entram na regra:', n_orig_top, 'de', sum(1 for g in G if not g.get('rb')), '| gestoras da regra sem página:', len(missing))
print(p.iloc[::24].to_string()); print(p.tail(2).to_string())
