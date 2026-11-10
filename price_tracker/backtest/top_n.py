"""Carteira de tamanho fixo pre-registrada (2026-11-10): as N melhores por percentil de ROIC + percentil de crescimento entre as elegiveis
(ROIC >= 12%, crescimento >= 15%, sem ciclicos e vestuario). Produto: N = 20; 10 e 15 como sensibilidade.
Peso: raiz do valor de mercado com teto de 2/N (peso igual como controle). EUA e Brasil.
Saidas: backtest/top_n.md, backtest/top_n.png. Uso: python3 backtest/top_n.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, shares, DUAL  # noqa: E402
from backtest import stats, D  # noqa: E402
from validation_factors import factors, reg  # noqa: E402

NS = (20, 15, 10)
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
pp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.1f}'.replace('.', ',')
n2 = lambda x: '—' if pd.isna(x) else f'{x:.2f}'.replace('.', ',')


def cap(w, mx):
    w = w / w.sum()
    for _ in range(50):
        over = w > mx + 1e-12
        if not over.any(): break
        ex = (w[over] - mx).sum(); w[over] = mx; free = ~over & (w < mx)
        if not free.any(): break
        w[free] += ex * w[free] / w[free].sum()
    return w / w.sum()


def pick(x, n):
    x = x.copy()
    x['score'] = x.roic.rank(pct=True) + x.growth.rank(pct=True)
    return x.sort_values(['score', 'roic'], ascending=False).head(n)


def build(el, adj, dates, n):
    """el: elegiveis com date, ticker, roic, growth, mcap. Devolve navs (raiz com teto, peso igual) e escolhidas."""
    chosen = pd.concat([pick(g, n) for _, g in el.groupby('date')])
    wr = {d: cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), 2 / n) for d, g in chosen.groupby('date')}
    we = {d: pd.Series(1.0, index=g.ticker) for d, g in chosen.groupby('date')}
    return run_weighted(wr, adj, dates), run_weighted(we, adj, dates), chosen


def mcap_us(c, rows):
    sh = shares(rows[['date', 'ticker', 'eps', 'last_fy', 'price']].drop_duplicates(['date', 'ticker']))
    m = pd.Series([p * sh.get((d, t), np.nan) for d, t, p in zip(rows.date, rows.ticker, rows.price)], index=rows.index)
    m = m.where(m > 0); m = m.fillna(m.groupby(rows.date).transform('median'))
    firm = rows.ticker.map(lambda t: DUAL.get(t, t))
    return m / rows.assign(firm=firm).groupby(['date', 'firm']).ticker.transform('size')


def main():
    # ---------------- EUA
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    c = bm.classify_new(f)
    el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & c.roic.notna() & c.growth.notna()].copy()
    el['mcap'] = mcap_us(c, el)
    navs, n_, dts, _ = bm.load_benchmarks()
    E = pd.read_csv(D / 'etfs_rivais.csv', index_col=0, parse_dates=True)
    s = E['QQQ'].loc[dates[0]:dates[-1]].dropna(); navs['Nasdaq-100 (QQQ)'] = s / s.iloc[0]
    chosen_us = {}
    for n in NS:
        a, b, ch = build(el, adj, dates, n)
        navs[f'Top {n} — raiz com teto'] = a; navs[f'Top {n} — peso igual'] = b; n_[f'Top {n} — raiz com teto'] = n_[f'Top {n} — peso igual'] = ch.groupby('date').size().mean()
        chosen_us[n] = ch; print('EUA', n, flush=True)
    out = ['# Carteira de tamanho fixo pré-registrada: as 20 melhores por ROIC + crescimento (EUA e Brasil)\n',
           '> ⚠️ **ROIC:** a nota usa o ROIC do modelo (oficial nos EUA; clássico no Brasil). Casos de ROIC aberrante (patrimônio negativo, empresas leves '
           'em ativos) ainda estão em aberto e podem subir no ranking.\n',
           '**Regra (registrada no PROTOCOLO antes de rodar):** elegíveis = ROIC ≥ 12% e crescimento do EPS ≥ 15%, sem cíclicos e sem vestuário. '
           'Nota = percentil do ROIC + percentil do crescimento; ficam as N maiores. Peso = raiz do valor de mercado com teto de 2/N por ação. '
           '**Produto: N = 20.** N = 15 e 10 são sensibilidade. Sem P/E justo, retorno esperado ou zGrowth.\n',
           '## 1. EUA (universo point-in-time do S&P 500)\n'] + bm.bench_table(navs, n_)
    Fct = factors(); cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'UMD', 'QMJ']
    out += ['', '### Alfa contra Fama-French 5 + momentum + qualidade (mensal, Newey-West)\n', '| Carteira | Alfa a.a. | t | R² |', '|---|---|---|---|']
    for k in [k for k in navs if k.startswith('Top')] + ['OoL novo', 'Nasdaq-100 (QQQ)']:
        r = navs[k].resample('ME').last().pct_change().dropna(); m, _ = reg(r - Fct['RF'].reindex(r.index), Fct[cols].reindex(r.index))
        out.append(f"| {k} | {pp(m.params['const'] * 12)} | {n2(m.tvalues['const'])} | {n2(m.rsquared)} |")
    # concentracao e giro (N=20)
    ch = chosen_us[20]
    sets = ch.groupby('date').ticker.apply(set); turn = np.mean([1 - len(a & b) / max(len(a), 1) for a, b in zip(sets.iloc[:-1], sets.iloc[1:])])
    sec_share = ch.sector.value_counts(normalize=True).head(4)
    out += ['', f'Top 20 nos EUA: {ch.groupby("date").size().min()}–{ch.groupby("date").size().max()} ações por trimestre; troca média de '
            f'{turn:.0%} dos nomes por trimestre; setores: ' + ', '.join(f'{k} {v:.0%}' for k, v in sec_share.items()) + '.\n',
            f'**Top 20 de hoje (EUA, {ch.date.max():%m/%Y}):** ' + ', '.join(ch[ch.date == ch.date.max()].ticker) + '\n']
    # ---------------- Brasil
    import oos_congelado as oc
    BD = ROOT.parent / 'brasil' / 'data'
    u = pd.read_csv(BD / 'universe.csv'); sec = u.set_index('yf').Setor_Atividade; tkr = u.set_index('yf').ticker; cvm = u.set_index('yf').Codigo_CVM
    b = pd.read_csv(BD / 'classes_pit.csv', parse_dates=['date'])
    adjb = pd.read_csv(BD / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = b.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    bd = sorted(d for d in b.date.unique() if d >= start); b = b[b.date.isin(bd)].copy()
    cyc = b.ticker.map(sec).isin(oc.CYC_SECTORS) | b.ticker.map(tkr).isin(oc.CYC_TICKERS); app = b.ticker.map(tkr).isin(oc.APPAREL)
    fund = pd.read_csv(BD / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
    elb = b[~cyc & ~app & (b.roic >= .12) & (b.growth >= .15) & b['cat_zg2.93'].notna()].copy()
    sh = []
    for rr in elb.itertuples():
        ff = fund[(fund.CD_CVM == cvm.get(rr.ticker)) & (fund.DT_RECEB <= rr.date) & (fund.fy == rr.last_fy)]
        ni = ff.sort_values('DT_RECEB').ni.iloc[-1] if len(ff) else np.nan
        sh.append(ni / rr.eps if pd.notna(ni) and rr.eps and abs(rr.eps) > 1e-6 and np.sign(ni) == np.sign(rr.eps) else np.nan)
    elb['sh'] = sh; elb['sh'] = elb.groupby('ticker').sh.transform(lambda s: s.ffill().bfill())
    elb['mcap'] = (elb.price * elb.sh).where(lambda s: s > 0); elb['mcap'] = elb.mcap.fillna(elb.groupby('date').mcap.transform('median'))
    nb, nnb = {}, {}
    for n in NS:
        a, bb, chb = build(elb, adjb, bd, n)
        nb[f'Top {n} — raiz com teto'] = a; nb[f'Top {n} — peso igual'] = bb; nnb[n] = chb.groupby('date').size().mean(); print('BR', n, flush=True)
    univ = b[b['cat_zg2.93'].notna()]
    nb['Universo (todas as classificadas), peso igual'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in univ.groupby('date')}, adjb, bd)
    for t, lab in (('BOVA11.SA', 'Ibovespa (BOVA11)'), ('SMAL11.SA', 'Small caps (SMAL11)')):
        s = adjb[t].loc[bd[0]:bd[-1]].dropna(); nb[lab] = s / s.iloc[0]
    IB = nb['Ibovespa (BOVA11)']; MI = IB.resample('ME').last(); SI = stats(IB)['CAGR']
    def wn(nav, y):
        M = nav.resample('ME').last(); a = M / M.shift(12 * y); c_ = (MI / MI.shift(12 * y)).reindex(a.index); k = a.notna() & c_.notna()
        return (a[k] > c_[k]).mean() if k.any() else np.nan
    out += ['', f'## 2. Brasil (fora da amostra, {pd.Timestamp(bd[0]):%m/%Y} a {pd.Timestamp(bd[-1]):%m/%Y}, em reais)\n',
            '| Carteira | Ações (média) | Retorno anual | vs Ibovespa | Pior queda | Janelas 3a > Ibov | Janelas 5a > Ibov |', '|---|---|---|---|---|---|---|']
    for k, nav in nb.items():
        st = stats(nav); nn = next((nnb[n] for n in NS if k.startswith(f'Top {n} ')), np.nan)
        out.append(f"| {k} | {'—' if pd.isna(nn) else f'{nn:.0f}'} | **{pc(st['CAGR'])}** | {pp(st['CAGR'] - SI)} | {pc(st['MaxDD'])} | {wn(nav, 3):.0%} | {wn(nav, 5):.0%} |")
    (ROOT / 'top_n.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot({k: v for k, v in navs.items() if k in bm.ORDER or k in ('Nasdaq-100 (QQQ)', 'Top 20 — raiz com teto', 'Top 20 — peso igual')},
                  ROOT / 'top_n.png', 'EUA: Top 20 por ROIC + crescimento (raiz com teto) × comparativos obrigatórios e QQQ')


if __name__ == '__main__':
    main()
