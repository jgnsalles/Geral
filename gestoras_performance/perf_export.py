"""Performance das gestoras do artefato Carteiras das Gestoras.

Entrada: saída de perf_base.py (fundo_mes.pkl, fundos_meta.csv, indices.csv) e gestoras_list.json.
Retorno da gestora no mês = média dos retornos de cota dos fundos elegíveis (classe Ações ou long biased, sem FIC,
exclusivo, previdência e indexado, na data), ponderada pelo PL do fim do mês anterior. Gestor do fundo na data.
Saída: perf.json para embutir no artefato.
Uso: python3 perf_export.py <out_dir> <gestoras_list.json> <ultimo_mes YYYY-MM> <perf.json>
"""
import sys, os, json
import pandas as pd, numpy as np

OUT, CJ, LAST, DEST = sys.argv[1:5]
P = pd.read_pickle(os.path.join(OUT, 'fundo_mes.pkl'))
F = pd.read_csv(os.path.join(OUT, 'fundos_meta.csv')).set_index('CNPJ_FUNDO')
IX = pd.read_csv(os.path.join(OUT, 'indices.csv'), index_col=0)
G = json.load(open(CJ))

M = [str(p) for p in pd.period_range('2005-01', LAST, freq='M')]
MI = {m: i for i, m in enumerate(M)}
P = P[P.ym.isin(MI) & P.gid.notna()]
E = P[P.eleg & P.r.notna() & P.pl_ant.gt(0)].copy()
# erros de cota: fundo que se afasta mais de 40 p.p. do Ibovespa no mês fica fora daquele mês
E = E[(E.r - E.ym.map(IX.ibov)).abs().le(0.40) | E.ym.map(IX.ibov).isna()]

def rint(v):  # retorno em centésimos de ponto-base (1e-6), inteiro, ou None
    return None if v is None or not np.isfinite(v) else int(round(v * 1e6))

def series(s, i0, i1):
    return [rint(s.get(M[i], np.nan)) for i in range(i0, i1 + 1)]

ib = IX.ibov.reindex(M); cdi = IX.cdi.reindex(M)
out = {'meses': M, 'ibov': [rint(v) for v in ib], 'cdi': [rint(v) for v in cdi], 'g': {}}

MIN_PL = 1e6
for g in G:
    x = E[E.gid == g['id']]
    if x.empty:
        continue
    agg = x.groupby('ym').apply(lambda d: pd.Series({'r': (d.r * d.pl_ant).sum() / d.pl_ant.sum(), 'w': d.pl_ant.sum(), 'n': d.CNPJ_FUNDO.nunique()}))
    agg = agg[agg.w >= MIN_PL]
    if agg.empty:
        continue
    pl = P[(P.gid == g['id']) & P.eleg].groupby('ym').pl.sum()
    i0, i1 = MI[agg.index.min()], MI[agg.index.max()]
    # fundos: os de maior PL médio (até 8), com série própria
    fs = x.groupby('CNPJ_FUNDO').agg(plm=('pl', 'mean'), plx=('pl', 'max'), a=('ym', 'min'), b=('ym', 'max'), n=('ym', 'size'))
    fs = fs[(fs.plx >= 10e6) & (fs.n >= 12)].sort_values('plm', ascending=False).head(8)
    funds = []
    for c, row in fs.iterrows():
        y = x[x.CNPJ_FUNDO == c].set_index('ym')
        a, b = MI[row.a], MI[row.b]
        plf = P[(P.CNPJ_FUNDO == c)].set_index('ym').pl
        nome = F.nome.get(c, '') if c in F.index else ''
        funds.append({'c': c, 'n': str(nome) if isinstance(nome, str) else '', 'o': a, 'r': series(y.r, a, b),
                      'pl': round(float(plf.get(row.b, np.nan)) / 1e6, 1) if np.isfinite(plf.get(row.b, np.nan)) else None,
                      'lb': bool(F.long_biased.get(c, False)) if c in F.index else False})
    out['g'][g['id']] = {'o': i0, 'r': series(agg.r, i0, i1),
                         'pl': [None if not np.isfinite(pl.get(M[i], np.nan)) else round(float(pl.get(M[i])) / 1e6, 1) for i in range(i0, i1 + 1)],
                         'nf': [int(agg.n.get(M[i])) if M[i] in agg.index else 0 for i in range(i0, i1 + 1)],
                         'f': funds}
print('gestoras com série:', len(out['g']), 'de', len(G))
miss = [g['n'] for g in G if g['id'] not in out['g']]
print('sem série:', len(miss), miss[:60])
json.dump(out, open(DEST, 'w'), separators=(',', ':'), ensure_ascii=False)
print('bytes', os.path.getsize(DEST))
