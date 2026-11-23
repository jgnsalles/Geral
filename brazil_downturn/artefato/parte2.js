// ================= Parte 2: por tipo de investidor =================
const ST={tipo:'total',rg:'fluxo',est:'todos',hz:'ex12',drv:'cdi',jan:'12'};
const key=()=>ST.est=='todos'?'todos':`${ST.rg}:${ST.est}`;
const NM=k=>window.P2.nomes[k];
const estLbl=e=>e=='todos'?'Todos os trimestres':window.P2.estados[ST.rg][e=='alta'?0:1];
function ctl(){
 const X=window.P2, st=document.getElementById('sel-tipo'), sr=document.getElementById('sel-reg');
 st.innerHTML=X.tipos.map(k=>`<option value="${k}">${X.nomes[k]}</option>`).join('');
 sr.innerHTML=Object.entries(X.regimes).map(([k,v])=>`<option value="${k}">${v}</option>`).join('');
 st.value=ST.tipo; sr.value=ST.rg;
 st.onchange=()=>{ST.tipo=st.value;drawP2();}; sr.onchange=()=>{ST.rg=sr.value;drawP2();};
 document.querySelectorAll('#seg-jan button').forEach(b=>b.onclick=()=>{ST.jan=b.dataset.k;document.querySelectorAll('#seg-jan button').forEach(x=>x.setAttribute('aria-pressed',x===b));pflow();});
 document.querySelectorAll('#seg-hz button').forEach(b=>b.onclick=()=>{ST.hz=b.dataset.k;document.querySelectorAll('#seg-hz button').forEach(x=>x.setAttribute('aria-pressed',x===b));pquint();});
}
function segEst(){
 const el=document.getElementById('seg-est'), X=window.P2, n=X.n_estado[ST.rg];
 el.innerHTML=[['todos','Todos'],['alta',X.estados[ST.rg][0]+' ('+(n.alta||0)+')'],['baixa',X.estados[ST.rg][1]+' ('+(n.baixa||0)+')']].map(([k,l])=>`<button type="button" data-k="${k}" aria-pressed="${ST.est==k}">${l}</button>`).join('');
 el.querySelectorAll('button').forEach(b=>b.onclick=()=>{ST.est=b.dataset.k;drawP2();});
 document.getElementById('now').innerHTML=`Vendo <b>${NM(ST.tipo)}</b> · <b>${estLbl(ST.est)}</b>`;
}
function inState(q){const X=window.P2,r=(ST.tipo=='total'?X.serie_longa:X.trimestres).find(x=>x.q==q);if(!r)return false;const e=ST.est=='todos'?'alta':ST.est;return r['st_'+ST.rg]==e;}
// "Todos" usa a série longa do Informe Diário (2006T1–2026T3); os tipos começam em 2019 porque o Perfil Mensal começa em 2019
function serieFlow(){const X=window.P2,k=ST.tipo;if(k=='total')return {S:X.serie_longa.map(r=>({q:r.q,v:{fr:r.fr,f:r.f,h:r.h,pos:r.pos}})),T:X.serie_longa};return {S:X.serie.map(r=>({q:r.q,v:r[k]})),T:X.trimestres};}
// janela de 12 meses: soma dos fluxos dos 4 últimos trimestres / posição no início do primeiro deles (posição = fluxo / taxa)
function janela(S){if(ST.jan!='12')return S;return S.map((r,i)=>{if(i<3)return {q:r.q,v:{...r.v,fr:null}};const w=S.slice(i-3,i+1);const b=w[0].v.fr?w[0].v.f/w[0].v.fr:null;const f=d3.sum(w,z=>z.v.f||0);
 return {q:r.q,v:{...r.v,f:f,fr:b&&w.every(z=>z.v.fr!=null)?f/b:null,pos:r.v.pos}};});}

