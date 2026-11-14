"""Formula Magica com G (pre-registrada em 2026-11-14): ROIC + crescimento + multiplo (EV/EBIT ou P/L). Saida: backtest/magic_g.md e .png"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import D  # noqa: E402
from roic3_backtest import top20  # noqa: E402
from pesos import DUAL  # noqa: E402


def score(x, cols):
    """cols: lista de (coluna, ascendente?). Soma das posicoes por data."""
    s = 0
    for col, asc in cols: s = s + x.groupby('date')[col].rank(ascending=asc)
    return s


def build(F, n, wt='eq'):
    out = {}
    for d, g in F.groupby('date'):
        g = g.assign(firm=g.ticker.map(lambda t: DUAL.get(t, t))).sort_values('score').drop_duplicates('firm')  # classe dupla conta uma vez
        ch = g.head(n)
        out[d] = pd.Series(1.0, index=ch.ticker) if wt == 'eq' else top_n.cap(pd.Series(np.sqrt(ch.mcap.values), index=ch.ticker), .10)
    return out


def annual(W, adj, dates):
    ann = []
    for k in range(4):
        ds = sorted(set([d for i, d in enumerate(dates) if i % 4 == k] + [dates[-1]]))
        ann.append(run_weighted({d: W[d] for d in ds if d in W}, adj, ds))
    t0 = max(a.index[0] for a in ann)
    return pd.concat([a.loc[t0:] / a.loc[t0:].iloc[0] for a in ann], axis=1).ffill().mean(axis=1)


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    c = bm.classify_new(f); sec, _ = bm.sector_maps(); c['sector'] = c.ticker.map(sec)
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    M = pd.read_csv(D / 'magic_features.csv', parse_dates=['date'])
    base = c.merge(M[['date', 'ticker', 'ebit', 'ev', 'roc', 'ey', 'mcap']], on=['date', 'ticker'], how='left')
    allm = c.copy(); allm['mcap'] = top_n.mcap_us(allm, allm)
    V = {}
    x = base[~base.fin & (base.sector != 'Utilities') & (base.ebit > 0) & (base.ev > 0) & base.roic.notna() & base.growth.notna()].copy()
    x['ev_ebit'] = x.ev / x.ebit; x['score'] = score(x, [('roic', False), ('growth', False), ('ev_ebit', True)]); V['1. ROIC + G + EV/EBIT'] = x
    V['4. ROIC + G + EV/EBIT, sem cíclicos e vestuário'] = x[~x.excluded].assign(score=lambda d: score(d, [('roic', False), ('growth', False), ('ev_ebit', True)]))
    y = base[~base.fin & (base.sector != 'Utilities') & base.pe.notna() & base.roic.notna() & base.growth.notna() & base.mcap.notna()].copy()
    y['score'] = score(y, [('roic', False), ('growth', False), ('pe', True)]); V['2. ROIC + G + P/L'] = y
    z = allm[allm.pe.notna() & allm.roic.notna() & allm.growth.notna() & allm.mcap.notna()].copy()
    z['score'] = score(z, [('roic', False), ('growth', False), ('pe', True)]); V['3. ROIC + G + P/L, com financeiras e utilities'] = z
    V['5. ROIC + G + P/L, sem cíclicos e vestuário'] = y[~y.excluded].assign(score=lambda d: score(d, [('roic', False), ('growth', False), ('pe', True)]))
    V['6. ROIC + G + P/L, sem cíclicos e vestuário, com financeiras e utilities'] = z[~z.excluded].assign(score=lambda d: score(d, [('roic', False), ('growth', False), ('pe', True)]))
    o = base[~base.fin & (base.sector != 'Utilities') & base.roc.notna() & base.ey.notna()].copy()
    o['score'] = score(o, [('roc', False), ('ey', False)])
    navs, n, _, _ = bm.load_benchmarks()
    navs['Top 20 da estratégia (OoL, raiz)'] = top20(c, adj, dates); n['Top 20 da estratégia (OoL, raiz)'] = 20
    navs['Fórmula Mágica original — Top 20, peso igual'] = run_weighted(build(o, 20), adj, dates); n['Fórmula Mágica original — Top 20, peso igual'] = 20
    navs['Fórmula Mágica original — Top 20, raiz'] = run_weighted(build(o, 20, 'sqrt'), adj, dates); n['Fórmula Mágica original — Top 20, raiz'] = 20
    for k, F in V.items():
        main_ = k[:2] in ('1.', '2.', '5.')
        navs[f'{k} — Top 20, peso igual'] = run_weighted(build(F, 20), adj, dates); n[f'{k} — Top 20, peso igual'] = 20
        navs[f'{k} — Top 20, raiz'] = run_weighted(build(F, 20, 'sqrt'), adj, dates); n[f'{k} — Top 20, raiz'] = 20
        if main_:
            navs[f'{k} — Top 30, peso igual'] = run_weighted(build(F, 30), adj, dates); n[f'{k} — Top 30, peso igual'] = 30
            navs[f'{k} — Top 30, troca anual'] = annual(build(F, 30), adj, dates); n[f'{k} — Top 30, troca anual'] = 30
        print(k, flush=True)
    out = ['# "Fórmula Mágica com G": ROIC + crescimento + múltiplo (pré-registrado em 2026-11-14)\n',
           '> ⚠️ **O ROIC pode estar errado** — aqui é o nosso ROIC triangulado (financeiras: ROE).\n',
           f'S&P 500 point-in-time, {dates[0]:%m/%Y} a {dates[-1]:%m/%Y}, trimestral salvo indicação, sem custos nem impostos. Soma das posições em cada critério; ficam as melhores.\n',
           '## 1. Período todo\n'] + bm.bench_table(navs, n)
    t1 = max(d for d in navs['S&P 500'].index if d <= pd.Timestamp('2019-12-31'))
    E = pd.read_csv(ROOT.parent / 'etfs' / 'navs_etf.csv', index_col=0, parse_dates=True)
    import yfinance as yf
    px = yf.download('SPYG', start='2019-06-01', progress=False, auto_adjust=True)['Close'].squeeze(); px.index = pd.to_datetime(px.index).tz_localize(None)
    keep = [k for k in navs if k in bm.ORDER or k.startswith('Top 20 da') or ('Top 20, raiz' in k) or k.startswith('Fórmula')]
    sub = {k: navs[k].loc[t1:] / navs[k].loc[t1:].iloc[0] for k in keep}
    s = px.loc[t1:dates[-1]].dropna(); sub['SPYG parado'] = s / s.iloc[0]
    for col in E.columns: q = E[col].loc[t1:].dropna(); sub[col] = q / q.iloc[0]
    out += ['', f'## 2. Período dos ETFs ({t1:%m/%Y}–{dates[-1]:%m/%Y})\n'] + bm.bench_table(sub, n)
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    for k in ('5. ROIC + G + P/L, sem cíclicos e vestuário', '4. ROIC + G + EV/EBIT, sem cíclicos e vestuário'):
        F = V[k]; l = F[F.date == F.date.max()].assign(firm=lambda d: d.ticker.map(lambda t: DUAL.get(t, t))).sort_values('score').drop_duplicates('firm').head(20)
        out += ['', f'## Hoje ({F.date.max():%m/%Y}) — {k}, Top 20\n', '| # | Ação | Empresa | Setor | ROIC | Crescimento | ' + ('EV/EBIT' if 'EV' in k else 'P/L') + ' |', '|---|---|---|---|---|---|---|']
        out += [f"| {i} | {r.ticker} | {str(u.name.get(r.ticker, r.ticker))[:28]} | {r.sector} | {r.roic:.0%} | {r.growth:.0%} | {(r.ev_ebit if 'EV' in k else r.pe):.1f} |".replace('.', ',')
                for i, r in enumerate(l.itertuples(), 1)]
    (ROOT / 'magic_g.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or k.startswith('Top 20 da') or k in ('Fórmula Mágica original — Top 20, peso igual',
                   '1. ROIC + G + EV/EBIT — Top 20, peso igual', '1. ROIC + G + EV/EBIT — Top 20, raiz', '2. ROIC + G + P/L — Top 20, raiz', '4. ROIC + G + EV/EBIT, sem cíclicos e vestuário — Top 20, raiz', '5. ROIC + G + P/L, sem cíclicos e vestuário — Top 20, raiz')},
                  ROOT / 'magic_g.png', 'Fórmula Mágica com G × original × Top 20 OoL × comparativos obrigatórios (S&P 500)')


if __name__ == '__main__':
    main()
