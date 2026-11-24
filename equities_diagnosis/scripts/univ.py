"""Volume anual por ticker de ação (CODBDI 02, lote padrão) no COTAHIST, para montar o universo de empresas.
Uso: python3 univ.py <pasta COTAHIST> <saida.pkl>"""
import sys, os, glob, zipfile, collections
import pandas as pd
D, OUT = sys.argv[1:3]; rows = []
for z in sorted(glob.glob(os.path.join(D, 'COTAHIST_A*.ZIP'))):
    y = os.path.basename(z)[10:14]; vol = collections.Counter(); nd = collections.Counter(); spec = {}
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        for line in zf.open(n):
            if line[:2] != b'01' or line[10:12] != b'02' or line[24:27] != b'010': continue
            tk = line[12:24].decode('latin1').strip(); vol[tk] += int(line[170:188]) / 100; nd[tk] += 1
            spec[tk] = line[39:49].decode('latin1').strip()
    rows += [(y, t, v, nd[t], spec[t]) for t, v in vol.items()]
    print('ok', y, len(vol), flush=True)
pd.DataFrame(rows, columns=['ano', 'tk', 'vol', 'dias', 'espec']).to_pickle(OUT)
