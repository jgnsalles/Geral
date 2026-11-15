"""Gera Price_Tracker_v3.xlsx: Opportunity of Lifetime reconstruido com o que aprendemos (ROIC triangulado, classes novas, cortes
testados, High ROIC/High Growth, Especiais, Formula Magica JG e JG + G, filtro de ciclicos e vestuario). Dados via Wisesheets
(=WISE(ticker, campo, ano) e =WISEPRICE(ticker, campo)), como na V2. Uso: python3 planilha/build_v3.py [--teste valores.json]"""
import sys, json, pathlib
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.formatting.rule import FormulaRule, CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula
import zipfile, shutil, re

HERE = pathlib.Path(__file__).parent
API = json.load(open(HERE / 'wise_dados.json'))  # dados da API do Wisesheets (planilha/wise_api.py)
TEST = None
OUT = HERE / 'Price_Tracker_v3.xlsx'
TICKERS = API['tickers']
import datetime as _dt
ATUALIZADO = _dt.date.today().strftime('%d/%m/%Y')
CODES = json.load(open(HERE / 'codes.json'))
R0, NROWS = 6, 400
R1 = R0 + NROWS - 1

F = 'Arial'
fnt = lambda **k: Font(name=F, size=k.pop('size', 10), **k)
INK, BLUE, WHITE, GREY = '262A33', '0000FF', 'FFFFFF', '66605C'
HEAD = PatternFill('solid', fgColor='262A33'); SUB = PatternFill('solid', fgColor='E9E4DF'); INP = PatternFill('solid', fgColor='FFF2CC')
thin = Side(style='thin', color='D9D2CC'); BOT = Border(bottom=thin)
PCT, PCT0, NUM1, NUM0, MULT = '0.0%;-0.0%;-', '0%;-0%;-', '#,##0.0;-#,##0.0;-', '#,##0;-#,##0;-', '0.0x;-0.0x;-'

wb = Workbook()
P = wb.active; P.title = 'Painel'
A = wb.create_sheet('Ações'); Dd = wb.create_sheet('Dados'); WS = wb.create_sheet('Wise'); AP = wb.create_sheet('API'); TS = wb.create_sheet('Campos')
C = wb.create_sheet('Classes'); PR = wb.create_sheet('Parâmetros')


def name(nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref)


def hdr(ws, r, c, text, w=None, fill=HEAD, color=WHITE, wrap=True):
    x = ws.cell(r, c, text); x.font = fnt(bold=True, color=color); x.fill = fill
    x.alignment = Alignment(horizontal='center', vertical='center', wrap_text=wrap)
    if w: ws.column_dimensions[L(c)].width = w
    return x

# ------------------------------------------------------------------ Parâmetros
PR.sheet_view.showGridLines = False
PR.column_dimensions['B'].width = 34; PR.column_dimensions['C'].width = 14; PR.column_dimensions['E'].width = 34; PR.column_dimensions['F'].width = 30
hdr(PR, 2, 2, 'Parâmetro'); hdr(PR, 2, 3, 'Valor')
params = [('ANO', 'Último exercício fechado', 2025, '0'), ('ATUALIZADO', 'Reserva (API) atualizada em', ATUALIZADO, '@'),
          ('ROIC_ALTO', 'ROIC: corte de qualidade', 0.12, PCT), ('ROIC_BAIXO', 'ROIC: piso', 0.10, PCT),
          ('CRESC_ALTO', 'Crescimento do EPS: corte', 0.15, PCT), ('CRESC_BAIXO', 'Crescimento do EPS: piso', 0.06, PCT),
          ('ZG_CORTE', 'zGrowth máximo (estabilidade)', 2.93, '0.00'),
          ('RET_ALTO', 'Retorno esperado: corte', 0.20, PCT), ('RET_BAIXO', 'Retorno esperado: piso', 0.08, PCT),
          ('WACC', 'Custo de capital', 0.085, PCT), ('G_TOPO', 'g máximo', 0.07, PCT), ('G_PISO', 'g mínimo', 0.035, PCT),
          ('G_TOPO_FIN', 'g máximo (financeiras)', 0.065, PCT), ('G_PISO_FIN', 'g mínimo (financeiras)', 0.03, PCT),
          ('ROIC_TETO', 'Teto do ROIC no P/E justo', 1.0, PCT0),
          ('HIGH_ROIC', 'High ROIC: ROIC acima de', 0.30, PCT0), ('HIGH_GROWTH', 'High Growth: crescimento acima de', 0.30, PCT0),
          ('ESP_ROIC', 'Especiais: ROIC acima de', 0.30, PCT0), ('ESP_G', 'Especiais: crescimento acima de', 0.30, PCT0),
          ('PL_MIN', 'P/L mínimo (Top 20)', 4, '0'), ('N_CARTEIRA', 'Ações na carteira', 20, '0'), ('TETO', 'Peso máximo por ação', 0.10, PCT0),
          ('VISAO_MAX', 'ROIC: visão descartada acima de', 2.0, PCT0), ('VISAO_TETO', 'ROIC: visão limitada a', 1.5, PCT0),
          ('DIVERG', 'ROIC: ativo e passivo "próximos" até', 2.0, '0.0x'), ('TAXA_ARR', 'Juros implícitos dos arrendamentos', 0.05, PCT),
          ('IR_PADRAO', 'Alíquota quando o IR não faz sentido', 0.21, PCT)]
for i, (nm, lab, v, f) in enumerate(params):
    r = 3 + i; PR.cell(r, 2, lab).font = fnt(); x = PR.cell(r, 3, v); x.font = fnt(color=BLUE); x.fill = INP; x.number_format = f
    x.alignment = Alignment(horizontal='right'); name(nm, f"'Parâmetros'!$C${r}")
    if nm.startswith('ARR_'):
        dv = DataValidation(type='list', formula1='"Sim,Não"', allow_blank=False); PR.add_data_validation(dv); dv.add(x)
# listas por código SIC (de / até)
SIC_TABS = [('CIC', 'Cíclicas (SIC)', [(1000, 1099), (1220, 1241), (1311, 1311), (1381, 1389), (2911, 2911), (3310, 3317), (3330, 3339), (2870, 2879),
                                       (5311, 5311), (4512, 4512), (3751, 3751), (7990, 7999), (5122, 5122), (3944, 3944)]),
            ('VES', 'Vestuário (SIC)', [(2200, 2399), (3020, 3021), (3100, 3199)]),
            ('ROE', 'Usa ROE (SIC)', [(6000, 6499), (6700, 6797), (6799, 6799)]),
            ('JGF', 'Fora da Fórmula Mágica (SIC)', [(6000, 6499), (6700, 6797), (6799, 6799), (4900, 4999)])]
for ti, (nm, title, rows) in enumerate(SIC_TABS):
    c0 = 5 + ti * 3
    hdr(PR, 2, c0, title, 10); PR.merge_cells(start_row=2, start_column=c0, end_row=2, end_column=c0 + 1)
    hdr(PR, 3, c0, 'De', 9, fill=SUB, color=INK); hdr(PR, 3, c0 + 1, 'Até', 9, fill=SUB, color=INK)
    for i in range(20):
        for j in range(2):
            x = PR.cell(4 + i, c0 + j, rows[i][j] if i < len(rows) else None); x.font = fnt(color=BLUE); x.fill = INP
    name(f'{nm}_DE', f"'Parâmetros'!${L(c0)}$4:${L(c0)}$23"); name(f'{nm}_ATE', f"'Parâmetros'!${L(c0 + 1)}$4:${L(c0 + 1)}$23")
    PR.column_dimensions[L(c0 + 2)].width = 3

