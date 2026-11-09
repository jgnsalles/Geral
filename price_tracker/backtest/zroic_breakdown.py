"""EUA: desempenho por nivel de zROIC em Good Companies, Great Returns e nas excluidas de OoL por ROIC medio;
no zROIC alto, separa pelo ROIC marginal de 5 anos (vs mediana do grupo e vs ROIC da propria empresa).
Uso: python3 backtest/zroic_breakdown.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import diag_two_countries as dg  # noqa: E402

pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
nm = lambda x: '—' if pd.isna(x) else f'{x:.1f}'.replace('.', ',')


def perf(x, univ):
    """Retorno medio anualizado das posicoes, excesso sobre o universo no mesmo trimestre, t (por trimestre), % negativas."""
    if x.empty: return dict(n=0)
    x = x.assign(ex=x.rq - x.date.map(univ))
    q = x.groupby('date').ex.mean()
    t = q.mean() / q.std() * np.sqrt(len(q)) if len(q) > 2 and q.std() > 0 else np.nan
    return dict(n=len(x), empresas=x.ticker.nunique(), ret=x.rq.mean() * 4, ex=x.ex.mean() * 4, t=t, neg=(x.rq < 0).mean(),
                roic=x.roic.median(), marg=x.roic_marg.median())


def row(label, p):
    if p.get('n', 0) == 0: return f'| {label} | 0 | | | | | | | |'
    return (f"| {label} | {p['n']} | {p['empresas']} | {pc(p['ret'])} | **{sg(p['ex'])}** | {nm(p['t'])} | {pc(p['neg'])} | "
            f"{pc(p['roic'])} | {pc(p['marg'])} |")


def main():
    c, adj = dg.us(); c = dg.enrich(c, adj)
    univ = c[c.cat.notna()].groupby('date').rq.mean()
    g = c[c.cat == dg.GCGR].copy()
    g['flaw'] = g.code.map(lambda s: next((i for i in range(4) if s[i] != 'HOGNG'[i]), None))
    groups = {'Good Companies, Great Returns (todas)': g, 'Excluídas de OoL por ROIC médio': g[g.flaw == 2],
              'Opportunity of Lifetime (referência)': c[c.cat == dg.OOL]}
    hdr = ['| Faixa | Posições | Empresas | Retorno a.a. | vs Universo | t | % negativas | ROIC (mediana) | ROIC marginal (mediana) |',
           '|---|---|---|---|---|---|---|---|---|']
    out = ['# EUA: desempenho por zROIC e ROIC marginal\n',
           '> ⚠️ **ROIC:** análise sobre estabilidade do ROIC e ROIC marginal; há problemas de dado conhecidos (ex.: Copart, Deere).\n',
           'Cenário-base (g 7%, ROIC 20%/10%, zGrowth 2,93), 2012–2026. Unidade = posição (ação × trimestre na classe). '
           'Retorno = média do retorno trimestral seguinte, anualizado; excesso = sobre a média do universo no mesmo trimestre. '
           'ROIC marginal de 5 anos = ΔNOPAT ÷ Δcapital investido (só quando o capital cresceu).\n']
    bins = [-np.inf, 0.15, 0.3, 0.5, 0.7, np.inf]
    labels = ['< 0,15', '0,15–0,30', '0,30–0,50', '0,50–0,70', '≥ 0,70 (instável)']
    for name, x in groups.items():
        out += [f'## {name}\n', '### Por faixa de zROIC\n'] + hdr
        out.append(row('**Todas**', perf(x, univ)))
        for lb, (lo, hi) in zip(labels, zip(bins[:-1], bins[1:])):
            out.append(row(lb, perf(x[(x.zroic >= lo) & (x.zroic < hi)], univ)))
        hi_cut = x.zroic.quantile(2 / 3)
        top = x[x.zroic >= hi_cut]
        med = x.roic_marg.median()
        out += ['', f'### zROIC alto (terço mais instável do grupo: zROIC ≥ {nm(hi_cut) if hi_cut >= 0.1 else f"{hi_cut:.2f}".replace(".", ",")}) por ROIC marginal\n'] + hdr
        out.append(row('**zROIC alto (todas)**', perf(top, univ)))
        out.append(row(f'ROIC marginal acima da mediana do grupo ({pc(med)})', perf(top[top.roic_marg > med], univ)))
        out.append(row('ROIC marginal abaixo da mediana do grupo', perf(top[top.roic_marg <= med], univ)))
        out.append(row('ROIC marginal acima do ROIC da empresa (melhora)', perf(top[top.roic_marg > top.roic], univ)))
        out.append(row('ROIC marginal abaixo do ROIC da empresa (piora)', perf(top[top.roic_marg <= top.roic], univ)))
        out.append(row('Sem ROIC marginal (capital não cresceu em 5 anos)', perf(top[top.roic_marg.isna()], univ)))
        low = x[x.zroic < hi_cut]
        out += ['', '### Para comparar: zROIC baixo/médio (dois terços mais estáveis) por ROIC marginal\n'] + hdr
        out.append(row('ROIC marginal acima do ROIC da empresa (melhora)', perf(low[low.roic_marg > low.roic], univ)))
        out.append(row('ROIC marginal abaixo do ROIC da empresa (piora)', perf(low[low.roic_marg <= low.roic], univ)))
        out.append('')
    (ROOT / 'zroic_breakdown.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
