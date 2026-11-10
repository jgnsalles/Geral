"""Retorno esperado com EPS medio de 3 anos crescendo 3 anos (para chegar a t+2), contra o EPS do ultimo ano crescendo 2 anos.
V0 atual: P/E justo x EPS(t) x (1+G)^2
V1: P/E justo x media(EPS t, t-1, t-2) x (1+G)^3            (G = mediana de 5 taxas, a do modelo)
V2: P/E justo x media(EPS t, t-1, t-2) x (1+CAGR 3 anos)^3  (CAGR = (EPS t / EPS t-3)^(1/3) - 1; sem CAGR valido usa G)
Sem os 3 anos de EPS, cai no V0. Universo point-in-time, sem zROIC, ROIC oficial corrigido, esboco (OoL a partir de 12%).
Saidas: backtest/eps_media.md
Uso: python3 backtest/eps_media.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import load_pit, asof, split_factor_after, run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
VNAME = {'V0': 'V0 atual: EPS do último ano × (1+G)²', 'V1': 'V1: EPS médio 3 anos × (1+G)³', 'V2': 'V2: EPS médio 3 anos × (1+CAGR 3a)³'}


def eps_hist(f, spl):
    cache, rows = {}, []
    for r in f[['date', 'ticker', 'last_fy']].itertuples():
        if r.ticker not in cache: cache[r.ticker] = load_pit(r.ticker)
        e, _ = asof(cache[r.ticker]['eps_diluted'], r.date)
        s = spl[r.ticker][spl[r.ticker] > 0] if r.ticker in spl else pd.Series(dtype=float)
        v = lambda y: e[y][0] / split_factor_after(s, e[y][1]) if y in e else np.nan
        y = int(r.last_fy)
        rows.append((v(y), v(y - 1), v(y - 2), v(y - 3)))
    return pd.DataFrame(rows, columns=['e0', 'e1', 'e2', 'e3'], index=f.index)


def classify(f, var):
    parts = []
    for d, x in f.groupby('date'):
        x = x.copy(); x['g'] = cb.g_rank(x, 0.07)
        r = x.roic.clip(upper=1.0)
        x['fair_pe'] = np.where(r > 0, (1 - x.g / r) / (0.085 - x.g), np.nan)
        avg = x[['e0', 'e1', 'e2']].mean(axis=1).where(x[['e0', 'e1', 'e2']].notna().all(axis=1))
        cagr = ((x.e0 / x.e3) ** (1 / 3) - 1).where((x.e0 > 0) & (x.e3 > 0))
        if var == 'V0':
            fut = x.eps * (1 + x.growth) ** 2
        else:
            gg = x.growth if var == 'V1' else cagr.fillna(x.growth)
            fut = (avg * (1 + gg) ** 3).fillna(x.eps * (1 + x.growth) ** 2)
        x['eps_fut'] = fut
        base = x.fair_pe * fut / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    x = pd.concat(parts)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, **vp.PARAMS['sketch']})
    try:
        c = engine.classify(x)
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(c.code.isna(), None, c.category)
    return c


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member].assign(zroic=0.0).reset_index(drop=True)
    px_ = load_prices(); adj = px_['adj_close']
    f = pd.concat([f, eps_hist(f, px_['stock_splits'])], axis=1)
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; Ms = spy.resample('ME').last(); S = stats(spy)['CAGR']
    out = ['# Retorno esperado com EPS médio de 3 anos (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** o P/E justo que multiplica o EPS usa o ROIC oficial (corrigido em 2026-11-10); casos suspeitos continuam em aberto.\n',
           'Configuração: sem zROIC, OoL a partir de ROIC 12%. Só muda o "retorno com convergência ao P/E justo"; o "múltiplo constante" '
           '(G + dividend yield) e todo o resto ficam iguais. A média de 3 anos está centrada em t−1, por isso cresce 3 anos para chegar a t+2. '
           f'S&P 500: {pc(S)} a.a.\n']
    res, C = [], {}
    for var in VNAME:
        c = classify(f, var); C[var] = c
        c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
        cc = c[c.date < dates[-1]]
        uq = cc[cc.cat.notna()].groupby('date').rq.mean()
        row = {'Variante': VNAME[var]}
        groups = {'OoL': c.cat == OOL, 'OoL High Returns': (c.cat == OOL) & (c.roic > .3), 'OoL High Growth': (c.cat == OOL) & (c.growth > .3),
                  'OoL Base': (c.cat == OOL) & (c.roic <= .3) & (c.growth <= .3), 'GCGR': c.cat == GCGR}
        for k, m in groups.items():
            nav = run_portfolio({d: g.ticker.tolist() for d, g in c[m].groupby('date')}, adj, dates)[0]
            Mn = nav.resample('ME').last(); w5 = ((Mn / Mn.shift(60)) > (Ms / Ms.shift(60)))[(Mn / Mn.shift(60)).notna() & (Ms / Ms.shift(60)).notna()].mean()
            row[k] = stats(nav)['CAGR']; row[k + ' n'] = c[m].groupby('date').size().mean(); row[k + ' w5'] = w5
        # o retorno esperado ordena? excesso mediano por faixa (OoL+GCGR)
        x = cc[cc.cat.isin([OOL, GCGR])].copy(); x['ex'] = x.rq - x.date.map(uq)
        x['q'] = x.groupby('date').ret.transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False) if len(s) >= 5 else np.nan)
        row['quint'] = (x.groupby('q').ex.median() * 4).to_dict()
        row['ic'] = x.groupby('date').apply(lambda s: s.ret.corr(s.ex, method='spearman')).mean()
        row['n_fallback'] = (c.e0.notna() & c[['e0', 'e1', 'e2']].isna().any(axis=1)).mean()
        res.append(row); print(var, flush=True)
    out += ['## 1. Carteiras\n', '| Variante | OoL | OoL ações | OoL: janelas 5a > S&P | High Returns | High Growth | OoL Base | GCGR | GCGR ações |',
            '|---|---|---|---|---|---|---|---|---|']
    for r in res:
        out.append(f"| {r['Variante']} | **{pc(r['OoL'])}** | {r['OoL n']:.0f} | {r['OoL w5']:.0%} | {pc(r['OoL High Returns'])} | {pc(r['OoL High Growth'])} | "
                   f"{pc(r['OoL Base'])} | **{pc(r['GCGR'])}** | {r['GCGR n']:.0f} |")
    out += ['', '## 2. O retorno esperado passa a ordenar?\n',
            'Posições da OoL + GCGR divididas em quintis do retorno esperado dentro de cada trimestre; excesso mediano a.a. sobre o universo. '
            'Correlação de postos média (retorno esperado × excesso do trimestre seguinte): positiva = ordena na direção certa.\n',
            '| Variante | Q1 (menor) | Q2 | Q3 | Q4 | Q5 (maior) | Correlação de postos |', '|---|---|---|---|---|---|---|']
    for r in res:
        q = r['quint']; out.append(f"| {r['Variante']} | " + ' | '.join(sg(q.get(i, np.nan)) for i in range(5)) + f" | {r['ic']:+.3f} |".replace('.', ','))
    # quem entra e sai da OoL
    a = C['V0'][C['V0'].cat == OOL]; b = C['V1'][C['V1'].cat == OOL]
    ka, kb = set(zip(a.date, a.ticker)), set(zip(b.date, b.ticker))
    ins = pd.Series([t for _, t in kb - ka]).value_counts(); outs = pd.Series([t for _, t in ka - kb]).value_counts()
    out += ['', '## 3. V1 contra o atual: quem entra e quem sai da OoL\n',
            f'Posições que entram: {len(kb - ka)}; que saem: {len(ka - kb)} (de {len(ka)}).\n',
            '- Entram (mais trimestres): ' + ', '.join(f'{t} ({n})' for t, n in ins.head(15).items()),
            '- Saem (mais trimestres): ' + ', '.join(f'{t} ({n})' for t, n in outs.head(15).items())]
    for tk in ['CPRI', 'TPR', 'FOSL', 'CLF', 'LULU', 'NVDA', 'ANET']:
        x0, x1 = C['V0'], C['V1']
        n0 = ((x0.ticker == tk) & (x0.cat == OOL)).sum(); n1 = ((x1.ticker == tk) & (x1.cat == OOL)).sum()
        out.append(f'- {tk}: {n0} → {n1} trimestres na OoL')
    (ROOT / 'eps_media.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
