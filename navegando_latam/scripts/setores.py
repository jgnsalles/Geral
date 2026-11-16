# Setor de cada empresa nas bases da LatAm. Ordem das fontes:
# 1) classificação manual das maiores posições; 2) Peru: setor informado pela SBS; 3) Brasil: classificação setorial da B3
# (a mesma do Navegando Brasil); 4) SEC: código SIC da empresa (ADRs e listadas nos EUA); 5) regras pelo nome.
import pandas as pd, numpy as np, json, re, os, time, unicodedata, requests, glob
W = '/home/user/work/latam'; RAW = '/home/user/raw/latam/sec'
SET = ['Financeiro', 'Mineração e metais', 'Petróleo e gás', 'Utilidades', 'Consumo básico', 'Consumo discricionário', 'Industrial e transporte',
       'Materiais', 'Comunicações', 'Tecnologia', 'Saúde', 'Imobiliário', 'Fundos e ETFs', 'Outros']
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'\b(S\.?A\.?B?\.?( DE C\.?V\.?)?|S\.?A\.?A\.?|SA|SAB|SAA|DE CV|CV|INC|LTD|LTDA|LIMITED|PLC|CORP|CORPORATION|CO|COMPANY|HOLDINGS?|GROUP|GRUPO|ADR|SPONSORED|PN|ON|PREF|PFD|CLASS [A-Z]|CL [A-Z]|N ?V|THE|DE|DEL|LA|EL|Y|E|AND)\b', ' ', s)
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', s)).strip()
# ---------- 1) manual (maiores posições sem classificação automática confiável)
MAN = {
 'MERCADOLIBRE': 'Consumo discricionário', 'NU HOLDINGS': 'Financeiro', 'NU': 'Financeiro', 'CREDICORP': 'Financeiro', 'CONSORCIO CREDICORP': 'Financeiro',
 'INTERCORP FINANCIAL SERVICES': 'Financeiro', 'BANCOLOMBIA': 'Financeiro', 'CIBEST': 'Financeiro', 'BANORTE': 'Financeiro', 'FINANCIERO BANORTE': 'Financeiro',
 'GRUPO FINANCIERO BANORTE': 'Financeiro', 'INBURSA': 'Financeiro', 'BANCO SANTANDER CHILE': 'Financeiro', 'BANCO CHILE': 'Financeiro', 'BANCO CREDITO INVERSIONES': 'Financeiro',
 'GALICIA': 'Financeiro', 'FINANCIERO GALICIA': 'Financeiro', 'BANCO MACRO': 'Financeiro', 'BBVA ARGENTINA': 'Financeiro', 'XP': 'Financeiro', 'STONECO': 'Financeiro', 'PAGSEGURO DIGITAL': 'Financeiro',
 'DLOCAL': 'Tecnologia', 'GLOBANT': 'Tecnologia', 'VTEX': 'Tecnologia', 'ARCO PLATFORM': 'Consumo discricionário', 'AFYA': 'Consumo discricionário', 'VASTA PLATFORM': 'Consumo discricionário',
 'COPA': 'Industrial e transporte', 'LATAM AIRLINES': 'Industrial e transporte', 'AEROPORTUARIO PACIFICO': 'Industrial e transporte', 'AEROPORTUARIO SURESTE': 'Industrial e transporte',
 'AEROPORTUARIO CENTRO NORTE': 'Industrial e transporte', 'CORPORACION AMERICA AIRPORTS': 'Industrial e transporte', 'PROMOTORA OPERADORA INFRAESTRUCTURA': 'Industrial e transporte',
 'VOLARIS': 'Industrial e transporte', 'CONTROLADORA VUELA COMPANIA AVIACION': 'Industrial e transporte', 'TRAXION': 'Industrial e transporte', 'FERREYCORP': 'Industrial e transporte',
 'INVERSIONES PORTUARIAS CHANCAY': 'Industrial e transporte', 'AENZA': 'Industrial e transporte', 'CUMBRA HOLD': 'Industrial e transporte',
 'FOMENTO ECONOMICO MEXICANO': 'Consumo básico', 'FOMENTO ECONOMICO MEX': 'Consumo básico', 'FEMSA': 'Consumo básico', 'WAL MART MEXICO': 'Consumo básico', 'WALMART MEXICO': 'Consumo básico',
 'ARCA CONTINENTAL': 'Consumo básico', 'COCA COLA FEMSA': 'Consumo básico', 'BIMBO': 'Consumo básico', 'GRUMA': 'Consumo básico', 'KIMBERLY CLARK MEXICO': 'Consumo básico',
 'CENCOSUD': 'Consumo básico', 'FALABELLA': 'Consumo discricionário', 'RIPLEY': 'Consumo discricionário', 'INRETAIL PERU': 'Consumo básico', 'ALICORP': 'Consumo básico',
 'CERVECERIAS UNIDAS': 'Consumo básico', 'U CERVECERIAS PERUANAS B J': 'Consumo básico', 'EMBOTELLADORA ANDINA': 'Consumo básico', 'LIVERPOOL': 'Consumo discricionário',
 'ALSEA': 'Consumo discricionário', 'GENTERA': 'Financeiro', 'REGIONAL': 'Financeiro', 'QUALITAS CONTROLADORA': 'Financeiro', 'BOLSA MEXICANA VALORES': 'Financeiro',
 'AMERICA MOVIL': 'Comunicações', 'TELEVISA': 'Comunicações', 'ENTEL': 'Comunicações', 'TELECOM ARGENTINA': 'Comunicações', 'MEGACABLE': 'Comunicações',
 'GRUPO MEXICO': 'Mineração e metais', 'SOUTHERN COPPER': 'Mineração e metais', 'INDUSTRIAS PENOLES': 'Mineração e metais', 'PENOLES': 'Mineração e metais', 'FRESNILLO': 'Mineração e metais',
 'CIA MINAS BUENAVENTURA': 'Mineração e metais', 'COMPANIA MINAS BUENAVENTURA': 'Mineração e metais', 'CIA MINERA BUENAVENTURA': 'Mineração e metais', 'MINSUR': 'Mineração e metais',
 'SOCIEDAD QUIMICA MINERA CHILE': 'Materiais', 'SQM': 'Materiais', 'TERNIUM': 'Mineração e metais', 'CEMEX': 'Materiais', 'ORBIA ADVANCE': 'Materiais', 'ALPEK': 'Materiais',
 'UNACEM': 'Materiais', 'CEMENTOS PACASMAYO': 'Materiais', 'CEMENTOS ARGOS': 'Materiais', 'CMPC': 'Materiais', 'EMPRESAS CMPC': 'Materiais', 'CORPORACION ACEROS AREQUIPA': 'Mineração e metais',
 'YPF': 'Petróleo e gás', 'VISTA ENERGY': 'Petróleo e gás', 'PAMPA ENERGIA': 'Utilidades', 'TRANSPORTADORA GAS SUR': 'Petróleo e gás', 'ECOPETROL': 'Petróleo e gás', 'GEOPARK': 'Petróleo e gás',
 'EMPRESAS COPEC': 'Petróleo e gás', 'MAPLE': 'Petróleo e gás', 'RELAPASA': 'Petróleo e gás', 'CENTRAL PUERTO': 'Utilidades', 'EDENOR': 'Utilidades', 'EMPRESA DISTRIBUIDORA COMERCIALIZADORA NORTE': 'Utilidades',
 'ENEL CHILE': 'Utilidades', 'ENEL AMERICAS': 'Utilidades', 'COLBUN': 'Utilidades', 'INTERCONEXION ELECTRICA': 'Utilidades', 'ISA': 'Utilidades', 'ENGIE ENERGIA PERU': 'Utilidades',
 'ORYGEN PERU': 'Utilidades', 'PLUZ ENERGIA PERU': 'Utilidades', 'LUZ SUR': 'Utilidades', 'AGUAS ANDINAS': 'Utilidades',
 'PARQUE ARAUCO': 'Imobiliário', 'FIBRA UNO': 'Imobiliário', 'FIBRA MACQUARIE MEXICO': 'Imobiliário', 'PROLOGIS PROPERTY MEXICO': 'Imobiliário', 'CORPORACION INMOBILIARIA VESTA': 'Imobiliário', 'VESTA': 'Imobiliário',
 'IRSA': 'Imobiliário', 'CRESUD': 'Consumo básico', 'ADECOAGRO': 'Consumo básico', 'LOMA NEGRA': 'Materiais', 'EXALMAR': 'Consumo básico', 'EDITORA COMERCIO': 'Comunicações',
 'HOCHSCHILD MINING': 'Mineração e metais', 'HUDBAY MINERALS': 'Mineração e metais', 'NEXA RESOURCES': 'Mineração e metais', 'MMG': 'Mineração e metais', 'SIERRA METALS': 'Mineração e metais',
 'SEA': 'Consumo discricionário', 'VALE': 'Mineração e metais', 'DESPEGAR': 'Consumo discricionário', 'CONTROLADORA VUELA': 'Industrial e transporte', 'BUENAVENTU': 'Mineração e metais', 'AZUL': 'Industrial e transporte',
 'NEXA RES': 'Mineração e metais', 'ZIM INTEGRATED SHIPPING': 'Industrial e transporte', 'KASPI': 'Financeiro', 'ALIBABA': 'Consumo discricionário', 'BARRICK': 'Mineração e metais', 'MISSION PRODUCE': 'Consumo básico',
 'PICS': 'Financeiro', 'PICPAY': 'Financeiro', 'TAIWAN SEMICONDUCTOR': 'Tecnologia', 'ASML': 'Tecnologia', 'AERCAP': 'Industrial e transporte', 'D MARKET': 'Consumo discricionário', 'VIPSHOP': 'Consumo discricionário',
 'LUXOFT': 'Tecnologia', 'CORE SCIENTIFIC': 'Tecnologia', 'AVAL ACCIONES': 'Financeiro', 'AVAL': 'Financeiro', 'VULCAN MATLS': 'Materiais', 'HERTZ': 'Industrial e transporte', 'EMPRESA DIST Y COMERCIAL NOR': 'Utilidades',
 'GLOBAL X': 'Fundos e ETFs', 'INVESCO': 'Fundos e ETFs', 'GENOMMA LAB': 'Saúde', 'INVERSIONES SURAMERICANA': 'Financeiro', 'GCC': 'Materiais', 'SMU': 'Consumo básico', 'CARSO': 'Industrial e transporte',
 'NUTRESA': 'Consumo básico', 'PAREX RESOURCES': 'Petróleo e gás', 'PLAZA': 'Imobiliário', 'DAVIVIENDA': 'Financeiro', 'CHEDRAUI': 'Consumo básico', 'COMERCIAL CHEDRAUI': 'Consumo básico', 'ALFA': 'Materiais',
 'CELSIA': 'Utilidades', 'QUALITAS': 'Financeiro', 'BECLE': 'Consumo básico', 'GRANA MONTERO': 'Industrial e transporte', 'BOLIVAR': 'Financeiro', 'TERPEL': 'Petróleo e gás', 'ORGANIZACION TERPEL': 'Petróleo e gás',
 'CIA BRASILEIRA DISTRIBUICAO': 'Consumo básico', 'ENERGETICA CEARA': 'Utilidades', 'CONCHA TORO': 'Consumo básico', 'VINA CONCHA TORO': 'Consumo básico', 'CAP': 'Mineração e metais', 'EXITO': 'Consumo básico',
 'ALMACENES EXITO': 'Consumo básico', 'VEF': 'Financeiro', 'MEGA': 'Comunicações',
 'JBS': 'Consumo básico', 'TECNOGLASS': 'Industrial e transporte', 'ARGOS': 'Materiais', 'GRUPO ARGOS': 'Materiais', 'GRUPO SURA': 'Financeiro', 'SURAMERICANA': 'Financeiro',
}
MANN = {norm(k): v for k, v in MAN.items()}
# ---------- 2) Peru (SBS)
PE = {'Otras Empresas Financieras': 'Financeiro', 'Bancos': 'Financeiro', 'Minería': 'Mineração e metais', 'Energía': 'Utilidades', 'Hidrocarburos': 'Petróleo e gás',
      'Alimentos': 'Consumo básico', 'Cemento': 'Materiais', 'Inmobiliaria y Construcción': 'Industrial e transporte', 'Inmobiliaria y Construccion': 'Industrial e transporte',
      'Almacenes Comerciales': 'Consumo básico', 'Pesca': 'Consumo básico', 'Maquinaria': 'Industrial e transporte'}
