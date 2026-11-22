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

## 2026-11-14 — Pré-registro: Fórmula Mágica de Joel Greenblatt (comparação, pedido do usuário)
Regra do livro (*The Little Book That Beats the Market*): retorno sobre capital = EBIT ÷ (capital de giro líquido + imobilizado líquido); rendimento =
EBIT ÷ valor da firma (valor de mercado + dívida + minoritários − caixa − aplicações). Ordena cada um, soma as posições, compra as melhores.
Sem financeiras e sem utilities. Dados do último exercício conhecido na data (SEC, point-in-time), universo S&P 500 point-in-time.
Versões: Top 20 e Top 30 em peso igual, rebalanceamento trimestral; Top 30 com troca anual (média das 4 versões, como no livro); Top 20 com o nosso peso
(raiz do valor de mercado, teto 10%). Comparações: 9 obrigatórios, Top 20 da estratégia, e no período 2019–2026 os ETFs (2 com mais OoL, troca mensal; SPYG).
**Resultado (2026-11-14, S&P 500, 2011–2026):** Fórmula Mágica Top 20 peso igual 15,1% a.a. (janelas 3a/5a/10a > S&P: 46%/28%/26%); Top 30 15,0%; Top 20 raiz com teto
16,3% (63%/50%/61%); Top 30 troca anual 15,1%. S&P 15,6%. Top 20 da estratégia OoL 20,5% (100%/100%/100%). 2019–2026: Fórmula 12,7–17,6%; ETFs OoL 18,7–18,9%;
SPYG 18,3%; Top 20 OoL 21,1%. A Fórmula Mágica não bate o S&P de forma consistente nas grandes empresas neste período.

## 2026-11-14 — Pré-registro: "Fórmula Mágica com G" (proposta do usuário)
Mesmo princípio de ranqueamento do Greenblatt, com três critérios somados (posição em cada um): **maior ROIC (o nosso, triangulado), maior crescimento
do lucro (mediana de 5 anos) e menor múltiplo**. Duas versões do múltiplo: (1) EV/EBIT (como o Greenblatt; sem financeiras e utilities) e (2) P/L
(sem financeiras e utilities, para comparar). Sensibilidade: (3) P/L com financeiras (ROE) e utilities; (4) versão 1 sem cíclicos e vestuário.
Lucro e múltiplo positivos (EBIT > 0, P/L > 0). Montagem como no teste do Greenblatt: Top 20 e Top 30 em peso igual, trimestral; Top 20 com raiz do valor de
mercado e teto de 10%; Top 30 com troca anual (média de 4). Comparações: Fórmula Mágica original, Top 20 da estratégia OoL, ETFs e os 9 obrigatórios, com janelas de 3, 5 e 10 anos.
**Resultado (2026-11-14, S&P 500 2011–2026, Top 20 raiz; janelas 3a/5a/10a > S&P):** Fórmula original 16,3% (63/50/61%); com G + EV/EBIT 16,6% (46/58/89%);
com G + P/L 18,3% (65/64/100%); com G + P/L e financeiras/utilities 18,9% (74/81/100%); **com G + EV/EBIT sem cíclicos e vestuário 19,7% (96/99/100%)**;
Top 20 OoL 20,5% (100/100/100%). Colocar o G melhora a Fórmula; tirar cíclicos e vestuário é o que mais ajuda (as listas sem o filtro trazem Delta, CF,
Deckers, Lululemon, Ralph Lauren). Nenhuma versão bate a Top 20 OoL no período todo. Obs.: classes duplas (GOOG/GOOGL) não foram unificadas nestas versões.

## 2026-11-14 — Pré-registro: ROIC + G + P/L sem cíclicos e vestuário (pedido do usuário)
(5) ROIC + G + P/L, sem financeiras e utilities, sem cíclicos e vestuário (produto testado); (6) igual, com financeiras (ROE) e utilities (sensibilidade).
Pensado depois de ver os resultados anteriores (risco de sobreajuste). Correção junto: classes duplas (GOOG/GOOGL etc.) contam uma vez só em todas as versões;
todas as versões anteriores são recalculadas com essa correção.
**Resultado (2026-11-14, com classes duplas unificadas):** (5) ROIC + G + P/L sem cíclicos e vestuário: Top 20 raiz 20,7% a.a. (janelas 3a/5a/10a 97/98/100%, pior queda −32,2%),
peso igual 20,6% (99/100/100%); Top 20 OoL 20,5% (100/100/100%, −34,4%). (6) com financeiras e utilities: 19,7%. 2019–2026: (5) 23,5% × Top 20 OoL 21,1%.
Empate técnico com a estratégia congelada usando só um ranking de três números — confirma que a vantagem vem de ROIC + crescimento + preço razoável + filtro de setores.
Pensado depois dos testes anteriores: não substitui a regra congelada sem decisão do usuário.

## 2026-11-14 — Ranking consolidado das estratégias (EUA, S&P 500, 2011–2026, ROIC triangulado)
Top 20 OoL 20,5% (janelas 3a/5a/10a 100/100/100%); OoL High ROIC 21,5% (95/100/100%); OoL High Growth 20,6% (92/100/100%); ROIC + G + P/L sem cíclicos 20,7%
(97/98/100%); N1 (todas com ROIC ≥ 12% e crescimento ≥ 15%, raiz) 18,9% (100/100/100%); N2 (ROIC > 30% e crescimento > 30%, ~9 ações) 24,5% raiz (86/88/100%,
pior queda −45%); OoL novo 18,2%; S&P 15,6%. Modelos nulos recalculados com o ROIC novo e classes duplas unificadas.

## 2026-11-14 — Relatório comparativo das 6 finalistas (EUA, 2011–2026)
`relatorio/calc.py` → `relatorio/dados.json` e `relatorio/finalistas.html` (publicado). Retorno a.a. / depois do IR / janelas 3a-5a-10a / pior queda / trades por ano:
Top 20 OoL 20,5% / 17,8% / 100-100-100% / −34% / 32; High ROIC 21,4% / 18,7% / 95-100-100% / −36% / 13; High Growth 20,7% / 18,1% / 92-100-100% / −34% / 15;
ROIC + G + P/L 20,7% / 17,8% / 97-98-100% / −32% / 37; Todas as de qualidade 18,9% / 17,1% / 100-100-100% / −33% / 39 (giro 41%); As excepcionais 24,6% / 22,3% /
86-88-100% / −45% / 6 (maior posição em média 43%; NVIDIA > 1/3 do ganho). Sobreposição média Top 20 × ROIC + G + P/L 53%; demais pares 16–40%.

