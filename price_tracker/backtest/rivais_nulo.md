# Regra congelada × modelos nulos × ETFs rivais × fatores (EUA, point-in-time)

> ⚠️ **ROIC:** os modelos nulos usam o mesmo ROIC oficial (corrigido em 2026-11-10); um erro nele afeta todos igualmente. Ainda em aberto: patrimônio negativo e ROIC > 100% em empresas leves em ativos.

**Regra congelada** = OoL novo / High ROIC / High Growth / GCGR novo, com a **raiz do valor de mercado** como ponderação principal. **Modelos nulos** = filtros simples, sem P/E justo, sem retorno esperado e sem zGrowth, com as mesmas exclusões de setor e as mesmas ponderações. ETFs a partir da data em que existem; o período comum começa em 07/2013 (início do QUAL).

## 1. Retornos

| Carteira | Ações | Retorno anual (período todo) | vs S&P | Retorno anual (período comum) | vs S&P (comum) | Pior queda |
|---|---|---|---|---|---|---|
| OoL novo — raiz | 42 | 18,9% | +3,3 | **17,5%** | +3,5 | -33,2% |
| OoL novo — peso igual | 42 | 17,1% | +1,6 | **14,9%** | +0,9 | -35,8% |
| OoL High ROIC (novo) — raiz | 16 | 20,4% | +4,9 | **19,9%** | +5,9 | -37,6% |
| OoL High ROIC (novo) — peso igual | 16 | 18,8% | +3,3 | **17,5%** | +3,5 | -33,8% |
| OoL High Growth (novo) — raiz | 16 | 20,0% | +4,4 | **20,0%** | +6,0 | -41,2% |
| OoL High Growth (novo) — peso igual | 16 | 19,3% | +3,8 | **18,5%** | +4,4 | -35,0% |
| GCGR novo — raiz | 23 | 18,0% | +2,4 | **17,6%** | +3,5 | -30,4% |
| GCGR novo — peso igual | 23 | 16,9% | +1,4 | **16,0%** | +2,0 | -32,3% |
| N1: só ROIC ≥ 12% e crescimento ≥ 15% — raiz | 68 | 19,1% | +3,6 | **17,8%** | +3,7 | -32,6% |
| N1: só ROIC ≥ 12% e crescimento ≥ 15% — peso igual | 68 | 17,7% | +2,2 | **15,6%** | +1,6 | -35,4% |
| N2: ROIC > 30% e crescimento > 30% — raiz | 10 | 28,0% | +12,4 | **30,3%** | +16,3 | -39,7% |
| N2: ROIC > 30% e crescimento > 30% — peso igual | 10 | 25,0% | +9,5 | **26,4%** | +12,4 | -35,7% |
| N3: ROIC > 30% (e crescimento ≥ 15%) — raiz | 25 | 21,9% | +6,3 | **21,4%** | +7,4 | -37,7% |
| N3: ROIC > 30% (e crescimento ≥ 15%) — peso igual | 25 | 20,4% | +4,8 | **19,3%** | +5,2 | -35,4% |
| N4: crescimento > 30% (e ROIC ≥ 12%) — raiz | 22 | 22,5% | +7,0 | **22,6%** | +8,6 | -38,9% |
| N4: crescimento > 30% (e ROIC ≥ 12%) — peso igual | 22 | 21,1% | +5,5 | **20,2%** | +6,2 | -33,3% |
| S&P 500 (SPY) | — | 15,6% | +0,0 | **14,0%** | +0,0 | -33,7% |
| S&P 500 equal weight (RSP) | — | 13,2% | -2,3 | **11,1%** | -2,9 | -39,0% |
| Qualidade (QUAL) | — | — | — | **13,6%** | -0,4 | -34,1% |
| Momentum (MTUM) | — | — | — | **15,6%** | +1,6 | -34,1% |
| Russell 1000 Growth (IWF) | — | 17,4% | +1,9 | **16,4%** | +2,4 | -32,7% |
| S&P 500 Growth (SPYG) | — | 17,4% | +1,9 | **16,5%** | +2,5 | -32,7% |
| Nasdaq-100 (QQQ) | — | 20,3% | +4,8 | **19,9%** | +5,9 | -35,1% |

### O P/E justo e o retorno esperado agregam? (regra − modelo nulo equivalente, período todo, p.p. a.a.)

| Comparação | Raiz | Peso igual |
|---|---|---|
| OoL novo − N1 | -0,2 | -0,6 |
| OoL High ROIC (novo) − N3 | -1,4 | -1,5 |
| OoL High Growth (novo) − N4 | -2,6 | -1,7 |

## 2. Regressão de fatores (mensal, retorno − taxa livre)

Fama-French 5 + momentum (UMD) + qualidade (QMJ, AQR). Erros de Newey-West. Meses disponíveis até 08/2026.

