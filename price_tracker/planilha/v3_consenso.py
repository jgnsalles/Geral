"""Price Tracker V3 com consenso (2026-11-22, decisão do usuário). Regra de ACOMPANHAMENTO, não testada (não há histórico do consenso).
Crescimento = EPS estimado do sell-side com haircut (ano+1 ×0,95; ano+2 ×0,90; ano+3 ×0,85), CAGR de 3 anos sobre o último EPS publicado,
teto de 40%. P/L = média do LTM e do 1 ano à frente. ROIC triangulado leve (4 anos). Top 20 com no máximo 6 ações por setor.
Abas: Painel · Ações · Carteira · Histórico (carteira-sombra) · Bagger Rank · Regras · Cálculo · Dados.
Uso: python3 planilha/v3_consenso.py planilha/Price_Tracker_v3.xlsx"""
import sys, json, re, shutil, zipfile, pathlib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.formatting.rule import FormulaRule
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import get_column_letter as L

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'planilha/Price_Tracker_v3.xlsx')
HERE = pathlib.Path(__file__).parent
TICK = json.load(open(HERE / 'universo_v2.json'))
EXTRAS = json.load(open(HERE / 'v2_extras.json')); CART = EXTRAS['carteira']; BAGGER = EXTRAS['bagger']
CODES = json.load(open(HERE / 'codes.json'))
R0, R1 = 5, 5 + len(TICK) + 29          # linhas das ações (sobram 30 para novas)
RG = lambda col, sh='': f"{sh}${col}${R0}:${col}${R1}"
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'

# ---------------- estilo ----------------
INK, PAPER, MUTED, RULE = '1F2A37', 'FFFFFF', '6B7280', 'D9DEE5'
ACC = {'ool': '0B6E4F', 'gcgr': '2E7D9A', 'cyc': 'C2571A', 'hr': '5B3A99', 'hg': 'B5338A', 'exc': '9A1B3D', 'top': '0F4C81', 'esp': '7A5C00', 'jg': '3C6E1F'}
F_H = Font(name='Aptos', bold=True, color='FFFFFF', size=10)
F_T = Font(name='Aptos Display', bold=True, size=18, color=INK)
F_S = Font(name='Aptos', size=10, color=MUTED)
F_B = Font(name='Aptos', size=10, color=INK)
F_BB = Font(name='Aptos', size=10, color=INK, bold=True)
thin = Border(bottom=Side(style='thin', color=RULE))
fill = lambda h: PatternFill('solid', start_color=h, end_color=h)
PCT, PCT0, NUM1, NUM2 = '0.0%', '0%', '0.0', '0.00'

wb = openpyxl.Workbook()
P = wb.active; P.title = 'Painel'
A = wb.create_sheet('Ações'); K = wb.create_sheet('Carteira'); H = wb.create_sheet('Histórico'); BG = wb.create_sheet('Bagger Rank')
G = wb.create_sheet('Regras'); C = wb.create_sheet('Cálculo'); D = wb.create_sheet('Dados')
QA, QC, QD, QG = "'Ações'!", "'Cálculo'!", 'Dados!', 'Regras!'


def head(ws, r, c, text, color=INK, w=None):
    x = ws.cell(r, c, text); x.font = F_H; x.fill = fill(color); x.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    if w: ws.column_dimensions[L(c)].width = w
    return x


def put(ws, r, c, v, fmt=None, font=F_B, al=None):
    x = ws.cell(r, c, v); x.font = font
    if fmt: x.number_format = fmt
    if al: x.alignment = Alignment(horizontal=al)
    return x


# ---------------- Regras ----------------
G['A1'] = 'Regras'; G['A1'].font = F_T
G['A2'] = 'Valores em amarelo podem ser mudados. Crescimento = consenso do sell-side com haircut: regra de acompanhamento, não testada no backtest.'; G['A2'].font = F_S
RULES = [('G_ALTO', 'Crescimento alto', .15, PCT0), ('G_BAIXO', 'Crescimento baixo', .06, PCT0), ('ZG', 'zGrowth máximo', 0.9, NUM2),
         ('ROIC_ALTO', 'ROIC alto', .12, PCT0), ('ROIC_BAIXO', 'ROIC baixo', .10, PCT0), ('RET_ALTO', 'Retorno esperado alto', .20, PCT0),
         ('RET_BAIXO', 'Retorno esperado baixo', .08, PCT0), ('WACC', 'WACC do P/E justo', .085, PCT), ('G_TOPO', 'g do P/E justo: maior', .07, PCT),
         ('G_PISO', 'g do P/E justo: menor', .035, PCT), ('G_FIN', 'Financeiras: g 0,5 p.p. menor', .005, PCT), ('HR_CORTE', 'High ROIC: ROIC acima de', .30, PCT0),
         ('HG_CORTE', 'High Growth: crescimento acima de', .30, PCT0), ('PL_MIN', 'Top 20: P/L mínimo', 4, '0'), ('N_LISTA', 'Tamanho das listas', 20, '0'),
         ('TETO', 'Peso máximo por ação', .10, PCT0), ('HAIRCUT_1', 'Haircut EPS ano+1 (só no retorno)', .97, NUM2), ('HAIRCUT_2', 'Haircut EPS ano+2', .94, NUM2),
         ('HAIRCUT_3', 'Haircut EPS ano+3', .91, NUM2), ('G_MAX', 'Teto do crescimento', 1.00, PCT0), ('CAP_SETOR', 'Top 20: máximo de ações por setor', 8, '0'), ('CAP_PESO_SETOR', 'Carteiras de 20: peso máximo por setor', .40, PCT0),
         ('BEAR_MIN', 'Bear: retorno mínimo para OoL, Top 20 e Especiais', -.10, PCT0), ('BEAR_PCTL', 'Bear: percentil da indústria', .70, NUM2),
         ('BEAR_CORTE', 'Bear: fração do próprio crescimento', .70, NUM2), ('BEAR_GMIN', 'Bear: crescimento mínimo', .06, PCT0), ('BEAR_MULT', 'Bear: fração do P/E justo', .80, NUM2),
         ('CRED_MARGEM', 'Credibilidade: consenso até histórico + ', .10, PCT0), ('STEP_X', 'Step change: EPS 2028 ÷ EPS 2025 a partir de', 1.8, NUM2),
         ('STEP_G', 'Step change: g maduro do múltiplo de saída', .045, PCT), ('STEP_MIN', 'Step change: retorno com devolução mínimo', -.10, PCT0),
         ('COMP_MC', 'Compounders: valor de mercado mínimo (US$)', 50e9, '#,##0,,,'), ('PEQ_MIN', 'Pequenas: valor de mercado mínimo (US$)', 2e9, '#,##0,,,'),
         ('PEQ_MAX', 'Pequenas: valor de mercado máximo (US$)', 30e9, '#,##0,,,'), ('ESC_MIN', 'Escadinha mínima (Compounders e Pequenas)', 70, '0'),
         ('PANICO', 'Ótima em pânico: queda em 12 meses de pelo menos', -.25, PCT0), ('QL_FALTA', 'Quase lá: falta cair no máximo', -.30, PCT0)]
head(G, 4, 1, 'Regra', w=34); head(G, 4, 2, 'Valor', w=12)
for i, (nmr, lab, v, f) in enumerate(RULES):
    r = 5 + i; put(G, r, 1, lab); x = put(G, r, 2, v, f); x.fill = fill('FFF4C2')
    wb.defined_names[nmr] = DefinedName(nmr, attr_text=f"Regras!$B${r}")
CYC = ['Oil & Gas Exploration & Production', 'Oil & Gas Equipment & Services', 'Oil & Gas Drilling', 'Oil & Gas Refining & Marketing', 'Copper', 'Steel',
       'Agricultural Inputs', 'Department Stores', 'Airlines, Airports & Air Services', 'Recreational Vehicles', 'Gambling, Resorts & Casinos',
       'Electronic Gaming & Multimedia', 'Oil & Gas Integrated', 'Oil & Gas Midstream', 'Gold', 'Silver', 'Other Precious Metals']
# seguros multilinha e distribuidoras de saúde saíram; petróleo integrado/midstream e ouro/prata entraram (decisões do usuário, 2026-11-22)
EXCL = ['FSLR']   # excluídas à mão (FSLR: depende de subsídio)
CYC_EX = []   # tickers que não são cíclicos apesar da indústria
APP = ['Apparel - Manufacturers', 'Apparel - Footwear & Accessories', 'Luxury Goods']
HEALTH = ['UNH', 'ELV', 'CNC', 'HUM', 'MOH', 'CI']
lists = [('Cíclicas (indústria)', CYC, 'CICLICAS'), ('Exceções: não cíclica (ticker)', CYC_EX, 'NAO_CICLICAS'), ('Vestuário (indústria)', APP, 'VESTUARIO'),
         ('Usam ROE (ticker)', HEALTH, 'ROE_TICKERS'), ('Excluídas à mão (ticker)', EXCL, 'EXCLUIR')]
for j, (lab, vals, nmr) in enumerate(lists):
    c = 4 + j; head(G, 4, c, lab, w=32)
    for i in range(25):
        x = G.cell(5 + i, c, vals[i] if i < len(vals) else None); x.font = F_B; x.fill = fill('FFF4C2')
    wb.defined_names[nmr] = DefinedName(nmr, attr_text=f"Regras!${L(c)}$5:${L(c)}$29")
head(G, 4, 9, 'Código', w=10); head(G, 4, 10, 'Classe', w=36)
for i, row in enumerate(CODES):
    put(G, 5 + i, 9, ''.join(row[:5])); put(G, 5 + i, 10, row[5])
wb.defined_names['COD'] = DefinedName('COD', attr_text=f"Regras!$I$5:$I${4 + len(CODES)}")
wb.defined_names['COD_CLASSE'] = DefinedName('COD_CLASSE', attr_text=f"Regras!$J$5:$J${4 + len(CODES)}")
# moeda de reporte e proporção da ADR: o EPS vem na moeda local e por ação ordinária; o preço vem em dólar e por ADR
ADRS = [('TSM', 'TWD', 5, 'Só câmbio'), ('ASML', 'EUR', 1, 'Sim'), ('NVO', 'DKK', 1, 'Sim'), ('SAP', 'EUR', 1, 'Sim'), ('RELX', 'GBP', 1, 'Sim'),
        ('UL', 'EUR', 1, 'Sim'), ('SPOT', 'EUR', 1, 'Sim'), ('RACE', 'EUR', 1, 'Sim'), ('RYAAY', 'EUR', 2.5, 'Sim'), ('ONON', 'CHF', 1, 'Sim'),
        ('IFNNY', 'EUR', 1, 'Sim'), ('BTI', 'GBP', 1, 'Sim'), ('CNI', 'CAD', 1, 'Sim'), ('CP', 'CAD', 1, 'Sim'), ('CNQ', 'CAD', 1, 'Sim'),
        ('SU', 'CAD', 1, 'Sim'), ('ENB', 'CAD', 1, 'Sim'), ('TRP', 'CAD', 1, 'Sim')]
for j, (h, wd) in enumerate([('Ticker (moeda ≠ USD)', 14), ('Moeda', 8), ('Ações por ADR', 9), ('Estimativa: Sim / Só câmbio / Não', 14)]): head(G, 4, 12 + j, h, w=wd)
for i in range(30):
    row = ADRS[i] if i < len(ADRS) else (None, None, None, None)
    for j, v in enumerate(row):
        x = G.cell(5 + i, 12 + j, v); x.font = F_B; x.fill = fill('FFF4C2')
for nmr, c in (('ADR_T', 'L'), ('ADR_M', 'M'), ('ADR_N', 'N'), ('ADR_E', 'O')):
    wb.defined_names[nmr] = DefinedName(nmr, attr_text=f"Regras!${c}$5:${c}$34")
