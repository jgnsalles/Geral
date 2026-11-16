"""Price Tracker v3 = a própria V2 (mesmas abas, fórmulas, gráficos e chamadas ao Wisesheets) + um bloco pequeno de colunas novas na aba
Formula: ROIC triangulado enxuto (último ano, 10 campos numa chamada por bloco), filtro de cíclicas/vestuário, High ROIC, High Growth,
Especiais, Top 20 com peso. Cortes novos: ROIC 12%, zROIC desligado. Edita o XML direto (não passa pelo openpyxl, para não perder nada).
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

# 2) colunas novas: BC.. (ROIC triangulado enxuto + listas)
C0 = col_idx('BC'); RAW = [L(C0 + i) for i in range(len(FIELDS))]  # BC..BL
NEW = ['NOPAT', 'Capital (ativo)', 'Capital (passivo)', 'ROIC ativo', 'ROIC passivo', 'ROIC triangulado', 'ROIC (usado)', 'Market Cap',
       'Cíclica', 'High ROIC', 'High Growth', 'Nota Esp.', 'Especiais', 'Nota Top', 'Top 20', '√ MC', 'Peso bruto', 'Peso']
NC = {n: L(C0 + len(FIELDS) + i) for i, n in enumerate(NEW)}
PCT, TXT, HDR, NUM = 29, 7, 3, 32
rng = lambda colL: f'{colL}$6:{colL}$206', lambda colL: f'{colL}$211:{colL}$233'
for a, b, h, g in BLOCKS:
    put(f'{RAW[0]}{g}', text='ROIC triangulado (último ano)', style=HDR); put(f'{NC["ROIC (usado)"]}{g}', text='v3', style=HDR)
    for i, fld in enumerate(FIELDS): put(f'{RAW[i]}{h}', text=fld, style=HDR)
    for n in NEW: put(f'{NC[n]}{h}', text=n, style=HDR)
    put(f'{RAW[0]}{a}', formula=f'IFERROR(_xldudf_WISE(B{a}:B{b},{RAW[0]}{h}:{RAW[-1]}{h},YEAR(TODAY())-1),"")', style=TXT, array=f'{RAW[0]}{a}:{RAW[-1]}{b}')
    put(f'{NC["Market Cap"]}{a}', formula=f'IFERROR(_xldudf_WISEPRICE(B{a}:B{b},"Market Cap"),"")', style=TXT, array=f'{NC["Market Cap"]}{a}:{NC["Market Cap"]}{b}')
    oi, pt, tx, ppe, gwi, tca, tcl, cash, debt, eq = RAW
    for r in range(a, b + 1):
        N_ = {k: f'{v}{r}' for k, v in NC.items()}
        put(N_['NOPAT'], f'IFERROR({oi}{r}*(1-IF(N({pt}{r})>0,MIN(MAX({tx}{r}/{pt}{r},0),0.5),0.21)),"")', style=NUM)
        put(N_['Capital (ativo)'], f'IFERROR(IF(AND(ISNUMBER({ppe}{r}),ISNUMBER({tca}{r}),ISNUMBER({tcl}{r})),{ppe}{r}+N({gwi}{r})+{tca}{r}-N({cash}{r})-{tcl}{r},""),"")', style=NUM)
        put(N_['Capital (passivo)'], f'IFERROR(IF(ISNUMBER({eq}{r}),{eq}{r}+N({debt}{r})-N({cash}{r}),""),"")', style=NUM)
        A_, P_ = N_['ROIC ativo'], N_['ROIC passivo']
        put(A_, f'IF(AND(ISNUMBER({N_["NOPAT"]}),N({N_["Capital (ativo)"]})>0),{N_["NOPAT"]}/{N_["Capital (ativo)"]},"")', style=PCT)
        put(P_, f'IF(AND(ISNUMBER({N_["NOPAT"]}),N({N_["Capital (passivo)"]})>0),{N_["NOPAT"]}/{N_["Capital (passivo)"]},"")', style=PCT)
        va, vp = f'AND(ISNUMBER({A_}),N({A_})>=0,N({A_})<=2)', f'AND(ISNUMBER({P_}),N({P_})>=0,N({P_})<=2)'
        ca, cp = f'MIN(N({A_}),1.5)', f'MIN(N({P_}),1.5)'
        put(N_['ROIC triangulado'], (f'IF(AND({va},{vp}),IF(AND(MIN({ca},{cp})>0,MAX({ca},{cp})<=2*MIN({ca},{cp})),AVERAGE({ca},{cp}),MIN({ca},{cp})),'
                                     f'IF({va},{ca},IF({vp},{cp},IF(OR(N({A_})>2,N({P_})>2),1.5,""))))'), style=PCT)
        put(N_['ROIC (usado)'], f'IF(F{r}="Financial Services",AB{r},IF(ISNUMBER({N_["ROIC triangulado"]}),{N_["ROIC triangulado"]},AB{r}))', style=PCT)
        put(N_['Cíclica'], f'IF(OR(COUNTIF({CYCR},G{r})>0,COUNTIF({APPR},G{r})>0),"✓","")', style=TXT)
        RS = N_['ROIC (usado)']
        put(N_['High ROIC'], f'IF(AND(AM{r}="Opportunity of Lifetime",N({RS})>30%),"✓","")', style=TXT)
        put(N_['High Growth'], f'IF(AND(AM{r}="Opportunity of Lifetime",N(AO{r})>30%),"✓","")', style=TXT)
        ql = f'AND(N({RS})>=12%,N(AO{r})>=15%,{N_["Cíclica"]}="")'
        put(N_['Nota Esp.'], f'IF({ql},MIN(N({RS})/30%,N(AO{r})/30%)+ROW()*1E-9,"")', style=TXT)
        for sc, rk in (('Nota Esp.', 'Especiais'), ('Nota Top', 'Top 20')):
            cl = NC[sc]
            cnt = f'COUNTIF({cl}$6:{cl}$206,">"&{cl}{r})+COUNTIF({cl}$211:{cl}$233,">"&{cl}{r})+1'
            if sc == 'Nota Top':
                put(N_['Nota Top'], f'IF(AND({ql},N(M{r})>=4,ISNUMBER(AG{r})),AG{r}+ROW()*1E-9,"")', style=TXT)
            put(N_[rk], f'IF(ISNUMBER({cl}{r}),IF({cnt}<=20,{cnt},""),"")', style=TXT)
        sq, w0 = NC['√ MC'], NC['Peso bruto']
        put(N_['√ MC'], f'IF(ISNUMBER({N_["Top 20"]}),SQRT(MAX(N({N_["Market Cap"]}),1)),"")', style=TXT)
        put(N_['Peso bruto'], f'IF(ISNUMBER({N_["Top 20"]}),MIN(10%,{sq}{r}/(SUM({sq}$6:{sq}$206)+SUM({sq}$211:{sq}$233))),"")', style=PCT)
        put(N_['Peso'], f'IF(ISNUMBER({N_["Top 20"]}),{w0}{r}/(SUM({w0}$6:{w0}$206)+SUM({w0}$211:{w0}$233)),"")', style=PCT)
        # 3) ligar o ROIC novo ao que já existia (classe, P/E justo, fórmula mágica) e a classe Cyclicals
        edit_formula(f'AQ{r}', lambda t, r=r: re.sub(r'\bAB(\d+)\b', lambda m: f'{RS}', t))
        edit_formula(f'O{r}', lambda t, r=r: t.replace(f'AVERAGE(AB{r})', f'MIN(1,{RS})'))
        edit_formula(f'AM{r}', lambda t, r=r: f'IF(AND({NC["Cíclica"]}{r}="✓",OR(({t})="Opportunity of Lifetime",({t})="Good Companies, Great Returns")),"Cyclicals",{t})')
    # fórmula mágica (Joel e JS) passa a usar o ROIC novo: as fórmulas são compartilhadas, basta trocar a mestre
    for r in range(a, b + 1):
        for colL in ('AH', 'AI'):
            edit_formula(f'{colL}{r}', lambda t: re.sub(r'(\$?)AB(\$?\d+)', lambda m: f'{m.group(1)}{NC["ROIC (usado)"]}{m.group(2)}', t))
# larguras
cols = root.find(q('cols'))
for i in range(len(FIELDS) + len(NEW)):
    c = etree.SubElement(cols, q('col')); n = C0 + i; c.set('min', str(n)); c.set('max', str(n)); c.set('width', '11'); c.set('customWidth', '1')
files[sheet] = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
# 4) recalcular tudo ao abrir; tirar o calcChain antigo
files.pop('xl/calcChain.xml', None)
files['[Content_Types].xml'] = re.sub(rb'<Override[^>]*calcChain[^>]*/>', b'', files['[Content_Types].xml'])
files['xl/_rels/workbook.xml.rels'] = re.sub(rb'<Relationship[^>]*calcChain[^>]*/>', b'', files['xl/_rels/workbook.xml.rels'])
files['xl/workbook.xml'] = re.sub(rb'<calcPr[^>]*/>', b'<calcPr calcId="191029" fullCalcOnLoad="1"/>', files['xl/workbook.xml'])
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in files.items(): zo.writestr(n, d)
print('ok', OUT)
