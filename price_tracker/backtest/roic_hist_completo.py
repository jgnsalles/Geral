"""Volatilidade do ROIC com TODO o historico disponivel (medida do usuario):
dispersao = media das variacoes absolutas ano contra ano do ROIC / media do ROIC. > 30% = volatil.
(a) Historico completo de cada empresa (todos os exercicios na SEC, ~2008-2025): carater estrutural do setor e da empresa.
(b) Versao point-in-time para carteira: em cada trimestre, todo o historico ate ali (exercicio y conta a partir de 30/06 de y+1).
Tambem a versao so com as quedas (media das quedas ano a ano / media do ROIC), para separar ciclo de crescimento.
ROIC oficial (B com reserva em A; financeiras e seguradoras de saude: ROE), corrigido em 2026-11-10.
Saidas: backtest/roic_hist_completo.md, roic_hist_completo.png, roic_hist_completo_carteiras.png, roic_hist_completo.csv
Uso: python3 backtest/roic_hist_completo.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
from trajetorias import annual  # noqa: E402
from validation_core import load_prices, universe_table  # noqa: E402
from roic_dispersao import group, SEC_PT  # noqa: E402

CUT = 0.30
pc = lambda x: '—' if pd.isna(x) else (f'{x:.0%}' if np.isfinite(x) else '∞')


def measure(r, down=False):
    """r: Series ROIC por exercicio (indice = ano). Variacoes so entre anos consecutivos."""
    r = r.dropna()
    if len(r) < 2: return np.nan, 0
    d = pd.Series(np.diff(r.values), index=r.index[1:])[np.diff(r.index.values) == 1]
    if down: d = d.clip(upper=0)
    mu = r.mean()
    if len(d) == 0: return np.nan, 0
    return (d.abs().mean() / mu if mu > 0 else np.inf), len(d)


def main():
    t = universe_table().set_index('ticker')
    spl = load_prices()['stock_splits']
    sec, ind = bm.sector_maps()
    ser, rows = {}, []
    for tk, r in t.iterrows():
        try:
            s = spl[tk][spl[tk] > 0] if tk in spl else pd.Series(dtype=float)
            a = annual(tk, bool(r.fin), s)
        except Exception:
            continue
        rr = a.roic.replace([np.inf, -np.inf], np.nan).dropna()
        rr = rr[rr.index >= 2005]
        ser[tk] = rr
        dsp, nd = measure(rr); ddn, _ = measure(rr, down=True)
        rows.append(dict(ticker=tk, fin=bool(r.fin), sector=sec(tk), industry=ind(tk), anos=len(rr), y0=rr.index.min() if len(rr) else np.nan,
                         y1=rr.index.max() if len(rr) else np.nan, roic_med=rr.mean() if len(rr) else np.nan, disp=dsp, disp_queda=ddn, n_var=nd))
    e = pd.DataFrame(rows).set_index('ticker')
    e = e[e.n_var >= 7].copy()  # pelo menos 8 anos seguidos
    e['volatil'] = e.disp > CUT; e['volatil_queda'] = e.disp_queda > CUT
    e['grp'] = [group(s, i) for s, i in zip(e.sector, e.industry)]
    e.to_csv(ROOT / 'roic_hist_completo.csv')

    out = ['# Volatilidade do ROIC com todo o histórico disponível (EUA)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10); financeiras e seguradoras de saúde usam ROE. Empresas com patrimônio negativo '
           'ou capital muito pequeno (ROIC > 100%, ainda em aberto) podem aparecer como voláteis por artefato do denominador.\n',
           '**Medida:** média de |ROIC do ano − ROIC do ano anterior| em **todo o histórico disponível** ÷ ROIC médio do mesmo período. '
           f'**> {pc(CUT)} = volátil.** Média ≤ 0 = volátil. Também mostro a versão **só com as quedas** (média das quedas ÷ ROIC médio; '
           'subidas contam zero), que separa ciclo de crescimento.\n',
           f'Base: {len(e)} empresas que foram do S&P 500 em algum momento desde 2011 e têm ≥ 8 anos seguidos de ROIC na SEC '
           f'(mediana de {e.anos.median():.0f} anos, em geral 2008–2025).\n']
    # 1) grupos
    out += ['## 1. Os grupos cíclicos que definimos\n',
            '| Grupo | Empresas | **% voláteis (histórico completo)** | Dispersão mediana | % voláteis só nas quedas | Dispersão mediana só nas quedas |', '|---|---|---|---|---|---|']
    for k in ['Energia', 'Materiais', 'Vestuário', 'Cíclicos duros', 'Demais']:
        x = e[e.grp == k]
        out.append(f'| {k} | {len(x)} | **{pc(x.volatil.mean())}** | {pc(x.disp.median())} | {pc(x.volatil_queda.mean())} | {pc(x.disp_queda.median())} |')
    out.append(f'| *Todas* | {len(e)} | {pc(e.volatil.mean())} | {pc(e.disp.median())} | {pc(e.volatil_queda.mean())} | {pc(e.disp_queda.median())} |')
    out += ['', '### Subsetores das nossas listas\n', '| Subsetor | Grupo | Empresas | % voláteis | Dispersão mediana | Só quedas: mediana | Empresas (dispersão) |', '|---|---|---|---|---|---|---|']
    for (g_, i), x in e[e.grp != 'Demais'].groupby(['grp', 'industry']):
        nm = ', '.join(f'{tk} {pc(v)}' for tk, v in x.disp.sort_values(ascending=False).items())
        out.append(f'| {i} | {g_} | {len(x)} | {pc(x.volatil.mean())} | {pc(x.disp.median())} | {pc(x.disp_queda.median())} | {nm} |')
    # 2) microsetores
    s = e.groupby(['sector', 'industry']).agg(emp=('disp', 'size'), vol=('volatil', 'mean'), med=('disp', 'median'), medq=('disp_queda', 'median'),
                                              volq=('volatil_queda', 'mean'), grp=('grp', 'first'))
    s = s[s.emp >= 3].reset_index()
    out += ['', '## 2. Microsetores por macrossetor (≥ 3 empresas), ordenados pela dispersão mediana\n',
            '✔ = já está nas nossas listas. **candidato** = fora das listas e com dispersão mediana > 30%.\n']
    order = e.groupby('sector').disp.median().sort_values(ascending=False).index
    for sct in order:
        x = s[s.sector == sct]
        if x.empty: continue
        xe_ = e[e.sector == sct]
        out += [f'### {SEC_PT.get(sct, sct)} — dispersão mediana {pc(xe_.disp.median())}; {pc(xe_.volatil.mean())} das empresas voláteis\n',
                '| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |', '|---|---|---|---|---|---|---|']
        for _, r in x.sort_values('med', ascending=False).iterrows():
            flag = '✔' if r.grp != 'Demais' else ('**candidato**' if r.med > CUT else '')
            out.append(f'| {r.industry} | {r.emp} | {pc(r.med)} | {pc(r.vol)} | {pc(r.medq)} | {pc(r.volq)} | {flag} |')
        out.append('')
    cand = s[(s.grp == 'Demais') & (s.med > CUT)].sort_values('med', ascending=False)
    out += ['### Resumo: candidatos fora das listas (dispersão mediana > 30% no histórico completo)\n',
            '| Subsetor | Macrossetor | Empresas | Dispersão mediana | Só quedas: mediana | Empresas mais voláteis |', '|---|---|---|---|---|---|']
    for _, r in cand.iterrows():
        nm = ', '.join(f'{tk} {pc(v)}' for tk, v in e[e.industry == r.industry].disp.sort_values(ascending=False).head(6).items())
        out.append(f'| {r.industry} | {SEC_PT.get(r.sector, r.sector)} | {r.emp} | {pc(r.med)} | {pc(r.medq)} | {nm} |')
    st = s[(s.grp != 'Demais') & (s.med <= CUT)]
    out += ['', '**Nas nossas listas, mas com dispersão mediana ≤ 30% no histórico completo:** ' +
            (', '.join(f'{r.industry} ({pc(r.med)})' for _, r in st.sort_values('med').iterrows()) or 'nenhum')]

    # 3) carteiras: versao point-in-time (todo o historico ate a data)
    f, dates = bm.base_data()
    disp_pit, dq_pit = [], []
    for r in f[['date', 'ticker']].itertuples():
        rr = ser.get(r.ticker)
        if rr is None or rr.empty: disp_pit.append(np.nan); dq_pit.append(np.nan); continue
        lim = r.date.year - 1 if r.date >= pd.Timestamp(r.date.year, 6, 30) else r.date.year - 2
        x = rr[rr.index <= lim]
        d1, nd = measure(x); d2, _ = measure(x, down=True)
        disp_pit.append(d1 if nd >= 4 else np.nan); dq_pit.append(d2 if nd >= 4 else np.nan)
    f['disp_hist'], f['disp_hist_q'] = disp_pit, dq_pit
    stab_all = (f.disp_hist <= CUT).to_numpy(); stab_q = (f.disp_hist_q <= CUT).to_numpy()
    cA = bm.classify_new(f, stability=stab_all); hA = bm.holdings_new(cA)
    cQ = bm.classify_new(f, stability=stab_q); hQ = bm.holdings_new(cQ)
    extra = {'OoL novo + estável no histórico (≤ 30%)': (cA, hA['OoL novo']), 'GCGR novo + estável no histórico': (cA, hA['GCGR novo']),
             'High ROIC + estável no histórico': (cA, hA['OoL High ROIC (novo)']), 'High Growth + estável no histórico': (cA, hA['OoL High Growth (novo)']),
             'OoL novo + quedas ≤ 30% no histórico': (cQ, hQ['OoL novo']), 'GCGR novo + quedas ≤ 30% no histórico': (cQ, hQ['GCGR novo'])}
    navs, n, dts, adj = bm.load_benchmarks(extra)
    out += ['', '## 3. Carteiras: estabilidade medida com todo o histórico até cada data (point-in-time)\n',
            'Em cada trimestre, a medida usa todos os exercícios já disponíveis (exercício y só conta a partir de 30/06 de y+1), com no mínimo 5 anos seguidos. '
            'As 8 linhas obrigatórias primeiro; depois as versões que exigem ROIC estável (todas as variações) e só quedas.\n'] + bm.bench_table(navs, n)
    # desempenho por posicao
    c0 = bm.classify_new(f)
    px = adj.reindex(pd.DatetimeIndex(dts), method='ffill'); fwd = px.shift(-1) / px - 1
    c0['rq'] = [fwd.at[d, tk] for d, tk in zip(c0.date, c0.ticker)]
    c0 = c0[c0.date < dts[-1]]; uq = c0[c0.cat.notna()].groupby('date').rq.mean(); c0['ex'] = c0.rq - c0.date.map(uq)
    out += ['', '### Posições da OoL e GCGR novas, por estabilidade no histórico até a data\n',
            '| Classe | Medida | Grupo | Posições | Excesso médio a.a. | Excesso mediano a.a. |', '|---|---|---|---|---|---|']
    for cat, lab in ((bm.OOL, 'OoL novo'), (bm.GCGR, 'GCGR novo')):
        x = c0[(c0.cat == cat) & ~c0.excluded]
        for mlab, col in (('todas as variações', 'disp_hist'), ('só quedas', 'disp_hist_q')):
            for gl, m in (('estável', x[col] <= CUT), ('volátil', x[col] > CUT)):
                y = x[m]; out.append(f'| {lab} | {mlab} | {gl} | {len(y)} | {y.ex.mean() * 4:+.1%} | {y.ex.median() * 4:+.1%} |'.replace('.', ','))
    (ROOT / 'roic_hist_completo.md').write_text('\n'.join(out))
    print('\n'.join(out))
    bm.bench_plot(navs, ROOT / 'roic_hist_completo_carteiras.png', 'Comparativos obrigatórios + estabilidade do ROIC no histórico completo até cada data')
    top = s.sort_values('med', ascending=False).head(35).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 11), dpi=130)
    col = {'Energia': '#bf8700', 'Materiais': '#8c6d1f', 'Vestuário': '#cf222e', 'Cíclicos duros': '#e8590c', 'Demais': '#1f6feb'}
    ax.barh(range(len(top)), top.med.clip(upper=2) * 100, color=[col[x] for x in top.grp])
    ax.scatter(top.medq.clip(upper=2) * 100, range(len(top)), color='black', s=14, zorder=3, label='Só quedas (mediana)')
    ax.set_yticks(range(len(top))); ax.set_yticklabels([f'{r.industry} ({r.emp})' for _, r in top.iterrows()], fontsize=8)
    ax.axvline(30, color='black', ls=':', lw=1); ax.set_xlabel('Dispersão mediana do ROIC no histórico completo (%; limitada a 200%)'); ax.grid(alpha=.3, axis='x')
    for k, v in col.items(): ax.barh([], [], color=v, label=k if k != 'Demais' else 'Fora das listas')
    ax.legend(fontsize=8, loc='lower right'); ax.set_title('Os 35 subsetores com ROIC mais volátil no histórico completo (nº de empresas)', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'roic_hist_completo.png'); plt.close(fig)


if __name__ == '__main__':
    main()
