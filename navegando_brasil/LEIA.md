# Navegando Brasil — fonte do build

Repositório de dados: github.com/jgnsalles/gestoras, branch `claude/great-dirac-q5zkmt`
(template `output/artifact/navegando_dilma_2_v2.template.html`, CSVs em `output/dashboard/`,
carteiras consolidadas extraídas da linha `const D=` de `output/artifact/carteiras_gestoras.html` para `data/carteiras.json`).

Montagem: `CSV=<pasta dos CSVs> python build.py` (guardado como build.py.txt) → `dist/index.html` + `dist/data/*`.
O último mês da série (`{{END}}`, `{{END_L}}` nos arquivos de src) sai do maior `ym` de `serie_mensal.csv`.
Arquivos: body.html (HTML das páginas, com {{NAV:a-b}} = linhas do template), framework.html (dash, carga assíncrona),
inject.js (draws novos dentro do módulo do Navegando), cw.js (Carteiras portado), glue.js (rotas, períodos, gestoras), extra.css.

## Fase 2 (feita em 10/11/2026): série de performance estendida até abr/2026

serie_mensal, posicoes_1/2, precos, ibov e acoes ganharam jan/2024–abr/2026; jan/2012–dez/2023 ficou igual.
Scripts em `fonte/dados_2024/` (rodar na ordem), seguindo os do repo gestoras:

1. `x_cvm.py` (extract.py + extract8.py + quotas.py): CDA (BLC_2/4/8, PL) e Informe Diário de dez/2023 em diante.
   Universo semeado por `roots.json`: master de 2018, master de dez/2023 (Dynamo, Navi e Bogari trocaram de CNPJ)
   e feeders com ≥ 50% no master em dez/2023. O PL de dez/2023 bate com a série antiga nos 30 fundos.
2. `masters.py` (holdings.py): master por mês = maior carteira de ações entre feeders/masters. Maina trocou de master em nov/2024.
3. `x_b3.py` + `yahoo.py` + `prices.py` (prices.py + prices_fix.py + divadj.py): retorno com dividendos do Yahoo;
   códigos trocados usam a série do código novo quando a correlação com a B3 é ≥ 0,95 (`rename.json`);
   sem Yahoo: COTAHIST + proventos do Fundamentus; sem cotação (Compass PASS5/6): preço implícito da CDA.
4. `analysis.py 2026-04` (analysis.py) e `export.py` (export_ds.py): junta aos CSVs antigos mantendo os representantes por empresa.

Por que abr/2026: a CVM já publicou CDA até out/2026, mas de mai/2026 em diante só 2–4 dos 30 masters aparecem
(carteiras em sigilo ainda não republicadas). Para estender, baixar os meses novos e rodar de novo com o novo fim.
Lacuna conhecida: Bahia AM Valuation sem CDA em mar/2025 (sem retorno em mar e abr/2025).

## Carteiras consolidadas atualizadas (10/11/2026)

`data/carteiras.json` foi reconstruído de jan/2024 a set/2026 com a CDA publicada pela CVM até 10/11/2026
(`dados_2024/cw_update.py`): `python cw_update.py <json antigo> <json novo> 2024-01 2026-09 [meses de conferência]`.
Por gestora: fundos/classes cujo gestor (registro CVM 175, ou registro do fundo para classes canceladas) é o CNPJ da gestora ou um dos `mb`;
t = ações, ações emprestadas, recibos e BDRs (BLC_4) + investimento no exterior (BLC_7), em R$ mil; c = o mesmo no arquivo CONFID (sigilo).
Conferência contra o json antigo (completo até fev/2026): ~60% das gestoras idênticas e ~94% do valor a menos de 5%; as diferenças vêm de fundos
que trocaram de gestor (o registro atual da CVM é usado para todo o período reconstruído, por isso a reconstrução começa em jan/2024).
Quantidades: o json antigo guarda uma base histórica própria por emissor (não reproduzível); de jan/2024 em diante elas são
número de ações da CDA corrigido por eventos detectados nos próprios dados (`cw_splits.py`: desdobramentos, grupamentos, bonificações
como SBSP 5:1, HAPV 1:15, MGLU 1:10, BBAS 2:1, ITUB/ITSA/LREN bonificações, AXIA7 distribuída em dez/2025), e `base_q = 2024-01` faz a página
não comparar quantidades através de dez/2023 → jan/2024.
A CVM republicou em 07/11/2026 os meses que estavam em sigilo: mar e abr/2026 ficaram 100% revelados; mai–jul/2026 ~44%, ago–set/2026 ~17%.
Out/2026 ficou de fora (3,5% revelado, entrega ainda em curso). A série de performance dos 30 fundos continua em abr/2026 pelo mesmo motivo.
