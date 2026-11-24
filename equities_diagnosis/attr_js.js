// =================== ATTRIBUTION ===================
// Retorno líquido da janela = soma das contribuições encadeadas: cada mês t entra multiplicado pelo
// acumulado da gestora até t-1, então ações + outros + taxas (+ câmbio) = retorno total exatamente.
let AT=null, LP=null;
const loadA=()=>AT?Promise.resolve(AT):fetch('attr.json').then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); }).then(d=>{ AT=d; return d; });
const loadL=()=>LP?Promise.resolve(LP):fetch('passivo.json').then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); }).then(d=>{ LP=d; return d; });
const AWIN=[[6,'6m'],[12,'1 ano'],[24,'2 anos'],[36,'3 anos'],[60,'5 anos'],[120,'10 anos'],[0,'Personalizada']];
S.aw=36; S.af=null; S.at=null;
const nameR=k=>AT.names[k]&&AT.names[k]!==AT.roots[k]?AT.names[k]:'';
function aCompute(gid,a,b){
  const p=PR[gid], rec=AT.g[gid]; if(!p||!rec) return {err:'Sem carteira na CDA para esta gestora.'};
  const U=S.cur==='USD'; let G=1, out={stk:0,oth:0,fee:0,fx:0,cov:0,conf:0,nop:0,est:0,nest:0,n:0,miss:0}; const C=new Map();
  for(let i=a;i<=b;i++){ const rn=p.rB[i]; if(rn==null) return {err:`Sem retorno da gestora em ${pmlong(i)}.`};
    const k=i-rec.o, rg0=k>=0&&k<rec.rg.length?rec.rg[k]:null, rg=rg0==null?rn:dec(rg0); if(rg0==null) out.miss++;
    const fx=U&&FXR[i]!=null?FXR[i]:0, rt=(1+rn)*(1+fx)-1;
    let sc=0; ((k>=0&&rec.p[k])||[]).forEach(([ri,w,c])=>{ const W=w/1e6, Cc=c/1e6; sc+=Cc;
      let e=C.get(ri); if(!e){ e={ri,c:0,ws:0,n:0,g:1}; C.set(ri,e); } e.c+=Cc*G; e.ws+=W; e.n++; e.g*=1+(W?Cc/W:0); });
    out.stk+=sc*G; out.oth+=(rg-sc)*G; out.fee+=(rn-rg)*G; out.fx+=(rt-rn)*G;
    if(k>=0&&rec.cov[k]!=null){ out.cov+=dec(rec.cov[k]); out.conf+=dec(rec.conf[k]); out.nop+=dec(rec.nop[k]); out.n++; const es=rec.est&&rec.est[k]?dec(rec.est[k]):0; out.est+=es; if(es>0.5) out.nest++; }
    G*=1+rt; }
  out.tot=G-1; out.m=b-a+1; out.rows=[...C.values()].map(e=>({...e, w:e.ws/(b-a+1), r:e.g-1}));
  if(out.n){ out.cov/=out.n; out.conf/=out.n; out.nop/=out.n; out.est/=out.n; } return out; }
function aBounds(gid){ const p=PR[gid], rec=AT.g[gid]; const lo=Math.max(p.o, rec?rec.o:p.o), hi=Math.min(p.last, PLAST);
  if(S.aw){ const b=hi, a=Math.max(lo, b-S.aw+1); return {a,b,cut:b-S.aw+1<lo}; }
  let a=S.af??Math.max(lo,hi-35), b=S.at??hi; a=Math.max(lo,Math.min(a,hi)); b=Math.max(a,Math.min(b,hi)); return {a,b,cut:false,lo,hi}; }
