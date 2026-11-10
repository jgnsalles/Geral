# Volatilidade do ROIC com todo o histórico disponível (EUA)

> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10); financeiras e seguradoras de saúde usam ROE. Empresas com patrimônio negativo ou capital muito pequeno (ROIC > 100%, ainda em aberto) podem aparecer como voláteis por artefato do denominador.

**Medida:** média de |ROIC do ano − ROIC do ano anterior| em **todo o histórico disponível** ÷ ROIC médio do mesmo período. **> 30% = volátil.** Média ≤ 0 = volátil. Também mostro a versão **só com as quedas** (média das quedas ÷ ROIC médio; subidas contam zero), que separa ciclo de crescimento.

Base: 537 empresas que foram do S&P 500 em algum momento desde 2011 e têm ≥ 8 anos seguidos de ROIC na SEC (mediana de 18 anos, em geral 2008–2025).

## 1. Os grupos cíclicos que definimos

| Grupo | Empresas | **% voláteis (histórico completo)** | Dispersão mediana | % voláteis só nas quedas | Dispersão mediana só nas quedas |
|---|---|---|---|---|---|
| Energia | 16 | **81%** | 83% | 75% | 45% |
| Materiais | 26 | **65%** | 45% | 46% | 25% |
| Vestuário | 9 | **89%** | 40% | 44% | 21% |
| Cíclicos duros | 40 | **60%** | 34% | 25% | 17% |
| Demais | 446 | **59%** | 36% | 32% | 19% |
| *Todas* | 537 | 60% | 38% | 33% | 20% |

### Subsetores das nossas listas

| Subsetor | Grupo | Empresas | % voláteis | Dispersão mediana | Só quedas: mediana | Empresas (dispersão) |
|---|---|---|---|---|---|---|
| Agricultural & Farm Machinery | Cíclicos duros | 1 | 100% | 41% | 15% | DE 41% |
| Air Freight & Logistics | Cíclicos duros | 4 | 25% | 24% | 13% | FDX 33%, UPS 29%, CHRW 18%, EXPD 13% |
| Automotive Parts & Equipment | Cíclicos duros | 2 | 50% | 31% | 17% | BWA 34%, APTV 28% |
| Building Products | Cíclicos duros | 8 | 38% | 26% | 13% | JCI 258%, TT 48%, CARR 38%, FBIN 27%, LII 25%, MAS 23%, AOS 21%, ALLE 18% |
| Cargo Ground Transportation | Cíclicos duros | 2 | 0% | 24% | 15% | JBHT 29%, ODFL 20% |
| Casinos & Gaming | Cíclicos duros | 3 | 100% | 69% | 42% | MGM 141%, WYNN 69%, LVS 55% |
| Construction & Engineering | Cíclicos duros | 5 | 60% | 34% | 13% | FLR 268%, FIX 46%, EME 34%, PWR 20%, J 17% |
| Construction Machinery & Heavy Transportation Equipment | Cíclicos duros | 3 | 67% | 31% | 17% | CAT 39%, CMI 31%, WAB 25% |
| Home Furnishings | Cíclicos duros | 1 | 100% | 96% | 27% | MHK 96% |
| Homebuilding | Cíclicos duros | 1 | 100% | 81% | 13% | LEN 81% |
| Household Appliances | Cíclicos duros | 1 | 100% | 81% | 43% | WHR 81% |
| Industrial Machinery | Cíclicos duros | 1 | 0% | 22% | 16% | FLS 22% |
| Motorcycle Manufacturers | Cíclicos duros | 1 | 100% | 42% | 25% | HOG 42% |
| Passenger Airlines | Cíclicos duros | 4 | 100% | 108% | 53% | ALK 179%, UAL 112%, DAL 104%, LUV 103% |
| Timber REITs | Cíclicos duros | 1 | 100% | 90% | 43% | WY 90% |
| Trading Companies & Distributors | Cíclicos duros | 2 | 50% | 19% | 10% | URI 30%, FAST 8% |
| Oil & Gas Drilling | Energia | 1 | 100% | 79% | 50% | HP 79% |
| Oil & Gas Equipment & Services | Energia | 4 | 75% | 169% | 99% | BKR ∞, NOV 237%, HAL 100%, SLB 28% |
| Oil & Gas Exploration & Production | Energia | 5 | 80% | 148% | 91% | EXE ∞, FANG 277%, EQT 148%, EOG 92%, TPL 21% |
| Oil & Gas Refining & Marketing | Energia | 2 | 100% | 76% | 36% | MPC 87%, VLO 64% |
| Oil & Gas Storage & Transportation | Energia | 4 | 75% | 40% | 24% | TRGP 68%, WMB 48%, KMI 32%, OKE 26% |
| Construction Materials | Materiais | 6 | 50% | 32% | 20% | BLDR 66%, JHX 49%, MLM 35%, VMC 29%, EXP 19%, CRH 18% |
| Copper | Materiais | 1 | 100% | 385% | 199% | FCX 385% |
| Diversified Chemicals | Materiais | 2 | 100% | 67% | 53% | CE 89%, EMN 46% |
| Fertilizers & Agricultural Chemicals | Materiais | 3 | 100% | 66% | 41% | MOS 73%, CF 66%, FMC 60% |
| Industrial Gases | Materiais | 2 | 50% | 35% | 26% | LIN 44%, APD 26% |
| Metal, Glass & Plastic Containers | Materiais | 1 | 0% | 29% | 24% | BALL 29% |
| Paper & Plastic Packaging Products & Materials | Materiais | 2 | 50% | 66% | 63% | AMCR 108%, PKG 25% |
| Specialty Chemicals | Materiais | 6 | 50% | 28% | 18% | ALB 71%, IFF 41%, LYB 33%, ECL 24%, SHW 21%, PPG 10% |
| Steel | Materiais | 3 | 100% | 96% | 54% | ATI 159%, CLF 96%, STLD 56% |
| Apparel, Accessories & Luxury Goods | Vestuário | 8 | 88% | 46% | 29% | FOSL 231%, UA 88%, UAA 88%, CPRI 52%, VFC 40%, TPR 38%, LULU 35%, RL 26% |
| Footwear | Vestuário | 1 | 100% | 34% | 10% | DECK 34% |

