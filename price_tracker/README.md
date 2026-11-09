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

## Resultado (snapshot 2026-11-09)

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