## 2026-11-14 — Cenário "mundo sem NVIDIA" (pedido do usuário; análise de sensibilidade, não muda regra)
A NVIDIA sai do universo em todas as datas (as estratégias escolhem a próxima da fila). Referência: S&P 500 sem NVIDIA (S&P 500 ajustado pela diferença
entre um S&P sintético com peso por valor de mercado com e sem a NVIDIA). Os 9 comparativos obrigatórios também são refeitos sem a NVIDIA.
**Resultado (sem NVIDIA):** S&P 500 15,6% → 14,9%. Top 20 OoL 20,5% → 20,3% (vantagem sobre o índice 5,0 → 5,4 p.p.; janelas 100/100/100%); High ROIC 21,4% → 20,2%;
High Growth 20,7% → 19,8%; ROIC + G + P/L 20,7% → 19,8%; Todas as de qualidade 18,9% → 18,0%; As excepcionais 24,6% → 21,0% (vantagem 9,0 → 6,1 p.p.).

## 2026-11-15 — Pré-registro: duas variações das "excepcionais" e o teste fora do S&P 500 (pedido do usuário)
(7) **Excepcionais completadas até 20**: as que têm ROIC > 30% e crescimento > 30% entram primeiro; o resto das 20 vagas é preenchido pelas que chegam
mais perto dos dois cortes ao mesmo tempo (nota = menor entre ROIC ÷ 30% e crescimento ÷ 30%), entre as de qualidade (ROIC ≥ 12%, crescimento ≥ 15%,
sem cíclicos e vestuário). Raiz do valor de mercado com teto de 10%; trimestral.
(8) **Excepcionais sem nunca vender**: a cada trimestre, um aporte igual, dividido em partes iguais entre as excepcionais do momento; nada é vendido.
Medido pelo retorno ponderado no tempo (comparável às demais) e, para os aportes, pela TIR contra o mesmo esquema de aportes no S&P 500 e na Top 20 sem
vender. Imposto só na venda final (diferido).
**Teste fora do S&P 500** com as 8 estratégias: universo das médias e pequenas dos EUA (fora do S&P 500 na data, valor de mercado ≥ US$ 1 bi, preço ≥ US$ 5,
giro ≥ US$ 5 milhões/dia), com a definição anterior de ROIC (o triangulado ainda não existe para essa base) e classes novas sem zROIC. Referências:
Russell 2000 (IWM), S&P SmallCap 600 (IJR), S&P MidCap 400 (IJH), S&P 500 e o universo em peso igual; janelas de 3, 5 e 10 anos contra o IWM.
**Resultado (2026-11-15).** S&P 500 (2011–2026): excepcionais completadas até 20 22,8% a.a. (20,3% após IR; janelas 3a/5a/10a 99/100/100%; pior queda −40%; 21 meses
atrás; maior peso 10%); excepcionais sem nunca vender 24,7% (ponderado no tempo; pior queda −50%; TIR dos aportes 24,7% antes e 23,1% após o IR final; cada
real virou 8,2 contra 5,7 na Top 20 sem vender e 3,4 no S&P). Fora do S&P 500 (médias e pequenas, ROIC anterior; Russell 2000 9,8%, S&P 14,2%): High ROIC 20,2%
(99/100/100% contra o IWM), High Growth 20,0%, Todas as de qualidade 16,9% (99/100/100%), Top 20 16,5% (80/77/100%; 81 meses atrás), Excepcionais até 20 16,4%,
ROIC + G + P/L 16,3%, Excepcionais 15,5%, sem vender 13,2%. A High ROIC é a única entre as primeiras nas duas bases.

## 2026-11-15 — Pré-registro: ROIC triangulado nas médias e pequenas e combinação núcleo + satélite (pedido do usuário)
(1) Mesma definição do ROIC triangulado (com a regra de "arte" e a de outliers) aplicada às médias e pequenas (dados extras da SEC para as 1.868 empresas);
as 8 estratégias são refeitas nessa base contra o Russell 2000.
(2) Combinação Top 20 da OoL + OoL High ROIC, com rebalanceamento trimestral entre as duas pernas: 100/0, 70/30, 50/50, 30/70 e 0/100, no S&P 500 e nas
médias e pequenas (ambas com o ROIC triangulado). Mesmas métricas: retorno, depois do IR, janelas de 3/5/10 anos, pior queda, meses atrás do índice, trades.
**Resultado (2026-11-15).** (1) Médias e pequenas com ROIC triangulado (Russell 2000 9,8%): High ROIC 19,9% (99/100/100% contra o IWM; 20 meses atrás), High Growth 18,7%
(100/100/100%), Todas as de qualidade 16,8% (100/100/100%), ROIC + G + P/L 15,9%, Excepcionais até 20 15,0%, Top 20 14,7% (76/71/100%; 85 meses atrás), Excepcionais 13,9%,
sem vender 13,9%. (2) Combinação Top 20 + High ROIC — S&P 500: 100/0 20,5%, 70/30 20,9%, 50/50 21,0%, 30/70 21,2%, 0/100 21,4% (janelas 3a 100/100/100/99/95%);
médias e pequenas: 14,7%, 16,4%, 17,5%, 18,5%, 19,9% (janelas 3a 76/89/98/100/99%). A mais robusta nas duas bases: 30% Top 20 + 70% High ROIC.

