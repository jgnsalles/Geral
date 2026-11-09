"""Atribuicao e carteira trimestral das 3 subclasses do esboco (OoL a partir de ROIC 12%):
High Returns + High Growth, High Growth (EPS > 30%), High Returns (ROIC > 30%).
Saidas: backtest/esboco_attribution.md e backtest/esboco_carteiras.xlsx
Uso: python3 backtest/esboco_attribution.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402

pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')


def build():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    base = cb.classify(cls[cls.date.isin(dates)].copy(), False, False, False)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': 0.12, 'Roic_Lo': 0.10})
    try:
        c = engine.classify(base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore'))
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(c.code.isna(), None, c.category)
    ool = c.cat == 'Opportunity of Lifetime'
    hr, hg = ool & (c.roic > 0.30), ool & (c.growth > 0.30)
    groups = {'High Returns + High Growth': hr & hg, 'High Growth (EPS > 30%)': hg, 'High Returns (ROIC > 30%)': hr}
    return c, groups, adj, dates


def main():
    c, groups, adj, dates = build()
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill(); fwd = px.shift(-1) / px - 1
    c['r'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    out = ['# Esboço: atribuição e carteiras trimestrais das 3 maiores subclasses (EUA, 2012–2026)\n',
           '> ⚠️ **ROIC:** High Returns inclui casos de ROIC distorcido pela medida (ex.: Marriott, FICO, Fortinet, Live Nation).\n',
           'Contribuição = soma, nos trimestres em que a ação esteve na carteira, de (1/N × retorno da ação no trimestre). '
           'As carteiras de cada trimestre estão em `esboco_carteiras.xlsx`.\n']
    sheets = {}
    for name, m in groups.items():
        x = c[m & c.date.isin(dates[:-1])].copy()
        x['n'] = x.groupby('date').ticker.transform('size'); x['c'] = x.r / x.n
        a = x.groupby('ticker').agg(contrib=('c', 'sum'), trim=('c', 'size'), ret=('r', 'mean'), p0=('date', 'min'), p1=('date', 'max')).sort_values('contrib', ascending=False)
        hold = {d: g.ticker.tolist() for d, g in c[m].groupby('date')}
        full = stats(run_portfolio(hold, adj, dates)[0])['CAGR']
        sens = [(k, stats(run_portfolio({d: [t for t in v if t not in set(a.index[:k])] for d, v in hold.items()}, adj, dates)[0])['CAGR']) for k in (1, 3, 5, 10)]
        row = lambda i, t, r: f"| {i} | {t} | {u['name'].get(t)} | {u.sector.get(t)} | {sg(r.contrib)} | {r.trim} | {sg(r.ret)} | {r.p0.year}–{r.p1.year} |"
        hdr = ['| # | Ticker | Empresa | Setor | Contribuição | Trim. | Retorno médio/trim. | Período |', '|---|---|---|---|---|---|---|---|']
        out += [f'## {name}\n', f'- Retorno anual: **{pc(full)}** · empresas distintas: {len(a)} · ações em média: {x.groupby("date").size().mean():.1f}'.replace('.', ',', 1),
                '- Sem as maiores contribuições: ' + ' · '.join(f'sem top {k}: {pc(v)}' for k, v in sens),
                f'- As 10 maiores somam {pc(a.contrib.head(10).sum() / a.contrib.sum())} da contribuição total\n', '**15 maiores**\n'] + hdr
        out += [row(i + 1, t, r) for i, (t, r) in enumerate(a.head(15).iterrows())]
        out += ['', '**10 menores**\n'] + hdr + [row(i + 1, t, r) for i, (t, r) in enumerate(a.tail(10).iloc[::-1].iterrows())] + ['']
        # carteiras trimestrais
        y = c[m].copy()
        y['Empresa'] = y.ticker.map(u['name']); y['Setor'] = y.ticker.map(u.sector)
        q = y.groupby('date').agg(N=('ticker', 'size'), Tickers=('ticker', lambda s: ', '.join(sorted(s)))).reset_index()
        q['date'] = q.date.dt.date; q.columns = ['Data do rebalanceamento', 'Ações', 'Carteira (tickers)']
        det = y[['date', 'ticker', 'Empresa', 'Setor', 'roic', 'growth', 'ret', 'r']].sort_values(['date', 'ticker']).copy()
        det['date'] = det.date.dt.date
        det.columns = ['Data', 'Ticker', 'Empresa', 'Setor', 'ROIC', 'Growth (mediana 5 anos)', 'Retorno esperado', 'Retorno no trimestre seguinte']
        sheets[name] = (q, det, a.assign(Empresa=a.index.map(u['name'])))
        print(name, len(a), flush=True)
    (ROOT / 'esboco_attribution.md').write_text('\n'.join(out))
    with pd.ExcelWriter(ROOT / 'esboco_carteiras.xlsx', engine='openpyxl') as w:
        short = {'High Returns + High Growth': 'HR+HG', 'High Growth (EPS > 30%)': 'High Growth', 'High Returns (ROIC > 30%)': 'High Returns'}
        for name, (q, det, a) in sheets.items():
            s = short[name]
            q.to_excel(w, sheet_name=f'{s} - por trimestre', index=False)
            det.to_excel(w, sheet_name=f'{s} - detalhe', index=False)
            aa = a.reset_index()[['ticker', 'Empresa', 'contrib', 'trim', 'ret', 'p0', 'p1']]
            aa.columns = ['Ticker', 'Empresa', 'Contribuição', 'Trimestres', 'Retorno médio/trim.', 'Primeiro', 'Último']
            aa['Primeiro'] = aa.Primeiro.dt.date; aa['Último'] = aa['Último'].dt.date
            aa.to_excel(w, sheet_name=f'{s} - atribuição', index=False)
        for ws in w.sheets.values():
            for col in ws.iter_cols(min_row=1, max_row=1):
                h = col[0].value or ''
                width = 80 if 'Carteira' in h else 30 if h in ('Empresa', 'Setor') else 14
                ws.column_dimensions[col[0].column_letter].width = width
                if h in ('ROIC', 'Growth (mediana 5 anos)', 'Retorno esperado', 'Retorno no trimestre seguinte', 'Contribuição', 'Retorno médio/trim.'):
                    for cell in ws[col[0].column_letter][1:]: cell.number_format = '0.0%'
            ws.freeze_panes = 'A2'
    print('\n'.join(out[:3]))


if __name__ == '__main__':
    main()
