"""Relatório FT do ramo A (crescimento previsível): relatorio/crescimento_previsivel.html a partir de dados_crescimento.json."""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_crescimento.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>')] + '@media print{.page{max-width:none}figure{break-inside:avoid}}</style>'
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
n2 = lambda x, n=2: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')
SC, SA = 'Sem cíclicas e vestuário', 'Todas'
E = d['eps'][SC]; Rv = d['receita'][SC]; Lv = d['alavancagem'][SC]; T = d['carteiras']
med3 = E['12']['Mediana de 5 anos do EPS (o nosso)']; g3 = E['12']['g normalizado do P/E justo']; k3 = E['12']['Constante de 8%']
rv3 = E['12']['Mediana de 5 anos da receita']; rr3 = Rv['12']['Mediana de 5 anos da receita']; lv3 = Lv['12']
t_reg, t_v1a = T['Top 20 · Registrada'], T['Top 20 · V1a receita no valuation']
sn = d['sem_nvda']; v1 = d['v1_coef']
form = lambda r: '—' if r.get('a') is None else f"{n2(r['a'] * 100, 1)}% {'+' if r['b'] >= 0 else '−'} {n2(abs(r['b']))}·x"

body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Ramo A · crescimento previsível · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">O lucro dá para prever?</div>
<h1>O lucro passado não prevê o lucro futuro. A receita prevê um pouco</h1>
<p class="deck">Mesmo sem os setores cíclicos, a mediana de cinco anos do EPS não diz nada sobre os próximos três. A receita é mais comportada e tem sinal, mas fraco. Na carteira, trocar o crescimento do EPS pelo da receita no valuation rendeu dois pontos a mais na Top 20 e piorou a "ROIC alto descontado": sem ganho robusto.</p>
<div class="byline">S&amp;P 500 point-in-time, só dados arquivados até cada data · crescimento realizado = variação anual do último EPS (ou receita) anual conhecido · R² e fórmulas com os valores limitados a −50%..100%</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra no P/E justo, no filtro e no desconto das carteiras testadas na parte 4. As partes 1 a 3 não dependem dele. Backtest; não é recomendação de investimento.</p>
<div class="big">
 <div><b>{n2(med3['ic'])}</b><span>correlação de ordem entre a mediana do EPS e o crescimento dos 3 anos seguintes, já sem cíclicas</span></div>
 <div><b>{pc(rr3['r2'], 1)}</b><span>R² da receita passada prevendo a receita futura (ordem {n2(rr3['ic'])})</span></div>
 <div><b>{n2(lv3['b'])}×</b><span>alavancagem operacional: EPS = {pc(lv3['a'])} + {n2(lv3['b'])} × receita (3 anos, R² {pc(lv3['r2'], 0)})</span></div>
 <div><b>{pc(t_v1a['cagr'])}</b><span>Top 20 com a receita no valuation, contra {pc(t_reg['cagr'])} da registrada</span></div>
</div>

<h2 class="chap" style="margin-top:44px">1. Tirar os cíclicos não salva a mediana do EPS</h2>
<figure><figcaption class="t">A correlação continua negativa sem cíclicos e sem financeiras</figcaption>
<figcaption class="s">Mediana de 5 anos do crescimento do EPS como previsão do crescimento anual dos anos seguintes. Fórmula: realizado = a + b × previsto. Ordem = correlação de ordem média por trimestre (t ajustado pela sobreposição).</figcaption>
<div id="t1" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>Você tinha razão em desconfiar: com os cíclicos, a correlação de 3 anos era {n2(d['eps'][SA]['12']['Mediana de 5 anos do EPS (o nosso)']['ic'])}. Sem eles ficou em {n2(med3['ic'])}, e sem financeiras, em {n2(d['eps']['Sem cíclicas, vestuário e financeiras']['12']['Mediana de 5 anos do EPS (o nosso)']['ic'])}. A queda é pequena e o sinal continua negativo, com t perto de −4: não é só ruído. O R² fica em torno de 1,5%. Para fins práticos, a mediana do EPS não prevê nada. O sinal levemente negativo vem da volta à média: quem cresceu muito tende a crescer menos.</span></div>
</figure>

