"""Navegando Brasil sem viés de seleção, passo 3: coloca na página o universo por regra (padrão), os selos "dead in AAAA" /
"fora do top 100 desde AAAA" e a seção dos fundos por regra. Parte da página já publicada (robustecida pelo patch_br.py).
Uso: python3 patch_sv.py <index.html publicado> <carteiras_sv.json> <fundos_regra_br.csv> <fundos_regra_ano_br.csv> <saida.html> [cw.js glue.js body.html]"""
import sys, gzip, base64, re, json, html
import pandas as pd
IDX, JS, FCSV, ACSV, OUT = sys.argv[1:6]; EXTRA = sys.argv[6:]
REP = [
    ("const ok=(g,i)=>{ if(g.rb&&LST()==='orig') return false;",
     "let ONE=null; const inTP=(g,i)=>!g.tp||g.tp.some(r=>i>=r[0]&&i<=r[1]);\n"
     "const DB=g=>g.dead?` <span class=\"cw-chip dead\">dead in ${g.dead}</span>`:'';\n"
     "const ok=(g,i)=>{ if(ONE!==g.id){ if(LST()==='orig'){ if(g.rb) return false; } else if(!inTP(g,i)) return false; }"),
    ("  const g=GI[S.g]; const box=$('g-casa'), none=$('g-casa-none');", "  const g=GI[S.g]; ONE=g?g.id:null; const box=$('g-casa'), none=$('g-casa-none');"),
    ("function renderR(){", "function renderR(){ ONE=null;"),
    ("function renderE(){", "function renderE(){ ONE=null;"),
    ("const chips=[]; if(g.rb) chips.push('<span class=\"cw-chip\">entre as 100 maiores do mês (lista robustecida)</span>');",
     "const chips=[]; if(g.dead) chips.push(`<span class=\"cw-chip dead\">dead in ${g.dead}</span>`);"
     " if(g.fora>0) chips.push(`<span class=\"cw-chip\">fora do top 100 desde ${g.fora}</span>`);"
     " if(g.fora===-1) chips.push('<span class=\"cw-chip\">nunca entre as 100 maiores (só na lista original)</span>');"
     " if(g.rb) chips.push('<span class=\"cw-chip\">entrou pela regra (100 maiores do mês)</span>');"),
    ("L(esc(o.g.n))}", "L(esc(o.g.n)+DB(o.g))}"),
    ("f:o=>L(esc(o.g.n)+(H.hasFunds(o.g.id)", "f:o=>L(esc(o.g.n)+DB(o.g)+(H.hasFunds(o.g.id)"),
    ("GBY[g.id] = { id: g.id, n: g.n, rs: g.rs, funds: [] };", "GBY[g.id] = { id: g.id, n: g.n, rs: g.rs, dead: g.dead, funds: [] };"),
    ("${g.funds.length ? 'com performance · ' : ''}${esc(g.rs)}</option>", "${g.funds.length ? 'com performance · ' : ''}${esc(g.rs)}${g.dead ? ' · dead in ' + g.dead : ''}</option>"),
    ('<option value="rb" selected>100 maiores de cada mês + lista original</option><option value="orig">só a lista original</option>',
     '<option value="rb" selected>100 maiores de cada mês (regra, sem viés)</option><option value="orig">só a lista original (escolhida hoje)</option>'),
    ('<h2 class="rx-sec">Visão de mercado: os 30 fundos no período</h2>', '__SV__<h2 class="rx-sec">Visão de mercado: os 30 fundos selecionados no período</h2>'),
    ('<h2 class="rx-sec">Os 30 fundos no período</h2>', '<h2 class="rx-sec">Os 30 fundos selecionados no período</h2>'),
]
METH_OLD = re.compile(r'<p><b>Lista robustecida\.</b>.*?</p>', re.S)
METH_NEW = ('<p><b>Sem viés de seleção.</b> O universo padrão é só a regra: em cada mês, as 100 maiores gestoras ativas de ações daquele mês, '
            'pelo patrimônio em ações da data (CDA da CVM de todos os fundos, gestor na data), incluindo as que fecharam depois. Fora: fundos indexados, fundos de fundos, '
            'gestoras de bancos, seguradoras, previdência e corretoras, e casas com uma ação acima de 50% da carteira. Uma gestora só conta nos meses em que estava entre as 100. '
            'A lista original (158 casas escolhidas hoje, entre sobreviventes) virou filtro opcional em "Gestoras". '
            '<b>dead in AAAA</b> = a gestora (ou o fundo) parou de aparecer na CVM naquele ano; quem só encolheu leva "fora do top 100 desde AAAA". '
            'Os 30 fundos com attribution continuam como estavam (seleção de 2014/2018); a seção "Todos os fundos de ações das 100 maiores" mostra o desempenho sem viés, '
            'por regra: em cada ano, os fundos de ações (sem FIC, indexados, previdência e exclusivos) das 100 maiores gestoras com PL ≥ R$ 100 mi no fim do ano anterior, '
            'contados até a última cota, inclusive os que encerraram.</p>')
