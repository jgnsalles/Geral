"""Gera price_tracker/painel/price_tracker.html: o painel do Price Tracker (substitui o uso diário do Excel V3).
A página lê o .xlsx salvo pelo Excel (valores já calculados com o Wisesheets) com SheetJS no navegador e já vem com os dados de hoje embutidos.
O MESMO "SPEC" (cabeçalhos procurados) é usado aqui em Python e no parser JS, para os dois lerem igual.
Uso: python3 painel/build_painel.py <planilha.xlsx> [saida.html]"""
import sys, json, math, pathlib, datetime
import openpyxl

SRC = sys.argv[1]
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(__file__).parent / 'price_tracker.html')
HERE = pathlib.Path(__file__).parent

SPEC = {
    'acoes': {'t': 'Ticker', 'nm': 'Empresa', 'sec': 'Setor', 'ind': 'Indústria', 'px': 'Preço', 'mc': 'Valor de mercado (US$ bi)', 'pl': 'P/L',
              'g': 'Crescimento', 'roic': 'ROIC', 'pej': 'P/E justo', 'ret': 'Retorno esperado', 'cls': 'Classe', 'lists': 'Listas', 'flag': 'Atenção',
              'gh': 'Cresc. histórico', 'zg': 'zGrowth', 'bag': 'Bagger #'},
    'calc1': {'graw': 'Crescimento sem teto', 'gv': 'Crescimento p/ valuation (c/ haircut)', 'gc': 'Crescimento do consenso (classe)',
              'ghm': 'Cresc. histórico (mediana)', 'na': 'n A', 'meda': 'mediana A', 'siga': 'σ A', 'np': 'n P', 'medp': 'mediana P', 'sigp': 'σ P',
              'va': 'ROIC ativo', 'vp': 'ROIC passivo', 'vm': 'ROIC marginal', 'tri': 'ROIC triangulado', 'roem': 'ROE (média)', 'fin': 'Usa ROE?',
              'ru': 'ROIC usado', 'fxh': 'Fator US$/ADR (balanço)', 'fxe': 'Fator US$/ADR (estimativas)', 'pll': 'P/L LTM', 'plf': 'P/L 1 ano à frente',
              'gg': 'g do P/E justo', 'dy': 'Dividend yield', 'rf': 'Ret. P/E justo', 'rc': 'Ret. múltiplo constante', 'cod': 'Código',
              'base': 'Classe (régua)', 'cyc': 'Cíclica', 'app': 'Vestuário', 'dup': 'Repetida', 'qual': 'Qualidade', 'hr': 'High ROIC',
              'hg': 'High Growth', 'exc': 'Excepcional', 'rks': 'Posição no setor', 'rkt': 'Posição Top 20', 'wt': 'Peso Top 20',
              'secw': 'peso do setor', 'rke': 'Posição Especiais', 'we': 'Peso Especiais', 'rkj': 'Posição JG+G', 'wj': 'Peso JG+G',
              'wx': 'Peso Excepcionais'},
    'calcn': {'eh': ['EPS estimado c/ haircut', 3], 'ga': ['Cresc. anual estimado c/ haircut', 3], 'gr0': ['Cresc. anual do consenso', 3], 'ghs': ['Cresc. histórico', 3], 'nop': ['NOPAT', 4],
              'ca': ['Capital ativo', 4], 'cp': ['Capital passivo', 4], 'ra': ['ROIC ativo', 4], 'rp': ['ROIC passivo', 4],
              'xa': ['sem outlier A', 4], 'xp': ['sem outlier P', 4], 'roe': ['ROE', 4]},
    'dados': {'est': 'Estimated EPS AVG', 'eps': 'EPS Diluted', 'ni': 'Net Income', 'oi': 'Operating Income', 'pt': 'Income Before Tax',
              'tx': 'Income Tax Expense', 'ppe': 'Property Plant Equipment Net', 'rou': 'Operating Lease Right Of Use Assets', 'gw': 'Goodwill',
              'int': 'Intangible Assets', 'tca': 'Total Current Assets', 'cash': 'Cash And Cash Equivalents', 'tcl': 'Total Current Liabilities',
              'debt': 'Total Debt', 'lease': 'Capital Lease Obligations', 'eq': 'Total Stockholders Equity', 'dyr': 'Dividend Yield'},
    'rules': {'ghi': 'Crescimento alto', 'glo': 'Crescimento baixo', 'zgmax': 'zGrowth máximo', 'rhi': 'ROIC alto', 'rlo': 'ROIC baixo',
              'rethi': 'Retorno esperado alto', 'retlo': 'Retorno esperado baixo', 'wacc': 'WACC do P/E justo', 'gtop': 'g do P/E justo: maior',
              'gfloor': 'g do P/E justo: menor', 'gfin': 'Financeiras', 'hrc': 'High ROIC', 'hgc': 'High Growth', 'plmin': 'Top 20: P/L mínimo',
              'nlista': 'Tamanho das listas', 'teto': 'Peso máximo por ação', 'h1': 'Haircut EPS ano+1', 'h2': 'Haircut EPS ano+2',
              'h3': 'Haircut EPS ano+3', 'gmax': 'Teto do crescimento', 'capn': 'Top 20: máximo de ações por setor',
              'capw': 'Top 20: peso máximo por setor'},
    'lists': {'cycl': 'Cíclicas (indústria)', 'notcyc': 'Exceções: não cíclica (ticker)', 'appl': 'Vestuário (indústria)',
              'roet': 'Usam ROE (ticker)', 'excl': 'Excluídas à mão (ticker)'},
}

