
// ---------- fluxo acumulado por tipo (seção 6)
let accMode='bi';
function pacc(){
 const X=window.P2, S=X.serie, ks=X.tipos.filter(k=>k!='total'), W=1000,H=360,m={l:56,r:150,t:14,b:28}, s=box('p-acc',W,H), t=tip('p-acc');
 const cum={}; ks.concat(['total']).forEach(k=>{let c=0;cum[k]=S.map(r=>{c+=(r[k].f||0);return accMode=='bi'?c:c/(S[0][k].h||NaN);});});
 const show2=ST.tipo=='total'?ks:ks; const all=show2.flatMap(k=>cum[k]).concat(cum[ST.tipo]).filter(isFinite);
 const x=d3.scaleBand().domain(S.map(r=>r.q)).range([m.l,W-m.r]).padding(0), y=d3.scaleLinear().domain(d3.extent(all.concat([0]))).nice().range([H-m.b,m.t]);
 const g=s.append('g').attr('class','grid');y.ticks(6).forEach(v=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(v)).attr('y2',y(v));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(v)+4).attr('text-anchor','end').text(accMode=='bi'?F(v,0):P(v))});
 S.forEach(r=>{if(r.q.endsWith('Q1'))s.append('text').attr('x',x(r.q)+x.bandwidth()/2).attr('y',H-8).attr('text-anchor','middle').text(r.q.slice(0,4));});
 s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
 const ln=d3.line().defined(v=>isFinite(v)).x((v,i)=>x(S[i].q)+x.bandwidth()/2).y(v=>y(v));
 const lst=ks.filter(k=>k!=ST.tipo).concat(ST.tipo=='total'?[]:[ST.tipo]);
 lst.forEach(k=>{const sel=k==ST.tipo;s.append('path').attr('d',ln(cum[k])).attr('fill','none').attr('stroke',css(sel?'--in':'--neu')).attr('stroke-width',sel?3:1.3).attr('opacity',sel?1:.8);});
 if(ST.tipo=='total'&&accMode=='bi')s.append('path').attr('d',ln(cum.total)).attr('fill','none').attr('stroke',css('--ink')).attr('stroke-width',2.5);
 // rótulos no fim, sem sobreposição
 const ends=(ST.tipo=='total'&&accMode=='bi'?['total']:[]).concat(ks).map(k=>({k,v:cum[k][cum[k].length-1]})).filter(o=>isFinite(o.v)).sort((a,b)=>b.v-a.v);
 let last=-1e9; ends.forEach(o=>{let yy=y(o.v);if(yy<last+12)yy=last+12;last=yy;const sel=o.k==ST.tipo;
  s.append('text').attr('x',W-m.r+6).attr('y',yy+4).style('font-size','11px').style('font-weight',sel?600:400).style('fill',css(sel?'--ink':'--ink2')).text(NM(o.k).replace(' (private banks e family offices, via fundo)','').replace(' (conta e ordem)','').replace('Fundos de pensão e RPPS','Fundações e RPPS')+' '+(accMode=='bi'?F(o.v,1):P(o.v)));});
 S.forEach((r,i)=>s.append('rect').attr('x',x(r.q)).attr('y',m.t).attr('width',x.bandwidth()).attr('height',H-m.t-m.b).attr('fill','transparent')
  .on('mousemove',ev=>show(t,ev,'p-acc',`<b>Acumulado até ${r.q.replace('Q','T')}</b>`+[ST.tipo].concat(['total','wealth','pensao','plataformas','private','varejo','alocadores']).filter((v,j,a)=>a.indexOf(v)==j).map(k=>row(NM(k).split(' (')[0],accMode=='bi'?'R$ '+F(cum[k][i],1)+' bi':P(cum[k][i]))).join(''))).on('mouseleave',()=>t.style('display','none')));
}

