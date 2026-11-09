"""Modelo hibrido: historico (SEC quando houver, senao Yahoo) + 2 anos projetados do Yahoo.
Le os snapshots congelados em data/raw/<fonte>/<data>/ e grava data/hybrid_<data>.csv.
Uso: python3 hybrid.py 2026-11-09"""
import sys, json, pathlib
import numpy as np, pandas as pd
import engine

YEARS = [2019, 2021, 2022, 2023, 2024, 2025]  # mesmos anos de ROIC da planilha
BASE_YEAR = 2026                              # equivale ao YEAR(TODAY()) fixado


def fy(end):
    """Ano fiscal no padrao da planilha: exercicio que fecha ate marco conta como ano anterior."""
    t = pd.Timestamp(end)
    return t.year if t.month > 3 else t.year - 1


def num(x):
    try:
        x = float(x)
        return x if np.isfinite(x) else np.nan
    except (TypeError, ValueError):
        return np.nan


def ratio(a, b):
    a, b = num(a), num(b)
    return a / b - 1 if np.isfinite(a) and np.isfinite(b) and b > 0 else np.nan


def by_year(d):
    return {fy(k): num(v) for k, v in (d or {}).items() if np.isfinite(num(v))}


def edgar_series(e, key):
    x = (e or {}).get('data', {}).get(key)
    return by_year(x['values']) if x else {}


def roic_years(y, e, roe_mode=False):
    """ROIC por ano = NOPAT / (Ativo total - Passivo circulante), definicao calibrada contra o Wisesheets."""
    src, out = {}, {}
    ed = {k: edgar_series(e, k) for k in ('op_income', 'pretax', 'tax', 'assets', 'cur_liab')}
    inc, bal = y.get('income', {}), y.get('balance', {})
    yh = {
        'op_income': by_year(inc.get('Operating Income') or inc.get('EBIT')),
        'pretax': by_year(inc.get('Pretax Income')), 'tax': by_year(inc.get('Tax Provision')),
        'assets': by_year(bal.get('Total Assets')), 'cur_liab': by_year(bal.get('Current Liabilities')),
    }
    # setor financeiro: o Wisesheets usa ROE (lucro liquido / patrimonio) -- confirmado contra os valores dele
    ed['net_income'], ed['equity'] = edgar_series(e, 'net_income'), edgar_series(e, 'equity')
    yh['net_income'] = by_year(inc.get('Net Income'))
    yh['equity'] = by_year(bal.get('Stockholders Equity'))
    no_cl = roe_mode or (not ed['cur_liab'] and not yh['cur_liab'])
    for yr in YEARS:
        for name, s in (('sec', ed), ('yahoo', yh)):
            if no_cl and yr in s['net_income'] and s['equity'].get(yr, 0) > 0:
                out[yr] = s['net_income'][yr] / s['equity'][yr]
                src[yr] = name + '-roe'
                break
            if all(yr in s[k] for k in ('op_income', 'assets', 'cur_liab')):
                pt, tx = s['pretax'].get(yr), s['tax'].get(yr)
                t = min(max(tx / pt, 0), 0.5) if pt and tx is not None and pt > 0 else 0.21
                ic = s['assets'][yr] - s['cur_liab'][yr]
                if ic > 0:
                    out[yr] = s['op_income'][yr] * (1 - t) / ic
                    src[yr] = name
                break
    return out, src


def eps_history(y, e):
    """EPS diluido realizado (GAAP) por ano fiscal: SEC se houver, senao Yahoo."""
    s = edgar_series(e, 'eps_diluted')
    if len(s) >= 3:
        return s, 'sec'
    return by_year(y.get('income', {}).get('Diluted EPS')), 'yahoo'


