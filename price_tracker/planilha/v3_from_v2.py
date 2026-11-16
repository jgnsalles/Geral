"""Price Tracker v3 = a própria V2 com o MODELO DETERMINÍSTICO do Python (crescimento pela mediana de 5 anos do EPS, ROIC triangulado com
outliers e visão marginal, P/E justo, retorno esperado, classes, Top 20, Especiais, JG+G e pesos), tudo com dados históricos do Wisesheets.
Teste de igualdade: planilha/teste_igualdade.py + planilha/teste_compara.py.
Histórico: v3 = a própria V2 (mesmas abas, fórmulas, gráficos e chamadas ao Wisesheets) + um bloco pequeno de colunas novas na aba
Formula: ROIC triangulado enxuto (último ano, 10 campos numa chamada por bloco), filtro de cíclicas/vestuário, High ROIC, High Growth,
Especiais, Top 20 com peso. Cortes novos: ROIC 12%, zROIC desligado. Edita o XML direto (não passa pelo openpyxl, para não perder nada).
Crescimento, P/L e retorno esperado vêm do histórico (mediana de 5 anos do EPS), não das estimativas do sell-side.
Uso: python3 planilha/v3_from_v2.py <V2.xlsx> <saida.xlsx>"""
import sys, re, zipfile
from xml.sax.saxutils import escape
from lxml import etree

SRC, OUT = sys.argv[1], sys.argv[2]
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
q = lambda t: f'{{{NS}}}{t}'
BLOCKS = [(6, 206, 5, 4), (211, 233, 210, 209)]  # (primeira linha, última, linha de cabeçalho, linha de grupo)
FIELDS = ['Operating Income', 'Income Before Tax', 'Income Tax Expense', 'Property Plant Equipment Net', 'Goodwill And Intangible Assets',
          'Total Current Assets', 'Total Current Liabilities', 'Cash And Cash Equivalents', 'Total Debt', 'Total Stockholders Equity']
CYC = ['Oil & Gas Exploration & Production', 'Oil & Gas Equipment & Services', 'Oil & Gas Drilling', 'Oil & Gas Refining & Marketing', 'Copper', 'Steel',
       'Agricultural Inputs', 'Department Stores', 'Airlines, Airports & Air Services', 'Recreational Vehicles', 'Gambling, Resorts & Casinos',
       'Electronic Gaming & Multimedia', 'Insurance - Diversified', 'Medical - Distribution', 'Leisure']
APP = ['Apparel - Manufacturers', 'Apparel - Footwear & Accessories', 'Luxury Goods']


def col_idx(ref):
    letters = re.match(r'([A-Z]+)', ref).group(1); n = 0
    for ch in letters: n = n * 26 + ord(ch) - 64
    return n


def L(n):
    s = ''
    while n: n, r = divmod(n - 1, 26); s = chr(65 + r) + s
    return s


z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
sheet = 'xl/worksheets/sheet4.xml'
root = etree.fromstring(files[sheet])
sd = root.find(q('sheetData'))
rows = {int(r.get('r')): r for r in sd.findall(q('row'))}


def row(r):
    if r not in rows:
        el = etree.Element(q('row')); el.set('r', str(r))
        after = [k for k in rows if k < r]
        if after: rows[max(after)].addnext(el)
        else: sd.insert(0, el)
        rows[r] = el
    return rows[r]


def put(ref, formula=None, value=None, style=None, text=None, array=None):
    r = int(re.search(r'\d+', ref).group(0)); rw = row(r); ci = col_idx(ref)
    for c in rw.findall(q('c')):
        if c.get('r') == ref: rw.remove(c)
    c = etree.Element(q('c')); c.set('r', ref)
    if style is not None: c.set('s', str(style))
    if text is not None:
        c.set('t', 'inlineStr'); is_ = etree.SubElement(c, q('is')); t = etree.SubElement(is_, q('t')); t.text = text
    elif formula is not None:
        f = etree.SubElement(c, q('f')); f.text = formula
        if array: f.set('t', 'array'); f.set('ref', array); c.set('cm', '1')
    elif value is not None:
        v = etree.SubElement(c, q('v')); v.text = str(value)
    pos = None
    for i, cc in enumerate(rw.findall(q('c'))):
        if col_idx(cc.get('r')) > ci: pos = cc; break
    if pos is not None: pos.addprevious(c)
    else: rw.append(c)


