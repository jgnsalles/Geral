"""Brasil v3: liquidez minima de R$ 10 mi/dia (mediana de 63 pregoes) e corte alto de ROIC em 17%.
Demais parametros: EUA + 2,5 p.p. (WACC 11%; g 9,5% -> 6% igual para financeiras; crescimento 17,5%/8,5%; retorno 22,5%/10,5%).
Uso: python3 brasil/run_v3.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import backtest_br as bb  # noqa: E402
from backtest import run_portfolio, stats  # noqa: E402

D = ROOT / 'data'
MIN_ADTV, MIN_N = 10e6, 40
bb.WACC, bb.GMAX, bb.GMIN, bb.FIN_SHIFT = 0.11, 0.095, 0.06, 0.0
TH = {'Growth_Hi': 0.175, 'Growth_Lo': 0.085, 'Return_Hi': 0.225, 'Return_Lo': 0.105, 'Roic_Hi': 0.17, 'Roic_Lo': 0.10}
CLASSES = ['Opportunity of Lifetime', 'Good Companies, Great Returns', 'Excellent but Fair', 'Good but Margin of Safety Required',
           'Cheap Slow Compounder', 'Interesting but Requires Attention', 'Cheap but Aggressive', 'Expensive for what you get',
           'Investable but Not Good', 'Expensive', 'Do not Waste Time']
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def prepare():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    cls = cls[[c for c in cls.columns if not c.startswith('cat_')]]
    close = pd.read_csv(D / 'prices_close.csv.gz', index_col=0, parse_dates=True)
    vol = pd.read_csv(D / 'prices_volume.csv.gz', index_col=0, parse_dates=True)
    tv = (close * vol).rolling(63, min_periods=20).median()
    cls['adtv'] = [tv.at[d, t] if t in tv.columns else np.nan for d, t in zip(cls.date, cls.ticker)]
    cls = cls[cls.adtv >= MIN_ADTV]
    parts = []
    for d, x in cls.groupby('date'):
        x = x.copy(); x['g'] = bb.g_rank(x)
        x['fair_pe'] = np.where(x.roic > 0, (1 - x.g / x.roic) / (bb.WACC - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    return pd.concat(parts), close


def classify(x, cut):
    saved = dict(engine.TH); engine.TH.update(TH); engine.TH['zGrowth'] = cut
    try:
        c = engine.classify(x)
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(c.code.isna(), None, c.category)
    return c


def attribution(c, cat, adj, dates, u, n=10):
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill(); fwd = px.shift(-1) / px - 1
    x = c[(c.cat == cat) & c.date.isin(dates[:-1])].copy()
    x['n'] = x.groupby('date').ticker.transform('size')
    x['r'] = [fwd.at[d, t] for d, t in zip(x.date, x.ticker)]
    x['c'] = x.r / x.n
    a = x.groupby('ticker').agg(contrib=('c', 'sum'), trims=('c', 'size'), ret_trim=('r', 'mean'), first=('date', 'min'), last=('date', 'max'))
    a = a.sort_values('contrib', ascending=False)
    hold = {d: g.ticker.tolist() for d, g in x.groupby('date')}
    sens = [(k, stats(run_portfolio({d: [t for t in v if t not in set(a.index[:k])] for d, v in hold.items()}, adj, dates)[0])['CAGR']) for k in (1, 3, 5)]
    row = lambda i, t, r: (f"| {i} | {t.replace('.SA', '')} | {u.Nome_Empresarial.get(t, t)} | {u.Setor_Atividade.get(t, '')} | {sg(r.contrib)} | "
                           f"{int(r.trims)} | {sg(r.ret_trim)} | {r['first'].year}–{r['last'].year} |")
    hdr = ['| # | Ticker | Empresa | Setor | Contribuição | Trim. | Retorno médio/trim. | Período |', '|---|---|---|---|---|---|---|---|']
    out = [f'### Atribuição: {cat}\n', f'- Ações distintas: {len(a)} · sem as maiores: ' + ' · '.join(f'sem top {k}: {pc(v)}' for k, v in sens) + '\n',
           f'**{n} maiores**\n'] + hdr + [row(i + 1, t, r) for i, (t, r) in enumerate(a.head(n).iterrows())]
    out += ['', f'**{n} menores**\n'] + hdr + [row(i + 1, t, r) for i, (t, r) in enumerate(a.tail(n).iloc[::-1].iterrows())] + ['']
    return out


def main():
    x, close = prepare()
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    u = pd.read_csv(D / 'universe.csv').set_index('yf')
    out = ['# Brasil v3: liquidez ≥ R$ 10 mi/dia e ROIC alto ≥ 17%\n',
           '> ⚠️ **ROIC:** corte alto reduzido para 17% (baixo 10%); ROIC clássico, ROE para financeiras.\n',
           'WACC 11%; g 9,5% → 6% (operacionais e financeiras); crescimento 17,5%/8,5%; retorno 22,5%/10,5%; ROIC 17%/10%.\n']
    for cut in (2.93, 0.9):
        c = classify(x, cut)
        cov = c.groupby('date').cat.apply(lambda s: s.notna().sum())
        start = cov[cov >= MIN_N].index.min()
        dates = [d for d in bb.rebalance_dates(close) if d >= start]
        c = c[c.date >= start]
        univ = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat.notna()].groupby('date')}, adj, dates)[0]
        uq = univ.resample('QE').last().pct_change().dropna()
        out += [f'## Corte zGrowth {str(cut).replace(".", ",")} — início {start:%d/%m/%Y}, {int(cov[cov.index >= start].median())} empresas classificadas por trimestre (mediana)\n',
                '| Carteira | Retorno anual | vs Universo EW | t | Max DD | Ações em média | Trimestres vazios |', '|---|---|---|---|---|---|---|']
        for cat in CLASSES:
            hold = {d: g.ticker.tolist() for d, g in c[c.cat == cat].groupby('date')}
            nav, _, _, n = run_portfolio(hold, adj, dates)
            q = nav.resample('QE').last().pct_change().dropna(); ex = (q - uq.reindex(q.index)).dropna()
            t = ex.mean() / ex.std() * np.sqrt(len(ex)) if ex.std() > 0 else np.nan
            s = stats(nav)
            out.append(f'| {cat} | {pc(s["CAGR"])} | {sg(ex.mean() * 4)} | {nm(t)} | {pc(s["MaxDD"])} | {nm(n)} | {sum(1 for d in dates[:-1] if not hold.get(d))} |')
        su = stats(univ)
        out.append(f'| *Universo EW (contraprova)* | {pc(su["CAGR"])} | | | {pc(su["MaxDD"])} | {c[c.cat.notna()].groupby("date").size().mean():.0f} | |')
        for b in bb.BENCH:
            nb = adj[b].loc[dates[0]:dates[-1]].dropna(); sb = stats(nb / nb.iloc[0])
            out.append(f'| *{b.replace(".SA", "")}* | {pc(sb["CAGR"])} | | | {pc(sb["MaxDD"])} | | |')
        out.append('')
        if cut == 2.93:
            for cat in ('Opportunity of Lifetime', 'Good Companies, Great Returns'):
                out += attribution(c, cat, adj, dates, u)
        print(cut, flush=True)
    (ROOT / 'run_v3.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