| Carteira | Alfa a.a. | t do alfa | Mercado | Tamanho (SMB) | Valor (HML) | Rentabilidade (RMW) | Investimento (CMA) | Momentum | Qualidade (QMJ) | R² |
|---|---|---|---|---|---|---|---|---|---|---|
| OoL novo — raiz | +1,8 | 1,34 | 1,10 | 0,03 | -0,08 | 0,14 | -0,15 | -0,01 | 0,05 | 0,91 |
| OoL novo — peso igual | +0,9 | 0,71 | 1,08 | 0,14 | 0,01 | 0,06 | -0,03 | -0,06 | 0,09 | 0,91 |
| OoL High ROIC (novo) — raiz | +2,8 | 1,28 | 1,12 | 0,17 | -0,21 | 0,33 | -0,22 | 0,04 | 0,02 | 0,80 |
| OoL High ROIC (novo) — peso igual | +1,8 | 1,05 | 1,11 | 0,21 | -0,14 | 0,11 | -0,13 | 0,01 | 0,13 | 0,80 |
| OoL High Growth (novo) — raiz | +2,9 | 1,01 | 1,13 | -0,03 | -0,32 | 0,24 | -0,24 | -0,07 | -0,09 | 0,77 |
| OoL High Growth (novo) — peso igual | +2,9 | 1,09 | 1,12 | 0,02 | -0,22 | -0,01 | -0,04 | -0,17 | 0,04 | 0,77 |
| GCGR novo — raiz | **+4,3** | **3,15** | 0,92 | 0,08 | -0,09 | 0,30 | 0,07 | -0,10 | -0,08 | 0,81 |
| GCGR novo — peso igual | +3,2 | 1,98 | 0,95 | 0,28 | -0,03 | 0,30 | 0,08 | -0,13 | 0,01 | 0,85 |
| N1: só ROIC ≥ 12% e crescimento ≥ 15% — raiz | +1,9 | 1,97 | 1,10 | -0,05 | -0,11 | 0,01 | -0,17 | -0,00 | 0,06 | 0,94 |
| N1: só ROIC ≥ 12% e crescimento ≥ 15% — peso igual | +1,1 | 1,02 | 1,10 | 0,11 | -0,04 | -0,04 | -0,10 | -0,05 | 0,13 | 0,93 |
| N2: ROIC > 30% e crescimento > 30% — raiz | **+9,7** | **2,56** | 1,11 | -0,13 | -0,27 | 0,28 | -0,46 | 0,09 | -0,16 | 0,62 |
| N2: ROIC > 30% e crescimento > 30% — peso igual | **+8,2** | **2,35** | 1,08 | -0,11 | -0,14 | -0,06 | -0,43 | 0,01 | -0,01 | 0,58 |
| N3: ROIC > 30% (e crescimento ≥ 15%) — raiz | +3,4 | 1,99 | 1,15 | 0,06 | -0,20 | 0,14 | -0,32 | 0,08 | 0,11 | 0,85 |
| N3: ROIC > 30% (e crescimento ≥ 15%) — peso igual | +2,6 | 1,59 | 1,15 | 0,13 | -0,14 | -0,11 | -0,27 | 0,03 | 0,23 | 0,83 |
| N4: crescimento > 30% (e ROIC ≥ 12%) — raiz | **+5,4** | **2,24** | 1,09 | -0,14 | -0,24 | 0,24 | -0,31 | -0,01 | -0,19 | 0,82 |
| N4: crescimento > 30% (e ROIC ≥ 12%) — peso igual | +4,6 | 1,97 | 1,10 | 0,00 | -0,17 | 0,01 | -0,15 | -0,11 | -0,02 | 0,81 |
| S&P 500 (SPY) | -0,2 | -0,91 | 0,99 | -0,11 | 0,02 | 0,04 | 0,02 | 0,00 | 0,01 | 1,00 |
| S&P 500 equal weight (RSP) | -1,1 | -1,41 | 0,97 | 0,15 | 0,16 | 0,09 | 0,14 | -0,06 | 0,01 | 0,96 |
| Qualidade (QUAL) | -0,9 | -1,08 | 0,99 | -0,06 | -0,04 | 0,11 | 0,03 | 0,02 | 0,07 | 0,96 |
| Momentum (MTUM) | -0,4 | -0,27 | 1,08 | -0,13 | -0,01 | -0,20 | 0,08 | 0,45 | -0,07 | 0,89 |
| Russell 1000 Growth (IWF) | +0,9 | 1,44 | 1,04 | -0,16 | -0,23 | 0,06 | -0,12 | 0,04 | -0,09 | 0,98 |
| S&P 500 Growth (SPYG) | +0,5 | 0,71 | 1,05 | -0,19 | -0,18 | 0,10 | -0,12 | 0,09 | -0,05 | 0,97 |
| Nasdaq-100 (QQQ) | **+3,1** | **2,19** | 1,09 | -0,25 | -0,26 | -0,10 | -0,20 | -0,00 | -0,07 | 0,92 |