"""ETF com mais 'cara de Opportunity of Lifetime' (pre-registrado em 2026-11-14). Saidas: etfs/resultado.md e .png. Uso: python3 etfs/etf_ool.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path.insert(0, str(P)); sys.path.insert(0, str(P / 'backtest'))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from roic3_backtest import top20  # noqa: E402

D = ROOT / 'data'
ETFS = ['SPY', 'RSP', 'QUAL', 'SPHQ', 'JQUA', 'MTUM', 'VLUE', 'USMV', 'IWF', 'IWD', 'VUG', 'VTV', 'SPYG', 'IJH', 'IJR', 'MOAT', 'SCHD', 'COWZ']


def panel():
    f, dates = bm.base_data(); c = bm.classify_new(f)
    c['mcap'] = top_n.mcap_us(c, c)
    c['ool'] = (c['cat'] == bm.OOL) & ~c.excluded
    sp = c[['date', 'ticker', 'ool', 'ret', 'mcap']].assign(base='sp')
    ms, _, _, _ = pd.read_pickle(P / 'mundo' / 'cache' / 'backtest_ms.pkl')
    ms = ms.assign(ool=(ms['cat'] == bm.OOL) & ~ms.cyc & ~ms.app)[['date', 'ticker', 'ool', 'ret', 'mcap']].assign(base='ms')
    return sp, ms, c, dates


def main():
    import yfinance as yf
    sp, ms, c, dates = panel(); print('painel ok', flush=True)
    h = pd.read_csv(D / 'holdings.csv', parse_dates=['filed', 'end']); mp = pd.read_csv(D / 'cusip_map.csv').dropna().drop_duplicates('cusip')
    h = h.merge(mp, on='cusip', how='left')
    T = [d for d in dates if d >= pd.Timestamp('2019-12-31')]
    msd = sorted(ms.date.unique())
    rows, overl = [], []
    adj_us = bm.load_prices()['adj_close']
    top = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15)].copy(); top['pe'] = top.price / top.eps.where(top.eps > 0); top = top[top.pe >= 4]
    T20 = {d: set(g.sort_values(['ret', 'roic'], ascending=False).head(20).ticker) for d, g in top.groupby('date')}
    for t in T:
        a = sp[sp.date == t]; m0 = max([d for d in msd if d <= t + pd.Timedelta(days=7)], default=None)
        b = ms[ms.date == m0] if m0 is not None else ms.iloc[0:0]
        pan = pd.concat([a, b[~b.ticker.isin(a.ticker)]]).set_index('ticker')
        for e in ETFS:
            if e == 'SPY':
                w = a.set_index('ticker').mcap.dropna(); w = w / w.sum()
            else:
                x = h[(h.etf == e) & (h.filed <= t)]
                if x.empty: continue
                x = x[x.end == x.end.max()]; w = x.groupby('ticker').pct.sum(); w = w[w > 0]; w = w / w.sum()
            cov = w[w.index.isin(pan.index)]
            if cov.sum() < .3: rows.append(dict(date=t, etf=e, cov=cov.sum(), s1=np.nan, s2=np.nan)); continue
            q = pan.loc[cov.index]
            s1 = (cov * q.ool.astype(float)).sum() / cov.sum()
            r = q.ret.clip(-.5, 1.0); k = r.notna()
            s2 = (cov[k] * r[k]).sum() / cov[k].sum() if k.any() else np.nan
            rows.append(dict(date=t, etf=e, cov=cov.sum(), s1=s1, s2=s2, t20=w[w.index.isin(T20.get(t, set()))].sum()))
    S = pd.DataFrame(rows); S.to_csv(ROOT / 'notas.csv', index=False)
    px = yf.download(' '.join(ETFS), start='2019-06-01', progress=False, auto_adjust=True)['Close']; px.index = pd.to_datetime(px.index).tz_localize(None)
    px = px.reindex(adj_us.index.union(px.index)).ffill()
    T_ = T + ([] if T[-1] == px.index.max() else [])
    navs, n_ = {}, {}
    def pick(col, k):
        W = {}
        for t, g in S[S['cov'] >= .5].groupby('date'):
            g = g.dropna(subset=[col]).sort_values(col, ascending=False).head(k)
            W[t] = pd.Series(1.0, index=g.etf)
        return W
    sel = {}
    for col, k, lab in (('s1', 1, 'ETF com mais OoL (1 por trimestre) — produto testado'), ('s1', 2, 'Os 2 ETFs com mais OoL'), ('s2', 1, 'ETF de maior retorno esperado médio')):
        W = pick(col, k); sel[lab] = W; navs[lab] = run_weighted(W, px, T); n_[lab] = k
    navs['ETFs em peso igual'] = run_weighted({t: pd.Series(1.0, index=[e for e in ETFS if e in px and np.isfinite(px.at[t, e])]) for t in T}, px, T); n_['ETFs em peso igual'] = len(ETFS)
    for e in ETFS:
        s = px[e].loc[T[0]:T[-1]].dropna()
        if len(s) and s.index[0] <= T[0] + pd.Timedelta(days=10): navs[f'ETF {e}'] = s / s.iloc[0]
    t0 = T[0]
    bnav, bn, _, _ = bm.load_benchmarks()
    navs2 = {k: (v.loc[t0:] / v.loc[t0:].iloc[0]) for k, v in bnav.items()}
    navs2['Top 20 da estratégia (ações)'] = (lambda v: v.loc[t0:] / v.loc[t0:].iloc[0])(top20(c, adj_us, dates)); bn['Top 20 da estratégia (ações)'] = 20
    for k, v in navs.items(): navs2[k] = v / v.iloc[0]; bn[k] = n_.get(k, np.nan)
    pc = lambda v: '—' if pd.isna(v) else f'{v:.0%}'
    avg = S.groupby('etf').agg(cov=('cov', 'mean'), s1=('s1', 'mean'), s2=('s2', 'mean'), t20=('t20', 'mean')).sort_values('s1', ascending=False)
    W1 = sel['ETF com mais OoL (1 por trimestre) — produto testado']
    chosen = pd.Series({t: w.index[0] for t, w in W1.items()})
    out = ['# Qual ETF mais parece Opportunity of Lifetime — e a estratégia de ficar nele (pré-registrado em 2026-11-14)\n',
           '> ⚠️ **O ROIC pode estar errado** — ele decide quem é OoL, logo a nota de cada ETF. S&P 500 com o ROIC novo (triangulado); médias e pequenas com o anterior.\n',
           f'Composição real (N-PORT da SEC), {T[0]:%m/%Y} a {T[-1]:%m/%Y}, trimestral, só com o que já era público na data. Sem custos nem impostos.\n',
           '## 1. Quanto de cada ETF é Opportunity of Lifetime (média do período)\n',
           '| ETF | Peso coberto pelo nosso universo | % em OoL (nota) | Retorno esperado médio | % nas ações da Top 20 | Vezes escolhido |', '|---|---|---|---|---|---|']
    for e, r in avg.iterrows():
        out.append(f'| {e} | {pc(r["cov"])} | **{pc(r.s1)}** | {pc(r.s2)} | {pc(r.t20)} | {(chosen == e).sum()} de {len(chosen)} |')
    out += ['', '## 2. Desempenho (mesmo período)\n'] + bm.bench_table(navs2, bn)
    out += ['', '**ETF escolhido em cada trimestre:** ' + ', '.join(f'{t:%m/%y} {e}' for t, e in chosen.items())]
    (ROOT / 'resultado.md').write_text('\n'.join(out)); print('\n'.join(out))
    keep = {k: v for k, v in navs2.items() if k in bm.ORDER or k in ('Top 20 da estratégia (ações)', 'ETF com mais OoL (1 por trimestre) — produto testado', 'ETFs em peso igual', 'ETF QUAL', 'ETF MTUM')}
    bm.bench_plot(keep, ROOT / 'resultado.png', 'ETF com mais "cara de OoL" × Top 20 em ações, ETFs e comparativos obrigatórios')


if __name__ == '__main__':
    main()
