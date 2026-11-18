"""Ramo D, parte 2 (backtest sem viés de seleção). Baseado no ramo C (2026-11-18, pré-registrado no PROTOCOLO): os gestores do "Navegando US" definem o universo (S&P 500 + médias e pequenas, ≥ US$ 2 bi),
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


# ---------------- V e BRK-B (faltavam no painel do S&P: o LPA não está no companyfacts) ----------------
import backtest as bt  # noqa: E402
import validation_portfolios as vp  # noqa: E402
pr = bm.load_prices(); close = pr['close']; divs = pr['dividends'].fillna(0)
def synth(tk, f):
    pit = bt.load_pit(tk)
    if tk == 'BRK-B':   # LPA básico por ação classe A ÷ 1.500 = por ação B
        import gzip as gz
        raw = json.load(gz.open(P / 'backtest' / 'data' / 'pit' / f'{tk}.json.gz', 'rt'))
    rows = []
    ni = pit.get('net_income', [])
    for d in DS:
        if tk not in close or not np.isfinite(close.at[d, tk]): continue
        s_ = {y: v for y, v in bt.asof(ni, d)[0].items()}
        if not s_: continue
        p_ = dict(pit); p_['eps_diluted'] = [('sint', 'USD/shares', pd.DataFrame([[pd.Timestamp(f'{y}-12-31'), v[0] / f(d), v[1]] for y, v in s_.items()], columns=['end', 'val', 'filed']))]
        ft = bt.features(p_, d, True, pd.Series(dtype=float, index=pd.DatetimeIndex([])))
        if ft is None: continue
        pz = close.at[d, tk]; dv = divs[tk]; dy = dv[(dv.index > d - pd.Timedelta(days=730)) & (dv.index <= d)].sum() / 2 / pz
        rows.append(dict(date=d, ticker=tk, fin=True, price=pz, dy=dy, **ft))
    return rows
SH = {'V': 1.95e9, 'BRK-B': 2.16e9}   # ações equivalentes (classe A de Visa convertida; Berkshire em ações B), aproximação constante
ex = []
for tk, sh in SH.items():
    try: ex += synth(tk, lambda d, sh=sh: sh)
    except Exception as e: print('sintético falhou', tk, repr(e)[:120])
if ex:
    X = vp.classify(pd.DataFrame(ex).assign(zroic=0.0), 'sketch', 'B')
    X['pe'] = X.price / X.eps.where(X.eps > 0); X['mcap'] = X.price * X.ticker.map(SH); X['util'] = False; X['excluded'] = False; X['in_sp'] = True
    X = X[X.date.isin(DS)]
    X['firm'] = X.ticker
    parts = []
    for d, x in pd.concat([U, X[[c_ for c_ in X.columns if c_ in U.columns]]], ignore_index=True).groupby('date'):
        x = x.copy(); x['g2'] = cb.g_rank(x, 0.07); r = x.roic.clip(upper=1.0)
        x['fpe2'] = np.where(r > 0, (1 - x.g2 / r) / (0.085 - x.g2), np.nan)
        base = x.fpe2 * x.eps * (1 + x.growth) ** 2 / x.price
        rf = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy; rc = x.growth + x.dy
        both = pd.Series(rf, index=x.index).notna() & rc.notna(); x['ret2'] = np.where(both, (rf + rc) / 2, x.growth); parts.append(x)
    U = pd.concat(parts); U['gap2'] = np.where((U.fpe2 > 0) & (U.pe > 0), np.log(U.fpe2 / U.pe), np.nan)
    print('V/BRK-B linhas', len(X))

# ---------------- gestores sem viés: 250 maiores ativos de cada trimestre (todos os 13F da SEC) ----------------
G = ROOT / 'data_gestores_sv'
CNT = pd.read_csv(G / 'contagem.csv.gz', dtype={'cusip6': str}, parse_dates=['per'])
MP = pd.read_csv(G / 'cusip_map.csv', dtype={'cusip6': str})
tk2c = MP.dropna(subset=['ticker']).drop_duplicates('ticker').set_index('ticker').cusip6
U['cusip6'] = U.ticker.map(tk2c)
fc = U.groupby('firm').cusip6.first(); U['cusip6'] = U.cusip6.fillna(U.firm.map(fc))
U['per'] = U.date.map(lambda d: pd.Timestamp(d) - pd.offsets.QuarterEnd(1))
cm = CNT.set_index(['per', 'cusip6'])
U['n250'] = [cm.n250.get((p, c), 0) if isinstance(c, str) else 0 for p, c in zip(U.per, U.cusip6)]
U['nnav'] = [cm.nnav.get((p, c), 0) if isinstance(c, str) else 0 for p, c in zip(U.per, U.cusip6)]
OUT['sem_cusip_no_painel'] = float(U[U.mcap >= 2e9].cusip6.isna().mean())

# cobertura do universo (≥ N): do valor das posições dos 250, quanto tem dado no painel
p2d = {pd.Timestamp(d) - pd.offsets.QuarterEnd(1): d for d in DS}
MPi = MP.set_index('cusip6')
cov = {}
for N in (3, 5, 10):
    rows = []
    for p, g in CNT[CNT.per.isin(p2d) & (CNT.n250 >= N)].groupby('per'):
        d = p2d[p]; u = U[(U.date == d)]; have = set(u.cusip6.dropna()); have2 = set(u[u.mcap >= 2e9].cusip6.dropna())
        t = g.v250.sum(); cat = []
        for cc, v in zip(g.cusip6, g.v250):
            st = 'com dado' if cc in have else None
            if st is None:
                m = MPi.loc[cc] if cc in MPi.index else None
                if m is None or pd.isna(m.ticker): st = 'sem ticker'
                elif isinstance(m.sectype, str) and ('Depositary' in m.sectype or 'ADR' in m.sectype or 'Foreign' in m.sectype): st = 'ADR/estrangeira'
                elif not m.listada_hoje: st = 'deslistada depois'
                else: st = 'sem dado (outro)'
            cat.append((st, v, cc))
        cdf = pd.DataFrame(cat, columns=['st', 'v', 'cc'])
        rows.append(dict(per=p, n=len(g), **{k: float(cdf[cdf.st == k].v.sum() / t) for k in ('com dado', 'sem ticker', 'ADR/estrangeira', 'deslistada depois', 'sem dado (outro)')},
                         n_falta=int((cdf.st != 'com dado').sum()), n_desl=int((cdf.st == 'deslistada depois').sum())))
    cv = pd.DataFrame(rows); cov[str(N)] = {k: float(cv[k].mean()) for k in cv.columns if k != 'per'}
    cov[str(N)]['_serie'] = cv[['per', 'n', 'n_falta', 'n_desl']].assign(per=cv.per.astype(str)).values.tolist()
OUT['cobertura'] = cov
OUT['universo'] = {str(N): float(U[(U.n250 >= N) & (U.mcap >= 2e9)].groupby('date').size().mean()) for N in (3, 5, 10)}
OUT['universo_fora_sp'] = {str(N): float((~U[(U.n250 >= N) & (U.mcap >= 2e9)].in_sp).mean()) for N in (3, 5, 10)}
print('cobertura', {k: {a: round(b, 3) for a, b in v.items() if a != '_serie'} for k, v in cov.items()}, OUT['universo'], flush=True)
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
    'Top 20 · S&P (original)': pick(SPt, ['ret', 'roic']),
    'ROIC alto descontado · S&P (original)': pick(SPb, ['gap', 'roic']),
    'Top 20 · lista do Navegando, ≥ 5 (ramo C, com viés)': pick(T2[T2.nnav >= 5], ['ret2', 'roic']),
}
for N in (3, 5, 10):
    SEL[f'Top 20 · 250 gestores, ≥ {N}'] = pick(T2[T2.n250 >= N], ['ret2', 'roic'])
for N in (3, 5, 10):
    SEL[f'ROIC alto descontado · 250 gestores, ≥ {N}'] = pick(B2[B2.n250 >= N], ['gap2', 'roic'])
import engine  # noqa: E402
_sv = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': .12, 'Roic_Lo': .10})
try:
    _c2 = engine.classify(U[['growth', 'zgrowth', 'roic', 'ret2']].rename(columns={'ret2': 'ret'}).assign(zroic=0.0))
    _c1 = engine.classify(U[['growth', 'zgrowth', 'roic', 'ret']].assign(zroic=0.0))
finally:
    engine.TH.clear(); engine.TH.update(_sv)
U['ool2'] = _c2.code.notna() & (_c2.category == 'Opportunity of Lifetime'); U['ool1'] = _c1.code.notna() & (_c1.category == 'Opportunity of Lifetime')
OO1 = U[U.in_sp & U.ool1 & ~U.excluded]; OO2 = U[liq & U.ool2 & ~U.excluded]
SEL['OoL · S&P (original, peso igual)'] = {d: calc2.dd_firm(g) for d, g in OO1.groupby('date')}
SEL['OoL · 250 gestores, ≥ 5 (peso igual)'] = {d: calc2.dd_firm(g) for d, g in OO2[OO2.n250 >= 5].groupby('date')}
SEL['OoL · lista do Navegando, ≥ 5 (ramo C, com viés; peso igual)'] = {d: calc2.dd_firm(g) for d, g in OO2[OO2.nnav >= 5].groupby('date')}
NEW = [k for k in SEL if '250 gestores' in k]
Wn = {k: ({d: pd.Series(1 / len(g), index=g.ticker) for d, g in v.items()} if 'OoL' in k else {d: calc2.cap_w(g) for d, g in v.items()}) for k, v in SEL.items()}
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
(ROOT / 'gestores_sv_tabela.md').write_text(f'Período: {D0.date()} a {D[-1].date()} (todas rebaseadas no início)\n\n' + '\n'.join(bm.bench_table(navs, nn)))
# fora do S&P, giro, sobreposição com a original
ext = {}
for k in SEL:
    v = SEL[k]; ds = sorted(v)
    fora_sp = float(np.mean([(~g.in_sp).mean() for g in v.values()]))
    w_fora = float(np.mean([Wn[k][d][[t for t in Wn[k][d].index if not v[d].set_index('ticker').in_sp.get(t, True)]].sum() for d in ds]))
    giro = float(np.mean([1 - len(set(v[a].ticker) & set(v[b].ticker)) / max(1, len(v[b])) for a, b in zip(ds, ds[1:])]))
    ext[k] = dict(fora_sp=fora_sp, peso_fora_sp=w_fora, giro_trim=giro, ng=float(np.mean([g.n250.mean() for g in v.values()])),
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
    b_ = 'OoL · S&P (original, peso igual)' if k.startswith('OoL') else 'ROIC alto descontado · S&P (original)' if k.startswith('ROIC') else 'Top 20 · S&P (original)'
    dd_ = (qr[k] - qr[b_]).dropna()
    dif[k] = dict(contra=b_, media_aa=float(dd_.mean() * 4), t=float(dd_.mean() / (dd_.std() / np.sqrt(len(dd_)))), melhor=float((dd_ > 0).mean()))
OUT['diferenca'] = dif
# sem NVIDIA para a melhor
best = 'Top 20 · 250 gestores, ≥ 5'
N_b = int(best.split('≥ ')[1].split(' ')[0])
src = (B2[(B2.n250 >= N_b) & (B2.ticker != 'NVDA')], ['gap2', 'roic']) if best.startswith('ROIC') else (T2[(T2.n250 >= N_b) & (T2.ticker != 'NVDA')], ['ret2', 'roic'])
nav_nv = run_weighted({d: calc2.cap_w(g) for d, g in pick(*src).items()}, adj, DS)
OUT['sem_nvda'] = dict(carteira=best, com=tab[best]['cagr'], sem=stats(nav_nv.dropna())['CAGR'])
M = pd.DataFrame({k: v.resample('ME').last() for k, v in navs.items()})
show = ['S&P 500', 'IWM (Russell 2000)', 'Top 20 · S&P (original)', 'Top 20 · lista do Navegando, ≥ 5 (ramo C, com viés)', 'Top 20 · 250 gestores, ≥ 5', 'OoL · 250 gestores, ≥ 5 (peso igual)', 'ROIC alto descontado · 250 gestores, ≥ 5']
OUT['nav'] = {'dates': [str(d.date()) for d in M.index], 'series': {k: [None if pd.isna(v) else round(float(v), 4) for v in M[k] / M[k].dropna().iloc[0]] for k in show}}
last = max(SEL[best])
OUT['hoje'] = {k: [[t, nm(t), float(w), int(SEL[k][last].set_index('ticker').n250.get(t, 0)), bool(SEL[k][last].set_index('ticker').in_sp.get(t, True))]
                   for t, w in Wn[k][last].sort_values(ascending=False).items()] for k in (best,)}
OUT['hoje_data'] = str(pd.Timestamp(last).date()); OUT['new'] = NEW; OUT['best'] = best

# imposto de 15% sobre o ganho realizado
from giro_menor import tax_weighted  # noqa: E402
OUT['imposto'] = {k: stats(tax_weighted(Wn[k], adj, DS).dropna())['CAGR'] for k in ('Top 20 · S&P (original)', best)}
# teste de limites (ações do universo sem dado): peso esperado = n_sem_dado / (n_com_dado + n_sem_dado), por trimestre
qd_ = pd.DatetimeIndex(DS); rb = navs[best].reindex(qd_, method='ffill').pct_change()
univ_ret = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in U[(U.n250 >= 5) & (U.mcap >= 2e9)].groupby('date')}, adj, DS).reindex(qd_, method='ffill').pct_change()
spr = navs['S&P 500'].reindex(qd_, method='ffill').pct_change()
ser = {pd.Timestamp(p): (n, nf, nd) for p, n, nf, nd in cov['5']['_serie']}
lim = {}
for cen in ('pessimista', 'neutro', 'otimista'):
    out_ = []
    for i in range(1, len(qd_)):
        d0 = qd_[i - 1]; p = d0 - pd.offsets.QuarterEnd(1)
        n, nf, nd = ser.get(p, (1, 0, 0)); w = nf / max(n, 1)
        r_s = {'pessimista': (nd / max(nf, 1)) * (-1.0) + (1 - nd / max(nf, 1)) * univ_ret.iloc[i], 'neutro': univ_ret.iloc[i], 'otimista': spr.iloc[i]}[cen]
        out_.append((1 - w) * rb.iloc[i] + w * r_s)
    r_ = np.array(out_, dtype=float); lim[cen] = float(np.prod(1 + r_) ** (4 / len(r_)) - 1)
OUT['limites'] = lim
# lista atual (13F de jun/2026 -> carteira de set/2026)
lastp = CNT.per.max()
cur = CNT[(CNT.per == lastp) & (CNT.n250 >= 3)].merge(MP[['cusip6', 'ticker', 'nome', 'sectype', 'listada_hoje']], on='cusip6', how='left')
ul = U[U.date == max(DS)].drop_duplicates('cusip6').set_index('cusip6')
for c_ in ('mcap', 'roic', 'growth', 'pe', 'ret2', 'gap2', 'excluded', 'in_sp'):
    cur[c_] = cur.cusip6.map(ul[c_]) if c_ in ul else np.nan
tsel = SEL[best].get(max(DS)); cur['top20_hoje'] = cur.ticker.isin(set(tsel.ticker)) if tsel is not None else False
cur.sort_values('n250', ascending=False)[['ticker', 'nome', 'cusip6', 'n250', 'nnav', 'mcap', 'roic', 'growth', 'pe', 'ret2', 'gap2', 'excluded', 'in_sp', 'top20_hoje', 'sectype']].rename(
    columns={'n250': 'n_gestores_250', 'nnav': 'n_gestores_navegando', 'ret2': 'retorno_esperado', 'gap2': 'desconto_log', 'excluded': 'ciclica_ou_vestuario'}).to_csv(ROOT / 'universo_gestores_atual.csv', index=False)
OUT['lista_atual'] = dict(periodo_13f=str(lastp.date()), n_ge5=int((cur.n250 >= 5).sum()), n_ge5_com_dado=int(((cur.n250 >= 5) & cur.mcap.notna()).sum()))
(ROOT / 'dados_gestores_sv.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else (float(v) if isinstance(v, (np.floating, np.integer)) else str(v))))
for k in ['S&P 500', 'IWM (Russell 2000)'] + list(SEL):
    t = tab[k]; e = ext.get(k, {})
    print(f"{k:45s} {t['cagr']:.1%} EW {tab.get(k + ' (peso igual)', {}).get('cagr', np.nan):.1%} vol {t['vol']:.1%} dd {t['dd']:.1%} w3 {t['w3']:.0%} w5 {t['w5']:.0%} w10 {t['w10']:.0%} p3 {t['p3']:+.1%} fora {e.get('fora_sp', np.nan):.0%} giro {e.get('giro_trim', np.nan):.0%}")
print(json.dumps({k: OUT[k] for k in ('diferenca', 'sem_nvda', 'universo', 'universo_fora_sp', 'limites', 'imposto', 'lista_atual')}, ensure_ascii=False, default=str))
