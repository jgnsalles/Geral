// =================== EMPRESAS ===================
// Retorno total de cada empresa na janela (classe mais negociada), incluindo as que saíram da bolsa:
// a série vai até o último pregão e o restante da janela fica parado (sem retorno). Quem detinha vem das carteiras do attribution.
let EM=null;
const loadE=()=>EM?Promise.resolve(EM):fetch('empresas.json').then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); }).then(d=>{ EM=d; return d; });
S.ew=12; S.ef=null; S.et=null; S.eu='all'; S.ev=0; S.esel=null;
function eWin(){ const hi=PLAST; if(S.ew) return {a:Math.max(0,hi-S.ew+1), b:hi}; let a=S.ef??hi-11, b=S.et??hi; a=Math.max(0,Math.min(a,hi)); b=Math.max(a,Math.min(b,hi)); return {a,b}; }
function eRet(e,a,b){ const U=S.cur==='USD'; let c=1, miss=0, n=0; const last=e.o+e.r.length-1;
  if(last<a||e.o>b) return null;
  for(let i=Math.max(a,e.o);i<=Math.min(b,last);i++){ const v=e.r[i-e.o]; if(v==null){ miss++; continue; } const fx=U&&FXR[i]!=null?FXR[i]:0; c*=(1+v/1e6)*(1+fx); n++; }
  // depois de sair da bolsa o valor fica parado; antes do IPO não conta
  let vol=0; for(let i=Math.max(a,e.o);i<=Math.min(b,last);i++) vol+=e.v[i-e.o]||0;
  return {ret:c-1, miss, n, ipo:e.o>a?e.o:null, out:e.dl&&last<b?last:null, vol:vol/Math.max(1,Math.min(b,last)-Math.max(a,e.o)+1)}; }
function eHolders(root,a,b){ if(!AT) return null; const ri=AT.roots.indexOf(root); if(ri<0) return [];
  const out=[]; Object.entries(AT.g).forEach(([gid,rec])=>{ if(!PSEL.has(gid)&&!PGI[gid]) return; let n=0,ws=0,wmax=0,c=0,first=null,last=null;
    for(let i=Math.max(a,rec.o);i<=Math.min(b,rec.o+rec.p.length-1);i++){ const arr=rec.p[i-rec.o]; if(!arr) continue; const x=arr.find(q=>q[0]===ri); if(!x) continue;
      const w=x[1]/1e6; n++; ws+=w; wmax=Math.max(wmax,w); c+=x[2]/1e6; if(first==null) first=i; last=i; }
    if(n) out.push({gid, g:PGI[gid]||{n:gid}, n, w:ws/n, wmax, c, first, last}); });
  return out.sort((x,y)=>y.w-x.w); }
