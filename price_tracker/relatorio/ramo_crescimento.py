"""Ramo A (2026-11-18, pedido do usuário): o crescimento é previsível?
 1. previsibilidade do crescimento do EPS sem cíclicos/vestuário (e sem financeiras)
 2. o g normalizado do P/E justo prevê o crescimento? R², fórmula, erro e viés (contra a mediana e a constante de 8%)
 3. receita: a passada prevê a futura? prevê o EPS? alavancagem operacional (EPS = a + b·receita)
 4. variantes pré-registradas (PROTOCOLO, 2026-11-18): o crescimento do P/E justo e do retorno esperado vindo de outro preditor
S&P 500 point-in-time, ROIC triangulado. Saída: relatorio/dados_crescimento.json.
Uso: python3 relatorio/ramo_crescimento.py [analise|carteiras]"""
import sys, json, pathlib
from multiprocessing import Pool
import numpy as np, pandas as pd
from scipy import stats as st
MODE = sys.argv[1] if len(sys.argv) > 1 else 'analise'; sys.argv = sys.argv[:1]
ROOT = pathlib.Path(__file__).parent; P = ROOT.parent
sys.path[:0] = [str(ROOT), str(P / 'backtest'), str(P)]
import calc2, top_n  # noqa: E402
import benchmarks as bm  # noqa: E402
from backtest import asof  # noqa: E402
from roic3 import load_pit2  # noqa: E402

CACHE = ROOT / 'cache_receita.pkl'


def rev_one(args):
    tk, ds = args
    p2 = load_pit2(tk)
    if 'revenue' not in p2: return []
    out = []
    for t in ds:
        r = asof(p2['revenue'], t)[0]
        if not r: continue
        last = max(r); v = {y: r[y][0] for y in r}
        rates = []
        for y in range(last - 4, last + 1):
            a, b = v.get(y - 1), v.get(y)
            rates.append(b / a - 1 if a and b is not None and a > 0 else np.nan)
        ok = [x for x in rates if np.isfinite(x)]
        out.append(dict(date=t, ticker=tk, rev=v[last], rev_fy=last, rev_med=float(np.median(ok)) if len(ok) >= 3 else np.nan,
                        rev_last=rates[-1], rev_n=len(ok)))
    return out


c, adj, dates, ref, nm = calc2.sp_data()
D = pd.DatetimeIndex(dates); iq = {d: i for i, d in enumerate(D)}
if CACHE.exists():
    rv = pd.read_pickle(CACHE)
else:
    jobs = [(t, sorted(pd.Timestamp(x) for x in g.date.unique())) for t, g in c.groupby('ticker')]
    with Pool(4) as pool:
        res = pool.map(rev_one, jobs, chunksize=8)
    rv = pd.DataFrame([r for rr in res for r in rr]); rv.to_pickle(CACHE)
p = c.merge(rv, on=['date', 'ticker'], how='left')
p['qi'] = p.date.map(iq)
key = p.set_index(['qi', 'ticker'])
for h in (4, 12, 20):
    f = key[['eps', 'rev']].copy(); f.index = pd.MultiIndex.from_arrays([f.index.get_level_values(0) - h, f.index.get_level_values(1)]); f.columns = [f'{x}_{h}' for x in f.columns]
    p = p.join(f, on=['qi', 'ticker'])
    ok = (p.eps > 0) & (p[f'eps_{h}'] > 0)
    p[f'R{h}'] = np.where(ok, (p[f'eps_{h}'] / p.eps) ** (4 / h) - 1, np.nan)        # crescimento anual realizado do EPS
    okr = (p.rev > 0) & (p[f'rev_{h}'] > 0)
    p[f'V{h}'] = np.where(okr, (p[f'rev_{h}'] / p.rev) ** (4 / h) - 1, np.nan)      # crescimento anual realizado da receita
p['pr_med'] = p.growth; p['pr_g'] = p.g; p['pr_8'] = .08
p['pr_rmed'] = p.rev_med; p['pr_rlast'] = p.rev_last
AMOSTRAS = {'Todas': p.ticker.notna(), 'Sem cíclicas e vestuário': ~p.excluded, 'Sem cíclicas, vestuário e financeiras': ~p.excluded & ~p.fin}
CL = (-.5, 1.0)


