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
P = P[P.ym.isin(MI)]
# só long only: fora os long biased (nome, Anbima L/S Direcional ou classe Multimercado)
LB2 = r'LONG[ -]?BIAS|\bL\.?B\.?\b|LONG[ -]?SHORT|\bL/S\b|\bLS\b|BIASED'
import unicodedata
dea = lambda x: unicodedata.normalize('NFD', str(x or '')).encode('ascii', 'ignore').decode().upper()
acoes_now = F.nome.map(dea).str.contains(r'\bACOES\b|\bACAO\b')  # nome atual diz "ações": classe multimercado antiga não conta
lbx = F.nomes.fillna('').str.contains(LB2) | F.anbima.fillna('').str.contains('L/S|Multimercado') | (F.classe.fillna('').eq('Multimercado') & ~acoes_now)
P = P[~P.CNPJ_FUNDO.map(lbx).fillna(False).astype(bool)]
print('fundos long biased excluídos:', int(lbx.sum()))
prv = F.anbima.fillna('').str.contains('Previd')
P = P[~P.CNPJ_FUNDO.map(prv).fillna(False).astype(bool)]
# foco: Brasil (sem fundos de investimento no exterior) e LatAm (fundos com LatAm/América Latina no nome)
LA = r'LATAM|\bLATIN\b|AMERICA LATINA|LATINOAMERIC'
lax = F.nomes.fillna('').str.contains(LA)
P['la'] = P.CNPJ_FUNDO.map(lax).fillna(False).astype(bool)
# exterior pelo nome ATUAL (o histórico tem muita troca de mandato) ou Anbima atual
EXT = r'INVESTIMENTO NO EXTERIOR|\bIE\b|GLOBAL|OFFSHORE|\bUSD\b|INTERNACIONAL|INTERNATIONAL|WORLD|\bBDR\b'
extx = F.nome.map(dea).str.contains(EXT) | (F.anbima.fillna('').str.contains('Exterior') & ~F.nome.map(dea).str.contains('ACOES$|EM ACOES -|DE ACOES -'))
P['ext'] = P.CNPJ_FUNDO.map(extx).fillna(False).astype(bool)
# e pelo nome em vigor no mês (ex.: Arbor foi "Global Equities BDR" até 2023)
import zipfile as _z
_h = pd.read_csv(_z.ZipFile(os.path.join(os.path.dirname(os.path.abspath(OUT)), 'raw', 'cad_fi_hist.zip')).open('cad_fi_hist_denom_social.csv'), sep=';', encoding='latin1', dtype=str)
_h = _h[_h.CNPJ_FUNDO.isin(set(P.CNPJ_FUNDO)) & _h.DENOM_SOCIAL.map(dea).str.contains(EXT)]
_h['a'] = pd.to_datetime(_h.DT_INI_DENOM_SOCIAL, errors='coerce').dt.strftime('%Y-%m'); _h['b'] = pd.to_datetime(_h.DT_FIM_DENOM_SOCIAL, errors='coerce').dt.strftime('%Y-%m').fillna('2100-01')
_x = P[['CNPJ_FUNDO', 'ym']].reset_index().merge(_h[['CNPJ_FUNDO', 'a', 'b']], on='CNPJ_FUNDO')
_x = _x[(_x.ym >= _x.a) & (_x.ym < _x.b)]
P.loc[P.index.isin(_x['index']), 'ext'] = True
print('fundo-mês exterior pelo nome na data:', len(set(_x['index'])))
E0 = P[P.eleg & P.r.notna() & P.pl_ant.gt(0)].copy()
# erros de cota: fundo que se afasta mais de 40 p.p. do Ibovespa no mês fica fora daquele mês
E0 = E0[(E0.r - E0.ym.map(IX.ibov)).abs().le(0.40) | E0.ym.map(IX.ibov).isna()]
EL = E0[E0.la & ~E0.CNPJ_FUNDO.map(F.nome.map(dea).str.contains('TECHNOLOG|DISRUPT')).fillna(False).astype(bool)]  # ex-LatAm que mudou de mandato
E = E0[~E0.ext & ~E0.la & E0.gid.notna()]
P = P[P.gid.notna() & ~P.ext & ~P.la]

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
# fundos LatAm (qualquer gestora)
import zipfile, glob
RAW = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'raw')
zh = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
hg = pd.read_csv(zh.open('cad_fi_hist_gestor.csv'), sep=';', encoding='latin1', dtype=str)
gn = hg.dropna(subset=['GESTOR']).drop_duplicates('CPF_CNPJ_GESTOR', keep='last').set_index('CPF_CNPJ_GESTOR').GESTOR
gid2n = {g['id']: g['n'] for g in G}
out['la'] = []
for c, y in EL.groupby('CNPJ_FUNDO'):
    y = y.set_index('ym')
    if len(y) < 12 or y.pl.max() < 10e6:
        continue
    a, b = MI[y.index.min()], MI[y.index.max()]
    gc = y.CPF_CNPJ_GESTOR.iloc[-1]; gi = y.gid.iloc[-1]
    out['la'].append({'c': c, 'n': str(F.nome.get(c, '') or ''), 'g': ('Gama (Fundamenta LatAm)' if 'FUNDAMENTA' in str(F.nome.get(c, '')) else None) or gid2n.get(gi) or str(gn.get(gc, gc)).title().replace(' Ltda','').replace('.','')[:40], 'gid': gi if isinstance(gi, str) else None,
                      'o': a, 'r': series(y.r, a, b), 'pl': round(float(y.pl.iloc[-1]) / 1e6, 1)})
print('fundos LatAm:', [(f['n'][:40], f['g'], M[f['o']], f['pl']) for f in out['la']])
print('gestoras com série:', len(out['g']), 'de', len(G))
miss = [g['n'] for g in G if g['id'] not in out['g']]
print('sem série:', len(miss), miss[:60])
json.dump(out, open(DEST, 'w'), separators=(',', ':'), ensure_ascii=False)
print('bytes', os.path.getsize(DEST))
