"""Backtest da regra congelada com o ROIC triangulado x oficial (2026-11-14). Saida: backtest/roic3_backtest.md e .png"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats, run_portfolio, D  # noqa: E402
from roic3_relatorio import with_tri  # noqa: E402


def top20(c, adj, dates):
    el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & c.roic.notna() & c.growth.notna()].copy()
    el['pe'] = el.price / el.eps.where(el.eps > 0); el = el[el.pe >= 4]; el['mcap'] = top_n.mcap_us(el, el)
    ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in el.groupby('date')])
    return run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), .10) for d, g in ch.groupby('date')}, adj, dates)


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    r3 = pd.read_csv(D / 'roic3.csv', parse_dates=['date'])
    m = with_tri(f, r3).drop(columns=['roic_tri', 'roic_oficial'])
    navs, n, _, _ = bm.load_benchmarks()
    navs['Top 20 (estratégia) — ROIC oficial'] = top20(bm.classify_new(f), adj, dates); n['Top 20 (estratégia) — ROIC oficial'] = 20
    ct = bm.classify_new(m)
    navs['Top 20 (estratégia) — ROIC triangulado'] = top20(ct, adj, dates); n['Top 20 (estratégia) — ROIC triangulado'] = 20
    for k, msk in bm.holdings_new(ct).items():
        if k == 'Cyclicals': continue
        lab = f'{k} — ROIC triangulado'
        navs[lab] = run_portfolio({d: g.ticker.tolist() for d, g in ct[msk].groupby('date')}, adj, dates)[0]; n[lab] = ct[msk].groupby('date').size().mean()
    out = ['# Regra congelada com o ROIC triangulado × ROIC oficial (EUA, point-in-time)\n',
           '> ⚠️ **O ROIC pode estar errado** — aqui comparamos a definição antiga com a nova (triangulada, com a regra de "arte" do usuário).\n',
           'As 9 linhas obrigatórias usam o ROIC oficial; as linhas "— ROIC triangulado" refazem as classes novas e a estratégia com o ROIC novo.\n'] + bm.bench_table(navs, n)
    (ROOT / 'roic3_backtest.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot(navs, ROOT / 'roic3_backtest.png', 'ROIC triangulado × oficial: estratégia e classes novas × comparativos obrigatórios')


if __name__ == '__main__':
    main()
