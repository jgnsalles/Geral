"""Relatorio comparativo das 6 estrategias finalistas (EUA, S&P 500 point-in-time, ROIC triangulado). Saida: relatorio/dados.json e relatorio/resumo.md"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path.insert(0, str(P)); sys.path.insert(0, str(P / 'backtest'))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted, DUAL  # noqa: E402
from backtest import stats, D  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402
from validation_factors import factors  # noqa: E402

NAMES = {'top20': 'Top 20 da OoL (estratégia congelada)', 'hroic': 'OoL High ROIC', 'hgrowth': 'OoL High Growth',
         'magicg': 'ROIC + G + P/L sem cíclicos', 'n1': 'Todas as de qualidade', 'n2': 'As excepcionais'}
DESC = {'top20': '20 de maior retorno esperado entre ROIC ≥ 12%, crescimento ≥ 15%, P/L ≥ 4; raiz do valor de mercado, teto 10%',
        'hroic': 'Classe OoL com ROIC > 30%; peso igual', 'hgrowth': 'Classe OoL com crescimento > 30%; peso igual',
        'magicg': 'Ranking ROIC + crescimento + P/L (sem financeiras, utilities, cíclicos e vestuário); 20 melhores; raiz com teto 10%',
        'n1': 'Todas com ROIC ≥ 12% e crescimento ≥ 15%; raiz do valor de mercado', 'n2': 'Todas com ROIC > 30% e crescimento > 30%; raiz do valor de mercado'}


def dedupe(x):
    return x.assign(firm=x.ticker.map(lambda t: DUAL.get(t, t))).sort_values('mcap', ascending=False).drop_duplicates(['date', 'firm'])


def weights(c):
    W = {}
    c = c.copy(); c['pe'] = c.price / c.eps.where(c.eps > 0)
    ok = ~c.excluded & c['cat'].notna()
    need = c[ok & (c.roic >= .12) & (c.growth >= .15)].copy(); need['mcap'] = top_n.mcap_us(need, need)
    c = c.merge(need[['date', 'ticker', 'mcap']], on=['date', 'ticker'], how='left')
    el = dedupe(c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4) & c.mcap.notna()])
    W['top20'] = {d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in
                  ((d, g.sort_values(['ret', 'roic'], ascending=False).head(20)) for d, g in el.groupby('date'))}
    hn = bm.holdings_new(c)
    for k, lab in (('hroic', 'OoL High ROIC (novo)'), ('hgrowth', 'OoL High Growth (novo)')):
        x = c[hn[lab]].assign(mcap=lambda d: d.mcap.fillna(1.0)); x = dedupe(x)
        W[k] = {d: pd.Series(1.0 / len(g), index=g.ticker) for d, g in x.groupby('date')}
    sec, _ = bm.sector_maps(); c['sector'] = c.ticker.map(sec)
    mf = pd.read_csv(D / 'magic_features.csv', parse_dates=['date'])[['date', 'ticker', 'mcap', 'ebit']]  # mesmo universo do teste registrado (EBIT > 0, EV e capital > 0)
    y = c[~c.fin & (c.sector != 'Utilities') & ~c.excluded & c.pe.notna() & c.roic.notna() & c.growth.notna()].drop(columns='mcap').merge(mf, on=['date', 'ticker'])
    y['score'] = y.groupby('date').roic.rank(ascending=False) + y.groupby('date').growth.rank(ascending=False) + y.groupby('date').pe.rank(ascending=True)
    y = y.assign(firm=y.ticker.map(lambda t: DUAL.get(t, t))).sort_values('score').drop_duplicates(['date', 'firm'])
    W['magicg'] = {d: top_n.cap(pd.Series(np.sqrt(g.head(20).mcap.values), index=g.head(20).ticker), .10) for d, g in y.groupby('date')}
    for k, m in (('n1', ok & (c.roic >= .12) & (c.growth >= .15)), ('n2', ok & (c.roic > .30) & (c.growth > .30))):
        x = c[m & c.mcap.notna()]; x = dedupe(x)
        w = {d: pd.Series(np.sqrt(g.mcap.values), index=g.ticker) for d, g in x.groupby('date')}
        W[k] = {d: s / s.sum() for d, s in w.items()}
    return W, c


def contrib(W, adj, dates, nav):
    """Contribuicao de cada acao (pontos de retorno acumulado): soma de NAV_inicio x peso x retorno do periodo."""
    out = {}
    for i, d in enumerate(dates[:-1]):
        w = W.get(d)
        if w is None or w.empty: continue
        nx = dates[i + 1]; w = w[[t for t in w.index if t in adj and np.isfinite(adj.at[d, t])]]; w = w / w.sum()
        seg = adj.loc[d:nx, w.index].ffill(); r = seg.iloc[-1] / seg.iloc[0] - 1
        v0 = nav.loc[:d].iloc[-1] if d in nav.index or len(nav.loc[:d]) else 1.0
        for t in w.index:
            if np.isfinite(r[t]): out[t] = out.get(t, 0.0) + v0 * w[t] * r[t]
    return pd.Series(out).sort_values(ascending=False)


def turnover(W):
    ds = sorted(W); tr, gi = [], []
    for a, b in zip(ds[:-1], ds[1:]):
        A, B = set(W[a].index), set(W[b].index); tr.append(len(A ^ B))
        dw = W[b].reindex(A | B, fill_value=0) - W[a].reindex(A | B, fill_value=0); gi.append(dw.abs().sum() / 2)
    yrs = (ds[-1] - ds[0]).days / 365.25
    held = []
    for t in set().union(*[set(w.index) for w in W.values()]):
        run = 0
        for d in ds:
            if t in W[d].index: run += 1
            elif run: held.append(run); run = 0
        if run: held.append(run)
    held = np.array(held) * 3
    return dict(trades=sum(tr) / yrs, turnover=sum(gi) / yrs, hold_mean=held.mean(), hold_median=float(np.median(held)), one_q=float(np.mean(held == 3)),
                n_mean=np.mean([len(w) for w in W.values()]), eff_n=np.mean([1 / (w ** 2).sum() for w in W.values()]),
                top_w=np.mean([w.max() for w in W.values()]), top5_w=np.mean([w.sort_values(ascending=False).head(5).sum() for w in W.values()]))


def metrics(nav, spy, rf):
    m = nav.resample('ME').last().pct_change().dropna(); s = spy.resample('ME').last().pct_change().reindex(m.index); f = rf.reindex(m.index).fillna(0)
    st = stats(nav); ex = m - f; se = s - f
    beta = np.cov(ex, se)[0, 1] / se.var(); alpha = (ex.mean() - beta * se.mean()) * 12
    down = ex[ex < 0]; sortino = ex.mean() * 12 / (np.sqrt((down ** 2).mean()) * np.sqrt(12)) if len(down) else np.nan
    te = (m - s).std() * np.sqrt(12); cs = stats(spy.loc[nav.index[0]:nav.index[-1]] / spy.loc[nav.index[0]:].iloc[0])['CAGR']
    dd = nav / nav.cummax() - 1; uw = dd < 0; longest = 0; cur = None
    for t, v in uw.items():
        if v: cur = cur or t; longest = max(longest, (t - cur).days)
        else: cur = None
    rel = (nav / spy.reindex(nav.index).ffill()); rdd = (rel / rel.cummax() - 1)
    relm = rel.resample('ME').last(); behind = (relm < relm.cummax()).astype(int); streak = mx = 0
    for v in behind: streak = streak + 1 if v else 0; mx = max(mx, streak)
    yr = nav.resample('YE').last().pct_change().dropna(); sy = spy.resample('YE').last().pct_change().reindex(yr.index)
    r12 = (nav.resample('ME').last().pct_change(12) - spy.resample('ME').last().pct_change(12).reindex(nav.resample('ME').last().index)).dropna()
    win = {y: bm.windows(nav, spy, y) for y in (3, 5, 10)}
    up = m[s > 0].mean() / s[s > 0].mean(); dn = m[s < 0].mean() / s[s < 0].mean()
    return dict(cagr=st['CAGR'], total=st['Total'], vol=m.std() * np.sqrt(12), sharpe=ex.mean() * 12 / (m.std() * np.sqrt(12)), sortino=sortino,
                maxdd=st['MaxDD'], dd_days=longest, calmar=st['CAGR'] / abs(st['MaxDD']), beta=beta, alpha=alpha, te=te, ir=(st['CAGR'] - cs) / te,
                up=up, down=dn, pos_m=(m > 0).mean(), beat_m=(m > s).mean(), best_y=yr.max(), worst_y=yr.min(), beat_y=(yr > sy).mean(),
                rel_dd=rdd.min(), behind_months=mx, worst12=r12.min(), w3=win[3][0], w5=win[5][0], w10=win[10][0], w3min=win[3][1], w5min=win[5][1],
                years={str(k.year): v for k, v in yr.items()})


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']; c = bm.classify_new(f)
    W, c = weights(c); print('pesos ok', flush=True)
    bnav, bn, _, _ = bm.load_benchmarks()
    spy = bnav['S&P 500']; rf = factors()['RF']
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker'); sec, ind = bm.sector_maps()
    nm = lambda t: str(u.name.get(t, u.name.get(DUAL.get(t, t), t)))
    out = dict(names=NAMES, desc=DESC, period=[str(dates[0].date()), str(dates[-1].date())], strat={})
    navs = {}
    for k in NAMES:
        nav = run_weighted(W[k], adj, dates); navs[k] = nav
        navt = tax_weighted(W[k], adj, dates)
        mt = metrics(nav, spy, rf); mt['cagr_tax'] = stats(navt)['CAGR']; mt.update(turnover(W[k]))
        cb = contrib(W[k], adj, dates, nav); tot = cb.sum()
        secb = cb.groupby(cb.index.map(lambda t: sec(t) or 'Outros')).sum().sort_values(ascending=False)
        last = max(W[k]); wl = W[k][last].sort_values(ascending=False)
        mt.update(top_contrib=[[t, nm(t), float(v)] for t, v in cb.head(10).items()], worst_contrib=[[t, nm(t), float(v)] for t, v in cb.tail(5).items()],
                  top5_share=float(cb.head(5).sum() / tot) if tot else None, n_names_ever=int(len(cb)), sector=[[s_, float(v)] for s_, v in secb.items()],
                  today=[[t, nm(t), str(ind(t) or ''), float(w)] for t, w in wl.items()], today_date=str(pd.Timestamp(last).date()))
        out['strat'][k] = {a: (float(b) if isinstance(b, (np.floating, float, np.integer, int)) and not isinstance(b, bool) else b) for a, b in mt.items()}
        print(k, round(mt['cagr'], 4), flush=True)
    # mensal e series
    allnav = {**{NAMES[k]: v for k, v in navs.items()}, **bnav}
    M = pd.DataFrame({k: v.resample('ME').last() for k, v in allnav.items()})
    out['nav_monthly'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(x) else round(float(x), 5) for x in M[k] / M[k].dropna().iloc[0]] for k in M}}
    R = pd.DataFrame({NAMES[k]: v.resample('ME').last().pct_change() for k, v in navs.items()}).dropna()
    S = spy.resample('ME').last().pct_change().reindex(R.index)
    out['corr'] = R.corr().round(3).to_dict(); out['corr_excess'] = R.sub(S, axis=0).corr().round(3).to_dict()
    out['corr_spy'] = {k: round(float(R[k].corr(S)), 3) for k in R}
    ks = list(NAMES); ov = {}; ovt = {}
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            vals = []
            for d in sorted(set(W[a]) & set(W[b])):
                A, B = W[a][d], W[b][d]; idx = A.index.union(B.index)
                vals.append(float(np.minimum(A.reindex(idx, fill_value=0), B.reindex(idx, fill_value=0)).sum()))
            ov[f'{a}|{b}'] = float(np.mean(vals)); ovt[f'{a}|{b}'] = vals
    out['overlap'] = ov; out['overlap_ts'] = {'dates': [str(pd.Timestamp(d).date()) for d in sorted(W['top20'])], 'series': ovt}
    dd = {NAMES[k]: (v / v.cummax() - 1).resample('ME').min() for k, v in navs.items()}; dd['S&P 500'] = (spy / spy.cummax() - 1).resample('ME').min()
    out['dd'] = {'dates': [str(d.date()) for d in dd['S&P 500'].index], 'series': {k: [round(float(x), 4) for x in v] for k, v in dd.items()}}
    roll = {}
    for k, v in navs.items():
        Mv = v.resample('ME').last(); Ms = spy.resample('ME').last()
        r3 = ((Mv / Mv.shift(36)) ** (1 / 3) - (Ms / Ms.shift(36)) ** (1 / 3)).dropna(); roll[NAMES[k]] = r3
    rd = sorted(set().union(*[set(x.index) for x in roll.values()]))
    out['roll3'] = {'dates': [str(d.date()) for d in rd], 'series': {k: [None if d not in x.index else round(float(x[d]), 4) for d in rd] for k, x in roll.items()}}
    # 9 obrigatorios
    out['bench'] = {k: {**{a: float(b) for a, b in stats(v).items()}, 'w3': bm.windows(v, spy, 3)[0], 'w5': bm.windows(v, spy, 5)[0], 'w10': bm.windows(v, spy, 10)[0]}
                    for k, v in bnav.items()}
    (ROOT / 'dados.json').write_text(json.dumps(out, ensure_ascii=False, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else float(o)))
    print('ok')


if __name__ == '__main__':
    main()
