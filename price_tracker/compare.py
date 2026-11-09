"""Compara o modelo hibrido com o snapshot do Wisesheets (zROIC ja corrigido para V:AA).
Uso: python3 compare.py 2026-11-09"""
import sys
import numpy as np, pandas as pd
import engine

DIMS = ['growth', 'zgrowth', 'roic', 'zroic', 'ret']
TIERS = {'Opportunity of Lifetime': 'A', 'Good Companies, Great Returns': 'A', 'Excellent but Fair': 'A',
         'Good but Margin of Safety Required': 'B', 'Cheap Slow Compounder': 'B', 'Interesting but Requires Attention': 'B',
         'Cheap but Aggressive': 'B', 'Expensive for what you get': 'C', 'Investable but Not Good': 'C',
         'Expensive': 'C', 'Do not Waste Time': 'D'}


def wise_baseline():
    w = pd.read_csv('data/wise_snapshot.csv')
    for c in w.columns:
        if c not in ('ticker', 'name', 'sector', 'industry', 'category', 'fin'):
            w[c] = pd.to_numeric(w[c], errors='coerce')
    yrs = [f'roic{y}' for y in (2019, 2021, 2022, 2023, 2024, 2025)]
    w['zroic'] = [engine.cv(list(r), m) for r, m in zip(w[yrs].to_numpy(), w.roic)]  # correcao V:AA
    w = engine.classify(w.drop(columns=['category']))
    return w


def main(day):
    w = wise_baseline()
    h = pd.read_csv(f'data/hybrid_{day}.csv')
    m = w.merge(h, on='row', suffixes=('_w', '_h'))
    m['ticker'] = m.ticker_w
    m['tier_w'] = m.category_w.map(TIERS); m['tier_h'] = m.category_h.map(TIERS)
    lines = []
    p = lines.append
    n = len(m)
    p(f'# Hibrido x Wisesheets ({day}) - {n} linhas\n')
    p(f'- Mesma classe: {(m.category_w == m.category_h).sum()} ({(m.category_w == m.category_h).mean():.0%})')
    p(f'- Mesmo tier: {(m.tier_w == m.tier_h).sum()} ({(m.tier_w == m.tier_h).mean():.0%})')
    ow, oh = m.category_w == 'Opportunity of Lifetime', m.category_h == 'Opportunity of Lifetime'
    p(f'- Opportunity of Lifetime: Wise {ow.sum()}, hibrido {oh.sum()}, em comum {(ow & oh).sum()}')
    p(f'  - so Wise: {", ".join(m.ticker[ow & ~oh])}')
    p(f'  - so hibrido: {", ".join(m.ticker[oh & ~ow])}')
    aw, ah = m.tier_w == 'A', m.tier_h == 'A'
    p(f'- Tier A: Wise {aw.sum()}, hibrido {ah.sum()}, em comum {(aw & ah).sum()}\n')

    p('## Matriz de tiers (linhas = Wise, colunas = hibrido)\n')
    p(pd.crosstab(m.tier_w, m.tier_h, dropna=False).to_markdown() + '\n')

    p('## Concordancia por dimensao (letra do codigo)\n')
    p('| Dimensao | Letra igual | Erro mediano | Correlacao |\n|---|---|---|---|')
    for i, d in enumerate(DIMS):
        cw, ch = m.code_w.str[i], m.code_h.str[i]
        valid = m.code_w.notna() & m.code_h.notna()
        err = (m[f'{d}_h'] - m[f'{d}_w']).abs()
        corr = m[[f'{d}_w', f'{d}_h']].replace([np.inf, -np.inf], np.nan).dropna().corr(method='spearman').iloc[0, 1]
        p(f'| {d} | {(cw == ch)[valid].mean():.0%} | {err.median():.3f} | {corr:.2f} |')
    p(f'\nSem codigo no hibrido (dado faltando): {m.code_h.isna().sum()} linhas\n')

    p('## Maiores distorcoes por dimensao\n')
    for d in DIMS:
        x = m[['ticker', f'{d}_w', f'{d}_h']].copy()
        x['diff'] = x[f'{d}_h'] - x[f'{d}_w']
        x = x.replace([np.inf, -np.inf], np.nan).dropna().reindex(x['diff'].abs().sort_values(ascending=False).index).dropna().head(10)
        p(f'### {d}\n\n' + x.to_markdown(index=False, floatfmt='.3f') + '\n')

    flags = h[h['flags'].fillna('') != ''][['ticker', 'flags']]
    p(f'## Alertas de dados ({len(flags)})\n\n' + flags.to_markdown(index=False) + '\n')

    cols = ['ticker', 'category_w', 'category_h', 'code_w', 'code_h'] + [f'{d}_{s}' for d in DIMS for s in 'wh']
    m[cols].to_csv(f'data/compare_{day}.csv', index=False)
    open(f'report_{day}.md', 'w').write('\n'.join(lines))
    print('\n'.join(lines[:12]))


if __name__ == '__main__':
    main(sys.argv[1])