FX = [('EUR', 'EURUSD', False, 1.08), ('GBP', 'GBPUSD', False, 1.27), ('DKK', 'USDDKK', True, 6.9), ('TWD', 'USDTWD', True, 32.0),
      ('CHF', 'USDCHF', True, 0.88), ('CAD', 'USDCAD', True, 1.38)]
for j, (h, wd) in enumerate([('Moeda', 8), ('US$ por unidade', 11), ('Par no Wisesheets', 12)]): head(G, 4, 17 + j, h, w=wd)
for i, (m, par, inv, fb) in enumerate(FX):
    G.cell(5 + i, 17, m).font = F_B
    f = f'=IFERROR(1/_xldudf_WISEPRICE("{par}","Price"),{1 / fb:.6f})' if inv else f'=IFERROR(_xldudf_WISEPRICE("{par}","Price"),{fb})'
    x = G.cell(5 + i, 18, f); x.number_format = '0.0000'; x.font = F_B
    G.cell(5 + i, 19, par).font = F_S
wb.defined_names['FX_M'] = DefinedName('FX_M', attr_text="Regras!$Q$5:$Q$14")
wb.defined_names['FX_V'] = DefinedName('FX_V', attr_text="Regras!$R$5:$R$14")
# nota qualitativa do usuário (produto crítico e barato, penetração): ticker e nota de 1 a 5; entra na média da Nota de boa empresa
for j, (h, wd) in enumerate([('Nota qualitativa: ticker', 14), ('Nota (1 a 5)', 10)]): head(G, 4, 21 + j, h, w=wd)
for i in range(40):
    for j in range(2):
        x = G.cell(5 + i, 21 + j); x.fill = fill('FFF4C2'); x.font = F_B
wb.defined_names['NQ_T'] = DefinedName('NQ_T', attr_text="Regras!$U$5:$U$44")
wb.defined_names['NQ_N'] = DefinedName('NQ_N', attr_text="Regras!$V$5:$V$44")
G.freeze_panes = 'A5'

# ---------------- Dados (Wisesheets) ----------------
D['A1'] = 'Dados do Wisesheets'; D['A1'].font = F_T
D['A2'] = 'Não editar. Cada bloco é uma única chamada para todas as ações.'; D['A2'].font = F_S
head(D, 4, 1, 'Ticker', w=10)
for r in range(R0, R1 + 1): D.cell(r, 1, f'=IF({QA}A{r}="","",{QA}A{r})').font = F_B
TK = f"{QA}$A${R0}:$A${R1}"
CH = 10000   # uma chamada por bloco: no teste do usuário (v4) as 593 linhas carregaram numa chamada só
CHUNKS = [(a, min(a + CH - 1, R1)) for a in range(R0, R1 + 1, CH)]
tk = lambda a, b: f"{QA}$A${a}:$A${b}"
col = [2]; DC = {}


def block(key, field, years, label=None, per_year=False):
    """years: lista de deslocamentos (ex. [-5..-1]); um campo, vários anos, uma chamada."""
    c0 = col[0]; cols = [L(c0 + i) for i in range(len(years))]
    head(D, 3, c0, label or field, color='4B5563')
    D.merge_cells(start_row=3, start_column=c0, end_row=3, end_column=c0 + len(years) - 1)
    for i, y in enumerate(years):
        x = D.cell(4, c0 + i, f'=YEAR(TODAY()){y:+d}'); x.font = F_H; x.fill = fill('6B7280'); x.alignment = Alignment(horizontal='center')
        D.column_dimensions[cols[i]].width = 11
    D.cell(2, c0, field).font = Font(name='Aptos', size=8, color='9CA3AF')   # nome do campo usado na chamada
    for a, b in CHUNKS:
        if per_year:   # uma chamada por ano, como a V2 fazia com as estimativas
            for c in cols:
                D[f'{c}{a}'] = ArrayFormula(f'{c}{a}:{c}{b}', f'=IFERROR(_xldudf_WISE({tk(a, b)},${cols[0]}$2,{c}$4),"")')
        else:
            D[f'{cols[0]}{a}'] = ArrayFormula(f'{cols[0]}{a}:{cols[-1]}{b}', f'=IFERROR(_xldudf_WISE({tk(a, b)},${cols[0]}$2,${cols[0]}$4:${cols[-1]}$4),"")')
    DC[key] = cols; col[0] += len(years) + 1


# nome, setor, indústria, preço e valor de mercado: uma chamada
c0 = col[0]; BASEF = ['Name', 'Sector', 'Industry', 'Price', 'Market Cap', '1y']
head(D, 3, c0, 'Cadastro e preço', color='4B5563'); D.merge_cells(start_row=3, start_column=c0, end_row=3, end_column=c0 + len(BASEF) - 1)
for i, f in enumerate(BASEF):
    x = D.cell(4, c0 + i, f); x.font = F_H; x.fill = fill('6B7280'); D.column_dimensions[L(c0 + i)].width = 16 if i < 3 else 12
for a, b in CHUNKS:
    D[f'{L(c0)}{a}'] = ArrayFormula(f'{L(c0)}{a}:{L(c0 + len(BASEF) - 1)}{b}', f'=IFERROR(_xldudf_WISEPRICE({tk(a, b)},${L(c0)}$4:${L(c0 + len(BASEF) - 1)}$4),"")')
DC['base'] = [L(c0 + i) for i in range(len(BASEF))]; col[0] += len(BASEF) + 1
block('DY', 'Dividend Yield', [-1])
block('EST', 'Estimated EPS AVG', [-1, 0, 1, 2])   # o ano passado entra como base no mesmo critério (ajustado) das estimativas             # consenso do sell-side: ano+1 = ano corrente
block('EPS', 'EPS Diluted', [-9, -8, -7, -6, -5, -4, -3, -2, -1])   # 2017–2025 (histórico longo para o gráfico e a mediana de 5 anos)              # último exercício = ano passado (decisão do usuário: o ano corrente vem vazio em muitas)
Y5 = [-4, -3, -2, -1]
for k, f in (('NI', 'Net Income'), ('OI', 'Operating Income'), ('PT', 'Income Before Tax'), ('TX', 'Income Tax Expense'), ('PPE', 'Property Plant Equipment Net'),
             ('ROU', 'Operating Lease Right Of Use Assets'), ('GW', 'Goodwill'), ('INT', 'Intangible Assets'),
             ('TCA', 'Total Current Assets'), ('CASH', 'Cash And Cash Equivalents'), ('TCL', 'Total Current Liabilities'),
             ('DEBT', 'Total Debt'), ('LEASE', 'Capital Lease Obligations'), ('EQ', 'Total Stockholders Equity')):
    block(k, f, Y5)
D.freeze_panes = 'B5'
NAME, SECT, IND, PRICE, MCAP, CH1Y = (f'{QD}{c}' for c in DC['base'])

# ---------------- Cálculo ----------------
C['A1'] = 'Cálculo'; C['A1'].font = F_T
C['A2'] = 'Contas do modelo, uma linha por ação (mesma linha da aba Ações). Não editar.'; C['A2'].font = F_S
head(C, 4, 1, 'Ticker', w=10)
for r in range(R0, R1 + 1): C.cell(r, 1, f'=IF({QA}A{r}="","",{QA}A{r})').font = F_B
cc = [2]; CC = {}


def cols(key, n, label, group=None, w=9):
    c0 = cc[0]; out = [L(c0 + i) for i in range(n)]
    for i in range(n):
        head(C, 4, c0 + i, label if n == 1 else f'{label} {i + 1}', color='4B5563', w=w)
    if group: C.cell(3, c0, group).font = F_BB
    CC[key] = out if n > 1 else out[0]; cc[0] += n
    return CC[key]


cols('SHE', 1, 'Último EPS já saiu?', 'Ano mais recente'); cols('SHR', 1, 'Último balanço já saiu?')
cols('E', 3, 'EPS estimado c/ haircut', 'Crescimento (consenso)', w=10); cols('GA', 3, 'Cresc. anual estimado c/ haircut'); cols('GR0', 3, 'Cresc. anual do consenso'); cols('GRAW', 1, 'Crescimento sem teto')
cols('GVR', 1, 'Crescimento valuation (bruto)'); cols('GCR', 1, 'Crescimento do consenso (bruto)'); cols('G', 1, 'Crescimento p/ valuation (c/ haircut)'); cols('GC', 1, 'Crescimento do consenso (classe)'); cols('ZG', 1, 'zGrowth'); cols('GH', 5, 'Cresc. histórico', 'Histórico (só conferência)'); cols('GHM', 1, 'Cresc. histórico (mediana)'); cols('GOH', 3, 'Cresc. lucro operacional'); cols('GOM', 1, 'Cresc. operacional (mediana)'); cols('GCAP', 1, 'Teto de credibilidade')
cols('ER', 8, 'Cresc. EPS ano a ano', 'Escadinha'); cols('RUN', 8, 'Sequência de altas'); cols('ESC', 1, 'Nota escadinha'); cols('ATY', 1, 'Consenso atípico?'); cols('ATX', 1, 'Atípico sem apoio operacional?')
cols('STEP', 1, 'Step change?', 'Step change (caso LLY)'); cols('PEJLT', 1, 'P/E justo maduro'); cols('RFADE', 1, 'Retorno com fade'); cols('EDEV', 1, 'EPS 2027 com devolução'); cols('RDEV', 1, 'Retorno com devolução'); cols('SOK', 1, 'Passa no step change?')
cols('GPI', 1, 'Mediana cresc. indústria', 'Indústria'); cols('GAPG', 1, 'Gap de crescimento vs indústria'); cols('PLI', 1, 'P/L ÷ indústria')
cols('RY', 4, 'ROIC do ano', 'Nota de boa empresa'); cols('MEDR', 1, 'ROIC mediano da indústria'); cols('SPR', 1, 'Spread vs pares'); cols('GIMP', 1, 'g implícito no preço'); cols('GSUS', 1, 'g sustentável'); cols('PISTA', 1, 'Pista (g crível − implícito)'); cols('RTAN', 1, 'ROIC sem goodwill'); cols('SHG', 1, 'Variação anual do nº de ações'); cols('ALAV', 1, 'Dívida ÷ lucro operacional')
cols('C1', 1, 'C1 ROIC vs pares'); cols('C2', 1, 'C2 ROIC incremental'); cols('C3', 1, 'C3 Pista marginal'); cols('C4', 1, 'C4 Moat'); cols('C5', 1, 'C5 Gestão por ação'); cols('C6', 1, 'C6 Existir em 15 anos'); cols('C7', 1, 'C7 Qualitativa'); cols('NOTA', 1, 'Nota de boa empresa'); cols('TCOMP', 1, 'Teste de compounder')
cols('PENT', 1, 'Preço de entrada (20%)', 'Oportunidades'); cols('FALTA', 1, 'Falta cair'); cols('CAPG', 1, 'Cresc. capital investido'); cols('COMP', 1, 'Compounder redondo'); cols('QL', 1, 'Quase lá'); cols('PEQ', 1, 'Pequena que compõe'); cols('PAN', 1, 'Ótima em pânico')
cols('FLAG', 1, 'Atenção', w=16)
cols('NOP', 4, 'NOPAT', 'ROIC triangulado (4 anos)', w=11); cols('CA', 4, 'Capital ativo', w=11); cols('CP', 4, 'Capital passivo', w=11)
cols('RA', 4, 'ROIC ativo'); cols('RP', 4, 'ROIC passivo')
for v in 'AP':
    cols(f'N{v}', 1, f'n {v}'); cols(f'MED{v}', 1, f'mediana {v}'); cols(f'SIG{v}', 1, f'σ {v}'); cols(f'DEV{v}', 2, f'desvio {v}'); cols(f'X{v}', 4, f'sem outlier {v}')
