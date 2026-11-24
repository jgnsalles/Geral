# Equities Diagnosis

Artefato: https://claude.ai/artifact/3YhpqKNGkJkqXuRmg2vqaY

Página própria (separada do Carteiras das Gestoras) para diagnóstico das gestoras de ações. Versão 1 = a parte de performance
copiada do Carteiras: ranking líquido em US$/R$ com horizontes 6m–10a, coluna desde o início do Apo, quartis, gráfico selecionável
e página de desempenho por gestora.

Dados: `data.json` publicado ao lado da página = `perf.json` gerado por `gestoras_performance/perf_export.py` + lista de gestoras.
Não versionado aqui (≈700 KB); regenerar com os scripts de `gestoras_performance/`.

## Attribution (aba Attribution)
1. `perf_export.py` com `DUMP_E=E_gross.pkl` → fundos-mês da base bruta (masters/diretos) das gestoras selecionadas (`E_sel.pkl`, `attr_funds.txt`).
2. `holdings.py raw/cda attr_funds.txt attr` → posições longas por fundo-mês + PL + confidencial (CDA).
3. `fic_links.py raw/cda attr_funds.txt links_attr.pkl` + `holdings.py` dos fundos investidos → look-through de cotas.
4. `b3_prices.py` (COTAHIST) + `b3_events.py` (API B3: proventos e desdobramentos) → `b3_returns.py` = retorno total mensal por ticker.
5. `XH=… XP=… XL=… attr_build.py E_sel.pkl holdings.pkl cda_pl.pkl ret.pkl perf.json nomes.json attr.json`.
   Conferência: correlação 0,974 entre soma das contribuições e retorno bruto dos fundos (meses com carteira > 70% revelada).

## Passivo (aba Passivo)
`perf_export.py` com `DUMP_EN=E_net.pkl` → `passivo_build.py E_net.pkl raw/perfil gestoras_perf.json <html Gestoras CVM> passivo.json`
(Perfil Mensal da CVM desde 2019 + Formulário de Referência anual).

`build_diag.py <scratch>` monta a página; publicar com data.json, attr.json e passivo.json ao lado.

## Empresas (aba Empresas)
1. `univ.py raw/b3 vol_anual.pkl` → volume anual por ticker no COTAHIST; universo = 250 mais negociadas de cada ano + tudo que os fundos já tiveram + Ibovespa e Small atuais (API de índices da B3).
2. `b3_prices.py` + `b3_events.py` + `b3_returns.py` (eventos deduplicados; grupamento/desdobramento não registrado inferido pelo salto diário; quedas reais mantidas).
3. `emp_build.py ret.pkl nomes.json tags.json raw/b3ev perf.json empresas.json` → série por empresa (classe mais negociada nos 12 meses anteriores), inclusive as que saíram da bolsa.

## Setores, LatAm e Fourth Sail
- `sectors.py` (classificação da B3 via API) + `sectors_cvm.py` (CVM: FCA ticker → CNPJ → SETOR_ATIV) → baldes; mapa manual em `build_diag.py` para o que faltar e para ações estrangeiras.
- `foreign.py raw/cda foreign.pkl` (bloco 7 da CDA de todos os fundos) → `foreign_prices.py`: preço mensal em R$ de ações estrangeiras = mediana de valor ÷ quantidade entre fundos (sem dividendos); cota dos fundos offshore Fourth Sail (via fundos da Tordesilhas).
- `prep_la.py`: attribution da Onyx LatAm (30.181.837) e do fundo brasileiro da Apo (41.333.289), Brasil + exterior.
- B3: saltos diários ≥ 50× ou ≤ 1/50 = mudança de cotação (lote de mil → unidade), neutralizados.
