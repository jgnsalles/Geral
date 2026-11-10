"""Setores excluidos pela regua de ciclicos (+ vestuario): valores da regua, desempenho medio e 5 melhores/piores empresas.
Desempenho = excesso sobre a media do universo no trimestre seguinte, anualizado. Universo point-in-time, sem zROIC, ROIC oficial corrigido.
Saida: backtest/ciclicos_setores.md. Uso: python3 backtest/ciclicos_setores.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import ciclicos as cy  # noqa: E402
from backtest import D  # noqa: E402
from validation_core import load_prices  # noqa: E402

sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
PT = {'Consumer Discretionary': 'Cons. discricionário', 'Energy': 'Energia', 'Materials': 'Materiais', 'Industrials': 'Indústria',
      'Financials': 'Financeiro', 'Communication Services': 'Comunicação', 'Health Care': 'Saúde'}

f, dates = bm.base_data()
adj = load_prices()['adj_close']
c = bm.classify_new(f)
px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
c = c[c.date < dates[-1]].copy()
uq = c[c.cat.notna()].groupby('date').rq.mean(); c['ex'] = c.rq - c.date.map(uq)
c['sub'] = c.industry.map(cy.canon)
S = pd.read_csv(D / 'ciclicos.csv').set_index('industry')
e = pd.read_csv(D / 'ciclicos_empresas.csv', index_col=0)
u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
xe = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
nm = lambda t: u.name.get(t) if t in u.index else str(xe.sec_name.get(t, t)).title()
subs = list(S[S.ciclico].sort_values('queda', ascending=False).index) + ['Apparel, Accessories & Luxury Goods', 'Footwear']
qual = c.cat.isin([bm.OOL, bm.GCGR])
out = ['# Setores excluídos: régua, desempenho e melhores/piores empresas\n',
       '> ⚠️ **ROIC:** a régua usa o histórico completo do ROIC oficial (corrigido em 2026-11-10).\n',
       '**Régua:** queda média do ROIC (média das quedas ano a ano ÷ ROIC médio) ≥ 30% **e** ≥ 2 colapsos (ROIC ≤ metade do pico dos 3 anos anteriores), '
       'mediana das empresas do subsetor. Vestuário e calçados entram por decisão do usuário, não pela régua.\n',
       '**Desempenho:** excesso sobre a média do universo no trimestre seguinte, anualizado (média por posição), 2012–2026. '
       '"Na OoL/GCGR" = só os trimestres em que a ação teria entrado na OoL ou na GCGR (é a classe Cyclicals); "No universo" = todos os trimestres '
       'em que a ação era do S&P 500. Melhores/piores = excesso médio de cada empresa nos trimestres em que teria entrado na OoL/GCGR.\n',
       '## Resumo\n',
       '| Subsetor | Macrossetor | Queda média | Colapsos | Variação total | Posições na OoL/GCGR | **Excesso na OoL/GCGR** | Mediana | No universo (todas as posições) |',
       '|---|---|---|---|---|---|---|---|---|']
det = []
for s_ in subs:
    x = c[c['sub'] == s_]; q = x[qual.loc[x.index]]
    if s_ in S.index:
        r = S.loc[s_]; reg = (pc(r.queda), f'{r.colapsos:g}'.replace('.', ','), pc(e[e.industry == s_].var_total.median()))
        if r.nivel != 'subsetor': reg = (reg[0] + '¹', reg[1] + '¹', reg[2])
    else:
        reg = ('decisão do usuário', '', pc(e[e.industry == s_].var_total.median()))
    sec = x.sector.dropna().iloc[0] if len(x) else ''
    out.append(f'| {s_} | {PT.get(sec, sec)} | {reg[0]} | {reg[1]} | {reg[2]} | {len(q)} | **{sg(q.ex.mean() * 4)}** | {sg(q.ex.median() * 4)} | {sg(x.ex.mean() * 4)} |')
    a = q.groupby('ticker').agg(n=('ex', 'size'), ex=('ex', 'mean')); a['ex'] *= 4; a = a.sort_values('ex')
    if len(a):
        fmt = lambda t, r: f"{t} ({nm(t)}, {int(r.n)} trim.) {sg(r.ex)}"
        det += [f'### {s_}\n', f'**Piores:** ' + '; '.join(fmt(t, r) for t, r in a.head(5).iterrows()), '',
                f'**Melhores:** ' + '; '.join(fmt(t, r) for t, r in a.iloc[::-1].head(5).iterrows()), '']
q_all = c[qual & c['sub'].isin(subs)]
out.append(f'| **Todos os excluídos** | | | | | {len(q_all)} | **{sg(q_all.ex.mean() * 4)}** | {sg(q_all.ex.median() * 4)} | {sg(c[c["sub"].isin(subs)].ex.mean() * 4)} |')
k = c[qual & ~c['sub'].isin(subs)]
out.append(f'| *OoL/GCGR que ficaram (comparação)* | | | | | {len(k)} | {sg(k.ex.mean() * 4)} | {sg(k.ex.median() * 4)} | |')
out += ['', '¹ Subsetor com uma empresa só: régua calculada na indústria GICS acima, junto com os vizinhos.\n', '## 5 piores e 5 melhores por subsetor\n'] + det
(ROOT / 'ciclicos_setores.md').write_text('\n'.join(out))
print('\n'.join(out))
