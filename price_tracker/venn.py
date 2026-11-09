"""Opportunity of Lifetime: Excel x Python metodo 1 (estimativas) x Python metodo 2 (historico).
Uso: python3 venn.py 2026-11-09"""
import sys
import pandas as pd
from compare import wise_baseline, TIERS

O = 'Opportunity of Lifetime'
SHORT = {'Good Companies, Great Returns': 'Good Co/Great Ret', 'Good but Margin of Safety Required': 'Good/Margin Safety',
         'Excellent but Fair': 'Excellent/Fair', 'Cheap Slow Compounder': 'Cheap Slow Comp',
         'Interesting but Requires Attention': 'Interesting/Attention', 'Cheap but Aggressive': 'Cheap Aggressive',
         'Expensive for what you get': 'Expensive for what', 'Investable but Not Good': 'Investable not Good',
         'Do not Waste Time': 'Do not Waste Time', 'Expensive': 'Expensive', O: '**OoL**'}

def main(day):
    w = wise_baseline().set_index('row')
    p1 = pd.read_csv(f'data/hybrid_{day}.csv').set_index('row')
    p2 = pd.read_csv(f'data/hist_{day}.csv').set_index('row')
    t = pd.DataFrame({'ticker': w.ticker, 'Excel': w.category, 'P1': p1.category.reindex(w.index), 'P2': p2.category.reindex(w.index)})
    t = t.drop_duplicates('ticker')
    e, a, b = t.Excel == O, t.P1 == O, t.P2 == O
    regions = [('Excel + P1 + P2', e & a & b), ('Excel + P1', e & a & ~b), ('Excel + P2', e & ~a & b),
               ('P1 + P2 (sem Excel)', ~e & a & b), ('So Excel', e & ~a & ~b), ('So P1 (estimativas)', ~e & a & ~b),
               ('So P2 (historico)', ~e & ~a & b)]
    out = [f'# Opportunity of Lifetime ({day})\n', f'Totais: Excel {e.sum()}, P1 {a.sum()}, P2 {b.sum()}\n']
    for name, m in regions:
        out.append(f'## {name} ({m.sum()})\n')
        if m.sum():
            x = t[m][['ticker', 'Excel', 'P1', 'P2']].copy()
            for c in ('Excel', 'P1', 'P2'): x[c] = x[c].map(SHORT)
            out.append(x.to_markdown(index=False) + '\n')
    open(f'report_ool_{day}.md', 'w').write('\n'.join(out))
    print('\n'.join(out))

if __name__ == '__main__':
    main(sys.argv[1])
