"""Extrai do artefato "Navegando US" (dados embutidos no HTML, gzip+base64 no <script id="nbd">) as posições trimestrais dos 13F de cada gestor.
Saída: relatorio/data_13f/posicoes.csv.gz (trimestre, gestor, tipo, cusip6, ticker, valor US$ mi). Uso: python3 -I relatorio/extrai_13f.py <arquivo.html>"""
import sys, re, gzip, base64, json, csv, pathlib
src = sys.argv[1]
out = pathlib.Path(__file__).parent / 'data_13f' / 'posicoes.csv.gz'
s = open(src, encoding='utf-8').read()
m = re.search(r'<script id="nbd" type="text/plain">(.*?)</script>', s, re.S)
d = json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())))
fc = d['f13']['fc']; n = 0
with gzip.open(out, 'wt', newline='') as fo:
    w = csv.writer(fo); w.writerow(['trimestre', 'gestor', 'tipo', 'cusip6', 'ticker', 'valor'])
    for gid, f in d['f13']['fundos'].items():
        for cu, (vals, _) in f['p'].items():
            tk = fc.get(cu, ['', '', '', ''])[3] or ''
            for q, v in zip(f['datas'], vals):
                if v is not None and v > 0:
                    w.writerow([q, gid, f['tipo'], cu, tk, v]); n += 1
print('linhas', n, 'gestores', len(d['f13']['fundos']), 'gerado em', d['gerado_em'])
