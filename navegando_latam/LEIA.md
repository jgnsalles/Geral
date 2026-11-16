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

## Gestoras do 13F (base "13F · gestoras LatAm")
- `scripts/f13_loop.sh` baixa os conjuntos do Form 13F desde 2016 e roda `scripts/f13.py` (gestoras com ≥ 40% do 13F em empresas da
  LatAm e ≥ US$ 20 mi nelas, mais Moneda, Fourth Sail e INCA). CUSIPs da LatAm em `latam_cusips.txt` (vindos do N-PORT).
- `scripts/attr_13f.py` → `f13_attr.json`: carteira 13F por trimestre, retorno = peso × preço (mediana entre gestores, sem dividendos),
  referência iShares Latin America 40 (ILF). Só ações (títulos de dívida fora); gestoras com ≥ 50% em LatAm ou pedidas.
- O 13F só cobre o que é listado nos EUA: ações compradas só em bolsas locais não aparecem.

## Só LatAm (sem Brasil)
Ranking e attribution dos EUA (N-PORT) e do 13F excluem quem é Brasil: gestoras sediadas no Brasil e carteiras com 70% ou mais da parte
latino-americana em Brasil (mediana no tempo). No 13F, foco em LatAm = ≥ 5 empresas da região e ≥ 50% da carteira nelas (mediana);
Moneda, Fourth Sail e INCA sempre entram. País de cada CUSIP em `cusip_pais.pkl` (do N-PORT). Fundos de um país só aparecem marcados.

## Setores
`scripts/setores.py` → `setores.json` (14 setores). Fontes, nesta ordem: lista manual das maiores posições; setor da SBS (Peru);
classificação setorial da B3 (Brasil, a mesma do Navegando Brasil); código SIC da SEC (empresas listadas nos EUA); regras pelo nome.
Cobertura ~99% do peso das carteiras dos fundos dos EUA e do 13F. A página mostra setor por ação, quadro de setores (peso e attribution)
no detalhe de cada fundo e os setores principais no ranking.

## Versão atual (redesenho): `src/app.html`
Telas: Empresas (início) → Empresa; Gestores (ranking) → Gestor; Sobre. Busca única no topo; rotas por hash (#e-<empresa>, #g-<base>-<id>).
- `scripts/build_combined.py` → `comb.json`: liga a mesma empresa entre Peru, N-PORT, 13F, Chile e o total dos fundos dos EUA (ISIN, CUSIP,
  nome); detentores atuais e de 12 meses antes (Peru por AFP, Chile por administradora), histórico trimestral de nº de gestores,
  índice de preço em US$ (N-PORT; Peru convertido de soles). Presença = média entre as bases da fração dos gestores que têm a ação.
- `scripts/build_app.py` monta a página com os dados embutidos. A página anterior (`src/page.html`, `scripts/build_page.py`) fica como referência.

## Regra: toda tabela é ordenável
Em `src/app.html`, um MutationObserver aplica `enhance()` a qualquer tabela que aparece em `main`: título de coluna clicável (alterna ↓/↑),
vazios sempre por último, etiquetas (nova, saiu, base) ignoradas na ordem, números lidos de %, p.p., US$ mi/bi; no celular, seletor
"Ordenar por". A ordem escolhida fica guardada por tabela e é reaplicada quando a tabela é redesenhada. Tabelas com ordenação própria sobre
os dados completos (ex.: lista de empresas, que é paginada) usam `data-own="1"`. Tabelas novas não precisam de código extra.