hdr(PR, 26, 5, 'Nunca cíclica / vestuário (ticker)', 16); PR.merge_cells(start_row=26, start_column=5, end_row=26, end_column=6)
for i in range(10):
    x = PR.cell(27 + i, 5, ['CTAS'][i] if i < 1 else None); x.font = fnt(color=BLUE); x.fill = INP
name('NAO_CIC', "'Parâmetros'!$E$27:$E$36")

# ------------------------------------------------------------------ Classes
C.sheet_view.showGridLines = False
CLASSES = [('Opportunity of Lifetime', '1B5E20', WHITE), ('Good Companies, Great Returns', '43A047', WHITE), ('Excellent but Fair', 'A5D6A7', INK),
           ('Good but Margin of Safety Required', 'C8E6C9', INK), ('Cheap Slow Compounder', 'FFF59D', INK), ('Interesting but Requires Attention', 'FFE082', INK),
           ('Cheap but Aggressive', 'FFCC80', INK), ('Expensive for what you get', 'FFAB91', INK), ('Investable but Not Good', 'EF9A9A', INK),
           ('Expensive', 'E57373', INK), ('Do not Waste Time', 'BDBDBD', INK), ('Cyclicals', '8D6E63', WHITE), ('Sem dados', 'F2F2F2', '9E9E9E')]
hdr(C, 2, 2, '#', 5); hdr(C, 2, 3, 'Classe', 34); hdr(C, 2, 4, 'Ações', 9)
for i, (cl, bg, fg) in enumerate(CLASSES):
    r = 3 + i; C.cell(r, 2, i + 1).font = fnt(); x = C.cell(r, 3, cl); x.font = fnt(bold=True, color=fg); x.fill = PatternFill('solid', fgColor=bg)
    y = C.cell(r, 4, f"=COUNTIF('Ações'!$N${R0}:$N${R1},C{r})"); y.font = fnt(); y.number_format = NUM0
name('CLASSE_ORDEM', "'Classes'!$C$3:$C$15")
hdr(C, 2, 7, 'Cresc.', 8); hdr(C, 2, 8, 'zG', 6); hdr(C, 2, 9, 'ROIC', 7); hdr(C, 2, 10, 'zROIC', 7); hdr(C, 2, 11, 'Retorno', 8); hdr(C, 2, 12, 'Classe', 34); hdr(C, 2, 13, 'Código', 9)
for i, row in enumerate(CODES):
    r = 3 + i
    for j in range(5): C.cell(r, 7 + j, row[j]).font = fnt(color=BLUE)
    C.cell(r, 12, row[5]).font = fnt(color=BLUE); C.cell(r, 13, f'=G{r}&H{r}&I{r}&J{r}&K{r}').font = fnt(color=GREY)
name('COD_CHAVE', f"'Classes'!$M$3:$M${2 + len(CODES)}"); name('COD_CLASSE', f"'Classes'!$L$3:$L${2 + len(CODES)}")
C.cell(4 + len(CODES), 7, 'Cresc.: H > corte · O ≥ piso · L abaixo   |   zG: O estável · P instável   |   ROIC: G > corte · O ≥ piso · L abaixo   |   zROIC: N (não usado)   |   Retorno: G > corte · O ≥ piso · B abaixo').font = fnt(size=9, color=GREY)

# ------------------------------------------------------------------ Dados (Wisesheets + cálculos intermediários)
Dd.sheet_view.showGridLines = False; Dd.freeze_panes = f'C{R0}'
Dd.cell(R0 - 1, 2, 'Ticker'); Dd.column_dimensions['B'].width = 11
for r in range(R0, R1 + 1): Dd.cell(r, 2, f"='Ações'!B{r}").font = fnt()
col = 3
COL = {}  # chave -> coluna (ou lista de colunas por ano)
# campos: (chave, nomes candidatos no add-in, chave na API, rótulo)
PRICE_F = [('nome', ['Name'], 'name', 'Empresa'), ('setor', ['Sector'], None, 'Setor'), ('ind', ['Industry'], None, 'Indústria'),
           ('preco', ['Price'], 'price', 'Preço'), ('mcap', ['Market Cap', 'MarketCap', 'Mkt Cap'], 'marketCap', 'Valor de mercado')]
FIELDS = [('opinc', ['Operating Income', 'Operating income'], 'operating_income', 'Lucro operacional'),
          ('pretax', ['Income Before Tax', 'Pretax income', 'Pretax Income'], 'pretax_income', 'Lucro antes do IR'),
          ('tax', ['Income Tax Expense', 'Income tax expense'], 'income_tax_expense', 'IR'),
          ('ni', ['Net Income', 'Net income'], 'net_income', 'Lucro líquido'),
          ('eps', ['EPS Diluted', 'Eps diluted', 'EPS diluted'], 'eps_diluted', 'EPS'),
          ('ppe', ['Property Plant Equipment Net', 'Property plant equipment net'], 'property_plant_equipment_net', 'Imobilizado'),
          ('rou', ['Operating Lease Right Of Use Assets', 'Operating lease right of use assets'], 'operating_lease_right_of_use_assets', 'Direito de uso'),
          ('gw', ['Goodwill'], 'goodwill', 'Ágio'), ('intang', ['Intangible Assets', 'Intangible assets'], 'intangible_assets', 'Intangíveis'),
          ('ltinv', ['Long Term Investments', 'Long term investments'], 'long_term_investments', 'Invest. longo prazo'),
          ('tca', ['Total Current Assets', 'Total current assets'], 'total_current_assets', 'Ativo circulante'),
          ('cash', ['Cash And Cash Equivalents', 'Cash and cash equivalents'], 'cash_and_cash_equivalents', 'Caixa'),
          ('stinv', ['Short Term Investments', 'Short term investments'], 'short_term_investments', 'Aplicações'),
          ('tcl', ['Total Current Liabilities', 'Total current liabilities'], 'total_current_liabilities', 'Passivo circulante'),
          ('std', ['Short Term Debt', 'Short term debt'], 'short_term_debt', 'Dívida curto prazo'),
          ('debt', ['Total Debt', 'Total debt'], 'total_debt', 'Dívida total'),
          ('lease', ['Total Lease Obligations', 'Total lease obligations', 'Capital Lease Obligations'], 'total_lease_obligations', 'Arrendamentos'),
          ('eq', ['Total Stockholders Equity', 'Total stockholders equity'], 'total_stockholders_equity', 'Patrimônio'),
          ('mino', ['Minority Interest', 'Minority interest'], 'minority_interest', 'Minoritários'),
          ('capex', ['Capital Expenditure', 'Capital expenditures', 'Capital Expenditures'], 'capital_expenditures', 'Capex'),
          ('da', ['Depreciation And Amortization', 'Depreciation and amortization'], 'depreciation_and_amortization', 'Depreciação'),
          ('acq', ['Acquisitions Net', 'Acquisitions net'], 'acquisitions_net', 'Aquisições'),
          ('eqinc', ['Income From Equity Method Investments', 'Income from equity method investments'], 'income_from_equity_method_investments', 'Equivalência'),
          ('dps', ['Dividends Per Share', 'Dividends per share', 'Dividend Per Share'], 'dividends_per_share', 'Dividendo/ação')]
