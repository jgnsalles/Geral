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

## 2026-11-14 — Pré-registro: versão de giro menor (pedido do usuário)
Igual à candidata congelada, com uma regra de permanência: a ação que já está na carteira só sai se cair para fora do **top 30** do ranking de
retorno esperado (ou deixar de ser elegível); as vagas são preenchidas pelas melhores do ranking que ainda não estão na carteira. Continua com 20 ações,
raiz do valor de mercado com teto de 10%, trimestral. Produto testado: top 30. Sensibilidade: top 25 e top 40.
Medidas: retorno antes e depois de 15% de IR sobre ganho realizado, trades por ano, giro e tempo de permanência. EUA e Brasil.
**Resultado (2026-11-14):** top 30 não ajudou. EUA: 19,9% → 19,6% antes do IR e 17,2% → 17,0% depois; trades por ano 32 → 21. Brasil: 13,5% → 12,8% e
11,7% → 11,2% depois do IR. O custo do IR caiu só 0,2 p.p. porque o rebalanceamento trimestral dos pesos (podar as que subiram) também realiza ganho.
Candidata mantida sem mudança.

## 2026-11-14 — Pré-registro: grade de frequência de rebalanceamento × tamanho da carteira (pedido do usuário)
Frequência: mensal, trimestral (atual) e anual. Tamanho: 10, 15, 20 (atual), 30 e 50 ações. Resto igual à candidata (ROIC ≥ 12%, crescimento ≥ 15%,
P/L ≥ 4, sem cíclicos/vestuário, ordem pelo retorno esperado, raiz do valor de mercado com teto de 10%; com 10 ações o teto deixa o peso igual).
Mensal: os fundamentos são os da última data trimestral (os dados só existem por trimestre); preço, P/L, valor de mercado e retorno esperado são
recalculados com o preço do fim de cada mês. Anual: média das 4 versões possíveis (começando em cada trimestre), para não depender do mês escolhido.
Mesma janela para todas (a partir do 4º trimestre da amostra). Antes e depois de 15% de IR sobre ganho realizado. EUA e Brasil.
**Resultado (2026-11-14):** EUA 06/2012–09/2026, 20 ações trimestral 19,0% (16,3% após IR); mensal 19,2%; anual 18,1%; 10 ações trimestral 22,7% (19,4% após IR),
mas o anual com 10 ações varia de 17,9% a 22,8% conforme o mês de início (sinal de concentração/sorte). Brasil: trimestral 14,9% com 15 ou 20 ações; anual perde ~2,5 p.p.
Mensal não agrega em nenhum dos dois. Candidata mantida (20, trimestral); 10 ações fica como observação, não como mudança.

## 2026-11-14 — Investigação do ROIC, etapa 1 (diagnóstico; nada é adotado aqui)
(1) Quanto a estratégia depende da definição do ROIC: Top 20 congelada com o ROIC oficial (B), com o clássico (A), com o menor dos dois (conservador)
e sem o filtro de ROIC (P/E justo continua com o B). (2) Auditoria componente por componente das ações das carteiras de hoje nos EUA.
(3) Diagnóstico dos casos extremos (ROIC > 100%, capital quase zero, patrimônio negativo, dados faltando).

## 2026-11-14 — Pré-registro: ROIC triangulado (definição do usuário + revisão da literatura)
Referências: McKinsey *Valuation* (capital investido pelo lado operacional e pelo do financiamento), Damodaran (arrendamentos capitalizados,
capital do início do ano), Mauboussin (ROIC incremental sobre o reinvestimento acumulado), Greenblatt (capital tangível) e o ROCE do Wisesheets (descartado).
**Três visões, calculadas por exercício (capital médio do ano) e resumidas como hoje: média de (média dos 3 últimos anos, média dos 6):**
1. **Ativo** = imobilizado (inclui propriedades de óleo e gás) + direito de uso de arrendamentos + ágio + intangíveis (vida definida e indefinida)
   + investimentos de longo prazo (participações e coligadas) + capital de giro operacional
   [(ativo circulante − caixa − aplicações de curto prazo) − (passivo circulante − dívida de curto prazo − arrendamento de curto prazo)].
