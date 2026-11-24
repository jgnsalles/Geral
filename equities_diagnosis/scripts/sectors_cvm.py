"""Setor pela CVM: ticker -> CNPJ (FCA, valores mobiliários 2010+) -> SETOR_ATIV (cadastro de companhias abertas).
Combina com a classificação da B3 já coletada (preferida) e grava os baldes.
Uso: python3 sectors_cvm.py <pasta cia> <codes.txt> <sectors_b3.json> <saida.json>"""
import sys, os, glob, zipfile, json, re, unicodedata, importlib.util
import pandas as pd
D, CODES, B3J, OUT = sys.argv[1:5]
spec = importlib.util.spec_from_file_location('sec', os.path.join(os.path.dirname(__file__), 'sectors.py'))
src = open(os.path.join(os.path.dirname(__file__), 'sectors.py')).read()
bucket_src = src[src.index('def bucket'):src.index('for k, v in cache.items()')]
dea = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
exec(bucket_src)
vm = []
for z in sorted(glob.glob(os.path.join(D, 'fca_cia_aberta_*.zip'))):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if 'valor_mobiliario' in n:
            d = pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str)
            vm.append(d[['CNPJ_Companhia', 'Codigo_Negociacao']])
vm = pd.concat(vm).dropna(); vm['root'] = vm.Codigo_Negociacao.str.strip().str.upper().str[:4]
cad = pd.read_csv(os.path.join(D, 'cad_cia_aberta.csv'), sep=';', encoding='latin1', dtype=str)
sec = cad.dropna(subset=['SETOR_ATIV']).drop_duplicates('CNPJ_CIA', keep='last').set_index('CNPJ_CIA').SETOR_ATIV
r2s = vm.assign(s=vm.CNPJ_Companhia.map(sec)).dropna(subset=['s']).groupby('root').s.agg(lambda x: x.value_counts().index[0])
b3 = json.load(open(B3J)) if os.path.exists(B3J) else {}
CVM = [('SEM SETOR', None), ('SEGURADORAS', 'Seguros'), ('PREVIDENCIA', 'Seguros'), ('BANCOS', 'Financials'), ('INTERMEDIACAO FINANCEIRA', 'Financials'),
       ('CREDITO IMOBILIARIO', 'Financials'), ('ARRENDAMENTO', 'Financials'), ('SECURITIZ', 'Financials'), ('BOLSA', 'Financials'),
       ('ENERGIA ELETRICA', 'Utilities'), ('SANEAMENTO', 'Utilities'), ('COMERCIO', 'Varejo'), ('TEXTIL', 'Varejo'),
       ('CONSTRUCAO CIVIL', 'Real Estate'), ('MAQUINAS', 'Industrials'), ('EMBALAGENS', 'Industrials'), ('SERVICOS EM GERAL', 'Industrials'),
       ('TRANSPORTE', 'Transporte'), ('COMUNICACAO', 'TMT'), ('TELECOMUNICAC', 'TMT'), ('GRAFICAS', 'TMT'),
       ('METALURGIA', 'Commodities'), ('EXTRACAO MINERAL', 'Commodities'), ('PETROLEO', 'Commodities'), ('PETROQUIMICOS', 'Commodities'),
       ('PAPEL E CELULOSE', 'Commodities'), ('AGRICULTURA', 'Commodities'), ('QUIMICA', 'Commodities'), ('SERVICOS MEDICOS', 'Saúde'),
       ('FARMACEUTICO', 'Saúde'), ('EDUCACAO', 'Educação'), ('ALIMENTOS', 'Consumo'), ('BEBIDAS', 'Consumo'), ('BRINQUEDOS', 'Consumo'),
       ('HOSPEDAGEM', 'Consumo'), ('REFLORESTAMENTO', 'Commodities')]
def bucket_cvm(raw):
    s = dea(raw).replace('EMP. ADM. PART. - ', '')
    for k, b in CVM:
        if k in s: return b or 'Outros'
    return 'Outros'
MALLS = {'ALOS', 'ALSO', 'MULT', 'IGTI', 'IGTA', 'BRML', 'SSBR', 'GSHP', 'SCAR', 'AGRU'}
out = {}
for c in open(CODES).read().split():
    raw = (b3.get(c) or {}).get('raw')
    src_ = 'B3'
    if not raw and c in r2s: raw = r2s[c]; src_ = 'CVM'
    b = (bucket(raw, c) if src_ == 'B3' else bucket_cvm(raw)) if raw else 'Outros'
    if c in MALLS: b = 'Malls'
    out[c] = {'raw': raw, 'b': b, 'src': src_ if raw else None}
json.dump(out, open(OUT, 'w'), ensure_ascii=False)
import collections
print(collections.Counter(v['b'] for v in out.values()).most_common()); print('sem setor:', sum(1 for v in out.values() if not v['raw']))
print(collections.Counter(r2s.values).most_common(40))
