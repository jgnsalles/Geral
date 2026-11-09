"""Analise setorial de Opportunity of Lifetime e Good Companies, Great Returns (cenario-base).
(1) setores nos 50 piores / todos / 50 melhores episodios; (2) retorno por setor; (3) carteira excluindo cada setor
e o grupo de industrias ciclicas, no periodo todo e nos dois subperiodos.
Uso: python3 backtest/sectors.py [corte]   (padrao 2.93; requer worst_cases.py rodado antes)"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
PT = {'Information Technology': 'Tecnologia', 'Consumer Discretionary': 'Consumo discricionário', 'Industrials': 'Industrial',
      'Financials': 'Financeiro', 'Health Care': 'Saúde', 'Communication Services': 'Comunicação', 'Consumer Staples': 'Consumo básico',
      'Materials': 'Materiais', 'Energy': 'Energia', 'Real Estate': 'Imobiliário', 'Utilities': 'Utilidades'}
CYCLICAL = {'Semiconductors', 'Semiconductor Materials & Equipment', 'Technology Hardware, Storage & Peripherals', 'Hardware, Equipment & Parts',
            'Electronic Components', 'Commodity Chemicals', 'Specialty Chemicals', 'Fertilizers & Agricultural Chemicals', 'Steel', 'Copper',
            'Construction Materials', 'Building Products', 'Homebuilding', 'Residential Construction', 'Air Freight & Logistics',
            'Cargo Ground Transportation', 'Passenger Airlines', 'Automobile Manufacturers', 'Auto - Manufacturers', 'Automotive Parts & Equipment',
            'Construction Machinery & Heavy Transportation Equipment', 'Agricultural & Farm Machinery', 'Oil & Gas Exploration & Production',
            'Oil & Gas Equipment & Services', 'Oil & Gas Refining & Marketing', 'Integrated Oil & Gas', 'Casinos & Gaming',
            'Hotels, Resorts & Cruise Lines', 'Computer & Electronics Retail', 'Homefurnishing Retail', 'Leisure Products'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')


def cagr_between(nav, a, b):
    s = nav.loc[a:b].dropna(); yrs = (s.index[-1] - s.index[0]).days / 365.25
    return (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1


def main(cut='2.93'):
    col = f'cat_zg{cut}'
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)].copy()
    cls['sector'] = cls.ticker.map(u.sector).map(PT)
    cls['cyc'] = cls.ticker.map(u.industry).isin(CYCLICAL)
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill(); fwd = px.shift(-1) / px - 1
    cls['rq'] = [fwd.at[d, t] for d, t in zip(cls.date, cls.ticker)]
    out = [f'# Análise setorial (corte zGrowth {cut.replace(".", ",")})\n',
           '> ⚠️ **ROIC:** quem entra em cada classe depende do ROIC; no setor financeiro a régua é o ROE.\n',
           'Indústrias cíclicas (grupo testado): ' + ', '.join(sorted(CYCLICAL)) + '.\n']
    for cat in (OOL, GCGR):
        tag = cat.split()[0].lower()
        ep = pd.read_csv(D / f'episodes_{tag}_{cut}.csv')
        ep['sector'] = ep.sector.map(PT); ep['cyc'] = ep.ticker.map(u.industry).isin(CYCLICAL)
        ep = ep.sort_values('contrib')
        w, b = ep.head(50), ep.tail(50)
        x = cls[cls[col] == cat]
        hold = {d: g.ticker.tolist() for d, g in x.groupby('date')}
        base = run_portfolio(hold, adj, dates)[0]
        bc, b1, b2 = stats(base)['CAGR'], cagr_between(base, '2012', '2019'), cagr_between(base, '2020', '2026')
        out += [f'## {cat}\n', f'Carteira completa: {pc(bc)} a.a. (2012–2019: {pc(b1)}; 2020–2026: {pc(b2)})\n',
                '| Setor | % dos 50 piores | % de todos | % dos 50 melhores | Retorno médio da posição (a.a.) | % posições negativas | Carteira sem o setor | Δ total | Δ 2012–19 | Δ 2020–26 |',
                '|---|---|---|---|---|---|---|---|---|---|']
        rows = []
        groups = [(s, x.sector == s, ep.sector == s) for s in ep.sector.value_counts().index] + [('**Cíclicos (grupo)**', x.cyc, ep.cyc)]
        for s, mx, me in groups:
            sw, sa, sb = me.loc[w.index].mean(), me.mean(), me.loc[b.index].mean()
            r = x[mx].rq
            nav = run_portfolio({d: [t for t in v if t not in set(x[mx & (x.date == d)].ticker)] for d, v in hold.items()}, adj, dates)[0]
            c, c1, c2 = stats(nav)['CAGR'], cagr_between(nav, '2012', '2019'), cagr_between(nav, '2020', '2026')
            rows.append((s, sw, sa, sb, r.mean() * 4, (r < 0).mean(), c, c - bc, c1 - b1, c2 - b2))
        for s, sw, sa, sb, rm, neg, c, d, d1, d2 in rows:
            out.append(f'| {s} | {pc(sw)} | {pc(sa)} | {pc(sb)} | {pc(rm)} | {pc(neg)} | {pc(c)} | **{sg(d)}** | {sg(d1)} | {sg(d2)} |')
        out.append('')
    (ROOT / f'sectors_{cut}.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '2.93')
