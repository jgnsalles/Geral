import gzip, base64, json, pathlib
W = pathlib.Path('/home/user/work/latam')
L = json.load(open(W / 'latam.json'))
D = {'gerado_em': L['gerado_em'], 'comb': json.load(open(W / 'comb.json')), 'fpe': L['fpe'], 'fus': L['fus'], 'f13': L['f13']}
for k in ('fpe',): D[k].pop('ids', None)
for k in ('fus', 'f13'): D[k].pop('ids', None)
D['f13']['fc'] = json.load(open(W / 'fora.json'))
raw = json.dumps(D, ensure_ascii=False, separators=(',', ':')).encode()
b64 = base64.b64encode(gzip.compress(raw, 9, mtime=0)).decode()
html = (W / 'src/app.html').read_text().replace('{{DATA}}', b64)
out = pathlib.Path('/tmp/claude-0/-home-user-Geral/fcac98de-4843-5238-88c1-7d682acd2098/scratchpad/latam/index.html'); out.write_text(html)
print('ok', len(raw) // 1024, 'KB de dados;', len(html) // 1024, 'KB de página')
