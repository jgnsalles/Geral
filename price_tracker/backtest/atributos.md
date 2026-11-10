# Atributos do modelo: fórmulas, decomposição e dispersão por desempenho (OoL e GCGR)

> ⚠️ **ROIC:** ROIC oficial (B com reserva em A; seguradoras de saúde e financeiras com ROE; imobilizado de utilities/REITs corrigido em 2026-11-10). Ainda há casos suspeitos (patrimônio negativo, ROIC > 100% em empresas leves em ativos).

Configuração: universo point-in-time (S&P 500 de cada trimestre), sem zROIC, OoL a partir de ROIC 12%. Todos os valores são os que o modelo via na data (só balanços já arquivados). Séries anuais não aparecem; só o valor final e seus componentes.

Grupos: as posições (ação × trimestre) de cada classe foram ordenadas pelo excesso de retorno do trimestre seguinte sobre a média do universo. Célula = **mediana** [percentil 25 – percentil 75]. Valores em US$ bi quando indicado. Componentes de ROIC só para operacionais; ROE só para financeiras e seguradoras de saúde.

## Resultado de cada grupo

| Variável | Fórmula | OoL: 20% piores | OoL: 60% do meio | OoL: 20% melhores | GCGR: 20% piores | GCGR: 60% do meio | GCGR: 20% melhores |
|---|---|---|---|---|---|---|---|
| Posições |  | 552 | 1654 | 552 | 312 | 935 | 312 |
| Excesso no trimestre seguinte (a.a.) | Retorno da ação − média do universo, × 4 | -61% [-87% – -50%] | 0,2% [-18% – 18%] | 65% [52% – 93%] | -59% [-79% – -45%] | -0,7% [-18% – 17%] | 66% [51% – 86%] |
| % financeiras/seguradoras |  | 9% | 16% | 11% | 14% | 19% | 12% |
| **Entradas de mercado** | | | | | | | |
| Preço | Fechamento no último pregão do trimestre (Yahoo) | 98,27 [53,78 – 191,08] | 86,26 [50,25 – 156,19] | 84,24 [44,11 – 169,45] | 79,84 [48,72 – 159,46] | 79,02 [49,73 – 136,03] | 74,56 [46,07 – 149,45] |
| Dividend yield | Soma dos dividendos dos últimos 730 dias ÷ 2 ÷ preço | 0,7% [0,0% – 1,7%] | 1,2% [0,0% – 2,0%] | 0,7% [0,0% – 1,7%] | 1,2% [0,0% – 2,1%] | 1,7% [0,7% – 2,5%] | 1,2% [0,0% – 2,4%] |
| **Lucro por ação e crescimento** | | | | | | | |
| EPS (último exercício) | Lucro por ação diluído do último 10-K arquivado até a data, ajustado por desdobramentos | 5,36 [2,58 – 9,06] | 4,65 [2,60 – 8,27] | 4,30 [1,98 – 8,11] | 4,35 [2,35 – 7,90] | 4,52 [2,82 – 7,80] | 4,56 [2,65 – 7,95] |
| P/L | Preço ÷ EPS (só EPS > 0) | 21,2 [14,6 – 31,3] | 20,2 [15,0 – 26,6] | 21,6 [15,2 – 30,2] | 17,9 [13,7 – 24,2] | 17,4 [13,2 – 22,3] | 17,2 [13,0 – 23,6] |
| Crescimento do EPS (métrica do modelo) | Mediana das 5 taxas anuais do EPS (mín. 3 válidas; taxa só quando o EPS do ano anterior > 0) | 28% [21% – 45%] | 25% [20% – 36%] | 30% [22% – 44%] | 24% [14% – 41%] | 20% [13% – 32%] | 23% [14% – 38%] |
|   · média das 5 taxas | Média simples das taxas válidas (referência; não entra no modelo) | 29% [20% – 50%] | 24% [17% – 35%] | 29% [20% – 44%] | 37% [14% – 100%] | 23% [13% – 66%] | 37% [15% – 104%] |
|   · desvio-padrão das 5 taxas | Desvio-padrão populacional das taxas válidas | 31% [19% – 52%] | 27% [15% – 43%] | 32% [18% – 56%] | 71% [20% – 185%] | 37% [16% – 118%] | 71% [25% – 192%] |
| zGrowth | Desvio-padrão das taxas ÷ crescimento (mediana). Corte 2,93 | 1,05 [0,68 – 1,50] | 0,98 [0,66 – 1,49] | 1,06 [0,69 – 1,55] | 2,85 [1,41 – 4,98] | 1,98 [1,09 – 3,95] | 3,13 [1,64 – 5,05] |
| **ROIC (operacionais) — último exercício decomposto** | | | | | | | |
| Lucro operacional (EBIT) | OperatingIncomeLoss | 1,41 [0,75 – 3,52] | 1,83 [1,02 – 5,15] | 1,81 [0,83 – 4,80] | 1,64 [0,96 – 3,65] | 2,02 [1,05 – 4,56] | 1,89 [0,98 – 3,84] |
| Alíquota de imposto | Imposto ÷ lucro antes do IR, limitada a 0–50%; 21% se não calculável | 21% [14% – 28%] | 23% [17% – 30%] | 20% [13% – 26%] | 21% [14% – 27%] | 22% [18% – 29%] | 21% [16% – 25%] |
| NOPAT | EBIT × (1 − alíquota) | 1,09 [0,56 – 2,71] | 1,39 [0,76 – 3,79] | 1,36 [0,65 – 3,84] | 1,29 [0,71 – 3,12] | 1,54 [0,81 – 3,38] | 1,48 [0,76 – 3,15] |
| Imobilizado líquido | PropertyPlantAndEquipmentNet (utilities/REITs: conceitos próprios) | 1,27 [0,53 – 3,15] | 1,82 [0,72 – 4,06] | 1,52 [0,58 – 3,31] | 2,13 [0,70 – 5,86] | 2,37 [0,74 – 5,65] | 1,86 [0,65 – 5,42] |
| Ágio (goodwill) | Goodwill | 0,90 [0,18 – 3,56] | 1,26 [0,39 – 4,89] | 0,79 [0,18 – 3,73] | 1,54 [0,30 – 4,08] | 2,19 [0,76 – 5,15] | 1,91 [0,38 – 5,15] |
| Intangíveis | Intangíveis líquidos excluindo ágio | 0,14 [0,00 – 0,86] | 0,22 [0,00 – 1,37] | 0,11 [0,00 – 0,76] | 0,35 [0,06 – 1,11] | 0,41 [0,05 – 1,42] | 0,35 [0,03 – 1,37] |
| Capital de giro operacional | (Ativo circulante − caixa) − (passivo circulante − dívida de curto prazo) | 0,51 [0,03 – 1,30] | 0,59 [-0,07 – 1,64] | 0,62 [-0,00 – 2,46] | 0,48 [-0,53 – 1,42] | 0,45 [-0,68 – 1,67] | 0,37 [-0,56 – 1,51] |
| Capital B (fim do ano) | Imobilizado + ágio + intangíveis + capital de giro operacional | 3,87 [1,75 – 11,77] | 5,31 [2,46 – 14,90] | 4,13 [1,96 – 12,75] | 5,44 [2,53 – 15,07] | 6,96 [3,00 – 17,73] | 5,98 [2,53 – 17,21] |
| Capital B médio | (Capital B do ano + do ano anterior) ÷ 2 | 3,64 [1,52 – 11,57] | 5,10 [2,35 – 14,35] | 4,15 [1,82 – 12,36] | 5,35 [2,52 – 14,54] | 6,36 [2,94 – 17,81] | 5,81 [2,54 – 17,33] |
|   · peso do imobilizado no capital | Imobilizado ÷ capital B | 33% [17% – 65%] | 31% [16% – 67%] | 33% [17% – 70%] | 40% [18% – 72%] | 38% [16% – 68%] | 41% [16% – 70%] |
|   · peso de ágio + intangíveis no capital | (Ágio + intangíveis) ÷ capital B | 32% [8,4% – 60%] | 39% [15% – 63%] | 29% [8,9% – 57%] | 41% [11% – 73%] | 43% [17% – 75%] | 42% [14% – 74%] |
|   · peso do capital de giro no capital | Capital de giro ÷ capital B | 17% [1,4% – 39%] | 13% [-1,4% – 37%] | 19% [2,1% – 39%] | 8,9% [-9,4% – 27%] | 8,3% [-7,6% – 28%] | 7,9% [-10% – 30%] |
| Crescimento do capital B no ano | Capital B do ano ÷ do ano anterior − 1 | 7,1% [0,0% – 19%] | 7,1% [-0,3% – 18%] | 8,2% [0,7% – 20%] | 5,3% [-1,9% – 16%] | 4,8% [-1,6% – 15%] | 4,9% [-3,6% – 21%] |
| ROIC do último ano (B) | NOPAT ÷ capital B médio (se ≤ 0 ou ausente, usa A) | 29% [18% – 44%] | 28% [18% – 41%] | 32% [20% – 43%] | 22% [14% – 33%] | 23% [16% – 37%] | 25% [15% – 43%] |
| Patrimônio líquido | StockholdersEquity | 3,58 [1,78 – 9,51] | 4,31 [1,90 – 10,52] | 4,67 [1,87 – 11,23] | 4,78 [1,95 – 11,09] | 5,87 [2,38 – 13,32] | 4,63 [1,72 – 10,85] |
| Dívida de longo prazo | LongTermDebt e equivalentes | 3,07 [0,87 – 7,90] | 3,70 [1,29 – 9,43] | 3,85 [1,21 – 9,43] | 4,01 [1,81 – 9,23] | 4,90 [2,10 – 10,27] | 4,93 [2,05 – 9,71] |
| Caixa | Caixa e equivalentes | 0,91 [0,36 – 2,16] | 0,97 [0,38 – 2,54] | 1,15 [0,45 – 3,16] | 1,37 [0,65 – 2,74] | 1,32 [0,61 – 3,03] | 1,32 [0,54 – 3,35] |
| ROIC do último ano (A, reserva) | NOPAT ÷ (patrimônio + dívida − caixa); capital operacional se ≤ 0 | 26% [18% – 38%] | 25% [16% – 35%] | 27% [19% – 37%] | 19% [14% – 27%] | 19% [15% – 31%] | 20% [14% – 33%] |
| **ROE (financeiras e seguradoras de saúde)** | | | | | | | |
| Lucro líquido | NetIncomeLoss | 1,12 [0,55 – 2,94] | 1,53 [0,77 – 4,22] | 1,38 [0,67 – 4,25] | 1,24 [0,68 – 2,62] | 1,66 [0,82 – 3,43] | 1,34 [0,70 – 2,89] |
| ROE do último ano | Lucro líquido ÷ patrimônio | 18% [17% – 25%] | 21% [17% – 30%] | 19% [16% – 24%] | 18% [13% – 25%] | 15% [12% – 21%] | 18% [12% – 22%] |
| **Métricas de ROIC do modelo (série de 6 anos resumida)** | | | | | | | |
|   · média dos 3 últimos anos | Média do ROIC anual dos 3 últimos exercícios | 27% [17% – 40%] | 25% [16% – 38%] | 29% [18% – 41%] | 19% [13% – 29%] | 20% [13% – 33%] | 22% [14% – 37%] |
|   · média dos 6 anos | Média do ROIC anual dos 6 exercícios | 25% [16% – 36%] | 23% [15% – 35%] | 26% [17% – 37%] | 18% [13% – 29%] | 19% [12% – 31%] | 19% [13% – 37%] |
| ROIC (métrica do modelo) | Média de (média 3 anos, média 6 anos). Cortes: 12% / 10% (esboço) | 26% [17% – 39%] | 24% [16% – 36%] | 27% [17% – 39%] | 18% [13% – 29%] | 20% [13% – 33%] | 21% [14% – 36%] |
|   · desvio-padrão dos 6 anos | Desvio-padrão populacional do ROIC anual | 6,8% [3,7% – 12%] | 5,3% [3,2% – 9,9%] | 6,8% [4,2% – 12%] | 6,2% [3,2% – 12%] | 4,9% [2,6% – 9,6%] | 7,2% [3,9% – 14%] |
| zROIC | Desvio-padrão ÷ ROIC do modelo (desligado nesta versão) | 0,24 [0,17 – 0,37] | 0,23 [0,15 – 0,32] | 0,26 [0,18 – 0,38] | 0,31 [0,18 – 0,52] | 0,26 [0,15 – 0,43] | 0,34 [0,19 – 0,54] |
| **Valor justo e retorno esperado** | | | | | | | |
| g (crescimento na perpetuidade) | Ranking do crescimento entre as ações da data: 7% (1º) a 3,5% (último); financeiras 6,5% a 3% | 6,4% [6,1% – 6,7%] | 6,3% [6,0% – 6,6%] | 6,5% [6,1% – 6,7%] | 6,2% [5,7% – 6,6%] | 5,9% [5,6% – 6,4%] | 6,1% [5,7% – 6,6%] |
| ROIC usado no P/E justo | ROIC do modelo limitado a 100% | 26% [17% – 39%] | 24% [16% – 36%] | 27% [17% – 39%] | 18% [13% – 29%] | 20% [13% – 33%] | 21% [14% – 36%] |
|   · taxa de reinvestimento | g ÷ ROIC usado | 24% [17% – 38%] | 26% [17% – 39%] | 23% [16% – 37%] | 33% [20% – 48%] | 30% [19% – 48%] | 29% [16% – 45%] |
| P/E justo | (1 − g ÷ ROIC) ÷ (8,5% − g) | 35,3 [29,1 – 42,3] | 32,8 [27,0 – 38,9] | 36,3 [28,7 – 42,8] | 27,2 [21,9 – 32,4] | 26,3 [21,1 – 31,9] | 29,3 [23,3 – 34,8] |
|   · P/E justo ÷ P/L | Quanto o múltiplo teria de subir para chegar ao justo | 1,5 [1,1 – 2,3] | 1,5 [1,2 – 2,1] | 1,5 [1,2 – 2,2] | 1,5 [1,2 – 1,8] | 1,5 [1,2 – 1,8] | 1,5 [1,2 – 2,1] |
|   · preço justo em 2 anos ÷ preço | P/E justo × EPS × (1 + crescimento)² ÷ preço | 2,6 [1,8 – 4,2] | 2,3 [1,8 – 3,5] | 2,6 [1,8 – 4,2] | 2,2 [1,7 – 3,1] | 2,1 [1,7 – 2,8] | 2,3 [1,7 – 3,5] |
| Retorno com convergência ao P/E justo | √(preço justo em 2 anos ÷ preço) − 1 + dividend yield | 62% [35% – 107%] | 55% [36% – 90%] | 63% [36% – 108%] | 50% [34% – 80%] | 47% [33% – 70%] | 54% [34% – 92%] |
| Retorno com múltiplo constante | Crescimento + dividend yield | 30% [22% – 46%] | 26% [21% – 37%] | 31% [23% – 46%] | 25% [16% – 41%] | 22% [15% – 33%] | 24% [16% – 39%] |
| Retorno esperado (métrica do modelo) | Média dos dois retornos acima. Cortes: 20% / 8% | 47% [31% – 74%] | 41% [30% – 61%] | 47% [33% – 75%] | 37% [27% – 57%] | 34% [26% – 51%] | 38% [28% – 63%] |