YRS = [4, 3, 2, 1, 0]
CHUNKS = [(R0 + i * 100, min(R0 + i * 100 + 99, R1)) for i in range(4)]  # até 100 tickers por chamada (limite do Wisesheets)

# --- aba Campos: descobre sozinha o nome que o add-in aceita (testa com a AAPL; poucas chamadas)
TS.sheet_view.showGridLines = False
for cc, (h, w) in enumerate([('Campo', 22), ('Nome escolhido', 34), ('Opção 1', 30), ('Teste 1', 12), ('Opção 2', 30), ('Teste 2', 12), ('Opção 3', 30), ('Teste 3', 12)], start=2):
    hdr(TS, 2, cc, h, w)
x = TS.cell(1, 2, 'Teste com:'); x.font = fnt(size=9, color=GREY); x = TS.cell(1, 3, 'AAPL'); x.font = fnt(color=BLUE, bold=True); x.fill = INP
PICK = {}
for i, (key, cands, api, lab) in enumerate(PRICE_F + FIELDS):
    r = 3 + i; TS.cell(r, 2, lab).font = fnt(bold=True)
    for j in range(3):
        nm_ = cands[j] if j < len(cands) else None
        x = TS.cell(r, 4 + 2 * j, nm_); x.font = fnt(color=BLUE); x.fill = INP
        if nm_:
            call = (f'IFERROR(_xldudf_WISEPRICE($C$1,{L(4 + 2 * j)}{r}),"")' if (key, cands, api, lab) in PRICE_F else
                    f'IFERROR(_xldudf_WISE($C$1,{L(4 + 2 * j)}{r},ANO),"")')
            # só testa a próxima opção se a anterior falhou (o IF não chama o add-in à toa)
            prevs = [f'{L(5 + 2 * q)}{r}' for q in range(j)]
            ok_prev = ','.join(f'ISNUMBER({x}),AND(ISTEXT({x}),{x}<>"")' for x in prevs)
            tst = f'=IF(OR({ok_prev}),"",{call})' if prevs else f'={call}'
            y = TS.cell(r, 5 + 2 * j, tst); y.font = fnt(size=9)
    TS.cell(r, 3, f'=IF(OR(ISNUMBER(E{r}),AND(ISTEXT(E{r}),E{r}<>"")),D{r},IF(OR(ISNUMBER(G{r}),AND(ISTEXT(G{r}),G{r}<>"")),F{r},IF(OR(ISNUMBER(I{r}),AND(ISTEXT(I{r}),I{r}<>"")),H{r},D{r})))').font = fnt(bold=True, color='1B5E20')
    PICK[key] = f"'Campos'!$C${r}"
TS.conditional_formatting.add('E3:I40', FormulaRule(formula=['AND(E3<>"",ISNUMBER(E3))'], fill=PatternFill('solid', fgColor='C8E6C9')))

# --- layout comum às abas Wise, API e Dados
def layout(ws):
    c0 = 3; cmap = {}
    for key, cands, api, lab in PRICE_F:
        hdr(ws, R0 - 3, c0, lab, 14); cmap[key] = c0; c0 += 1
    for k in [5] + YRS:
        cmap.setdefault('eps', {})[k] = None
    blocks = {}
    first = c0
    for k in [5] + YRS:
        hdr(ws, R0 - 3, c0, 'EPS', 9); y = ws.cell(R0 - 1, c0, f'=ANO-{k}' if k else '=ANO'); y.font = fnt(bold=True); y.number_format = '0'
        cmap['eps'][k] = c0; c0 += 1
    blocks['eps'] = (first, c0 - 1)
    for k in YRS:
        first = c0
        for key, cands, api, lab in FIELDS:
            if key == 'eps': continue
            cmap.setdefault(key, {})
            hdr(ws, R0 - 3, c0, lab, 11); y = ws.cell(R0 - 1, c0, f'=ANO-{k}' if k else '=ANO'); y.font = fnt(bold=True); y.number_format = '0'
            cmap[key][k] = c0; c0 += 1
        blocks[k] = (first, c0 - 1)
    return cmap, blocks, c0
for ws in (WS, AP, Dd):
    ws.sheet_view.showGridLines = False; ws.freeze_panes = f'C{R0}'; ws.cell(R0 - 1, 2, 'Ticker').font = fnt(bold=True); ws.column_dimensions['B'].width = 11
    for r in range(R0, R1 + 1): ws.cell(r, 2, f"='Ações'!B{r}").font = fnt()
COL, BLOCKS, col = layout(Dd); layout(WS); layout(AP)
# SIC (só na API; usado para cíclicas, financeiras e utilities)
for ws in (AP, Dd):
    hdr(ws, R0 - 3, col, 'SIC', 8); hdr(ws, R0 - 3, col + 1, 'Atividade (SIC)', 24)
COL['sic'], COL['sicd'] = col, col + 1; col += 2
RAW_LAST = col - 1
# nomes dos campos (linha 4) nas abas Wise: vêm da aba Campos
for key, cands, api, lab in PRICE_F:
    WS.cell(R0 - 2, COL[key], f'={PICK[key]}').font = fnt(size=8, color=GREY)
for key, cands, api, lab in FIELDS:
    for k, cc in COL[key].items(): WS.cell(R0 - 2, cc, f'={PICK[key]}').font = fnt(size=8, color=GREY)
# chamadas do add-in: matrizes de até 100 tickers; bloco vazio não chama nada
for a, b in CHUNKS:
    T = f'$B${a}:$B${b}'; gate = f'COUNTA(\'Ações\'!$B${a}:$B${b})=0'
    p0, p1 = COL['nome'], COL['mcap']
    WS.cell(a, p0).value = ArrayFormula(f'{L(p0)}{a}:{L(p1)}{b}', f'=IF({gate},"",IFERROR(_xldudf_WISEPRICE({T},{L(p0)}${R0 - 2}:{L(p1)}${R0 - 2}),""))')
    e0, e1 = BLOCKS['eps']
    WS.cell(a, e0).value = ArrayFormula(f'{L(e0)}{a}:{L(e1)}{b}', f'=IF({gate},"",IFERROR(_xldudf_WISE({T},{L(e0)}${R0 - 2},{L(e0)}${R0 - 1}:{L(e1)}${R0 - 1}),""))')
    for k in YRS:
        f0, f1 = BLOCKS[k]
        WS.cell(a, f0).value = ArrayFormula(f'{L(f0)}{a}:{L(f1)}{b}', f'=IF({gate},"",IFERROR(_xldudf_WISE({T},{L(f0)}${R0 - 2}:{L(f1)}${R0 - 2},{L(f0)}${R0 - 1}),""))')