## 2026-11-16 — Pré-registro: "ROIC alto descontado", setores de crescimento estável e PEG (pedido do usuário; antes de rodar qualquer carteira)
Contexto: a atribuição (relatorio/o_que_o_modelo_acerta.html) mostrou que o ROIC persiste, o crescimento passado não, e que o P/L fecha ~30% da distância ao
P/E justo em 3 anos. Hipótese do usuário: comprar ROIC alto descontado em relação ao P/E justo, de preferência onde o crescimento do EPS é previsível.
Todas: S&P 500 point-in-time, ROIC triangulado (financeiras e seguradoras de saúde: ROE), sem cíclicos e vestuário, trimestrais, top 20, raiz do valor de
mercado com teto de 10% (peso igual como controle), duplas classes deduplicadas. Desconto = log(P/E justo ÷ P/L), com P/E justo do modelo (ROIC limitado
a 100%, g pelo ranking do crescimento) e P/L > 0.
**Grupo** = subindústria GICS com ≥ 5 empresas no universo na data; senão, o setor GICS.
**Setor estável (ex-ante)**: em cada data, os grupos são ordenados pela mediana do |zGrowth| das suas empresas (zGrowth = desvio-padrão dos 5 crescimentos
anuais do EPS ÷ mediana, só dados até a data); estável = terço de grupos com a menor mediana. Robustez (secundária): terço com a maior correlação de ordem
entre o crescimento previsto há 3 anos e o realizado desde então (dado conhecido na data).
**Empresa estável (variante)**: |zGrowth| < 0,5 e crescimento (mediana de 5 anos) entre 5% e 30%.
Carteiras: (i) ROIC alto descontado: ROIC ≥ 12%, ordenado pelo desconto; (ii) = (i) só em setores estáveis; (iii) = (i) só em empresas estáveis;
(iv) Top 20 atual (qualidade, P/L ≥ 4, ordem pelo retorno esperado) só em setores estáveis; (v) contraste PEG: entre as de qualidade (ROIC ≥ 12%,
crescimento ≥ 15%), as 20 de menor P/L ÷ (crescimento × 100).
Comparação: Top 20, JG+G e os 9 comparativos obrigatórios, janelas de 3/5/10 anos, pior janela, pior queda, volatilidade; decomposição do retorno
(EPS, re-rating, dividendos) e cenário sem NVIDIA para a melhor. Status: exploratória (proposta depois de ver a atribuição).
**Resultado (2026-11-16).** S&P 500 15,6% a.a.; Top 20 20,5%; JG+G 20,7%. (i) ROIC alto descontado 20,4% (peso igual 19,9%; janelas 3a/5a/10a 99/100/100%;
pior queda −37%); (ii) só setores estáveis 16,8% (69/84/100%); (iii) só empresas estáveis 13,4% (48/53/66%; ~9 ações); robustez (setores previsíveis) 16,2%;
(iv) Top 20 só setores estáveis 18,8%; (v) PEG entre as de qualidade 21,4% (96/96/100%; sem NVIDIA 20,6%). Decomposição em 3 anos: a (i) teve EPS −3,9% a.a.
e re-rating +18,1% a.a. (desconto médio na compra 1,01 em log); as empresas estáveis tinham desconto de 0,14 e re-rating ~0 (previsibilidade já no preço).
Previsão do crescimento (3 anos): a mediana da própria empresa tem correlação de ordem −0,09 com o realizado; uma constante de 8% erra menos (10% contra 16%).
A régua de setor estável (|zGrowth|) não separou previsibilidade e a previsibilidade por grupo quase não persiste (correlação 0,13 entre 2012–18 e 2019–26).
Conclusão: confirmada a tese "ROIC alto descontado" (igual à Top 20, mais simples); rejeitada a de setores/empresas estáveis. Exploratória.


## 2026-11-18 — Pré-registro: universo dos gestores (13F do "Navegando US"), antes de rodar qualquer carteira
Hipótese do usuário: quem põe dinheiro de verdade sabe algo sobre o crescimento do lucro. As ações detidas por vários gestores ativos formariam um universo com
mais crescimento do EPS. Dentro dele, o re-rating via ROIC pegaria as que crescem e reprecificam.
**Dados**: 13F dos 148 gestores do artefato "Navegando US" (94 long-only, 54 hedge funds e ativistas; trimestres de 2016-03 a 2026-09; posições ≥ 0,2% da carteira).
**Contagem**: n_gest(ação, trimestre) = número de gestores com posição > 0. Para não olhar o futuro, a carteira montada no fim do trimestre t usa os 13F do
trimestre t−1 (arquivados até ~45 dias depois). Ligação com o nosso universo pelo ticker do cadastro do artefato; duplas classes somadas pela empresa.
**Período**: rebalanceamentos de 2016-06-30 a 2026-09-30; todas as carteiras e os comparativos são medidos nesse mesmo período (rebaseados).
**Premissa (teste 1)**: no S&P 500 point-in-time, comparar as ações com n_gest ≥ 3 e ≥ 5 com as demais: correlação de ordem por trimestre de n_gest
com o crescimento do EPS 1 e 3 anos à frente, com o re-rating e com o excesso sobre o S&P; diferença de medianas; decomposição EPS / re-rating / dividendos.
**Carteiras (teste 2)**, trimestrais, raiz do valor de mercado com teto de 10% (peso igual como controle), sem cíclicos e vestuário:
(i) ROIC alto descontado (ROIC ≥ 12%, top 20 pelo desconto ao P/E justo) só entre n_gest ≥ 3 e só entre n_gest ≥ 5;
(ii) Top 20 (regra congelada) só entre n_gest ≥ 3 e ≥ 5; (iii) controle: as 20 mais detidas (n_gest; desempate pelo valor de mercado), sem filtro de qualidade.
Comparação: Top 20 e ROIC alto descontado originais e os 9 comparativos, no mesmo período; janelas de 3/5/10 anos, pior janela, pior queda, volatilidade,
decomposição e cenário sem NVIDIA para a melhor. Ressalva registrada antes: a lista de gestores é a de hoje (viés de sobrevivência dos gestores).
Status: exploratória.

## 2026-11-18 — Pré-registro: crescimento pela receita e sem previsão de crescimento (ramo A do pedido do usuário; antes de rodar as carteiras)
Achados que motivam (relatorio/ramo_crescimento.py, S&P 500 PIT, sem cíclicos e vestuário, 3 anos): a mediana de 5 anos do EPS tem correlação de ordem −0,08 com
o crescimento futuro do EPS (R² 1,5%); o g normalizado do P/E justo, sendo transformação monotônica dela, tem a mesma ordem (−0,07; erro mediano 10,7% contra 15,2% da
mediana e 10,3% da constante de 8%); a mediana de 5 anos da RECEITA prevê a receita (ordem +0,31, R² 7,8%) e prevê o EPS com o sinal certo (+0,08; R² 1,3%).
Variantes (só o crescimento usado no P/E justo e no retorno esperado muda; ROIC, cortes, exclusões, pesos e datas iguais às registradas):
**V1a — receita no valuation:** crescimento previsto do EPS = a + b·(mediana de 5 anos do crescimento da receita), com a e b estimados só em 2011–2018 (regressão do
crescimento realizado do EPS em 3 anos, limitado a −50%..100%, sem cíclicos e vestuário) e aplicados a todas as datas; esse crescimento entra no ranking do g
(7%→3,5%; financeiras 6,5%→3%) e nos dois cenários do retorno esperado. O filtro de qualidade continua sendo o crescimento do EPS ≥ 15%.
**V1b — receita também no filtro:** como a V1a, e o filtro de crescimento passa a ser mediana de 5 anos da receita ≥ 10%.
**V2 — sem previsão de crescimento:** g igual para todas (5,25%; financeiras 4,75%) e crescimento de 8% para todas no retorno esperado; o P/E justo passa a depender só do ROIC.
Carteiras: Top 20 (qualidade, P/L ≥ 4, ordem pelo retorno esperado) e "ROIC alto descontado" (ROIC ≥ 12%, ordem pelo desconto ao P/E justo; na V1b com receita ≥ 10%),
cada uma na versão registrada e nas variantes V1a, V1b e V2; raiz do valor de mercado com teto de 10%; trimestrais. Comparação com os 9 comparativos, janelas de
3/5/10 anos, decomposição do retorno e cenário sem NVIDIA para a melhor. Status: exploratória (proposta depois de ver a previsibilidade).
**Resultado (2026-11-18).** Previsibilidade (sem cíclicos e vestuário, 3 anos): mediana do EPS → EPS: ordem −0,08, R² 1,5%; g normalizado: mesma ordem (−0,07),
erro mediano 10,7% (mediana 15,2%; constante de 8% 10,3%), viés +3,9 p.p.; receita → receita: ordem +0,31, R² 7,8% (receita futura = 3,6% + 0,35·passada);
receita → EPS: ordem +0,08, R² 1,3%; alavancagem no mesmo período: EPS = 7,2% + 0,70·receita (R² 8,6%, ordem 0,35). Tirar cíclicos e financeiras quase não muda a mediana do EPS.
Carteiras (S&P 15,6%): Top 20 registrada 20,5%, V1a 22,5% (janelas 3a 99%; sem NVIDIA 21.6%), V2 21,1%, V1b 18,6%;
ROIC alto descontado registrada 20,4%, V1a 16,7%, V2 17,1%, V1b 19,1%.
Conclusão: a receita no valuation ajudou a Top 20 e piorou a descontada; ganho não robusto (6 variantes). O filtro de crescimento do EPS ≥ 15% ajuda a carteira mesmo sem prever o lucro. Nada muda na regra. Exploratória.
**Resultado (2026-11-18).** Período 2016-06 a 2026-09 (S&P 500 15,3% a.a.). Premissa: o número de gestores tem correlação de ordem 0,05 com o crescimento do EPS em 1 ano
(t 4,0) e 0,08 em 3 anos (t 6,7; positiva em 100% dos trimestres); com o re-rating, −0,01 (zero). Decomposição em 3 anos: ≥ 5 gestores EPS 10,1% a.a., re-rating −1,0%;
< 3 gestores EPS 5,6%, re-rating +0,3%. Carteiras (raiz com teto; peso igual): ROIC alto descontado original 22,4% (21,1%); com ≥ 3 gestores 23,7% (22,5%); ≥ 5 gestores
23,2% (22,7%); Top 20 original 21,9% (21,2%); Top 20 ≥ 3 gestores 22,2%; ≥ 5 gestores 23,2% (22,3%); as 20 mais detidas 20,4% (EPS +19,7% a.a., re-rating −5,2%).
Diferença trimestral contra a original: +1,2 p.p. a.a. (t 1,4) para ≥ 3; +0,8 (t 0,5) para ≥ 5; Top 20 ≥ 5 +1,1 (t 1,3). Sobreposição com a original 88% (≥ 3) e 78% (≥ 5).
Sem NVIDIA: ≥ 3 gestores 23,6% contra 22,2% da original. Conclusão: os gestores preveem o lucro, não o re-rating; como filtro, ganho pequeno e não significativo. Exploratória.


