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
  $('q-grp').innerHTML=[[4,'Só 4º quartil'],[3,'3º e 4º quartis']].map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.qg===v}">${l}</button>`).join('');
  $('q-grp').onclick=e=>{ const x=e.target.closest('button'); if(!x) return; S.qg=+x.dataset.v; renderQ(); };
  $('q-win').innerHTML=[[12,'12 meses'],[36,'3 anos']].map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.qw===v}">${l}</button>`).join('');
  $('q-win').onclick=e=>{ const x=e.target.closest('button'); if(!x) return; S.qw=+x.dataset.v; renderQ(); };
  if(!AT||!LP||!FL){ $('q-body').innerHTML='<p class="loading">Carregando carteiras, passivo e fluxos…</p>';
    Promise.all([loadA(),loadL(),loadF()]).then(renderQ).catch(e=>{ $('q-body').innerHTML=`<p class="loading">Não foi possível carregar os dados (${esc(e.message)}).</p>`; }); return; }
  const QG=S.qg, inG=o=>(o.q12&&o.q12>=QG)||(o.q36&&o.q36>=QG), U0=qUniverse();
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
  const gl=QG===4?'4º quartil':'3º e 4º quartis';
  $('q-h').textContent=`Quem está no ${gl}`;
  $('q-sub').textContent=`${GR.length} das ${ENT.length} gestoras do ranking estão no ${gl} em 12 meses ou em 3 anos (retorno líquido em US$ até ${pmlong(PLAST)}). Dinheiro em R$; passivo pelo Perfil Mensal da CVM; captação pelo Informe Diário.`;
  // ---------- 1. passivo
  const cats=LP.cats, catR=g=>cats.map((c,k)=>sum(g.filter(e=>e.mix),e=>e.aum*e.mix[k]));
  const cg=catR(GR), cr=catR(RE), tg=sum(GR,e=>e.aum), tr=sum(RE,e=>e.aum), ng=sum(GR.filter(e=>!e.mix),e=>e.aum), nr=sum(RE.filter(e=>!e.mix),e=>e.aum);
  const dispG=sum(GR,e=>e.disp), f12G=sum(GR,e=>e.f12), a12G=sum(GR.filter(e=>e.f12!=null),e=>e.a12), f12R=sum(RE,e=>e.f12), a12R=sum(RE.filter(e=>e.f12!=null),e=>e.a12);
  const order=cats.map((c,k)=>k).sort((x,y)=>cg[y]-cg[x]);
  const mixRow=(lbl,arr,t,nn)=>`<div class="nm">${lbl}</div><div class="stack">${order.map(k=>arr[k]>0?`<i style="width:${arr[k]/t*100}%;background:${LCOL[k%LCOL.length]}" title="${esc(cats[k])}: ${nf(arr[k]/t*100,1)}%"></i>`:'').join('')}${nn>0?`<i style="width:${nn/t*100}%;background:var(--grid)" title="sem Perfil Mensal: ${nf(nn/t*100,1)}%"></i>`:''}</div><div class="v">${plmi(t)}</div>`;
  const top3=GR.slice().sort((x,y)=>(y.aum||0)-(x.aum||0)).slice(0,3);
  const mobK=cats.map((c,k)=>k).filter(k=>(MOBN[cats[k]]??.5)>=1), mobShare=mobK.reduce((s,k)=>s+cg[k],0)/Math.max(1e-9,tg-ng);
  let html=`<div class="qtake"><b>Resumo.</b><ul style="margin:4px 0 0;padding-left:18px">`+
    `<li>R$ ${nf(tg/1000,1)} bi em fundos long only de ${GR.length} gestoras (${pct(tg/(tg+tr),0)} do dinheiro do ranking). As três maiores: ${top3.map(e=>`${esc(e.n)} (${plmi(e.aum)})`).join(', ')}.</li>`+
    `<li>${pct(mobShare,0)} desse dinheiro está em plataformas ou com alocadores (fundos e clubes), que trocam de gestora com mais facilidade.</li>`+
    `<li>Captação líquida em 12 meses: grupo ${fmo(f12G)} (${pct(a12G?f12G/a12G:null,0)} do PL de um ano atrás); demais gestoras ${fmo(f12R)} (${pct(a12R?f12R/a12R:null,0)}).</li></ul></div>`;
  html+=`<div class="qsec">1 · Passivo<b>Quanto dinheiro e de quem</b></div>`;
  html+=`<div class="dec">${kpis([
    ['PL do grupo', 'R$ '+nf(tg/1000,1)+' bi', `${GR.length} gestoras · ${pct(tg/(tg+tr),0)} do total`],
    ['Dinheiro disputável', 'R$ '+nf(dispG/1000,1)+' bi', 'PL × mobilidade do tipo de cotista'],
    ['Captação 12m', fmo(f12G), a12G?`${pct(f12G/a12G,1)} do PL de 12 meses atrás`:''],
    ['Cotistas', sum(GR,e=>e.nc).toLocaleString('pt-BR'), 'nos fundos long only do grupo'],
  ])}</div>`;
  html+=`<div class="card"><div class="hd"><h2>Tipo de cotista: grupo × demais gestoras</h2><small>% do PL · R$ à direita</small></div>`+
    `<div class="qmix">${mixRow(`<b>${gl}</b>`,cg,tg,ng)}${mixRow('Demais',cr,tr,nr)}</div>`+
    `<div class="pleg">${order.filter(k=>cg[k]+cr[k]>0).map(k=>`<span><i style="background:${LCOL[k%LCOL.length]}"></i>${esc(cats[k])}</span>`).join('')}<span><i style="background:var(--grid)"></i>sem Perfil Mensal</span></div>`+
    `<div class="tblwrap"><table><thead><tr><th class="l">Tipo de cotista</th><th>Grupo (R$)</th><th>% grupo</th><th>% demais</th><th>Mobilidade</th></tr></thead><tbody>${order.filter(k=>cg[k]>0||cr[k]>0).map(k=>`<tr><td class="l"><span class="sw" style="background:${LCOL[k%LCOL.length]}"></span>${esc(cats[k])}</td><td style="font-weight:600">${plmi(cg[k])}</td><td>${pct(cg[k]/tg,1)}</td><td class="muted">${pct(cr[k]/tr,1)}</td><td class="muted">${pct(MOBN[cats[k]]??.5,0)}</td></tr>`).join('')}</tbody></table></div></div>`;
  // ---------- doadores
  html+=`<div class="qsec">2 · Doadores de share<b>Onde está o dinheiro mais fácil de capturar</b></div>`+
    `<div class="card"><div class="hd"><h2>Gestoras do grupo</h2><small>ordenadas pelo potencial · clique no cabeçalho para reordenar</small></div><div class="tblwrap" style="max-height:640px;overflow-y:auto"><table id="q-don"></table></div>`+
    `<p class="note"><b>Potencial</b> = PL × mobilidade × intensidade. Mobilidade = média ponderada pelo tipo de cotista: plataformas e fundos/clubes 100%, private e estrangeiros 70%, varejo, PJ e bancos 50%, previdência, RPPS e seguradoras 30% (sem Perfil Mensal: 60%). Intensidade: 1 se está no grupo nas duas janelas, 0,7 se só numa; × 0,8 se não perdeu dinheiro em 12 meses. É um critério de julgamento para ordenar a lista, não uma previsão.</p></div>`;
  // ---------- 3. fluxos
  const qtab=(w)=>{ const qq=e=>w===12?e.q12:e.q36; return `<table><thead><tr><th class="l">Quartil ${w===12?'12m':'3 anos'}</th><th>Gestoras</th><th>PL hoje</th><th>Captação 12m</th><th>% PL</th><th>Captação 3a</th><th>% PL</th></tr></thead><tbody>${[1,2,3,4].map(q=>{ const g=ENT.filter(e=>qq(e)===q), f1=sum(g,e=>e.f12), f3=sum(g,e=>e.f36), a1=sum(g.filter(e=>e.f12!=null),e=>e.a12), a3=sum(g.filter(e=>e.f36!=null),e=>e.a36);
      return `<tr><td class="l">${qbadge(q)} ${QLBL[q-1]}</td><td class="muted">${g.length}</td><td>${plmi(sum(g,e=>e.aum))}</td><td>${fmo(f1)}</td><td>${a1?pcp(f1/a1).replace(' p.p.','%'):'–'}</td><td>${fmo(f3)}</td><td>${a3?pcp(f3/a3).replace(' p.p.','%'):'–'}</td></tr>`; }).join('')}</tbody></table>`; };
  html+=`<div class="qsec">3 · Fluxos<b>O dinheiro já está saindo? Para onde?</b></div>`+
    `<div class="grid2"><div class="card"><div class="hd"><h2>Por quartil de 12 meses</h2></div><div class="tblwrap">${qtab(12)}</div></div><div class="card"><div class="hd"><h2>Por quartil de 3 anos</h2></div><div class="tblwrap">${qtab(36)}</div></div></div>`+
    `<div class="card"><div class="hd"><h2>Crescimento só por captação, últimos 3 anos</h2><small>por quartil de 3 anos · captação do mês ÷ PL do mês anterior, acumulada</small></div><div id="q-fchart"></div>`+
    `<p class="note">Captação líquida = aplicações − resgates do Informe Diário, nos fundos usados na performance (FICs da gestora e fundos diretos); fundos LatAm por PL − PL anterior × (1 + retorno). % PL = captação ÷ PL no início do período. Movimentos entre fundos da mesma casa podem aparecer como saída de um fundo e entrada em outro fora da base (ex.: um fundo long biased).</p></div>`;
  // ---------- 4. dissecação (em R$)
  const W=S.qw, qw=o=>W===12?o.q12:o.q36, curS=S.cur; S.cur='BRL';
  const seen=new Set(), comp=[];
  U0.forEach(o=>{ const q=qw(o); if(!q||seen.has(o.key)||!AT.g[o.key]) return; const rec=AT.g[o.key]; const b=Math.min(o.e,o.p.last), a=Math.max(b-W+1,o.p.o,rec.o); if(b-a+1<W*0.75) return;
    const r=aCompute(o.id,a,b); if(r.err) return; seen.add(o.key); comp.push({o,q,r,a,b,bh:behav(o.key,a,b)}); });
  S.cur=curS;
  const LO=comp.filter(x=>x.q>=QG), WI=comp.filter(x=>x.q===1);
  const pairs=g=>g.flatMap(x=>x.r.rows.map(y=>({x,id:x.o.id,g:x.o.g,root:AT.roots[y.ri],ri:y.ri,sec:secOf(AT.roots[y.ri]),c:y.c,w:y.w,n:y.n,r:y.r,ms:y.ms})));
  const PL_=pairs(LO), PW=pairs(WI);
  const mean=(a,f)=>a.length?a.reduce((s,x)=>s+f(x),0)/a.length:null;
  const hit=P=>({h:P.length?P.filter(x=>x.c>0).length/P.length:null, up:mean(P.filter(x=>x.c>0),x=>x.c), dn:mean(P.filter(x=>x.c<0),x=>x.c)});
  const hL=hit(PL_), hW=hit(PW);
  const WL=W===12?'12 meses':'3 anos';
  html+=`<div class="qsec">4 · Dissecação · ${WL}<b>O que o grupo errou e o que os vencedores fizeram diferente</b></div>`+
    `<p class="note" style="margin-top:0">Grupo = ${gl} na janela de ${WL} (${LO.length} gestoras com carteira); comparação = 1º quartil na mesma janela (${WI.length}). Em R$, média simples entre gestoras.</p>`+
    `<div class="dec">${[['Retorno líquido',x=>x.r.tot],['Ações',x=>x.r.stk],['Outros',x=>x.r.oth],['Taxas e custos',x=>x.r.fee]].map(([l,f],k)=>{ const a=mean(LO,f), b=mean(WI,f); return `<div class="kpi"><div class="lbl">${l} · média</div><div class="v">${k?pcp(a):pc(a)}</div><div class="d">1º quartil ${k?pcp(b):pc(b)} · diferença ${pcp(b!=null&&a!=null?b-a:null)}</div></div>`; }).join('')}`+
    `<div class="kpi"><div class="lbl">Acerto</div><div class="v">${pct(hL.h,0)}</div><div class="d">posições que somaram · 1º quartil ${pct(hW.h,0)}</div></div>`+
    `<div class="kpi"><div class="lbl">Ganho ÷ perda média</div><div class="v">${hL.up&&hL.dn?nf(hL.up/-hL.dn,2):'–'}</div><div class="d">por posição · 1º quartil ${hW.up&&hW.dn?nf(hW.up/-hW.dn,2):'–'}</div></div></div>`;
  const prow=(x,k)=>`<tr><td class="muted">${k}</td><td class="l">${esc(x.g.n)}</td><td class="l secbar" style="--c:${secC(x.sec)}"><span class="tk">${esc(dispR(x.root))}</span> <span class="muted">${esc(nameR(x.ri).slice(0,22))}</span></td><td>${pct(x.w,1)}</td>${spanCell(x.ms)}<td>${pc(x.r)}</td><td style="font-weight:600">${pcp(x.c)}</td></tr>`;
  const phead='<thead><tr><th>#</th><th class="l">Gestora</th><th class="l">Empresa</th><th>Peso médio</th><th class="l">Períodos na carteira</th><th>Retorno na carteira</th><th>Contribuição</th></tr></thead>';
  const srt=PL_.slice().sort((x,y)=>x.c-y.c), secs=SECN;
  html+=`<div class="grid2"><div class="card"><div class="hd"><h2>Maiores erros do grupo</h2><small>gestora × empresa · p.p. do retorno</small></div>${secLegend()}<div class="tblwrap" style="max-height:560px;overflow-y:auto"><table>${phead}<tbody>${srt.slice(0,30).map((x,k)=>prow(x,k+1)).join('')}</tbody></table></div></div>`+
    `<div class="card"><div class="hd"><h2>Maiores acertos do grupo</h2><small>o que funcionou mesmo assim</small></div>${secLegend()}<div class="tblwrap" style="max-height:560px;overflow-y:auto"><table>${phead}<tbody>${srt.slice().reverse().slice(0,30).map((x,k)=>prow(x,k+1)).join('')}</tbody></table></div></div></div>`;
  // por empresa: consenso e diferença para o 1º quartil
  const agg=new Map(); const add=(P,side)=>P.forEach(x=>{ if(!agg.has(x.root)) agg.set(x.root,{root:x.root,ri:x.ri,sec:x.sec,L:{c:0,n:0,who:[],r:[]},W:{c:0,n:0,who:[],r:[]}}); const a=agg.get(x.root)[side]; a.c+=x.c; a.n++; a.who.push(x.g.n); a.r.push(x.r); });
  add(PL_,'L'); add(PW,'W');
  const nL=Math.max(1,LO.length), nW=Math.max(1,WI.length);
  const E_=[...agg.values()].map(e=>({...e, cl:e.L.c/nL, cw:e.W.c/nW, gap:e.W.c/nW-e.L.c/nL}));
  const erow=(e,k)=>`<tr><td class="muted">${k}</td><td class="l secbar" style="--c:${secC(e.sec)}"><span class="tk">${esc(dispR(e.root))}</span> <span class="muted">${esc(nameR(e.ri).slice(0,22))}</span></td><td title="${esc(e.L.who.join(', '))}">${e.L.n} de ${LO.length}</td><td>${pcp(e.cl)}</td><td class="muted" title="${esc(e.W.who.join(', '))}">${e.W.n} de ${WI.length}</td><td>${pcp(e.cw)}</td><td style="font-weight:600">${pcp(e.gap)}</td></tr>`;
  const ehead=`<thead><tr><th>#</th><th class="l">Empresa</th><th>No grupo</th><th>Contrib. média grupo</th><th>No 1º quartil</th><th>Contrib. média 1º quartil</th><th>Diferença</th></tr></thead>`;
  const cons=E_.filter(e=>e.L.n>=2).sort((x,y)=>x.L.c-y.L.c).slice(0,20);
  html+=`<div class="card"><div class="hd"><h2>Erros de consenso</h2><small>ações que 2+ gestoras do grupo tinham e mais tiraram do grupo somado · passe o mouse para ver quem</small></div>${secLegend()}<div class="tblwrap" style="max-height:560px;overflow-y:auto"><table>${ehead}<tbody>${cons.map((e,k)=>erow(e,k+1)).join('')}</tbody></table></div>`+
    `<p class="note">Contribuição média = soma das contribuições dividida pelo número de gestoras do lado (quem não tinha a ação entra com zero). Diferença = 1º quartil − grupo: positiva = a ação ajudou mais os vencedores.</p></div>`;
  // setores
  const bs={}; E_.forEach(e=>{ (bs[e.sec]=bs[e.sec]||{l:0,w:0}); bs[e.sec].l+=e.cl; bs[e.sec].w+=e.cw; });
  const sk=Object.keys(bs).sort((x,y)=>(bs[y].w-bs[y].l)-(bs[x].w-bs[x].l)), mxs=Math.max(1e-9,...sk.map(k=>Math.abs(bs[k].w-bs[k].l)));
  const gapBars=sk.map(k=>{ const g=bs[k].w-bs[k].l, wpc=Math.abs(g)/mxs*50; return `<div class="nm"><span class="secp"><i style="background:${secC(k)}"></i>${esc(k)}</span></div><div class="tr" title="1º quartil ${nf(bs[k].w*100,1)} p.p. · grupo ${nf(bs[k].l*100,1)} p.p."><span class="ax" style="left:50%"></span><i style="background:${g>=0?'var(--up)':'var(--down)'};${g>=0?`left:50%;width:${wpc}%`:`right:50%;width:${wpc}%`}"></i></div><div class="v">${pcp(g)}<small class="muted" style="display:block;font-size:10.5px">${nf(bs[k].w*100,1)} vs ${nf(bs[k].l*100,1)}</small></div>`; }).join('');
  const gTot=sum(sk,k=>bs[k].w-bs[k].l);
  const gp=E_.slice().sort((x,y)=>y.gap-x.gap).slice(0,15), gn=E_.slice().sort((x,y)=>x.gap-y.gap).slice(0,15);
  html+=`<div class="card"><div class="hd"><h2>Onde está a diferença: 1º quartil − grupo, por setor</h2><small>contribuição média das ações · total ${pcp(gTot)}</small></div><div class="dbar">${gapBars}</div>`+
    `<p class="note">Direita (verde) = o setor rendeu mais para os vencedores (por terem mais peso, ações melhores ou ambos); esquerda = o grupo foi melhor ali. Valores embaixo: 1º quartil vs grupo, em p.p.</p></div>`+
    `<div class="grid2"><div class="card"><div class="hd"><h2>O que os vencedores tinham e o grupo não</h2><small>maior diferença a favor do 1º quartil</small></div><div class="tblwrap" style="max-height:520px;overflow-y:auto"><table>${ehead}<tbody>${gp.map((e,k)=>erow(e,k+1)).join('')}</tbody></table></div></div>`+
    `<div class="card"><div class="hd"><h2>Onde o grupo foi melhor</h2><small>maior diferença a favor do grupo</small></div><div class="tblwrap" style="max-height:520px;overflow-y:auto"><table>${ehead}<tbody>${gn.map((e,k)=>erow(e,k+1)).join('')}</tbody></table></div></div></div>`;
  // ---------- 5. comportamento
  const BQ=[1,2,3,4].map(q=>{ const g=comp.filter(x=>x.q===q&&x.bh); return {q,k:g.length,giro:med(g.map(x=>x.bh.giro)),hold:med(g.map(x=>x.bh.hold)),n:med(g.map(x=>x.bh.n)),top:med(g.map(x=>x.bh.top)),cov:med(g.map(x=>x.bh.cov)),ex:med(g.map(x=>x.bh.ex)),ret:med(g.map(x=>x.r.tot))}; });
  html+=`<div class="qsec">5 · Comportamento · ${WL}<b>Quem perde está girando demais?</b></div>`+
    `<div class="card"><div class="hd"><h2>Mediana por quartil</h2><small>quartil da janela de ${WL}</small></div><div class="tblwrap"><table><thead><tr><th class="l">Quartil</th><th>Gestoras</th><th>Retorno R$</th><th>Giro anual</th><th>Holding implícito</th><th>Permanência média</th><th>Nº ações</th><th>Top 10</th><th>Em ações</th><th>Ex-Brasil</th></tr></thead><tbody>${BQ.map(x=>`<tr${x.q>=QG?' class="mine"':''}><td class="l">${qbadge(x.q)} ${QLBL[x.q-1]}</td><td class="muted">${x.k}</td><td>${pc(x.ret)}</td><td style="font-weight:600">${pct(x.giro,0)}</td><td>${yrs(x.giro?1/x.giro:null)}</td><td>${yrs(x.hold)}</td><td>${x.n==null?'–':nf(x.n,0)}</td><td>${pct(x.top,0)}</td><td>${pct(x.cov,0)}</td><td>${pct(x.ex,0)}</td></tr>`).join('')}</tbody></table></div></div>`+
    `<div class="card"><div class="hd"><h2>Todas as gestoras</h2><small>linhas do grupo destacadas · clique no cabeçalho para ordenar</small></div><div class="tblwrap" style="max-height:620px;overflow-y:auto"><table id="q-beh"></table></div>`+
    `<p class="note"><b>Giro anual</b> = metade da soma das mudanças de peso de um mês para o outro, já descontado o efeito do preço (a carteira do mês anterior é atualizada pelo retorno de cada ação), × 12; compras e vendas dentro do mesmo mês não aparecem, então é um piso. Meses com carteira em sigilo ficam de fora. <b>Holding implícito</b> = 1 ÷ giro. <b>Permanência média</b> = tempo que cada posição relevante (≥ 0,5% do PL) ficou na carteira, ponderado pelo peso, contando toda a história até o fim da janela (posições ainda abertas contam até hoje, então subestima). <b>Nº ações</b> = posições ≥ 0,2% do PL. <b>Top 10</b> = peso das 10 maiores sobre a parte em ações. <b>Em ações</b> = parte do PL em ações identificadas.</p></div>`;
  html+=`<p class="note"><b>Como o grupo é formado.</b> Mesmas gestoras e mesma conta da aba Performance (fundos long only, cota líquida), sempre em US$: retorno de 12 meses e retorno anualizado de 3 anos até ${pmlong(PLAST)}, divididos em quatro partes iguais. Gestoras sem 3 anos de história só têm o quartil de 12 meses. Na dissecação e no comportamento, os quartis são os da janela escolhida.</p>`;
  $('q-body').innerHTML=html;
  // tabelas ordenáveis
  sTable('q-don',[
    {k:'g',l:'Gestora',cls:'l',v:e=>e.n,asc:true,f:e=>`<td class="l"><a href="#" data-q="${e.main.id}">${esc(e.n)}</a>${e.both?' <span class="chip warn" title="no grupo em 12 meses e em 3 anos">nas duas janelas</span>':''}</td>`},
    {k:'q12',l:'12m<br><small>US$</small>',v:e=>e.r12,f:e=>`<td>${qbadge(e.q12)} ${pc(e.r12,0)}</td>`},
    {k:'q36',l:'3 anos<br><small>US$ a.a.</small>',v:e=>e.r36,f:e=>`<td>${qbadge(e.q36)} ${pc(e.r36,0)}</td>`},
    {k:'aum',l:'PL',v:e=>e.aum,f:e=>`<td>${plmi(e.aum)}</td>`},
    {k:'f12',l:'Captação<br><small>12m</small>',v:e=>e.f12,f:e=>`<td>${fmo(e.f12)}${e.f12!=null&&e.a12?`<small class="muted" style="display:block;font-size:11px">${pct(e.f12/e.a12,0)}</small>`:''}</td>`},
    {k:'f36',l:'Captação<br><small>3 anos</small>',v:e=>e.f36,f:e=>`<td>${fmo(e.f36)}${e.f36!=null&&e.a36?`<small class="muted" style="display:block;font-size:11px">${pct(e.f36/e.a36,0)}</small>`:''}</td>`},
    {k:'nc',l:'Cotistas',v:e=>e.nc,f:e=>`<td class="muted">${e.nc==null?'–':e.nc.toLocaleString('pt-BR')}</td>`},
    ...[['Plataf.',[2]],['Fundos e clubes',[3]],['PF',[0,1]],['Prev./inst.',[4,5,6]]].map(([l,ks],j)=>({k:'m'+j,l,v:e=>e.mix?ks.reduce((s,k)=>s+e.mix[k],0):null,f:e=>`<td class="muted">${e.mix?pct(ks.reduce((s,k)=>s+e.mix[k],0),0):'–'}</td>`})),
    {k:'disp',l:'Disputável',v:e=>e.disp,f:e=>`<td>${plmi(e.disp)}${e.mobEst?' <span class="chip" title="sem Perfil Mensal: mobilidade assumida de 60%">est.</span>':''}</td>`},
    {k:'pot',l:'Potencial',v:e=>e.pot,f:e=>`<td style="font-weight:600">${plmi(e.pot)}</td>`},
  ], GR, 'pot', ()=>'', 1e9, renderQ);
  const BR=comp.map(x=>({...x, n:x.o.g.n, mine:x.q>=QG}));
  sTable('q-beh',[
    {k:'g',l:'Gestora',cls:'l',v:x=>x.n,asc:true,f:x=>`<td class="l">${esc(x.n)}</td>`},
    {k:'q',l:'Quartil',v:x=>-x.q,f:x=>`<td>${qbadge(x.q)}</td>`},
    {k:'ret',l:'Retorno R$',v:x=>x.r.tot,f:x=>`<td>${pc(x.r.tot)}</td>`},
    {k:'giro',l:'Giro anual',v:x=>x.bh&&x.bh.giro,f:x=>`<td style="font-weight:600">${pct(x.bh&&x.bh.giro,0)}</td>`},
    {k:'hi',l:'Holding<br><small>implícito</small>',v:x=>x.bh&&x.bh.giro?1/x.bh.giro:null,f:x=>`<td>${yrs(x.bh&&x.bh.giro?1/x.bh.giro:null)}</td>`},
    {k:'hold',l:'Permanência<br><small>média</small>',v:x=>x.bh&&x.bh.hold,f:x=>`<td>${yrs(x.bh&&x.bh.hold)}</td>`},
    {k:'n',l:'Nº ações',v:x=>x.bh&&x.bh.n,f:x=>`<td class="muted">${x.bh&&x.bh.n!=null?nf(x.bh.n,0):'–'}</td>`},
    {k:'top',l:'Top 10',v:x=>x.bh&&x.bh.top,f:x=>`<td class="muted">${pct(x.bh&&x.bh.top,0)}</td>`},
    {k:'cov',l:'Em ações',v:x=>x.bh&&x.bh.cov,f:x=>`<td class="muted">${pct(x.bh&&x.bh.cov,0)}</td>`},
  ], BR, 'giro', x=>x.mine?'data-mine="1"':'', 1e9, renderQ);
  $('q-body').querySelectorAll('a[data-q]').forEach(x=>x.onclick=e=>{ e.preventDefault(); S.g=x.dataset.q; setView('l'); renderL(); });
  // gráfico de captação acumulada por quartil de 3 anos
  const a0=PLAST-35, QC=['var(--up)','var(--accent-ink)','var(--warn)','var(--down)'];
  const ser=[1,2,3,4].map(q=>{ const g=ENT.filter(e=>e.q36===q&&e.fl); const r=new Array(PN).fill(null);
    for(let i=a0;i<=PLAST;i++){ let f=0,p=0; g.forEach(e=>{ const j=i-e.fl.o, v=j>=0&&j<e.fl.f.length?e.fl.f[j]:null, pl=e.rows.reduce((s,o)=>s+(o.p.pl[i-1]||0),0); if(v!=null&&pl>0){ f+=v; p+=pl; } }); r[i]=p>0?f/p:null; }
    return {name:QLBL[q-1], r, color:QC[q-1], sw:q===1||q===4?2.4:1.6}; });
  cumChart($('q-fchart'), ser, a0, PLAST, {endLabels:true, noLegend:true, label:'Captação acumulada por quartil'});
}