cols('VA', 1, 'ROIC ativo'); cols('VP', 1, 'ROIC passivo'); cols('VM', 1, 'ROIC marginal'); cols('TRI', 1, 'ROIC triangulado')
cols('ROE', 4, 'ROE', 'Financeiras'); cols('ROEM', 1, 'ROE (média)'); cols('FIN', 1, 'Usa ROE?')
cols('ROIC', 1, 'ROIC usado', 'Valuation'); cols('FXH', 1, 'Fator US$/ADR (balanço)'); cols('FXE', 1, 'Fator US$/ADR (estimativas)'); cols('PLL', 1, 'P/L LTM'); cols('PLF', 1, 'P/L 1 ano à frente'); cols('PL', 1, 'P/L (média)')
cols('g', 1, 'g do P/E justo'); cols('PEJ', 1, 'P/E justo'); cols('DYv', 1, 'Dividend yield')
cols('RF', 1, 'Ret. P/E justo'); cols('RC', 1, 'Ret. múltiplo constante'); cols('RET', 1, 'Retorno esperado')
cols('P70', 1, 'Cresc. p70 da indústria', 'Cenário bear'); cols('GB', 1, 'Crescimento bear'); cols('MB', 1, 'Múltiplo bear'); cols('RB', 1, 'Retorno bear'); cols('BOK', 1, 'Passa no bear?')
cols('COD', 1, 'Código', 'Classe'); cols('BASE', 1, 'Classe (régua)', w=22); cols('CYC', 1, 'Cíclica'); cols('APP', 1, 'Vestuário'); cols('DUP', 1, 'Repetida')
cols('CLS', 1, 'Classe', w=22); cols('QUAL', 1, 'Qualidade'); cols('HR', 1, 'High ROIC'); cols('HG', 1, 'High Growth'); cols('EXC', 1, 'Excepcional')
cols('SEC', 1, 'Setor', 'Top 20 com limite por setor', w=16); cols('NOTA0', 1, 'Nota (antes do limite)'); cols('RKS', 1, 'Posição no setor')
for k in 'EJ': cols(f'NOTA0{k}', 1, f'Nota {k} (antes do limite)'); cols(f'RKS{k}', 1, f'Posição no setor ({k})')
for k, lab in (('T', 'Top 20'), ('E', 'Especiais'), ('J', 'JG+G')):
    cols(f'NOTA{k}', 1, f'Nota {lab}', lab); cols(f'RK{k}', 1, f'Posição {lab}'); cols(f'S{k}', 1, '√ valor'); cols(f'F{k}', 1, 'no teto?'); cols(f'W0{k}', 1, 'peso bruto'); cols(f'W{k}', 1, f'Peso {lab}'); cols(f'WU{k}', 1, 'peso (ordem)')
    cols(f'WA{k}', 1, 'peso antes do teto de setor'); cols(f'SW{k}', 1, 'peso do setor'); cols(f'WB{k}', 1, 'peso c/ teto de setor'); cols(f'WC{k}', 1, 'peso redistribuído')
cols('JR', 1, 'JG: ROIC'); cols('JGr', 1, 'JG: cresc.'); cols('JP', 1, 'JG: P/L')
cols('SX', 1, '√ valor (Exc.)', 'Excepcionais'); cols('WX', 1, 'Peso Excepcionais'); cols('WXU', 1, 'peso (ordem)')
OPEN = [('O_COMP', 'Compounders'), ('O_QL', 'Quase lá'), ('O_PAN', 'Pânico'), ('O_PEQ', 'Pequenas'), ('O_OOL', 'OoL'), ('O_GCGR', 'GCGR'), ('O_EBF', 'Excellent but Fair'), ('O_CYC', 'Cyclicals'), ('O_HR', 'High ROIC'), ('O_HG', 'High Growth'), ('O_EXC', 'Excepcionais')]
for k, lab in OPEN: cols(k, 1, f'Ordem {lab}', 'Ordem nas listas' if k == 'O_OOL' else None)
C.freeze_panes = 'B5'

def X(key, i, r):
    """i = ano lógico (0 = o mais antigo); se o exercício do ano corrente já saiu, anda uma coluna (como o Python, que usa o último publicado)"""
    if key in ('DY', 'EST') or key == 'base': return f'{QD}{DC[key][i]}{r}'
    return f'{QD}{DC[key][i]}{r}'
cr = lambda key, r: f'{CC[key]}{r}'
crr = lambda key, i, r: f'{CC[key][i]}{r}'
rngr = lambda key, r: f'{CC[key][0]}{r}:{CC[key][-1]}{r}'
col_rg = lambda key: f'${CC[key]}${R0}:${CC[key]}${R1}'


def metric(key, r):
    x = CC[key]; n = len(x); parts = []
    for i in range(n):
        rest = f'COUNT({x[i + 1]}{r}:{x[-1]}{r})' if i < n - 1 else '0'
        parts.append(f'IF(AND(ISNUMBER({x[i]}{r}),{rest}<3),{x[i]}{r},0)')
    rg = rngr(key, r)
    return f'=IF(COUNT({rg})=0,"",(({"+".join(parts)})/MIN(3,COUNT({rg}))+AVERAGE({rg}))/2)'


def rank_desc(key, r, tie=None):
    rg, x = col_rg(key), cr(key, r)
    gt = f'SUMPRODUCT(ISNUMBER({rg})*({rg}>{x}))'
    if tie:
        tg = col_rg(tie)
        eq = f'SUMPRODUCT(ISNUMBER({rg})*({rg}={x})*(({tg}>{cr(tie, r)})+({tg}={cr(tie, r)})*(ROW({rg})<ROW())))'
    else:
        eq = f'SUMPRODUCT(ISNUMBER({rg})*({rg}={x})*(ROW({rg})<ROW()))'
    return f'({gt}+{eq}+1)'