## 2026-11-18 — Pré-registro: gestores como universo amplo (ramo C do pedido do usuário; antes de rodar)
Pedido: usar os gestores do "Navegando US" como o filtro ANTERIOR, num universo maior que o S&P 500, e por cima os nossos filtros e a seleção pelo desconto ao P/E justo.
Universo em cada data trimestral (2016-06 a 2026-09): ações detidas por ≥ N gestores no 13F do trimestre anterior (N = 1, 3, 5; posições ≥ 0,2% da carteira, como no
artefato), entre as que têm dado fundamentalista point-in-time: painel do S&P 500 (calc2.sp_data) + painel de médias e pequenas (calc2.ms_data; ROIC triangulado; em datas em
que a ação está nos dois, vale a linha do S&P). Piso de liquidez: valor de mercado ≥ US$ 2 bi na data. O g do P/E justo (7%→3,5%; financeiras 6,5%→3%), o P/E justo e o
retorno esperado são recalculados no universo combinado em cada data (mesma fórmula registrada; ROIC limitado a 100% no P/E justo).
Filtros iguais aos registrados: ROIC ≥ 12% (financeiras e seguradoras de saúde com ROE), sem cíclicos e vestuário, P/L > 0.
Carteiras: (i) "ROIC alto descontado": as 20 de maior log(P/E justo ÷ P/L) (desempate pelo ROIC); (ii) Top 20: além disso crescimento ≥ 15%, P/L ≥ 4, todas as métricas
da classe presentes, ordem pelo retorno esperado. Cada uma para N = 1, 3 e 5. Peso pela raiz do valor de mercado com teto de 10% (peso igual como controle); trimestral;
uma linha por empresa (classes duplas). Comparação: as mesmas regras só no S&P 500 (com e sem gestores, como no ramo B), os 9 comparativos e o IWM, no mesmo período;
janelas de 3/5/10 anos, pior janela, pior queda, volatilidade, decomposição EPS/re-rating/dividendos, % de ações fora do S&P, giro e cenário sem NVIDIA para a melhor.
Ressalvas registradas antes: lista de gestores de hoje (viés de sobrevivência dos gestores); o painel de médias e pequenas cobre empresas ≥ US$ 1 bi com dados da SEC.
Status: exploratória.

**Resultado (2026-11-18, ramo C).** Período 2016-06 a 2026-09 (S&P 500 15,3% a.a.; IWM 10,4%). Universo por trimestre (≥ US$ 2 bi, com dado): ≥ 1 gestor 942 ações (57% fora do
S&P), ≥ 3: 716 (47%), ≥ 5: 522 (36%). Cobertura: 63% do valor das posições dos gestores cai nos painéis; 10% sem ticker; 27% com ticker fora dos painéis (ADRs/estrangeiras,
ETFs; BRK-B e V não estão no painel do S&P — lacuna de dados que afeta todas as carteiras). Carteiras (raiz com teto; peso igual): Top 20 amplo ≥ 1: 21,8% (20,3%); ≥ 3: 24,6% (22,7%);
≥ 5: 25,2% (24,7%; janelas 3a 100%; pior queda −31%; 38% das ações fora do S&P; sem NVIDIA 24,5%); Top 20 S&P original 21,9%. Diferença trimestral da Top 20 amplo ≥ 5
contra a original: +3,1 p.p. a.a., t 2,56, melhor em 71% dos trimestres (com 6 variantes, o limite corrigido é t ≈ 2,6: no limite). ROIC alto descontado amplo ≥ 1/3/5:
24,0%/23,0%/24,5% contra 22,4% no S&P (t 0,6/0,2/0,9; sem padrão). Conclusão: o universo dos gestores ajuda a Top 20 (que filtra crescimento) e não o desconto puro.
Exploratória; a Top 20 ampla com ≥ 5 gestores é candidata a acompanhamento ao lado da regra antes de qualquer troca.