# ---------- 3) B3
B3S = {'Financeiro': 'Financeiro', 'Materiais Básicos': 'Materiais', 'Petróleo, Gás e Biocombustíveis': 'Petróleo e gás', 'Utilidade Pública': 'Utilidades', 'Consumo não Cíclico': 'Consumo básico',
       'Consumo Cíclico': 'Consumo discricionário', 'Bens Industriais': 'Industrial e transporte', 'Comunicações': 'Comunicações', 'Tecnologia da Informação': 'Tecnologia', 'Saúde': 'Saúde'}
ac = pd.read_csv('/home/user/work/out/acoes.csv')
ac['set'] = ac.setor.map(B3S)
ac.loc[ac.subsetor.fillna('').str.contains('Mineração|Siderurgia|Metalurgia'), 'set'] = 'Mineração e metais'
ac.loc[ac.subsetor.fillna('').str.contains('Exploração de Imóveis'), 'set'] = 'Imobiliário'
B3tk = {t[:4]: s for t, s in zip(ac.tk, ac.set) if isinstance(s, str)}
B3nm = {norm(n): s for n, s in zip(ac.empresa, ac.set) if isinstance(s, str) and isinstance(n, str)}
# ---------- 4) SEC (SIC)
TK = json.load(open(RAW + '/company_tickers.json'))
sec_tk = {v['ticker'].upper(): v['cik_str'] for v in TK.values()}
sec_nm = {}
for v in TK.values(): sec_nm.setdefault(norm(v['title']), v['cik_str'])
CACHE = RAW + '/sic.json'; sic = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
S = requests.Session(); S.headers['User-Agent'] = 'Navegando-Research/1.0 research@example.org'
def get_sic(cik):
    k = str(cik)
    if k not in sic:
        r = S.get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json', timeout=30); time.sleep(0.12)
        sic[k] = [r.json().get('sic'), r.json().get('sicDescription')] if r.ok else [None, None]
    return sic[k]
