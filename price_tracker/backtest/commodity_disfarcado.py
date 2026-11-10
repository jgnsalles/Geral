"""Quem e um "commodity disfarcado" (fora de Energia e Materiais) e o efeito de tirar Energia, Materiais, vestuario e esses nomes.
Dois sinais point-in-time, com limiares fixados antes de olhar o resultado:
  (1) Mercado: regressao dos 60 meses anteriores do retorno mensal da acao contra S&P 500 (SPY) e um fator de commodities
      (50% DBC + 25% XLE + 25% XLB). Commodity disfarcado se t do fator de commodities >= 2.
  (2) Lucro: nos ultimos 10 exercicios arquivados, 2 ou mais anos com queda do EPS > 25% (ou passagem para prejuizo).
"Commodity disfarcado" = (1) ou (2). Sem zROIC, universo point-in-time, ROIC oficial corrigido, esboco (OoL a partir de 12%).
Saidas: backtest/commodity_disfarcado.md, backtest/commodity_disfarcado.png
Uso: python3 backtest/commodity_disfarcado.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, load_pit, asof, split_factor_after, D  # noqa: E402
from validation_core import load_prices  # noqa: E402
import setores_derrotas as sd  # noqa: E402

OOL, GCGR = sd.OOL, sd.GCGR
APPAREL = {'Apparel, Accessories & Luxury Goods', 'Footwear', 'Textiles'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
pc1 = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def comm_t(r, mkt, cmd, d):
    """t do fator de commodities na regressao dos 60 meses ate d."""
    y = r.loc[:d].iloc[-60:]
    X = pd.concat([mkt, cmd], axis=1).reindex(y.index)
    m = y.notna() & X.notna().all(axis=1)
    if m.sum() < 36: return np.nan, np.nan
    y, X = y[m].values, np.c_[np.ones(m.sum()), X[m].values]
    b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; s2 = e @ e / (len(y) - 3); cov = s2 * np.linalg.inv(X.T @ X)
    return b[2] / np.sqrt(cov[2, 2]), b[2]


def eps_drops(pit, d, splits):
    e, _ = asof(pit['eps_diluted'], d)
    if not e: return np.nan
    last = max(e); v = {y: e[y][0] / split_factor_after(splits, e[y][1]) for y in e if last - 10 <= y <= last}
    n = 0
    for y in range(last - 9, last + 1):
        a, b = v.get(y - 1), v.get(y)
        if a is None or b is None or a <= 0: continue
        if b / a - 1 < -0.25: n += 1
    return n


def main():
    c = pd.read_csv(ROOT / 'atributos.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    xe = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
    c['sector'] = c.ticker.map(lambda t: sd.MANUAL[t][0] if t in sd.MANUAL else u.sector.get(t))
    c['industry'] = c.ticker.map(lambda t: sd.MANUAL[t][1] if t in sd.MANUAL else u.industry.get(t))
    name = lambda t: u.name.get(t) if t in u.index else xe.sec_name.get(t, t)
    px_ = load_prices(); adj = px_['adj_close']; spl = px_['stock_splits']
    etf = pd.read_csv(D / 'commodity_etfs.csv', index_col=0, parse_dates=True)
    mret = lambda s: s.resample('ME').last().pct_change()
    cmd = (0.5 * mret(etf.DBC) + 0.25 * mret(etf.XLE) + 0.25 * mret(etf.XLB)).rename('cmd')
    mkt = mret(adj.SPY).rename('mkt')
    R = adj.resample('ME').last().pct_change()
    ts, bs, dr, cache = [], [], [], {}
    for r in c[['date', 'ticker']].itertuples():
        d = r.date
        if r.ticker in R:
            t_, b_ = comm_t(R[r.ticker], mkt, cmd, d)
        else:
            t_, b_ = np.nan, np.nan
        if r.ticker not in cache: cache[r.ticker] = load_pit(r.ticker)
        s = spl[r.ticker][spl[r.ticker] > 0] if r.ticker in spl else pd.Series(dtype=float)
        ts.append(t_); bs.append(b_); dr.append(eps_drops(cache[r.ticker], d, s))
    c['cmd_t'], c['cmd_b'], c['eps_drops'] = ts, bs, dr
    c['sig_mkt'] = c.cmd_t >= 2; c['sig_eps'] = c.eps_drops >= 2
    c['disf'] = (c.sig_mkt | c.sig_eps) & ~c.sector.isin(['Energy', 'Materials'])
    c['em'] = c.sector.isin(['Energy', 'Materials']); c['app'] = c.industry.isin(APPAREL)
    c.to_csv(ROOT / 'commodity_disfarcado.csv', index=False)

    out = ['# Commodity disfarçado: quem é e o efeito de retirar (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). Commodities disfarçados costumam ter ROIC alto só no pico do ciclo; '
           'o ROIC entra na seleção e no P/E justo.\n',
           '**Definição (limiares fixados antes de ver o resultado), medida em cada trimestre só com dados passados:**\n',
           '1. **Sinal de mercado:** nos 60 meses anteriores, o retorno da ação responde a commodities além do mercado — regressão do retorno mensal contra '
           'S&P 500 e um fator de commodities (50% DBC + 25% XLE + 25% XLB), com t do fator de commodities ≥ 2.',
           '2. **Sinal de lucro:** nos 10 últimos exercícios, 2 ou mais anos com queda do EPS acima de 25% (ou ida para prejuízo).\n',
           'Commodity disfarçado = sinal 1 ou 2, fora de Energia e Materiais. Configuração: sem zROIC, OoL a partir de ROIC 12%.\n']
    # desempenho das posicoes
    out += ['## 1. Desempenho das posições (excesso sobre o universo no trimestre seguinte, a.a.)\n',
            '| Classe | Grupo | Posições | Excesso médio | Excesso mediano | % acima do universo |', '|---|---|---|---|---|---|']
    for cat in (OOL, GCGR):
        x = c[c.cat == cat]
        for lab, m in (('Energia e Materiais', x.em), ('Vestuário', x.app), ('Commodity disfarçado: só sinal de mercado', x.disf & x.sig_mkt & ~x.sig_eps),
                       ('Commodity disfarçado: só sinal de lucro', x.disf & x.sig_eps & ~x.sig_mkt), ('Commodity disfarçado: os dois sinais', x.disf & x.sig_eps & x.sig_mkt),
                       ('Demais', ~x.em & ~x.app & ~x.disf)):
            y = x[m]
            out.append(f"| {'OoL' if cat == OOL else 'GCGR'} | {lab} | {len(y)} | {sg(y.ex.mean() * 4)} | {sg(y.ex.median() * 4)} | {pc((y.ex > 0).mean())} |")
    # carteiras
    dates = sorted(c.date.unique()); last = adj.index[adj.index <= dates[-1] + pd.offsets.QuarterEnd()][-1]
    dates = [pd.Timestamp(d) for d in dates] + [last]
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; Ms = spy.resample('ME').last(); S = stats(spy)['CAGR']
    ool = c.cat == OOL
    G = {'OoL': ool, 'OoL High Returns': ool & (c.roic > .3), 'OoL High Growth': ool & (c.growth > .3), 'OoL Base': ool & (c.roic <= .3) & (c.growth <= .3),
         'GCGR': c.cat == GCGR}
    V = {'Atual': np.ones(len(c), bool), 'Sem Energia e Materiais': ~c.em, '+ sem vestuário': ~c.em & ~c.app,
         '+ sem commodity disfarçado': ~c.em & ~c.app & ~c.disf}
    out += ['', '## 2. Carteiras\n', f'S&P 500: {pc1(S)} a.a. Entre parênteses: ações por trimestre; janelas de 5 anos acima do S&P.\n',
            '| Carteira | ' + ' | '.join(V) + ' |', '|---|' + '---|' * len(V)]
    curves = {}
    for k, m in G.items():
        row = [k]
        for vn, vm in V.items():
            mm = m & vm
            nav = run_portfolio({d: g.ticker.tolist() for d, g in c[mm].groupby('date')}, adj, dates)[0]
            Mn = nav.resample('ME').last(); w5 = ((Mn / Mn.shift(60)) > (Ms / Ms.shift(60))).dropna().mean()
            row.append(f"**{pc1(stats(nav)['CAGR'])}** ({c[mm].groupby('date').size().mean():.0f}; {pc(w5)})")
            if k == 'OoL': curves[vn] = nav
        out.append('| ' + ' | '.join(row) + ' |')
    # quem sao
    x = c[c.disf]
    e = x.groupby('ticker').agg(q=('ex', 'size'), ex=('ex', 'mean'), t=('cmd_t', 'median'), drops=('eps_drops', 'max'), sector=('sector', 'first'),
                                industry=('industry', 'first'), mk=('sig_mkt', 'mean'), ep=('sig_eps', 'mean'),
                                cls=('cat', lambda s: '/'.join(sorted({'OoL' if v == OOL else 'GCGR' for v in s}))))
    tot = c.groupby('ticker').size(); e['share'] = e.q / tot.reindex(e.index)
    e['ex'] *= 4
    out += ['', '## 3. Quem são os commodities disfarçados\n',
            f'{e.index.nunique()} empresas foram marcadas em pelo menos um trimestre em que estavam na OoL ou na GCGR. '
            '"t commodities" = mediana do t do fator de commodities nos trimestres marcados; "quedas de EPS" = máximo de anos com queda > 25% em 10.\n']
    for s_, g in e.sort_values('ex').groupby('sector'):
        out += [f'### {s_} ({len(g)})\n', '| Ticker | Empresa | Subsetor | Classe | Trim. marcados | Sinal de mercado | Sinal de lucro | t commodities | Quedas de EPS (10a) | Excesso médio a.a. (marcados) |',
                '|---|---|---|---|---|---|---|---|---|---|']
        for t, r in g.iterrows():
            out.append(f'| {t} | {name(t)} | {r.industry} | {r.cls} | {r.q} | {pc(r.mk)} | {pc(r.ep)} | {n1(r.t)} | {r.drops:.0f} | {sg(r.ex)} |')
        out.append('')
    (ROOT / 'commodity_disfarcado.md').write_text('\n'.join(out))
    print('\n'.join(out))
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=140)
    sty = {'Atual': ('#8c959f', '-'), 'Sem Energia e Materiais': ('#54aeff', '-'), '+ sem vestuário': ('#8250df', '-'), '+ sem commodity disfarçado': ('#1f6feb', '-')}
    for k, nav in curves.items():
        ax.plot(nav.index, (nav - 1) * 100, color=sty[k][0], lw=2.2 if k.startswith('+ sem c') else 1.6, label=f'OoL — {k} ({pc1(stats(nav)["CAGR"])} a.a.)')
    ax.plot(spy.index, (spy - 1) * 100, color='black', ls='--', lw=1.6, label=f'S&P 500 ({pc1(S)} a.a.)')
    ax.grid(alpha=.3); ax.legend(fontsize=8); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.')))
    ax.set_title('Opportunity of Lifetime: retirando setores cíclicos passo a passo — retorno total acumulado', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'commodity_disfarcado.png'); plt.close(fig)


if __name__ == '__main__':
    main()