function pflow(){
 const X=window.P2, k=ST.tipo, {S:S0,T}=serieFlow(), S=janela(S0), W=1000,H=426,m={l:52,r:12,t:40,b:26},h1=250,gap=30,h2=H-m.t-m.b-h1-gap;
 document.getElementById('ft-flow').textContent=(ST.jan=='12'?'Fluxo em 12 meses: ':'Fluxo trimestral: ')+NM(k)+(k=='total'?' (2006–2026)':' (2019–2026)');
 const s=box('p-flow',W,H), t=tip('p-flow');
 const x=d3.scaleBand().domain(S.map(r=>r.q)).range([m.l,W-m.r]).padding(S.length>40?.12:.18);
 const v=S.map(r=>r.v.fr).filter(z=>z!=null), vp=v.filter(z=>z>0).sort(d3.ascending), vn=v.filter(z=>z<0).map(Math.abs).sort(d3.ascending);
 const eU=Math.max(.04,(d3.quantile(vp,.92)||0)*1.15), eD=Math.max(.04,(d3.quantile(vn,.92)||0)*1.15);
 const y=d3.scaleLinear().domain([-eD,eU]).range([m.t+h1,m.t]).clamp(true);
 const over=fr=>fr!=null&&(fr>eU||fr<-eD);
 // marca o valor só no pico de cada sequência de barras que passam da escala
 const peak=new Set();{let run=[];const flush=()=>{if(run.length){peak.add(run.reduce((a,b)=>Math.abs(b.v.fr)>Math.abs(a.v.fr)?b:a).q);run=[];}};S.forEach(r=>{if(over(r.v.fr)&&(!run.length||Math.sign(run[0].v.fr)==Math.sign(r.v.fr)))run.push(r);else{flush();if(over(r.v.fr))run.push(r);}});flush();}
 S.forEach(r=>{if(inState(r.q))s.append('rect').attr('x',x(r.q)-x.step()*x.paddingInner()/2).attr('y',m.t).attr('width',x.step()).attr('height',H-m.t-m.b).attr('fill',css('--soft'));});
 const g=s.append('g').attr('class','grid');y.ticks(6).forEach(tv=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(tv)).attr('y2',y(tv));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(tv)+4).attr('text-anchor','end').text(P(tv))});
 const every=S.length>40?2:1;
 S.forEach(r=>{const fr=r.v.fr;if(r.q.endsWith('Q1')&&(+r.q.slice(0,4))%every==0)s.append('text').attr('x',x(r.q)+x.bandwidth()/2).attr('y',H-6).attr('text-anchor','middle').text(r.q.slice(0,4));if(fr==null)return;const top=Math.min(y(fr),y(0)),hh=Math.max(1,Math.abs(y(fr)-y(0)));
  s.append('rect').attr('x',x(r.q)).attr('y',top).attr('width',x.bandwidth()).attr('height',hh).attr('rx',x.bandwidth()>8?2:1).attr('fill',css(fr>=0?'--in':'--out'));
  if(over(fr)){const cx=x(r.q)+x.bandwidth()/2, up=fr>0, ye=up?m.t:m.t+h1, d=up?-1:1, sz=Math.max(3.5,Math.min(7,x.bandwidth()/2+.5));
   s.append('path').attr('d',`M${cx-sz},${ye} L${cx+sz},${ye} L${cx},${ye+d*sz*1.4}Z`).attr('fill',css('--ink'));
   if(peak.has(r.q))s.append('text').attr('class','num').attr('x',cx).attr('y',up?ye-sz*1.4-3:ye+sz*1.4+11).attr('text-anchor','middle').style('fill',css('--ink')).style('font-size','10.5px').style('font-weight',600).text(PP(fr,0)+'%');}});
 s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
 const y0=m.t+h1+gap, y2=d3.scaleLinear().domain([0,.16]).range([y0+h2,y0]);
 [0,.08,.16].forEach(tv=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y2(tv)).attr('y2',y2(tv));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y2(tv)+4).attr('text-anchor','end').text(P(tv))});
 s.append('path').attr('d',d3.line().defined(r=>r.cdi!=null).x(r=>x(r.q)+x.bandwidth()/2).y(r=>y2(r.cdi))(T.filter(r=>x(r.q)!=null))).attr('fill','none').attr('stroke',css('--ink')).attr('stroke-width',2);
 S.forEach(r=>{const tr=T.find(z=>z.q==r.q)||{};s.append('rect').attr('x',x(r.q)-x.step()*x.paddingInner()/2).attr('y',m.t).attr('width',x.step()).attr('height',H-m.t-m.b).attr('fill','transparent')
  .on('mousemove',ev=>show(t,ev,'p-flow',`<b>${r.q.replace('Q','T')}</b>${row(ST.jan=='12'?'Fluxo em 12 meses':'Fluxo no trimestre',P(r.v.fr,1)+' da posição')}${row('Em reais','R$ '+F(r.v.f,2)+' bi')}${row('Posição no fim','R$ '+F(r.v.h,1)+' bi')}${row('Gestoras com entrada',P(r.v.pos))}${row('Ibovespa no trimestre',P(tr.ibov_q,1))}${row('CDI',P(tr.cdi,1))}${row('Treasury 10a',tr.ust==null?'—':P(tr.ust,2))}`)).on('mouseleave',()=>t.style('display','none'));});
 const SS=X.serie;
 // composição
 const f0=SS[0],f1=SS[SS.length-1], tot0=f0.total.h, tot1=f1.total.h;
 document.getElementById('p-comp').innerHTML='<table><thead><tr><th class="l">Tipo de passivo</th><th>% do passivo em '+f0.q.replace('Q','T')+'</th><th>% em '+f1.q.replace('Q','T')+'</th><th>Fluxo acumulado (R$ bi)</th><th>Fluxo / posição média</th></tr></thead><tbody>'+
  X.tipos.filter(z=>z!='total').map(z=>{const acc=d3.sum(SS,r=>r[z].f||0), mean=d3.mean(SS,r=>r[z].h);return `<tr${z==k?' style="font-weight:600"':''}><td class="l">${NM(z)}</td><td class="n">${P(f0[z].h/tot0,1)}</td><td class="n">${P(f1[z].h/tot1,1)}</td><td class="n ${acc>=0?'pos':'neg'}">${F(acc,1)}</td><td class="n">${P(acc/mean,0)}</td></tr>`}).join('')+'</tbody></table>';
}