# Dados: add-in primeiro; se vazio, a reserva da API
for r in range(R0, R1 + 1):
    for key, cands, api, lab in PRICE_F:
        cc = COL[key]; w_, a_ = f"'Wise'!{L(cc)}{r}", f"'API'!{L(cc)}{r}"
        Dd.cell(r, cc, f'=IF({w_}<>"",{w_},IF({a_}<>"",{a_},""))' if key in ('nome', 'setor', 'ind') else f'=IF(ISNUMBER({w_}),{w_},IF(ISNUMBER({a_}),{a_},""))')
    for key, cands, api, lab in FIELDS:
        for k, cc in COL[key].items():
            w_, a_ = f"'Wise'!{L(cc)}{r}", f"'API'!{L(cc)}{r}"
            Dd.cell(r, cc, f'=IF(ISNUMBER({w_}),{w_},IF(ISNUMBER({a_}),{a_},""))')
    Dd.cell(r, COL['sic'], f"=IF(ISNUMBER('API'!{L(COL['sic'])}{r}),'API'!{L(COL['sic'])}{r},\"\")")
    Dd.cell(r, COL['sicd'], f"=IF('API'!{L(COL['sicd'])}{r}<>\"\",'API'!{L(COL['sicd'])}{r},\"\")")
hdr(Dd, R0 - 3, col, 'Dividend yield', 11, fill=SUB, color=INK); COL['dy'] = col; col += 1
YLAB = None
# cálculos por ano
CALC = ['t', 'nopat', 'wc', 'ativo', 'passivo', 'ra', 'rp', 'roe']
CL = {'t': 'Alíquota', 'nopat': 'NOPAT', 'wc': 'Capital de giro', 'ativo': 'Capital (ativo)', 'passivo': 'Capital (passivo)', 'ra': 'ROIC ativo', 'rp': 'ROIC passivo', 'roe': 'ROE'}
for key in CALC:
    COL[key] = {}
    for k in YRS:
        hdr(Dd, R0 - 3, col, CL[key], 11, fill=SUB, color=INK); y = Dd.cell(R0 - 1, col, f'=ANO-{k}' if k else '=ANO'); y.font = fnt(bold=True); y.number_format = '0'
        COL[key][k] = col; col += 1
COL['reinv'] = {}
for k in [3, 2, 1, 0]:
    hdr(Dd, R0 - 3, col, 'Reinvestimento', 11, fill=SUB, color=INK); y = Dd.cell(R0 - 1, col, f'=ANO-{k}' if k else '=ANO'); y.font = fnt(bold=True); y.number_format = '0'
    COL['reinv'][k] = col; col += 1
COL['gr'] = {}
for k in YRS:
    hdr(Dd, R0 - 3, col, 'Cresc. EPS', 11, fill=SUB, color=INK); y = Dd.cell(R0 - 1, col, f'=ANO-{k}' if k else '=ANO'); y.font = fnt(bold=True); y.number_format = '0'
    COL['gr'][k] = col; col += 1
SUM = [('vA', 'ROIC ativo (resumo)'), ('vP', 'ROIC passivo (resumo)'), ('vM', 'ROIC marginal'), ('vROE', 'ROE (resumo)'), ('okA', 'Ativo válido'), ('okP', 'Passivo válido'),
       ('okM', 'Marginal válido'), ('cA', 'Ativo limitado'), ('cP', 'Passivo limitado'), ('tri', 'ROIC triangulado'), ('growth', 'Crescimento'), ('zg', 'zGrowth'),
       ('eps0', 'EPS último'), ('ebit', 'EBIT'), ('cap_t', 'Capital tangível'), ('ev', 'Valor da firma'), ('roc', 'ROC (JG)'), ('ey', 'EBIT/EV (JG)')]
for key, lab in SUM:
    hdr(Dd, R0 - 3, col, lab, 12, fill=SUB, color=INK); COL[key] = col; col += 1


def c(key, k=None, r='{r}', absrow=False):
    cc = COL[key] if k is None else COL[key][k]
    return f'{L(cc)}{r}'


