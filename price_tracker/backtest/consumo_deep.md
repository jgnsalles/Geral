# Sem Energia e Materiais; e o que separa vencedores de perdedores no Consumo (EUA, point-in-time)

> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). Marcas e varejo têm pouco capital, então o ROIC delas tende a ser alto; ROIC acima de 100% em empresas leves em ativos ainda está em aberto.

Configuração: sem zROIC, OoL a partir de ROIC 12%.

## A. Sem Energia e Materiais

Mesmas carteiras, só retirando as ações desses dois setores (a classificação das demais não muda). S&P 500: 15,6% a.a.

| Carteira | Atual | Sem Energia e Materiais | Ações retiradas por trimestre | Janelas 5a > S&P (atual → sem) | Janelas 10a > S&P (atual → sem) |
|---|---|---|---|---|---|
| OoL | 15,2% | **15,7%** | 2.5 | 27% → 35% | 4% → 15% |
| OoL High Returns | 16,3% | **16,2%** | 0.2 | 43% → 44% | 33% → 33% |
| OoL High Growth | 16,8% | **18,0%** | 1.2 | 44% → 51% | 33% → 34% |
| OoL Base | 13,5% | **13,9%** | 1.1 | 12% → 21% | 0% → 1% |
| GCGR | 15,9% | **15,9%** | 1.5 | 54% → 55% | 34% → 34% |

## B. Consumo Discricionário: vencedores × perdedores

49 empresas de consumo discricionário que passaram ≥ 4 trimestres na OoL e/ou na GCGR. Retorno = excesso médio sobre o universo enquanto estavam na classe. Terços: perdedores ≤ -12% a.a.; vencedores ≥ +5% a.a. Métricas **na primeira compra** (sem viés de olhar o futuro).

### B1. Por tipo de negócio

| Tipo | Empresas | Perdedores | Meio | Vencedores | Excesso mediano | Empresas |
|---|---|---|---|---|---|---|
| Bens duráveis para casa | 6 | 2 | 2 | 2 | -1% | MHK↓, WHR↓, MAT, HAS, LEN↑, GRMN↑ |
| Internet e marketplaces | 3 | 1 | 0 | 2 | +6% | ETSY↓, EBAY↑, AMZN↑ |
| Lojas de departamento | 1 | 0 | 1 | 0 | -4% | KSS |
| Marcas de vestuário e acessórios | 8 | 7 | 1 | 0 | -26% | UA↓, LULU↓, DECK↓, TPR↓, FOSL↓, CPRI↓, VFC↓, RL |
| Restaurantes | 6 | 1 | 3 | 2 | -3% | DPZ↓, CMG, MCD, YUM, DRI↑, SBUX↑ |
| Serviços ao consumidor | 1 | 0 | 0 | 1 | +21% | HRB↑ |
| Varejo de reforma e autopeças | 6 | 1 | 1 | 4 | +7% | AN↓, GPC, AZO↑, LOW↑, ORLY↑, HD↑ |
| Varejo especializado | 8 | 1 | 5 | 2 | +1% | SIG↓, URBN, ULTA, BBY, TSCO, GAP, TJX↑, WSM↑ |
| Veículos e autopeças (indústria) | 5 | 3 | 1 | 1 | -13% | HOG↓, GT↓, BWA↓, APTV, TSLA↑ |
| Viagem, hotéis e cassinos | 5 | 1 | 1 | 3 | +5% | WYNN↓, MAR, BKNG↑, HLT↑, EXPE↑ |

↑ vencedor, ↓ perdedor (ordenado do pior para o melhor).

### B2. Métricas na primeira compra (mediana por grupo)

Separação = (mediana dos vencedores − mediana dos perdedores) ÷ intervalo interquartil do consumo. Correlação = Spearman entre a métrica e o excesso, com 49 empresas (|ρ| > 0,28 ≈ significativo a 5%).

