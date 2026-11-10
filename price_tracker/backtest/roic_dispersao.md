# Nova medida de volatilidade do ROIC: variação absoluta média ÷ ROIC médio (EUA, point-in-time)

> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10); financeiras e seguradoras de saúde usam ROE. A medida herda qualquer erro do ROIC; empresas com patrimônio negativo ou ROIC > 100% (ainda em aberto) podem distorcer.

**Fórmula:** nos 6 últimos exercícios, calcula-se |ROIC do ano − ROIC do ano anterior| para cada um dos 5 pares; a média dessas 5 variações é dividida pela média do ROIC dos 6 anos. **> 30% = ROIC volátil**; ≤ 30% = estável. Média do ROIC ≤ 0 conta como volátil. Exige ao menos 3 variações válidas.

*Exemplo:* ROIC de 20%, 25%, 18%, 22%, 30%, 26% → variações 5, 7, 4, 8, 4 (média 5,6 p.p.) ÷ média 23,5% = 24% → estável.

Base: 523 empresas que foram do S&P 500 em algum trimestre entre 2011 e 2026, 20707 observações (empresa × trimestre). Classificação da empresa = mediana da medida ao longo dos trimestres.

## 1. Os setores cíclicos que definimos ficam acima de 30%?

| Grupo | Empresas | **% empresas voláteis** | Dispersão mediana | % das observações voláteis |
|---|---|---|---|---|
| Energia | 18 | **89%** | 58% | 81% |
| Materiais | 26 | **54%** | 37% | 51% |
| Vestuário | 9 | **44%** | 29% | 45% |
| Cíclicos duros | 42 | **52%** | 30% | 49% |
| Demais | 428 | **47%** | 28% | 44% |
| *Todas* | 523 | 49% | 29% | 46% |

### Cada subsetor da nossa lista de cíclicos

| Subsetor | Grupo | Empresas | % voláteis | Dispersão mediana |
|---|---|---|---|---|
| Agricultural & Farm Machinery | Cíclicos duros | 1 | 100% | 30% |
| Air Freight & Logistics | Cíclicos duros | 4 | 25% | 21% |
| Automotive Parts & Equipment | Cíclicos duros | 3 | 67% | 35% |
| Building Products | Cíclicos duros | 8 | 25% | 18% |
| Cargo Ground Transportation | Cíclicos duros | 2 | 0% | 17% |
| Casinos & Gaming | Cíclicos duros | 3 | 100% | 86% |
| Construction & Engineering | Cíclicos duros | 5 | 60% | 31% |
| Construction Machinery & Heavy Transportation Equipment | Cíclicos duros | 3 | 33% | 25% |
| Home Furnishings | Cíclicos duros | 1 | 0% | 25% |
| Homebuilding | Cíclicos duros | 1 | 0% | 21% |
| Household Appliances | Cíclicos duros | 1 | 100% | 39% |
| Industrial Machinery | Cíclicos duros | 1 | 0% | 17% |
| Motorcycle Manufacturers | Cíclicos duros | 1 | 100% | 30% |
| Passenger Airlines | Cíclicos duros | 4 | 100% | 69% |
| Timber REITs | Cíclicos duros | 1 | 100% | 63% |
| Trading Companies & Distributors | Cíclicos duros | 3 | 67% | 33% |
| Oil & Gas Drilling | Energia | 1 | 100% | 32% |
| Oil & Gas Equipment & Services | Energia | 4 | 100% | 48% |
| Oil & Gas Exploration & Production | Energia | 7 | 86% | 212% |
| Oil & Gas Refining & Marketing | Energia | 2 | 100% | 56% |
| Oil & Gas Storage & Transportation | Energia | 4 | 75% | 48% |
| Construction Materials | Materiais | 4 | 25% | 23% |
| Copper | Materiais | 1 | 100% | 691% |
| Diversified Chemicals | Materiais | 2 | 100% | 48% |
| Fertilizers & Agricultural Chemicals | Materiais | 3 | 100% | 58% |
| Industrial Gases | Materiais | 2 | 50% | 28% |
| Metal, Glass & Plastic Containers | Materiais | 1 | 0% | 18% |
| Paper & Plastic Packaging Products & Materials | Materiais | 4 | 50% | 34% |
| Specialty Chemicals | Materiais | 6 | 17% | 18% |
| Steel | Materiais | 3 | 100% | 67% |
| Apparel, Accessories & Luxury Goods | Vestuário | 8 | 50% | 30% |
| Footwear | Vestuário | 1 | 0% | 26% |

