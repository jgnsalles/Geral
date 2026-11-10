"""Relatorio da regua de setores ciclicos e da classe Cyclicals, com os comparativos obrigatorios.
Saidas: backtest/ciclicos.md, backtest/ciclicos_regua.png, backtest/ciclicos_carteiras.png
Uso: python3 backtest/ciclicos_analise.py"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import ciclicos as cy  # noqa: E402
import benchmarks as bm  # noqa: E402
from backtest import D  # noqa: E402

SEC_PT = {'Consumer Discretionary': 'Consumo discricionário', 'Consumer Staples': 'Consumo básico', 'Energy': 'Energia', 'Materials': 'Materiais',
          'Industrials': 'Indústria', 'Information Technology': 'Tecnologia', 'Financials': 'Financeiro', 'Communication Services': 'Comunicação',
          'Health Care': 'Saúde', 'Utilities': 'Utilidades públicas', 'Real Estate': 'Imobiliário'}
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
n1 = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def main():
    S, e, ref, cut = cy.build()
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    out = ['# Setores cíclicos: régua por subsetor e a classe Cyclicals (EUA)\n',
           '> ⚠️ **ROIC:** a régua usa o histórico completo do ROIC oficial (corrigido em 2026-11-10; financeiras e seguradoras de saúde com ROE). '
           'Subsetores de capital muito pequeno ou patrimônio negativo (distribuidoras de saúde, algumas seguradoras) podem passar por artefato do denominador.\n',
           '## 1. A régua\n',
           'Olha o **setor, não a empresa**, e usa **só fundamentos** (nenhum retorno de ação entra). Para cada empresa, em todo o histórico da SEC (em geral 2008–2025):\n',
           '- **Queda média** = média das quedas do ROIC de um ano para o outro (subidas contam zero) ÷ ROIC médio. Mede quanto o ROIC costuma perder quando cai, '
           'em proporção ao seu nível. Contar só as quedas separa ciclo de crescimento: quem só sobe tem queda média baixa.',
           '- **Colapsos** = quantas vezes o ROIC caiu para a metade ou menos do maior valor dos 3 anos anteriores (episódios distintos). Mede se o tombo se repete.\n',
           'O subsetor recebe a **mediana** das suas empresas (empresas com ROIC médio ≤ 0 ficam fora). Subsetor com uma só empresa é decidido na indústria GICS '
           'imediatamente acima, junto com os subsetores irmãos.\n',
           f'**Régua:** cíclico se **queda média ≥ 2× a dos setores defensivos** (consumo básico + utilidades: {pc(ref)}, logo corte em **{pc(cut)}**) '
           f'**e** **mediana de colapsos ≥ 2** (o ROIC já foi à metade ao menos duas vezes).\n',
           '*Por que 2×:* é o ponto em que o ROIC perde, nas quedas, o dobro do que perde num setor defensivo típico. Âncoras: consumo básico e utilidades ficam '
           'entre 4% e 25%; petróleo, aço, fertilizantes e químicos básicos ficam entre 36% e 70%. O corte de 30% cai no meio do vão entre os dois grupos.\n']
    # sensibilidade
    v = e[e.queda.notna()]
    sens = []
    for mult in (1.5, 2.0, 2.5):
        c_ = mult * ref
        sens.append((mult, set(S[(S.queda >= c_) & (S.colapsos >= 2) & (S.empresas >= 2)].industry)))
    base = sens[1][1]
    out += ['**Sensibilidade do multiplicador:** ' + '; '.join(
        f'{m:g}× ({pc(m * ref)}): {len(s_)} subsetores' + (f" (entram {', '.join(sorted(s_ - base))})" if s_ - base else '') +
        (f" (saem {', '.join(sorted(base - s_))})" if base - s_ else '') for m, s_ in sens) + '\n']
    # 2) lista
    cyc = S[S.ciclico].sort_values('queda', ascending=False)
    emp = lambda ind: ', '.join(f"{t} ({pc(r.queda)}; {r.colapsos:.0f})" for t, r in e[e.industry == ind].sort_values('queda', ascending=False).iterrows())
    out += ['## 2. Subsetores cíclicos pela régua\n',
            '| Subsetor | Macrossetor | Empresas | Queda média (mediana) | Colapsos (mediana) | Nível da decisão | Empresas (queda média; colapsos) |', '|---|---|---|---|---|---|---|']
    for _, r in cyc.iterrows():
        out.append(f'| **{r.industry}** | {SEC_PT.get(r.sector, r.sector)} | {r.empresas:.0f} | {pc(r.queda)} | {r.colapsos:.1f} | {r.nivel} | {emp(r.industry)} |'.replace('.0 |', ' |'))
    near = S[~S.ciclico & ((S.queda >= 0.8 * cut) | (S.colapsos >= 2) & (S.queda >= 0.6 * cut))].sort_values('queda', ascending=False)
    out += ['', '### Perto da linha, mas fora (não cíclicos pela régua)\n', '| Subsetor | Macrossetor | Empresas | Queda média | Colapsos | Por que ficou fora |', '|---|---|---|---|---|---|']
    for _, r in near.iterrows():
        why = []
        if r.queda < cut: why.append(f'queda média < {pc(cut)}')
        if r.colapsos < 2: why.append('menos de 2 colapsos')
        if r.empresas < 2: why.append('uma empresa só')
        out.append(f'| {r.industry} | {SEC_PT.get(r.sector, r.sector)} | {r.empresas:.0f} | {pc(r.queda)} | {r.colapsos:.1f} | {", ".join(why)} |')
    # por macrossetor
    out += ['', '### Quanto de cada macrossetor é cíclico\n', '| Macrossetor | Subsetores | Cíclicos | Quais |', '|---|---|---|---|']
    for sct, x in S.groupby('sector'):
        out.append(f"| {SEC_PT.get(sct, sct)} | {len(x)} | {x.ciclico.sum()} | {', '.join(x[x.ciclico].industry) or '—'} |")
    # 3) carteiras
    f, dates = bm.base_data()
    old_new = bm.vp.classify(f.assign(zroic=0.0), 'sketch', 'B')
    sec, ind = bm.sector_maps(); old_new['sector'] = old_new.ticker.map(sec); old_new['industry'] = old_new.ticker.map(ind)
    exc_prev = old_new.sector.isin({'Energy', 'Materials'}) | old_new.industry.isin(bm.APPAREL)
    extra = {'OoL novo da rodada anterior (sem Energia, Materiais e vestuário)': (old_new, (old_new.cat == bm.OOL) & ~exc_prev),
             'OoL sem nenhuma exclusão de setor': (old_new, old_new.cat == bm.OOL)}
    navs, n, dts, adj = bm.load_benchmarks(extra)
    out += ['', '## 3. Carteiras com a classe Cyclicals\n',
            '**Novo** = esboço (ROIC 12%), sem zROIC, sem vestuário e **sem os subsetores cíclicos da régua**. As ações desses subsetores que seriam OoL ou GCGR '
            'formam a classe **Cyclicals**. Energia e Materiais deixam de ser excluídos em bloco: dutos, químicos especiais, materiais de construção, gases '
            'industriais e embalagens voltam a poder entrar na OoL.\n'] + bm.bench_table(navs, n)
    # quem e a classe Cyclicals
    c = bm.classify_new(f)
    px = adj.reindex(pd.DatetimeIndex(dts), method='ffill'); fwd = px.shift(-1) / px - 1
    c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    cc = c[c.date < dts[-1]]; uq = cc[cc.cat.notna()].groupby('date').rq.mean(); cc = cc.assign(ex=cc.rq - cc.date.map(uq))
    m = cc.cat.isin([bm.OOL, bm.GCGR]) & cc.cyclical & ~cc.industry.isin(bm.APPAREL)
    a = cc[m].groupby('ticker').agg(q=('ex', 'size'), ex=('ex', 'mean'), ind=('industry', 'first'),
                                    cls=('cat', lambda s: '/'.join(sorted({'OoL' if x == bm.OOL else 'GCGR' for x in s})))).sort_values('ex')
    a['ex'] *= 4
    nm = lambda t: u.name.get(t, t) if t in u.index else t
    out += ['', '### Quem está na classe Cyclicals\n',
            f'{len(a)} empresas, {cc[m].groupby("date").size().mean():.0f} ações por trimestre em média. Excesso médio por posição: ' +
            f'{cc[m].ex.mean() * 4:+.1%}'.replace('.', ',') + '; mediano: ' + f'{cc[m].ex.median() * 4:+.1%}'.replace('.', ',') + '.\n',
            '| Ticker | Empresa | Subsetor | Viria de | Trimestres | Excesso médio a.a. |', '|---|---|---|---|---|---|']
    for t, r in a.iterrows():
        out.append(f'| {t} | {nm(t)} | {cy.canon(r.ind)} | {r.cls} | {r.q} | {r.ex:+.0%} |')
    (ROOT / 'ciclicos.md').write_text('\n'.join(out))
    print('\n'.join(out))
    bm.bench_plot(navs, ROOT / 'ciclicos_carteiras.png', 'Comparativos obrigatórios com a classe Cyclicals — universo point-in-time, retorno total acumulado')
    # grafico da regua
    x = S[S.empresas >= 2].copy()
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=130)
    colors = np.where(x.ciclico, '#cf222e', np.where(x.sector.isin(cy.DEFENSIVE_SECTORS), '#2da44e', '#8c959f'))
    ax.scatter(x.queda.clip(upper=1.0) * 100, x.colapsos + np.random.default_rng(0).uniform(-.12, .12, len(x)), s=18 + x.empresas * 8, c=colors, alpha=.75, edgecolor='white')
    for _, r in x[x.ciclico | (x.queda > .25)].iterrows():
        ax.annotate(r.industry, (min(r.queda, 1.0) * 100, r.colapsos), fontsize=6.5, xytext=(3, 3), textcoords='offset points')
    ax.axvline(cut * 100, color='black', ls='--', lw=1); ax.axhline(1.5, color='black', ls=':', lw=1)
    ax.fill_between([cut * 100, 105], 1.5, 5, color='#cf222e', alpha=.06)
    ax.set_xlim(0, 105); ax.set_xlabel('Queda média do ROIC (mediana do subsetor, % do ROIC médio; limitada a 100%)'); ax.set_ylabel('Colapsos do ROIC (mediana)')
    ax.scatter([], [], c='#cf222e', label='Cíclico pela régua'); ax.scatter([], [], c='#2da44e', label='Defensivo (referência)'); ax.scatter([], [], c='#8c959f', label='Demais')
    ax.legend(fontsize=8, loc='upper left'); ax.grid(alpha=.3)
    ax.set_title(f'Régua de setores cíclicos: queda média ≥ {pc(cut)} (2× a dos defensivos) e ≥ 2 colapsos — cada ponto é um subsetor', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'ciclicos_regua.png'); plt.close(fig)


if __name__ == '__main__':
    main()