| Métrica | Perdedores | Meio | Vencedores | Separação | Correlação (ρ) |
|---|---|---|---|---|---|
| Tamanho: log10 NOPAT (US$ bi) | -0,1 | -0,1 | 0,0 | 0,5 | **+0,40** |
| Peso do capital de giro no capital | 27% | 31% | -1% | -0,6 | **-0,38** |
| Peso do imobilizado no capital | 45% | 62% | 79% | 0,7 | **+0,35** |
| Retorno esperado | 32% | 29% | 37% | 0,2 | +0,24 |
| ROIC último ano ÷ mediana dos 5 anteriores | 1,2 | 1,2 | 1,3 | 0,2 | +0,23 |
| Dividend yield | 0,0% | 1,2% | 0,9% | 0,5 | +0,22 |
| Crescimento do capital no ano | 5% | 5% | 5% | 0,0 | -0,20 |
| Desvio-padrão do ROIC (6a) | 9% | 5% | 8% | -0,0 | +0,20 |
| zGrowth | 1,1 | 1,1 | 1,8 | 0,4 | +0,14 |
| Anos de queda do EPS (de 5) | 1,0 | 0,0 | 1,0 | 0,0 | +0,11 |
| Crescimento do EPS no último ano | 22% | 20% | 24% | 0,2 | +0,11 |
| Peso de ágio + intangíveis no capital | 19% | 11% | 19% | 0,0 | +0,11 |
| Dívida ÷ patrimônio | 0,4 | 0,5 | 0,4 | -0,0 | +0,09 |
| Crescimento: média dos 2 últimos − G | 2% | -1% | -3% | -0,4 | -0,08 |
| Alta da ação nos 12 meses antes | 4% | 33% | 18% | 0,3 | +0,08 |
| ROIC do último ano | 24% | 29% | 31% | 0,3 | +0,07 |
| ROIC do modelo | 23% | 25% | 27% | 0,1 | +0,07 |
| P/E justo | 33,2 | 32,7 | 31,9 | -0,1 | +0,06 |
| Reinvestimento (g ÷ ROIC) | 27% | 24% | 23% | -0,2 | -0,06 |
| Alíquota de imposto | 29% | 34% | 24% | -0,3 | -0,00 |
| P/L | 18,3 | 18,8 | 22,2 | 0,3 | -0,00 |
| Crescimento do EPS (G) | 23% | 19% | 27% | 0,2 | -0,00 |
| P/L 2 anos depois ÷ P/L na compra *(depois)* | 0,8 | 1,1 | 1,3 | 1,1 | **+0,61** |
| Trimestres na OoL/GCGR *(depois)* | 12,0 | 18,0 | 22,0 | 0,8 | **+0,31** |
| ROIC do último ano, 2 anos depois *(depois)* | 32% | 25% | 20% | -0,6 | -0,17 |
| EPS 2 anos depois da 1ª compra ÷ EPS na compra − 1 *(depois)* | 28% | 14% | 10% | -0,4 | -0,04 |

*(depois)* = medido depois da compra; não serve para escolher, só para entender o que aconteceu.

### B3. Todas as empresas

