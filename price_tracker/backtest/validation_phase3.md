# Fase 3: alfa contra fatores conhecidos (universo point-in-time, ROIC oficial)

> ⚠️ **ROIC:** carteiras com o ROIC oficial (B com reserva em A).

Regressões mensais 10/2011–08/2026, erros de Newey-West (6 defasagens). Fatores: Fama-French 5 (mercado, tamanho, valor, rentabilidade, investimento), momentum (Kenneth French) e Quality Minus Junk (AQR, EUA).

## 1. Retorno da carteira − taxa livre de risco

| Carteira | Alfa a.a. | t | Mkt | SMB | HML | RMW | CMA | UMD | QMJ | R² |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Good Companies, Great Returns | **+0,8%** | 0,57 | 1,00 | 0,27 | 0,06 | 0,17 | 0,07 | -0,10 | 0,11 | 0,90 |
| C3 OoL original (controle) | **-1,0%** | -0,65 | 1,09 | 0,11 | -0,05 | 0,12 | -0,05 | -0,07 | 0,03 | 0,84 |
| C2a OoL Base | **-0,4%** | -0,23 | 0,98 | 0,27 | 0,24 | 0,10 | 0,03 | -0,02 | 0,11 | 0,82 |
| C2b OoL High Returns | **+0,6%** | 0,29 | 1,07 | 0,22 | -0,15 | 0,28 | -0,08 | -0,01 | 0,06 | 0,78 |
| C2c OoL High Growth | **-0,3%** | -0,13 | 1,10 | 0,04 | -0,18 | 0,15 | -0,03 | -0,17 | -0,06 | 0,75 |
| C2d OoL corte 12% (todas) | **-0,7%** | -0,57 | 1,07 | 0,14 | 0,02 | 0,11 | -0,02 | -0,08 | 0,07 | 0,90 |
| Universo EW | **-0,5%** | -0,65 | 0,97 | 0,15 | 0,13 | 0,10 | 0,10 | -0,05 | 0,07 | 0,95 |

## 2. Retorno da carteira − universo EW (long-short contra a contraprova)

| Carteira | Alfa a.a. | t | Mkt | SMB | HML | RMW | CMA | UMD | QMJ | R² |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Good Companies, Great Returns | **+1,3%** | 1,22 | 0,03 | 0,13 | -0,07 | 0,07 | -0,03 | -0,05 | 0,04 | 0,13 |
| C3 OoL original (controle) | **-0,5%** | -0,27 | 0,12 | -0,04 | -0,18 | 0,03 | -0,15 | -0,02 | -0,04 | 0,21 |
| C2a OoL Base | **+0,1%** | 0,08 | 0,00 | 0,12 | 0,11 | 0,01 | -0,07 | 0,03 | 0,04 | 0,07 |
| C2b OoL High Returns | **+1,1%** | 0,49 | 0,09 | 0,08 | -0,27 | 0,18 | -0,18 | 0,04 | -0,01 | 0,20 |
| C2c OoL High Growth | **+0,2%** | 0,07 | 0,13 | -0,11 | -0,31 | 0,05 | -0,13 | -0,12 | -0,14 | 0,23 |
| C2d OoL corte 12% (todas) | **-0,2%** | -0,13 | 0,09 | -0,00 | -0,11 | 0,01 | -0,12 | -0,03 | -0,01 | 0,21 |

Leitura dos betas: RMW e QMJ positivos = exposição a qualidade/rentabilidade; UMD = momentum; HML negativo = viés de crescimento; SMB = tamanho. O alfa é o que sobra depois desses fatores.