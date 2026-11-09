"""Fase 4 do protocolo: overfitting e significancia (universo point-in-time, ROIC oficial).
 1. Deflated Sharpe Ratio (Bailey & Lopez de Prado) do excesso mensal sobre o universo EW, com ~400 tentativas.
 2. Probability of Backtest Overfitting (CSCV) numa grade de 96 configuracoes da familia OoL (corte de ROIC x corte de Growth).
 3. Walk-forward: melhor configuracao da grade em 2012-2018, avaliada em 2019-2026; candidatas congeladas em 2019-2026.
 4. Intervalo de confianca por bootstrap em blocos (6 meses) do excesso anual.
 5. Placebo: carteiras aleatorias do mesmo tamanho a cada trimestre (500 sorteios).
Uso: python3 backtest/validation_overfit.py"""
import sys, itertools, pathlib, math
import numpy as np, pandas as pd
from scipy.stats import norm
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

N_TRIALS = 400
rng = np.random.default_rng(42)
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
n2 = lambda x: '—' if pd.isna(x) else f'{x:.2f}'.replace('.', ',')


def trial_sr_var():
    """Variancia do Sharpe (trimestral -> mensal) entre as configuracoes ja testadas, a partir das varreduras salvas."""
    ts = []
    for f in list(D.glob('sweep_*.csv')) + list(D.glob('roic_sweep*.csv')):
        x = pd.read_csv(f)
        for c in ('ool_t', 'gcgr_t'):
            if c in x: ts += x[c].dropna().tolist()
    sr_q = np.array(ts) / math.sqrt(58)          # t = SR * sqrt(T), T ~ 58 trimestres
    return float(np.var(sr_q / math.sqrt(3))), len(ts)  # Sharpe mensal ~ trimestral / sqrt(3)


def dsr(e, n_trials, var_sr):
    e = e.dropna(); T = len(e)
    sr = e.mean() / e.std()
    g = 0.5772156649
    sr0 = math.sqrt(var_sr) * ((1 - g) * norm.ppf(1 - 1 / n_trials) + g * norm.ppf(1 - 1 / (n_trials * math.e)))
    sk, ku = e.skew(), e.kurt() + 3
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)
    return sr, sr0, norm.cdf(z), T