# fórmulas
for r in range(R0, R1 + 1):
    t = f'$B{r}'
    def W(key, k=None):
        return f'{c(key, k).format(r=r)}'
    N = lambda key, k: f'N({W(key, k)})' if key in COL and k in COL[key] else '0'  # vazio/texto (ou campo não puxado) vira 0
    for k in YRS:
        Dd.cell(r, COL['t'][k], f'=IF(AND(ISNUMBER({W("pretax", k)}),ISNUMBER({W("tax", k)})),IF({W("pretax", k)}>0,MIN(MAX({W("tax", k)}/{W("pretax", k)},0),0.5),IR_PADRAO),IR_PADRAO)')
        ebit_k = f'IF(ISNUMBER({W("opinc", k)}),{W("opinc", k)},{W("pretax", k)})'  # sem lucro operacional: usa o lucro antes do IR
        Dd.cell(r, COL['nopat'][k], f'=IF(OR(ISNUMBER({W("opinc", k)}),ISNUMBER({W("pretax", k)})),({ebit_k}+{N("lease", k)}*TAXA_ARR+{N("eqinc", k)})*(1-{W("t", k)}),"")')
        Dd.cell(r, COL['wc'][k], f'=IF(AND(ISNUMBER({W("tca", k)}),ISNUMBER({W("tcl", k)})),({W("tca", k)}-{N("cash", k)}-{N("stinv", k)})-({W("tcl", k)}-{N("std", k)}),"")')
        Dd.cell(r, COL['ativo'][k], f'=IF(AND(ISNUMBER({W("ppe", k)}),ISNUMBER({W("wc", k)})),{W("ppe", k)}+{N("rou", k)}+{N("gw", k)}+{N("intang", k)}+{N("ltinv", k)}+{W("wc", k)},"")')
        Dd.cell(r, COL['passivo'][k], f'=IF(ISNUMBER({W("eq", k)}),{W("eq", k)}+{N("mino", k)}+{N("debt", k)}+{N("lease", k)}-{N("cash", k)}-{N("stinv", k)},"")')
        Dd.cell(r, COL['ra'][k], f'=IF(AND(ISNUMBER({W("nopat", k)}),N({W("ativo", k)})>0),{W("nopat", k)}/{W("ativo", k)},"")')
        Dd.cell(r, COL['rp'][k], f'=IF(AND(ISNUMBER({W("nopat", k)}),N({W("passivo", k)})>0),{W("nopat", k)}/{W("passivo", k)},"")')
        Dd.cell(r, COL['roe'][k], f'=IF(AND(ISNUMBER({W("ni", k)}),N({W("eq", k)})>0),{W("ni", k)}/{W("eq", k)},"")')
        if k not in COL['gr']: continue
        prev = W('eps', k + 1)
        Dd.cell(r, COL['gr'][k], f'=IF(AND(ISNUMBER({prev}),ISNUMBER({W("eps", k)})),IF({prev}>0,{W("eps", k)}/{prev}-1,""),"")')
    for k in [3, 2, 1, 0]:
        Dd.cell(r, COL['reinv'][k], f'=IF(AND(ISNUMBER({W("capex", k)}),ISNUMBER({W("da", k)}),ISNUMBER({W("wc", k)}),ISNUMBER({W("wc", k + 1)})),ABS({W("capex", k)})-{W("da", k)}-{N("acq", k)}+{W("wc", k)}-{W("wc", k + 1)},"")')
    rng = lambda key: f'{c(key, 4).format(r=r)}:{c(key, 0).format(r=r)}'
    last3 = lambda key: f'{c(key, 2).format(r=r)}:{c(key, 0).format(r=r)}'
    summ = lambda key: f'=IF(COUNT({rng(key)})>=2,AVERAGE(IF(COUNT({last3(key)})>0,AVERAGE({last3(key)}),MEDIAN({rng(key)})),MEDIAN({rng(key)})),"")'
    Dd.cell(r, COL['vA'], summ('ra')); Dd.cell(r, COL['vP'], summ('rp')); Dd.cell(r, COL['vROE'], summ('roe'))
    rv = f'{c("reinv", 3).format(r=r)}:{c("reinv", 0).format(r=r)}'
    Dd.cell(r, COL['vM'], f'=IF(AND(COUNT({rv})>=3,ISNUMBER({W("nopat", 0)}),ISNUMBER({W("nopat", 4)})),IF(AVERAGE({rv})>0,({W("nopat", 0)}-{W("nopat", 4)})/(AVERAGE({rv})*4),""),"")')
    for ok, v in (('okA', 'vA'), ('okP', 'vP'), ('okM', 'vM')):
        Dd.cell(r, COL[ok], f'=IF(ISNUMBER({W(v)}),AND({W(v)}>=0,{W(v)}<=VISAO_MAX),FALSE)')
    Dd.cell(r, COL['cA'], f'=IF({W("okA")},MIN({W("vA")},VISAO_TETO),"")'); Dd.cell(r, COL['cP'], f'=IF({W("okP")},MIN({W("vP")},VISAO_TETO),"")')
    a, p, m = W('cA'), W('cP'), W('vM')
    Dd.cell(r, COL['tri'], (f'=IF(AND({W("okA")},{W("okP")}),IF(AND(MIN({a},{p})>0,MAX({a},{p})<=DIVERG*MIN({a},{p})),AVERAGE({a},{p}),'
                            f'IF({W("okM")},IF(ABS({a}-{m})<=ABS({p}-{m}),{a},{p}),MIN({a},{p}))),'
                            f'IF({W("okA")},{a},IF({W("okP")},{p},IF(OR(N({W("vA")})>VISAO_MAX,N({W("vP")})>VISAO_MAX),VISAO_TETO,IF({W("okM")},MIN({m},VISAO_TETO),"")))))'))
    gr = f'{c("gr", 4).format(r=r)}:{c("gr", 0).format(r=r)}'
    Dd.cell(r, COL['growth'], f'=IF(COUNT({gr})>=3,MEDIAN({gr}),"")')
    Dd.cell(r, COL['zg'], f'=IF(ISNUMBER({W("growth")}),IF({W("growth")}<>0,STDEVP({gr})/{W("growth")},""),"")')
    Dd.cell(r, COL['eps0'], f'=IF(ISNUMBER({W("eps", 0)}),{W("eps", 0)},"")')
    Dd.cell(r, COL['dy'], f'=IF(AND(N({W("dps", 0)})>0,N({W("preco")})>0),{W("dps", 0)}/{W("preco")},0)')
    Dd.cell(r, COL['ebit'], f'=IF(ISNUMBER({W("opinc", 0)}),{W("opinc", 0)},"")')
    Dd.cell(r, COL['cap_t'], f'=IF(AND(ISNUMBER({W("wc", 0)}),ISNUMBER({W("ppe", 0)})),{W("wc", 0)}+{W("ppe", 0)},"")')
    Dd.cell(r, COL['ev'], f'=IF(ISNUMBER({W("mcap")}),{W("mcap")}+{N("debt", 0)}+0-{N("cash", 0)}-{N("stinv", 0)},"")')
    Dd.cell(r, COL['roc'], f'=IF(AND(N({W("ebit")})>0,N({W("cap_t")})>0),{W("ebit")}/{W("cap_t")},"")')
    Dd.cell(r, COL['ey'], f'=IF(AND(N({W("ebit")})>0,N({W("ev")})>0),{W("ebit")}/{W("ev")},"")')
for cc in range(3, col):
    for r in range(R0, R1 + 1): Dd.cell(r, cc).font = fnt()
for key in ('t', 'ra', 'rp', 'roe', 'gr'):
    for cc in COL[key].values():
        for r in range(R0, R1 + 1): Dd.cell(r, cc).number_format = PCT
for key in ('vA', 'vP', 'vM', 'vROE', 'cA', 'cP', 'tri', 'growth', 'roc', 'ey', 'dy'):
    for r in range(R0, R1 + 1): Dd.cell(r, COL[key]).number_format = PCT
for r in range(R0, R1 + 1): Dd.cell(r, COL['zg']).number_format = '0.00'

# ------------------------------------------------------------------ Ações (a tabela principal)
A.sheet_view.showGridLines = False; A.freeze_panes = f'C{R0}'
dref = lambda key, r: f"'Dados'!{L(COL[key])}{r}"
COLS = [('B', 'Ticker', 10), ('C', 'Empresa', 26), ('D', 'SIC', 7), ('E', 'Indústria', 26), ('F', 'Preço', 9), ('G', 'Valor de mercado', 12),
        ('H', 'ROIC', 8), ('I', 'Cresc. EPS', 8), ('J', 'zGrowth', 7), ('K', 'P/L', 7), ('L', 'P/E justo', 8), ('M', 'Retorno esperado', 9),
        ('N', 'Classe', 30), ('O', 'Top 20', 7), ('P', 'Peso', 7), ('Q', 'High ROIC', 7), ('R', 'High Growth', 7), ('S', 'Especiais', 8),
        ('T', 'JG', 6), ('U', 'JG + G', 7), ('V', 'Cíclica / vestuário', 9), ('W', 'Usa ROE', 7)]
for cl, lab, w in COLS:
    hdr(A, R0 - 1, ord(cl) - 64, lab, w)
A.row_dimensions[R0 - 1].height = 30
x = A.cell(2, 2, 'Price Tracker v3'); x.font = fnt(bold=True, size=16)
x = A.cell(3, 2, '="Dados do Wisesheets (API) em "&ATUALIZADO'); x.font = fnt(size=9, color=GREY)
# auxiliares (agrupadas e ocultas): Y em diante
AUX = ['fin', 'cyc', 'util', 'g', 'cG', 'cZ', 'cR', 'cRet', 'base', 'quali', 'elig', 'sTop', 'sqrtm', 'w0', 'capd', 'hrs', 'hgs', 'esp', 'espS', 'jgOk', 'jgS', 'jg2Ok', 'jg2S', 'cycS', 'jgR', 'jg2R', 'hrR', 'hgR', 'cycR']
AX = {k: 25 + i for i, k in enumerate(AUX)}  # col Y=25
AXL = {k: L(v) for k, v in AX.items()}
ALAB = {'fin': 'ROE?', 'cyc': 'Cíclica?', 'util': 'Fora JG?', 'g': 'g', 'cG': 'Cód. cresc.', 'cZ': 'Cód. zG', 'cR': 'Cód. ROIC', 'cRet': 'Cód. retorno',
        'base': 'Classe (antes do filtro)', 'quali': 'Qualidade', 'elig': 'Elegível Top 20', 'sTop': 'Nota Top 20', 'sqrtm': '√ valor', 'w0': 'Peso bruto',
        'capd': 'No teto?', 'hrs': 'Nota High ROIC', 'hgs': 'Nota High Growth', 'esp': 'Nota Especiais', 'espS': 'Ordem Especiais', 'jgOk': 'JG ok', 'jgS': 'Nota JG',
        'jg2Ok': 'JG+G ok', 'jg2S': 'Nota JG+G', 'cycS': 'Nota cíclica', 'jgR': 'Ordem JG', 'jg2R': 'Ordem JG+G', 'hrR': 'Ordem High ROIC', 'hgR': 'Ordem High Growth', 'cycR': 'Ordem cíclicas'}