## Onde melhores e piores mais diferem

Diferença das medianas (20% melhores − 20% piores) dividida pelo intervalo interquartil da classe inteira. Acima de ±0,25 já é uma separação perceptível; abaixo de ±0,1 é ruído.

| Variável | OoL: diferença ÷ IQR | GCGR: diferença ÷ IQR |
|---|---|---|
| P/E justo | +0,07 | +0,19 |
| EPS (último exercício) | -0,18 | +0,04 |
| ROIC (métrica do modelo) | +0,04 | +0,17 |
| ROIC usado no P/E justo | +0,04 | +0,17 |
| média dos 3 últimos anos | +0,07 | +0,16 |
| taxa de reinvestimento | -0,07 | -0,15 |
| Patrimônio líquido | +0,13 | -0,01 |
| desvio-padrão dos 6 anos | +0,01 | +0,12 |
| Dívida de longo prazo | +0,10 | +0,12 |
| ROIC do último ano (B) | +0,09 | +0,12 |
| Preço | -0,12 | -0,06 |
| Lucro operacional (EBIT) | +0,11 | +0,08 |
| Caixa | +0,11 | -0,02 |
| Retorno com convergência ao P/E justo | +0,01 | +0,10 |
| zROIC | +0,06 | +0,10 |
| preço justo em 2 anos ÷ preço | +0,00 | +0,09 |
| NOPAT | +0,09 | +0,08 |
| zGrowth | +0,01 | +0,09 |
| ROE do último ano | +0,09 | -0,04 |
| Crescimento do EPS (métrica do modelo) | +0,08 | -0,05 |
| Ágio (goodwill) | -0,03 | +0,08 |
| Imobilizado líquido | +0,08 | -0,06 |
| Lucro líquido | +0,08 | +0,04 |
| média dos 6 anos | +0,08 | +0,06 |
| Alíquota de imposto | -0,07 | +0,00 |
| P/L | +0,04 | -0,07 |
| ROIC do último ano (A, reserva) | +0,03 | +0,07 |
| Capital de giro operacional | +0,06 | -0,05 |
| Crescimento do capital B no ano | +0,06 | -0,03 |
| desvio-padrão das 5 taxas | +0,06 | -0,01 |
| P/E justo ÷ P/L | +0,01 | +0,06 |
| peso de ágio + intangíveis no capital | -0,06 | +0,01 |
| g (crescimento na perpetuidade) | +0,02 | -0,05 |
| peso do capital de giro no capital | +0,05 | -0,03 |
| Capital B médio | +0,05 | +0,03 |
| Retorno esperado (métrica do modelo) | -0,00 | +0,04 |
| Capital B (fim do ano) | +0,02 | +0,04 |
| Retorno com múltiplo constante | +0,03 | -0,04 |
| Dividend yield | +0,03 | +0,00 |
| Intangíveis | -0,02 | +0,00 |
| média das 5 taxas | -0,01 | +0,00 |
| peso do imobilizado no capital | -0,01 | +0,01 |
## Mesma análise por empresa (robustez)