| Grupo | Ticker | Empresa | Tipo | Classe | Trim. | Excesso a.a. | ROIC | Tendência ROIC | G | Cresc. último ano | P/L | Alta 12m antes | Imobilizado no capital | EPS 2a depois | P/L 2a depois ÷ compra |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vencedores | TSLA | Tesla, Inc. | Veículos e autopeças (indústria) | GCGR/OoL | 8 | +47% | 43% | 1,6 | 122% | +19% | 40,9 | -7% | 81% | -75% | 8,2 |
| Vencedores | EXPE | Expedia Group | Viagem, hotéis e cassinos | GCGR/OoL | 6 | +24% | 14% | 3,2 | 69% | +69% | 18,8 | +22% | 77% | +10% | 1,4 |
| Vencedores | HRB | H&R BLOCK INC | Serviços ao consumidor | GCGR | 4 | +21% | 144% | — | 9% | +52% | 7,8 | -23% | 38% | -101% | — |
| Vencedores | WSM | Williams-Sonoma, Inc. | Varejo especializado | GCGR/OoL | 5 | +19% | 116% | 1,5 | 21% | +21% | 18,0 | +1% | 140% | +1% | 1,6 |
| Vencedores | SBUX | Starbucks Corporation | Restaurantes | GCGR/OoL | 20 | +12% | 27% | 2,5 | 21% | +138% | 30,1 | +48% | 94% | +44% | 1,5 |
| Vencedores | HD | The Home Depot, Inc. | Varejo de reforma e autopeças | OoL | 46 | +12% | 13% | 1,2 | 17% | +28% | 16,4 | +7% | 83% | +49% | 1,6 |
| Vencedores | GRMN | Garmin | Bens duráveis para casa | GCGR/OoL | 22 | +11% | 42% | 0,9 | 13% | +13% | 18,9 | +34% | 36% | +36% | 1,3 |
| Vencedores | LEN | Lennar | Bens duráveis para casa | GCGR/OoL | 32 | +11% | 19% | 1,3 | 24% | +24% | 14,0 | -6% | — | -1% | 1,3 |
| Vencedores | ORLY | O'Reilly Automotive | Varejo de reforma e autopeças | GCGR/OoL | 49 | +10% | 12% | 1,6 | 32% | +26% | 24,6 | +58% | 60% | +63% | 1,0 |
| Vencedores | LOW | Lowe's Companies, Inc. | Varejo de reforma e autopeças | OoL | 30 | +9% | 15% | 1,2 | 27% | +27% | 22,3 | -0% | 94% | -18% | 1,7 |
| Vencedores | HLT | Hilton Worldwide Holdings Inc. | Viagem, hotéis e cassinos | GCGR/OoL | 14 | +8% | 12% | 0,6 | 63% | -75% | 58,9 | +35% | 56% | +138% | 0,7 |
| Vencedores | TJX | TJX Companies | Varejo especializado | GCGR/OoL | 15 | +7% | 48% | 1,9 | 16% | +7% | 22,2 | +17% | 89% | +10% | 1,1 |
| Vencedores | AMZN | Amazon.com, Inc. | Internet e marketplaces | OoL | 31 | +6% | 106% | 0,3 | 33% | +24% | 68,4 | -5% | 62% | -104% | — |
| Vencedores | EBAY | eBay Inc. | Internet e marketplaces | GCGR/OoL | 50 | +6% | 15% | 1,3 | 35% | -26% | 21,7 | +21% | 16% | +46% | 1,3 |
| Vencedores | DRI | Darden Restaurants, Inc. | Restaurantes | OoL | 20 | +5% | 19% | 3,2 | 24% | +24% | 23,5 | +45% | 90% | -109% | — |
| Vencedores | BKNG | Booking Holdings Inc. | Viagem, hotéis e cassinos | GCGR/OoL | 40 | +5% | 49% | 1,1 | 99% | +99% | 34,8 | +42% | 3% | +75% | 0,9 |
| Vencedores | AZO | AutoZone | Varejo de reforma e autopeças | GCGR/OoL | 58 | +5% | 36% | 1,3 | 28% | +30% | 16,7 | +18% | 118% | +43% | 1,0 |
| Meio | MAR | Marriott International, Inc. | Viagem, hotéis e cassinos | GCGR/OoL | 23 | +4% | 23% | 1,8 | 22% | +27% | 31,6 | +45% | 52% | +4% | 1,2 |
| Meio | GPC | Genuine Parts Company | Varejo de reforma e autopeças | OoL | 11 | +4% | 21% | 1,3 | 16% | +16% | 18,8 | +28% | 19% | +11% | 1,1 |
| Meio | GAP | GAP INC | Varejo especializado | OoL | 18 | +3% | 35% | 1,3 | 19% | +19% | 8,6 | -11% | 87% | +24% | 2,1 |
| Meio | TSCO | Tractor Supply Company | Varejo especializado | GCGR/OoL | 28 | +2% | 26% | 1,3 | 26% | +22% | 30,4 | +37% | 55% | +29% | 1,0 |
| Meio | HAS | Hasbro | Bens duráveis para casa | GCGR | 5 | +1% | 26% | 1,0 | 10% | +3% | 13,0 | -20% | 11% | -23% | 2,1 |
| Meio | APTV | Aptiv PLC | Veículos e autopeças (indústria) | GCGR/OoL | 20 | +1% | 31% | 1,0 | 22% | +17% | 17,4 | +55% | 65% | +30% | 0,9 |
| Meio | BBY | Best Buy | Varejo especializado | GCGR/OoL | 28 | -1% | 27% | 1,4 | 49% | +49% | 12,9 | +56% | 59% | +36% | 1,1 |
| Meio | YUM | Yum! Brands, Inc. | Restaurantes | OoL | 20 | -2% | 57% | 1,2 | 15% | +23% | 21,3 | +4% | 86% | -31% | 1,7 |
| Meio | ULTA | Ulta Beauty, Inc. | Varejo especializado | GCGR/OoL | 24 | -2% | 25% | 1,1 | 26% | +31% | 43,7 | +47% | 62% | +37% | 0,9 |
| Meio | MAT | MATTEL INC /DE/ | Bens duráveis para casa | OoL | 18 | -3% | 31% | 1,2 | 28% | +28% | 13,9 | +17% | 22% | +19% | 1,5 |
| Meio | KSS | KOHLS Corp | Lojas de departamento | GCGR | 14 | -4% | 14% | 1,0 | 13% | +15% | 13,4 | -5% | 90% | +14% | 1,0 |
| Meio | MCD | McDonald's Corporation | Restaurantes | GCGR/OoL | 18 | -4% | 25% | 1,2 | 13% | +15% | 18,6 | +33% | 94% | +5% | 1,0 |
| Meio | URBN | URBAN OUTFITTERS INC | Varejo especializado | OoL | 10 | -5% | 25% | 1,0 | 17% | +36% | 24,8 | +52% | 66% | +4% | 0,9 |
| Meio | RL | Ralph Lauren Corporation | Marcas de vestuário e acessórios | GCGR/OoL | 10 | -6% | 21% | 1,0 | 12% | +5% | 19,1 | -7% | 32% | -45% | 1,1 |
| Meio | CMG | Chipotle Mexican Grill, Inc. | Restaurantes | GCGR/OoL | 34 | -7% | 24% | 1,5 | 43% | +20% | 61,8 | +54% | 105% | +55% | 0,9 |
| Perdedores | AN | AUTONATION, INC. | Varejo de reforma e autopeças | GCGR/OoL | 14 | -12% | 11% | 1,2 | 30% | +21% | 17,5 | +22% | 58% | +28% | 0,7 |
| Perdedores | BWA | BORGWARNER INC | Veículos e autopeças (indústria) | GCGR | 10 | -13% | 13% | 1,9 | 19% | -6% | 18,5 | -8% | 54% | +37% | 1,1 |
| Perdedores | DPZ | Domino's Pizza, Inc. | Restaurantes | GCGR/OoL | 21 | -13% | 113% | 1,1 | 24% | +14% | 38,6 | +34% | 55% | +42% | 0,8 |
| Perdedores | WYNN | Wynn Resorts | Viagem, hotéis e cassinos | GCGR/OoL | 20 | -13% | 19% | 1,8 | 278% | +278% | 25,6 | +4% | 116% | +47% | 1,4 |
| Perdedores | GT | GOODYEAR TIRE & RUBBER CO /OH/ | Veículos e autopeças (indústria) | OoL | 16 | -16% | 12% | 2,5 | 208% | +285% | 3,1 | +5% | 80% | -46% | 2,5 |
| Perdedores | HOG | HARLEY-DAVIDSON, INC. | Veículos e autopeças (indústria) | GCGR | 12 | -17% | 26% | 1,3 | 19% | +18% | 15,7 | -7% | 34% | -1% | 1,1 |
| Perdedores | VFC | V F CORP | Marcas de vestuário e acessórios | GCGR/OoL | 22 | -17% | 16% | 1,3 | 15% | +54% | 18,3 | +51% | 11% | +36% | 1,3 |
| Perdedores | CPRI | Capri Holdings Ltd | Marcas de vestuário e acessórios | OoL | 20 | -20% | 70% | 1,1 | 153% | +63% | 27,5 | +43% | 38% | +38% | 0,4 |
| Perdedores | WHR | WHIRLPOOL CORP /DE/ | Bens duráveis para casa | OoL | 4 | -21% | 13% | 1,1 | 17% | +17% | 14,9 | -3% | 45% | -124% | — |
| Perdedores | FOSL | Fossil Group, Inc. | Marcas de vestuário e acessórios | OoL | 15 | -25% | 34% | 1,6 | 22% | +22% | 16,6 | -34% | 32% | +42% | 1,0 |
| Perdedores | TPR | Tapestry, Inc. | Marcas de vestuário e acessórios | GCGR/OoL | 20 | -27% | 74% | 1,2 | 22% | +25% | 17,8 | +22% | 54% | +24% | 0,9 |
| Perdedores | ETSY | ETSY INC | Internet e marketplaces | GCGR | 10 | -29% | 30% | 2,2 | 25% | +26% | 36,6 | -38% | 13% | -34% | 0,8 |
| Perdedores | DECK | Deckers Outdoor Corporation | Marcas de vestuário e acessórios | OoL | 9 | -35% | 84% | 1,5 | 21% | +51% | 33,2 | +86% | 54% | +44% | 0,4 |
| Perdedores | SIG | SIGNET JEWELERS LTD | Varejo especializado | OoL | 7 | -49% | 13% | 0,7 | 17% | +24% | 14,0 | -35% | 15% | +27% | 0,6 |
| Perdedores | MHK | MOHAWK INDUSTRIES INC | Bens duráveis para casa | GCGR | 4 | -60% | 11% | 1,2 | 34% | +4% | 17,9 | +1% | 45% | -21% | 0,4 |
| Perdedores | LULU | Lululemon Athletica | Marcas de vestuário e acessórios | OoL | 11 | -61% | 63% | 0,7 | 37% | -11% | 76,5 | +61% | 69% | +119% | 0,2 |
| Perdedores | UA | Under Armour, Inc. | Marcas de vestuário e acessórios | OoL | 5 | -78% | 23% | 0,6 | 23% | +11% | 34,9 | -56% | 25% | +0% | 0,6 |
### B4. O sinal de composição do capital vale fora do consumo?

Correlação de Spearman (métrica na 1ª compra × excesso médio na classe), empresas não financeiras com ≥ 4 trimestres:

| Grupo | Empresas | Capital de giro no capital | Imobilizado no capital | Tamanho |
|---|---|---|---|---|
| Consumo discricionário | 49 | **−0,38** | **+0,35** | **+0,40** |
| Todas as não financeiras | 243 | −0,02 | −0,03 | +0,04 |
| Fora do consumo | 194 | +0,07 | −0,07 | −0,04 |
| Tecnologia | 53 | +0,04 | +0,13 | −0,01 |
| Indústria | 50 | −0,16 | −0,13 | −0,04 |
| Saúde | 30 | −0,15 | +0,02 | +0,16 |

O sinal é **específico do consumo**: ali ele separa modelos de negócio (marca que vende no atacado e carrega estoque e recebíveis × varejista/operador
que recebe à vista e é financiado por fornecedores). Não é um fator geral.
