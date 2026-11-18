"""Ramo C (2026-11-18, pré-registrado no PROTOCOLO): os gestores do "Navegando US" definem o universo (S&P 500 + médias e pequenas, ≥ US$ 2 bi),
e por cima vêm os filtros registrados e a seleção pelo desconto ao P/E justo ("ROIC alto descontado") ou pelo retorno esperado (Top 20). N = 1, 3, 5 gestores.
Entrada: relatorio/data_13f/posicoes.csv.gz. Saída: relatorio/dados_gestores_amplo.json e relatorio/gestores_amplo_tabela.md.
Uso: python3 relatorio/ramo_gestores_amplo.py"""
import sys, json, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import calc2, top_n  # noqa: E402
import combos as cb  # noqa: E402
import benchmarks as bm  # noqa: E402
from pesos import run_weighted, DUAL  # noqa: E402
from backtest import stats  # noqa: E402

firm = lambda t: DUAL.get(t, t)
c, adj_sp, dates, ref, nm_sp = calc2.sp_data()
n, adj_ms, dates_ms, iwm, nm_ms = calc2.ms_data()
D = pd.DatetimeIndex(dates)
D0 = D[D >= pd.Timestamp('2016-06-30')][0]
DS = [d for d in dates if pd.Timestamp(d) >= D0]
iq = {d: i for i, d in enumerate(D)}
adj = pd.concat([adj_sp, adj_ms[[k for k in adj_ms.columns if k not in adj_sp.columns]]], axis=1).sort_index()
A = adj.reindex(D, method='ffill')
nm = lambda t: nm_sp(t) if t in set(c.ticker) else nm_ms(t)
OUT = {'periodo': [str(D0.date()), str(D[-1].date())]}

# ---------------- painel combinado ----------------
cols = ['date', 'ticker', 'fin', 'util', 'excluded', 'price', 'eps', 'pe', 'roic', 'growth', 'zgrowth', 'dy', 'mcap', 'fair_pe', 'ret']
sp = c[c.date >= D0].copy()
miss = sp.mcap.isna()
sp.loc[miss, 'mcap'] = top_n.mcap_us(sp, sp[miss])
sp['in_sp'] = True
ms = n[n.date >= D0].copy(); ms['in_sp'] = False
sp_keys = set(zip(sp.date, sp.ticker))
ms = ms[[(d, t) not in sp_keys for d, t in zip(ms.date, ms.ticker)]]
U = pd.concat([sp[cols + ['in_sp']], ms[cols + ['in_sp']]], ignore_index=True)
U = U[U.date.isin(DS)].copy()
U['firm'] = U.ticker.map(firm)
# g, P/E justo e retorno esperado recalculados no universo combinado (fórmula registrada)
parts = []
for d, x in U.groupby('date'):
    x = x.copy(); x['g2'] = cb.g_rank(x, 0.07)
    r = x.roic.clip(upper=1.0)
    x['fpe2'] = np.where(r > 0, (1 - x.g2 / r) / (0.085 - x.g2), np.nan)
    base = x.fpe2 * x.eps * (1 + x.growth) ** 2 / x.price
    rf = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
    rc = x.growth + x.dy
    both = pd.Series(rf, index=x.index).notna() & rc.notna()
    x['ret2'] = np.where(both, (rf + rc) / 2, x.growth)
    parts.append(x)
U = pd.concat(parts)
U['gap2'] = np.where((U.fpe2 > 0) & (U.pe > 0), np.log(U.fpe2 / U.pe), np.nan)
U['gap'] = np.where((U.fair_pe > 0) & (U.pe > 0), np.log(U.fair_pe / U.pe), np.nan)   # versão só-S&P (g ranqueado no S&P), como no ramo B

# ---------------- gestores (13F do trimestre anterior) ----------------
x13 = pd.read_csv(ROOT / 'data_13f' / 'posicoes.csv.gz')
x13['firm'] = x13.ticker.map(lambda t: firm(t) if isinstance(t, str) else t)
cnt = x13.dropna(subset=['ticker']).groupby(['trimestre', 'firm']).gestor.nunique()