## 2. Microsetores (subsetores GICS) por volatilidade do ROIC

Subsetores com 3 ou mais empresas. Marcados com ✔ os que já estão nas nossas listas (Energia, Materiais, vestuário, cíclicos duros).

### Comunicação — 67% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Movies & Entertainment | 4 | 100% | 85% | **novo candidato** |
| Interactive Media & Services | 5 | 40% | 21% |  |

### Consumo discricionário — 48% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Automobile Manufacturers | 3 | 100% | 90% | **novo candidato** |
| Casinos & Gaming | 3 | 100% | 86% | ✔ |
| Hotels, Resorts & Cruise Lines | 7 | 71% | 58% | **novo candidato** |
| Automotive Parts & Equipment | 3 | 67% | 35% | ✔ |
| Broadline Retail | 3 | 67% | 63% | **novo candidato** |
| Apparel, Accessories & Luxury Goods | 8 | 50% | 30% | ✔ |
| Restaurants | 6 | 33% | 24% |  |
| Automotive Retail | 5 | 20% | 14% |  |
| Apparel Retail | 4 | 0% | 13% |  |
| Other Specialty Retail | 3 | 0% | 15% |  |

### Financeiro — 55% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Multi-line Insurance | 3 | 100% | 83% | **novo candidato** |
| Consumer Finance | 4 | 100% | 42% | **novo candidato** |
| Financial Exchanges & Data | 9 | 78% | 38% | **novo candidato** |
| Property & Casualty Insurance | 8 | 75% | 35% | **novo candidato** |
| Life & Health Insurance | 5 | 60% | 33% | **novo candidato** |
| Regional Banks | 7 | 57% | 32% | **novo candidato** |
| Investment Banking & Brokerage | 6 | 50% | 29% | **novo candidato** |
| Diversified Banks | 7 | 43% | 25% |  |
| Transaction & Payment Processing Services | 9 | 33% | 20% |  |
| Asset Management & Custody Banks | 11 | 27% | 24% |  |
| Insurance Brokers | 5 | 20% | 13% |  |

### Energia — 89% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Oil & Gas Equipment & Services | 4 | 100% | 48% | ✔ |
| Oil & Gas Exploration & Production | 7 | 86% | 212% | ✔ |
| Oil & Gas Storage & Transportation | 4 | 75% | 48% | ✔ |

### Materiais — 54% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Fertilizers & Agricultural Chemicals | 3 | 100% | 58% | ✔ |
| Steel | 3 | 100% | 67% | ✔ |
| Paper & Plastic Packaging Products & Materials | 4 | 50% | 34% | ✔ |
| Construction Materials | 4 | 25% | 23% | ✔ |
| Specialty Chemicals | 6 | 17% | 18% | ✔ |

### Indústria — 31% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Passenger Airlines | 4 | 100% | 69% | ✔ |
| Trading Companies & Distributors | 3 | 67% | 33% | ✔ |
| Construction & Engineering | 5 | 60% | 31% | ✔ |
| Aerospace & Defense | 11 | 36% | 26% |  |
| Construction Machinery & Heavy Transportation Equipment | 3 | 33% | 25% | ✔ |
| Electrical Components & Equipment | 4 | 25% | 10% |  |
| Building Products | 8 | 25% | 18% | ✔ |
| Air Freight & Logistics | 4 | 25% | 21% | ✔ |
| Industrial Machinery & Supplies & Components | 14 | 21% | 19% |  |
| Rail Transportation | 3 | 0% | 15% |  |
| Environmental & Facilities Services | 4 | 0% | 11% |  |
| Diversified Support Services | 3 | 0% | 14% |  |

