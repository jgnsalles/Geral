import gzip, base64, pathlib
W = pathlib.Path('/home/user/work/latam')
b64 = base64.b64encode(gzip.compress((W / 'latam.json').read_bytes(), 9, mtime=0)).decode()
html = (W / 'src/page.html').read_text().replace('{{DATA}}', b64)
out = pathlib.Path('/tmp/claude-0/-home-user-Geral/fcac98de-4843-5238-88c1-7d682acd2098/scratchpad/latam/index.html'); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html); print('ok', len(html) // 1024, 'KB')
