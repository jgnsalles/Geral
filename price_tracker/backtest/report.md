# Backtest: uma carteira por classe (método 2, só histórico)

> ⚠️ **ROIC:** o backtest usa o ROIC clássico (NOPAT ÷ (patrimônio + dívida − caixa)) e ROE para financeiras, com os
> cortes 20%/10% desenhados para a fórmula do Wisesheets. O ROIC ainda precisa ser investigado e os cortes revistos.

## Estratégia testada

Para cada classe da planilha (Opportunity of Lifetime, Good Companies, Great Returns etc.): a cada trimestre, comprar **só as
empresas daquela classe**, em **equal weight**, e segurar até o próximo trimestre. Comparação contra SPY (S&P 500), QQQ (Nasdaq-100),
RSP (S&P 500 equal weight) e o **Universo EW**, a contraprova: todas as empresas do universo em equal weight.

## Regras

- **Universo:** S&P 500 atual + ações da planilha com balanço na SEC = 541 empresas; ~400 classificadas por trimestre
  (ficam fora ADRs/EPS em outra moeda e empresas sem dado suficiente).
- **Point-in-time:** em cada trimestre, só entram números com data de arquivamento na SEC anterior ao rebalanceamento.
  EPS convertido para a base de ações de hoje pelos desdobramentos posteriores ao arquivamento.
- **Classificação (método 2):** Growth = mediana do crescimento do EPS em 5 anos (mínimo 3 válidos); zGrowth = desvio ÷ Growth;
  ROIC = média (últimos 3 anos, últimos 6 anos); `g` por ranking do Growth; P/E justo `(1 − g/ROIC)/(8,5% − g)`;
  retorno = média de (P/E converge ao justo em 2 anos) e (múltiplo constante) + dividend yield. Mesma tabela de classes e cortes
  da planilha; zGrowth com 2,93 (atual do P2) e 0,9 (original).
- **Carteiras:** rebalanceamento no último pregão de cada trimestre, retorno total (com dividendos), classe vazia fica em caixa,
  custo de 10 bps por unidade de giro em cada ponta ("CAGR liq.").
- **Período:** 30/03/2012 a 30/09/2026 (59 trimestres). Começa quando ≥ 40% do universo já tem classe (o XBRL da SEC começa em 2009).

"vs Universo EW" = excesso anualizado sobre a contraprova; t = estatística t desse excesso trimestral (|t| ≳ 2 é significativo).

## Resultados

### Corte zGrowth 2.93

| Carteira | CAGR | CAGR liq. | Vol | Max DD | vs Universo EW | t | 2012–2019 | 2020–2026 | N médio | Trim. em caixa |
|---|---|---|---|---|---|---|---|---|---|---|
| **Opportunity of Lifetime** | 18,3% | 18,2% | 19,7% | -35,3% | +2,3% | 1,0 | 16,3% | 20,6% | 30 | 0 |
| **Good Companies, Great Returns** | 20,6% | 20,3% | 18,2% | -34,2% | +3,9% | 3,0 | 18,8% | 22,6% | 38 | 0 |
| **Excellent but Fair** | 12,2% | 11,9% | 21,5% | -38,3% | -3,0% | -0,8 | 13,0% | 11,4% | 5 | 0 |
| **Good but Margin of Safety Required** | 13,5% | 13,1% | 18,0% | -38,1% | -2,5% | -1,2 | 17,2% | 9,3% | 16 | 0 |
| **Cheap Slow Compounder** | 13,1% | 12,7% | 22,5% | -42,5% | -1,6% | -0,4 | 16,0% | 9,8% | 4 | 0 |
| **Interesting but Requires Attention** | 19,0% | 18,7% | 19,6% | -36,7% | +2,6% | 1,6 | 18,2% | 19,7% | 14 | 0 |
| **Cheap but Aggressive** | 17,3% | 16,9% | 25,5% | -53,4% | +2,2% | 0,5 | 22,1% | 11,8% | 5 | 1 |
| **Expensive for what you get** | 16,3% | 15,9% | 16,8% | -34,5% | -0,4% | -0,2 | 17,1% | 15,2% | 12 | 0 |
| **Investable but Not Good** | 8,4% | 8,0% | 22,2% | -40,7% | -6,4% | -1,7 | 10,7% | 5,6% | 4 | 2 |
| **Expensive** | 16,1% | 15,8% | 20,5% | -39,3% | +0,2% | 0,1 | 24,1% | 7,4% | 15 | 0 |
| **Do not Waste Time** | 15,7% | 15,6% | 16,7% | -37,3% | -0,8% | -1,5 | 17,9% | 13,1% | 220 | 0 |
| Universo EW (contraprova) | 16,5% | 16,4% | 16,9% | -36,8% | — | — | 17,9% | 14,8% | 364 | 0 |
| SPY | 14,3% | 14,3% | 16,6% | -33,7% | — | — | 13,5% | 15,1% | — | 0 |
| QQQ | 19,0% | 19,0% | 20,6% | -35,1% | — | — | 17,2% | 20,7% | — | 0 |
| RSP | 11,9% | 11,9% | 17,0% | -39,0% | — | — | 12,7% | 10,9% | — | 0 |

### Corte zGrowth 0.9

