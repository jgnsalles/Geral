"""Backtest point-in-time do metodo 2 (so historico): a cada trimestre classifica o universo usando apenas
dados arquivados na SEC ate a vespera do rebalanceamento, compra equal weight cada classe e segura ate o
proximo trimestre. Compara com SPY, QQQ, RSP (S&P 500 equal weight) e com o universo inteiro equal weight.

Uso: python3 backtest/backtest.py
Saidas: backtest/data/classes_pit.csv (classe de cada acao em cada data), backtest/data/nav_<corte>.csv,
        backtest/report.md e graficos em backtest/*.png"""
import sys, json, gzip, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent))
import engine  # noqa: E402

D = ROOT / 'data'
N_HIST = 5              # janela da mediana de crescimento (decisao do usuario)
CUTS = {'zg2.93': 2.93, 'zg0.9': 0.9}
COST_BPS = 10           # custo por unidade de giro (one-way)
STALE_DAYS = 550        # ultimo exercicio mais velho que isso: acao fica fora naquela data
START = '2010-01-01'
BENCH = ['SPY', 'QQQ', 'RSP']


# ---------------------------------------------------------------- dados point-in-time
def fy(end):
    t = pd.Timestamp(end)
    return t.year if t.month > 3 else t.year - 1


def load_pit(tk):
    f = D / 'pit' / f'{tk}.json.gz'
    if not f.exists(): return None
    raw = json.load(gzip.open(f, 'rt'))
    out = {}
    for key, cands in raw.items():
        cs = []
        for c in cands:
            df = pd.DataFrame(c['rows'], columns=['end', 'val', 'filed'])
            df['end'] = pd.to_datetime(df.end); df['filed'] = pd.to_datetime(df.filed)
            cs.append((c['concept'], c['unit'], df.sort_values('filed')))
        out[key] = cs
    return out


def asof(cands, t):
    """Mesmo criterio do coletor atual, mas so com o que foi arquivado ate t.
    Devolve {ano_fiscal: (valor, data_de_arquivamento, fim_do_exercicio)} e a unidade."""
    known = []
    for concept, unit, df in cands:
        x = df[df.filed <= t]
        if x.empty: continue
        x = x.groupby('end').tail(1)  # ultimo arquivamento conhecido de cada exercicio
        known.append((concept, unit, x))
    if not known: return {}, None
    latest = max(x.end.max() for _, _, x in known)
    elig = [k for k in known if k[2].end.max() >= latest - pd.Timedelta(days=400)]
    main = elig[0]
    vals = {r.end: (r.val, r.filed) for r in main[2].itertuples()}
    for c in known:
        if c is main or c[1] != main[1]: continue
        for r in c[2].itertuples():
            if r.end not in vals and not any(abs((r.end - e).days) < 30 for e in vals):
                vals[r.end] = (r.val, r.filed)
    out = {}
    for end, (v, filed) in sorted(vals.items()):
        out[fy(end)] = (float(v), filed, end)
    return out, main[1]


def split_factor_after(splits, d):
    """Produto dos desdobramentos ocorridos depois da data d (converte valores por acao para a base de hoje)."""
    s = splits[splits.index > d]
    return float(np.prod(s.values)) if len(s) else 1.0


def ratio(a, b):
    return a / b - 1 if a is not None and b is not None and np.isfinite(a) and np.isfinite(b) and b > 0 else np.nan


