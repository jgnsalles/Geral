"""Investigacao do ROIC, etapa 1 (2026-11-14). (1) Sensibilidade da Top 20 congelada a definicao do ROIC; (2) auditoria dos componentes
das acoes das carteiras de hoje (EUA); (3) casos extremos. Saida: backtest/roic_auditoria.md. Uso: python3 backtest/roic_auditoria.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats, load_pit, asof, D  # noqa: E402

pc = lambda v: '—' if v is None or pd.isna(v) else f'{v:.0%}'
pc1 = lambda v: '—' if v is None or pd.isna(v) else f'{v:.1%}'.replace('.', ',')
bi = lambda v: '—' if v is None or pd.isna(v) else f'{v / 1e9:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def top20(c, adj, dates):
    el = c[~c.excluded & (c.roic_sel >= .12) & (c.growth >= .15) & c.growth.notna() & c.roic_sel.notna()].copy()
    el['pe'] = el.price / el.eps.where(el.eps > 0); el = el[el.pe >= 4]
    el['mcap'] = top_n.mcap_us(el, el)
    ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in el.groupby('date')])
    W = {d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in ch.groupby('date')}
    return run_weighted(W, adj, dates), ch


def comps(tk, t, fin):
    """Componentes do ROIC (B) e (A) do ultimo exercicio conhecido em t."""
    pit = load_pit(tk)
    s = {k: asof(pit.get(k, []), t)[0] for k in ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income', 'ppe', 'assets_cur', 'cur_liab',
                                                'debt_cur', 'goodwill', 'intangibles')}
    ys = [y for y in s['op_income'] or s['net_income']]
    if not ys: return {}
    y = max(ys); g = lambda k, yy=y: s[k][yy][0] if s[k] and yy in s[k] else None
    oi, pt, tx = g('op_income'), g('pretax'), g('tax')
    tr = min(max(tx / pt, 0), .5) if pt and tx is not None and pt > 0 else .21
    nopat = oi * (1 - tr) if oi is not None else None
    ac, cl, ppe = g('assets_cur'), g('cur_liab'), g('ppe')
    wc = (ac - (g('cash') or 0)) - (cl - (g('debt_cur') or 0)) if ac is not None and cl is not None else None
    gwi = (g('goodwill') or 0) + (g('intangibles') or 0)
    capb = ppe + gwi + wc if ppe is not None and wc is not None else None
    eq = g('equity'); capa = eq + (g('lt_debt') or 0) - (g('cash') or 0) if eq is not None else None
    miss = [k for k in ('ppe', 'assets_cur', 'cur_liab', 'cash', 'lt_debt', 'goodwill', 'intangibles') if g(k) is None]
    return dict(fy=y, nopat=nopat, ppe=ppe, gwi=gwi, wc=wc, capb=capb, eq=eq, capa=capa, ni=g('net_income'),
                rb=nopat / capb if nopat is not None and capb and capb > 0 else None, ra=nopat / capa if nopat is not None and capa and capa > 0 else None,
                roe=g('net_income') / eq if g('net_income') is not None and eq and eq > 0 else None, miss=miss)


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    f['roic_min'] = np.fmin(f.roic, f.roic_a.where(f.roic_a.notna(), f.roic))
    V = {'Oficial (B: capital operacional + ágio e intangíveis)': f.roic, 'Clássico (A: patrimônio + dívida − caixa)': f.roic_a.fillna(f.roic),
         'Conservador (o menor de A e B)': f.roic_min, 'Sem filtro de ROIC (P/E justo segue com o B)': pd.Series(1.0, index=f.index)}
    navs, nn, picks = {}, {}, {}
    for k, sel in V.items():
        base = f.copy()
        if k.startswith('Clássico') or k.startswith('Conservador'): base['roic'] = sel  # muda tambem o P/E justo
        c = bm.classify_new(base); c['roic_sel'] = sel.values if not k.startswith('Sem') else 1.0
        if not k.startswith('Sem') and not k.startswith('Oficial'): c['roic_sel'] = c.roic
        navs[k], ch = top20(c, adj, dates); nn[k] = 20; picks[k] = ch; print(k, flush=True)
    off = picks['Oficial (B: capital operacional + ágio e intangíveis)']
    so = set(zip(off.date, off.ticker))
    out = ['# Investigação do ROIC — etapa 1: diagnóstico\n', '> ⚠️ **O ROIC pode estar errado** — é exatamente o que este arquivo investiga.\n',
           '## 1. Quanto a estratégia depende da definição do ROIC (Top 20 congelada, EUA)\n',
           '| Definição | Retorno anual | Pior queda | Posições iguais à oficial |', '|---|---|---|---|']
    for k, nav in navs.items():
        st = stats(nav); sk = set(zip(picks[k].date, picks[k].ticker))
        out.append(f"| {k} | **{pc1(st['CAGR'])}** | {pc1(st['MaxDD'])} | {len(sk & so) / len(so):.0%} |")
    s = adj['SPY'].loc[dates[0]:dates[-1]].dropna(); out.append(f"| S&P 500 | {pc1(stats(s / s.iloc[0])['CAGR'])} | {pc1(stats(s / s.iloc[0])['MaxDD'])} | — |")
    # 2. distribuicao e casos extremos na ultima data
    c = bm.classify_new(f); last = c[c.date == c.date.max()]
    op = last[~last.fin]
    out += ['', f'## 2. Distribuição do ROIC oficial hoje ({last.date.max():%m/%Y}, S&P 500, empresas operacionais: {len(op)})\n',
            f"Mediana {pc(op.roic.median())}; acima de 100%: {(op.roic > 1).sum()}; negativo: {(op.roic < 0).sum()}; sem valor: {op.roic.isna().sum()}; "
            f"oficial e clássico em lados diferentes do corte de 12%: {(((op.roic >= .12) != (op.roic_a >= .12)) & op.roic_a.notna()).sum()} empresas; "
            f"usaram o clássico por falta de dado do oficial em algum ano: {(op.n_ic_fallback > 0).sum()}.\n"]
    # 3. auditoria das carteiras de hoje
    h = pd.read_csv(ROOT / 'hoje_classes.csv'); h = h[h.pais == 'EUA']
    tks = list(dict.fromkeys(h.ticker)) + [t for t in op[op.roic > 1].ticker if t not in set(h.ticker)]
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    rows = []
    for t in tks:
        r = last[last.ticker == t]
        if r.empty: continue
        r = r.iloc[0]; x = comps(t, last.date.max(), bool(r.fin))
        if not x: continue
        why = []
        if r.fin: why.append('financeira: ROE')
        else:
            if x['eq'] is not None and x['eq'] <= 0: why.append('patrimônio negativo')
            if x['wc'] is not None and x['capb'] and x['wc'] < -0.3 * x['capb']: why.append('capital de giro muito negativo')
            if x['capb'] is not None and x['ppe'] is not None and x['capb'] < 0.5 * (x['ppe'] + x['gwi']): why.append('capital encolhido pelo giro')
            if r.roic > 1: why.append('ROIC > 100%')
            if x['miss']: why.append('falta: ' + ', '.join(x['miss']))
            if pd.notna(r.roic_a) and abs(r.roic - r.roic_a) > .15: why.append('A e B muito diferentes')
        rows.append(dict(t=t, nm=str(u.name.get(t, t))[:28], ind=r.industry, roic=r.roic, ra=r.roic_a, fy=x['fy'], nopat=x['nopat'], ppe=x['ppe'], gwi=x['gwi'],
                         wc=x['wc'], capb=x['capb'], eq=x['eq'], rb=x['rb'] if not r.fin else x['roe'], why='; '.join(why) or 'ok', inport=t in set(h.ticker)))
    R = pd.DataFrame(rows)
    out += ['## 3. Auditoria das ações das carteiras de hoje e dos ROICs acima de 100% (EUA)\n',
            'Valores em US$ bilhões do último exercício. ROIC do modelo = média (últimos 3 anos, todos os 6 anos) do ROIC anual; "último ano" = só o exercício mais recente.\n',
            '| Ação | Empresa | Na carteira? | ROIC do modelo | Clássico (A) | Último ano | Lucro operacional após IR | Imobilizado | Ágio + intangíveis | Capital de giro | Capital (B) | Patrimônio | Diagnóstico |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in R.sort_values('roic', ascending=False).itertuples():
        out.append(f"| {r.t} | {r.nm} | {'sim' if r.inport else 'não'} | **{pc(r.roic)}** | {pc(r.ra)} | {pc(r.rb)} | {bi(r.nopat)} | {bi(r.ppe)} | {bi(r.gwi)} | {bi(r.wc)} | {bi(r.capb)} | {bi(r.eq)} | {r.why} |")
    flag = R[R.why != 'ok']
    out += ['', '**Resumo dos diagnósticos (carteiras de hoje):** ' + ', '.join(f'{k}: {v}' for k, v in
             pd.Series([w for s_ in R[R.inport].why for w in s_.split('; ')]).value_counts().items())]
    (ROOT / 'roic_auditoria.md').write_text('\n'.join(out)); print('\n'.join(out)); R.to_csv(ROOT / 'roic_auditoria.csv', index=False)


if __name__ == '__main__':
    main()
