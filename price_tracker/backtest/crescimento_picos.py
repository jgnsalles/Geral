"""Regra de picos no crescimento (pre-registrada em 2026-11-14): EUA e Brasil. Saida: backtest/crescimento_picos.md e .png"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import benchmarks as bm  # noqa: E402
import engine, picos, top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats, run_portfolio, D  # noqa: E402
from roic3_backtest import top20  # noqa: E402

GY = ['gy1', 'gy2', 'gy3', 'gy4', 'gy5']


def with_picos(f):
    f = f.copy(); g, z = [], []
    for row in f[GY].itertuples(index=False):
        adj = picos.adjust([float(x) for x in row]); ok = [x for x in adj if np.isfinite(x)]
        gr = float(np.median(ok)) if len(ok) >= min(3, len(adj)) and ok else np.nan
        g.append(gr); z.append(engine.cv(adj, gr) if np.isfinite(gr) else np.nan)
    f['growth_antigo'] = f.growth; f['growth'] = g; f['zgrowth'] = z
    return f


def brasil():
    import backtest_br as bb, sem2021
    BD = ROOT.parent / 'brasil' / 'data'
    V = {}
    for lab, excl, spike, fn in (('A: atual (sem 2021)', {2021}, False, 'classes_pit.csv'), ('B: regra de picos (2021 volta)', set(), True, 'classes_pit_picos.csv'),
                                 ('C: picos + sem 2021', {2021}, True, 'classes_pit_picos_sem2021.csv')):
        p = BD / fn
        if not p.exists():
            bb.EXCL, bb.SPIKE = excl, spike
            u = pd.read_csv(BD / 'universe.csv'); fund = pd.read_csv(BD / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund = {c: g for c, g in fund.groupby('CD_CVM')}
            rd = lambda n: pd.read_csv(BD / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
            close, vol = rd('close'), rd('volume'); divs, splits = rd('dividends').fillna(0), rd('stock_splits').fillna(0)
            bb.classify_all(u, fund, close, vol, divs, splits, bb.rebalance_dates(close)).to_csv(p, index=False)
            bb.EXCL, bb.SPIKE = {2021}, False
        V[lab] = pd.read_csv(p, parse_dates=['date'])
    u = pd.read_csv(BD / 'universe.csv'); idx = u.set_index('yf')
    fund = pd.read_csv(BD / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
    adj = pd.read_csv(BD / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    base = V['A: atual (sem 2021)']; cov = base.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    dates = sorted(d for d in base.date.unique() if d >= start)
    res, today = {}, {}
    for k, raw in V.items():
        c = sem2021.frozen(raw, idx, fund, start)
        ool = c[(c.cat == bm.OOL) & c.ok]
        el = c[c.ok & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4) & c.cat.notna()]
        ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in el.groupby('date')])
        res[k] = (run_weighted({d: pd.Series(np.sqrt(g.mcap.values), index=g.ticker) for d, g in ool.groupby('date')}, adj, dates),
                  run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in ch.groupby('date')}, adj, dates))
        today[k] = set(ch[ch.date == ch.date.max()].ticker.map(idx.ticker))
    s = adj['BOVA11.SA'].loc[dates[0]:dates[-1]].dropna()
    return res, today, stats(s / s.iloc[0])['CAGR'], dates


def main():
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    navs, n, _, _ = bm.load_benchmarks()
    fp = with_picos(f); cp = bm.classify_new(fp); c0 = bm.classify_new(f)
    navs['Top 20 — atual'] = top20(c0, adj, dates); n['Top 20 — atual'] = 20
    navs['Top 20 — com regra de picos'] = top20(cp, adj, dates); n['Top 20 — com regra de picos'] = 20
    for k, msk in bm.holdings_new(cp).items():
        lab = f'{k} — com regra de picos'
        navs[lab] = run_portfolio({d: g.ticker.tolist() for d, g in cp[msk].groupby('date')}, adj, dates)[0]; n[lab] = cp[msk].groupby('date').size().mean()
    print('EUA ok', flush=True)
    chg = (fp.growth - fp.growth_antigo).abs() > 1e-9
    out = ['# Regra de picos no crescimento (pré-registrada em 2026-11-14)\n', '> ⚠️ **O ROIC pode estar errado** (EUA já com o ROIC triangulado).\n',
           f'Um ano é pico/vale se o lucro for ≥ 1,5× (ou ≤ 1/1,5) a média geométrica dos vizinhos; as duas variações viram uma de 2 anos. '
           f'Nos EUA, a regra mudou o crescimento em {chg.mean():.0%} das observações.\n', '## EUA (2011–2026)\n'] + bm.bench_table(navs, n)
    last = fp[fp.date == fp.date.max()]; ch_ = last[(last.growth - last.growth_antigo).abs() > .05].copy()
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    t0 = pd.concat([g.assign(pe=g.price / g.eps.where(g.eps > 0)) for _, g in c0[c0.date == c0.date.max()].groupby('date')])
    tp = cp[cp.date == cp.date.max()].copy()
    def top_set(c):
        el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15)].copy(); el['pe'] = el.price / el.eps.where(el.eps > 0); el = el[el.pe >= 4]
        return set(el.sort_values(['ret', 'roic'], ascending=False).head(20).ticker)
    a, b = top_set(c0[c0.date == c0.date.max()]), top_set(tp)
    out += ['', f'**Top 20 de hoje (EUA):** saem {", ".join(sorted(a - b)) or "—"}; entram {", ".join(sorted(b - a)) or "—"}.', '',
            '**Maiores mudanças de crescimento hoje (EUA, ações classificadas):**\n', '| Ação | Empresa | Crescimento antes | Depois |', '|---|---|---|---|']
    for r in ch_.assign(d=(ch_.growth - ch_.growth_antigo).abs()).sort_values('d', ascending=False).head(15).itertuples():
        out.append(f'| {r.ticker} | {str(u.name.get(r.ticker, r.ticker))[:30]} | {r.growth_antigo:.0%} | {r.growth:.0%} |')
    res, today, SI, bd = brasil()
    out += ['', f'## Brasil ({pd.Timestamp(bd[0]):%m/%Y}–{pd.Timestamp(bd[-1]):%m/%Y}, em reais; Ibovespa {pc(SI)} a.a.)\n',
            '| Versão do crescimento | OoL novo (raiz) | Top 20 (raiz, teto 10%) |', '|---|---|---|']
    for k, (a1, a2) in res.items(): out.append(f"| {k} | {pc(stats(a1)['CAGR'])} | **{pc(stats(a2)['CAGR'])}** |")
    A = today['A: atual (sem 2021)']
    out += [''] + [f"Top 20 de hoje, {k}: saem {', '.join(sorted(A - s)) or '—'}; entram {', '.join(sorted(s - A)) or '—'}." for k, s in today.items() if not k.startswith('A')]
    out.append('\n(Brasil: valor de mercado estimado como no script sem2021; serve para comparar as versões entre si.)')
    (ROOT / 'crescimento_picos.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or k.startswith('Top 20')}, ROOT / 'crescimento_picos.png',
                  'Regra de picos no crescimento: Top 20 com e sem × comparativos obrigatórios (EUA)')


if __name__ == '__main__':
    main()
