"""Relatório FT do ramo dos gestores (relatorio/universo_gestores.html) a partir de dados_gestores.json. Uso: python3 relatorio/build_gestores.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_gestores.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
n2 = lambda x, n=2: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')
T, ic, fx, dc, df = d['carteiras'], d['premissa_ic'], d['premissa_faixas'], d['premissa_decomp'], d['diferenca']
G = d['gestores']
o3, o0 = T['ROIC alto descontado, ≥ 3 gestores'], T['ROIC alto descontado (original)']
t5, t0 = T['Top 20, ≥ 5 gestores'], T['Top 20 (original)']
md = T['As 20 mais detidas (controle)']
sp = T['S&P 500']
eps3 = ic['Crescimento do EPS em 3 anos (a.a.)']['todos']; rr3 = ic['Re-rating em 3 anos (a.a.)']['todos']; ex3 = ic['Excesso sobre o S&P em 3 anos (a.a.)']['todos']
dd3 = df['ROIC alto descontado, ≥ 3 gestores']
dm = d['decomp']['As 20 mais detidas (controle)']['12']; do = d['decomp']['ROIC alto descontado (original)']['12']; dg = d['decomp']['ROIC alto descontado, ≥ 3 gestores']['12']
per = f"{d['periodo'][0][:7]} a {d['periodo'][1][:7]}"

body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Universo dos gestores · {per}</span></div>
<div class="kicker">Seguir o dinheiro</div>
<h1>Os gestores acertam o lucro. O re-rating continua sendo nosso</h1>
<p class="deck">As ações que mais gestores ativos carregam cresceram o lucro mais rápido nos anos seguintes. Mas o mercado já cobrava por isso: o múltiplo delas não subiu. Usar a lista dos gestores como filtro antes do "ROIC alto descontado" somou cerca de 1 ponto ao ano, sem significância estatística.</p>
<div class="byline">13F de {G['n']} gestores do "Navegando US" ({G['longo']} long-only, {G['hedge']} hedge funds e ativistas) · S&amp;P 500 point-in-time · carteiras trimestrais montadas com o 13F do trimestre anterior · {per}</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele define o filtro (ROIC ≥ 12%) e o P/E justo, de onde sai o desconto. A lista de gestores é a de hoje: quem fechou ou foi mal no caminho não está nela (viés de sobrevivência). Backtest, sem custos; não é recomendação.</p>

<div class="big">
 <div><b>{n2(eps3['ic'])}</b><span>correlação entre o número de gestores e o crescimento do EPS nos 3 anos seguintes (positiva em {pc(eps3['pos'], 0)} dos trimestres)</span></div>
 <div><b>{n2(rr3['ic'])}</b><span>idem para o re-rating: zero. Os gestores não antecipam a reprecificação</span></div>
 <div><b>{pc(o3['cagr'])}</b><span>ROIC alto descontado só entre ações com ≥ 3 gestores, contra {pc(o0['cagr'])} sem o filtro e {pc(sp['cagr'])} do S&amp;P</span></div>
 <div><b>t = {n2(dd3['t'], 1)}</b><span>a diferença de {pp(dd3['media_aa'])} ao ano não é distinguível de sorte (precisaria de t ≈ 2)</span></div>
</div>

<div class="cols">
 <div class="prose">
  <p>A ideia era simples: se quem põe dinheiro de verdade escolhe empresas cujo lucro vai crescer, a lista dos gestores pode ser o universo. Dentro dela, o nosso re-rating via ROIC escolheria as que, além de crescer, estão baratas. Juntando as duas coisas, as ações cresceriam o lucro e ainda ganhariam múltiplo.</p>
  <p>A primeira metade se confirmou. Nos 13F de {G['n']} gestores desde 2016, quanto mais gestores carregam uma ação, mais o lucro dela cresce depois. As ações com cinco ou mais gestores tiveram o EPS crescendo {pc(dc['≥ 5 gestores']['eps'])} ao ano em 3 anos, contra {pc(dc['< 3 gestores']['eps'])} das demais. O efeito aparece em praticamente todos os trimestres.</p>
  <p>A segunda metade não veio. O múltiplo dessas ações não subiu: o re-rating médio foi de {pc(dc['≥ 5 gestores']['rr'])} ao ano. O mercado já sabia o que os gestores sabiam e cobrava por isso. As 20 mais detidas são o caso extremo: lucro crescendo {pc(dm['eps'])} ao ano e múltiplo caindo {pc(-dm['rr'])}, porque elas foram compradas caras (desconto de {n2(dm['gap'])} em log, ou seja, acima do P/E justo).</p>
  <p>Na prática, o filtro dos gestores troca 2 ou 3 das 20 ações do "ROIC alto descontado" e melhora um pouco o lucro da carteira, ao custo de um pouco de re-rating. O saldo foi positivo ({pp(dd3['media_aa'])} ao ano), mas pequeno demais para separar de sorte em dez anos.</p>
 </div>
 <aside class="box"><h3>O que fazer</h3><ol>
  <li><b>Premissa:</b> confirmada para o lucro, rejeitada para o re-rating.</li>
  <li><b>Filtro dos gestores:</b> pode entrar como desempate ou checagem, não como regra. Ganho de ~1 p.p. sem significância.</li>
  <li><b>Não compre as "mais detidas":</b> crescem, mas já vêm caras. Renderam {pc(md['cagr'])}, menos que as nossas carteiras.</li>
  <li><b>Para confirmar:</b> acompanhar a versão com ≥ 3 gestores ao lado da original nos próximos trimestres.</li></ol></aside>
</div>

<h2 class="chap" style="margin-top:56px">1. A premissa: os gestores sabem algo sobre o lucro?</h2>
<figure><figcaption class="t">Mais gestores, mais crescimento do lucro depois</figcaption>
<figcaption class="s">Ações do S&amp;P 500 agrupadas pelo número de gestores com posição no 13F do trimestre anterior: crescimento mediano do EPS (1 e 3 anos à frente, ao ano) e re-rating mediano em 3 anos.</figcaption>
<div class="legend" id="lg1"></div><div id="c1"></div>
<div class="sowhat"><b>E daí</b><span>De 1–2 gestores para 10 ou mais, o crescimento mediano do lucro em 3 anos vai de {pc(fx['1–2']['R12'])} para {pc(fx['10 ou mais']['R12'])} ao ano. O re-rating fica perto de zero em todas as faixas. As ações sem nenhum gestor (cerca de {fx['0 gestores']['n']:.0f} por trimestre) fogem do padrão, com crescimento de {pc(fx['0 gestores']['R12'])}; a relação vale de 1 gestor em diante.</span></div>
</figure>

<figure><figcaption class="t">O sinal é do lucro, não do múltiplo</figcaption>
<figcaption class="s">Correlação de ordem média, por trimestre, entre o número de gestores e cada resultado futuro; estatística t ajustada para a sobreposição das janelas. "Qualidade" = só ações com ROIC ≥ 12%, sem cíclicas.</figcaption>
<div id="c2" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>A correlação com o crescimento do lucro é pequena ({n2(eps3['ic'])}), mas muito consistente (t = {n2(eps3['t'], 1)}). Com o re-rating, é zero. Também há correlação com o excesso de retorno em 3 anos ({n2(ex3['ic'])}), que vem do lucro, não do múltiplo. É o oposto do nosso modelo: o ROIC prevê o re-rating, os gestores preveem o lucro.</span></div>
</figure>

<figure><figcaption class="t">Onde os gestores estão, o lucro cresce, mas o múltiplo não sobe</figcaption>
<figcaption class="s">Retorno anual em 3 anos decomposto em crescimento do EPS, re-rating e dividendos (média por trimestre, peso igual).</figcaption>
<div class="legend" id="lg3"></div><div id="c3"></div>
</figure>

<h2 class="chap" style="margin-top:56px">2. As carteiras</h2>
<figure><figcaption class="t">O filtro dos gestores somou cerca de 1 ponto ao ano ao ROIC alto descontado e à Top 20</figcaption>
<figcaption class="s">Valor acumulado de US$ 1 desde {d['periodo'][0][:7]}, rebalanceamento trimestral, raiz do valor de mercado com teto de 10%.</figcaption>
<div class="legend" id="lg4"></div><div id="c4"></div>
<div id="c5" class="tablebox" style="margin-top:12px"></div>
<div class="src">Janelas: % das janelas móveis que bateram o S&amp;P 500. Com dez anos de dados, há pouquíssimas janelas de 10 anos. "Peso igual" = a mesma carteira com pesos iguais.</div>
<div class="sowhat"><b>E daí</b><span>Com ≥ 3 gestores, o ROIC alto descontado foi de {pc(o0['cagr'])} para {pc(o3['cagr'])}, e a Top 20 com ≥ 5 gestores foi de {pc(t0['cagr'])} para {pc(t5['cagr'])}. Mas as carteiras com e sem o filtro têm {pc(d['sobreposicao']['ROIC alto descontado, ≥ 3 gestores'], 0)} das ações em comum, e a diferença trimestral tem t entre {n2(min(v['t'] for v in df.values()), 1)} e {n2(max(v['t'] for v in df.values()), 1)}. Sem a NVIDIA, a versão com ≥ 3 gestores fica em {pc(d['sem_nvda']['sem'])}, contra {pc(d['sem_nvda']['original_sem'])} da original.</span></div>
</figure>

<figure><figcaption class="t">O filtro troca um pouco de re-rating por um pouco de lucro</figcaption>
<figcaption class="s">Decomposição do retorno anual em 3 anos das posições de cada carteira, e o número médio de gestores por ação.</figcaption>
<div class="legend" id="lg6"></div><div id="c6"></div>
<div class="sowhat"><b>E daí</b><span>Com o filtro, o lucro das ações piora menos ({pc(dg['eps'])} contra {pc(do['eps'])} ao ano), e o re-rating é um pouco menor ({pc(dg['rr'])} contra {pc(do['rr'])}). É exatamente a troca que a premissa previa, só que em escala pequena: o "ROIC alto descontado" já tinha, em média, {n2(do['ng'], 0)} gestores por ação.</span></div>
</figure>

<figure><figcaption class="t">Hoje: o ROIC alto descontado entre as ações com ≥ 3 gestores</figcaption>
<figcaption class="s">Composição em {d['hoje_data']}, com peso e número de gestores no último 13F disponível.</figcaption>
<div id="c7" class="tablebox"></div>
</figure>

<p class="method" style="margin-top:36px"><b>Método.</b> Posições dos 13F extraídas dos dados do artefato "Navegando US" (gerado em 17/11/2026): {G['n']} gestores ativos, trimestres de {G['trimestres'][0]} a {G['trimestres'][1]}, só posições ≥ 0,2% da carteira. Número de gestores = gestores com posição na empresa (duplas classes somadas). A carteira montada no fim do trimestre t usa o 13F do trimestre t−1, já arquivado. Universo: membros do S&amp;P 500 na data, ROIC triangulado (financeiras e seguradoras de saúde com ROE), sem cíclicas e vestuário. "ROIC alto descontado" = ROIC ≥ 12%, as 20 de maior log(P/E justo ÷ P/L); Top 20 = regra congelada do PROTOCOLO. Todas as carteiras e os 9 comparativos foram medidos de {d['periodo'][0]} a {d['periodo'][1]}. Pré-registrado no PROTOCOLO em 18/11/2026. Exploratória. Código: <code>relatorio/ramo_gestores.py</code>.</p>
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
function bars(id,cats,series,cols,opt={}){const W=1000,H=opt.h||300,m={l:64,r:16,t:16,b:44};const s=svgBox(id,W,H);
 const all=series.flat().filter(v=>v!=null);const x0=d3.scaleBand().domain(cats).range([m.l,W-m.r]).padding(.25);const x1=d3.scaleBand().domain(d3.range(series.length)).range([0,x0.bandwidth()]).padding(.08);
 const y=d3.scaleLinear().domain([Math.min(0,d3.min(all))*1.2,Math.max(0,d3.max(all))*1.2]).range([H-m.b,m.t]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(v=>P(v,0)).tickSize(-(W-m.l-m.r)));
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x0).tickSize(0)).selectAll('text').style('font-size','13px').attr('dy','1.2em');
 series.forEach((ser,j)=>ser.forEach((v,i)=>{if(v==null)return;s.append('rect').attr('x',x0(cats[i])+x1(j)).attr('width',x1.bandwidth()).attr('y',y(Math.max(0,v))).attr('height',Math.abs(y(v)-y(0))).attr('fill',cols[j]);
  s.append('text').attr('class','num').attr('x',x0(cats[i])+x1(j)+x1.bandwidth()/2).attr('y',v>=0?y(v)-4:y(v)+13).attr('text-anchor','middle').style('font-size','11px').text(P(v,0));}));
 s.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0)).attr('stroke',css('--ink'));}
function stacked(id,rows,keys,cols){const W=1000,rh=34,m={l:250,r:70,t:10,b:28},H=m.t+m.b+rows.length*rh;const s=svgBox(id,W,H);
 let lo=0,hi=0;rows.forEach(r=>{let p=0,n=0;keys.forEach(k=>{r[k]>0?p+=r[k]:n+=r[k]});hi=Math.max(hi,p);lo=Math.min(lo,n)});
 const x=d3.scaleLinear().domain([Math.min(lo,0)*1.1,hi*1.08]).range([m.l,W-m.r]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(8).tickFormat(v=>P(v,0)).tickSize(-(H-m.t-m.b)));
 rows.forEach((r,i)=>{const y=m.t+i*rh;let p=0,n=0;s.append('text').attr('x',m.l-8).attr('y',y+rh/2+5).attr('text-anchor','end').style('font-size','14px').text(r.nome);
  keys.forEach((k,j)=>{const v=r[k];const a=v>=0?p:n+v;v>=0?p+=v:n+=v;s.append('rect').attr('x',x(a)).attr('y',y+6).attr('width',Math.abs(x(a+Math.abs(v))-x(a))).attr('height',rh-12).attr('fill',cols[j]);});
  s.append('text').attr('class','num').attr('x',x(Math.max(p,0))+6).attr('y',y+rh/2+5).text(P(r.tot)+(r.ng!=null?` · ${Math.round(r.ng)} gestores`:''));});
 s.append('line').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b).attr('stroke',css('--ink'));}
function draw(){
 const C=[css('--oxford'),css('--mandarin'),css('--teal')];
 const F=D.premissa_faixas,cats=Object.keys(F);
 legend('lg1',[['EPS em 1 ano',css('--slate')],['EPS em 3 anos (a.a.)',C[0]],['Re-rating em 3 anos (a.a.)',C[1]]]);
 bars('c1',cats,[cats.map(k=>F[k].R4),cats.map(k=>F[k].R12),cats.map(k=>F[k].RR12)],[css('--slate'),C[0],C[1]]);
 const T=v=>v==null?'—':v.toFixed(2).replace('.',',');
 table('c2',['Resultado futuro','Correlação (todas)','t','% trimestres positiva','Correlação (qualidade)','t'],Object.entries(D.premissa_ic).map(([k,v])=>[k,T(v.todos.ic),T(v.todos.t),P(v.todos.pos,0),T(v.qualidade.ic),T(v.qualidade.t)]));
 legend('lg3',[['Crescimento do EPS',C[0]],['Re-rating',C[1]],['Dividendos',C[2]]]);
 stacked('c3',Object.entries(D.premissa_decomp).map(([k,v])=>({nome:k,...v})),['eps','rr','div'],C);
 const show=Object.keys(D.nav.series),pal=[css('--ink'),css('--slate'),css('--oxford'),css('--teal'),css('--velvet'),css('--mandarin'),css('--claret')];
 legend('lg4',show.map((k,i)=>[k,pal[i%pal.length]]));
 {const W=1000,H=380,m={l:56,r:20,t:14,b:30};const s=svgBox('c4',W,H);const dt=D.nav.dates.map(v=>new Date(v));
  const all=show.flatMap(k=>D.nav.series[k]).filter(v=>v!=null);const x=d3.scaleTime().domain(d3.extent(dt)).range([m.l,W-m.r]);const y=d3.scaleLinear().domain([0,d3.max(all)*1.05]).range([H-m.b,m.t]).nice();
  s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(v=>'US$ '+v.toFixed(0)).tickSize(-(W-m.l-m.r)));
  s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(10));
  show.forEach((k,i)=>{const pts=D.nav.series[k].map((v,j)=>[dt[j],v]).filter(p=>p[1]!=null);s.append('path').attr('d',d3.line().x(p=>x(p[0])).y(p=>y(p[1]))(pts)).attr('fill','none').attr('stroke',pal[i%pal.length]).attr('stroke-width',k.includes('≥ 3')?3:1.8).attr('stroke-dasharray',k=='S&P 500'?'5 4':null);});}
 const order=['S&P 500','S&P 500 equal weight','OoL antigo','GCGR antigo','OoL novo','GCGR novo','OoL High ROIC (novo)','OoL High Growth (novo)','Cyclicals','Top 20 (original)','ROIC alto descontado (original)'].concat(D.new);
 table('c5',['Carteira','Retorno anual','Peso igual','Volatilidade','Pior queda','Janelas 3a','Janelas 5a','Janelas 10a','Pior janela 3a (p.p./ano)'],order.filter(k=>D.carteiras[k]).map(k=>{const t=D.carteiras[k],e=D.carteiras[k+' (peso igual)'];return [k,P(t.cagr),e?P(e.cagr):'—',P(t.vol),P(t.dd,0),k=='S&P 500'?'—':P(t.w3,0),k=='S&P 500'?'—':P(t.w5,0),k=='S&P 500'?'—':P(t.w10,0),t.p3==null?'—':((t.p3*100>=0?'+':'')+(t.p3*100).toFixed(1)).replace('.',',')];}));
 legend('lg6',[['Crescimento do EPS',C[0]],['Re-rating',C[1]],['Dividendos',C[2]]]);
 stacked('c6',Object.entries(D.decomp).map(([k,v])=>({nome:k,...v['12']})),['eps','rr','div'],C);
 table('c7',['Ação','Empresa','Peso','Gestores'],D.hoje['ROIC alto descontado, ≥ 3 gestores'].map(r=>[r[0],r[1],P(r[2]),r[3]]));
}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>Universo dos Gestores</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__DATA__', json.dumps(d, ensure_ascii=False))
(ROOT / 'universo_gestores.html').write_text(html)
print('ok', len(html))
