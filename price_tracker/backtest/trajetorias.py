"""Trajetoria de ROIC e EPS das 10 piores atribuicoes da OoL e da GCGR (sem zROIC).
Serie anual com os dados mais recentes da SEC (inclui reapresentacoes) + metricas point-in-time que o modelo usou em cada trimestre.
Saidas: backtest/trajetorias.md, backtest/trajetorias_ool.png, backtest/trajetorias_gcgr.png
Uso: python3 backtest/trajetorias.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from backtest import load_pit, asof, split_factor_after, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices, universe_table  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
WORST = {OOL: ['LULU', 'CLF', 'SIG', 'CPRI', 'TDC', 'AYI', 'UA', 'AMG', 'TPR', 'FOSL'],
         GCGR: ['WYNN', 'MOH', 'ETR', 'HPQ', 'ETSY', 'IT', 'PODD', 'BEN', 'WU', 'OTIS']}
pc = lambda x: '—' if x is None or not np.isfinite(x) else f'{x:.0%}'
sg = lambda x: '—' if x is None or not np.isfinite(x) else f'{x:+.0%}'
mm = lambda x: '—' if x is None or not np.isfinite(x) else f'{x / 1e6:,.0f}'.replace(',', '.')
f2 = lambda x: '—' if x is None or not np.isfinite(x) else f'{x:.2f}'.replace('.', ',')


def annual(tk, fin, splits, t=pd.Timestamp('2027-01-01')):
    """Serie anual completa com os valores mais recentes arquivados, e componentes do ROIC."""
    pit = load_pit(tk)
    eps, _ = asof(pit['eps_diluted'], t)
    s = {k: asof(pit.get(k, []), t)[0] for k in ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income',
                                                'ppe', 'assets_cur', 'cur_liab', 'debt_cur', 'goodwill', 'intangibles')}
    g = lambda k, y: s[k][y][0] if y in s[k] else np.nan
    z = lambda v: 0 if not np.isfinite(v) else v
    def capb(y):
        ac, cl, pp = g('assets_cur', y), g('cur_liab', y), g('ppe', y)
        if not (np.isfinite(ac) and np.isfinite(cl) and np.isfinite(pp)): return np.nan
        return pp + z(g('goodwill', y)) + z(g('intangibles', y)) + (ac - z(g('cash', y))) - (cl - z(g('debt_cur', y)))
    years = sorted(set(eps) | set(s['op_income']) | set(s['net_income']))
    rows = []
    for y in years:
        e = eps[y][0] / split_factor_after(splits, eps[y][1]) if y in eps else np.nan
        oi, pt, tx = g('op_income', y), g('pretax', y), g('tax', y)
        tr = min(max(tx / pt, 0), .5) if np.isfinite(pt) and np.isfinite(tx) and pt > 0 else .21
        nopat = oi * (1 - tr)
        cb, cp = capb(y), capb(y - 1)
        cap = (cb + cp) / 2 if np.isfinite(cb) and np.isfinite(cp) else cb
        eq = g('equity', y)
        ia = engine.invested_capital(eq, g('lt_debt', y), g('cash', y), g('ppe', y), g('assets_cur', y), g('cur_liab', y), g('debt_cur', y))[0] if np.isfinite(eq) else np.nan
        ra = nopat / ia if ia and np.isfinite(ia) and ia > 0 else np.nan
        rb = nopat / cap if np.isfinite(cap) and cap > 0 else np.nan
        roic = (g('net_income', y) / eq if eq and eq > 0 else np.nan) if fin else (rb if np.isfinite(rb) else ra)
        rows.append(dict(fy=y, eps=e, nopat=nopat, ni=g('net_income', y), roic=roic, roic_b=rb, roic_a=ra, cap_b=cb, cap_avg=cap, ppe=g('ppe', y),
                         gw=g('goodwill', y), intang=g('intangibles', y), ac=g('assets_cur', y), cash=g('cash', y), cl=g('cur_liab', y),
                         debt_cur=g('debt_cur', y), equity=eq, ic_a=ia))
    a = pd.DataFrame(rows).set_index('fy')
    a['eps_g'] = [engine_ratio(a.eps.get(y), a.eps.get(y - 1)) for y in a.index]
    return a


def engine_ratio(x, y):
    return x / y - 1 if x is not None and y is not None and np.isfinite(x) and np.isfinite(y) and y > 0 else np.nan


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates)]
    c = vp.classify(f[f.pit_member].assign(zroic=0.0), 'sketch', 'B')
    px = load_prices(); adj = px['adj_close']; spl = px['stock_splits']
    ut = universe_table().set_index('ticker').fin
    names = pd.concat([pd.read_csv(D / 'universe.csv')[['ticker', 'name']],
                       pd.read_csv(D / 'universe_pit_extra.csv').rename(columns={'sec_name': 'name'})[['ticker', 'name']]]).drop_duplicates('ticker').set_index('ticker')['name']
    out = ['# Trajetória de ROIC e lucro por ação das 10 piores da OoL e da GCGR (sem zROIC)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B: NOPAT ÷ capital operacional médio com ágio e intangíveis; reserva em A). Esta análise expõe '
           'casos em que o ROIC calculado é absurdo — ver seção 3.\n',
           'Série anual com os dados mais recentes da SEC (inclui reapresentações). "Modelo na compra" = o que o modelo via na data '
           '(point-in-time): ROIC = média(últimos 3 anos, 6 anos); crescimento = mediana de 5 taxas anuais do EPS.\n',
           '**Sinais testados na compra:** *EPS no pico* = EPS do último ano é o maior dos últimos 6; *ROIC no pico* = ROIC do último ano '
           '≥ 1,2 × mediana dos 5 anos anteriores; *crescimento de base deprimida* = alguma das 5 taxas > 100% ou EPS caiu > 30% num ano da janela.\n']
    summary, absurd = [], []
    for cat, tks in WORST.items():
        fig, axs = plt.subplots(5, 4, figsize=(20, 22), dpi=110)
        out += [f'## {"1" if cat == OOL else "2"}. {cat}\n']
        for i, tk in enumerate(tks):
            sp_ = spl[tk][spl[tk] > 0] if tk in spl else pd.Series(dtype=float)
            fin = bool(ut.get(tk, False))
            a = annual(tk, fin, sp_)
            held = c[(c.ticker == tk) & (c.cat == cat)].date.sort_values()
            mdl = f[(f.ticker == tk)].sort_values('date').set_index('date')
            d0, d1 = held.iloc[0], held.iloc[-1]
            fy0 = int(mdl.last_fy.get(d0)); fyx = int(mdl.last_fy.get(d1))
            yrs = [y for y in a.index if fy0 - 7 <= y <= fyx + 4]
            a = a.loc[yrs]
            # sinais na compra (dados point-in-time da linha do modelo)
            r0 = mdl.loc[d0]
            ry = [r0[f'ry{k}'] for k in range(1, 7)]; gy = [r0[f'gy{k}'] for k in range(1, 6)]
            e_pit = a.eps.loc[[y for y in a.index if fy0 - 5 <= y <= fy0]]
            eps_peak = np.isfinite(a.eps.get(fy0, np.nan)) and a.eps.get(fy0) >= e_pit.max() - 1e-9
            prior = [v for v in ry[:-1] if np.isfinite(v)]
            roic_peak = bool(prior) and np.isfinite(ry[-1]) and ry[-1] >= 1.2 * np.median(prior)
            depressed = any(np.isfinite(v) and v > 1 for v in gy) or any(np.isfinite(v) and v < -0.3 for v in gy)
            e_after = a.eps.get(fyx + 2, a.eps.get(fyx + 1, np.nan)); r_after = a.roic.get(fyx + 2, a.roic.get(fyx + 1, np.nan))
            pre = a.roic.loc[[y for y in a.index if fy0 - 5 <= y <= fy0 - 3]].mean()
            summary.append(dict(cat=cat, tk=tk, eps_peak=eps_peak, roic_peak=roic_peak, depressed=depressed,
                                eps_chg=engine_ratio(e_after, a.eps.get(fy0)), roic0=a.roic.get(fy0), roic_after=r_after))
            out += [f'### {tk} — {names.get(tk, tk)}\n',
                    f'Na carteira de {d0:%m/%Y} a {d1:%m/%Y} ({len(held)} trimestres; exercícios {fy0} a {fyx} eram os últimos disponíveis). '
                    f'Modelo na compra: ROIC {pc(r0.roic)}, crescimento {pc(r0.growth)}, zGrowth {r0.zgrowth:.2f}. '.replace('.', ',', 0) +
                    f'Sinais: EPS no pico **{"sim" if eps_peak else "não"}**, ROIC no pico **{"sim" if roic_peak else "não"}**, '
                    f'crescimento de base deprimida **{"sim" if depressed else "não"}**.\n',
                    '| Exercício | EPS | Cresc. EPS | ROIC (oficial) | NOPAT (US$ mi) | Capital B médio (US$ mi) | Patrimônio (US$ mi) | Situação |',
                    '|---|---|---|---|---|---|---|---|']
            for y, r in a.iterrows():
                tag = 'compra' if y == fy0 else ('na carteira' if fy0 < y <= fyx else ('depois' if y > fyx else ''))
                out.append(f'| {y} | {f2(r.eps)} | {sg(r.eps_g)} | {pc(r.roic)} | {mm(r.nopat)} | {mm(r.cap_avg)} | {mm(r.equity)} | {tag} |')
                if not fin and np.isfinite(r.roic) and (r.roic > 1 or r.roic < 0) and fy0 - 6 <= y <= fyx:
                    absurd.append((tk, y, r))
            out.append('')
            # graficos
            ax, bx = axs[i // 2, (i % 2) * 2], axs[i // 2, (i % 2) * 2 + 1]
            span = (fy0 - 0.5, fyx + 0.5)
            for z_ in (ax, bx): z_.axvspan(*span, color='#fff3b0', alpha=.8, lw=0, label='Exercícios usados enquanto na carteira')
            rr = (a.roic * 100).clip(-100, 300)
            ax.plot(a.index, rr, marker='o', color='#1f6feb', lw=2, label='ROIC anual (oficial)')
            ax.axhline(30, color='#2da44e', ls='--', lw=1); ax.axhline(12, color='#8c959f', ls=':', lw=1); ax.axhline(0, color='black', lw=.6)
            ax.set_title(f'{tk} — ROIC (%)', fontsize=10); ax.grid(alpha=.3)
            bx.bar(a.index, a.eps, color=np.where(a.eps >= 0, '#57606a', '#cf222e'), alpha=.8, label='EPS anual (US$)')
            b2 = bx.twinx(); b2.plot(a.index, (a.eps_g * 100).clip(-100, 200), color='#8250df', marker='.', lw=1.4, label='Cresc. EPS (%)')
            b2.axhline(30, color='#8250df', ls='--', lw=.8); b2.set_ylim(-100, 200)
            bx.set_title(f'{tk} — EPS (barras, US$) e crescimento (linha, %)', fontsize=10); bx.grid(alpha=.3)
            for z_ in (ax, bx): z_.xaxis.set_major_locator(mt.MaxNLocator(integer=True)); z_.tick_params(labelsize=8)
            if i == 0: ax.legend(fontsize=7, loc='upper left'); bx.legend(fontsize=7, loc='upper left'); b2.legend(fontsize=7, loc='upper right')
        fig.suptitle(f'{cat}: as 10 piores atribuições — ROIC e EPS por exercício (faixa amarela = exercícios que o modelo via enquanto segurava a ação). '
                     'ROIC limitado a 300% e crescimento a 200% no gráfico.', fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, .98)); fig.savefig(ROOT / f'trajetorias_{"ool" if cat == OOL else "gcgr"}.png'); plt.close(fig)

    S = pd.DataFrame(summary)
    tab = ['## Resumo dos sinais na compra\n', '| Classe | Ticker | EPS no pico | ROIC no pico | Base deprimida | ROIC na compra | ROIC 2 anos após a saída | EPS 2 anos após a saída vs compra |',
           '|---|---|---|---|---|---|---|---|']
    for r in S.itertuples():
        tab.append(f"| {'OoL' if r.cat == OOL else 'GCGR'} | {r.tk} | {'sim' if r.eps_peak else 'não'} | {'sim' if r.roic_peak else 'não'} | "
                   f"{'sim' if r.depressed else 'não'} | {pc(r.roic0)} | {pc(r.roic_after)} | {sg(r.eps_chg)} |")
    for cat in (OOL, GCGR):
        x = S[S.cat == cat]
        tab.append(f"| **{'OoL' if cat == OOL else 'GCGR'}: total** | | {x.eps_peak.sum()}/10 | {x.roic_peak.sum()}/10 | {x.depressed.sum()}/10 | | | |")
    abs_ = ['## 3. ROIC absurdo (> 100% ou negativo): de onde vem\n',
            'Componentes do capital B no fim do exercício (US$ mi): imobilizado + ágio + intangíveis + (ativo circulante − caixa) − (passivo circulante − dívida CP).\n',
            '| Ticker | Exercício | ROIC | NOPAT | Imobilizado | Ágio | Intangíveis | Ativo circ. − caixa | Passivo circ. − dívida CP | Capital B (fim) | Capital B médio | Patrimônio | ROIC (A) |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for tk, y, r in absurd:
        abs_.append(f'| {tk} | {y} | **{pc(r.roic)}** | {mm(r.nopat)} | {mm(r.ppe)} | {mm(r.gw)} | {mm(r.intang)} | {mm(r.ac - (r.cash if np.isfinite(r.cash) else 0))} | '
                    f'{mm(r.cl - (r.debt_cur if np.isfinite(r.debt_cur) else 0))} | {mm(r.cap_b)} | {mm(r.cap_avg)} | {mm(r.equity)} | {pc(r.roic_a)} |')
    i = out.index(next(l for l in out if l.startswith('## 1.')))
    out = out[:i] + tab + [''] + abs_ + [''] + out[i:]
    (ROOT / 'trajetorias.md').write_text('\n'.join(out))
    print('\n'.join(out[:i + len(tab) + len(abs_) + 2]))


if __name__ == '__main__':
    main()
