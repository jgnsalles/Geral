"""Grade pre-registrada (2026-11-14): rebalanceamento mensal/trimestral/anual x carteira de 10/15/20/30/50 acoes. EUA e Brasil.
Saida: backtest/grade_freq_n.md e .png. Uso: python3 backtest/grade_freq_n.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'mundo'))
import backtest_mundo as bmu  # noqa: E402
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402

NS = (10, 15, 20, 30, 50)


def reprice(q, p_new):
    """Recalcula P/L, valor de mercado e retorno esperado com um preco novo (fundamentos fixos)."""
    x = q.copy(); x['p_new'] = x.ticker.map(p_new)
    x = x[np.isfinite(x.p_new) & (x.p_new > 0)]
    base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.p_new
    rf = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
    rc = x.growth + x.dy
    x['ret'] = np.where(np.isfinite(rf) & np.isfinite(rc), (rf + rc) / 2, x.growth)
    x['pe'] = x.p_new / x.eps.where(x.eps > 0); x['mcap'] = x.mcap * x.p_new / x.price
    return x[x.pe >= 4]


def weights(pool, dates, n):
    W = {}
    for d in dates:
        g = pool(d)
        if g is None or g.empty: continue
        ch = g.sort_values(['ret', 'roic'], ascending=False).drop_duplicates('ticker').head(n)
        W[d] = top_n.cap(pd.Series(np.sqrt(ch.mcap.values), index=ch.ticker), .10)
    return W


def trades(W):
    ds = sorted(W); t = [len(set(W[b].index) ^ set(W[a].index)) for a, b in zip(ds[:-1], ds[1:])]
    yrs = (ds[-1] - ds[0]).days / 365.25
    return sum(t) / yrs if yrs > 0 else np.nan


def run_country(qual, close, adj, start_idx=3):
    qd = sorted(qual.date.unique()); qd = [pd.Timestamp(d) for d in qd]
    Q = {d: g for d, g in qual.groupby('date')}
    def pool_at(d):
        q0 = max((x for x in qd if x <= d), default=None)
        if q0 is None: return None
        return reprice(Q[q0], close.loc[:d].iloc[-1])
    t0 = qd[start_idx]; end = qd[-1]
    me = close.loc[qd[0]:end].resample('ME').last().index
    months = [close.index[close.index <= m][-1] for m in me]; months = sorted(set(m for m in months if m >= qd[0]))
    if months[-1] != end: months.append(end)
    res = {}
    for n in NS:
        for fq, sets in (('1m', [months]), ('1q', [qd]), ('1y', [[d for i, d in enumerate(qd) if i % 4 == k] + [end] for k in range(4)])):
            cg, ct, tr, navs = [], [], [], []
            for ds in sets:
                ds = sorted(set(ds)); W = weights(pool_at, ds[:-1], n)
                nav = run_weighted(W, adj, ds); navt = tax_weighted(W, adj, ds)
                cut = lambda s: (s.loc[t0:] / s.loc[t0:].iloc[0])
                cg.append(stats(cut(nav))['CAGR']); ct.append(stats(cut(navt))['CAGR']); tr.append(trades(W)); navs.append(cut(nav))
            res[(n, fq)] = dict(cagr=np.mean(cg), tax=np.mean(ct), trades=np.mean(tr), lo=min(cg), hi=max(cg), nav=navs[0] if len(navs) == 1 else pd.concat(navs, axis=1).ffill().mean(axis=1))
            print(n, fq, f"{np.mean(cg):.3f}", flush=True)
    return res, t0, end


def main():
    import yfinance as yf
    pr = bm.load_prices(); close_us, adj_us = pr['close'], pr['adj_close']
    sp, _, _ = bmu.us_sp()
    sp['qual'] = ~sp.excluded & (sp.roic >= .12) & (sp.growth >= .15) & sp.roic.notna() & sp.growth.notna()
    sp.loc[sp.qual, 'mcap'] = top_n.mcap_us(sp, sp[sp.qual])
    q_us = sp[sp.qual & sp.mcap.notna() & sp.eps.gt(0)][['date', 'ticker', 'price', 'eps', 'growth', 'dy', 'fair_pe', 'roic', 'mcap']]
    fx = yf.download('BRL=X', start='2010-01-01', progress=False, auto_adjust=True)['Close'].squeeze(); fx.index = pd.to_datetime(fx.index).tz_localize(None)
    br, _ = bmu.brasil(fx)
    BD = ROOT.parent / 'brasil' / 'data'
    close_br = pd.read_csv(BD / 'prices_close.csv.gz', index_col=0, parse_dates=True); adj_br = pd.read_csv(BD / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    q_br = br[br.ok & (br.roic >= .12) & (br.growth >= .15) & br.cat.notna() & br.mcap.notna() & br.eps.gt(0)][['date', 'ticker', 'price', 'eps', 'growth', 'dy', 'fair_pe', 'roic', 'mcap']]
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    out = ['# Frequência de rebalanceamento × tamanho da carteira (pré-registrado em 2026-11-14)\n',
           '> ⚠️ **O ROIC pode estar errado** — ele define quem é elegível e entra no P/E justo, logo na ordem das ações.\n',
           'Regra da candidata em tudo, menos a frequência e o número de ações. Mensal: fundamentos da última data trimestral, preço do fim do mês. '
           'Anual: média das 4 versões (uma começando em cada trimestre). IR de 15% sobre ganho realizado; sem corretagem. Com 10 ações, o teto de 10% deixa o peso igual.\n']
    keep_us = {}
    for lab, q, close, adj, b, curr in (('EUA', q_us, close_us, adj_us, 'SPY', 'dólares'), ('Brasil', q_br, close_br, adj_br, 'BOVA11.SA', 'reais')):
        res, t0, end = run_country(q, close, adj)
        s = adj[b].loc[t0:end].dropna(); sb = stats(s / s.iloc[0])['CAGR']
        out += [f'\n## {lab} ({t0:%m/%Y}–{end:%m/%Y}, em {curr}; {"S&P 500" if lab == "EUA" else "Ibovespa"} {pc(sb)} a.a.)\n']
        for title, key in (('Retorno anual antes do IR', 'cagr'), ('Retorno anual depois de 15% de IR', 'tax'), ('Trades por ano (compras + vendas)', 'trades')):
            out += [f'**{title}**\n', '| Ações | Mensal | Trimestral | Anual |', '|---|---|---|---|']
            for n in NS:
                cell = lambda fq: (f"{res[(n, fq)][key]:.0f}" if key == 'trades' else pc(res[(n, fq)][key])) + (' ← atual' if (n, fq) == (20, '1q') else '')
                out.append(f'| {n} | ' + ' | '.join(cell(fq) for fq in ('1m', '1q', '1y')) + ' |')
            out.append('')
        out.append('Anual, faixa entre as 4 versões (antes do IR): ' + '; '.join(f"{n}: {pc(res[(n, '1y')]['lo'])} a {pc(res[(n, '1y')]['hi'])}" for n in NS))
        if lab == 'EUA': keep_us = {f'{n} ações, {dict(m="mensal", q="trimestral", y="anual")[fq[1]]}': res[(n, fq)]['nav'] for n in NS for fq in ('1m', '1q', '1y')}
    navs, nn, _, _ = bm.load_benchmarks()
    t0 = min(v.index[0] for v in keep_us.values())
    navs = {k: (v.loc[t0:] / v.loc[t0:].iloc[0]) for k, v in navs.items()}
    for k, v in keep_us.items(): navs[k] = v; nn[k] = int(k.split()[0])
    out += ['\n## EUA: comparativos obrigatórios e a grade (antes do IR, mesma janela)\n'] + bm.bench_table(navs, nn)
    (ROOT / 'grade_freq_n.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or k.startswith('20 ações') or k in ('10 ações, trimestral', '50 ações, trimestral')},
                  ROOT / 'grade_freq_n.png', 'EUA: 20 ações mensal/trimestral/anual, 10 e 50 trimestral × comparativos obrigatórios — antes do IR')


if __name__ == '__main__':
    main()
