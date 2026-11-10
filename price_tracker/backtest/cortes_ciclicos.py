"""Teste de dois cortes de setores ciclicos pela metrica do usuario (variacao total do ROIC: media das variacoes absolutas ano contra ano / ROIC medio,
historico completo, mediana do subsetor): ciclico se >= 50% ou se >= 35%. Comparado com a regua anterior (queda media + colapsos).
Saidas: backtest/cortes_ciclicos.md, backtest/cortes_ciclicos.png
Uso: python3 backtest/cortes_ciclicos.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import ciclicos as cy  # noqa: E402
from backtest import D, stats  # noqa: E402

pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'


def main():
    e = pd.read_csv(D / 'ciclicos_empresas.csv', index_col=0)
    v = e[e.var_total.notna()]
    S = v.groupby('industry').var_total.median().sort_values(ascending=False)
    cuts = {'50%': set(S[S >= 0.50].index), '35%': set(S[S >= 0.35].index)}
    regua = cy.cyclical_industries()
    f, dates = bm.base_data()
    extra, C = {}, {}
    for k, cyc in [('corte 50%', cuts['50%']), ('corte 35%', cuts['35%'])]:
        c = bm.classify_new(f, cyc=cyc); h = bm.holdings_new(c); C[k] = (c, h)
        for nm in ('OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)', 'Cyclicals'):
            extra[f'{nm.replace(" (novo)", "")} — {k}'] = (c, h[nm])
    navs, n, dts, adj = bm.load_benchmarks(extra)
    out = ['# Dois cortes de setores cíclicos pela variação total do ROIC: 50% e 35% (EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** a variação total usa o histórico completo do ROIC oficial (corrigido em 2026-11-10); subsetores de capital pequeno ou '
           'que saíram de prejuízo ficam com a medida inflada. A classificação dos setores usa dados até 2025 (olha o futuro em relação a 2012).\n',
           '**Métrica (do usuário):** média das variações absolutas do ROIC ano contra ano ÷ ROIC médio, em todo o histórico; subsetor = mediana das empresas. '
           'Subsetor com variação ≥ corte = cíclico: sai da OoL e da GCGR e vai para a classe **Cyclicals**. Vestuário continua excluído nos dois cortes. '
           'As 9 linhas obrigatórias usam a régua anterior (queda média ≥ 30% e ≥ 2 colapsos); abaixo delas, os dois cortes novos.\n',
           f'**Corte 50%:** {len(cuts["50%"])} subsetores cíclicos. **Corte 35%:** {len(cuts["35%"])}. **Régua anterior:** {len(regua)}.\n',
           '## 1. Retornos\n'] + bm.bench_table(navs, n)
    # resumo compacto
    out += ['', '### Resumo (retorno anual; janelas de 5 anos acima do S&P)\n', '| Carteira | Régua anterior | Corte 50% | Corte 35% |', '|---|---|---|---|']
    M = navs['S&P 500'].resample('ME').last()
    def cell(k):
        s = navs[k].dropna(); Mn = s.resample('ME').last(); w = ((Mn / Mn.shift(60)) > (M / M.shift(60))).dropna().mean()
        return f"{stats(s)['CAGR']:.1%} ({w:.0%}; {n[k]:.0f} ações)".replace('.', ',', 1)
    for nm, base in (('OoL novo', 'OoL novo'), ('GCGR novo', 'GCGR novo'), ('OoL High ROIC', 'OoL High ROIC (novo)'), ('OoL High Growth', 'OoL High Growth (novo)'), ('Cyclicals', 'Cyclicals')):
        out.append(f'| {nm} | {cell(base)} | {cell(f"{nm} — corte 50%")} | {cell(f"{nm} — corte 35%")} |')
    out += [f"| *Referências* | S&P 500 {stats(navs['S&P 500'])['CAGR']:.1%}; S&P 500 EW {stats(navs['S&P 500 equal weight'])['CAGR']:.1%}; "
            f"OoL antigo {stats(navs['OoL antigo'])['CAGR']:.1%}; GCGR antigo {stats(navs['GCGR antigo'])['CAGR']:.1%} | | |".replace('.', ',')]
    # listas
    out += ['', '## 2. Subsetores cíclicos em cada corte\n', '| Subsetor | Variação total | Corte 50% | Corte 35% | Régua anterior |', '|---|---|---|---|---|']
    for ind, val in S[S >= 0.35].items():
        out.append(f"| {ind} | {pc(val)} | {'✔' if ind in cuts['50%'] else ''} | ✔ | {'✔' if ind in regua else ''} |")
    extra_r = sorted(regua - cuts['35%'])
    if extra_r: out.append(f"\nNa régua anterior mas abaixo de 35% na variação total: {', '.join(extra_r)}.")
    # quem sai da OoL
    out += ['', '## 3. Quem vai para Cyclicals (ações que seriam OoL ou GCGR), por corte\n']
    px = adj.reindex(pd.DatetimeIndex(dts), method='ffill'); fwd = px.shift(-1) / px - 1
    for k, (c, h) in C.items():
        cc = c.copy(); cc['rq'] = [fwd.at[d, t] for d, t in zip(cc.date, cc.ticker)]; cc = cc[cc.date < dts[-1]]
        uq = cc[cc.cat.notna()].groupby('date').rq.mean(); cc['ex'] = cc.rq - cc.date.map(uq)
        m = h['Cyclicals'].reindex(cc.index).fillna(False)
        a = cc[m].groupby('ticker').agg(q=('ex', 'size'), ex=('ex', 'mean'), ind=('industry', 'first')); a['ex'] *= 4
        out += [f'### {k}: {a.index.nunique()} empresas; excesso médio por posição {cc[m].ex.mean() * 4:+.1%}, mediano {cc[m].ex.median() * 4:+.1%}\n'.replace('.', ','),
                'Maiores perdas evitadas: ' + ', '.join(f'{t} ({r.ex:+.0%})' for t, r in a.sort_values('ex').head(10).iterrows()),
                '', 'Maiores ganhos perdidos: ' + ', '.join(f'{t} ({r.ex:+.0%})' for t, r in a.sort_values('ex', ascending=False).head(10).iterrows()), '']
    (ROOT / 'cortes_ciclicos.md').write_text('\n'.join(out))
    print('\n'.join(out))
    keep = bm.ORDER + [k for k in navs if '— corte' in k and k.split(' — ')[0] in ('OoL novo', 'Cyclicals')]
    bm.bench_plot({k: navs[k] for k in keep}, ROOT / 'cortes_ciclicos.png', 'Comparativos obrigatórios + OoL novo e Cyclicals com os cortes de 50% e 35% na variação total do ROIC')


if __name__ == '__main__':
    main()
