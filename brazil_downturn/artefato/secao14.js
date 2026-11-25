
// ================= Parte 3: estrangeiro pelo Formulário de Referência =================
let EF=null, EPF='tem', EANO=null;
function drawEF(){
 const X=EF; if(!X)return; const A=X.agregado, last=A[A.length-1];
 document.getElementById('e-kpis').innerHTML=[
  ['R$ '+F(last.nres_bi,0)+' bi','de estrangeiros nas casas de ações em dez/'+last.y+' ('+P(last.sh)+' do patrimônio delas)'],
  ['−0,64','correlação do fluxo estrangeiro anual com o Ibovespa em dólar (doméstico: −0,23)'],
  ['t = 0,5','sensibilidade do fluxo estrangeiro ao alpha de 12 meses (doméstico: t = 2,6)'],
  ['R$ '+F(X.ticket.mediana_mi,0)+' mi','por investidor não residente, na mediana; '+X.ticket.inv_por_casa_mediana+' investidores por casa']
 ].map(([b,s])=>`<div><b>${b}</b><span>${s}</span></div>`).join('');
 document.getElementById('e-tab').innerHTML='<table><thead><tr><th class="l">Ano</th><th>Casas de ações</th><th>Com estrangeiro</th><th>Estrangeiro (R$ bi)</th><th>% do patrimônio</th><th>Investidores não residentes</th><th>R$ mi por investidor</th><th>5 maiores</th><th>Fluxo estrangeiro</th><th>Fluxo doméstico</th></tr></thead><tbody>'+
  A.map(r=>`<tr><td class="l">${r.y}</td><td class="n">${r.casas}</td><td class="n">${r.casas_com}</td><td class="n">${F(r.nres_bi,1)}</td><td class="n">${P(r.sh)}</td><td class="n">${r.n_inv}</td><td class="n">${F(r.tk_mi,0)}</td><td class="n">${P(r.top5)}</td><td class="n ${r.fr_nres>=0?'pos':'neg'}">${r.fr_nres==null?'—':P(r.fr_nres,1)+' · R$ '+F(r.f_nres_bi,1)+' bi'}</td><td class="n ${r.fr_dom>=0?'pos':'neg'}">${r.fr_dom==null?'—':P(r.fr_dom,1)}</td></tr>`).join('')+'</tbody></table><p class="note">2017 tem menos casas porque muitas gestoras ainda não entregavam o Formulário com a abertura por cliente. Fluxo: a partir de 2018.</p>';
 // dispersão
 {const R=A.filter(r=>r.fr_nres!=null), W=1000,H=340,m={l:56,r:20,t:14,b:40}, s=box('e-sc',W,H), t=tip('e-sc');
  const x=d3.scaleLinear().domain([-.35,.55]).range([m.l,W-m.r]), y=d3.scaleLinear().domain([-.35,.5]).range([H-m.b,m.t]);
  const g=s.append('g').attr('class','grid');y.ticks(6).forEach(v=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(v)).attr('y2',y(v));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(v)+4).attr('text-anchor','end').text(P(v))});
  x.ticks(8).forEach(v=>s.append('text').attr('class','num').attr('x',x(v)).attr('y',H-m.b+18).attr('text-anchor','middle').text(P(v)));
  s.append('text').attr('x',W-m.r).attr('y',H-4).attr('text-anchor','end').text('Ibovespa em dólar no ano →');
  s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
  s.append('line').attr('class','zero').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b);
  R.forEach(r=>{s.append('line').attr('x1',x(r.ibov_usd)).attr('x2',x(r.ibov_usd)).attr('y1',y(r.fr_nres)).attr('y2',y(r.fr_dom)).attr('stroke',css('--rule')).attr('stroke-width',2);
   s.append('circle').attr('cx',x(r.ibov_usd)).attr('cy',y(r.fr_dom)).attr('r',6).attr('fill',css('--bg')).attr('stroke',css('--out')).attr('stroke-width',2);
   s.append('circle').attr('cx',x(r.ibov_usd)).attr('cy',y(r.fr_nres)).attr('r',7).attr('fill',css('--in')).attr('stroke',css('--bg')).attr('stroke-width',2);
   s.append('text').attr('class','lab').attr('x',x(r.ibov_usd)+10).attr('y',y(r.fr_nres)+4).style('font-size','12px').text(r.y);
   s.append('rect').attr('x',x(r.ibov_usd)-14).attr('y',m.t).attr('width',28).attr('height',H-m.t-m.b).attr('fill','transparent').on('mousemove',ev=>show(t,ev,'e-sc',`<b>${r.y}</b>${row('Ibovespa em dólar',P(r.ibov_usd))}${row('Dólar',PP(r.usdbrl,0)+'%')}${row('Fluxo estrangeiro',P(r.fr_nres,1)+' · R$ '+F(r.f_nres_bi,1)+' bi')}${row('Fluxo doméstico',P(r.fr_dom,1)+' · R$ '+F(r.f_dom_bi,1)+' bi')}${row('CDI fim do ano',P(r.cdi,1))}`)).on('mouseleave',()=>t.style('display','none'));});
  const G=X.regimes; document.getElementById('e-reg').innerHTML='<table><thead><tr><th class="l">Regime (ano)</th><th class="l">Estado</th><th class="l">Anos</th><th>Estrangeiro, % ao ano</th><th>Doméstico, % ao ano</th></tr></thead><tbody>'+
   Object.values(G).flatMap(g=>[['alta',0],['baixa',1]].map(([k,i])=>`<tr><td class="l">${i?'':g.nome}</td><td class="l">${g.rot[i]}</td><td class="l">${g[k].anos.join(', ')}</td><td class="n ${g[k].fr_est>=0?'pos':'neg'}">${P(g[k].fr_est,1)}</td><td class="n ${g[k].fr_dom>=0?'pos':'neg'}">${P(g[k].fr_dom,1)}</td></tr>`)).join('')+'</tbody></table>';}
 // sensibilidade
 {const R=[['Estrangeiro',X.sens.estrangeiro],['Doméstico (mesmas casas)',X.sens.domestico]], W=1000,rh=52,m={l:260,r:30,t:6,b:30},H=m.t+m.b+R.length*rh, s=box('e-sens',W,H);
  const x=d3.scaleLinear().domain([-40,70]).range([m.l,W-m.r]);
  const g=s.append('g').attr('class','grid');[-40,-20,0,20,40,60].forEach(v=>{g.append('line').attr('x1',x(v)).attr('x2',x(v)).attr('y1',m.t).attr('y2',H-m.b);s.append('text').attr('class','num').attr('x',x(v)).attr('y',H-8).attr('text-anchor','middle').text(v)});
  R.forEach(([n,o],i)=>{const y0=m.t+i*rh;s.append('text').attr('class','lab').attr('x',m.l-12).attr('y',y0+rh/2+4).attr('text-anchor','end').text(n);
   [['a12','--in',0],['a36','--ink2',1]].forEach(([c,cl,j])=>{const v=o[c],se=Math.abs(v.b/v.t),yy=y0+12+j*16;
    s.append('rect').attr('x',Math.min(x(0),x(v.b))).attr('y',yy).attr('width',Math.abs(x(v.b)-x(0))).attr('height',12).attr('rx',2).attr('fill',css(cl)).attr('opacity',Math.abs(v.t)>=2?1:.35);
    s.append('line').attr('x1',x(Math.max(-40,v.b-1.96*se))).attr('x2',x(Math.min(70,v.b+1.96*se))).attr('y1',yy+6).attr('y2',yy+6).attr('stroke',css('--ink'));
    s.append('text').attr('class','num').attr('x',x(Math.min(70,v.b+1.96*se))+6).attr('y',yy+10).text(F(v.b,0)+' p.p. (t '+F(v.t,1)+')');});});
  s.append('line').attr('class','zero').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b);}
 // perfil
 const PFS={tem:[X.perfil_tem,'Tem estrangeiro','Não tem'],rec:[X.perfil_rec,'Recebeu','Perdeu'],ruim:[X.perfil_rec_ruim,'Recebeu','Perdeu']}[EPF];
 if(PFS[0]){const order=['ex12_l','ex36_l','pl_ant','top10','n_acoes','beta36_l','vol36_l','te36_l','idade','sh_lb_l','consenso','dep'];
  dumbbell('e-pf',order.filter(a=>PFS[0][a]).map(a=>({nome:X.attr[a],w:PFS[0][a].w,l:PFS[0][a].l,t:PFS[0][a].t!=null&&Math.abs(PFS[0][a].t)<1e6?PFS[0][a].t:null,extra:row('Anos com o mesmo sinal',PFS[0][a].same+' de '+PFS[0][a].ny)})),[PFS[1]+' (percentil médio)',PFS[2]]);document.getElementById('e-pf-l1').textContent=PFS[1];document.getElementById('e-pf-l2').textContent=PFS[2];}
 // listas por ano
 const anos=Object.keys(X.tops).sort(), sel=document.getElementById('e-ano'); if(!EANO)EANO=anos[anos.length-1];
 sel.innerHTML=anos.slice().reverse().map(a=>`<option value="${a}">${a}</option>`).join(''); sel.value=EANO; sel.onchange=()=>{EANO=sel.value;drawEF();};
 const T=X.tops[EANO], ag=A.find(r=>String(r.y)==EANO)||{};
 document.getElementById('e-ano-s').innerHTML=`Em <b>${EANO}</b>: ${T.n_rec} casas receberam R$ ${F(T.rec_bi,1)} bi de estrangeiros e ${T.n_saq} perderam R$ ${F(-T.saq_bi,1)} bi. Ibovespa em dólar ${P(ag.ibov_usd)}, dólar ${PP(ag.usdbrl,0)}%.`;
 const tb=L=>'<table><thead><tr><th class="l">Gestora</th><th>R$ mi</th><th>% da posição</th><th>Posição no fim (R$ mi)</th><th>Investidores</th><th>Alpha 12m</th></tr></thead><tbody>'+L.map(r=>`<tr><td class="l">${r.nome}</td><td class="n ${r.f_mi>=0?'pos':'neg'}">${r.f_mi.toLocaleString('pt-BR')}</td><td class="n">${r.pct==null?'nova':P(r.pct,0)}</td><td class="n">${r.pos_mi.toLocaleString('pt-BR')}</td><td class="n">${r.n_inv}</td><td class="n">${r.a12==null?'—':PP(r.a12,0)}</td></tr>`).join('')+'</tbody></table>';
 document.getElementById('e-rec').innerHTML=tb(T.rec); document.getElementById('e-saq').innerHTML=tb(T.saq);
 const Mx=X.maiores[EANO]||[];
 document.getElementById('e-mai').innerHTML='<table><thead><tr><th class="l">Gestora</th><th>Estrangeiro (R$ mi)</th><th>% do patrimônio da casa</th><th>Investidores</th><th>R$ mi por investidor</th></tr></thead><tbody>'+Mx.map(r=>`<tr><td class="l">${r.nome}</td><td class="n">${r.pos_mi.toLocaleString('pt-BR')}</td><td class="n">${P(r.sh)}</td><td class="n">${r.n_inv}</td><td class="n">${F(r.tk_mi,0)}</td></tr>`).join('')+'</tbody></table>';
}
document.querySelectorAll('#e-pf-seg button').forEach(b=>b.onclick=()=>{EPF=b.dataset.k;document.querySelectorAll('#e-pf-seg button').forEach(x=>x.setAttribute('aria-pressed',x===b));drawEF();});
fetch('data/estrangeiro_fre.json').then(r=>r.json()).then(j=>{EF=j;drawEF();}).catch(()=>{});
