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

# --- retorno antes da entrada
def prior(t, d, m):
    s = adj[t].loc[:d].dropna()
    if s.empty: return np.nan
    p0 = adj[t].loc[:d - pd.DateOffset(months=m)].dropna()
    return s.iloc[-1] / p0.iloc[-1] - 1 if len(p0) else np.nan
S['m12'] = [prior(r.t, r.ini, 12) for r in S.itertuples()]; S['m6'] = [prior(r.t, r.ini, 6) for r in S.itertuples()]
S['spy12'] = [prior('SPY', r.ini, 12) for r in S.itertuples()]
S['rel12'] = S.m12 - S.spy12
out2 = ['', '## O que a ação vinha fazendo antes de entrar\n',
        '| Grupo | Passagens | Retorno nos 12 meses antes (mediana) | Nos 6 meses antes (mediana) | 12 meses antes vs S&P (mediana) | % que vinha caindo em 12 meses |',
        '|---|---|---|---|---|---|']
for lab, m in (('Erros: perdeu do S&P', S.ex < 0), ('Acertos: bateu o S&P', S.ex >= 0), ('20 maiores perdas', S.index.isin(S.sort_values('r').head(20).index))):
    x = S[m]
    out2.append(f'| {lab} | {len(x)} | {pc(x.m12.median())} | {pc(x.m6.median())} | {pc(x.rel12.median())} | {(x.m12 < 0).mean():.0%} |')
out2 += ['', '### Desempenho conforme o que a ação vinha fazendo nos 12 meses antes\n',
         '| Retorno nos 12 meses antes | Passagens | % que perdeu dinheiro | % que perdeu do S&P | Excesso mediano |', '|---|---|---|---|---|']
for a, b, l in ((-9, -.2, 'caiu mais de 20%'), (-.2, 0, 'caiu até 20%'), (0, .2, 'subiu até 20%'), (.2, .5, 'subiu 20–50%'), (.5, 99, 'subiu mais de 50%')):
    x = S[(S.m12 >= a) & (S.m12 < b)]
    out2.append(f'| {l} | {len(x)} | {(x.r < 0).mean():.0%} | {(x.ex < 0).mean():.0%} | {pc(x.ex.median())} |')
out2 += ['', '### As 20 maiores perdas: o que vinham fazendo antes\n', '| Ação | Empresa | Entrada | 12 meses antes | 6 meses antes | S&P 12 meses antes | Retorno na carteira |', '|---|---|---|---|---|---|---|']
for _, r in S.sort_values('r').head(20).iterrows():
    out2.append(f'| {r.t} | {nm(r.t)} | {r.ini:%m/%Y} | **{pc(r.m12)}** | {pc(r.m6)} | {pc(r.spy12)} | {pc(r.r)} |')
with open(ROOT / 'top20_erros.md', 'a') as fh: fh.write('\n'.join(out2))
print('\n'.join(out2))

# --- decomposicao das 20 maiores perdas: lucro x multiplo
fv = pd.read_csv(D / 'val_features.csv', parse_dates=['date'], usecols=['date', 'ticker', 'eps', 'price', 'gy1', 'gy2', 'gy3', 'gy4', 'gy5'])
fv = fv.drop_duplicates(['date', 'ticker']).set_index(['ticker', 'date']).sort_index()
def at(t, d):
    try:
        s = fv.loc[t]; s = s[s.index <= d]
        return s.iloc[-1] if len(s) else None
    except KeyError:
        return None
rows = ['', '## Diagnóstico das 20 maiores perdas: caiu o lucro ou o múltiplo?\n',
        'Lucro por ação e P/L na entrada e na saída (último balanço anual conhecido em cada data). Retorno de preço ≈ variação do lucro × variação do P/L.\n',
        '| Ação | Empresa | Entrada → saída | EPS na entrada → saída | P/L na entrada → saída | Maior taxa de crescimento do EPS nos 5 anos antes | Retorno |', '|---|---|---|---|---|---|---|']
for _, r in S.sort_values('r').head(20).iterrows():
    a, b = at(r.t, r.ini), at(r.t, r.fim)
    if a is None: continue
    e0 = a.eps; e1 = b.eps if b is not None else np.nan
    p1 = adj[r.t].loc[:r.fim].dropna().iloc[-1]
    pe0 = a.price / e0 if e0 > 0 else np.nan; pe1 = p1 / e1 if pd.notna(e1) and e1 > 0 else np.nan
    gmax = np.nanmax([a[f'gy{i}'] for i in range(1, 6)])
    rows.append(f"| {r.t} | {nm(r.t)} | {r.ini:%m/%Y} → {r.fim:%m/%Y} | {e0:.2f} → {e1:.2f} ({pc(e1 / e0 - 1) if e0 > 0 and pd.notna(e1) else '—'}) | "
                f"{'—' if pd.isna(pe0) else f'{pe0:.0f}'} → {'—' if pd.isna(pe1) else f'{pe1:.0f}'} | {pc(gmax)} | {pc(r.r)} |".replace('.', ','))
with open(ROOT / 'top20_erros.md', 'a') as fh: fh.write('\n'.join(rows))
print('\n'.join(rows))