CSS = '.cw-chip.dead { color: #9b3b3b; border-color: #c98f8f; }\n'


def patch(s, reps, strict=True):
    for a, b in reps:
        n = s.count(a)
        if strict: assert n >= 1, a[:70]
        s = s.replace(a, b)
    return s


A = pd.read_csv(ACSV); F = pd.read_csv(FCSV)
data = dict(ano=json.loads(A.to_json(orient='records')), fundos=json.loads(F.to_json(orient='records')))
SEC = ('<h2 class="rx-sec">Todos os fundos de ações das 100 maiores: sem viés de seleção</h2>\n'
       '<p class="rx-note" id="sv-res"></p>\n<div style="overflow-x:auto"><table class="rx-table" id="sv-ano"></table></div>\n'
       '<details style="margin:10px 0 24px"><summary style="cursor:pointer">Lista dos fundos (inclui os encerrados)</summary>'
       '<input id="sv-q" type="search" placeholder="Buscar fundo ou gestora" style="margin:8px 0;max-width:320px;width:100%">'
       '<div style="overflow-x:auto;max-height:480px;overflow-y:auto"><table class="rx-table" id="sv-f"></table></div></details>\n'
       '<script type="application/json" id="sv-data">' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + '</script>\n'
       '<script>(function(){const D=JSON.parse(document.getElementById("sv-data").textContent);'
       'const p=(x,n=1)=>x==null?"–":(x*100).toFixed(n).replace(".",",")+"%";const e=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c]));'
       'const full=D.ano.filter(r=>r.meses===12);const an=k=>Math.pow(full.reduce((a,r)=>a*(1+r[k]),1),1/full.length)-1;'
       'document.getElementById("sv-res").innerHTML=`Média anual ${full[0].ano}–${full[full.length-1].ano}: <b>todos os fundos da regra ${p(an("ret_medio"))}</b> · os 30 selecionados ${p(an("ret_30_selecionados"))} · Ibovespa ${p(an("ibov"))}. '
       '${D.fundos.length} fundos passaram pela regra; ${D.fundos.filter(f=>f.dead).length} encerraram e continuam na conta até a última cota.`;'
       'document.getElementById("sv-ano").innerHTML="<thead><tr><th>Ano</th><th>Fundos</th><th>Gestoras</th><th>Encerraram no ano</th><th>Média da regra</th><th>Mediana</th><th>Bateram o Ibov</th><th>30 selecionados</th><th>Ibovespa</th></tr></thead><tbody>"'
       '+D.ano.map(r=>`<tr><td>${r.ano}${r.meses<12?" (até mês "+r.meses+")":""}</td><td>${r.fundos}</td><td>${r.gestoras}</td><td>${r.encerraram_no_ano}</td><td><b>${p(r.ret_medio)}</b></td><td>${p(r.ret_mediano_vivos)}</td><td>${p(r.pct_bateu_ibov,0)}</td><td>${p(r.ret_30_selecionados)}</td><td>${p(r.ibov)}</td></tr>`).join("")+"</tbody>";'
       'const T=document.getElementById("sv-f");const draw=q=>{q=(q||"").toLowerCase();T.innerHTML="<thead><tr><th>Fundo</th><th>Gestora</th><th>Na regra</th><th>Retorno anual</th></tr></thead><tbody>"'
       '+D.fundos.filter(f=>!q||(f.fundo+" "+f.gestora).toLowerCase().includes(q)).map(f=>`<tr><td>${e(f.fundo)}${f.dead?` <span class="cw-chip dead">dead in ${f.dead}</span>`:""}</td><td>${e(f.gestora)}</td><td>${f.de}–${f.ate}</td><td>${p(f.ret_anual)}</td></tr>`).join("")+"</tbody>";};'
       'draw("");document.getElementById("sv-q").addEventListener("input",ev=>draw(ev.target.value));})();</script>\n    ')

s = open(IDX).read()
s = patch(s, REP)
s = s.replace('__SV__', SEC, 1)
s, n = METH_OLD.subn(METH_NEW, s); assert n >= 1
s = s.replace('.cw-chip.warn {', CSS + '.cw-chip.warn {', 1)
b64 = base64.b64encode(gzip.compress(open(JS, 'rb').read(), 9, mtime=0)).decode()
s, n = re.subn(r'(<script type="text/plain" id="nbd-carteiras\.json">)[^<]*(</script>)', lambda m: m.group(1) + b64 + m.group(2), s); assert n == 1
open(OUT, 'w').write(s)
for f in EXTRA:
    t = open(f).read(); t = patch(t, REP, strict=False); t = METH_OLD.sub(METH_NEW, t); open(f, 'w').write(t.replace('__SV__', ''))
print('ok', len(s) // 1024, 'KB')