function pbutter(){
 const X=window.P2, E=X.estados_agg[ST.rg], ks=X.tipos, lab=X.estados[ST.rg], W=1000,rh=20,gap=14,m={l:270,r:30,t:30,b:28};
 const H=m.t+m.b+ks.length*(2*rh+gap), s=box('p-butter',W,H), t=tip('p-butter');
 const all=ks.flatMap(k=>['alta','baixa'].flatMap(e=>[E[e][k].inv,E[e][k].tira])); const ext=Math.min(.35,Math.max(.12,d3.max(all.map(Math.abs))*1.05));
 const x=d3.scaleLinear().domain([-ext,ext]).range([m.l,W-m.r]).clamp(true);
 const g=s.append('g').attr('class','grid');x.ticks(8).forEach(tv=>{g.append('line').attr('x1',x(tv)).attr('x2',x(tv)).attr('y1',m.t).attr('y2',H-m.b);s.append('text').attr('class','num').attr('x',x(tv)).attr('y',H-8).attr('text-anchor','middle').text(P(tv))});
 s.append('text').attr('x',x(-ext)).attr('y',14).text('← tirou');s.append('text').attr('x',x(ext)).attr('y',14).attr('text-anchor','end').text('investiu →');
 ks.forEach((k,i)=>{const y0=m.t+i*(2*rh+gap), sel=k==ST.tipo;
  if(sel)s.append('rect').attr('x',0).attr('y',y0-4).attr('width',W).attr('height',2*rh+8).attr('fill',css('--soft'));
  s.append('text').attr('class','lab').attr('x',m.l-12).attr('y',y0+rh+4).attr('text-anchor','end').style('font-weight',sel?600:400).text(NM(k).replace(' (private banks e family offices, via fundo)',' (PB e MFO)'));
  ['alta','baixa'].forEach((e,j)=>{const r=E[e][k], yy=y0+j*rh+2, hh=rh-5;
   s.append('text').attr('class','num').attr('x',m.l-4).attr('y',yy+hh-3).attr('text-anchor','end').style('font-size','10px').text(j?'▼':'▲');
   s.append('rect').attr('x',x(r.tira)).attr('y',yy).attr('width',x(0)-x(r.tira)).attr('height',hh).attr('rx',2).attr('fill',css('--out')).attr('opacity',j?.6:1);
   s.append('rect').attr('x',x(0)).attr('y',yy).attr('width',x(r.inv)-x(0)).attr('height',hh).attr('rx',2).attr('fill',css('--in')).attr('opacity',j?.6:1);
   s.append('rect').attr('x',x(r.fr)-1.5).attr('y',yy-2).attr('width',3).attr('height',hh+4).attr('fill',css('--ink'));
   s.append('rect').attr('x',m.l).attr('y',yy).attr('width',W-m.l-m.r).attr('height',rh).attr('fill','transparent')
    .on('mousemove',ev=>show(t,ev,'p-butter',`<b>${NM(k)} · ${lab[j]}</b>${row('Investiu (por trimestre)',P(r.inv,1)+' · R$ '+F(r.inv_bi,1)+' bi')}${row('Tirou',P(r.tira,1)+' · R$ '+F(r.tira_bi,1)+' bi')}${row('Líquido',P(r.fr,1)+' · R$ '+F(r.f_bi,1)+' bi')}${row('Trimestres',r.n)}`)).on('mouseleave',()=>t.style('display','none'));});});
 s.append('line').attr('class','zero').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t-4).attr('y2',H-m.b);
 // texto automático
 const nets=ks.filter(k=>k!='total').map(k=>({k,a:E.alta[k].fr,b:E.baixa[k].fr}));
 const mostA=[...nets].sort((p,q)=>q.a-p.a)[0], mostB=[...nets].sort((p,q)=>q.b-p.b)[0], leastA=[...nets].sort((p,q)=>p.a-q.a)[0], leastB=[...nets].sort((p,q)=>p.b-q.b)[0];
 document.getElementById('sw-butter').innerHTML=`Com <b>${lab[0].toLowerCase()}</b>, quem mais pôs foi <b>${NM(mostA.k)}</b> (${PP(mostA.a)}% por trimestre) e quem mais tirou foi <b>${NM(leastA.k)}</b> (${PP(leastA.a)}%). Com <b>${lab[1].toLowerCase()}</b>, quem mais pôs foi <b>${NM(mostB.k)}</b> (${PP(mostB.b)}%) e quem mais tirou foi <b>${NM(leastB.k)}</b> (${PP(leastB.b)}%). Troque o regime na barra para comparar. Estrangeiro e empresas têm posições pequenas (1–4% do passivo), e um único caso move os números deles.`;
}