| Carteira | CAGR | CAGR liq. | Vol | Max DD | vs Universo EW | t | 2012–2019 | 2020–2026 | N médio | Trim. em caixa |
|---|---|---|---|---|---|---|---|---|---|---|
| **Opportunity of Lifetime** | 17,1% | 16,9% | 20,1% | -36,5% | +1,4% | 0,5 | 16,3% | 17,9% | 16 | 0 |
| **Good Companies, Great Returns** | 20,8% | 20,5% | 19,8% | -33,9% | +4,4% | 2,1 | 18,1% | 23,7% | 29 | 0 |
| **Excellent but Fair** | 10,4% | 10,0% | 22,6% | -46,8% | -4,5% | -1,1 | 18,8% | 1,4% | 3 | 1 |
| **Good but Margin of Safety Required** | 15,9% | 15,5% | 19,9% | -32,9% | -0,2% | -0,1 | 18,1% | 13,5% | 8 | 0 |
| **Cheap Slow Compounder** | 14,9% | 14,7% | 18,4% | -44,3% | -0,2% | -0,0 | 21,7% | 7,5% | 1 | 23 |
| **Interesting but Requires Attention** | 19,2% | 19,0% | 17,8% | -37,5% | +2,7% | 2,3 | 17,6% | 20,9% | 34 | 0 |
| **Cheap but Aggressive** | 15,9% | 15,6% | 21,6% | -38,8% | +0,5% | 0,2 | 21,6% | 9,7% | 10 | 0 |
| **Expensive for what you get** | 14,1% | 13,8% | 17,5% | -37,4% | -2,1% | -1,1 | 15,2% | 12,7% | 17 | 0 |
| **Investable but Not Good** | 11,7% | 11,4% | 18,3% | -36,8% | -4,1% | -1,6 | 14,6% | 8,5% | 9 | 0 |
| **Expensive** | 12,3% | 12,0% | 20,3% | -38,5% | -3,3% | -1,0 | 18,0% | 5,9% | 7 | 4 |
| **Do not Waste Time** | 15,7% | 15,6% | 16,7% | -37,4% | -0,8% | -1,7 | 18,0% | 13,0% | 228 | 0 |
| Universo EW (contraprova) | 16,5% | 16,4% | 16,9% | -36,8% | — | — | 17,9% | 14,8% | 364 | 0 |
| SPY | 14,3% | 14,3% | 16,6% | -33,7% | — | — | 13,5% | 15,1% | — | 0 |
| QQQ | 19,0% | 19,0% | 20,6% | -35,1% | — | — | 17,2% | 20,7% | — | 0 |
| RSP | 11,9% | 11,9% | 17,0% | -39,0% | — | — | 12,7% | 10,9% | — | 0 |


## Leitura

1. **Viés de sobrevivência:** a contraprova (Universo EW) fez 16,5% a.a. contra 11,9% do RSP, o S&P 500 equal weight real. Cerca de 4,6 p.p. por ano
   vêm de usar só empresas que existem hoje, então a comparação justa é contra o Universo EW, não contra SPY/QQQ.
2. **Opportunity of Lifetime:** 18,3% a.a. (corte 2,93) e 17,1% (corte 0,9). Ganhou do Universo EW por 2,3 e 1,4 p.p. a.a., sem significância
   (t = 1,0 e 0,5), e todo o ganho veio de 2020–2026; em 2012–2019 perdeu da contraprova (16,3% contra 17,9%).
3. **Good Companies, Great Returns:** a melhor e a mais consistente: 20,6% / 20,8% a.a., ganhou do Universo EW nos dois subperíodos e nos dois cortes
   (t = 3,0 e 2,1). Também ganhou do QQQ.
4. **Interesting but Requires Attention** também ficou acima da contraprova nos dois cortes (t = 1,6 e 2,3).
5. **As piores:** Investable but Not Good, Excellent but Fair e Good but Margin of Safety Required. Excellent but Fair e as classes pequenas têm poucas
   ações (3 a 5) e são muito ruidosas.

## Limitações

- Universo de hoje (viés de sobrevivência). Empresas que saíram da bolsa não estão nos preços do Yahoo.
- Só empresas com XBRL na SEC: japonesas e europeias da planilha ficam fora.
- EPS anual GAAP (sem TTM, sem ajuste de itens não recorrentes); dívida da SEC só de longo prazo; dívida/caixa ausentes viram 0.
- Setor financeiro pela classificação de hoje. Execução no fechamento do mesmo pregão do sinal (levemente otimista).

## Exemplo: carteira Opportunity of Lifetime vigente em 01/06/2021 (rebalanceamento de 31/03/2021)

- zGrowth 2,93 (23): ADBE, AMAT, AMZN, BX, DPZ, GNRC, HD, HII, LII, LMT, LOW, LRCX, MAS, META, NVDA, ORLY, PGR, POOL, REGN, STX, TER, TROW, VRSN
- zGrowth 0,9 (11): ADBE, DPZ, GNRC, HD, LRCX, MAS, ORLY, PGR, POOL, TROW, VRSN

## Como rodar

```bash
python3 backtest/universe.py
python3 backtest/fetch_pit.py
python3 backtest/fetch_prices.py
python3 backtest/backtest.py
python3 backtest/summarize.py
```
