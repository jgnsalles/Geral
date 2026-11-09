# Backtest no Brasil (método 2, só histórico)

> ⚠️ **ROIC:** ROIC clássico (EBIT × (1 − t) ÷ (patrimônio + dívida − caixa)) e ROE para financeiras; cortes 20%/10% não revistos.

## Dados e regras
- Fundamentos: DFPs da CVM (dados abertos), 2010–2026, consolidado quando existe; point-in-time pela data de entrega (DT_RECEB) e versão.
- Preços: Yahoo (.SA), retorno total; benchmarks BOVA11 (Ibovespa) e SMAL11 (small caps). Universo: ações listadas hoje na B3 (cadastro FCA),
  o ticker mais líquido de cada empresa; filtro de liquidez de R$ 2 mi/dia (mediana de 63 pregões).
- Parâmetros (pedido do usuário): WACC 12%; g de 9% (maior crescimento) a 4%; financeiras de 8,5% a 3,5%. Cortes de classe iguais aos dos EUA.
- Crescimento = mediana de 5 anos do lucro líquido dos controladores; LPA da CVM (ON/PN; units pela composição) só para o P/L.
- Período: 30/06/2014 a 30/09/2026 (começa quando há ≥ 60 empresas classificadas; mediana de 94 por trimestre).

## Como rodar
```bash
python3 brasil/fetch_cvm.py
python3 brasil/universe_prices.py
python3 brasil/prep_br.py
python3 brasil/backtest_br.py
```
