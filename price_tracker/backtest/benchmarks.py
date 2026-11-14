"""Comparativos obrigatorios de toda analise de desempenho (instrucao permanente do usuario, 2026-11-10):
S&P 500, S&P 500 equal weight, OoL antigo, GCGR antigo, OoL novo, GCGR novo, OoL High ROIC (novo), OoL High Growth (novo).
Antigo = cortes originais (ROIC 20%/10%, zROIC 0,7). Novo = esboco (ROIC 12%/10%), sem zROIC, sem vestuario e sem subsetores ciclicos
(regua de ciclicos.py, menos as excecoes NOT_CYCLICAL); as acoes de subsetores ciclicos que seriam OoL ou GCGR vao para a classe Cyclicals (desde 2026-11-10).
Universo point-in-time, ROIC oficial (corrigido em 2026-11-10), equal weight, rebalanceamento trimestral.
Uso: from benchmarks import load_benchmarks, bench_table, bench_plot"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
EXCL_SECTORS = {'Energy', 'Materials'}
APPAREL = {'Apparel, Accessories & Luxury Goods', 'Footwear', 'Textiles'}
ORDER = ['S&P 500', 'S&P 500 equal weight', 'OoL antigo', 'GCGR antigo', 'OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)', 'Cyclicals']
STYLE = {'S&P 500': ('#000000', '--', 2.0), 'S&P 500 equal weight': ('#8c959f', ':', 1.8), 'OoL antigo': ('#54aeff', '-', 1.4),
         'GCGR antigo': ('#f0a35e', '-', 1.4), 'OoL novo': ('#1f6feb', '-', 2.6), 'GCGR novo': ('#e8590c', '-', 2.4),
         'OoL High ROIC (novo)': ('#2da44e', '-', 1.8), 'OoL High Growth (novo)': ('#8250df', '-', 1.8), 'Cyclicals': ('#bf8700', '--', 1.8)}


def sector_maps():
    import setores_derrotas as sd
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    sec = lambda t: sd.MANUAL[t][0] if t in sd.MANUAL else u.sector.get(t)
    ind = lambda t: sd.MANUAL[t][1] if t in sd.MANUAL else u.industry.get(t)
    return sec, ind


ROIC_FILE = 'roic3.csv'  # 2026-11-14 (decisao do usuario): ROIC triangulado com regra de outliers e o oficial nos EUA; None = definicao antiga (B)


def base_data(roic=ROIC_FILE):
    """roic: arquivo do ROIC triangulado (empresas operacionais; financeiras seguem com ROE) ou None para a definicao antiga."""
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member].reset_index(drop=True)
    if roic:
        r3 = pd.read_csv(D / roic, parse_dates=['date'])[['date', 'ticker', 'roic_tri']]
        f = f.merge(r3, on=['date', 'ticker'], how='left')
        f['roic_antigo'] = f.roic
        f['roic'] = np.where(f.fin, f.roic, f.roic_tri); f = f.drop(columns='roic_tri')
    return f, dates


def classify_new(f, stability=None, cyc=None):
    """Classificacao 'nova'. stability: None = sem criterio de estabilidade do ROIC; ou serie booleana (True = estavel)."""
    z = 0.0 if stability is None else np.where(stability, 0.0, 9.0)
    c = vp.classify(f.assign(zroic=z), 'sketch', 'B')
    sec, ind = sector_maps()
    c['sector'] = c.ticker.map(sec); c['industry'] = c.ticker.map(ind)
    from ciclicos import cyclical_industries, canon
    if cyc is None: cyc = cyclical_industries()
    c['cyclical'] = c.industry.map(canon).isin(cyc)
    c['excluded'] = c.cyclical | c.industry.isin(APPAREL)
    return c


def holdings_new(c):
    ok = ~c.excluded; ool = (c.cat == OOL) & ok
    return {'OoL novo': ool, 'GCGR novo': (c.cat == GCGR) & ok, 'OoL High ROIC (novo)': ool & (c.roic > 0.30),
            'OoL High Growth (novo)': ool & (c.growth > 0.30),
            'Cyclicals': c.cat.isin([OOL, GCGR]) & c.cyclical & ~c.industry.isin(APPAREL)}


def load_benchmarks(extra=None):
    """Devolve (navs, n_acoes, dates, adj). extra: dict nome -> (classificacao, mascara) para carteiras adicionais."""
    f, dates = base_data()
    adj = load_prices()['adj_close']
    old = vp.classify(f, 'orig', 'B')
    new = classify_new(f)
    H = {'OoL antigo': (old, old.cat == OOL), 'GCGR antigo': (old, old.cat == GCGR)}
    H.update({k: (new, m) for k, m in holdings_new(new).items()})
    if extra: H.update(extra)
    navs, n = {}, {}
    for k, (c, m) in H.items():
        navs[k] = run_portfolio({d: g.ticker.tolist() for d, g in c[m].groupby('date')}, adj, dates)[0]
        n[k] = c[m].groupby('date').size().mean()
    for b, nm in (('SPY', 'S&P 500'), ('RSP', 'S&P 500 equal weight')):
        s = adj[b].loc[dates[0]:dates[-1]]; navs[nm] = s / s.iloc[0]
    return navs, n, dates, adj


def windows(nav, ref, years):
    """% das janelas moveis (mensais) de `years` anos em que nav bate ref, e a pior diferenca anualizada (p.p.)."""
    M, R = nav.dropna().resample('ME').last(), ref.dropna().resample('ME').last()
    k = 12 * years; a = (M / M.shift(k)) ** (1 / years); b = ((R / R.shift(k)) ** (1 / years)).reindex(a.index)
    ok = a.notna() & b.notna()
    if not ok.any(): return np.nan, np.nan
    d = (a - b)[ok]
    return (d > 0).mean(), d.min()


def bench_table(navs, n, ref='S&P 500'):
    """Tabela padrao (pedido do usuario, 2026-11-14): sempre com janelas moveis de 3, 5 e 10 anos contra o S&P 500 (ou `ref`)."""
    pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
    pw = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
    pp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.1f}'.replace('.', ',')
    R = navs[ref]
    keys = ORDER + [k for k in navs if k not in ORDER]
    out = [f'| Carteira | Retorno total | Retorno anual | Volatilidade | Pior queda | Ações (média) | Janelas 3a > {ref} | Janelas 5a > {ref} | Janelas 10a > {ref} | Pior janela 3a (p.p./ano) | Pior janela 5a (p.p./ano) |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for k in keys:
        if k not in navs: continue
        s = navs[k].dropna(); st = stats(s)
        w = {y: windows(s, R, y) if k != ref else (np.nan, np.nan) for y in (3, 5, 10)}
        bold = '**' if k in ('OoL novo', 'GCGR novo') else ''
        out.append(f"| {bold}{k}{bold} | {pc(s.iloc[-1] - 1)} | {bold}{pc(st['CAGR'])}{bold} | {pc(st['Vol'])} | {pc(st['MaxDD'])} | "
                   f"{'—' if k not in n or pd.isna(n[k]) else f'{n[k]:.0f}'} | {pw(w[3][0])} | {pw(w[5][0])} | {pw(w[10][0])} | {pp(w[3][1])} | {pp(w[5][1])} |")
    return out


def bench_plot(navs, path, title):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    keys = ORDER + [k for k in navs if k not in ORDER]
    extra_cols = iter(['#cf222e', '#bf8700', '#0a7ea4', '#6e7781', '#d4a72c', '#a40e26', '#116329', '#953800', '#4c2889', '#57606a'])
    for k in keys:
        if k not in navs: continue
        col, ls, lw = STYLE[k] if k in STYLE else (next(extra_cols), '-.', 2.0)
        s = (navs[k] - 1) * 100
        ax.plot(s.index, s, color=col, ls=ls, lw=lw, label=f'{k} (' + f'{stats(navs[k].dropna())["CAGR"]:.1%}'.replace('.', ',') + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title(title, fontsize=10)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


if __name__ == '__main__':
    navs, n, dates, adj = load_benchmarks()
    print('\n'.join(bench_table(navs, n)))
    bench_plot(navs, ROOT / 'benchmarks.png', 'Comparativos obrigatórios — universo point-in-time, retorno total acumulado')
