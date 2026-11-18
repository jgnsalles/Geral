"""Navegando Brasil robustecido, passo 3: coloca o carteiras.json novo na página e o seletor "lista original / robustecida".
Uso: python3 patch_br.py <index.html> <carteiras_novo.json> <index_saida.html> [cw.js body.html (cópias em fonte/, editadas no lugar)]"""
import sys, gzip, base64, re
IDX, JS, OUT = sys.argv[1:4]; EXTRA = sys.argv[4:]
SEL = ('<label>Gestoras <select id="lst"><option value="rb" selected>100 maiores de cada mês + lista original</option>'
       '<option value="orig">só a lista original</option></select></label>\n      ')
REP = [
    ("const ok=(g,i)=>{", "const LST=()=>{ const e=$('lst'); return e?e.value:'rb'; };\nconst ok=(g,i)=>{ if(g.rb&&LST()==='orig') return false;"),
    ("if(g.man) chips.push(", "if(g.rb) chips.push('<span class=\"cw-chip\">entre as 100 maiores do mês (lista robustecida)</span>'); if(g.man) chips.push("),
    ("['lim','covmin'].forEach(id=>", "['lim','covmin','lst'].forEach(id=>"),
    ('<label>Carteira revelada mínima', SEL + '<label>Carteira revelada mínima'),
    ('<p><b>Carteira confidencial.</b>', '<p><b>Lista robustecida.</b> Além das gestoras independentes da lista original, entram as 100 maiores gestoras ativas de ações de cada mês, '
     'com o ranking refeito em cada data pelo patrimônio em ações daquela data (CDA da CVM de todos os fundos, gestor na data). Fora: fundos indexados, '
     'fundos de fundos e gestoras de bancos, seguradoras, previdência e corretoras. Cada gestora adicionada só aparece nos meses em que estava entre as 100 maiores: '
     'quem fechou ou encolheu continua nos meses antigos, e quem só cresceu depois não entra no passado. O seletor "Gestoras", em Hoje, volta à lista original.</p>\n      '
     '<p><b>Carteira confidencial.</b>'),
]


def patch(s, reps):
    for a, b in reps:
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    return s


s = open(IDX).read()
s = patch(s, REP)
b64 = base64.b64encode(gzip.compress(open(JS, 'rb').read(), 9, mtime=0)).decode()
s, n = re.subn(r'(<script type="text/plain" id="nbd-carteiras\.json">)[^<]*(</script>)', lambda m: m.group(1) + b64 + m.group(2), s)
assert n == 1
open(OUT, 'w').write(s)
for f in EXTRA:
    t = open(f).read()
    t = patch(t, [r for r in REP if r[0] in t])
    open(f, 'w').write(t)
print('ok', len(s) // 1024, 'KB')
