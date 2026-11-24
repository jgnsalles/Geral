// =================== 4º QUARTIL ===================
// Quartis sempre em US$ (12 meses e 3 anos até o último mês), sobre as mesmas gestoras do ranking de performance.
let FL=null;
const loadF=()=>FL?Promise.resolve(FL):fetch('fluxos.json').then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); }).then(d=>{ FL=d; return d; });
S.qg=4; S.qw=12;
// quão fácil o dinheiro troca de gestora (julgamento; aparece na nota)
const MOBN={'PF varejo':.5,'PF private':.7,'Plataformas (conta e ordem)':1,'Fundos e clubes':1,'Previdência':.3,'RPPS':.3,'Seguradoras':.3,'PJ não financeira':.5,'Bancos e financeiras':.5,'Estrangeiros':.7,'Outros':.5};
const qbadge=q=>q?`<span class="qb q${q}" title="${QLBL[q-1]}">Q${q}</span>`:'<span class="zero">–</span>';
const fmo=v=>v==null?'<span class="zero">–</span>':`<span class="${v>0?'pos':v<0?'neg':'zero'}">${v>0?'+':v<0?'−':''}${plmi(Math.abs(v))}</span>`;
const med=a=>{ const v=a.filter(x=>x!=null&&isFinite(x)).sort((x,y)=>x-y); return v.length?v[Math.floor(v.length/2)]:null; };
function qUniverse(){
  const rows=PG.filter(g=>PR[g.id]&&PSEL.has(g.id)).map(g=>{ const p=PR[g.id], r=p.usd?p.rB:toUSD(p.rB);
    const e=r[PLAST]!=null?PLAST:(p.last<PLAST&&p.last>=PLAST-3&&r[p.last]!=null?p.last:null); if(e==null) return null;
    const s12=pstats(r,e-11,e,null), s36=pstats(r,e-35,e,null);
    return {id:g.id,g,p,e,key:attrKey(g.id),r12:s12?s12.ret:null,r36:s36?s36.ann:null}; }).filter(Boolean);
  const q12=qOf(new Map(rows.map(o=>[o.id,o.r12]))), q36=qOf(new Map(rows.map(o=>[o.id,o.r36])));
  rows.forEach(o=>{ o.q12=q12.get(o.id)||null; o.q36=q36.get(o.id)||null; });
  return rows; }
function LPlast(key){ const r=LP.g[key]; if(!r) return null; let li=r.p.length-1; while(li>0&&!r.p[li]) li--; if(!r.p[li]) return null; return {p:r.p[li],pl:r.pl[li],nc:r.ncot[li]}; }
// giro, concentração e tempo de permanência a partir das carteiras mensais do attribution
function behav(key,a,b){ const rec=AT.g[key]; if(!rec) return null; const P=rec.p, o=rec.o;
  const es=k=>rec.est&&rec.est[k]!=null&&rec.est[k]>5e5;
  const norm=arr=>{ const t=arr.reduce((s,x)=>s+x[1],0), m=new Map(); if(t>0) arr.forEach(([ri,w])=>m.set(ri,(m.get(ri)||0)+w/t)); return m; };
  let nT=0,sT=0,nN=0,sN=0,sTop=0,sCov=0,sEx=0;
  for(let i=a;i<=b;i++){ const k=i-o, cur=k>=0&&k<P.length?P[k]:null; if(!cur||!cur.length) continue;
    const tot=cur.reduce((s,x)=>s+x[1],0); if(tot<=0) continue; nN++;
    sN+=cur.filter(x=>x[1]>=2000).length; sTop+=cur.map(x=>x[1]).sort((x,y)=>y-x).slice(0,10).reduce((s,x)=>s+x,0)/tot; sCov+=tot/1e6;
    sEx+=cur.filter(x=>isEx(AT.roots[x[0]])).reduce((s,x)=>s+x[1],0)/tot;
    const nx=i+1<=b&&k+1<P.length?P[k+1]:null;
    if(nx&&nx.length&&!es(k)&&!es(k+1)){ const d=norm(cur.map(([ri,w,c])=>[ri,Math.max(0,w+c)])), n=norm(nx.map(([ri,w])=>[ri,w]));
      let t=0; new Set([...d.keys(),...n.keys()]).forEach(ri=>t+=Math.abs((n.get(ri)||0)-(d.get(ri)||0))); sT+=t/2; nT++; } }
  // permanência: sequências de meses com a ação (≥ 0,5% do PL), aceitando 1 mês de buraco; conta toda a história até b
  const pres=new Map(); P.forEach((arr,k)=>{ const i=o+k; if(!arr||i>b) return; arr.forEach(([ri,w])=>{ if(w<5000) return; if(!pres.has(ri)) pres.set(ri,[]); pres.get(ri).push([i,w]); }); });
  let hw=0,hs=0; pres.forEach(list=>{ let st=0; for(let j=1;j<=list.length;j++){ if(j<list.length&&list[j][0]<=list[j-1][0]+2) continue; const sp=list.slice(st,j); st=j;
      if(sp[sp.length-1][0]<a) continue; const len=sp[sp.length-1][0]-sp[0][0]+1, w=sp.filter(x=>x[0]>=a).reduce((s,x)=>s+x[1],0); hw+=w*len; hs+=w; } });
  return {n:nN?sN/nN:null, top:nN?sTop/nN:null, cov:nN?sCov/nN:null, ex:nN?sEx/nN:null, giro:nT>=Math.min(6,(b-a)/2)?sT/nT*12:null, hold:hs?hw/hs/12:null, m:nN}; }