def avalia(df, y, x):
    """pooled: realizado = a + b·preditor (os dois limitados a −50%..100%); IC = correlação de ordem média por trimestre"""
    z = df.dropna(subset=[y, x])
    err = z[y] - z[x]
    out = dict(n=int(len(z)), mae=float(err.abs().median()), vies=float(err.median()), real_med=float(z[y].median()), prev_med=float(z[x].median()))
    if z[x].nunique() > 5:
        yy, xx = z[y].clip(*CL), z[x].clip(*CL)
        sl = st.linregress(xx, yy)
        ics = [st.spearmanr(g[x], g[y])[0] for _, g in z.groupby('date') if len(g) > 30 and g[x].nunique() > 5]
        ics = np.array([v for v in ics if np.isfinite(v)])
        out.update(a=float(sl.intercept), b=float(sl.slope), r2=float(sl.rvalue ** 2), ic=float(ics.mean()), ic_pos=float((ics > 0).mean()),
                   ic_t=float(ics.mean() / (ics.std() / np.sqrt(max(len(ics) / 4, 1)))))
        # erro do preditor calibrado (a + b·x), para comparar só a informação
        out['mae_cal'] = float((yy - (sl.intercept + sl.slope * xx)).abs().median())
    return out


OUT = {'periodo': [str(D[0].date()), str(D[-1].date())]}
if MODE == 'analise':
    PRED = [('pr_med', 'Mediana de 5 anos do EPS (o nosso)'), ('pr_g', 'g normalizado do P/E justo'), ('pr_8', 'Constante de 8%'),
            ('pr_rmed', 'Mediana de 5 anos da receita'), ('pr_rlast', 'Receita do último ano')]
    eps = {}
    for am, m in AMOSTRAS.items():
        eps[am] = {str(h): {lab: avalia(p[m], f'R{h}', col) for col, lab in PRED} for h in (4, 12, 20)}
    OUT['eps'] = eps
    rev = {}
    for am, m in AMOSTRAS.items():
        rev[am] = {str(h): {lab: avalia(p[m], f'V{h}', col) for col, lab in (('pr_rmed', 'Mediana de 5 anos da receita'), ('pr_rlast', 'Receita do último ano'),
                                                                            ('pr_8', 'Constante de 8%'), ('pr_med', 'Mediana de 5 anos do EPS'))} for h in (4, 12, 20)}
    OUT['receita'] = rev
    lev = {}
    for am, m in AMOSTRAS.items():
        lev[am] = {str(h): avalia(p[m].assign(_v=p[m][f'V{h}']), f'R{h}', '_v') for h in (4, 12, 20)}
    OUT['alavancagem'] = lev
    # quintis do previsto x realizado (3 anos, sem cíclicos): EPS pela mediana do EPS, pela receita; receita pela receita
    q = p[~p.excluded].copy(); quint = {}
    for nm_, x, y in (('EPS pela mediana do EPS', 'pr_med', 'R12'), ('EPS pela mediana da receita', 'pr_rmed', 'R12'), ('Receita pela mediana da receita', 'pr_rmed', 'V12')):
        z = q.dropna(subset=[x, y]).copy()
        z['qq'] = z.groupby('date')[x].transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False))
        quint[nm_] = z.groupby('qq').agg(prev=(x, 'median'), real=(y, 'median')).round(4).values.tolist()
    OUT['quintis'] = quint
    # estabilidade: dispersão anual do crescimento (EPS x receita), mediana por empresa
    OUT['dispersao'] = dict(eps=float(p[~p.excluded].zgrowth.abs().median()),
                            rev_iqr=float(q.groupby('ticker').V4.std().median()), eps_iqr=float(q.groupby('ticker').R4.std().median()))
    (ROOT / 'dados_crescimento.json').write_text(json.dumps(OUT, ensure_ascii=False, default=lambda v: None if (isinstance(v, float) and not np.isfinite(v)) else float(v)))
    for am in AMOSTRAS:
        print('==', am)
        for h in ('4', '12'):
            for lab, r in OUT['eps'][am][h].items():
                print(f"  EPS h={h:>2} {lab:38s} r2={r.get('r2', np.nan):.3f} a={r.get('a', np.nan):+.3f} b={r.get('b', np.nan):+.3f} ic={r.get('ic', np.nan):+.3f} t={r.get('ic_t', np.nan):+.1f} mae={r['mae']:.3f} mae_cal={r.get('mae_cal', np.nan):.3f} vies={r['vies']:+.3f} n={r['n']}")
            for lab, r in OUT['receita'][am][h].items():
                print(f"  REC h={h:>2} {lab:38s} r2={r.get('r2', np.nan):.3f} a={r.get('a', np.nan):+.3f} b={r.get('b', np.nan):+.3f} ic={r.get('ic', np.nan):+.3f} mae={r['mae']:.3f} vies={r['vies']:+.3f}")
            r = OUT['alavancagem'][am][h]; print(f"  ALAV h={h:>2} EPS = {r['a']:+.3f} + {r['b']:.2f}·receita  r2={r['r2']:.3f} ic={r['ic']:+.3f}")
    print(OUT['quintis'], OUT['dispersao'])
