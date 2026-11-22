"""Teste mecânico da V3 com consenso: dados da SEC na aba Dados (consenso sintético = EPS × (1+g)^n, g de 10% a 59% por ticker), recalcula no LibreOffice e confere.
Uso: python3 planilha/teste_v3consenso.py <v3.xlsx> <pasta>"""
import sys, json, subprocess, pathlib, collections
import numpy as np, openpyxl
SRC, TMP = sys.argv[1], pathlib.Path(sys.argv[2]); TMP.mkdir(exist_ok=True)
cols = json.load(open(SRC + '.cols.json')); DC, CC, R0, R1 = cols['DC'], cols['CC'], cols['R0'], cols['R1']
T = json.load(open('planilha/teste.json'))['data']
MAP = {'EPS': 'eps', 'NI': 'ni', 'OI': 'opinc', 'PT': 'pretax', 'TX': 'tax', 'PPE': 'ppe', 'GW': 'gw', 'INT': 'intang', 'TCA': 'tca', 'CASH': 'cash',
       'TCL': 'tcl', 'DEBT': 'debt', 'EQ': 'eq', 'ROU': 'rou', 'LEASE': 'lease'}
wb = openpyxl.load_workbook(SRC); ws = wb['Dados']; wa = wb['Ações']
for r in range(R0, R1 + 1):
    tk = wa[f'A{r}'].value; v = T.get(tk)
    for k, cl in DC.items():
        for c in cl: ws[f'{c}{r}'].value = None
    if not v: continue
    b = DC['base']
    for c, val in zip(b, (v['nome'], v['setor'], v['ind'], v['preco'], v['mcap'])): ws[f'{c}{r}'] = val
    ws[f'{DC["DY"][0]}{r}'] = v['dy']
    for k, src in MAP.items():
        for i, c in enumerate(DC[k]): ws[f'{c}{r}'] = v.get(f'{src}{3 - i}')
    e0 = v.get('eps0')
    gi = 0.10 + (sum(map(ord, tk)) % 50) / 100   # crescimento sintético de 10% a 59%
    for j, c in enumerate(DC['EST']): ws[f'{c}{r}'] = e0 * (1 + gi) ** (j + 1) if e0 else None
wb.save(TMP / 'in.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(TMP / 'out'), str(TMP / 'in.xlsx')], check=True, capture_output=True, timeout=1500)
o = openpyxl.load_workbook(TMP / 'out' / 'in.xlsx', data_only=True)
err = collections.Counter()
for sh in o.sheetnames:
    for row in o[sh].iter_rows():
        for x in row:
            if isinstance(x.value, str) and x.value.startswith('#') and x.value not in ('#',): err[(sh, x.column_letter)] += 1
print('erros:', err.most_common(10))
c = o['Cálculo']; a = o['Ações']
num = lambda x: x if isinstance(x, (int, float)) and not isinstance(x, bool) else None
chk = []
for r in range(R0, R1 + 1):
    tk = a[f'A{r}'].value
    if tk not in T: continue
    g = num(c[f'{CC["G"]}{r}'].value); graw = num(c[f'{CC["GRAW"]}{r}'].value)
    if g is not None: assert g <= 1.0 + 1e-9
    chk.append((tk, graw, g, num(c[f'{CC["PL"]}{r}'].value), num(c[f'{CC["PLL"]}{r}'].value), num(c[f'{CC["PLF"]}{r}'].value), c[f'{CC["SEC"]}{r}'].value,
                num(c[f'{CC["RKT"]}{r}'].value), num(c[f'{CC["WT"]}{r}'].value)))
print('amostra (ticker, G sem teto, G, P/L, P/L LTM, P/L fwd):', [x[:6] for x in chk[:3]])
top = [x for x in chk if x[7] is not None]
print('Top 20:', len(top), 'por setor:', collections.Counter(x[6] for x in top).most_common(4), 'soma pesos:', round(sum(x[8] for x in top), 6))
p = o['Painel']; print('Painel Top 20:', [p.cell(r, 3).value for r in range(9, 14)], 'Bagger:', [p.cell(r, 8).value for r in range(9, 14)])
