"""Decomposicao da Opportunity of Lifetime sem zROIC (universo point-in-time, ROIC oficial, esboco 12%).
1. OoL em 4 partes disjuntas (Ambos, So High Returns, So High Growth, Base): peso, retorno, contribuicao.
2. O que mudou ao tirar o zROIC: empresas que entraram, por subclasse.
3. Atribuicao por empresa (maiores e menores) em cada parte.
4. Graficos de dispersao por empresa.
Saidas: backtest/attrib_sem_zroic.md, backtest/attrib_sem_zroic.png
Uso: python3 backtest/attrib_sem_zroic.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL = 'Opportunity of Lifetime'
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
sp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.2f}'.replace('.', ',')
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')
PARTS = ['Ambos (ROIC > 30% e EPS > 30%)', 'Só High Returns (ROIC > 30%)', 'Só High Growth (EPS > 30%)', 'OoL Base']
COL = dict(zip(PARTS, ['#cf222e', '#2da44e', '#8250df', '#57606a']))


def part(r):
    hr, hg = r.roic > 0.30, r.growth > 0.30
    return np.select([hr & hg, hr, hg], PARTS[:3], PARTS[3])


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member]
    adj = load_prices()['adj_close']
    u = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'name', 'sector']],
                   pd.read_csv(D / 'universe_pit_extra.csv').rename(columns={'sec_name': 'name'})[['ticker', 'name']]]).drop_duplicates('ticker').set_index('ticker')
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    def prep(c):
        c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
        return c[c.date < dates[-1]].copy()
    com = prep(vp.classify(f, 'sketch', 'B'))
    sem = prep(vp.classify(f.assign(zroic=0.0), 'sketch', 'B'))
    uq = sem[sem.cat.notna()].groupby('date').rq.mean()
    Y = (len(dates) - 1) / 4
    o = sem[sem.cat == OOL].copy()
    o['part'] = part(o); o['n'] = o.groupby('date').ticker.transform('size')
    o['ctr'] = o.rq / o.n                     # contribuicao ao retorno da OoL no trimestre
    o['ex'] = o.rq - o.date.map(uq); o['exc'] = o.ex / o.n  # contribuicao ao excesso da OoL sobre o universo
    old = set(zip(com[com.cat == OOL].date, com[com.cat == OOL].ticker))
    o['novo'] = [(d, t) not in old for d, t in zip(o.date, o.ticker)]
    tot_r, tot_x = o.ctr.sum() / Y, o.exc.sum() / Y

    out = ['# Decomposição da Opportunity of Lifetime sem zROIC (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A); zROIC desligado; OoL a partir de ROIC 12%.\n',
           'Contribuição = retorno de cada ação ÷ nº de ações da OoL no trimestre, somado e dividido pelo nº de anos '
           f'({Y:.1f}). As partes somam exatamente o retorno médio aritmético da OoL (que é maior que o CAGR por causa da volatilidade). '
           'Excesso = sobre a média do universo no mesmo trimestre.\n',
           '## 1. A OoL em quatro partes que não se sobrepõem\n',
           'Os números de High Returns e High Growth da análise anterior incluíam as empresas que estão nas duas; aqui cada ação aparece uma vez só.\n',
           '| Parte | Peso médio na OoL | Ações por trimestre | Retorno médio da parte (a.a.) | Excesso da parte (a.a.) | **Contribuição ao retorno da OoL** | **Contribuição ao excesso da OoL** |',
           '|---|---|---|---|---|---|---|']
    for p in PARTS:
        x = o[o.part == p]; w = (x.groupby('date').size() / o.groupby('date').size()).reindex(o.date.unique()).fillna(0).mean()
        out.append(f'| {p} | {pc(w)} | {x.groupby("date").size().reindex(o.date.unique()).fillna(0).mean():.1f} | {pc(x.rq.mean() * 4)} | {sg(x.ex.mean() * 4)} | '
                   f'**{sp(x.ctr.sum() / Y)} p.p.** | **{sp(x.exc.sum() / Y)} p.p.** |')
    out.append(f'| **OoL inteira** | 100% | {o.groupby("date").size().mean():.1f} | {pc(tot_r)} | {sg(tot_x)} | **{sp(tot_r)} p.p.** | **{sp(tot_x)} p.p.** |')

    # 2) o que entrou ao tirar o zROIC
    nw = o[o.novo]
    out += ['', '## 2. O que mudou ao tirar o zROIC\n',
            f'Entraram {len(nw)} posições ({nw.ticker.nunique()} empresas, {len(nw) / o.date.nunique():.1f} por trimestre). '
            f'Contribuição delas ao excesso da OoL: {sp(nw.exc.sum() / Y)} p.p. a.a.\n',
            '| Parte | Posições novas | Empresas | Excesso médio a.a. | Contribuição ao excesso da OoL | Empresas (por contribuição) |', '|---|---|---|---|---|---|']
    for p in PARTS:
        x = nw[nw.part == p]
        if x.empty: out.append(f'| {p} | 0 | 0 | — | — | |'); continue
        a = x.groupby('ticker').exc.sum().sort_values(ascending=False)
        out.append(f'| {p} | {len(x)} | {x.ticker.nunique()} | {sg(x.ex.mean() * 4)} | {sp(x.exc.sum() / Y)} p.p. | '
                   + ', '.join(f'{t} ({sp(v / Y)})' for t, v in a.items()) + ' |')

    # 3) atribuicao por empresa
    def agg(x):
        return x.groupby('ticker').agg(ctr=('exc', 'sum'), trim=('exc', 'size'), ex=('ex', 'mean'), rq=('rq', 'mean'), roic=('roic', 'median'),
                                       growth=('growth', 'median'), pe=('pe', 'median'), exp=('ret', 'median'), p0=('date', 'min'), p1=('date', 'max'),
                                       novo=('novo', 'sum'))
    o['pe'] = o.price / o.eps.where(o.eps > 0)
    hdr = ['| Ticker | Empresa | Setor | Contribuição ao excesso da OoL (p.p. a.a.) | Trim. | Excesso médio a.a. | Retorno esperado | ROIC | Crescimento | P/L | Período |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    def row(t, r):
        star = ' *' if r.novo else ''
        return (f"| {t}{star} | {u['name'].get(t, '')} | {u['sector'].get(t, '') if isinstance(u['sector'].get(t, ''), str) else ''} | {sp(r.ctr / Y)} | {r.trim} | "
                f"{sg(r.ex * 4)} | {pc(r.exp)} | {pc(r.roic)} | {pc(r.growth)} | {n1(r.pe)} | {r.p0.year}–{r.p1.year} |")
    out += ['', '## 3. Atribuição por empresa\n', '\\* = empresa com posições que só existem sem o zROIC.\n']
    for p in PARTS:
        a = agg(o[o.part == p]).sort_values('ctr', ascending=False)
        pos, neg = a.ctr.clip(lower=0).sum(), a.ctr.clip(upper=0).sum()
        out += [f'### {p}\n', f'{len(a)} empresas. Soma dos positivos {sp(pos / Y)} p.p., dos negativos {sp(neg / Y)} p.p.; '
                f'as 5 maiores somam {sp(a.ctr.head(5).sum() / Y)} p.p.; sem elas a parte contribuiria {sp((a.ctr.sum() - a.ctr.head(5).sum()) / Y)} p.p. '
                f'Mediana do excesso por empresa: {sg(a.ex.median() * 4)}; empresas com excesso positivo: {pc((a.ex > 0).mean())}.\n',
                '**Maiores**\n'] + hdr + [row(t, r) for t, r in a.head(12).iterrows()] + \
               ['', '**Menores**\n'] + hdr + [row(t, r) for t, r in a.tail(12).iloc[::-1].iterrows()] + ['']

    # 4) dispersao
    A = agg(o); A['part'] = o.groupby('ticker').part.agg(lambda s: s.value_counts().index[0])
    A['ctr_y'] = A.ctr / Y; A['ex_a'] = A.ex * 4
    fig, ax = plt.subplots(2, 2, figsize=(15, 11), dpi=130); ax = ax.ravel()
    lab = set(A.ctr_y.nlargest(10).index) | set(A.ctr_y.nsmallest(8).index)
    def sc(axx, xcol, ycol, xl, yl, logx=False, kx=100, ky=100):
        for p in PARTS:
            d = A[A.part == p]
            axx.scatter(d[xcol] * kx, d[ycol] * ky, s=8 + d.trim * 6, c=COL[p], alpha=.55, edgecolor='white', lw=.5, label=p)
        for t in lab:
            axx.annotate(t, (A.at[t, xcol] * kx, A.at[t, ycol] * ky), fontsize=7, xytext=(3, 3), textcoords='offset points')
        axx.axhline(0, color='black', lw=.8); axx.grid(alpha=.3); axx.set_xlabel(xl, fontsize=9); axx.set_ylabel(yl, fontsize=9)
        if logx: axx.set_xscale('symlog', linthresh=100)
    sc(ax[0], 'roic', 'ex_a', 'ROIC (mediana nas compras, %)', 'Excesso médio sobre o universo (% a.a.)')
    ax[0].axvline(30, color='#2da44e', ls='--', lw=1)
    sc(ax[1], 'growth', 'ex_a', 'Crescimento do EPS 5a (mediana, %)', 'Excesso médio sobre o universo (% a.a.)')
    ax[1].axvline(30, color='#8250df', ls='--', lw=1)
    sc(ax[2], 'exp', 'ex_a', 'Retorno esperado pelo modelo (mediana, %)', 'Excesso médio realizado sobre o universo (% a.a.)')
    ax[2].set_xlim(0, min(A.exp.quantile(.98) * 100, 300))
    sc(ax[3], 'trim', 'ctr_y', 'Trimestres na OoL', 'Contribuição ao excesso da OoL (p.p. a.a.)', kx=1)
    for a_ in ax[:3]:
        a_.set_ylim(max(A.ex_a.min() * 100 * 1.05, -150), min(A.ex_a.max() * 100 * 1.05, 250))
    ax[0].set_xlim(0, min(A.roic.quantile(.98) * 100, 200)); ax[1].set_xlim(-5, min(A.growth.quantile(.98) * 100, 150))
    ax[0].legend(fontsize=7, loc='upper right'); fig.suptitle('Opportunity of Lifetime sem zROIC: cada ponto é uma empresa (tamanho = trimestres na carteira)', fontsize=11)
    fig.tight_layout(); fig.savefig(ROOT / 'attrib_sem_zroic.png'); plt.close(fig)
    (ROOT / 'attrib_sem_zroic.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
