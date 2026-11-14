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
    adj = bm.load_prices()['adj_close']
    navs, n, dates, _ = bm.load_benchmarks()  # ja com o ROIC oficial novo (triangulado com outliers)
    for lab_, file_ in (('ROIC antigo', None), ('triangulado sem regra de outliers', 'roic3_sem_outliers.csv'), ('triangulado com outliers (oficial)', 'roic3.csv')):
        f, dates = bm.base_data(file_); c = bm.classify_new(f)
        navs[f'Top 20 — {lab_}'] = top20(c, adj, dates); n[f'Top 20 — {lab_}'] = 20
        if file_ != 'roic3.csv':
            for k, msk in bm.holdings_new(c).items():
                if k in ('OoL novo', 'OoL High ROIC (novo)'):
                    navs[f'{k} — {lab_}'] = run_portfolio({d: g.ticker.tolist() for d, g in c[msk].groupby('date')}, adj, dates)[0]; n[f'{k} — {lab_}'] = c[msk].groupby('date').size().mean()
    out = ['# Regra congelada com o ROIC triangulado × ROIC oficial (EUA, point-in-time)\n',
           '> ⚠️ **O ROIC pode estar errado** — aqui comparamos a definição antiga com a nova (triangulada, com a regra de "arte" do usuário).\n',
           'As 9 linhas obrigatórias já usam o ROIC oficial novo (triangulado com a regra de outliers). As outras comparam com o ROIC antigo e com o triangulado sem a regra de outliers.\n'] + bm.bench_table(navs, n)
    (ROOT / 'roic3_backtest.md').write_text('\n'.join(out)); print('\n'.join(out))
    bm.bench_plot(navs, ROOT / 'roic3_backtest.png', 'ROIC triangulado × oficial: estratégia e classes novas × comparativos obrigatórios')


if __name__ == '__main__':
    main()