2. **Passivo** = patrimônio + minoritários + dívida total (curto + longo prazo) + dívida de arrendamento − caixa − aplicações de curto prazo.
3. **Marginal** = (NOPAT ajustado do ano t − NOPAT ajustado de t−5) ÷ reinvestimento acumulado de t−5 a t−1 (capex − depreciação + aquisições + variação
   do capital de giro); sem valor se o reinvestimento ≤ 0.
**Numerador (ativo e passivo):** NOPAT = lucro operacional × (1 − alíquota efetiva, entre 0 e 50%; 21% se indefinida) + juros implícitos dos arrendamentos
× (1 − alíquota) [dívida de arrendamento × taxa média informada; 5% se não houver] + resultado de equivalência patrimonial × (1 − alíquota).
**Arrendamentos antes de 2019** (fora do balanço): dívida = valor presente a 5% da tabela de aluguéis futuros da nota; ativo de direito de uso = esse mesmo valor.
**Financeiras e seguradoras de saúde:** continuam com ROE (sem mudança).
**Regra de "arte" (combinação), definida pelo usuário:**
 a) cada visão: < 0 ou > 200% é descartada; entre 150% e 200% conta como 150%;
 b) ativo e passivo válidos e próximos (maior ≤ 2× a menor): ROIC = média dos dois;
 c) muito diferentes (> 2×): vale a mais próxima do marginal; sem marginal válido, a menor;
 d) só uma das duas válida: ela; nenhuma válida mas alguma > 200%: 150%; nenhuma: usa o marginal se válido, senão sem ROIC;
 e) o marginal não entra na média; alerta "qualidade caindo" se marginal < 12% e reinvestimento acumulado pequeno (< 10% do capital).
**Marginal:** ano sem capex ou depreciação é completado pela média dos anos com dado (mínimo 3 de 5). **Correções de dado incluídas:** intangíveis de vida indefinida (Comcast etc.), imobilizado de petroleiras, aplicações de curto prazo fora do capital de giro.
**Não entra agora (variante futura):** capitalização de P&D. **Ordem:** primeiro a conferência empresa por empresa (validação qualitativa do usuário);
o backtest com a regra congelada vem depois, contra o ROIC oficial atual.
**2026-11-14:** conferência aceita pelo usuário ("Ok"); segue o backtest da regra congelada com o ROIC triangulado contra o oficial.
**Resultado (2026-11-14):** Top 20 com ROIC triangulado 20,3% a.a. (oficial 19,9%; S&P 15,6%), pior queda −32,7% (oficial −28,1%).
OoL novo 17,1% → 18,3%; High ROIC 18,8% → 21,7%; High Growth 19,3% → 20,5%; GCGR novo 16,9% → 16,5%. Ganho pequeno, mas na direção certa em quase
todas as classes, com uma definição mais defensável. Adoção depende do usuário.

## 2026-11-14 — Decisão: ROIC triangulado adotado como oficial nos EUA; pré-registro da regra de outliers
Decisão do usuário: adotar o ROIC triangulado (financeiras e seguradoras de saúde seguem com ROE). Médias e pequenas, estrangeiras e Brasil ainda não têm
os dados novos e seguem com a definição anterior.
**Regra de outliers (pedido do usuário: "tira outliers, não 2021 como regra")**, aplicada à série anual de cada visão (ativo e passivo) antes da média de 6 anos:
um ano é outlier se |ROIC do ano − mediana dos 6 anos| > 3 × σ, com σ = máx(1,4826 × desvio absoluto mediano, 25% da mediana em módulo, 2 p.p.).
Só os 4 anos mais antigos podem sair (os 2 mais recentes sempre ficam, para não punir quem está melhorando, como a NVIDIA); ficam no mínimo 3 anos.
Comparação: Top 20 e classes novas com o triangulado sem e com a regra de outliers, mais os 9 comparativos obrigatórios.
**Resultado da regra de outliers (2026-11-14):** neutra. Top 20: 20,3% → 20,5%; OoL novo 18,3% → 18,2%; High ROIC 21,7% → 21,5%. Adotada (decisão do usuário).
Com o ROIC novo: OoL novo 18,2%, GCGR novo 16,8%, High ROIC 21,5%, High Growth 20,6%, Top 20 20,5% (S&P 15,6%).

