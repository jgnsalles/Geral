"""Transforma as contas da CVM em uma tabela por empresa x exercicio x versao (com data de entrega).
Saida: data/fund.csv.gz"""
import pathlib, re
import numpy as np, pandas as pd

D = pathlib.Path(__file__).parent / 'data'

def lvl(c): return c.count('.')

def extract(g):
    g = g.assign(L=g.CD_CONTA.map(lvl))
    sc = np.where(g.ESCALA_MOEDA.eq('MIL'), 1000.0, 1.0)
    g = g.assign(V=g.VL_CONTA * sc)
    dre, bpa, bpp = g[g.ST == 'DRE'], g[g.ST == 'BPA'], g[g.ST == 'BPP']
    first = lambda df, m: df.loc[m, 'V'].iloc[0] if m.any() else np.nan
    d2 = dre[dre.L == 1]
    out = {}
    out['ebit'] = first(d2, d2.DS_CONTA.str.startswith('Resultado Antes do Resultado Financeiro'))
    out['pretax'] = first(d2, d2.DS_CONTA.str.startswith('Resultado Antes dos Tributos'))
    out['tax'] = first(d2, d2.DS_CONTA.str.startswith('Imposto de Renda e Contribui'))
    ni = first(dre, dre.DS_CONTA.str.startswith('Atribuído a Sócios da Empresa Controladora'))
    # 2026-11-11: algumas empresas preenchem a linha 'atribuido a controladora' com 0 (ex.: Sabesp 2023-2025); nesse caso usa o lucro
    # consolidado do periodo (3.11) menos a parte dos nao controladores
    tot = first(d2, d2.CD_CONTA.eq('3.11'))
    if not np.isnan(ni) and ni == 0 and not np.isnan(tot) and tot != 0:
        nc = first(dre, dre.DS_CONTA.str.startswith('Atribuído a Sócios Não Controladores'))
        ni = tot - (0.0 if np.isnan(nc) else nc)
    if np.isnan(ni):
        m = d2.DS_CONTA.str.contains('Lucro', case=False) & d2.DS_CONTA.str.contains('Período|Exercício', case=False) & ~d2.CD_CONTA.str.startswith('3.99')
        ni = d2.loc[m, 'V'].iloc[-1] if m.any() else np.nan
    out['ni'] = ni
    eps = dre[dre.CD_CONTA.str.startswith('3.99.01.')]
    out['eps_on'] = eps.loc[eps.DS_CONTA.str.strip().eq('ON'), 'VL_CONTA'].iloc[0] if eps.DS_CONTA.str.strip().eq('ON').any() else np.nan
    out['eps_pn'] = eps.loc[eps.DS_CONTA.str.strip().str.startswith('PN'), 'VL_CONTA'].iloc[0] if eps.DS_CONTA.str.strip().str.startswith('PN').any() else np.nan
    p2 = bpp[bpp.L == 1]
    out['equity'] = first(p2, p2.DS_CONTA.str.startswith('Patrimônio Líquido'))
    p3 = bpp[bpp.L == 2]
    out['debt'] = p3.loc[p3.DS_CONTA.str.strip().str.startswith('Empréstimos'), 'V'].sum()
    a3 = bpa[bpa.L == 2]
    a2 = bpa[bpa.L == 1]
    out['ppe'] = first(a3, a3.DS_CONTA.str.strip().eq('Imobilizado') & a3.CD_CONTA.str.startswith('1.02.'))
    out['ac'] = first(a2, a2.DS_CONTA.str.strip().str.startswith('Ativo Circulante'))
    out['cl'] = first(p2, p2.DS_CONTA.str.strip().str.startswith('Passivo Circulante'))
    out['debt_cur'] = p3.loc[p3.DS_CONTA.str.strip().str.startswith('Empréstimos') & p3.CD_CONTA.str.startswith('2.01.'), 'V'].sum()
    out['cash'] = a3.loc[a3.DS_CONTA.str.strip().isin(['Caixa e Equivalentes de Caixa', 'Aplicações Financeiras']) & a3.CD_CONTA.str.startswith('1.01.'), 'V'].sum()
    return pd.Series(out)

def main():
    f = pd.read_csv(D / 'cvm_facts.csv.gz', dtype={'CD_CVM': str, 'CD_CONTA': str})
    docs = pd.read_csv(D / 'cvm_docs.csv.gz', dtype={'CD_CVM': str})
    # consolidado quando existir naquela versao; senao individual
    has_con = f[f.GRP == 'con'].groupby(['CD_CVM', 'DT_REFER', 'VERSAO']).size().rename('n_con')
    f = f.merge(has_con, on=['CD_CVM', 'DT_REFER', 'VERSAO'], how='left')
    f = f[(f.GRP == 'con') | f.n_con.isna()]
    t = f.groupby(['CD_CVM', 'DT_REFER', 'VERSAO']).apply(extract).reset_index()
    t = t.merge(docs.drop_duplicates(['CD_CVM', 'DT_REFER', 'VERSAO']), on=['CD_CVM', 'DT_REFER', 'VERSAO'], how='left')
    t['CD_CVM'] = t.CD_CVM.astype(int)
    t.to_csv(D / 'fund.csv.gz', index=False)
    print(len(t), t.CD_CVM.nunique(), t.DT_RECEB.isna().sum())

if __name__ == '__main__':
    main()