<h2 class="chap" style="margin-top:44px">2. O g normalizado do P/E justo</h2>
<figure><figcaption class="t">O g erra menos que a mediana, mas só porque fica perto da média</figcaption>
<figcaption class="s">Sem cíclicas e vestuário. Erro = mediana do |realizado − previsto|. Viés = mediana de (realizado − previsto); positivo quer dizer que o preditor subestima.</figcaption>
<div id="t2" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>O g é a posição da mediana num ranking, convertida para uma escala de 7% a 3,5%. Por isso ele <b>ordena as empresas exatamente como a mediana</b>: a correlação de ordem é a mesma ({n2(g3['ic'])} contra {n2(med3['ic'])}). O que muda é a escala. Como o g espreme todo mundo entre 3,5% e 7%, ele erra pouco ({pc(g3['mae'])}, contra {pc(med3['mae'])} da mediana), praticamente o mesmo que chutar 8% para todas ({pc(k3['mae'])}). Esse erro menor não é previsão: é só ficar perto da média. O viés de {pp(g3['vies'])} mostra que o g subestima o crescimento típico, que ficou perto de {pc(g3['real_med'], 0)} ao ano. A fórmula ajustada (realizado = {form(g3)}) tem inclinação negativa: mais g, menos crescimento.</span></div>
</figure>

<h2 class="chap" style="margin-top:44px">3. A receita é mais comportada</h2>
<figure><figcaption class="t">Ordenando pela receita, o crescimento futuro sobe; ordenando pelo EPS, cai</figcaption>
<figcaption class="s">Quintos do preditor em cada trimestre (sem cíclicas e vestuário) e o crescimento anual realizado em 3 anos (medianas).</figcaption>
<div class="legend" id="lg3"></div><div id="c3"></div>
<div class="sowhat"><b>E daí</b><span>A receita passada prevê a receita futura: correlação de ordem {n2(rr3['ic'])}, R² {pc(rr3['r2'], 1)}, receita futura = {form(rr3).replace('x', 'receita passada')}. O quinto que crescia {pc(d['quintis']['Receita pela mediana da receita'][4][0], 0)} continuou crescendo {pc(d['quintis']['Receita pela mediana da receita'][4][1], 0)}, contra {pc(d['quintis']['Receita pela mediana da receita'][0][1], 0)} do quinto mais lento. Ela também prevê o EPS com o sinal certo (ordem {n2(rv3['ic'])}, R² {pc(rv3['r2'], 1)}), mas fraco: o erro ({pc(rv3['mae'])}) ainda é maior que o da constante de 8%. A dispersão ano a ano do crescimento da receita é de {pc(d['dispersao']['rev_iqr'], 0)}, contra {pc(d['dispersao']['eps_iqr'], 0)} do EPS.</span></div>
</figure>
<figure><figcaption class="t">Preditores do crescimento: R², fórmula e erro</figcaption>
<figcaption class="s">Sem cíclicas e vestuário. "EPS" = crescimento futuro do EPS; "Receita" = crescimento futuro da receita. 1, 3 e 5 anos.</figcaption>
<div id="t3" class="tablebox"></div>
</figure>
<figure><figcaption class="t">Alavancagem operacional: cada ponto de receita vira ~0,7 ponto de EPS, mais 7% ao ano</figcaption>
<figcaption class="s">No mesmo período: crescimento anual do EPS = a + b × crescimento anual da receita.</figcaption>
<div id="t4" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>O intercepto de ~{pc(lv3['a'], 0)} é o lucro por ação que cresce mesmo com a receita parada: recompras, margem e alavancagem financeira. A inclinação abaixo de 1 parece contradizer a alavancagem operacional, mas é efeito do ruído do EPS, que achata a reta. A correlação de ordem de {n2(lv3['ic'])} mostra que, no mesmo período, a receita explica bem mais do EPS do que qualquer previsão feita antes.</span></div>
</figure>

