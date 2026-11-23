# Performance das gestoras (aba "Performance" do artefato Carteiras das Gestoras)

Artefato: https://claude.ai/artifact/FgEspc6hKKbuF83qguuiz1

1. `brazil_downturn/01_extrai_informe.py raw painel_fundos.pkl` (branch claude/brazil-gestoras-inflows-analysis-8f1cg5): Informe Diário da CVM → fundo-mês.
2. `perf_base.py raw painel_fundos.pkl gestoras_list.json cdi.json out`: gestor na data, flags FIC/exclusivo, retornos por fundo, Ibovespa (mediana dos fundos indexados) e CDI (BCB SGS 4391).
   `gestoras_list.json` = lista de gestoras (id, n, rs, cnpj, mb) tirada do próprio artefato.
3. `perf_export.py out gestoras_list.json 2026-10 perf.json`: retorno mensal por gestora (média ponderada pelo PL do mês anterior dos fundos elegíveis) e dos 8 maiores fundos.
4. `assemble.py <html do artefato> perf.json perf_section.html perf_js.js saida.html`: injeta a aba e o bloco da página da gestora.

0. `shorts.py raw/cda ibov_pts.json fundos_eleg.txt shorts.pkl`: posição vendida por fundo-mês a partir da CDA (futuro de Ibovespa vendido + ações tomadas em aluguel), usada para excluir long biased (mediana 12m ≥ 10% do PL).