## 2. Microsetores por macrossetor (≥ 3 empresas), ordenados pela dispersão mediana

✔ = já está nas nossas listas. **candidato** = fora das listas e com dispersão mediana > 30%.

### Energia — dispersão mediana 83%; 81% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Oil & Gas Equipment & Services | 4 | 169% | 75% | 99% | 75% | ✔ |
| Oil & Gas Exploration & Production | 5 | 148% | 80% | 91% | 80% | ✔ |
| Oil & Gas Storage & Transportation | 4 | 40% | 75% | 24% | 50% | ✔ |

### Tecnologia — dispersão mediana 46%; 76% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Systems Software | 6 | 843% | 83% | 283% | 67% | **candidato** |
| Electronic Manufacturing Services | 3 | 72% | 100% | 26% | 33% | **candidato** |
| Technology Hardware, Storage & Peripherals | 9 | 68% | 100% | 19% | 44% | **candidato** |
| Communications Equipment | 6 | 55% | 50% | 24% | 50% | **candidato** |
| Semiconductors | 19 | 49% | 84% | 25% | 37% | **candidato** |
| Electronic Components | 3 | 46% | 67% | 24% | 33% | **candidato** |
| Semiconductor Materials & Equipment | 3 | 41% | 100% | 18% | 33% | **candidato** |
| IT Consulting & Other Services | 4 | 37% | 75% | 25% | 50% | **candidato** |
| Application Software | 15 | 34% | 60% | 19% | 27% | **candidato** |
| Internet Services & Infrastructure | 3 | 32% | 67% | 9% | 33% | **candidato** |
| Electronic Equipment & Instruments | 4 | 32% | 50% | 17% | 0% | **candidato** |

### Materiais — dispersão mediana 45%; 65% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Steel | 3 | 96% | 100% | 54% | 100% | ✔ |
| Fertilizers & Agricultural Chemicals | 3 | 66% | 100% | 41% | 100% | ✔ |
| Construction Materials | 6 | 32% | 50% | 20% | 0% | ✔ |
| Specialty Chemicals | 6 | 28% | 50% | 18% | 17% | ✔ |

