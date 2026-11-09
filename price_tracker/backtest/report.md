# Backtest: um ETF por classe (método 2, só histórico)

> ⚠️ **ROIC:** o backtest usa o ROIC clássico (NOPAT ÷ (patrimônio + dívida − caixa)) e ROE para financeiras, com os
> cortes 20%/10% desenhados para a fórmula do Wisesheets. O ROIC ainda precisa ser investigado e os cortes revistos.

## Regras

- **Universo:** S&P 500 atual + ações da planilha com balanço na SEC = 541 empresas. Ficam fora as que reportam EPS em outra
  moeda ou por ação ordinária (ADRs) e as sem dado suficiente; na prática, ~400 ações classificadas por trimestre.
- **Classificação point-in-time:** em cada trimestre, só entram números de balanço com data de arquivamento na SEC anterior ao
  rebalanceamento. EPS convertido para a base de ações de hoje pelos desdobramentos posteriores ao arquivamento.
- **Método 2:** Growth = mediana do crescimento do EPS nos últimos 5 anos (mínimo 3 válidos); zGrowth = desvio desses anos ÷ Growth;
  ROIC = média (últimos 3 anos, últimos 6 anos); `g` por ranking do Growth (7% → 3,5%; financeiras 6,5% → 3%);
  P/E justo `(1 − g/ROIC)/(8,5% − g)`; retorno = média de (P/E converge ao justo em 2 anos) e (múltiplo constante) + dividend yield.
  Mesma tabela de classes e cortes da planilha; zGrowth testado com 2,93 (atual do P2) e 0,9 (original).
- **Carteiras:** equal weight dentro de cada classe, rebalanceamento no último pregão de cada trimestre, retorno total
  (com dividendos). Classe vazia fica em caixa. Custo: 10 bps por unidade de giro em cada ponta (coluna "CAGR liq.").
- **Período:** 30/03/2012 a 30/09/2026 (59 trimestres). Começa quando ≥ 40% do universo já tem classe (o XBRL da SEC começa em 2009 e a janela
  de crescimento precisa de anos anteriores).

## Resultado (corte zGrowth 2,93)

| Carteira | CAGR | CAGR liq. | Vol | Sharpe* | Max DD | N médio |
|---|---|---|---|---|---|---|
| Good Companies, Great Returns | 20,6% | 20,3% | 18,2% | 1,13 | −34% | 38 |
| **Tier A** | 19,2% | 19,1% | 18,4% | 1,05 | −34% | 74 |
| Interesting but Requires Attention | 19,0% | 18,7% | 19,6% | 0,97 | −37% | 14 |
| QQQ | 19,0% | 19,0% | 20,6% | 0,92 | −35% | — |
| **Opportunity of Lifetime** | 18,3% | 18,2% | 19,7% | 0,93 | −35% | 30 |
| Tier B | 16,9% | 16,6% | 18,2% | 0,93 | −38% | 38 |
| **Universo EW (contraprova)** | 16,5% | 16,4% | 16,9% | 0,97 | −37% | 364 |
| Tier D (Do not Waste Time) | 15,7% | 15,6% | 16,7% | 0,94 | −37% | 220 |
| SPY | 14,3% | 14,3% | 16,6% | 0,86 | −34% | — |
| Tier C | 14,1% | 13,9% | 17,1% | 0,83 | −37% | 31 |
| RSP (S&P 500 equal weight) | 11,9% | 11,9% | 17,0% | 0,70 | −39% | — |

\* Sharpe sem taxa livre de risco (CAGR ÷ vol). Todas as classes individuais estão em `report` abaixo e em `data/nav_*.csv`.

### Excesso sobre o universo equal weight (a medida mais limpa)

| Carteira | zG 2,93 | t-stat | zG 0,9 | t-stat | 2012–2019 | 2020–2026 |
|---|---|---|---|---|---|---|
| Opportunity of Lifetime | +2,3% a.a. | 1,0 | +1,4% | 0,5 | 16,3% (univ. 17,9%) | 20,6% (univ. 14,8%) |
| Good Companies, Great Returns | +3,9% | **3,0** | +4,4% | **2,1** | 18,8% | 22,6% |
| Tier A | +2,8% | **2,1** | +2,7% | 1,4 | 17,7% | 20,8% |
| Tier B | +0,6% | 0,5 | +2,1% | **2,3** | 18,4% | 15,0% |
| Tier C | −2,1% | −1,6 | −2,6% | **−2,0** | 18,4% | 9,3% |
| Tier D | −0,8% | −1,5 | −0,8% | −1,7 | 17,9% | 13,1% |

(subperíodos com corte 2,93)

## Leitura

1. **Viés de sobrevivência é grande:** o universo equal weight fez 16,5% a.a. contra 11,9% do RSP, o S&P 500 equal weight de verdade.
   Cerca de 4,6 p.p. por ano vêm de usar só empresas que existem hoje. Por isso a comparação justa é contra o universo EW, não contra SPY/QQQ.
2. **A ordem dos tiers faz sentido:** A > B > D > C. O tier A bate o universo em ~2,8 p.p. a.a. e o C perde ~2,1–2,6 p.p.
3. **Opportunity of Lifetime não se destaca sozinha:** +1,4 a +2,3 p.p. a.a., estatisticamente fraco (t ≈ 0,5–1,0). Todo o ganho vem de 2020–2026;
   em 2012–2019 perdeu do universo.
4. **Good Companies, Great Returns é a classe mais consistente:** ganhou nos dois subperíodos e nos dois cortes, com t entre 2 e 3.
5. **O corte do zGrowth importa pouco para os tiers**, mas o de 0,9 deixa várias classes pequenas ou vazias (Cheap Slow Compounder ficou 23 trimestres em caixa).
6. **Contra benchmarks reais:** o tier A ganhou do SPY por ~5 p.p. a.a. e empatou com o QQQ, mas boa parte da vantagem sobre o SPY é viés de sobrevivência (ver item 1).

## Limitações

- Universo de hoje (viés de sobrevivência, ver acima). Empresas que saíram da bolsa não estão nos preços do Yahoo.
- Só empresas com XBRL na SEC: japonesas e europeias da planilha ficam fora.
- EPS anual GAAP (sem TTM, sem ajuste de itens não recorrentes); dívida da SEC só de longo prazo; dívida/caixa ausentes viram 0.
- Setor financeiro definido pela classificação de hoje (GICS / setor da planilha).
- Execução no fechamento do mesmo pregão que gera o sinal (levemente otimista).

## Exemplo: carteira Opportunity of Lifetime vigente em 01/06/2021 (rebalanceamento de 31/03/2021)

- zGrowth 2,93 (23): ADBE, AMAT, AMZN, BX, DPZ, GNRC, HD, HII, LII, LMT, LOW, LRCX, MAS, META, NVDA, ORLY, PGR, POOL, REGN, STX, TER, TROW, VRSN
- zGrowth 0,9 (11): ADBE, DPZ, GNRC, HD, LRCX, MAS, ORLY, PGR, POOL, TROW, VRSN

## Como rodar

```bash
python3 backtest/universe.py
python3 backtest/fetch_pit.py
python3 backtest/fetch_prices.py
python3 backtest/backtest.py
```