for k, cc in AX.items():
    hdr(A, R0 - 1, cc, ALAB[k], 10, fill=SUB, color=INK)
rr = lambda k: f'${AXL[k]}${R0}:${AXL[k]}${R1}'
for r in range(R0, R1 + 1):
    i = r - R0
    tk = TICKERS[i] if i < len(TICKERS) else None
    x = A.cell(r, 2, tk); x.font = fnt(color=BLUE, bold=True); x.fill = INP
    e = f'$B{r}=""'
    A.cell(r, 3, f'=IF({e},"",{dref("nome", r)})'); A.cell(r, 4, f'=IF({e},"",{dref("sic", r)})'); A.cell(r, 5, f'=IF({e},"",IF({dref("ind", r)}<>"",{dref("ind", r)},{dref("sicd", r)}))')
    A.cell(r, 6, f'=IF({e},"",{dref("preco", r)})'); A.cell(r, 7, f'=IF({e},"",IFERROR({dref("mcap", r)}/1000000,""))')
    ax = lambda k: f'${AXL[k]}{r}'
    A.cell(r, AX['fin'], f'=IF({e},FALSE,SUMPRODUCT((N(D{r})>=ROE_DE)*(N(D{r})<=ROE_ATE)*(ROE_DE<>""))>0)')
    A.cell(r, AX['cyc'], f'=IF(OR({e},COUNTIF(NAO_CIC,$B{r})>0),FALSE,OR(SUMPRODUCT((N(D{r})>=CIC_DE)*(N(D{r})<=CIC_ATE)*(CIC_DE<>""))>0,SUMPRODUCT((N(D{r})>=VES_DE)*(N(D{r})<=VES_ATE)*(VES_DE<>""))>0))')
    A.cell(r, AX['util'], f'=IF({e},FALSE,SUMPRODUCT((N(D{r})>=JGF_DE)*(N(D{r})<=JGF_ATE)*(JGF_DE<>""))>0)')
    A.cell(r, 8, f'=IF({e},"",IF({ax("fin")},{dref("vROE", r)},{dref("tri", r)}))')
    A.cell(r, 9, f'=IF({e},"",{dref("growth", r)})'); A.cell(r, 10, f'=IF({e},"",{dref("zg", r)})')
    A.cell(r, 11, f'=IF(AND(ISNUMBER(F{r}),N({dref("eps0", r)})>0),F{r}/{dref("eps0", r)},"")')
    # g pelo ranking do crescimento, separado entre financeiras e as demais
    A.cell(r, AX['g'], (f'=IF(ISNUMBER(I{r}),IF({ax("fin")},G_TOPO_FIN,G_TOPO)-(COUNTIFS({rr("fin")},{ax("fin")},$I${R0}:$I${R1},">"&I{r}))'
                        f'*(IF({ax("fin")},G_TOPO_FIN-G_PISO_FIN,G_TOPO-G_PISO))/MAX(COUNTIFS({rr("fin")},{ax("fin")},$I${R0}:$I${R1},">-1E+300")-1,1),"")'))
    A.cell(r, 12, f'=IF(AND(ISNUMBER(H{r}),ISNUMBER({ax("g")})),IF(MIN(H{r},ROIC_TETO)>{ax("g")},(1-{ax("g")}/MIN(H{r},ROIC_TETO))/(WACC-{ax("g")}),""),"")')
    dy = f'N({dref("dy", r)})'
    A.cell(r, 13, (f'=IF(ISNUMBER(I{r}),IF(AND(ISNUMBER(L{r}),N({dref("eps0", r)})>0,N(F{r})>0),'
                   f'AVERAGE(SQRT(MAX(L{r}*{dref("eps0", r)}*(1+I{r})^2/F{r},0))-1+{dy},I{r}+{dy}),I{r}+{dy}),"")'))
    A.cell(r, AX['cG'], f'=IF(ISNUMBER(I{r}),IF(I{r}>CRESC_ALTO,"H",IF(I{r}>=CRESC_BAIXO,"O","L")),"")')
    A.cell(r, AX['cZ'], f'=IF(ISNUMBER(J{r}),IF(J{r}<ZG_CORTE,"O","P"),"")')
    A.cell(r, AX['cR'], f'=IF(ISNUMBER(H{r}),IF(H{r}>ROIC_ALTO,"G",IF(H{r}>=ROIC_BAIXO,"O","L")),"")')
    A.cell(r, AX['cRet'], f'=IF(ISNUMBER(M{r}),IF(M{r}>RET_ALTO,"G",IF(M{r}>=RET_BAIXO,"O","B")),"")')
    A.cell(r, AX['base'], f'=IF({e},"",IFERROR(INDEX(COD_CLASSE,MATCH({ax("cG")}&{ax("cZ")}&{ax("cR")}&"N"&{ax("cRet")},COD_CHAVE,0)),"Do not Waste Time"))')
    A.cell(r, 14, f'=IF({e},"",IF(AND(NOT(ISNUMBER(H{r})),NOT(ISNUMBER(I{r}))),"Sem dados",IF(AND({ax("cyc")},OR({ax("base")}="Opportunity of Lifetime",{ax("base")}="Good Companies, Great Returns")),"Cyclicals",{ax("base")})))')
    A.cell(r, AX['quali'], f'=IF({e},FALSE,AND(ISNUMBER(H{r}),ISNUMBER(I{r}),N(H{r})>=ROIC_ALTO,N(I{r})>=CRESC_ALTO,NOT({ax("cyc")})))')
    A.cell(r, AX['elig'], f'=AND({ax("quali")},ISNUMBER(K{r}),N(K{r})>=PL_MIN,ISNUMBER(M{r}))')
    A.cell(r, AX['sTop'], f'=IF({ax("elig")},M{r}+ROW()*1E-12,"")')
    A.cell(r, 15, f'=IF({ax("elig")},IF(COUNTIF({rr("sTop")},">"&{ax("sTop")})+1<=N_CARTEIRA,COUNTIF({rr("sTop")},">"&{ax("sTop")})+1,""),"")')
    A.cell(r, AX['sqrtm'], f'=IF(AND(ISNUMBER(O{r}),N(G{r})>0),SQRT(G{r}),IF(ISNUMBER(O{r}),1,""))')
    A.cell(r, AX['w0'], f'=IF(ISNUMBER({ax("sqrtm")}),{ax("sqrtm")}/SUM({rr("sqrtm")}),"")')
    A.cell(r, AX['capd'], f'=IF(ISNUMBER({ax("w0")}),{ax("w0")}>=TETO,"")')
    A.cell(r, 16, (f'=IF(ISNUMBER({ax("w0")}),IF({ax("capd")},TETO,{ax("w0")}*(1-TETO*COUNTIF({rr("capd")},TRUE))'
                   f'/MAX(SUMIF({rr("capd")},FALSE,{rr("w0")}),1E-9)),"")'))
    A.cell(r, AX['hrs'], f'=IF(AND(N$14="",TRUE,N{r}="Opportunity of Lifetime",N(H{r})>HIGH_ROIC),M{r}+ROW()*1E-12,"")'.replace('N$14="",TRUE,', ''))
    A.cell(r, AX['hgs'], f'=IF(AND(N{r}="Opportunity of Lifetime",N(I{r})>HIGH_GROWTH),M{r}+ROW()*1E-12,"")')
    A.cell(r, 17, f'=IF(ISNUMBER({ax("hrs")}),"✓","")'); A.cell(r, 18, f'=IF(ISNUMBER({ax("hgs")}),"✓","")')
    A.cell(r, AX['esp'], f'=IF({ax("quali")},MIN(H{r}/ESP_ROIC,I{r}/ESP_G)+ROW()*1E-12,"")')
    A.cell(r, 19, f'=IF(ISNUMBER({ax("esp")}),IF(COUNTIF({rr("esp")},">"&{ax("esp")})+1<=N_CARTEIRA,COUNTIF({rr("esp")},">"&{ax("esp")})+1,""),"")')
    A.cell(r, AX['jgOk'], f'=IF({e},FALSE,AND(NOT({ax("util")}),ISNUMBER({dref("roc", r)}),ISNUMBER({dref("ey", r)})))')
    A.cell(r, AX['jgS'], (f'=IF({ax("jgOk")},COUNTIFS({rr("jgOk")},TRUE,\'Dados\'!${L(COL["roc"])}${R0}:${L(COL["roc"])}${R1},">"&{dref("roc", r)})+'
                          f'COUNTIFS({rr("jgOk")},TRUE,\'Dados\'!${L(COL["ey"])}${R0}:${L(COL["ey"])}${R1},">"&{dref("ey", r)})+2+ROW()*1E-9,"")'))
    A.cell(r, 20, f'=IF(ISNUMBER({ax("jgS")}),IF(COUNTIF({rr("jgS")},"<"&{ax("jgS")})+1<=N_CARTEIRA,COUNTIF({rr("jgS")},"<"&{ax("jgS")})+1,""),"")')
    A.cell(r, AX['jg2Ok'], f'=IF({e},FALSE,AND(NOT({ax("util")}),NOT({ax("cyc")}),ISNUMBER(H{r}),ISNUMBER(I{r}),ISNUMBER(K{r}),N({dref("ebit", r)})>0))')
    A.cell(r, AX['jg2S'], (f'=IF({ax("jg2Ok")},COUNTIFS({rr("jg2Ok")},TRUE,$H${R0}:$H${R1},">"&H{r})+COUNTIFS({rr("jg2Ok")},TRUE,$I${R0}:$I${R1},">"&I{r})'
                           f'+COUNTIFS({rr("jg2Ok")},TRUE,$K${R0}:$K${R1},"<"&K{r})+3+ROW()*1E-9,"")'))
    A.cell(r, 21, f'=IF(ISNUMBER({ax("jg2S")}),IF(COUNTIF({rr("jg2S")},"<"&{ax("jg2S")})+1<=N_CARTEIRA,COUNTIF({rr("jg2S")},"<"&{ax("jg2S")})+1,""),"")')
    A.cell(r, 22, f'=IF({ax("cyc")},"✓","")'); A.cell(r, 23, f'=IF({ax("fin")},"✓","")')
    A.cell(r, AX['cycS'], f'=IF(N{r}="Cyclicals",M{r}+ROW()*1E-12,"")')
    A.cell(r, AX['jgR'], f'=T{r}'); A.cell(r, AX['jg2R'], f'=U{r}')
    for kk, sc in (('hrR', 'hrs'), ('hgR', 'hgs'), ('cycR', 'cycS')):
        A.cell(r, AX[kk], f'=IF(ISNUMBER({ax(sc)}),COUNTIF({rr(sc)},">"&{ax(sc)})+1,"")')
    for cc in list(range(3, 24)) + list(AX.values()):
        A.cell(r, cc).font = fnt()
    for cc, f in ((6, '#,##0.00;-#,##0.00;-'), (7, NUM0), (8, PCT), (9, PCT), (10, '0.00'), (11, MULT), (12, MULT), (13, PCT), (16, PCT), (AX['g'], PCT)):
        A.cell(r, cc).number_format = f
    for cc in (15, 17, 18, 19, 20, 21, 22, 23): A.cell(r, cc).alignment = Alignment(horizontal='center')
    A.cell(r, 14).font = fnt(bold=True)