### Consumo discricionário — dispersão mediana 43%; 72% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Automobile Manufacturers | 3 | 240% | 100% | 169% | 100% | **candidato** |
| Hotels, Resorts & Cruise Lines | 7 | 99% | 100% | 45% | 71% | **candidato** |
| Casinos & Gaming | 3 | 69% | 100% | 42% | 67% | ✔ |
| Broadline Retail | 3 | 55% | 100% | 44% | 67% | **candidato** |
| Apparel, Accessories & Luxury Goods | 8 | 46% | 88% | 29% | 50% | ✔ |
| Apparel Retail | 3 | 39% | 67% | 19% | 0% | **candidato** |
| Restaurants | 6 | 29% | 50% | 11% | 17% |  |
| Other Specialty Retail | 3 | 28% | 33% | 11% | 33% |  |
| Automotive Retail | 4 | 16% | 25% | 7% | 0% |  |

### Comunicação — dispersão mediana 38%; 71% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Movies & Entertainment | 3 | 83% | 100% | 40% | 67% | **candidato** |
| Interactive Media & Services | 5 | 38% | 60% | 19% | 40% | **candidato** |

### Financeiro — dispersão mediana 34%; 59% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Multi-line Insurance | 3 | 87% | 100% | 45% | 67% | **candidato** |
| Regional Banks | 7 | 79% | 86% | 31% | 57% | **candidato** |
| Life & Health Insurance | 5 | 58% | 80% | 29% | 40% | **candidato** |
| Consumer Finance | 4 | 42% | 75% | 19% | 0% | **candidato** |
| Asset Management & Custody Banks | 11 | 40% | 64% | 19% | 18% | **candidato** |
| Property & Casualty Insurance | 8 | 36% | 62% | 16% | 38% | **candidato** |
| Investment Banking & Brokerage | 5 | 31% | 60% | 14% | 20% | **candidato** |
| Diversified Banks | 7 | 31% | 57% | 17% | 14% | **candidato** |
| Financial Exchanges & Data | 8 | 30% | 50% | 13% | 12% |  |
| Transaction & Payment Processing Services | 10 | 25% | 40% | 13% | 20% |  |
| Insurance Brokers | 6 | 20% | 33% | 8% | 17% |  |

### Saúde — dispersão mediana 33%; 56% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Health Care Distributors | 4 | 80% | 75% | 34% | 50% | **candidato** |
| Biotechnology | 8 | 67% | 75% | 31% | 50% | **candidato** |
| Life Sciences Tools & Services | 9 | 40% | 56% | 24% | 33% | **candidato** |
| Health Care Supplies | 3 | 33% | 67% | 17% | 33% | **candidato** |
| Health Care Equipment | 15 | 29% | 47% | 15% | 27% |  |
| Health Care Services | 5 | 26% | 20% | 17% | 0% |  |
| Managed Health Care | 4 | 22% | 25% | 12% | 25% |  |

### Imobiliário — dispersão mediana 28%; 50% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Retail REITs | 3 | 31% | 67% | 20% | 0% | **candidato** |
| Telecom Tower REITs | 3 | 25% | 0% | 7% | 0% |  |
| Multi-Family Residential REITs | 3 | 24% | 33% | 13% | 0% |  |

### Indústria — dispersão mediana 25%; 38% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Passenger Airlines | 4 | 108% | 100% | 53% | 100% | ✔ |
| Construction & Engineering | 5 | 34% | 60% | 13% | 20% | ✔ |
| Construction Machinery & Heavy Transportation Equipment | 3 | 31% | 67% | 17% | 0% | ✔ |
| Building Products | 8 | 26% | 38% | 13% | 12% | ✔ |
| Aerospace & Defense | 11 | 24% | 36% | 13% | 18% |  |
| Air Freight & Logistics | 4 | 24% | 25% | 13% | 0% | ✔ |
| Industrial Machinery & Supplies & Components | 14 | 21% | 21% | 12% | 7% |  |
| Rail Transportation | 3 | 18% | 0% | 12% | 0% |  |
| Electrical Components & Equipment | 4 | 14% | 25% | 10% | 25% |  |
| Diversified Support Services | 3 | 12% | 33% | 6% | 33% |  |