function pheat(){
 const X=window.P2, dv=Object.keys(X.drivers_nome), tb=document.getElementById('p-heat');
 const col=r=>{const a=Math.min(1,Math.abs(r)/.75);return r>=0?`rgba(42,120,214,${a*.55})`:`rgba(235,104,52,${a*.55})`;};
 tb.innerHTML='<thead><tr><th class="l" style="text-align:left">Tipo</th>'+dv.map(d=>`<th data-d="${d}" class="${d==ST.drv?'on':''}">${X.drivers_nome[d]}</th>`).join('')+'</tr></thead><tbody>'+
  X.tipos.map(k=>`<tr class="${k==ST.tipo?'sel':''}"><td class="l">${NM(k)}</td>${dv.map(d=>{const r=X.drivers[k][d];return `<td data-d="${d}" style="background:${col(r.r)}${Math.abs(r.t)>=2?';font-weight:600':''}">${(r.r>0?'+':'')+F(r.r,2)}<br><span style="color:var(--muted);font-weight:400">(${F(r.t,1)})</span></td>`}).join('')}</tr>`).join('')+'</tbody>';
 tb.querySelectorAll('[data-d]').forEach(c=>c.onclick=()=>{ST.drv=c.dataset.d;pheat();});
 // dispersão
 const S=window.P2.serie, T=X.trimestres, k=ST.tipo, d=ST.drv, W=1000,H=300,m={l:52,r:20,t:12,b:40};
 const pts=S.map(r=>{const tr=T.find(z=>z.q==r.q);return {q:r.q,x:d=='ind_alpha'?null:tr?tr[d]:null,y:r[k].fr}}).filter(p=>p.x!=null&&p.y!=null);
 const s=box('p-drv',W,H), t=tip('p-drv');
 if(!pts.length){s.append('text').attr('x',W/2).attr('y',H/2).attr('text-anchor','middle').text('Escolha outra coluna para ver a dispersão (alpha mediano não é série de mercado).');return;}
 const x=d3.scaleLinear().domain(d3.extent(pts,p=>p.x)).nice().range([m.l,W-m.r]), yv=pts.map(p=>Math.abs(p.y)).sort(d3.ascending), ext=Math.max(.05,d3.quantile(yv,.95)*1.2);
 const y=d3.scaleLinear().domain([-ext,ext]).range([H-m.b,m.t]).clamp(true);
 const g=s.append('g').attr('class','grid');y.ticks(5).forEach(tv=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(tv)).attr('y2',y(tv));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(tv)+4).attr('text-anchor','end').text(P(tv))});
 x.ticks(6).forEach(tv=>s.append('text').attr('class','num').attr('x',x(tv)).attr('y',H-m.b+18).attr('text-anchor','middle').text(P(tv,d.startsWith('d')||d=='ust'?1:0)));
 s.append('text').attr('x',W-m.r).attr('y',H-4).attr('text-anchor','end').text(X.drivers_nome[d]+' →');
 s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
 const mx=d3.mean(pts,p=>p.x),my=d3.mean(pts,p=>p.y),b=d3.sum(pts,p=>(p.x-mx)*(p.y-my))/d3.sum(pts,p=>(p.x-mx)**2),[a0,a1]=x.domain();
 s.append('line').attr('x1',x(a0)).attr('x2',x(a1)).attr('y1',y(my+b*(a0-mx))).attr('y2',y(my+b*(a1-mx))).attr('stroke',css('--muted')).attr('stroke-dasharray','5 4').attr('stroke-width',1.5);
 pts.forEach(p=>{s.append('circle').attr('cx',x(p.x)).attr('cy',y(p.y)).attr('r',6).attr('fill',css(p.y>=0?'--in':'--out')).attr('stroke',css('--bg')).attr('stroke-width',2)
  .on('mousemove',ev=>show(t,ev,'p-drv',`<b>${p.q.replace('Q','T')}</b>${row('Fluxo',P(p.y,1))}${row(X.drivers_nome[d],P(p.x,2))}`)).on('mouseleave',()=>t.style('display','none'));});
 const mv=X.drivers_mv, cn={cdi:'CDI nível',dcdi_12:'Δ CDI 12m',ibov_12:'Ibovespa 12m',dust_12:'Δ Treasury 12m'};
 document.getElementById('p-mv').innerHTML='<table><thead><tr><th class="l">Regressão com as quatro juntas (coeficientes padronizados, t)</th>'+Object.values(cn).map(c=>`<th>${c}</th>`).join('')+'<th>R²</th></tr></thead><tbody>'+
  X.tipos.map(k2=>`<tr${k2==k?' style="font-weight:600"':''}><td class="l">${NM(k2)}</td>${Object.keys(cn).map(c=>{const tt=mv[k2].t[c];return `<td class="n ${Math.abs(tt)>=2?(tt>0?'pos':'neg'):''}">${F(mv[k2].coef[c],2)} <span style="color:var(--muted)">(${F(tt,1)})</span></td>`}).join('')}<td class="n">${F(mv[k2].r2,2)}</td></tr>`).join('')+'</tbody></table><p class="note">Erro HAC (4 trimestres). Coeficiente = desvios-padrão de fluxo por desvio-padrão da variável.</p>';
}