## 2026-11-18 — Pré-registro: Top 20 no universo dos gestores SEM viés de seleção (ramo D; antes de rodar)
Pedido do usuário: adotar a regra "Top 20 no universo dos gestores (≥ 5 gestores, ≥ US$ 2 bi)", mas antes refazer o teste sem o viés da lista de gestores de hoje
(o Navegando US só tem quem sobreviveu) e com dados de todas as empresas possíveis.
Gestores (point-in-time, todos os declarantes de 13F, inclusive os que fecharam): fonte SEC Form 13F Data Sets (formulários 13F-HR originais; o último por CIK e
período). Gestor ativo = 20 a 400 posições em ações (sem opções, sem dívida), as 10 maiores somando ≥ 25% da carteira 13F, e nome fora da lista de exclusão
(indexadores, bancos, corretoras, seguradoras, fundos de pensão e soberanos: Vanguard, BlackRock, State Street, Geode, Northern Trust, Fidelity Management Trust/FMR
como conglomerado, JPMorgan, Goldman, Morgan Stanley, Bank of America/Merrill, Wells Fargo, UBS, Credit Suisse, Deutsche Bank, Barclays, BNP, Citi, RBC, TD, BMO,
Nomura, Mizuho, MUFG, Norges, CPP, CalPERS e similares). A lista de exclusão pode ser ajustada olhando SÓ os nomes dos maiores declarantes, antes de qualquer retorno.
Em cada trimestre: as 250 maiores pelo valor da carteira 13F. Número de gestores por ação = quantos desses 250 a detêm com peso ≥ 0,2% (como no Navegando US).
Defasagem: carteira da data d usa o 13F do período anterior (arquivado até 45 dias depois; só arquivamentos com data ≤ d).
Mapeamento CUSIP → ticker: OpenFIGI (CUSIP de 9 dígitos) com reserva por nome (SEC company_tickers.json); cobertura reportada em valor.
Universo: ≥ 5 gestores (principal), ≥ 3 e ≥ 10 (sensibilidade); valor de mercado ≥ US$ 2 bi; ações com dado fundamentalista point-in-time (painéis do S&P 500 e de médias e
pequenas, mais as ações do universo que faltarem e tiverem companyfacts e preço, com o mesmo código: backtest.features, roic3.one, vp.classify).
Viés de sobrevivência do lado das ações: as ações do universo sem dado (deslistadas, sem preço) são contadas e o resultado é cercado pelo teste de limites já registrado
(pessimista: −100% no trimestre em que somem; neutro: retorno do universo; otimista: S&P 500), com peso esperado igual à taxa de seleção das elegíveis com dado.
Carteiras: Top 20 (regras registradas: ROIC ≥ 12%, crescimento ≥ 15%, P/L ≥ 4, sem cíclicos e vestuário, todas as métricas da classe, ordem pelo retorno esperado recalculado
no universo; raiz do valor de mercado com teto de 10%; peso igual como controle) e "ROIC alto descontado" (top 20 pelo log(P/E justo ÷ P/L)), para N = 3, 5 e 10.
Comparação: a versão do ramo C (lista de hoje), a Top 20 original, os 9 comparativos + IWM, janelas 3/5/10, pior queda, volatilidade, decomposição, sem NVIDIA, giro e
imposto de 15% sobre o ganho realizado. Critério para adotar: Top 20 ≥ 5 gestores sem viés acima da Top 20 original no mesmo período, em retorno e nas janelas de 3 anos.
Status: exploratória (proposta depois dos resultados do ramo C).

Adendo ao pré-registro do ramo D (2026-11-18, antes de rodar; pedido extra do usuário): variante de universo "Navegando US robustecido" = gestores da lista do
Navegando US (suas posições ≥ 0,2%, como no artefato) MAIS os 100 maiores gestores ativos de cada trimestre (mesma regra de gestor ativo, pelo valor 13F) que não
estão na lista (comparação por CIK). Contagem por emissor (CUSIP de 6 dígitos). Top 20 com ≥ 5 gestores (principal da variante) e ≥ 3 (sensibilidade), mesmas regras.
A lista dos 100 maiores ativos por trimestre vai para relatorio/top100_ativos_por_trimestre.csv. Contagem por emissor também no universo dos 250 (CUSIP de 6 dígitos).
Variante "Navegando US robustecido" CANCELADA pelo usuário antes de rodar (2026-11-18): fica só a regra dos 250 ativos. A lista top 100 por trimestre continua sendo salva.
Adendo (2026-11-18, antes de rodar): a variante "Navegando US robustecido" foi cancelada pelo usuário; fica só a regra principal (250 maiores ativos, ≥ 5; ≥ 3 e ≥ 10 como sensibilidade). Mantém-se só a lista dos 100 maiores ativos por trimestre (para atualizar o Navegando US).

**Resultado (2026-11-18, ramo D: gestores sem viés).** 2016-06 a 2026-09 (S&P 500 15,3% a.a.). 250 maiores gestores ativos de cada trimestre, de todos os 13F da SEC (em média 74 deles
estão na lista do Navegando US). Universo ≥ 5 gestores: 472 ações por trimestre com dado (28% fora do S&P); 72% do valor das posições tem dado; o resto é ADR (5%),
estrangeiras sem ADR/ETFs/fechadas (14%), deslistadas (4%) e sem ticker (5%). Visa e BRK-B incluídas com LPA aproximado. Carteiras (raiz com teto): Top 20 original 22,0%;
lista do Navegando ≥ 5 (com viés, refeita com contagem por emissor) 23,1%; 250 gestores ≥ 3 / ≥ 5 / ≥ 10: 22,8% / 21,8% / 22,2%
(diferença da ≥ 5 contra a original: -0.0 p.p. a.a., t -0.01); ROIC alto descontado ≥ 5 21,4% (original 22,4%);
OoL ≥ 5 (peso igual) 18,6% (original 17,8%; com a lista do Navegando 21,5%).
Limites (ações sem dado): 17.7% a 20.1%. Com imposto: 18.9% contra 19.1%.
Conclusão: o ganho do ramo C era viés de sobrevivência da lista de gestores. A regra NÃO passou no critério de adoção; fica a Top 20 original. Exploratória.

- 2026-11-22 — **V3 da planilha com consenso + haircut (decisão do usuário).** Regra de ACOMPANHAMENTO, NÃO testada (não há histórico do consenso); a regra testada continua a do backtest. Crescimento = EPS estimado do sell-side (Wisesheets "Estimated EPS AVG") com haircut (ano+1 ×0,95; ano+2 ×0,90; ano+3 ×0,85), CAGR de 3 anos sobre o último EPS publicado, teto de 40%; zGrowth 0,9; P/L = média do LTM e do 1 ano à frente; retorno = média de (P/E justo × EPS ano+2 com haircut ÷ preço)^(1/2) − 1 + dy e (G + dy); ROIC triangulado leve (4 anos, sem dívida de curto prazo, aplicações e investimentos de longo prazo); Top 20 com no máximo 6 ações por setor; universo = 563 ações da V2 do usuário; alerta "consenso ≫ histórico" (G − mediana histórica > 15 p.p. e G > 2×). Gerador: planilha/v3_consenso.py. Carteira-sombra na aba Histórico.

