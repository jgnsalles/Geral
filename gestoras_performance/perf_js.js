// ---------- performance (Informe Diário: cota dos fundos de ações da gestora) ----------
const PM=PF.meses, PN=PM.length, PI={}; PM.forEach((m,i)=>PI[m]=i);
const pml=i=>{const [y,m]=PM[i].split('-'); return `${MES[+m-1]}/${y.slice(2)}`;};
const pmlong=i=>{const [y,m]=PM[i].split('-'); return `${MES[+m-1]}/${y}`;};
const dec=v=>v==null?null:v/1e6;
const IBVB=PF.ibov.map(dec), CDIB=PF.cdi.map(dec);
// moeda: retorno em US$ = (1 + retorno em R$) × (dólar no fim do mês anterior / dólar no fim do mês) − 1
const FXR=(PF.fxr||[]).map(dec);
const toUSD=r=>r.map((v,i)=>v==null||FXR[i]==null?null:(1+v)*(1+FXR[i])-1);
let IBV=IBVB, CDI=CDIB;
S.cur='USD';
const PR={}; Object.entries(PF.g).forEach(([id,x])=>{ const r=new Array(PN).fill(null), pl=new Array(PN).fill(null), nf=new Array(PN).fill(0);
  x.r.forEach((v,k)=>r[x.o+k]=dec(v)); x.pl.forEach((v,k)=>pl[x.o+k]=v); x.nf.forEach((v,k)=>nf[x.o+k]=v);
  const f=x.f.map(fd=>{ const fr=new Array(PN).fill(null); fd.r.forEach((v,k)=>fr[fd.o+k]=dec(v)); return {...fd, rr:fr}; });
  f.forEach(fd=>fd.rrB=fd.rr); PR[id]={o:x.o, last:x.o+x.r.length-1, r, rB:r, pl, nf, f}; });