function psens(){
 const X=window.P2, ks=X.tipos, kk=key(), W=1000,rh=40,m={l:270,r:30,t:10,b:30}, H=m.t+m.b+ks.length*rh, s=box('p-sens',W,H), t=tip('p-sens');
 const R=ks.map(k=>({k,r:(X.sens[k][kk]||{}).ambos})); const vals=R.flatMap(o=>o.r?[o.r.a12.b+1.96*Math.abs(o.r.a12.b/o.r.a12.t),o.r.a36.b+1.96*Math.abs(o.r.a36.b/o.r.a36.t),o.r.a12.b-1.96*Math.abs(o.r.a12.b/o.r.a12.t),o.r.a36.b-1.96*Math.abs(o.r.a36.b/o.r.a36.t)]:[]).filter(isFinite);
 const x=d3.scaleLinear().domain([Math.max(-30,Math.min(-5,d3.min(vals))),Math.min(60,Math.max(20,d3.max(vals)))]).range([m.l,W-m.r]).clamp(true);
 const g=s.append('g').attr('class','grid');x.ticks(8).forEach(tv=>{g.append('line').attr('x1',x(tv)).attr('x2',x(tv)).attr('y1',m.t).attr('y2',H-m.b);s.append('text').attr('class','num').attr('x',x(tv)).attr('y',H-8).attr('text-anchor','middle').text(tv)});
 R.forEach((o,i)=>{const y0=m.t+i*rh, sel=o.k==ST.tipo;
  if(sel)s.append('rect').attr('x',0).attr('y',y0).attr('width',W).attr('height',rh).attr('fill',css('--soft'));
  s.append('text').attr('class','lab').attr('x',m.l-12).attr('y',y0+rh/2+4).attr('text-anchor','end').style('font-weight',sel?600:400).text(NM(o.k).replace(' (private banks e family offices, via fundo)',' (PB e MFO)'));
  if(!o.r){s.append('text').attr('x',x(0)+6).attr('y',y0+rh/2+4).text('poucas observações');return;}
  [['a12','--in',0],['a36','--ink2',1]].forEach(([c,cl,j])=>{const v=o.r[c], se=Math.abs(v.b/v.t), yy=y0+8+j*13;
   s.append('rect').attr('x',Math.min(x(0),x(v.b))).attr('y',yy).attr('width',Math.abs(x(v.b)-x(0))).attr('height',10).attr('rx',2).attr('fill',css(cl)).attr('opacity',Math.abs(v.t)>=2?1:.35);
   s.append('line').attr('x1',x(v.b-1.96*se)).attr('x2',x(v.b+1.96*se)).attr('y1',yy+5).attr('y2',yy+5).attr('stroke',css('--ink')).attr('stroke-width',1);});
  s.append('rect').attr('x',m.l).attr('y',y0).attr('width',W-m.l-m.r).attr('height',rh).attr('fill','transparent')
   .on('mousemove',ev=>show(t,ev,'p-sens',`<b>${NM(o.k)}</b>${row('Alpha 12m',F(o.r.a12.b,1)+' p.p. (t '+F(o.r.a12.t,1)+')')}${row('Alpha 36m',F(o.r.a36.b,1)+' p.p. (t '+F(o.r.a36.t,1)+')')}${row('Observações',o.r.n)}`)).on('mouseleave',()=>t.style('display','none'));});
 s.append('line').attr('class','zero').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b);
 s.append('text').attr('x',W-m.r).attr('y',H-18).attr('text-anchor','end').style('font-size','11px').text('p.p. de fluxo por trimestre, do pior ao melhor alpha →');
}

