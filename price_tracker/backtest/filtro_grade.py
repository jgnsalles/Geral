"""Das acoes que o filtro (P/L < 6 ou lucro +150% no ultimo ano) tirou da Top 20: quais foi bom tirar e quais foi ruim, e uma grade de cortes.
EUA e Brasil. Exploratorio (feito olhando os erros). Saida: backtest/filtro_grade.md. Uso: python3 backtest/filtro_grade.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import benchmarks as bm, top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats, D  # noqa: E402
import oos_congelado as oc  # noqa: E402

pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
pp = lambda v: '—' if pd.isna(v) else f'{v * 100:+.1f}'.replace('.', ',')

# ---------- EUA
f, dates = bm.base_data(); adj = bm.load_prices()['adj_close']; c = bm.classify_new(f)
el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & c.roic.notna() & c.growth.notna()].copy()
el['mcap'] = top_n.mcap_us(c, el); el['pe'] = el.price / el.eps.where(el.eps > 0); el['glast'] = el.gy5
# ---------- Brasil
BD = ROOT.parent / 'brasil' / 'data'
u = pd.read_csv(BD / 'universe.csv'); sec = u.set_index('yf').Setor_Atividade; tkr = u.set_index('yf').ticker; cvm = u.set_index('yf').Codigo_CVM
b = pd.read_csv(BD / 'classes_pit.csv', parse_dates=['date'])
r = b.roic.clip(upper=1.0); b['fair_pe'] = np.where(r > 0, (1 - b.g / r) / (0.12 - b.g), np.nan)
base = b.fair_pe * b.eps * (1 + b.growth) ** 2 / b.price
b['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + b.dy; b['ret_const'] = b.growth + b.dy
both = b.ret_fair.notna() & b.ret_const.notna(); b['ret'] = np.where(both, (b.ret_fair + b.ret_const) / 2, b.growth)
adjb = pd.read_csv(BD / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
cov = b.groupby('date')['cat_zg2.93'].apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
bd = sorted(d for d in b.date.unique() if d >= start); b = b[b.date.isin(bd)].copy()
cyc = b.ticker.map(sec).isin(oc.CYC_SECTORS) | b.ticker.map(tkr).isin(oc.CYC_TICKERS); app = b.ticker.map(tkr).isin(oc.APPAREL)
fund = pd.read_csv(BD / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
elb = b[~cyc & ~app & (b.roic >= .12) & (b.growth >= .15) & b['cat_zg2.93'].notna()].copy()
sh, gl = [], []
for rr in elb.itertuples():
    ff = fund[(fund.CD_CVM == cvm.get(rr.ticker)) & (fund.DT_RECEB <= rr.date)].sort_values('DT_RECEB').groupby('fy').tail(1).set_index('fy')
    y = int(rr.last_fy); ni = ff.ni
    sh.append(ni.get(y) / rr.eps if pd.notna(ni.get(y)) and rr.eps and abs(rr.eps) > 1e-6 and np.sign(ni.get(y)) == np.sign(rr.eps) else np.nan)
    gl.append(ni.get(y) / ni.get(y - 1) - 1 if pd.notna(ni.get(y)) and pd.notna(ni.get(y - 1)) and ni.get(y - 1) > 0 else np.nan)
elb['sh'] = sh; elb['sh'] = elb.groupby('ticker').sh.transform(lambda s: s.ffill().bfill()); elb['glast'] = gl
elb['mcap'] = (elb.price * elb.sh).where(lambda s: s > 0); elb['mcap'] = elb.mcap.fillna(elb.groupby('date').mcap.transform('median'))
elb['pe'] = elb.price / elb.eps.where(elb.eps > 0)

def port(E, A, ds, pe_min, g_max):
    m = pd.Series(True, index=E.index)
    if pe_min: m &= ~(E.pe < pe_min)
    if g_max: m &= ~(E.glast > g_max)
    x = E[m]
    ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(20) for _, g in x.groupby('date')])
    w = {d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), 0.1) for d, g in ch.groupby('date')}
    return run_weighted(w, A, ds), ch

def removed(E, A, ds, pe_min, g_max):
    """posicoes que estariam na Top 20 sem filtro e saem com o filtro; retorno do trimestre seguinte vs indice."""
    _, ch0 = port(E, A, ds, None, None)
    px = A.reindex(pd.DatetimeIndex(ds), method='ffill'); fwd = px.shift(-1) / px - 1
    ch0 = ch0[ch0.date < ds[-1]].copy(); ch0['r'] = [fwd.at[d, t] for d, t in zip(ch0.date, ch0.ticker)]
    ch0['out_pe'] = ch0.pe < pe_min; ch0['out_g'] = ch0.glast > g_max
    return ch0, fwd

out = ['# Filtro de P/L baixo e lucro explosivo: quem foi bom tirar e a grade de cortes (EUA e Brasil)\n',
       '> ⚠️ O ROIC pode estar errado. **Exploratório:** feito olhando os próprios erros; um corte que só funciona num país é provável sobreajuste.\n']
for lab, E, A, ds, bench in (('EUA', el, adj, dates, 'SPY'), ('Brasil', elb, adjb, bd, 'BOVA11.SA')):
    ch0, fwd = removed(E, A, ds, 6, 1.5)
    ch0['ex'] = ch0.r - ch0.date.map(fwd[bench])
    rm = ch0[ch0.out_pe | ch0.out_g]
    out += [f'## {lab}: as posições que o filtro (P/L < 6 ou lucro +150% no último ano) tira\n',
            f'{len(rm)} de {len(ch0)} posições ({len(rm) / len(ch0):.0%}). "Bom tirar" = rendeu menos que o índice no trimestre seguinte.\n',
            '| Motivo | Posições | Bom tirar | Ruim tirar | Excesso médio do trimestre (a.a.) |', '|---|---|---|---|---|']
    for why, m in (('P/L < 6', rm.out_pe & ~rm.out_g), ('Lucro +150% no último ano', rm.out_g & ~rm.out_pe), ('Os dois', rm.out_pe & rm.out_g)):
        x = rm[m]
        if len(x): out.append(f'| {why} | {len(x)} | {(x.ex < 0).sum()} | {(x.ex >= 0).sum()} | {pp(x.ex.mean() * 4)} |')
    out += ['', '**Por faixa de P/L (todas as posições da Top 20 sem filtro):**\n', '| P/L | Posições | % que perdeu do índice | Excesso médio (a.a.) |', '|---|---|---|---|']
    for a, bb, l in ((0, 4, 'abaixo de 4'), (4, 6, '4 a 6'), (6, 8, '6 a 8'), (8, 12, '8 a 12'), (12, 999, 'acima de 12')):
        x = ch0[(ch0.pe >= a) & (ch0.pe < bb)]
        if len(x): out.append(f'| {l} | {len(x)} | {(x.ex < 0).mean():.0%} | {pp(x.ex.mean() * 4)} |')
    out += ['', '**Por crescimento do lucro no último ano:**\n', '| Crescimento | Posições | % que perdeu do índice | Excesso médio (a.a.) |', '|---|---|---|---|']
    for a, bb, l in ((-9, 1, 'até 100%'), (1, 1.5, '100–150%'), (1.5, 2, '150–200%'), (2, 3, '200–300%'), (3, 99, 'acima de 300%')):
        x = ch0[(ch0.glast >= a) & (ch0.glast < bb)]
        if len(x): out.append(f'| {l} | {len(x)} | {(x.ex < 0).mean():.0%} | {pp(x.ex.mean() * 4)} |')
    good = rm[rm.ex < 0].groupby('ticker').agg(n=('ex', 'size'), ex=('ex', 'mean'), pe=('pe', 'median'), g=('glast', 'median')).sort_values('ex').head(8)
    bad = rm[rm.ex >= 0].groupby('ticker').agg(n=('ex', 'size'), ex=('ex', 'mean'), pe=('pe', 'median'), g=('glast', 'median')).sort_values('ex', ascending=False).head(8)
    fmt = lambda d: ', '.join(f"{t} (P/L {r.pe:.0f}, lucro {r.g:+.0%}, {pp(r.ex * 4)})".replace('nan', '—') for t, r in d.iterrows())
    out += ['', f'**Bom ter tirado:** {fmt(good)}', '', f'**Ruim ter tirado:** {fmt(bad)}', '']
    # grade
    idx = stats(A[bench].loc[ds[0]:ds[-1]].dropna() / A[bench].loc[ds[0]:ds[-1]].dropna().iloc[0])['CAGR']
    out += [f'### Grade de cortes ({lab}) — retorno anual da Top 20 (índice {pc(idx)})\n',
            '| P/L mínimo \\ crescimento máximo no último ano | sem corte | 300% | 200% | 150% | 100% |', '|---|---|---|---|---|---|']
    for pe_min in (None, 3, 4, 5, 6, 8):
        row = [('sem corte' if pe_min is None else f'P/L ≥ {pe_min}')]
        for g_max in (None, 3.0, 2.0, 1.5, 1.0):
            nav, _ = port(E, A, ds, pe_min, g_max); row.append(pc(stats(nav)['CAGR']))
        out.append('| ' + ' | '.join(row) + ' |'); print(lab, pe_min, flush=True)
    out.append('')
(ROOT / 'filtro_grade.md').write_text('\n'.join(out)); print('\n'.join(out))