const lastPL=(p,i)=>{ for(let j=i;j>=Math.max(0,i-2);j--) if(p.pl[j]!=null) return p.pl[j]; return null; };
// estatísticas numa janela [a,b] de uma série mensal; exige todos os meses
function pstats(r,a,b,bench){
  if(a<0) return null; let c=1, cb=1, peak=1, mdd=0, n=0, s=0, s2=0, hit=0, nb=0, sxy=0, sb=0, sb2=0;
  for(let i=a;i<=b;i++){ const v=r[i]; if(v==null) return null; c*=1+v; n++; s+=v; s2+=v*v; if(c>peak) peak=c; mdd=Math.min(mdd,c/peak-1);
    const w=bench?bench[i]:null; if(w!=null){ cb*=1+w; nb++; if(v>w) hit++; sxy+=v*w; sb+=w; sb2+=w*w; } }
  const ann=n>=12?Math.pow(c,12/n)-1:null, bann=nb===n&&n>=12?Math.pow(cb,12/n)-1:null;
  const mu=s/n, vol=n>2?Math.sqrt(Math.max(0,(s2-n*mu*mu)/(n-1))*12):null;
  const beta=nb===n&&n>=12?((sxy-s*sb/n)/(sb2-sb*sb/n)):null;
  return {n, ret:c-1, ann, bret:nb===n?cb-1:null, bann, ex:ann!=null&&bann!=null?ann-bann:(nb===n?(c-1)-(cb-1):null),
    vol, mdd, hit:nb===n?hit/n:null, beta};
}
const pc=(v,d=1)=>v==null||!isFinite(v)?'<span class="zero">–</span>':`<span class="${v>0?'pos':v<0?'neg':'zero'}">${v>0?'+':v<0?'−':''}${nf(Math.abs(v*100),d)}%</span>`;
const pcp=(v,d=1)=>v==null||!isFinite(v)?'<span class="zero">–</span>':`<span class="${v>0?'pos':v<0?'neg':'zero'}">${v>0?'+':v<0?'−':''}${nf(Math.abs(v*100),d)} p.p.</span>`;
const plmi=v=>v==null?'–':v>=1000?'R$ '+nf(v/1000,1)+' bi':'R$ '+nf(v,0)+' mi';
// gráfico de retorno acumulado (aceita valores negativos)
function cumChart(el, series, a, b, opt={}){
  const w=opt.w||900,h=opt.h||320,ml_=50,mr=opt.endLabels?110:14,mt=10,mb=26, iw=w-ml_-mr, ih=h-mt-mb;
  const paths=series.map(s=>{ const v=new Array(b-a+2).fill(null); let c=1, started=false; v[0]=0;
    for(let i=a;i<=b;i++){ const x=s.r[i]; if(x==null){ if(started) v[i-a+1]=null; continue; } c*=1+x; started=true; v[i-a+1]=c-1; }
    return {...s, v}; });
  let lo=0, hi=0; paths.forEach(p=>p.v.forEach(x=>{ if(x!=null){ lo=Math.min(lo,x); hi=Math.max(hi,x);} }));
  if(hi===lo){ el.innerHTML='<div class="empty">Sem dados no período.</div>'; return; }
  const step=niceStep(hi-lo,5,0.01), top=Math.ceil(hi/step)*step, bot=Math.floor(lo/step)*step;
  const X=k=>ml_+k/(b-a+1)*iw, Y=v=>mt+ih-(v-bot)/(top-bot)*ih;
  const mIdx=k=>a+k-1; // ponto k = fim do mês a+k-1 (k=0: início da janela)
  let g='';
  for(let v=bot;v<=top+1e-9;v+=step) g+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${ml_-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--muted)">${pct(v,step<0.05?1:0)}</text>`;
  g+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--axis)"/>`;
  const n=b-a+1, every=n<=14?1:n<=36?3:n<=72?6:n<=150?12:24;
  for(let k=1;k<=n;k++){ const i=mIdx(k), mo=+PM[i].slice(5); const okt=every>=12?(mo===12&&((+PM[i].slice(0,4)+1)%(every/12)===0)):(mo%every===0);
    if(okt) g+=`<text x="${X(k)}" y="${h-6}" text-anchor="middle" font-size="11" fill="var(--muted)">${every>=12?String(+PM[i].slice(0,4)+1):pml(i)}</text>`; }
  paths.slice().reverse().forEach(p=>{ let d='',pen=false; p.v.forEach((v,k)=>{ if(v==null){pen=false;return;} d+=(pen?'L':'M')+X(k).toFixed(1)+','+Y(v).toFixed(1); pen=true; });
    g+=`<path d="${d}" fill="none" stroke="${p.color}" stroke-width="${p.sw||2}" stroke-linejoin="round"${p.dashArr?` stroke-dasharray="${p.dashArr}"`:''}/>`; });
  if(opt.endLabels){ const ends=paths.map(p=>{ for(let k=p.v.length-1;k>=0;k--) if(p.v[k]!=null) return {p,k,y:Y(p.v[k]),v:p.v[k]}; return null; }).filter(Boolean).sort((x,y)=>x.y-y.y);
    for(let k=1;k<ends.length;k++) if(ends[k].y-ends[k-1].y<13) ends[k].y=ends[k-1].y+13;
    const over=ends.length?ends[ends.length-1].y-(mt+ih):0; if(over>0) ends.forEach(e=>e.y-=over);
    ends.forEach(e=>{ g+=`<circle cx="${X(e.k)}" cy="${Y(e.v)}" r="3" fill="${e.p.color}"/><text x="${w-mr+6}" y="${e.y+4}" font-size="11" font-weight="600" fill="var(--ink)">${esc(e.p.name.length>13?e.p.name.slice(0,12)+'…':e.p.name)} <tspan font-weight="400" fill="var(--ink-2)">${(e.v>=0?'+':'−')+nf(Math.abs(e.v*100),0)}%</tspan></text>`; }); }
  el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(opt.label||'Retorno acumulado')}">${g}<line class="xh" y1="${mt}" y2="${mt+ih}" stroke="var(--ink-2)" opacity="0"/><g class="dots"></g><rect x="${ml_}" y="${mt}" width="${iw}" height="${ih}" fill="transparent" class="hit"/></svg>`+
    (opt.noLegend?'':`<div class="legend">${paths.map(p=>`<span><i style="background:${p.color}"></i>${esc(p.name)}</span>`).join('')}</div>`)+
    `<details class="tv"><summary>Ver tabela</summary><div class="tblwrap" style="max-height:260px;overflow-y:auto"><table><thead><tr><th class="l">Fim de</th>${paths.map(p=>`<th>${esc(p.name)}</th>`).join('')}</tr></thead><tbody>${range(1,n).reverse().map(k=>`<tr><td class="l">${pmlong(mIdx(k))}</td>${paths.map(p=>`<td>${p.v[k]==null?'–':pct(p.v[k],1)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details><div class="tip" hidden></div>`;
  const svg=el.querySelector('svg'), tip=el.querySelector('.tip'), xh=svg.querySelector('.xh'), dots=svg.querySelector('.dots');
  svg.querySelector('.hit').addEventListener('mousemove',e=>{ const r=svg.getBoundingClientRect(), sx=(e.clientX-r.left)/r.width*w;
    const k=Math.max(0,Math.min(n,Math.round((sx-ml_)/iw*n)));
    xh.setAttribute('x1',X(k)); xh.setAttribute('x2',X(k)); xh.setAttribute('opacity','.35');
    const rows=paths.map(p=>({p,v:p.v[k]})).filter(o=>o.v!=null).sort((x,y)=>y.v-x.v);
    dots.innerHTML=rows.map(o=>`<circle cx="${X(k)}" cy="${Y(o.v)}" r="4" fill="${o.p.color}" stroke="var(--surface)" stroke-width="2"/>`).join('');
    tip.innerHTML=`<b>${k===0?'início: '+pmlong(a):'fim de '+pmlong(mIdx(k))}</b>`+rows.map(o=>`<div class="row"><span><i style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${o.p.color};margin-right:6px"></i>${esc(o.p.name)}</span><span>${pct(o.v,1)}</span></div>`).join('');
    tip.hidden=false; const px=X(k)/w*r.width; tip.style.left=Math.max(0,Math.min(px+14, r.width-tip.offsetWidth))+'px'; tip.style.top='8px'; });
  svg.querySelector('.hit').addEventListener('mouseleave',()=>{tip.hidden=true; xh.setAttribute('opacity','0'); dots.innerHTML='';});
}
const IBS={name:'Ibovespa', r:IBV, color:'var(--ink-2)', dashArr:'5 4', sw:1.6};
const CDS={name:'CDI', r:CDI, color:'var(--muted)', dashArr:'2 3', sw:1.4};
// último mês com Ibovespa e ao menos metade das gestoras com retorno
const PLAST=(()=>{ const ids=Object.keys(PR); for(let i=PN-1;i>=0;i--){ if(IBV[i]==null) continue; const k=ids.filter(id=>PR[id].r[i]!=null).length; if(k>=ids.length*0.5) return i; } return PN-1; })();
const PWIN=[[12,'12m'],[36,'3a'],[60,'5a'],[120,'10a'],[0,'Desde o início']];
const PH=[[6,'6m'],[12,'1 ano'],[24,'2 anos'],[36,'3 anos'],[60,'5 anos'],[120,'10 anos']];
const hv=(s,n)=>s==null?null:(n>12?s.ann:s.ret);
const hcell=(s,n,bold)=>`<td${bold?' style="font-weight:600"':''} title="${s&&s.ex!=null?'vs índice: '+(s.ex>=0?'+':'−')+nf(Math.abs(s.ex*100),1)+' p.p.'+(n>12?' a.a.':''):''}">${pc(hv(s,n))}</td>`;

// ----- aba Performance
// gestoras extras (só performance, fora das carteiras: SPX, Dynamo...)
const PNM={'08752088':'Brasil Capital','45999585':'TB','14229647':'Núcleo','18529041':'SFA','53980469':'JGP Equities','11888689':'STK','13143849':'Bahia AM','09175140':'Galt','13911006':'Parcitas','49640512':'Capsigma','02228585':'Tática','15555653':'Onyx','06182127':'Constellation'};
const PG=[...G.map(g=>PNM[g.id]?{...g,n:PNM[g.id]}:g), ...(PF.x||[]).filter(x=>!GI[x.id])]; const PGI={}; PG.forEach(g=>PGI[g.id]=g);
// seleção de gestoras do ranking (escolhida a dedo; as demais continuam com o bloco de desempenho na própria página)
const PSEL=new Set(["10957035", "11752203", "07078144", "35098801", "32541657", "00533944", "11570951", "09326542", "09267871", "45999585", "14205023", "10917835", "17776271", "14229647", "42462859", "11959069", "06182127", "27957477", "17544838", "28375224", "27133825", "13143849", "43020918", "31227292", "08947719", "10626543", "11530232", "06015560", "09175140", "28925400", "51744631", "04714159", "18529041", "23345332", "08752088", "13911006", "04581293", "14359791", "11401701", "53980469", "18730786", "49640512", "05336089", "08251477", "31340246", "22688191", "29389196", "23862803", "11888689", "15555653", "02228585", "12330774", "72116353", "23890968", "37947185"]);
// fundos LatAm entram no mesmo ranking (benchmark próprio quando o factsheet traz, senão Ibovespa)
(PF.la||[]).forEach((f,k)=>{ const id='la'+k, rr=new Array(PN).fill(null); f.r.forEach((v,j)=>rr[f.o+j]=dec(v)); const last=f.o+f.r.length-1;
  let bm=null; if(f.bm){ bm=new Array(PN).fill(null); f.bm.forEach((v,j)=>bm[f.o+j]=dec(v)); }
  const pl=new Array(PN).fill(null); if(f.pl!=null) pl[last]=f.pl;
  PR[id]={o:f.o, last, r:rr, rB:rr, pl, nf:new Array(PN).fill(1), f:[], bm, bmB:bm, bmn:f.bmn, usd:!!f.cur};
  const nm=/FUNDAMENTA/.test(f.n)?'Fundamenta LatAm (Gama)':/EXPLORITAS/.test(f.n)?'Exploritas Marathon':`${f.g.replace(/ Equity$/,'')} LatAm`;
  const g={id, n:nm, rs:f.n, cnpj:f.c, reg:f.cur?'LatAm · factsheet US$ líquido':'LatAm', gid:f.gid}; PG.push(g); PGI[id]=g; PSEL.add(id); });
function applyCur(){ const U=S.cur==='USD';
  IBV=U?toUSD(IBVB):IBVB; CDI=U?toUSD(CDIB):CDIB; IBS.r=IBV; CDS.r=CDI;
  Object.values(PR).forEach(p=>{ if(p.usd){ // série já em dólar: em reais converte ao contrário
      p.r=U?p.rB:p.rB.map((v,i)=>v==null||FXR[i]==null?null:(1+v)/(1+FXR[i])-1); p.bm=p.bmB&&(U?p.bmB:p.bmB.map((v,i)=>v==null||FXR[i]==null?null:(1+v)/(1+FXR[i])-1)); }
    else { p.r=U?toUSD(p.rB):p.rB; p.f.forEach(fd=>fd.rr=U?toUSD(fd.rrB):fd.rrB); } }); }
applyCur();
S.pend=PLAST; S.pwin=36; S.psel=null;
['p-min'].forEach(id=>$(id).addEventListener('change',renderP)); $('p-q').addEventListener('input',renderP);
$('p-end').addEventListener('change',()=>{S.pend=+$('p-end').value; renderP();});
const curSeg=(el,cb)=>{ el.innerHTML=[['USD','US$'],['BRL','R$']].map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${S.cur===v}">${l}</button>`).join('');
  el.onclick=e=>{const x=e.target.closest('button'); if(!x||x.dataset.v===S.cur) return; S.cur=x.dataset.v; applyCur(); cb();}; };
// quartis: a tabela é dividida em 4 grupos pela coluna de ordenação; cada célula de retorno ganha a cor do seu quartil naquela coluna
const QLBL=['1º quartil','2º quartil','3º quartil','4º quartil'];
function qOf(vals){ // vals: Map id->v (maior = melhor); devolve Map id->1..4
  const v=[...vals].filter(([,x])=>x!=null&&isFinite(x)).sort((a,b)=>b[1]-a[1]), n=v.length, q=new Map();
  v.forEach(([id],k)=>q.set(id, Math.min(4, Math.floor(k*4/n)+1))); return q; }
function quartis(cols, rows){
  const tb=$('p-tbl').tBodies[0]; if(!tb) return; const byId=new Map(rows.map(o=>[o.g.id,o]));
  const trs=[...tb.rows]; const ncol=cols.length;
  // cor por coluna de retorno (horizontes, desde o Apo e vs Ibov)
  cols.forEach((c,ci)=>{ if(!/^h\d+$|^apo$|^ex$/.test(c.k)) return; const q=qOf(new Map(rows.map(o=>[o.g.id,c.v(o)])));
    trs.forEach(tr=>{ const k=q.get(tr.dataset.g); const td=tr.cells[ci]; if(td&&k) td.classList.add('qc'+k); }); });
  // grupos pela coluna ordenada (só se for numérica de "maior = melhor" ou "menor = melhor")
  const st=S.sort['p-tbl'], c=cols.find(x=>x.k===st.k); if(!c||!c.v||['g','sel'].includes(c.k)) return;
  const vals=new Map(rows.map(o=>[o.g.id, c.v(o)==null?null:c.v(o)*(st.dir<0?1:-1)])); const q=qOf(vals);
  const fmtv=v=>c.k==='beta'?nf(v,2):c.k==='pl'?plmi(v):(c.k==='ex'?pcp(v):pc(v));
  let last=null;
  trs.forEach(tr=>{ const k=q.get(tr.dataset.g)||0; if(k===last) return; last=k;
    const ids=[...q].filter(([,x])=>x===k).map(([id])=>id), vs=ids.map(id=>c.v(byId.get(id))).filter(x=>x!=null).sort((a,b)=>a-b);
    const med=vs.length?vs[Math.floor(vs.length/2)]:null;
    const lbl=k?`<b>${QLBL[k-1]}</b> · ${ids.length} ${ids.length===1?'linha':'linhas'} · ${c.l.replace(/<br>.*$/,'').replace(/<[^>]+>/g,'')}: de ${fmtv(vs[0])} a ${fmtv(vs[vs.length-1])} · mediana ${fmtv(med)}`:`<b>Sem dado nesta coluna</b>`;
    tr.insertAdjacentHTML('beforebegin', `<tr class="qhead q${k}"><td colspan="${ncol}" class="l">${lbl}</td></tr>`); });
}
function renderP(){
  const b=S.pend, W_=S.pwin, minpl=+$('p-min').value, fq=$('p-q').value.trim().toLowerCase();
  $('p-end').innerHTML=''; for(let i=PN-1;i>=12;i--) if(IBV[i]!=null) $('p-end').add(new Option(pmlong(i),i)); $('p-end').value=b;
  $('p-win').innerHTML=PWIN.map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${W_===v}">${l}</button>`).join('');
  curSeg($('p-cur'),renderP);
  $('p-win').onclick=e=>{const x=e.target.closest('button'); if(!x) return; S.pwin=+x.dataset.v; renderP();};
  // desde o início do Apo (jul/22): mesma janela para todos
  const AO=(Object.values(PR).find(p=>p.usd)||{}).o, AN=AO!=null&&b>=AO?b-AO+1:null;
  const hz=(r,bn)=>({...Object.fromEntries(PH.map(([n])=>[n, b-n+1>=0?pstats(r,b-n+1,b,bn):null])), apo:AN?pstats(r,AO,b,bn):null});
  const acell=s=>`<td style="border-left:1px solid var(--border)" title="${s&&s.ex!=null?'vs índice: '+(s.ex>=0?'+':'−')+nf(Math.abs(s.ex*100),1)+' p.p. a.a.':''}">${s?`<b>${pc(s.ann??s.ret)}</b><small class="muted" style="display:block;font-size:11px">${pc(s.ret,0)} total</small>`:pc(null)}</td>`;
  const rows=PG.filter(g=>PR[g.id]&&PSEL.has(g.id)).map(g=>{ const p=PR[g.id]; const a=W_?b-W_+1:Math.max(p.o,0); const BN=p.bm||IBV; const s=b<=p.last&&b>=p.o?pstats(p.r,a,b,BN):null;
      // "desde o início": primeira sequência contínua até b
      let st=s; if(!W_ && b>=p.o){ let a2=b; while(a2>p.o && p.r[a2-1]!=null) a2--; st=p.r[b]!=null?pstats(p.r,a2,b,BN):null; if(st) st.a=a2; }
      return {g, p, s:st, h:hz(p.r,BN), pl:lastPL(p,Math.min(b,p.last)), live:b<=p.last+2}; })
    .filter(o=>o.p.r[b]!=null && (o.pl||0)>=minpl && (!fq||o.g.n.toLowerCase().includes(fq)||o.g.rs.toLowerCase().includes(fq)));
  const rowsW=rows.filter(o=>o.s);
  const a=W_?b-W_+1:null; const ib=W_?pstats(IBV,a,b):null, cd=W_?pstats(CDI,a,b):null;
  $('p-h').textContent=W_?`Retorno de ${pmlong(a)} a ${pmlong(b)}`:`Retorno desde o início, até ${pmlong(b)}`;
  $('p-sub').textContent=`${rows.length} das ${PSEL.size} gestoras selecionadas com dado em ${pmlong(b)}; ${rowsW.length} com série completa na janela das estatísticas${minpl?` e PL em fundos de ações ≥ ${plmi(minpl)}`:''}. Retornos em ${S.cur==='USD'?'dólar (convertidos pela PTAX de fim de mês; Ibovespa e CDI também em US$)':'reais (Apo convertido de US$ pela PTAX)'}. Retorno ponderado pelo PL dos fundos long only da gestora (sem long biased), cota líquida de taxas (FICs da gestora ou fundo direto; Apo classe B líquida).`;
  const beat=rowsW.filter(o=>o.s.ex!=null&&o.s.ex>0).length, med=q=>{const v=rowsW.map(q).filter(x=>x!=null).sort((x,y)=>x-y); return v.length?v[Math.floor(v.length/2)]:null;};
  $('p-kpis').innerHTML=kpis([
    [W_>=12?'Ibovespa (a.a.)':'Ibovespa', W_?pc(W_>=12?ib.ann:ib.ret):'–', W_?`${pc(ib.ret,0)} no período · CDI ${pc(W_>=12?cd.ann:cd.ret)}${W_>=12?' a.a.':''}`:'janela varia por gestora'],
    ['Bateram o Ibovespa', `${beat} de ${rowsW.length}`, rowsW.length?`${pct(beat/rowsW.length,0)} das gestoras`:''],
    [W_>=12||!W_?'Mediana (a.a.)':'Mediana', pc(med(o=>W_&&W_<12?o.s.ret:o.s.ann)), `excesso mediano ${pcp(med(o=>o.s.ex))}`],
    ['Melhor', rowsW.length?esc(rowsW.slice().sort((x,y)=>(y.s.ann??y.s.ret)-(x.s.ann??x.s.ret))[0].g.n):'–', rowsW.length?pc(rowsW.slice().sort((x,y)=>(y.s.ann??y.s.ret)-(x.s.ann??x.s.ret))[0].s[W_&&W_<12?'ret':'ann'])+(W_&&W_<12?'':' a.a.'):''],
  ]);
  if(!S.psel) S.psel=rows.slice().sort((x,y)=>(y.pl||0)-(x.pl||0)).slice(0,5).map(o=>o.g.id);
  const ann=!W_||W_>=12; const WL=W_?PWIN.find(x=>x[0]===W_)[1]:'desde início';
  const cols=[
    {k:'sel',l:'',f:o=>{const k=S.psel.indexOf(o.g.id); const st=k>=0?serStyle(k):null; return `<td class="l" style="width:1%"><input type="checkbox" data-g="${o.g.id}" ${k>=0?'checked':''} aria-label="comparar ${esc(o.g.n)}" style="min-height:auto">${st?`<span class="sw" style="background:${st.color};margin-left:6px"></span>`:''}</td>`;}},
    {k:'g',l:'Gestora',cls:'l',v:o=>o.g.n,asc:true,f:o=>`<td class="l">${GI[o.g.id]?`<a href="#g-${o.g.id}" data-open="${o.g.id}">${esc(o.g.n)}</a>`:o.g.gid&&GI[o.g.gid]?`<a href="#g-${o.g.gid}" data-open="${o.g.gid}" title="${esc(o.g.rs)}">${esc(o.g.n)}</a>`:`<span title="${esc(o.g.rs)}">${esc(o.g.n)}</span>`}${o.g.reg?` <span class="chip new" title="${o.p.bmn?'comparado ao '+esc(o.p.bmn)+' do factsheet':'comparado ao Ibovespa'}">${o.g.reg}</span>`:GI[o.g.id]?'':' <span class="chip" title="fora do painel de carteiras">só performance</span>'}${o.live?'':' <span class="chip">sem dados recentes</span>'}</td>`},
    {k:'pl',l:'PL long only',v:o=>o.pl,f:o=>`<td class="muted">${plmi(o.pl)}</td>`},
    ...PH.map(([n,l])=>({k:'h'+n,l:n>12?`${l}<br><small>a.a.</small>`:l,v:o=>hv(o.h[n],n),f:o=>hcell(o.h[n],n,n===36)})),
    ...(AN?[{k:'apo',l:`Desde ${pml(AO)}<br><small>início Apo · a.a.</small>`,v:o=>o.h.apo?(o.h.apo.ann??o.h.apo.ret):null,f:o=>acell(o.h.apo)}]:[]),
    {k:'ex',l:`vs Ibov<br><small>${WL} ${ann?'a.a.':''}</small>`,v:o=>o.s?o.s.ex:null,f:o=>`<td>${pcp(o.s?o.s.ex:null)}</td>`},
    {k:'vol',l:`Vol a.a.<br><small>${WL}</small>`,v:o=>o.s?o.s.vol:null,asc:true,f:o=>`<td class="muted">${!o.s||o.s.vol==null?'–':pct(o.s.vol,1)}</td>`},
    {k:'mdd',l:`Pior queda<br><small>${WL}</small>`,v:o=>o.s?o.s.mdd:null,f:o=>`<td>${pc(o.s?o.s.mdd:null,0)}</td>`},
    {k:'beta',l:`Beta<br><small>${WL}</small>`,v:o=>o.s?o.s.beta:null,asc:true,f:o=>`<td class="muted">${!o.s||o.s.beta==null?'–':nf(o.s.beta,2)}</td>`},
  ];
  if(!S.sort['p-tbl']) S.sort['p-tbl']={k:'h36',dir:-1};
  const st=S.sort['p-tbl']; if(!cols.find(c=>c.k===st.k)) S.sort['p-tbl']={k:'h36',dir:-1};
  if(rows.length) sTable('p-tbl', cols, rows, 'h36', o=>`data-g="${o.g.id}"`, 1e9, renderP);
  else $('p-tbl').innerHTML='<tbody><tr><td class="l empty">Nenhuma gestora com série completa nessa janela.</td></tr></tbody>';
  $('p-tbl').querySelectorAll('tr.link').forEach(tr=>tr.classList.remove('link'));
  if(rows.length) quartis(cols, rows);
  if(rows.length){ const ref=(nm,r)=>{ const h=hz(r,null), s2=W_?pstats(r,b-W_+1,b,null):null;
      return `<tr style="background:var(--surface-2)"><td></td><td class="l" style="font-weight:600">${nm}</td><td></td>${PH.map(([n])=>hcell(h[n],n,n===36)).join('')}${AN?acell(h.apo):''}<td></td><td class="muted">${s2&&s2.vol!=null?pct(s2.vol,1):'–'}</td><td>${pc(s2?s2.mdd:null,0)}</td><td></td></tr>`; };
    $('p-tbl').tHead.insertAdjacentHTML('beforeend', ref('Ibovespa',IBV)+ref('CDI',CDI)); }
  $('p-tbl').querySelectorAll('a[data-open]').forEach(x=>x.onclick=e=>{e.preventDefault(); openG(x.dataset.open);});
  $('p-tbl').querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>{ const id=cb.dataset.g;
    if(cb.checked){ if(S.psel.length>=8){cb.checked=false; return;} S.psel.push(id);} else S.psel=S.psel.filter(x=>x!==id); renderP(); });
  // gráfico comparativo
  const a0=W_?a:Math.max(0,Math.min(...S.psel.filter(id=>PR[id]).map(id=>PR[id].o)));
  $('p-ct').textContent=`Retorno acumulado de ${pmlong(a0)} a ${pmlong(b)}`;
  $('p-cs').textContent=`em ${S.cur==='USD'?'US$':'R$'} · até 8 linhas · Ibovespa e CDI tracejados`;
  cumChart($('p-chart'), [...S.psel.filter(id=>PR[id]).map((id,k)=>({name:PGI[id].n, r:PR[id].r, ...serStyle(k)})), IBS, CDS], a0, b, {endLabels:true, noLegend:true, label:'Retorno acumulado das gestoras marcadas'});
  chipSelector($('p-chips'), rows.slice().sort((x,y)=>x.g.n.localeCompare(y.g.n)).map(o=>({key:o.g.id,label:o.g.n})), S.psel, 8, renderP);
  $('p-note').innerHTML=PNOTE;
}
const PNOTE=`<b>Moeda.</b> Em US$, o retorno mensal de cada série em reais é convertido pela PTAX de venda de fim de mês (BCB, série 3696): (1 + retorno em R$) × dólar do mês anterior ÷ dólar do mês − 1. Ibovespa e CDI recebem a mesma conversão. O Apo já vem em US$ do factsheet; em R$ ele é convertido no sentido contrário. <br><b>LatAm.</b> Fundos LatAm entram como linhas próprias (selo LatAm): Onyx, Fundamenta (feeder em reais da Gama), Exploritas e Fama, pelo Informe Diário, comparados ao Ibovespa; Apo Capital Latam Fund (offshore, US$) transcrito do factsheet de out/2026 pela classe B líquida e comparado ao MSCI LatAm do próprio factsheet. INCA e Fourth Sail (Tordesilhas) não têm fundos na CVM. <br><b>Como é calculado.</b> Fonte: Informe Diário da CVM (cota e PL de cada fundo, 2005 em diante). Para cada gestora, entram só os fundos <b>long only</b> da classe Ações que ela geria <i>naquela data</i> (histórico de gestores da CVM, somando os CNPJs da mesma casa), excluídos fundos de cotas (FIC), exclusivos, de previdência e indexados, e os fundos de investimento no exterior ou LatAm (estes ficam na tabela LatAm). Long biased fica de fora: fundos com long biased, long short ou L/S no nome (atual ou antigo), classificados pela Anbima como L/S ou multimercado, ou registrados na CVM como multimercado (salvo se o nome atual diz ações). Além disso, pela carteira da CDA: o fundo sai nos meses em que a mediana de 12 meses da posição vendida (futuro de Ibovespa vendido + ações tomadas em aluguel e vendidas) passa de 10% do PL. Os long only ficam tipicamente entre 0% e 5%. `+
  `O retorno do mês é a média dos retornos de cota desses fundos ponderada pelo PL do fim do mês anterior. <b>Base líquida para todos.</b> O retorno é o da cota que o cotista recebe, já descontadas as taxas de administração e de performance. Nas estruturas master-feeder as taxas são cobradas no FIC, então em vez do master entram os FICs da própria gestora cujo fundo investido principal (≥ 50% do PL do FIC, pela CDA) é um master elegível naquele mês; o master representado sai. Fundos sem FIC próprio (o cotista aplica direto) entram pela própria cota, que já é líquida. Cerca de 57% do peso vem de FICs. O Apo usa a classe B líquida do factsheet. Conferência com tabelas de peers líquidas: diferença mediana de 0,2 p.p. por ano. `+
  `Ibovespa = mediana mensal dos fundos indexados ao índice com PL ≥ R$ 50 mi (correlação 0,9997 com o índice; fica abaixo dele pela taxa de administração, ~0,5% a.a.). CDI: Banco Central (SGS 4391). Pior queda = maior queda do pico ao vale com cotas mensais. Beta e meses acima do Ibovespa usam retornos mensais. Janelas exigem todos os meses com dado; gestoras que encerraram ou trocaram de CNPJ fora da lista aparecem só até o último mês disponível.`;

