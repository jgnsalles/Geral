# Protocolo de validação (pré-registro) — Price Tracker

Data do registro: 2026-11-10. Este documento congela hipóteses, regras e critérios de sucesso **antes** dos testes de
confirmação. Qualquer mudança depois desta data deve ser registrada no fim do arquivo, com data e motivo.

> ⚠️ **ROIC:** a definição oficial de ROIC será escolhida na Fase 1 por critérios de validade econômica, sem olhar retorno,
> e só então congelada. Os demais parâmetros abaixo valem para qualquer definição.

## 1. Histórico de exploração (transparência)

Até esta data foram testadas cerca de **400 configurações** no mesmo período (EUA, 2012–2026): combinações de cortes
(ROIC, zROIC, Growth, zGrowth, retorno), g e WACC do P/E justo, definições de ROIC, ajustes de P/E justo, exclusões,
setores e duas parametrizações de Brasil. Esse número entra no cálculo do Deflated Sharpe Ratio e no limiar de significância.

## 2. Estratégias candidatas (congeladas)

Todas: método histórico point-in-time (só dados arquivados até a data), equal weight, rebalanceamento trimestral no último
pregão do trimestre, retorno total, custo de 10 bps por ponta. g por ranking da mediana de 5 anos do crescimento do EPS;
P/E justo `(1 − g/ROIC)/(WACC − g)`; retorno = média de (P/E converge ao justo em 2 anos) e (múltiplo constante) + dividend yield.

| # | Estratégia | ROIC alto / baixo | Growth alto / baixo | zGrowth | zROIC | Retorno alto / baixo | g / WACC |
|---|---|---|---|---|---|---|---|
| C1 | Good Companies, Great Returns (original) | 20% / 10% | 15% / 6% | 2,93 | 0,7 | 20% / 8% | 7%→3,5% / 8,5% |
| C2a | Esboço: OoL Base (ROIC ≥ 12%, sem HR/HG) | 12% / 10% | 15% / 6% | 2,93 | 0,7 | 20% / 8% | 7%→3,5% / 8,5% |
| C2b | Esboço: OoL High Returns (OoL com ROIC > 30%) | idem | idem | idem | idem | idem | idem |
| C2c | Esboço: OoL High Growth (OoL com EPS > 30%) | idem | idem | idem | idem | idem | idem |
| C2d | Esboço: OoL inteira (corte 12%) | idem | idem | idem | idem | idem | idem |
| C3 | Controle: Opportunity of Lifetime original | 20% / 10% | 15% / 6% | 2,93 | 0,7 | 20% / 8% | 7%→3,5% / 8,5% |

Quem tem ROIC > 30% e EPS > 30% entra em C2b e C2c. Financeiras: ROE no lugar do ROIC.

## 3. Testes de confirmação

1. **ROIC oficial (Fase 1):** escolhido entre (A) patrimônio + dívida − caixa com capital operacional quando ≤ 0 (atual),
   (B) capital operacional com ágio e intangíveis de aquisição, capital médio do ano, (C) ROIC marginal de 5 anos.
   Critérios, nesta ordem: % de valores absurdos (< 0 ou > 100%), persistência de um ano para o outro (correlação de postos),
   concordância com ROIC calculado à mão em ~30 empresas revisadas pelo usuário. **Retorno não entra na escolha.**
   Robustez: as estratégias são rodadas também com as outras duas definições.
2. **Universo point-in-time (Fase 2):** S&P 500 da data de cada rebalanceamento (base pública desde 1996). Empresas sem preço
   (deslistadas): teste de limites — cenário pessimista (−100% no trimestre da saída), neutro (retorno do universo) e otimista
   (retorno do S&P 500). Período: o mais longo que os balanços da SEC permitirem (≈ 2012 em diante).
3. **Fatores (Fase 3):** regressão mensal contra Fama-French 5 fatores + momentum + Quality Minus Junk (AQR).
4. **Overfitting (Fase 4):** Deflated Sharpe Ratio com ~400 tentativas; Probability of Backtest Overfitting (CSCV) na grade de
   configurações; walk-forward com calibração em 2012–2018 e teste em 2019–2026 **sem ajuste**; intervalos por bootstrap em blocos;
   placebo com carteiras aleatórias do mesmo tamanho.
5. **Japão (Fase 5):** mesmas regras (parâmetros dos EUA, sem recalibrar), dados EDINET + preços Yahoo (.T), universo TOPIX 500
   ou equivalente líquido, período disponível (≈ 2015 em diante).
6. **Implementação (Fase 6), poucas variantes definidas aqui:** rebalanceamento trimestral × mensal; equal weight × peso por score
   (rank de crescimento + rank de ROIC) com teto de 10% por ação × inverso da volatilidade; teto setorial de 35%.

## 4. Critérios de sucesso (definidos antes de testar)