def block_boot(e, B=5000, L=6):
    e = e.dropna().to_numpy(); T = len(e); means = []
    for _ in range(B):
        idx = np.concatenate([(np.arange(L) + s) % T for s in rng.integers(0, T, size=T // L + 1)])[:T]
        means.append(e[idx].mean() * 12)
    return np.percentile(means, [5, 50, 95])


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member]
    adj = load_prices()['adj_close']
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    f['rq'] = [fwd.at[d, t] if t in fwd.columns else np.nan for d, t in zip(f.date, f.ticker)]
    base = vp.classify(f, 'sketch', 'B')                         # fair PE / retorno nao dependem dos cortes
    univ_q = base[base.cat.notna()].groupby('date').rq.mean()
    out = ['# Fase 4: overfitting e significância (universo point-in-time, ROIC oficial)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A).\n']

    # 1) Deflated Sharpe nas candidatas (mensal)
    m = pd.read_csv(D / 'val_monthly.csv', index_col=0, parse_dates=True)
    var_sr, n_obs = trial_sr_var()
    out += ['## 1. Deflated Sharpe Ratio (excesso mensal sobre o universo EW)\n',
            f'Tentativas consideradas: {N_TRIALS}. Variância do Sharpe entre tentativas estimada a partir de {n_obs} configurações das varreduras.\n',
            '| Carteira | Excesso a.a. | Sharpe mensal | Sharpe exigido por sorte | Prob. DSR | IC 90% do excesso a.a. (bootstrap) |', '|---|---|---|---|---|---|']
    for c in [c for c in m.columns if c.startswith('PIT|') and 'Universo' not in c]:
        e = (m[c] - m['PIT|Universo EW']).dropna()
        sr, sr0, p, T = dsr(e, N_TRIALS, var_sr)
        lo, mid, hi = block_boot(e)
        out.append(f"| {c.split('|')[1]} | {sg(e.mean() * 12)} | {n2(sr)} | {n2(sr0)} | **{p:.0%}** | {sg(lo)} a {sg(hi)} |")

    # 2) PBO via CSCV na grade
    roic_cuts = np.round(np.arange(0.10, 0.401, 0.02), 2); growth_cuts = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
    grid = {}
    for rc, gc in itertools.product(roic_cuts, growth_cuts):
        saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': float(rc), 'Roic_Lo': min(0.10, float(rc)), 'Growth_Hi': gc})
        try:
            c = engine.classify(base.drop(columns=['category', 'code', 'order', 'cat'], errors='ignore'))
        finally:
            engine.TH.clear(); engine.TH.update(saved)
        q = c[c.category == 'Opportunity of Lifetime'].groupby('date').rq.mean()
        grid[(rc, gc)] = (q - univ_q).reindex(univ_q.index)
    G = pd.DataFrame(grid).iloc[:-1]  # ultimo trimestre sem retorno
    G = G.fillna(0)
    S = 10; blocks = np.array_split(np.arange(len(G)), S)
    lam = []
    for comb in itertools.combinations(range(S), S // 2):
        isx = np.concatenate([blocks[i] for i in comb]); oos = np.concatenate([blocks[i] for i in range(S) if i not in comb])
        sr_is = G.iloc[isx].mean() / G.iloc[isx].std(); sr_oos = G.iloc[oos].mean() / G.iloc[oos].std()
        best = sr_is.idxmax()
        rank = (sr_oos.rank(pct=True))[best]
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        lam.append(math.log(rank / (1 - rank)))
    pbo = float(np.mean(np.array(lam) <= 0))
    out += ['', '## 2. Probability of Backtest Overfitting (CSCV)\n',
            f'Grade de {G.shape[1]} configurações da Opportunity of Lifetime (corte de ROIC de 10% a 40% × corte de Growth de 10% a 35%), '
            f'{len(G)} trimestres em {S} blocos, {len(lam)} combinações. **PBO = {pbo:.0%}** '
            '(probabilidade de a melhor configuração dentro da amostra ficar abaixo da mediana fora dela; abaixo de 50% indica que escolher pelo passado ajuda).\n']

    # 3) walk-forward
    is_m = G.index < pd.Timestamp('2019-01-01')
    best = (G[is_m].mean() / G[is_m].std()).idxmax()
    oos_best = G.loc[~is_m, best].mean() * 4
    oos_med = G.loc[~is_m].mean().median() * 4
    out += ['## 3. Walk-forward (calibração 2012–2018, teste 2019–2026)\n',
            f'Melhor configuração em 2012–2018: ROIC ≥ {pc(best[0])}, Growth ≥ {pc(best[1])} — excesso no teste: **{sg(oos_best)} a.a.** '
            f'(mediana das 96 configurações no teste: {sg(oos_med)}).\n',
            '| Candidata congelada | Excesso 2012–2018 | Excesso 2019–2026 |', '|---|---|---|']
    for c in [c for c in m.columns if c.startswith('PIT|') and 'Universo' not in c]:
        e = (m[c] - m['PIT|Universo EW']).dropna()
        out.append(f"| {c.split('|')[1]} | {sg(e[e.index < '2019-01-01'].mean() * 12)} | **{sg(e[e.index >= '2019-01-01'].mean() * 12)}** |")

    # 4) placebo
    out += ['', '## 4. Placebo: carteiras aleatórias do mesmo tamanho\n',
            '500 sorteios por candidata: a cada trimestre, o mesmo número de ações sorteado entre as empresas classificadas do universo point-in-time.\n',
            '| Carteira | Retorno médio a.a. | Placebo: mediana | Placebo: percentil 95 | Percentil da candidata |', '|---|---|---|---|---|']
    pools = {d: g for d, g in base[base.cat.notna()].groupby('date')}
    for cname, (params, sel) in vp.CANDS.items():
        c = vp.classify(f, params, 'B')
        hold = c[sel(c)]
        real = hold.groupby('date').rq.mean().reindex(univ_q.index).iloc[:-1]
        sizes = hold.groupby('date').size()
        sims = []
        for _ in range(500):
            rs = []
            for d in univ_q.index[:-1]:
                k = int(sizes.get(d, 0)); pool = pools[d].rq.dropna().to_numpy()
                rs.append(pool[rng.choice(len(pool), size=min(k, len(pool)), replace=False)].mean() if k else 0.0)
            sims.append(np.mean(rs) * 4)
        sims = np.array(sims); r = real.fillna(0).mean() * 4
        out.append(f'| {cname} | {sg(r)} | {sg(np.median(sims))} | {sg(np.percentile(sims, 95))} | **{(sims < r).mean():.0%}** |')
        print(cname, flush=True)
    (ROOT / 'validation_phase4.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