for r in range(R0, R1 + 1):
    w = lambda key, f, fmt=None, i=None: put(C, r, C[f'{(CC[key][i] if i is not None else CC[key])}{r}'].column, f, fmt)
    put(C, r, C[f'{CC["SHE"]}{r}'].column, '=0')
    put(C, r, C[f'{CC["SHR"]}{r}'].column, '=0')
    SH = cr('SHE', r)
    eb = f'{QD}{DC["EST"][0]}{r}'
    BASE_EPS = f'IF(AND(ISNUMBER({eb}),N({eb})>0),{eb},{X("EPS", 8, r)})'   # base: EPS do ano passado no critério do consenso (ajustado); se faltar, o contábil
    # consenso com haircut: ano+1 é o primeiro exercício ainda não publicado
    for j, hc in enumerate(('HAIRCUT_1', 'HAIRCUT_2', 'HAIRCUT_3')):
        e0 = f'{QD}{DC["EST"][j + 1]}{r}'
        w('E', f'=IFERROR({e0}*{hc},"")', '0.00', j)
        if False: pass
    E1, E2, E3 = (crr('E', j, r) for j in range(3))
    for j, (a_, b_) in enumerate(((BASE_EPS, E1), (E1, E2), (E2, E3))):
        w('GA', f'=IFERROR(IF(AND(ISNUMBER({a_}),ISNUMBER({b_})),IF({a_}>0,{b_}/{a_}-1,""),""),"")', PCT0, j)
    b0 = BASE_EPS
    # crescimento = MEDIANA dos 3 crescimentos anuais do consenso (2025→26, 26→27, 27→28): um ano atípico, para cima ou para baixo,
    # não contamina (decisão do usuário, 2026-11-22; mesma lógica da mediana histórica do modelo testado)
    R1_, R2_, R3_ = (f'{QD}{DC["EST"][j + 1]}{r}' for j in range(3))
    for j, (a_, b_) in enumerate(((b0, R1_), (R1_, R2_), (R2_, R3_))):
        w('GR0', f'=IFERROR(IF(AND(ISNUMBER({a_}),ISNUMBER({b_})),IF({a_}>0,{b_}/{a_}-1,""),""),"")', PCT0, j)
    gr0, gah = rngr('GR0', r), rngr('GA', r)
    w('GRAW', f'=IF(COUNT({gah})>=2,MEDIAN({gah}),"")', PCT)
    w('GVR', f'=IF(ISNUMBER({cr("GRAW", r)}),MIN(G_MAX,{cr("GRAW", r)}),"")', PCT)
    w('GCR', f'=IF(COUNT({gr0})>=2,MIN(G_MAX,MEDIAN({gr0})),"")', PCT)
    # credibilidade: o crescimento usado não passa do maior histórico (EPS 5 anos ou lucro operacional) + margem (regra de acompanhamento, 22/11)
    for j in range(3):
        a_, b_ = X('OI', j, r), X('OI', j + 1, r)
        w('GOH', f'=IF(AND(ISNUMBER({a_}),ISNUMBER({b_})),IF({a_}>0,{b_}/{a_}-1,""),"")', PCT0, j)
    goh = rngr('GOH', r)
    w('GOM', f'=IF(COUNT({goh})>=2,MEDIAN({goh}),"")', PCT)
    gcap = cr('GCAP', r)
    w('GCAP', f'=IF(OR(ISNUMBER({cr("GHM", r)}),ISNUMBER({cr("GOM", r)})),MAX(IF(ISNUMBER({cr("GHM", r)}),{cr("GHM", r)},-9),IF(ISNUMBER({cr("GOM", r)}),{cr("GOM", r)},-9))+CRED_MARGEM,"")', PCT)
    w('G', f'=IF(ISNUMBER({cr("GVR", r)}),IF(ISNUMBER({gcap}),MIN({cr("GVR", r)},{gcap}),{cr("GVR", r)}),"")', PCT)
    w('GC', f'=IF(ISNUMBER({cr("GCR", r)}),IF(ISNUMBER({gcap}),MIN({cr("GCR", r)},{gcap}),{cr("GCR", r)}),"")', PCT)
    Gv = cr('G', r)          # com haircut: P/E justo e retorno esperado
    Gc = cr('GC', r)         # consenso puro: classe, filtros e listas
    ga = rngr('GA', r)
    # zGrowth: dispersão dos 2 crescimentos mais próximos da mediana (o ano atípico não conta, como na mediana)
    md = f'MEDIAN({gr0})'
    w('ZG', (f'=IFERROR(IF(N({Gc})=0,"",IF(COUNT({gr0})=3,MIN({md}-MIN({gr0}),MAX({gr0})-{md})/2/ABS({Gc}),'
             f'IF(COUNT({gr0})=2,_xlfn.STDEV.P({gr0})/ABS({Gc}),""))),"")'), NUM2)
    for i in range(5):   # os 5 últimos crescimentos (2021–2025), como a mediana do modelo testado
        a_, b_ = X('EPS', i + 3, r), X('EPS', i + 4, r)
        w('GH', f'=IF(AND(ISNUMBER({a_}),ISNUMBER({b_})),IF({a_}>0,{b_}/{a_}-1,""),"")', PCT0, i)
    gh = rngr('GH', r)
    w('GHM', f'=IF(COUNT({gh})>=3,MEDIAN({gh}),"")', PCT)
    GH = cr('GHM', r)
    for i in range(8):
        a_, b_ = X('EPS', i, r), X('EPS', i + 1, r)
        w('ER', f'=IF(AND(ISNUMBER({a_}),ISNUMBER({b_})),IF({a_}>0,{b_}/{a_}-1,""),"")', PCT0, i)
        prev = crr('RUN', i - 1, r) if i else '0'
        w('RUN', f'=IF(N({crr("ER", i, r)})>0,{prev}+1,0)', '0', i)
    er = rngr('ER', r)
    w('ESC', (f'=IFERROR(IF(COUNT({er})>=6,IF(MEDIAN({er})>0,40*COUNTIF({er},">0")/COUNT({er})+20*MAX({rngr("RUN", r)})/COUNT({er})'
              f'+20*IF(MIN({er})>-0.1,1,0)+20*MAX(0,1-MIN(1,_xlfn.STDEV.P({er})/MEDIAN({er})/1.5)),0),""),"")'), '0')
    w('ATY', f'=IFERROR(IF(MAX(MAX({gr0})-{md},{md}-MIN({gr0}))>MAX(0.3,ABS({md})),1,0),0)')
    w('ATX', f'=IF(AND({cr("ATY", r)}=1,NOT(AND(ISNUMBER({cr("GOM", r)}),N({cr("GOM", r)})>=N({cr("GCR", r)})-CRED_MARGEM))),1,0)')
    w('FLAG', (f'=IF({QA}A{r}="","",IF(NOT(ISNUMBER({Gc})),"Sem estimativa",_xlfn.TEXTJOIN(" · ",TRUE,'
               f'IF(N({cr("GCR", r)})>N({cr("GC", r)})+0.0001,"Consenso cortado pela história",""),'
               f'IF(N({cr("GRAW", r)})>G_MAX,"Crescimento limitado ao teto",""),IF(N({b0})<=0,"Lucro negativo no último ano",""),IF({cr("ATX", r)}=1,"Consenso atípico sem apoio operacional",""),IF({cr("SOK", r)}=0,"Step change: devolução abaixo de "&TEXT(-STEP_MIN,"0%"),""),IF(AND(N({cr("GAPG", r)})>0.3,N({cr("PLI", r)})>3),"Preço e crescimento muito acima da indústria",""))))'))
    # ROIC triangulado leve (4 anos)
    for j in range(4):
        pt, tx = X('PT', j, r), X('TX', j, r)
        tr = f'IF(AND(ISNUMBER({pt}),ISNUMBER({tx})),IF({pt}>0,MIN(MAX({tx}/{pt},0),0.5),0.21),0.21)'
        w('NOP', f'=IF(ISNUMBER({X("OI", j, r)}),({X("OI", j, r)}+N({X("LEASE", j, r)})*0.05)*(1-{tr}),"")', '#,##0,,', j)
        w('CA', f'=IF(AND(ISNUMBER({X("PPE", j, r)}),ISNUMBER({X("TCA", j, r)}),ISNUMBER({X("TCL", j, r)})),{X("PPE", j, r)}+N({X("ROU", j, r)})+N({X("GW", j, r)})+N({X("INT", j, r)})'
                f'+{X("TCA", j, r)}-N({X("CASH", j, r)})-{X("TCL", j, r)},"")', '#,##0,,', j)
        w('CP', f'=IF(ISNUMBER({X("EQ", j, r)}),{X("EQ", j, r)}+N({X("DEBT", j, r)})+N({X("LEASE", j, r)})-N({X("CASH", j, r)}),"")', '#,##0,,', j)
    for v, cap in (('A', 'CA'), ('P', 'CP')):
        for j in range(4):
            c1 = crr(cap, j, r); nop = crr('NOP', j, r)
            cvl = f'IF(ISNUMBER({crr(cap, j - 1, r)}),({c1}+{crr(cap, j - 1, r)})/2,{c1})' if j > 0 else c1
            w(f'R{v}', f'=IF(AND(ISNUMBER({nop}),ISNUMBER({c1})),IF({cvl}>0,{nop}/{cvl},""),"")', PCT0, j)
        ser = rngr(f'R{v}', r); nn, md, sg = cr(f'N{v}', r), cr(f'MED{v}', r), cr(f'SIG{v}', r)
        w(f'N{v}', f'=COUNT({ser})')
        w(f'MED{v}', f'=IF({nn}>=4,MEDIAN({ser}),"")', PCT0)
        C[sg] = ArrayFormula(sg, f'=IF({nn}>=4,MAX(1.4826*MEDIAN(IF(ISNUMBER({ser}),ABS({ser}-{md}))),0.25*ABS({md}),0.02),"")'); C[sg].number_format = PCT0
        for i in range(2):   # só os 2 anos mais antigos podem sair
            xv = crr(f'R{v}', i, r)
            w(f'DEV{v}', f'=IF(AND({nn}>=4,ISNUMBER({xv})),IF(ABS({xv}-{md})>3*{sg},ABS({xv}-{md}),-1),-1)', NUM2, i)
        for i in range(4):
            xv = crr(f'R{v}', i, r)
            if i >= 2:
                w(f'X{v}', f'=IF(ISNUMBER({xv}),{xv},"")', PCT0, i); continue
            di, dj = crr(f'DEV{v}', i, r), crr(f'DEV{v}', 1 - i, r)
            ahead = f'({dj}>{di})' if i == 0 else f'({dj}>={di})'
            w(f'X{v}', f'=IF(NOT(ISNUMBER({xv})),"",IF({di}<0,{xv},IF(1+{ahead}<={nn}-3,"",{xv})))', PCT0, i)
    w('VA', metric('XA', r), PCT); w('VP', metric('XP', r), PCT)
    n3, n0, a3, a0 = crr('NOP', 3, r), crr('NOP', 0, r), crr('CA', 3, r), crr('CA', 0, r)
    w('VM', f'=IF(AND(ISNUMBER({n3}),ISNUMBER({n0}),ISNUMBER({a3}),ISNUMBER({a0})),IF({a3}-{a0}>0,({n3}-{n0})/({a3}-{a0}),""),"")', PCT)
    A_, P_, M_ = cr('VA', r), cr('VP', r), cr('VM', r)
    va, vp, vm = (f'AND(ISNUMBER({x}),N({x})>=0,N({x})<=2)' for x in (A_, P_, M_))
    ca, cp = f'MIN(N({A_}),1.5)', f'MIN(N({P_}),1.5)'
    w('TRI', (f'=IF(AND({va},{vp}),IF(AND(MIN({ca},{cp})>0,MAX({ca},{cp})<=2*MIN({ca},{cp})),({ca}+{cp})/2,'
              f'IF({vm},IF(ABS({ca}-{M_})<=ABS({cp}-{M_}),{ca},{cp}),MIN({ca},{cp}))),'
              f'IF({va},{ca},IF({vp},{cp},IF(OR(N({A_})>2,N({P_})>2),1.5,IF(OR(ISNUMBER({A_}),ISNUMBER({P_})),MAX(IF(ISNUMBER({A_}),{A_},-9),IF(ISNUMBER({P_}),{P_},-9)),IF({vm},MIN(N({M_}),1.5),""))))))'), PCT)
    for j in range(4):
        w('ROE', f'=IF(AND(ISNUMBER({X("NI", j, r)}),N({X("EQ", j, r)})>0),{X("NI", j, r)}/{X("EQ", j, r)},"")', PCT0, j)
    w('ROEM', metric('ROE', r), PCT)
    w('FIN', f'=IF(OR({SECT}{r}="Financial Services",COUNTIF(ROE_TICKERS,{QA}A{r})>0),1,0)')
    FIN = cr('FIN', r)
    w('ROIC', f'=IF({FIN}=1,{cr("ROEM", r)},{cr("TRI", r)})', PCT)
    RO, PL = cr('ROIC', r), cr('PL', r)
    e1raw = f'{QD}{DC["EST"][1]}{r}'
    tk_ = f'{QA}A{r}'
    fxu = f'IFERROR(INDEX(FX_V,MATCH(INDEX(ADR_M,MATCH({tk_},ADR_T,0)),FX_M,0))*INDEX(ADR_N,MATCH({tk_},ADR_T,0)),1)'
    w('FXH', f'={fxu}', '0.000')
    fxo = f'IFERROR(INDEX(FX_V,MATCH(INDEX(ADR_M,MATCH({tk_},ADR_T,0)),FX_M,0)),1)'   # só o câmbio (estimativa já vem por ADR)
    w('FXE', f'=IF(IFERROR(INDEX(ADR_E,MATCH({tk_},ADR_T,0)),"Sim")="Não",1,IF(IFERROR(INDEX(ADR_E,MATCH({tk_},ADR_T,0)),"Sim")="Só câmbio",{fxo},{cr("FXH", r)}))', '0.000')
    FH, FE = cr('FXH', r), cr('FXE', r)
    bus = f'IF(AND(ISNUMBER({eb}),N({eb})>0),{eb}*{FE},{X("EPS", 8, r)}*{FH})'   # EPS-base em dólar por ADR
    w('PLL', f'=IFERROR(IF({bus}<>0,{PRICE}{r}/({bus}),""),"")', NUM1)
    w('PLF', f'=IFERROR(IF({e1raw}<>0,{PRICE}{r}/({e1raw}*{FE}),""),"")', NUM1)
    l_, f_ = cr('PLL', r), cr('PLF', r)   # média só quando os dois são positivos; com prejuízo num deles, usa o outro (média de P/L negativo com positivo não faz sentido)
    w('PL', f'=IF(AND(N({l_})>0,N({f_})>0),({l_}+{f_})/2,IF(N({f_})>0,{f_},IF(N({l_})>0,{l_},IF(COUNT({l_},{f_})=0,"",N({l_})))))', NUM1)
    grg, frg = col_rg('G'), col_rg('FIN')
    Gc_class = Gc; Gc = Gv
    w('g', (f'=IF(ISNUMBER({Gc}),(G_TOPO-{FIN}*G_FIN)-SUMPRODUCT(ISNUMBER({grg})*({grg}>{Gc})*({frg}={FIN}))*(G_TOPO-G_PISO)'
            f'/MAX(1,SUMPRODUCT(ISNUMBER({grg})*({frg}={FIN}))-1),"")'), PCT)
    gg = cr('g', r)
    w('PEJ', f'=IFERROR(IF(N({RO})>0,(1-{gg}/MIN(1,{RO}))/(WACC-{gg}),""),"")', NUM1)
    w('DYv', f'=N({X("DY", 0, r)})', PCT)
    PE, DY = cr('PEJ', r), cr('DYv', r)
    w('RF', f'=IFERROR(IF({PE}*{E2}*{FE}/{PRICE}{r}>0,SQRT({PE}*{E2}*{FE}/{PRICE}{r})-1+{DY},""),"")', PCT)
    w('RC', f'=IF(ISNUMBER({Gc}),{Gc}+{DY},"")', PCT)
    w('RET', f'=IF(AND(ISNUMBER({cr("RF", r)}),ISNUMBER({cr("RC", r)})),({cr("RF", r)}+{cr("RC", r)})/2,IF(ISNUMBER({Gc}),{Gc},""))', PCT)
    # cenário bear: cresce o menor entre o próprio e o maior entre (p70 da indústria, 70% do próprio, 6%); múltiplo = menor entre 80% do justo e o atual
    gvr, indr = col_rg('G'), f'{QD}${DC["base"][2]}${R0}:${DC["base"][2]}${R1}'
    w('P70', f'=IFERROR(_xlfn.AGGREGATE(16,6,{gvr}/({indr}={IND}{r}),BEAR_PCTL),"")', PCT)
    w('GB', f'=IF(ISNUMBER({Gv}),MIN({Gv},MAX(N({cr("P70", r)}),BEAR_CORTE*{Gv},BEAR_GMIN)),"")', PCT)
    w('MB', f'=IF(AND(ISNUMBER({cr("PEJ", r)}),N({PL})>0),MIN(BEAR_MULT*{cr("PEJ", r)},{PL}),"")', NUM1)
    w('RB', f'=IFERROR(IF(ISNUMBER({cr("MB", r)}),IF({cr("MB", r)}*({bus})*(1+{cr("GB", r)})^2/{PRICE}{r}>0,SQRT({cr("MB", r)}*({bus})*(1+{cr("GB", r)})^2/{PRICE}{r})-1+{DY},-1),""),"")', PCT)
    w('BOK', f'=IF(ISNUMBER({cr("RB", r)}),IF({cr("RB", r)}>BEAR_MIN,1,0),1)')   # só informativo (o filtro bear não passou no backtest, 22/11)
    # step change (caso LLY): EPS 2028 ≥ 1,8 × 2025 → múltiplo de saída com g maduro e cenário de devolução de 1/3 do ganho até 2027
    w('STEP', f'=IF(AND(N({b0})>0,N({R3_})>0),IF({R3_}/{b0}>=STEP_X,1,0),0)')
    w('PEJLT', f'=IFERROR(IF(N({RO})>0,(1-STEP_G/MIN(1,{RO}))/(WACC-STEP_G),""),"")', NUM1)
    mlt = f'MIN({cr("PEJ", r)},{cr("PEJLT", r)})'
    w('RFADE', f'=IF({cr("STEP", r)}=1,IFERROR(IF({mlt}*{E2}*{FE}/{PRICE}{r}>0,SQRT({mlt}*{E2}*{FE}/{PRICE}{r})-1+{DY},-1),""),"")', PCT)
    w('EDEV', f'=IF({cr("STEP", r)}=1,IFERROR(IF({E2}>{b0},{E2}-({E2}-{b0})/3,{E2}),""),"")', '0.00')
    w('RDEV', f'=IF({cr("STEP", r)}=1,IFERROR(IF({mlt}*{cr("EDEV", r)}*{FE}/{PRICE}{r}>0,SQRT({mlt}*{cr("EDEV", r)}*{FE}/{PRICE}{r})-1+{DY},-1),""),"")', PCT)
    w('SOK', f'=IF({cr("STEP", r)}=1,IF(N({cr("RDEV", r)})>STEP_MIN,1,0),1)')
    gcr_ = col_rg('GC'); plr_ = col_rg('PL')
    w('GPI', f'=IFERROR(_xlfn.AGGREGATE(16,6,{gcr_}/({indr}={IND}{r}),0.5),"")', PCT)
    w('GAPG', f'=IF(AND(ISNUMBER({Gc}),ISNUMBER({cr("GPI", r)})),{Gc}-{cr("GPI", r)},"")', PCT)
    w('PLI', f'=IFERROR(IF(N({PL})>0,{PL}/_xlfn.AGGREGATE(16,6,{plr_}/(({indr}={IND}{r})*({plr_}>0)),0.5),""),"")', NUM2)
    # preço de entrada: o preço em que o retorno esperado chega ao corte (20%)
    kk = f'{cr("PEJ", r)}*{E2}*{FE}'; den = f'(1+2*RET_ALTO-N({cr("RC", r)})-{DY})'
    w('PENT', f'=IFERROR(IF(AND(N({cr("PEJ", r)})>0,{den}>0,{kk}>0,ISNUMBER({cr("RC", r)})),{kk}/{den}^2,""),"")', '#,##0.00')
    w('FALTA', f'=IFERROR(IF(ISNUMBER({cr("PENT", r)}),{cr("PENT", r)}/{PRICE}{r}-1,""),"")', PCT0)
    w('CAPG', f'=IFERROR(IF(AND(N({crr("CA", 0, r)})>0,N({crr("CA", 3, r)})>0),({crr("CA", 3, r)}/{crr("CA", 0, r)})^(1/3)-1,""),"")', PCT)
    # ---- Nota de boa empresa (framework v4.2 do usuário; base McKinsey: valor = (ROIC − custo de capital) × crescimento) ----
    for j in range(4):
        w('RY', f'=IF({FIN}=1,IF(ISNUMBER({crr("ROE", j, r)}),{crr("ROE", j, r)},""),IF(ISNUMBER({crr("RA", j, r)}),{crr("RA", j, r)},IF(ISNUMBER({crr("RP", j, r)}),{crr("RP", j, r)},"")))', PCT0, j)
    ry = rngr('RY', r); rur = col_rg('ROIC')
    w('MEDR', f'=IFERROR(_xlfn.AGGREGATE(16,6,{rur}/({indr}={IND}{r}),0.5),"")', PCT)
    w('SPR', f'=IF(AND(ISNUMBER({RO}),ISNUMBER({cr("MEDR", r)})),{RO}-{cr("MEDR", r)},"")', PCT)
    w('C1', (f'=IF(ISNUMBER({cr("SPR", r)}),IF(OR({RO}<WACC+0.1,{RO}<1.5*{cr("MEDR", r)}),MIN(3,1+4*_xlfn.PERCENTRANK.INC({col_rg("SPR")},{cr("SPR", r)})),'
             f'1+4*_xlfn.PERCENTRANK.INC({col_rg("SPR")},{cr("SPR", r)})),"")'), NUM1)
    vm = cr('VM', r)
    w('C2', f'=IF(NOT(ISNUMBER({vm})),3,IF(AND({vm}>=0.8*N({RO}),{vm}>=WACC),5,IF({vm}>=0.5*N({RO}),4,IF({vm}>=WACC,3,IF({vm}>=0,2,1)))))', '0')
    r1_ = f'MIN(1,MAX(0.000001,N({RO})))'
    w('GIMP', f'=IFERROR(IF(N({PL})>0,(WACC*{PL}-1)/({PL}-1/{r1_}),""),"")', PCT)
    w('GSUS', (f'=IFERROR(IF(AND(N({crr("CA", 0, r)})>0,ISNUMBER({crr("CA", 3, r)}),SUM({crr("NOP", 1, r)}:{crr("NOP", 3, r)})>0),'
               f'MAX(0,MIN(0.3,({crr("CA", 3, r)}-{crr("CA", 0, r)})/SUM({crr("NOP", 1, r)}:{crr("NOP", 3, r)})*MIN(N({RO}),IF(ISNUMBER({vm}),MAX(0,{vm}),N({RO}))))),""),"")'), PCT)
    gcred = f'MIN(N({Gc}),IF(ISNUMBER({cr("GSUS", r)}),{cr("GSUS", r)},N({Gc})),0.15)'
    w('PISTA', f'=IF(AND(ISNUMBER({Gc}),ISNUMBER({cr("GIMP", r)})),{gcred}-{cr("GIMP", r)},"")', PCT)
    pi = cr('PISTA', r)
    w('C3', f'=IF(N({PL})<=0,1,IF(AND(N({PL})>0,{PL}<1/{r1_}),5,IF(NOT(ISNUMBER({pi})),3,IF({pi}>=0.05,5,IF({pi}>=0.02,4,IF({pi}>=0,3,IF({pi}>=-0.03,2,1)))))))', '0')
    w('RTAN', f'=IFERROR(IF(({crr("CA", 3, r)}-N({X("GW", 3, r)})-N({X("INT", 3, r)}))>0,{crr("NOP", 3, r)}/({crr("CA", 3, r)}-N({X("GW", 3, r)})-N({X("INT", 3, r)})),""),"")', PCT0)
    allr = lambda th: f'COUNTIF({ry},">="&{th})=COUNT({ry})'
    w('C4', (f'=IF(COUNT({ry})<2,3,MIN(5,IF(AND({allr("0.2")},MIN({ry})>=0.7*AVERAGE({ry})),5,IF({allr("0.15")},4,IF({allr("WACC")},3,IF(COUNTIF({ry},">="&WACC)>COUNT({ry})/2,2,1))))'
             f'+IF(N({cr("RTAN", r)})>=0.4,1,0)))'), '0')
    sh0 = f'{X("NI", 0, r)}/{X("EPS", 5, r)}'; sh3 = f'{X("NI", 3, r)}/{X("EPS", 8, r)}'
    w('SHG', f'=IFERROR(IF(AND(({sh0})>0,({sh3})>0),(({sh3})/({sh0}))^(1/3)-1,""),"")', PCT)
    gwr = f'IFERROR((N({X("GW", 3, r)})+1)/(N({X("GW", 0, r)})+1),1)'; oir = f'IFERROR(IF(AND(N({X("OI", 0, r)})>0,N({X("OI", 3, r)})>0),{X("OI", 3, r)}/{X("OI", 0, r)},""),"")'
    w('C5', (f'=MAX(1,MIN(5,3+IF(N({cr("SHG", r)})<=-0.01,1,0)-IF(N({cr("SHG", r)})>=0.02,1,0)+IF(ISNUMBER({oir}),IF({gwr}<={oir},1,IF({gwr}>1.2*{oir},-1,0)),0)))'), '0')
    w('ALAV', f'=IFERROR(IF(N({X("OI", 3, r)})>0,N({X("DEBT", 3, r)})/{X("OI", 3, r)},""),"")', NUM1)
    epsr = f'{QD}{DC["EPS"][0]}{r}:{QD}{DC["EPS"][-1]}{r}'
    w('C6', (f'=IF({CY}=1,1,1+IF(AND(COUNT({epsr})>=6,MIN({epsr})>0),1,0)+IF(OR({FIN}=1,AND(ISNUMBER({cr("ALAV", r)}),N({cr("ALAV", r)})<=2)),1,0)'
             f'+IF(N({cr("ESC", r)})>=ESC_MIN,1,0)+IF(N({MCAP}{r})>=10E9,1,0))'), '0')
    w('C7', f'=IFERROR(INDEX(NQ_N,MATCH({QA}A{r},NQ_T,0))*1,"")', '0')
    w('NOTA', f'=IF({QA}A{r}="","",AVERAGE({cr("C1", r)},{cr("C2", r)},{cr("C3", r)},{cr("C4", r)},{cr("C5", r)},{cr("C6", r)},{cr("C7", r)}))', NUM1)
    w('TCOMP', f'=IF(AND(N({cr("RTAN", r)})>=0.3,COUNTIF({goh},">=0.1")>=2),1,0)')
    Gc = Gc_class
    RT, ZG = cr('RET', r), cr('ZG', r)
    w('COD', (f'=IF(AND(ISNUMBER({Gc}),ISNUMBER({ZG}),ISNUMBER({RO}),ISNUMBER({RT})),IF({Gc}>G_ALTO,"H",IF({Gc}>=G_BAIXO,"O","L"))&IF({ZG}<ZG,"O","P")'
              f'&IF({RO}>ROIC_ALTO,"G",IF({RO}>=ROIC_BAIXO,"O","L"))&"N"&IF({RT}>RET_ALTO,"G",IF({RT}>=RET_BAIXO,"O","B")),"")'))
    w('BASE', f'=IF({QA}A{r}="","",IF({cr("COD", r)}="","Sem dados",IFERROR(INDEX(COD_CLASSE,MATCH({cr("COD", r)},COD,0)),"Do not Waste Time")))')
    w('CYC', f'=IF(AND(COUNTIF(CICLICAS,{IND}{r})>0,COUNTIF(NAO_CICLICAS,{QA}A{r})=0),1,0)')
    w('APP', f'=IF(COUNTIF(VESTUARIO,{IND}{r})>0,1,0)')
    mo = f'OR(AND(N({cr("PLL", r)})>0,N({cr("PLL", r)})<2),AND(N({cr("PLF", r)})>0,N({cr("PLF", r)})<2))'   # EPS em outra moeda (ADR): fora das listas
    xm = f'COUNTIF(EXCLUIR,{QA}A{r})>0'
    w('DUP', (f'=IF(OR(AND({QA}A{r}<>"",COUNTIF({QA}$A${R0}:A{r},{QA}A{r})>1),{mo},{xm}),1,0)' if r > R0 else f'=IF(OR({mo},{xm}),1,0)'))
    B_, CY, AP, DU = cr('BASE', r), cr('CYC', r), cr('APP', r), cr('DUP', r)
    w('CLS', f'=IF({xm},"Excluída (manual)",IF({mo},"Moeda diferente (fora)",IF({cr("ATX", r)}=1,"Consenso atípico (fora)",IF(OR({B_}="{OOL}",{B_}="{GCGR}"),IF({CY}=1,"Cyclicals",IF({AP}=1,"Excluída (vestuário)",IF(AND({B_}="{OOL}",{cr("SOK", r)}=0),"OoL reprovada no step change",{B_}))),{B_}))))')
    CL = cr('CLS', r)
    w('QUAL', f'=IF(AND({DU}=0,{CY}=0,{AP}=0,{cr("COD", r)}<>"",N({RO})>=ROIC_ALTO,N({Gc})>=G_ALTO,{cr("ATX", r)}=0,{cr("SOK", r)}=1),1,0)')
    Q = cr('QUAL', r)
    w('HR', f'=IF(AND({DU}=0,{CL}="{OOL}",N({RO})>HR_CORTE),1,0)')
    w('HG', f'=IF(AND({DU}=0,{CL}="{OOL}",N({Gc})>HG_CORTE),1,0)')
    w('EXC', f'=IF(AND({Q}=1,N({RO})>HR_CORTE,N({Gc})>HG_CORTE),1,0)')
    w('SEC', f'=IF({SECT}{r}="","",{SECT}{r})')
    w('NOTA0', f'=IF(AND({Q}=1,N({PL})>=PL_MIN),{RT},"")', PCT)
    n0c, srg, nrg, rrg = cr('NOTA0', r), col_rg('SEC'), col_rg('NOTA0'), col_rg('ROIC')
    w('RKS', (f'=IF(ISNUMBER({n0c}),1+SUMPRODUCT(({srg}={cr("SEC", r)})*ISNUMBER({nrg})*(({nrg}>{n0c})+({nrg}={n0c})*(({rrg}>{RO})+({rrg}={RO})*(ROW({nrg})<ROW())))),"")'))
    w('NOTAT', f'=IF(AND(ISNUMBER({n0c}),N({cr("RKS", r)})<=CAP_SETOR),{n0c},"")', PCT)
    # Especiais: retorno > 20%; primeiro as que têm ROIC > 30% e crescimento > 30%; depois as demais pela nota 1,5 × ROIC + g (decisão do usuário, 2026-11-22)
    w('NOTA0E', f'=IF(AND({Q}=1,N({RT})>RET_ALTO),IF(AND({RO}>HR_CORTE,{Gc}>HG_CORTE),10,0)+1.5*MIN({RO},1.5)+{Gc},"")', NUM2)
    el = f'AND({FIN}=0,{SECT}{r}<>"Utilities",{CY}=0,{AP}=0,{DU}=0,{cr("ATX", r)}=0,{cr("SOK", r)}=1,N({PL})>0,ISNUMBER({RO}),ISNUMBER({Gc}),N({X("OI", 3, r)})>0)'
    w('JR', f'=IF({el},{RO},"")'); w('JGr', f'=IF({el},{Gc},"")'); w('JP', f'=IF({el},{PL},"")')
    w('NOTA0J', (f'=IF(ISNUMBER({cr("JR", r)}),-(_xlfn.RANK.AVG({cr("JR", r)},{col_rg("JR")},0)+_xlfn.RANK.AVG({cr("JGr", r)},{col_rg("JGr")},0)'
                f'+_xlfn.RANK.AVG({cr("JP", r)},{col_rg("JP")},1)),"")'))
    for k in 'EJ':   # mesmo limite de ações por setor da Top 20 (sem ele, o teto de 40% pode ficar impossível de cumprir)
        n0, nr = cr(f'NOTA0{k}', r), col_rg(f'NOTA0{k}')
        tie = f'(({rrg}>{RO})+({rrg}={RO})*(ROW({nr})<ROW()))' if k == 'E' else f'(ROW({nr})<ROW())'
        w(f'RKS{k}', f'=IF(ISNUMBER({n0}),1+SUMPRODUCT(({srg}={cr("SEC", r)})*ISNUMBER({nr})*(({nr}>{n0})+({nr}={n0})*{tie})),"")')
        w(f'NOTA{k}', f'=IF(AND(ISNUMBER({n0}),N({cr(f"RKS{k}", r)})<=CAP_SETOR),{n0},"")', NUM2)
    for k in 'TEJ':
        rd = rank_desc(f'NOTA{k}', r, None if k == 'J' else 'ROIC')
        w(f'RK{k}', f'=IF(ISNUMBER({cr(f"NOTA{k}", r)}),IF({rd}<=N_LISTA,{rd},""),"")')
        s_, f_, w0, sr, fr, w0r = cr(f'S{k}', r), cr(f'F{k}', r), cr(f'W0{k}', r), col_rg(f'S{k}'), col_rg(f'F{k}'), col_rg(f'W0{k}')
        w(f'S{k}', f'=IF(ISNUMBER({cr(f"RK{k}", r)}),SQRT(MAX(N({MCAP}{r}),1)),"")', '#,##0')
        tot = f'SUM({sr})'; big = f'SUMPRODUCT(ISNUMBER({sr})*({sr}>{s_}),{sr})'; kk = f'SUMPRODUCT(ISNUMBER({sr})*({sr}>{s_}))'
        w(f'F{k}', f'=IF(ISNUMBER({s_}),IF({tot}-{big}>0,(1-{kk}*TETO)*{s_}/({tot}-{big})>TETO+1E-12,TRUE),"")')
        w(f'W0{k}', f'=IF(ISNUMBER({s_}),IF({f_},TETO,(1-COUNTIF({fr},TRUE)*TETO)*{s_}/({tot}-SUMIF({fr},TRUE,{sr}))),"")', PCT)
        # teto de peso por setor (40%) em todas as carteiras de 20: as melhores do setor ficam, com o peso reduzido; o excesso vai para os outros setores
        wa, sw, wb_ = cr(f'WA{k}', r), cr(f'SW{k}', r), cr(f'WB{k}', r)
        war, swr, wbr, scr = col_rg(f'WA{k}'), col_rg(f'SW{k}'), col_rg(f'WB{k}'), col_rg('SEC')
        w(f'WA{k}', f'=IF(ISNUMBER({w0}),{w0}/SUM({w0r}),"")', PCT)
        w(f'SW{k}', f'=IF(ISNUMBER({wa}),SUMIF({scr},{cr("SEC", r)},{war}),"")', PCT)
        w(f'WB{k}', f'=IF(ISNUMBER({wa}),IF({sw}>CAP_PESO_SETOR,{wa}*CAP_PESO_SETOR/{sw},{wa}),"")', PCT)
        capd = f'SUMPRODUCT(ISNUMBER({wbr})*({swr}>CAP_PESO_SETOR),{wbr})'; free = f'SUMPRODUCT(ISNUMBER({wbr})*({swr}<=CAP_PESO_SETOR),{wbr})'
        w(f'WC{k}', f'=IFERROR(IF(ISNUMBER({wb_}),IF({sw}>CAP_PESO_SETOR,{wb_},{wb_}*(1-{capd})/{free}),""),"")', PCT)
        wc, wcr = cr(f'WC{k}', r), col_rg(f'WC{k}')
        over = f'(SUMIF({wcr},">"&TETO)-TETO*COUNTIF({wcr},">"&TETO))'
        room = f'SUMPRODUCT(ISNUMBER({wcr})*({wcr}<TETO)*({swr}<=CAP_PESO_SETOR),{wcr})'
        w(f'W{k}', f'=IFERROR(IF(ISNUMBER({wc}),IF({wc}>TETO,TETO,IF({sw}<=CAP_PESO_SETOR,{wc}*(1+{over}/{room}),{wc})),""),"")', PCT)
        w(f'WU{k}', f'=IF(ISNUMBER({cr(f"W{k}", r)}),{cr(f"W{k}", r)}+ROW()*1E-12,"")', PCT)
    w('SX', f'=IF({cr("EXC", r)}=1,SQRT(MAX(N({MCAP}{r}),1)),"")', '#,##0')
    w('WX', f'=IF(ISNUMBER({cr("SX", r)}),{cr("SX", r)}/SUM({col_rg("SX")}),"")', PCT)
    w('WXU', f'=IF(ISNUMBER({cr("WX", r)}),{cr("WX", r)}+ROW()*1E-12,"")', PCT)
    rr_ = col_rg('RET')
    ok_ = f'AND({DU}=0,{CY}=0,{AP}=0,{cr("ATX", r)}=0,{cr("SOK", r)}=1)'; NT = cr('NOTA', r)
    w('COMP', f'=IF(AND({ok_},N({MCAP}{r})>=COMP_MC,N({NT})>=4,ISNUMBER({RT})),1,0)')
    w('QL', f'=IF(AND({cr("COMP", r)}=1,N({RT})<RET_ALTO,ISNUMBER({cr("FALTA", r)}),N({cr("FALTA", r)})>=QL_FALTA),1,0)')
    w('PEQ', f'=IF(AND({ok_},N({MCAP}{r})>=PEQ_MIN,N({MCAP}{r})<=PEQ_MAX,N({NT})>=4,N({Gc})>=0.12,N({PL})>0,N({PL})<=1.3*N({cr("PEJ", r)}),ISNUMBER({RT})),1,0)')
    w('PAN', f'=IF(AND({DU}=0,{CY}=0,{AP}=0,{cr("ATX", r)}=0,N({NT})>=3.5,ISNUMBER({CH1Y}{r}),N({CH1Y}{r})<=PANICO,N({crr("ER", 7, r)})>0,N({Gc})>0),1,0)')
    for k, v in (('O_COMP', f'IF({cr("COMP", r)}=1,{RT},"")'), ('O_QL', f'IF({cr("QL", r)}=1,{cr("FALTA", r)},"")'),
                 ('O_PEQ', f'IF({cr("PEQ", r)}=1,{RT},"")'), ('O_PAN', f'IF({cr("PAN", r)}=1,-{CH1Y}{r},"")')):
        w(k, f'=IFERROR({v}+ROW()*1E-12,"")', PCT)
    for k, cond in (('O_OOL', f'{CL}="{OOL}"'), ('O_GCGR', f'{CL}="{GCGR}"'), ('O_EBF', f'{CL}="Excellent but Fair"'), ('O_CYC', f'{CL}="Cyclicals"'), ('O_HR', f'{cr("HR", r)}=1'),
                    ('O_HG', f'{cr("HG", r)}=1'), ('O_EXC', f'{cr("EXC", r)}=1')):
        crg = col_rg(k)
        # posição pelo retorno esperado entre as da mesma lista (o filtro da lista vem da própria coluna: só quem tem número)
        w(k, f'=IF(AND({DU}=0,{cond},ISNUMBER({RT})),{RT}+ROW()*1E-12,"")', PCT)