### Tecnologia — 65% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Technology Hardware, Storage & Peripherals | 9 | 89% | 53% | **novo candidato** |
| Systems Software | 6 | 83% | 128% | **novo candidato** |
| Semiconductors | 15 | 80% | 43% | **novo candidato** |
| Semiconductor Materials & Equipment | 4 | 75% | 39% | **novo candidato** |
| Communications Equipment | 6 | 67% | 43% | **novo candidato** |
| Electronic Components | 3 | 67% | 52% | **novo candidato** |
| Application Software | 16 | 56% | 32% | **novo candidato** |
| Electronic Manufacturing Services | 4 | 50% | 34% | **novo candidato** |
| Electronic Equipment & Instruments | 4 | 50% | 29% | **novo candidato** |
| Internet Services & Infrastructure | 3 | 33% | 29% |  |
| IT Consulting & Other Services | 4 | 25% | 20% |  |

### Saúde — 46% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Health Care Distributors | 4 | 75% | 63% | **novo candidato** |
| Biotechnology | 8 | 75% | 54% | **novo candidato** |
| Health Care Supplies | 3 | 67% | 31% | **novo candidato** |
| Health Care Equipment | 16 | 44% | 28% |  |
| Life Sciences Tools & Services | 9 | 33% | 24% |  |
| Managed Health Care | 4 | 25% | 18% |  |
| Health Care Services | 5 | 20% | 26% |  |

### Utilidades públicas — 31% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Electric Utilities | 15 | 33% | 24% |  |
| Multi-Utilities | 11 | 27% | 13% |  |

### Imobiliário — 33% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Retail REITs | 3 | 33% | 20% |  |
| Multi-Family Residential REITs | 3 | 33% | 22% |  |
| Telecom Tower REITs | 3 | 0% | 22% |  |

### Consumo básico — 7% das empresas voláteis

| Subsetor | Empresas | % voláteis | Dispersão mediana | Já na lista |
|---|---|---|---|---|
| Packaged Foods & Meats | 9 | 22% | 25% |  |
| Household Products | 3 | 0% | 15% |  |
| Consumer Staples Merchandise Retail | 5 | 0% | 18% |  |
| Soft Drinks & Non-alcoholic Beverages | 3 | 0% | 25% |  |

### Candidatos novos: subsetores fora das nossas listas com ≥ 50% das empresas voláteis

| Subsetor | Macrossetor | Empresas | % voláteis | Dispersão mediana | Empresas voláteis (mais voláteis primeiro) |
|---|---|---|---|---|---|
| Movies & Entertainment | Comunicação | 4 | 100% | 85% | LYV, TKO, NFLX, DIS |
| Automobile Manufacturers | Consumo discricionário | 3 | 100% | 90% | F, TSLA, GM |
| Consumer Finance | Financeiro | 4 | 100% | 42% | SLM, COF, SYF, AXP |
| Multi-line Insurance | Financeiro | 3 | 100% | 83% | AIG, L, AIZ |
| Technology Hardware, Storage & Peripherals | Tecnologia | 9 | 89% | 53% | SNDK, HPE, HPQ, WDC, STX, AAPL, NTAP, SMCI |
| Systems Software | Tecnologia | 6 | 83% | 128% | CRWD, PANW, NOW, GEN, FTNT |
| Semiconductors | Tecnologia | 15 | 80% | 43% | MRVL, AMD, MU, FSLR, AVGO, NXPI, ON, NVDA |
| Financial Exchanges & Data | Financeiro | 9 | 78% | 38% | COIN, SPGI, MSCI, ICE, MCO, CME, CBOE |
| Semiconductor Materials & Equipment | Tecnologia | 4 | 75% | 39% | KLAC, TER, AMAT |
| Health Care Distributors | Saúde | 4 | 75% | 63% | COR, MCK, CAH |
| Property & Casualty Insurance | Financeiro | 8 | 75% | 35% | HIG, ALL, CINF, ACGL, CB, PGR |
| Biotechnology | Saúde | 8 | 75% | 54% | VRTX, INCY, MRNA, REGN, GILD, ABBV |
| Hotels, Resorts & Cruise Lines | Consumo discricionário | 7 | 71% | 58% | NCLH, EXPE, HLT, MAR, RCL |
| Electronic Components | Tecnologia | 3 | 67% | 52% | COHR, GLW |
| Broadline Retail | Consumo discricionário | 3 | 67% | 63% | ETSY, AMZN |
| Health Care Supplies | Saúde | 3 | 67% | 31% | COO, ALGN |
| Communications Equipment | Tecnologia | 6 | 67% | 43% | LITE, MSI, CIEN, ANET |
| Life & Health Insurance | Financeiro | 5 | 60% | 33% | PRU, MET, GL |
| Regional Banks | Financeiro | 7 | 57% | 32% | KEY, ZION, RF, CFG |
| Application Software | Tecnologia | 16 | 56% | 32% | DDOG, WDAY, CRM, ADSK, TDC, PTC, TTD, INTU |
| Investment Banking & Brokerage | Financeiro | 6 | 50% | 29% | HOOD, GS, SCHW |
| Electronic Manufacturing Services | Tecnologia | 4 | 50% | 34% | TEL, JBL |
| Electronic Equipment & Instruments | Tecnologia | 4 | 50% | 29% | KEYS, ZBRA |

