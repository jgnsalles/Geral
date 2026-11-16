# Peru (SBS): ações locais nas carteiras das AFP, por emissor/ISIN, AFP e tipo de fundo. Mensal.
# Fonte: Boletim estatístico do SPP, quadro CA-0001 (abas "Inversión en acciones locales" em miles de soles e em unidades).
import glob, os, re, shutil, tempfile, pandas as pd, numpy as np
D = '/home/user/raw/latam/pe'; OUT = '/home/user/work/latam/pe_acoes.pkl'
MES = {'en': 1, 'fe': 2, 'ma': 3, 'ab': 4, 'my': 5, 'jn': 6, 'jl': 7, 'ag': 8, 'se': 9, 'oc': 10, 'no': 11, 'di': 12}
ISIN = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}\d$')
def sheets(f):
    head = open(f, 'rb').read(4)
    if head[:2] == b'PK':
        tmp = tempfile.mktemp(suffix='.xlsx'); shutil.copy(f, tmp)
        x = pd.read_excel(tmp, sheet_name=None, header=None, engine='openpyxl'); os.remove(tmp); return x
    return pd.read_excel(f, sheet_name=None, header=None, engine='xlrd')
def title(df):
    t = ' '.join(str(v) for v in df.iloc[:6].values.ravel() if isinstance(v, str))
    return t.upper()
def parse(df, units):
    # linha de cabeçalho: códigos AFP+tipo (ex.: HA01, IN02, PR03, RI00)
    hr = next(i for i in range(min(15, len(df))) if sum(bool(re.match(r'^[A-Z]{2}0[0-3]$', str(v))) for v in df.iloc[i]) >= 3)
    cols = {j: str(v) for j, v in enumerate(df.iloc[hr]) if re.match(r'^[A-Z]{2}0[0-3]$', str(v))}
    rows = []; labels = []; sector = ''; prev_isin = False
    for i in range(hr + 1, len(df)):
        r = df.iloc[i]; a = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ''
        if not a or a.lower().startswith('total'): continue
        if ISIN.match(a):
            if labels:                       # rótulos desde o último ISIN: [setor..., emissor]
                issuer = labels[-1]
                if len(labels) >= 2: sector = labels[-2]
                labels = []
            for j, code in cols.items():
                v = pd.to_numeric(r.iloc[j], errors='coerce')
                if pd.notna(v) and v != 0: rows.append((a, issuer, sector, code[:2], code[2:], float(v)))
            prev_isin = True
        else:
            labels.append(a); prev_isin = False
    return pd.DataFrame(rows, columns=['isin', 'emissor', 'setor', 'afp', 'fundo', 'v'])
out = []; TOT = []
for f in sorted(glob.glob(D + '/CA-0001-*.XLS')):
    m = re.search(r'CA-0001-([a-z]{2})(\d{4})', f); ym = f'{m.group(2)}-{MES[m.group(1)]:02d}'
    try: S = sheets(f)
    except Exception as e: print(ym, 'erro', e); continue
    val = qty = tot1 = None
    for n, df in S.items():
        t = title(df)
        if 'ACCIONES LOCALES' in t and 'UNIDADES' in t: qty = df
        elif 'ACCIONES LOCALES' in t: val = df
        elif 'CARTERA POR TIPO DE INSTRUMENTO Y SECTOR' in t and tot1 is None: tot1 = df
    if val is None: print(ym, 'sem aba de ações', list(S)[:15]); continue
    V = parse(val, False)
    if qty is not None:
        Q = parse(qty, True).rename(columns={'v': 'q'})[['isin', 'afp', 'fundo', 'q']]
        V = V.merge(Q, on=['isin', 'afp', 'fundo'], how='left')
    if tot1 is not None:     # patrimônio da carteira de cada fundo (linha TOTAL do quadro 1)
        hr = next(i for i in range(min(15, len(tot1))) if sum(bool(re.match(r'^[A-Z]{2}0[0-3]$', str(v))) for v in tot1.iloc[i]) >= 3)
        cols = {j: str(v) for j, v in enumerate(tot1.iloc[hr]) if re.match(r'^[A-Z]{2}0[0-3]$', str(v))}
        tr = [i for i in range(len(tot1)) if str(tot1.iloc[i, 0]).strip().upper() == 'TOTAL']
        if tr:
            r = tot1.iloc[tr[-1]]
            for j, c in cols.items():
                v = pd.to_numeric(r.iloc[j], errors='coerce')
                if pd.notna(v) and v > 0: TOT.append((ym, c[:2], c[2:], float(v)))
    V['ym'] = ym; out.append(V)
    print(ym, len(V), V.emissor.nunique(), round(V.v.sum() / 1e6, 2), 'bi soles')
A = pd.concat(out); A.to_pickle(OUT)
pd.DataFrame(TOT, columns=['ym', 'afp', 'fundo', 'tot']).to_pickle(OUT.replace('acoes', 'totais'))
print('totais', len(TOT))