def prev_q(d):
    q = pd.Timestamp(d) - pd.offsets.QuarterEnd(1)
    return f'{q.year}-{q.month:02d}'


U['q13f'] = U.date.map(prev_q)
U['ng'] = [cnt.get((q, f), 0) for q, f in zip(U.q13f, U.firm)]

# cobertura: do valor das posições, quanto caiu no painel combinado (na data que usa aquele 13F)
q2d = {prev_q(d): d for d in DS}
cov = []
for q, g in x13[x13.trimestre.isin(q2d)].groupby('trimestre'):
    d = q2d[q]; u = U[U.date == d]; fs = set(u.firm); fs2 = set(u[u.mcap >= 2e9].firm)
    tot = g.valor.sum(); notk = g[g.ticker.isna()].valor.sum()
    inp = g[g.firm.isin(fs)].valor.sum(); in2 = g[g.firm.isin(fs2)].valor.sum()
    cov.append(dict(q=q, sem_ticker=notk / tot, no_painel=inp / tot, no_painel_2bi=in2 / tot, fora=(tot - notk - inp) / tot))
cv = pd.DataFrame(cov)
OUT['cobertura'] = {k: float(cv[k].mean()) for k in ('sem_ticker', 'no_painel', 'no_painel_2bi', 'fora')}
fora = x13[x13.trimestre.isin(q2d) & x13.ticker.notna()].copy()
fora['in'] = [f in set(U[U.date == q2d[q]].firm) for q, f in zip(fora.trimestre, fora.firm)]
top_out = fora[~fora['in']].groupby('ticker').valor.sum().sort_values(ascending=False).head(15)
OUT['fora_exemplos'] = [[t, float(v / fora.valor.sum())] for t, v in top_out.items()]
OUT['universo'] = {str(N): float(U[(U.ng >= N) & (U.mcap >= 2e9)].groupby('date').size().mean()) for N in (1, 3, 5)}
OUT['universo_fora_sp'] = {str(N): float((~U[(U.ng >= N) & (U.mcap >= 2e9)].in_sp).mean()) for N in (1, 3, 5)}
print('cobertura', OUT['cobertura'], OUT['universo'], flush=True)

# ---------------- futuro (decomposição) ----------------
U['qi'] = U.date.map(iq)
key = U.drop_duplicates(['qi', 'ticker']).set_index(['qi', 'ticker'])
for h in (4, 12):
    f = key[['eps', 'pe']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'{v}_{h}' for v in f.columns]
    U = U.join(f, on=['qi', 'ticker'])
    tr = [A.at[D[iq[d] + h], t] / A.at[d, t] if iq[d] + h < len(D) and t in A and A.at[d, t] > 0 else np.nan for d, t in zip(U.date, U.ticker)]
    U[f'lt_{h}'] = np.log(np.array(tr, dtype=float))
    ok = (U.eps > 0) & (U[f'eps_{h}'] > 0)
    U[f'le_{h}'] = np.where(ok, np.log(U[f'eps_{h}'] / U.eps), np.nan)
    U[f'lp_{h}'] = np.where(ok, np.log(U[f'pe_{h}'] / U.pe), np.nan)
    U[f'ld_{h}'] = U[f'lt_{h}'] - U[f'le_{h}'] - U[f'lp_{h}']
ann = lambda v, h: float(np.expm1(v * 4 / h))


# ---------------- carteiras ----------------
def pick(df, sort, n=20):
    df = calc2.dd_firm(df)
    return {d: g.sort_values(sort, ascending=False).head(n) for d, g in df.groupby('date')}


