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
- 2026-11-10 — **Correção de leitura:** o usuário quis o filtro de crescimento só no **último ano** (y/y > 150%), não em qualquer um dos 5 anos
  (que tirava 46% das posições). Com a leitura certa saem 10% das posições. O teste anterior fica registrado como leitura errada; roda-se o correto.
- 2026-11-10 — **Resultado com a leitura certa (último ano > 150% ou P/L < 6 fora):** EUA 19,3% a.a. (sem filtro 19,7%; pior queda −32,2% contra
  −28,6%). Brasil 9,9% a.a. (sem filtro 12,5%; Ibovespa 10,9%). Também piora; filtros rejeitados.
- 2026-11-10 — **CANDIDATA FINAL CONGELADA (aprovada pelo usuário) para o teste no Japão, sem nenhum ajuste depois:**
  1. Elegíveis: ROIC do modelo ≥ 12% e crescimento do EPS (mediana de 5 anos) ≥ 15%; sem vestuário/calçados/têxteis e sem subsetores cíclicos
     (régua + exceções B); **fora se P/L < 4** (lucro positivo). Sem corte de crescimento do último ano.
  2. Ordenação: retorno esperado do modelo (P/E justo com ROIC limitado a 100% + múltiplo constante + dividendos), sem o corte de 20%; ficam as
     **20** maiores (empate: maior ROIC).
  3. Peso: raiz do valor de mercado com teto de 10% por ação. Rebalanceamento trimestral.
  Resultado conhecido (dentro da amostra/exploratório): EUA 19,7% a.a. (S&P 15,6%); Brasil 12,9% a.a. (Ibovespa 10,9%).
  Comparar no Japão com o TOPIX e o universo com peso igual; critério de sucesso: retorno acima dos dois.
- 2026-11-10 — **Teste fora da amostra nas estrangeiras listadas nos EUA (antes de rodar):** regra candidata congelada, sem ajuste, mesmos
  parâmetros dos EUA. Setores por código SIC da SEC (mapeamento fixado em `estrangeiras/backtest_fpi.py` antes de rodar). Só empresas com lucro por
  ação em dólar; preço ≥ US$ 2 e giro ≥ US$ 2 milhões/dia. Critério: Top 20 acima do universo estrangeiro de peso igual e dos ETFs ex-EUA.
- 2026-11-10 — **Resultado nas estrangeiras listadas nos EUA (inconclusivo):** com início quando há ≥ 50 empresas classificadas (03/2018): Top 20
  26,8% a.a. contra universo estrangeiro 7,3%, EFA 8,0% e S&P 15,1%; com ≥ 100 (03/2022): 34,1% contra 3,2%. Mas só ~9 a 12 ações elegíveis por
  trimestre (a Top 20 nunca enche) e a lista parte de quem tem ticker hoje (viés de sobrevivência). Sinal na direção certa, amostra fraca.
- 2026-11-10 — **Teste fora da amostra nas médias e pequenas dos EUA (antes de rodar):** universo = empresas americanas listadas na Nasdaq/NYSE
  (lista atual da SEC, sem as estrangeiras) que **não** estão no S&P 500 na data, com valor de mercado ≥ US$ 1 bi (preço × lucro líquido ÷ EPS),
  preço ≥ US$ 5 e giro mediano ≥ US$ 5 milhões/dia. Regra candidata congelada, sem ajuste, mesmos parâmetros. Setores por SIC (mesmo mapeamento
  das estrangeiras). Critério: Top 20 acima do universo de peso igual e dos ETFs de médias e pequenas (IJH, IJR, IWM). Limite conhecido: lista
  parte de quem tem ticker hoje (viés de sobrevivência).
- 2026-11-10 — **Resultado nas médias e pequenas dos EUA (06/2011–09/2026, 684 classificadas e 93 elegíveis por data):** Top 20 raiz com teto
  16,5% a.a. contra universo de peso igual 11,9%, S&P 400 (IJH) 10,5%, S&P 600 (IJR) 10,6% e Russell 2000 9,8%. **Passou.** Mas as elegíveis de
  qualidade com peso igual renderam 17,1% (97% das janelas de 5 anos acima do universo, contra 58% da Top 20): a ordenação por retorno esperado não
  agregou aqui. Lista parte de quem tem ticker hoje (viés de sobrevivência; o universo de peso igual sofre o mesmo viés).
- 2026-11-10 — **Teste fora da amostra na China, ações A (antes de rodar):** regra candidata congelada, mesmos parâmetros dos EUA. Fundamentos
  anuais em lote do Eastmoney com data de divulgação; preços do Yahoo em yuan. Diferenças forçadas pelos dados e mapeamento de setores Shenwan
  fixados em `china/backtest_cn.py` antes de rodar. Critério: Top 20 acima do universo de peso igual e do CSI 300/CSI 500.
- 2026-11-10 — **Resultado na China, ações A (06/2013–09/2026): FALHOU.** Top 20 raiz com teto 3,7% a.a. contra universo de peso igual 8,5%,
  CSI 300 5,3% e CSI 500 6,5% (índices sem dividendos). O próprio filtro de qualidade também ficou abaixo do universo (elegíveis 6,1–6,6%).
  Ressalvas: ROIC reconstruído com poucos itens; crescimento pelo lucro líquido; universo de peso igual com viés de sobrevivência e efeito
  pequenas-empresas típico do mercado chinês.

