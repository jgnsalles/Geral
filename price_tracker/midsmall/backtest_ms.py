"""Teste fora da amostra da estrategia candidata congelada (2026-11-10) nas MEDIAS E PEQUENAS dos EUA (fora do S&P 500 na data, valor de mercado >= US$ 1 bi).
Regra congelada: elegiveis ROIC >= 12%, crescimento do EPS >= 15%, P/L >= 4, sem ciclicos e vestuario; as 20 de maior retorno esperado;
peso pela raiz do valor de mercado com teto de 10%; trimestral. Mesmos parametros dos EUA (WACC 8,5%, g 7% -> 3,5%).
Mapeamento de setores (SIC da SEC, fixado antes de rodar): ver CYC_SIC e APPAREL_SIC.
Limites: so empresas que publicam o lucro por acao em dolar (sem converter moeda nem razao de ADR); lista parte de quem tem ticker hoje.
Saidas: midsmall/resultado.md, midsmall/resultado.png. Uso: python3 midsmall/backtest_ms.py"""
import sys, json, gzip, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; D = ROOT / 'data'
sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT.parent))
import backtest as bt  # noqa: E402
import validation_portfolios as vp  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402

MIN_N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
SPH = pd.read_csv(ROOT.parent / 'backtest' / 'data' / 'pit_membership' / 'sp500_hist.csv', parse_dates=['date']).set_index('date').tickers


def in_ranges(s, rs):
    return any(a <= s <= b for a, b in rs)
CYC_SIC = [(1000, 1099), (1220, 1241), (1311, 1311), (1381, 1389), (2911, 2911), (3310, 3317), (3330, 3339), (2870, 2879),
           (5311, 5311), (4512, 4512), (3751, 3751), (7990, 7999), (5122, 5122), (3944, 3944)]
APPAREL_SIC = [(2200, 2399), (3020, 3021), (3100, 3199)]


def load_pit(f):
    raw = json.load(gzip.open(f, 'rt')); out = {}
    for key, cands in raw.items():
        cs = []
        for c in cands:
            df = pd.DataFrame(c['rows'], columns=['end', 'val', 'filed']); df['end'] = pd.to_datetime(df.end); df['filed'] = pd.to_datetime(df.filed)
            cs.append((c['concept'], c['unit'], df.sort_values('filed')))
        out[key] = cs
    return out