Uma estratégia candidata é considerada **confirmada** se cumprir todos:

1. Excesso sobre o universo equal weight point-in-time > 0 no cenário **neutro** e ≥ 0 no **pessimista** do teste de limites.
2. Alfa contra FF5 + momentum + QMJ > 0, com t ≥ 2.
3. Deflated Sharpe Ratio com probabilidade ≥ 90% (considerando ~400 tentativas).
4. Excesso > 0 no período de teste do walk-forward (2019–2026), com parâmetros congelados.
5. Japão: excesso > 0 sobre o universo equal weight japonês (com amostra mais curta, basta o sinal).

Estratégias que cumprirem 1–4 e falharem em 5 são **confirmadas só para os EUA**. As demais ficam como **exploratórias**.

## 5. Expectativa de retorno do produto

O retorno esperado será reportado como uma faixa, aplicando ao excesso medido um desconto de 30% a 50% (decaimento fora da
amostra documentado na literatura), além de custos e do resultado do teste de limites de sobrevivência.

## 6. Registro de mudanças

- 2026-11-10 — criação do protocolo.
- 2026-11-10 — **ROIC oficial congelado (Fase 1):** definição (B) operacional com aquisições — NOPAT ÷ média do ano de
  [imobilizado + ágio + intangíveis + (ativo circulante − caixa) − (passivo circulante − dívida de curto prazo)] — com reserva em (A)
  (patrimônio + dívida − caixa; capital operacional se ≤ 0) quando (B) não é calculável. Teto de 100% no ROIC usado no P/E justo
  (a classificação usa o valor sem teto). Financeiras: ROE. Escolha por validade econômica (absurdos 10,8%, cobertura 98,6%,
  persistência 0,82), sem olhar retorno; aprovada pelo usuário.
- 2026-11-10 — **Resultados das Fases 2 a 4 (EUA, universo point-in-time, ROIC oficial):** nenhuma candidata confirmada.
  Critério 1 (excesso no teste de limites): passa C1, C2b, C2c, C2d, C3; falha C2a. Critério 2 (alfa contra FF5 + UMD + QMJ com t ≥ 2):
  falha em todas (maior t = 1,22, C1). Critério 3 (Deflated Sharpe ≥ 90%): falha em todas (0% a 5%). Critério 4 (excesso no teste
  2019–2026): passa em todas, mas todas tiveram excesso negativo em 2012–2018. PBO da grade = 58%. Viés de sobrevivência do universo
  antigo: +4 a +9 p.p. ao ano nas candidatas. Status de todas: **exploratória**. Fase 5 (Japão) pendente da chave da EDINET.
- 2026-11-10 — **Correções no ROIC (aprovadas pelo usuário; mudam a definição congelada):** (1) seguradoras de saúde (UNH, ELV, CNC, HUM,
  MOH, CI) passam a ser tratadas como financeiras: ROE no lugar do ROIC e bloco de g das financeiras. Motivo: o capital operacional (B) fica
  perto de zero (ativo circulante = aplicações; passivo circulante = sinistros a pagar), gerando ROIC de 111% a 2.001%. (2) Bug de coleta:
  o imobilizado de concessionárias (`PublicUtilitiesPropertyPlantAndEquipmentNet`) e de REITs (`RealEstateInvestmentPropertyNet`) não era
  lido; Entergy tinha imobilizado de US$ 0,2–0,5 bi (real ≈ US$ 50 bi) e ROIC de 140–370%. 67 empresas tiveram os dados da SEC rebaixados.
  Todos os testes point-in-time foram refeitos depois disso. Achado de exploração, não de confirmação.
- 2026-11-10 — **Definição "novo" (exploratória, para testar no Japão sem ajuste):** esboço (ROIC 12%/10%), sem zROIC, sem vestuário/calçados e sem
  subsetores cíclicos. Régua de cíclico (só fundamentos, histórico completo do ROIC, mediana do subsetor): queda média ≥ 2× a dos defensivos (30%) e
  ≥ 2 colapsos. Exceções escolhidas pelo usuário depois de ver o retorno (opção B): hotéis/cruzeiros, entretenimento, biotecnologia, montadoras e
  químicos básicos voltam. Excluídos (vão para a classe Cyclicals): Oil & Gas E&P, Equipment & Services, Drilling, Refining & Marketing; Copper; Steel;
  Fertilizers & Agricultural Chemicals; Department Stores; Passenger Airlines; Motorcycle Manufacturers; Casinos & Gaming; Interactive Home
  Entertainment; Multi-line Insurance; Health Care Distributors; Leisure Products; Apparel, Accessories & Luxury Goods; Footwear.
  Resultado EUA 2012–2026: OoL novo 17,1% a.a.; GCGR novo 16,9%; High ROIC 18,8%; High Growth 19,3%; Cyclicals 5,5%; S&P 500 15,6%.
  As exceções foram escolhidas olhando o retorno: o ganho delas sobre a régua pura (~0,5 p.p.) é suspeito de sobreajuste.