const yrs=v=>v==null||!isFinite(v)?'<span class="zero">–</span>':nf(v,1)+' a';
function renderQ(){
  $('q-win').innerHTML=[[12,'12 meses'],[36,'3 anos']].map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.qw===v}">${l}</button>`).join('');
  $('q-win').onclick=e=>{ const x=e.target.closest('button'); if(!x) return; S.qw=+x.dataset.v; renderQ(); };
  if(!AT||!LP||!FL){ $('q-body').innerHTML='<p class="loading">Carregando carteiras, passivo e fluxos…</p>';
    Promise.all([loadA(),loadL(),loadF()]).then(renderQ).catch(e=>{ $('q-body').innerHTML=`<p class="loading">Não foi possível carregar os dados (${esc(e.message)}).</p>`; }); return; }
  const QG=4, inG=o=>(o.q12&&o.q12>=QG)||(o.q36&&o.q36>=QG), U0=qUniverse();
  // uma linha por casa (Onyx Brasil e Onyx LatAm dividem passivo e carteira)
  const EM=new Map(); U0.forEach(o=>{ if(!EM.has(o.key)) EM.set(o.key,{key:o.key,rows:[]}); EM.get(o.key).rows.push(o); });
  const plAt=(o,i)=>lastPL(o.p,Math.min(i,o.p.last));
  const ENT=[...EM.values()].map(e=>{ e.rows.sort((x,y)=>(plAt(y,PLAST)||0)-(plAt(x,PLAST)||0)); e.main=e.rows[0]; e.n=e.rows.map(o=>o.g.n).join(' + ');
    e.inG=e.rows.some(inG); e.both=e.rows.some(o=>o.q12>=QG&&o.q36>=QG); e.q12=e.main.q12; e.q36=e.main.q36; e.r12=e.main.r12; e.r36=e.main.r36;
    const lp=LPlast(e.key), plp=e.rows.reduce((s,o)=>s+(plAt(o,PLAST)||0),0);
    e.mix=lp?lp.p.map(v=>v/1e4):null; e.aum=plp||(lp?lp.pl:null); e.nc=lp?lp.nc:null;
    const f=FL[e.key]; const fs=n=>{ if(!f) return null; let s=0,k=0; for(let i=PLAST-n+1;i<=PLAST;i++){ const j=i-f.o; if(j>=0&&j<f.f.length&&f.f[j]!=null){ s+=f.f[j]; k++; } } return k?s:null; };
    e.fl=f; e.f12=fs(12); e.f36=fs(36);
    const pla=n=>e.rows.reduce((s,o)=>s+(o.p.pl[PLAST-n]||0),0); e.a12=pla(12)||null; e.a36=pla(36)||null;
    e.mob=e.mix?e.mix.reduce((s,v,k)=>s+v*(MOBN[LP.cats[k]]??.5),0):.6; e.mobEst=!e.mix;
    e.disp=e.aum!=null?e.aum*e.mob:null; e.pot=e.disp!=null?e.disp*(e.both?1:.7)*(e.f12!=null&&e.f12<0?1:.8):null;
    return e; });
  const GR=ENT.filter(e=>e.inG), RE=ENT.filter(e=>!e.inG), sum=(a,f)=>a.reduce((s,x)=>s+(f(x)||0),0);
  // ---------- contas
  const cats=LP.cats, catR=g=>cats.map((c,k)=>sum(g.filter(e=>e.mix),e=>e.aum*e.mix[k]));
  const cg=catR(GR), cr=catR(RE), tg=sum(GR,e=>e.aum), tr=sum(RE,e=>e.aum), ng=sum(GR.filter(e=>!e.mix),e=>e.aum), nr=sum(RE.filter(e=>!e.mix),e=>e.aum);
  const dispG=sum(GR,e=>e.disp), f12G=sum(GR,e=>e.f12), a12G=sum(GR.filter(e=>e.f12!=null),e=>e.a12);
  const MV=[2,3], mvG=MV.reduce((s,k)=>s+cg[k],0)/Math.max(1e-9,tg-ng), mvR=MV.reduce((s,k)=>s+cr[k],0)/Math.max(1e-9,tr-nr);
  const fq=q=>{ const g=ENT.filter(e=>e.q36===q), f=sum(g,e=>e.f36), a=sum(g.filter(e=>e.f36!=null),e=>e.a36); return a?f/a:null; };
  const W=S.qw, WL=W===12?'12 meses':'3 anos', qw=o=>W===12?o.q12:o.q36, curS=S.cur; S.cur='BRL';
  const seen=new Set(), comp=[];
  U0.forEach(o=>{ const q=qw(o); if(!q||seen.has(o.key)||!AT.g[o.key]) return; const rec=AT.g[o.key]; const b=Math.min(o.e,o.p.last), a=Math.max(b-W+1,o.p.o,rec.o); if(b-a+1<W*0.75) return;
    const r=aCompute(o.id,a,b); if(r.err) return; seen.add(o.key); comp.push({o,q,r,bh:behav(o.key,a,b)}); });
  S.cur=curS;
  const LO=comp.filter(x=>x.q===4), WI=comp.filter(x=>x.q===1), nL=Math.max(1,LO.length), nW=Math.max(1,WI.length);
  const mean=(a,f)=>a.length?a.reduce((s,x)=>s+f(x),0)/a.length:null;
  const pairs=g=>g.flatMap(x=>x.r.rows.map(y=>({g:x.o.g,root:AT.roots[y.ri],ri:y.ri,sec:secOf(AT.roots[y.ri]),c:y.c})));
  const PLo=pairs(LO), PWi=pairs(WI);
  const hit=P=>({h:P.length?P.filter(x=>x.c>0).length/P.length:null, pr:(()=>{ const u=mean(P.filter(x=>x.c>0),x=>x.c), d=mean(P.filter(x=>x.c<0),x=>x.c); return u&&d?u/-d:null; })()});
  const hL=hit(PLo), hW=hit(PWi);
  const agg=new Map(); const add=(P,side)=>P.forEach(x=>{ if(!agg.has(x.root)) agg.set(x.root,{root:x.root,ri:x.ri,sec:x.sec,L:{c:0,who:[]},W:{c:0,who:[]}}); const a=agg.get(x.root)[side]; a.c+=x.c; a.who.push(x.g.n); });
  add(PLo,'L'); add(PWi,'W');
  const EA=[...agg.values()].map(e=>({...e, cl:e.L.c/nL, cw:e.W.c/nW}));
  const cons=EA.filter(e=>e.L.who.length>=2).sort((x,y)=>x.L.c-y.L.c).slice(0,8);
  const wins=EA.filter(e=>e.W.who.length>=2&&e.cw>0).sort((x,y)=>(y.cw-y.cl)-(x.cw-x.cl)).slice(0,8);
  const bs={}; EA.forEach(e=>{ (bs[e.sec]=bs[e.sec]||{l:0,w:0}); bs[e.sec].l+=e.cl; bs[e.sec].w+=e.cw; });
  const sk=Object.keys(bs).sort((x,y)=>(bs[y].w-bs[y].l)-(bs[x].w-bs[x].l));
  const dTot=mean(WI,x=>x.r.tot)-mean(LO,x=>x.r.tot), dStk=mean(WI,x=>x.r.stk)-mean(LO,x=>x.r.stk);
  const BQ=[1,2,3,4].map(q=>{ const g=comp.filter(x=>x.q===q&&x.bh); return {q,giro:med(g.map(x=>x.bh.giro)),n:med(g.map(x=>x.bh.n)),top:med(g.map(x=>x.bh.top))}; });
  const who=a=>{ const u=[...new Set(a)]; return u.length>3?u.slice(0,3).join(', ')+` +${u.length-3}`:u.join(', '); };
  const tk=e=>`<span class="tk">${esc(dispR(e.root))}</span> <span class="muted">${esc(nameR(e.ri).slice(0,16))}</span>`;
  const a0=PLAST-35, QC=['var(--up)','var(--accent-ink)','var(--warn)','var(--down)'];
  const ser=[1,2,3,4].map(q=>{ const g=ENT.filter(e=>e.q36===q&&e.fl); const r=new Array(PN).fill(null);
    for(let i=a0;i<=PLAST;i++){ let f=0,p=0; g.forEach(e=>{ const j=i-e.fl.o, v=j>=0&&j<e.fl.f.length?e.fl.f[j]:null, pl=e.rows.reduce((s,o)=>s+(o.p.pl[i-1]||0),0); if(v!=null&&pl>0){ f+=v; p+=pl; } }); r[i]=p>0?f/p:null; }
    return {name:QLBL[q-1], r, color:QC[q-1], sw:q===1||q===4?2.4:1.4}; });
  const cumE=q=>{ let c=1; for(let i=a0;i<=PLAST;i++){ const v=ser[q-1].r[i]; if(v!=null) c*=1+v; } return c-1; };
  // ---------- página
  $('q-h').textContent='Quem está no 4º quartil';
  $('q-sub').textContent=`${GR.length} gestoras no 4º quartil em 12 meses ou 3 anos (retorno líquido em US$ até ${pmlong(PLAST)}).`;
  const top3=GR.slice().sort((x,y)=>(y.aum||0)-(x.aum||0)).slice(0,3);
  const c1=cons[0], s1=sk[0];
  let html=`<div class="qtake"><ul style="margin:0;padding-left:18px">`+
    `<li><b>R$ ${nf(tg/1000,1)} bi</b> em fundos ruins, ${pct(tg/(tg+tr),0)} do dinheiro do ranking. ${pct(sum(top3,e=>e.aum)/tg,0)} disso em três casas: ${top3.map(e=>esc(e.n)).join(', ')}.</li>`+
    `<li><b>${pct(mvG,0)}</b> está em plataformas e alocadores, o dinheiro que troca de gestora (demais: ${pct(mvR,0)}).</li>`+
    `<li><b>O dinheiro sai da classe, não vai para os vencedores:</b> em 3 anos, o 4º quartil perdeu ${pct(-cumE(4),0)} do PL por resgates, mas o 1º quartil também perdeu ${pct(-cumE(1),0)}.</li>`+
    (c1?`<li><b>Onde erraram (${WL}):</b> ${pcp(dTot)} de diferença para o 1º quartil, ${pcp(dStk)} nas ações. Maior erro coletivo: ${esc(dispR(c1.root))} (${c1.L.who.length} de ${LO.length} tinham); maior falta: ${esc(s1)}.</li>`:'')+
    `</ul></div>`;
  // 1
  const order=cats.map((c,k)=>k).sort((x,y)=>cg[y]-cg[x]).filter(k=>cg[k]/tg>=0.02||cr[k]/tr>=0.02);
  const oth=(arr,t,nn)=>t-nn-order.reduce((s,k)=>s+arr[k],0);
  const bar=(lbl,arr,t,nn)=>`<div class="nm">${lbl}</div><div class="stack">${order.map(k=>`<i style="width:${arr[k]/t*100}%;background:${LCOL[k%LCOL.length]}" title="${esc(cats[k])}: ${nf(arr[k]/t*100,0)}%"></i>`).join('')}<i style="width:${(oth(arr,t,nn)+nn)/t*100}%;background:var(--grid)" title="outros / sem dado"></i></div><div class="v">${plmi(t)}</div>`;
  html+=`<div class="qsec">1<b>Quanto dinheiro e de quem</b></div>`+
    `<div class="dec">${kpis([['PL no 4º quartil','R$ '+nf(tg/1000,1)+' bi',`${GR.length} gestoras`],['Disputável','R$ '+nf(dispG/1000,1)+' bi','ponderado por tipo de cotista'],['Captação 12m',fmo(f12G),a12G?`${pct(f12G/a12G,0)} do PL`:'']])}</div>`+
    `<div class="card"><div class="qmix">${bar('<b>4º quartil</b>',cg,tg,ng)}${bar('Demais',cr,tr,nr)}</div>`+
    `<div class="pleg">${order.map(k=>`<span><i style="background:${LCOL[k%LCOL.length]}"></i>${esc(cats[k])} ${nf(cg[k]/tg*100,0)}% <span class="muted">vs ${nf(cr[k]/tr*100,0)}%</span></span>`).join('')}</div></div>`;
  // 2
  html+=`<div class="qsec">2<b>De quem tirar share</b></div><div class="card"><div class="tblwrap"><table id="q-don"></table></div>`+
    `<p class="note">Ordem = PL × quanto do passivo é móvel × (mais peso se está no 4º quartil nas duas janelas e já perde dinheiro). Móvel = plataformas + fundos e clubes.</p></div>`;
  // 3
  html+=`<div class="qsec">3<b>Para onde vai o dinheiro</b></div><div class="card"><div class="hd"><h2>PL ganho ou perdido só por captação, 3 anos</h2><small>por quartil de 3 anos</small></div><div id="q-fchart"></div></div>`;
  // 4
  const crow=(e,side)=>side==='L'?`<tr><td class="l secbar" style="--c:${secC(e.sec)}">${tk(e)}</td><td class="l muted" style="white-space:normal;font-size:12px">${esc(who(e.L.who))}</td><td style="font-weight:600">${pcp(e.cl)}</td></tr>`
    :`<tr><td class="l secbar" style="--c:${secC(e.sec)}">${tk(e)}</td><td class="l muted" style="white-space:normal;font-size:12px">${esc(who(e.W.who))}</td><td style="font-weight:600">${pcp(e.cw)}</td><td class="muted">${pcp(e.cl)}</td></tr>`;
  const mxs=Math.max(1e-9,...sk.map(k=>Math.abs(bs[k].w-bs[k].l)));
  html+=`<div class="qsec">4<b>O que deu errado · ${WL}</b></div>`+
    `<div class="dec">${kpis([['Diferença p/ 1º quartil',pcp(dTot),`retorno médio ${pc(mean(LO,x=>x.r.tot),0)} vs ${pc(mean(WI,x=>x.r.tot),0)}`],['Vem das ações',pcp(dStk),'o resto: caixa, trades no mês, taxas'],['Acerto',pct(hL.h,0),`1º quartil ${pct(hW.h,0)}`],['Ganho ÷ perda',hL.pr?nf(hL.pr,1)+'×':'–',`1º quartil ${hW.pr?nf(hW.pr,1)+'×':'–'}`]])}</div>`+
    `<div class="grid2"><div class="card"><div class="hd"><h2>Erros coletivos</h2><small>o que mais tirou do 4º quartil</small></div><div class="tblwrap"><table><thead><tr><th class="l">Empresa</th><th class="l">Quem tinha</th><th>Média</th></tr></thead><tbody>${cons.map(e=>crow(e,'L')).join('')}</tbody></table></div></div>`+
    `<div class="card"><div class="hd"><h2>O que os vencedores tinham</h2><small>maior vantagem do 1º quartil</small></div><div class="tblwrap"><table><thead><tr><th class="l">Empresa</th><th class="l">Quem tinha (1º quartil)</th><th>Média 1º q.</th><th>Média 4º q.</th></tr></thead><tbody>${wins.map(e=>crow(e,'W')).join('')}</tbody></table></div></div></div>`+
    `<div class="card"><div class="hd"><h2>Diferença por setor</h2><small>1º quartil − 4º quartil, p.p. por gestora</small></div><div class="dbar">${sk.filter(k=>Math.abs(bs[k].w-bs[k].l)>=0.01).map(k=>{ const g=bs[k].w-bs[k].l, w_=Math.abs(g)/mxs*50; return `<div class="nm"><span class="secp"><i style="background:${secC(k)}"></i>${esc(k)}</span></div><div class="tr"><span class="ax" style="left:50%"></span><i style="background:${g>=0?'var(--up)':'var(--down)'};${g>=0?`left:50%;width:${w_}%`:`right:50%;width:${w_}%`}"></i></div><div class="v">${pcp(g)}</div>`; }).join('')}</div>`+
    `<p class="note">"Média" = contribuição somada ÷ nº de gestoras do quartil (quem não tinha conta zero). Verde = setor rendeu mais para os vencedores; setores com diferença abaixo de 1 p.p. omitidos.</p></div>`;
  // 5
  html+=`<div class="qsec">5<b>Giram demais?</b></div><div class="card"><div class="tblwrap"><table><thead><tr><th class="l">Quartil (${WL})</th><th>Giro anual</th><th>Holding</th><th>Nº ações</th><th>Top 10</th></tr></thead><tbody>${BQ.map(x=>`<tr${x.q===4?' class="mine"':''}><td class="l">${qbadge(x.q)} ${QLBL[x.q-1]}</td><td style="font-weight:600">${pct(x.giro,0)}</td><td>${yrs(x.giro?1/x.giro:null)}</td><td>${x.n==null?'–':nf(x.n,0)}</td><td>${pct(x.top,0)}</td></tr>`).join('')}</tbody></table></div>`+
    `<p class="note">Medianas. Giro = troca de carteira de um mês para o outro, sem o efeito do preço (piso: não vê trades dentro do mês). Holding = 1 ÷ giro. Por gestora, na aba Attribution.</p></div>`;
  html+=`<p class="note">Quartis = retorno líquido em US$ de 12 meses e 3 anos (a.a.), mesmas gestoras da aba Performance. Passivo: Perfil Mensal da CVM; captação: aplicações − resgates do Informe Diário; seções 4 e 5 em R$, pela carteira da CDA.</p>`;
  $('q-body').innerHTML=html;
  sTable('q-don',[
    {k:'g',l:'Gestora',cls:'l',v:e=>e.n,asc:true,f:e=>`<td class="l"><a href="#" data-q="${e.main.id}">${esc(e.n)}</a></td>`},
    {k:'q',l:'12m · 3a',v:e=>(e.q12||0)+(e.q36||0),f:e=>`<td>${qbadge(e.q12)} ${qbadge(e.q36)}</td>`},
    {k:'aum',l:'PL',v:e=>e.aum,f:e=>`<td>${plmi(e.aum)}</td>`},
    {k:'f12',l:'Captação 12m',v:e=>e.f12!=null&&e.a12?e.f12/e.a12:null,f:e=>`<td>${fmo(e.f12)} <small class="muted">${e.f12!=null&&e.a12?pct(e.f12/e.a12,0):''}</small></td>`},
    {k:'mv',l:'Passivo móvel',v:e=>e.mix?e.mix[2]+e.mix[3]:null,f:e=>`<td>${e.mix?pct(e.mix[2]+e.mix[3],0):'–'}</td>`},
    {k:'pot',l:'Potencial',v:e=>e.pot,f:e=>`<td style="font-weight:600">${plmi(e.pot)}</td>`},
  ], GR, 'pot', ()=>'', 10, renderQ);
  $('q-body').querySelectorAll('a[data-q]').forEach(x=>x.onclick=e=>{ e.preventDefault(); S.g=x.dataset.q; setView('l'); renderL(); });
  cumChart($('q-fchart'), ser, a0, PLAST, {endLabels:true, noLegend:true, h:260, label:'Captação acumulada por quartil'});
}
