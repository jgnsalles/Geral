# Navegando LatAm

Artifact: https://claude.ai/artifact/AjT5A1E5a8NwkUs1aawrrM

Fontes, do mais fácil ao mais difícil (testadas em 16/11/2026):
1. Peru · SBS — ações locais das 4 AFPs por emissor/ISIN, valor e unidades, mensal desde 2014 (quadro CA-0001, Excel por mês).
   `scripts/pe.py` lê os arquivos baixados em `/home/user/raw/latam/pe` (links da página da SBS, que exige navegador por proteção anti-robô).
2. EUA · SEC N-PORT — carteiras dos fundos registrados nos EUA; filtro de ações com país de investimento na LatAm.
   `scripts/nport_loop.sh` baixa e extrai os trimestres (`scripts/nport.py`).
3. Chile · CMF — fondos mutuos, carteira por instrumento, só o último trimestre em Excel (articles-91849_document_2.xlsx).
4. Colômbia · Superfinanciera — pensões obrigatórias mensais, mas ações locais só por tipo (sem emissor).
5. Chile · Superintendencia de Pensiones — emissores em relatório PDF; centro de estatísticas não respondeu a acesso automatizado.
6. Argentina · CNV/CAFCI — carteira semanal só interna; API da CAFCI recusa acesso automatizado.
7. México · CNBV/CONSAR — carteira por fundo só em PDF de cada operadora; Afores agregadas.

Montagem: `python scripts/build_data.py` → `latam.json`; `python scripts/build_page.py` → index.html com os dados embutidos (gzip+base64).

## Attribution por fundo (aba "Por fundo")
- Peru: `scripts/attr_pe.py` → `pe_attr.json`. 16 fundos (4 AFPs × tipos 0–3), mensal desde 2014. Carteira = ações locais do fundo;
  preço = valor ÷ quantidade (soles, sem dividendos); contribuição = peso no fim do mês anterior × retorno; referência = ações locais de todas as AFPs.
- EUA: `scripts/nport_fundos.py` (carteira completa dos fundos com ≥ 50% em ações da LatAm, retorno mensal da cota e fluxos) e
  `scripts/attr_us.py` → `us_attr.json`. Preço em US$ = valor ÷ quantidade, mediana entre todos os fundos na mesma data; resto = cota − explicado.
- `scripts/nport_loop2.sh` baixa o histórico do N-PORT (2019T4 em diante) e roda os dois extratores (agora com ações preferenciais, categoria EP).
