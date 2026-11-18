"""Relatório FT do ramo C (relatorio/gestores_universo_amplo.html) a partir de dados_gestores_amplo.json. Uso: python3 relatorio/build_gestores_amplo.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_gestores_amplo.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>') + len('</style>')]
src_js = (ROOT / 'build_gestores.py').read_text()
helpers = src_js[src_js.index('function bars('):src_js.index('function draw(){')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
n2 = lambda x, n=2: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')
T, E, DF, CV, UV, UF = d['carteiras'], d['extra'], d['diferenca'], d['cobertura'], d['universo'], d['universo_fora_sp']
per = f"{d['periodo'][0][:7]} a {d['periodo'][1][:7]}"
b = d['best']; tb = T[b]; eb = E[b]; db = DF[b]
t0, o0, sp, iwm = T['Top 20 · S&P (original)'], T['ROIC alto descontado · S&P (original)'], T['S&P 500'], T['IWM (Russell 2000)']
k3t, k1t = 'Top 20 · amplo, ≥ 3 gestores', 'Top 20 · amplo, ≥ 1 gestor'
k1o, k3o, k5o = 'ROIC alto descontado · amplo, ≥ 1 gestor', 'ROIC alto descontado · amplo, ≥ 3 gestores', 'ROIC alto descontado · amplo, ≥ 5 gestores'
dec_b, dec_0 = d['decomp'][b]['12'], d['decomp']['Top 20 · S&P (original)']['12']

body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Gestores como universo · {per}</span></div>
<div class="kicker">Seguir o dinheiro, escolher o preço</div>
<h1>Os gestores escolhem o campo. A Top 20 escolhe as jogadas</h1>
<p class="deck">Usar como universo as ações que pelo menos cinco gestores carregam, de qualquer tamanho e não só do S&amp;P 500, e aplicar por cima a Top 20 rendeu {pc(tb['cagr'])} ao ano, contra {pc(t0['cagr'])} da Top 20 no S&amp;P. No "ROIC alto descontado", o universo maior não somou nada robusto.</p>
<div class="byline">13F dos gestores do "Navegando US" · S&amp;P 500 + médias e pequenas (≥ US$ 2 bi), point-in-time · carteiras trimestrais com o 13F do trimestre anterior · {per}</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele define o filtro (ROIC ≥ 12%) e o P/E justo. A lista de gestores é a de hoje (viés de sobrevivência), e foram testadas 6 versões: um resultado isolado bom pode ser sorte. Backtest, sem custos; não é recomendação.</p>

<div class="big">
 <div><b>{pc(tb['cagr'])}</b><span>Top 20 no universo amplo com ≥ 5 gestores, contra {pc(t0['cagr'])} da Top 20 só no S&amp;P e {pc(sp['cagr'])} do S&amp;P</span></div>
 <div><b>{pp(db['media_aa'])}</b><span>ao ano sobre a Top 20 original; melhor em {pc(db['melhor'], 0)} dos trimestres (t = {n2(db['t'], 1)})</span></div>
 <div><b>{pc(eb['fora_sp'], 0)}</b><span>das ações vêm de fora do S&amp;P ({pc(eb['peso_fora_sp'], 0)} do peso); valor de mercado mediano de US$ {eb['mcap_med']:.0f} bi</span></div>
 <div><b>{pc(CV['no_painel'], 0)}</b><span>do valor das posições dos gestores cai no nosso universo com dados; o resto é estrangeiro, ADR, ETF ou sem ticker</span></div>
</div>

<div class="cols">
 <div class="prose">
  <p>A pergunta era combinar as duas coisas: deixar os gestores dizerem onde vale procurar, num universo maior que o S&amp;P 500, e por cima aplicar os nossos filtros e a escolha pelo múltiplo. O teste usa as ações americanas detidas por pelo menos 1, 3 ou 5 gestores no 13F do trimestre anterior, com valor de mercado acima de US$ 2 bi, e recalcula o P/E justo e o retorno esperado nesse universo combinado.</p>
  <p>Na Top 20 o resultado foi claro e cresce com o número de gestores: {pc(T[k1t]['cagr'])} com 1 gestor, {pc(T[k3t]['cagr'])} com 3 e {pc(tb['cagr'])} com 5. Com 5 gestores, a carteira bateu o S&amp;P em todas as janelas de 3, 5 e 10 anos, teve a menor queda máxima do grupo ({pc(tb['dd'], 0)}) e quase não depende da NVIDIA ({pc(d['sem_nvda']['sem'])} sem ela). Cerca de {pc(eb['fora_sp'], 0)} das ações vêm de fora do S&amp;P, mas não são microempresas: o valor de mercado mediano é de US$ {eb['mcap_med']:.0f} bi.</p>
  <p>No "ROIC alto descontado" o universo maior não ajudou de forma confiável: {pc(T[k1o]['cagr'])}, {pc(T[k3o]['cagr'])} e {pc(T[k5o]['cagr'])}, contra {pc(o0['cagr'])} no S&amp;P, sem padrão e com t abaixo de 1. Com 1 gestor, a carteira ficou mais volátil e bateu o S&amp;P em menos janelas de 3 anos ({pc(T[k1o]['w3'], 0)}). Comprar só pelo desconto, num universo cheio de empresas menores, traz mais armadilhas.</p>
  <p>A diferença tem lógica: a Top 20 exige crescimento do EPS de 15% ou mais, e os gestores ajudam a separar o crescimento que continua (era o achado do relatório anterior). O "ROIC alto descontado" não olha o crescimento, então o filtro dos gestores tem menos o que corrigir.</p>
 </div>
 <aside class="box"><h3>O que fica</h3><ol>
  <li><b>Top 20 com ≥ 5 gestores, universo amplo:</b> a melhor versão, {pp(db['media_aa'])} ao ano, t = {n2(db['t'], 1)}. Promissora, mas é 1 de 6 testes: corrigindo para isso, fica no limite da significância.</li>
  <li><b>ROIC alto descontado:</b> fica no S&amp;P; o universo maior não somou.</li>
  <li><b>Cobertura:</b> {pc(CV['fora'], 0)} do dinheiro dos gestores está em ações sem dado no nosso painel (estrangeiras, ADRs, ETFs).</li>
  <li><b>Para decidir:</b> acompanhar a Top 20 ampla com ≥ 5 gestores ao lado da regra, antes de trocar.</li></ol></aside>
</div>

<h2 class="chap" style="margin-top:56px">1. O universo</h2>
<figure><figcaption class="t">Os gestores apontam para cerca de {UV['5']:.0f} ações com dados; um terço fora do S&amp;P</figcaption>
<figcaption class="s">Ações por trimestre no universo (≥ US$ 2 bi, com dado fundamentalista) e a parcela fora do S&amp;P 500, por número mínimo de gestores. À direita, para onde vai o dinheiro dos gestores.</figcaption>
<div id="c1" class="tablebox"></div>
<div class="src">Fora do painel, as maiores posições são {", ".join(t for t, _ in d['fora_exemplos'][:8])}. Berkshire (BRK-B) e Visa não estão no nosso painel do S&amp;P 500, uma lacuna de dados que afeta todas as carteiras; as demais são estrangeiras (ADRs), ETFs ou empresas sem balanço na SEC.</div>
</figure>

<h2 class="chap" style="margin-top:56px">2. As carteiras</h2>
<figure><figcaption class="t">Na Top 20, quanto mais gestores no filtro, melhor; no desconto puro, não</figcaption>
<figcaption class="s">Valor acumulado de US$ 1 desde {d['periodo'][0][:7]}, rebalanceamento trimestral, raiz do valor de mercado com teto de 10%.</figcaption>
<div class="legend" id="lg2"></div><div id="c2"></div>
<div id="c3" class="tablebox" style="margin-top:12px"></div>
<div class="src">Janelas: % das janelas móveis que bateram o S&amp;P 500 (com dez anos de dados, há poucas janelas de 10 anos). "Peso igual": a mesma carteira com pesos iguais. Giro: % das ações trocadas por trimestre.</div>
<div class="sowhat"><b>E daí</b><span>A Top 20 com ≥ 5 gestores no universo amplo rendeu {pc(tb['cagr'])} ao ano ({pc(T[b + ' (peso igual)']['cagr'])} com peso igual), bateu o S&amp;P em {pc(tb['w3'], 0)} das janelas de 3 anos e caiu no máximo {pc(-tb['dd'], 0)}. Contra a Top 20 do S&amp;P, ganhou em {pc(db['melhor'], 0)} dos trimestres. Foi a única das 6 versões novas com diferença estatística (t = {n2(db['t'], 1)}); como testamos 6, o limite justo seria t ≈ 2,6. Ela está no limite.</span></div>
</figure>

<figure><figcaption class="t">De onde veio o retorno: o mesmo motor da Top 20 original</figcaption>
<figcaption class="s">Retorno anual em 3 anos das posições, decomposto em crescimento do EPS, re-rating e dividendos.</figcaption>
<div class="legend" id="lg4"></div><div id="c4"></div>
<div class="sowhat"><b>E daí</b><span>As duas Top 20 têm o mesmo motor, lucro crescendo e re-rating, nas posições com 3 anos de histórico à frente: EPS {pc(dec_b['eps'])} contra {pc(dec_0['eps'])} ao ano e re-rating {pc(dec_b['rr'])} contra {pc(dec_0['rr'])}. A vantagem da versão ampla não vem de um motor diferente, e sim de escolher melhor dentro de um campo maior. O "ROIC alto descontado" continua sendo uma aposta pura no múltiplo, com o lucro encolhendo no período.</span></div>
</figure>

<figure><figcaption class="t">Hoje: a Top 20 no universo amplo com ≥ 5 gestores</figcaption>
<figcaption class="s">Composição em {d['hoje_data']}, com peso, número de gestores no último 13F e se a ação está no S&amp;P 500.</figcaption>
<div id="c5" class="tablebox"></div>
</figure>

<p class="method" style="margin-top:36px"><b>Método.</b> Universo trimestral: ações com ≥ N gestores (N = 1, 3, 5) no 13F do trimestre anterior (posições ≥ 0,2% da carteira, como no "Navegando US"), entre as que têm dado point-in-time no painel do S&amp;P 500 ou no de médias e pequenas (ROIC triangulado; financeiras e seguradoras de saúde com ROE), com valor de mercado ≥ US$ 2 bi. O g do P/E justo, o P/E justo e o retorno esperado são recalculados no universo combinado. Filtros registrados: ROIC ≥ 12%, sem cíclicos e vestuário, P/L &gt; 0; Top 20: crescimento ≥ 15%, P/L ≥ 4, ordem pelo retorno esperado; "ROIC alto descontado": ordem por log(P/E justo ÷ P/L). Peso pela raiz do valor de mercado com teto de 10%. Pré-registrado no PROTOCOLO em 18/11/2026. Código: <code>relatorio/ramo_gestores_amplo.py</code>.</p>
</div>
'''

js = r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const D=__DATA__;
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const P=(x,n=1)=>x==null?'—':(x*100).toFixed(n).replace('.',',')+'%';
function svgBox(id,w,h){const el=d3.select('#'+id);el.selectAll('*').remove();return el.append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img');}
function legend(id,items){document.getElementById(id).innerHTML=items.map(([n,c])=>`<span><i style="--c:${c};height:10px"></i>${n}</span>`).join('');}
function table(id,head,rows){document.getElementById(id).innerHTML='<table><thead><tr>'+head.map((h,i)=>`<th class="${i==0?'l':''}">${h}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map((c,i)=>`<td class="${(i==0||/^[A-Za-zÀ-ú]/.test(String(c)))?'l':'n'}">${c}</td>`).join('')+'</tr>').join('')+'</tbody></table>';}
__HELPERS__
function draw(){
 const C=[css('--oxford'),css('--mandarin'),css('--teal')];
 const cv=D.cobertura;
 table('c1',['Gestores (mínimo)','Ações por trimestre','Fora do S&P 500'],['1','3','5'].map(k=>[`≥ ${k}`,Math.round(D.universo[k]),P(D.universo_fora_sp[k],0)]).concat([['Dinheiro dos gestores: no nosso painel',P(cv.no_painel,0),''],['Sem ticker (CUSIP sem correspondência)',P(cv.sem_ticker,0),''],['Com ticker, fora do painel',P(cv.fora,0),'']]));
 const show=Object.keys(D.nav.series),pal=[css('--ink'),css('--slate'),css('--oxford'),css('--teal'),css('--wheat'),css('--mandarin'),css('--velvet'),css('--jade'),css('--claret'),'#9a6b4f'];
 legend('lg2',show.map((k,i)=>[k,pal[i%pal.length]]));
 {const W=1000,H=420,m={l:56,r:20,t:14,b:30};const s=svgBox('c2',W,H);const dt=D.nav.dates.map(v=>new Date(v));
  const all=show.flatMap(k=>D.nav.series[k]).filter(v=>v!=null);const x=d3.scaleTime().domain(d3.extent(dt)).range([m.l,W-m.r]);const y=d3.scaleLinear().domain([0,d3.max(all)*1.05]).range([H-m.b,m.t]).nice();
  s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(v=>'US$ '+v.toFixed(0)).tickSize(-(W-m.l-m.r)));
  s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(10));
  show.forEach((k,i)=>{const pts=D.nav.series[k].map((v,j)=>[dt[j],v]).filter(p=>p[1]!=null);s.append('path').attr('d',d3.line().x(p=>x(p[0])).y(p=>y(p[1]))(pts)).attr('fill','none').attr('stroke',pal[i%pal.length]).attr('stroke-width',k==D.best?3.4:1.6).attr('stroke-dasharray',(k=='S&P 500'||k.startsWith('IWM'))?'5 4':null);});}
 const order=['S&P 500','S&P 500 equal weight','IWM (Russell 2000)','OoL antigo','GCGR antigo','OoL novo','GCGR novo','OoL High ROIC (novo)','OoL High Growth (novo)','Cyclicals','Top 20 · S&P (original)','Top 20 · S&P, ≥ 3 gestores','ROIC alto descontado · S&P (original)','ROIC alto descontado · S&P, ≥ 3 gestores'].concat(D.new);
 const pp=v=>v==null?'—':((v*100>=0?'+':'')+(v*100).toFixed(1)).replace('.',',');
 table('c3',['Carteira','Retorno anual','Peso igual','Volatilidade','Pior queda','Janelas 3a','5a','10a','Pior janela 3a (p.p./ano)','Fora do S&P','Giro'],order.filter(k=>D.carteiras[k]).map(k=>{const t=D.carteiras[k],e=D.carteiras[k+' (peso igual)'],x=D.extra[k]||{};const s=k=='S&P 500';
  return [k,P(t.cagr),e?P(e.cagr):'—',P(t.vol),P(t.dd,0),s?'—':P(t.w3,0),s?'—':P(t.w5,0),s?'—':P(t.w10,0),s?'—':pp(t.p3),x.fora_sp==null?'—':P(x.fora_sp,0),x.giro_trim==null?'—':P(x.giro_trim,0)];}));
 legend('lg4',[['Crescimento do EPS',C[0]],['Re-rating',C[1]],['Dividendos',C[2]]]);
 stacked('c4',Object.entries(D.decomp).map(([k,v])=>({nome:k.replace('ROIC alto descontado','Descontado'),...v['12']})),['eps','rr','div'],C);
 table('c5',['Ação','Empresa','Peso','Gestores','No S&P?'],D.hoje[D.best].map(r=>[r[0],r[1],P(r[2]),r[3],r[4]?'sim':'não']));
}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>Gestores como Universo</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__HELPERS__', helpers).replace('__DATA__', json.dumps(d, ensure_ascii=False))
(ROOT / 'gestores_universo_amplo.html').write_text(html)
print('ok', len(html))
