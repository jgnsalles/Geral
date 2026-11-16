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
