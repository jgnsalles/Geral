"""Devolve subsetores da lista de ciclicos para a analise (OoL/GCGR) e compara, com os comparativos obrigatorios.
A: pedido do usuario (hoteis, entretenimento, brinquedos, distribuidoras de saude).
B: os que de fato renderam acima do universo como Cyclicals (hoteis, entretenimento, biotecnologia, montadoras, quimicos basicos).
Saidas: backtest/ciclicos_volta.md, backtest/ciclicos_volta.png. Uso: python3 backtest/ciclicos_volta.py"""
import sys, pathlib
import pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import ciclicos as cy  # noqa: E402
from backtest import stats  # noqa: E402

A = {'Hotels, Resorts & Cruise Lines', 'Movies & Entertainment', 'Leisure Products', 'Health Care Distributors'}
B = {'Hotels, Resorts & Cruise Lines', 'Movies & Entertainment', 'Biotechnology', 'Automobile Manufacturers', 'Diversified Chemicals'}
base = cy.cyclical_industries()
f, dates = bm.base_data()
extra = {}
for lab, back in (('A: volta hotéis, entretenimento, brinquedos e distrib. de saúde', A), ('B: volta hotéis, entretenimento, biotec, montadoras e químicos', B)):
    c = bm.classify_new(f, cyc=base - back); h = bm.holdings_new(c)
    for nm in ('OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)', 'Cyclicals'):
        extra[f'{nm.replace(" (novo)", "")} — {lab[:1]}'] = (c, h[nm])
navs, n, dts, adj = bm.load_benchmarks(extra)
M = navs['S&P 500'].resample('ME').last()
def cell(k):
    s = navs[k].dropna(); Mn = s.resample('ME').last(); w = ((Mn / Mn.shift(60)) > (M / M.shift(60))).dropna().mean()
    return f"{stats(s)['CAGR']:.1%}".replace('.', ',') + f" ({w:.0%}; {n[k]:.0f} ações)"
out = ['# Devolvendo subsetores da lista de cíclicos (EUA, point-in-time)\n',
       '> ⚠️ **ROIC:** a régua de cíclicos usa o histórico completo do ROIC oficial (corrigido em 2026-11-10).\n',
       '**A** = pedido do usuário: hotéis/cruzeiros, entretenimento, brinquedos e distribuidoras de saúde voltam para a OoL/GCGR. '
       '**B** = os subsetores que renderam acima do universo como Cyclicals: hotéis/cruzeiros, entretenimento, biotecnologia, montadoras e químicos básicos. '
       'Atenção: as duas escolhas foram feitas olhando o retorno destes mesmos dados.\n',
       '## Comparativos obrigatórios + variantes\n'] + bm.bench_table(navs, n)
out += ['', '### Resumo (retorno anual; janelas de 5 anos acima do S&P; ações)\n', '| Carteira | Régua atual | A | B |', '|---|---|---|---|']
for nm, b in (('OoL novo', 'OoL novo'), ('GCGR novo', 'GCGR novo'), ('OoL High ROIC', 'OoL High ROIC (novo)'), ('OoL High Growth', 'OoL High Growth (novo)'), ('Cyclicals', 'Cyclicals')):
    out.append(f'| {nm} | {cell(b)} | {cell(nm + " — A")} | {cell(nm + " — B")} |')
(ROOT / 'ciclicos_volta.md').write_text('\n'.join(out)); print('\n'.join(out))
keep = bm.ORDER + [k for k in navs if k.startswith('OoL novo — ')]
bm.bench_plot({k: navs[k] for k in keep}, ROOT / 'ciclicos_volta.png', 'Comparativos obrigatórios + OoL novo devolvendo subsetores (A = pedido; B = os que renderam bem)')