**Na nossa lista, mas com ROIC estável (< 30% das empresas voláteis):** Air Freight & Logistics (25%), Building Products (25%), Construction Materials (25%), Specialty Chemicals (17%)

## 3. Nova medida × zROIC (desvio-padrão ÷ ROIC do modelo, corte 0,7)

Correlação de postos entre as duas: +0,75.

| | zROIC < 0,7 (estável) | zROIC ≥ 0,7 (volátil) |
|---|---|---|
| **Nova ≤ 30% (estável)** | 54% | 0% |
| **Nova > 30% (volátil)** | 31% | 16% |

A nova medida é bem mais rígida: o zROIC usa o desvio-padrão em torno da média, que um ROIC alto dilui; a nova soma cada salto de um ano para o outro.

## 4. Carteiras: a nova medida como critério de estabilidade

As 8 linhas obrigatórias e, abaixo, as versões novas exigindo ROIC estável pela nova medida (≤ 30%). "Novo" = esboço (ROIC 12%), sem zROIC, sem Energia, Materiais e vestuário.

| Carteira | Retorno total | Retorno anual | Volatilidade | Pior queda | Ações (média) | Janelas 5a > S&P | Janelas 10a > S&P |
|---|---|---|---|---|---|---|---|
| S&P 500 | 775,2% | 15,6% | 16,7% | -33,7% | — | — | — |
| S&P 500 equal weight | 544,3% | 13,2% | 17,3% | -39,0% | — | 8% | 0% |
| OoL antigo | 728,3% | 15,1% | 20,0% | -35,9% | 27 | 37% | 15% |
| GCGR antigo | 713,0% | 15,0% | 17,8% | -37,2% | 34 | 46% | 27% |
| **OoL novo** | 960,6% | **17,0%** | 18,7% | -35,0% | 42 | 51% | 34% |
| **GCGR novo** | 838,4% | **16,1%** | 18,2% | -34,4% | 24 | 56% | 34% |
| OoL High ROIC (novo) | 1203,0% | 18,7% | 20,4% | -33,6% | 17 | 65% | 34% |
| OoL High Growth (novo) | 1314,6% | 19,3% | 21,5% | -34,6% | 16 | 59% | 34% |
| OoL novo + estabilidade nova (≤ 30%) | 1013,4% | 17,4% | 18,6% | -38,1% | 29 | 48% | 34% |
| GCGR novo + estabilidade nova (≤ 30%) | 785,6% | 15,7% | 18,1% | -32,3% | 26 | 57% | 34% |
| OoL High ROIC + estabilidade nova | 1127,4% | 18,2% | 20,3% | -36,0% | 11 | 54% | 33% |
| OoL High Growth + estabilidade nova | 1280,3% | 19,1% | 22,0% | -39,1% | 7 | 36% | 32% |

### Posições da OoL e GCGR novas: ROIC volátil × estável pela nova medida

| Classe | Grupo | Posições | Excesso médio a.a. | Excesso mediano a.a. | % acima do universo |
|---|---|---|---|---|---|
| OoL novo | Estável (≤ 30%) | 1693 | +3,4% | +1,3% | 51% |
| OoL novo | Volátil (> 30%) | 758 | +4,5% | +2,3% | 51% |
| GCGR novo | Estável (≤ 30%) | 734 | -0,1% | -2,5% | 47% |
| GCGR novo | Volátil (> 30%) | 658 | +4,7% | +1,5% | 51% |