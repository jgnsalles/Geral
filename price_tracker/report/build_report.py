"""Gera o relatorio em PDF da rodada 2 (ROIC com capital operacional quando patrimonio <= 0).
Uso: python3 report/build_report.py"""
import sys, re, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt

R = pathlib.Path(__file__).parent; PT = R.parent
sys.path[:0] = [str(R), str(PT), str(PT / 'backtest'), str(PT / 'brasil')]
from pdfkit import P, bullets, table, img, build, md_tables, find_table, S, PageBreak, Spacer, KeepTogether, cm  # noqa: E402
import summarize  # noqa: E402

B, BR = PT / 'backtest', PT / 'brasil'
OUT = R / 'Relatorio_Price_Tracker_Rodada2.pdf'


def md_to_cells(md):
    lines = [l for l in md.splitlines() if l.startswith('|')]
    return [[c.strip() for c in l.strip().strip('|').split('|')] for i, l in enumerate(lines) if i != 1]


def cols(cells, keep):
    return [[r[i] for i in keep] for r in cells] if cells else None


def brazil_chart(path):
    import run_v3 as v3, backtest_br as bb
    from backtest import run_portfolio
    x, close = v3.prepare(); c = v3.classify(x, 2.93)
    adj = pd.read_csv(v3.D / 'prices_adj_close.csv.gz', index_col=0, parse_dates=True)
    cov = c.groupby('date').cat.apply(lambda s: s.notna().sum()); start = cov[cov >= v3.MIN_N].index.min()
    dates = [d for d in bb.rebalance_dates(close) if d >= start]; c = c[c.date >= start]
    navs = {}
    for cat in ('Opportunity of Lifetime', 'Good Companies, Great Returns'):
        navs[cat] = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat == cat].groupby('date')}, adj, dates)[0]
    navs['Universo EW'] = run_portfolio({d: g.ticker.tolist() for d, g in c[c.cat.notna()].groupby('date')}, adj, dates)[0]
    for b in ('BOVA11.SA', 'SMAL11.SA'):
        nb = adj[b].loc[dates[0]:dates[-1]].dropna(); navs[b.replace('.SA', '')] = nb / nb.iloc[0]
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    sty = {'Opportunity of Lifetime': ('#1f6feb', '-', 2.4), 'Good Companies, Great Returns': ('#e8590c', '-', 2.4),
           'Universo EW': ('#57606a', '--', 1.6), 'BOVA11': ('#000000', '--', 1.6), 'SMAL11': ('#8c959f', ':', 1.6)}
    for k, (col, ls, lw) in sty.items():
        s = (navs[k] - 1) * 100
        ax.plot(s.index, s, color=col, ls=ls, lw=lw, label=f'{k} ({s.iloc[-1]:+.0f}%)'.replace('.', ','))
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:.0f}%')); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Brasil (v3): retorno total acumulado, equal weight, rebalanceamento trimestral', fontsize=10)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def venn_summary():
    t = (PT / 'report_ool_2026-11-09.md').read_text()
    rows = [['Grupo', 'N', 'Empresas']]
    for sec in t.split('## ')[1:]:
        name = sec.split('\n')[0]
        tks = [l.split('|')[1].strip() for l in sec.splitlines() if l.startswith('|') and not l.startswith('| ticker') and not l.startswith('|:')]
        m = re.match(r'(.+) \((\d+)\)', name)
        if m: rows.append([m.group(1), m.group(2), ', '.join(tks) or '—'])
    return rows


def attribution_cells(cat_heading, which):
    t = md_tables(B / 'attribution_2.93.md')
    secs = [cells for h, cells in t if which in h.lower()]
    idx = 0 if cat_heading == 'ool' else 1
    cells = secs[idx]
    return cols(cells, [0, 1, 2, 3, 4, 6, 8])