// ----- bloco de performance na página da gestora
S.gpw=60;
function renderGP(g){
  const box=$('g-perf'), p=PR[g.id];
  if(!p){ box.innerHTML=`<div class="hd"><h2>Desempenho</h2></div><div class="empty">Sem fundos long only elegíveis no Informe Diário da CVM para esta gestora (só long biased, FICs, exclusivos ou fundos de outra classe).</div>`; return; }
  const b=Math.min(p.last, PLAST); let a1=b; while(a1>p.o && p.r[a1-1]!=null) a1--;
  const st=k=>{ const a=b-k+1; return a>=a1?pstats(p.r,a,b,IBV):null; }, s0=pstats(p.r,a1,b,IBV);
  const kp=(lbl,s,k)=>[lbl, s?pc(k>=12?s.ann:s.ret):'–', s?`${k>12?'a.a. · ':''}Ibov ${pc(k>=12?s.bann:s.bret)} · ${pcp(s.ex)}`:'sem série completa'];
  const w=S.gpw, a=w?Math.max(a1,b-w+1):a1;
  const yrs=[]; for(let y=+PM[b].slice(0,4); y>=+PM[a1].slice(0,4); y--){ const i0=Math.max(a1,PI[y+'-01']??0), i1=Math.min(b,PI[y+'-12']??b);
    if(i1<i0) continue; const s=pstats(p.r,i0,i1,IBV), c=pstats(CDI,i0,i1); if(s) yrs.push({y,s,c,part:i1-i0+1<12,i0,i1}); }
  const fn=p.f.map(f=>{ let fa=Math.min(b,f.o+f.r.length-1); const fb=fa; let fa0=fb; while(fa0>f.o && f.rr[fa0-1]!=null) fa0--;
    const z=k=>fb-k+1>=fa0?pstats(f.rr,fb-k+1,fb,IBV):null; return {f, end:fb, s12:z(12), s36:z(36), s60:z(60), s0:pstats(f.rr,fa0,fb,IBV), a:fa0}; });
  box.innerHTML=`<div class="hd"><h2>Desempenho dos fundos long only</h2><span class="hdctl"><span class="seg" id="g-cur"></span><span class="seg" id="g-pw">${PWIN.map(([v,l])=>`<button type="button" data-v="${v}" aria-pressed="${w===v}">${l}</button>`).join('')}</span></span></div>`+
    `<p class="note" style="margin:0 0 10px">Em ${S.cur==='USD'?'US$ (PTAX de fim de mês)':'R$'} · até ${pmlong(b)} · ${p.nf[b]||0} fundo(s) no mês · PL ${plmi(lastPL(p,b))} · série desde ${pmlong(a1)}. <a href="#performance" id="g-p2">Ver ranking</a></p>`+
    `<div class="kpis">${kpis([kp('12 meses',st(12),12),kp('3 anos',st(36),36),kp('5 anos',st(60),60),kp(`Desde ${pml(a1)}`,s0,b-a1+1)])}</div>`+
    `<div class="chart" id="g-pchart"></div>`+
    `<div class="grid2" style="margin-top:14px;margin-bottom:0"><div><div class="lbl" style="margin-bottom:6px">Ano a ano</div><div class="tblwrap" style="max-height:340px;overflow-y:auto"><table><thead><tr><th class="l">Ano</th><th>Gestora</th><th>Ibovespa</th><th>vs Ibov</th><th>CDI</th></tr></thead><tbody>${
      yrs.map(o=>`<tr><td class="l">${o.y}${o.part?` <small class="muted">${pml(o.i0)}–${pml(o.i1)}</small>`:''}</td><td style="font-weight:600">${pc(o.s.ret)}</td><td class="muted">${pc(o.s.bret)}</td><td>${pcp(o.s.bret==null?null:o.s.ret-o.s.bret)}</td><td class="muted">${pc(o.c?o.c.ret:null)}</td></tr>`).join('')}</tbody></table></div></div>`+
    `<div><div class="lbl" style="margin-bottom:6px">Fundos usados (maiores por PL médio)</div><div class="tblwrap" style="max-height:340px;overflow-y:auto"><table><thead><tr><th class="l">Fundo</th><th>PL</th><th>12m</th><th>3a a.a.</th><th>Desde a.a.</th></tr></thead><tbody>${
      fn.length?fn.map(o=>`<tr><td class="l em">${esc(o.f.n||o.f.c)}<small>${esc(o.f.c)}${o.f.lb?' · long biased':''}${o.end<b?` · até ${pml(o.end)}`:''}</small></td><td class="muted">${o.end>=b-2?plmi(o.f.pl):'–'}</td><td>${pc(o.s12?o.s12.ret:null)}</td><td>${pc(o.s36?o.s36.ann:null)}</td><td>${pc(o.s0?(o.s0.ann??o.s0.ret):null)}<small>${pml(o.a)}</small></td></tr>`).join(''):'<tr><td class="l empty">–</td></tr>'}</tbody></table></div></div></div>`;
  cumChart($('g-pchart'), [{name:g.n, r:p.r, color:SER[0], sw:2.4}, IBS, CDS], a, b, {h:280, label:`Retorno acumulado de ${g.n}`});
  curSeg($('g-cur'),()=>renderGP(g));
  $('g-pw').onclick=e=>{const x=e.target.closest('button'); if(!x) return; S.gpw=+x.dataset.v; renderGP(g);};
  $('g-p2').onclick=e=>{e.preventDefault(); setView('p'); renderP();};
}