def sic2(s):
    try: s = int(s)
    except (TypeError, ValueError): return None
    if s in (1311, 1381, 1382, 1389) or 2900 <= s < 3000: return 'Petróleo e gás'
    if 1000 <= s < 1500 or 3300 <= s < 3400: return 'Mineração e metais'
    if 1500 <= s < 1800: return 'Industrial e transporte'
    if 2000 <= s < 2200: return 'Consumo básico'
    if 2200 <= s < 2400 or s == 3711 or 3940 <= s < 3950: return 'Consumo discricionário'
    if 2834 <= s <= 2836: return 'Saúde'
    if 2400 <= s < 2700 or 2800 <= s < 2900 or 3000 <= s < 3300: return 'Materiais'
    if 2700 <= s < 2800: return 'Comunicações'
    if 3570 <= s < 3580 or 3600 <= s < 3700 or 7370 <= s < 7380: return 'Tecnologia'
    if 3841 <= s <= 3851 or 8000 <= s < 8100: return 'Saúde'
    if 3400 <= s < 4000 or 4000 <= s < 4800 or 5000 <= s < 5100 or 7300 <= s < 7370 or 7380 <= s < 7400 or 8700 <= s < 8800: return 'Industrial e transporte'
    if 4800 <= s < 4900: return 'Comunicações'
    if 4900 <= s < 5000: return 'Utilidades'
    if 5100 <= s < 5200 or 5400 <= s < 5500 or s == 5912: return 'Consumo básico'
    if 5200 <= s < 6000 or 7000 <= s < 7100 or 7800 <= s < 8000 or 8200 <= s < 8300: return 'Consumo discricionário'
    if 6500 <= s < 6560 or s == 6798: return 'Imobiliário'
    if 6000 <= s < 6800: return 'Financeiro'
    return None