## 2026-11-14 — Pré-registro: regra de outliers no crescimento (pedido do usuário)
Problema: o crescimento é a mediana das 5 últimas variações anuais do lucro por ação, mas um ano excepcional (ganho ou perda não recorrente, ex.: separação
da Kenvue na J&J em 2023) gera duas variações extremas seguidas, uma para cima e outra para baixo, e distorce a mediana e o zGrowth.
**Regra:** um ano é "pico" (ou "vale") se o lucro daquele ano for ≥ 1,5× (ou ≤ 1/1,5) a média geométrica do ano anterior e do seguinte (lucros positivos).
O ano sai e as duas variações que o envolvem viram uma só: a variação anualizada de dois anos (do ano anterior ao seguinte). Picos tratados do maior para o
menor, sem sobreposição; o último ano nunca sai (não tem ano seguinte). Mediana e zGrowth recalculados com as variações ajustadas.
**Testes:** EUA (com o ROIC oficial novo): classes novas e Top 20 sem e com a regra. Brasil (lucro da controladora): (A) atual, sem 2021; (B) regra de
picos no lugar de tirar 2021; (C) as duas juntas. Mais os 9 comparativos obrigatórios. Nada é adotado sem decisão do usuário.
**Resultado (2026-11-14):** EUA pior: Top 20 20,5% → 19,7%; OoL novo 18,2% → 17,6%; High ROIC 21,5% → 20,4%; High Growth 20,6% → 21,2%. A regra mudou o crescimento
em 37% das observações (agressiva demais: funde ciclos reais, não só eventos únicos). Brasil: Top 20 13,5% nas três versões; OoL novo A 12,8%, B 13,8%, C 13,0%.
Nada adotado; decisão do usuário pendente.

## 2026-11-14 — Pré-registro: regra de picos menos agressiva (pedido do usuário)
Igual à anterior, mas o pico/vale exige lucro ≥ **2×** (ou ≤ ½) a média geométrica dos vizinhos (antes 1,5×). Mesmos testes (EUA e Brasil A/B/C).
Atenção: limite escolhido depois de ver o resultado de 1,5× (risco de sobreajuste maior).
**Resultado 2× (2026-11-14):** EUA: Top 20 20,5% → 22,4% (pior queda −34,4% → −32,0%); OoL novo 18,2% = 18,2%; High ROIC 21,5% = 21,5%; High Growth 20,6% → 21,7%;
GCGR novo 16,8% → 15,2%. Mudou 21% das observações (1,5×: 37%). Hoje sai J&J, entra Arch Capital. Brasil: Top 20 A 13,5%, B 13,2%, C 13,5%; OoL A 12,8%, B 13,6%, C 13,2%.
Ganho grande na Top 20 com limite escolhido após ver o 1,5× — tratar com cautela. Decisão do usuário pendente.
**Decisão do usuário (2026-11-14): regra de picos NÃO adotada** (nem 1,5× nem 2×). Argumento: o pico gera uma variação extrema para cima e outra para baixo,
que se cancelam, e a mediana já protege. Crescimento segue como estava (EUA: mediana de 5 anos; Brasil: mediana sem 2021).
**Racional registrado (2026-11-14):** um pico isolado gera uma variação muito alta seguida de uma muito baixa; na mediana de 5 anos as duas vão para as pontas
e sobram as 3 do meio. Evidência: com a regra, OoL novo e High ROIC não mudaram (18,2% e 21,5%). A mediana só falha com várias distorções na mesma janela
(ex.: J&J — 2021 +42%, 2023 +104% Kenvue, 2024 −58%, 2025 +90%), caso raro que nenhuma versão resolveu sem efeito colateral. O ganho da Top 20 com 2×
(+1,9 p.p.) foi tratado como provável sobreajuste. Brasil: mantido sem 2021 (decisão de 2026-11-11); pela mesma lógica poderia voltar, a reavaliar.
**Pendências do ROIC:** levar o triangulado ao Brasil (CVM), às médias e pequenas e às estrangeiras; separar o braço financeiro de empresas como a Deere;
testar P&D capitalizado como variante.

