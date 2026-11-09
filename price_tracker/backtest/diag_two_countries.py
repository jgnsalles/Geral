"""Opportunity of Lifetime x Good Companies, Great Returns em EUA e Brasil.
(1) Desempenho relativo de cada "defeito" que tirou a empresa de OoL e a colocou em GCGR.
(2) Perfil na entrada dos 20% piores, todos e 20% melhores episodios de cada classe.
Uso: python3 backtest/diag_two_countries.py"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import engine  # noqa: E402
from backtest import D as DUS  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
FLAW = {0: 'Growth médio', 1: 'Growth instável (zGrowth)', 2: 'ROIC médio', 3: 'ROIC instável (zROIC)'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')
METRICS = [('Growth (mediana 5 anos)', 'growth', pc), ('zGrowth', 'zgrowth', nm), ('Último crescimento anual', 'g_last', pc),
           ('ROIC', 'roic', pc), ('zROIC', 'zroic', nm), ('Retorno esperado', 'ret', pc), ('P/L de entrada', 'pe', nm),
           ('P/E justo', 'fair_pe', nm), ('P/L ÷ P/E justo', 'pe_rel', nm), ('Dividend yield', 'dy', pc),
           ('Retorno 12m antes', 'mom12', pc), ('Trimestres na classe', 'quarters', nm), ('Retorno do episódio', 'ep_ret', pc)]


def us():
    cls = pd.read_csv(DUS / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(DUS / 'universe.csv')
    adj = pd.read_csv(DUS / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    cls = cls[cls.date >= start].copy()
    cls['cat'] = cls['cat_zg2.93']
    saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = 2.93
    cls['code'] = cls.apply(engine.code, axis=1); engine.TH['zGrowth'] = saved
    return cls, adj


def br():
    import run_v3 as v3
    x, close = v3.prepare()
    c = v3.classify(x, 2.93)
    cov = c.groupby('date').cat.apply(lambda s: s.notna().sum())
    start = cov[cov >= v3.MIN_N].index.min()
    adj = pd.read_csv(v3.D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    return c[c.date >= start].copy(), adj


def enrich(c, adj):
    dates = sorted(c.date.unique())
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill()
    fwd = px.shift(-1) / px - 1
    b1 = adj.reindex(pd.DatetimeIndex(dates) - pd.DateOffset(years=1), method='ffill').set_axis(pd.DatetimeIndex(dates))
    c = c[c.date < dates[-1]].copy()
    c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    c['mom12'] = [px.at[d, t] / b1.at[d, t] - 1 for d, t in zip(c.date, c.ticker)]
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c['pe_rel'] = c.pe / c.fair_pe.where(c.fair_pe > 0)
    c['i'] = c.date.map({d: i for i, d in enumerate(dates)})
    ev = {(i, t): v for i, t, v in zip(c.i, c.ticker, c.eps)}
    prev = [ev.get((i - 4, t)) for i, t in zip(c.i, c.ticker)]
    c['g_last'] = [v / p - 1 if p is not None and pd.notna(p) and p > 0 and pd.notna(v) else np.nan for v, p in zip(c.eps, prev)]
    return c


def flaw_table(c, country):
    univ = c[c.cat.notna()].groupby('date').rq.mean()
    o = c[c.cat == OOL].groupby('date').rq.mean()
    g = c[c.cat == GCGR].copy()
    g['flaw'] = g.code.map(lambda s: next((FLAW[i] for i in range(4) if s[i] != 'HOGNG'[i]), None))
    nq = c.date.nunique()
    rows = [('**Opportunity of Lifetime (referência)**', c[c.cat == OOL].groupby('date').size().mean(), np.nan, o.mean() * 4, np.nan, np.nan,
             (o - univ.reindex(o.index)).mean() * 4)]
    tot = g.groupby('date').size()
    for f, x in g.groupby('flaw'):
        q = x.groupby('date').rq.mean()
        d = (q - o.reindex(q.index)).dropna()
        t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 and d.std() > 0 else np.nan
        share = (x.groupby('date').size() / tot).reindex(tot.index).fillna(0)
        contrib = (share * (q - o.reindex(q.index)).reindex(tot.index).fillna(0)).sum() / nq * 4
        rows.append((f, x.groupby('date').size().mean(), share.mean(), q.mean() * 4, d.mean() * 4, t, (q - univ.reindex(q.index)).mean() * 4, contrib))
    qg = g.groupby('date').rq.mean()
    out = [f'### {country}\n', '| Grupo | Ações (média) | % de GCGR | Retorno médio a.a. | vs OoL (a.a.) | t vs OoL | vs Universo EW | Contribuição para GCGR − OoL |',
           '|---|---|---|---|---|---|---|---|']
    for r in rows:
        if len(r) == 7:
            out.append(f'| {r[0]} | {nm(r[1])} | — | {pc(r[3])} | — | — | {sg(r[6])} | — |')
        else:
            out.append(f'| {r[0]} | {nm(r[1])} | {pc(r[2])} | {pc(r[3])} | {sg(r[4])} | {nm(r[5])} | {sg(r[6])} | **{sg(r[7])}** |')
    out.append(f'| **Good Companies, Great Returns (total)** | {nm(tot.mean())} | 100% | {pc(qg.mean() * 4)} | {sg((qg - o.reindex(qg.index)).mean() * 4)} | | {sg((qg - univ.reindex(qg.index)).mean() * 4)} | |\n')
    return out


def episodes(c, cat):
    x = c[c.cat == cat].sort_values(['ticker', 'date']).copy()
    x['n'] = x.groupby('date').ticker.transform('size')
    x['c'] = x.rq / x.n
    x['ep'] = (x.groupby('ticker').i.diff() != 1).cumsum()
    ep = x.groupby('ep').agg(ticker=('ticker', 'first'), quarters=('c', 'size'), contrib=('c', 'sum'),
                             ep_ret=('rq', lambda s: (1 + s.fillna(0)).prod() - 1))
    first = x.groupby('ep').first()
    for _, col, _ in METRICS:
        if col not in ('quarters', 'ep_ret'): ep[col] = first[col]
    return ep.sort_values('contrib')


def profile_table(c, country):
    out = [f'### {country}\n']
    eps = {cat: episodes(c, cat) for cat in (OOL, GCGR)}
    hdr = '| Indicador | ' + ' | '.join(f'{k} {s}' for k in ('OoL', 'GCGR') for s in ('piores 20%', 'todos', 'melhores 20%')) + ' |'
    out += [f'Episódios: OoL {len(eps[OOL])}, GCGR {len(eps[GCGR])}.\n', hdr, '|---|' + '---|' * 6]
    for name, col, f in METRICS:
        cells = []
        for cat in (OOL, GCGR):
            ep = eps[cat]; k = max(1, int(round(len(ep) * 0.2)))
            cells += [f(ep.head(k)[col].median()), f(ep[col].median()), f(ep.tail(k)[col].median())]
        out.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    out.append('')
    return out


def main():
    out = ['# Opportunity of Lifetime × Good Companies, Great Returns: EUA e Brasil\n',
           '> ⚠️ **ROIC:** dois dos quatro defeitos são de ROIC; régua de ROIC de 20%/10% nos EUA e 17%/10% no Brasil.\n',
           'EUA: cenário-base (g 7%, ROIC 20%/10%), 2012–2026. Brasil: v3 (liquidez ≥ R$ 10 mi/dia, ROIC 17%/10%, parâmetros EUA + 2,5 p.p.), 2015–2026. '
           'Corte zGrowth 2,93 nos dois. Retornos: média trimestral anualizada (aritmética).\n',
           '## 1. O que tirou a empresa de Opportunity of Lifetime: desempenho de cada defeito\n']
    data = {'EUA': enrich(*us()), 'Brasil': enrich(*br())}
    for k, c in data.items():
        out += flaw_table(c, k)
    out += ['## 2. Perfil na entrada: piores 20%, todos e melhores 20% dos episódios (medianas)\n']
    for k, c in data.items():
        out += profile_table(c, k)
    (ROOT / 'diag_two_countries.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