A.column_dimensions.group(L(AX['fin']), L(AX['cycR']), hidden=True)
# cores das classes
for cl, bg, fg in CLASSES:
    A.conditional_formatting.add(f'N{R0}:N{R1}', CellIsRule(operator='equal', formula=[f'"{cl}"'], fill=PatternFill('solid', fgColor=bg), font=Font(name=F, bold=True, color=fg)))
A.conditional_formatting.add(f'O{R0}:O{R1}', FormulaRule(formula=[f'ISNUMBER(O{R0})'], fill=PatternFill('solid', fgColor='0F5499'), font=Font(name=F, bold=True, color=WHITE)))
for cl in ('Q', 'R', 'S', 'T', 'U'):
    A.conditional_formatting.add(f'{cl}{R0}:{cl}{R1}', FormulaRule(formula=[f'{cl}{R0}<>""'], fill=PatternFill('solid', fgColor='DCEBF7')))
A.conditional_formatting.add(f'V{R0}:V{R1}', FormulaRule(formula=[f'V{R0}<>""'], fill=PatternFill('solid', fgColor='EFE3DC')))
A.auto_filter.ref = f'B{R0 - 1}:W{R1}'

# ------------------------------------------------------------------ Painel
P.sheet_view.showGridLines = False
x = P.cell(2, 2, 'Price Tracker v3'); x.font = fnt(bold=True, size=18)
x = P.cell(3, 2, '="Dados do Wisesheets (API) em "&ATUALIZADO&"   ·   "&COUNTIF(\'Ações\'!C' + str(R0) + ':C' + str(R1) + ',"?*")&" ações com dados"'); x.font = fnt(size=10, color=GREY)
# contagem por classe
r = 5
for i, (cl, bg, fg) in enumerate(CLASSES):
    cc = 2 + i
    x = P.cell(r, cc, cl); x.font = fnt(bold=True, size=8, color=fg); x.fill = PatternFill('solid', fgColor=bg); x.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    y = P.cell(r + 1, cc, f"=COUNTIF('Ações'!$N${R0}:$N${R1},\"{cl}\")"); y.font = fnt(bold=True, size=14); y.alignment = Alignment(horizontal='center')
    P.column_dimensions[L(cc)].width = 12
