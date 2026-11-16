# EUA: posições e attribution dos fundos registrados nos EUA focados em América Latina (N-PORT).
# Cada fundo tem uma carteira por trimestre. Contribuição de cada ação entre duas carteiras = peso na carteira anterior × retorno
# da ação no intervalo (preço em US$ = valor ÷ quantidade, mediana entre todos os fundos com a ação na mesma data; desdobramentos
# corrigidos pela razão de quantidades). Retorno do fundo = retorno mensal da cota informado no N-PORT, encadeado.
import pandas as pd, numpy as np, glob, os, re, json
from fractions import Fraction
W = '/home/user/work/latam'
H, I = [], []
for f in sorted(glob.glob(W + '/nf/*.pkl')):
    d = pd.read_pickle(f); H.append(d['h']); I.append(d['info'])
H = pd.concat(H); I = pd.concat(I)
for c in ['NET_ASSETS'] + [x for x in I.columns if 'FLOW' in x]: I[c] = pd.to_numeric(I[c], errors='coerce')
I['rd'] = pd.to_datetime(I.REPORT_DATE, format='%d-%b-%Y', errors='coerce'); H['rd'] = pd.to_datetime(H.REPORT_DATE, format='%d-%b-%Y', errors='coerce')
I = I.sort_values(['SERIES_ID', 'rd', 'FILING_DATE']).drop_duplicates(['SERIES_ID', 'rd'], keep='last')       # 1 carteira por data
H = H[H.ACCESSION_NUMBER.isin(set(I.ACCESSION_NUMBER))]
H = H.merge(I[['ACCESSION_NUMBER', 'SERIES_ID', 'NET_ASSETS']], on='ACCESSION_NUMBER')
H['ym'] = H.rd.dt.strftime('%Y-%m'); I['ym'] = I.rd.dt.strftime('%Y-%m')
I = I.sort_values(['SERIES_ID', 'rd', 'FILING_DATE']).drop_duplicates(['SERIES_ID', 'ym'], keep='last')   # 1 carteira por mês
H = H[H.ACCESSION_NUMBER.isin(set(I.ACCESSION_NUMBER))]
H['usd'] = H.PERCENTAGE / 100 * H.NET_ASSETS
H['key'] = H['isin'].fillna('').where(H['isin'].fillna('') != '', H.ISSUER_CUSIP.fillna('') + '|' + H.ISSUER_NAME.fillna('').str.upper().str[:30])
EQ = H.ASSET_CAT.isin(['EC', 'EP']) & (H.PAYOFF_PROFILE != 'Short')
# ---- preços em US$ por título e mês: todos os fundos (base ampla de ações da LatAm + carteiras completas dos fundos LatAm)
P = []
for f in sorted(glob.glob(W + '/np2/*.pkl')):
    x = pd.read_pickle(f); x['ym'] = pd.to_datetime(x.REPORT_DATE, format='%d-%b-%Y', errors='coerce').dt.strftime('%Y-%m')
    x['key'] = x['isin'].fillna('').where(x['isin'].fillna('') != '', x.ISSUER_CUSIP.fillna('') + '|' + x.ISSUER_NAME.fillna('').str.upper().str[:30])
    x = x[(x.BALANCE > 0) & (x.usd > 0)]
    P.append(x[['key', 'ym', 'SERIES_ID', 'usd', 'BALANCE']])
y = H[EQ & (H.BALANCE > 0) & (H.usd > 0)][['key', 'ym', 'SERIES_ID', 'usd', 'BALANCE']]
P = pd.concat(P + [y]).drop_duplicates(['key', 'ym', 'SERIES_ID'])
P['px'] = P.usd / P.BALANCE
PX = P.groupby(['key', 'ym']).px.median()
QS = P.groupby(['key', 'ym', 'SERIES_ID']).BALANCE.sum()
SIMPLE = sorted({Fraction(a, b) for a in range(1, 11) for b in range(1, 11)} | {Fraction(x) for x in (15, 20, 25, 50, 100)} | {Fraction(1, x) for x in (15, 20, 25, 50, 100)})
def sret(key, m0, m1):
    a, b = PX.get((key, m0)), PX.get((key, m1))
    if a is None or b is None or not (a > 0 and b > 0): return np.nan
    ratio = b / a
    if abs(np.log(ratio)) > np.log(1.6):        # possível desdobramento: razão de quantidades entre os fundos com o título nas duas datas
        try:
            q0 = QS.loc[(key, m0)]; q1 = QS.loc[(key, m1)]; qq = (q1 / q0).dropna(); qq = qq[qq > 0]
            if len(qq):
                qm = float(qq.median()); f = min(SIMPLE, key=lambda c: abs(np.log(qm / float(c))))
                if abs(np.log(qm / float(f))) < 0.03 and abs(np.log(float(f))) > np.log(1.25) and abs(np.log(ratio * float(f))) < abs(np.log(ratio)): ratio *= float(f)
        except KeyError: pass
    return min(max(ratio - 1, -0.8), 3)
