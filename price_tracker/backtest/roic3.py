"""ROIC triangulado (pre-registrado em 2026-11-14, ver PROTOCOLO.md): visoes do ativo, do passivo e marginal + regra de 'arte' do usuario.
Saida: backtest/data/roic3.csv (uma linha por acao e data do universo point-in-time). Uso: python3 backtest/roic3.py"""
import sys, json, gzip, pathlib
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import load_pit, asof, D  # noqa: E402

BASE = ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income', 'ppe', 'assets_cur', 'cur_liab', 'debt_cur', 'goodwill', 'intangibles')


def load_pit2(tk):
    f = D / 'pit2' / f'{tk}.json.gz'
    if not f.exists(): return {}
    raw = json.load(gzip.open(f, 'rt')); out = {}
    for key, cands in raw.items():
        cs = []
        for c in cands:
            df = pd.DataFrame(c['rows'], columns=['end', 'val', 'filed']); df['end'] = pd.to_datetime(df.end); df['filed'] = pd.to_datetime(df.filed)
            cs.append((c['concept'], c['unit'], df.sort_values('filed')))
        out[key] = cs
    return out


def pv_leases(v, r=0.05):
    ys = [v.get(f'fl_y{i}') for i in range(1, 6)]
    if all(x is None for x in ys): return None
    ys = [x or 0.0 for x in ys]; pv = sum(x / (1 + r) ** (i + 1) for i, x in enumerate(ys))
    after = v.get('fl_after') or 0.0; avg = np.mean([x for x in ys if x > 0]) if any(x > 0 for x in ys) else 0
    if after > 0 and avg > 0:
        n = int(min(max(round(after / avg), 1), 15)); ann = after / n
        pv += sum(ann / (1 + r) ** (6 + i) for i in range(n))
    return pv


def year_vals(s, y):
    g = lambda k: s[k][y][0] if k in s and y in s[k] else None
    v = {k: g(k) for k in s}
    return v


def combine(a, p, m):
    ok = lambda x: x is not None and np.isfinite(x) and 0 <= x <= 2.0
    cl = lambda x: min(x, 1.5)
    va, vp_ = ok(a), ok(p)
    if va and vp_:
        lo, hi = sorted([cl(a), cl(p)])
        if lo > 0 and hi <= 2 * lo: return (cl(a) + cl(p)) / 2, 'média ativo e passivo'
        if ok(m): return (cl(a) if abs(cl(a) - m) <= abs(cl(p) - m) else cl(p)), 'divergem: a mais próxima do marginal'
        return lo, 'divergem: a menor'
    if va: return cl(a), 'só o ativo válido'
    if vp_: return cl(p), 'só o passivo válido'
    if any(x is not None and np.isfinite(x) and x > 2.0 for x in (a, p)): return 1.5, 'acima de 200%: 150%'
    if ok(m): return cl(m), 'só o marginal'
    return np.nan, 'sem ROIC'


