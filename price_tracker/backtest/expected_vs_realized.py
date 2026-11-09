"""(1) Distribuicao das atribuicoes e dos retornos por posicao: Opportunity of Lifetime x Good Companies, Great Returns.
(2) Retorno esperado (modelo, a.a.) x retorno realizado (a.a. em 3 anos e em 1 ano) de cada compra.
Uso: python3 backtest/expected_vs_realized.py [corte]   (padrao 2.93)"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt

ROOT = pathlib.Path(__file__).parent
D = ROOT / 'data'
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
COL = {OOL: '#1f6feb', GCGR: '#e8590c'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
P = mt.FuncFormatter(lambda v, _: f'{v:.0%}')


def fwd_return(adj, d, t, years):
    s = adj[t].dropna()
    s0 = s[s.index <= d]
    if s0.empty: return np.nan
    end = d + pd.DateOffset(years=years)
    if s.index[-1] < end - pd.Timedelta(days=7): return np.nan
    s1 = s[s.index <= end]
    return (s1.iloc[-1] / s0.iloc[-1]) ** (1 / years) - 1


def main(cut='2.93'):
    col = f'cat_zg{cut}'
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    x = cls[cls.date.isin(dates[:-1]) & cls[col].isin([OOL, GCGR])].copy()
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill()
    fwdq = px.shift(-1) / px - 1
    x['rq'] = [fwdq.at[d, t] for d, t in zip(x.date, x.ticker)]
    x['n'] = x.groupby(['date', col]).ticker.transform('size')
    x['c'] = x.rq / x.n
    x['r3'] = [fwd_return(adj, d, t, 3) for d, t in zip(x.date, x.ticker)]
    x['r1'] = [fwd_return(adj, d, t, 1) for d, t in zip(x.date, x.ticker)]
    out = [f'# Distribuições e retorno esperado × realizado (corte zGrowth {cut.replace(".", ",")})\n',
           '> ⚠️ **ROIC:** o retorno esperado vem do P/E justo, que usa o ROIC (clássico, cortes não revistos).\n']

    # ---------- (1) distribuicoes
    att = {c: x[x[col] == c].groupby('ticker').c.sum() for c in (OOL, GCGR)}
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.5), dpi=130)
    bins = np.linspace(-0.04, 0.14, 46)
    for c in (OOL, GCGR):
        ax[0].hist(att[c].clip(-0.04, 0.14), bins=bins, alpha=.55, color=COL[c], label=f'{c} ({len(att[c])} ações)', density=True)
    ax[0].set_title('Atribuição por ação (contribuição total na carteira)'); ax[0].xaxis.set_major_formatter(P); ax[0].set_ylabel('Densidade')
    ax[0].legend(fontsize=8); ax[0].axvline(0, color='k', lw=.8)
    bins = np.linspace(-0.6, 0.8, 57)
    for c in (OOL, GCGR):
        r = x[x[col] == c].rq.dropna()
        ax[1].hist(r.clip(-0.6, 0.8), bins=bins, alpha=.55, color=COL[c], label=f'{c} ({len(r)} posições)', density=True)
    ax[1].set_title('Retorno de cada posição no trimestre (sem efeito de peso)'); ax[1].xaxis.set_major_formatter(P)
    ax[1].legend(fontsize=8); ax[1].axvline(0, color='k', lw=.8)
    fig.tight_layout(); fig.savefig(ROOT / f'dist_attribution_{cut}.png'); plt.close(fig)
    out += ['## 1. Distribuições\n', '| Estatística | Atribuição OoL | Atribuição GCGR | Retorno/trim. OoL | Retorno/trim. GCGR |', '|---|---|---|---|---|']
    rq = {c: x[x[col] == c].rq.dropna() for c in (OOL, GCGR)}
    for name, f in [('Média', 'mean'), ('Mediana', 'median'), ('Desvio-padrão', 'std'), ('Percentil 5', lambda s: s.quantile(.05)),
                    ('Percentil 95', lambda s: s.quantile(.95)), ('Mínimo', 'min'), ('Máximo', 'max')]:
        g = (lambda s: getattr(s, f)()) if isinstance(f, str) else f
        out.append(f'| {name} | {pc(g(att[OOL]))} | {pc(g(att[GCGR]))} | {pc(g(rq[OOL]))} | {pc(g(rq[GCGR]))} |')
    out.append(f'| Assimetria (skew) | {att[OOL].skew():.2f} | {att[GCGR].skew():.2f} | {rq[OOL].skew():.2f} | {rq[GCGR].skew():.2f} |'.replace('.', ','))
    out.append(f'| % posições negativas | | | {pc((rq[OOL] < 0).mean())} | {pc((rq[GCGR] < 0).mean())} |')
    out.append(f'| Peso médio por ação (1/N) | {pc((1 / x[x[col] == OOL].n).mean())} | {pc((1 / x[x[col] == GCGR].n).mean())} | | |\n')

    # ---------- (2) esperado x realizado
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=130, sharey=True)
    edges = [0.2, 0.3, 0.4, 0.6, 1.0, np.inf]
    labels = ['20–30%', '30–40%', '40–60%', '60–100%', '>100%']
    tab = {}
    for ax, c in zip(axes, (OOL, GCGR)):
        y = x[(x[col] == c) & x.r3.notna()]
        ax.scatter(y.ret.clip(upper=2), y.r3.clip(-0.5, 1.2), s=9, alpha=.35, color=COL[c])
        y = y.assign(b=pd.cut(y.ret, edges, labels=labels, right=False))
        mids = y.groupby('b', observed=False).agg(e=('ret', 'median'), r=('r3', 'median'), n=('r3', 'size'))
        ax.plot(mids.e.clip(upper=2), mids.r, 'k-o', lw=2, label='mediana por faixa de retorno esperado')
        ax.axhline(0, color='grey', lw=.8); ax.plot([0.2, 1.2], [0.2, 1.2], ls=':', color='grey', label='realizado = esperado')
        rho = y[['ret', 'r3']].rank().corr().iloc[0, 1]
        ax.set_title(f'{c}\n{len(y)} compras com 3 anos de histórico · correlação de postos {rho:.2f}'.replace('.', ',', 1) if False else
                     f'{c}\n{len(y)} compras com 3 anos de histórico · correlação de postos {rho:.2f}')
        ax.set_xlabel('Retorno esperado pelo modelo na compra (a.a.)'); ax.xaxis.set_major_formatter(P); ax.yaxis.set_major_formatter(P)
        ax.legend(fontsize=8, loc='upper right'); ax.grid(alpha=.3)
        for h in (3, 1):
            z = x[(x[col] == c) & x[f'r{h}'].notna()].assign(b=lambda d: pd.cut(d.ret, edges, labels=labels, right=False))
            tab[(c, h)] = z.groupby('b', observed=False).agg(n=(f'r{h}', 'size'), e=('ret', 'median'), r=(f'r{h}', 'median'),
                                                            m=(f'r{h}', 'mean'), neg=(f'r{h}', lambda s: (s < 0).mean()))
    axes[0].set_ylabel('Retorno realizado nos 3 anos seguintes (a.a.)')
    fig.suptitle('Retorno esperado × realizado em 3 anos, por compra (ação × trimestre na classe)')
    fig.tight_layout(); fig.savefig(ROOT / f'expected_vs_realized_{cut}.png'); plt.close(fig)

    out += ['## 2. Retorno esperado × realizado, por faixa de retorno esperado\n',
            'Compra = ação × trimestre em que estava na classe (a mesma ação aparece em vários trimestres).\n']
    for h in (3, 1):
        out += [f'### Realizado em {h} ano{"s" if h > 1 else ""} (a.a.)\n',
                '| Faixa esperada | OoL: compras | OoL: esperado (med.) | OoL: realizado (med.) | OoL: % negativas | GCGR: compras | GCGR: esperado (med.) | GCGR: realizado (med.) | GCGR: % negativas |',
                '|---|---|---|---|---|---|---|---|---|']
        for lb in labels:
            a, b = tab[(OOL, h)].loc[lb], tab[(GCGR, h)].loc[lb]
            out.append(f'| {lb} | {int(a.n)} | {pc(a.e)} | {pc(a.r)} | {pc(a.neg)} | {int(b.n)} | {pc(b.e)} | {pc(b.r)} | {pc(b.neg)} |')
        out.append('')
    # ambas as classes juntas
    z = x[x.r3.notna()].assign(b=lambda d: pd.cut(d.ret, edges, labels=labels, right=False))
    j = z.groupby('b', observed=False).agg(n=('r3', 'size'), r=('r3', 'median'), neg=('r3', lambda s: (s < 0).mean()))
    out += ['### As duas classes juntas (realizado em 3 anos)\n', '| Faixa esperada | Compras | Realizado (mediana) | % negativas |', '|---|---|---|---|']
    out += [f'| {lb} | {int(r.n)} | {pc(r.r)} | {pc(r.neg)} |' for lb, r in j.iterrows()]
    (ROOT / f'expected_vs_realized_{cut}.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '2.93')
