# Setor de cada emissor das carteiras consolidadas (raiz de 4 letras) para o Navegando Brasil.
# Fontes: acoes.csv (classificação setorial da B3 usada na série), lista de empresas listadas da B3 (segmento → setor),
# BDRs e ativos no exterior à parte. Uso: python setores.py <carteiras.json> <acoes.csv> <b3 all.json> <saída setores.json>
import json, csv, sys, re, collections
CW, AC, B3, OUT = sys.argv[1:5]
NICE = {'Petróleo, Gás e Biocombustíveis': 'Petróleo e gás', 'Consumo não Cíclico': 'Consumo não cíclico', 'Consumo Cíclico': 'Consumo cíclico',
        'Tecnologia da Informação': 'Tecnologia', 'Utilidade Pública': 'Utilidade pública', 'Materiais Básicos': 'Materiais básicos', 'Bens Industriais': 'Bens industriais'}
nice = lambda s: NICE.get(s, s)
A = {}
for f in AC.split(','):
    for r in csv.DictReader(open(f)):
        if r['setor'] and not r['setor'].startswith('Outros'): A.setdefault(r['tk'][:4], nice(r['setor']))
R = json.load(open(B3)); SEG = {r['issuingCompany']: r['segment'] for r in R}; BDR = {r['issuingCompany'] for r in R if r.get('typeBDR')}
m = collections.defaultdict(collections.Counter)
for k, s in A.items():
    if k in SEG: m[SEG[k]][s] += 1
S2 = {g: c.most_common(1)[0][0] for g, c in m.items() if g not in ('Não Classificados', 'Não Classificado', 'Outros')}
MAN = {'Gestão de Recursos e Investimentos': 'Financeiro', 'Outros Intermediarios Financeiros': 'Financeiro', 'Securitizadoras de Recebíveis': 'Financeiro', 'Resseguradoras': 'Financeiro',
       'Corretoras de Seguros e Resseguros': 'Financeiro', 'Seguradoras': 'Financeiro', 'Bancos': 'Financeiro', 'Serviços Financeiros Diversos': 'Financeiro', 'Holdings Diversificadas': 'Financeiro',
       'Exploração de Imóveis': 'Imobiliário', 'Incorporações': 'Consumo cíclico', 'Construção Civil': 'Consumo cíclico', 'Energia Elétrica': 'Utilidade pública', 'Água e Saneamento': 'Utilidade pública',
       'Gás': 'Utilidade pública', 'Telecomunicações': 'Comunicações', 'Programas e Serviços': 'Tecnologia', 'Computadores e Equipamentos': 'Tecnologia', 'Medicamentos e Outros Produtos': 'Saúde',
       'Serv.Méd.Hospit..Análises e Diagnósticos': 'Saúde', 'Material Aeronáutico e de Defesa': 'Bens industriais', 'Exploração de Rodovias': 'Bens industriais', 'Transporte Aéreo': 'Bens industriais',
       'Minerais Metálicos': 'Materiais básicos', 'Siderurgia': 'Materiais básicos', 'Papel e Celulose': 'Materiais básicos', 'Exploração. Refino e Distribuição': 'Petróleo e gás',
       'Carnes e Derivados': 'Consumo não cíclico', 'Agricultura': 'Consumo não cíclico', 'Açucar e Alcool': 'Consumo não cíclico', 'Serviços Educacionais': 'Consumo cíclico', 'Aluguel de carros': 'Consumo cíclico'}
for g, s in MAN.items(): S2.setdefault(g, s)
# renomeações recentes sem segmento útil
FIX = {'AXIA': 'Utilidade pública', 'B3SA': 'Financeiro', 'MBRF': 'Consumo não cíclico', 'EMBJ': 'Bens industriais', 'MOTV': 'Bens industriais', 'ISAE': 'Utilidade pública', 'AZZA': 'Consumo cíclico',
       'RIPI': 'Utilidade pública', 'ANDG': 'Saúde', 'TOKY': 'Consumo cíclico', 'COGN': 'Consumo cíclico', 'CMET': 'Petróleo e gás',
       'AMBV': 'Consumo não cíclico', 'BPNM': 'Financeiro', 'OHLB': 'Bens industriais', 'NETC': 'Comunicações', 'TESA': 'Consumo não cíclico', 'BRTO': 'Comunicações', 'TNLP': 'Comunicações',
       'CARD': 'Tecnologia', 'BRTP': 'Comunicações', 'UBBR': 'Financeiro', 'RDCD': 'Financeiro', 'CREM': 'Saúde', 'PRGA': 'Consumo não cíclico', 'OGXP': 'Petróleo e gás', 'CNFB': 'Bens industriais'}
D = json.load(open(CW)); E = D['emissores']
out = {}; src = collections.Counter()
for r, (n, tks, old) in E.items():
    if '.' in r: out[r] = 'Exterior'; src['ext'] += 1; continue
    if r in FIX: out[r] = FIX[r]; src['fix'] += 1; continue
    if r in BDR or re.search(r'\b[A-Z0-9]{4}3[1-59]\b', tks or ''): out[r] = 'BDRs'; src['bdr'] += 1; continue
    if r in A: out[r] = A[r]; src['acoes'] += 1; continue
    s = S2.get(SEG.get(r, ''))
    if s: out[r] = s; src['b3'] += 1; continue
    for o in (old or '').split():
        if o[:4] in A: out[r] = A[o[:4]]; src['antigo'] += 1; break
    else: out[r] = 'Outros'; src['sem'] += 1
# conferência por peso no último mês
W = collections.Counter(); tot = 0
for g in D['gestoras']:
    for r, e in g['p'].items():
        w = e[1][-1] if e[1] and len(e[1]) + e[0] + g['o'] >= len(D['meses']) else 0
        W[out.get(r, 'Fundos no exterior')] += w; tot += w
print(src); print({k: round(v / tot, 3) for k, v in W.most_common()})
miss = collections.Counter()
for g in D['gestoras']:
    for r, e in g['p'].items():
        if out.get(r) == 'Outros': miss[r] += e[1][-1] if e[1] else 0
print('sem setor (peso):', [(r, E[r][0][:20]) for r, _ in miss.most_common(15)])
json.dump(out, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