- 2026-11-22 — **Decisões do usuário (mudança de regra, registrada antes de qualquer novo teste):**
  1. Seguros multilinha e distribuidoras de saúde deixam de ser cíclicos (passam a NOT_CYCLICAL em backtest/ciclicos.py; na planilha, saem da lista de cíclicas). Ficam 13 subsetores cíclicos. Os backtests anteriores NÃO foram refeitos com a mudança.
  2. ROIC triangulado: a visão marginal deixa de ser usada sozinha quando as visões do ativo e do passivo existem mas são negativas (caso Bloom Energy: ativo e passivo negativos na média, marginal de 92% vindo de uma virada de prejuízo para lucro). Nesse caso o ROIC é a maior das duas visões (negativa), e a ação não passa no filtro de qualidade. O marginal só é usado sozinho quando não há dado de ativo nem de passivo. Aplicado na planilha V3; no Python (roic3.combine) fica pendente de aplicar e reprocessar.

- 2026-11-22 — **Resultado: backtest das 8 seleções com as regras de 22/11** (relatorio/backtest_8.py, oito_selecoes.html). roic3.combine aplicado e roic3.csv reprocessado
  (S&P; 2,4% das observações caem na regra nova; médias e pequenas NÃO reprocessadas). Crescimento histórico (a regra testável; a planilha usa consenso com haircut, não testável).
  Retorno anual 2011-09 a 2026-09 (S&P 15,6%): Excepcionais 24,6% (sem NVDA 21,0%; sem as 3 maiores 19,7%), Especiais 22,9% (19,4%), High ROIC 21,4% (18,9%),
  High Growth 20,7% (18,5%), Top 20 20,7% / com máx. 8 por setor 20,6% (18,6%), JG+G 20,4% (19,3%), OoL 18,0% (16,8%), GCGR 16,8% (16,0%).
  Janelas de 3 anos acima do S&P: Top 20 100% (pior janela +0,7 p.p.), Especiais 99%, High ROIC 95%, Excepcionais 86% (pior −9,4 p.p.; pior queda −45%; maior peso 43%).
  Efeito das duas mudanças: entre −0,3 e +0,1 p.p. por seleção (desprezível). O limite de 8 por setor quase não atua (−0,1 p.p.).

- 2026-11-22 — **Mais decisões do usuário (regra):** (3) petróleo integrado e midstream, ouro, prata e metais preciosos passam a ser cíclicos (`FORCE_CYCLICAL` em ciclicos.py; na planilha, indústrias do Wisesheets equivalentes); (4) FSLR excluída à mão (depende de subsídio; lista "Excluídas à mão" na aba Regras); (5) Top 20 da planilha: teto de PESO de 40% por setor (além do máximo de 8 ações por setor e do teto de 10% por ação): as melhores do setor ficam, com o peso reduzido proporcionalmente; o excesso vai para os outros setores. Backtests não refeitos com (3)–(5).

- 2026-11-22 — **Universo da planilha (decisão do usuário):** só ações negociadas e reportadas em dólar. Saem a América Latina inteira (NU, BAP, MELI, PBR, ITUB, FMX) e as empresas que reportam em outra moeda (o Wisesheets não converte: BAP aparecia com P/L 3,6 porque o EPS vinha em soles): TSM, NVO, ASML, SAP, RELX, UL, RTO, FER, RACE, BTI, IFNNY, RYAAY, SPOT, ONON, HDB, IBN, SKHY, KSPI, BABA, PDD, TCOM, NTES e as canadenses CNI, CP, CNQ, SU, ENB, TRP. Saem também ADRs com proporção diferente de 1 ação (DEO, SHEL, TTE) e a BRK-B (EPS por ação classe A). A guarda "P/L entre 0 e 2 = moeda diferente" continua para casos novos.

- 2026-11-22 — **Universo da planilha: voltam 18 empresas com conversão de moeda e de ADR** (decisão do usuário): TSM, ASML, NVO, SAP, RELX, UL, SPOT, RACE, RYAAY, ONON, IFNNY, BTI e as canadenses CNI, CP, CNQ, SU, ENB, TRP. Tabela na aba Regras com a moeda de reporte, ações por ADR e se a estimativa também precisa de conversão; câmbio puxado do Wisesheets (com valor de reserva). A conversão vale só onde lucro e preço se comparam (P/L, P/E justo, retorno); ROIC e crescimento são razões na mesma moeda e não mudam. China, Índia e América Latina continuam fora.

- 2026-11-22 — **Crescimento da planilha medido de 2026 a 2028** (decisão do usuário, caso UBS): o 1º ano do consenso costuma ser rebote de uma base deprimida (UBS: +44% em 2026, depois 13–15%). O crescimento da classe e o do valuation passam a ser a taxa anual entre o EPS estimado de 2026 e o de 2028 (reserva: 2026→2027, depois 2025→2028); o zGrowth usa só os crescimentos de 2027 e 2028. UBS: 23,5% → 14,4%, sai da OoL.

- 2026-11-22 — **Especiais e JG+G com os mesmos limites da Top 20** (decisão do usuário): no máximo 8 ações por setor e 40% do peso por setor (as melhores ficam, com peso reduzido), além do teto de 10% por ação. Sem o limite de 8 ações, o teto de 40% pode ficar impossível de cumprir junto com o de 10%.

- 2026-11-22 — **Crescimento = mediana dos 3 crescimentos anuais do consenso** (2025→26, 26→27, 27→28), substituindo o "2026 a 2028" do mesmo dia (decisão do usuário): um ano atípico, para cima ou para baixo (rebote de base deprimida ou tombo em 2026), não contamina a classe nem o g do P/E justo. Valuation usa as mesmas medianas com haircut. zGrowth = dispersão dos 2 crescimentos mais próximos da mediana. Alerta "Consenso com ano atípico" quando um dos três fica a mais de 30 p.p. da mediana. UBS: 15,3% (volta a OoL, raspando).

- 2026-11-22 — **Pré-registro (ramo J, antes de rodar): cenário bear e Especiais nova** (pedido do usuário). S&P 500 PIT, crescimento histórico (mediana 5a), ROIC triangulado com as regras de 22/11.
  Bear por ação e data: g_bear = MIN(g, MAX(percentil 70 do crescimento da mesma indústria GICS na data, 0,7·g, 6%)); múltiplo_bear = MIN(0,8·P/E justo, P/L);
  retorno_bear = (múltiplo_bear·EPS·(1+g_bear)²/preço)^(1/2) − 1 + dy. Sem P/E justo ou sem P/L (prejuízo) → bear indefinido → barrada.
  Filtro: retorno_bear > −10% para entrar na OoL (e por consequência High ROIC e High Growth), na Top 20 e na Especiais; Excepcionais (qualidade) também filtrada; GCGR e JG+G sem filtro.
  Especiais nova: qualidade + retorno esperado > 20% + bear > −10%; primeiro as com ROIC > 30% e crescimento > 30%, completa até 20 pela maior 1,5·ROIC + g; raiz do valor de mercado, teto 10% por ação, 40% e 8 ações por setor.
  Comparação antes/depois nas 8 seleções (definições de relatorio/backtest_8.py), 9 comparativos, janelas 3/5/10, perdedores evitados × vencedores perdidos (retorno de 1 ano das barradas), frequência de quedas ≤ −30% em 1 ano. Critério: o filtro vale se reduzir as quedas fortes sem baixar o retorno da Top 20 em mais de 0,5 p.p. ao ano.

