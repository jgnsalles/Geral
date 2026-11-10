"""Regra congelada (2026-11-10) contra (1) modelos nulos simples, (2) ETFs rivais de qualidade/crescimento/momentum e (3) fatores.
Modelos nulos (universo point-in-time, mesmas exclusoes de setor e mesma ponderacao):
  N1 "So ROIC e crescimento": ROIC >= 12% e crescimento do EPS >= 15% (os cortes de qualidade da OoL, sem zGrowth, sem retorno esperado/P-E justo).
  N2 "Ambos > 30%": ROIC > 30% e crescimento > 30% (so magnitude).
  N3 "So ROIC > 30%" e N4 "So crescimento > 30%" (ROIC >= 12%): equivalentes simples da High ROIC e da High Growth.
ETFs: QUAL (qualidade MSCI), MTUM (momentum), IWF (Russell 1000 Growth), SPYG (S&P 500 Growth), QQQ (Nasdaq-100).
Fatores: Fama-French 5 + momentum + QMJ (AQR), mensal, Newey-West 6 defasagens.
Saidas: backtest/rivais_nulo.md, backtest/rivais_nulo.png. Uso: python3 backtest/rivais_nulo.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, shares, DUAL  # noqa: E402
from backtest import stats, D  # noqa: E402
from validation_factors import factors, reg  # noqa: E402

pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
pp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.1f}'.replace('.', ',')
n2 = lambda x: '—' if pd.isna(x) else f'{x:.2f}'.replace('.', ',')


def main():
    f, dates = bm.base_data()
    adj = bm.load_prices()['adj_close']
    c = bm.classify_new(f)  # tem roic, growth, excluded, cat
    ok = ~c.excluded & c.cat.notna()
    hn = bm.holdings_new(c)
    H = {'OoL novo': hn['OoL novo'], 'OoL High ROIC (novo)': hn['OoL High ROIC (novo)'], 'OoL High Growth (novo)': hn['OoL High Growth (novo)'],
         'GCGR novo': hn['GCGR novo'],
         'N1: só ROIC ≥ 12% e crescimento ≥ 15%': ok & (c.roic >= .12) & (c.growth >= .15),
         'N2: ROIC > 30% e crescimento > 30%': ok & (c.roic > .30) & (c.growth > .30),
         'N3: ROIC > 30% (e crescimento ≥ 15%)': ok & (c.roic > .30) & (c.growth >= .15),
         'N4: crescimento > 30% (e ROIC ≥ 12%)': ok & (c.growth > .30) & (c.roic >= .12)}
    sh = shares(pd.concat([c[m][['date', 'ticker', 'eps', 'last_fy', 'price']] for m in H.values()]).drop_duplicates(['date', 'ticker']))
    navs, n = {}, {}
    for k, m in H.items():
        x = c[m].copy()
        x['mcap'] = [p * sh.get((d, t), np.nan) for d, t, p in zip(x.date, x.ticker, x.price)]
        x['mcap'] = x.mcap.where(x.mcap > 0); x['mcap'] = x.mcap.fillna(x.groupby('date').mcap.transform('median'))
        x['firm'] = x.ticker.map(lambda t: DUAL.get(t, t)); x['mcap'] = x.mcap / x.groupby(['date', 'firm']).ticker.transform('size')
        for wn, fn in (('raiz', lambda g: np.sqrt(g.mcap.values)), ('peso igual', lambda g: np.ones(len(g)))):
            navs[f'{k} — {wn}'] = run_weighted({d: pd.Series(fn(g), index=g.ticker) for d, g in x.groupby('date')}, adj, dates)
            n[f'{k} — {wn}'] = x.groupby('date').size().mean()
        print(k, flush=True)
    E = pd.read_csv(D / 'etfs_rivais.csv', index_col=0, parse_dates=True)
    ETF = {'SPY': 'S&P 500 (SPY)', 'RSP': 'S&P 500 equal weight (RSP)', 'QUAL': 'Qualidade (QUAL)', 'MTUM': 'Momentum (MTUM)',
           'IWF': 'Russell 1000 Growth (IWF)', 'SPYG': 'S&P 500 Growth (SPYG)', 'QQQ': 'Nasdaq-100 (QQQ)'}
    for t, lab in ETF.items():
        s = E[t].loc[dates[0]:dates[-1]].dropna(); navs[lab] = s / s.iloc[0]
    # periodo comum: a partir do inicio do QUAL
    c0 = E['QUAL'].first_valid_index(); c0 = max(d for d in navs['S&P 500 (SPY)'].index if d <= c0 + pd.Timedelta(days=10))
    def stc(s, a=None):
        s = s.dropna();
        if a is not None: s = s.loc[a:]; s = s / s.iloc[0]
        return stats(s)
    S_all, S_com = stc(navs['S&P 500 (SPY)'])['CAGR'], stc(navs['S&P 500 (SPY)'], c0)['CAGR']
    order = [k for k in navs if k.startswith('OoL novo')] + [k for k in navs if 'High ROIC (novo)' in k] + [k for k in navs if 'High Growth (novo)' in k] + \
            [k for k in navs if k.startswith('GCGR novo')] + [k for k in navs if k[:2] in ('N1', 'N2', 'N3', 'N4')] + list(ETF.values())
    out = ['# Regra congelada × modelos nulos × ETFs rivais × fatores (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** os modelos nulos usam o mesmo ROIC oficial (corrigido em 2026-11-10); um erro nele afeta todos igualmente. Ainda em aberto: '
           'patrimônio negativo e ROIC > 100% em empresas leves em ativos.\n',
           '**Regra congelada** = OoL novo / High ROIC / High Growth / GCGR novo, com a **raiz do valor de mercado** como ponderação principal. '
           '**Modelos nulos** = filtros simples, sem P/E justo, sem retorno esperado e sem zGrowth, com as mesmas exclusões de setor e as mesmas ponderações. '
           f'ETFs a partir da data em que existem; o período comum começa em {c0:%m/%Y} (início do QUAL).\n',
           '## 1. Retornos\n', '| Carteira | Ações | Retorno anual (período todo) | vs S&P | Retorno anual (período comum) | vs S&P (comum) | Pior queda |',
           '|---|---|---|---|---|---|---|']
    for k in order:
        a = stc(navs[k]); b = stc(navs[k], c0)
        full = k not in ETF.values() or navs[k].index[0] <= navs['S&P 500 (SPY)'].index[0] + pd.Timedelta(days=10)
        out.append(f"| {k} | {n[k]:.0f} | {pc(a['CAGR']) if full else '—'} | {pp(a['CAGR'] - S_all) if full else '—'} | **{pc(b['CAGR'])}** | {pp(b['CAGR'] - S_com)} | {pc(a['MaxDD'])} |"
                   .replace('| nan |', '| — |') if k in n else
                   f"| {k} | — | {pc(a['CAGR']) if full else '—'} | {pp(a['CAGR'] - S_all) if full else '—'} | **{pc(b['CAGR'])}** | {pp(b['CAGR'] - S_com)} | {pc(a['MaxDD'])} |")
    # o que a camada de valuation agrega: regra - N1 (mesmos cortes de qualidade, sem valuation)
    out += ['', '### O P/E justo e o retorno esperado agregam? (regra − modelo nulo equivalente, período todo, p.p. a.a.)\n',
            '| Comparação | Raiz | Peso igual |', '|---|---|---|']
    for a, b in (('OoL novo', 'N1: só ROIC ≥ 12% e crescimento ≥ 15%'), ('OoL High ROIC (novo)', 'N3: ROIC > 30% (e crescimento ≥ 15%)'),
                 ('OoL High Growth (novo)', 'N4: crescimento > 30% (e ROIC ≥ 12%)')):
        out.append(f"| {a} − {b.split(':')[0]} | {pp(stc(navs[a + ' — raiz'])['CAGR'] - stc(navs[b + ' — raiz'])['CAGR'])} | "
                   f"{pp(stc(navs[a + ' — peso igual'])['CAGR'] - stc(navs[b + ' — peso igual'])['CAGR'])} |")
    # fatores
    Fct = factors(); cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'UMD', 'QMJ']
    out += ['', '## 2. Regressão de fatores (mensal, retorno − taxa livre)\n',
            f'Fama-French 5 + momentum (UMD) + qualidade (QMJ, AQR). Erros de Newey-West. Meses disponíveis até {Fct.dropna().index.max():%m/%Y}.\n',
            '| Carteira | Alfa a.a. | t do alfa | Mercado | Tamanho (SMB) | Valor (HML) | Rentabilidade (RMW) | Investimento (CMA) | Momentum | Qualidade (QMJ) | R² |',
            '|---|---|---|---|---|---|---|---|---|---|---|']
    for k in order:
        r = navs[k].resample('ME').last().pct_change().dropna()
        y = r - Fct['RF'].reindex(r.index)
        m, nobs = reg(y, Fct[cols].reindex(r.index))
        a, t = m.params['const'] * 12, m.tvalues['const']
        bold = '**' if abs(t) >= 2 else ''
        out.append(f"| {k} | {bold}{pp(a)}{bold} | {bold}{n2(t)}{bold} | " + ' | '.join(n2(m.params[cc]) for cc in cols) + f' | {n2(m.rsquared)} |')
    (ROOT / 'rivais_nulo.md').write_text('\n'.join(out)); print('\n'.join(out))
    keep = ['OoL novo — raiz', 'OoL High ROIC (novo) — raiz', 'OoL High Growth (novo) — raiz', 'N1: só ROIC ≥ 12% e crescimento ≥ 15% — raiz',
            'N2: ROIC > 30% e crescimento > 30% — raiz'] + list(ETF.values())
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    cols_ = ['#1f6feb', '#2da44e', '#8250df', '#57606a', '#bf8700', '#000000', '#8c959f', '#cf222e', '#e8590c', '#0a7ea4', '#953800', '#6e40c9']
    for k, col in zip(keep, cols_):
        s = navs[k].loc[c0:]; s = s / s.iloc[0]
        ax.plot(s.index, (s - 1) * 100, color=col, lw=2.4 if k.startswith('OoL novo') else 1.4, ls='--' if '(' in k and k in ETF.values() else '-',
                label=f'{k} (' + pc(stats(s)['CAGR']) + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=7, loc='upper left')
    ax.set_title(f'Regra congelada × modelos nulos × ETFs rivais, desde {c0:%m/%Y} — retorno total acumulado', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'rivais_nulo.png'); plt.close(fig)


if __name__ == '__main__':
    main()