# as colunas de ordem guardam o retorno; a posição é calculada no Painel com LARGE (sem duplicar conta)

# ---------------- Ações ----------------
A['A1'] = 'Ações'; A['A1'].font = F_T
A['A2'] = 'Digite os tickers na coluna A (formato do Wisesheets). O resto se preenche sozinho.'; A['A2'].font = F_S
AC = [('Ticker', 10, None), ('Empresa', 26, None), ('Setor', 18, None), ('Indústria', 24, None), ('Preço', 9, '#,##0.00'), ('Valor de mercado (US$ bi)', 11, '#,##0'),
      ('P/L', 7, NUM1), ('Crescimento', 10, PCT), ('ROIC', 9, PCT), ('P/E justo', 8, NUM1), ('Retorno esperado', 10, PCT), ('Classe', 26, None),
      ('Listas', 30, None), ('Atenção', 24, None), ('Cresc. histórico', 10, PCT), ('zGrowth', 8, NUM2), ('Bagger #', 8, '0')]
for i, (h, wd, f) in enumerate(AC): head(A, 4, i + 1, h, w=wd)
A.row_dimensions[4].height = 32
for r in range(R0, R1 + 1):
    t = TICK[r - R0] if r - R0 < len(TICK) else None
    x = A.cell(r, 1, t); x.font = F_BB; x.fill = fill('FFF4C2')
    blank = f'{QA}A{r}=""'.replace(QA, '')
    vals = [f'=IF({NAME}{r}="","",{NAME}{r})', f'=IF({SECT}{r}="","",{SECT}{r})', f'=IF({IND}{r}="","",{IND}{r})', f'=IF({PRICE}{r}="","",{PRICE}{r})',
            f'=IFERROR(IF({MCAP}{r}="","",{MCAP}{r}/1E9),"")', f'={QC}{cr("PL", r)}', f'={QC}{cr("GC", r)}', f'={QC}{cr("ROIC", r)}', f'={QC}{cr("PEJ", r)}',
            f'={QC}{cr("RET", r)}', f'={QC}{cr("CLS", r)}',
            (f'=_xlfn.TEXTJOIN(" · ",TRUE,IF(ISNUMBER({QC}{cr("RKT", r)}),"Top 20 #"&{QC}{cr("RKT", r)},""),IF(ISNUMBER({QC}{cr("RKE", r)}),"Especiais",""),'
             f'IF({QC}{cr("EXC", r)}=1,"Excepcional",""),IF({QC}{cr("HR", r)}=1,"High ROIC",""),IF({QC}{cr("HG", r)}=1,"High Growth",""),'
             f'IF(ISNUMBER({QC}{cr("RKJ", r)}),"JG+G",""))'),
            f'={QC}{cr("FLAG", r)}', f'={QC}{cr("GHM", r)}', f'={QC}{cr("ZG", r)}',
            f"=IFERROR(INDEX('Bagger Rank'!$B$5:$B$400,MATCH(A{r},'Bagger Rank'!$A$5:$A$400,0)),\"\")"]
    for i, v in enumerate(vals):
        x = A.cell(r, i + 2, v); x.font = F_B; x.border = thin
        if AC[i + 1][2]: x.number_format = AC[i + 1][2]
    A.cell(r, 14).font = Font(name='Aptos', size=10, color='B42318', bold=True)
