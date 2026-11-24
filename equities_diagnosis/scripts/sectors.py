"""Setor de cada empresa (raiz de 4 letras): classificação da B3 (GetDetail via código CVM) e, na falta, a planilha antiga
de setores. Agrupa nos baldes do Equities Diagnosis.
Uso: python3 sectors.py <codigos.txt> <acoes.csv antigo> <saida.json>"""
import sys, json, base64, time, urllib.request, unicodedata, csv, os
CODES, OLD, OUT = sys.argv[1:4]
BASE = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/'
def get(fn, payload):
    q = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    for k in range(4):
        try:
            with urllib.request.urlopen(BASE + fn + '/' + q, timeout=60) as r:
                b = r.read(); return json.loads(b) if b else None
        except Exception:
            time.sleep(3 * (k + 1))
    return None
dea = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
cache = json.load(open(OUT)) if os.path.exists(OUT) else {}
old = {}
for row in csv.DictReader(open(OLD, encoding='utf-8')):
    old[row['tk'][:4]] = f"{row['setor']} / {row['subsetor']}"
for code in open(CODES).read().split():
    if code in cache and cache[code].get('raw'): continue
    sup = get('GetListedSupplementCompany', {'issuingCompany': code, 'language': 'pt-br'})
    raw = None
    if sup and isinstance(sup, list) and sup and sup[0].get('codeCVM'):
        det = get('GetDetail', {'codeCVM': sup[0]['codeCVM'], 'language': 'pt-br'})
        raw = (det or {}).get('industryClassification')
    cache[code] = {'raw': raw or old.get(code)}
    time.sleep(0.25)
    if len(cache) % 50 == 0:
        json.dump(cache, open(OUT, 'w'), ensure_ascii=False); print(len(cache), flush=True)

def bucket(raw, name):
    s = dea(raw); n = dea(name)
    if not s: return 'Outros'
    if 'SHOPPING' in n or ('EXPLORACAO DE IMOVEIS' in s): return 'Malls'
    if 'PREVIDENCIA E SEGUROS' in s or 'SEGURADORA' in s or 'CORRETORA DE SEGUROS' in s: return 'Seguros'
    if 'FINANCEIRO' in s or 'BANCOS' in s or 'HOLDINGS DIVERSIFICADAS' in s or 'SERVICOS FINANCEIROS' in s: return 'Financials'
    if 'UTILIDADE PUBLICA' in s or 'ENERGIA ELETRICA' in s or 'AGUA E SANEAMENTO' in s or ('GAS' in s and 'PETROLEO' not in s): return 'Utilities'
    if 'PETROLEO' in s or 'MATERIAIS BASICOS' in s or 'MINERACAO' in s or 'SIDERURGIA' in s or 'PAPEL E CELULOSE' in s or 'QUIMICOS' in s \
       or 'AGROPECUARIA' in s or 'ACUCAR E ALCOOL' in s or 'MADEIRA' in s: return 'Commodities'
    if 'CONSTRUCAO CIVIL' in s or 'INCORPORAC' in s or 'IMOVEIS' in s: return 'Real Estate'
    if 'SAUDE' in s: return 'Saúde'
    if 'TECNOLOGIA DA INFORMACAO' in s or 'COMUNICACOES' in s or 'TELECOMUNIC' in s or 'MIDIA' in s or 'PROGRAMAS E SERVICOS' in s: return 'TMT'
    if 'TRANSPORTE' in s or 'ALUGUEL DE CARROS' in s or 'LOGISTICA' in s or 'RODOVIAS' in s or 'PORTUARI' in s: return 'Transporte'
    if 'EDUCAC' in s or 'ENSINO' in s: return 'Educação'
    if 'COMERCIO' in s or 'TECIDOS' in s or 'VESTUARIO' in s or 'CALCADOS' in s or 'VAREJO' in s or 'ELETRODOMESTICOS' in s or 'UTILIDADES DOMESTICAS' in s: return 'Varejo'
    if 'CONSUMO NAO CICLICO' in s or 'ALIMENTOS' in s or 'BEBIDAS' in s or 'CARNES' in s or 'HIGIENE' in s or 'PRODUTOS DE USO PESSOAL' in s: return 'Consumo'
    if 'BENS INDUSTRIAIS' in s or 'MAQUINAS' in s or 'MATERIAL DE TRANSPORTE' in s or 'CONSTRUCAO E ENGENHARIA' in s or 'SERVICOS' in s: return 'Industrials'
    if 'CONSUMO CICLICO' in s or 'VIAGENS E LAZER' in s or 'HOTEIS' in s or 'AUTOMOVEIS' in s: return 'Consumo'
    return 'Outros'
for k, v in cache.items():
    v['b'] = bucket(v.get('raw'), k)
json.dump(cache, open(OUT, 'w'), ensure_ascii=False)
import collections
print(collections.Counter(v['b'] for v in cache.values()).most_common())
