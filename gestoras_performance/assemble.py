"""Monta o novo HTML do artefato Carteiras das Gestoras com a aba Performance.
Uso: python3 assemble.py <html_original> <perf.json> <perf_section.html> <perf_js.js> <saida.html>
"""
import sys
SRC, PJ, SEC, JS, DEST = sys.argv[1:6]
h = open(SRC, encoding='utf-8').read()
perf = open(PJ, encoding='utf-8').read()
sec = open(SEC, encoding='utf-8').read()
js = open(JS, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (old[:80], h.count(old))
    h = h.replace(old, new)

# aba
rep('<button role="tab" id="t-e" aria-selected="false" data-v="e">Ação</button>',
    '<button role="tab" id="t-e" aria-selected="false" data-v="e">Ação</button>\n    <button role="tab" id="t-p" aria-selected="false" data-v="p">Performance</button>')
# seção nova antes do rodapé
rep('<p class="note" id="foot"></p>', sec + '\n<p class="note" id="foot"></p>')
# bloco na página da gestora
rep('<div class="kpis" id="g-kpis"></div>', '<div class="kpis" id="g-kpis"></div>\n  <div class="card" id="g-perf"></div>')
# dados
rep('<script>\nconst D=', '<script>\nconst PF=' + perf + ';\nconst D=')
# render da gestora chama o bloco de performance
rep("    ['5 maiores', pct(cur.slice(0,5).reduce((s,o)=>s+o.w,0),0), cur[0]?`maior: ${cur[0].r} (${pct(cur[0].w,1)})`:'–'],\n  ]);",
    "    ['5 maiores', pct(cur.slice(0,5).reduce((s,o)=>s+o.w,0),0), cur[0]?`maior: ${cur[0].r} (${pct(cur[0].w,1)})`:'–'],\n  ]);\n  renderGP(g);")
# navegação
rep('// ---------- navegação', js + '\n// ---------- navegação')
rep("function setView(v){ S.view=v; ['r','g','e'].forEach(", "function setView(v){ S.view=v; ['r','g','e','p'].forEach(")
rep("const h=v==='g'?`#g-${S.g}`:v==='e'?`#a-${S.e}`:'#resumo';", "const h=v==='g'?`#g-${S.g}`:v==='e'?`#a-${S.e}`:v==='p'?'#performance':'#resumo';")
rep("function render(){ if(S.view==='g') renderG(); else if(S.view==='e') renderE(); else renderR(); }",
    "function render(){ if(S.view==='g') renderG(); else if(S.view==='e') renderE(); else if(S.view==='p') renderP(); else renderR(); }")
rep("  if(h==='resumo'){ setView('r'); renderR(); return true; } return false; }",
    "  if(h==='resumo'){ setView('r'); renderR(); return true; }\n  if(h==='performance'){ setView('p'); renderP(); return true; } return false; }")
rep('<meta name="description" content="Evolução das maiores posições em ações das gestoras independentes, a partir da CDA da CVM">',
    '<meta name="description" content="Evolução das maiores posições em ações e rentabilidade dos fundos de ações das gestoras independentes, a partir da CDA e do Informe Diário da CVM">')
open(DEST, 'w', encoding='utf-8').write(h)
print('ok', len(h))
# tira o esqueleto que o serviço acrescenta na publicação
pre = '<body>\n'
i = h.find(pre)
if h.startswith('<!doctype html><html><head><meta charset=utf8>') and i > 0:
    h = h[i + len(pre):]
if h.rstrip().endswith('</body></html>'):
    h = h.rstrip()[:-len('</body></html>')] + '\n'
open(DEST, 'w', encoding='utf-8').write(h)
print('sem esqueleto', len(h), h[:60].replace('\n', ' '))
