"""Teste 'mundo' pre-registrado (2026-11-12, ver PROTOCOLO.md): regra congelada sobre S&P 500 PIT + medias/pequenas dos EUA + estrangeiras
listadas nos EUA + Brasil (em dolar). Retorno esperado do Brasil menos 3,5 p.p. (diferenca de WACC). Saidas: mundo/resultado.md e .png.
Uso: python3 mundo/backtest_mundo.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
for s in ('', 'backtest', 'brasil', 'midsmall', 'estrangeiras'): sys.path.insert(0, str(P / s))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
import backtest_ms, backtest_fpi, sem2021  # noqa: E402

BR_ADJ = 0.035
COLS = ['date', 'ticker', 'base', 'nome', 'roic', 'growth', 'pe', 'ret', 'mcap', 'elig']


def us_sp():
    f, dates = bm.base_data(); c = bm.classify_new(f); adj = bm.load_prices()['adj_close']
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c['elig'] = ~c.excluded & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4) & c.roic.notna() & c.growth.notna()
    c['mcap'] = np.nan; c.loc[c.elig, 'mcap'] = top_n.mcap_us(c, c[c.elig])
    u = pd.read_csv(P / 'backtest' / 'data' / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    c['nome'] = c.ticker.map(u.name).fillna(c.ticker); c['base'] = 'S&P 500'
    return c, adj, dates


def generic(mod, base):
    cache = ROOT / 'cache' / f'{mod.__name__}.pkl'
    if cache.exists():
        c, adj, dates, u = pd.read_pickle(cache)
    else:
        c, adj, dates, u, _ = mod.build(); cache.parent.mkdir(exist_ok=True); pd.to_pickle((c, adj, dates, u), cache)
    c['elig'] = ~c.cyc & ~c.app & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4)
    nm = u.drop_duplicates('ticker').set_index('ticker')
    col = 'name' if 'name' in nm else ('title' if 'title' in nm else None)
    c['nome'] = c.ticker.map(nm[col]) if col else c.ticker; c['base'] = base
    return c, adj, dates


def brasil(fx):
    D = P / 'brasil' / 'data'
    u = pd.read_csv(D / 'universe.csv'); idx = u.set_index('yf')
    fund = pd.read_csv(D / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
    raw = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    cov = raw.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    c = sem2021.frozen(raw, idx, fund, start)
    c['elig'] = c.ok & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4) & c.cat.notna()
    f = fx.reindex(c.date, method='ffill').values
    c['mcap'] = c.mcap / f; c['ret_brl'] = c.ret; c['ret'] = c.ret - BR_ADJ
    c['nome'] = c.ticker.map(idx.Nome_Empresarial).astype(str).str.title(); c['base'] = 'Brasil'
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    adj = adj.div(fx.reindex(adj.index, method='ffill'), axis=0)
    return c, adj


def top20(el, adj, dates):
    ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in el.groupby('date')])
    nav = run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in ch.groupby('date')}, adj, dates)
    return nav, ch


def main():
    import yfinance as yf
    ext = yf.download('BRL=X ACWI SPY', start='2010-01-01', progress=False, auto_adjust=True)['Close']
    ext.index = pd.to_datetime(ext.index).tz_localize(None); fx = ext['BRL=X'].ffill()
    sp, adj_sp, d_sp = us_sp(); print('S&P ok', flush=True)
    ms, adj_ms, d_ms = generic(backtest_ms, 'Médias e pequenas EUA'); print('mid/small ok', flush=True)
    fp, adj_fp, _ = generic(backtest_fpi, 'Estrangeiras nos EUA'); print('estrangeiras ok', flush=True)
    br, adj_br = brasil(fx); print('Brasil ok', flush=True)
    # datas: as do S&P (trimestrais); as outras bases entram na data trimestral mais proxima anterior
    dates = [d for d in d_sp if d >= max(min(d_ms), min(br.date))]
    def align(c):
        m = pd.Series(sorted(dates)); c = c.copy()
        c['date'] = c.date.map(lambda x: m[m <= x + pd.Timedelta(days=7)].max() if (m <= x + pd.Timedelta(days=7)).any() else pd.NaT)
        return c.dropna(subset=['date']).sort_values('date').drop_duplicates(['date', 'ticker'], keep='last')
    parts = [align(x[x.date >= dates[0] - pd.Timedelta(days=7)])[COLS] for x in (sp, ms, fp, br)]
    allc = pd.concat(parts, ignore_index=True); allc = allc[allc.date.isin(dates)]
    adj = pd.concat([adj_sp, adj_ms, adj_fp, adj_br], axis=1); adj = adj.loc[:, ~adj.columns.duplicated()].sort_index().ffill(limit=5)
    el = allc[allc.elig.fillna(False).astype(bool) & allc.ret.notna() & allc.mcap.notna()].copy()
    # mesma empresa em duas bases (ADR x local): fica a de maior valor de mercado
    el['firm'] = el.nome.str.lower().str.replace(r'[^a-z0-9]', '', regex=True).str[:12]
    el = el.sort_values('mcap', ascending=False).drop_duplicates(['date', 'firm'])
    navs, n, ch_all = {}, {}, None
    nav, ch = top20(el, adj, dates); navs['MUNDO — Top 20 (regra congelada)'] = nav; n['MUNDO — Top 20 (regra congelada)'] = ch.groupby('date').size().mean(); ch_all = ch
    el2 = el.copy(); el2.loc[el2.base == 'Brasil', 'ret'] += BR_ADJ
    nav2, _ = top20(el2, adj, dates); navs['Mundo sem o ajuste do Brasil (sensibilidade)'] = nav2; n['Mundo sem o ajuste do Brasil (sensibilidade)'] = 20
    for b in el.base.unique():
        nb, cb = top20(el[el.base == b], adj, dates); navs[f'Top 20 só {b}'] = nb; n[f'Top 20 só {b}'] = cb.groupby('date').size().mean()
    navs['Todas as elegíveis do mundo (peso igual)'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in el.groupby('date')}, adj, dates)
    n['Todas as elegíveis do mundo (peso igual)'] = el.groupby('date').size().mean()
    for t, lab in (('ACWI', 'Mundo — MSCI ACWI'), ('SPY', 'S&P 500 (SPY)')):
        s = ext[t].loc[dates[0]:dates[-1]].dropna(); navs[lab] = s / s.iloc[0]
    # comparativos obrigatorios (EUA), no mesmo periodo
    bnav, bn, _, _ = bm.load_benchmarks()
    for k in bm.ORDER:
        if k in bnav and k not in ('S&P 500',):
            s = bnav[k].loc[dates[0]:]; navs[f'EUA: {k}'] = s / s.iloc[0]; n[f'EUA: {k}'] = bn.get(k, np.nan)
    W = navs['Mundo — MSCI ACWI']; MW = W.resample('ME').last(); SW = stats(W)['CAGR']
    def win(nav, y):
        M = nav.resample('ME').last(); a = M / M.shift(12 * y); b = (MW / MW.shift(12 * y)).reindex(a.index); k = a.notna() & b.notna()
        return (a[k] > b[k]).mean() if k.any() else np.nan
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    pp = lambda v: '—' if pd.isna(v) else f'{v * 100:+.1f}'.replace('.', ',')
    out = ['# Teste "mundo": a regra congelada escolhendo entre todas as bases (pré-registrado em 2026-11-12)\n',
           '> ⚠️ **O ROIC pode estar errado.** Ele decide quem é elegível (≥ 12%) e entra no P/E justo, logo no retorno esperado e na ordem. '
           'No Brasil é o ROIC clássico; nas estrangeiras, parte é IFRS e não foi conferida.\n',
           f'Período {pd.Timestamp(dates[0]):%m/%Y} a {pd.Timestamp(dates[-1]):%m/%Y}, em dólares, trimestral, sem custos nem impostos. '
           'Bases: S&P 500 point-in-time, médias e pequenas dos EUA (≥ US$ 1 bi), estrangeiras listadas nos EUA e Brasil (convertido pelo câmbio). '
           f'Retorno esperado do Brasil − 3,5 p.p. Elegíveis por data (média): {el.groupby("date").size().mean():.0f}.\n',
           '| Carteira | Ações (média) | Retorno anual | vs ACWI | Pior queda | Janelas 3a > ACWI | Janelas 5a > ACWI |', '|---|---|---|---|---|---|---|']
    for k, nav in navs.items():
        s = stats(nav)
        out.append(f"| {k} | {'—' if pd.isna(n.get(k, np.nan)) else f'{n[k]:.0f}'} | **{pc(s['CAGR'])}** | {pp(s['CAGR'] - SW)} | {pc(s['MaxDD'])} | {win(nav, 3):.0%} | {win(nav, 5):.0%} |")
    sh = ch_all.base.value_counts(normalize=True)
    out += ['', '**De onde vieram as escolhas (% das posições):** ' + ', '.join(f'{k} {v:.0%}' for k, v in sh.items())]
    yr = ch_all.assign(y=ch_all.date.dt.year).groupby(['y', 'base']).size().unstack(fill_value=0)
    out += ['', '| Ano | ' + ' | '.join(yr.columns) + ' |', '|---|' + '---|' * len(yr.columns)]
    out += [f'| {y} | ' + ' | '.join(f'{v / r.sum():.0%}' for v in r) + ' |' for y, r in yr.iterrows()]
    last = ch_all[ch_all.date == ch_all.date.max()].copy()
    last['w'] = top_n.cap(pd.Series(np.sqrt(last.mcap.values), index=last.index), .10).values
    out += ['', f'## Top 20 do mundo hoje ({pd.Timestamp(last.date.max()):%m/%Y})\n', '| # | Ação | Empresa | Base | Peso | Retorno esperado | ROIC | Crescimento | P/L |', '|---|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(last.itertuples(), 1):
        out.append(f'| {i} | {r.ticker.replace(".SA", "")} | {str(r.nome)[:40]} | {r.base} | {pc(r.w)} | {r.ret:.0%} | {r.roic:.0%} | {r.growth:.0%} | {r.pe:.0f} |')
    (ROOT / 'resultado.md').write_text('\n'.join(out)); print('\n'.join(out))
    last.to_csv(ROOT / 'top20_hoje.csv', index=False)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=140)
    pal = ['#1f6feb', '#54aeff', '#2da44e', '#8250df', '#bf8700', '#e8590c', '#57606a', '#000000', '#cf222e', '#0a7ea4', '#953800', '#6e40c9', '#8c959f', '#d4a72c', '#1a7f37', '#a40e26', '#4d2d00']
    for (k, nav), col in zip(navs.items(), pal):
        ls = '--' if k in ('Mundo — MSCI ACWI', 'S&P 500 (SPY)') else (':' if k.startswith('EUA:') else '-')
        ax.plot(nav.index, (nav - 1) * 100, color=col, ls=ls, lw=2.8 if k.startswith('MUNDO') else 1.2, label=f'{k} ({pc(stats(nav)["CAGR"])} a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=6.5, loc='upper left', ncol=2)
    ax.set_title('Teste mundo: regra congelada sobre todas as bases × ACWI, S&P e comparativos — retorno total acumulado em dólares', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'resultado.png'); plt.close(fig)


if __name__ == '__main__':
    main()
