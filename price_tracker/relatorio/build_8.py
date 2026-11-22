"""Relatório FT das 8 seleções (relatorio/oito_selecoes.html) a partir de dados_8.json."""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_8.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>') + len('</style>')]
N, new, old, rob = d['names'], d['new'], d['old'], d['rob']
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
sp = d['bench']['S&P 500']
order = sorted(new, key=lambda k: -new[k]['cagr'])
best = order[0]
safest = max(new, key=lambda k: (new[k]['w3'] or 0, -abs(new[k]['maxdd'])))
robust = max(new, key=lambda k: rob[k]['sem as 3 maiores'][0])
body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Backtest das 8 seleções · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">As regras de 22/11 no teste</div>
<h1>Oito jeitos de comprar qualidade, e qual aguenta tirar as vencedoras</h1>
<p class="deck">Todas as seleções do Painel bateram o S&amp;P 500 desde 2011. A diferença aparece quando se tiram as maiores vencedoras e quando se olha o caminho, não só o ponto de chegada.</p>
<div class="byline">S&amp;P 500 point-in-time, rebalanceamento trimestral, retorno total em dólares · regras de 22/11/2026 (seguros multilinha e distribuidoras de saúde fora das cíclicas; ROIC sem o marginal sozinho quando ativo e passivo são negativos)</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Todas as seleções dependem dele (ROIC triangulado; financeiras e seguradoras de saúde com ROE).
<b>Atenção:</b> este backtest usa o crescimento <b>histórico</b> (mediana de 5 anos do EPS), que é a regra testável. A planilha V3 usa o <b>consenso do sell-side com haircut</b>, que não tem histórico para testar: as listas da planilha não são exatamente estas.</p>
<div class="big">
 <div><b>{pc(new[best]['cagr'])}</b><span>maior retorno anual: {N[best]}</span></div>
 <div><b>{pc(sp)}</b><span>S&amp;P 500 no mesmo período</span></div>
 <div><b>{pc(rob[robust]['sem as 3 maiores'][0])}</b><span>{N[robust]} sem as 3 maiores vencedoras (a mais robusta)</span></div>
 <div><b>{pc(new[safest]['w3'], 0)}</b><span>das janelas de 3 anos acima do S&amp;P: {N[safest]}</span></div>
</div>

<figure><figcaption class="t">A tabela principal</figcaption>
<figcaption class="s">Ordenada pelo retorno anual. Imposto de 15% sobre o ganho realizado. Janelas móveis mensais contra o S&amp;P 500.</figcaption>
<div id="t1" class="tablebox"></div></figure>

<figure><figcaption class="t">Tirando as vencedoras (e as perdedoras) do universo</figcaption>
<figcaption class="s">Retorno anual refazendo a carteira sem a ação de maior contribuição, sem as 3 maiores, sem a pior, sem as 3 piores e sem a NVIDIA. As ações tiradas aparecem em cinza.</figcaption>
<div id="t2" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>Uma seleção que só funciona com uma ou duas ações é aposta, não método. A queda "sem as 3 maiores" mede quanto do resultado depende de acertar poucos nomes.</span></div></figure>

<figure><figcaption class="t">O caminho: quanto cada seleção valeria</figcaption>
<figcaption class="s">US$ 1 investido em {d['periodo'][0][:7]}, escala logarítmica.</figcaption>
<div class="legend" id="lg3"></div><div id="c3"></div></figure>

<figure><figcaption class="t">De onde veio o retorno</figcaption>
<figcaption class="s">Retorno anual das posições em 3 anos, decomposto em crescimento do EPS, re-rating (mudança do P/L) e dividendos.</figcaption>
<div class="legend" id="lg4"></div><div id="c4"></div></figure>

<figure><figcaption class="t">Quem foi a melhor em cada janela de 3 anos</figcaption>
<figcaption class="s">Proporção das janelas móveis de 3 anos em que cada seleção teve o maior retorno entre as nove.</figcaption>
<div id="c5"></div></figure>