function renderA(){
  const ids=PG.filter(g=>PR[g.id]&&!/^la/.test(g.id)&&PSEL.has(g.id)).map(g=>g.id);
  if(!S.g||!ids.includes(S.g)) S.g=(S.psel||[]).find(id=>ids.includes(id))||ids.slice().sort((x,y)=>(lastPL(PR[y],PR[y].last)||0)-(lastPL(PR[x],PR[x].last)||0))[0];
  const g=PGI[S.g]; $('a-q').value=g.n;
  $('a-win').innerHTML=AWIN.map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.aw===v}">${l}</button>`).join('');
  $('a-win').onclick=e=>{const x=e.target.closest('button'); if(!x) return; S.aw=+x.dataset.v; renderA();};
  curSeg($('a-cur'),renderA);
  if(!AT){ $('a-body').innerHTML='<p class="loading">Carregando carteiras…</p>'; loadA().then(renderA).catch(e=>{$('a-body').innerHTML=`<p class="loading">Não foi possível carregar as carteiras (${esc(e.message)}).</p>`;}); return; }
  if(!AT.g[S.g]){ $('a-h').textContent=g.n; $('a-sub').textContent=''; $('a-custom').hidden=true; $('a-body').innerHTML='<div class="card"><div class="empty">Sem carteira na CDA para os fundos desta gestora.</div></div>'; return; }
  const bd=aBounds(S.g); $('a-custom').hidden=S.aw!==0;
  if(S.aw===0){ const opt=(sel,v,lo,hi)=>{ sel.innerHTML=''; for(let i=hi;i>=lo;i--) sel.add(new Option(pmlong(i),i)); sel.value=v; };
    opt($('a-from'),bd.a,bd.lo,bd.hi); opt($('a-to'),bd.b,bd.lo,bd.hi);
    $('a-from').onchange=()=>{S.af=+$('a-from').value; renderA();}; $('a-to').onchange=()=>{S.at=+$('a-to').value; renderA();}; }
  const o=aCompute(S.g,bd.a,bd.b);
  $('a-h').textContent=`${g.n} · ${pml(bd.a)} a ${pml(bd.b)}`;
  $('a-sub').textContent=`${o.m||bd.b-bd.a+1} meses${bd.cut?' (série começa depois do início da janela)':''} · em ${S.cur==='USD'?'US$':'R$'} · retorno líquido do cotista decomposto pela carteira de ações dos fundos long only da gestora`;
  if(o.err){ $('a-body').innerHTML=`<div class="card"><div class="empty">${esc(o.err)}</div></div>`; return; }
  const U=S.cur==='USD';
  const dec5=[['Retorno líquido',o.tot,'no período, '+(U?'em US$':'em R$')],['Ações',o.stk,`${o.rows.length} emissores`],
    ['Outros',o.oth,'caixa, operações no mês, sigilo'],['Taxas e custos',o.fee,'líquido − bruto dos fundos'],...(U?[['Câmbio',o.fx,'variação do real']]:[])];
  const sorted=o.rows.slice().sort((x,y)=>y.c-x.c), top=sorted.filter(x=>x.c>0).slice(0,12), bot=sorted.filter(x=>x.c<0).slice(-12).reverse();
  const mx=Math.max(1e-9,...sorted.map(x=>Math.abs(x.c)));
  const bars=(list,col)=>list.map(x=>{ const wpc=Math.abs(x.c)/mx*50; return `<div class="nm" title="${esc(nameR(x.ri))}"><b>${esc(AT.roots[x.ri])}</b> ${esc(nameR(x.ri).slice(0,22))}</div><div class="tr"><span class="ax" style="left:50%"></span><i style="background:${col};${x.c>=0?`left:50%;width:${wpc}%`:`right:50%;width:${wpc}%`}"></i></div><div class="v">${pcp(x.c)}</div>`; }).join('');
  $('a-body').innerHTML=`<div class="dec">${dec5.map(([l,v,d],k)=>`<div class="kpi"><div class="lbl">${l}</div><div class="v">${k?pcp(v):pc(v)}</div><div class="d">${d}</div></div>`).join('')}</div>`+
    `<div class="grid2"><div class="card"><div class="hd"><h2>Maiores contribuições</h2><small>p.p. do retorno no período</small></div><div class="dbar">${bars(top,'var(--up)')||'<div class="empty">–</div>'}</div></div>`+
    `<div class="card"><div class="hd"><h2>Maiores detratores</h2><small>p.p. do retorno no período</small></div><div class="dbar">${bars(bot,'var(--down)')||'<div class="empty">–</div>'}</div></div></div>`+
    `<div class="card"><div class="hd"><h2>Todos os emissores</h2><small>clique no cabeçalho para ordenar</small></div><div class="tblwrap" style="max-height:560px;overflow-y:auto"><table id="a-tbl"></table></div>`+
    `<p class="note">Carteira revelada em média ${pct(o.cov,0)} do PL dos fundos; ${pct(o.conf,0)} em sigilo na CVM; ${pct(o.nop,1)} em ativos sem preço na B3 (renomeados, fechados, exterior)${o.nest?`; em ${o.nest} mês(es) a carteira do mês ainda está em sigilo e foi estimada pela última revelada (até 6 meses antes)`:''}${o.miss?`; ${o.miss} mês(es) sem carteira, tratados como "outros"`:''}. ${S.cur==='USD'?'As contribuições das ações são em reais; o efeito do dólar aparece na linha Câmbio.':''}</p></div>`+
    `<p class="note"><b>Como é calculado.</b> Peso de cada emissor = posição no fim do mês anterior ÷ PL do fundo, pela CDA da CVM, somando os fundos long only da gestora na mesma ponderação da performance; cotas de outros fundos (ex.: um fundo que investe no master) são abertas nas ações desse fundo; quando a carteira do mês ainda está em sigilo, usa-se a última revelada (até 6 meses). Retorno do emissor = fechamento da B3 + proventos em dinheiro na data-com, ajustado por desdobramentos, grupamentos e bonificações (API da B3). Contribuição do mês = peso × retorno, encadeada pelo retorno acumulado da gestora até o mês anterior, de modo que ações + outros + taxas${U?' + câmbio':''} = retorno líquido. "Outros" junta caixa, compras e vendas feitas dentro do mês, posições em sigilo e ativos sem preço. "Taxas" = retorno da cota do cotista (FIC) menos o do master.</p>`;
  sTable('a-tbl',[
    {k:'e',l:'Emissor',cls:'l',v:x=>AT.roots[x.ri],asc:true,f:x=>`<td class="l"><span class="tk">${esc(AT.roots[x.ri])}</span> <span class="muted">${esc(nameR(x.ri))}</span></td>`},
    {k:'w',l:'Peso médio',v:x=>x.w,f:x=>`<td>${pct(x.w,1)}</td>`},
    {k:'n',l:'Meses',v:x=>x.n,f:x=>`<td class="muted">${x.n}</td>`},
    {k:'r',l:'Retorno na carteira',v:x=>x.r,f:x=>`<td>${pc(x.r)}</td>`},
    {k:'c',l:'Contribuição',v:x=>x.c,f:x=>`<td style="font-weight:600">${pcp(x.c)}</td>`},
  ], o.rows, 'c', ()=>'', 1e9, renderA);
}
$('a-q').addEventListener('change',()=>{ const q=$('a-q').value.trim().toLowerCase(); const g=PG.find(x=>x.n.toLowerCase()===q)||PG.find(x=>PR[x.id]&&x.n.toLowerCase().includes(q)); if(g){ S.g=g.id; renderA(); } });