def build_row(w, y, e, fx=None):
    info, est = y.get('info', {}), y.get('earnings_estimate', {})
    price = num(info.get('currentPrice')) if np.isfinite(num(info.get('currentPrice'))) else num(info.get('regularMarketPrice'))
    e_m1 = num(est.get('0y', {}).get('yearAgoEps'))
    e_0, e_1 = num(est.get('0y', {}).get('avg')), num(est.get('+1y', {}).get('avg'))
    lo1, hi1 = num(est.get('+1y', {}).get('low')), num(est.get('+1y', {}).get('high'))
    disp1 = (hi1 - lo1) / abs(e_1) if np.isfinite(e_1) and e_1 != 0 else np.nan
    est_ccy = est.get('0y', {}).get('currency')
    flags = []
    if est_ccy and info.get('currency') and est_ccy != info.get('currency'):
        rate = num((fx or {}).get(f'{est_ccy}{info.get("currency")}'))
        if np.isfinite(rate):
            e_m1, e_0, e_1 = e_m1 * rate, e_0 * rate, e_1 * rate  # converte EPS para a moeda do preco
            flags.append(f'EPS convertido {est_ccy}->{info.get("currency")} @ {rate:.4f}')
        else:
            flags.append(f'moeda EPS {est_ccy} != preco {info.get("currency")}')
    if not np.isfinite(e_0) or not np.isfinite(e_1):
        flags.append('sem estimativa Yahoo')

    hist, hsrc = eps_history(y, e)
    last_fy = fy(pd.Timestamp(info['lastFiscalYearEnd'], unit='s')) if num(info.get('lastFiscalYearEnd')) == num(info.get('lastFiscalYearEnd')) and info.get('lastFiscalYearEnd') else max(hist, default=np.nan)
    a = [hist.get(last_fy - 2), hist.get(last_fy - 1), hist.get(last_fy)]
    if np.isfinite(num(a[2])) and np.isfinite(e_m1) and e_m1 > 0 and not 0.6 < a[2] / e_m1 < 1.6:
        flags.append(f'EPS realizado {a[2]:.2f} vs base da estimativa {e_m1:.2f}')
    gr = [ratio(a[1], a[0]), ratio(a[2], a[1]), ratio(e_0, e_m1), ratio(e_1, e_0)]

    growth = engine.growth_metric(gr)
    zgrowth = engine.cv(gr, growth)
    ry, rsrc = roic_years(y, e, roe_mode=(w.get('sector') == 'Financial Services'))
    roic = engine.roic_metric([ry.get(k) for k in YEARS])
    zroic = engine.cv([ry.get(k) for k in YEARS], roic)

    divs = y.get('dividends_by_year') or {}
    dy = np.nanmean([num(divs.get(str(BASE_YEAR - 2), 0)) / price, num(divs.get(str(BASE_YEAR - 1), 0)) / price]) if price > 0 else np.nan
    if any(f.startswith('moeda') for f in flags):
        dy = np.nan  # dividendos podem estar na moeda do EPS
    return dict(
        row=w['row'], ticker=w['ticker'], fin=w['fin'], price=price, currency=info.get('currency'),
        eps_m1=e_m1, eps_0=e_0, eps_1=e_1, disp1=disp1, n_analysts=num(est.get('+1y', {}).get('numberOfAnalysts')), eps_src=hsrc, a_m2=a[0], a_m1=a[1], a_0=a[2],
        h1=gr[0], h2=gr[1], f0=gr[2], f1=gr[3], growth=growth, zgrowth=zgrowth,
        **{f'roic{k}': ry.get(k) for k in YEARS}, roic=roic, zroic=zroic,
        roic_n=len(ry), roic_src=','.join(sorted(set(rsrc.values()))), dy=dy, flags='; '.join(flags))


# Configuracao escolhida no teste controlado (experiments.py, 2026-11-09):
#  - Growth e zGrowth so com os 2 anos projetados (o historico GAAP misturado com estimativa ajustada distorce)
#  - zGrowth com 2 pontos tem outra escala: corte recalibrado por percentil (0,9 no Wise -> 0,49 aqui)
#  - Retorno "multiplo constante" = crescimento do EPS no ano +1 (+ dividend yield)
ZGROWTH_CUT = 0.49


def finish(df):
    df['growth_mixed'], df['zgrowth_mixed'] = df['growth'], df['zgrowth']
    df['growth'] = [engine.growth_metric([a, b]) for a, b in zip(df.f0, df.f1)]
    df['zgrowth'] = [engine.cv([a, b], g) for a, b, g in zip(df.f0, df.f1, df.growth)]
    df['g'] = engine.block_g(df)
    df['fair_pe'] = engine.fair_pe(df.g, df.roic)
    eps2 = df.eps_1 * (1 + df.f1)                         # extrapola 1 ano com o ultimo crescimento projetado
    base = df.fair_pe * eps2 / df.price
    df['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + df.dy
    df['ret_const'] = df.f1 + df.dy
    fallback = df[['f0', 'f1']].mean(axis=1)              # AGGREGATE(1,6,R:S)
    both = df.ret_fair.notna() & df.ret_const.notna()
    df['ret'] = np.where(both, (df.ret_fair + df.ret_const) / 2, fallback)
    saved = engine.TH['zGrowth']
    engine.TH['zGrowth'] = ZGROWTH_CUT
    try:
        return engine.classify(df)
    finally:
        engine.TH['zGrowth'] = saved


def main(day):
    w = pd.read_csv('data/wise_snapshot.csv')
    fxf = pathlib.Path(f'data/raw/yahoo/{day}/_fx.json')
    fx = json.loads(fxf.read_text()) if fxf.exists() else {}
    rows = []
    for _, r in w.iterrows():
        yf = pathlib.Path(f'data/raw/yahoo/{day}/{r.ticker}.json')
        ef = pathlib.Path(f'data/raw/edgar/{day}/{r.ticker}.json')
        y = json.loads(yf.read_text()) if yf.exists() else {}
        e = json.loads(ef.read_text()) if ef.exists() else None
        rows.append(build_row(r, y, e, fx) if y else dict(row=r.row, ticker=r.ticker, fin=r.fin, flags='sem dados Yahoo'))
    df = finish(pd.DataFrame(rows))
    out = f'data/hybrid_{day}.csv'
    df.to_csv(out, index=False)
    print(out, len(df), df.category.value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1])