## 2026-11-14 — Pré-registro: ETF escolhido pela "cara de Opportunity of Lifetime" (pedido do usuário)
Composição real dos ETFs pelos relatórios N-PORT da SEC (trimestrais, desde o fim de 2019; ticker pelo CUSIP via OpenFIGI). SPY: composição reconstruída
com o S&P 500 point-in-time e peso por valor de mercado (o SPY não entrega N-PORT). ETFs: SPY, RSP, QUAL, SPHQ, JQUA, MTUM, VLUE, USMV, IWF, IWD, VUG, VTV,
SPYG, IJH, IJR, MOAT, SCHD, COWZ.
Em cada data trimestral, só com o que já era público (último N-PORT arquivado até a data) e a classificação daquela data (S&P 500 com o ROIC novo;
médias e pequenas com a definição anterior):
**Nota principal = % do peso do ETF (coberto pelo nosso universo) em ações Opportunity of Lifetime (novo).** Sensibilidade: retorno esperado médio ponderado
das ações do ETF (limitado a −50%/+100%). Estratégia: fica 1 trimestre no ETF de maior nota (sensibilidade: os 2 maiores, peso igual).
Comparações: SPY, os ETFs em peso igual, cada ETF sozinho, a Top 20 da estratégia no mesmo período e os 9 comparativos obrigatórios.
**Resultado (2026-11-14, 12/2019–09/2026):** os ETFs com mais OoL são os de crescimento: VUG, SPYG e IWF (33–34% do peso em OoL), depois QUAL (26%) e SPY (24%);
valor, dividendos e baixa volatilidade ficam em 6–10%. Ficar no ETF de maior nota: 18,7% a.a. (pior queda −32,7%) contra SPY 15,2%, ETFs em peso igual 13,9%,
SPYG parado 18,3%, VUG 18,2% e Top 20 em ações 21,1%. A rotação agrega só ~0,4 p.p. sobre ficar parado no SPYG; ~10 trocas em 7 anos. Período curto e favorável a crescimento.
**Padrão a partir de 2026-11-14 (pedido do usuário):** toda tabela de desempenho traz janelas móveis de 3, 5 e 10 anos (% que batem a referência e a pior janela).
**ETF × OoL em janelas:** ETF com mais OoL bate o S&P em 43% das janelas de 3 anos e 82% das de 5 (Top 20 em ações: 100% e 100%). Contra o SPYG parado, a rotação
ganha em só 39% (3a) e 23% (5a) das janelas: não agrega. Os 2 ETFs com mais OoL: 85% e 59% contra o SPYG.

## 2026-11-14 — Pré-registro: ETF com mais OoL trocado todo mês (pedido do usuário)
Igual ao teste trimestral, mas a nota é recalculada no fim de cada mês: composição do ETF = último N-PORT público (só existe por trimestre); fundamentos da
última data trimestral; preço do fim do mês → retorno esperado e classe OoL recalculados (OoL = crescimento > 15%, zGrowth < 2,93, ROIC > 12%, retorno
esperado > 20%, sem cíclicos/vestuário). Fica 1 mês no ETF de maior nota. Comparações: versão trimestral, SPYG parado, S&P 500, Top 20 em ações; janelas de 3 e 5 anos.
**Resultado (2026-11-14):** troca mensal 18,9% a.a. (trimestral 18,7%; SPYG parado 18,3%; S&P 15,2%; Top 20 em ações 21,1%). Bate o S&P em 59% das janelas de 3 anos
e 95% das de 5 (trimestral: 43% e 82%). Contra o SPYG parado: 63% (3a) e 32% (5a); os 2 ETFs com mais OoL, troca mensal: 85% e 68%. 13 trocas em 82 meses.
Melhora pouco sobre o trimestral; continua bem atrás da Top 20 em ações (100%/100% contra o S&P).