- 2026-11-22 — **Planilha/painel (decisões do usuário):** (a) **cenário bear**: g_bear = MIN(g, MAX(p70 do crescimento da indústria, 0,7 × g, 6%)); múltiplo_bear = MIN(0,8 × P/E justo, P/L atual); retorno_bear em 2 anos como o retorno esperado. OoL, Top 20 e Especiais exigem retorno_bear > −10% (OoL que falha vira "OoL reprovada no bear"; o filtro de qualidade também cobre Excepcionais). (b) **Especiais**: retorno esperado > 20%; primeiro as com ROIC > 30% e crescimento > 30%, completando até 20 pela nota 1,5 × ROIC + g. Backtest no Python pré-registrado à parte (ramo J).
  **Resultado (ramo J, 2026-11-22):** Top 20 20,6% → 20,4% (filtro tira 0,1 ação/trimestre); posições com queda ≥ 30% em 1 ano 6,1% → 6,1%. OoL 18,0% → 17,8%; High Growth 20,7% → 20,0%;
  Excepcionais 24,6% → 23,6%; High ROIC 21,4% → 21,4%. Na OoL, as ações barradas renderam 19% no ano seguinte (mediana) contra 15% das mantidas; 12% das saídas caíram ≥ 30%,
  25% subiram ≥ 50% (ex.: NVDA 2020/2023, FSLR 2012). **Filtro bear: não passa no critério registrado** (não reduziu as quedas fortes). Especiais nova: 22,9% → 23,5%,
  Sharpe 1,10 → 1,15, janelas 3a 99% → 100%, pior janela −0,1 → +1,7 p.p.; retorno passa a vir metade de re-rating (antes quase todo de EPS). Status: exploratória.
  Relatório: relatorio/cenario_bear.html (https://claude.ai/artifact/L14AV98btdQSBJtdEdiubc).

- 2026-11-22 — **Pré-registro do ramo K (diagnóstico dos perdedores e novo bear), antes de olhar resultados.** Episódio = permanência contínua de uma ação numa carteira (Top 20 c/ limite por setor, Especiais nova, OoL, High ROIC, High Growth, Excepcionais, JG+G; S&P PIT 2011–2026, crescimento histórico). Retorno total do 1º trimestre em carteira ao 1º trimestre fora; TIR anualizada; **perdedor = TIR < −10% a.a.** Sinais candidatos, todos conhecidos na entrada: (1) bear atual ≤ −10%; (2) bear com piso de 50% do próprio crescimento ≤ −10%; (3) P/L > 1,5× P/E justo; (4) P/L acima do percentil 80 da indústria; (5) crescimento > 2× a mediana do setor; (6) ROIC do último ano < 80% da média dos dois anteriores; (7) EPS do último ano caiu; (8) retorno dos 12 meses anteriores > 80%; (9) zGrowth > 1,5. Base: episódios únicos (ação × data de entrada). Descoberta 2012–2018, confirmação 2019–2026. **Um sinal passa se, nos dois períodos:** lift (taxa de perdedores entre os marcados ÷ taxa geral) ≥ 1,5; TIR mediana dos marcados ≥ 10 p.p. abaixo dos não marcados; e a fração dos perdedores marcados ≥ 1,5× a fração dos grandes vencedores (TIR > 30%) marcados. Quem passar vira exclusão (como o bear) e é testado nas carteiras contra os comparativos e as janelas.
  **Resultado do ramo K (2026-11-22):** 1.389 episódios, 204 perdedores (15%; 134 únicos). Na entrada, perdedores × grandes vencedores: P/L 19,9 × 20,0; crescimento previsto 32% × 31%; ROIC 24% × 28%; retorno esperado 46% × 55%; bear 20% × 25%. Depois: P/L dos perdedores 19,9 → 19,5, dos vencedores 20,0 → 28,8; 52% dos perdedores tinham EPS 10%+ menor dois anos depois (vencedores 24%). Tipos: múltiplo comprimiu com lucro ok 32% (ações caras, P/L ~28), lucro caiu 28% (ações baratas, P/L ~16), queda curta de 1 trimestre 21%, mercado antecipou a queda do lucro 7%, prejuízo 6%, ROIC caiu 5%. Taxa de perdedores: High ROIC 9%, demais 14–17%. **Nenhum dos 9 sinais passou** (bear atual: lift 1,34 × 1,96; bear com piso de 50%: 0,95 × 2,26; P/L > 1,5× justo: 1,11 × 1,72). Nenhuma regra nova testada nas carteiras. Recomendação: bear só como informação, não como corte. Relatório: relatorio/perdedores.html.

- 2026-11-22 — **PRÉ-REGISTRO ramo L (bear v2 pela indústria; antes de rodar).** Indústria = GICS indústria na data; se < 5 ações, o setor. Sinais medidos nos episódios únicos (ação × entrada) do ramo K, descoberta 2012–2018, confirmação 2019–2026, mesmo critério do ramo K (lift ≥ 1,5; TIR mediana dos marcados ≥ 10 p.p. abaixo dos não marcados; recall dos perdedores ≥ 1,5× o dos grandes vencedores; nos DOIS períodos).
  (a) gap de crescimento = g − mediana da indústria > X, X ∈ {10, 20, 30 p.p.}; gap de múltiplo = P/L ÷ mediana do P/L da indústria > Y, Y ∈ {1,5; 2; 3}; combinado (gap g > X E gap P/L > Y). O X/Y é escolhido pelo maior lift na DESCOBERTA e só esse é conferido na confirmação.
  (b) bear v2 (mediana): g_bear = MIN(g, MAX(mediana da indústria, 6%)); P/E justo_bear = (1 − g_bear/MIN(ROIC,1))/(8,5% − g_bear); múltiplo_bear = MIN(P/L, MAX(mediana do P/L da indústria, P/E justo_bear)); retorno_bear = (múltiplo_bear/P/L·(1+g_bear)²)^½ − 1 + dy; corte ∈ {−10%, 0%} escolhido na descoberta.
  (c) igual a (b) com o percentil 70 da indústria no lugar da mediana (crescimento e P/L).
  Se algum passar: teste nas 8 seleções contra a versão atual e o bear antigo (retorno, IR, pior queda, janelas, quedas ≥ 30%, sem as 3 maiores, sem NVIDIA). À parte, REGRA DE VENDA: vende a posição quando o EPS do último exercício < 80% de EPS_entrada × (1 + g_entrada)^(anos desde a entrada); não volta enquanto continuar selecionada sem interrupção. Critério para adotar qualquer regra: retorno ≥ ao atual E menos quedas ≥ 30% em pelo menos 5 das 8 seleções.
- 2026-11-22 — **RESULTADO ramo L (bear v2 pela indústria): nada passou.** Reclassificação: das 134 perdas únicas, só 8 eram "crescimento muito acima da indústria (> 15 p.p.), P/L > 1,3× a indústria e crescimento não entregue" (SMCI 2024, CMG 2024); 60 eram crescimento não entregue com preço normal; 37 quedas curtas; 29 outras. Perdedores e grandes vencedores tinham o mesmo gap de crescimento vs indústria (~18 p.p.) e ~88–90% de ambos entregaram 10 p.p.+ abaixo da mediana prevista (volta à média); P/L ÷ indústria: perdedores 0,84×, vencedores 0,98×. Sinais (parâmetro escolhido em 2012–18): gap g > 30 p.p. lift 1,28/1,07; P/L > 1,5× indústria 1,27/1,40; gap g > 30 p.p. E P/L > 3× 1,11/2,45 (marca 1–2%); bear v2 mediana ≤ −10% 1,28/1,49; bear v2 p70 ≤ 0% 1,11/1,56 — nenhum ≥ 1,5 nos dois períodos. Regra de venda (EPS < 80% da trajetória): Top 20 20,6% → 18,9%, Excepcionais 24,6% → 20,5%, quedas ≥ 30% iguais ou maiores; passa no critério em 1 de 8 seleções (só GCGR); bear antigo também 1 de 8. Decisão recomendada: bear (antigo ou v2) só como informação, sem corte; sem regra de venda.

- 2026-11-22 — **PRÉ-REGISTRO ramo M (robustez; antes de rodar).** S&P 500 point-in-time, crescimento histórico, ROIC triangulado, regras de 22/11 (Especiais nova, limites por setor).
  R1. Piso de valor de mercado para Top 20 e Especiais: US$ 20 bi e US$ 50 bi (variantes).
  R2. Consistência histórica como filtro na Top 20 e na Especiais: ≥ 4 dos 5 crescimentos anuais do EPS positivos e zGrowth ≤ 1,0.
  R3. Carteira "Compounders redondos": valor de mercado ≥ US$ 50 bi, ROIC ≥ 20%, crescimento mediano entre 8% e 35%, ≥ 4 de 5 anos positivos,
      zGrowth ≤ 1,0, sem cíclicas/vestuário, P/L ≤ 1,3 × P/E justo; até 25 ações pelo retorno esperado; raiz do valor de mercado, tetos 10%/40%.
  R4. "Quase lá → entra": os mesmos compounders (sem o limite de P/L), só quando o retorno esperado ≥ 20% (mínimo 5 ações; abaixo disso, o resto em S&P 500).
  R5. Indústrias perigosas: % de posições com queda ≥ 30% em 1 ano por indústria (carteiras do Painel). Exclusão recomendada só se ≥ 1,5× a média nos dois
      períodos (2012–18 e 2019–26) e com ≥ 30 posições; mostrar o custo de excluir.
  Critério de adoção para R1/R2: retorno ≥ versão atual − 0,5 p.p. ao ano E (pior queda menor OU quedas fortes menores) E janelas de 3 anos ≥ atuais − 5 p.p.
  R3/R4 são carteiras novas: reportar com os 9 comparativos e janelas; adoção só como lista de acompanhamento.
- 2026-11-22 — **PRÉ-REGISTRO ramo M, parte 2 (antes de rodar; pedido do usuário: escadinha, pequenas que compõem, ótima em pânico).**
  Nota de escadinha (backtest, 5 crescimentos anuais do EPS): 40 × % de anos com alta + 20 × maior sequência ÷ 5 + 20 × (nenhum ano abaixo de −10%)
  + 20 × max(0, 1 − min(1, desvio/mediana ÷ 1,5)); zero se a mediana ≤ 0.
  E1. Top 20 e Especiais só com escadinha ≥ 60 (filtro). E2. "Pequenas que compõem": valor de mercado US$ 2–30 bi, ROIC ≥ 20%, escadinha ≥ 70,
  crescimento ≥ 12%, P/L ≤ 1,3 × P/E justo; até 20 pelo retorno esperado; tetos 10%/40%. E3. "Ótima em pânico": ROIC ≥ 15%, escadinha ≥ 60, sem
  cíclicas/vestuário, ação caiu ≥ 25% em 12 meses, EPS do último ano subiu; peso igual, máx. 20 (as que mais caíram); trimestral.
  Critérios: E1 como R1/R2; E2 e E3 como carteiras novas (reportar com comparativos e janelas; adoção só como lista de acompanhamento).
- 2026-11-22 — **PRÉ-REGISTRO ramo M, parte 3: "Nota de boa empresa" (framework v4.2 do usuário; antes de rodar).** Nota = média de critérios de 1 a 5.
  No backtest (só com o que existe no painel histórico): C1 ROIC vs pares = 1 + 4 × percentil do spread (ROIC − mediana da indústria) no universo da data,
  limitado a 3 se ROIC < custo de capital + 10 p.p. (18,5%) ou < 1,5 × a mediana da indústria; C2 ROIC incremental (marginal): 5 se ≥ 0,8 × ROIC e ≥ 8,5%,
  4 se ≥ 0,5 × ROIC, 3 se ≥ 8,5% ou sem dado, 2 se ≥ 0, 1 se < 0; C3 pista = min(crescimento, 15%) − g implícito, g implícito = (8,5% × P/L − 1) ÷ (P/L − 1/min(ROIC,1)):
  5 se ≥ +5 p.p., 4 se ≥ +2, 3 se ≥ 0, 2 se ≥ −3, senão 1 (5 se o P/L < 1/ROIC); C4 moat (ROIC anual ry1–ry6): 5 se todos ≥ 20% e mínimo ≥ 0,7 × média,
  4 se todos ≥ 15%, 3 se todos ≥ 8,5%, 2 se a maioria ≥ 8,5%, senão 1; C6 existir em 15 anos = 1 + (escadinha ≥ 70) + (valor ≥ US$ 10 bi) + (não cíclica) + (5 anos sem queda do EPS abaixo de −25%).
  (C5 gestão por ação não tem histórico no painel do backtest: fica só na planilha.) Testes nas carteiras Top 20, Especiais e Excepcionais:
  N1 filtro nota ≥ 3,5; N2 ordem: retorno esperado + 5 p.p. × (nota − 3); N3 peso: raiz do valor de mercado × nota (com os mesmos tetos).
  Critério: escolher a forma que mantém o retorno (≥ atual − 0,5 p.p.) e as janelas de 3 anos (≥ atuais − 5 p.p.); reportar o trade-off de todas.
