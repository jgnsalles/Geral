# Brazil Downturn

Fluxos das gestoras de ações no Brasil (2006–out/2026): macro × performance, e quem capta na seca.
Artefato: https://claude.ai/artifact/3br1cpXrM8dMvBxEPgQkPP

Rodar na ordem (dados brutos da CVM numa pasta `raw/`: cad_fi.csv, cad_fi_hist.zip, registro_fundo_classe.zip, infd/inf_diario_fi_*.zip):

1. `01_extrai_informe.py raw painel_fundos.pkl` — Informe Diário → fundo-mês (PL, cota, captação, resgate).
2. `02_painel_gestoras.py raw painel_fundos.pkl carteiras.json cdi_m.json out` — gestor na data, flags FIC/exclusivo datadas,
   fluxo híbrido (captação−resgate dos fundos que continuam elegíveis + fundos novos líquidos de migrações de master), índices.
   `carteiras.json` vem do artefato Navegando Brasil; `cdi_m.json` é a série SGS 4391 do BCB.
3. `03_analise.py out carteiras.json gestoras_fr.json resultado.json` — ciclo, decomposição, Fama-MacBeth, perfil de quem capta na seca.
   `FLOW=rep` refaz tudo com captação−resgate reportados (robustez). `gestoras_fr.json` vem do artefato Gestoras CVM.

`artefato/` tem o template, os dados da página e os resultados completos (principal e robustez).

Parte 2, por tipo de investidor (2019T2–2026T1):

4. `04_extrai_perfil.py raw/perfil out/fundo_mes.pkl out/perfil.pkl` — Perfil Mensal da CVM (% do PL por tipo de cotista).
5. `05_extrai_cotistas_fundos.py raw/cda raw/perfil out/fundo_mes.pkl out` — CDA bloco 2 (quem são os fundos cotistas) no fim de cada trimestre e o Perfil deles.
6. `06_passivo.py raw out carteiras.json ust10.csv passivo.json` — posição e fluxo de cada tipo de investidor final por gestora-trimestre
   (abertura recursiva dos feeders, classificação dos fundos de outras casas), regimes (Ibov, Selic, Treasury FRED DGS10, fluxo da indústria),
   sensibilidade a CDI/Ibov/Treasury, alpha 12m × 36m, perfil 0–100 de quem recebe e listas. Resumo em `artefato/passivo_resumo.txt`.

A página é montada de `artefato/template.html` (dados da parte 1 em `bd_data.json`, parte 2 em `artefato/data/passivo.json`).