// =================== PASSIVO ===================
const LCOL=['var(--s1)','var(--s7)','var(--s2)','var(--s4)','var(--s3)','var(--s6)','var(--s5)','var(--s8)','var(--ink-2)','var(--accent-ink)','var(--muted)'];
function stackArea(el,M0,o,P,cats,i0){ // P: array de arrays em 1e4
  const w=900,h=260,ml_=40,mr=10,mt=8,mb=24,iw=w-ml_-mr,ih=h-mt-mb, n=P.length;
  const X=k=>ml_+(n<=1?iw/2:k/(n-1)*iw), Y=v=>mt+ih-v*ih;
  let s=''; [0,.25,.5,.75,1].forEach(v=>s+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${ml_-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--muted)">${v*100}%</text>`);
  const base=new Array(n).fill(0);
  cats.forEach((c,ci)=>{ let top=[],bot=[]; P.forEach((p,k)=>{ const v=p?p[ci]/1e4:0; bot.push([X(k),Y(base[k])]); base[k]+=v; top.push([X(k),Y(base[k])]); });
    const d='M'+top.map(q=>q.map(x=>x.toFixed(1)).join(',')).join('L')+'L'+bot.reverse().map(q=>q.map(x=>x.toFixed(1)).join(',')).join('L')+'Z';
    s+=`<path d="${d}" fill="${LCOL[ci%LCOL.length]}" opacity=".85"><title>${esc(c)}</title></path>`; });
  for(let k=0;k<n;k++){ const m=M0[o+k]; if(m.endsWith('-01')) s+=`<text x="${X(k)}" y="${h-6}" text-anchor="middle" font-size="11" fill="var(--muted)">${m.slice(0,4)}</text>`; }
  el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Composição do passivo ao longo do tempo" style="width:100%;height:auto;display:block">${s}</svg>`;
}
function renderL(){
  const ids=PG.filter(g=>PR[g.id]&&!/^la/.test(g.id)&&PSEL.has(g.id)).map(g=>g.id);
  if(!S.g||!ids.includes(S.g)) S.g=(S.psel||[]).find(id=>ids.includes(id))||ids.slice().sort((x,y)=>(lastPL(PR[y],PR[y].last)||0)-(lastPL(PR[x],PR[x].last)||0))[0];
  const g=PGI[S.g]; $('l-q').value=g.n; $('l-h').textContent=`Passivo · ${g.n}`;
  if(!LP){ loadL().then(renderL).catch(e=>{$('l-body').innerHTML=`<p class="loading">Não foi possível carregar o passivo (${esc(e.message)}).</p>`;}); return; }
  const M0=LP.meses, cats=LP.cats, rec=LP.g[S.g];
  const leg=`<div class="pleg">${cats.map((c,k)=>`<span><i style="background:${LCOL[k%LCOL.length]}"></i>${esc(c)}</span>`).join('')}</div>`;
  let html='';
  if(rec){ const last=rec.p.length-1; let li=last; while(li>0&&!rec.p[li]) li--;
    const at=k=>k>=0&&rec.p[k]?rec.p[k]:null, cur=at(li), y1=at(li-12), y3=at(li-36);
    $('l-sub').textContent=`Fundos long only da gestora (FICs e fundos diretos da performance) · ${pmlong(PI[M0[rec.o+li]])} · PL ${plmi(rec.pl[li])} · ${rec.ncot[li].toLocaleString('pt-BR')} cotistas em ${rec.nf[li]} fundo(s)`;
    html+=`<div class="card"><div class="hd"><h2>Composição atual</h2><small>% do PL por tipo de cotista · Perfil Mensal da CVM</small></div>`+
      `<div class="stack">${cur.map((v,k)=>v>0?`<i style="width:${v/100}%;background:${LCOL[k%LCOL.length]}" title="${esc(cats[k])}: ${nf(v/100,1)}%"></i>`:'').join('')}</div>${leg}`+
      `<div class="tblwrap"><table><thead><tr><th class="l">Tipo de cotista</th><th>Atual</th><th>12 meses antes</th><th>3 anos antes</th><th>Δ 12m</th></tr></thead><tbody>${cats.map((c,k)=>({c,k,v:cur[k]})).filter(x=>x.v>=10||(y1&&y1[x.k]>=10)||(y3&&y3[x.k]>=10)).sort((a,b)=>b.v-a.v).map(x=>`<tr><td class="l"><span class="sw" style="background:${LCOL[x.k%LCOL.length]}"></span>${esc(x.c)}</td><td style="font-weight:600">${nf(x.v/100,1)}%</td><td class="muted">${y1?nf(y1[x.k]/100,1)+'%':'–'}</td><td class="muted">${y3?nf(y3[x.k]/100,1)+'%':'–'}</td><td>${y1?pcp((x.v-y1[x.k])/1e4):'–'}</td></tr>`).join('')}</tbody></table></div></div>`;
    html+=`<div class="card"><div class="hd"><h2>Ao longo do tempo</h2><small>desde ${pml(PI[M0[rec.o]])}</small></div><div id="l-area"></div>${leg}</div>`;
  } else { $('l-sub').textContent=''; html+=`<div class="card"><div class="empty">Sem Perfil Mensal para os fundos desta gestora.</div></div>`; }
  const fr=LP.fr[S.g];
  if(fr){ const ys=Object.keys(fr).sort(); const cl=LP.fr_classes; const used=cl.map((c,k)=>k).filter(k=>ys.some(y=>fr[y].a[k]>0));
    html+=`<div class="card"><div class="hd"><h2>Gestora inteira · Formulário de Referência</h2><small>AUM por classe de cliente (R$ mi), todos os produtos, anual</small></div><div class="tblwrap"><table><thead><tr><th class="l">Ano</th>${used.map(k=>`<th>${esc(cl[k])}</th>`).join('')}<th>Total</th></tr></thead><tbody>${ys.slice().reverse().map(y=>{ const a=fr[y].a, t=a.reduce((s,v)=>s+v,0); return `<tr><td class="l">${y}</td>${used.map(k=>`<td title="${t?nf(a[k]/t*100,0)+'%':''}">${a[k]?a[k].toLocaleString('pt-BR')+`<small class="muted" style="display:block;font-size:11px">${t?nf(a[k]/t*100,0)+'%':''}</small>`:'<span class="zero">–</span>'}</td>`).join('')}<td style="font-weight:600">${t.toLocaleString('pt-BR')}</td></tr>`; }).join('')}</tbody></table></div><p class="note">O Formulário de Referência cobre todos os produtos da gestora (multimercados, previdência, carteiras), não só ações. Clubes e fundos de investimento incluem plataformas e alocadores.</p></div>`; }
  // comparação entre gestoras
  const rows=ids.map(id=>{ const r=LP.g[id]; if(!r) return null; let li=r.p.length-1; while(li>0&&!r.p[li]) li--; if(!r.p[li]) return null; return {id,g:PGI[id],p:r.p[li],pl:r.pl[li],nc:r.ncot[li],m:r.o+li}; }).filter(Boolean);
  const big=cats.map((c,k)=>k).filter(k=>rows.some(x=>x.p[k]>=500));
  html+=`<div class="card"><div class="hd"><h2>Passivo atual de todas as gestoras</h2><small>% do PL dos fundos long only · clique no nome para abrir</small></div><div class="tblwrap" style="max-height:620px;overflow-y:auto"><table id="l-tbl"></table></div></div>`;
  html+=`<p class="note"><b>Como é calculado.</b> Perfil Mensal da CVM (desde jan/2019): cada fundo informa o % do PL detido por tipo de cotista. Aqui entram os mesmos fundos da performance líquida (FICs da gestora que alimentam masters long only e fundos diretos), ponderados pelo PL do mês. "Plataformas (conta e ordem)" são clientes de distribuidores que aplicam em nome deles; "Fundos e clubes" são outros fundos cotistas (alocadores, fundos de fundos, exclusivos de famílias). O campo de maior cotista vem vazio na CVM e ficou de fora.</p>`;
  $('l-body').innerHTML=html;
  if(rec) stackArea($('l-area'),M0,rec.o,rec.p,cats);
  sTable('l-tbl',[
    {k:'g',l:'Gestora',cls:'l',v:x=>x.g.n,asc:true,f:x=>`<td class="l"><a href="#" data-l="${x.id}">${esc(x.g.n)}</a></td>`},
    {k:'pl',l:'PL',v:x=>x.pl,f:x=>`<td class="muted">${plmi(x.pl)}</td>`},
    {k:'nc',l:'Cotistas',v:x=>x.nc,f:x=>`<td class="muted">${x.nc.toLocaleString('pt-BR')}</td>`},
    ...big.map(k=>({k:'c'+k,l:esc(cats[k]),v:x=>x.p[k],f:x=>`<td style="background:color-mix(in srgb,${LCOL[k%LCOL.length]} ${Math.round(x.p[k]/100*0.5)}%,transparent)">${x.p[k]>=50?nf(x.p[k]/100,0)+'%':'<span class="zero">–</span>'}</td>`})),
  ], rows, 'pl', ()=>'', 1e9, renderL);
  $('l-tbl').querySelectorAll('a[data-l]').forEach(x=>x.onclick=e=>{e.preventDefault(); S.g=x.dataset.l; renderL(); window.scrollTo({top:0});});
}
$('l-q').addEventListener('change',()=>{ const q=$('l-q').value.trim().toLowerCase(); const g=PG.find(x=>x.n.toLowerCase()===q)||PG.find(x=>PR[x.id]&&x.n.toLowerCase().includes(q)); if(g){ S.g=g.id; renderL(); } });
$('dl-a').innerHTML=PG.filter(g=>PR[g.id]&&!/^la/.test(g.id)&&PSEL.has(g.id)).map(g=>`<option value="${esc(g.n)}"></option>`).join('');
