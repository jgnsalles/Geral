# País e setor das empresas do Navegando US (mesmas regras do fora.py do LatAm: cadastro da SEC, código SIC, nomes de ETF).
import json, re, os, time, collections
W = '/home/user/work/us'; L = '/home/user/work/latam'
src = open(L + '/scripts/setores.py').read(); exec(src[:src.index('out = {}')])            # norm, sic2, classify, TK, S (sessão SEC)
fo = open(L + '/scripts/fora.py').read(); exec(fo[fo.index("CACHE = RAW + '/meta2.json'"):fo.index('out, src_ =')])   # get_meta, match, pais_of, ETFR...
WU = '/home/user/work/us'; A = json.load(open(WU + '/us_attr.json'))
EMP = {e: v[0] for e, v in A['emp'].items()}
MANP.update({'TAIWAN SEMICONDUCTOR': 'Taiwan', 'ASML': 'Holanda', 'NOVO NORDISK': 'Dinamarca', 'SHOPIFY': 'Canadá', 'SPOTIFY': 'Suécia', 'ARM HOLDINGS': 'Reino Unido', 'ACCENTURE': 'Irlanda',
             'MEDTRONIC': 'Irlanda', 'LINDE': 'Reino Unido', 'CHUBB': 'Suíça', 'AON': 'Irlanda', 'EATON': 'Irlanda', 'JOHNSON CONTROLS': 'Irlanda', 'SEA': 'Singapura', 'NU HLDGS': 'Brasil',
             'MERCADOLIBRE': 'Uruguai', 'ALIBABA': 'China', 'PDD': 'China', 'BAIDU': 'China', 'JD COM': 'China', 'TENCENT': 'China', 'CANADIAN PAC': 'Canadá', 'CANADIAN NATL': 'Canadá',
             'BROOKFIELD': 'Canadá', 'SAP SE': 'Alemanha', 'SONY': 'Japão', 'TOYOTA': 'Japão', 'UNILEVER': 'Reino Unido', 'DIAGEO': 'Reino Unido', 'NOVARTIS': 'Suíça', 'ROCHE': 'Suíça'})
FIXUS = {norm(k): v for k, v in {'CHARLES SCHWAB': (None, 'Financeiro'), 'DISNEY WALT': (None, 'Comunicações'), 'GALLAGHER ARTHUR': (None, 'Financeiro'), 'WABTEC': (None, 'Industrial e transporte'),
  'TE CONNECTIVITY': ('Suíça', 'Tecnologia'), 'CORTEVA': (None, 'Materiais'), 'CREDICORP': ('Peru', 'Financeiro'), 'KENVUE': (None, 'Consumo básico'), 'CANADIAN NATL': ('Canadá', 'Industrial e transporte'),
  'FIDELITY MERRIMACK': ('ETFs', 'Fundos e ETFs')}.items()}
CT = {}
for v in TK.values(): CT.setdefault(v['cik_str'], (v['title'], v['ticker']))
out = {}; n_sec = 0
for e, n in EMP.items():
    sm, fs = classify(n)
    cik = match(n); pm = next((v for k_, v in MANP.items() if norm(n).startswith(k_)), None)
    if cik:
        sc, st, inc = get_meta(cik); n_sec += 1
        o = [pm or pais_of(st, inc, e), sm if fs == 'manual' else (sic2(sc) or sm)] + list(CT.get(cik, ('', '')))
    else:
        o = [pm or ('EUA' if e[:1].isdigit() else 'Outros'), sm, '', '']
    for k_, v in MANS.items():
        if norm(n).startswith(k_): o[1] = v
    if o[1] == 'Fundos e ETFs' or re.search(ETFR + r'|\bTRUST\b.*\b(ETF|FD|FUND)\b|\bINDEX\b|\bSPDR\b', n.upper()): o = ['ETFs', 'Fundos e ETFs'] + o[2:]
    for k_, v in FIXUS.items():
        if norm(n).startswith(k_): o = [v[0] or o[0], v[1] or o[1]] + o[2:]
    out[e] = o
json.dump(meta, open(CACHE, 'w')); json.dump(out, open(WU + '/classe.json', 'w'), ensure_ascii=False)
print('SEC', n_sec, 'de', len(EMP)); print(collections.Counter(v[0] for v in out.values()).most_common(15)); print(collections.Counter(v[1] for v in out.values()).most_common(16))