<h2 class="chap" style="margin-top:44px">4. E na carteira?</h2>
<figure><figcaption class="t">Receita no valuation: +2 pontos na Top 20, −4 na "ROIC alto descontado"</figcaption>
<figcaption class="s">Variantes pré-registradas em 18/11: V1a usa o crescimento do EPS previsto pela receita (a = {pc(v1['a'])}, b = {n2(v1['b'])}, estimados em 2011–2018) no P/E justo e no retorno esperado; V1b também troca o filtro para receita ≥ 10%; V2 não prevê crescimento (g igual para todas, 8% no retorno). Raiz do valor de mercado com teto de 10%; trimestral.</figcaption>
<div class="legend" id="lg5"></div><div id="c5"></div>
<div id="t5" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>A Top 20 com a receita no valuation (V1a) fez {pc(t_v1a['cagr'])} ao ano, contra {pc(t_reg['cagr'])} da registrada, com janelas parecidas ({pc(t_v1a['w3'], 0)} das de 3 anos acima do S&amp;P). Sem NVIDIA: {pc(sn['sem'])}. Mas a mesma troca <b>piorou</b> a "ROIC alto descontado" ({pc(T['ROIC alto descontado · V1a receita no valuation']['cagr'])} contra {pc(T['ROIC alto descontado · Registrada']['cagr'])}). Tirar a previsão de crescimento (V2) deu o mesmo padrão. E trocar o filtro do EPS pela receita (V1b) piorou as duas. Duas conclusões honestas:
(1) o ganho da V1a na Top 20 está dentro do que se espera de testar seis variantes, e não se repetiu na outra carteira, então não é robusto;
(2) o filtro de crescimento do EPS ≥ 15% <b>ajuda</b> a carteira mesmo sem prever o lucro. Ele parece selecionar qualidade e o re-rating que vem com ela, não crescimento futuro.</span></div>
</figure>
<figure><figcaption class="t">De onde veio o retorno das variantes (3 anos)</figcaption>
<figcaption class="s">Decomposição do retorno anual em 3 anos e o crescimento da receita previsto contra o realizado (medianas das posições).</figcaption>
<div id="t6" class="tablebox"></div>
</figure>

<section class="verdict"><h2>O veredito</h2><div class="vgrid">
 <div><span class="tag" style="--c:var(--claret)">EPS</span><h4>A mediana do EPS não prevê, nem sem cíclicos</h4><p>Correlação {n2(med3['ic'])} e R² de {pc(med3['r2'], 1)} em 3 anos. Sem cíclicos melhora pouco. Não é contaminação, é volta à média.</p></div>
 <div><span class="tag" style="--c:var(--oxford)">g normalizado</span><h4>Mesma ordem, erro menor só por ficar perto da média</h4><p>Ordena como a mediana ({n2(g3['ic'])}). Erra {pc(g3['mae'])}, como a constante de 8%. Subestima o crescimento típico em {pp(g3['vies'], 0)}.</p></div>
 <div><span class="tag" style="--c:var(--teal)">Receita</span><h4>Persiste e tem o sinal certo, mas é fraca para o EPS</h4><p>Receita → receita: ordem {n2(rr3['ic'])}, R² {pc(rr3['r2'], 1)}. Receita → EPS: ordem {n2(rv3['ic'])}, R² {pc(rv3['r2'], 1)}. Alavancagem: EPS ≈ {pc(lv3['a'], 0)} + {n2(lv3['b'], 1)} × receita.</p></div>
 <div><span class="tag" style="--c:var(--wheat)">Carteira</span><h4>Sem troca por enquanto</h4><p>A receita no valuation ajudou a Top 20 (+2 p.p.) e atrapalhou a "descontada" (−4 p.p.). Fica registrada como exploratória; o filtro do EPS ≥ 15% continua.</p></div>
