"""Teste: preenche a V3 com os mesmos dados (SEC) que o Python usa, recalcula no LibreOffice e compara com o Python.
Uso: python3 planilha/teste_igualdade.py <v3.xlsx> <pasta_tmp>"""
import sys, json, subprocess, pathlib
import openpyxl
SRC, TMP = sys.argv[1], pathlib.Path(sys.argv[2]); TMP.mkdir(exist_ok=True)
cols = json.load(open(SRC + '.cols.json')); O, D = cols['O'], cols['D']
T = json.load(open('planilha/teste.json'))['data']
MAP = {'EPS': 'eps', 'NI': 'ni', 'OI': 'opinc', 'PT': 'pretax', 'TX': 'tax', 'EQI': 'eqi', 'PPE': 'ppe', 'ROU': 'rou', 'GW': 'gw', 'INT': 'intang',
       'LTI': 'ltinv', 'TCA': 'tca', 'CASH': 'cash', 'STI': 'stinv', 'TCL': 'tcl', 'STD': 'std', 'DEBT': 'debt', 'LEASE': 'lease', 'EQ': 'eq',
       'MINO': 'mino', 'CAPEX': 'capex', 'DA': 'da', 'ACQ': 'acq'}
KIND = {k: ('bal' if len(v) == 8 else 'cf' if len(v) == 6 else 'inc') for k, v in D.items()}
wb = openpyxl.load_workbook(SRC); ws = wb['Formula']
for a, b in ((6, 206), (211, 233)):
    for r in range(a, b + 1):
        tk = ws[f'B{r}'].value; v = T.get(tk)
        for colL in 'EFGHIJKL': ws[f'{colL}{r}'].value = None
        for k, cl in D.items():
            for c in cl: ws[f'{c}{r}'].value = None
        ws[f'N{r}'].value = None; ws[f'{O["Market Cap"]}{r}'].value = None
        if not v: continue
        ws[f'E{r}'].value, ws[f'F{r}'].value, ws[f'G{r}'].value = v['nome'], v['setor'], v['ind']
        ws[f'N{r}'].value = v['preco']; ws[f'{O["Market Cap"]}{r}'].value = v['mcap']
        ws[f'AC{r}'].value = ws[f'AD{r}'].value = v['dy']
        for k, cl in D.items():
            n = len(cl)
            for i, c in enumerate(cl):
                kk = {'inc': 5 - i, 'bal': 6 - i, 'cf': 5 - i}[KIND[k]]
                ws[f'{c}{r}'].value = v.get(f'{MAP[k]}{kk}')
wb.save(TMP / 'in.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(TMP / 'out'), str(TMP / 'in.xlsx')], check=True,
               capture_output=True, timeout=900)
print('ok')