def edit_formula(ref, fn):
    r = int(re.search(r'\d+', ref).group(0))
    for c in rows[r].findall(q('c')):
        if c.get('r') == ref:
            f = c.find(q('f'))
            if f is not None and f.text: f.text = fn(f.text)
            v = c.find(q('v'))
            if v is not None: c.remove(v)
            return True
    return False


# 1) cortes novos
for c in rows[48].findall(q('c')):
    if c.get('r') == 'AV48': c.find(q('v')).text = '0.12'
for c in rows[50].findall(q('c')):
    if c.get('r') == 'AV50': c.find(q('v')).text = '99'
put('AW48', text='v3: 12% (antes 20%)', style=7); put('AW50', text='v3: desligado (antes 0,7)', style=7)
# listas de cíclicas e vestuário (editáveis)
put('AU55', text='Cíclicas (indústria)', style=3); put('AV55', text='Vestuário (indústria)', style=3)
for i in range(20):
    if i < len(CYC): put(f'AU{56 + i}', text=CYC[i], style=7)
    if i < len(APP): put(f'AV{56 + i}', text=APP[i], style=7)
CYCR, APPR = '$AU$56:$AU$75', '$AV$56:$AV$75'

# ============================================================================================================
# 2) MODELO DETERMINÍSTICO (o mesmo do Python: backtest.py, roic3.py, validation_portfolios.py, relatorio/calc2.py)
#    Tudo vem do HISTÓRICO do Wisesheets (nenhuma estimativa de sell-side). Ano mais recente = YEAR(TODAY())-1.
# ============================================================================================================
for c in rows[47].findall(q('c')):
    if c.get('r') == 'AV47': c.find(q('v')).text = '2.93'
put('AW47', text='v3: 2,93 (histórico; antes 0,9)', style=7)
put('AU77', text='ROE (seguradoras de saúde)', style=3)
HEALTH = ['UNH', 'ELV', 'CNC', 'HUM', 'MOH', 'CI']
for i, t in enumerate(HEALTH): put(f'AU{78 + i}', text=t, style=7)
HLR = '$AU$78:$AU$83'
PCT, TXT, HDR, NUM = 29, 7, 3, 32

cur = [col_idx('BC')]


def take(n):
    out = [L(cur[0] + i) for i in range(n)]; cur[0] += n
    return out


# --- saídas (o que se olha) ---
OUTN = ['ROIC ativo', 'ROIC passivo', 'ROIC marginal', 'ROIC triangulado', 'ROIC (usado)', 'Market Cap', 'Cíclica', 'Vestuário', 'Qualidade',
        'High ROIC', 'High Growth', 'Excepcional', 'Especiais', 'Peso Esp.', 'Top 20', 'Peso Top 20', 'JG+G', 'Peso JG+G']
O = dict(zip(OUTN, take(len(OUTN))))
FIRST_DATA = cur[0]
# --- dados do Wisesheets: um campo por chamada, vários anos (como o ROIC da V2) ---
INC = [('EPS', 'EPS Diluted'), ('NI', 'Net Income'), ('OI', 'Operating Income'), ('PT', 'Income Before Tax'), ('TX', 'Income Tax Expense'),
       ('EQI', 'Income From Equity Method Investments')]
BAL = [('PPE', 'Property Plant Equipment Net'), ('ROU', 'Operating Lease Right Of Use Assets'), ('GW', 'Goodwill'), ('INT', 'Intangible Assets'),
       ('LTI', 'Long Term Investments'), ('TCA', 'Total Current Assets'), ('CASH', 'Cash And Cash Equivalents'), ('STI', 'Short Term Investments'),
       ('TCL', 'Total Current Liabilities'), ('STD', 'Short Term Debt'), ('DEBT', 'Total Debt'), ('LEASE', 'Capital Lease Obligations'),
       ('EQ', 'Total Stockholders Equity'), ('MINO', 'Minority Interest')]
