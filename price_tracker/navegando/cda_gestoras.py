"""Navegando Brasil robustecido, passo 1: CDA da CVM de TODOS os fundos, agregada por gestora e mês (2005-01 a 2026-09).
Gestor de cada fundo NA DATA (cad_fi_hist_gestor; reserva: cad_fi atual; classes da RCVM 175: registro_fundo_classe).
Fundos indexados/passivos ficam fora pelo nome (Ibovespa, IBrX, índice, ETF, passivo... salvo "ativo").
Fundos de fundos não entram porque só contam ações detidas diretamente (BLC_4) e no exterior (BLC_7).
t = ações, ações emprestadas, recibos e BDRs (BLC_4) + investimento no exterior (BLC_7), como em cw_update.py; c = o mesmo no CONFID (sigilo).
Saída: <RAW>/agg/{tot,hold}_<ano>.pkl.  Uso: python3 cda_gestoras.py <pasta com os zips da CVM> [anos...]"""
import sys, re, zipfile, glob, os, unicodedata
import pandas as pd, numpy as np

RAW = sys.argv[1]; YEARS = [int(y) for y in sys.argv[2:]] or list(range(2005, 2027))
OUT = os.path.join(RAW, 'agg'); os.makedirs(OUT, exist_ok=True)
EQ = ['Ações', 'Ações e outros TVM cedidos em empréstimo', 'Certificado ou recibo de depósito de valores mobiliários', 'Brazilian Depository Receipt - BDR']
EXT = 'Investimento no Exterior'
REN = {'CNPJ_FUNDO_CLASSE': 'CNPJ_FUNDO', 'TP_FUNDO_CLASSE': 'TP_FUNDO'}
deacc = lambda s: unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().upper()
IDX = re.compile(r'IBOVESPA|\bIBOV\b|IBRX|\bIBX\b|INDICE|INDEX|INDEXAD|PASSIV|\bETF\b|\bSMLL\b|\bIDIV\b|\bMSCI\b|S&P|\bSP ?500\b|NASDAQ|\bPIBB\b')
ACT = re.compile(r'ATIV[OA]|ACTIVE|ALPHA|PLUS')


def is_index(name):
    n = deacc(name)
    return bool(IDX.search(n)) and not ACT.search(n)