P.row_dimensions[r].height = 36
LISTS = [('Top 20 · Opportunity of Lifetime', 'O', ['Peso', 'Retorno', 'ROIC', 'Cresc.', 'P/L'], ['P', 'M', 'H', 'I', 'K'], '0F5499'),
         ('High ROIC', AXL['hrR'], ['Retorno', 'ROIC', 'Cresc.', 'P/L'], ['M', 'H', 'I', 'K'], '990F3D'),
         ('High Growth', AXL['hgR'], ['Retorno', 'ROIC', 'Cresc.', 'P/L'], ['M', 'H', 'I', 'K'], 'C2410C'),
         ('Especiais', 'S', ['ROIC', 'Cresc.', 'Retorno', 'Classe'], ['H', 'I', 'M', 'N'], '593380'),
         ('Fórmula Mágica JG + G', 'U', ['ROIC', 'Cresc.', 'P/L', 'Classe'], ['H', 'I', 'K', 'N'], '0D7680'),
         ('Fórmula Mágica JG', 'T', ['ROC', 'EBIT/EV', 'P/L', 'Classe'], [None, None, 'K', 'N'], '5A6774'),
         ('Cyclicals', AXL['cycR'], ['Retorno', 'ROIC', 'Cresc.', 'Indústria'], ['M', 'H', 'I', 'E'], '8D6E63')]
FMT = {'P': PCT, 'M': PCT, 'H': PCT, 'I': PCT, 'K': MULT, 'N': '@', 'E': '@'}
top = 9
for li, (title, rk, labs, cols, color) in enumerate(LISTS):
    c0 = 2 if li % 2 == 0 else 2 + 9 + 1
    r0 = top + (li // 2) * 25
    x = P.cell(r0, c0, title); x.font = fnt(bold=True, size=12, color=WHITE)
    for cc in range(c0, c0 + 3 + len(labs)): P.cell(r0, cc).fill = PatternFill('solid', fgColor=color)
    for j, h in enumerate(['#', 'Ticker', 'Empresa'] + labs):
        y = P.cell(r0 + 1, c0 + j, h); y.font = fnt(bold=True, size=9, color=GREY); y.border = BOT
    rkr = f"'Ações'!${rk}${R0}:${rk}${R1}"
    for k in range(1, 21):
        rr_ = r0 + 1 + k
        P.cell(rr_, c0, k).font = fnt(size=9, color=GREY)
        m = f'MATCH({k},{rkr},0)'
        P.cell(rr_, c0 + 1, f"=IFERROR(INDEX('Ações'!$B${R0}:$B${R1},{m}),\"\")").font = fnt(bold=True)
        P.cell(rr_, c0 + 2, f"=IFERROR(INDEX('Ações'!$C${R0}:$C${R1},{m}),\"\")").font = fnt(size=9)
        for j, cl in enumerate(cols):
            if cl is None:
                key = 'roc' if j == 0 else 'ey'; src = f"'Dados'!${L(COL[key])}${R0}:${L(COL[key])}${R1}"; fm = PCT
            else:
                src = f"'Ações'!${cl}${R0}:${cl}${R1}"; fm = FMT[cl]
            y = P.cell(rr_, c0 + 3 + j, f'=IFERROR(INDEX({src},{m}),"")'); y.font = fnt(size=9); y.number_format = fm
for cc, w in ((2, 4), (3, 9), (4, 24), (12, 4), (13, 9), (14, 24)):
    P.column_dimensions[L(cc)].width = w
for cc in list(range(5, 11)) + list(range(15, 21)): P.column_dimensions[L(cc)].width = 10
P.column_dimensions['I'].width = 22; P.column_dimensions['S'].width = 22

# ------------------------------------------------------------------ aba API: reserva com valores (mesmo layout), por exercício fixo
num = lambda v: (float(v) if v not in (None, '') else None)
ANO_V = 2025
for r in range(R0, R1 + 1):
    i = r - R0
    if i >= len(TICKERS): break
    t = TICKERS[i]; fin = API['fin'].get(t, {}); pr = API['price'].get(t) or {}; pf = API['profile'].get(t) or {}
    AP.cell(r, COL['nome']).value = pr.get('name') or pf.get('name') or fin.get('_name')
    AP.cell(r, COL['preco']).value = num(pr.get('price')); AP.cell(r, COL['mcap']).value = num(pr.get('marketCap'))
    AP.cell(r, COL['sic']).value = int(pf['sic']) if pf.get('sic') else None
    AP.cell(r, COL['sicd']).value = (pf.get('sicDescription') or '').title() or None
    for key, cands, api, lab in FIELDS:
        for k, cc in COL[key].items():
            row = fin.get(str(ANO_V - k))
            if row: AP.cell(r, cc).value = row.get(api)

for ws in wb.worksheets:
    ws.sheet_properties.tabColor = {'Painel': '0F5499', 'Ações': '1B5E20', 'Dados': '9E9E9E', 'Wise': '9E9E9E', 'API': '9E9E9E', 'Campos': 'C9A227', 'Classes': '9E9E9E', 'Parâmetros': 'C9A227'}[ws.title]
wb.save(OUT)
if True:  # matriz dinâmica (spill) igual à V2, nas abas Wise: cm="1" nas células com fórmula de matriz + metadata.xml
    tmp = OUT.with_suffix('.tmp.xlsx'); shutil.move(OUT, tmp)
    with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
        names = zi.namelist(); sheet = None
        wbx = zi.read('xl/workbook.xml').decode(); rels = zi.read('xl/_rels/workbook.xml.rels').decode()
        rid = re.search(r'<sheet [^>]*name="Wise"[^>]*r:id="(rId\d+)"', wbx).group(1)
        rel = re.search(rf'<Relationship [^>]*Id="{rid}"[^>]*/>', rels).group(0)
        sheet = 'xl/' + re.search(r'Target="/?(?:xl/)?([^"]+)"', rel).group(1)
        for nm in names:
            data = zi.read(nm)
            if nm == sheet:
                data = re.sub(rb'<c (r="[A-Z]+\d+"[^>]*?)>(<f t="array")', rb'<c \1 cm="1">\2', data)
            elif nm == '[Content_Types].xml':
                data = data.replace(b'</Types>', b'<Override PartName="/xl/metadata.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml"/></Types>')
            elif nm == 'xl/_rels/workbook.xml.rels':
                data = data.replace(b'</Relationships>', b'<Relationship Id="rIdMeta1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata" Target="metadata.xml"/></Relationships>')
            zo.writestr(nm, data)
        zo.writestr('xl/metadata.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><metadata xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:xda="http://schemas.microsoft.com/office/spreadsheetml/2017/dynamicarray"><metadataTypes count="1"><metadataType name="XLDAPR" minSupportedVersion="120000" copy="1" pasteAll="1" pasteValues="1" merge="1" splitFirst="1" rowColShift="1" clearFormats="1" clearComments="1" assign="1" coerce="1" cellMeta="1"/></metadataTypes><futureMetadata name="XLDAPR" count="1"><bk><extLst><ext uri="{bdbb8cdc-fa1e-496e-a857-3c3f30c029c3}"><xda:dynamicArrayProperties fDynamic="1" fCollapsed="0"/></ext></extLst></bk></futureMetadata><cellMetadata count="1"><bk><rc t="1" v="0"/></bk></cellMetadata></metadata>')
    tmp.unlink()
print('ok', OUT, 'colunas Dados', col)