# ---------- 5) nome
RULES = [(r'BANCO|BANK|BANC|FINANC|CREDIT|SEGUR|INSURANCE|CAPITAL|INVEST|BOLSA|PAGOS|FINTECH', 'Financeiro'),
         (r'MINER|MINING|GOLD|SILVER|COPPER|COBRE|METAL|ACERO|STEEL|ZINC|LITHIUM|LITIO|SIDER', 'Mineração e metais'),
         (r'PETRO|OIL|GAS|ENERG(Y|IA) (PETRO|OIL)|HIDROCARB', 'Petróleo e gás'),
         (r'ELECTRIC|ELETR|ENERGI|ENERGY|POWER|AGUAS|WATER|SANEAMENTO|UTILIT|GENERAC|TRANSMIS', 'Utilidades'),
         (r'AEROPORT|AIRPORT|AIRLINE|AVIA|PORT|LOGIST|TRANSPORT|RAIL|FERRO|INFRA|CONSTRUC|INGENIER|ENGINEER', 'Industrial e transporte'),
         (r'TELE|MOVIL|MOBILE|CABLE|MEDIA|COMUNIC', 'Comunicações'),
         (r'FOOD|ALIMENT|BEBIDA|BEVERAGE|CERVE|BREW|COCA|SUPERMERC|FARMAC|PHARMACY', 'Consumo básico'),
         (r'RETAIL|TIENDA|LOJA|STORE|HOTEL|EDUCA|RESTAUR|AUTO', 'Consumo discricionário'),
         (r'CEMENT|CIMENT|PAPEL|PAPER|CELUL|QUIMIC|CHEMIC|PLAST', 'Materiais'),
         (r'SALUD|SAUDE|HEALTH|HOSPITAL|MEDIC|PHARMA', 'Saúde'),
         (r'SOFTWARE|TECHNOLOG|TECNOLOG|DIGITAL|DATA', 'Tecnologia'),
         (r'FIBRA|INMOBIL|IMOBIL|REAL ESTATE|PROPERT|REIT|SHOPPING|MALL', 'Imobiliário'),
         (r'ETF|ISHARES|INDEX|FUND|FUNDO|TRUST', 'Fundos e ETFs')]
