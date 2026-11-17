# Navegando US

148 gestoras ativas e independentes (lista em `gestoras.txt`: CIK | nome | long-only ou hedge), a partir do 13F da SEC.
Mesmo app do Navegando LatAm (src/app.html), só com a base 13F e referência S&P 500 (SPY).

Ordem:
1. `scripts/f13us_loop.sh` → baixa os arquivos trimestrais do 13F (2016–) e roda `f13us.py` (carteira completa dessas gestoras, sem opções; preço mediano por CUSIP entre todos os gestores).
2. `scripts/edgar_q.py 2026-09-30 f13/zz_2026q3_edgar.pkl` → entregas mais recentes direto do EDGAR (antes de entrarem nos arquivos trimestrais).
3. `scripts/attr_us13.py` → pesos, retorno e attribution por gestora (corrige unidade trocada linha a linha e desdobramentos); `us_attr.json`.
4. `scripts/classifica_us.py` → país e setor de cada empresa (cadastro da SEC: endereço e SIC; nome e ticker); `classe.json`.
5. `scripts/build_us.py` → monta comb.json e embute os dados em index.html.

Limites: 13F mostra só ações listadas nos EUA (ADRs incluídos), sem vendidos, opções ou caixa; posições < 0,2% da carteira ficam fora das listas.
Sem 13F recente: Oaktree (até 2026-06 via relatório combinado), Greenlight (até 2023), Scion (até 2025), Omega/Cooperman (até 2018).