def main():
    st = []
    title = 'Price Tracker: relatório da rodada 2'
    # capa
    st += [Spacer(1, 2.2 * cm), P('Price Tracker', 'title'), P('Relatório da rodada 2: backtests, diagnósticos e Brasil, com o ROIC corrigido para patrimônio negativo', 'subtitle'),
           P('Novembro de 2026 · dados até 30/09/2026 (backtests) e 09/11/2026 (modelo atual)', 'small'), Spacer(1, 0.6 * cm),
           P('⚠️ **ROIC:** todos os resultados dependem da definição de ROIC. Nesta rodada, o capital investido passou a usar o capital operacional '
             '(imobilizado + capital de giro) quando o patrimônio é negativo ou quando patrimônio + dívida − caixa ≤ 0. Ainda ficam pendentes: '
             'caixa excessivo (ex.: Doximity, Manhattan Associates), intangíveis de aquisições (ex.: AbbVie, FICO), negócios asset-light com capital de giro '
             'negativo (MSCI, Hilton, Marriott seguem sem ROIC) e a revisão dos cortes de 20%/10%, desenhados para a fórmula do Wisesheets.', 'warn'),
           P('Sumário executivo', 'h1')]
    st += bullets([
        '**A correção do ROIC mexeu pouco.** 6,4% das observações (70 empresas) passaram a usar capital operacional e só 1,3% das classificações mudaram (44 empresas). No Brasil, nenhuma classe da versão final mudou.',
        '**Good Companies, Great Returns é a classe mais robusta.** EUA 2012–2026: 20,7% a.a., +4,0 p.p. sobre a contraprova (universo equal weight, 16,5%), t = 3,1; ganha nos dois subperíodos, nos dois cortes de zGrowth e nos 6 cenários de P/E justo. No Brasil: 14,7% a.a., +1,3 p.p. sobre a contraprova e +2,6 p.p. sobre o Ibovespa.',
        '**Opportunity of Lifetime não se sustenta sozinha.** EUA: 18,1% a.a., +2,1 p.p., t = 1,0, todo o ganho em 2020–2026 e dependente de 5 nomes (sem eles, empata com a contraprova). Brasil: −6,7% a.a. com 3 ações em média.',
        '**Por que Good Companies, Great Returns ganha:** o ganho vem de empresas excelentes com ROIC entre 10% e 20% (+2,2 p.p. dos +1,9 p.p. de diferença). A Opportunity of Lifetime paga mais caro (P/L 23,7 contra 19,6) pela perfeição já precificada e entra tarde: ações que acabaram de virar Opportunity of Lifetime rendem 11,4% a.a. no trimestre seguinte; as que caem dela para Good Companies, Great Returns rendem 37,4%.',
        '**O retorno esperado do modelo não ordena dentro das classes:** prometer 25% ou 130% a.a. leva ao mesmo realizado mediano (~14% a.a. em 3 anos).',
        '**O viés de sobrevivência é grande:** a contraprova supera o RSP (S&P 500 equal weight real) em ~4,6 p.p. a.a. nos EUA e o SMAL11 em ~6 p.p. no Brasil. Por isso a comparação justa é contra a contraprova.',
        '**ROIC estável não é premiado e ROIC "instável" é em boa parte artefato** de capital investido perto de zero; a investigação do ROIC continua sendo a prioridade.'])
    st.append(PageBreak())

    # 2. o que mudou
    st += [P('1. O que mudou nesta rodada', 'h1'),
           P('**Regra nova de capital investido (empresas operacionais):** padrão = patrimônio + dívida − caixa. Se o patrimônio for ≤ 0 (tipicamente por recompras) '
             'ou esse valor for ≤ 0, usa o capital operacional = imobilizado líquido + (ativo circulante − caixa) − (passivo circulante − dívida de curto prazo). '
             'Financeiras continuam com ROE. Novos dados coletados: imobilizado, ativo circulante e dívida de curto prazo (SEC e CVM).'),
           table([['Empresa', 'Patrimônio', 'ROIC antes', 'ROIC agora', 'Observação'],
                  ['Domino\'s', 'negativo', 'sem ROIC', '135%', 'franquia, pouco capital'],
                  ['Philip Morris', 'negativo', 'sem ROIC', '~200%', 'intangíveis fora do capital operacional'],
                  ['McDonald\'s', 'negativo', 'sem ROIC', '35%', 'coerente'],
                  ['AutoZone / Starbucks', 'negativo', 'sem ROIC', '51% / 55%', 'coerente'],
                  ['McKesson', 'pequeno', '1.066%', '29%', 'distorção corrigida'],
                  ['AbbVie / FICO', 'negativo', '21% / 57%', '184% / 417%', '**inflado:** ágio e intangíveis de aquisição ficam fora'],
                  ['MSCI, Hilton, Marriott', 'negativo', 'sem ROIC', 'sem ROIC', 'capital operacional também negativo (asset-light)']],
                 widths=[4 * cm, 2.3 * cm, 2.4 * cm, 2.6 * cm, 6.3 * cm]), Spacer(1, 6),
           P('**Impacto:** nos EUA, 6,4% das observações trimestrais (70 empresas) usam capital operacional em ao menos um ano da janela; 1,3% das classificações mudaram '
             '(44 empresas). Na Opportunity of Lifetime entram, em algum momento, CPRT, DVA, FICO, FTNT, LYV, TDG e VRSN e saem trimestres de DELL, DXCM, IDXX, IQV, LII, MAS, MO, '
             'MSI, VRSK, WYNN e YUM. No Brasil, 108 de 7.165 observações tiveram o ROIC alterado em mais de 1 p.p., sem efeito nas classes da versão final.'),
           P('**Resultado em uma linha:** os números da rodada 2 ficam a ±0,5 p.p. dos da rodada 1 nas classes principais; todas as conclusões se mantêm.')]
    o = pd.read_csv(PT / 'backtest/data/stats_zg2.93.csv').set_index('Carteira')
    st.append(Spacer(1, 4))

    # 3. historico
    st += [P('2. Linha do tempo das decisões', 'h1')]
    st += bullets([
        '**Planilha:** estratégia decodificada (Growth, zGrowth, ROIC, zROIC, retorno → 37 combinações → 11 classes). Corrigido o bug do zROIC (incluía a coluna U, o g) e removido o P/E fixo de 25 da Amazon.',
        '**Replicação em Python:** o motor reproduz as 224 classes do Excel. Descobertas sobre o Wisesheets: ROIC = NOPAT ÷ (ativo total − passivo circulante); no setor financeiro o "ROIC" é ROE; Growth = média de (mediana, média, média dos 2 últimos anos); financeiras com g próprio (6,5% → 3%).',
        '**Fonte gratuita (híbrido):** Yahoo (2 anos de projeção) + SEC. Concordância com o Wise ~60%; o teto é o horizonte de projeção (2 anos contra 4).',
        '**Decisões do usuário:** ROIC clássico (patrimônio + dívida − caixa) para operacionais e ROE para financeiras; ranking do g pela mediana de 5 anos do crescimento realizado; nesta rodada, capital operacional quando o patrimônio é negativo.',
        '**Backtest:** só o método histórico (P2) é testável sem olhar o futuro; point-in-time pela data de arquivamento na SEC/CVM; equal weight, rebalanceamento trimestral; universo S&P 500 atual + planilha (541 empresas) e B3 com liquidez.',
        '**Testados e descartados:** P/E justo com ROIC normalizado e em dois estágios; g máximo de 6%; ROIC marginal e média no P/E justo; limites de P/L e de salto de lucro; exclusões setoriais.',
        '**Brasil:** CVM (2010+), WACC 11%, g 9,5% → 6% (igual para financeiras), cortes de crescimento/retorno + 2,5 p.p., ROIC alto 17%, liquidez ≥ R$ 10 mi/dia.'])
    st.append(PageBreak())

    # 4. modelo atual
    st += [P('3. Modelo atual: Opportunity of Lifetime no Excel, no P1 (estimativas) e no P2 (histórico)', 'h1'),
           P('Snapshot de 09/11/2026. Excel = Wisesheets (ROIC do Wise); P1 = Yahoo com 2 anos projetados; P2 = só histórico. P1 e P2 com o ROIC da rodada 2.'),
           table(venn_summary(), widths=[4.6 * cm, 1.2 * cm, 11.8 * cm]), Spacer(1, 4),
           P('Os 7 nomes nos três (núcleo robusto) são a base mais confiável. O P2 ainda inclui muitos exclusivos porque o corte de zGrowth recalibrado (2,93) quase não filtra.', 'small')]

    # 5. backtest EUA
    t293 = md_to_cells(summarize.table('zg2.93'))
    st += [P('4. Backtest EUA: uma carteira por classe (2012–2026)', 'h1'),
           P('Classificação point-in-time (só balanços já arquivados na SEC), equal weight, rebalanceamento no último pregão de cada trimestre, retorno total. '
             '"vs Universo EW" = excesso sobre a contraprova; t ≳ 2 é significativo. Corte de zGrowth 2,93 (o corte de 0,9 dá a mesma ordem).'),
           table(cols(t293, [0, 1, 2, 4, 5, 6, 7, 8, 9]), widths=[5.2 * cm] + [1.55 * cm] * 8), Spacer(1, 6),
           img(B / 'classes_zg2.93.png', width=17.6 * cm),
           P('**Leitura:** Good Companies, Great Returns é a melhor e a única com significância clara; Interesting but Requires Attention aparece bem, mas pode ter viés de seleção. '
             'Opportunity of Lifetime fica acima da contraprova, abaixo do QQQ e sem significância. As classes de baixo (Investable but Not Good, Good but Margin of Safety Required, Excellent but Fair) perdem.')]
    st.append(PageBreak())

    # 6. diagnostico
    d = B / 'diagnose_2.93.md'
    st += [P('5. Diagnóstico: por que Good Companies, Great Returns supera Opportunity of Lifetime (EUA)', 'h1'),
           P('**Tamanho** (a hipótese de carteira grande demais não se confirma):', 'h2'), table(find_table(d, 'Tamanho'), widths=[6 * cm, 5.8 * cm, 5.8 * cm]),
           P('**Qual defeito gera a diferença** (Good Companies, Great Returns = Opportunity of Lifetime com um defeito):', 'h2'),
           table(find_table(d, 'De onde vem'), widths=[4.4 * cm] + [2.2 * cm] * 6),
           P('**Perfil na compra:**', 'h2'), table(find_table(d, 'Perfil'), widths=[8 * cm, 4.8 * cm, 4.8 * cm]),
           P('**Migração entre as classes (retorno no trimestre seguinte):**', 'h2'), table(find_table(d, 'Migração'), widths=[8 * cm, 4 * cm, 5.6 * cm]),
           P('**Leitura:** o ganho vem das empresas excelentes com ROIC um degrau abaixo (10–20%), mais baratas e menos disputadas. A Opportunity of Lifetime compra o "perfeito" depois que ele subiu: '
             'o lucro dela cresce mais no ano seguinte (10,8% contra 4,6%), mas a ação rende menos porque o mercado já cobrava pela qualidade.')]
    st.append(PageBreak())

    # 7. cenarios
    sc = md_tables(B / 'scenarios.md')[0][1]
    st += [P('6. Ajustes testados no P/E justo: g máximo × ROIC usado no P/E justo', 'h1'),
           P('Cada célula: CAGR (excesso a.a. sobre a contraprova; t) · ações em média. Corte de zGrowth 2,93.'),
           table(sc, widths=[3.6 * cm] + [2.33 * cm] * 6),
           P('**Leitura:** nenhum cenário melhora a Opportunity of Lifetime de forma relevante; baixar o g máximo para 6% a piora e manda para Excellent but Fair empresas que iam bem. '
             'Good Companies, Great Returns fica entre 20,0% e 20,7% em todos. Antes deste teste, o ROIC normalizado e o modelo de dois estágios também foram testados e descartados.')]

    # 8. atribuicao
    a = (B / 'attribution_2.93.md').read_text()
    lines = [l[2:] for l in a.splitlines() if l.startswith('- CAGR') or l.startswith('- Sem as')]
    st += [P('7. Atribuição por ação (EUA)', 'h1'),
           table([['', 'Opportunity of Lifetime', 'Good Companies, Great Returns'],
                  ['Retorno anual', '18,1%', '20,7%'], ['Sem as 5 maiores', '16,3% (≈ contraprova)', '19,7%'], ['Sem as 10 maiores', '15,5%', '18,7%'],
                  ['Sem as 15 maiores', '14,5%', '18,0%'], ['Peso das 15 maiores', '37%', '23%'], ['Sem as 10 piores', '20,6%', '22,1%']],
                 widths=[5 * cm, 6.3 * cm, 6.3 * cm]),
           P('**Opportunity of Lifetime: maiores contribuições**', 'h2'), table(attribution_cells('ool', 'maiores')[:11], widths=[0.8 * cm, 1.6 * cm, 5 * cm, 4 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm]),
           P('**Opportunity of Lifetime: menores contribuições**', 'h2'), table(attribution_cells('ool', 'menores')[:11], widths=[0.8 * cm, 1.6 * cm, 5 * cm, 4 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm]),
           P('**Good Companies, Great Returns: maiores contribuições**', 'h2'), table(attribution_cells('gcgr', 'maiores')[:11], widths=[0.8 * cm, 1.6 * cm, 5 * cm, 4 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm]),
           P('**Good Companies, Great Returns: menores contribuições**', 'h2'), table(attribution_cells('gcgr', 'menores')[:11], widths=[0.8 * cm, 1.6 * cm, 5 * cm, 4 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm]),
           P('**Leitura:** a Opportunity of Lifetime é uma aposta em poucos compounders grandes de tecnologia/IA (Arista, NVIDIA) segurados por anos; Good Companies, Great Returns ganha com '
             'empresas médias menos acompanhadas na hora da reprecificação (Fabrinet, Tower, Installed Building Products, Comfort Systems) e não depende de poucos nomes. '
             'Cirrus Logic e Kinsale aparecem como vencedoras numa classe e perdedoras na outra: o momento da entrada importa mais do que a empresa.')]
    st.append(PageBreak())

    # 9. distribuicoes e esperado x realizado
    e = B / 'expected_vs_realized_2.93.md'
    st += [P('8. Distribuições e retorno esperado × realizado', 'h1'), img(B / 'dist_attribution_2.93.png', width=15.5 * cm),
           table(find_table(e, 'Distribuições'), widths=[4.6 * cm] + [3.25 * cm] * 4),
           P('A Opportunity of Lifetime tem caudas mais gordas dos dois lados: perde mais vezes (38,4% das posições contra 35,0%) e compensa com poucos ganhos enormes (assimetria 1,9 contra 0,5).'),
           img(B / 'expected_vs_realized_2.93.png', width=15.5 * cm),
           table(find_table(e, 'duas classes juntas'), widths=[5 * cm, 3.5 * cm, 4.5 * cm, 4.6 * cm]),
           P('**Leitura:** o retorno esperado não prevê o realizado dentro das classes (correlação ≈ 0). O modelo superestima o nível (promete 25–130% a.a., entrega ~14%). '
             'Esperado acima de 100% tem mais chance de perda (18,8%), mas a mediana não cai: serve como alerta, não como filtro.')]
    st.append(PageBreak())

    # 10. piores casos
    w = B / 'worst_cases_2.93.md'
    pl = [l for l in w.read_text().splitlines() if l.startswith('- **P/L de entrada') or l.startswith('- **Retorno esperado')][:2]
    st += [P('9. Piores episódios da Opportunity of Lifetime: o que tinham na entrada', 'h1'),
           table(find_table(w, 'Perfil na entrada'), widths=[7 * cm, 3.5 * cm, 3.6 * cm, 3.5 * cm]),
           P('Retorno no trimestre seguinte por faixa (todas as posições da Opportunity of Lifetime):', 'small')] + [P(l[2:], 'small') for l in pl] + [
           P('**Leitura quantitativa:** os piores são quase iguais à média; destaca-se o **último crescimento anual do lucro** (41,8% contra 29,7%) com P/L **menor** (22,4 contra 26,1): lucro no pico. '
             'Limitar o P/L em 40x ou 60x, ou excluir saltos de lucro, não melhora a carteira de forma robusta (testado na rodada 1).'),
           P('**Leitura qualitativa (pesquisa dos casos):**', 'h2'),
           table([['Padrão', 'Exemplos', 'O que aconteceu'],
                  ['Lucro no pico do ciclo ou da pandemia (maior grupo)', 'AMAT 2017, CRUS 2017, WDC 2014, STM 2023, CF 2024, GNRC 2022, POOL, CHRW, TGT 2022', 'Entra logo após salto de lucro; o ciclo vira'],
                  ['Choque de produto ou regulação', 'BA e LUV 2018 (737 MAX), DXCM 2024 (carta de advertência da FDA), BIIB, HUM 2012', 'Evento específico'],
                  ['Marca de consumo perdendo força', 'LULU 2024, TPR 2012, DECK 2025, CMG 2023', 'Concorrência, tarifas, troca de CEO depois da queda'],
                  ['Crescimento que normaliza / aquisição grande', 'KNSL 2024, VRSK 2025, NFLX 2025 (Warner Bros), TTWO 2021', 'Mercado precificava a continuidade']],
                 widths=[4.6 * cm, 7.4 * cm, 5.6 * cm]),
           P('Checklist sugerido (não backtestável de forma honesta): lucro acima da tendência por ciclo? aquisição transformadora em curso? dependência de um cliente/produto/regulador? '
             'marca perdendo participação? A troca de CEO, nos casos vistos, veio depois da queda.', 'small')]

    # 11. setores
    sct = find_table(B / 'sectors_2.93.md', 'Opportunity of Lifetime')
    st += [P('10. Setores (Opportunity of Lifetime)', 'h1'), table(cols(sct, [0, 1, 2, 3, 4, 6, 7, 8, 9]), widths=[3.6 * cm] + [1.75 * cm] * 8),
           P('**Leitura:** nenhum setor justifica exceção. Tecnologia é o motor (excluir custa 2,6 p.p. a.a.); cíclicos têm alta dispersão e aparecem mais entre os melhores do que entre os piores. '
             'Industrial e Saúde vão mal na Opportunity of Lifetime, mas bem em Good Companies, Great Returns: o risco é o momento do ciclo, não o setor.')]
    st.append(PageBreak())

    # 12. zROIC
    zb = md_tables(B / 'zroic_breakdown.md')
    zu = md_tables(B / 'zroic_unstable.md')
    st += [P('11. Estabilidade do ROIC (zROIC) e ROIC marginal (EUA)', 'h1'),
           P('**Excluídas de Opportunity of Lifetime por ROIC médio, por faixa de zROIC:**', 'h2'), table(zb[3][1], widths=[3.6 * cm] + [1.75 * cm] * 8),
           P('**Mesmo grupo, terço mais instável, por ROIC marginal de 5 anos:**', 'h2'), table(zb[4][1], widths=[5.2 * cm] + [1.55 * cm] * 8),
           P('**Excluídas por ROIC instável (zROIC ≥ 0,7), em 5 faixas:**', 'h2'), table(zu[0][1], widths=[3.6 * cm] + [1.75 * cm] * 8),
           P('**Leitura:** a estabilidade do ROIC não é premiada (o ROIC mais estável é a faixa de menor excesso). Nas excluídas por ROIC médio, ROIC marginal **abaixo** do histórico '
             '(capital novo ainda sem retorno, fundo de ciclo) rendeu mais (+15,4 p.p., t = 2,2). No grupo "ROIC instável" não há padrão: boa parte da instabilidade vem de capital '
             'investido perto de zero (caixa excessivo, recompras), ou seja, é artefato de medição. O corte de 0,7 hoje barra empresas estáveis.')]
    st.append(PageBreak())

    # 13. Brasil
    roic_p = pd.read_csv(R / 'roic_paises.csv'); rp = [list(roic_p.columns)] + roic_p.astype(str).values.tolist()
    v3 = md_tables(BR / 'run_v3.md')
    brazil_chart(R / 'brasil_v3.png')
    st += [P('12. Brasil', 'h1'),
           P('Dados da CVM (DFP 2010+, point-in-time pela data de entrega), preços do Yahoo, B3 com liquidez ≥ R$ 10 mi/dia. Parâmetros: EUA + 2,5 p.p. (WACC 11%, g 9,5% → 6% igual para '
             'financeiras, crescimento 17,5%/8,5%, retorno 22,5%/10,5%) e ROIC alto de 17%. Período: 03/2015 a 09/2026, ~81 empresas classificadas por trimestre.'),
           P('**ROIC: Brasil × EUA (observações trimestrais 2014–2026):**', 'h2'), table(rp, widths=[5 * cm] + [2.1 * cm] * 6),
           P('A alíquota efetiva mediana é ~20% nos dois países; a diferença está no lucro operacional por capital investido (mix setorial: energia, saneamento, siderurgia, construção).', 'small'),
           P('**Resultado (corte de zGrowth 2,93):**', 'h2'), table(cols(v3[0][1], [0, 1, 2, 3, 4, 5, 6]), widths=[5.4 * cm] + [2.03 * cm] * 6),
           img(R / 'brasil_v3.png', width=15 * cm),
           P('**Atribuição:** a Opportunity of Lifetime depende da Unipar e sofre com CVC e Blau (sem a maior contribuição: −11,5% a.a.). Good Companies, Great Returns é espalhada '
             '(Bradesco, Yduqs, Cosan, CVC 2016–18, Magazine Luiza 2019–22; sem as 5 maiores ainda faz 10,6% a.a.). CVC e Magazine Luiza repetem o padrão americano: vencedoras com um '
             'defeito, perdedoras quando ficam "perfeitas".'),
           P('**Leitura:** com réguas absolutas o Brasil tem poucas empresas por classe; só Good Companies, Great Returns tem amostra razoável, e mantém a direção dos EUA, com vantagem menor e não significativa.')]
    st.append(PageBreak())

    # 14. dois paises
    dt = md_tables(B / 'diag_two_countries.md')
    st += [P('13. Dois países: o que tirou a empresa de Opportunity of Lifetime e o perfil de melhores e piores', 'h1'),
           P('**EUA: desempenho de cada defeito**', 'h2'), table(dt[0][1], widths=[4.4 * cm] + [1.88 * cm] * 7),
           P('**Brasil: desempenho de cada defeito**', 'h2'), table(dt[1][1], widths=[4.4 * cm] + [1.88 * cm] * 7),
           P('**EUA: perfil na entrada (piores 20%, todos, melhores 20%)**', 'h2'), table(dt[2][1], widths=[4.4 * cm] + [2.2 * cm] * 6),
           P('**Brasil: perfil na entrada**', 'h2'), table(dt[3][1], widths=[4.4 * cm] + [2.2 * cm] * 6),
           P('**Padrões comuns:** (1) o crescimento estrutural de 5 anos é o indicador que mais separa vencedores de perdedores nos quatro grupos; (2) "Growth instável" é o pior defeito nos dois '
             'países; (3) pagar caro pela perfeição é o maior risco da Opportunity of Lifetime (EUA: entrada depois de alta forte e salto de lucro; Brasil: P/L de 23x contra 10x da média).')]
    st.append(PageBreak())

    # 15. limitacoes e proximos passos
    st += [P('14. Limitações', 'h1')] + bullets([
        '**Viés de sobrevivência:** universos de hoje (S&P 500 atual + planilha; B3 listada hoje). A contraprova mede o viés.',
        '**ROIC:** caixa excessivo, intangíveis de aquisições, asset-light com capital de giro negativo, braços financeiros (ex.: Deere) e cortes de 20%/10% não revistos.',
        '**Método histórico:** sem estimativas de consenso point-in-time; o Excel e o P1 não são backtestáveis.',
        '**Cobertura:** japonesas e europeias da planilha ficam fora do backtest (sem XBRL na SEC).',
        '**Execução:** compra no fechamento do mesmo pregão do sinal (levemente otimista); custo de 10 bps por ponta.',
        '**Múltiplos testes:** muitos cortes foram testados; resultados com t < 2 devem ser lidos como indício.'])
    st += [P('15. Próximos passos sugeridos', 'h1')] + bullets([
        '**Terminar a investigação do ROIC:** caixa excessivo (limite ou caixa operacional), intangíveis de aquisição (capital operacional + ágio/intangíveis), média do capital de dois anos, teto de ROIC; depois, recalibrar os cortes (absolutos ou por percentil, por país).',
        '**Rever o zROIC:** com o ROIC corrigido, reavaliar se o corte de 0,7 deve existir.',
        '**Regras candidatas a backtestar nos dois países:** excluir de Good Companies, Great Returns o defeito "Growth instável"; evitar entradas na Opportunity of Lifetime depois de alta forte combinada com salto de lucro; exigir crescimento estrutural maior.',
        '**ETF:** pela evidência atual, Good Companies, Great Returns é a classe candidata; a Opportunity of Lifetime pura é concentrada e frágil.'])
    st += [P('Anexo: onde está cada análise', 'h1'), P('Código e tabelas em `price_tracker/` (branch claude/brave-tesla-93qd1w). Para refazer tudo: `./run_all.sh`; para o PDF: `python3 report/build_report.py`.', 'small')]
    st += [table([['Análise', 'Arquivo'], ['Backtest EUA (tabelas e gráficos)', 'backtest/summarize.py · classes_zg*.png'], ['Diagnóstico OoL × GCGR', 'backtest/diagnose_*.md'],
                  ['Cenários de P/E justo', 'backtest/scenarios.md'], ['Atribuição', 'backtest/attribution_2.93.md'], ['Distribuições / esperado × realizado', 'backtest/expected_vs_realized_2.93.md'],
                  ['Piores episódios / setores', 'backtest/worst_cases_2.93.md · sectors_2.93.md'], ['zROIC e ROIC marginal', 'backtest/zroic_breakdown.md · zroic_unstable.md'],
                  ['Dois países', 'backtest/diag_two_countries.md'], ['ROIC ano a ano (excluídas por ROIC médio)', 'backtest/roic_historico_roic_medio.xlsx'],
                  ['Brasil', 'brasil/run_v3.md · attribution_br*.md'], ['Modelo atual (Excel × P1 × P2)', 'report_ool_2026-11-09.md · report_2026-11-09.md']],
                 widths=[7 * cm, 10.6 * cm])]
    build(OUT, st, title)
    print(OUT)


if __name__ == '__main__':
    main()
