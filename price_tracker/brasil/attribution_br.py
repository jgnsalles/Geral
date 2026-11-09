"""Atribuicao por acao no Brasil (parametros EUA + 2,5 p.p., ROIC 20%/10%, corte zGrowth 2,93).
Uso: python3 brasil/attribution_br.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
import rerun_params as rp  # noqa: E402  (ajusta WACC e g ao importar)
import backtest_br as bb  # noqa: E402
from backtest import run_portfolio, stats  # noqa: E402

D = ROOT / 'data'
CLASSES = ['Cheap but Aggressive', 'Cheap Slow Compounder', 'Do not Waste Time']
pc = lambda x: f'{x:.1%}'.replace('.', ',')
sg = lambda x: f'{x:+.1%}'.replace('.', ',')


def classified():
    cls = pd.read_csv(D / 'classes_pit.csv', parse_dates=['date'])
    cls = cls[[c for c in cls.columns if not c.startswith('cat_')]]
    parts = []
    for d, x in cls.groupby('date'):
        x = x.copy(); x['g'] = bb.g_rank(x)
        x['fair_pe'] = np.where(x.roic > 0, (1 - x.g / x.roic) / (bb.WACC - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy
        x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna()
        x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    x = pd.concat(parts)
    engine.TH.update({'Growth_Hi': 0.175, 'Growth_Lo': 0.085, 'Return_Hi': 0.225, 'Return_Lo': 0.105, 'zGrowth': 2.93})
    c = engine.classify(x); c['cat'] = np.where(c.code.isna(), None, c.category)
    return c


def main(classes=None, tag=''):
    classes = classes or CLASSES
    c = classified()
    u = pd.read_csv(D / 'universe.csv').set_index('yf')
    adj = pd.read_csv(D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    close = pd.read_csv(D / 'prices_close.csv.gz', index_col=0, parse_dates=True)
    cov = c.groupby('date').cat.apply(lambda s: s.notna().sum()); start = cov[cov >= 60].index.min()
    dates = [d for d in bb.rebalance_dates(close) if d >= start]
    px = adj.reindex(pd.DatetimeIndex(dates)).ffill(); fwd = px.shift(-1) / px - 1
    out = [f'# Atribuição no Brasil: {", ".join(classes)}\n',
           '> ⚠️ **ROIC:** classes dependem do corte de ROIC 20%/10%, mais restritivo no Brasil.\n',
           'Parâmetros: WACC 11%; g 9,5% → 6%; crescimento 17,5%/8,5%; retorno 22,5%/10,5%; ROIC 20%/10%; zGrowth 2,93. '
           'Contribuição = soma de (1/N × retorno trimestral) nos trimestres em que a ação esteve na classe.\n']
    for cat in classes:
        x = c[(c.cat == cat) & c.date.isin(dates[:-1])].copy()
        x['n'] = x.groupby('date').ticker.transform('size')
        x['r'] = [fwd.at[d, t] for d, t in zip(x.date, x.ticker)]
        x['c'] = x.r / x.n
        a = x.groupby('ticker').agg(contrib=('c', 'sum'), trims=('c', 'size'), ret_trim=('r', 'mean'), first=('date', 'min'), last=('date', 'max'))
        a = a.sort_values('contrib', ascending=False)
        a['empresa'] = a.index.map(u.Nome_Empresarial); a['setor'] = a.index.map(u.Setor_Atividade)
        hold = {d: g.ticker.tolist() for d, g in x.groupby('date')}
        full = stats(run_portfolio(hold, adj, dates)[0])['CAGR']
        sens = []
        for k in (1, 3, 5):
            drop = set(a.index[:k])
            sens.append((k, stats(run_portfolio({d: [t for t in v if t not in drop] for d, v in hold.items()}, adj, dates)[0])['CAGR']))
        n = 15 if len(a) > 30 else 10
        out += [f'## {cat}\n', f'- Retorno anual: **{pc(full)}** · ações distintas: {len(a)} · ações em média: {x.groupby("date").size().mean():.1f}'.replace('.', ',', 1),
                '- Sem as maiores: ' + ' · '.join(f'sem top {k}: {pc(v)}' for k, v in sens),
                f'- {n} maiores somam {pc(a.contrib.head(n).sum() / a.contrib.sum())} da contribuição total\n',
                f'### {n} maiores\n', '| # | Ticker | Empresa | Setor | Contribuição | Trim. | Retorno médio/trim. | Período |', '|---|---|---|---|---|---|---|---|']
        row = lambda i, t, r: f"| {i} | {t.replace('.SA', '')} | {r.empresa} | {r.setor} | {sg(r.contrib)} | {int(r.trims)} | {sg(r.ret_trim)} | {r['first'].year}–{r['last'].year} |"
        out += [row(i + 1, t, r) for i, (t, r) in enumerate(a.head(n).iterrows())]
        out += ['', f'### {n} menores\n', '| # | Ticker | Empresa | Setor | Contribuição | Trim. | Retorno médio/trim. | Período |', '|---|---|---|---|---|---|---|---|']
        out += [row(i + 1, t, r) for i, (t, r) in enumerate(a.tail(n).iloc[::-1].iterrows())]
        out.append('')
    (ROOT / f'attribution_br{tag}.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'ool_gcgr':
        main(['Opportunity of Lifetime', 'Good Companies, Great Returns'], '_ool_gcgr')
    else:
        main()
