"""Erros da Top 20 por retorno esperado (EUA): passagens pela carteira que perderam dinheiro ou do S&P, e se o ranking errou mais no topo.
Saida: backtest/top20_erros.md. Uso: python3 backtest/top20_erros.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm, top_n  # noqa: E402
from backtest import D  # noqa: E402

f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']; c = bm.classify_new(f)
el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & c.roic.notna() & c.growth.notna()].copy(); el['mcap'] = top_n.mcap_us(c, el)
parts = []
for d, g in el.groupby('date'):
    g = g.sort_values(['ret', 'roic'], ascending=False).head(20).copy(); g['rank'] = range(1, len(g) + 1); parts.append(g)
ch = pd.concat(parts)
px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
ch = ch[ch.date < dates[-1]].copy()
ch['r'] = [fwd.at[d, t] for d, t in zip(ch.date, ch.ticker)]; ch['spy'] = ch.date.map(fwd['SPY'])
ch['pe'] = ch.price / ch.eps.where(ch.eps > 0)
u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker'); xe = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
nm = lambda t: u.name.get(t) if t in u.index else str(xe.sec_name.get(t, t)).title()
di = {d: i for i, d in enumerate(dates)}
st = []
for t, g in ch.sort_values('date').groupby('ticker'):
    k = g.date.map(di); grp = (k.diff() != 1).cumsum()
    for _, s in g.groupby(grp):
        r0 = s.iloc[0]
        st.append(dict(t=t, ini=s.date.iloc[0], fim=dates[di[s.date.iloc[-1]] + 1], q=len(s), r=(1 + s.r).prod() - 1, spy=(1 + s.spy).prod() - 1,
                       ret=r0.ret, rank=r0['rank'], roic=r0.roic, growth=r0.growth, pe=r0.pe, sector=r0.sector))
S = pd.DataFrame(st); S['ex'] = S.r - S.spy
pc = lambda v: '—' if pd.isna(v) else f'{v:+.0%}'
p0 = lambda v: '—' if pd.isna(v) else f'{v:.0%}'
out = ['# Os erros da Top 20 por retorno esperado (EUA, 2011–2026)\n', '> ⚠️ O ROIC pode estar errado.\n',
       f'Cada linha é uma **passagem** de uma ação pela carteira: da entrada até a saída. Foram {len(S)} passagens de {S.t.nunique()} empresas. '
       'Erro = a ação perdeu dinheiro, ou rendeu menos que o S&P 500 nos mesmos trimestres.\n',
       '## Quantas vezes o ranking errou\n', '| | Passagens | % que perdeu dinheiro | % que perdeu do S&P |', '|---|---|---|---|',
       f'| Todas | {len(S)} | {(S.r < 0).mean():.0%} | {(S.ex < 0).mean():.0%} |']
out += ['', '## O erro foi maior no topo do ranking? (por posição na entrada)\n', '| Posição no ranking | Passagens | % que perdeu do S&P | Excesso mediano | Retorno esperado mediano na entrada |', '|---|---|---|---|---|']
for a, b in ((1, 5), (6, 10), (11, 15), (16, 20)):
    x = S[(S['rank'] >= a) & (S['rank'] <= b)]
    out.append(f'| {a}–{b} | {len(x)} | {(x.ex < 0).mean():.0%} | {pc(x.ex.median())} | {p0(x.ret.median())} |')
out += ['', '## Por retorno esperado na entrada\n', '| Retorno esperado | Passagens | % que perdeu dinheiro | % que perdeu do S&P | Excesso mediano |', '|---|---|---|---|---|']
for a, b, l in ((0, .5, 'até 50%'), (.5, 1, '50–100%'), (1, 2, '100–200%'), (2, 99, 'acima de 200%')):
    x = S[(S.ret >= a) & (S.ret < b)]
    out.append(f'| {l} | {len(x)} | {(x.r < 0).mean():.0%} | {(x.ex < 0).mean():.0%} | {pc(x.ex.median())} |')
row = lambda r: f"| {r.t} | {nm(r.t)} | {r.ini:%m/%Y}–{r.fim:%m/%Y} | {r.q} | {r['rank']} | {p0(r.ret)} | {p0(r.roic)} | {p0(r.growth)} | {'—' if pd.isna(r.pe) else f'{r.pe:.0f}'} | **{pc(r.r)}** | {pc(r.spy)} |"
hdr = ['| Ação | Empresa | Na carteira | Trim. | Posição na entrada | Retorno esperado na entrada | ROIC | Crescimento | P/L | Retorno da ação | S&P no mesmo período |', '|---|---|---|---|---|---|---|---|---|---|---|']
out += ['', '## 20 maiores perdas em dinheiro\n'] + hdr + [row(r) for _, r in S.sort_values('r').head(20).iterrows()]
out += ['', '## 20 piores contra o S&P (subiram, mas menos que o índice, ou caíram)\n'] + hdr + [row(r) for _, r in S.sort_values('ex').head(20).iterrows()]
by = S[S.ex < 0].groupby('sector').size().sort_values(ascending=False).head(6)
out += ['', '**Setores com mais erros:** ' + ', '.join(f'{k} ({v})' for k, v in by.items())]
(ROOT / 'top20_erros.md').write_text('\n'.join(out)); print('\n'.join(out))