<figure><figcaption class="t">O efeito das duas mudanças de regra</figcaption>
<figcaption class="s">Retorno anual com as regras anteriores e com as de 22/11 (mesmo período, mesmo código).</figcaption>
<div id="t6" class="tablebox"></div></figure>

<figure><figcaption class="t">Quanto elas andam juntas</figcaption>
<figcaption class="s">Correlação dos retornos mensais e sobreposição média de ações (ações em comum ÷ ações das duas).</figcaption>
<div id="t7" class="tablebox"></div><div id="t7b" class="tablebox" style="margin-top:12px"></div></figure>

<figure><figcaption class="t">As ações e os setores que fizeram o resultado</figcaption>
<figcaption class="s">Contribuição acumulada (soma de peso × retorno de cada trimestre). Cinco maiores, cinco piores e os três setores que mais somaram.</figcaption>
<div class="attr" id="c8"></div></figure>

<figure><figcaption class="t">Os 9 comparativos de sempre</figcaption>
<figcaption class="s">Retorno anual e % das janelas de 3, 5 e 10 anos acima do S&amp;P 500 (carteiras de peso igual por classe, regras novas).</figcaption>
<div id="t9" class="tablebox"></div></figure>
<section class="verdict"><h2>O veredito</h2><div id="ver" class="vgrid"></div></section>
<p class="method" style="margin-top:30px"><b>Método.</b> Mesmas definições de relatorio/calc2.py: Top 20 = 20 de maior retorno esperado entre as de qualidade (ROIC ≥ 12%, crescimento ≥ 15%, P/L ≥ 4, sem cíclicas e vestuário), raiz do valor de mercado com teto de 10%; Especiais = as 20 com maior mín(ROIC/30%, crescimento/30%); Excepcionais = ROIC e crescimento acima de 30%, peso pela raiz do valor de mercado; JG+G = soma dos rankings de ROIC, crescimento e P/L; OoL, GCGR, High ROIC e High Growth com peso igual. Código: relatorio/backtest_8.py.</p>
</div>'''
js = r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const D=__DATA__;const N=D.names;const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const P=(x,n=1)=>x==null?'—':(x*100).toFixed(n).replace('.',',')+'%';const PP=(x,n=1)=>x==null?'—':((x>=0?'+':'')+(x*100).toFixed(n)).replace('.',',');
const COL=()=>({top20c:css('--oxford'),top20:css('--slate'),ool:css('--teal'),n2:css('--claret'),n2t20:css('--wheat'),hroic:css('--velvet'),gcgr:css('--jade'),magicg:css('--mandarin'),hgrowth:css('--black')});
function svgBox(id,w,h){const el=d3.select('#'+id);el.selectAll('*').remove();return el.append('svg').attr('viewBox',`0 0 ${w} ${h}`);}
function table(id,head,rows){document.getElementById(id).innerHTML='<table><thead><tr>'+head.map((h,i)=>`<th class="${i==0?'l':''}">${h}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map((c,i)=>`<td class="${i==0?'l':'n'}">${c}</td>`).join('')+'</tr>').join('')+'</tbody></table>';}
function draw(){const C=COL();const K=Object.keys(D.new).sort((a,b)=>D.new[b].cagr-D.new[a].cagr);
 table('t1',['Seleção','Retorno','Depois do IR','Volat.','Pior queda','Sharpe','Janelas 3a / 5a / 10a','Pior janela 3a','Meses atrás','Trades/ano','Ações','Maior peso'],
  K.map(k=>{const r=D.new[k];return[N[k],P(r.cagr),P(r.cagr_tax),P(r.vol,0),P(r.maxdd,0),r.sharpe.toFixed(2).replace('.',','),`${P(r.w3,0)} / ${P(r.w5,0)} / ${P(r.w10,0)}`,PP(r.w3min),r.behind,Math.round(r.trades),r.n_mean.toFixed(0),P(r.top_w,0)]}).concat([['S&P 500',P(D.bench['S&P 500']),'','','','','','','','','','']]));
 const labs=['sem a maior','sem as 3 maiores','sem a pior','sem as 3 piores','sem NVIDIA'];
 table('t2',['Seleção','Original'].concat(labs),K.map(k=>[N[k],P(D.new[k].cagr)].concat(labs.map(l=>`${P(D.rob[k][l][0])} <span style="color:var(--ink2);font-size:11px">${l=='sem NVIDIA'?'':D.rob[k][l][1].join(', ')}</span>`))));
 legendL('lg3',K.concat(['S&P 500']),C);line('c3',C);
 const dc=[css('--oxford'),css('--mandarin'),css('--teal')];document.getElementById('lg4').innerHTML=[['Crescimento do EPS',dc[0]],['Re-rating',dc[1]],['Dividendos',dc[2]]].map(([n,c])=>`<span><i style="--c:${c};height:10px"></i>${n}</span>`).join('');
 stacked('c4',K.filter(k=>D.new[k].decomp),dc);
 bars('c5',K,C);
 table('t6',['Seleção','Regras anteriores','Regras de 22/11','Diferença'],K.map(k=>[N[k],P(D.old[k].cagr),P(D.new[k].cagr),PP(D.new[k].cagr-D.old[k].cagr)+' p.p.']));
 const L=D.corr.labels;document.getElementById('t7').innerHTML='<table><thead><tr><th class="l"></th>'+L.map(l=>`<th>${l}</th>`).join('')+'</tr></thead><tbody>'+D.corr.m.map((r,i)=>`<tr><td class="l">${L[i]}</td>`+r.map(v=>`<td class="n" style="background:color-mix(in srgb, var(--oxford) ${Math.round(Math.max(0,v-.5)*160)}%, transparent)">${v.toFixed(2).replace('.',',')}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
 const ov=Object.entries(D.overlap).sort((a,b)=>b[1]-a[1]);table('t7b',['Par','Sobreposição média'],ov.slice(0,10).map(([k,v])=>[k,P(v,0)]).concat([['…menor sobreposição','']]).concat(ov.slice(-4).map(([k,v])=>[k,P(v,0)])));
 const box=document.getElementById('c8');box.innerHTML='';K.forEach(k=>{const r=D.new[k];const row=a=>`<tr><td class="l">${a[0]}</td><td class="n">${(a[1]*100).toFixed(0)}</td></tr>`;
  box.insertAdjacentHTML('beforeend',`<div style="--c:${C[k]}"><h4>${N[k]}</h4><table><tbody>${r.best5.map(row).join('')}<tr><td class="l" style="color:var(--ink2);font-size:12px">… piores</td><td></td></tr>${r.worst5.map(row).join('')}<tr><td class="l" style="color:var(--ink2);font-size:12px">setores</td><td></td></tr>${r.sector.slice(0,3).map(s=>`<tr><td class="l">${s[0]}</td><td class="n">${P(s[2],0)}</td></tr>`).join('')}</tbody></table></div>`);});
 const b9=Object.keys(D.bench9);table('t9',['Carteira','Retorno anual','Janelas 3a / 5a / 10a'],b9.map(k=>[k,P(D.bench9[k]),D.win9[k].map(v=>P(v,0)).join(' / ')]));
 const top=K[0],rob=K.slice().sort((a,b)=>D.rob[b][labs[1]][0]-D.rob[a][labs[1]][0])[0],w3=K.slice().sort((a,b)=>(D.new[b].w3-D.new[a].w3)||(D.new[b].maxdd-D.new[a].maxdd))[0];
 document.getElementById('ver').innerHTML=[[css('--teal'),'Maior retorno',`${N[top]}: ${P(D.new[top].cagr)} ao ano; sem as 3 maiores vencedoras, ${P(D.rob[top][labs[1]][0])}.`],
  [css('--oxford'),'Mais robusta a tirar vencedoras',`${N[rob]}: ${P(D.rob[rob][labs[1]][0])} sem as 3 maiores.`],
  [css('--claret'),'Caminho mais consistente',`${N[w3]}: ${P(D.new[w3].w3,0)} das janelas de 3 anos acima do S&P, pior queda de ${P(D.new[w3].maxdd,0)}.`]].map(([c,t,x])=>`<div><span class="tag" style="--c:${c}">${t}</span><p>${x}</p></div>`).join('');}
function legendL(id,ks,C){document.getElementById(id).innerHTML=ks.map(k=>`<span><i style="--c:${k=='S&P 500'?css('--ink'):C[k]}"></i>${N[k]||k}</span>`).join('');}
function line(id,C){const W=1000,H=380,m={l:50,r:20,t:10,b:30};const s=svgBox(id,W,H);const dt=D.nav.dates.map(x=>new Date(x));
 const x=d3.scaleTime().domain(d3.extent(dt)).range([m.l,W-m.r]);const all=Object.values(D.nav.series).flat().filter(v=>v);const y=d3.scaleLog().domain([d3.min(all)*.9,d3.max(all)*1.1]).range([H-m.b,m.t]);
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(8));s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6,'~g').tickSize(-(W-m.l-m.r)));
 const key=Object.fromEntries(Object.entries(N).map(([k,v])=>[v,k]));
 Object.entries(D.nav.series).forEach(([n,v])=>{const k=key[n];s.append('path').attr('d',d3.line().defined(q=>q[1]).x(q=>x(q[0])).y(q=>y(q[1]))(dt.map((t,i)=>[t,v[i]]))).attr('fill','none').attr('stroke',n=='S&P 500'?css('--ink'):C[k]).attr('stroke-width',n=='S&P 500'?2.5:1.6).attr('stroke-dasharray',n=='S&P 500'?'5 4':null);});}
function stacked(id,ks,cols){const W=1000,rh=32,m={l:230,r:70,t:6,b:26},H=m.t+m.b+ks.length*rh;const s=svgBox(id,W,H);const v=ks.map(k=>D.new[k].decomp);
 const lo=Math.min(0,d3.min(v,q=>Math.min(q.le,0)+Math.min(q.lp,0))),hi=d3.max(v,q=>Math.max(q.le,0)+Math.max(q.lp,0)+Math.max(q.ld,0));const x=d3.scaleLinear().domain([lo*1.1,hi*1.1]).range([m.l,W-m.r]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(8).tickFormat(q=>P(q,0)).tickSize(-(H-m.t-m.b)));
 ks.forEach((k,i)=>{const q=D.new[k].decomp,yy=m.t+i*rh;let p=0,n=0;s.append('text').attr('x',m.l-8).attr('y',yy+rh/2+5).attr('text-anchor','end').style('font-size','13px').text(N[k]);
  [['le',0],['lp',1],['ld',2]].forEach(([c,j])=>{const val=q[c];const a=val>=0?p:n+val;val>=0?p+=val:n+=val;s.append('rect').attr('x',x(a)).attr('y',yy+6).attr('width',Math.abs(x(a+Math.abs(val))-x(a))).attr('height',rh-12).attr('fill',cols[j]);});
  s.append('text').attr('class','num').attr('x',x(p)+6).attr('y',yy+rh/2+5).text(P(q.lt));});s.append('line').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b).attr('stroke',css('--ink'));}
function bars(id,K,C){const W=1000,rh=28,m={l:230,r:60,t:6,b:10},H=m.t+m.b+K.length*rh;const s=svgBox(id,W,H);const v=K.map(k=>D.best3[N[k]]||0);const x=d3.scaleLinear().domain([0,d3.max(v)*1.15||1]).range([m.l,W-m.r]);
 K.forEach((k,i)=>{const yy=m.t+i*rh;s.append('text').attr('x',m.l-8).attr('y',yy+rh/2+5).attr('text-anchor','end').style('font-size','13px').text(N[k]);s.append('rect').attr('x',m.l).attr('y',yy+6).attr('height',rh-12).attr('width',x(v[i])-m.l).attr('fill',C[k]);s.append('text').attr('class','num').attr('x',x(v[i])+6).attr('y',yy+rh/2+5).text(P(v[i],0));});}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>Oito seleções</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__DATA__', json.dumps(d, ensure_ascii=False))
(ROOT / 'oito_selecoes.html').write_text(html); print('ok', len(html))