CF = [('CAPEX', 'Capital Expenditure'), ('DA', 'Depreciation And Amortization'), ('ACQ', 'Acquisitions Net')]
NY = {'inc': 7, 'bal': 8, 'cf': 6}   # 1 ano a mais: usa o último exercício publicado (como o Python)
YOFF = {'inc': 6, 'bal': 7, 'cf': 6}   # primeiro ano = YEAR(TODAY())-YOFF
FIN_ONLY = {'EPS', 'NI', 'EQ'}       # o bloco das financeiras só precisa destes
D = {}
DATA = []
for kind, lst in (('inc', INC), ('bal', BAL), ('cf', CF)):
    for k, name in lst:
        D[k] = take(NY[kind]); DATA.append((k, name, kind))
FIRST_CALC = cur[0]
# --- contas intermediárias ---
C = {}
for k, n in (('GR', 5), ('NOP', 6), ('WC', 7), ('AST', 7), ('PAS', 7), ('RA', 6), ('RP', 6), ('ROE', 6), ('RE', 5)):
    C[k] = take(n)
for v in ('A', 'P'):
    C[f'N{v}'], C[f'MED{v}'], C[f'SIG{v}'] = take(3)
    C[f'DEV{v}'] = take(4); C[f'X{v}'] = take(6)
C['ROE_M'], C['FIN'], C['SHR'], C['SHE'] = take(4)
for k in ('E', 'T', 'J'):
    C[f'NOTA{k}'], C[f'S{k}'], C[f'F{k}'], C[f'W{k}'] = take(4)
C['JR'], C['JG'], C['JP'] = take(3)
LAST = cur[0] - 1
C = {k: ([v] if isinstance(v, str) else v) for k, v in C.items()}

CALC_HDR = {'GR': 'Crescimento do EPS', 'NOP': 'NOPAT', 'WC': 'Capital de giro', 'AST': 'Capital (ativo)', 'PAS': 'Capital (passivo)',
            'RA': 'ROIC ativo (ano)', 'RP': 'ROIC passivo (ano)', 'ROE': 'ROE (ano)', 'RE': 'Reinvestimento', 'XA': 'ROIC ativo sem outliers',
            'XP': 'ROIC passivo sem outliers', 'DEVA': 'Desvio (ativo)', 'DEVP': 'Desvio (passivo)'}


def yrs(kind, i):
    return f'YEAR(TODAY())-{YOFF[kind] - i}'


def rng(cols, r):
    return f'{cols[0]}{r}:{cols[-1]}{r}'


def metric(x, r):
    """engine.roic_metric: média(média dos 3 últimos válidos, média de todos)."""
    n = len(x); parts = []
    for i in range(n):
        rest = f'COUNT({x[i + 1]}{r}:{x[-1]}{r})' if i < n - 1 else '0'
        parts.append(f'IF(AND(ISNUMBER({x[i]}{r}),{rest}<3),{x[i]}{r},0)')
    return (f'IF(COUNT({rng(x, r)})=0,"",(({"+".join(parts)})/MIN(3,COUNT({rng(x, r)}))+AVERAGE({rng(x, r)}))/2)')


def style_of(ref):
    r = int(re.search(r'\d+', ref).group(0))
    for c in rows.get(r, etree.Element('x')).findall(q('c')):
        if c.get('r') == ref: return c.get('s')
    return None


B1, B2 = BLOCKS[0], BLOCKS[1]
both = lambda col: (f'{col}${B1[0]}:{col}${B1[1]}', f'{col}${B2[0]}:{col}${B2[1]}')


def rank_desc(col, r, tie=None):
    """posição (1 = maior) entre os dois blocos; empate: maior `tie` (ROIC), depois a linha de cima. Sem COUNTIF de texto (perde precisão)."""
    out = []
    for (a0, b0) in ((B1[0], B1[1]), (B2[0], B2[1])):
        rg = f'{col}${a0}:{col}${b0}'; x = f'{col}{r}'
        gt = f'SUMPRODUCT(ISNUMBER({rg})*({rg}>{x}))'
        if tie:
            tg = f'{tie}${a0}:{tie}${b0}'
            eq = f'SUMPRODUCT(ISNUMBER({rg})*({rg}={x})*(({tg}>{tie}{r})+({tg}={tie}{r})*(ROW({rg})<ROW())))'
        else:
            eq = f'SUMPRODUCT(ISNUMBER({rg})*({rg}={x})*(ROW({rg})<ROW()))'
        out.append(f'{gt}+{eq}')
    return '(' + '+'.join(out) + '+1)'


