"""Cenario: o mundo sem a NVIDIA (2026-11-14). Saida: relatorio/sem_nvda.json"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path.insert(0, str(P)); sys.path.insert(0, str(P / 'backtest')); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats  # noqa: E402
from giro_menor import tax_weighted  # noqa: E402
from validation_factors import factors  # noqa: E402
import calc  # noqa: E402

DROP = {'NVDA'}


def main():
    f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']
    bnav, _, _, _ = bm.load_benchmarks(); spy = bnav['S&P 500']
    # S&P sem NVIDIA: SPY x (sintetico sem / sintetico com)
    c0 = bm.classify_new(f)
    allm = c0[['date', 'ticker', 'price', 'eps', 'last_fy']].copy(); allm['mcap'] = top_n.mcap_us(allm, allm)
    Wc = {d: (g.set_index('ticker').mcap.dropna() / g.mcap.sum()) for d, g in allm.groupby('date')}
    We = {d: w.drop(list(DROP & set(w.index))) for d, w in Wc.items()}
    sc, se = run_weighted(Wc, adj, dates), run_weighted(We, adj, dates)
    ratio = (se / sc).reindex(spy.index).ffill()
    spy_ex = spy * ratio / ratio.iloc[0]
    print('S&P sem NVIDIA', stats(spy)['CAGR'], stats(spy_ex)['CAGR'], flush=True)
    # 9 obrigatorios sem NVIDIA
    orig = bm.base_data
    bm.base_data = lambda *a, **k: (lambda r: (r[0][~r[0].ticker.isin(DROP)].reset_index(drop=True), r[1]))(orig(*a, **k))
    try: bex, _, _, _ = bm.load_benchmarks()
    finally: bm.base_data = orig
    bex['S&P 500'] = spy_ex
    # estrategias
    fe = f[~f.ticker.isin(DROP)].reset_index(drop=True)
    out = {'spy': stats(spy)['CAGR'], 'spy_ex': stats(spy_ex)['CAGR'], 'strat': {}, 'bench': {}}
    Wo, _ = calc.weights(c0); Wx, _ = calc.weights(bm.classify_new(fe))
    rf = factors()['RF']
    navs = {}
    for k in calc.NAMES:
        a = run_weighted(Wo[k], adj, dates); b = run_weighted(Wx[k], adj, dates); navs[k] = (a, b)
        ma, mb = calc.metrics(a, spy, rf), calc.metrics(b, spy_ex, rf)
        out['strat'][k] = dict(cagr=ma['cagr'], cagr_ex=mb['cagr'], tax_ex=stats(tax_weighted(Wx[k], adj, dates))['CAGR'],
                               w3_ex=mb['w3'], w5_ex=mb['w5'], w10_ex=mb['w10'], w3min_ex=mb['w3min'], maxdd_ex=mb['maxdd'], behind_ex=mb['behind_months'],
                               vol_ex=mb['vol'], excess=ma['cagr'] - stats(spy)['CAGR'], excess_ex=mb['cagr'] - stats(spy_ex)['CAGR'],
                               nvda_w=float(np.mean([w.get('NVDA', 0.0) for w in Wo[k].values()])), nvda_q=float(np.mean([('NVDA' in w.index) for w in Wo[k].values()])))
        print(k, round(ma['cagr'], 4), round(mb['cagr'], 4), flush=True)
    for k, v in bex.items():
        out['bench'][k] = dict(cagr=stats(v)['CAGR'], maxdd=stats(v)['MaxDD'], w3=bm.windows(v, spy_ex, 3)[0], w5=bm.windows(v, spy_ex, 5)[0], w10=bm.windows(v, spy_ex, 10)[0])
    M = pd.DataFrame({**{calc.NAMES[k] + ' (sem NVIDIA)': v[1].resample('ME').last() for k, v in navs.items()}, 'S&P 500 (sem NVIDIA)': spy_ex.resample('ME').last(),
                      'As excepcionais (com NVIDIA)': navs['n2'][0].resample('ME').last(), 'S&P 500': spy.resample('ME').last()})
    out['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(x) else round(float(x), 5) for x in M[k] / M[k].dropna().iloc[0]] for k in M}}
    (ROOT / 'sem_nvda.json').write_text(json.dumps(out, ensure_ascii=False, default=float)); print(json.dumps({k: {a: round(b, 3) for a, b in v.items()} for k, v in out['strat'].items()}, indent=0))


if __name__ == '__main__':
    main()