fonte = {}
def classify(name, tickers=(), pais=None, sbs=None):
    n = norm(name)
    for k in [n] + [' '.join(n.split()[:i]) for i in (3, 2, 1)]:
        if k and k in MANN: return MANN[k], 'manual'
    for k, v in MANN.items():
        if len(k) >= 8 and (n.startswith(k) or (len(n) >= 12 and k.startswith(n))): return v, 'manual'
    if sbs and sbs in PE: return PE[sbs], 'SBS'
    if pais == 'BR' or any(re.match(r'^[A-Z]{4}\d{1,2}$', t or '') for t in tickers):
        for t in tickers:
            if t and t[:4] in B3tk: return B3tk[t[:4]], 'B3'
        for k in [n, ' '.join(n.split()[:2]), n.split()[0] if n else '']:
            if k in B3nm: return B3nm[k], 'B3'
    cik = None
    for t in tickers:
        if t and t.upper() in sec_tk: cik = sec_tk[t.upper()]; break
    if cik is None:
        for k in [n, ' '.join(n.split()[:3]), ' '.join(n.split()[:2])]:
            if k in sec_nm: cik = sec_nm[k]; break
    if cik is not None:
        s = sic2(get_sic(cik)[0])
        if s: return s, 'SEC'
    for rx, s in RULES:
        if re.search(rx, n): return s, 'nome'
    return 'Outros', 'sem'
out = {}
# Peru
pe = json.load(open(W + '/pe_attr.json'))
out['pe'] = {e: classify(e, sbs=s) for e, s in pe['emissores'].items()}
# EUA (fundos e agregado) e 13F: nomes e tickers
us = json.load(open(W + '/us_attr.json')); f13 = json.load(open(W + '/f13_attr.json')); lt = json.load(open(W + '/latam.json'))
tick = {}
for f in sorted(glob.glob(W + '/nf/*.pkl')):
    h = pd.read_pickle(f)['h']
    for n, t in zip(h.ISSUER_NAME, h.ticker):
        if isinstance(t, str): tick.setdefault(norm(n), set()).add(t.upper().split()[0])
def tks(name): return tuple(tick.get(norm(name), ()))
out['us'] = {e: classify(v[0], tks(v[0]), v[1]) for e, v in us['emp'].items()}
out['f13'] = {e: classify(v[0], ()) for e, v in f13['emp'].items()}
out['agg'] = {e: classify(v['nome'], (v.get('tk') or '',), v.get('pais')) for e, v in lt['us']['emp'].items()}
json.dump(sic, open(CACHE, 'w'))
json.dump({k: {e: s for e, (s, src) in v.items()} for k, v in out.items()}, open(W + '/setores.json', 'w'), ensure_ascii=False)
# conferência: peso coberto por fonte, nas carteiras de fundos dos EUA e 13F (último período)
for base, D_, nmf in (('us', us, lambda e: us['emp'].get(e, [e])[0]), ('f13', f13, lambda e: f13['emp'].get(e, [e])[0])):
    wsrc = {}; miss = {}
    for f in D_['fundos'].values():
        for e, v in f['p'].items():
            if e.startswith('Outros'): continue
            w = v[0][-1] or 0; s, src = out[base].get(e, ('Outros', 'sem')); wsrc[src] = wsrc.get(src, 0) + w
            if src == 'sem': miss[nmf(e)] = miss.get(nmf(e), 0) + w
    tot = sum(wsrc.values()); print(base, {k: round(v / tot, 3) for k, v in wsrc.items()})
    print('  sem setor:', sorted(miss.items(), key=lambda z: -z[1])[:25])
