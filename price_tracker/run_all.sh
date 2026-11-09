#!/usr/bin/env bash
# Roda todas as analises da rodada, em ordem (dados ja coletados).
set -e
cd "$(dirname "$0")"
D=2026-11-09
echo "== Modelo atual (Wise x P1 x P2)"
python3 hybrid.py $D && python3 compare.py $D && python3 hist_method.py $D && python3 venn.py $D
echo "== Backtest EUA"
rm -f backtest/data/classes_pit.csv
python3 backtest/backtest.py && python3 backtest/summarize.py
echo "== Diagnosticos EUA"
python3 backtest/diagnose.py 2.93 && python3 backtest/diagnose.py 0.9
python3 backtest/scenarios.py
python3 backtest/attribution.py 2.93
python3 backtest/expected_vs_realized.py 2.93
python3 backtest/worst_cases.py 2.93 && python3 backtest/sectors.py 2.93
python3 backtest/zroic_breakdown.py && python3 backtest/zroic_unstable.py
echo "== Brasil"
rm -f brasil/data/classes_pit.csv
python3 brasil/backtest_br.py && python3 brasil/rerun_params.py && python3 brasil/run_v3.py
python3 brasil/attribution_br.py && python3 brasil/attribution_br.py ool_gcgr
echo "== Dois paises e historico de ROIC"
python3 backtest/diag_two_countries.py && python3 backtest/roic_history_flaw.py
echo "== fim"
