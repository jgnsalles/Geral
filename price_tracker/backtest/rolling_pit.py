"""Universo point-in-time (S&P 500 da foto de cada trimestre), ROIC oficial, estrutura do esboco (OoL a partir de ROIC 12%).
(1) Retorno acumulado no periodo todo; (2) janelas moveis de 1, 3, 5, 8 e 10 anos (passo mensal) testando a hipotese
OoL > Good Companies, Great Returns > mercado > demais classes.
Saidas: backtest/rolling_pit.md, backtest/rolling_pit_acumulado.png, backtest/rolling_pit_janelas.png
Uso: python3 backtest/rolling_pit.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

SEM_Z = '--sem-zroic' in sys.argv; SUF = '_sem_zroic' if SEM_Z else ''
NOTA = ' **Variante sem o critério de estabilidade do ROIC (zROIC desligado).**' if SEM_Z else ''
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
lab = lambda s: s  # nomes ja em portugues/ingles das classes


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member]
    if SEM_Z: f = f.assign(zroic=0.0)
    adj = load_prices()['adj_close']
    c = vp.classify(f, 'sketch', 'B')
    ool = c.cat == OOL
    groups = {
        'Opportunity of Lifetime (todas)': ool,
        'OoL High Returns (ROIC > 30%)': ool & (c.roic > 0.30),
        'OoL High Growth (EPS > 30%)': ool & (c.growth > 0.30),
        'OoL Base': ool & (c.roic <= 0.30) & (c.growth <= 0.30),
        'Good Companies, Great Returns (ROIC 10–12%)': c.cat == GCGR,
        'Demais classes (todas as outras)': c.cat.notna() & ~ool & (c.cat != GCGR),
        'Universo EW (contraprova)': c.cat.notna(),
    }
    nav = {}
    for k, m in groups.items():
        nav[k] = run_portfolio({d: g.ticker.tolist() for d, g in c[m].groupby('date')}, adj, dates)[0]
        print(k, flush=True)
    for b, nm in (('SPY', 'S&P 500 (SPY)'), ('RSP', 'S&P 500 equal weight (RSP)')):
        s = adj[b].loc[dates[0]:dates[-1]]; nav[nm] = s / s.iloc[0]
    N = pd.DataFrame(nav).ffill()
    M = N.resample('ME').last()
    out = ['# Universo point-in-time: retorno acumulado e janelas móveis (EUA)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A); estrutura do esboço (OoL a partir de ROIC 12%, ROIC médio 10–12%).' + NOTA + '\n',
           f'Universo = membros do S&P 500 na foto de cada trimestre. Período {dates[0]:%m/%Y} a {dates[-1]:%m/%Y}. '
           'Membros sem dados (27% em 2011, caindo para ~0 em 2026) ficam de fora (cenário neutro do teste de limites).\n',
           '## 1. Retorno acumulado no período todo\n', '| Carteira | Retorno total | CAGR | Vol | Max DD | Ações (média) |', '|---|---|---|---|---|---|']
    for k in N.columns:
        s = stats(N[k].dropna()); n = c[groups[k]].groupby('date').size().mean() if k in groups else np.nan
        out.append(f'| {k} | {pc(N[k].dropna().iloc[-1] - 1)} | {pc(s["CAGR"])} | {pc(s["Vol"])} | {pc(s["MaxDD"])} | {"—" if pd.isna(n) else f"{n:.0f}"} |')
    # grafico acumulado
    fig, ax = plt.subplots(figsize=(11, 6), dpi=140)
    sty = {'Opportunity of Lifetime (todas)': ('#1f6feb', '-', 2.6), 'OoL High Returns (ROIC > 30%)': ('#2da44e', '-', 1.6),
           'OoL High Growth (EPS > 30%)': ('#8250df', '-', 1.6), 'OoL Base': ('#54aeff', ':', 1.6),
           'Good Companies, Great Returns (ROIC 10–12%)': ('#e8590c', '-', 2.2), 'Demais classes (todas as outras)': ('#bf8700', '--', 1.4),
           'Universo EW (contraprova)': ('#57606a', '--', 1.6), 'S&P 500 (SPY)': ('#000000', '--', 2.0), 'S&P 500 equal weight (RSP)': ('#8c959f', ':', 1.6)}
    for k, (col, ls, lw) in sty.items():
        s = (N[k] - 1) * 100
        ax.plot(s.index, s, color=col, ls=ls, lw=lw, label=f'{k} (' + f'{s.dropna().iloc[-1]:+,.0f}%'.replace(',', '.') + ')')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Universo point-in-time (S&P 500 de cada trimestre): retorno total acumulado', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / f'rolling_pit_acumulado{SUF}.png'); plt.close(fig)

    # 2) janelas moveis
    O, G, R, U = 'Opportunity of Lifetime (todas)', 'Good Companies, Great Returns (ROIC 10–12%)', 'Demais classes (todas as outras)', 'Universo EW (contraprova)'
    S = 'S&P 500 (SPY)'
    out += ['', '## 2. Janelas móveis (passo mensal)\n',
            'Para cada janela, comparo o retorno acumulado. "Ordem completa" = OoL > Good Companies > S&P 500 > demais classes. '
            'As janelas se sobrepõem, então não são independentes: a contagem mostra a experiência de quem entrou em cada mês.\n',
            '| Janela | Nº de janelas | OoL > S&P 500 | OoL > contraprova | GCGR > S&P 500 | OoL > GCGR | GCGR > demais | **Ordem completa** | OoL − S&P 500 (mediana a.a.) | Pior janela OoL − S&P 500 (a.a.) |',
            '|---|---|---|---|---|---|---|---|---|---|']
    curves = {}
    for yrs in (1, 3, 5, 8, 10):
        k = 12 * yrs
        W = (M / M.shift(k) - 1).dropna()
        if W.empty: continue
        ann = (1 + W) ** (1 / yrs) - 1
        d_os = ann[O] - ann[S]
        order = (W[O] > W[G]) & (W[G] > W[S]) & (W[S] > W[R])
        out.append(f'| {yrs} ano{"s" if yrs > 1 else ""} | {len(W)} | {(W[O] > W[S]).mean():.0%} | {(W[O] > W[U]).mean():.0%} | {(W[G] > W[S]).mean():.0%} | '
                   f'{(W[O] > W[G]).mean():.0%} | {(W[G] > W[R]).mean():.0%} | **{order.mean():.0%}** | {sg(d_os.median())} | {sg(d_os.min())} |')
        curves[yrs] = d_os
    # subclasses nas janelas
    out += ['', '### Subclasses da Opportunity of Lifetime contra o S&P 500\n',
            '| Janela | High Returns > S&P | High Growth > S&P | OoL Base > S&P | High Returns − S&P (mediana a.a.) | High Growth − S&P (mediana a.a.) | OoL Base − S&P (mediana a.a.) |',
            '|---|---|---|---|---|---|---|']
    for yrs in (1, 3, 5, 8, 10):
        k = 12 * yrs
        W = (M / M.shift(k) - 1).dropna()
        if W.empty: continue
        ann = (1 + W) ** (1 / yrs) - 1
        hr, hg, bs = 'OoL High Returns (ROIC > 30%)', 'OoL High Growth (EPS > 30%)', 'OoL Base'
        out.append(f'| {yrs} ano{"s" if yrs > 1 else ""} | {(W[hr] > W[S]).mean():.0%} | {(W[hg] > W[S]).mean():.0%} | {(W[bs] > W[S]).mean():.0%} | '
                   f'{sg((ann[hr] - ann[S]).median())} | {sg((ann[hg] - ann[S]).median())} | {sg((ann[bs] - ann[S]).median())} |')
    (ROOT / f'rolling_pit{SUF}.md').write_text('\n'.join(out))
    # grafico das janelas
    fig, ax = plt.subplots(figsize=(11, 5), dpi=140)
    for (yrs, s), col in zip(curves.items(), ['#d0d7de', '#8c959f', '#1f6feb', '#8250df', '#000000']):
        ax.plot(s.index, s * 100, color=col, lw=1.8 if yrs >= 5 else 1.2, label=f'Janela de {yrs} ano{"s" if yrs > 1 else ""}')
    ax.axhline(0, color='#cf222e', lw=1); ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:+.0f} p.p.'))
    ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax.set_title('Opportunity of Lifetime − S&P 500: excesso anualizado em cada janela (data = fim da janela)', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / f'rolling_pit_janelas{SUF}.png'); plt.close(fig)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