for bi, (a, b, h, g) in enumerate(BLOCKS):
    fin_block = bi == 1
    # cabeçalhos
    put(f'{O["ROIC ativo"]}{g}', text='Modelo (igual ao Python)', style=HDR)
    for n in OUTN: put(f'{O[n]}{h}', text=n, style=HDR)
    for k, name, kind in DATA:
        put(f'{D[k][0]}{g}', text=name, style=HDR)
        for i, colL in enumerate(D[k]): put(f'{colL}{h}', formula=yrs(kind, i), style=HDR)
        if fin_block and k not in FIN_ONLY: continue
        put(f'{D[k][0]}{a}', formula=f'IFERROR(_xldudf_WISE(B{a}:B{b},${D[k][0]}${g},{D[k][0]}${h}:{D[k][-1]}${h}),"")', style=NUM,
            array=f'{D[k][0]}{a}:{D[k][-1]}{b}')
    for k, cols in C.items():
        if k in CALC_HDR: put(f'{cols[0]}{g}', text=CALC_HDR[k], style=HDR)
        for i, colL in enumerate(cols): put(f'{colL}{h}', text=f'{k}{i}' if len(cols) > 1 else k, style=HDR)
    put(f'{O["Market Cap"]}{a}', formula=f'IFERROR(_xldudf_WISEPRICE(B{a}:B{b},"Market Cap"),"")', style=NUM, array=f'{O["Market Cap"]}{a}:{O["Market Cap"]}{b}')
    # cabeçalhos das colunas da V2 que mudam de sentido
    for colL, t in (('M', 'P/L'), ('N', 'Preço'), ('T', 'Mediana 5a'), ('AE', 'P/E justo'), ('AF', 'Múlt. const.')):
        put(f'{colL}{h}', text=t, style=style_of(f'{colL}{h}'))
    for i, colL in enumerate('PQRS'):
        put(f'{colL}{h}', formula=f'_xlfn.CONCAT("EPS ",YEAR(TODAY())-{4 - i})', style=style_of(f'{colL}{h}'))
    st = {k: style_of(f'{k}{a}') for k in ('M', 'N', 'O', 'Q', 'T', 'AE', 'AF', 'AG', 'AP', 'AQ', 'AR')}
    put(f'N{a}', formula=f'IFERROR(_xldudf_WISEPRICE(B{a}:B{b},"Price"),"")', style=st['N'], array=f'N{a}:N{b}')

    for r in range(a, b + 1):
        shr, she = f'{C["SHR"][0]}{r}', f'{C["SHE"][0]}{r}'
        put(shr, f'IF(ISNUMBER({D["OI"][-1]}{r}),1,0)', style=TXT)   # último exercício do resultado operacional já saiu?
        put(she, f'IF(ISNUMBER({D["EPS"][-1]}{r}),1,0)', style=TXT)  # idem para o EPS
        X = lambda k, i, sh=None: f'IF({sh or (she if k in ("EPS", "NI") else shr)}=1,{D[k][i + 1]}{r},{D[k][i]}{r})'
        Y = lambda k, i: f'{C[k][i]}{r}'
        # ---- crescimento (backtest.features): 5 crescimentos do EPS, mediana se >= 3 válidos; zGrowth = DP populacional / mediana
        for i in range(5):
            pv, cu = X('EPS', i), X('EPS', i + 1)
            put(Y('GR', i), f'IF(AND(ISNUMBER({pv}),ISNUMBER({cu})),IF({pv}>0,{cu}/{pv}-1,""),"")', style=PCT)
        gr = rng(C['GR'], r)
        put(f'T{r}', f'IF(COUNT({gr})>=3,MEDIAN({gr}),"")', style=st['T'])
        put(f'AP{r}', f'IF(AND(COUNT({gr})>=2,N(AO{r})<>0),_xlfn.STDEV.P({gr})/AO{r},"")', style=st['AP'])
        for i, colL in enumerate('PQRS'): put(f'{colL}{r}', f'IF(ISNUMBER({Y("GR", i + 1)}),{Y("GR", i + 1)},"")', style=st['Q'])
        # ---- ROIC triangulado (roic3.py)
        for i in range(6):   # anos de resultado: i -> balanço i+1
            pt, tx = X('PT', i), X('TX', i)
            tr = f'IF(AND(ISNUMBER({pt}),ISNUMBER({tx})),IF({pt}>0,MIN(MAX({tx}/{pt},0),0.5),0.21),0.21)'
            put(Y('NOP', i), f'IF(ISNUMBER({X("OI", i)}),({X("OI", i)}+N({X("LEASE", i + 1)})*0.05+N({X("EQI", i)}))*(1-{tr}),"")', style=NUM)
        for j in range(7):
            put(Y('WC', j), f'IF(AND(ISNUMBER({X("TCA", j)}),ISNUMBER({X("TCL", j)})),({X("TCA", j)}-N({X("CASH", j)})-N({X("STI", j)}))-({X("TCL", j)}-N({X("STD", j)})),"")', style=NUM)
            put(Y('AST', j), f'IF(AND(ISNUMBER({X("PPE", j)}),ISNUMBER({Y("WC", j)})),{X("PPE", j)}+N({X("ROU", j)})+N({X("GW", j)})+N({X("INT", j)})+N({X("LTI", j)})+{Y("WC", j)},"")', style=NUM)
            put(Y('PAS', j), f'IF(ISNUMBER({X("EQ", j)}),{X("EQ", j)}+N({X("MINO", j)})+N({X("DEBT", j)})+N({X("LEASE", j)})-N({X("CASH", j)})-N({X("STI", j)}),"")', style=NUM)
        for v, cap in (('A', 'AST'), ('P', 'PAS')):
            for i in range(6):
                c1, c0 = Y(cap, i + 1), Y(cap, i)
                cc = f'IF(ISNUMBER({c0}),({c1}+{c0})/2,{c1})'
                put(Y(f'R{v}', i), f'IF(AND(ISNUMBER({Y("NOP", i)}),ISNUMBER({c1})),IF({cc}>0,{Y("NOP", i)}/{cc},""),"")', style=PCT)
            ser = rng(C[f'R{v}'], r); nn, md, sg = Y(f'N{v}', 0), Y(f'MED{v}', 0), Y(f'SIG{v}', 0)
            put(nn, f'COUNT({ser})', style=TXT)
            put(md, f'IF({nn}>=4,MEDIAN({ser}),"")', style=PCT)
            put(sg, f'IF({nn}>=4,MAX(1.4826*MEDIAN(IF(ISNUMBER({ser}),ABS({ser}-{md}))),0.25*ABS({md}),0.02),"")', style=PCT, array=sg)
            for i in range(4):   # só os 4 anos mais antigos podem sair
                xv = Y(f'R{v}', i)
                put(Y(f'DEV{v}', i), f'IF(AND({nn}>=4,ISNUMBER({xv})),IF(ABS({xv}-{md})>3*{sg},ABS({xv}-{md}),-1),-1)', style=TXT)
            for i in range(6):
                xv = Y(f'R{v}', i)
                if i >= 4:
                    put(Y(f'X{v}', i), f'IF(ISNUMBER({xv}),{xv},"")', style=PCT); continue
                di = Y(f'DEV{v}', i)
                ahead = '+'.join(f'({Y(f"DEV{v}", j)}>{di})' if j > i else f'({Y(f"DEV{v}", j)}>={di})' for j in range(4) if j != i)
                put(Y(f'X{v}', i), f'IF(NOT(ISNUMBER({xv})),"",IF({di}<0,{xv},IF(1+{ahead}<={nn}-3,"",{xv})))', style=PCT)
        A_, P_, M_ = f'{O["ROIC ativo"]}{r}', f'{O["ROIC passivo"]}{r}', f'{O["ROIC marginal"]}{r}'
        put(A_, metric(C['XA'], r), style=PCT)
        put(P_, metric(C['XP'], r), style=PCT)
        for i in range(5):   # anos last-5..last-1
            put(Y('RE', i), (f'IF(AND(ISNUMBER({X("CAPEX", i)}),ISNUMBER({X("DA", i)}),ISNUMBER({Y("WC", i + 1)}),ISNUMBER({Y("WC", i)})),'
                             f'ABS({X("CAPEX", i)})-{X("DA", i)}-N({X("ACQ", i)})+{Y("WC", i + 1)}-{Y("WC", i)},"")'), style=NUM)
        re_ = rng(C['RE'], r)
        put(M_, (f'IF(AND(COUNT({re_})>=3,ISNUMBER({Y("NOP", 5)}),ISNUMBER({Y("NOP", 0)})),IF(AVERAGE({re_})>0,'
                 f'({Y("NOP", 5)}-{Y("NOP", 0)})/(5*AVERAGE({re_})),""),"")'), style=PCT)
        va, vp, vm = (f'AND(ISNUMBER({x}),N({x})>=0,N({x})<=2)' for x in (A_, P_, M_))
        ca, cp = f'MIN(N({A_}),1.5)', f'MIN(N({P_}),1.5)'
        put(f'{O["ROIC triangulado"]}{r}', (f'IF(AND({va},{vp}),IF(AND(MIN({ca},{cp})>0,MAX({ca},{cp})<=2*MIN({ca},{cp})),({ca}+{cp})/2,'
                                           f'IF({vm},IF(ABS({ca}-{M_})<=ABS({cp}-{M_}),{ca},{cp}),MIN({ca},{cp}))),'
                                           f'IF({va},{ca},IF({vp},{cp},IF(OR(N({A_})>2,N({P_})>2),1.5,IF({vm},MIN(N({M_}),1.5),"")))))'), style=PCT)
        # ---- financeiras e seguradoras de saúde: ROE (lucro ÷ patrimônio do fim do ano), mesma média
        for i in range(6):
            put(Y('ROE', i), f'IF(AND(ISNUMBER({X("NI", i)}),N({X("EQ", i + 1, she)})>0),{X("NI", i)}/{X("EQ", i + 1, she)},"")', style=PCT)
        put(Y('ROE_M', 0), metric(C['ROE'], r), style=PCT)
        fin = Y('FIN', 0)
        put(fin, f'IF(OR(F{r}="Financial Services",COUNTIF({HLR},B{r})>0),1,0)', style=TXT)
        tri, U_ = f'{O["ROIC triangulado"]}{r}', f'{O["ROIC (usado)"]}{r}'
        nodata = f'AND(COUNT({rng(D["OI"], r)})=0,COUNT({rng(D["NI"], r)})=0)'   # Wisesheets não devolveu nada: usa o ROIC da V2
        put(U_, f'IFERROR(IF({nodata},AB{r},IF({fin}=1,{Y("ROE_M", 0)},{tri})),"")', style=PCT)
        # ---- valuation (validation_portfolios.classify): P/L, P/E justo, retorno esperado
        put(f'M{r}', f'IF(AND(ISNUMBER(N{r}),ISNUMBER({X("EPS", 5)})),IF({X("EPS", 5)}<>0,N{r}/{X("EPS", 5)},""),"")', style=st['M'])
        put(f'AQ{r}', f'{U_}', style=st['AQ'])
        put(f'AR{r}', '0', style=st['AR'])   # sem zROIC (regra nova)
        put(f'O{r}', f'IFERROR(IF(N(AQ{r})>0,(1-U{r}/MIN(1,AQ{r}))/(8.5%-U{r}),""),"")', style=st['O'])
        dy = f'(N(AC{r})+N(AD{r}))/2'
        put(f'AE{r}', f'IFERROR(IF(O{r}*(1+AO{r})^2/M{r}>0,SQRT(O{r}*(1+AO{r})^2/M{r})-1+{dy},""),"")', style=st['AE'])
        put(f'AF{r}', f'IF(ISNUMBER(AO{r}),AO{r}+{dy},"")', style=st['AF'])
        put(f'AG{r}', f'IF(AND(ISNUMBER(AE{r}),ISNUMBER(AF{r})),(AE{r}+AF{r})/2,IF(ISNUMBER(AO{r}),AO{r},""))', style=st['AG'])
        # ---- exclusões e classes (benchmarks.classify_new / holdings_new)
        cyc, app = f'{O["Cíclica"]}{r}', f'{O["Vestuário"]}{r}'
        put(cyc, f'IF(COUNTIF({CYCR},G{r})>0,"✓","")', style=TXT)
        put(app, f'IF(COUNTIF({APPR},G{r})>0,"✓","")', style=TXT)
        edit_formula(f'AM{r}', lambda t: (f'IF(OR(NOT(ISNUMBER(AO{r})),NOT(ISNUMBER(AP{r})),NOT(ISNUMBER(AQ{r})),NOT(ISNUMBER(AS{r}))),"Sem dados",'
                                          f'IF(OR(({t})="Opportunity of Lifetime",({t})="Good Companies, Great Returns"),'
                                          f'IF({cyc}="✓","Cyclicals",IF({app}="✓","Excluída (vestuário)",{t})),{t}))'))
        allm = f'ISNUMBER(AO{r}),ISNUMBER(AP{r}),ISNUMBER(AQ{r}),ISNUMBER(AG{r})'
        ql = f'{O["Qualidade"]}{r}'
        dup = f'COUNTIF($B${B2[0]}:$B${B2[1]},B{r})=0' if not fin_block else 'TRUE'   # ação repetida nos dois blocos conta uma vez só
        put(ql, f'IF(AND({dup},{cyc}="",{app}="",{allm},N(AQ{r})>=12%,N(AO{r})>=15%),"✓","")', style=TXT)
        put(f'{O["High ROIC"]}{r}', f'IF(AND(AM{r}="Opportunity of Lifetime",N(AQ{r})>30%),"✓","")', style=TXT)
        put(f'{O["High Growth"]}{r}', f'IF(AND(AM{r}="Opportunity of Lifetime",N(AO{r})>30%),"✓","")', style=TXT)
        put(f'{O["Excepcional"]}{r}', f'IF(AND({ql}="✓",N(AQ{r})>30%,N(AO{r})>30%),"✓","")', style=TXT)
        # notas de ordenação (desempate pelo ROIC, como no Python)
        put(Y('NOTAE', 0), f'IF({ql}="✓",MIN(AQ{r}/0.3,AO{r}/0.3),"")', style=TXT)
        put(Y('NOTAT', 0), f'IF(AND({ql}="✓",N(M{r})>=4),AG{r},"")', style=TXT)
        # JG+G (Fórmula Mágica com crescimento): não financeiras, sem utilities, sem excluídas, P/L > 0, EBIT > 0
        el = f'AND({fin}=0,F{r}<>"Utilities",{cyc}="",{app}="",N(M{r})>0,ISNUMBER(AQ{r}),ISNUMBER(AO{r}),N({X("OI", 5)})>0)'
        put(Y('JR', 0), f'IF({el},AQ{r},"")', style=TXT); put(Y('JG', 0), f'IF({el},AO{r},"")', style=TXT); put(Y('JP', 0), f'IF({el},M{r},"")', style=TXT)
        if not fin_block:
            jr, jg, jp = (f'{C[k][0]}${B1[0]}:{C[k][0]}${B1[1]}' for k in ('JR', 'JG', 'JP'))
            put(Y('NOTAJ', 0), (f'IF(ISNUMBER({Y("JR", 0)}),-(_xlfn.RANK.AVG({Y("JR", 0)},{jr},0)+_xlfn.RANK.AVG({Y("JG", 0)},{jg},0)'
                                f'+_xlfn.RANK.AVG({Y("JP", 0)},{jp},1)),"")'), style=TXT)
        else:
            put(Y('NOTAJ', 0), '""', style=TXT)
        for k, outr, outw in (('E', 'Especiais', 'Peso Esp.'), ('T', 'Top 20', 'Peso Top 20'), ('J', 'JG+G', 'Peso JG+G')):
            nt = C[f'NOTA{k}'][0]; rk = f'{O[outr]}{r}'
            rd = rank_desc(nt, r, None if k == 'J' else 'AQ')
            put(rk, f'IF(ISNUMBER({nt}{r}),IF({rd}<=20,{rd},""),"")', style=TXT)
            # pesos: raiz do valor de mercado com teto de 10% (top_n.cap, solução fechada do "water-filling")
            s_, f_, w_ = C[f'S{k}'][0], C[f'F{k}'][0], C[f'W{k}'][0]
            sa, sb = both(s_); fa, fb = both(f_); wa, wb = both(w_)
            mc = f'{O["Market Cap"]}{r}'
            put(f'{s_}{r}', f'IF(ISNUMBER({rk}),SQRT(MAX(N({mc}),1)),"")', style=TXT)
            tot = f'(SUM({sa})+SUM({sb}))'
            bigger = f'(SUMPRODUCT(ISNUMBER({sa})*({sa}>{s_}{r}),{sa})+SUMPRODUCT(ISNUMBER({sb})*({sb}>{s_}{r}),{sb}))'
            kk = f'(SUMPRODUCT(ISNUMBER({sa})*({sa}>{s_}{r}))+SUMPRODUCT(ISNUMBER({sb})*({sb}>{s_}{r})))'
            put(f'{f_}{r}', f'IF(ISNUMBER({s_}{r}),IF({tot}-{bigger}>0,(1-{kk}*10%)*{s_}{r}/({tot}-{bigger})>10%+1E-12,TRUE),"")', style=TXT)
            m_ = f'(COUNTIF({fa},TRUE)+COUNTIF({fb},TRUE))'
            sf = f'(SUMIF({fa},TRUE,{sa})+SUMIF({fb},TRUE,{sb}))'
            put(f'{w_}{r}', f'IF(ISNUMBER({s_}{r}),IF({f_}{r},10%,(1-{m_}*10%)*{s_}{r}/({tot}-{sf})),"")', style=TXT)
            put(f'{O[outw]}{r}', f'IF(ISNUMBER({w_}{r}),{w_}{r}/(SUM({wa})+SUM({wb})),"")', style=PCT)
    # Fórmula Mágica da V2 (Joel e JS) passa a usar o ROIC do modelo
    for r in range(a, b + 1):
        for colL in ('AH', 'AI'):
            edit_formula(f'{colL}{r}', lambda t: re.sub(r'(\$?)AB(\$?\d+)', lambda m: f'{m.group(1)}{O["ROIC (usado)"]}{m.group(2)}', t))