A.freeze_panes = 'B5'; A.auto_filter.ref = f'A4:{L(len(AC))}{R1}'
CLS_COLORS = [(OOL, ACC['ool']), (GCGR, ACC['gcgr']), ('Cyclicals', ACC['cyc']), ('Excluída (vestuário)', '9CA3AF'), ('Sem dados', 'D1D5DB')]
for nm_, colr in CLS_COLORS:
    A.conditional_formatting.add(f'L{R0}:L{R1}', FormulaRule(formula=[f'$L{R0}="{nm_}"'], fill=fill(colr), font=Font(color='FFFFFF' if nm_ not in ('Sem dados',) else INK, bold=True)))

# ---------------- Painel ----------------
P['A1'] = 'Price Tracker'; P['A1'].font = Font(name='Aptos Display', bold=True, size=24, color=INK)
P['A2'] = '=" Atualizado em "&TEXT(TODAY(),"dd/mm/")&YEAR(TODAY())&" · "&COUNTA(' + f"{QA}A{R0}:A{R1}" + ')&" ações · regras na aba Regras"'; P['A2'].font = F_S
P.column_dimensions['A'].width = 4
CL_RG, RT_RG, TK_RG = f"{QC}{col_rg('CLS')}", f"{QC}{col_rg('RET')}", f"{QA}$A${R0}:$A${R1}"
kpis = [('Compounders redondos', f'=SUM({QC}{col_rg("COMP")})', '0B6E4F'), ('Quase lá', f'=SUM({QC}{col_rg("QL")})', '1F6E8C'),
        ('Ótima em pânico', f'=SUM({QC}{col_rg("PAN")})', 'B42318'), ('Pequenas que compõem', f'=SUM({QC}{col_rg("PEQ")})', '7A5C00'),
        ('Opportunity of Lifetime', f'=COUNTIFS({CL_RG},"{OOL}",{QC}{col_rg("DUP")},0)', ACC['ool']), ('Excepcionais', f'=SUM({QC}{col_rg("EXC")})', ACC['exc'])]
