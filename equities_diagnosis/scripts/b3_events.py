"""Proventos em dinheiro e eventos (desdobramento, grupamento, bonificação) por emissor, pela API pública da B3.
Uso: python3 b3_events.py <codigos.txt com códigos de 4 letras> <saida_dir>
Grava um JSON por código: {code, tradingName, stock: [...], cash: [...]}; pula os que já existem."""
import sys, os, json, base64, time, urllib.request
CODES, OUT = sys.argv[1:3]
os.makedirs(OUT, exist_ok=True)
BASE = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/'

def get(fn, payload):
    q = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    for k in range(4):
        try:
            with urllib.request.urlopen(BASE + fn + '/' + q, timeout=60) as r:
                b = r.read()
                return json.loads(b) if b else None
        except Exception as e:
            time.sleep(2 * (k + 1))
    return None

for code in open(CODES).read().split():
    f = os.path.join(OUT, code + '.json')
    if os.path.exists(f):
        continue
    sup = get('GetListedSupplementCompany', {'issuingCompany': code, 'language': 'pt-br'})
    rec = {'code': code, 'tradingName': None, 'stock': [], 'cash': []}
    if sup and isinstance(sup, list) and sup:
        s = sup[0]; rec['tradingName'] = (s.get('tradingName') or '').strip(); rec['stock'] = s.get('stockDividends') or []
        if rec['tradingName']:
            page = 1
            while True:
                d = get('GetListedCashDividends', {'language': 'pt-br', 'pageNumber': page, 'pageSize': 120, 'tradingName': rec['tradingName']})
                if not d or not d.get('results'):
                    break
                rec['cash'] += d['results']
                if page >= d['page']['totalPages']:
                    break
                page += 1
    json.dump(rec, open(f, 'w'), ensure_ascii=False)
    print(code, rec['tradingName'], len(rec['stock']), len(rec['cash']), flush=True)
    time.sleep(0.3)
