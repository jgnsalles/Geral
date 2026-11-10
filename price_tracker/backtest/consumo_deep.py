"""(A) OoL e GCGR sem Energia e Materiais. (B) Mergulho no Consumo Discricionario: o que separa vencedores de perdedores.
Sem zROIC, universo point-in-time, ROIC oficial corrigido, esboco (OoL a partir de ROIC 12%). Le backtest/atributos.csv.
Saidas: backtest/consumo_deep.md, backtest/consumo_deep.png
Uso: python3 backtest/consumo_deep.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import run_portfolio, stats, load_pit, asof, split_factor_after, D  # noqa: E402
from validation_core import load_prices  # noqa: E402
import setores_derrotas as sd  # noqa: E402

OOL, GCGR = sd.OOL, sd.GCGR
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
pc1 = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.0%}'
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')
TYPE = {'Apparel, Accessories & Luxury Goods': 'Marcas de vestuário e acessórios', 'Footwear': 'Marcas de vestuário e acessórios',
        'Apparel Retail': 'Varejo especializado', 'Other Specialty Retail': 'Varejo especializado', 'Computer & Electronics Retail': 'Varejo especializado',
        'Homefurnishing Retail': 'Varejo especializado', 'Broadline Retail (lojas de departamento)': 'Lojas de departamento',
        'Home Improvement Retail': 'Varejo de reforma e autopeças', 'Automotive Retail': 'Varejo de reforma e autopeças', 'Distributors': 'Varejo de reforma e autopeças',
        'Broadline Retail': 'Internet e marketplaces', 'Hotels, Resorts & Cruise Lines': 'Viagem, hotéis e cassinos', 'Casinos & Gaming': 'Viagem, hotéis e cassinos',
        'Restaurants': 'Restaurantes', 'Automobile Manufacturers': 'Veículos e autopeças (indústria)', 'Automotive Parts & Equipment': 'Veículos e autopeças (indústria)',
        'Motorcycle Manufacturers': 'Veículos e autopeças (indústria)', 'Home Furnishings': 'Bens duráveis para casa', 'Household Appliances': 'Bens duráveis para casa',
        'Homebuilding': 'Bens duráveis para casa', 'Leisure Products': 'Bens duráveis para casa', 'Consumer Electronics': 'Bens duráveis para casa',
        'Specialized Consumer Services': 'Serviços ao consumidor'}
# metricas ex ante (na primeira compra): (coluna, nome, formato)
EXANTE = [('roic', 'ROIC do modelo', 'p'), ('roic_y', 'ROIC do último ano', 'p'), ('roic_trend', 'ROIC último ano ÷ mediana dos 5 anteriores', 'x'),
          ('roic_std', 'Desvio-padrão do ROIC (6a)', 'p'), ('growth', 'Crescimento do EPS (G)', 'p'), ('g_last', 'Crescimento do EPS no último ano', 'p'),
          ('g_accel', 'Crescimento: média dos 2 últimos − G', 'p'), ('neg_years', 'Anos de queda do EPS (de 5)', 'n'), ('zgrowth', 'zGrowth', 'n'),
          ('pe', 'P/L', 'x'), ('fair_pe', 'P/E justo', 'x'), ('ret', 'Retorno esperado', 'p'), ('dy', 'Dividend yield', 'p1'),
          ('mom12', 'Alta da ação nos 12 meses antes', 'p'), ('log_nopat', 'Tamanho: log10 NOPAT (US$ bi)', 'n'), ('t', 'Alíquota de imposto', 'p'),
          ('sh_ppe', 'Peso do imobilizado no capital', 'p'), ('sh_gwi', 'Peso de ágio + intangíveis no capital', 'p'), ('sh_nwc', 'Peso do capital de giro no capital', 'p'),
          ('cap_g', 'Crescimento do capital no ano', 'p'), ('lev', 'Dívida ÷ patrimônio', 'x'), ('reinv', 'Reinvestimento (g ÷ ROIC)', 'p')]
EXPOST = [('eps_2y', 'EPS 2 anos depois da 1ª compra ÷ EPS na compra − 1', 'p'), ('roic_2y', 'ROIC do último ano, 2 anos depois', 'p'),
          ('pe_2y', 'P/L 2 anos depois ÷ P/L na compra', 'x'), ('quarters', 'Trimestres na OoL/GCGR', 'n')]


def fmt(v, k):
    if pd.isna(v) or not np.isfinite(v): return '—'
    return {'p': pc, 'p1': pc1, 'x': n1, 'n': n1}[k](v)


def part_a(c, adj):
    dates = sorted(c.date.unique()); dates = dates + [dates[-1] + pd.offsets.QuarterEnd()]
    dates = [pd.Timestamp(d) for d in dates]
    last_px = adj.index[adj.index <= dates[-1]][-1]; dates[-1] = last_px
    spy = adj['SPY'].loc[dates[0]:dates[-1]]; spy = spy / spy.iloc[0]; Ms = spy.resample('ME').last(); S = stats(spy)['CAGR']
    ex = c.sector.isin(['Energy', 'Materials'])
    ool = c.cat == OOL
    G = {'OoL': ool, 'OoL High Returns': ool & (c.roic > .3), 'OoL High Growth': ool & (c.growth > .3), 'OoL Base': ool & (c.roic <= .3) & (c.growth <= .3), 'GCGR': c.cat == GCGR}
    out = ['## A. Sem Energia e Materiais\n', 'Mesmas carteiras, só retirando as ações desses dois setores (a classificação das demais não muda). '
           f'S&P 500: {pc1(S)} a.a.\n', '| Carteira | Atual | Sem Energia e Materiais | Ações retiradas por trimestre | Janelas 5a > S&P (atual → sem) | Janelas 10a > S&P (atual → sem) |',
           '|---|---|---|---|---|---|']
    for k, m in G.items():
        r = []
        for mm in (m, m & ~ex):
            nav = run_portfolio({d: g.ticker.tolist() for d, g in c[mm].groupby('date')}, adj, dates)[0]
            Mn = nav.resample('ME').last()
            r.append((stats(nav)['CAGR'], ((Mn / Mn.shift(60)) > (Ms / Ms.shift(60)))[(Mn / Mn.shift(60)).notna() & (Ms / Ms.shift(60)).notna()].mean(), ((Mn / Mn.shift(120)) > (Ms / Ms.shift(120)))[(Mn / Mn.shift(120)).notna() & (Ms / Ms.shift(120)).notna()].mean()))
        out.append(f'| {k} | {pc1(r[0][0])} | **{pc1(r[1][0])}** | {c[m & ex].groupby("date").size().reindex(c.date.unique()).fillna(0).mean():.1f} | '
                   f'{pc(r[0][1])} → {pc(r[1][1])} | {pc(r[0][2])} → {pc(r[1][2])} |')
    return out


def main():
    c = pd.read_csv(ROOT / 'atributos.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    xe = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
    c['sector'] = c.ticker.map(lambda t: sd.MANUAL[t][0] if t in sd.MANUAL else u.sector.get(t))
    c['industry'] = c.ticker.map(lambda t: sd.MANUAL[t][1] if t in sd.MANUAL else u.industry.get(t))
    name = lambda t: u.name.get(t) if t in u.index else xe.sec_name.get(t, t)
    px_ = load_prices(); adj = px_['adj_close']; spl = px_['stock_splits']
    out = ['# Sem Energia e Materiais; e o que separa vencedores de perdedores no Consumo (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). Marcas e varejo têm pouco capital, então o ROIC delas tende a ser alto; '
           'ROIC acima de 100% em empresas leves em ativos ainda está em aberto.\n',
           'Configuração: sem zROIC, OoL a partir de ROIC 12%.\n']
    out += part_a(c, adj)

    # B) consumo
    x = c[c.sector == 'Consumer Discretionary'].sort_values('date').copy()
    x['type'] = x.industry.map(TYPE).fillna('Outros')
    RY = [f'ry{i}' for i in range(1, 7)]; GY = [f'gy{i}' for i in range(1, 6)]
    x['roic_trend'] = x.ry6 / x[RY[:-1]].median(axis=1).where(lambda s: s > 0)
    x['g_last'] = x.gy5; x['g_accel'] = x[['gy4', 'gy5']].mean(axis=1) - x.growth; x['neg_years'] = (x[GY] < 0).sum(axis=1)
    x['log_nopat'] = np.log10(x.nopat.where(x.nopat > 0)); x['lev'] = x.debt / x.equity.where(x.equity > 0)
    dts = pd.DatetimeIndex(sorted(c.date.unique()))
    pxq = adj.reindex(dts, method='ffill'); b1 = adj.reindex(dts - pd.DateOffset(years=1), method='ffill').set_axis(dts)
    x['mom12'] = [pxq.at[d, t] / b1.at[d, t] - 1 for d, t in zip(x.date, x.ticker)]
    e = x.groupby('ticker').agg(ex=('ex', 'mean'), quarters=('ex', 'size'), type=('type', 'first'), industry=('industry', 'first'),
                                classes=('cat', lambda s: '/'.join(sorted({'OoL' if v == OOL else 'GCGR' for v in s}))))
    e['ex'] *= 4
    first = x.groupby('ticker').first()
    for col, _, _ in EXANTE: e[col] = first[col]
    e['d0'] = first.date
    # ex post: EPS e ROIC 2 anos depois da 1a compra
    eps2, roic2, pe2 = [], [], []
    for t, r in e.iterrows():
        p = load_pit(t); s = spl[t][spl[t] > 0] if t in spl else pd.Series(dtype=float)
        t0 = r.d0; t2 = t0 + pd.DateOffset(years=2)
        e0, _ = asof(p['eps_diluted'], t0); e2, _ = asof(p['eps_diluted'], t2)
        v = lambda E: (E[max(E)][0] / split_factor_after(s, E[max(E)][1])) if E else np.nan
        a, b = v(e0), v(e2)
        eps2.append(b / a - 1 if a and a > 0 and np.isfinite(b) else np.nan)
        f2 = x[(x.ticker == t)]
        pxa = adj[t].reindex([t0, t2], method='ffill') if t in adj else pd.Series([np.nan, np.nan])
        pe2.append((pxa.iloc[1] / b) / (pxa.iloc[0] / a) if a and a > 0 and b and b > 0 else np.nan)
        roic2.append(np.nan)
    e['eps_2y'], e['pe_2y'] = eps2, pe2
    fv = pd.read_csv(D / 'val_features.csv', parse_dates=['date'], usecols=['date', 'ticker', 'ry6']).set_index(['ticker', 'date']).sort_index()
    for t, r in e.iterrows():
        try:
            s = fv.loc[t]; s = s[s.index >= r.d0 + pd.DateOffset(years=2)]
            e.at[t, 'roic_2y'] = s.ry6.iloc[0] if len(s) else np.nan
        except KeyError:
            e.at[t, 'roic_2y'] = np.nan
    el = e[e.quarters >= 4].copy()
    q1, q2 = el.ex.quantile(1 / 3), el.ex.quantile(2 / 3)
    el['grupo'] = np.where(el.ex <= q1, 'Perdedores', np.where(el.ex >= q2, 'Vencedores', 'Meio'))
    GR = ['Perdedores', 'Meio', 'Vencedores']
    out += ['', '## B. Consumo Discricionário: vencedores × perdedores\n',
            f'{len(el)} empresas de consumo discricionário que passaram ≥ 4 trimestres na OoL e/ou na GCGR. Retorno = excesso médio sobre o universo '
            f'enquanto estavam na classe. Terços: perdedores ≤ {sg(q1)} a.a.; vencedores ≥ {sg(q2)} a.a. '
            'Métricas **na primeira compra** (sem viés de olhar o futuro).\n',
            '### B1. Por tipo de negócio\n', '| Tipo | Empresas | Perdedores | Meio | Vencedores | Excesso mediano | Empresas |', '|---|---|---|---|---|---|---|']
    for k, g in el.groupby('type'):
        nm = ', '.join(f"{t}{'↓' if r.grupo == 'Perdedores' else ('↑' if r.grupo == 'Vencedores' else '')}" for t, r in g.sort_values('ex').iterrows())
        out.append(f"| {k} | {len(g)} | {(g.grupo == 'Perdedores').sum()} | {(g.grupo == 'Meio').sum()} | {(g.grupo == 'Vencedores').sum()} | {sg(g.ex.median())} | {nm} |")
    out.append('\n↑ vencedor, ↓ perdedor (ordenado do pior para o melhor).\n')
    out += ['### B2. Métricas na primeira compra (mediana por grupo)\n',
            'Separação = (mediana dos vencedores − mediana dos perdedores) ÷ intervalo interquartil do consumo. Correlação = Spearman entre a métrica e o excesso, '
            f'com {len(el)} empresas (|ρ| > 0,28 ≈ significativo a 5%).\n',
            '| Métrica | Perdedores | Meio | Vencedores | Separação | Correlação (ρ) |', '|---|---|---|---|---|---|']
    rows = []
    for col, nm, k in EXANTE + EXPOST:
        s = el[col].replace([np.inf, -np.inf], np.nan); iqr = s.quantile(.75) - s.quantile(.25)
        med = [s[el.grupo == g].median() for g in GR]
        sep = (med[2] - med[0]) / iqr if iqr and iqr > 0 else np.nan
        rho = s.corr(el.ex, method='spearman')
        rows.append((col in dict((a, 1) for a, _, _ in EXPOST), abs(np.nan_to_num(rho)), f"| {nm}{' *(depois)*' if col in [a for a, _, _ in EXPOST] else ''} | "
                     f"{fmt(med[0], k)} | {fmt(med[1], k)} | {fmt(med[2], k)} | {n1(sep) if np.isfinite(sep) else '—'} | "
                     + (f'**{rho:+.2f}**' if abs(rho) > .28 else f'{rho:+.2f}').replace('.', ',') + ' |'))
    for _, _, r in sorted(rows, key=lambda z: (z[0], -z[1])): out.append(r)
    out += ['', '*(depois)* = medido depois da compra; não serve para escolher, só para entender o que aconteceu.\n',
            '### B3. Todas as empresas\n',
            '| Grupo | Ticker | Empresa | Tipo | Classe | Trim. | Excesso a.a. | ROIC | Tendência ROIC | G | Cresc. último ano | P/L | Alta 12m antes | Imobilizado no capital | EPS 2a depois | P/L 2a depois ÷ compra |',
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for g in GR[::-1]:
        for t, r in el[el.grupo == g].sort_values('ex', ascending=False).iterrows():
            out.append(f"| {g} | {t} | {name(t)} | {r.type} | {r.classes} | {r.quarters} | {sg(r.ex)} | {pc(r.roic)} | {n1(r.roic_trend)} | {pc(r.growth)} | "
                       f"{sg(r.g_last)} | {n1(r.pe)} | {sg(r.mom12)} | {pc(r.sh_ppe)} | {sg(r.eps_2y)} | {n1(r.pe_2y)} |")
    (ROOT / 'consumo_deep.md').write_text('\n'.join(out))
    el.to_csv(ROOT / 'consumo_deep.csv')
    print('\n'.join(out))
    # grafico: as 6 metricas com maior |rho| ex ante + EPS depois
    top = sorted([(abs(el[col].replace([np.inf, -np.inf], np.nan).corr(el.ex, method='spearman')), col, nm, k) for col, nm, k in EXANTE], reverse=True)[:5]
    top += [(0, 'eps_2y', 'EPS 2 anos depois ÷ compra − 1 (depois)', 'p')]
    fig, axs = plt.subplots(2, 3, figsize=(17, 10), dpi=120)
    colr = {'Perdedores': '#cf222e', 'Meio': '#8c959f', 'Vencedores': '#2da44e'}
    for ax, (_, col, nm, k) in zip(axs.ravel(), top):
        d = el[[col, 'ex', 'grupo']].replace([np.inf, -np.inf], np.nan).dropna()
        lo, hi = d[col].quantile(.02), d[col].quantile(.98); d[col] = d[col].clip(lo, hi)
        sc = 100 if k in ('p', 'p1') else 1
        for g in GR:
            dd = d[d.grupo == g]; ax.scatter(dd[col] * sc, dd.ex * 100, s=30, color=colr[g], alpha=.8, label=g)
        for t in d.index:
            if t in el.ex.nlargest(6).index or t in el.ex.nsmallest(6).index:
                ax.annotate(t, (d.at[t, col] * sc, d.at[t, 'ex'] * 100), fontsize=7, xytext=(3, 2), textcoords='offset points')
        rho = el[col].replace([np.inf, -np.inf], np.nan).corr(el.ex, method='spearman')
        ax.axhline(0, color='black', lw=.7); ax.grid(alpha=.3); ax.set_title(f'{nm} — ρ = {rho:+.2f}'.replace('.', ','), fontsize=10)
        ax.set_ylabel('Excesso médio na classe (% a.a.)', fontsize=8)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle('Consumo discricionário (OoL + GCGR): cada ponto é uma empresa; métricas na primeira compra', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(ROOT / 'consumo_deep.png'); plt.close(fig)


if __name__ == '__main__':
    main()
