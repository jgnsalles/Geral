"""Nova medida de volatilidade do ROIC (definida pelo usuario, 2026-11-10):
dispersao = media das variacoes absolutas ano contra ano do ROIC (6 anos -> 5 variacoes) / media do ROIC dos 6 anos.
> 30% = ROIC volatil; <= 30% = estavel. Media do ROIC <= 0 conta como volatil. Precisa de >= 3 variacoes validas.
1. Os setores ciclicos definidos (Energia, Materiais, vestuario, ciclicos duros) caem acima de 30%?
2. Microsetores (subsetores GICS) com ROIC volatil, dentro de cada macrossetor.
3. Comparacao com o zROIC.
4. Carteiras usando a nova medida como criterio de estabilidade, com os 8 comparativos obrigatorios.
Universo point-in-time (membros do S&P 500 em cada trimestre), ROIC oficial (corrigido em 2026-11-10); financeiras e seguradoras de saude: ROE.
Saidas: backtest/roic_dispersao.md, backtest/roic_dispersao.png, backtest/roic_dispersao_carteiras.png
Uso: python3 backtest/roic_dispersao.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402

CUT = 0.30
HARD = {'Automotive Parts & Equipment', 'Motorcycle Manufacturers', 'Passenger Airlines', 'Homebuilding', 'Home Furnishings', 'Household Appliances',
        'Building Products', 'Construction Machinery & Heavy Transportation Equipment', 'Agricultural & Farm Machinery', 'Industrial Machinery',
        'Construction & Engineering', 'Timber REITs', 'Casinos & Gaming', 'Trading Companies & Distributors', 'Air Freight & Logistics',
        'Cargo Ground Transportation', 'Marine Transportation'}
SEC_PT = {'Consumer Discretionary': 'Consumo discricionário', 'Consumer Staples': 'Consumo básico', 'Energy': 'Energia', 'Materials': 'Materiais',
          'Industrials': 'Indústria', 'Information Technology': 'Tecnologia', 'Financials': 'Financeiro', 'Communication Services': 'Comunicação',
          'Health Care': 'Saúde', 'Utilities': 'Utilidades públicas', 'Real Estate': 'Imobiliário'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'


def dispersion(f):
    R = f[[f'ry{i}' for i in range(1, 7)]].to_numpy(dtype=float)
    d = np.abs(np.diff(R, axis=1))
    nd = np.isfinite(d).sum(axis=1)
    mad = np.where(nd >= 3, np.nanmean(np.where(np.isfinite(d), d, np.nan), axis=1), np.nan)
    mu = np.nanmean(R, axis=1)
    out = np.where(np.isnan(mad), np.nan, np.where(mu > 0, mad / np.where(mu > 0, mu, 1), np.inf))
    return pd.Series(out, index=f.index)


def group(sec, ind):
    if sec == 'Energy': return 'Energia'
    if sec == 'Materials': return 'Materiais'
    if ind in bm.APPAREL: return 'Vestuário'
    if ind in HARD: return 'Cíclicos duros'
    return 'Demais'


def main():
    f, dates = bm.base_data()
    sec, ind = bm.sector_maps()
    f['sector'] = f.ticker.map(sec); f['industry'] = f.ticker.map(ind)
    f['disp'] = dispersion(f)
    f['vol'] = f.disp > CUT
    f['grp'] = [group(s, i) for s, i in zip(f.sector, f.industry)]
    g = f[f.disp.notna()]
    # empresa: mediana da dispersao ao longo das datas
    e = g.groupby('ticker').agg(disp=('disp', 'median'), share=('vol', 'mean'), sector=('sector', 'first'), industry=('industry', 'first'),
                                grp=('grp', 'first'), n=('disp', 'size'))
    e['volatil'] = e.disp > CUT
    out = ['# Nova medida de volatilidade do ROIC: variação absoluta média ÷ ROIC médio (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10); financeiras e seguradoras de saúde usam ROE. A medida herda qualquer erro do ROIC; '
           'empresas com patrimônio negativo ou ROIC > 100% (ainda em aberto) podem distorcer.\n',
           '**Fórmula:** nos 6 últimos exercícios, calcula-se |ROIC do ano − ROIC do ano anterior| para cada um dos 5 pares; a média dessas 5 variações '
           f'é dividida pela média do ROIC dos 6 anos. **> {pc(CUT)} = ROIC volátil**; ≤ {pc(CUT)} = estável. Média do ROIC ≤ 0 conta como volátil. '
           'Exige ao menos 3 variações válidas.\n',
           '*Exemplo:* ROIC de 20%, 25%, 18%, 22%, 30%, 26% → variações 5, 7, 4, 8, 4 (média 5,6 p.p.) ÷ média 23,5% = 24% → estável.\n',
           f'Base: {g.ticker.nunique()} empresas que foram do S&P 500 em algum trimestre entre {dates[0]:%Y} e {dates[-1]:%Y}, '
           f'{len(g)} observações (empresa × trimestre). Classificação da empresa = mediana da medida ao longo dos trimestres.\n']

    # 1) grupos ciclicos
    out += ['## 1. Os setores cíclicos que definimos ficam acima de 30%?\n',
            '| Grupo | Empresas | **% empresas voláteis** | Dispersão mediana | % das observações voláteis |', '|---|---|---|---|---|']
    for k in ['Energia', 'Materiais', 'Vestuário', 'Cíclicos duros', 'Demais']:
        x = e[e.grp == k]; y = g[g.grp == k]
        out.append(f'| {k} | {len(x)} | **{pc(x.volatil.mean())}** | {pc(x.disp.median())} | {pc(y.vol.mean())} |')
    out.append(f'| *Todas* | {len(e)} | {pc(e.volatil.mean())} | {pc(e.disp.median())} | {pc(g.vol.mean())} |')
    # ciclicos duros por subsetor
    out += ['', '### Cada subsetor da nossa lista de cíclicos\n', '| Subsetor | Grupo | Empresas | % voláteis | Dispersão mediana |', '|---|---|---|---|---|']
    for (gr, i), x in e[e.grp != 'Demais'].groupby(['grp', 'industry']):
        out.append(f'| {i} | {gr} | {len(x)} | {pc(x.volatil.mean())} | {pc(x.disp.median())} |')

    # 2) microsetores
    s = e.groupby(['sector', 'industry']).agg(emp=('disp', 'size'), vol=('volatil', 'mean'), med=('disp', 'median'), grp=('grp', 'first'))
    s = s[s.emp >= 3].reset_index()
    out += ['', '## 2. Microsetores (subsetores GICS) por volatilidade do ROIC\n',
            'Subsetores com 3 ou mais empresas. Marcados com ✔ os que já estão nas nossas listas (Energia, Materiais, vestuário, cíclicos duros).\n']
    for sct, x in s.sort_values('vol', ascending=False).groupby('sector', sort=False):
        out += [f'### {SEC_PT.get(sct, sct)} — {pc(e[e.sector == sct].volatil.mean())} das empresas voláteis\n',
                '| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |', '|---|---|---|---|---|']
        for _, r in x.sort_values('vol', ascending=False).iterrows():
            flag = '✔' if r.grp != 'Demais' else ('**novo candidato**' if r.vol >= .5 else '')
            out.append(f'| {r.industry} | {r.emp} | {pc(r.vol)} | {pc(r.med)} | {flag} |')
        out.append('')
    cand = s[(s.grp == 'Demais') & (s.vol >= .5)].sort_values('vol', ascending=False)
    names = lambda i: ', '.join(e[(e.industry == i) & e.volatil].sort_values('disp', ascending=False).index[:8])
    out += ['### Candidatos novos: subsetores fora das nossas listas com ≥ 50% das empresas voláteis\n',
            '| Subsetor | Macrossetor | Empresas | % voláteis | Dispersão mediana | Empresas voláteis (mais voláteis primeiro) |', '|---|---|---|---|---|---|']
    for _, r in cand.iterrows():
        out.append(f'| {r.industry} | {SEC_PT.get(r.sector, r.sector)} | {r.emp} | {pc(r.vol)} | {pc(r.med)} | {names(r.industry)} |')
    stable = s[(s.grp != 'Demais') & (s.vol < .3)]
    if len(stable):
        out += ['', '**Na nossa lista, mas com ROIC estável (< 30% das empresas voláteis):** ' +
                ', '.join(f'{r.industry} ({pc(r.vol)})' for _, r in stable.iterrows())]

    # 3) comparacao com zROIC
    gz = g[g.zroic.notna()]
    zv = gz.zroic >= 0.7
    out += ['', '## 3. Nova medida × zROIC (desvio-padrão ÷ ROIC do modelo, corte 0,7)\n',
            f'Correlação de postos entre as duas: {gz.disp.replace(np.inf, 99).corr(gz.zroic, method="spearman"):+.2f}.\n'.replace('.', ',', 1),
            '| | zROIC < 0,7 (estável) | zROIC ≥ 0,7 (volátil) |', '|---|---|---|',
            f'| **Nova ≤ 30% (estável)** | {pc(((~zv) & ~gz.vol).mean())} | {pc((zv & ~gz.vol).mean())} |',
            f'| **Nova > 30% (volátil)** | {pc(((~zv) & gz.vol).mean())} | {pc((zv & gz.vol).mean())} |',
            '', 'A nova medida é bem mais rígida: o zROIC usa o desvio-padrão em torno da média, que um ROIC alto dilui; a nova soma cada salto de um ano para o outro.\n']

    # 4) carteiras com a nova medida
    c_new = bm.classify_new(f, stability=~f.vol.fillna(True).to_numpy())
    hn = bm.holdings_new(c_new)
    extra = {'OoL novo + estabilidade nova (≤ 30%)': (c_new, hn['OoL novo']), 'GCGR novo + estabilidade nova (≤ 30%)': (c_new, hn['GCGR novo']),
             'OoL High ROIC + estabilidade nova': (c_new, hn['OoL High ROIC (novo)']), 'OoL High Growth + estabilidade nova': (c_new, hn['OoL High Growth (novo)'])}
    navs, n, dts, adj = bm.load_benchmarks(extra)
    out += ['## 4. Carteiras: a nova medida como critério de estabilidade\n',
            'As 8 linhas obrigatórias e, abaixo, as versões novas exigindo ROIC estável pela nova medida (≤ 30%). '
            '"Novo" = esboço (ROIC 12%), sem zROIC, sem Energia, Materiais e vestuário.\n'] + bm.bench_table(navs, n)
    # desempenho das posicoes volateis x estaveis dentro da OoL/GCGR novas (sem criterio)
    c0 = bm.classify_new(f)
    px = adj.reindex(pd.DatetimeIndex(dts), method='ffill'); fwd = px.shift(-1) / px - 1
    c0['rq'] = [fwd.at[d, t] for d, t in zip(c0.date, c0.ticker)]
    c0 = c0[c0.date < dts[-1]]; uq = c0[c0.cat.notna()].groupby('date').rq.mean(); c0['ex'] = c0.rq - c0.date.map(uq)
    out += ['', '### Posições da OoL e GCGR novas: ROIC volátil × estável pela nova medida\n',
            '| Classe | Grupo | Posições | Excesso médio a.a. | Excesso mediano a.a. | % acima do universo |', '|---|---|---|---|---|---|']
    for cat, lab in ((bm.OOL, 'OoL novo'), (bm.GCGR, 'GCGR novo')):
        x = c0[(c0.cat == cat) & ~c0.excluded]
        for gl, m in (('Estável (≤ 30%)', x.disp <= CUT), ('Volátil (> 30%)', x.disp > CUT)):
            y = x[m]; out.append(f'| {lab} | {gl} | {len(y)} | {y.ex.mean() * 4:+.1%} | {y.ex.median() * 4:+.1%} | {pc((y.ex > 0).mean())} |'.replace('.', ','))
    (ROOT / 'roic_dispersao.md').write_text('\n'.join(out))
    print('\n'.join(out))
    bm.bench_plot(navs, ROOT / 'roic_dispersao_carteiras.png', 'Comparativos obrigatórios + versões com a nova medida de estabilidade do ROIC (≤ 30%)')
    # grafico: % volateis por subsetor (top 30)
    top = s.sort_values('vol', ascending=False).head(35).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 11), dpi=130)
    col = {'Energia': '#bf8700', 'Materiais': '#8c6d1f', 'Vestuário': '#cf222e', 'Cíclicos duros': '#e8590c', 'Demais': '#1f6feb'}
    ax.barh(range(len(top)), top.vol * 100, color=[col[x] for x in top.grp])
    ax.set_yticks(range(len(top))); ax.set_yticklabels([f'{r.industry} ({r.emp})' for _, r in top.iterrows()], fontsize=8)
    ax.axvline(50, color='black', ls=':', lw=1); ax.set_xlabel('% das empresas com ROIC volátil (> 30%)'); ax.grid(alpha=.3, axis='x')
    for k, v in col.items(): ax.barh([], [], color=v, label=k if k != 'Demais' else 'Fora das listas (candidato)')
    ax.legend(fontsize=8, loc='lower right'); ax.set_title('Os 35 subsetores com ROIC mais volátil (nº de empresas)', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'roic_dispersao.png'); plt.close(fig)


if __name__ == '__main__':
    main()
