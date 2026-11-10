"""Monta o Navegando Brasil (artifact multi-arquivo): index.html + data/*.

Fontes: template do Navegando Dilma 2 v2 (CSS, HTML das seções, módulo de gráficos),
HTML do Carteiras das Gestoras (dados consolidados por gestora) e src/*.
"""
import re, pathlib, shutil, json
H = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('/home/user/jgnsalles/gestoras')
TPL = (REPO / 'output/artifact/navegando_dilma_2_v2.template.html').read_text().split('\n')
CSV = pathlib.Path(__import__('os').environ.get('CSV', str(REPO / 'output/dashboard')))
import csv
END = max(r['ym'] for r in csv.DictReader(open(CSV / 'serie_mensal.csv')))   # último mês da série de performance
MES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
END_L = MES[int(END[5:]) - 1] + '/' + END[:4]
src = lambda n: (H / 'src' / n).read_text().replace('{{END}}', END).replace('{{END_L}}', END_L)

head = TPL[:175]   # até antes de </style></head>
assert TPL[175].startswith('</style></head>'), TPL[175]
head = '\n'.join(head).replace('<title>Navegando Dilma 2 v2</title>', '<title>Navegando Brasil</title>')

body = src('body.html')
def nav(m):
    a, b = int(m.group(1)), int(m.group(2))
    return '\n'.join(TPL[a - 1:b])
body = re.sub(r'\{\{NAV:(\d+)-(\d+)\}\}', nav, body)
body = body.replace('<button class="rx-btn rx-go-cartas" type="button">Ver cartas da gestora</button>', '')
body = body.replace('<div class="rx">', '<div class="rx"><p id="nb-loading">Carregando…</p>', 1)
# textos do Navegando que citavam o recorte 2014-2018 ou a aba Ciclo
body = body.replace('Toque para ver no Ciclo.', 'Toque para abrir a empresa.')
body = body.replace('<p class="rx-note">Viés de sobrevivência: a lista acima só tem fundos que chegaram a 2018.', '<p class="rx-note">Viés de sobrevivência: a lista dos 30 só tem fundos que chegaram a 2018.')

d3 = TPL[506] + '\n' + TPL[507] + '\n' + TPL[508]
assert TPL[506].startswith('<script>// https://d3js.org'), TPL[506][:40]

js_lines = TPL[529:1861]          # módulos do Navegando (com <script> ... </script>)
js = '\n'.join(js_lines)
js = js.replace("const DEF = { fundo: '1', inicio: '2013-12', fim: '2018-12', pg: 'ciclo', aba: 'perf', emp: 'ano' };",
                "const DEF = { fundo: '1', inicio: '2012-01', fim: '" + END + "', pg: 'hoje', aba: 'perf', emp: 'ano' };")
assert "inicio: '2012-01', fim: '" + END in js
old_bub = "on('click', (ev, r) => { dash.setParams({ pg: 'ciclo', cTk: r.tk }); go('cy-acao-card'); });"
assert old_bub in js
js = js.replace(old_bub, "on('click', (ev, r) => { dash.setParams({ pg: 'empresa', er: NB_cwRoot(r.tk) }); go('topo'); });")
# acréscimos dentro do 1º módulo (antes do fechamento do IIFE)
marker = "\n})();\n</script>\n<script>\n(() => {"
assert js.count(marker) == 1
js = js.replace(marker, '\n' + src('inject.js') + marker)

css_extra = src('extra.css')
fw = src('framework.js'); glue = src('glue.js')
html = (head + '\n' + css_extra + '\n</style></head>\n' + body + '\n' + d3 + '\n' + fw + '\n' + js + '\n<script>\n' + src('cw.js') + '\n</script>\n<script>\n' + glue + '\n</script>\n</body></html>\n')
out = H / 'dist'; (out / 'data').mkdir(parents=True, exist_ok=True)
(out / 'index.html').write_text(html)
for n in ['fundos', 'serie_mensal', 'posicoes_1', 'posicoes_2', 'precos', 'acoes', 'ibov', 'encerrados']:
    shutil.copy(CSV / (n + '.csv'), out / 'data' / (n + '.csv'))
shutil.copy(H / 'data/carteiras.json', out / 'data/carteiras.json')
# divide arquivos grandes em partes de até 1 MB (o app do iPhone não entrega arquivos grandes inteiros)
LIM = 1_000_000; parts = {}
for f in sorted((out / 'data').iterdir()):
    if f.suffix == '.txt': f.unlink(); continue
for f in sorted((out / 'data').iterdir()):
    t = f.read_text()
    if len(t.encode()) <= LIM: continue
    chunks, cur, size = [], [], 0
    for line in t.splitlines(keepends=True):
        b = len(line.encode())
        if size + b > LIM and cur: chunks.append(''.join(cur)); cur, size = [], 0
        if b > LIM:
            for i in range(0, len(line), 900_000): chunks.append(line[i:i + 900_000])
            continue
        cur.append(line); size += b
    if cur: chunks.append(''.join(cur))
    assert ''.join(chunks) == t
    for k, c in enumerate(chunks): (out / 'data' / f'{f.name}.{k + 1}.txt').write_text(c)
    parts[f.name] = len(chunks); f.unlink()
html = html.replace('{{PARTS}}', json.dumps(parts))
(out / 'index.html').write_text(html)
print('partes', parts)
print('ok', len(html), sum(p.stat().st_size for p in (out / 'data').iterdir()))
