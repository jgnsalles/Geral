# Fase 4: overfitting e significância (universo point-in-time, ROIC oficial)

> ⚠️ **ROIC:** ROIC oficial (B com reserva em A).

## 1. Deflated Sharpe Ratio (excesso mensal sobre o universo EW)

Tentativas consideradas: 400. Variância do Sharpe entre tentativas estimada a partir de 584 configurações das varreduras.

| Carteira | Excesso a.a. | Sharpe mensal | Sharpe exigido por sorte | Prob. DSR | IC 90% do excesso a.a. (bootstrap) |
|---|---|---|---|---|---|
| C1 Good Companies, Great Returns | +1,3% | 0,09 | 0,21 | **5%** | -0,4% a +3,0% |
| C3 OoL original (controle) | +1,4% | 0,05 | 0,21 | **1%** | -1,9% a +5,0% |
| C2a OoL Base | +0,1% | 0,01 | 0,21 | **0%** | -2,1% a +2,3% |
| C2b OoL High Returns | +2,9% | 0,08 | 0,21 | **4%** | -0,7% a +6,6% |
| C2c OoL High Growth | +2,0% | 0,05 | 0,21 | **1%** | -2,7% a +6,8% |
| C2d OoL corte 12% (todas) | +1,2% | 0,06 | 0,21 | **2%** | -1,1% a +3,6% |

## 2. Probability of Backtest Overfitting (CSCV)

Grade de 96 configurações da Opportunity of Lifetime (corte de ROIC de 10% a 40% × corte de Growth de 10% a 35%), 60 trimestres em 10 blocos, 252 combinações. **PBO = 58%** (probabilidade de a melhor configuração dentro da amostra ficar abaixo da mediana fora dela; abaixo de 50% indica que escolher pelo passado ajuda).

## 3. Walk-forward (calibração 2012–2018, teste 2019–2026)

Melhor configuração em 2012–2018: ROIC ≥ 40,0%, Growth ≥ 25,0% — excesso no teste: **+5,0% a.a.** (mediana das 96 configurações no teste: +7,7%).

| Candidata congelada | Excesso 2012–2018 | Excesso 2019–2026 |
|---|---|---|
| C1 Good Companies, Great Returns | -0,8% | **+3,3%** |
| C3 OoL original (controle) | -3,3% | **+5,9%** |
| C2a OoL Base | -0,7% | **+0,9%** |
| C2b OoL High Returns | -1,9% | **+7,3%** |
| C2c OoL High Growth | -3,7% | **+7,3%** |
| C2d OoL corte 12% (todas) | -2,0% | **+4,3%** |

## 4. Placebo: carteiras aleatórias do mesmo tamanho

500 sorteios por candidata: a cada trimestre, o mesmo número de ações sorteado entre as empresas classificadas do universo point-in-time.

| Carteira | Retorno médio a.a. | Placebo: mediana | Placebo: percentil 95 | Percentil da candidata |
|---|---|---|---|---|
| C1 Good Companies, Great Returns | +15,8% | +14,6% | +16,2% | **87%** |
| C3 OoL original (controle) | +16,2% | +14,5% | +16,6% | **92%** |
| C2a OoL Base | +14,6% | +14,5% | +17,0% | **53%** |
| C2b OoL High Returns | +17,8% | +14,5% | +17,2% | **97%** |
| C2c OoL High Growth | +16,8% | +14,3% | +17,3% | **92%** |
| C2d OoL corte 12% (todas) | +15,9% | +14,5% | +16,1% | **92%** |