# Métrica × retorno, com R² (OoL e GCGR, EUA, point-in-time)

> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). ROIC, zROIC, P/E justo, reinvestimento e retorno esperado dependem dele.

Configuração: sem zROIC, OoL a partir de ROIC 12%. Retorno = excesso sobre a média do universo, anualizado. **Empresa**: mediana da métrica nas posições da empresa na classe × excesso médio (mín. 4 trimestres; OoL 207 empresas, GCGR 179). **Posição**: métrica na data × excesso do trimestre seguinte (OoL 2758, GCGR 1559 posições). Métrica e retorno aparados em 1%/99%. Entre parênteses, o sinal da inclinação (+ = métrica maior, retorno maior). Em negrito, R² ≥ 0,02.

**Escala do R²:** 0,01 = a métrica explica 1% da variação do retorno. Em retorno de ações, um R² de 0,01 por posição já é relevante economicamente; por empresa (poucas observações), valores abaixo de ~0,04 não se distinguem de acaso.

**Atenção ao R² por empresa (mediana):** a mediana da métrica inclui trimestres posteriores à compra. Se a ação sobe, o P/L sobe junto, então P/L, P/E justo ÷ P/L e retorno com convergência ficam mecanicamente ligados ao retorno. Por isso há a coluna **na primeira compra** (métrica no primeiro trimestre da empresa na classe), que não tem esse viés.

| Métrica | OoL: empresa, na 1ª compra | GCGR: empresa, na 1ª compra | OoL: empresa, mediana | GCGR: empresa, mediana | OoL: por posição | GCGR: por posição |
|---|---|---|---|---|---|---|
| Alíquota de imposto | **0,080** (−) | 0,000 (−) | **0,083** (−) | 0,000 (−) | 0,004 (−) | 0,000 (−) |
| ROE do último ano (financeiras) | **0,035** (−) | **0,068** (+) | **0,039** (−) | **0,057** (+) | 0,001 (+) | 0,011 (+) |
| P/E justo | 0,016 (+) | **0,063** (+) | **0,037** (+) | **0,091** (+) | 0,000 (+) | 0,007 (+) |
| Desvio-padrão do ROIC (6a) | 0,009 (+) | **0,045** (+) | 0,016 (+) | 0,015 (+) | 0,000 (+) | 0,002 (+) |
| ROIC do modelo | 0,005 (+) | **0,032** (+) | 0,006 (+) | **0,025** (+) | 0,000 (+) | 0,003 (+) |
| Tamanho: log10 NOPAT (US$ bi) | **0,029** (+) | 0,000 (+) | **0,048** (+) | 0,004 (+) | 0,005 (+) | 0,000 (+) |
| Reinvestimento (g ÷ ROIC) | 0,013 (−) | **0,024** (−) | 0,016 (−) | **0,035** (−) | 0,000 (−) | 0,004 (−) |
| P/E justo ÷ P/L | 0,001 (−) | **0,021** (+) | **0,029** (−) | 0,000 (+) | 0,000 (−) | 0,004 (+) |
| ROIC do último ano | 0,010 (+) | 0,017 (+) | 0,008 (+) | **0,025** (+) | 0,000 (+) | 0,006 (+) |
| Retorno esperado | 0,002 (−) | 0,013 (+) | 0,013 (−) | 0,002 (+) | 0,000 (−) | 0,003 (+) |
| Retorno com convergência ao P/E justo | 0,002 (−) | 0,012 (+) | 0,019 (−) | 0,001 (+) | 0,000 (−) | 0,003 (+) |
| g (perpetuidade) | 0,001 (+) | 0,009 (+) | 0,014 (+) | 0,015 (+) | 0,000 (+) | 0,000 (+) |
| zROIC | 0,003 (+) | 0,008 (+) | 0,008 (+) | 0,003 (+) | 0,000 (+) | 0,001 (+) |
| P/L | 0,002 (+) | 0,007 (+) | **0,103** (+) | **0,046** (+) | 0,000 (−) | 0,000 (+) |
| Retorno com múltiplo constante | 0,001 (−) | 0,007 (+) | 0,001 (+) | 0,006 (+) | 0,000 (−) | 0,000 (+) |
| Crescimento do EPS (G) | 0,001 (−) | 0,007 (+) | 0,001 (+) | 0,007 (+) | 0,000 (−) | 0,000 (+) |
| Crescimento do capital no ano | 0,000 (+) | 0,004 (+) | 0,008 (−) | 0,010 (+) | 0,000 (−) | 0,003 (+) |
| Peso de ágio + intangíveis no capital | 0,001 (+) | 0,002 (+) | 0,001 (+) | 0,003 (+) | 0,000 (−) | 0,001 (+) |
| Dividend yield | 0,002 (+) | 0,001 (+) | 0,001 (−) | 0,006 (−) | 0,000 (−) | 0,000 (+) |
| zGrowth | 0,000 (−) | 0,001 (−) | 0,002 (−) | 0,000 (+) | 0,000 (+) | 0,001 (+) |