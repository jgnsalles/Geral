"""Teste fora da amostra no Brasil com a regra CONGELADA em 2026-11-10 (ver PROTOCOLO.md), sem nenhum ajuste depois de ver o resultado.
Regra: OoL = ROIC >= 12% (medio 10-12%), sem zROIC, demais cortes como nos EUA; P/E justo com ROIC limitado a 100%;
sem vestuario/calcados/texteis e sem os subsetores ciclicos da regua (mapeados abaixo para os setores da CVM ANTES de rodar);
ponderacao principal: raiz do valor de mercado; peso igual como controle. Parametros brasileiros ja existentes (WACC 12%, g 9%->4%).
Saidas: brasil/oos_congelado.md, brasil/oos_congelado.png. Uso: python3 brasil/oos_congelado.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest'))
import engine  # noqa: E402
from backtest import stats  # noqa: E402
from pesos import run_weighted  # noqa: E402

D = ROOT / 'data'
WACC = 0.12
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
# mapeamento feito antes de rodar: subsetores ciclicos da regua dos EUA -> empresas/setores da CVM
CYC_SECTORS = {'Petróleo e Gás', 'Emp. Adm. Part. - Petróleo e Gás', 'Extração Mineral', 'Emp. Adm. Part. - Extração Mineral'}
CYC_TICKERS = {'GGBR4', 'USIM5', 'GOAU4', 'CBAV3', 'FESA4', 'PMAM3', 'BRAP4', 'UGPA3', 'OPCT3', 'AZTE3',  # aco/metais, refino/distribuicao, servicos de petroleo
               'AZUL3', 'FHER3', 'BMKS3', 'RVEE3', 'PFRM3'}  # aerea, fertilizantes, produtos de lazer, distribuidora de saude
APPAREL = {'AZZA3', 'ALPA4', 'VULC3', 'GRND3', 'TFCO4', 'CAMB3', 'CEDO4', 'DOHL4', 'CTKA4'}  # marcas, calcados e texteis


def main():
    u = pd.read_csv(D / 'universe.csv'); u['tk'] = u.ticker
    sec = u.set_index('yf').Setor_Atividade; tkr = u.set_index('yf').ticker; cvm = u.set_index('yf').Codigo_CVM; nm = u.set_index('yf').Nome_Empresarial
    c = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    adj = read('adj_close')
    cov = c.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    dates = sorted(d for d in c.date.unique() if d >= start)
    c = c[c.date.isin(dates)].copy()
    # regra congelada
    r = c.roic.clip(upper=1.0)
    c['fair_pe'] = np.where(r > 0, (1 - c.g / r) / (WACC - c.g), np.nan)
    base = c.fair_pe * c.eps * (1 + c.growth) ** 2 / c.price
    c['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + c.dy
    c['ret_const'] = c.growth + c.dy
    both = c.ret_fair.notna() & c.ret_const.notna(); c['ret'] = np.where(both, (c.ret_fair + c.ret_const) / 2, c.growth)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': 0.12, 'Roic_Lo': 0.10, 'zRoic': 0.7})
    try:
        n = engine.classify(c.assign(zroic=0.0))
    finally:
        engine.TH.clear(); engine.TH.update(saved)
    c['cat_new'] = np.where(n.code.isna(), None, n.category)
    c['cyc'] = c.ticker.map(sec).isin(CYC_SECTORS) | c.ticker.map(tkr).isin(CYC_TICKERS)
    c['app'] = c.ticker.map(tkr).isin(APPAREL)
    ok = ~c.cyc & ~c.app
    # valor de mercado: preco x (lucro liquido / LPA) do ultimo exercicio entregue
    fund = pd.read_csv(D / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB'])
    fund['fy'] = fund.DT_REFER.dt.year
    shares = []
    for rr in c.itertuples():
        f = fund[(fund.CD_CVM == cvm.get(rr.ticker)) & (fund.DT_RECEB <= rr.date) & (fund.fy == rr.last_fy)]
        ni = f.sort_values(['DT_RECEB']).ni.iloc[-1] if len(f) else np.nan
        shares.append(ni / rr.eps if pd.notna(ni) and rr.eps and abs(rr.eps) > 1e-6 and np.sign(ni) == np.sign(rr.eps) else np.nan)
    c['sh'] = shares
    c['sh'] = c.groupby('ticker').sh.transform(lambda s: s.ffill().bfill())
    c['mcap'] = (c.price * c.sh).where(lambda s: s > 0)
    c['mcap'] = c.mcap.fillna(c.groupby('date').mcap.transform('median'))
    H = {'OoL antigo': c['cat_zg2.93'] == OOL, 'GCGR antigo': c['cat_zg2.93'] == GCGR,
         'OoL novo': (c.cat_new == OOL) & ok, 'GCGR novo': (c.cat_new == GCGR) & ok,
         'OoL High ROIC (novo)': (c.cat_new == OOL) & ok & (c.roic > .3), 'OoL High Growth (novo)': (c.cat_new == OOL) & ok & (c.growth > .3),
         'Cyclicals': c.cat_new.isin([OOL, GCGR]) & c.cyc & ~c.app, 'Universo (todas as classificadas)': c.cat_new.notna()}
    navs, nn = {}, {}
    for k, m in H.items():
        x = c[m]
        for wn, col in (('peso igual', None), ('raiz do valor de mercado', 'mcap')):
            w = {d: pd.Series(1.0 if col is None else np.sqrt(g[col].values), index=g.ticker) for d, g in x.groupby('date')}
            navs[(k, wn)] = run_weighted(w, adj, dates); nn[(k, wn)] = x.groupby('date').size().mean()
    for b, lab in (('BOVA11.SA', 'Ibovespa (BOVA11)'), ('SMAL11.SA', 'Small caps (SMAL11)')):
        s = adj[b].loc[dates[0]:dates[-1]].dropna(); navs[(lab, '')] = s / s.iloc[0]
    B = navs[('Ibovespa (BOVA11)', '')]; MB = B.resample('ME').last()
    pc = lambda v: f'{v:.1%}'.replace('.', ',')
    def win(nav, y):
        M = nav.resample('ME').last(); a = (M / M.shift(12 * y)); b = (MB / MB.shift(12 * y)).reindex(a.index)
        mk = a.notna() & b.notna(); return (a[mk] > b[mk]).mean() if mk.any() else np.nan
    out = ['# Brasil, fora da amostra, com a regra congelada (2026-11-10)\n',
           '> ⚠️ **ROIC:** no Brasil o ROIC é o clássico (lucro operacional após IR ÷ patrimônio + dívida − caixa; capital operacional se ≤ 0), '
           'não a definição B dos EUA, que não foi reconstruída com os dados da CVM; financeiras usam ROE.\n',
           f'Período {pd.Timestamp(dates[0]):%m/%Y} a {pd.Timestamp(dates[-1]):%m/%Y}, em reais, rebalanceamento trimestral, liquidez mínima de R$ 2 milhões/dia, '
           'sem custos nem impostos. Regra aplicada sem nenhum ajuste depois de ver o resultado; o mapeamento dos setores cíclicos e do vestuário para os '
           'setores da CVM foi fixado antes de rodar (ver o código). Parâmetros brasileiros de antes (WACC 12%, g de 9% a 4%).\n',
           '| Carteira | Ponderação | Retorno anual | vs Ibovespa | Pior queda | Ações (média) | Janelas 3a > Ibov | Janelas 5a > Ibov |', '|---|---|---|---|---|---|---|---|']
    SB = stats(B)['CAGR']
    for (k, wn), nav in navs.items():
        s = stats(nav)
        out.append(f"| {k} | {wn or '—'} | **{pc(s['CAGR'])}** | {f"{(s['CAGR'] - SB) * 100:+.1f}".replace('.', ',')} p.p. | {pc(s['MaxDD'])} | {nn.get((k, wn), float('nan')):.0f} | {win(nav, 3):.0%} | {win(nav, 5):.0%} |".replace('nan', '—'))
    # quem esta na OoL nova hoje
    last = c[c.date == c.date.max()]
    cur = last[H['OoL novo'].reindex(last.index)]
    out += ['', f'## OoL novo hoje ({pd.Timestamp(c.date.max()):%m/%Y}): {len(cur)} ações\n',
            ', '.join(f"{tkr.get(t, t)} ({str(nm.get(t, t)).title()[:30]})" for t in cur.sort_values('mcap', ascending=False).ticker)]
    (ROOT / 'oos_congelado.md').write_text('\n'.join(out)); print('\n'.join(out))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    cols = {'OoL novo': '#1f6feb', 'GCGR novo': '#e8590c', 'OoL High ROIC (novo)': '#2da44e', 'OoL High Growth (novo)': '#8250df', 'Cyclicals': '#bf8700',
            'OoL antigo': '#54aeff', 'GCGR antigo': '#f0a35e', 'Universo (todas as classificadas)': '#6e7781'}
    for (k, wn), nav in navs.items():
        if wn == 'peso igual': continue
        col = cols.get(k, '#000'); ls = '--' if k.startswith('Ibov') else (':' if k.startswith('Small') else '-')
        ax.plot(nav.index, (nav - 1) * 100, color=col if wn else ('#000' if k.startswith('Ibov') else '#8c959f'), ls=ls, lw=2.4 if k == 'OoL novo' else 1.5,
                label=f"{k}{' — ' + wn if wn else ''} (" + pc(stats(nav)['CAGR']) + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=7, loc='upper left')
    ax.set_title('Brasil, fora da amostra, regra congelada (raiz do valor de mercado) — retorno total acumulado em reais', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'oos_congelado.png'); plt.close(fig)


if __name__ == '__main__':
    main()