### Utilidades públicas — dispersão mediana 25%; 36% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Multi-Utilities | 11 | 27% | 36% | 20% | 27% |  |
| Electric Utilities | 14 | 25% | 36% | 18% | 21% |  |

### Consumo básico — dispersão mediana 23%; 31% das empresas voláteis

| Subsetor | Empresas | Dispersão mediana | % voláteis | Só quedas: mediana | % voláteis só nas quedas | |
|---|---|---|---|---|---|---|
| Packaged Foods & Meats | 10 | 31% | 50% | 21% | 10% | **candidato** |
| Soft Drinks & Non-alcoholic Beverages | 4 | 23% | 0% | 14% | 0% |  |
| Consumer Staples Merchandise Retail | 5 | 20% | 20% | 12% | 0% |  |
| Household Products | 3 | 18% | 0% | 10% | 0% |  |

### Resumo: candidatos fora das listas (dispersão mediana > 30% no histórico completo)

| Subsetor | Macrossetor | Empresas | Dispersão mediana | Só quedas: mediana | Empresas mais voláteis |
|---|---|---|---|---|---|
| Systems Software | Tecnologia | 6 | 843% | 283% | TWLO ∞, PANW ∞, NOW 1088%, GEN 598%, FTNT 41%, MSFT 22% |
| Automobile Manufacturers | Consumo discricionário | 3 | 240% | 169% | TSLA ∞, F 240%, GM 98% |
| Hotels, Resorts & Cruise Lines | Consumo discricionário | 7 | 99% | 45% | EXPE 310%, NCLH 129%, RCL 99%, CCL 99%, MAR 64%, HLT 54% |
| Multi-line Insurance | Financeiro | 3 | 87% | 45% | AIG ∞, L 87%, AIZ 47% |
| Movies & Entertainment | Comunicação | 3 | 83% | 40% | LYV 92%, NFLX 83%, DIS 36% |
| Health Care Distributors | Saúde | 4 | 80% | 34% | COR 104%, CAH 94%, MCK 66%, HSIC 16% |
| Regional Banks | Financeiro | 7 | 79% | 31% | HBAN 170%, RF 117%, CFG 98%, ZION 79%, KEY 70%, FITB 52% |
| Electronic Manufacturing Services | Tecnologia | 3 | 72% | 26% | JBL 141%, TEL 72%, IPGP 41% |
| Technology Hardware, Storage & Peripherals | Tecnologia | 9 | 68% | 19% | P ∞, STX ∞, HPE 92%, HPQ 69%, WDC 68%, NTAP 42% |
| Biotechnology | Saúde | 8 | 67% | 31% | MRNA 277%, VRTX 184%, INCY 179%, REGN 88%, GILD 46%, ABBV 31% |
| Life & Health Insurance | Financeiro | 5 | 58% | 29% | PRU 121%, MET 77%, PFG 58%, GL 45%, AFL 22% |
| Broadline Retail | Consumo discricionário | 3 | 55% | 44% | ETSY 132%, AMZN 55%, EBAY 34% |
| Communications Equipment | Tecnologia | 6 | 55% | 24% | CIEN 399%, LITE 245%, MSI 84%, FFIV 25%, ANET 25%, CSCO 22% |
| Semiconductors | Tecnologia | 19 | 49% | 25% | NXPI ∞, AMD 238%, ON 158%, MU 131%, STM 130%, TSEM 101% |
| Electronic Components | Tecnologia | 3 | 46% | 24% | COHR 47%, GLW 46%, APH 17% |
| Consumer Finance | Financeiro | 4 | 42% | 19% | COF 50%, SLM 50%, SYF 34%, AXP 25% |
| Semiconductor Materials & Equipment | Tecnologia | 3 | 41% | 18% | TER 94%, LRCX 41%, AMAT 40% |
| Asset Management & Custody Banks | Financeiro | 11 | 40% | 19% | KKR 74%, ARES 74%, BX 57%, AMG 48%, IVZ 41%, STT 40% |
| Life Sciences Tools & Services | Saúde | 9 | 40% | 24% | CRL 144%, ILMN 125%, BIO 54%, TECH 45%, A 40%, IQV 27% |
| Apparel Retail | Consumo discricionário | 3 | 39% | 19% | GAP 45%, URBN 39%, TJX 21% |
| Interactive Media & Services | Comunicação | 5 | 38% | 19% | MTCH 98%, TRIP 53%, META 38%, GOOG 19%, GOOGL 19% |
| IT Consulting & Other Services | Tecnologia | 4 | 37% | 25% | ACN 46%, EPAM 41%, IT 32%, CTSH 14% |
| Property & Casualty Insurance | Financeiro | 8 | 36% | 16% | HIG 185%, ALL 85%, CINF 67%, PGR 40%, ACGL 32%, CB 27% |
| Application Software | Tecnologia | 15 | 34% | 19% | WDAY ∞, CRM 155%, ADSK 84%, CDNS 72%, TDC 59%, PTC 58% |
| Health Care Supplies | Saúde | 3 | 33% | 17% | ALGN 87%, COO 33%, WST 26% |
| Internet Services & Infrastructure | Tecnologia | 3 | 32% | 9% | VRSN 142%, GDDY 32%, AKAM 18% |
| Electronic Equipment & Instruments | Tecnologia | 4 | 32% | 17% | ZBRA 47%, KEYS 47%, TDY 18%, ROP 13% |
| Packaged Foods & Meats | Consumo básico | 10 | 31% | 21% | KHC 241%, TSN 48%, SJM 47%, MDLZ 47%, CAG 40%, GIS 22% |
| Investment Banking & Brokerage | Financeiro | 5 | 31% | 14% | GS 57%, SCHW 37%, MS 31%, IBKR 14%, RJF 13% |
| Retail REITs | Imobiliário | 3 | 31% | 20% | KIM 40%, SPG 31%, FRT 20% |
| Diversified Banks | Financeiro | 7 | 31% | 17% | C 137%, TFC 39%, BAC 37%, WFC 31%, JPM 21%, PNC 20% |

