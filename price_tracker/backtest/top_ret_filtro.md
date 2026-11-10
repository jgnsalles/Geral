# Top 20 por retorno esperado + filtros: fora crescimento do lucro no último ano > 150% e P/L < 6 (EUA e Brasil)

> ⚠️ **ROIC:** a nota usa o ROIC do modelo (oficial nos EUA; clássico no Brasil). Casos de ROIC aberrante (patrimônio negativo, empresas leves em ativos) ainda estão em aberto e podem subir no ranking.

**Regra (registrada no PROTOCOLO antes de rodar):** elegíveis = ROIC ≥ 12% e crescimento do EPS ≥ 15%, sem cíclicos e sem vestuário. Ordenação = **retorno esperado do modelo** (P/E justo + múltiplo constante + dividendos), sem o corte de 20%; ficam as N maiores. **Fora:** alguma taxa anual de crescimento do lucro > 150% nos 5 anos, ou P/L < 6. Peso = raiz do valor de mercado com teto de 2/N por ação. **Produto: N = 20.** N = 15 e 10 são sensibilidade. Sem P/E justo, retorno esperado ou zGrowth.

## 1. EUA (universo point-in-time do S&P 500)

| Carteira | Retorno total | Retorno anual | Volatilidade | Pior queda | Ações (média) | Janelas 5a > S&P | Janelas 10a > S&P |
|---|---|---|---|---|---|---|---|
| S&P 500 | 775,2% | 15,6% | 16,7% | -33,7% | — | — | — |
| S&P 500 equal weight | 544,3% | 13,2% | 17,3% | -39,0% | — | 12% | 0% |
| OoL antigo | 728,3% | 15,1% | 20,0% | -35,9% | 27 | 55% | 44% |
| GCGR antigo | 713,0% | 15,0% | 17,8% | -37,2% | 34 | 69% | 80% |
| **OoL novo** | 969,7% | **17,1%** | 18,8% | -35,8% | 42 | 82% | 100% |
| **GCGR novo** | 944,9% | **16,9%** | 18,1% | -32,3% | 23 | 89% | 100% |
| OoL High ROIC (novo) | 1228,3% | 18,8% | 20,4% | -33,8% | 16 | 98% | 100% |
| OoL High Growth (novo) | 1319,9% | 19,3% | 21,8% | -35,0% | 16 | 90% | 100% |
| Cyclicals | 122,3% | 5,5% | 23,6% | -52,8% | 5 | 0% | 0% |
| Nasdaq-100 (QQQ) | 1503,4% | 20,3% | 20,6% | -35,1% | — | 100% | 100% |
| Top 20 — raiz com teto | 1309,8% | 19,3% | 19,7% | -32,2% | 20 | 100% | 100% |
| Top 20 — peso igual | 1271,9% | 19,1% | 20,0% | -32,9% | 20 | 90% | 100% |
| Top 15 — raiz com teto | 1265,6% | 19,0% | 20,3% | -30,3% | 15 | 96% | 100% |
| Top 15 — peso igual | 1211,1% | 18,7% | 20,7% | -33,8% | 15 | 88% | 100% |
| Top 10 — raiz com teto | 1789,3% | 21,6% | 21,0% | -30,0% | 10 | 100% | 100% |
| Top 10 — peso igual | 1704,7% | 21,3% | 21,3% | -33,3% | 10 | 100% | 100% |

### Alfa contra Fama-French 5 + momentum + qualidade (mensal, Newey-West)

| Carteira | Alfa a.a. | t | R² |
|---|---|---|---|
| Top 20 — raiz com teto | +3,5 | 1,53 | 0,83 |
| Top 20 — peso igual | +3,4 | 1,44 | 0,85 |
| Top 15 — raiz com teto | +3,8 | 1,43 | 0,78 |
| Top 15 — peso igual | +3,2 | 1,22 | 0,80 |
| Top 10 — raiz com teto | +6,2 | 1,88 | 0,71 |
| Top 10 — peso igual | +5,3 | 1,70 | 0,73 |
| OoL novo | +0,9 | 0,71 | 0,91 |
| Nasdaq-100 (QQQ) | +3,1 | 2,19 | 0,92 |

Top 20 nos EUA: 20–20 ações por trimestre; troca média de 21% dos nomes por trimestre; setores: Information Technology 28%, Consumer Discretionary 21%, Industrials 16%, Health Care 10%.

**Top 20 de hoje (EUA, 09/2026):** COIN, SMCI, APP, NVDA, LYV, MO, PODD, PGR, EXPE, BKNG, EME, SBAC, HIG, STX, PTC, CMG, WRB, FIX, TRV, LII


## 2. Brasil (fora da amostra, 06/2014 a 09/2026, em reais)

| Carteira | Ações (média) | Retorno anual | vs Ibovespa | Pior queda | Janelas 3a > Ibov | Janelas 5a > Ibov |
|---|---|---|---|---|---|---|
| Top 20 — raiz com teto | 15 | **9,9%** | -1,0 | -44,2% | 56% | 69% |
| Top 20 — peso igual | 15 | **9,1%** | -1,8 | -47,0% | 54% | 68% |
| Top 15 — raiz com teto | 13 | **10,5%** | -0,4 | -44,4% | 60% | 70% |
| Top 15 — peso igual | 13 | **9,7%** | -1,2 | -47,0% | 54% | 68% |
| Top 10 — raiz com teto | 9 | **11,0%** | +0,1 | -46,7% | 69% | 91% |
| Top 10 — peso igual | 9 | **11,1%** | +0,2 | -48,6% | 71% | 82% |
| Universo (todas as classificadas), peso igual | — | **11,9%** | +1,0 | -49,3% | 73% | 84% |
| Ibovespa (BOVA11) | — | **10,9%** | +0,0 | -46,9% | 0% | 0% |
| Small caps (SMAL11) | — | **4,9%** | -6,0 | -51,1% | 46% | 39% |