"""Copia os dados do Wisesheets de uma planilha salva pelo usuário para a V3 gerada (casando bloco e ano), recalcula no LibreOffice.
Uso: python3 planilha/injeta_dados.py <planilha_do_usuario.xlsx> <v3_gerada.xlsx> <pasta_saida>  -> <pasta>/out/in.xlsx"""
import sys, re, json, subprocess, pathlib
import openpyxl

SRC, NEW, OUT = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
Y = 2026


def years(ws, formulas):
    out, cur = {}, None
    for c in range(2, ws.max_column + 1):
        h = ws.cell(3, c).value
        if h: cur = h
        v = ws.cell(4, c).value
        if formulas and isinstance(v, str) and v.startswith('=YEAR'):
            m = re.search(r'([+-]\d+)\s*$', v.replace('=YEAR(TODAY())', ''))
            v = Y + int(m.group(1)) if m else Y
        if cur: out[(cur, v)] = c
    return out


src = openpyxl.load_workbook(SRC, data_only=True); sd = src['Dados']
row_of = {sd[f'A{r}'].value: r for r in range(5, sd.max_row + 1) if sd[f'A{r}'].value}
wb = openpyxl.load_workbook(NEW); d = wb['Dados']; a = wb['Ações']
yn, yo = years(d, True), years(sd, False)
for key, c in yn.items():
    co = yo.get(key)
    for r in range(5, d.max_row + 1):
        sr = row_of.get(a[f'A{r}'].value)
        d.cell(r, c).value = sd.cell(sr, co).value if (sr and co) else None
for r in range(5, 11): wb['Regras'].cell(r, 18).value = src['Regras'].cell(r, 18).value   # câmbio do Wisesheets
wb.save(OUT / 'in.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(OUT / 'out'), str(OUT / 'in.xlsx')],
               check=True, capture_output=True, timeout=1500)
print('ok', OUT / 'out' / 'in.xlsx')
