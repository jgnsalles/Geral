"""Combina correcoes no modelo hibrido e mede a aderencia final (classe/tier) ao Wisesheets.
Uso: python3 experiments.py 2026-11-09"""
import sys, itertools
import numpy as np, pandas as pd
import engine
from compare import wise_baseline, TIERS


def quantile_cut(wise_vals, hyb_vals, wise_cut):
    """Corte equivalente: mesmo percentil do universo que o corte original ocupa no Wise."""
    q = (wise_vals.dropna() < wise_cut).mean()
    return float(np.nanquantile(hyb_vals.dropna(), q))


def run(h, w, growth='G1', zg='Z1', ret='R1', recal=False):
    d = h.copy()
    if growth == 'G2':
        d['growth'] = d[['f0', 'f1']].apply(lambda r: engine.growth_metric(list(r)), axis=1)
    if zg == 'Z2':
        d['zgrowth'] = [engine.cv([a, b], g) for a, b, g in zip(d.f0, d.f1, d.growth)]
    elif zg == 'Z5':  # dispersao das estimativas dos analistas (+1y)
        d['zgrowth'] = d.disp1
    d['g'] = engine.block_g(d)
    d['fair_pe'] = engine.fair_pe(d.g, d.roic)
    eps2 = d.eps_1 * (1 + d.f1)
    base = d.fair_pe * eps2 / d.price
    d['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + d.dy
    const = {'R1': np.sqrt((d.eps_1 / d.eps_m1).clip(lower=0)) - 1, 'R4': d.f1}.get(ret, np.nan)
    d['ret_const'] = const + d.dy if ret != 'R5' else np.nan
    fb = d[['f0', 'f1']].mean(axis=1)
    if ret == 'R5':
        d['ret'] = d.ret_fair.fillna(fb)
    else:
        both = d.ret_fair.notna() & d.ret_const.notna()
        d['ret'] = np.where(both, (d.ret_fair + d.ret_const) / 2, fb)
    th = dict(engine.TH)
    if recal:  # recalibra apenas os cortes de dispersao (zGrowth), cuja escala muda com a fonte
        engine.TH['zGrowth'] = quantile_cut(w.zgrowth, d.zgrowth, th['zGrowth'])
    out = engine.classify(d)
    used = dict(engine.TH)
    engine.TH.clear(); engine.TH.update(th)
    return out, used


def summary(out, w):
    same = (out.category.values == w.category.values)
    tw, th = w.category.map(TIERS).values, out.category.map(TIERS).values
    ow, oh = w.category.values == 'Opportunity of Lifetime', out.category.values == 'Opportunity of Lifetime'
    aw, ah = tw == 'A', th == 'A'
    return dict(classe=same.mean(), tier=(tw == th).mean(), OoL_comum=int((ow & oh).sum()), OoL_h=int(oh.sum()),
                A_comum=int((aw & ah).sum()), A_h=int(ah.sum()))


def main(day):
    w = wise_baseline().set_index('row')
    h = pd.read_csv(f'data/hybrid_{day}.csv').set_index('row').loc[w.index]
    print(f"Wise: OoL={int((w.category=='Opportunity of Lifetime').sum())}, tier A={int(w.category.map(TIERS).eq('A').sum())}\n")
    res = []
    for g, z, r, rc in itertools.product(['G1', 'G2'], ['Z1', 'Z2', 'Z5'], ['R1', 'R4', 'R5'], [False, True]):
        out, used = run(h, w, g, z, r, rc)
        res.append(dict(growth=g, zg=z, ret=r, recal=rc, zcut=round(used['zGrowth'], 3), **summary(out, w)))
    df = pd.DataFrame(res).sort_values(['tier', 'classe'], ascending=False)
    pd.set_option('display.width', 200)
    print(df.head(12).to_string(index=False, float_format='{:.0%}'.format))
    print('\nbase (G1 Z1 R1 sem recal):')
    print(df[(df.growth == 'G1') & (df.zg == 'Z1') & (df.ret == 'R1') & ~df.recal].to_string(index=False, float_format='{:.0%}'.format))
    df.to_csv(f'data/experiments_{day}.csv', index=False)


if __name__ == '__main__':
    main(sys.argv[1])