# ---- empresas: LEI ou nome normalizado
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'\b(S\.?A\.?B?\.?( DE C\.?V\.?)?|SA|SAB|DE CV|INC|LTD|ADR|SPONSORED|CORP|PN|ON|PREF|PFD|CLASS [A-Z]|CL [A-Z])\b|[-,./]', ' ', str(s).upper())).strip()[:40]
H['n2'] = H.ISSUER_NAME.map(norm)
lei = H[H.ISSUER_LEI.fillna('').str.len().eq(20)].groupby('key').ISSUER_LEI.agg(lambda x: x.mode().iloc[0])
H['emp'] = H.key.map(lei).fillna(H.n2)
H.loc[~EQ, 'emp'] = 'Outros ativos (caixa, títulos, derivativos)'
nome = H[EQ].groupby('emp').agg(n=('n2', lambda x: x.mode().iloc[0]), pais=('INVESTMENT_COUNTRY', lambda x: x.mode().iloc[0]))
# ---- retorno mensal de cada fundo
rets = {}
for r in I.itertuples():
    for k, col in enumerate(['MONTHLY_TOTAL_RETURN1', 'MONTHLY_TOTAL_RETURN2', 'MONTHLY_TOTAL_RETURN3']):
        v = getattr(r, col)
        if pd.notna(v): rets[(r.SERIES_ID, (r.rd - pd.offsets.MonthEnd(2 - k)).strftime('%Y-%m'))] = v / 100
out = {'fundos': {}, 'emp': {e: [x.n, x.pais] for e, x in nome.iterrows()}}
for sid, inf in I.groupby('SERIES_ID'):
    inf = inf.sort_values('rd'); dates = list(inf.ym)
    if len(dates) < 3: continue
    h = H[H.SERIES_ID == sid]
    W_ = h.groupby(['emp', 'ym']).PERCENTAGE.sum().unstack().reindex(columns=dates) / 100
    K_ = h.groupby(['key', 'emp', 'ym']).PERCENTAGE.sum().unstack().reindex(columns=dates) / 100
    # meses do fundo (retorno mensal), do 1º ao último mês com carteira
    m0, m1 = pd.Period(dates[0]), pd.Period(dates[-1]); months = [str(p) for p in pd.period_range(m0, m1, freq='M')]
    R = [rets.get((sid, m)) for m in months]
    C = {e: [None] * len(dates) for e in W_.index}; EXPL = [None] * len(dates); RF = [None] * len(dates)
    for j in range(1, len(dates)):
        a, b = dates[j - 1], dates[j]
        gap = [str(p) for p in pd.period_range(pd.Period(a) + 1, pd.Period(b), freq='M')]
        if len(gap) > 6: continue
        rf = [rets.get((sid, m)) for m in gap]
        RF[j] = float(np.prod([1 + x for x in rf]) - 1) if all(x is not None for x in rf) else None
        tot = 0.0
        for (key, e), w0 in K_[a].dropna().items():
            if e.startswith('Outros'): continue
            r_ = sret(key, a, b)
            if np.isnan(r_): continue
            C[e][j] = (C[e][j] or 0) + w0 * r_; tot += w0 * r_
        EXPL[j] = tot
    inf_last = inf.iloc[-1]
    flows = [(x.SALES_FLOW_MON1 or 0) + (x.SALES_FLOW_MON2 or 0) + (x.SALES_FLOW_MON3 or 0) + (x.REINVESTMENT_FLOW_MON1 or 0) + (x.REINVESTMENT_FLOW_MON2 or 0) + (x.REINVESTMENT_FLOW_MON3 or 0) - (x.REDEMPTION_FLOW_MON1 or 0) - (x.REDEMPTION_FLOW_MON2 or 0) - (x.REDEMPTION_FLOW_MON3 or 0) for x in inf.fillna(0).itertuples()]
    p = {}
    for e in W_.index:
        wv = [None if pd.isna(x) else int(round(x * 1e4)) for x in W_.loc[e]]
        cv = [None if x is None else int(round(x * 1e6)) for x in C.get(e, [None] * len(dates))]
        if max(abs(v or 0) for v in wv) < 5 and max(abs(v or 0) for v in cv) < 50: continue
        p[e] = [wv, cv]
    hl = h[h.ASSET_CAT.isin(['EC', 'EP']) & h.INVESTMENT_COUNTRY.isin(['BR', 'MX', 'CL', 'PE', 'CO', 'AR', 'UY', 'PA'])]
    mixp = hl.groupby(['ym', 'INVESTMENT_COUNTRY']).PERCENTAGE.sum().unstack().fillna(0); mixp = mixp.div(mixp.sum(axis=1), axis=0)
    br = float(mixp.get('BR', pd.Series(0, index=mixp.index)).median()) if len(mixp) else 0
    if br >= 0.7: continue                                          # fundos de Brasil ficam fora: só LatAm
    mix = mixp.iloc[-1].sort_values(ascending=False) if len(mixp) else pd.Series(dtype=float)
    out['fundos'][sid] = {'nome': inf_last.SERIES_NAME, 'reg': inf_last.REGISTRANT_NAME, 'datas': dates, 'meses': months, 'R': [None if x is None else round(x, 5) for x in R],
                          'RF': [None if x is None else round(x, 5) for x in RF], 'EX': [None if x is None else round(x, 5) for x in EXPL],
                          'NA': [round(x / 1e6, 1) for x in inf.NET_ASSETS], 'FL': [round(x / 1e6, 1) for x in flows], 'lat': [round(x, 1) for x in inf.lat_pct], 'mix': [[k, round(float(v), 3)] for k, v in mix.items() if v >= 0.03], 'p': p}
json.dump(out, open(W + '/us_attr.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for sid, f in sorted(out['fundos'].items(), key=lambda z: -z[1]['NA'][-1])[:20]:
    rf = [x for x in f['RF'] if x is not None]; ex = [x for x in f['EX'] if x is not None]
    print(f"{f['nome'][:40]:40} {f['datas'][0]}..{f['datas'][-1]} n={len(f['datas'])} NA={f['NA'][-1]:8.0f} fundo={np.prod([1+x for x in rf])-1:+.2f} explic={np.prod([1+x for x in ex])-1:+.2f}")
print('ok', len(out['fundos']), 'fundos', os.path.getsize(W + '/us_attr.json') // 1024, 'KB')