function pquint(){
 const X=window.P2, k=ST.tipo, Qd=(X.quintis[k][key()]||{})[ST.hz], W=1000,H=290,m={l:52,r:10,t:30,b:40};
 document.getElementById('ft-quint').textContent='Fluxo por quintil de alpha: '+NM(k)+' · '+estLbl(ST.est);
 const s=box('p-quint',W,H), t=tip('p-quint');
 if(!Qd||!Qd.length){s.append('text').attr('x',W/2).attr('y',H/2).attr('text-anchor','middle').text('Sem observações suficientes nesse recorte.');return;}
 const x=d3.scaleBand().domain(Qd.map(q=>q.q)).range([m.l,W-m.r]).padding(.3), v=Qd.map(q=>q.med);
 const y=d3.scaleLinear().domain([Math.min(-.02,d3.min(v)*1.2),Math.max(.02,d3.max(v)*1.2)]).range([H-m.b,m.t]).nice();
 const g=s.append('g').attr('class','grid');y.ticks(6).forEach(tv=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(tv)).attr('y2',y(tv));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(tv)+4).attr('text-anchor','end').text(P(tv,1))});
 Qd.forEach(q=>{const top=Math.min(y(q.med),y(0)),hh=Math.max(1,Math.abs(y(q.med)-y(0)));
  s.append('rect').attr('x',x(q.q)).attr('y',top).attr('width',x.bandwidth()).attr('height',hh).attr('rx',3).attr('fill',css(q.med>=0?'--in':'--out'));
  s.append('text').attr('class','num').attr('x',x(q.q)+x.bandwidth()/2).attr('y',q.med>=0?y(q.med)-6:y(q.med)+15).attr('text-anchor','middle').style('fill',css('--ink')).text(P(q.med,1)+' · '+P(q.pos)+' com entrada');
  s.append('text').attr('x',x(q.q)+x.bandwidth()/2).attr('y',H-14).attr('text-anchor','middle').text(q.q==1?'1 (pior alpha)':q.q==5?'5 (melhor)':q.q);
  s.append('rect').attr('x',x(q.q)).attr('y',m.t).attr('width',x.bandwidth()).attr('height',H-m.t-m.b).attr('fill','transparent').on('mousemove',ev=>show(t,ev,'p-quint',`<b>Quintil ${q.q}</b>${row('Fluxo mediano',P(q.med,2))}${row('% com entrada',P(q.pos))}${row('Gestora-trimestres',q.n)}`)).on('mouseleave',()=>t.style('display','none'));});
 s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
}