**Nas nossas listas, mas com dispersão mediana ≤ 30% no histórico completo:** Air Freight & Logistics (24%), Building Products (26%), Specialty Chemicals (28%)

## 3. Carteiras: estabilidade medida com todo o histórico até cada data (point-in-time)

Em cada trimestre, a medida usa todos os exercícios já disponíveis (exercício y só conta a partir de 30/06 de y+1), com no mínimo 5 anos seguidos. As 8 linhas obrigatórias primeiro; depois as versões que exigem ROIC estável (todas as variações) e só quedas.

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
| OoL novo + estável no histórico (≤ 30%) | 542,6% | 13,2% | 17,8% | -35,1% | 21 | 34% | 22% |
| GCGR novo + estável no histórico | 1007,8% | 17,4% | 18,3% | -34,8% | 30 | 54% | 34% |
| High ROIC + estável no histórico | 501,0% | 12,7% | 19,8% | -34,2% | 8 | 25% | 5% |
| High Growth + estável no histórico | 305,1% | 9,8% | 23,6% | -48,0% | 5 | 10% | 0% |
| OoL novo + quedas ≤ 30% no histórico | 676,0% | 14,6% | 18,3% | -36,5% | 34 | 38% | 23% |
| GCGR novo + quedas ≤ 30% no histórico | 937,6% | 16,9% | 17,6% | -32,2% | 26 | 64% | 34% |

### Posições da OoL e GCGR novas, por estabilidade no histórico até a data

| Classe | Medida | Grupo | Posições | Excesso médio a.a. | Excesso mediano a.a. |
|---|---|---|---|---|---|
| OoL novo | todas as variações | estável | 1198 | +1,2% | +0,1% |
| OoL novo | todas as variações | volátil | 1076 | +6,8% | +4,5% |
| OoL novo | só quedas | estável | 1877 | +3,4% | +0,6% |
| OoL novo | só quedas | volátil | 397 | +5,9% | +5,0% |
| GCGR novo | todas as variações | estável | 506 | -0,6% | -3,7% |
| GCGR novo | todas as variações | volátil | 767 | +5,1% | +2,1% |
| GCGR novo | só quedas | estável | 945 | +2,0% | -1,3% |
| GCGR novo | só quedas | volátil | 328 | +5,4% | +2,8% |