Ordenar por um único trimestre mistura sorte com volatilidade: as ações mais voláteis caem nos dois extremos. Aqui cada empresa é uma observação: excesso médio de todas as suas posições na classe (mín. 4 trimestres) e mediana de cada atributo ao longo delas. Diferença das medianas (20% melhores − 20% piores) ÷ IQR, e a mediana de cada grupo.

| Variável | OoL: piores | OoL: meio | OoL: melhores | OoL: dif ÷ IQR | GCGR: piores | GCGR: meio | GCGR: melhores | GCGR: dif ÷ IQR |
|---|---|---|---|---|---|---|---|---|
| Empresas / excesso mediano a.a. | 42 / -23% | 123 / +1% | 42 / +22% |  | 36 / -23% | 107 / +1% | 36 / +21% |  |
| desvio-padrão dos 6 anos | 5,6% | 5,6% | 6,9% | +0,17 | 4,7% | 5,2% | 13% | **+0,95** |
| NOPAT | 0,95 | 1,18 | 2,86 | **+0,86** | 1,22 | 1,44 | 1,48 | +0,09 |
| Lucro operacional (EBIT) | 1,19 | 1,49 | 3,62 | **+0,86** | 1,44 | 1,87 | 2,02 | +0,15 |
| P/L | 16,2 | 19,5 | 26,5 | **+0,82** | 15,0 | 17,8 | 19,1 | **+0,45** |
| P/E justo | 33,5 | 32,5 | 37,4 | **+0,32** | 23,6 | 26,1 | 31,9 | **+0,81** |
| Caixa | 0,61 | 1,04 | 2,04 | **+0,76** | 0,89 | 1,19 | 1,85 | **+0,40** |
| média dos 3 últimos anos | 20% | 24% | 25% | +0,23 | 16% | 18% | 27% | **+0,74** |
| ROIC (métrica do modelo) | 20% | 23% | 27% | **+0,37** | 17% | 19% | 28% | **+0,70** |
| ROIC usado no P/E justo | 20% | 23% | 27% | **+0,37** | 17% | 19% | 28% | **+0,70** |
| Lucro líquido | 0,92 | 1,31 | 2,52 | **+0,65** | 1,43 | 1,66 | 1,52 | +0,04 |
| média dos 6 anos | 19% | 22% | 26% | **+0,40** | 16% | 18% | 27% | **+0,65** |
| P/E justo ÷ P/L | 1,8 | 1,5 | 1,2 | **-0,63** | 1,5 | 1,5 | 1,6 | +0,16 |
| Alíquota de imposto | 23% | 23% | 16% | **-0,59** | 20% | 23% | 21% | +0,09 |
| Dívida de longo prazo | 1,40 | 2,83 | 5,45 | **+0,58** | 5,97 | 3,83 | 6,27 | +0,04 |
| desvio-padrão das 5 taxas | 33% | 31% | 34% | +0,01 | 55% | 63% | 131% | **+0,54** |
| ROIC do último ano (A, reserva) | 20% | 26% | 26% | **+0,37** | 18% | 18% | 27% | **+0,54** |
| taxa de reinvestimento | 32% | 27% | 23% | **-0,41** | 39% | 31% | 23% | **-0,51** |
| zGrowth | 1,17 | 1,05 | 1,10 | -0,09 | 1,99 | 2,36 | 3,39 | **+0,49** |
| Retorno com múltiplo constante | 25% | 26% | 32% | **+0,43** | 25% | 23% | 35% | **+0,48** |
| Retorno com convergência ao P/E justo | 76% | 57% | 47% | **-0,48** | 53% | 46% | 61% | +0,17 |
| preço justo em 2 anos ÷ preço | 3,1 | 2,4 | 2,2 | **-0,44** | 2,3 | 2,1 | 2,6 | +0,21 |
| Crescimento do EPS (métrica do modelo) | 23% | 26% | 32% | **+0,44** | 24% | 22% | 33% | **+0,40** |
| ROIC do último ano (B) | 20% | 28% | 31% | **+0,43** | 19% | 21% | 27% | **+0,42** |
| média das 5 taxas | 28% | 24% | 32% | +0,18 | 28% | 28% | 54% | **+0,42** |
| zROIC | 0,21 | 0,24 | 0,27 | **+0,31** | 0,30 | 0,31 | 0,44 | **+0,40** |
| Dividend yield | 0,8% | 1,3% | 0,8% | -0,01 | 2,0% | 1,6% | 1,1% | **-0,40** |
| g (crescimento na perpetuidade) | 6,3% | 6,3% | 6,5% | **+0,39** | 6,1% | 6,0% | 6,5% | **+0,38** |
| Retorno esperado (métrica do modelo) | 54% | 43% | 41% | **-0,38** | 44% | 34% | 51% | +0,23 |
| EPS (último exercício) | 6,45 | 4,63 | 4,65 | **-0,33** | 5,05 | 4,26 | 4,67 | -0,07 |
| Imobilizado líquido | 1,07 | 1,49 | 1,94 | **+0,32** | 2,79 | 2,21 | 2,41 | -0,07 |
| Ágio (goodwill) | 0,95 | 1,22 | 1,59 | +0,17 | 1,55 | 1,98 | 3,32 | **+0,31** |
| ROE do último ano | 23% | 20% | 20% | **-0,26** | 15% | 18% | 16% | +0,16 |
| Crescimento do capital B no ano | 8,7% | 7,0% | 9,7% | +0,07 | 2,2% | 5,1% | 6,0% | +0,23 |
| Preço | 85,78 | 85,45 | 107,55 | +0,21 | 70,95 | 74,39 | 79,07 | +0,10 |
| peso do imobilizado no capital | 34% | 33% | 31% | -0,08 | 28% | 39% | 37% | +0,19 |
| Capital de giro operacional | 0,49 | 0,52 | 0,74 | +0,16 | 0,67 | 0,51 | 0,32 | -0,17 |
| Patrimônio líquido | 4,27 | 3,80 | 5,42 | +0,15 | 5,78 | 5,89 | 5,45 | -0,03 |
| Intangíveis | 0,30 | 0,23 | 0,14 | -0,14 | 0,55 | 0,38 | 0,57 | +0,02 |
| Capital B (fim do ano) | 4,63 | 4,13 | 5,63 | +0,10 | 6,05 | 7,05 | 8,13 | +0,10 |
| peso de ágio + intangíveis no capital | 30% | 42% | 27% | -0,06 | 53% | 39% | 53% | -0,00 |
| Capital B médio | 4,11 | 4,02 | 4,55 | +0,05 | 5,54 | 6,13 | 6,58 | +0,05 |
| peso do capital de giro no capital | 15% | 11% | 15% | -0,01 | 8,4% | 9,0% | 6,8% | -0,05 |

> **Correção (2026-11-10, ver `metrica_retorno.md`):** a tabela por empresa acima usa a **mediana** de cada métrica ao longo das posições,
> o que inclui trimestres depois da compra. Quando a ação sobe, o P/L sobe junto, então P/L, P/E justo ÷ P/L e retorno esperado ficam
> mecanicamente ligados ao retorno. Medido **na primeira compra**, o P/L não tem relação com o retorno (R² 0,002 na OoL) e o retorno
> esperado também não (0,002). A conclusão "as piores pareciam baratas" era em grande parte esse viés.