def one(args):
    tk, fin, dates = args
    pit = load_pit(tk); pit2 = load_pit2(tk)
    if pit is None: return []
    rows = []
    for t in dates:
        if fin: continue
        s = {k: asof(pit.get(k, []), t)[0] for k in BASE}
        s.update({k: asof(c, t)[0] for k, c in pit2.items()})
        if not s['op_income']: continue
        last = max(s['op_income'])
        Y = list(range(last - 11, last + 1))
        V = {y: year_vals(s, y) for y in Y}
        ast, pas, nop, wc = {}, {}, {}, {}
        for y in Y:
            v = V[y]; oi = v.get('op_income')
            if oi is None: continue
            pt, tx = v.get('pretax'), v.get('tax'); tr = min(max(tx / pt, 0), .5) if pt and tx is not None and pt > 0 else .21
            ll = v.get('lease_liab')
            if ll is None and (v.get('lease_liab_cur') is not None or v.get('lease_liab_nc') is not None): ll = (v.get('lease_liab_cur') or 0) + (v.get('lease_liab_nc') or 0)
            pre = False
            if ll is None: ll = pv_leases(v); pre = ll is not None
            rou = v.get('rou') if v.get('rou') is not None else (ll if pre else None)
            rate = v.get('lease_rate'); rate = (rate / 100 if rate and rate > 1 else rate) if rate else .05
            nop[y] = oi * (1 - tr) + ((ll or 0) * rate + (v.get('eq_income') or 0)) * (1 - tr)
            it = v.get('intang_tot')
            if it is None and (v.get('intang_fin') is not None or v.get('intang_indef') is not None): it = (v.get('intang_fin') or 0) + (v.get('intang_indef') or 0)
            if it is None: it = v.get('intangibles')
            gw = v.get('goodwill')
            if gw is None and v.get('intang_incl_gw') is not None: gw, it = v['intang_incl_gw'], 0
            ppe = max([x for x in (v.get('ppe'), v.get('ppe_og')) if x is not None], default=None)
            ac, cl_, cash = v.get('assets_cur'), v.get('cur_liab'), v.get('cash') or 0
            sti = v.get('st_inv') or 0
            if ac is not None and cl_ is not None:
                wc[y] = (ac - cash - sti) - (cl_ - (v.get('debt_cur') or 0) - (v.get('lease_liab_cur') or 0))
            if ppe is not None and y in wc:
                ast[y] = ppe + (rou or 0) + (gw or 0) + (it or 0) + (v.get('lt_inv') or 0) + wc[y]
            eq = v.get('equity')
            if eq is not None:
                if v.get('ltd_tot') is not None: debt = v['ltd_tot'] + (v.get('st_borr') or 0)
                elif v.get('ltd_nc') is not None or v.get('ltd_cur') is not None: debt = (v.get('ltd_nc') or 0) + (v.get('ltd_cur') or 0) + (v.get('st_borr') or 0)
                else: debt = (v.get('lt_debt') or 0) + (v.get('debt_cur') or 0)
                pas[y] = eq + (v.get('minority') or 0) + debt + (ll or 0) - cash - sti
        def series(cap):
            out = []
            for y in range(last - 5, last + 1):
                c0, c1 = cap.get(y), cap.get(y - 1)
                c = (c0 + c1) / 2 if c0 is not None and c1 is not None else c0
                out.append(nop[y] / c if y in nop and c is not None and c > 0 else np.nan)
            return out
        ra, rp = series(ast), series(pas)
        a = engine.roic_metric(ra); p = engine.roic_metric(rp)
        reinv = []
        for y in range(last - 5, last):
            v = V[y]
            if v.get('capex') is None or v.get('da') is None or y not in wc or y - 1 not in wc: continue
            reinv.append(v['capex'] - v['da'] + (v.get('acq') or 0) + (wc[y] - wc[y - 1]))
        reinv = [np.mean(reinv)] * 5 if len(reinv) >= 3 else None  # ano sem dado: completa com a media dos anos com dado (minimo 3 de 5)
        m = np.nan; alert = False
        if reinv is not None and last in nop and last - 5 in nop:
            R = sum(reinv)
            if R > 0: m = (nop[last] - nop[last - 5]) / R
            capl = ast.get(last) or pas.get(last)
            alert = bool(capl and capl > 0 and np.isfinite(m) and m < .12 and R < .10 * capl)
        tri, rule = combine(a, p, m)
        rows.append(dict(date=t, ticker=tk, roic_ativo=a, roic_passivo=p, roic_marg=m, roic_tri=tri, regra=rule, alerta_qualidade=alert,
                         ativo_last=ast.get(last), passivo_last=pas.get(last), nopat_last=nop.get(last), last_fy=last))
    return rows


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'], usecols=['date', 'ticker', 'fin', 'pit_member'])
    f = f[f.pit_member]
    jobs = [(t, bool(g.fin.iloc[0]), sorted(g.date.unique())) for t, g in f.groupby('ticker')]
    jobs = [(t, fn, [pd.Timestamp(d) for d in ds]) for t, fn, ds in jobs]
    with Pool(4) as pool:
        res = pool.map(one, jobs, chunksize=4)
    out = pd.DataFrame([r for rr in res for r in rr]); out.to_csv(D / 'roic3.csv', index=False); print(out.shape)
    print(out.regra.value_counts(normalize=True))


if __name__ == '__main__':
    main()
