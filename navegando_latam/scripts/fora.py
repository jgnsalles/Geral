# País e setor das posições 13F fora da parte LatAm ex-Brasil (para mostrar o tamanho da LatAm em cada carteira).
# País: endereço comercial no cadastro da SEC (submissions); setor: código SIC (mesma tabela de setores.py); Brasil: B3.
import json, re, os, time, requests
W = '/home/user/work/latam'; RAW = '/home/user/raw/latam/sec'
src = open(W + '/scripts/setores.py').read(); exec(src[:src.index('out = {}')])   # norm, sic2, RULES, B3, MAN, classify
F = json.load(open(W + '/f13_attr.json'))['fundos']
EMP = {}
for f in F.values():
    for e, n, w, br in f['fora']:
        if e != '_resto': EMP[e] = (n, br)
CACHE = RAW + '/meta2.json'; meta = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def get_meta(cik):
    k = str(cik)
    if k not in meta:
        r = S.get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json', timeout=30); time.sleep(0.12)
        j = r.json() if r.ok else {}
        ad = j.get('addresses', {}); meta[k] = [j.get('sic'), (ad.get('business') or {}).get('stateOrCountry') or (ad.get('mailing') or {}).get('stateOrCountry'), j.get('stateOfIncorporation')]
    return meta[k]
# índice por nome: nome completo e 2 primeiras palavras (abreviações comuns expandidas)
ABR = {'INTL': 'INTERNATIONAL', 'HLDGS': '', 'HLDG': '', 'TECHNOLOGIES': 'TECHNOLOGY', 'SYS': 'SYSTEMS', 'FINL': 'FINANCIAL', 'PHARMACEUTICALS': 'PHARMACEUTICAL', 'MFG': 'MANUFACTURING', 'SVCS': 'SERVICES', 'ENTMT': 'ENTERTAINMENT', 'GRP': ''}
def nx(s): return ' '.join(ABR.get(w, w) for w in norm(re.sub(r'(?i)\b(class [a-z]|cl [a-z]|common stock|cmn|com|new|spons?(ored)?|adr|ads|ord|shs|-?\s*a$)\b', ' ', s)).split() if ABR.get(w, w))
SECN = [(nx(v['title']).split(), v['cik_str']) for v in TK.values()]
BYW = {}
for tk_, c in SECN:
    if tk_: BYW.setdefault(tk_[0][:4], []).append((tk_, c))
def pre(a, b): return len(a) >= 2 and len(b) >= 2 and (a.startswith(b) or b.startswith(a))
def match(n):
    q = [t for t in nx(n).split() if len(t) >= 2]
    if not q: return None
    best, bs = None, 0
    for tk_, c in BYW.get(q[0][:4], []):
        if not pre(q[0], tk_[0]): continue
        sc = sum(any(pre(x, y) for y in tk_) for x in q) / len(q) + sum(any(pre(y, x) for x in q) for y in tk_) / len(tk_) / 2
        if sc > bs: best, bs = c, sc
    return best if bs >= 0.75 else None
ETFR = r'ISHARES|SPDR|VANECK|KRANESHARES|\bETF\b|PROSHARES|DIREXION|GLOBAL X|WISDOMTREE|SELECT SECTOR|INVESCO QQQ'
MANS = {'PDD': 'Consumo discricionário', 'ENBRIDGE': 'Petróleo e gás', 'SUPER SGHC': 'Consumo discricionário', 'TENARIS': 'Petróleo e gás', 'GRAB': 'Tecnologia'}
MANP = {'KASPI': 'Cazaquistão', 'TAIWAN SEMICONDUCTOR': 'Taiwan', 'SUPER GROUP': 'Reino Unido', 'MAKEMYTRIP': 'Índia', 'QIAGEN': 'Holanda', 'AERCAP': 'Irlanda',
        'FRONTLINE': 'Bermudas', 'SUPER SGHC': 'Reino Unido', 'D MARKET': 'Turquia', 'SOLARIS RES': 'Canadá', 'DHT': 'Bermudas', 'PICS': 'Brasil', 'ABIVAX': 'França', 'ASML': 'Holanda'}
US = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR'.split())
CC = {'X0': 'Reino Unido', 'K3': 'Hong Kong', 'F4': 'China', 'M5': 'Coreia do Sul', 'M0': 'Japão', 'F5': 'Taiwan', 'K7': 'Índia', 'U0': 'Singapura', 'I0': 'França', '2M': 'Alemanha',
      'V8': 'Suíça', 'P7': 'Holanda', 'L2': 'Irlanda', 'C3': 'Austrália', 'T3': 'África do Sul', 'L3': 'Israel', 'D5': 'Brasil', 'O5': 'México', 'F3': 'Chile', 'N4': 'Luxemburgo',
      'W0': 'Suécia', 'L6': 'Itália', 'U3': 'Espanha', 'G7': 'Dinamarca', 'Q8': 'Noruega', 'C4': 'Bélgica', 'R1': 'Peru', 'F8': 'Colômbia', 'C1': 'Argentina', 'X1': 'Uruguai', 'K8': 'Indonésia',
      'W8': 'Turquia', 'N8': 'Malásia', 'R6': 'Filipinas', 'W1': 'Tailândia', 'K1': 'Grécia', 'R9': 'Polônia', 'C9': 'Áustria', 'H9': 'Finlândia', 'E9': 'Ilhas Cayman', 'D0': 'Bermudas', 'D8': 'Ilhas Virgens', 'B9': 'Bahamas'}
def pais_of(st, inc, e):
    for c in (st, inc):
        if not c: continue
        if c in US: return 'EUA'
        if re.match(r'^A[0-9]$|^B0$', c): return 'Canadá'
        if c in CC and c not in ('E9', 'D0', 'D8', 'B9'): return CC[c]
    for c in (st, inc):
        if c in CC: return CC[c]
    return 'EUA' if e[:1].isdigit() else 'Outros'
out, src_ = {}, {'sec': 0, 'sem': 0}
for e, (n, br) in EMP.items():
    if br: out[e] = ['Brasil', classify(n, (), 'BR')[0]]; continue
    sm, fs = classify(n)
    cik = match(n); pm = next((v for k_, v in MANP.items() if norm(n).startswith(k_)), None)
    if cik:
        sc, st, inc = get_meta(cik); src_['sec'] += 1
        out[e] = [pm or pais_of(st, inc, e), sm if fs == 'manual' else (sic2(sc) or sm)]
    else:
        src_['sem'] += 1; out[e] = [pm or ('EUA' if e[:1].isdigit() else 'Outros'), sm]
    for k_, v in MANS.items():
        if norm(n).startswith(k_): out[e][1] = v
    if out[e][1] == 'Fundos e ETFs' or re.search(ETFR, n.upper()): out[e] = ['ETFs', 'Fundos e ETFs']
json.dump(meta, open(CACHE, 'w'))
json.dump(out, open(W + '/fora.json', 'w'), ensure_ascii=False)
import collections
print(src_, collections.Counter(v[0] for v in out.values()).most_common(12))
print([(EMP[e][0], v) for e, v in list(out.items())[:15]])
