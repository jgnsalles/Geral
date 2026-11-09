# Price Tracker em Python (teste controlado do modelo híbrido)

Replica a lógica da aba `Formula` do `Price_Tracker_v2.xlsx` sem Excel/Wisesheets, com fontes gratuitas,
e compara o resultado com o último refresh do Wisesheets salvo na planilha.

## Como rodar

```bash
python3 extract_wise.py ../Price_Tracker_v2.xlsx data/wise_snapshot.csv   # gabarito (valores do Wisesheets)
python3 fetch_yahoo.py data/wise_snapshot.csv 2026-11-09                   # congela snapshot Yahoo
python3 fetch_edgar.py data/wise_snapshot.csv 2026-11-09                   # congela snapshot SEC
python3 fetch_fx.py 2026-11-09                                             # congela câmbio
python3 hybrid.py 2026-11-09                                               # modelo -> data/hybrid_<data>.csv
python3 compare.py 2026-11-09                                              # relatório -> report_<data>.md
python3 experiments.py 2026-11-09                                          # testa combinações de correções
```

Tudo roda sobre snapshots datados em `data/raw/`: o mesmo snapshot gera sempre o mesmo resultado.

## Arquivos

| Arquivo | Função |
|---|---|
| `engine.py` | Lógica da planilha (Growth, zGrowth, ROIC, zROIC, g, P/E justo, classe). Reproduz 224/224 classes do Excel com os dados do Wisesheets. |
| `hybrid.py` | Modelo híbrido: histórico (SEC, senão Yahoo) + 2 anos projetados (Yahoo). |
| `roic_calib.py` | Descobre a definição de ROIC do Wisesheets. |
| `compare.py`, `variants.py`, `experiments.py` | Comparação e testes de correções. |

## Descobertas sobre o Wisesheets

- **ROIC** = NOPAT ÷ (ativo total − passivo circulante), valores de fim de ano. No setor **Financial Services** ele usa **ROE** (lucro líquido ÷ patrimônio). Nos bancos bate na 3ª casa decimal.
- **Growth (coluna T)** = média de (mediana dos 4 anos, média dos 4 anos, média das colunas R:S).
- O bloco de financeiras (linhas 211–233) tem `g` próprio: de 6,5% a 3%, ranqueado só entre elas.

## ROIC usado no modelo

Por decisão do usuário, o padrão é o **ROIC clássico** = NOPAT ÷ (patrimônio + dívida − caixa) para empresas operacionais
e **ROE** para o setor financeiro. A fórmula do Wise (ativo total − passivo circulante) está errada como capital investido
e fica disponível só para comparação (`ROIC_DEF = 'wise'` em `hybrid.py`). Os números da tabela abaixo foram medidos
com a fórmula do Wise, para isolar as outras distorções.

Com o ROIC clássico (mesmo snapshot): ROIC mediano das operacionais vai de 14,7% para 22,1%, a fração acima de 20% vai de
31% para 52%, o tier A vai para 57 nomes e a Opportunity of Lifetime para 22. Empresas com capital investido ≤ 0
(patrimônio negativo/recompras: MSCI, DPZ, HLT, PM; MOH) ficam sem ROIC. **Os cortes 20%/10% precisam ser revistos para essa definição.**

## Ranking do `g` (decisão do usuário, 2026-11-09)

O ranking que define o `g` (7% → 3,5%) e, por tabela, o P/E justo passa a usar a **mediana do crescimento do EPS nos últimos 3 anos realizados**
(`rank_growth` em `hybrid.py`), como crescimento normalizado. O Growth que entra no código da classe continua sendo o projetado.
Anos com EPS-base negativo não têm crescimento definido; com menos de 2 anos válidos a ação fica sem `rank_growth`
(MNST, WDC, ROG.SW, CPRX, SAF.PA, GIVN.SW, COLO-B.CO, 6367.T, 7741.T, HOOD, SOFI), sem `g`, e o retorno cai no fallback do Excel (média do crescimento projetado).

## Bug do coletor da SEC (corrigido em 2026-11-09)

`fetch_edgar.py` parava no primeiro conceito/unidade XBRL com algum dado (ex.: EPS de COST só até 2010). Isso deixava dívida, caixa,
patrimônio e EPS desatualizados em dezenas de empresas e, no ROIC clássico, dívida/caixa ausentes viravam zero. Agora o coletor escolhe o
conceito que chega ao último exercício e completa os anos que faltam. **Resultados anteriores com o ROIC clássico estavam contaminados.**

**Pendência para a investigação do ROIC:** em 35 empresas nem a SEC nem o Yahoo trouxeram dívida e/ou caixa, e o modelo assume 0 (sinalizado em `flags`).
Para dívida real (UL, DEO, RELX, AZN, ações japonesas) isso infla o ROIC. Além disso a dívida da SEC é só de longo prazo, sem arrendamentos.

## Resultado (snapshot 2026-11-09) — medido ANTES das duas mudanças acima, com a fórmula de ROIC do Wise

| | Modelo inicial | Modelo corrigido |
|---|---|---|
| Mesma classe | 56% | 59% |
| Mesmo tier | 61% | 63% |
| Opportunity of Lifetime em comum (Wise = 13) | 9 | 12 |

Teto do teste: trocando só crescimento, zGrowth e retorno pelos valores do Wise, a concordância sobe para 88% das classes,
com as 13 Opportunity of Lifetime idênticas. **A maior parte da diferença vem do horizonte de projeção (Yahoo: 2 anos; Wise: 4 anos), não da lógica.**

### Distorções e como foram tratadas

| Distorção | Tratamento |
|---|---|
| EPS histórico GAAP (SEC) × estimativa ajustada (Yahoo): ABBV, GPC, APTV, ON… | Growth e zGrowth só com os 2 anos projetados |
| zGrowth com 2 pontos tem outra escala | Corte recalibrado por percentil: 0,9 → 0,49 |
| ADRs com EPS em outra moeda (ASML, ONON, CNI, ABBN, NOVN…) | Conversão pelo câmbio congelado |
| Setor financeiro sem passivo circulante | ROE, igual ao Wisesheets |
| EPS da SEC não ajustado a desdobramento (BKNG) | Fica só como alerta: o histórico GAAP saiu do crescimento |
| Retorno "múltiplo constante": Wise mede 2027→2029, Yahoo só alcança 2026→2027 | Usa o crescimento do ano +1. **Limite estrutural da fonte gratuita** |
| ROIC de DPZ (patrimônio negativo) | Exceção conhecida |
| ROG.SW, CPRX sem estimativa no Yahoo | Ficam sem classe |
