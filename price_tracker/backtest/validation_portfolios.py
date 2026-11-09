"""Fase 2 do protocolo: candidatas congeladas em (a) universo point-in-time (membros do S&P 500 na data) e (b) universo atual,
com o ROIC oficial (B com reserva em A) e, como robustez, com (A) e (C). Teste de limites para membros sem dados.
Saidas: backtest/data/val_monthly.csv (retornos mensais para as Fases 3 e 4), backtest/validation_phase2.md
Uso: python3 backtest/validation_portfolios.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import combos as cb  # noqa: E402
from backtest import run_portfolio, stats, D  # noqa: E402
from validation_core import load_prices, universe_table  # noqa: E402
from pit_universe import membership, at  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
PARAMS = {'orig': {'Roic_Hi': 0.20, 'Roic_Lo': 0.10}, 'sketch': {'Roic_Hi': 0.12, 'Roic_Lo': 0.10}}
CANDS = {  # nome: (parametros, selecao)
    'C1 Good Companies, Great Returns': ('orig', lambda c: c.cat == GCGR),
    'C3 OoL original (controle)': ('orig', lambda c: c.cat == OOL),
    'C2a OoL Base': ('sketch', lambda c: (c.cat == OOL) & (c.roic <= 0.30) & (c.growth <= 0.30)),
    'C2b OoL High Returns': ('sketch', lambda c: (c.cat == OOL) & (c.roic > 0.30)),
    'C2c OoL High Growth': ('sketch', lambda c: (c.cat == OOL) & (c.growth > 0.30)),
    'C2d OoL corte 12% (todas)': ('sketch', lambda c: c.cat == OOL),
}
ROIC_DEFS = {'B': ('roic', 'zroic'), 'A': ('roic_a', 'zroic_a'), 'C': ('roic_marg', 'zroic')}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def classify(f, params, roic_def):
    rc, zc = ROIC_DEFS[roic_def]
    f = f.copy(); f['roic'], f['zroic'] = f[rc], f[zc]
    parts = []
    for d, x in f.groupby('date'):
        x = x.copy(); x['g'] = cb.g_rank(x, 0.07)
        r = x.roic.clip(upper=1.0)
        x['fair_pe'] = np.where(r > 0, (1 - x.g / r) / (0.085 - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    x = pd.concat(parts)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, **PARAMS[params]})
    try:
        c = engine.classify(x)
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat'] = np.where(c.code.isna(), None, c.category)
    return c


def quarterly(nav, dates):
    s = nav.reindex(pd.DatetimeIndex(dates), method='ffill')
    return s.pct_change().dropna()


def cagr_q(r):
    return (1 + r).prod() ** (4 / len(r)) - 1


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    px = load_prices(); adj = px['adj_close']
    t = universe_table(); mem, miss, miss_list = membership(set(t.ticker))
    first = f[f.pit_member].groupby('date').size()
    start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates)]
    spy_q = quarterly(adj['SPY'], dates); rsp_q = quarterly(adj['RSP'], dates)
    out = ['# Fase 2: universo point-in-time, definições de ROIC e teste de limites (EUA)\n',
           '> ⚠️ **ROIC:** oficial = (B) operacional com aquisições, com reserva em (A); (A) e (C) como robustez.\n',
           f'Período: {dates[0]:%d/%m/%Y} a {dates[-1]:%d/%m/%Y} ({len(dates) - 1} trimestres). Universo point-in-time = membros do S&P 500 na data '
           '(composição histórica pública); universo atual = S&P 500 de hoje + planilha (o que usávamos antes).\n']
    monthly, res = {}, []
    for uname, umask in (('PIT', f.pit_member), ('Atual', f.cur_universe)):
        for rdef in ('B', 'A', 'C'):
            cache = {}
            for cname, (params, sel) in CANDS.items():
                if params not in cache: cache[params] = classify(f[umask], params, rdef)
                c = cache[params]
                hold = {d: g.ticker.tolist() for d, g in c[sel(c)].groupby('date')}
                nav, net, to, n = run_portfolio(hold, adj, dates)
                res.append(dict(u=uname, roic=rdef, cand=cname, nav=nav, net=net, n=n, to=to,
                                share={d: len(hold.get(d, [])) / max(1, c[c.cat.notna() & (c.date == d)].shape[0]) for d in dates}))
                if rdef == 'B': monthly[f'{uname}|{cname}'] = nav.resample('ME').last().pct_change()
            c = cache['orig']
            univ = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat.notna()].groupby('date')}, adj, dates)[0]
            res.append(dict(u=uname, roic=rdef, cand='Universo EW', nav=univ, net=univ, n=c[c.cat.notna()].groupby('date').size().mean(), to=np.nan,
                            share={d: 1.0 for d in dates}))
            if rdef == 'B': monthly[f'{uname}|Universo EW'] = univ.resample('ME').last().pct_change()
            print(uname, rdef, flush=True)
    for b in ('SPY', 'RSP'):
        monthly[f'Bench|{b}'] = adj[b].loc[dates[0]:dates[-1]].resample('ME').last().pct_change()
    pd.DataFrame(monthly).to_csv(D / 'val_monthly.csv')

    get = lambda u, r, c: next(x for x in res if x['u'] == u and x['roic'] == r and x['cand'] == c)
    # 1) PIT x Atual, ROIC oficial
    out += ['## 1. Universo point-in-time × universo atual (ROIC oficial B)\n',
            '| Carteira | PIT: CAGR | PIT: vs Universo EW | PIT: t | PIT: ações | Atual: CAGR | Atual: vs Universo EW | Viés (Atual − PIT) |',
            '|---|---|---|---|---|---|---|---|']
    for cname in list(CANDS) + ['Universo EW']:
        a, b = get('PIT', 'B', cname), get('Atual', 'B', cname)
        ua, ub = get('PIT', 'B', 'Universo EW'), get('Atual', 'B', 'Universo EW')
        qa, qu = quarterly(a['nav'], dates), quarterly(ua['nav'], dates)
        e = (qa - qu).dropna(); t = e.mean() / e.std() * np.sqrt(len(e)) if e.std() > 0 else np.nan
        exa = stats(a['nav'])['CAGR'] - stats(ua['nav'])['CAGR']; exb = stats(b['nav'])['CAGR'] - stats(ub['nav'])['CAGR']
        out.append(f"| {cname} | {pc(stats(a['nav'])['CAGR'])} | {sg(exa) if cname != 'Universo EW' else '—'} | {nm(t) if cname != 'Universo EW' else '—'} | {nm(a['n'])} | "
                   f"{pc(stats(b['nav'])['CAGR'])} | {sg(exb) if cname != 'Universo EW' else '—'} | {sg(stats(b['nav'])['CAGR'] - stats(a['nav'])['CAGR'])} |")
    out.append(f"| *SPY* | {pc(cagr_q(spy_q))} | | | | | | |")
    out.append(f"| *RSP (S&P 500 equal weight real)* | {pc(cagr_q(rsp_q))} | | | | | | |")
    # 2) teste de limites (PIT, ROIC B)
    nmiss = {d: miss[max(k for k in miss if k <= d)] for d in dates}
    nmem = {d: len(at(mem, d)) + nmiss[d] for d in dates}
    exit_share = {}
    for i, d in enumerate(dates[:-1]):
        lost_now = set(at(miss_list, d)); lost_next = set(at(miss_list, dates[i + 1]))
        members_next = set(at(mem, dates[i + 1])) | lost_next
        exit_share[d] = len([x for x in lost_now if x not in members_next]) / max(1, len(lost_now))
    uq = quarterly(get('PIT', 'B', 'Universo EW')['nav'], dates)
    scen = {'Pessimista (−100% na saída)': lambda d: exit_share.get(d, 0) * -1 + (1 - exit_share.get(d, 0)) * uq.get(dates[dates.index(d) + 1], np.nan) if d != dates[-1] else np.nan,
            'Neutro (retorno do universo)': lambda d: uq.get(dates[dates.index(d) + 1], np.nan) if d != dates[-1] else np.nan,
            'Otimista (retorno do SPY)': lambda d: spy_q.get(dates[dates.index(d) + 1], np.nan) if d != dates[-1] else np.nan}
    out += ['', '## 2. Teste de limites: membros do índice sem dados (PIT, ROIC oficial)\n',
            f'Membros sem dados: {nmiss[dates[0]]} em {dates[0]:%Y} ({nmiss[dates[0]] / nmem[dates[0]]:.0%}), '
            f'{nmiss[dates[len(dates) // 2]]} em {dates[len(dates) // 2]:%Y}, {nmiss[dates[-1]]} em {dates[-1]:%Y}. '
            'Cada carteira recebe esses membros na mesma proporção em que a classe aparece no universo classificado.\n'.replace('.', ',', 0),
            '| Carteira | ' + ' | '.join(f'{s}: CAGR / vs Universo' for s in scen) + ' |', '|---|' + '---|' * len(scen)]
    u_adj = {}
    for s, fn in scen.items():
        rq = []
        for i, d in enumerate(dates[:-1]):
            m = nmiss[d]; n = get('PIT', 'B', 'Universo EW')['n']
            rq.append((uq.iloc[i] * n + fn(d) * m) / (n + m))
        u_adj[s] = pd.Series(rq, index=uq.index)
    for cname in CANDS:
        x = get('PIT', 'B', cname); q = quarterly(x['nav'], dates)
        cells = []
        for s, fn in scen.items():
            rq = []
            for i, d in enumerate(dates[:-1]):
                n_c = max(x['share'][d] * get('PIT', 'B', 'Universo EW')['n'], 1e-9)
                m_c = nmiss[d] * x['share'][d]
                rq.append((q.iloc[i] * n_c + fn(d) * m_c) / (n_c + m_c))
            r = pd.Series(rq, index=q.index)
            cells.append(f'{pc(cagr_q(r))} / {sg(cagr_q(r) - cagr_q(u_adj[s]))}')
        out.append(f'| {cname} | ' + ' | '.join(cells) + ' |')
    out.append('| *Universo EW* | ' + ' | '.join(f'{pc(cagr_q(u_adj[s]))} / —' for s in scen) + ' |')
    # 3) robustez de ROIC (PIT)
    out += ['', '## 3. Robustez à definição de ROIC (universo point-in-time)\n',
            '| Carteira | (B) oficial: CAGR / vs Universo | (A) atual: CAGR / vs Universo | (C) marginal: CAGR / vs Universo |', '|---|---|---|---|']
    for cname in CANDS:
        cells = []
        for r in 'BAC':
            x, u0 = get('PIT', r, cname), get('PIT', r, 'Universo EW')
            cells.append(f"{pc(stats(x['nav'])['CAGR'])} / {sg(stats(x['nav'])['CAGR'] - stats(u0['nav'])['CAGR'])} ({nm(x['n'])} ações)")
        out.append(f'| {cname} | ' + ' | '.join(cells) + ' |')
    (ROOT / 'validation_phase2.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
