"""Por que Good Companies, Great Returns rende tanto quanto (ou mais que) a Opportunity of Lifetime?
Universo point-in-time, ROIC oficial, estrutura do esboco (OoL a partir de ROIC 12%).
 1. Perfil e desempenho de cada grupo: OoL (Base, High Returns, High Growth) e GCGR por motivo de desqualificacao.
 2. Atribuicao por empresa dentro de cada motivo e da OoL Base.
 3. Contrafactuais: OoL se cada criterio fosse relaxado (as empresas barradas por ele entrariam na OoL).
Uso: python3 backtest/why_ool.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

SEM_Z = '--sem-zroic' in sys.argv; SUF = '_sem_zroic' if SEM_Z else ''
NOTA = ' **Variante sem o critério de estabilidade do ROIC (zROIC desligado).**' if SEM_Z else ''
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
FLAW = {0: 'Crescimento médio (6–15%)', 1: 'Crescimento instável (zGrowth ≥ 2,93)', 2: 'ROIC médio (10–12%)', 3: 'ROIC instável (zROIC ≥ 0,7)'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member]
    if SEM_Z: f = f.assign(zroic=0.0)
    adj = load_prices()['adj_close']
    u = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'name', 'sector']],
                   pd.read_csv(D / 'universe_pit_extra.csv').rename(columns={'sec_name': 'name'})[['ticker', 'name']]]).drop_duplicates('ticker').set_index('ticker')
    c = vp.classify(f, 'sketch', 'B')
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    b1 = adj.reindex(pd.DatetimeIndex(dates) - pd.DateOffset(years=1), method='ffill').set_axis(pd.DatetimeIndex(dates))
    c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    c['mom12'] = [px.at[d, t] / b1.at[d, t] - 1 for d, t in zip(c.date, c.ticker)]
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c = c[c.date < dates[-1]]
    univ_q = c[c.cat.notna()].groupby('date').rq.mean()
    ool = c.cat == OOL
    c['flaw'] = np.where(c.cat == GCGR, c.code.map(lambda s: next((i for i in range(4) if isinstance(s, str) and s[i] != 'HOGNG'[i]), -1)), -1)
    groups = {'OoL High Returns (ROIC > 30%)': ool & (c.roic > 0.30), 'OoL High Growth (EPS > 30%)': ool & (c.growth > 0.30),
              'OoL Base': ool & (c.roic <= 0.30) & (c.growth <= 0.30), 'Opportunity of Lifetime (todas)': ool}
    for k, v in FLAW.items(): groups[f'GCGR — {v}'] = c.flaw == k
    groups['Good Companies, Great Returns (todas)'] = c.cat == GCGR
    out = ['# Por que Good Companies, Great Returns acompanha ou supera a Opportunity of Lifetime? (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial; dois dos quatro motivos de desqualificação são de ROIC.' + NOTA + '\n',
           'Unidade = posição (ação × trimestre). Retorno = média do retorno do trimestre seguinte, anualizada; excesso sobre a média do universo no mesmo trimestre. '
           'Perfil = medianas no momento da compra.\n',
           '## 1. Perfil e desempenho por grupo\n',
           '| Grupo | Posições | Empresas | Retorno a.a. | vs Universo | % negativas | P/L | P/E justo | ROIC | Crescimento 5a | Retorno esperado | Retorno 12m antes | Div. yield |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for k, m in groups.items():
        x = c[m]
        ex = (x.rq - x.date.map(univ_q)).mean() * 4
        out.append(f'| {k} | {len(x)} | {x.ticker.nunique()} | {pc(x.rq.mean() * 4)} | **{sg(ex)}** | {pc((x.rq < 0).mean())} | {n1(x.pe.median())} | {n1(x.fair_pe.median())} | '
                   f'{pc(x.roic.median())} | {pc(x.growth.median())} | {pc(x.ret.median())} | {pc(x.mom12.median())} | {pc(x.dy.median())} |')

    # 2) atribuicao por empresa
    def attrib(m, title, n=10):
        x = c[m].copy(); x['n'] = x.groupby('date').ticker.transform('size'); x['ctr'] = x.rq / x.n
        x['ex'] = x.rq - x.date.map(univ_q)
        a = x.groupby('ticker').agg(ctr=('ctr', 'sum'), trim=('ctr', 'size'), ex=('ex', 'mean'), pe=('pe', 'median'), roic=('roic', 'median'),
                                    growth=('growth', 'median'), p0=('date', 'min'), p1=('date', 'max')).sort_values('ctr', ascending=False)
        row = lambda t, r: (f"| {t} | {u['name'].get(t, '')} | {sg(r.ctr)} | {r.trim} | {sg(r.ex * 4)} | {n1(r.pe)} | {pc(r.roic)} | {pc(r.growth)} | {r.p0.year}–{r.p1.year} |")
        hdr = ['| Ticker | Empresa | Contribuição | Trim. | Excesso médio a.a. | P/L | ROIC | Crescimento | Período |', '|---|---|---|---|---|---|---|---|---|']
        return ([f'### {title}\n', f'{x.ticker.nunique()} empresas. As 10 maiores somam {pc(a.ctr.head(10).sum() / a.ctr.sum()) if a.ctr.sum() else "—"} da contribuição.\n',
                 '**Maiores contribuições**\n'] + hdr + [row(t, r) for t, r in a.head(n).iterrows()] +
                ['', '**Menores contribuições**\n'] + hdr + [row(t, r) for t, r in a.tail(n).iloc[::-1].iterrows()] + [''])
    out += ['', '## 2. Atribuição por empresa\n']
    out += attrib(groups['OoL Base'], 'OoL Base')
    for k, v in FLAW.items():
        out += attrib(c.flaw == k, f'GCGR — {v}')

    # 3) contrafactuais (carteiras de verdade, NAV diario)
    def port(m):
        return run_portfolio({d: g.ticker.tolist() for d, g in c[m].groupby('date')}, adj, dates)[0]
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]
    univ = port(c.cat.notna())
    cf = {'OoL atual (todas)': ool}
    for k, v in FLAW.items():
        cf[f'OoL + barradas por {v.split(" (")[0].lower()}'] = ool | (c.flaw == k)
    cf['OoL + todas as GCGR (qualquer defeito)'] = ool | (c.cat == GCGR)
    cf['OoL sem a Base (só High Returns e High Growth)'] = groups['OoL High Returns (ROIC > 30%)'] | groups['OoL High Growth (EPS > 30%)']
    cf['OoL sem a Base + GCGR com ROIC médio'] = cf['OoL sem a Base (só High Returns e High Growth)'] | (c.flaw == 2)
    out += ['## 3. Contrafactuais: e se o critério fosse diferente?\n',
            'Cada linha é uma carteira real (equal weight, trimestral, retorno total) no universo point-in-time.\n',
            '| Carteira | Retorno anual | vs Universo EW | vs S&P 500 | Ações (média) | Janelas de 5 anos > S&P 500 |', '|---|---|---|---|---|---|']
    M_spy = spy.resample('ME').last()
    for k, m in cf.items():
        nav = port(m); s = stats(nav)
        Mn = nav.resample('ME').last(); w = ((Mn / Mn.shift(60)) > (M_spy / M_spy.shift(60)))[(Mn / Mn.shift(60)).notna()]
        out.append(f"| {k} | {pc(s['CAGR'])} | {sg(s['CAGR'] - stats(univ)['CAGR'])} | {sg(s['CAGR'] - stats(spy)['CAGR'])} | {c[m].groupby('date').size().mean():.0f} | {w.mean():.0%} |")
        print(k, flush=True)
    out.append(f"| *Universo EW* | {pc(stats(univ)['CAGR'])} | — | {sg(stats(univ)['CAGR'] - stats(spy)['CAGR'])} | | |")
    out.append(f"| *S&P 500 (SPY)* | {pc(stats(spy)['CAGR'])} | | — | | |")
    (ROOT / f'why_ool{SUF}.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