for i, (lab, f, colr) in enumerate(kpis):
    c = [3, 12, 21, 30, 39, 48][i]   # colunas de cada bloco
    x = P.cell(4, c, f); x.font = Font(name='Aptos Display', bold=True, size=22, color=colr)
    y = P.cell(5, c, lab); y.font = Font(name='Aptos', size=9, color=MUTED, bold=True)
TKc = lambda m: f'IFERROR(INDEX({TK_RG},{m}),"")'


NAMES = f"'Ações'!$B${R0}:$B${R1}"
DESC_FONT = Font(name='Aptos', size=9, italic=True, color=MUTED)


COLS = ['#', 'Ação', 'Empresa', 'Indústria', 'Valor (US$ bi)', 'Peso', 'Nota', 'ROIC', 'Cresc.', 'Cresc. hist.', 'Escad.', 'P/L', 'P/E justo', 'Retorno', 'Falta cair', 'Bagger', '⚠']
FMT = [None, None, None, None, '#,##0', PCT, NUM1, PCT0, PCT0, PCT0, '0', NUM1, NUM1, PCT0, PCT0, '0', None]
WID = [4, 9, 24, 22, 8, 7, 6, 7, 7, 8, 6, 7, 8, 8, 8, 7, 3]
NW = len(COLS)


def header(r0, c0, title, colr, desc, show_peso):
    P.merge_cells(start_row=r0 - 1, start_column=c0, end_row=r0 - 1, end_column=c0 + NW - 1)
    d = P.cell(r0 - 1, c0, desc); d.font = DESC_FONT; d.alignment = Alignment(wrap_text=True, vertical='bottom')
    P.merge_cells(start_row=r0, start_column=c0, end_row=r0, end_column=c0 + NW - 1)
    x = P.cell(r0, c0, title); x.font = Font(name='Aptos', bold=True, size=12, color='FFFFFF'); x.fill = fill(colr)
    for j, h in enumerate(COLS):
        if h == 'Peso' and not show_peso: continue
        y = P.cell(r0 + 1, c0 + j, h); y.font = Font(name='Aptos', size=9, bold=True, color=MUTED); y.border = thin


def row_vals(m, wcol):
    """mesmas colunas em todas as listas: ação, empresa, peso, ROIC, crescimento, P/L atual, P/E justo, retorno, bagger, alerta"""
    g = lambda key: f'=IFERROR(INDEX({QC}{col_rg(key)},{m}),"")'
    return [None, f'={TKc(m)}', f'=IFERROR(INDEX({NAMES},{m}),"")', f"=IFERROR(INDEX('Ações'!$D${R0}:$D${R1},{m}),\"\")", f"=IFERROR(INDEX('Ações'!$F${R0}:$F${R1},{m}),\"\")", g(wcol) if wcol else None, g('NOTA'), g('ROIC'), g('GC'), g('GHM'), g('ESC'), g('PL'), g('PEJ'),
            f'=IFERROR(INDEX({RT_RG},{m}),"")', f'=IFERROR(IF(INDEX({QC}{col_rg("FALTA")},{m})<0,INDEX({QC}{col_rg("FALTA")},{m}),""),"")', f"=IFERROR(INDEX('Ações'!$Q${R0}:$Q${R1},{m}),\"\")",
            f'=IFERROR(IF(INDEX({QC}{col_rg("FLAG")},{m})<>"","⚠",""),"")']


def write_row(r, c0, k_formula, vals):
    vals[0] = k_formula
    for j, v in enumerate(vals):
        if v is None: continue
        x = P.cell(r, c0 + j, v); x.font = F_BB if j == 1 else F_B; x.border = thin
        x.number_format = FMT[j] or 'General'
        if j == NW - 1: x.font = Font(name='Aptos', size=10, bold=True, color='B42318')
        if j == 0: x.alignment = Alignment(horizontal='center'); x.font = F_S


def ranked(r0, c0, title, colr, wk, desc, n=20):
    """lista com peso (Top 20, Especiais, JG+G), ORDENADA PELO PESO"""
    header(r0, c0, title, colr, desc, True)
    wur = f"{QC}{col_rg('WU' + wk[1:])}"
    for k in range(1, n + 1):
        write_row(r0 + 1 + k, c0, k, row_vals(f'MATCH(LARGE({wur},{k}),{wur},0)', wk))
    P.cell(r0 + n + 2, c0 + 4, 'Soma').font = F_S  # noqa
    P.cell(r0 + n + 2, c0 + 5, f'=SUM({L(c0 + 5)}{r0 + 2}:{L(c0 + 5)}{r0 + n + 1})').number_format = PCT0


def opened(r0, c0, title, colr, ok, desc, n=40, wsort=None, wcol=None):
    """lista aberta: pelo peso quando tem (Excepcionais), senão pelo retorno esperado"""
    header(r0, c0, title, colr, desc, bool(wcol))
    key = f"{QC}{col_rg(wsort or ok)}"
    for k in range(1, n + 1):
        write_row(r0 + 1 + k, c0, f'=IFERROR(IF(ISNUMBER(LARGE({key},{k})),{k},""),"")', row_vals(f'MATCH(LARGE({key},{k}),{key},0)', wcol))


DESC = {
    'top': 'As 20 de maior retorno esperado entre as de qualidade (ROIC ≥ 12%, crescimento ≥ 15%, P/L ≥ 4, sem cíclicas). Peso pela raiz do valor de mercado, teto de 10% por ação e de 40% por setor (as melhores do setor ficam, com peso menor).',
    'esp': 'Retorno esperado > 20% e bear > −10%. Primeiro as com ROIC > 30% e crescimento > 30%; completa até 20 pela maior nota 1,5 × ROIC + crescimento. Mesmo peso e tetos da Top 20 (10% por ação, 40% por setor).',
    'jg': 'Fórmula Mágica com crescimento: soma das posições em ROIC, crescimento e P/L (menor é melhor). Sem financeiras, utilities e cíclicas.',
    'ool': 'Classe Opportunity of Lifetime: crescimento > 15%, ROIC > 12% e retorno esperado > 20%. Ordem: retorno esperado.',
    'hr': 'Opportunity of Lifetime com ROIC acima de 30%. Ordem: retorno esperado.',
    'hg': 'Opportunity of Lifetime com crescimento acima de 30%. Ordem: retorno esperado.',
    'exc': 'Qualidade com ROIC > 30% e crescimento > 30% ao mesmo tempo. Peso pela raiz do valor de mercado. Ordem: peso.',
    'gcgr': 'Good Companies, Great Returns: boas empresas com retorno esperado alto, um degrau abaixo da OoL. Ordem: retorno esperado.',
    'ebf': 'Excellent but Fair: empresas ótimas (crescimento e ROIC altos, crescimento estável), mas o retorno esperado ficou entre 8% e 20%. Ordem: retorno esperado.',
    'comp': 'Grandes (≥ US$ 50 bi) com Nota de boa empresa ≥ 4 (ROIC vs pares, ROIC incremental, pista, moat, gestão por ação, existir em 15 anos). Ordem: retorno esperado. Falta cair = queda até o retorno chegar a 20%.',
    'ql': 'Compounders redondos com retorno esperado abaixo de 20%, a no máximo 30% de queda do preço de entrada. Ordem: os mais perto de entrar.',
    'pan': 'Nota ≥ 3,5, ação caiu 25% ou mais em 12 meses e o lucro do último ano subiu: o mercado em pânico com uma empresa que segue entregando. Ordem: maior queda.',
    'peq': 'US$ 2–30 bi, Nota ≥ 4, crescimento ≥ 12% e P/L até 1,3× o justo: as que podem ficar muito grandes. Ordem: retorno esperado.',
    'cyc': 'Seriam OoL ou GCGR, mas estão num subsetor cíclico (lista na aba Regras). Ficam fora das carteiras. Ordem: retorno esperado.'}