def features(pit, t, fin, splits):
    """Metricas do metodo 2 para uma acao numa data t (so dados conhecidos ate t)."""
    eps, unit = asof(pit['eps_diluted'], t)
    if not eps or unit != 'USD/shares': return None  # EPS em outra moeda / por acao ordinaria (ADR): fora
    last = max(eps)
    if (t - eps[last][2]).days > STALE_DAYS: return None
    e = {y: v / split_factor_after(splits, filed) for y, (v, filed, _) in eps.items()}
    rates = [ratio(e.get(y), e.get(y - 1)) for y in range(last - N_HIST + 1, last + 1)]
    ok = [r for r in rates if np.isfinite(r)]
    growth = float(np.median(ok)) if len(ok) >= (N_HIST + 1) // 2 else np.nan
    zgrowth = engine.cv(rates, growth) if np.isfinite(growth) else np.nan

    s = {k: asof(pit[k], t)[0] for k in ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income')}
    g = lambda k, y: s[k][y][0] if y in s[k] else None
    roics, num, den = [], {}, {}
    for y in range(last - 5, last + 1):
        if fin:
            ni, eq = g('net_income', y), g('equity', y)
            if ni is not None and eq is not None:
                num[y], den[y] = ni, eq
            roics.append(ni / eq if ni is not None and eq and eq > 0 else np.nan)
            continue
        oi, eq = g('op_income', y), g('equity', y)
        if oi is None or eq is None:
            roics.append(np.nan); continue
        pt, tx = g('pretax', y), g('tax', y)
        tr = min(max(tx / pt, 0), 0.5) if pt and tx is not None and pt > 0 else 0.21
        ic = eq + (g('lt_debt', y) or 0.0) - (g('cash', y) or 0.0)
        num[y], den[y] = oi * (1 - tr), ic
        roics.append(oi * (1 - tr) / ic if ic > 0 else np.nan)
    roic = engine.roic_metric(roics)
    zroic = engine.cv(roics, roic)
    # ROIC marginal de 5 anos: delta NOPAT / delta capital investido (financeiras: delta lucro / delta patrimonio)
    y1, y0 = last, last - 5
    roic_marg, d_ic = np.nan, np.nan
    if y1 in num and y0 in num:
        d_ic = den[y1] - den[y0]
        if d_ic > 0:
            roic_marg = (num[y1] - num[y0]) / d_ic
    return dict(growth=growth, zgrowth=zgrowth, roic=roic, zroic=zroic, roic_marg=roic_marg, d_ic=d_ic, eps=e[last], last_fy=last,
                n_rates=len(ok), n_roic=int(np.isfinite(roics).sum()))


# ---------------------------------------------------------------- classificacao em cada data
def rebalance_dates(px):
    qs = pd.date_range(START, px.index.max(), freq='QS')
    out = []
    for q in qs:
        prev = px.index[px.index < q]
        if len(prev): out.append(prev[-1])  # fechamento do ultimo pregao antes do trimestre
    return out


def classify_all(u, close, divs, splits_all, dates):
    pits = {tk: load_pit(tk) for tk in u.ticker}
    rows = []
    for d in dates:
        for r in u.itertuples():
            pit = pits.get(r.ticker)
            if pit is None or r.ticker not in close: continue
            p = close.at[d, r.ticker]
            if not np.isfinite(p) or p <= 0: continue
            sp = splits_all[r.ticker]; sp = sp[sp > 0]
            f = features(pit, d, r.fin, sp)
            if f is None: continue
            dv = divs[r.ticker]
            dy = dv[(dv.index > d - pd.Timedelta(days=730)) & (dv.index <= d)].sum() / 2 / p
            rows.append(dict(date=d, ticker=r.ticker, fin=r.fin, price=p, dy=dy, **f))
        print(d.date(), sum(1 for x in rows if x['date'] == d), flush=True)
    df = pd.DataFrame(rows)
    out = []
    for d, x in df.groupby('date'):
        x = x.copy()
        x['g'] = engine.block_g(x)
        x['fair_pe'] = engine.fair_pe(x.g, x.roic)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        for name, cut in CUTS.items():
            saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
            try:
                c = engine.classify(x)
            finally:
                engine.TH['zGrowth'] = saved
            x[f'cat_{name}'] = np.where(c.code.isna(), None, c.category)  # sem dado suficiente: fora de toda classe
        out.append(x)
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- carteiras
TIERS = {'Opportunity of Lifetime': 'A', 'Good Companies, Great Returns': 'A', 'Excellent but Fair': 'A',
         'Good but Margin of Safety Required': 'B', 'Cheap Slow Compounder': 'B', 'Interesting but Requires Attention': 'B',
         'Cheap but Aggressive': 'B', 'Expensive for what you get': 'C', 'Investable but Not Good': 'C',
         'Expensive': 'C', 'Do not Waste Time': 'D'}


def portfolios(cls, col):
    """{nome: {data: [tickers]}} para cada classe e para o universo inteiro (contraprova)."""
    p = {}
    for d, x in cls.groupby('date'):
        x = x[x[col].notna()]
        groups = {c: g.ticker.tolist() for c, g in x.groupby(col)}
        for c, tks in groups.items():
            p.setdefault(c, {})[d] = tks
        p.setdefault('Universo EW', {})[d] = x.ticker.tolist()
    return p


def run_portfolio(holdings, adj, dates):
    """NAV diario de uma carteira equal weight rebalanceada nas datas; devolve NAV bruto, liquido, giro e n."""
    nav, nav_net, v, vn = [], [], 1.0, 1.0
    prev_w = pd.Series(dtype=float)
    turn, ns = [], []
    for i, d in enumerate(dates[:-1]):
        nxt = dates[i + 1]
        tks = [t for t in holdings.get(d, []) if t in adj and np.isfinite(adj.at[d, t])]
        seg = adj.loc[d:nxt]
        if not tks:  # classe vazia: fica em caixa (retorno zero)
            path = pd.Series(1.0, index=seg.index)
            w_end, w = pd.Series(dtype=float), pd.Series(dtype=float)
        else:
            rel = seg[tks].ffill().div(seg[tks].iloc[0])
            path = rel.mean(axis=1)
            w = pd.Series(1 / len(tks), index=tks)
            w_end = (rel.iloc[-1] * w) / (rel.iloc[-1] * w).sum()
        to = (w.reindex(w.index.union(prev_w.index), fill_value=0)
              - prev_w.reindex(w.index.union(prev_w.index), fill_value=0)).abs().sum() / 2 if i else w.sum() / 2 if len(w) else 0
        turn.append(to); ns.append(len(tks))
        cost = to * 2 * COST_BPS / 1e4
        seg_nav = v * path; seg_net = vn * (1 - cost) * path
        nav.append(seg_nav.iloc[:-1] if i < len(dates) - 2 else seg_nav)
        nav_net.append(seg_net.iloc[:-1] if i < len(dates) - 2 else seg_net)
        v, vn = seg_nav.iloc[-1], seg_net.iloc[-1]
        prev_w = w_end
    return pd.concat(nav), pd.concat(nav_net), np.mean(turn[1:]) if len(turn) > 1 else np.nan, np.mean(ns)


def stats(nav):
    nav = nav.dropna()
    yrs = (nav.index[-1] - nav.index[0]).days / 365.25
    r = nav.pct_change().dropna()
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    dd = (nav / nav.cummax() - 1).min()
    return dict(CAGR=cagr, Vol=vol, Sharpe=cagr / vol if vol else np.nan, MaxDD=dd, Total=nav.iloc[-1] - 1)


def main():
    u = pd.read_csv(D / 'universe.csv')
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    close, adj, divs, splits = read('close'), read('adj_close'), read('dividends').fillna(0), read('stock_splits').fillna(0)
    dates = rebalance_dates(close)
    cache = D / 'classes_pit.csv'
    if cache.exists():
        cls = pd.read_csv(cache, parse_dates=['date'])
    else:
        cls = classify_all(u, close, divs, splits, dates)
        cls.to_csv(cache, index=False)
    cov = cls.groupby('date').size()
    covA = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = covA[covA >= 0.4 * len(u)].index.min()  # comeca quando >= 40% do universo tem classe
    dates = [d for d in dates if d >= start]
    print('inicio do backtest:', start.date(), '| datas:', len(dates))
    results = {}
    for name in CUTS:
        ports = portfolios(cls[cls.date >= start], f'cat_{name}')
        navs = {}
        rows = []
        for pname, hold in ports.items():
            g, n, to, avg_n = run_portfolio(hold, adj, dates)
            navs[pname] = g; navs[pname + ' (liq.)'] = n
            rows.append(dict(Carteira=pname, **stats(g), **{'CAGR liq.': stats(n)['CAGR']}, Giro=to, **{'N medio': avg_n},
                             **{'Trim. vazios': sum(1 for d in dates[:-1] if not hold.get(d))}))
        for b in BENCH:
            nb = adj[b].loc[dates[0]:dates[-1]]; nb = nb / nb.iloc[0]
            navs[b] = nb
            rows.append(dict(Carteira=b, **stats(nb), **{'CAGR liq.': stats(nb)['CAGR']}, Giro=0, **{'N medio': np.nan}, **{'Trim. vazios': 0}))
        pd.DataFrame(navs).to_csv(D / f'nav_{name}.csv')
        results[name] = pd.DataFrame(rows)
    # cobertura por data
    pd.DataFrame({'com_dados': cov, 'com_classe': covA}).to_csv(D / 'coverage.csv')
    return results, start, dates


if __name__ == '__main__':
    res, start, dates = main()
    for k, v in res.items():
        v.to_csv(D / f'stats_{k}.csv', index=False)
        print('\n==', k)
        print(v.sort_values('CAGR', ascending=False).to_string(index=False, float_format=lambda x: f'{x:.3f}'))
