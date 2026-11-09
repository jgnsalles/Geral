"""Fase 1 do protocolo: compara tres definicoes de ROIC por criterios de validade economica (sem olhar retorno).
 (A) atual: NOPAT / (patrimonio + divida - caixa); capital operacional quando patrimonio <= 0 ou o valor <= 0
 (B) operacional com aquisicoes: NOPAT / media do ano de [imobilizado + agio + intangiveis + (ativo circulante - caixa)
     - (passivo circulante - divida de curto prazo)]
 (C) marginal de 5 anos: (NOPAT_t - NOPAT_t-5) / (capital B_t - capital B_t-5), quando o capital cresceu
Financeiras: ROE nas tres. Dados mais recentes de cada exercicio (SEC).
Saidas: backtest/roic_definicoes.md e backtest/roic_definicoes_amostra.xlsx
Uso: python3 backtest/roic_definitions.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import load_pit, asof, D  # noqa: E402

YEARS = list(range(2010, 2026))
KEYS = ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income', 'ppe', 'assets_cur', 'cur_liab', 'debt_cur', 'goodwill', 'intangibles')
SAMPLE = ['MSFT', 'AAPL', 'NVDA', 'GOOG', 'META', 'AMZN', 'ANET', 'DOCS', 'MANH', 'VEEV', 'FICO', 'MSCI', 'MAR', 'HLT', 'ABBV', 'PM',
          'MCD', 'AZO', 'DPZ', 'HD', 'ORLY', 'COST', 'WMT', 'JNJ', 'UNP', 'CAT', 'DE', 'LULU', 'KO', 'BKNG', 'TXN', 'CPRT', 'MCK', 'V']
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
n2 = lambda x: '—' if pd.isna(x) else f'{x:.2f}'.replace('.', ',')


def series(tk, fin, now):
    pit = load_pit(tk)
    if pit is None: return None
    s = {k: asof(pit.get(k, []), now)[0] for k in KEYS}
    g = lambda k, y: s[k][y][0] if y in s[k] else None
    rows = []
    for y in YEARS:
        r = {'ticker': tk, 'year': y, 'fin': fin}
        if fin:
            ni, eq = g('net_income', y), g('equity', y)
            v = ni / eq if ni is not None and eq and eq > 0 else np.nan
            r.update(A=v, B=v, nopat=ni, icB=eq)
            rows.append(r); continue
        oi, eq = g('op_income', y), g('equity', y)
        if oi is None:
            rows.append(r); continue
        pt, tx = g('pretax', y), g('tax', y)
        tr = min(max(tx / pt, 0), 0.5) if pt and tx is not None and pt > 0 else 0.21
        nopat = oi * (1 - tr)
        icA = engine.invested_capital(eq, g('lt_debt', y), g('cash', y), g('ppe', y), g('assets_cur', y), g('cur_liab', y), g('debt_cur', y))[0] if eq is not None else np.nan
        ac, cl, ppe = g('assets_cur', y), g('cur_liab', y), g('ppe', y)
        icB = np.nan
        if ac is not None and cl is not None and ppe is not None:
            icB = ppe + (g('goodwill', y) or 0) + (g('intangibles', y) or 0) + (ac - (g('cash', y) or 0)) - (cl - (g('debt_cur', y) or 0))
        r.update(nopat=nopat, icA=icA, icB=icB, A=nopat / icA if icA and icA > 0 else np.nan)
        rows.append(r)
    df = pd.DataFrame(rows)
    if df.empty or 'icB' not in df: return df
    if not fin:
        avg = (df.icB + df.icB.shift(1)) / 2
        cap = avg.where(avg.notna(), df.icB)
        df['B'] = np.where(cap > 0, df.nopat / cap, np.nan)
    d_n, d_c = df.nopat - df.nopat.shift(5), df.icB - df.icB.shift(5)
    df['C'] = np.where(d_c > 0, d_n / d_c, np.nan)
    return df


def main():
    u = pd.read_csv(D / 'universe.csv')
    now = pd.Timestamp('2026-11-08')
    parts = [series(r.ticker, bool(r.fin), now) for r in u.itertuples()]
    df = pd.concat([p for p in parts if p is not None and not p.empty], ignore_index=True)
    df = df[df.year >= 2012]
    op = df[~df.fin.astype(bool) & df.nopat.notna()]
    out = ['# Fase 1: definições de ROIC — critérios de validade econômica\n',
           '> ⚠️ **ROIC:** escolha feita sem olhar retorno, como pré-registrado no PROTOCOLO.md.\n',
           '(A) atual: patrimônio + dívida − caixa (capital operacional se ≤ 0). (B) operacional com ágio e intangíveis, capital médio do ano. '
           '(C) marginal de 5 anos sobre o capital de (B). Empresas operacionais do universo (S&P 500 atual + planilha), exercícios 2012–2025.\n',
           '## 1. Distribuição e valores absurdos\n',
           '| Critério | (A) atual | (B) operacional + aquisições | (C) marginal 5 anos |', '|---|---|---|---|']
    stats = {}
    for k in 'ABC':
        v = op[k]
        stats[k] = dict(cob=v.notna().mean(), med=v.median(), p10=v.quantile(.1), p90=v.quantile(.9),
                        neg=(v < 0).sum() / v.notna().sum(), hi=(v > 1).sum() / v.notna().sum(), absurd=((v < 0) | (v > 1) | v.isna()).mean())
    rows = [('Cobertura (valor calculável)', 'cob', pc), ('Mediana', 'med', pc), ('Percentil 10', 'p10', pc), ('Percentil 90', 'p90', pc),
            ('Negativos', 'neg', pc), ('Acima de 100%', 'hi', pc), ('**Absurdos ou indefinidos (< 0, > 100% ou sem valor)**', 'absurd', pc)]
    for lab, key, f in rows:
        out.append(f'| {lab} | ' + ' | '.join(f(stats[k][key]) for k in 'ABC') + ' |')
    # persistencia
    out += ['', '## 2. Persistência (o ROIC de um ano prevê o do ano seguinte?)\n',
            'Correlação de postos (Spearman) entre empresas, média dos anos; e % de empresas cujo ROIC muda mais de 10 p.p. de um ano para o outro.\n',
            '| Critério | (A) | (B) | (C) |', '|---|---|---|---|']
    pers = {}
    for k in 'ABC':
        p = op.pivot_table(index='ticker', columns='year', values=k)
        c1 = [p[y].rank().corr(p[y + 1].rank()) for y in p.columns[:-1] if y + 1 in p.columns]
        c3 = [p[y].rank().corr(p[y + 3].rank()) for y in p.columns[:-3] if y + 3 in p.columns]
        jump = ((p.diff(axis=1).abs() > 0.10).sum().sum()) / p.diff(axis=1).notna().sum().sum()
        pers[k] = (np.nanmean(c1), np.nanmean(c3), jump)
    out.append('| Correlação de postos t → t+1 | ' + ' | '.join(n2(pers[k][0]) for k in 'ABC') + ' |')
    out.append('| Correlação de postos t → t+3 | ' + ' | '.join(n2(pers[k][1]) for k in 'ABC') + ' |')
    out.append('| Variação > 10 p.p. num ano | ' + ' | '.join(pc(pers[k][2]) for k in 'ABC') + ' |')
    # casos problematicos conhecidos
    known = ['DOCS', 'MANH', 'VEEV', 'FICO', 'MAR', 'HLT', 'MSCI', 'ABBV', 'PM', 'DE', 'CPRT', 'MCK']
    out += ['', '## 3. Casos problemáticos conhecidos (ROIC de 2024)\n', '| Empresa | (A) | (B) | (C) |', '|---|---|---|---|']
    for t in known:
        x = df[(df.ticker == t) & (df.year == 2024)]
        if len(x): out.append(f'| {t} | ' + ' | '.join(pc(x[k].iloc[0]) for k in 'ABC') + ' |')
    (ROOT / 'roic_definicoes.md').write_text('\n'.join(out))
    # amostra para revisao qualitativa
    nm = u.set_index('ticker')['name']
    with pd.ExcelWriter(ROOT / 'roic_definicoes_amostra.xlsx', engine='openpyxl') as w:
        res = []
        for t in SAMPLE:
            x = df[(df.ticker == t) & (df.year >= 2016)].set_index('year')
            if x.empty: continue
            for k, lab in (('A', '(A) atual'), ('B', '(B) operacional + aquisições'), ('C', '(C) marginal 5 anos')):
                res.append({'Ticker': t, 'Empresa': nm.get(t), 'Definição': lab, **{str(y): x[k].get(y) for y in range(2016, 2026)}})
            res.append({'Ticker': t, 'Empresa': nm.get(t), 'Definição': 'Sua avaliação (qual parece certo?)'})
        pd.DataFrame(res).to_excel(w, sheet_name='Amostra (34 empresas)', index=False)
        ws = w.sheets['Amostra (34 empresas)']
        for col in ws.iter_cols(min_col=4, max_col=13):
            for cell in col[1:]: cell.number_format = '0.0%'
        for i, wd in enumerate([8, 34, 32] + [9] * 10, start=1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = wd
        ws.freeze_panes = 'D2'
        comp = df[df.ticker.isin(SAMPLE) & (df.year >= 2022)][['ticker', 'year', 'nopat', 'icA', 'icB', 'A', 'B', 'C']]
        comp.columns = ['Ticker', 'Ano', 'NOPAT', 'Capital (A)', 'Capital (B)', 'ROIC (A)', 'ROIC (B)', 'ROIC (C)']
        comp.to_excel(w, sheet_name='Componentes 2022-2025', index=False)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