liq = U.mcap >= 2e9
okq = ~U.excluded & (U.roic >= .12) & (U.pe > 0)
complete = U[['growth', 'zgrowth', 'roic']].notna().all(axis=1)
B2 = U[liq & okq & U.gap2.notna()]                                        # universo amplo
T2 = U[liq & okq & complete & U.ret2.notna() & (U.growth >= .15) & (U.pe >= 4)]
SPb = U[U.in_sp & okq & U.gap.notna() & U.mcap.notna()]                  # só S&P (como o ramo B)
SPt = U[U.in_sp & okq & complete & U.ret.notna() & (U.growth >= .15) & (U.pe >= 4) & U.mcap.notna()]
SEL = {
    'ROIC alto descontado · S&P (original)': pick(SPb, ['gap', 'roic']),
    'ROIC alto descontado · S&P, ≥ 3 gestores': pick(SPb[SPb.ng >= 3], ['gap', 'roic']),
    'Top 20 · S&P (original)': pick(SPt, ['ret', 'roic']),
    'Top 20 · S&P, ≥ 3 gestores': pick(SPt[SPt.ng >= 3], ['ret', 'roic']),
}
for N in (1, 3, 5):
    SEL[f'ROIC alto descontado · amplo, ≥ {N} gestor{"es" if N > 1 else ""}'] = pick(B2[B2.ng >= N], ['gap2', 'roic'])
    SEL[f'Top 20 · amplo, ≥ {N} gestor{"es" if N > 1 else ""}'] = pick(T2[T2.ng >= N], ['ret2', 'roic'])
NEW = [k for k in SEL if 'amplo' in k]
Wn = {k: {d: calc2.cap_w(g) for d, g in v.items()} for k, v in SEL.items()}
We = {k: {d: pd.Series(1 / len(g), index=g.ticker) for d, g in v.items()} for k, v in SEL.items()}
navs9, n9, _, _ = bm.load_benchmarks()
rebase = lambda s: (s.loc[D0:] / s.loc[D0:].iloc[0])
navs = {k: rebase(v) for k, v in navs9.items()}
navs['IWM (Russell 2000)'] = rebase(adj_ms['IWM'].dropna())
nn = dict(n9); nn['IWM (Russell 2000)'] = None
for k in SEL:
    navs[k] = run_weighted(Wn[k], adj, DS); nn[k] = float(np.mean([len(g) for g in SEL[k].values()]))
    navs[k + ' (peso igual)'] = run_weighted(We[k], adj, DS); nn[k + ' (peso igual)'] = nn[k]
R = navs['S&P 500']
tab = {}
for k, s in navs.items():
    s = s.dropna(); stt = stats(s); w = {y: bm.windows(s, R, y) for y in (3, 5, 10)}
    tab[k] = dict(cagr=stt['CAGR'], vol=stt['Vol'], dd=stt['MaxDD'], n=nn.get(k), w3=w[3][0], w5=w[5][0], w10=w[10][0], p3=w[3][1], p5=w[5][1])
OUT['carteiras'] = tab
(ROOT / 'gestores_amplo_tabela.md').write_text(f'Período: {D0.date()} a {D[-1].date()} (todas rebaseadas no início)\n\n' + '\n'.join(bm.bench_table(navs, nn)))
# fora do S&P, giro, sobreposição com a original
ext = {}
for k in SEL:
    v = SEL[k]; ds = sorted(v)
    fora_sp = float(np.mean([(~g.in_sp).mean() for g in v.values()]))
    w_fora = float(np.mean([Wn[k][d][[t for t in Wn[k][d].index if not v[d].set_index('ticker').in_sp.get(t, True)]].sum() for d in ds]))
    giro = float(np.mean([1 - len(set(v[a].ticker) & set(v[b].ticker)) / max(1, len(v[b])) for a, b in zip(ds, ds[1:])]))
    ext[k] = dict(fora_sp=fora_sp, peso_fora_sp=w_fora, giro_trim=giro, ng=float(np.mean([g.ng.mean() for g in v.values()])),
                  mcap_med=float(np.median(np.concatenate([g.mcap.values for g in v.values()])) / 1e9))