- 2026-11-10 — **REGRA CONGELADA (antes dos testes fora da amostra do Brasil, do modelo nulo e dos rivais).** Nenhum ajuste a partir daqui.
  Classe: OoL = ROIC ≥ 12% (médio 10–12%), sem zROIC, crescimento 15%/6%, zGrowth 2,93, retorno esperado 20%/8%; P/E justo com ROIC limitado a
  100%; ROIC oficial (B com reserva em A; financeiras e seguradoras de saúde com ROE). Exclusões: vestuário, calçados e têxteis + subsetores
  cíclicos da régua com as exceções da opção B (lista no registro anterior). **Ponderação principal: raiz do valor de mercado** (peso igual como
  controle). Rebalanceamento trimestral. Subclasses reportadas: High ROIC (ROIC > 30%) e High Growth (EPS > 30%).
  Brasil: os setores cíclicos e o vestuário são mapeados para os setores da CVM antes de rodar (lista em `brasil/oos_congelado.py`).
- 2026-11-10 — **Pré-registro da carteira de tamanho fixo (antes de rodar):** produto = **20 ações** (escolha do usuário); 10 e 15 são
  reportadas como sensibilidade, sem escolher depois. Elegíveis: ROIC do modelo ≥ 12% e crescimento do EPS (mediana de 5 anos) ≥ 15%, sem
  vestuário/calçados/têxteis e sem subsetores cíclicos (régua + exceções B; no Brasil, o mapeamento de `brasil/oos_congelado.py`). Nota = percentil
  do ROIC + percentil do crescimento entre os elegíveis da data; ficam as N maiores notas (empate: maior ROIC); com menos de N elegíveis, ficam todos.
  Sem P/E justo, retorno esperado ou zGrowth. Peso = raiz do valor de mercado com teto de 2/N por ação (redistribuído); peso igual como controle.
  Rebalanceamento trimestral. EUA: S&P 500 de cada trimestre, comparar com os 9 comparativos e o QQQ. Brasil: universo líquido da CVM, comparar
  com Ibovespa e universo.
- 2026-11-10 — **Resultado da carteira de tamanho fixo (pré-registrada):** EUA (dentro da amostra) Top 20 raiz com teto 22,2% a.a. (S&P 15,6%,
  QQQ 20,3%; alfa FF5+UMD+QMJ +3,9, t 1,76). **Brasil (fora da amostra): falhou** — Top 20 9,8% a.a. contra Ibovespa 10,9% e universo 11,9%;
  10 e 15 ações também abaixo. A OoL novo da regra congelada (com P/E justo e retorno esperado) passou no Brasil (13,5%, +2,6 p.p. sobre o Ibovespa).
- 2026-11-10 — **Pré-registro (sugestão do usuário, feita depois de ver EUA e Brasil):** mesma carteira de tamanho fixo, mesmas elegíveis
  (ROIC ≥ 12%, crescimento ≥ 15%, sem cíclicos e vestuário), mas ordenadas pelo **retorno esperado do modelo** (P/E justo + múltiplo constante +
  dividendos, ROIC limitado a 100% no P/E justo), sem o corte de 20%: ficam as N de maior retorno esperado (empate: maior ROIC). Produto N = 20;
  15 e 10 como sensibilidade. Peso = raiz do valor de mercado com teto de 2/N; peso igual como controle. EUA e Brasil (parâmetros brasileiros).
  Por ter sido proposta depois dos resultados, conta como exploratória até o Japão.
- 2026-11-10 — **Resultado da Top 20 por retorno esperado:** EUA 19,7% a.a. (S&P 15,6%, QQQ 20,3%; pior queda −28,6%, a menor das carteiras;
  alfa +4,5, t 1,82). Brasil 12,5% a.a. (Ibovespa 10,9%, universo 11,9%). Primeira regra que fica acima do índice nos dois países.
- 2026-11-10 — **Pré-registro (regra do usuário, depois de ver os erros):** Top 20 por retorno esperado com dois filtros a mais nas elegíveis:
  fora se alguma taxa anual de crescimento do lucro nos 5 anos da janela passar de **150%**, e fora se o **P/L < 6** (lucro positivo). O resto igual.
  EUA e Brasil (no Brasil, crescimento do lucro líquido dos controladores, como no modelo brasileiro). Exploratória até o Japão.
- 2026-11-10 — **Resultado dos filtros (crescimento anual > 150% e P/L < 6 fora): piorou nos dois países.** EUA 18,8% a.a. (sem os filtros 19,7%;
  pior queda −38,1% contra −28,6%). Brasil 7,7% a.a. (sem os filtros 12,5%; Ibovespa 10,9%). Filtros rejeitados; fica a Top 20 sem eles.