B0 = (2, 20, 38)
RA_, RB_ = 8, 8 + 44
for (k, title, colr, dk), c0 in zip([('O_COMP', 'Compounders redondos', '0B6E4F', 'comp'), ('O_QL', 'Quase lá', '1F6E8C', 'ql'),
                                     ('O_PAN', 'Ótima em pânico', 'B42318', 'pan')], B0):
    opened(RA_, c0, title, colr, k, DESC[dk], n=40)
ranked(RB_, B0[0], 'Top 20 · a carteira (máx. 40% por setor)', ACC['top'], 'WT', DESC['top'])
ranked(RB_, B0[1], 'Especiais · as 20 mais excepcionais (máx. 40% por setor)', ACC['esp'], 'WE', DESC['esp'])
ranked(RB_, B0[2], 'JG+G · Fórmula Mágica com crescimento (máx. 40% por setor)', ACC['jg'], 'WJ', DESC['jg'])
R2, R3, R4 = RB_ + 26, RB_ + 26 + 44, RB_ + 26 + 88
R5 = RB_ + 26 + 132
for (r0, c0), (k, title, colr, dk, ws, wc) in zip([(R2, B0[0]), (R2, B0[1]), (R2, B0[2]), (R3, B0[0]), (R3, B0[1]), (R3, B0[2]), (R4, B0[0]), (R4, B0[1])],
        [('O_PEQ', 'Pequenas que compõem', '7A5C00', 'peq', None, None),
         ('O_OOL', 'Opportunity of Lifetime', ACC['ool'], 'ool', None, None), ('O_GCGR', 'Good Companies, Great Returns', ACC['gcgr'], 'gcgr', None, None),
         ('O_EBF', 'Excellent but Fair', '1F6E8C', 'ebf', None, None),
         ('O_HR', 'High ROIC', ACC['hr'], 'hr', None, None), ('O_HG', 'High Growth', ACC['hg'], 'hg', None, None),
         ('O_EXC', 'Excepcionais', ACC['exc'], 'exc', 'WXU', 'WX')]):
    opened(r0, c0, title, colr, k, DESC[dk], wsort=ws, wcol=wc)
opened(R4, B0[2], 'Cyclicals', ACC['cyc'], 'O_CYC', DESC['cyc'])
for c0 in B0:
    for j, wd in enumerate(WID): P.column_dimensions[L(c0 + j)].width = wd
    P.column_dimensions[L(c0 + NW)].width = 3
for r0 in (RA_ - 1, RB_ - 1, R2 - 1, R3 - 1, R4 - 1): P.row_dimensions[r0].height = 36
P.sheet_view.showGridLines = False

# ---------------- Carteira ----------------
K['A1'] = 'Minha carteira'; K['A1'].font = F_T
K['A2'] = 'Digite os tickers da carteira na coluna A. Eles precisam estar também na aba Ações.'; K['A2'].font = F_S
KC = [('Ticker', 10), ('Empresa', 26), ('Classe', 26), ('Listas', 30), ('Retorno esperado', 10), ('ROIC', 9), ('Crescimento', 10), ('P/L', 7), ('Atenção', 16), ('Bagger #', 8)]
for i, (h, wd) in enumerate(KC): head(K, 4, i + 1, h, w=wd)
for i in range(30):
    r = 5 + i; t = CART[i] if i < len(CART) else None
    x = K.cell(r, 1, t); x.font = F_BB; x.fill = fill('FFF4C2')
    m = f'MATCH(A{r},{TK_RG},0)'
    src = {2: 'B', 3: 'L', 4: 'M', 5: 'K', 6: 'I', 7: 'H', 8: 'G', 9: 'N', 10: 'Q'}
    for c, sc in src.items():
        x = K.cell(r, c, f'=IF(A{r}="","",IFERROR(INDEX({QA}${sc}${R0}:${sc}${R1},{m}),"não está na aba Ações"))'); x.font = F_B; x.border = thin
        x.number_format = {5: PCT, 6: PCT, 7: PCT, 8: NUM1}.get(c, 'General')
K.freeze_panes = 'B5'
for nm_, colr in CLS_COLORS:
    K.conditional_formatting.add('C5:C34', FormulaRule(formula=[f'$C5="{nm_}"'], fill=fill(colr), font=Font(color='FFFFFF' if nm_ != 'Sem dados' else INK, bold=True)))

# ---------------- Bagger Rank (da V2, editável) ----------------
BG['A1'] = 'Bagger Rank'; BG['A1'].font = F_T
BG['A2'] = 'Informação de qualidade (não entra na regra). Edite à vontade.'; BG['A2'].font = F_S
head(BG, 4, 1, 'Ticker', w=12); head(BG, 4, 2, 'Posição', w=10)
for i, (t, rk) in enumerate(BAGGER):
    x = BG.cell(5 + i, 1, t); x.font = F_BB; x.fill = fill('FFF4C2'); y = BG.cell(5 + i, 2, rk); y.font = F_B; y.fill = fill('FFF4C2')
BG.freeze_panes = 'A5'

# ---------------- Histórico (carteira-sombra) ----------------
H['A1'] = 'Histórico da Top 20'; H['A1'].font = F_T
H['A2'] = 'A cada trimestre: copie o bloco "Hoje" e cole COMO VALORES na primeira linha vazia da tabela de baixo.'; H['A2'].font = F_S
H['H4'] = 'S&P 500 (SPY) hoje'; H['H4'].font = F_BB
H['I4'] = '=IFERROR(_xldudf_WISEPRICE("SPY","Price"),"")'; H['I4'].number_format = '#,##0.00'
for j, (h, wd) in enumerate([('Data', 11), ('Ticker', 10), ('Peso', 8), ('Preço', 10), ('SPY', 10)]): head(H, 4, 1 + j, h, color=ACC['top'], w=wd)
H.cell(3, 1, 'Hoje').font = F_BB
for k in range(1, 21):
    r = 4 + k; m = f"MATCH({k},{QC}{col_rg('RKT')},0)"
    vals = ['=TODAY()', f'=IFERROR(INDEX({TK_RG},{m}),"")', f'=IFERROR(INDEX({QC}{col_rg("WT")},{m}),"")',
            f"=IFERROR(INDEX('Ações'!$E${R0}:$E${R1},{m}),\"\")", '=$I$4']
    for j, v in enumerate(vals):
        x = H.cell(r, 1 + j, v); x.font = F_B; x.number_format = ['dd/mm/yyyy', 'General', PCT, '#,##0.00', '#,##0.00'][j]
T0 = 28
H.cell(T0 - 1, 1, 'Registro (cole aqui, como valores)').font = F_BB
for j, (h, wd) in enumerate([('Data', 11), ('Ticker', 10), ('Peso', 8), ('Preço de entrada', 10), ('SPY na entrada', 10), ('Preço hoje', 10), ('Retorno', 9), ('Contribuição', 10)]):
    head(H, T0, 1 + j, h, w=wd)
for r in range(T0 + 1, T0 + 801):
    H.cell(r, 6, f"=IF(B{r}=\"\",\"\",IFERROR(INDEX('Ações'!$E${R0}:$E${R1},MATCH(B{r},{TK_RG},0)),\"\"))").number_format = '#,##0.00'
    H.cell(r, 7, f'=IF(OR(B{r}="",NOT(ISNUMBER(F{r}))),"",F{r}/D{r}-1)').number_format = PCT
    H.cell(r, 8, f'=IF(ISNUMBER(G{r}),C{r}*G{r},"")').number_format = PCT
    for c in (1, 3, 4, 5): H.cell(r, c).number_format = ['dd/mm/yyyy', None, PCT, '#,##0.00', '#,##0.00'][[1, 2, 3, 4, 5].index(c)] or 'General'
RG_ = lambda c: f'${c}${T0 + 1}:${c}${T0 + 800}'
for j, (h, wd) in enumerate([('Carteira de', 11), ('Retorno da carteira', 11), ('S&P 500 no período', 11), ('Diferença', 10)]): head(H, T0, 11 + j, h, color=ACC['top'], w=wd)
for i in range(40):
    r = T0 + 1 + i
    H.cell(r, 11, f'=IFERROR(MIN({RG_("A")}),"")' if i == 0 else f'=IFERROR(IF(_xlfn.MINIFS({RG_("A")},{RG_("A")},">"&K{r - 1})=0,"",_xlfn.MINIFS({RG_("A")},{RG_("A")},">"&K{r - 1})),"")').number_format = 'dd/mm/yyyy'
    if i == 0: H.cell(r, 11).value = f'=IF(COUNT({RG_("A")})=0,"",MIN({RG_("A")}))'
    H.cell(r, 12, f'=IF(K{r}="","",IFERROR(SUMIFS({RG_("H")},{RG_("A")},K{r})/SUMIFS({RG_("C")},{RG_("A")},K{r}),""))').number_format = PCT
    H.cell(r, 13, f'=IF(K{r}="","",IFERROR($I$4/AVERAGEIFS({RG_("E")},{RG_("A")},K{r})-1,""))').number_format = PCT
    H.cell(r, 14, f'=IF(AND(ISNUMBER(L{r}),ISNUMBER(M{r})),L{r}-M{r},"")').number_format = PCT
H.freeze_panes = 'A5'

for ws, colr in ((P, '0F4C81'), (A, '0B6E4F'), (K, '0B6E4F'), (H, '0F4C81'), (BG, 'C9A227'), (G, 'C9A227'), (C, '9CA3AF'), (D, '9CA3AF')):
    ws.sheet_properties.tabColor = colr
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)

# matriz dinâmica (spill) como na V2: cm="1" + metadata.xml
tmp = OUT.with_suffix('.tmp.xlsx'); shutil.move(OUT, tmp)
with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for nm in zi.namelist():
        data = zi.read(nm)
        if nm.startswith('xl/worksheets/sheet'):
            data = re.sub(rb'<c (r="[A-Z]+\d+"[^>]*?)>(<f t="array")', rb'<c \1 cm="1">\2', data)
        elif nm == '[Content_Types].xml':
            data = data.replace(b'</Types>', b'<Override PartName="/xl/metadata.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml"/></Types>')
        elif nm == 'xl/_rels/workbook.xml.rels':
            data = data.replace(b'</Relationships>', b'<Relationship Id="rIdMeta1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata" Target="metadata.xml"/></Relationships>')
        zo.writestr(nm, data)
    zo.writestr('xl/metadata.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><metadata xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:xda="http://schemas.microsoft.com/office/spreadsheetml/2017/dynamicarray"><metadataTypes count="1"><metadataType name="XLDAPR" minSupportedVersion="120000" copy="1" pasteAll="1" pasteValues="1" merge="1" splitFirst="1" rowColShift="1" clearFormats="1" clearComments="1" assign="1" coerce="1" cellMeta="1"/></metadataTypes><futureMetadata name="XLDAPR" count="1"><bk><extLst><ext uri="{bdbb8cdc-fa1e-496e-a857-3c3f30c029c3}"><xda:dynamicArrayProperties fDynamic="1" fCollapsed="0"/></ext></extLst></bk></futureMetadata><cellMetadata count="1"><bk><rc t="1" v="0"/></bk></cellMetadata></metadata>')
tmp.unlink()
json.dump({'DC': DC, 'CC': CC, 'R0': R0, 'R1': R1}, open(str(OUT) + '.cols.json', 'w'))
n_pts = sum(len(v) for v in DC.values()) * (R1 - R0 + 1) + 1
print('ok', OUT, 'linhas', R0, R1, 'números pedidos ~', n_pts, 'chamadas', sum(len(v) if k == 'EST' else 1 for k, v in DC.items()) * len(CHUNKS) + 1)