function pperfil(){
 const X=window.P2, k=ST.tipo, p=X.perfil[k][key()];
 document.getElementById('ft-pf2').textContent='Quem recebe e quem perde: '+NM(k)+' · '+estLbl(ST.est);
 if(!p){box('p-perfil',1000,80).append('text').attr('x',500).attr('y',40).attr('text-anchor','middle').text('Poucas observações nesse recorte.');return;}
 const order=['ex12_l','ex36_l','size0','top10','n_acoes','beta36_l','vol36_l','te36_l','idade','sh_lb_l','consenso','dep'].filter(a=>p.tab[a]);
 dumbbell('p-perfil',order.map(a=>({nome:X.attr[a],w:p.tab[a].w,l:p.tab[a].l,t:p.tab[a].t,extra:row('Trimestres com o mesmo sinal',p.tab[a].same+' de '+p.tab[a].nq)+row('Observações',p.n)+row('% que recebeu',P(p.pct_win))})),['Receberam (percentil médio)','Perderam']);
}

function ptops(){
 const X=window.P2, k=ST.tipo, T=X.tops[k][key()];
 document.getElementById('tops-sub').innerHTML=`Soma do fluxo de <b>${NM(k)}</b> em <b>${estLbl(ST.est).toLowerCase()}</b>, em R$ milhões, com o alpha de 12 meses médio da gestora nesses trimestres e a posição média desse tipo nela.`;
 const tb=L=>'<table><thead><tr><th class="l">Gestora</th><th>R$ mi</th><th>Alpha 12m</th><th>Posição média (R$ mi)</th><th>Trim.</th></tr></thead><tbody>'+L.map(r=>`<tr><td class="l">${r.nome}</td><td class="n ${r.f_mi>=0?'pos':'neg'}">${r.f_mi.toLocaleString('pt-BR')}</td><td class="n">${r.a12==null?'—':PP(r.a12,0)}</td><td class="n">${r.h_mi==null?'—':r.h_mi.toLocaleString('pt-BR')}</td><td class="n">${r.nq}</td></tr>`).join('')+'</tbody></table>';
 document.getElementById('p-rec').innerHTML=T?tb(T.rec):''; document.getElementById('p-saq').innerHTML=T?tb(T.saq):'';
}

let ctlDone=false;
function drawP2(){if(!window.P2)return;if(!ctlDone){ctl();ctlDone=true;}segEst();pflow();pbutter();pheat();psens();pquint();pperfil();ptops();}
fetch('data/passivo.json').then(r=>r.json()).then(j=>{window.P2=j;drawP2();}).catch(()=>{document.getElementById('now').textContent='Não foi possível carregar os dados desta parte.';});