num = lambda v: (round(v, 6) if isinstance(v, float) and math.isfinite(v) else v) if isinstance(v, (int, float)) and not isinstance(v, bool) else (None if v in ('', None) else v)


def grid(ws):
    return [[c for c in row] for row in ws.iter_rows(values_only=True)]


def parse(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    A, C, D, G = (grid(wb[n]) for n in ('Ações', 'Cálculo', 'Dados', 'Regras'))
    hA = {v: i for i, v in reversed(list(enumerate(A[3]))) if v}
    hC = {}
    for i, v in enumerate(C[3]):
        if v and v not in hC: hC[v] = i
    # blocos da Dados: nome na linha 3 (índice 2), anos na linha 4 (índice 3), até a próxima coluna vazia
    blocks = {}; cur = None
    for i, (b, y) in enumerate(zip(D[2], D[3])):
        if b: cur = b; blocks[cur] = {'cols': [], 'years': []}
        if cur and isinstance(y, (int, float)): blocks[cur]['cols'].append(i); blocks[cur]['years'].append(int(y))
        if y is None and b is None: cur = None
    tkD = {row[0]: row for row in D[4:] if row and row[0]}
    stocks = []
    for r, row in enumerate(A[4:], start=4):
        t = row[hA['Ticker']] if 'Ticker' in hA else None
        if not t: continue
        s = {k: num(row[hA[h]]) if h in hA else None for k, h in SPEC['acoes'].items()}
        crow = C[r] if r < len(C) else []
        for k, h in SPEC['calc1'].items(): s[k] = num(crow[hC[h]]) if h in hC and hC[h] < len(crow) else None
        for k, (h, n) in SPEC['calcn'].items():
            s[k] = [num(crow[hC[f'{h} {i + 1}']]) if f'{h} {i + 1}' in hC else None for i in range(n)]
        drow = tkD.get(t, [])
        for k, h in SPEC['dados'].items():
            b = blocks.get(h); s[k] = [num(drow[c]) if c < len(drow) else None for c in b['cols']] if b and drow else None
        stocks.append(s)
    years = {k: blocks[h]['years'] for k, h in SPEC['dados'].items() if h in blocks}
    rules = {}
    for row in G[4:40]:
        lab, val = (row[0] if row else None), (row[1] if row and len(row) > 1 else None)
        if not lab: continue
        for k, h in SPEC['rules'].items():
            if k not in rules and str(lab).startswith(h): rules[k] = num(val)
    hdr = G[3]
    lists = {}
    for k, h in SPEC['lists'].items():
        if h in hdr:
            c = hdr.index(h); lists[k] = [row[c] for row in G[4:] if len(row) > c and row[c]]
    adr, fx = {}, {}
    if 'Ticker (moeda ≠ USD)' in hdr:
        c = hdr.index('Ticker (moeda ≠ USD)')
        for row in G[4:]:
            if len(row) > c + 3 and row[c]: adr[row[c]] = {'moeda': row[c + 1], 'n': num(row[c + 2]), 'est': row[c + 3]}
    if 'US$ por unidade' in hdr:
        c = hdr.index('US$ por unidade')
        for row in G[4:]:
            if len(row) > c and row[c - 1]: fx[row[c - 1]] = num(row[c])
    return {'stocks': stocks, 'years': years, 'rules': rules, 'lists': lists, 'adr': adr, 'fx': fx}


model = parse(SRC)
model['fonte'] = 'Dados embutidos: planilha de ' + datetime.date.today().strftime('%d/%m/%Y')
html = (HERE / 'template.html').read_text()
html = html.replace('/*__SPEC__*/null', json.dumps(SPEC, ensure_ascii=False)).replace('/*__DATA__*/null', json.dumps(model, ensure_ascii=False, separators=(',', ':')))
OUT.write_text(html)
json.dump(model, open(HERE / 'modelo_embutido.json', 'w'), ensure_ascii=False)
print('ok', OUT, len(model['stocks']), 'ações', len(html) // 1024, 'KB')
