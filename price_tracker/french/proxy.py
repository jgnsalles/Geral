"""Teste-proxy da ideia central da regra congelada (qualidade + nao pagar caro) com as carteiras publicas de Kenneth French.
NAO e a regra congelada: French ordena por rentabilidade operacional (OP = lucro operacional / patrimonio), nao ROIC, e por
valor patrimonial/preco (BM), nao P/L justo; nao ha crescimento do EPS. Serve para ver se a ideia vale em mais regioes e mais anos.
Carteiras (pesos por valor de mercado, ja publicadas):
  Qualidade        = quartil (EUA: quintil) mais alto de OP, media simples dos grupos de BM
  Qualidade sem as caras = mesmo, excluindo o grupo de BM mais baixo (as mais caras)
  Qualidade so as caras  = OP alto e BM mais baixo
Internacional: so as grandes (metade de cima do valor de mercado). Uso: python3 -I proxy.py <pasta raw>"""
import sys, pathlib, io
import numpy as np, pandas as pd
R = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(__file__).parent


def block(fn, title):
    L = (R / fn).read_text(errors='ignore').splitlines()
    i = next(k for k, l in enumerate(L) if l.strip().startswith(title)) + 1
    rows = [L[i]]
    for l in L[i + 1:]:
        if not l.strip() or not l.strip()[:6].isdigit(): break
        rows.append(l)
    df = pd.read_csv(io.StringIO('\n'.join(rows)), index_col=0)
    df.index = pd.to_datetime(df.index.astype(str).str.strip(), format='%Y%m') + pd.offsets.MonthEnd(0)
    df.columns = [c.strip() for c in df.columns]
    return df.replace([-99.99, -999], np.nan) / 100


def fac(fn):
    f = block(fn, ',Mkt-RF') if False else None
    L = (R / fn).read_text(errors='ignore').splitlines()
    i = next(k for k, l in enumerate(L) if 'Mkt-RF' in l)
    rows = [L[i]]
    for l in L[i + 1:]:
        if not l.strip() or not l.strip()[:6].isdigit() or len(l.split(',')[0].strip()) != 6: break
        rows.append(l)
    df = pd.read_csv(io.StringIO('\n'.join(rows)), index_col=0)
    df.index = pd.to_datetime(df.index.astype(str).str.strip(), format='%Y%m') + pd.offsets.MonthEnd(0)
    df.columns = [c.strip() for c in df.columns]; df = df / 100
    return df['Mkt-RF'] + df['RF']


def cagr(r):
    r = r.dropna(); return (1 + r).prod() ** (12 / len(r)) - 1 if len(r) else np.nan


def dd(r):
    n = (1 + r.dropna()).cumprod(); return (n / n.cummax() - 1).min()


def sets_intl(df):
    c = list(df.columns); big = c[16:]  # metade grande
    hi = [big[k] for k in (3, 7, 11, 15)]  # OP4 em BM1..BM4
    return {'Qualidade': df[hi].mean(axis=1), 'Qualidade sem as caras': df[hi[1:]].mean(axis=1), 'Qualidade só as caras': df[hi[0]],
            'Pior rentabilidade': df[[big[k] for k in (0, 4, 8, 12)]].mean(axis=1)}


def sets_us(df):
    c = list(df.columns); hi = [c[k] for k in (4, 9, 14, 19, 24)]
    return {'Qualidade': df[hi].mean(axis=1), 'Qualidade sem as caras': df[hi[1:]].mean(axis=1), 'Qualidade só as caras': df[hi[0]],
            'Pior rentabilidade': df[[c[k] for k in (0, 5, 10, 15, 20)]].mean(axis=1)}


REG = [('EUA (desde 1963)', '25_Portfolios_BEME_OP_5x5.csv', 'F-F_Research_Data_Factors.csv', sets_us),
       ('Europa', 'Europe_32_Portfolios_ME_BE-ME_OP_2x4x4.csv', 'Europe_3_Factors.csv', sets_intl),
       ('Japão', 'Japan_32_Portfolios_ME_BE-ME_OP_2x4x4.csv', 'Japan_3_Factors.csv', sets_intl),
       ('Ásia-Pacífico ex-Japão', 'Asia_Pacific_ex_Japan_32_Portfolios_ME_BE-ME_OP_2x4x4.csv', 'Asia_Pacific_ex_Japan_3_Factors.csv', sets_intl),
       ('América do Norte', 'North_America_32_Portfolios_ME_BE-ME_OP_2x4x4.csv', 'North_America_3_Factors.csv', sets_intl),
       ('Desenvolvidos (todos)', 'Developed_32_Portfolios_ME_BE-ME_OP_2x4x4.csv', 'Developed_3_Factors.csv', sets_intl)]
pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
pp = lambda v: '—' if pd.isna(v) else f'{v * 100:+.1f}'.replace('.', ',')
out, navs = [], {}
for name, fn, ff, fsets in REG:
    df = block(fn, 'Average Value Weighted Returns -- Monthly'); mkt = fac(ff)
    S = {'Mercado': mkt.reindex(df.index), **fsets(df)}
    navs[name] = S
    per = [('Período todo', df.index[0], df.index[-1])]
    if name.startswith('EUA'): per += [('1963–1990', '1963', '1990'), ('1991–2010', '1991', '2010'), ('2011–2026', '2011', '2026')]
    else: per += [('até 2010', '1990', '2010'), ('2011–2026', '2011', '2026')]
    out += [f'\n## {name} ({df.index[0]:%m/%Y}–{df.index[-1]:%m/%Y})\n', '| Carteira | ' + ' | '.join(p[0] for p in per) + ' | Pior queda | Anos > mercado |',
            '|---|' + '---|' * (len(per) + 2)]
    for k, r in S.items():
        cells = []
        for _, a, b in per:
            x, m = r.loc[a:b], S['Mercado'].loc[a:b]
            cells.append(pc(cagr(x)) if k == 'Mercado' else f'{pc(cagr(x))} ({pp(cagr(x) - cagr(m))})')
        A = (1 + r).resample('YE').prod(); M = (1 + S['Mercado']).resample('YE').prod()
        out.append(f"| {k} | " + ' | '.join(cells) + f" | {pc(dd(r))} | {'—' if k == 'Mercado' else f'{(A > M).mean():.0%}'} |")
# emergentes: 2x2 OP x BM, sem tamanho
em = block('Emerging_Markets_4_Portfolios_BE-ME_OP.csv', 'Average Value Weighted Returns -- Monthly')
mk = fac('Emerging_5_Factors.csv').reindex(em.index)
out += [f'\n## Emergentes ({em.index[0]:%m/%Y}–{em.index[-1]:%m/%Y}; só 2×2, sem separar tamanho)\n', '| Carteira | Período todo | até 2010 | 2011–2026 |', '|---|---|---|---|']
for k, r in {'Mercado': mk, **{c: em[c] for c in em.columns}}.items():
    out.append(f'| {k} | ' + ' | '.join(pc(cagr(r.loc[a:b])) if k == 'Mercado' else f'{pc(cagr(r.loc[a:b]))} ({pp(cagr(r.loc[a:b]) - cagr(mk.loc[a:b]))})'
                                        for a, b in ((None, None), (None, '2010'), ('2011', None))) + ' |')
txt = '\n'.join(out); (OUT / 'resultado.md').write_text(txt); print(txt)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 3, figsize=(15, 8), dpi=130)
for ax, (name, S) in zip(axs.flat, navs.items()):
    for k, col, ls in (('Mercado', '#000', '--'), ('Qualidade', '#1f6feb', '-'), ('Qualidade sem as caras', '#2da44e', '-'), ('Qualidade só as caras', '#cf222e', ':')):
        n = (1 + S[k].dropna()).cumprod(); ax.plot(n.index, (n - 1) * 100, color=col, ls=ls, lw=1.6, label=f'{k} ({pc(cagr(S[k]))} a.a.)')
    ax.set_title(name, fontsize=10); ax.grid(alpha=.3); ax.legend(fontsize=7, loc='upper left'); ax.set_yscale('symlog', linthresh=100)
fig.suptitle('Proxy de Fama-French: rentabilidade alta × mercado — retorno total acumulado em dólares (%)', fontsize=11)
fig.tight_layout(); fig.savefig(OUT / 'resultado.png'); plt.close(fig)