# cabeçalhos da aba Portfolio (espelha a Formula com 1 coluna de deslocamento)
s2 = 'xl/worksheets/sheet2.xml'; t2 = files[s2].decode()
for pc, fc in (('N', 'M'), ('O', 'N'), ('Q', 'P'), ('R', 'Q'), ('S', 'R'), ('T', 'S'), ('AE', 'AE'), ('AF', 'AF')):
    t2, n = re.subn(rf'<c r="{pc}5"( s="\d+")?[^>]*?(/>|>.*?</c>)', lambda m: f'<c r="{pc}5"{m.group(1) or ""} t="str"><f>Formula!{fc}$5</f></c>', t2, count=1, flags=re.S)
    assert n == 1, pc
files[s2] = t2.encode()

# larguras e agrupamento: dados e contas ficam recolhidos (o que importa são as saídas)
cols = root.find(q('cols'))
for n in range(col_idx('BC'), LAST + 1):
    c = etree.SubElement(cols, q('col')); c.set('min', str(n)); c.set('max', str(n)); c.set('width', '11'); c.set('customWidth', '1')
    if n >= FIRST_DATA: c.set('outlineLevel', '1'); c.set('hidden', '1')
dim = root.find(q('dimension'))
if dim is not None: dim.set('ref', f'A1:{L(LAST)}{max(rows)}')
for rw in rows.values():
    if 'spans' in rw.attrib: del rw.attrib['spans']   # dica de colunas da V2 ficou curta
files[sheet] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
# 4) recalcular tudo ao abrir; tirar o calcChain antigo
files.pop('xl/calcChain.xml', None)
files['[Content_Types].xml'] = re.sub(rb'<Override[^>]*calcChain[^>]*/>', b'', files['[Content_Types].xml'])
files['xl/_rels/workbook.xml.rels'] = re.sub(rb'<Relationship[^>]*calcChain[^>]*/>', b'', files['xl/_rels/workbook.xml.rels'])
files['xl/workbook.xml'] = re.sub(rb'<calcPr[^>]*/>', b'<calcPr calcId="191029" fullCalcOnLoad="1"/>', files['xl/workbook.xml'])
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in files.items(): zo.writestr(n, d)
json_cols = {'O': O, 'D': D, 'C': C}
import json; open(OUT + '.cols.json', 'w').write(json.dumps(json_cols))
print('ok', OUT, 'colunas até', L(LAST))
