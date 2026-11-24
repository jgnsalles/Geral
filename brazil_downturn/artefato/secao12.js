
let TQ=null;
function ptri(){
 const X=window.P2, k=ST.tipo, sel=document.getElementById('sel-q'), qs=Object.keys((X.tri||{})[k]||{}).sort();
 if(!qs.length){document.getElementById('t-rec').innerHTML='';document.getElementById('t-saq').innerHTML='';document.getElementById('tri-sum').textContent='';return;}
 if(!TQ||!qs.includes(TQ))TQ=qs[qs.length-1];
 sel.innerHTML=qs.slice().reverse().map(q=>`<option value="${q}">${q.replace('Q','T')}${X.estimados.includes(q)?' (estimado)':''}</option>`).join(''); sel.value=TQ;
 sel.onchange=()=>{TQ=sel.value;ptri();};
 const d=X.tri[k][TQ], tr=X.trimestres.find(z=>z.q==TQ)||{};
 document.getElementById('tri-sum').innerHTML=`<b>${NM(k)}</b> em <b>${TQ.replace('Q','T')}</b>${X.estimados.includes(TQ)?' (estimado)':''}: ${d.n_rec} gestoras captaram R$ ${F(d.rec_bi*1000,0)} mi e ${d.n_saq} sacaram R$ ${F(-d.saq_bi*1000,0)} mi${d.top3_rec!=null?'; as 3 maiores ficaram com '+P(d.top3_rec)+' das entradas':''}. Ibovespa no trimestre ${P(tr.ibov_q,1)}, CDI ${P(tr.cdi,1)}.`;
 const tb=L=>'<table><thead><tr><th class="l">Gestora</th><th>R$ mi</th><th>% da posição</th><th>Alpha 12m</th><th>Posição no início (R$ mi)</th></tr></thead><tbody>'+L.map(r=>`<tr><td class="l">${r.nome}</td><td class="n ${r.f_mi>=0?'pos':'neg'}">${r.f_mi.toLocaleString('pt-BR',{maximumFractionDigits:1})}</td><td class="n">${r.pct==null?'nova':P(r.pct,0)}</td><td class="n">${r.a12==null?'—':PP(r.a12,0)}</td><td class="n">${r.h_mi.toLocaleString('pt-BR')}</td></tr>`).join('')+'</tbody></table>';
 document.getElementById('t-rec').innerHTML=d.rec.length?tb(d.rec):'<p class="note">Ninguém captou.</p>';
 document.getElementById('t-saq').innerHTML=d.saq.length?tb(d.saq):'<p class="note">Ninguém sacou.</p>';
}