</div></section>
<p class="method" style="margin-top:30px"><b>Método.</b> Painel trimestral do S&amp;P 500 point-in-time ({d['periodo'][0]} a {d['periodo'][1]}). Crescimento realizado = (último EPS anual conhecido em t+h ÷ conhecido em t)^(1/anos) − 1, só com EPS positivo nas duas pontas; receita da SEC (Revenues e equivalentes) com a data de arquivamento. Mediana de 5 anos = mediana dos 5 crescimentos anuais com base positiva (mínimo 3). R² e fórmula: regressão agrupada com os valores limitados a −50%..100%. Correlação de ordem: Spearman por trimestre, média, com t ajustado pela sobreposição. Código: <code>relatorio/ramo_crescimento.py</code>.</p>
</div>'''

js = r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const D=__DATA__;
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const P=(x,n=1)=>x==null?'—':(x*100).toFixed(n).replace('.',',')+'%';
const N=(x,n=2)=>x==null?'—':x.toFixed(n).replace('.',',');
const F=r=>r.a==null?'—':`${(r.a*100).toFixed(1).replace('.',',')}% ${r.b>=0?'+':'−'} ${Math.abs(r.b).toFixed(2).replace('.',',')}·x`;
function svgBox(id,w,h){const el=d3.select('#'+id);el.selectAll('*').remove();return el.append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img');}
function legend(id,items){document.getElementById(id).innerHTML=items.map(([n,c])=>`<span><i style="--c:${c};height:10px"></i>${n}</span>`).join('');}
function table(id,head,rows){const el=document.getElementById(id);el.innerHTML='<table><thead><tr>'+head.map((h,i)=>`<th class="${i==0?'l':''}">${h}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map((c,i)=>`<td class="${i==0?'l':'n'}">${c}</td>`).join('')+'</tr>').join('')+'</tbody></table>';}
function bars(id,cats,series,cols){const W=1000,H=300,m={l:56,r:16,t:16,b:44};const s=svgBox(id,W,H);const all=series.flat();
 const x0=d3.scaleBand().domain(cats).range([m.l,W-m.r]).padding(.22);const x1=d3.scaleBand().domain(d3.range(series.length)).range([0,x0.bandwidth()]).padding(.08);
 const y=d3.scaleLinear().domain([Math.min(0,d3.min(all))*1.15,d3.max(all)*1.15]).range([H-m.b,m.t]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(v=>P(v,0)).tickSize(-(W-m.l-m.r)));
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x0).tickSize(0)).selectAll('text').style('font-size','13px').attr('dy','1.2em');
 series.forEach((ser,j)=>ser.forEach((v,i)=>{s.append('rect').attr('x',x0(cats[i])+x1(j)).attr('width',x1.bandwidth()).attr('y',y(Math.max(0,v))).attr('height',Math.abs(y(v)-y(0))).attr('fill',cols[j]);
  s.append('text').attr('class','num').attr('x',x0(cats[i])+x1(j)+x1.bandwidth()/2).attr('y',v>=0?y(v)-4:y(v)+13).attr('text-anchor','middle').style('font-size','11px').text(P(v,0));}));
 s.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0)).attr('stroke',css('--ink'));}
function lines(id,dates,series,cols){const W=1000,H=360,m={l:60,r:16,t:12,b:30};const s=svgBox(id,W,H);const dt=dates.map(d=>new Date(d));
 const x=d3.scaleTime().domain(d3.extent(dt)).range([m.l,W-m.r]);const ys=Object.values(series).flat().filter(v=>v!=null);
 const y=d3.scaleLog().domain([d3.min(ys)*.95,d3.max(ys)*1.05]).range([H-m.b,m.t]);
 s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6,'~g').tickFormat(v=>v.toFixed(0)+'×').tickSize(-(W-m.l-m.r)));
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(8));
 Object.entries(series).forEach(([k,v],i)=>{const pts=v.map((y_,j)=>[dt[j],y_]).filter(p=>p[1]!=null);
  s.append('path').attr('d',d3.line().x(p=>x(p[0])).y(p=>y(p[1]))(pts)).attr('fill','none').attr('stroke',cols[i]).attr('stroke-width',k.includes('S&P')?2:2.2).attr('stroke-dasharray',k.includes('S&P')?'5 4':null);
});}
function draw(){
 const SC='Sem cíclicas e vestuário',H=['4','12'];const lab={4:'1 ano',12:'3 anos',20:'5 anos'};
 const MED='Mediana de 5 anos do EPS (o nosso)';
 table('t1',['Amostra','Horizonte','R²','Fórmula (x = mediana)','Ordem','t','Erro','Viés'],Object.keys(D.eps).flatMap(am=>H.map(h=>{const r=D.eps[am][h][MED];return [am,lab[h],P(r.r2,1),F(r),N(r.ic),N(r.ic_t,1),P(r.mae),P(r.vies)];})));
 const PR=['Mediana de 5 anos do EPS (o nosso)','g normalizado do P/E justo','Constante de 8%','Mediana de 5 anos da receita','Receita do último ano'];
 table('t2',['Preditor do EPS','Horizonte','R²','Fórmula','Ordem','Erro','Erro se calibrado','Viés'],H.flatMap(h=>PR.map(k=>{const r=D.eps[SC][h][k];return [k,lab[h],P(r.r2,1),F(r),N(r.ic),P(r.mae),P(r.mae_cal),P(r.vies)];})));
 const q=D.quintis,C=[css('--claret'),css('--oxford'),css('--teal')];legend('lg3',[['EPS ordenado pela mediana do EPS',C[0]],['EPS ordenado pela mediana da receita',C[1]],['Receita ordenada pela mediana da receita',C[2]]]);
 bars('c3',['1º quinto (mais lento)','2º','3º','4º','5º (mais rápido)'],[q['EPS pela mediana do EPS'].map(r=>r[1]),q['EPS pela mediana da receita'].map(r=>r[1]),q['Receita pela mediana da receita'].map(r=>r[1])],C);
 const rows=[];['4','12','20'].forEach(h=>{['Mediana de 5 anos da receita','Receita do último ano','Constante de 8%'].forEach(k=>{const r=D.receita[SC][h][k];rows.push(['Receita ← '+k,lab[h],P(r.r2,1),F(r),N(r.ic),P(r.mae),P(r.vies)]);});
  ['Mediana de 5 anos da receita','Mediana de 5 anos do EPS (o nosso)','Constante de 8%'].forEach(k=>{const r=D.eps[SC][h][k];rows.push(['EPS ← '+k,lab[h],P(r.r2,1),F(r),N(r.ic),P(r.mae),P(r.vies)]);});});
 table('t3',['Previsto ← preditor','Horizonte','R²','Fórmula','Ordem','Erro','Viés'],rows);
 table('t4',['Amostra','Horizonte','Fórmula (x = receita no mesmo período)','R²','Ordem'],Object.keys(D.alavancagem).flatMap(am=>['4','12','20'].map(h=>{const r=D.alavancagem[am][h];return [am,lab[h],F(r).replace('x','receita'),P(r.r2,1),N(r.ic)];})));
 const ks=Object.keys(D.nav.series);const pal=[css('--ink2'),css('--oxford'),css('--jade'),css('--teal'),css('--mandarin'),css('--claret')];
 const keep=['S&P 500','Top 20 · Registrada','Top 20 · V1a receita no valuation','Top 20 · V2 sem previsão de crescimento','ROIC alto descontado · Registrada','ROIC alto descontado · V1a receita no valuation'];
 const ser={};keep.forEach(k=>ser[k]=D.nav.series[k]);legend('lg5',keep.map((k,i)=>[k,pal[i]]));lines('c5',D.nav.dates,ser,pal);
 const T=D.carteiras;const order=['S&P 500','S&P 500 equal weight','OoL antigo','GCGR antigo','OoL novo','GCGR novo','OoL High ROIC (novo)','OoL High Growth (novo)','Cyclicals'].concat(Object.keys(T).filter(k=>k.includes(' · ')));
 table('t5',['Carteira','Retorno anual','Volatilidade','Pior queda','Janelas 3a > S&P','5a','10a','Pior janela 3a'],order.map(k=>{const t=T[k];return [k.includes(' · ')?`<b>${k}</b>`:k,P(t.cagr),P(t.vol),P(t.dd,0),k=='S&P 500'?'—':P(t.w3,0),k=='S&P 500'?'—':P(t.w5,0),k=='S&P 500'?'—':P(t.w10,0),k=='S&P 500'?'—':((t.p3>=0?'+':'')+(t.p3*100).toFixed(1)).replace('.',',')+' p.p.'];}));
 table('t6',['Carteira','EPS a.a.','Re-rating a.a.','Dividendos','Total','Receita prevista','Receita realizada','EPS realizado'],Object.entries(D.decomp).map(([k,v])=>[k,P(v.eps),P(v.rr),P(v.div),P(v.tot),P(v.rev_prev),P(v.rev_real),P(v.eps_real)]));
 window.__drawn=true;}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>Crescimento previsível</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__DATA__', json.dumps(d, ensure_ascii=False))
(ROOT / 'crescimento_previsivel.html').write_text(html)
print('ok', len(html))
