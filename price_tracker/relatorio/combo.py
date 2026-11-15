"""Combinacao Top 20 da OoL + OoL High ROIC (pre-registro de 2026-11-15), S&P 500 e medias/pequenas. Saida: relatorio/dados3.json"""
import sys, json, pathlib
sys.argv = sys.argv[:1]
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; sys.path.insert(0, str(ROOT))
import calc2  # noqa: E402
from calc2 import weights, run_weighted, tax_weighted, stats, factors, bm  # noqa: E402
import calc  # noqa: E402

MIX = [(1.0, '100% Top 20'), (.7, '70% Top 20 + 30% High ROIC'), (.5, '50% / 50%'), (.3, '30% Top 20 + 70% High ROIC'), (0.0, '100% High ROIC')]


def blend(W, a):
    out = {}
    for d in sorted(set(W['top20']) | set(W['hroic'])):
        x = W['top20'].get(d, pd.Series(dtype=float)) * a; y = W['hroic'].get(d, pd.Series(dtype=float)) * (1 - a)
        z = x.add(y, fill_value=0); z = z[z > 0]
        if len(z): out[d] = z / z.sum()
    return out


def go(c, adj, dates, ref, refname):
    W = weights(c); rf = factors()['RF']; res = {}; nav_m = {}
    for a, lab in MIX:
        Wb = blend(W, a); nav = run_weighted(Wb, adj, dates)
        mt = calc.metrics(nav, ref, rf); mt['cagr_tax'] = stats(tax_weighted(Wb, adj, dates))['CAGR']; mt.update(calc.turnover(Wb))
        res[lab] = {k: v for k, v in mt.items() if k != 'years'}; nav_m[lab] = nav.resample('ME').last()
        print(refname, lab, round(mt['cagr'], 4), round(mt['w3'], 3), flush=True)
    M = pd.DataFrame(nav_m)
    return {'ref': refname, 'ref_cagr': stats(ref.loc[dates[0]:dates[-1]] / ref.loc[dates[0]:].iloc[0])['CAGR'], 'mix': res,
            'nav': {'dates': [str(d.date()) for d in M.index], 'series': {k: [round(float(x), 5) for x in M[k] / M[k].iloc[0]] for k in M}}}


if __name__ == '__main__':
    c, adj, dates, ref, _ = calc2.sp_data(); sp = go(c, adj, dates, ref, 'S&P 500')
    n, adj2, dates2, iwm, _ = calc2.ms_data(); ms = go(n, adj2, dates2, iwm, 'Russell 2000 (IWM)')
    (ROOT / 'dados3.json').write_text(json.dumps({'sp': sp, 'ms': ms}, ensure_ascii=False, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else float(o)))
