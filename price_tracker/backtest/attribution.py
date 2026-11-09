"""Atribuicao por acao: Opportunity of Lifetime x Good Companies, Great Returns (cenario-base).
Contribuicao de uma acao = soma, nos trimestres em que esteve na carteira, de (peso 1/N) x retorno da acao no trimestre.
Uso: python3 backtest/attribution.py [corte]   (padrao 2.93)"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402

CLASSES = ['Opportunity of Lifetime', 'Good Companies, Great Returns']
pc = lambda x: f'{x:.1%}'.replace('.', ',')
sg = lambda x: f'{x:+.1%}'.replace('.', ',')


def main(cut='2.93'):
    col = f'cat_zg{cut}'
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill()
    fwd = px.shift(-1) / px - 1
    lines = [f'# Atribuição por ação (cenário-base: g 7%, ROIC original, corte zGrowth {cut.replace(".", ",")})\n',
             '> ⚠️ **ROIC:** quem entra em cada classe depende do ROIC (clássico, cortes 20%/10% ainda não revistos).\n',
             'Contribuição = soma, nos trimestres em que a ação esteve na carteira, de (1/N) × retorno da ação no trimestre, '
             'em pontos percentuais do retorno acumulado aritmético da carteira.\n']
    for cat in CLASSES:
        x = cls[(cls[col] == cat) & cls.date.isin(dates[:-1])].copy()
        x['n'] = x.groupby('date').ticker.transform('size')
        x['r'] = [fwd.at[d, t] if t in fwd.columns else np.nan for d, t in zip(x.date, x.ticker)]
        x['c'] = x.r / x.n
        a = x.groupby('ticker').agg(contrib=('c', 'sum'), trims=('c', 'size'), ret_trim=('r', 'mean'),
                                    first=('date', 'min'), last=('date', 'max')).sort_values('contrib', ascending=False)
        a['setor'] = a.index.map(u.sector)
        total = a.contrib.sum()
        hold = {d: g.ticker.tolist() for d, g in x.groupby('date')}
        full = stats(run_portfolio(hold, adj, dates)[0])['CAGR']
        sens = []
        for k in (5, 10, 15):
            drop = set(a.index[:k])
            nav = run_portfolio({d: [t for t in v if t not in drop] for d, v in hold.items()}, adj, dates)[0]
            sens.append((k, stats(nav)['CAGR']))
        dropb = set(a.index[-10:])
        navb = run_portfolio({d: [t for t in v if t not in dropb] for d, v in hold.items()}, adj, dates)[0]

        def row(i, t, r):
            per = f"{r['first'].year}–{r['last'].year}"
            return f"| {i} | {t} | {r.setor} | {sg(r.contrib)} | {pc(r.contrib / total)} | {int(r.trims)} | {sg(r.ret_trim)} | {per} |"
        hdr = ['| # | Ação | Setor | Contribuição | % do total | Trimestres | Retorno médio/trim. | Período |', '|---|---|---|---|---|---|---|---|']
        lines += [f'## {cat}\n', f'- CAGR da carteira: **{pc(full)}** · ações distintas: {len(a)} · contribuição total: {sg(total)}',
                  '- Sem as maiores contribuições: ' + ' · '.join(f'sem top {k}: {pc(c)}' for k, c in sens),
                  f'- Sem as 10 piores: {pc(stats(navb)["CAGR"])}',
                  f'- As 15 maiores somam {pc(a.contrib.head(15).sum() / total)} do total; as 15 menores, {pc(a.contrib.tail(15).sum() / total)}\n',
                  '### 15 maiores contribuições\n'] + hdr
        lines += [row(i + 1, t, r) for i, (t, r) in enumerate(a.head(15).iterrows())]
        lines += ['', '### 15 menores contribuições\n'] + hdr
        lines += [row(i + 1, t, r) for i, (t, r) in enumerate(a.tail(15).iloc[::-1].iterrows())]
        lines += ['']
        a.to_csv(D / f'attribution_{cat.split()[0].lower()}_{cut}.csv')
    both = [set(pd.read_csv(D / f'attribution_{c.split()[0].lower()}_{cut}.csv').ticker) for c in CLASSES]
    lines += [f'Ações que passaram pelas duas carteiras em algum momento: {len(both[0] & both[1])}.']
    (ROOT / f'attribution_{cut}.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '2.93')