def gestor_map():
    z = zipfile.ZipFile(os.path.join(RAW, 'cad_fi_hist.zip'))
    h = pd.read_csv(z.open('cad_fi_hist_gestor.csv'), sep=';', encoding='latin1', dtype=str)
    h = h[h.PF_PJ_GESTOR == 'PJ'][['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'GESTOR', 'DT_INI_GESTOR', 'DT_FIM_GESTOR']].copy()
    h['ini'] = pd.to_datetime(h.DT_INI_GESTOR, errors='coerce'); h['fim'] = pd.to_datetime(h.DT_FIM_GESTOR, errors='coerce').fillna(pd.Timestamp('2100-01-01'))
    cad = pd.read_csv(os.path.join(RAW, 'cad_fi.csv'), sep=';', encoding='latin1', dtype=str)
    cad = cad[cad.PF_PJ_GESTOR == 'PJ'][['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'GESTOR']].dropna(subset=['CPF_CNPJ_GESTOR'])
    z = zipfile.ZipFile(os.path.join(RAW, 'registro_fundo_classe.zip'))
    rf = pd.read_csv(z.open('registro_fundo.csv'), sep=';', encoding='latin1', dtype=str)
    rc = pd.read_csv(z.open('registro_classe.csv'), sep=';', encoding='latin1', dtype=str)
    fmt = lambda c: f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if isinstance(c, str) and len(c) == 14 else c
    rf = rf[rf.Tipo_Pessoa_Gestor.fillna('PJ').str.upper().str.startswith('PJ') | rf.CPF_CNPJ_Gestor.fillna('').str.len().eq(14)]
    rf['g'] = rf.CPF_CNPJ_Gestor.fillna('').str.zfill(14).map(fmt)
    rcx = rc.merge(rf[['ID_Registro_Fundo', 'g', 'Gestor']], on='ID_Registro_Fundo')
    reg = pd.concat([rcx.assign(f=rcx.CNPJ_Classe.str.zfill(14).map(fmt))[['f', 'g', 'Gestor']],
                     rf.assign(f=rf.CNPJ_Fundo.str.zfill(14).map(fmt))[['f', 'g', 'Gestor']]]).drop_duplicates('f')
    reg.columns = ['CNPJ_FUNDO', 'CPF_CNPJ_GESTOR', 'GESTOR']
    names = pd.concat([h[['CPF_CNPJ_GESTOR', 'GESTOR']], cad[['CPF_CNPJ_GESTOR', 'GESTOR']], reg[['CPF_CNPJ_GESTOR', 'GESTOR']]]).dropna().drop_duplicates('CPF_CNPJ_GESTOR', keep='last')
    names.to_pickle(os.path.join(OUT, 'gestor_nomes.pkl'))
    return h, cad.set_index('CNPJ_FUNDO').CPF_CNPJ_GESTOR, reg.set_index('CNPJ_FUNDO').CPF_CNPJ_GESTOR


H, CAD, REG = gestor_map()
H_by = {f: g[['CPF_CNPJ_GESTOR', 'ini', 'fim']].values for f, g in H.groupby('CNPJ_FUNDO')}


def gestor_on(funds, d):
    """CNPJ do gestor de cada fundo na data d."""
    out = {}
    for f in funds:
        g = None
        iv = H_by.get(f)
        if iv is not None:
            ok = [x for x in iv if x[1] <= d <= x[2]]
            if ok: g = ok[-1][0]
        if g is None and d >= pd.Timestamp('2023-10-01'): g = REG.get(f)
        if g is None: g = CAD.get(f)
        if g is None: g = REG.get(f)
        out[f] = g
    return out


def read(zf, key, cols):
    out = []
    for n in [n for n in zf.namelist() if key in n and 'fiim' not in n and 'fie' not in n]:
        for c in pd.read_csv(zf.open(n), sep=';', encoding='latin1', dtype=str, chunksize=500000, quoting=3, on_bad_lines='skip'):
            c = c.rename(columns=REN)
            out.append(c[[x for x in cols if x in c.columns]])
    return pd.concat(out) if out else pd.DataFrame(columns=cols)


CC = {'USA': 'US', 'HKG': 'HK', 'JPN': 'JP', 'DEU': 'GR', 'CAN': 'CN', 'BEL': 'BB', 'GBR': 'LN', 'FRA': 'FP', 'NLD': 'NA', 'CHE': 'SW', 'CHN': 'CH', 'KOR': 'KS',
      'TWN': 'TT', 'ESP': 'SM', 'ITA': 'IM', 'MEX': 'MM', 'ARG': 'AR', 'CHL': 'CI', 'PER': 'PE', 'COL': 'CB', 'IND': 'IN', 'DNK': 'DC', 'SWE': 'SS', 'NOR': 'NO', 'IRL': 'ID', 'AUS': 'AU'}


def key_ext(tp, cd, pais, emissor):
    if tp in ('Depository Receipt no Exterior(DR)', 'Ação ordinária', 'Ação preferencial'):
        c = str(cd or '').strip().upper()
        m = re.match(r'^([A-Z0-9.\-/]{1,10})(?:\s+([A-Z]{2}))?(?:\s+EQUITY)?$', c)
        if m and not c.isdigit():
            return m.group(1).replace('/', '.') + '.' + (m.group(2) or CC.get(str(pais), 'US')), str(emissor or '').strip()
    return 'EXT.FUNDOS', ''


def process(zf, label):
    cols4 = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC', 'TP_APLIC', 'CD_ATIVO', 'DS_ATIVO', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']
    b4 = read(zf, 'BLC_4', cols4); b4 = b4[b4.TP_APLIC.isin(EQ)].copy()
    b4['key'] = b4.CD_ATIVO.fillna('').str.strip().str.upper(); b4['nm'] = b4.DS_ATIVO
    cols7 = ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC', 'TP_APLIC', 'TP_ATIVO', 'CD_ATIVO_BV_MERC', 'CD_PAIS', 'EMISSOR', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']
    b7 = read(zf, 'BLC_7', cols7); b7 = b7[b7.TP_APLIC == EXT].copy()
    if len(b7):
        kk = [key_ext(*x) for x in zip(b7.TP_ATIVO, b7.CD_ATIVO_BV_MERC, b7.CD_PAIS, b7.EMISSOR)]
        b7['key'] = [k for k, _ in kk]; b7['nm'] = [n for _, n in kk]
    X = pd.concat([b4[['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC', 'key', 'nm', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']],
                   b7[['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC', 'key', 'nm', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL']] if len(b7) else None])
    X['v'] = pd.to_numeric(X.VL_MERC_POS_FINAL, errors='coerce').fillna(0); X['q'] = pd.to_numeric(X.QT_POS_FINAL, errors='coerce').fillna(0)
    X = X[X.v > 0]; X['ym'] = X.DT_COMPTC.str[:7]
    cf = read(zf, '_CONFID_', ['CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_COMPTC', 'TP_APLIC', 'VL_MERC_POS_FINAL'])
    cf = cf[cf.TP_APLIC.isin(EQ + [EXT])].copy(); cf['v'] = pd.to_numeric(cf.VL_MERC_POS_FINAL, errors='coerce').fillna(0); cf['ym'] = cf.DT_COMPTC.str[:7]
    tots, holds = [], []
    for ym, x in X.groupby('ym'):
        d = pd.Timestamp(ym + '-28')
        fn = x.drop_duplicates('CNPJ_FUNDO').set_index('CNPJ_FUNDO').DENOM_SOCIAL
        idx = {f for f, n in fn.items() if is_index(n)}
        gm = gestor_on(fn.index, d)
        x = x[~x.CNPJ_FUNDO.isin(idx)].copy(); x['g'] = x.CNPJ_FUNDO.map(gm); x = x[x.g.notna()]
        c = cf[cf.ym == ym]; c = c[~c.CNPJ_FUNDO.isin(idx)].copy()
        if len(c):
            gmc = gestor_on(c.CNPJ_FUNDO.unique(), d); c['g'] = c.CNPJ_FUNDO.map(gmc); c = c[c.g.notna()]
        t = x.groupby('g').v.sum(); cc = c.groupby('g').v.sum() if len(c) else pd.Series(dtype=float)
        nf = x.groupby('g').CNPJ_FUNDO.nunique()
        tt = pd.DataFrame({'t': t, 'c': cc, 'nf': nf}).fillna(0); tt['ym'] = ym; tots.append(tt.reset_index().rename(columns={'index': 'g'}))
        hh = x[x.key != ''].groupby(['g', 'key']).agg(v=('v', 'sum'), q=('q', 'sum'), nm=('nm', 'first')).reset_index(); hh['ym'] = ym; holds.append(hh)
        sem = x[x.key == ''].groupby('g').v.sum()
        print(label, ym, 'fundos', len(fn), 'indexados fora', len(idx), 'gestoras', len(t), 'R$ bi', round(t.sum() / 1e9, 1), 'sem código', round(sem.sum() / 1e9, 2), flush=True)
    return pd.concat(tots), pd.concat(holds)


for y in YEARS:
    files = [os.path.join(RAW, f'cda_fi_{y}.zip')] if os.path.exists(os.path.join(RAW, f'cda_fi_{y}.zip')) else sorted(glob.glob(os.path.join(RAW, f'cda_fi_{y}[01][0-9].zip')))
    T, Hh = [], []
    for f in files:
        try: zf = zipfile.ZipFile(f)
        except zipfile.BadZipFile: print('zip ruim', f); continue
        t, h = process(zf, os.path.basename(f)); T.append(t); Hh.append(h)
    if T:
        pd.concat(T).to_pickle(os.path.join(OUT, f'tot_{y}.pkl')); pd.concat(Hh).to_pickle(os.path.join(OUT, f'hold_{y}.pkl'))
