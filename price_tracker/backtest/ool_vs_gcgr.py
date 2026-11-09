"""Opportunity of Lifetime x Good Companies, Great Returns (sem zROIC, universo point-in-time, ROIC oficial, esboco 12%).
1. Diagnostico das 10 piores atribuicoes de cada classe: metricas na compra, o que aconteceu com lucro e multiplo.
2. Comparacao OoL x GCGR: perfil, distribuicao, concentracao, faixas de retorno esperado/ROIC/crescimento.
Saidas: backtest/ool_vs_gcgr.md, backtest/ool_vs_gcgr.png
Uso: python3 backtest/ool_vs_gcgr.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
SHORT = {OOL: 'OoL', GCGR: 'GCGR'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
pc1 = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
sg0 = lambda x: '—' if pd.isna(x) else f'{x:+.0%}'
sp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.2f}'.replace('.', ',')
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')
RY = [f'ry{i}' for i in range(1, 7)]; GY = [f'gy{i}' for i in range(1, 6)]


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    allf = f[f.date.isin(dates)].set_index(['date', 'ticker']).sort_index()  # para olhar o lucro depois da saida
    f = f[f.date.isin(dates) & f.pit_member].assign(zroic=0.0)
    adj = load_prices()['adj_close']
    u = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'name', 'sector']],
                   pd.read_csv(D / 'universe_pit_extra.csv').rename(columns={'sec_name': 'name'})[['ticker', 'name']]]).drop_duplicates('ticker').set_index('ticker')
    nm = lambda t: str(u['name'].get(t, t))
    sec = lambda t: u['sector'].get(t) if isinstance(u['sector'].get(t), str) else ''
    c = vp.classify(f, 'sketch', 'B')
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    c = c[c.date < dates[-1]].copy()
    uq = c[c.cat.notna()].groupby('date').rq.mean()
    c['ex'] = c.rq - c.date.map(uq); c['pe'] = c.price / c.eps.where(c.eps > 0)
    b1 = adj.reindex(pd.DatetimeIndex(dates) - pd.DateOffset(years=1), method='ffill').set_axis(pd.DatetimeIndex(dates))
    c['mom12'] = [px.at[d, t] / b1.at[d, t] - 1 for d, t in zip(c.date, c.ticker)]
    Y = (len(dates) - 1) / 4
    di = {d: i for i, d in enumerate(dates)}
    G = {}
    for cat in (OOL, GCGR):
        x = c[c.cat == cat].copy(); x['n'] = x.groupby('date').ticker.transform('size')
        x['exc'] = x.ex / x.n; G[cat] = x

    out = ['# Opportunity of Lifetime × Good Companies, Great Returns (EUA, point-in-time, sem zROIC)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A); zROIC desligado; OoL a partir de ROIC 12%, ROIC médio 10–12%. '
           'O ROIC entra na classificação, no P/E justo e no retorno esperado: se ele estiver errado, o diagnóstico muda.\n',
           'Contribuição = excesso de cada ação sobre o universo ÷ nº de ações da classe no trimestre, somado e dividido pelos anos '
           f'({Y:.1f}). Lucro e P/L na compra e na saída (trimestre seguinte ao último na carteira): retorno de preço ≈ variação do lucro × variação do P/L.\n']

    # 1) diagnostico das 10 piores
    def stints(x):
        """sequencias consecutivas de trimestres na carteira"""
        x = x.sort_values('date'); k = x.date.map(di); grp = (k.diff() != 1).cumsum()
        return [g for _, g in x.groupby(grp)]

    for cat in (OOL, GCGR):
        x = G[cat]; a = x.groupby('ticker').exc.sum().sort_values()
        out += [f'## 1{"a" if cat == OOL else "b"}. As 10 piores atribuições da {cat}\n',
                '| # | Ticker | Empresa | Setor | Contribuição (p.p. a.a.) | Trim. | Períodos | Retorno no período | Universo no período | '
                'P/L na compra → saída | Lucro (EPS) na compra → saída | ROIC na compra (série 6 anos) | Cresc. EPS na compra (5 anos) | Retorno esperado | Alta 12m antes |',
                '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for i, (t, v) in enumerate(a.head(10).items(), 1):
            y = x[x.ticker == t]
            per, rets, unis, pes, epss, ros, gro, exps, moms = [], [], [], [], [], [], [], [], []
            for s in stints(y):
                d0, d1 = s.date.iloc[0], s.date.iloc[-1]; dn = dates[di[d1] + 1]
                per.append(f'{d0:%m/%y}–{dn:%m/%y}')
                rets.append(sg0(np.prod(1 + s.rq) - 1)); unis.append(sg0(np.prod(1 + s.date.map(uq)) - 1))
                r0 = s.iloc[0]
                e1 = allf.eps.get((dn, t), np.nan); p1 = allf.price.get((dn, t), np.nan)
                pe1 = p1 / e1 if e1 and e1 > 0 else np.nan
                pes.append(f'{n1(r0.pe)} → {n1(pe1) if e1 > 0 else "neg."}')
                epss.append(f'{r0.eps:.2f} → sem dado (saiu do S&P 500)'.replace('.', ',', 1) if pd.isna(e1) else
                            f'{r0.eps:.2f} → {e1:.2f} ({sg0(e1 / r0.eps - 1) if r0.eps > 0 else "—"})'.replace('.', ','))
                ros.append(' / '.join(pc(v_) for v_ in r0[RY] if pd.notna(v_)))
                gro.append(' / '.join(pc(v_) for v_ in r0[GY] if pd.notna(v_)))
                exps.append(pc(r0.ret)); moms.append(sg0(r0.mom12))
            j = lambda L: '<br>'.join(L)
            out.append(f'| {i} | {t} | {nm(t)} | {sec(t)} | **{sp(v / Y)}** | {len(y)} | {j(per)} | {j(rets)} | {j(unis)} | {j(pes)} | {j(epss)} | '
                       f'{j(ros)} | {j(gro)} | {j(exps)} | {j(moms)} |')
        out.append('')

    # 2) comparacao
    def prof(x, nav):
        a = x.groupby('ticker').agg(exc=('exc', 'sum'), ex=('ex', 'mean')).sort_values('exc', ascending=False)
        s = stats(nav)
        return {'Retorno anual (carteira)': pc1(s['CAGR']), 'Volatilidade': pc1(s['Vol']), 'Pior queda': pc1(s['MaxDD']),
                'Ações por trimestre': f"{x.groupby('date').size().mean():.0f}", 'Empresas diferentes': f'{len(a)}',
                'Excesso médio por posição (a.a.)': sg(x.ex.mean() * 4), 'Excesso mediano por posição (a.a.)': sg(x.ex.median() * 4),
                '% posições acima do universo': pc(((x.ex) > 0).mean()), '% empresas com excesso > 0': pc((a.ex > 0).mean()),
                'Contribuição total ao excesso (p.p. a.a.)': sp(a.exc.sum() / Y), 'Contribuição das 10 maiores': sp(a.exc.head(10).sum() / Y),
                'Contribuição das 10 piores': sp(a.exc.tail(10).sum() / Y), 'Sem as 10 maiores': sp((a.exc.sum() - a.exc.head(10).sum()) / Y),
                'Sem as 10 maiores e as 10 piores': sp((a.exc.sum() - a.exc.head(10).sum() - a.exc.tail(10).sum()) / Y),
                'ROIC (mediana)': pc(x.roic.median()), 'Crescimento EPS 5a (mediana)': pc(x.growth.median()), 'P/L (mediana)': n1(x.pe.median()),
                'P/E justo (mediana)': n1(x.fair_pe.median()), 'Retorno esperado (mediana)': pc(x.ret.median()), 'Dividend yield (mediana)': pc1(x.dy.median()),
                'Alta 12m antes da compra (mediana)': sg0(x.mom12.median()), 'Trimestres seguidos na carteira (média por empresa)': n1(x.groupby('ticker').size().mean()),
                'Maior setor': f"{x.ticker.map(sec).replace('', np.nan).value_counts(normalize=True).index[0]} ({pc(x.ticker.map(sec).replace('', np.nan).value_counts(normalize=True).iloc[0])})"}
    navs = {k: run_portfolio({d: g.ticker.tolist() for d, g in G[k].groupby('date')}, adj, dates)[0] for k in G}
    P = {k: prof(G[k], navs[k]) for k in G}
    out += ['## 2. OoL × GCGR lado a lado\n', '| | Opportunity of Lifetime | Good Companies, Great Returns |', '|---|---|---|']
    out += [f'| {k} | {P[OOL][k]} | {P[GCGR][k]} |' for k in P[OOL]]

    # defeitos da GCGR
    g = G[GCGR]; flaw = g.code.map(lambda s: next((i for i in range(4) if s[i] != 'HOGNG'[i]), -1))
    FL = {0: 'Crescimento médio (6–15%)', 1: 'Crescimento instável (zGrowth ≥ 2,93)', 2: 'ROIC médio (10–12%)'}
    out += ['', '### GCGR por motivo de ter ficado fora da OoL\n', '| Motivo | Peso na GCGR | Excesso médio a.a. | Mediana | Contribuição ao excesso da GCGR | Sem as 5 maiores | Maiores | Piores |',
            '|---|---|---|---|---|---|---|---|']
    for k, v in FL.items():
        y = g[flaw == k]; a = y.groupby('ticker').exc.sum().sort_values(ascending=False)
        out.append(f'| {v} | {pc(len(y) / len(g))} | {sg(y.ex.mean() * 4)} | {sg(y.ex.median() * 4)} | {sp(a.sum() / Y)} | {sp((a.sum() - a.head(5).sum()) / Y)} | '
                   f"{', '.join(a.head(5).index)} | {', '.join(a.tail(5).index[::-1])} |")
    # faixas
    out += ['', '### Excesso mediano por faixa (a.a.)\n', '| Variável | Faixa | OoL: posições | OoL: média | OoL: mediana | GCGR: posições | GCGR: média | GCGR: mediana |',
            '|---|---|---|---|---|---|---|---|']
    BINS = {'Retorno esperado': ('ret', [-1, .3, .4, .5, .75, 1, 100], ['< 30%', '30–40%', '40–50%', '50–75%', '75–100%', '> 100%']),
            'ROIC': ('roic', [-1, .15, .2, .3, .5, 100], ['< 15%', '15–20%', '20–30%', '30–50%', '> 50%']),
            'Crescimento EPS': ('growth', [-1, .1, .15, .3, .5, 1, 100], ['< 10%', '10–15%', '15–30%', '30–50%', '50–100%', '> 100%']),
            'Alta 12m antes': ('mom12', [-10, 0, .2, .5, 100], ['< 0%', '0–20%', '20–50%', '> 50%'])}
    for name, (col, bins, labs) in BINS.items():
        for lab in labs:
            row = [name, lab]
            for k in (OOL, GCGR):
                x = G[k]; m = pd.cut(x[col], bins, labels=labs) == lab; y = x[m]
                row += [str(len(y)), sg(y.ex.mean() * 4) if len(y) >= 30 else '—', sg(y.ex.median() * 4) if len(y) >= 30 else '—']
            out.append('| ' + ' | '.join(row) + ' |')

    # graficos
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5), dpi=130)
    col = {OOL: '#1f6feb', GCGR: '#e8590c'}
    for k in G:
        a = G[k].groupby('ticker').exc.sum().sort_values(ascending=False) / Y * 100
        ax[0].plot(np.arange(1, len(a) + 1) / len(a) * 100, a.cumsum().values, color=col[k], lw=2, label=f'{SHORT[k]} ({len(a)} empresas)')
        e = G[k].groupby('ticker').ex.mean() * 400
        ax[1].hist(e.clip(-80, 80), bins=32, range=(-80, 80), alpha=.5, color=col[k], label=f'{SHORT[k]} (mediana {e.median():+.1f}%)'.replace('.', ','), density=True)
        n = navs[k]; ax[2].plot(n.index, (n - 1) * 100, color=col[k], lw=2, label=f'{SHORT[k]} ({pc1(stats(n)["CAGR"])} a.a.)')
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    ax[2].plot(spy.index, (spy - 1) * 100, color='black', ls='--', lw=1.6, label=f'S&P 500 ({pc1(stats(spy)["CAGR"])} a.a.)')
    ax[0].axhline(0, color='black', lw=.8); ax[0].set_xlabel('% das empresas, da maior para a menor contribuição'); ax[0].set_ylabel('Contribuição acumulada ao excesso (p.p. a.a.)')
    ax[0].set_title('Concentração: de onde vem o excesso', fontsize=10)
    ax[1].axvline(0, color='black', lw=.8); ax[1].set_xlabel('Excesso médio por empresa sobre o universo (% a.a.)'); ax[1].set_title('Distribuição por empresa', fontsize=10)
    ax[2].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax[2].set_title('Retorno total acumulado', fontsize=10)
    for a_ in ax: a_.grid(alpha=.3); a_.legend(fontsize=8)
    fig.suptitle('Opportunity of Lifetime × Good Companies, Great Returns — universo point-in-time, sem zROIC', fontsize=11)
    fig.tight_layout(); fig.savefig(ROOT / 'ool_vs_gcgr.png'); plt.close(fig)
    (ROOT / 'ool_vs_gcgr.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
