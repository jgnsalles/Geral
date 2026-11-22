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
# opcional (--sec-eps): preenche anos de EPS vazios (2017–2021) com o 10-K da SEC, na escala do Wisesheets (fator = Wise ÷ SEC no 1º ano comum,
# corrige desdobramentos). Só para validar aqui; no Excel o Wisesheets preenche esses anos sozinho.
if '--sec-eps' in sys.argv:
    import gzip
    PIT = pathlib.Path(__file__).parent.parent / 'backtest' / 'data' / 'pit'
    ecols = {v: c for (k, v), c in yn.items() if k == 'EPS Diluted' and isinstance(v, int)}
    nfill = 0; print('anos EPS', sorted(ecols))
    for r in range(5, d.max_row + 1):
        t = a[f'A{r}'].value; f = PIT / f'{t}.json.gz'
        if not t or not f.exists(): continue
        try: rows = [x for cc in json.load(gzip.open(f))['eps_diluted'] if 'shares' in cc.get('unit', '') for x in cc['rows']]
        except Exception: continue
        sec = {}
        for end, v, filed in sorted(rows, key=lambda x: x[2]): sec[int(end[:4])] = v
        have = {y: d.cell(r, c).value for y, c in ecols.items() if isinstance(d.cell(r, c).value, (int, float))}
        comm = [y for y in sorted(have) if sec.get(y) not in (None, 0)]
        if not comm: continue
        fac = have[comm[0]] / sec[comm[0]]
        if not (0.01 <= abs(fac) <= 100): continue
        for y, c in ecols.items():
            if y not in have and y in sec: d.cell(r, c).value = round(sec[y] * fac, 4); nfill += 1
    print('EPS preenchidos pela SEC:', nfill)
    # variação de 12 meses (coluna '1y' do Wisesheets), se vier vazia: preços ajustados do backtest
    import pandas as pd
    px = pd.read_csv(pathlib.Path(__file__).parent.parent / 'backtest' / 'data' / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    c1y = [c for (k, v), c in yn.items() if v == '1y']
    if c1y:
        last = px.index[-1]; i0 = px.index.searchsorted(last - pd.Timedelta(days=365)); n1 = 0
        for r in range(5, d.max_row + 1):
            t = a[f'A{r}'].value
            if t in px and d.cell(r, c1y[0]).value in (None, '') and pd.notna(px[t].iloc[-1]) and pd.notna(px[t].iloc[i0]):
                d.cell(r, c1y[0]).value = float(px[t].iloc[-1] / px[t].iloc[i0] - 1); n1 += 1
        print('1y preenchidos pelos preços:', n1, 'até', last.date())
for r in range(5, 11): wb['Regras'].cell(r, 18).value = src['Regras'].cell(r, 18).value   # câmbio do Wisesheets
wb.save(OUT / 'in.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(OUT / 'out'), str(OUT / 'in.xlsx')],
               check=True, capture_output=True, timeout=1500)
print('ok', OUT / 'out' / 'in.xlsx')
