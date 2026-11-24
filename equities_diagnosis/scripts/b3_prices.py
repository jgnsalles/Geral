"""Fechamentos diários (mercado à vista, lote padrão) do COTAHIST da B3 para os tickers pedidos.
Uso: python3 b3_prices.py <pasta com COTAHIST_A*.ZIP> <tickers.txt> <saida.pkl>"""
import sys, os, glob, zipfile
import pandas as pd
D, TL, OUT = sys.argv[1:4]
want = set(open(TL).read().split()); rows = []
for z in sorted(glob.glob(os.path.join(D, 'COTAHIST_A*.ZIP'))):
    try:
        zf = zipfile.ZipFile(z)
    except zipfile.BadZipFile:
        print('arquivo inválido', z, flush=True); continue
    for n in zf.namelist():
        for line in zf.open(n):
            if line[:2] != b'01' or line[24:27] not in (b'010', b'020'):  # 010 = vista, 020 = fracionário
                continue
            tk = line[12:24].decode('latin1').strip()
            if tk not in want:
                continue
            fat = int(line[210:217]) or 1
            rows.append((tk, line[2:10].decode(), int(line[108:121]) / 100 / fat, int(line[170:188]) / 100, line[24:27] == b'010'))
    print('ok', os.path.basename(z), flush=True)
B = pd.DataFrame(rows, columns=['tk', 'dt', 'close', 'vol', 'lote'])
# prefere o lote padrão; fracionário só quando não houve negócio no lote padrão
B = B.sort_values(['tk', 'dt', 'lote']).drop_duplicates(['tk', 'dt'], keep='last')
B['dt'] = pd.to_datetime(B.dt, format='%Y%m%d')
B.to_pickle(OUT); print(B.shape, B.tk.nunique())