OUT['extra'] = ext
# decomposição (3 anos e 1 ano)
dec = {}
for k in SEL:
    rows = [(d, t, w) for d, ws in Wn[k].items() for t, w in ws.items()]
    hh = pd.DataFrame(rows, columns=['date', 'ticker', 'w']).merge(U.drop_duplicates(['date', 'ticker']), on=['date', 'ticker'], how='left')
    out = {}
    for h in (4, 12):
        y = hh.dropna(subset=[f'le_{h}', f'lp_{h}', f'lt_{h}'])
        g = y.groupby('date').apply(lambda z_: pd.Series({c_: np.average(z_[c_], weights=z_.w) for c_ in (f'le_{h}', f'lp_{h}', f'ld_{h}', f'lt_{h}')}), include_groups=False).mean()
        out[str(h)] = dict(eps=ann(g[f'le_{h}'], h), rr=ann(g[f'lp_{h}'], h), div=ann(g[f'ld_{h}'], h), tot=ann(g[f'lt_{h}'], h))
    dec[k] = out
OUT['decomp'] = dec
# diferença trimestral contra a original do S&P
qd = pd.DatetimeIndex(DS)
qr = {k: navs[k].reindex(qd, method='ffill').pct_change().dropna() for k in SEL}
dif = {}
for k in NEW:
    b_ = 'ROIC alto descontado · S&P (original)' if k.startswith('ROIC') else 'Top 20 · S&P (original)'
    dd_ = (qr[k] - qr[b_]).dropna()
    dif[k] = dict(contra=b_, media_aa=float(dd_.mean() * 4), t=float(dd_.mean() / (dd_.std() / np.sqrt(len(dd_)))), melhor=float((dd_ > 0).mean()))
OUT['diferenca'] = dif
# sem NVIDIA para a melhor
best = max(NEW, key=lambda k: tab[k]['cagr'])
N_b = int(best.split('≥ ')[1].split(' ')[0])
src = (B2[(B2.ng >= N_b) & (B2.ticker != 'NVDA')], ['gap2', 'roic']) if best.startswith('ROIC') else (T2[(T2.ng >= N_b) & (T2.ticker != 'NVDA')], ['ret2', 'roic'])
nav_nv = run_weighted({d: calc2.cap_w(g) for d, g in pick(*src).items()}, adj, DS)
OUT['sem_nvda'] = dict(carteira=best, com=tab[best]['cagr'], sem=stats(nav_nv.dropna())['CAGR'])
M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()})
show = ['S&P 500', 'IWM (Russell 2000)', 'ROIC alto descontado · S&P (original)', 'Top 20 · S&P (original)'] + NEW
OUT['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(v) else round(float(v), 4) for v in M[k] / M[k].dropna().iloc[0]] for k in show}}
last = max(SEL[best])
OUT['hoje'] = {k: [[t, nm(t), float(w), int(SEL[k][last].set_index('ticker').ng.get(t, 0)), bool(SEL[k][last].set_index('ticker').in_sp.get(t, True))]
                   for t, w in Wn[k][last].sort_values(ascending=False).items()] for k in (best, 'ROIC alto descontado · amplo, ≥ 3 gestores')}
OUT['hoje_data'] = str(pd.Timestamp(last).date()); OUT['new'] = NEW; OUT['best'] = best
(ROOT / 'dados_gestores_amplo.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
for k in ['S&P 500', 'IWM (Russell 2000)'] + list(SEL):
    t = tab[k]; e = ext.get(k, {})
    print(f"{k:45s} {t['cagr']:.1%} EW {tab.get(k + ' (peso igual)', {}).get('cagr', np.nan):.1%} vol {t['vol']:.1%} dd {t['dd']:.1%} w3 {t['w3']:.0%} w5 {t['w5']:.0%} w10 {t['w10']:.0%} p3 {t['p3']:+.1%} fora {e.get('fora_sp', np.nan):.0%} giro {e.get('giro_trim', np.nan):.0%}")
print(json.dumps({k: OUT[k] for k in ('diferenca', 'sem_nvda', 'cobertura', 'universo', 'universo_fora_sp')}, ensure_ascii=False, default=str))
