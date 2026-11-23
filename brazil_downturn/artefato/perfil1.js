let pf1='seca';
// dumbbell 0-100: rows=[{nome,w,l,t}] (w e l em percentil 0-100)
function dumbbell(id,rows,labels){
 const W=1000,rh=32,m={l:300,r:40,t:26,b:30},H=m.t+m.b+rows.length*rh, s=box(id,W,H), t=tip(id);
 const x=d3.scaleLinear().domain([0,100]).range([m.l,W-m.r]);
 const g=s.append('g').attr('class','grid');[0,25,50,75,100].forEach(v=>{g.append('line').attr('x1',x(v)).attr('x2',x(v)).attr('y1',m.t).attr('y2',H-m.b);s.append('text').attr('class','num').attr('x',x(v)).attr('y',H-10).attr('text-anchor','middle').text(v)});
 s.append('line').attr('x1',x(50)).attr('x2',x(50)).attr('y1',m.t-6).attr('y2',H-m.b).attr('stroke',css('--muted')).attr('stroke-dasharray','4 3');
 s.append('text').attr('x',x(0)).attr('y',14).text('0 = menos');s.append('text').attr('x',x(50)).attr('y',14).attr('text-anchor','middle').text('mediana');s.append('text').attr('x',x(100)).attr('y',14).attr('text-anchor','end').text('100 = mais');
 rows.forEach((r,i)=>{const yy=m.t+i*rh+rh/2, sig=r.t!=null&&Math.abs(r.t)>=2;
  s.append('text').attr('class','lab').attr('x',m.l-12).attr('y',yy+4).attr('text-anchor','end').style('font-weight',sig?600:400).style('fill',sig?css('--ink'):css('--ink2')).text(r.nome);
  s.append('line').attr('x1',x(r.l)).attr('x2',x(r.w)).attr('y1',yy).attr('y2',yy).attr('stroke',css(r.w>=r.l?'--in':'--out')).attr('stroke-width',sig?3:1.5).attr('opacity',sig?.9:.45);
  s.append('circle').attr('cx',x(r.l)).attr('cy',yy).attr('r',6.5).attr('fill',css('--bg')).attr('stroke',css('--out')).attr('stroke-width',2);
  s.append('circle').attr('cx',x(r.w)).attr('cy',yy).attr('r',6.5).attr('fill',css('--in')).attr('stroke',css('--bg')).attr('stroke-width',1.5);
  s.append('rect').attr('x',0).attr('y',yy-rh/2).attr('width',W).attr('height',rh).attr('fill','transparent')
   .on('mousemove',ev=>show(t,ev,id,`<b>${r.nome}</b>${row(labels[0],F(r.w,0))}${row(labels[1],F(r.l,0))}${row('Diferença',PP(r.w/100-r.l/100,0)+' pontos')}${row('t',r.t==null?'—':F(r.t,1))}${r.extra||''}`)).on('mouseleave',()=>t.style('display','none'));});
}
function perfil(){
 const P=pf1=='seca'?D.perfil_seca:D.perfil_cheia;
 const order=['ex12_l_rk','ex36_l_rk','size_rk','top10_rk','n_acoes_rk','cli_pf_rk','cli_inst_rk','cli_fundos_rk','perf_fee_rk','te36_l_rk','beta36_l_rk','vol36_l_rk','idade_rk','consenso_rk','sh_lb_l_rk'];
 const T=Object.fromEntries(P.tab.map(r=>[r.var,r]));
 const nm={'ex12_l_rk':'Alpha 12 meses','ex36_l_rk':'Alpha 36 meses','size_rk':'Tamanho (PL em ações)','top10_rk':'Concentração (peso das 10 maiores)','n_acoes_rk':'Nº de ações na carteira','cli_pf_rk':'% de clientes pessoa física','cli_inst_rk':'% de clientes institucionais','cli_fundos_rk':'% de clientes fundos/alocadores','perf_fee_rk':'% da receita com performance','te36_l_rk':'Tracking error 36m','beta36_l_rk':'Beta 36m','vol36_l_rk':'Volatilidade 36m','idade_rk':'Idade da gestora','consenso_rk':'Peso nas 20 ações mais detidas','sh_lb_l_rk':'% do PL em long biased'};
 dumbbell('c-perfil',order.map(k=>({nome:nm[k],w:T[k].win*100,l:T[k].lose*100,t:T[k].t,extra:row('Anos com o mesmo sinal',T[k].anos_mesmo_sinal+' de '+T[k].anos)})),['Captaram (percentil médio)','Tiveram saída']);
}
document.querySelectorAll('#pf1-seg button').forEach(b=>b.onclick=()=>{pf1=b.dataset.k;document.querySelectorAll('#pf1-seg button').forEach(x=>x.setAttribute('aria-pressed',x===b));perfil();});