## 2026-11-11 — Proxy Fama-French (mais países e mais anos), NÃO é a regra congelada
Carteiras públicas de Kenneth French (rentabilidade operacional × valor patrimonial/preço, peso por valor de mercado). Rentabilidade alta bateu o
mercado no período todo nos EUA desde 1963 (+2,5 p.p.), Europa (+1,9), Japão (+2,2), Ásia-Pacífico ex-Japão (+2,9) e emergentes (OP alto e barata +4,4);
quase todo o ganho veio até 2010. Desde 2011 a vantagem sumiu fora dos EUA (±0,5) e nos EUA o proxy perdeu (sem o filtro de crescimento do EPS).
Detalhes: french/resultado.md. Script: french/proxy.py.

## 2026-11-11 — Correção de dado no Brasil (não é mudança de regra)
Bug na leitura da CVM: algumas empresas preenchem a linha "lucro atribuído à controladora" com 0 (ex.: Sabesp 2023–2025, Pague Menos 2023,
Vivara 2022, Tegma 2025); 425 balanços afetados, a maioria de 2021 em diante. Corrigido em `brasil/prep_br.py` (usa o lucro consolidado − não controladores).
Regra congelada reaplicada sem mudança. Brasil, raiz do valor de mercado: OoL novo 13,5% → 13,3%; Top 20 12,9% → 12,5% (Ibovespa 10,9%).
Observação do usuário (não muda nada ainda): o crescimento brasileiro é a mediana de 5 variações anuais do lucro líquido e esconde quedas recentes
(2025: São Martinho −62%, Engie −40%, Cemig −31%) e a recuperação pós-COVID de 2021.

## 2026-11-11 — Pré-registro: crescimento do Brasil sem o ano da recuperação pós-COVID (pedido do usuário)
Motivo: o crescimento de 2021 (2021 sobre 2020) reflete a volta da pandemia, não a economia do negócio. Variantes, registradas antes de rodar:
A) tira o crescimento de 2021 da mediana (janela de 5 anos fica com 4 variações quando inclui 2021);
B) tira 2020 e 2021 (a queda e a volta da COVID).
Resto da regra congelada igual. Comparação: OoL novo e Top 20 (raiz com teto), Brasil, contra a regra atual e o Ibovespa.

**Resultado (2026-11-11):** Top 20 (raiz, teto 10%, mesma conta dentro do script): com 2021 13,1%, sem 2021 13,5%, sem 2020–2021 12,9% (Ibovespa 10,9%).
OoL novo (raiz): 13,3% / 12,8% / 13,5%. Diferenças pequenas, dentro do ruído. **Decisão do usuário: adotar A (sem 2021) no Brasil**
(`EXCL = {2021}` em `brasil/backtest_br.py`; classes antigas em `classes_pit_com2021.csv`). EUA sem mudança por enquanto.
**Número oficial da candidata no Brasil (P/L ≥ 4, `backtest/filtro_grade.py`):** 12,9% antes → 12,4% com o dado corrigido → **12,0%** sem 2021 (sem 2020–2021 também 12,0%); Ibovespa 10,9%. O script `brasil/sem2021.py` estima o valor de mercado de outro jeito e dá números mais altos; vale o oficial.

## 2026-11-12 — Pré-registro: teste "mundo" (todas as bases juntas)
Pedido do usuário: aplicar a regra congelada num só universo com todas as bases já montadas, para escolher as maiores oportunidades em qualquer lugar.
Universo: S&P 500 point-in-time + médias e pequenas dos EUA (≥ US$ 1 bi) + estrangeiras listadas nos EUA (20-F/40-F) + Brasil (CVM), tudo em dólar.
Cada base mantém a própria classificação, o próprio mapa de cíclicos/vestuário e o próprio retorno esperado (EUA: WACC 8,5%; Brasil: WACC 12%).
Para comparar o Brasil com os EUA, o retorno esperado brasileiro é reduzido em 3,5 p.p. (a diferença de WACC), fixado antes de rodar.
Preços do Brasil convertidos para dólar pelo câmbio diário (BRL=X). Mesma empresa em duas bases (ADR e ação local): fica só a de maior valor de mercado.
Regra igual: elegíveis ROIC ≥ 12%, crescimento ≥ 15%, P/L ≥ 4, sem cíclicos e vestuário; Top 20 por retorno esperado; raiz do valor de mercado, teto 10%; trimestral.
Comparações: MSCI ACWI (ACWI), S&P 500, as Top 20 de cada base sozinha e os 9 comparativos obrigatórios dos EUA. Sensibilidade (não é o produto): sem o ajuste de 3,5 p.p.

**Resultado do teste mundo (2026-11-12, 06/2014–09/2026, em dólares):** Top 20 mundo 14,4% a.a. (sem o ajuste do Brasil 14,6%) contra ACWI 10,3% e S&P 500 13,6%.
Pior que a Top 20 só do S&P 500 no mesmo período (17,2%). As médias e pequenas dominam a lista (67% das posições) com retornos esperados extremos e dados ruidosos
(hoje: Cal-Maine com crescimento de 338%, Power Solutions com ROIC de 2.258%, Rayonier com ROIC de 444%). Juntar as bases não melhorou o resultado.
