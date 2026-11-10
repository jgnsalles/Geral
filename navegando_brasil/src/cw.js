// Carteiras das Gestoras (CDA/CVM agregada por gestora) — portado para o Navegando Brasil.
// Exposto como window.CW.init(D, hooks). Renderiza as partes "Hoje", "Gestora · posições da casa" e "Empresa · detentores".
window.CW = (() => {
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let D,M,NM,G,E,GI={},H={};
const MES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
const ml=i=>{const [y,m]=M[i].split('-'); return `${MES[+m-1]}/${y.slice(2)}`;};
const mlong=i=>{const [y,m]=M[i].split('-'); return `${MES[+m-1]}/${y}`;};
const nf=(v,d=1)=>v.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=(v,d=1)=>v==null||!isFinite(v)?'–':nf(v*100,d)+'%';
const pp=v=>v==null?'<span class="zero">–</span>':Math.abs(v)<0.00095?'<span class="zero">0,0</span>':`<span class="${v>0?'rx-pos':'rx-neg'}">${v>0?'+':'−'}${nf(Math.abs(v*100),1)}</span>`;
const brl=v=>{ if(v==null) return '–'; const a=Math.abs(v), s=v<0?'−':'';
  if(a>=1e9) return s+'R$ '+nf(a/1e9,1)+' bi';
  if(a>=1e6) return s+'R$ '+nf(a/1e6,0)+' mi';
  return s+'R$ '+nf(a/1e3,0)+' mil'; };
const SER=['#2f6fd0','#d9822b','#2a9d8f','#c4467a','#7a5cc4','#8a9a2b','#b5523b','#4a90a4'];
const ename=r=>(E[r]&&E[r][0])||r;
const etks=r=>(E[r]&&E[r][1])||r;
const eold=r=>(E[r]&&E[r][2])||'';
const logo=(r,big)=>`<span class="cw-lg${big?' big':''}" aria-hidden="true">${esc(r.slice(0,4))}</span>`;

// ---- acesso aos dados
const lastIdx=g=>g.o+g.t.length-1;
const inR=(g,i)=>i>=g.o && i<=lastIdx(g);
const tot=(g,i)=>!inR(g,i)||g.t[i-g.o]==null?null:g.t[i-g.o]*1e3;
const cnf=(g,i)=>!inR(g,i)?0:g.c[i-g.o]*1e3;
const cov=(g,i)=>{ if(!inR(g,i)) return null; const t=tot(g,i)||0, c=cnf(g,i); return t+c>0?t/(t+c):null; };
const lim=()=>Math.max(0.001,(parseFloat($('lim').value)||2)/100);
const covMin=()=>parseFloat($('covmin').value);
const ok=(g,i)=>{ const c=cov(g,i); return c!=null && tot(g,i)>0 && c>=covMin(); };
const W=(g,r,i)=>{ const e=g.p[r]; if(!e) return 0; const k=i-g.o-e[0]; return (k<0||k>=e[1].length)?0:e[1][k]/1e4; };
const Q=(g,r,i)=>{ if(!ok(g,i)) return null; const e=g.p[r]; if(!e) return 0; const k=i-g.o-e[0]; if(k<0||k>=e[2].length) return 0; const q=e[2][k]; return q<0?null:q; };
const val=(g,r,i)=>W(g,r,i)*(tot(g,i)||0);
function delta(g,r,i,k){
  const j=i-k; const a=Q(g,r,j), b=Q(g,r,i); if(a==null||b==null) return null;
  if(Math.max(W(g,r,i),W(g,r,j))<0.005) return null;
  if(a===0&&b===0) return null;
  if(a===0) return {d:'nova', flow:val(g,r,i)};
  if(b===0) return {d:'zerou', flow:-val(g,r,j)};
  for(let m=j+1;m<i;m++){ if(Q(g,r,m)===0) return {d:'nova', flow:val(g,r,i)}; }
  return {d:b/a-1, flow:(b-a)*val(g,r,i)/b};
}
function lastMove(g,r,i,k){ for(let m=i;m>i-k;m--){ const x=delta(g,r,m,1); if(isBuy(x)||isSell(x)) return m; } return null; }
const movSort=(id,mv)=>{ const o=$(id)?$(id).value:'v';
  const f={v:(a,b)=>Math.abs(b.x.flow)-Math.abs(a.x.flow), r:(a,b)=>((b.m??-1)-(a.m??-1))||(Math.abs(b.x.flow)-Math.abs(a.x.flow)), b:(a,b)=>b.x.flow-a.x.flow}[o]||((a,b)=>0);
  return mv.sort(f); };
const whenCell=m=>m==null?'<td style="text-align:left" class="co">aos poucos</td>':`<td style="text-align:left">${ml(m)}</td>`;
const isBuy=x=>x&&(x.d==='nova'||(typeof x.d==='number'&&x.d>=0.10));
const isSell=x=>x&&(x.d==='zerou'||(typeof x.d==='number'&&x.d<=-0.10));
function dq(x){ if(!x) return '<span class="zero">–</span>'; if(x.d==='nova') return '<span class="cw-chip new">nova</span>'; if(x.d==='zerou') return '<span class="cw-chip down">zerou</span>';
  const v=x.d; return Math.abs(v)<0.005?'<span class="zero">0%</span>':`<span class="${v>0?'rx-pos':'rx-neg'}">${v>0?'+':'−'}${nf(Math.abs(v*100),Math.abs(v)<0.1?1:0)}%</span>`; }
function since(g,r,i){ let s=null; for(let j=i;j>=g.o;j--){ const q=Q(g,r,j); if(q===0) break; if(q==null){ if(W(g,r,j)>0) s=j; continue; } s=j; } return s; }
function heldFor(g,r,i){ const s=since(g,r,i); if(s==null) return ['–','–'];
  const n=i-s+1, cut=s===g.o; const y=n/12;
  const dur=n<12?`${n} ${n===1?'mês':'meses'}`:`${cut?'≥ ':''}${nf(y,y<10?1:0)} anos`;
  return [(cut?'≤ ':'')+ml(s), dur]; }
function bestMonth(g){
  for(let i=lastIdx(g);i>=g.o;i--){ const c=cov(g,i); if(c!=null && c>=0.9 && tot(g,i)>0) return i; }
  for(let i=lastIdx(g);i>=g.o;i--) if(tot(g,i)>0) return i;
  return lastIdx(g);
}
const latestTot=g=>{for(let i=lastIdx(g);i>=g.o;i--){const c=cov(g,i); if(c!=null&&c>=0.9&&tot(g,i)>0) return tot(g,i);} return 0;};
let GOOD=0;
function fillMonths(sel, from, to, v){ sel.innerHTML=''; for(let i=to;i>=from;i--) sel.add(new Option(mlong(i),i)); sel.value=v; }
const maxW=(g,r,a,b)=>{let m=0; for(let j=a;j<=b;j++){const v=W(g,r,j); if(v>m) m=v;} return m;};
const tkCell=r=>`<td><span class="cw-tkc">${logo(r)}<span class="tk">${esc(r)}</span></span></td>`;
const range=(a,b)=>{const r=[];for(let i=a;i<=b;i++) r.push(i);return r;};
function niceStep(vmax,n,minStep){ const raw=vmax/n; const p=Math.pow(10,Math.floor(Math.log10(raw))); const s=[1,2,2.5,5,10].map(k=>k*p).find(k=>k>=raw); return Math.max(s,minStep);}
function xTicks(i0,i1){ const n=i1-i0; const every=n<=14?1:n<=36?3:n<=72?6:n<=150?12:24; const out=[];
  for(let i=i0;i<=i1;i++){ const m=+M[i].slice(5); if(every>=12? (m===1 && ((+M[i].slice(0,4))%(every/12)===0)) : ((m-1)%every===0)) out.push(i);} return out; }
const fmt2=(v,opt)=>opt.fmt==='int'?Math.round(v).toLocaleString('pt-BR'):pct(v,1);

// ---------- gráficos ----------
function lineChart(el, series, i0, i1, opt={}){
  const w=opt.w||640,h=opt.h||260,ml_=44,mr=opt.endLabels?78:12,mt=10,mb=26, iw=w-ml_-mr, ih=h-mt-mb;
  let vmax=0; series.forEach(s=>{for(let i=i0;i<=i1;i++){const v=s.vals(i); if(v!=null&&v>vmax) vmax=v;}});
  if(!(vmax>0)){ el.innerHTML='<p class="rx-note">Sem dados no período.</p>'; return; }
  const step=opt.fmt==='int'?niceStep(vmax,4,1):niceStep(vmax,4,0.01); const top=Math.ceil(vmax/step)*step;
  const X=i=>ml_+(i1===i0?iw/2:(i-i0)/(i1-i0)*iw), Y=v=>mt+ih-(v/top)*ih;
  const fmt=opt.fmt==='int'?(v=>Math.round(v).toLocaleString('pt-BR')):(v=>pct(v,step<0.01?1:0));
  let g='';
  for(let v=0;v<=top+1e-9;v+=step) g+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--cds-chart-grid)"/><text x="${ml_-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--color-fg-muted)">${fmt(v)}</text>`;
  xTicks(i0,i1).forEach(i=>g+=`<text x="${X(i)}" y="${h-6}" text-anchor="middle" font-size="11" fill="var(--color-fg-muted)">${ml(i)}</text>`);
  g+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--cds-chart-axis)"/>`;
  if(opt.mark!=null && opt.mark>=i0 && opt.mark<=i1) g+=`<line x1="${X(opt.mark)}" x2="${X(opt.mark)}" y1="${mt}" y2="${mt+ih}" stroke="var(--cds-chart-axis)" stroke-dasharray="3 3"/>`;
  series.slice().reverse().forEach(s=>{
    let d='',pen=false;
    for(let i=i0;i<=i1;i++){ const v=s.vals(i); if(v==null){pen=false; continue;} d+=`${pen?'L':'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen=true; }
    g+=`<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"${s.dashArr?` stroke-dasharray="${s.dashArr}"`:''}/>`;
  });
  if(opt.endLabels){
    const ends=series.map(s=>{ for(let i=i1;i>=i0;i--){ const v=s.vals(i); if(v!=null) return {s,i,y:Y(v)}; } return null; }).filter(Boolean).sort((a,b)=>a.y-b.y);
    for(let k=1;k<ends.length;k++) if(ends[k].y-ends[k-1].y<12) ends[k].y=ends[k-1].y+12;
    const over=ends.length?ends[ends.length-1].y-(mt+ih):0; if(over>0) ends.forEach(e=>e.y-=over);
    ends.forEach(e=>{ const x=X(e.i); g+=`<circle cx="${x}" cy="${Y(e.s.vals(e.i))}" r="3" fill="${e.s.color}"/><text x="${w-mr+6}" y="${e.y+4}" font-size="11" font-weight="600" fill="var(--color-fg)">${esc(e.s.name)}</text>`; });
  }
  el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-label="${esc(opt.label||'gráfico')}">${g}<line class="xh" y1="${mt}" y2="${mt+ih}" stroke="var(--color-fg-muted)" opacity="0"/><g class="dots"></g><rect x="${ml_}" y="${mt}" width="${iw}" height="${ih}" fill="transparent" class="hit"/></svg><div class="rx-tip" hidden></div>`;
  const svg=el.querySelector('svg'), tip=el.querySelector('.rx-tip'), xh=svg.querySelector('.xh'), dots=svg.querySelector('.dots');
  const mv=e=>{
    const r=svg.getBoundingClientRect(), sx=(e.clientX-r.left)/r.width*w;
    const i=Math.max(i0,Math.min(i1,Math.round(i0+(sx-ml_)/iw*(i1-i0))));
    xh.setAttribute('x1',X(i)); xh.setAttribute('x2',X(i)); xh.setAttribute('opacity','.35');
    const rows=series.map(s=>({s,v:s.vals(i)})).filter(o=>o.v!=null).sort((a,b)=>b.v-a.v);
    dots.innerHTML=rows.map(o=>`<circle cx="${X(i)}" cy="${Y(o.v)}" r="4" fill="${o.s.color}" stroke="var(--color-panel)" stroke-width="2"/>`).join('');
    tip.innerHTML=`<div class="d">${mlong(i)}${opt.tipNote?opt.tipNote(i):''}</div>`+rows.map(o=>`<div class="r"><span class="s" style="background:${o.s.color}"></span><span>${esc(o.s.name)}: ${fmt2(o.v,opt)}</span></div>`).join('');
    tip.hidden=false; const px=X(i)/w*r.width; tip.style.left=Math.max(0,Math.min(px+14, r.width-tip.offsetWidth))+'px'; tip.style.top='8px';
  };
  const hit=svg.querySelector('.hit'); hit.addEventListener('pointermove',mv); hit.addEventListener('pointerdown',mv);
  hit.addEventListener('pointerleave',()=>{tip.hidden=true; xh.setAttribute('opacity','0'); dots.innerHTML='';});
}
// empilhado: séries [{name,color,vals}] + "Outras" (resto até o total)
function stackChart(el, series, rest, i0, i1, opt={}){
  const w=opt.w||900,h=opt.h||340,ml_=44,mr=12,mt=10,mb=26, iw=w-ml_-mr, ih=h-mt-mb;
  const all=[...series, ...(rest?[{name:'Outras',color:'var(--cds-chart-muted)',vals:rest}]:[])];
  let vmax=0; for(let i=i0;i<=i1;i++){ let s=0; all.forEach(x=>{ const v=x.vals(i); if(v>0) s+=v; }); if(s>vmax) vmax=s; }
  if(!(vmax>0)){ el.innerHTML='<p class="rx-note">Sem dados no período.</p>'; return; }
  const step=niceStep(vmax,4,0.01), top=Math.ceil(vmax/step)*step;
  const X=i=>ml_+(i1===i0?iw/2:(i-i0)/(i1-i0)*iw), Y=v=>mt+ih-(v/top)*ih;
  let g=''; for(let v=0;v<=top+1e-9;v+=step) g+=`<line x1="${ml_}" x2="${w-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--cds-chart-grid)"/><text x="${ml_-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--color-fg-muted)">${pct(v,0)}</text>`;
  xTicks(i0,i1).forEach(i=>g+=`<text x="${X(i)}" y="${h-6}" text-anchor="middle" font-size="11" fill="var(--color-fg-muted)">${ml(i)}</text>`);
  const base=new Map(range(i0,i1).map(i=>[i,0]));
  all.forEach(s=>{ const up=[],dn=[]; let gap=false;
    for(let i=i0;i<=i1;i++){ const v=s.vals(i); const b=base.get(i); const t=b+(v>0?v:0); up.push(`${X(i).toFixed(1)},${Y(t).toFixed(1)}`); dn.push(`${X(i).toFixed(1)},${Y(b).toFixed(1)}`); base.set(i,t); if(v==null) gap=true; }
    g+=`<path d="M${up.join('L')}L${dn.reverse().join('L')}Z" fill="${s.color}" opacity=".85" stroke="var(--color-panel)" stroke-width=".5"/>`; });
  el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-label="Posições empilhadas">${g}<line class="xh" y1="${mt}" y2="${mt+ih}" stroke="var(--color-fg)" opacity="0"/><rect x="${ml_}" y="${mt}" width="${iw}" height="${ih}" fill="transparent" class="hit"/></svg><div class="rx-tip" hidden></div>`;
  const svg=el.querySelector('svg'), tip=el.querySelector('.rx-tip'), xh=svg.querySelector('.xh');
  const mv=e=>{ const r=svg.getBoundingClientRect(), sx=(e.clientX-r.left)/r.width*w;
    const i=Math.max(i0,Math.min(i1,Math.round(i0+(sx-ml_)/iw*(i1-i0)))); xh.setAttribute('x1',X(i)); xh.setAttribute('x2',X(i)); xh.setAttribute('opacity','.3');
    const rows=all.map(s=>({s,v:s.vals(i)})).filter(o=>o.v>0.0005).sort((a,b)=>b.v-a.v);
    tip.innerHTML=`<div class="d">${mlong(i)}${opt.tipNote?opt.tipNote(i):''}</div>`+rows.map(o=>`<div class="r"><span class="s" style="background:${o.s.color}"></span><span>${esc(o.s.name)}: ${pct(o.v,1)}</span></div>`).join('');
    tip.hidden=false; const px=X(i)/w*r.width; tip.style.left=Math.max(0,Math.min(px+14, r.width-tip.offsetWidth))+'px'; tip.style.top='8px'; };
  const hit=svg.querySelector('.hit'); hit.addEventListener('pointermove',mv); hit.addEventListener('pointerdown',mv); hit.addEventListener('pointerleave',()=>{tip.hidden=true; xh.setAttribute('opacity','0');});
  el.insertAdjacentHTML('beforeend',`<div class="rx-legend" style="margin-top:6px">${all.map(s=>`<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join('')}</div>`);
}

const QB=[0.02,0.05,0.10,0.15];
function qcol(v,l){ if(!(v>0)) return 'var(--q0)'; if(v<l) return 'var(--q1)'; let k=2; QB.forEach(b=>{ if(b>l && v>=b) k++;}); return `var(--q${Math.min(5,k)})`; }
function scaleLegend(el){ const l=lim(); const steps=[[`< ${pct(l,1)}`,'var(--q1)']]; const bs=[l,...QB.filter(b=>b>l)];
  bs.forEach((b,k)=>steps.push([k<bs.length-1?`${pct(b,0)}–${pct(bs[k+1],0)}`:`≥ ${pct(b,0)}`, `var(--q${Math.min(5,k+2)})`]));
  el.innerHTML=`<span>Peso:</span><i style="background:var(--q0);border:1px solid var(--color-border-line)"></i><span>zero</span>`+steps.map(s=>`<i style="background:${s[1]}"></i><span>${s[0]}</span>`).join(''); }
function heatmap(el, rows, i0, i1, opt){
  if(!rows.length){ el.innerHTML='<p class="rx-note">Nenhuma posição acima do mínimo no período.</p>'; return; }
  const n=i1-i0+1, cw=Math.max(4,Math.min(22,Math.floor(1040/n))), rh=20, lw=opt.lw||170, top=6, covH=opt.cov?26:0;
  const w=lw+n*cw+10, h=top+rows.length*rh+covH+22; const l=lim();
  let s='';
  rows.forEach((r,k)=>{ const y=top+k*rh;
    s+=`<g class="r" data-key="${esc(r.key)}"${opt.onRow?' style="cursor:pointer"':''}><text x="${lw-8}" y="${y+rh/2+4}" text-anchor="end">${r.labelSvg}</text>`;
    for(let i=i0;i<=i1;i++){ const v=r.val(i); if(v==null) continue; s+=`<rect x="${lw+(i-i0)*cw}" y="${y+1}" width="${cw-1}" height="${rh-2}" rx="1.5" fill="${qcol(v,l)}" data-i="${i}" data-k="${k}"/>`; }
    s+='</g>'; });
  if(opt.cov){ const y0=top+rows.length*rh+4; s+=`<text x="${lw-8}" y="${y0+16}" text-anchor="end">revelado</text>`;
    for(let i=i0;i<=i1;i++){ const c=opt.cov(i); if(c==null) continue; const hh=Math.max(1,c*18); s+=`<rect x="${lw+(i-i0)*cw}" y="${y0+20-hh}" width="${cw-1}" height="${hh}" fill="${c<covMin()?'var(--color-bad)':'var(--cds-chart-axis)'}" data-i="${i}" data-cov="1"/>`; } }
  const yx=top+rows.length*rh+covH+16;
  xTicks(i0,i1).forEach(i=>s+=`<text x="${lw+(i-i0)*cw+cw/2}" y="${yx}" text-anchor="middle" style="fill:var(--color-fg-muted)">${ml(i)}</text>`);
  if(opt.mark!=null && opt.mark>=i0 && opt.mark<=i1) s+=`<rect x="${lw+(opt.mark-i0)*cw-1}" y="${top-2}" width="${cw+1}" height="${rows.length*rh+covH+4}" fill="none" stroke="var(--color-fg)" stroke-width="1.5" rx="2"/>`;
  el.innerHTML=`<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="Mapa de calor das posições">${s}</svg><div class="rx-tip" hidden></div>`;
  el.style.position='relative';
  const svg=el.querySelector('svg'), tip=el.querySelector('.rx-tip');
  svg.addEventListener('pointermove',e=>{ const t=e.target; if(!t.dataset||t.dataset.i==null){tip.hidden=true;return;}
    const i=+t.dataset.i; let html;
    if(t.dataset.cov){ html=`<div class="d">${mlong(i)}</div><div class="r">Carteira revelada: ${pct(opt.cov(i),0)}</div>`; }
    else { const r=rows[+t.dataset.k]; html=`<div class="d">${esc(r.tipTitle)}</div><div class="r">${mlong(i)}: ${pct(r.val(i),1)}</div>`+(r.tipExtra?r.tipExtra(i):''); }
    tip.innerHTML=html; tip.hidden=false; const er=el.getBoundingClientRect();
    tip.style.left=Math.max(0,Math.min(e.clientX-er.left+el.scrollLeft+14, el.scrollLeft+er.width-tip.offsetWidth-4))+'px'; tip.style.top=(e.clientY-er.top+14)+'px'; });
  svg.addEventListener('pointerleave',()=>tip.hidden=true);
  svg.addEventListener('click',e=>{ const t=e.target;
    if(t.dataset&&t.dataset.i!=null&&opt.onCol&&!opt.onRow) opt.onCol(+t.dataset.i);
    else if(opt.onRow){ const gEl=t.closest('g.r'); if(gEl) opt.onRow(gEl.dataset.key); } });
  if(opt.mark!=null){ const x=lw+(opt.mark-i0)*cw; if(x>el.clientWidth) el.scrollLeft=x-el.clientWidth+80; }
}
function spark(vals,l){ const w=80,h=22; const vm=Math.max(l*1.5,...vals.filter(v=>v!=null)); if(!(vm>0)) return '';
  let d='',pen=false; vals.forEach((v,k)=>{ if(v==null){pen=false;return;} const x=k/(vals.length-1)*w, y=h-2-(v/vm)*(h-4); d+=(pen?'L':'M')+x.toFixed(1)+','+y.toFixed(1); pen=true;});
  const ly=h-2-(l/vm)*(h-4); const last=vals[vals.length-1];
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><line x1="0" x2="${w}" y1="${ly}" y2="${ly}" stroke="var(--cds-chart-grid)" stroke-dasharray="2 2"/><path d="${d}" fill="none" stroke="#2f6fd0" stroke-width="1.5"/>${last!=null?`<circle cx="${w}" cy="${h-2-(last/vm)*(h-4)}" r="2.5" fill="#2f6fd0"/>`:''}</svg>`; }

function moreRows(el,n,key,cb){ el.innerHTML=n>25?`<button type="button" class="rx-btn">${S[key]?'Mostrar só as 25 primeiras':`Mostrar todas (${n})`}</button>`:''; el.onclick=e=>{ if(!e.target.closest('button')) return; S[key]=!S[key]; cb(); }; }
// ---------- estado ----------
const S={g:null, gm:null, gsel:null, grng:120, e:null, em:null, erng:120, rm:null, more:{}, sort:{}, gviz:'map', eviz:'map', esel:null};
const RNG=[[36,'3a'],[60,'5a'],[120,'10a'],[9999,'Tudo']];
function vizButtons(el,key,cb,opts){ el.innerHTML=(opts||[['map','Mapa'],['line','Linhas']]).map(([v,l])=>`<button type="button" class="rx-subtab" aria-selected="${S[key]===v}" data-v="${v}">${l}</button>`).join('');
  el.onclick=e=>{const b=e.target.closest('button'); if(!b) return; S[key]=b.dataset.v; cb();}; }
const serStyle=k=>({color:SER[k%8], dashArr:k>=8?'7 4':null});
function chipSelector(el, items, sel, max, onChange){
  el.innerHTML=items.map(it=>{ const k=sel.indexOf(it.key); const st=k>=0?serStyle(k):null;
    return `<button type="button" class="rx-chip" data-k="${esc(it.key)}" aria-pressed="false" style="${st?`border-color:${st.color};border-width:2px;font-weight:600`:''}">${esc(it.label)}</button>`; }).join('');
  el.onclick=e=>{ const b=e.target.closest('button'); if(!b) return; const key=b.dataset.k; const k=sel.indexOf(key);
    if(k>=0) sel.splice(k,1); else { if(sel.length>=max) return; sel.push(key); } onChange(); }; }
function segButtons(el,key,cb){ el.innerHTML=RNG.map(([v,l])=>`<button type="button" class="rx-subtab" aria-selected="${S[key]===v}" data-v="${v}">${l}</button>`).join('');
  el.onclick=e=>{const b=e.target.closest('button'); if(!b) return; S[key]=+b.dataset.v; cb();}; }
const tiles=arr=>arr.map(k=>`<div class="rx-tile"><span class="rx-tile-label">${k[0]}</span><span class="rx-tile-value">${k[1]}</span><span class="rx-tile-note">${k[2]}</span></div>`).join('');

const FUNDOS_EXT='EXT.FUNDOS';
const isReal=r=>r!==FUNDOS_EXT;
// tabela ordenável
function sTable(id, cols, rows, defK, rowAttr, limit, redraw){
  const st=S.sort[id]||(S.sort[id]={k:defK,dir:-1}); const col=cols.find(c=>c.k===st.k)||cols[0];
  const sorted=rows.slice().sort((a,b)=>{ const x=col.v(a), y=col.v(b); const xn=x==null||Number.isNaN(x), yn=y==null||Number.isNaN(y);
    if(xn&&yn) return 0; if(xn) return 1; if(yn) return -1; return (x<y?-1:x>y?1:0)*st.dir; });
  const el=$(id);
  el.innerHTML=`<thead><tr>${cols.map(c=>`<th data-k="${c.k}"${c.cls==='l'?' style="text-align:left"':''}>${c.v?`<button type="button">${c.l}</button>`:c.l}${st.k===c.k?(st.dir<0?' ↓':' ↑'):''}</th>`).join('')}</tr></thead><tbody>`+
    sorted.slice(0,limit).map(r=>`<tr ${rowAttr(r)}>${cols.map(c=>c.f(r)).join('')}</tr>`).join('')+'</tbody>';
  el.tHead.onclick=e=>{ const th=e.target.closest('th'); if(!th) return; const c=cols.find(x=>x.k===th.dataset.k); if(!c||!c.v) return;
    if(st.k===c.k) st.dir*=-1; else { st.k=c.k; st.dir=c.asc?1:-1; } (redraw||renderR)(); };
  return sorted.length;
}
const dn=d=>d==null?'<span class="zero">–</span>':d===0?'<span class="zero">0</span>':`<span class="${d>0?'rx-pos':'rx-neg'}">${d>0?'+':'−'}${Math.abs(d)}</span>`;
const dpct=d=>d==null||!isFinite(d)?'<span class="zero">–</span>':Math.abs(d)<0.005?'<span class="zero">0%</span>':`<span class="${d>0?'rx-pos':'rx-neg'}">${d>0?'+':'−'}${nf(Math.abs(d*100),0)}%</span>`;
const KS=[1,3,6,12];
const L=(s,cls)=>`<td style="text-align:left"${cls?` class="${cls}"`:''}>${s}</td>`;

// ---------- HOJE ----------
function renderR(){
  if(S.rm==null) S.rm=GOOD;
  const i=S.rm, kSel=+$('r-k').value, l=lim();
  fillMonths($('r-m'),0,NM-1,i);
  const gv=G.filter(g=>ok(g,i));
  let tt=0,cc=0; G.forEach(g=>{ tt+=tot(g,i)||0; cc+=cnf(g,i); });
  const conf=tt+cc>0?cc/(tt+cc):0;
  $('r-h').textContent=`Carteiras de ${mlong(i)}`;
  $('r-sub').innerHTML=`<b>${gv.length}</b> gestoras com carteira revelada ${$('covmin').selectedOptions[0].text} neste mês. No total das gestoras, <b>${pct(conf,0)}</b> das ações ainda estão confidenciais em ${ml(i)}`+(i!==GOOD?` (o mês mais recente bem revelado é ${mlong(GOOD)}).`:'.')+` Variações comparam só gestoras com carteira válida nas duas datas; compras e vendas usam a quantidade de ações.`;
  const A={}; const get=r=>A[r]||(A[r]={r,n:0,nAny:0,v:0,dn:{},dv:{},b:{},s:{},fb:{},fs:{}});
  gv.forEach(g=>Object.keys(g.p).forEach(r=>{ if(!isReal(r)) return; const w=W(g,r,i); if(w>0){ const a=get(r); a.nAny++; a.v+=w*tot(g,i); if(w>=l) a.n++; } }));
  const news=[];
  KS.forEach(k=>{ const j=i-k; if(j<0) return;
    const gb=gv.filter(g=>ok(g,j));
    gb.forEach(g=>Object.keys(g.p).forEach(r=>{ if(!isReal(r)) return;
      const wi=W(g,r,i), wj=W(g,r,j); if(!(wi>0||wj>0)) return; const a=get(r);
      a.dn[k]=(a.dn[k]||0)+(wi>=l?1:0)-(wj>=l?1:0);
      a.dv[k]=a.dv[k]||[0,0]; a.dv[k][0]+=wi*tot(g,i); a.dv[k][1]+=wj*tot(g,j);
      const x=delta(g,r,i,k); if(!x) return;
      if(isBuy(x)){ a.b[k]=(a.b[k]||0)+1; a.fb[k]=(a.fb[k]||0)+x.flow; } else if(isSell(x)){ a.s[k]=(a.s[k]||0)+1; a.fs[k]=(a.fs[k]||0)+x.flow; }
      if(k===kSel && x.d==='nova' && wi>=l) news.push({g,r,w:wi,v:wi*tot(g,i)}); })); });
  const all=Object.values(A);
  const N=key=>S.more[key]?50:10;
  const btn=(key,len)=>{ const b=document.querySelector(`[data-more="${key}"]`); b.hidden=len<=10; b.textContent=S.more[key]?'Ver menos':'Ver mais'; };
  const tkc={k:'r',l:'Ação',cls:'l',v:a=>a.r,asc:true,f:a=>tkCell(a.r)};
  const nmc={k:'nm',l:'Nome',cls:'l',f:a=>L(esc(ename(a.r)),'cw-nm')};
  const ra=a=>`data-r="${esc(a.r)}"`;
  $('r1s').textContent=`nº de gestoras com ≥ ${pct(l,1)} da carteira`;
  btn('r1', sTable('r1',[tkc,{k:'n',l:'Gestoras',v:a=>a.n,f:a=>`<td>${a.n}</td>`},
    ...[3,6,12].map(k=>({k:'d'+k,l:`Δ ${k}m`,v:a=>a.dn[k]??null,f:a=>`<td>${dn(a.dn[k]??null)}</td>`})),nmc],
    all.filter(a=>a.n>0), 'n', ra, N('r1')));
  const buy=$('r2t').value==='b', C=buy?'b':'s', F=buy?'fb':'fs';
  $('r2s').textContent=`nº de gestoras ${buy?'comprando':'vendendo'} ≥ 10% das ações · valor em ${kSel}m`;
  if(!S.sort.r2) S.sort.r2={k:'c'+kSel,dir:-1};
  btn('r2', sTable('r2',[tkc,...KS.map(k=>({k:'c'+k,l:`${k}m`,v:a=>a[C][k]||0,f:a=>`<td${k===kSel?' style="font-weight:600"':''}>${a[C][k]||'<span class="zero">0</span>'}</td>`})),
    {k:'f',l:`Valor ${kSel}m`,v:a=>buy?(a[F][kSel]||0):-(a[F][kSel]||0),f:a=>`<td>${brl(a[F][kSel]||0)}</td>`},nmc],
    all.filter(a=>KS.some(k=>a[C][k]>0)), 'c'+kSel, ra, N('r2')));
  const dv=(a,k)=>{ const x=a.dv[k]; return x&&x[1]>0?x[0]/x[1]-1:null; };
  btn('r3', sTable('r3',[tkc,{k:'v',l:'Valor',v:a=>a.v,f:a=>`<td>${brl(a.v)}</td>`},
    ...[3,6,12].map(k=>({k:'v'+k,l:`Δ ${k}m`,v:a=>dv(a,k),f:a=>`<td>${dpct(dv(a,k))}</td>`})),
    {k:'na',l:'Gestoras',v:a=>a.nAny,f:a=>`<td>${a.nAny}</td>`},nmc],
    all.filter(a=>a.v>0), 'v', ra, N('r3')));
  $('r4s').textContent=`não existiam em ${ml(Math.max(0,i-kSel))}, hoje ≥ ${pct(l,1)}`;
  if(news.length) btn('r4', sTable('r4',[tkc,{k:'g',l:'Gestora',cls:'l',v:o=>o.g.n,asc:true,f:o=>L(esc(o.g.n))},
      {k:'v',l:'Valor',v:o=>o.v,f:o=>`<td>${brl(o.v)}</td>`},{k:'w',l:'% carteira',v:o=>o.w,f:o=>`<td>${pct(o.w,1)}</td>`}],
      news, 'v', o=>`data-g="${o.g.id}"`, N('r4')));
  else { $('r4').innerHTML='<tbody><tr><td style="text-align:left" class="rx-note">Nenhuma nova posição relevante no período.</td></tr></tbody>'; btn('r4',0); }
  ['r1','r2','r3'].forEach(id=>$(id).querySelectorAll('tbody tr[data-r]').forEach(tr=>tr.onclick=()=>{S.em=i; H.openE(tr.dataset.r);}));
  $('r4').querySelectorAll('tbody tr[data-g]').forEach(tr=>tr.onclick=()=>{S.gm=i; H.openG(tr.dataset.g,true);});
}

// ---------- GESTORA (posições da casa) ----------
function setGestora(id, keepMonth){ const g=GI[id]; if(S.g!==id) S.gsel=null; S.g=id; if(!g) return;
  if(!keepMonth || S.gm==null || !inR(g,S.gm)) S.gm=bestMonth(g); }
function renderG(){
  const g=GI[S.g]; const box=$('g-casa'), none=$('g-casa-none');
  box.hidden=!g; none.hidden=!!g; if(!g) return;
  const i=S.gm, l=lim();
  fillMonths($('g-m'), g.o, lastIdx(g), i);
  $('g-rs').innerHTML=g.mb&&g.mb.length
    ? `<details><summary style="cursor:pointer">Soma de ${g.mb.length} CNPJs de gestora da mesma casa</summary><div style="margin-top:4px">${g.mb.map(m=>`${esc(m[0])} · ${esc(m[1])}${/CANC/i.test(m[2])?' · <i>cancelado</i>':''}`).join('<br>')}</div></details>`
    : `${esc(g.rs)} · CNPJ ${esc(g.cnpj)}`;
  const t=tot(g,i), c=cov(g,i), roots=Object.keys(g.p);
  const cur=roots.map(r=>({r,w:W(g,r,i)})).filter(o=>o.w>=l).sort((a,b)=>b.w-a.w);
  const chips=[]; if(g.man) chips.push('<span class="cw-chip">incluída manualmente</span>');
  if(c!=null && c<0.9) chips.push(`<span class="cw-chip warn">${pct(1-c,0)} da carteira ainda confidencial em ${ml(i)}</span>`);
  if(i!==bestMonth(g)) chips.push(`<span class="cw-chip">mês mais recente bem revelado: ${ml(bestMonth(g))}</span>`);
  $('g-chips').innerHTML=chips.join('');
  const prevT=tot(g,i-12), nHeld=roots.filter(r=>W(g,r,i)>0).length;
  $('g-kpis').innerHTML=tiles([
    ['Carteira de ações divulgada', brl(t), prevT>0&&t>0?`${t>=prevT?'+':'−'}${pct(Math.abs(t/prevT-1),0)} em 12 meses`:mlong(i)],
    ['Carteira revelada', pct(c,0), cnf(g,i)>0?`${brl(cnf(g,i))} confidencial`:'nenhuma posição confidencial'],
    [`Posições ≥ ${pct(l,1)}`, String(cur.length), `somam ${pct(cur.reduce((s,o)=>s+o.w,0),0)} · ${nHeld} emissores ≥ 0,5%`],
    ['5 maiores', pct(cur.slice(0,5).reduce((s,o)=>s+o.w,0),0), cur[0]?`maior: ${cur[0].r} (${pct(cur[0].w,1)})`:'–'],
  ]);
  if(!S.gsel) S.gsel=cur.slice(0,6).map(o=>o.r);
  const colorOf=r=>{const k=S.gsel.indexOf(r); return k>=0?serStyle(k).color:null;};
  $('g-tt').textContent=`Posições ≥ ${pct(l,1)} em ${mlong(i)}`;
  if(!cur.length){ $('g-tbl').innerHTML=`<tbody><tr><td style="text-align:left" class="rx-note">${t>0?'Nenhuma posição acima do mínimo neste mês.':'A carteira deste mês está toda confidencial ou não foi entregue.'}</td></tr></tbody>`; }
  else { const wmax=cur[0].w;
    $('g-tbl').innerHTML=`<thead><tr><th style="text-align:left">Emissor</th><th>% carteira</th><th>Valor</th><th>Δ ações 3m</th><th>Δ ações 12m</th><th>Δ peso 12m</th><th style="text-align:left">Desde</th><th style="text-align:left">Há</th><th style="text-align:left">24 meses</th></tr></thead><tbody>`+
    cur.map(o=>{ const r=o.r, hf=heldFor(g,r,i); const sp=range(i-23,i).map(k=>ok(g,k)?W(g,r,k):null); const col=colorOf(r);
      return `<tr data-r="${esc(r)}"><td style="text-align:left;white-space:normal"><span class="cw-tkc">${logo(r)}<span><span class="tk">${esc(r)}</span> <span class="co">${esc(ename(r))}</span></span></span></td>`+
        `<td><span class="cw-wbar"><i style="width:${Math.round(o.w/wmax*60)}px"></i>${pct(o.w,1)}</span></td><td>${brl(o.w*t)}</td><td>${dq(delta(g,r,i,3))}</td><td>${dq(delta(g,r,i,12))}</td><td>${pp(inR(g,i-12)?o.w-W(g,r,i-12):null)}</td><td style="text-align:left">${hf[0]}</td><td style="text-align:left" class="co">${hf[1]}</td><td style="text-align:left">${spark(sp,l)}</td></tr>`;}).join('')+'</tbody>';
  }
  $('g-tbl').querySelectorAll('tbody tr[data-r]').forEach(tr=>tr.onclick=()=>{ if(isReal(tr.dataset.r)){ S.em=i; H.openE(tr.dataset.r);} });
  const outs=inR(g,i-6)?roots.filter(r=>W(g,r,i-6)>=l && W(g,r,i)<l).sort((a,b)=>W(g,b,i-6)-W(g,a,i-6)):[];
  $('g-outs').innerHTML=outs.length?`<p class="rx-note" style="margin-top:10px">Saíram ou caíram abaixo de ${pct(l,1)} desde ${ml(i-6)}:</p><div class="rx-chips-b">${outs.map(r=>`<button type="button" class="rx-chip" data-r="${esc(r)}"><b>${esc(r)}</b> ${pct(W(g,r,i-6),1)} → ${pct(W(g,r,i),1)}</button>`).join('')}</div>`:'';
  $('g-outs').querySelectorAll('[data-r]').forEach(b=>b.onclick=()=>{ if(isReal(b.dataset.r)){ S.em=i; H.openE(b.dataset.r);} });
  // compras e vendas da casa
  const k=+$('g-k').value;
  const mv=movSort('g-ord',roots.map(r=>({r,x:delta(g,r,i,k)})).filter(o=>isBuy(o.x)||isSell(o.x)).map(o=>({...o,m:lastMove(g,o.r,i,k)})));
  $('g-mov').innerHTML=!ok(g,i-k)?`<tbody><tr><td style="text-align:left" class="rx-note">Sem carteira comparável em ${mlong(i-k)}.</td></tr></tbody>`:mv.length?
    `<thead><tr><th style="text-align:left">Emissor</th><th>Δ ações</th><th>Valor</th><th style="text-align:left">Quando</th><th>Peso ${ml(i-k)}</th><th>Peso ${ml(i)}</th></tr></thead><tbody>`+mv.map(o=>`<tr data-r="${esc(o.r)}">${tkCell(o.r)}<td>${dq(o.x)}</td><td class="${o.x.flow>0?'rx-pos':'rx-neg'}">${brl(o.x.flow)}</td>${whenCell(o.m)}<td>${pct(W(g,o.r,i-k),1)}</td><td>${pct(W(g,o.r,i),1)}</td></tr>`).join('')+'</tbody>'
    :'<tbody><tr><td style="text-align:left" class="rx-note">Nenhuma mudança de ≥ 10% nas ações no período.</td></tr></tbody>';
  $('g-mov').querySelectorAll('tbody tr[data-r]').forEach(tr=>tr.onclick=()=>{ if(isReal(tr.dataset.r)){ S.em=i; H.openE(tr.dataset.r);} });
  // histórico
  const i1=lastIdx(g), i0=Math.max(g.o, i1-S.grng+1);
  segButtons($('g-rng'),'grng',renderG); vizButtons($('g-viz'),'gviz',renderG,[['map','Mapa'],['stack','Empilhado'],['line','Linhas']]);
  const hr=roots.filter(r=>{ for(let j=i0;j<=i1;j++) if(ok(g,j)&&W(g,r,j)>=l) return true; return false; })
    .sort((a,b)=>(W(g,b,i)-W(g,a,i))||(maxW(g,b,i0,i1)-maxW(g,a,i0,i1)));
  $('g-mapbox').hidden=S.gviz!=='map'; $('g-linebox').hidden=S.gviz==='map';
  $('g-hist-note').textContent=S.gviz==='map'?'Cada célula é o peso na carteira de ações divulgada da casa; a faixa de baixo mostra quanto da carteira estava revelado. Clique numa coluna para mudar o mês.'
    :S.gviz==='stack'?'Peso das posições escolhidas abaixo, empilhadas; "Outras" é o restante da carteira revelada. Passe o mouse para ver o mês.'
    :'Peso das posições escolhidas abaixo. Passe o mouse para ver o mês.';
  const tipNote=j=>{const c=cov(g,j); return c!=null&&c<0.9?` · ${pct(c,0)} revelado`:'';};
  if(S.gviz!=='map'){
    const ser=S.gsel.map((r,kk)=>({name:r, ...serStyle(kk), vals:j=>ok(g,j)?W(g,r,j):null}));
    if(S.gviz==='line') lineChart($('g-line'), ser, i0, i1, {mark:i, endLabels:true, w:900, h:340, label:'Peso das posições selecionadas', tipNote});
    else stackChart($('g-line'), ser, j=>{ if(!ok(g,j)) return null; let s=0; S.gsel.forEach(r=>s+=W(g,r,j)); let all=0; roots.forEach(r=>all+=W(g,r,j)); return Math.max(0,Math.min(1,all)-s); }, i0, i1, {tipNote});
    chipSelector($('g-chips2'), hr.map(r=>({key:r,label:r})), S.gsel, 12, renderG);
    return;
  }
  scaleLegend($('g-scale'));
  const hrs=S.gall?hr:hr.slice(0,25); moreRows($('g-hmore'), hr.length, 'gall', renderG);
  heatmap($('g-hm'), hrs.map(r=>({key:r, labelSvg:`<tspan style="font-weight:600;fill:var(--color-fg)">${esc(r)}</tspan> ${esc(ename(r).slice(0,16))}`, tipTitle:`${r} · ${ename(r)}`,
      val:j=>ok(g,j)?W(g,r,j):null, tipExtra:j=>`<div class="r">Valor: ${brl(val(g,r,j))}</div>`})),
    i0, i1, {mark:i, cov:j=>cov(g,j), onCol:j=>{S.gm=j; renderG();}});
}

// ---------- EMPRESA (detentores) ----------
function holders(r,i,l){ return G.filter(g=>ok(g,i)&&W(g,r,i)>=l).map(g=>({g,w:W(g,r,i)})).sort((a,b)=>b.w-a.w); }
function renderE(){
  if(S.em==null) S.em=GOOD;
  const r=S.e, i=S.em, l=lim(); if(!r) return;
  $('e-q').value=r; fillMonths($('e-m'),0,NM-1,i);
  $('e-nome').innerHTML=`<span class="cw-tkc">${logo(r,true)}<span><b>${esc(r)}</b> · ${esc(ename(r))}<br><span class="rx-note">Tickers: ${esc(etks(r))}${eold(r)?` · código anterior: ${esc(eold(r))}`:''}</span></span></span>`;
  const all=holders(r,i,1e-9), rel=all.filter(o=>o.w>=l), n12=holders(r,Math.max(0,i-12),l).length;
  const k=+$('e-k').value; const mv=G.filter(g=>ok(g,i)&&ok(g,i-k)).map(g=>({g,x:delta(g,r,i,k)})).filter(o=>isBuy(o.x)||isSell(o.x));
  const nb=mv.filter(o=>isBuy(o.x)).length, ns=mv.length-nb;
  const vAll=all.reduce((s,o)=>s+val(o.g,r,i),0);
  $('e-kpis').innerHTML=tiles([
    [`Gestoras com ≥ ${pct(l,1)}`, String(rel.length), `${n12} doze meses antes · ${all.length} com qualquer peso`],
    ['Valor nas gestoras', brl(vAll), `peso médio ${rel.length?pct(rel.reduce((s,o)=>s+o.w,0)/rel.length,1):'–'} entre as relevantes`],
    [`Compraram × venderam (${k}m)`, `${nb} × ${ns}`, `líquido ${brl(mv.reduce((s,o)=>s+o.x.flow,0))}`],
    ['Maior detentora', all[0]?esc(all[0].g.n):'–', all[0]?`${pct(all[0].w,1)} da carteira`:''],
  ]);
  const fq=$('e-fq').value.trim().toLowerCase(), fv=+$('e-fv').value, fg=+$('e-fg').value, fd=$('e-fd').value;
  const rows=($('e-only').value==='1'?rel:all).map(o=>{ const hf=heldFor(o.g,r,i), s0=since(o.g,r,i);
      return {...o, v:val(o.g,r,i), t:tot(o.g,i), d3:delta(o.g,r,i,3), d12:delta(o.g,r,i,12), dw:inR(o.g,i-12)?o.w-W(o.g,r,i-12):null, hf, s0}; })
    .filter(o=>(!fq||o.g.n.toLowerCase().includes(fq)||o.g.rs.toLowerCase().includes(fq)) && o.v>=fv && (o.t||0)>=fg
      && (!fd || (fd==='b'?isBuy(o.d3):isSell(o.d3))));
  $('e-tt').textContent=`Detentores em ${mlong(i)}`;
  $('e-cnt2').textContent=`${rows.length} de ${all.length} gestoras`;
  const dnum=x=>!x?null:x.d==='nova'?1e9:x.d==='zerou'?-1:x.d;
  const wmax=Math.max(...rows.map(o=>o.w),1e-9);
  if(rows.length) sTable('e-tbl',[
      {k:'g',l:'Gestora',cls:'l',v:o=>o.g.n,asc:true,f:o=>L(esc(o.g.n)+(H.hasFunds(o.g.id)?' <span class="cw-chip new" title="tem performance e attribution">perf.</span>':''))},
      {k:'w',l:'% carteira',v:o=>o.w,f:o=>`<td><span class="cw-wbar"><i style="width:${Math.round(o.w/wmax*60)}px"></i>${pct(o.w,1)}</span></td>`},
      {k:'v',l:'Valor',v:o=>o.v,f:o=>`<td>${brl(o.v)}</td>`},
      {k:'d3',l:'Δ ações 3m',v:o=>dnum(o.d3),f:o=>`<td>${dq(o.d3)}</td>`},
      {k:'d12',l:'Δ ações 12m',v:o=>dnum(o.d12),f:o=>`<td>${dq(o.d12)}</td>`},
      {k:'dw',l:'Δ peso 12m',v:o=>o.dw,f:o=>`<td>${pp(o.dw)}</td>`},
      {k:'s',l:'Desde',cls:'l',v:o=>o.s0,asc:true,f:o=>L(o.hf[0])},
      {k:'h',l:'Há',cls:'l',v:o=>o.s0==null?null:i-o.s0,f:o=>L(o.hf[1],'co')},
      {k:'t',l:'Carteira da gestora',v:o=>o.t,f:o=>`<td class="co">${brl(o.t)}</td>`},
      {k:'c',l:'Revelado',v:o=>cov(o.g,i),f:o=>`<td>${pct(cov(o.g,i),0)}</td>`},
    ], rows, 'w', o=>`data-g="${o.g.id}"`, 1e9, renderE);
  else $('e-tbl').innerHTML=`<tbody><tr><td style="text-align:left" class="rx-note">${all.length?'Nenhuma gestora com esses filtros.':`Nenhuma gestora acompanhada tinha essa ação em ${mlong(i)}.`}</td></tr></tbody>`;
  $('e-tbl').querySelectorAll('tbody tr[data-g]').forEach(tr=>tr.onclick=()=>{S.gm=i; H.openG(tr.dataset.g,true);});
  mv.forEach(o=>{o.m=lastMove(o.g,r,i,k);}); movSort('e-ord',mv);
  $('e-mov').innerHTML=mv.length?`<thead><tr><th style="text-align:left">Gestora</th><th>Δ ações</th><th>Valor</th><th style="text-align:left">Quando</th><th>Peso ${ml(i-k)}</th><th>Peso ${ml(i)}</th></tr></thead><tbody>`+
    mv.map(o=>`<tr data-g="${o.g.id}">${L(esc(o.g.n))}<td>${dq(o.x)}</td><td class="${o.x.flow>0?'rx-pos':'rx-neg'}">${brl(o.x.flow)}</td>${whenCell(o.m)}<td>${pct(W(o.g,r,i-k),1)}</td><td>${pct(W(o.g,r,i),1)}</td></tr>`).join('')+'</tbody>'
    :'<tbody><tr><td style="text-align:left" class="rx-note">Nenhuma gestora mudou ≥ 10% das ações no período.</td></tr></tbody>';
  $('e-mov').querySelectorAll('tbody tr[data-g]').forEach(tr=>tr.onclick=()=>{S.gm=i; H.openG(tr.dataset.g,true);});
  const i1=NM-1, i0=Math.max(0,i1-S.erng+1);
  segButtons($('e-rng'),'erng',renderE);
  $('e-ct').textContent=`Gestoras com posição ≥ ${pct(l,1)}`;
  const cnt=range(0,NM-1).map(j=>holders(r,j,l).length);
  lineChart($('e-cnt'), [{name:'Gestoras', color:SER[0], vals:j=>j<=GOOD?cnt[j]:null}], i0, i1, {fmt:'int', mark:i, label:'Número de gestoras com a posição', h:240});
  $('e-cnt').insertAdjacentHTML('beforeend',`<p class="rx-note">A linha para em ${mlong(GOOD)}: depois disso parte das carteiras ainda está confidencial e a contagem cairia artificialmente.</p>`);
  const gs=G.filter(g=>{for(let j=i0;j<=i1;j++) if(ok(g,j)&&W(g,r,j)>=l) return true; return false;}).sort((a,b)=>(W(b,r,i)-W(a,r,i))||(maxW(b,r,i0,i1)-maxW(a,r,i0,i1)));
  vizButtons($('e-viz'),'eviz',renderE);
  $('e-mapbox').hidden=S.eviz!=='map'; $('e-linebox').hidden=S.eviz!=='line';
  if(!S.esel || S.eselFor!==r){ S.esel=gs.slice(0,5).map(g=>g.id); S.eselFor=r; }
  if(S.eviz==='line'){
    const short=g=>g.n.length>14?g.n.slice(0,13)+'…':g.n;
    lineChart($('e-line'), S.esel.map((id,kk)=>({name:short(GI[id]), ...serStyle(kk), vals:j=>ok(GI[id],j)?W(GI[id],r,j):null})), i0, i1,
      {mark:i, endLabels:true, w:900, h:340, label:'Peso da ação nas gestoras selecionadas'});
    chipSelector($('e-chips2'), gs.map(g=>({key:g.id,label:g.n})), S.esel, 8, renderE);
    return;
  }
  scaleLegend($('e-scale'));
  const gss=S.eall?gs:gs.slice(0,25); moreRows($('e-hmore'), gs.length, 'eall', renderE);
  heatmap($('e-hm'), gss.map(g=>({key:g.id, labelSvg:esc(g.n.slice(0,24)), tipTitle:g.n, val:j=>ok(g,j)?W(g,r,j):null,
      tipExtra:j=>`<div class="r">Revelado: ${pct(cov(g,j),0)}</div>`})),
    i0, i1, {mark:i, lw:190, onRow:id=>{S.gm=i; H.openG(id,true);}});
}

let ROOTS=[];
function init(data, hooks){
  D=data; H=hooks; M=D.meses; NM=M.length; G=D.gestoras; E=D.emissores;
  G.forEach(g=>GI[g.id]=g);
  G.sort((a,b)=>latestTot(b)-latestTot(a));
  GOOD=(()=>{ for(let i=NM-1;i>=0;i--){ let t=0,c=0; G.forEach(g=>{t+=tot(g,i)||0; c+=cnf(g,i);}); if(t>0 && t/(t+c)>=0.8) return i; } return NM-1; })();
  E[FUNDOS_EXT]=['Fundos no exterior','cotas de fundos offshore · carteira não aberta',''];
  ROOTS=Object.keys(E).filter(isReal).sort();
  $('dl-e').innerHTML=ROOTS.map(r=>`<option value="${esc(r)}">${esc(ename(r))} · ${esc(etks(r))}</option>`).join('');
  // eventos
  $('r-m').addEventListener('change',()=>{S.rm=+$('r-m').value; renderR();});
  ['r-k','r2t'].forEach(id=>$(id).addEventListener('change',renderR));
  document.querySelectorAll('[data-more]').forEach(b=>b.addEventListener('click',()=>{ const k=b.dataset.more; S.more[k]=!S.more[k]; renderR(); }));
  $('g-m').addEventListener('change',()=>{S.gm=+$('g-m').value; renderG();});
  $('g-k').addEventListener('change',renderG);
  $('g-ord').addEventListener('change',renderG); $('e-ord').addEventListener('change',renderE);
  $('e-q').addEventListener('change',()=>{ const r=findE($('e-q').value); if(r) H.openE(r); });
  $('e-m').addEventListener('change',()=>{S.em=+$('e-m').value; renderE();});
  ['e-k','e-only','e-fv','e-fg','e-fd'].forEach(id=>$(id).addEventListener('change',renderE));
  $('e-fq').addEventListener('input',renderE);
  ['lim','covmin'].forEach(id=>$(id).addEventListener('change',()=>{S.gsel=null; H.rerender();}));
  $('cw-gen').textContent=`Carteiras: CVM, de ${mlong(0)} a ${mlong(NM-1)}, ${G.length} gestoras independentes, gerado em ${D.gerado_em}.`;
  S.e=(()=>{ const c={}; G.forEach(g=>{ if(!ok(g,GOOD)) return; Object.keys(g.p).forEach(r=>{ if(W(g,r,GOOD)>=0.02) c[r]=(c[r]||0)+1; }); }); return Object.keys(c).sort((a,b)=>c[b]-c[a])[0]||ROOTS[0]; })();
}
function findE(q){ q=String(q||'').trim().toUpperCase(); if(!q) return null;
  return ROOTS.find(x=>x===q)||ROOTS.find(x=>etks(x).split(' ').includes(q))||ROOTS.find(x=>eold(x).split(' ').includes(q.slice(0,4)))||ROOTS.find(x=>x===q.slice(0,4))||ROOTS.find(x=>ename(x).toUpperCase().includes(q)); }
return { init, renderR, renderG, renderE, setGestora, findE, S, get G(){return G;}, get GI(){return GI;}, ename, hasRoot:r=>!!E[r], monthIdx:ym=>M.indexOf(ym) };
})();
