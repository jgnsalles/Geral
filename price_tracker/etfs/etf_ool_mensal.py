"""ETF com mais OoL trocado todo mes (pre-registrado em 2026-11-14). Saida: etfs/resultado_mensal.md e .png"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path.insert(0, str(P)); sys.path.insert(0, str(P / 'backtest')); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from roic3_backtest import top20  # noqa: E402
from etf_ool import ETFS, D  # noqa: E402

COLS = ['date', 'ticker', 'growth', 'zgrowth', 'roic', 'fair_pe', 'eps', 'dy', 'price', 'ex', 'mcap']


def ool_at(q, rel):
    """q: classificacao trimestral; rel: preco_novo/preco_antigo por ticker. Recalcula retorno esperado e o flag OoL."""
    x = q.copy(); x['r'] = x.ticker.map(rel); x = x[np.isfinite(x.r) & (x.r > 0)]
    p = x.price * x.r
    base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / p
    rf = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy; rc = x.growth + x.dy
    x['ret'] = np.where(np.isfinite(rf) & np.isfinite(rc), (rf + rc) / 2, x.growth)
    x['ool'] = (x.growth > .15) & (x.zgrowth < 2.93) & (x.roic > .12) & (x.ret > .20) & ~x.ex
    x['mcap'] = x.mcap * x.r
    return x.set_index('ticker')


def main():
    import yfinance as yf
    f, dates = bm.base_data(); c = bm.classify_new(f); c['mcap'] = top_n.mcap_us(c, c); c['ex'] = c.excluded
    ms, adj_ms, _, _ = pd.read_pickle(P / 'mundo' / 'cache' / 'backtest_ms.pkl'); ms['ex'] = ms.cyc | ms.app
    pr = bm.load_prices(); close, adj_us = pr['close'], pr['adj_close']
    h = pd.read_csv(D / 'holdings.csv', parse_dates=['filed', 'end']).merge(pd.read_csv(D / 'cusip_map.csv').dropna().drop_duplicates('cusip'), on='cusip', how='left')
    Q = sorted(d for d in dates if d >= pd.Timestamp('2019-12-31')); msd = sorted(ms.date.unique())
    me = close.loc[Q[0]:].resample('ME').last().index
    months = sorted({close.index[close.index <= m][-1] for m in me if m <= Q[-1] + pd.Timedelta(days=3)})
    px = yf.download(' '.join(ETFS), start='2019-06-01', progress=False, auto_adjust=True)['Close']; px.index = pd.to_datetime(px.index).tz_localize(None)
    px = px.reindex(adj_us.index.union(px.index)).ffill()
    rows = []
    for t in months:
        q0 = max(d for d in Q if d <= t); a = c[c.date == q0][COLS]
        rel_a = close.loc[:t].iloc[-1] / close.loc[q0]
        pa = ool_at(a, rel_a)
        m0 = max([d for d in msd if d <= q0 + pd.Timedelta(days=7)], default=None)
        if m0 is not None:
            b = ms[ms.date == m0][COLS]; rel_b = adj_ms.loc[:t].iloc[-1] / adj_ms.loc[:m0].iloc[-1]
            pb = ool_at(b, rel_b); pan = pd.concat([pa, pb[~pb.index.isin(pa.index)]])
        else: pan = pa
        for e in ETFS:
            if e == 'SPY': w = pa.mcap.dropna(); w = w / w.sum()
            else:
                x = h[(h.etf == e) & (h.filed <= t)]
                if x.empty: continue
                x = x[x.end == x.end.max()]; w = x.groupby('ticker').pct.sum(); w = w[w > 0]; w = w / w.sum()
            cov = w[w.index.isin(pan.index)]
            if cov.sum() < .5: continue
            rows.append(dict(date=t, etf=e, s1=(cov * pan.loc[cov.index].ool.astype(float)).sum() / cov.sum()))
    S = pd.DataFrame(rows)
    W = {t: pd.Series(1.0, index=[g.sort_values('s1', ascending=False).etf.iloc[0]]) for t, g in S.groupby('date')}
    W2 = {t: pd.Series(1.0, index=g.sort_values('s1', ascending=False).etf.iloc[:2]) for t, g in S.groupby('date')}
    T = months
    navs = {'ETF com mais OoL — troca mensal': run_weighted(W, px, T), 'Os 2 ETFs com mais OoL — troca mensal': run_weighted(W2, px, T)}
    q = pd.read_csv(ROOT / 'notas.csv', parse_dates=['date']); q = q[q['cov'] >= .5]
    Wq = {t: pd.Series(1.0, index=[g.sort_values('s1', ascending=False).etf.iloc[0]]) for t, g in q.groupby('date')}
    navs['ETF com mais OoL — troca trimestral'] = run_weighted(Wq, px, Q)
    t0 = T[0]
    bnav, bn, _, _ = bm.load_benchmarks()
    out_n = {k: v.loc[t0:] / v.loc[t0:].iloc[0] for k, v in bnav.items()}
    out_n['Top 20 da estratégia (ações)'] = (lambda v: v.loc[t0:] / v.loc[t0:].iloc[0])(top20(c, adj_us, dates)); bn['Top 20 da estratégia (ações)'] = 20
    s = px['SPYG'].loc[t0:T[-1]].dropna(); out_n['SPYG parado'] = s / s.iloc[0]
    for k, v in navs.items(): out_n[k] = v / v.iloc[0]; bn[k] = 1 if 'Os 2' not in k else 2
    ch = pd.Series({t: w.index[0] for t, w in W.items()})
    sw = int((ch != ch.shift()).sum() - 1)
    out = ['# ETF com mais OoL trocado todo mês (pré-registrado em 2026-11-14)\n', '> ⚠️ **O ROIC pode estar errado** — ele decide quem é OoL.\n',
           f'{T[0]:%m/%Y} a {T[-1]:%m/%Y}. Composição dos ETFs só muda por trimestre (N-PORT); preço, retorno esperado e classe mudam todo mês. Sem custos nem impostos.\n',
           '## Contra o S&P 500\n'] + bm.bench_table(out_n, bn)
    sub = {k: out_n[k] for k in ('SPYG parado', 'ETF com mais OoL — troca mensal', 'Os 2 ETFs com mais OoL — troca mensal', 'ETF com mais OoL — troca trimestral', 'Top 20 da estratégia (ações)', 'S&P 500')}
    out += ['', '## Contra o SPYG parado\n'] + bm.bench_table(sub, bn, ref='SPYG parado')
    out += ['', f'**Trocas de ETF (mensal):** {sw} em {len(ch)} meses. Vezes escolhido: ' + ', '.join(f'{k} {v}' for k, v in ch.value_counts().items())]
    (ROOT / 'resultado_mensal.md').write_text('\n'.join(out)); print('\n'.join(out))
    pd.DataFrame({k: out_n[k] for k in ('Os 2 ETFs com mais OoL — troca mensal', 'ETF com mais OoL — troca mensal', 'ETF com mais OoL — troca trimestral')}).to_csv(ROOT / 'navs_etf.csv')
    bm.bench_plot({k: v for k, v in out_n.items() if k in bm.ORDER or k in sub}, ROOT / 'resultado_mensal.png', 'ETF com mais OoL: troca mensal × trimestral × SPYG × Top 20 e comparativos obrigatórios')


if __name__ == '__main__':
    main()