// ---------- seção 13
const PFT=['plataformas','private','varejo','estrangeiro']; let PFK='plataformas';
function ppf(){
 const X=window.P2; if(!X.pf)return;
 if(PFT.includes(ST.tipo))PFK=ST.tipo;
 const el=document.getElementById('seg-pf'); el.innerHTML=PFT.map(k=>`<button type="button" data-k="${k}" aria-pressed="${k==PFK}">${NM(k).split(' (')[0]}</button>`).join('');
 el.querySelectorAll('button').forEach(b=>b.onclick=()=>{PFK=b.dataset.k;ppf();});
 document.getElementById('ft-pf').textContent='Cotistas e posição média: '+NM(PFK);
 const R=X.pf[PFK].serie;
 const small=(id,vals,fmt,col)=>{const W=480,H=220,m={l:56,r:10,t:12,b:26},s=box(id,W,H),t=tip(id);
  const x=d3.scaleBand().domain(R.map(r=>r.q)).range([m.l,W-m.r]), y=d3.scaleLinear().domain([0,d3.max(vals)*1.1]).nice().range([H-m.b,m.t]);
  const g=s.append('g').attr('class','grid');y.ticks(4).forEach(v=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(v)).attr('y2',y(v));s.append('text').attr('class','num').attr('x',m.l-6).attr('y',y(v)+4).attr('text-anchor','end').text(fmt(v))});
  R.forEach(r=>{if(r.q.endsWith('Q1')&&(+r.q.slice(0,4))%2==1)s.append('text').attr('x',x(r.q)).attr('y',H-8).attr('text-anchor','middle').text(r.q.slice(0,4));});
  s.append('path').attr('d',d3.line().defined(v=>v!=null&&isFinite(v)).x((v,i)=>x(R[i].q)+x.bandwidth()/2).y(v=>y(v))(vals)).attr('fill','none').attr('stroke',css(col)).attr('stroke-width',2.2);
  R.forEach((r,i)=>s.append('rect').attr('x',x(r.q)).attr('y',m.t).attr('width',x.bandwidth()).attr('height',H-m.t-m.b).attr('fill','transparent').on('mousemove',ev=>show(t,ev,id,`<b>${r.q.replace('Q','T')}</b>${row('Cotistas (encadeado)',r.n_enc.toLocaleString('pt-BR'))}${row('Cotistas (soma simples)',r.n.toLocaleString('pt-BR'))}${row('Posição média','R$ '+F(r.pos_media_mil,0)+' mil')}${row('Posição total','R$ '+F(r.h,1)+' bi')}`)).on('mouseleave',()=>t.style('display','none')));};
 small('pf-n',R.map(r=>r.n_enc),v=>v>=1e3?F(v/1e3,0)+' mil':F(v,0),'--in');
 small('pf-a',R.map(r=>r.pos_media_mil),v=>F(v,0),'--ink');
 // acumulado novos x existentes
 {const W=1000,H=280,m={l:56,r:12,t:14,b:26},s=box('pf-acc',W,H),t=tip('pf-acc');
  let a=0,b=0,c=0; const E=R.map(r=>a+=r.ext||0), I=R.map(r=>b+=r.int||0), T=R.map(r=>c+=r.f||0);
  const x=d3.scaleBand().domain(R.map(r=>r.q)).range([m.l,W-m.r]), y=d3.scaleLinear().domain(d3.extent(E.concat(I,T,[0]))).nice().range([H-m.b,m.t]);
  const g=s.append('g').attr('class','grid');y.ticks(6).forEach(v=>{g.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(v)).attr('y2',y(v));s.append('text').attr('class','num').attr('x',m.l-8).attr('y',y(v)+4).attr('text-anchor','end').text(F(v,v%1?1:0))});
  R.forEach(r=>{if(r.q.endsWith('Q1'))s.append('text').attr('x',x(r.q)+x.bandwidth()/2).attr('y',H-8).attr('text-anchor','middle').text(r.q.slice(0,4));});
  s.append('line').attr('class','zero').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0));
  const ln=d3.line().x((v,i)=>x(R[i].q)+x.bandwidth()/2).y(v=>y(v));
  [[E,'--in',2.2],[I,'--out',2.2],[T,'--ink',2.8]].forEach(([v,cl,w])=>s.append('path').attr('d',ln(v)).attr('fill','none').attr('stroke',css(cl)).attr('stroke-width',w));
  R.forEach((r,i)=>s.append('rect').attr('x',x(r.q)).attr('y',m.t).attr('width',x.bandwidth()).attr('height',H-m.t-m.b).attr('fill','transparent').on('mousemove',ev=>show(t,ev,'pf-acc',`<b>Até ${r.q.replace('Q','T')}</b>${row('Cotistas novos','R$ '+F(E[i],1)+' bi')}${row('Quem já estava','R$ '+F(I[i],1)+' bi')}${row('Total','R$ '+F(T[i],1)+' bi')}${row('No trimestre','R$ '+F(r.f,2)+' bi')}`)).on('mouseleave',()=>t.style('display','none')));}
 // bandas
 {const B=[['pulverizado','--in'],['medio',null],['grande','--out'],['existentes','--ink2'],['inconsistente','--grid']], lab=X.estados[ST.rg];
  const rowsB=PFT.flatMap(k=>[['todos','Todos os trimestres',X.pf[k].estados.todos],['alta',lab[0],X.pf[k].estados[ST.rg].alta],['baixa',lab[1],X.pf[k].estados[ST.rg].baixa]].map(([e,l,v])=>({k,e,l,v})));
  const W=1000,rh=24,gap=12,m={l:300,r:14,t:6,b:24},H=m.t+m.b+PFT.length*(3*rh+gap),s=box('pf-band',W,H),t=tip('pf-band');
  const x=d3.scaleLinear().domain([0,1]).range([m.l,W-m.r]);
  [0,.25,.5,.75,1].forEach(v=>s.append('text').attr('class','num').attr('x',x(v)).attr('y',H-6).attr('text-anchor','middle').text(P(v)));
  rowsB.forEach((o,i)=>{const gi=Math.floor(i/3), yy=m.t+gi*(3*rh+gap)+(i%3)*rh, sel=o.k==PFK;
   if(i%3==0)s.append('text').attr('class','lab').attr('x',8).attr('y',yy+rh+rh/2+4).style('font-weight',sel?600:400).text(NM(o.k).split(' (')[0]);
   s.append('text').attr('x',m.l-8).attr('y',yy+rh/2+4).attr('text-anchor','end').style('font-size','11.5px').text(o.l);
   let acc=0; B.forEach(([b,cl])=>{const v=o.v[b]||0;s.append('rect').attr('x',x(acc)).attr('y',yy+3).attr('width',Math.max(0,x(acc+v)-x(acc)-1)).attr('height',rh-6).attr('fill',cl?css(cl):'#7fb0ea').attr('opacity',sel?1:.75);acc+=v;});
   s.append('rect').attr('x',m.l).attr('y',yy).attr('width',W-m.l-m.r).attr('height',rh).attr('fill','transparent').on('mousemove',ev=>show(t,ev,'pf-band',`<b>${NM(o.k).split(' (')[0]} · ${o.l}</b>${row('Pulverizado',P(o.v.pulverizado))}${row('Médio',P(o.v.medio))}${row('Grande',P(o.v.grande))}${row('Quem já estava',P(o.v.existentes))}${row('Inconsistente',P(o.v.inconsistente))}${row('Entradas','R$ '+F(o.v.entrada_bi,1)+' bi')}${row('Líquido','R$ '+F(o.v.f_bi,1)+' bi')}${row('Líquido de cotistas novos','R$ '+F(o.v.ext_bi,1)+' bi')}${row('Líquido de quem já estava','R$ '+F(o.v.int_bi,1)+' bi')}`)).on('mouseleave',()=>t.style('display','none'));});}
}