def main():
    u = pd.read_csv(D / 'universe.csv'); u['sic'] = pd.to_numeric(u.sic, errors='coerce').fillna(0).astype(int)
    u['fin'] = u.sic.between(6000, 6499) | (u.sic.between(6700, 6799) & (u.sic != 6798))
    u['cyc'] = u.sic.map(lambda s: in_ranges(s, CYC_SIC)); u['app'] = u.sic.map(lambda s: in_ranges(s, APPAREL_SIC))
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    close, adj, vol = read('close'), read('adj_close'), read('volume')
    spl = read('splits'); divs = read('dividends').fillna(0)
    dv = (close * vol).rolling(63, min_periods=20).median()
    dates = [d for d in bt.rebalance_dates(close) if d >= pd.Timestamp('2011-06-30')]
    MEM = {}
    for d in dates:
        m = SPH[SPH.index <= d]; MEM[d] = set(m.iloc[-1].split(',')) if len(m) else set()
    rows, pits = [], {}
    usd_rep = set()
    for r in u.itertuples():
        f = D / 'pit' / f'{r.ticker}.json.gz'
        if not f.exists() or r.ticker not in close: continue
        pit = load_pit(f); pits[r.ticker] = pit
        if 'eps_diluted' not in pit: continue
        sp = spl[r.ticker].dropna() if r.ticker in spl else pd.Series(dtype=float, index=pd.DatetimeIndex([])); sp = sp[sp > 0]
        for d in dates:
            p = close.at[d, r.ticker]
            if not np.isfinite(p) or p < 5 or not (dv.at[d, r.ticker] >= 5e6): continue
            if r.ticker.replace('-', '.') in MEM[d] or r.ticker in MEM[d]: continue
            ft = bt.features(pit, d, bool(r.fin), sp)
            if ft is None: continue
            usd_rep.add(r.ticker)
            pe = p / ft['eps'] if ft['eps'] and ft['eps'] > 0 else np.nan
            if pd.notna(pe) and not 1 <= pe <= 300: continue  # LPA inconsistente com o preco (razao de ADR, moeda): fora
            ni, _ = bt.asof(pit.get('net_income', []), d); y = ft['last_fy']
            sh = ni[y][0] / ft['eps'] if y in ni and ft['eps'] and np.sign(ni[y][0]) == np.sign(ft['eps']) else np.nan
            if not (np.isfinite(sh) and p * sh >= 1e9): continue
            dvd = divs[r.ticker]; dy = dvd[(dvd.index > d - pd.Timedelta(days=730)) & (dvd.index <= d)].sum() / 2 / p
            rows.append(dict(date=d, ticker=r.ticker, fin=bool(r.fin), price=p, dy=dy, cyc=r.cyc, app=r.app, country=r.sicdesc, sh=sh, **ft))
        print(r.ticker, flush=True) if len(rows) % 2000 == 0 else None
    f = pd.DataFrame(rows)
    cnt = f.groupby('date').size(); print('classificadas por data:', cnt.iloc[::4].to_dict()); start = cnt[cnt >= MIN_N].index.min()
    f = f[f.date >= start]; dates = [d for d in dates if d >= start]
    c = vp.classify(f, 'sketch', 'B')
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c['sh'] = c.groupby('ticker').sh.transform(lambda s: s.ffill().bfill()); c['mcap'] = (c.price * c.sh).where(lambda s: s > 0)
    c['mcap'] = c.mcap.fillna(c.groupby('date').mcap.transform('median'))
    el = c[~c.cyc & ~c.app & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4)].copy()
    navs, nn, chosen = {}, {}, None
    for n in (20, 15, 10):
        ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(n) for _, g in el.groupby('date')])
        navs[f'Top {n} — raiz com teto'] = run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), 2 / n) for d, g in ch.groupby('date')}, adj, dates)
        navs[f'Top {n} — peso igual'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in ch.groupby('date')}, adj, dates)
        nn[f'Top {n} — raiz com teto'] = nn[f'Top {n} — peso igual'] = ch.groupby('date').size().mean()
        if n == 20: chosen = ch
    navs['Universo médias e pequenas (peso igual)'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in c.groupby('date')}, adj, dates)
    nn['Universo médias e pequenas (peso igual)'] = c.groupby('date').size().mean()
    navs['Elegíveis de qualidade (peso igual)'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in el.groupby('date')}, adj, dates)
    nn['Elegíveis de qualidade (peso igual)'] = el.groupby('date').size().mean()
    for t, lab in (('IJH', 'S&P MidCap 400 (IJH)'), ('IJR', 'S&P SmallCap 600 (IJR)'), ('IWM', 'Russell 2000 (IWM)'), ('SPY', 'S&P 500 (SPY)')):
        s = adj[t].loc[dates[0]:dates[-1]].dropna(); navs[lab] = s / s.iloc[0]
    U = navs['Universo médias e pequenas (peso igual)']; MU = U.resample('ME').last()
    def win(nav, y):
        M = nav.resample('ME').last(); a = M / M.shift(12 * y); b = (MU / MU.shift(12 * y)).reindex(a.index); k = a.notna() & b.notna()
        return (a[k] > b[k]).mean() if k.any() else np.nan
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    pp = lambda v: '—' if pd.isna(v) else f'{v * 100:+.1f}'.replace('.', ',')
    SU = stats(U)['CAGR']
    out = ['# Teste fora da amostra: médias e pequenas dos EUA (fora do S&P 500 na data, valor de mercado ≥ US$ 1 bi)\n',
           '> ⚠️ **O ROIC pode estar errado** (patrimônio negativo e ROIC > 100% em empresas leves em ativos ainda em aberto).\n',
           f'Período {pd.Timestamp(dates[0]):%m/%Y} a {pd.Timestamp(dates[-1]):%m/%Y}, em dólares, trimestral, sem custos nem impostos. Regra congelada, sem ajuste. '
           f'Universo: {u.shape[0]} empresas americanas na Nasdaq/NYSE; entram as fora do S&P 500 na data, com valor de mercado ≥ US$ 1 bi, '
           f'preço ≥ US$ 5 e giro mediano ≥ US$ 5 milhões/dia ({len(usd_rep)} empresas com dados). Classificadas por data (mediana): {int(c.groupby("date").size().median())}; '
           f'elegíveis de qualidade (mediana): {int(el.groupby("date").size().median())}.\n',
           '**Limitação:** a lista parte de quem tem ticker hoje (empresas que quebraram ou foram compradas faltam, o que favorece o resultado).\n',
           '| Carteira | Ações (média) | Retorno anual | vs universo | Pior queda | Janelas 3a > universo | Janelas 5a > universo |', '|---|---|---|---|---|---|---|']
    for k, nav in navs.items():
        s = stats(nav)
        out.append(f"| {k} | {'—' if k not in nn else f'{nn[k]:.0f}'} | **{pc(s['CAGR'])}** | {pp(s['CAGR'] - SU)} | {pc(s['MaxDD'])} | {win(nav, 3):.0%} | {win(nav, 5):.0%} |")
    ch = chosen
    out += ['', f'**Setores das escolhas da Top 20 (% das posições, SIC):** ' +
            ', '.join(f'{k} {v:.0%}' for k, v in ch.country.value_counts(normalize=True).head(10).items()),
            '', f'**Top 20 de hoje ({ch.date.max():%m/%Y}):** ' + ', '.join(ch[ch.date == ch.date.max()].ticker)]
    (ROOT / 'resultado.md').write_text('\n'.join(out)); print('\n'.join(out))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    sty = {'Top 20 — raiz com teto': ('#1f6feb', '-', 2.6), 'Top 20 — peso igual': ('#54aeff', '-', 1.6), 'Universo médias e pequenas (peso igual)': ('#57606a', '--', 1.8),
           'Elegíveis de qualidade (peso igual)': ('#2da44e', ':', 1.6), 'S&P MidCap 400 (IJH)': ('#bf8700', '--', 1.4),
           'S&P SmallCap 600 (IJR)': ('#e8590c', '--', 1.4), 'Russell 2000 (IWM)': ('#cf222e', ':', 1.4), 'S&P 500 (SPY)': ('#000000', '--', 1.6)}
    for k, (col, ls, lw) in sty.items():
        s = navs[k]; ax.plot(s.index, (s - 1) * 100, color=col, ls=ls, lw=lw, label=f'{k} (' + pc(stats(s)['CAGR']) + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Médias e pequenas dos EUA: estratégia candidata congelada × universo e ETFs — retorno total acumulado', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'resultado.png'); plt.close(fig)


if __name__ == '__main__':
    main()
