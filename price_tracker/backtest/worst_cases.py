"""Piores episodios (entrada -> saida de uma acao na classe) de Opportunity of Lifetime e Good Companies, Great Returns,
com os parametros do modelo na entrada, comparados a mediana de todos os episodios e aos 50 melhores.
Uso: python3 backtest/worst_cases.py [corte]   (padrao 2.93)"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
D = ROOT / 'data'
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
nm = lambda x, n=1: '—' if pd.isna(x) else f'{x:.{n}f}'.replace('.', ',')
METRICS = [('Growth (mediana EPS 5a)', 'growth', pc), ('zGrowth', 'zgrowth', nm), ('Último crescimento anual do EPS', 'g_last', pc),
           ('ROIC', 'roic', pc), ('zROIC', 'zroic', nm), ('ROIC marginal 5a', 'roic_marg', pc),
           ('Retorno esperado', 'ret', pc), ('Retorno esperado (P/E justo)', 'ret_fair', pc), ('g do ranking', 'g', pc),
           ('P/L de entrada', 'pe', nm), ('P/E justo', 'fair_pe', nm), ('P/L ÷ P/E justo', 'pe_rel', nm),
           ('Dividend yield', 'dy', pc), ('Retorno 12m antes da entrada', 'mom12', pc), ('Retorno 3a antes da entrada', 'mom36', pc),
           ('Anos de EPS válidos (de 5)', 'n_rates', nm), ('Trimestres na classe', 'quarters', nm)]


def main(cut='2.93'):
    col = f'cat_zg{cut}'
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    di = {d: i for i, d in enumerate(dates)}
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill()
    fwd = px.shift(-1) / px - 1
    lag = lambda k: adj.reindex(pd.DatetimeIndex(dates) - pd.DateOffset(years=k), method='ffill').set_axis(pd.DatetimeIndex(dates))
    b1, b3 = lag(1), lag(3)
    cls = cls[cls.date.isin(dates[:-1])].copy()
    cls['pe'] = cls.price / cls.eps.where(cls.eps > 0)
    cls['pe_rel'] = cls.pe / cls.fair_pe.where(cls.fair_pe > 0)
    cls['mom12'] = [px.at[d, t] / b1.at[d, t] - 1 for d, t in zip(cls.date, cls.ticker)]
    cls['mom36'] = [px.at[d, t] / b3.at[d, t] - 1 for d, t in zip(cls.date, cls.ticker)]
    cls['rq'] = [fwd.at[d, t] for d, t in zip(cls.date, cls.ticker)]
    # ultimo crescimento anual do EPS (de classes_pit nao temos as taxas; aproximamos pela variacao do eps base entre datas)
    e = cls.pivot_table(index='date', columns='ticker', values='eps')
    e4 = e.shift(4)
    cls['g_last'] = [e.at[d, t] / e4.at[d, t] - 1 if pd.notna(e4.at[d, t]) and e4.at[d, t] > 0 else np.nan for d, t in zip(cls.date, cls.ticker)]
    out = [f'# Piores episódios: o que tinham na entrada (corte zGrowth {cut.replace(".", ",")})\n',
           '> ⚠️ **ROIC:** ROIC e zROIC são parâmetros comparados; a definição ainda está em revisão.\n',
           'Episódio = período contínuo em que a ação ficou na classe. Contribuição = soma de (1/N × retorno trimestral) no episódio. '
           'Parâmetros medidos no trimestre de entrada.\n']
    for cat in (OOL, GCGR):
        x = cls[cls[col] == cat].copy().sort_values(['ticker', 'date'])
        x['n'] = x.groupby('date').ticker.transform('size')
        x['c'] = x.rq / x.n
        x['i'] = x.date.map(di)
        x['ep'] = (x.groupby('ticker').i.diff() != 1).cumsum()
        ep = x.groupby('ep').agg(ticker=('ticker', 'first'), entry=('date', 'min'), exit=('date', 'max'), quarters=('c', 'size'),
                                 contrib=('c', 'sum'), ep_ret=('rq', lambda s: (1 + s.fillna(0)).prod() - 1))
        first = x.groupby('ep').first()
        for _, c, _ in METRICS:
            if c not in ('quarters',): ep[c] = first[c]
        ep['sector'] = ep.ticker.map(u.sector); ep['name'] = ep.ticker.map(u['name'])
        ep = ep.sort_values('contrib')
        worst, best = ep.head(50), ep.tail(50)
        out += [f'## {cat}: {len(ep)} episódios\n', '### Perfil na entrada: 50 piores × todos × 50 melhores (medianas)\n',
                '| Parâmetro | 50 piores | Todos os episódios | 50 melhores |', '|---|---|---|---|']
        for n, c, f in METRICS:
            out.append(f'| {n} | **{f(worst[c].median())}** | {f(ep[c].median())} | {f(best[c].median())} |')
        out.append(f'| Retorno do episódio | **{pc(worst.ep_ret.median())}** | {pc(ep.ep_ret.median())} | {pc(best.ep_ret.median())} |')
        # setores
        sw = worst.sector.value_counts(normalize=True); sa = ep.sector.value_counts(normalize=True)
        out += ['', '**Setores (% dos episódios):** ' + ' · '.join(f'{s} {pc(sw.get(s, 0))} (todos {pc(sa.get(s, 0))})' for s in sa.index[:7]), '']
        if cat == OOL:
            out += ['### Os 50 piores episódios\n',
                    '| # | Ticker | Empresa | Setor | Entrada | Saída | Trim. | Retorno do episódio | Contribuição | Growth | zG | ROIC | zROIC | Ret. esperado | P/L | P/E justo | Retorno 12m antes |',
                    '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
            for k, (_, r) in enumerate(worst.iterrows()):
                out.append(f'| {k + 1} | {r.ticker} | {r["name"]} | {r.sector} | {r.entry:%Y-%m} | {r.exit:%Y-%m} | {r.quarters} | {pc(r.ep_ret)} | {pc(r.contrib)} | '
                           f'{pc(r.growth)} | {nm(r.zgrowth)} | {pc(r.roic)} | {nm(r.zroic)} | {pc(r.ret)} | {nm(r.pe)} | {nm(r.fair_pe)} | {pc(r.mom12)} |')
            out.append('')
        ep.to_csv(D / f'episodes_{cat.split()[0].lower()}_{cut}.csv')
        # posicoes por faixa (todas as posicoes trimestrais da classe) para testar regras simples
        out += [f'### {cat}: retorno médio no trimestre seguinte por faixa (todas as {len(x)} posições)\n']
        for n, c, edges in [('P/L de entrada', 'pe', [0, 20, 30, 40, 60, np.inf]), ('Retorno esperado', 'ret', [0.2, 0.4, 0.6, 1.0, np.inf]),
                            ('Retorno 12m antes', 'mom12', [-np.inf, 0, 0.25, 0.5, 1.0, np.inf]), ('ROIC', 'roic', [0, 0.2, 0.3, 0.5, np.inf]),
                            ('Growth', 'growth', [0.15, 0.25, 0.4, 0.6, np.inf])]:
            b = pd.cut(x[c], edges, right=False)
            t = x.groupby(b, observed=True).rq.agg(['size', 'mean', lambda s: (s < 0).mean()])
            out.append(f'- **{n}:** ' + ' · '.join(f'{iv}: {pc(r["mean"] * 4)} a.a., {pc(r["<lambda_0>"])} neg. (n={int(r["size"])})' for iv, r in t.iterrows()))
        out.append('')
    (ROOT / f'worst_cases_{cut}.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '2.93')