function renderE(){
  $('e-win').innerHTML=AWIN.map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.ew===v}">${l}</button>`).join('');
  $('e-win').onclick=e=>{const x=e.target.closest('button'); if(!x) return; S.ew=+x.dataset.v; renderE();};
  curSeg($('e-cur'),renderE);
  if(!EM||!AT){ $('e-body').innerHTML='<p class="loading">Carregando empresas…</p>'; Promise.all([loadE(),loadA()]).then(renderE).catch(e=>{$('e-body').innerHTML=`<p class="loading">Não foi possível carregar (${esc(e.message)}).</p>`;}); return; }
  const {a,b}=eWin(); $('e-custom').hidden=S.ew!==0;
  if(S.ew===0){ const opt=(sel,v)=>{ sel.innerHTML=''; for(let i=PLAST;i>=0;i--) sel.add(new Option(pmlong(i),i)); sel.value=v; }; opt($('e-from'),a); opt($('e-to'),b);
    $('e-from').onchange=()=>{S.ef=+$('e-from').value; renderE();}; $('e-to').onchange=()=>{S.et=+$('e-to').value; renderE();}; }
  S.eu=$('e-u').value; S.ev=+$('e-v').value;
  const ib=pstats(IBV,a,b);
  const rows=Object.entries(EM.e).map(([root,e])=>{ const s=eRet(e,a,b); if(!s||s.n<Math.min(3,b-a+1)) return null; return {root,e,...s}; }).filter(Boolean)
    .filter(o=>(S.eu==='all'||(S.eu==='ib'&&o.e.ib)||(S.eu==='sm'&&o.e.sm)||(S.eu==='h'&&o.e.h)) && o.vol>=S.ev);
  const H=new Map(rows.map(o=>[o.root,eHolders(o.root,a,b)]));
  $('e-h').textContent=`Empresas · ${pml(a)} a ${pml(b)}`;
  $('e-sub').textContent=`${rows.length} empresas · retorno total (preço + proventos) em ${S.cur==='USD'?'US$':'R$'} · quem detinha = gestoras do ranking com a ação na carteira em algum mês da janela`;
  const up=rows.filter(o=>o.ret>0).length, med=rows.map(o=>o.ret).sort((x,y)=>x-y)[Math.floor(rows.length/2)], outs=rows.filter(o=>o.out!=null);
  const srt=rows.slice().sort((x,y)=>y.ret-x.ret), win=srt.slice(0,20), los=srt.slice(-20).reverse();
  const chips=o=>{ const h=H.get(o.root)||[]; return h.length?h.slice(0,3).map(x=>`<span class="chip" title="peso médio ${pct(x.w,1)} em ${x.n} meses">${esc(x.g.n)} ${pct(x.w,0)}</span>`).join(' ')+(h.length>3?` <span class="muted">+${h.length-3}</span>`:''):'<span class="muted">nenhuma</span>'; };
  const st=o=>(o.out!=null?` <span class="chip down" title="último pregão em ${pmlong(o.out)}">saiu ${pml(o.out)}</span>`:'')+(o.ipo!=null?` <span class="chip new">estreou ${pml(o.ipo)}</span>`:'');
  const tbl=(list)=>`<table class="etbl"><thead><tr><th class="l">Empresa</th><th>Retorno</th><th class="l">Quem detinha (peso médio)</th></tr></thead><tbody>${list.map(o=>`<tr class="link${S.esel===o.root?' sel':''}" data-r="${esc(o.root)}"><td class="l"><span class="tk">${esc(o.e.tk)}</span> <span class="muted">${esc(o.e.n.slice(0,22))}</span>${st(o)}</td><td style="font-weight:600">${pc(o.ret,0)}</td><td class="l hold">${chips(o)}</td></tr>`).join('')}</tbody></table>`;
  $('e-body').innerHTML=`<div class="kpis">${kpis([['Empresas',String(rows.length),`${up} subiram · ${rows.length-up} caíram`],['Mediana',pc(med),`Ibovespa ${pc(ib?ib.ret:null)}`],
      ['Melhor',win[0]?esc(win[0].e.tk):'–',win[0]?pc(win[0].ret,0):''],['Saíram da bolsa',String(outs.length),'no período (falência, fechamento ou incorporação)']])}</div>`+
    `<div class="grid2"><div class="card"><div class="hd"><h2>Winners</h2><small>clique para ver quem detinha</small></div><div class="tblwrap">${tbl(win)}</div></div>`+
    `<div class="card"><div class="hd"><h2>Losers</h2><small>clique para ver quem detinha</small></div><div class="tblwrap">${tbl(los)}</div></div></div>`+
    `<div class="card" id="e-det"></div>`+
    `<div class="card"><div class="hd"><h2>Todas as empresas</h2><small>clique no cabeçalho para ordenar</small></div><div class="tblwrap" style="max-height:560px;overflow-y:auto"><table id="e-all"></table></div></div>`+
    `<p class="note"><b>Como é calculado.</b> Universo: todas as ações que algum fundo das gestoras do ranking teve na carteira desde 2005, a composição atual do Ibovespa e do Small (B3) e as 250 ações mais negociadas da B3 em cada ano, que aproximam quem esteve nesses índices no passado. Retorno total = fechamento da B3 + proventos, ajustado por desdobramentos e grupamentos, na classe mais negociada nos 12 meses anteriores. Empresas que saíram da bolsa entram com a série até o último pregão (falências e recuperações aparecem com a queda inteira; fechamentos de capital e incorporações, pelo último preço). Quedas muito grandes só são descartadas quando parecem erro de dado (voltam no mês seguinte ou batem com um fator de desdobramento). "Quem detinha" usa as carteiras da CDA das gestoras do ranking (aba Attribution).</p>`;
  const bind=()=>$('e-body').querySelectorAll('tr[data-r]').forEach(tr=>tr.onclick=()=>{ S.esel=tr.dataset.r; renderEDet(a,b,rows,H); $('e-det').scrollIntoView({behavior:'smooth',block:'nearest'}); });
  sTable('e-all',[
    {k:'tk',l:'Empresa',cls:'l',v:o=>o.e.tk,asc:true,f:o=>`<td class="l"><span class="tk">${esc(o.e.tk)}</span> <span class="muted">${esc(o.e.n.slice(0,26))}</span>${st(o)}</td>`},
    {k:'ret',l:'Retorno',v:o=>o.ret,f:o=>`<td style="font-weight:600">${pc(o.ret,0)}</td>`},
    {k:'ex',l:'vs Ibov',v:o=>ib?o.ret-ib.ret:null,f:o=>`<td>${pcp(ib?o.ret-ib.ret:null)}</td>`},
    {k:'nh',l:'Gestoras',v:o=>(H.get(o.root)||[]).length,f:o=>`<td class="muted">${(H.get(o.root)||[]).length||'–'}</td>`},
    {k:'vol',l:'Negociado/mês',v:o=>o.vol,f:o=>`<td class="muted">${plmi(o.vol)}</td>`},
    {k:'tag',l:'Índice hoje',cls:'l',v:o=>(o.e.ib?2:0)+(o.e.sm?1:0),f:o=>`<td class="l muted">${[o.e.ib?'Ibov':'',o.e.sm?'Small':''].filter(Boolean).join(' · ')||'–'}</td>`},
  ], rows, 'ret', o=>`data-r="${esc(o.root)}"`, 1e9, renderE);
  bind();
  if(!S.esel||!rows.find(o=>o.root===S.esel)) S.esel=win[0]?win[0].root:null;
  renderEDet(a,b,rows,H);
}
function renderEDet(a,b,rows,H){ const o=rows.find(x=>x.root===S.esel), el=$('e-det'); if(!o){ el.innerHTML=''; return; }
  document.querySelectorAll('.etbl tr.sel').forEach(t=>t.classList.remove('sel')); document.querySelectorAll(`.etbl tr[data-r="${CSS.escape(o.root)}"]`).forEach(t=>t.classList.add('sel'));
  const h=H.get(o.root)||[]; const e=o.e; const U=S.cur==='USD';
  const rr=new Array(PN).fill(null); e.r.forEach((v,k)=>{ const i=e.o+k; if(v!=null){ const fx=U&&FXR[i]!=null?FXR[i]:0; rr[i]=(1+v/1e6)*(1+fx)-1; } });
  el.innerHTML=`<div class="hd"><h2><span class="tk">${esc(e.tk)}</span> ${esc(e.n)}</h2><small>${pc(o.ret,0)} de ${pml(a)} a ${pml(b)}${o.out!=null?` · último pregão ${pmlong(o.out)}`:''}</small></div><div class="chart" id="e-chart"></div>`+
    `<div class="lbl" style="margin:10px 0 6px">Gestoras do ranking que tinham a ação na janela (${h.length})</div>`+
    (h.length?`<div class="tblwrap"><table><thead><tr><th class="l">Gestora</th><th>Meses</th><th class="l">De</th><th class="l">Até</th><th>Peso médio</th><th>Peso máx.</th><th>Contribuição</th></tr></thead><tbody>${h.map(x=>`<tr><td class="l"><a href="#g-${x.gid}" data-open="${x.gid}">${esc(x.g.n)}</a></td><td class="muted">${x.n}</td><td class="l muted">${pml(x.first)}</td><td class="l muted">${pml(x.last)}</td><td>${pct(x.w,1)}</td><td class="muted">${pct(x.wmax,1)}</td><td>${pcp(x.c)}</td></tr>`).join('')}</tbody></table></div><p class="note">Contribuição = soma mensal de peso × retorno da ação na carteira da gestora, em reais, sem encadear.</p>`:'<div class="empty">Nenhuma gestora do ranking teve a ação nesse período.</div>');
  cumChart($('e-chart'),[{name:e.tk,r:rr,color:SER[0],sw:2.4},IBS],a,b,{h:240,label:`Retorno de ${e.tk}`});
  el.querySelectorAll('a[data-open]').forEach(x=>x.onclick=ev=>{ev.preventDefault(); openG(x.dataset.open);});
}
['e-u','e-v'].forEach(id=>$(id).addEventListener('change',()=>renderE()));
