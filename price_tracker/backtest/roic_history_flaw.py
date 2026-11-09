"""Historico anual de ROIC das empresas que cairam de Opportunity of Lifetime para Good Companies, Great Returns
pelo defeito "ROIC medio" (EUA: 10%-20%; Brasil: 10%-17%). Saida: backtest/roic_historico_roic_medio.xlsx
Uso: python3 backtest/roic_history_flaw.py"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import diag_two_countries as dg  # noqa: E402
import engine  # noqa: E402
from backtest import load_pit, asof, D as DUS  # noqa: E402

YEARS = list(range(2009, 2026))
GCGR = dg.GCGR


def flaw_positions(c):
    g = c[(c.cat == GCGR)].copy()
    g = g[g.code.map(lambda s: next((i for i in range(4) if s[i] != 'HOGNG'[i]), None)) == 2]  # ROIC medio
    return g.groupby('ticker').agg(trimestres=('date', 'size'), primeira=('date', 'min'), ultima=('date', 'max'),
                                   roic_modelo_mediano=('roic', 'median'), retorno_medio_trim=('rq', 'mean'))


def roic_us(tk, fin):
    pit = load_pit(tk)
    if pit is None: return {}
    t = pd.Timestamp('2026-11-08')
    s = {k: asof(pit.get(k, []), t)[0] for k in ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income', 'ppe', 'assets_cur', 'cur_liab', 'debt_cur')}
    g = lambda k, y: s[k][y][0] if y in s[k] else None
    out = {}
    for y in YEARS:
        if fin:
            ni, eq = g('net_income', y), g('equity', y)
            if ni is not None and eq and eq > 0: out[y] = ni / eq
            continue
        oi, eq = g('op_income', y), g('equity', y)
        if oi is None or eq is None: continue
        pt, tx = g('pretax', y), g('tax', y)
        tr = min(max(tx / pt, 0), 0.5) if pt and tx is not None and pt > 0 else 0.21
        ic = engine.invested_capital(eq, g('lt_debt', y), g('cash', y), g('ppe', y), g('assets_cur', y), g('cur_liab', y), g('debt_cur', y))[0]
        if ic > 0: out[y] = oi * (1 - tr) / ic
    return out


def roic_br(cvm, fin, fund):
    f = fund[fund.CD_CVM == cvm].sort_values(['DT_REFER', 'VERSAO']).groupby('DT_REFER').tail(1)
    out = {}
    for _, x in f.iterrows():
        y = x.DT_REFER.year
        if y not in YEARS: continue
        if fin:
            if pd.notna(x.ni) and x.equity > 0: out[y] = x.ni / x.equity
            continue
        if pd.isna(x.ebit) or pd.isna(x.equity): continue
        tr = min(max(-x.tax / x.pretax, 0), 0.5) if pd.notna(x.tax) and pd.notna(x.pretax) and x.pretax > 0 else 0.34
        ic = engine.invested_capital(x.equity, x.debt, x.cash, x.get('ppe'), x.get('ac'), x.get('cl'), x.get('debt_cur'))[0]
        if ic > 0: out[y] = x.ebit * (1 - tr) / ic
    return out


def main():
    sheets = {}
    # EUA
    c, adj = dg.us(); c = dg.enrich(c, adj)
    p = flaw_positions(c)
    u = pd.read_csv(DUS / 'universe.csv').set_index('ticker')
    rows = []
    for tk, r in p.iterrows():
        h = roic_us(tk, bool(u.fin.get(tk, False)))
        rows.append({'Ticker': tk, 'Empresa': u['name'].get(tk), 'Setor': u.sector.get(tk), 'Financeira (ROE)': bool(u.fin.get(tk, False)),
                     'Trimestres em GCGR por ROIC médio': r.trimestres, 'Primeiro': r.primeira.date(), 'Último': r.ultima.date(),
                     'ROIC do modelo (mediana)': r.roic_modelo_mediano, 'Retorno médio por trimestre': r.retorno_medio_trim,
                     **{str(y): h.get(y) for y in YEARS}})
    sheets['EUA (corte 20%)'] = pd.DataFrame(rows).sort_values('Trimestres em GCGR por ROIC médio', ascending=False)
    # Brasil
    c, adj = dg.br(); c = dg.enrich(c, adj)
    p = flaw_positions(c)
    ub = pd.read_csv(ROOT.parent / 'brasil/data/universe.csv').set_index('yf')
    fund = pd.read_csv(ROOT.parent / 'brasil/data/fund.csv.gz', parse_dates=['DT_REFER'])
    rows = []
    for tk, r in p.iterrows():
        h = roic_br(int(ub.Codigo_CVM[tk]), bool(ub.fin[tk]), fund)
        rows.append({'Ticker': tk.replace('.SA', ''), 'Empresa': ub.Nome_Empresarial[tk], 'Setor': ub.Setor_Atividade[tk], 'Financeira (ROE)': bool(ub.fin[tk]),
                     'Trimestres em GCGR por ROIC médio': r.trimestres, 'Primeiro': r.primeira.date(), 'Último': r.ultima.date(),
                     'ROIC do modelo (mediana)': r.roic_modelo_mediano, 'Retorno médio por trimestre': r.retorno_medio_trim,
                     **{str(y): h.get(y) for y in YEARS}})
    sheets['Brasil (corte 17%)'] = pd.DataFrame(rows).sort_values('Trimestres em GCGR por ROIC médio', ascending=False)
    out = ROOT / 'roic_historico_roic_medio.xlsx'
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name, index=False)
            ws = w.sheets[name]
            for col in ws.iter_cols(min_row=2):
                h = ws.cell(1, col[0].column).value
                if h in [str(y) for y in YEARS] + ['ROIC do modelo (mediana)', 'Retorno médio por trimestre']:
                    for cell in col: cell.number_format = '0.0%'
            for i, wdt in enumerate([10, 38, 26, 10, 12, 11, 11, 12, 12] + [8] * len(YEARS), start=1):
                ws.column_dimensions[ws.cell(1, i).column_letter].width = wdt
            ws.freeze_panes = 'C2'
    for name, df in sheets.items():
        print(name, len(df)); print(df[['Ticker', 'Empresa', 'Trimestres em GCGR por ROIC médio', 'ROIC do modelo (mediana)'] + [str(y) for y in range(2017, 2026)]].round(3).to_string(index=False))


if __name__ == '__main__':
    main()
