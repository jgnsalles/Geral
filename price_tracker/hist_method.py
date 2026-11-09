"""Metodo 2 (so historico, sem nenhuma estimativa de analista).
 Growth  = mediana do crescimento do EPS nos ultimos 3 anos realizados (rank_growth)
 zGrowth = desvio-padrao desses 3 crescimentos / Growth (corte recalibrado por percentil vs. Wise)
 ROIC, zROIC, dy, g e P/E justo: iguais ao metodo 1
 Retorno = media de 2 cenarios sobre o EPS dos ultimos 12 meses (Yahoo trailingEps):
   (a) P/E converge ao justo:  (P/E justo * EPS12m * (1+Growth)^2 / preco)^(1/2) - 1 + dy
   (b) multiplo constante:     Growth + dy
Uso: python3 hist_method.py 2026-11-09"""
import sys, json, pathlib
import numpy as np, pandas as pd
import engine
from compare import wise_baseline
from experiments import quantile_cut


def main(day):
    h = pd.read_csv(f'data/hybrid_{day}.csv')
    fxf = pathlib.Path(f'data/raw/yahoo/{day}/_fx.json')
    fx = json.loads(fxf.read_text()) if fxf.exists() else {}
    d = h.copy()
    d['growth'] = d.rank_growth
    rates = d[['hg1', 'hg2', 'hg3']].to_numpy()
    d['zgrowth'] = [engine.cv(list(r), g) if np.isfinite(g) else np.nan for r, g in zip(rates, d.growth)]
    rate = [1.0 if (a == b or pd.isna(a) or pd.isna(b)) else fx.get(f'{a}{b}', np.nan) for a, b in zip(d.fin_ccy, d.currency)]
    base_eps = d.eps_ttm * np.array(rate, dtype=float)
    flags = ['' if np.isfinite(r) else 'sem cambio para EPS' for r in rate]
    gh = d.growth
    base = d.fair_pe * base_eps * (1 + gh) ** 2 / d.price
    ret_fair = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + d.dy
    ret_const = gh + d.dy
    both = pd.Series(ret_fair).notna().to_numpy() & ret_const.notna().to_numpy()
    d['ret_fair'], d['ret_const'] = ret_fair, ret_const
    d['ret'] = np.where(both, (ret_fair + ret_const) / 2, gh)
    d['flags'] = [f'{a}; {b}'.strip('; ') for a, b in zip(h['flags'].fillna(''), flags)]
    w = wise_baseline()
    cut = quantile_cut(w.zgrowth, d.zgrowth, engine.TH['zGrowth'])
    saved = engine.TH['zGrowth']; engine.TH['zGrowth'] = cut
    try:
        out = engine.classify(d.drop(columns=['category', 'code', 'order'], errors='ignore'))
    finally:
        engine.TH['zGrowth'] = saved
    out.to_csv(f'data/hist_{day}.csv', index=False)
    print(f'zGrowth corte recalibrado: {cut:.3f}')
    print(out.category.value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1])
