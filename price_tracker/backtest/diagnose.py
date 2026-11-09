"""Diagnostico: por que Good Companies, Great Returns (GCGR) superou Opportunity of Lifetime (OoL)?
Uso: python3 backtest/diagnose.py [corte_zgrowth]   (padrao 2.93)
Saida: backtest/diagnose_<corte>.md"""
import sys, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent))
import engine  # noqa: E402

D = ROOT / 'data'
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
FLAW = {0: 'Growth médio (6–15%)', 1: 'Growth instável (zGrowth)', 2: 'ROIC médio (10–20%)', 3: 'ROIC instável (zROIC)'}
pct = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
nm = lambda x, n=1: '—' if pd.isna(x) else f'{x:.{n}f}'.replace('.', ',')


def main(cut=2.93):
    col = 'cat_zg2.93' if cut == 2.93 else 'cat_zg0.9'
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').set_index('ticker')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = cls.groupby('date')[col].apply(lambda s: s.notna().sum())
    start = cov[cov >= 0.4 * len(u)].index.min()
    dates = sorted(d for d in cls.date.unique() if d >= start)
    cls = cls[cls.date.isin(dates)].copy()

    # codigo de cada acao (para saber o "defeito" de quem esta em GCGR)
    saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
    cls['code'] = cls.apply(engine.code, axis=1)
    engine.TH['zGrowth'] = saved
    ref = 'HOGNG'
    cls['flaw'] = cls.code.map(lambda c: '; '.join(FLAW[i] for i in range(4) if c and c[i] != ref[i]) if isinstance(c, str) else None)

    # retorno de cada acao em cada trimestre (fechamento d -> fechamento do proximo d)
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill()
    fwd = px.shift(-1) / px - 1
    cls['r'] = [fwd.at[d, t] if t in fwd.columns else np.nan for d, t in zip(cls.date, cls.ticker)]
    back = adj.reindex(pd.DatetimeIndex(dates) - pd.Timedelta(days=365), method='ffill')
    back.index = pd.DatetimeIndex(dates)
    cls['mom12'] = [px.at[d, t] / back.at[d, t] - 1 if t in px.columns else np.nan for d, t in zip(cls.date, cls.ticker)]
    cls['pe'] = cls.price / cls.eps.where(cls.eps > 0)
    # crescimento do EPS realizado no ano seguinte (EPS do ultimo exercicio conhecido ~4 trimestres depois)
    e = cls.pivot_table(index='date', columns='ticker', values='eps')
    e_next = e.shift(-4)
    cls['eps_next'] = [e_next.at[d, t] / e.at[d, t] - 1 if e.at[d, t] and e.at[d, t] > 0 else np.nan for d, t in zip(cls.date, cls.ticker)]
    cls['sector'] = cls.ticker.map(u.sector)
    cls = cls[cls.date < dates[-1]]  # ultimo rebalanceamento ainda nao tem retorno
    o, g = cls[cls[col] == OOL], cls[cls[col] == GCGR]

    out = [f'# Diagnóstico: Good Companies, Great Returns × Opportunity of Lifetime (corte zGrowth {cut})\n',
           '> ⚠️ **ROIC:** dois dos quatro defeitos que separam as classes são de ROIC; com outra definição de ROIC a fronteira muda.\n']

    # 1. tamanho
    no, ng = o.groupby('date').size(), g.groupby('date').size()
    out += ['## 1. Tamanho das carteiras\n', '| | Opportunity of Lifetime | Good Companies, Great Returns |', '|---|---|---|',
            f'| Ações por trimestre (média) | {nm(no.mean(), 0)} | {nm(ng.mean(), 0)} |',
            f'| Mínimo / máximo | {no.min()} / {no.max()} | {ng.min()} / {ng.max()} |',
            f'| Ações distintas no período | {o.ticker.nunique()} | {g.ticker.nunique()} |', '']

    # 2. atribuicao por defeito
    qo = o.groupby('date').r.mean()
    gq = g.groupby(['date', 'flaw']).r.agg(['mean', 'size']).reset_index()
    tot = g.groupby('date').size()
    gq['share'] = gq['size'] / gq.date.map(tot)
    gq['vs_ool'] = gq['mean'] - gq.date.map(qo)
    gq['contrib'] = gq.share * gq.vs_ool
    rows = []
    for f, x in gq.groupby('flaw'):
        nav = (1 + x.set_index('date')['mean']).prod()
        yrs = len(x) / 4
        rows.append((f, x['size'].mean(), x.share.mean(), (x['mean'].mean()) * 4, x.vs_ool.mean() * 4,
                     x.contrib.sum() / (len(dates) - 1) * 4, len(x)))
    rows.sort(key=lambda r: -r[5])
    gap = (g.groupby('date').r.mean() - qo).mean() * 4
    out += ['## 2. De onde vem a diferença: o "defeito" de cada ação de Good Companies, Great Returns\n',
            'Good Companies, Great Returns = Opportunity of Lifetime com exatamente um defeito. Atribuição (retornos trimestrais, média aritmética anualizada):\n',
            '| Defeito | Ações (média) | % da carteira | Retorno médio a.a. | vs Opportunity of Lifetime | Contribuição para a diferença | Trimestres |',
            '|---|---|---|---|---|---|---|']
    for f, n, sh, ret, vs, ctb, nq in rows:
        out.append(f'| {f} | {nm(n)} | {pc(sh)} | {pc(ret)} | {pct(vs)} | **{pct(ctb)}** | {nq} |')
    out += [f'| **Total (GCGR − OoL)** | | | | | **{pct(gap)}** | |', '']

    # 3. ano a ano
    yo = o.groupby(o.date.dt.year).r.mean()
    yr = pd.DataFrame({'OoL': (1 + o.groupby('date').r.mean()).groupby(lambda d: d.year).prod() - 1,
                       'GCGR': (1 + g.groupby('date').r.mean()).groupby(lambda d: d.year).prod() - 1})
    yr['dif'] = yr.GCGR - yr.OoL
    out += ['## 3. Ano a ano (retorno das carteiras, ano do rebalanceamento)\n', '| Ano | Opportunity of Lifetime | Good Companies, Great Returns | Diferença |', '|---|---|---|---|']
    out += [f'| {y} | {pc(r.OoL)} | {pc(r.GCGR)} | {pct(r.dif)} |' for y, r in yr.iterrows()]
    out += ['']

    # 4. caracteristicas na compra
    def med(x, c): return x.groupby('date')[c].median().median()
    chars = [('Growth histórico (mediana 5 anos)', 'growth', pc), ('zGrowth', 'zgrowth', nm), ('ROIC', 'roic', pc), ('zROIC', 'zroic', nm),
             ('Retorno esperado', 'ret', pc), ('P/L (preço ÷ EPS do último ano)', 'pe', nm), ('P/E justo', 'fair_pe', nm),
             ('Dividend yield', 'dy', pc), ('Retorno da ação nos 12 meses anteriores', 'mom12', pc),
             ('**Crescimento do EPS no ano seguinte (realizado)**', 'eps_next', pc), ('Retorno no trimestre seguinte', 'r', pc)]
    out += ['## 4. Perfil das empresas no momento da compra (mediana)\n', '| Característica | Opportunity of Lifetime | Good Companies, Great Returns |', '|---|---|---|']
    out += [f'| {n} | {f(med(o, c))} | {f(med(g, c))} |' for n, c, f in chars]
    out += ['']

    # 5. setores
    so = o.groupby('sector').size() / len(o); sg = g.groupby('sector').size() / len(g)
    s = pd.DataFrame({'OoL': so, 'GCGR': sg}).fillna(0).sort_values('OoL', ascending=False)
    ro = o.groupby('sector').r.mean() * 4; rg = g.groupby('sector').r.mean() * 4
    out += ['## 5. Setores (peso médio e retorno médio a.a. das ações do setor dentro da carteira)\n',
            '| Setor | Peso OoL | Retorno OoL | Peso GCGR | Retorno GCGR |', '|---|---|---|---|---|']
    out += [f'| {i} | {pc(r.OoL)} | {pc(ro.get(i))} | {pc(r.GCGR)} | {pc(rg.get(i))} |' for i, r in s.iterrows() if max(r.OoL, r.GCGR) >= 0.02]
    out += ['']

    # 6. maiores contribuicoes
    def contrib(x):
        n = x.groupby('date').ticker.transform('size')
        c = (x.r / n).groupby(x.ticker).sum() / (len(dates) - 1) * 4
        q = x.groupby('ticker').size()
        return pd.DataFrame({'contrib': c, 'trim': q}).sort_values('contrib', ascending=False)
    co, cg = contrib(o), contrib(g)
    out += ['## 6. Maiores contribuições (pontos de retorno aritmético a.a. que cada ação trouxe para a carteira)\n',
            '| # | OoL | contribuição (trim.) | GCGR | contribuição (trim.) |', '|---|---|---|---|---|']
    for i in range(10):
        a, b = co.iloc[i], cg.iloc[i]
        out.append(f'| {i + 1} | {co.index[i]} | {pct(a.contrib)} ({int(a.trim)}) | {cg.index[i]} | {pct(b.contrib)} ({int(b.trim)}) |')
    out += [f'| | **Top 10 / total** | {pc(co.contrib.head(10).sum() / co.contrib.sum())} | | {pc(cg.contrib.head(10).sum() / cg.contrib.sum())} |']
    out += [f'| | **Piores 5** | {", ".join(co.index[-5:][::-1])} | | {", ".join(cg.index[-5:][::-1])} |', '']

    # 7. migracao entre as classes
    di = {d: i for i, d in enumerate(dates)}
    lab = {(di[d], t): c for d, t, c in zip(cls.date, cls.ticker, cls[col])}
    m = cls.copy()
    m['prev'] = [lab.get((di[d] - 1, t)) for d, t in zip(m.date, m.ticker)]
    seg = {'GCGR que veio de OoL': m[(m[col] == GCGR) & (m.prev == OOL)],
           'GCGR que vai virar OoL (próximo trimestre)': None,
           'OoL que veio de GCGR': m[(m[col] == OOL) & (m.prev == GCGR)],
           'OoL "nova" (não era OoL nem GCGR)': m[(m[col] == OOL) & ~m.prev.isin([OOL, GCGR])],
           'OoL que já era OoL': m[(m[col] == OOL) & (m.prev == OOL)],
           'GCGR que já era GCGR': m[(m[col] == GCGR) & (m.prev == GCGR)]}
    m['next'] = [lab.get((di[d] + 1, t)) for d, t in zip(m.date, m.ticker)]
    seg['GCGR que vai virar OoL (próximo trimestre)'] = m[(m[col] == GCGR) & (m.next == OOL)]
    out += ['## 7. Migração entre as duas classes (retorno no trimestre seguinte à classificação)\n',
            '| Grupo | Observações | Retorno médio no trimestre (a.a.) |', '|---|---|---|']
    out += [f'| {k} | {len(v)} | {pc(v.r.mean() * 4)} |' for k, v in seg.items()]
    out += ['']

    path = ROOT / f'diagnose_{cut}.md'
    path.write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 2.93)
