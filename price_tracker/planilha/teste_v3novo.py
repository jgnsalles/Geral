"""Teste da V3 nova: coloca os dados da SEC (os mesmos do Python) na aba Dados, recalcula no LibreOffice e compara com o Python.
Uso: python3 planilha/teste_v3novo.py <v3.xlsx> <pasta>"""
import sys, json, subprocess, pathlib
import numpy as np, pandas as pd, openpyxl
sys.path[:0] = ['backtest', '.']
SRC, TMP = sys.argv[1], pathlib.Path(sys.argv[2]); TMP.mkdir(exist_ok=True)
cols = json.load(open(SRC + '.cols.json')); DC, CC, R0, R1 = cols['DC'], cols['CC'], cols['R0'], cols['R1']
T = json.load(open('planilha/teste.json'))['data']
MAP = {'EPS': 'eps', 'NI': 'ni', 'OI': 'opinc', 'PT': 'pretax', 'TX': 'tax', 'PPE': 'ppe', 'GW': 'gw', 'INT': 'intang', 'TCA': 'tca', 'CASH': 'cash',
       'STI': 'stinv', 'TCL': 'tcl', 'STD': 'std', 'DEBT': 'debt', 'EQ': 'eq', 'ROU': 'rou', 'LTI': 'ltinv', 'LEASE': 'lease'}
wb = openpyxl.load_workbook(SRC); ws = wb['Dados']; wa = wb['Ações']
for r in range(R0, R1 + 1):
    tk = wa[f'A{r}'].value; v = T.get(tk)
    for k, cl in DC.items():
        for c in cl: ws[f'{c}{r}'].value = None
    if not v: continue
    b = DC['base']; ws[f'{b[0]}{r}'], ws[f'{b[1]}{r}'], ws[f'{b[2]}{r}'], ws[f'{b[3]}{r}'], ws[f'{b[4]}{r}'] = v['nome'], v['setor'], v['ind'], v['preco'], v['mcap']
    ws[f'{DC["DY"][0]}{r}'] = ws[f'{DC["DY"][1]}{r}'] = v['dy']
    for k, src in MAP.items():
        cl = DC[k]; n = len(cl)
        for i, c in enumerate(cl): ws[f'{c}{r}'] = v.get(f'{src}{n - 2 - i}')
wb.save(TMP / 'in.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(TMP / 'out'), str(TMP / 'in.xlsx')], check=True, capture_output=True, timeout=900)
print('recalculado')
