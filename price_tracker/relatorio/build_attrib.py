"""Monta o relatório FT da atribuição (relatorio/o_que_o_modelo_acerta.html) a partir de dados_attrib.json e do CSS do relatório anterior."""
import json, pathlib, re
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_attrib.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
nm2 = lambda x, n=2: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')

dec3 = {r['nome']: r for r in d['decomp']['12']}
U3, T3 = dec3['Universo (S&P, peso igual)'], dec3['Top 20']
pers3 = d['roic_pers']['12']['ic']; gic = d['growth']['12']['ic']['ic']
rr3 = d['rerating']['12']['slope']
orc = d['oracle']
eps3_gain = [orc[k]['EPS em 3 anos'] for k in ('Top 20', 'OoL')]
rr_gain = [orc[k]['Re-rating em 1 ano'] for k in ('Top 20', 'OoL')]
miss = d['misses']
fm3 = d['fm']['12']
sig = d['sinais']

body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Análise de atribuição · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">Anatomia de uma estratégia vencedora</div>
<h1>O modelo acerta a qualidade, não o futuro. E é por isso que funciona</h1>
<p class="deck">Quinze anos de compras do S&amp;P 500 decompostos ação por ação mostram que o retorno alto do ROIC persiste, o crescimento passado não se repete e o mercado acaba pagando mais pela qualidade que dura. Prever o negócio melhor que o modelo renderia pouco.</p>
<div class="byline">S&amp;P 500 point-in-time, {d['n_obs']:,} observações ação-trimestre · 5 carteiras: Top 20, Opportunity of Lifetime, High ROIC, High Growth e Excepcionais · em dólares</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele pesa duas vezes aqui: é o filtro das carteiras e é o objeto de um dos testes (se ele persiste). Usamos o ROIC triangulado oficial (14/11/2026); financeiras usam ROE. Erro de medida faria a persistência parecer <i>menor</i> do que é. Backtest, sem custos de transação; não é recomendação de investimento.</p>

<div class="big">
 <div><b>{nm2(pers3)}</b><span>correlação do ROIC de hoje com o de 3 anos depois (por posição)</span></div>
 <div><b>{nm2(gic)}</b><span>idem para o crescimento do EPS: o passado não prevê o futuro</span></div>
 <div><b>{pc(rr3, 0)}</b><span>da distância até o P/E justo que o P/L fecha em 3 anos</span></div>
 <div><b>{pp(min(eps3_gain), 0)} a {pp(max(eps3_gain), 0)}</b><span>ao ano, para quem soubesse o lucro dos 3 anos seguintes e vetasse as 20% piores</span></div>
</div>

<div class="cols">
 <div class="prose">
  <p>Toda carteira vencedora deixa uma pergunta incômoda: ela ganhou pelo motivo certo? A resposta decide se vale a pena colocar uma camada de julgamento por cima de uma regra que já funciona. Por isso refizemos as quinze temporadas do modelo separando, em cada ação comprada, o que veio do crescimento do lucro, o que veio da mudança do múltiplo e o que veio dos dividendos. Depois conferimos cada previsão do modelo contra o que de fato aconteceu.</p>
  <p>O resultado é mais simples do que parece. O modelo faz três apostas implícitas. A primeira, que o ROIC alto continua alto, se confirmou de forma impressionante. A segunda, que o lucro continua crescendo no ritmo dos últimos cinco anos, falhou por completo: o crescimento passado não diz nada sobre o futuro. A terceira, que o preço converge para o P/E justo, se confirmou parcialmente: cerca de um terço da distância em três anos.</p>
  <p>Quando o lucro das ações escolhidas não cresceu mais que o da média, de onde veio o retorno a mais? Do re-rating. O mercado passou a pagar múltiplos maiores por empresas cuja rentabilidade se mostrou durável. É uma conclusão importante para quem pensa em julgar caso a caso. O ganho não está em adivinhar o lucro do ano que vem, e sim em ficar com a qualidade enquanto o mercado demora a reconhecê-la.</p>
 </div>
 <aside class="box"><h3>As cinco perguntas</h3><ol>
  <li><b>De onde veio o retorno?</b> Do re-rating, não do lucro (exceto nas Excepcionais).</li>
  <li><b>As previsões se confirmaram?</b> ROIC sim, crescimento não, P/E justo em parte.</li>
  <li><b>O que explica o retorno?</b> Entre o que se sabe na compra, só o ROIC.</li>
  <li><b>Onde o modelo errou?</b> Nas grandes altas que vieram de empresas com crescimento parado.</li>
  <li><b>Quanto vale o julgamento?</b> Sobre o negócio, pouco. Sobre o preço, muito, mas preço não se prevê.</li></ol></aside>
</div>

<h2 class="chap" style="margin-top:56px">1. De onde veio o retorno</h2>
<figure><figcaption class="t">As carteiras ganharam do mercado pelo múltiplo, não pelo lucro</figcaption>
<figcaption class="s">Retorno anual das posições em 3 anos, decomposto em crescimento do EPS, re-rating (mudança do P/L) e dividendos. Média ponderada pelas posições de cada trimestre.</figcaption>
<div class="legend" id="lg1"></div><div id="c1"></div>
<div class="src">Fonte: balanços da SEC na data, preços ajustados. Só posições com EPS positivo no começo e no fim; ficam de fora {pc(T3['sem_dado'], 0)} a {pc(dec3['Excepcionais']['sem_dado'], 0)} das posições (as mais recentes, sem 3 anos de futuro, e as que deram prejuízo).</div>
<div class="sowhat"><b>E daí</b><span>Na Top 20, o lucro cresceu {pc(T3['eps'])} ao ano, menos que o do mercado ({pc(U3['eps'])}). O retorno a mais veio todo do re-rating: {pc(T3['rr'])} ao ano, contra {pc(U3['rr'])} no mercado. As Excepcionais são a exceção: o lucro delas cresceu {pc(dec3['Excepcionais']['eps'])} ao ano. É a única carteira cujo ganho vem do negócio, e isso explica tanto o retorno quanto a volatilidade.</span></div>
</figure>

<figure><figcaption class="t">No curto prazo, preço é humor; em cinco anos, é lucro</figcaption>
<figcaption class="s">Quanto da diferença de retorno entre as ações do S&amp;P vem de cada parte, por horizonte (participação na variância do retorno).</figcaption>
<div class="legend" id="lg2"></div><div id="c2"></div>
<div class="sowhat"><b>E daí</b><span>Em 1 ano, {pc(d['var_decomp']['4']['lp'], 0)} da diferença entre as ações vem do múltiplo. Em 5 anos, {pc(d['var_decomp']['20']['le'], 0)} vem do lucro. Quem julga uma empresa pelo próximo trimestre está julgando humor. O modelo ganha porque segura as posições tempo suficiente para o lucro durável aparecer no preço.</span></div>
</figure>

<h2 class="chap" style="margin-top:56px">2. O que o modelo previu e o que aconteceu</h2>
<figure><figcaption class="t">O ROIC alto é teimoso: três em cada quatro continuam acima de 30% depois de três anos</figcaption>
<figcaption class="s">De cada faixa de ROIC hoje (linhas), para onde as empresas foram três anos depois (colunas). Empresas não financeiras do S&amp;P 500.</figcaption>
<div id="c3" class="tablebox"></div>
<div id="c3b" class="tablebox" style="margin-top:14px"></div>
<div class="sowhat"><b>E daí</b><span>A aposta central do modelo se confirmou. A correlação entre o ranking de ROIC de hoje e o de 3 anos depois é {nm2(pers3)} (e {nm2(d['roic_pers']['20']['ic'])} em 5 anos). Nas carteiras, o ROIC mediano na compra é praticamente o mesmo 3 anos depois, e mais de 90% das posições continuam acima de 12%. Se o ROIC pode estar errado, o erro não impediu de achar empresas que continuam boas.</span></div>
</figure>

<figure><figcaption class="t">O crescimento passado não prevê o futuro: todo mundo volta para perto de 8% a 12%</figcaption>
<figcaption class="s">Crescimento anual do EPS previsto (a mediana dos 5 anos anteriores) contra o realizado nos 3 anos seguintes, por quinto do crescimento previsto. Medianas.</figcaption>
<div class="legend" id="lg4"></div><div id="c4"></div>
<div id="c4b" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>O quinto que vinha crescendo {pc(d['growth']['12']['quint'][4][0], 0)} ao ano cresceu {pc(d['growth']['12']['quint'][4][1], 0)} depois. O que vinha encolhendo cresceu {pc(d['growth']['12']['quint'][0][1], 0)}. A correlação é até levemente negativa ({nm2(gic)}). O modelo sobrevive a isso porque usa o crescimento como filtro de qualidade e porque o P/E justo usa um g conservador (7% a 3,5%). <b>Para a camada qualitativa, a lição é direta:</b> não adianta discordar do modelo com base em projeções de crescimento. Ninguém prevê crescimento bem, nem o modelo, nem o sell-side.</span></div>
</figure>

<figure><figcaption class="t">O P/E justo funciona como bússola: o preço anda na direção dele, devagar</figcaption>
<figcaption class="s">Distância entre o P/E justo e o P/L de compra (em log, por quinto) e quanto o P/L de fato se moveu depois. Barras: 1, 3 e 5 anos.</figcaption>
<div class="legend" id="lg5"></div><div id="c5"></div>
<div class="sowhat"><b>E daí</b><span>As ações mais baratas em relação ao P/E justo tiveram o múltiplo subindo; as mais caras, caindo. Em cada horizonte o P/L fecha {pc(d['rerating']['4']['slope'], 0)}, {pc(rr3, 0)} e {pc(d['rerating']['20']['slope'], 0)} da distância (1, 3 e 5 anos) e acerta a direção em {pc(d['rerating']['12']['hit'], 0)} dos casos. É aqui que mora o ganho do modelo: na convergência do múltiplo de empresas cujo ROIC se mantém.</span></div>
</figure>

<figure><figcaption class="t">Ordenar pelo retorno esperado ajuda, mas só depois do filtro de qualidade</figcaption>
<figcaption class="s">Excesso anual sobre o S&amp;P 500 por quinto do retorno esperado, só entre as ações de qualidade (ROIC ≥ 12%, crescimento ≥ 15%, sem cíclicas). 1 e 3 anos.</figcaption>
<div class="legend" id="lg6"></div><div id="c6"></div>
<div id="c6b" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>No universo inteiro, o retorno esperado quase não ordena nada (correlação {nm2(d['exp_ret']['4']['ic']['ic'], 3)}). Entre as de qualidade, o quinto de maior retorno esperado bateu o de menor por {pp(d['exp_ret']['4']['quint_qual'][4] - d['exp_ret']['4']['quint_qual'][0])} ao ano. Atenção ao tamanho: no período, o sinal mais forte entre as de qualidade foi simplesmente ser grande. É a década das megacaps, algo que não se deve esperar que se repita.</span></div>
</figure>

<h2 class="chap" style="margin-top:56px">3. O que explica o retorno</h2>
<figure><figcaption class="t">Do que se sabe na compra, só o ROIC prevê o retorno de 3 anos</figcaption>
<figcaption class="s">Quanto da diferença de retorno entre as ações cada grupo de variáveis explica (R² médio das regressões trimestre a trimestre), em 1 e 3 anos.</figcaption>
<div class="legend" id="lg7"></div><div id="c7"></div>
<div class="sowhat"><b>E daí</b><span>As quatro variáveis conhecidas na compra (ROIC, crescimento, P/L e retorno esperado) explicam {pc(fm3['r2']['ante'], 0)} da diferença de retorno em 3 anos. Dentro disso, só o ROIC tem efeito estatisticamente claro (t = {nm2(fm3['t_ante'][0], 1)}); as outras três somem quando o ROIC está na conta. O lucro realizado explica outros {pc(fm3['r2']['eps'], 0)}. Juntando tudo, mesmo sabendo o futuro, {pc(1 - fm3['r2']['tudo'], 0)} da diferença continua sem explicação: é o ruído do mercado.</span></div>
</figure>

<h2 class="chap" style="margin-top:56px">4. Onde o modelo errou</h2>
<figure><figcaption class="t">Os vencedores fizeram a carteira; os erros foram pequenos e rápidos</figcaption>
<figcaption class="s">As 10 maiores e as 10 menores contribuições acumuladas (soma de peso × retorno do trimestre, em pontos percentuais), com o que aconteceu com o lucro, o múltiplo e o ROIC durante o período em carteira.</figcaption>
<div class="attr" id="c8"></div>
<div class="sowhat"><b>E daí</b><span>A assimetria é o que a regra entrega. O pior erro da Top 20 (Boeing, 1 trimestre no começo de 2020) custou 5 pontos; Meta, em 36 trimestres, rendeu 20. As piores posições quase sempre saíram rápido, porque o modelo vende quando o ROIC ou o crescimento caem. Os grandes ganhos vieram de empresas mantidas por anos com o ROIC subindo (NVIDIA de 37% para 133%, Applied Materials de 15% para 44%). Um vetador humano que tirasse "as caras" teria vendido justamente essas.</span></div>
</figure>

<figure><figcaption class="t">Nove em cada dez grandes vencedoras não estavam na Top 20 na hora certa. O motivo mais comum: o crescimento estava parado</figcaption>
<figcaption class="s">Ações entre as 10% de maior retorno nos 3 anos seguintes, em cada trimestre: por que a Top 20 não as tinha naquele momento. À direita, o que essas ações tinham antes e o que fizeram depois (medianas).</figcaption>
<div id="c9" style="max-width:560px"></div><div id="c9b" class="tablebox" style="margin-top:12px"></div>
<div class="sowhat"><b>E daí</b><span>A Top 20 tinha {pc(miss['pct_t20'], 0)} das grandes vencedoras, contra {pc(miss['base_t20'], 1)} se escolhesse ao acaso: {nm2(miss['pct_t20'] / miss['base_t20'], 1)} vez o acaso. A OoL tinha {pc(miss['pct_ool'], 0)}. As que ficaram de fora por "crescimento abaixo de 15%" tinham ROIC alto (mediana {pc(miss['por_motivo']['Crescimento < 15%']['roic0'], 0)}) e o crescimento voltou a {pc(miss['por_motivo']['Crescimento < 15%']['g3'], 0)} ao ano. Parece um padrão a explorar. <b>Testamos, e não é:</b> o grupo inteiro de empresas com ROIC ≥ 20% e crescimento parado rendeu {pp(d['pausa']['ROIC ≥ 20% e crescimento < 15%']['4'])} ao ano sobre o S&amp;P, contra {pp(d['pausa']['OoL']['4'])} da OoL. As vencedoras desse grupo só são óbvias olhando para trás.</span></div>
</figure>

<figure><figcaption class="t">As 25 maiores altas de setembro de 2016 a setembro de 2026, e o que o modelo viu nelas</figcaption>
<figcaption class="s">Entre as ações do S&amp;P 500 em setembro de 2016: retorno total em 10 anos, motivo pelo qual não estavam na Top 20 naquela data, e em quantos trimestres apareceram depois na Top 20 e na OoL.</figcaption>
<div id="c10" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>O modelo perdeu a largada de quase todas, mas pegou a maior parte da corrida. NVIDIA não entrou em 2016 (o lucro tinha crescido −4% ao ano), mas esteve na Top 20 em 17 trimestres e na OoL em 28. O mesmo vale para Lam, KLA, Seagate e Applied Materials. As que o modelo nunca pegou são, em geral, cíclicas que ele exclui de propósito (refino) ou empresas com dados insuficientes (Eli Lilly). <b>A oportunidade do julgamento humano está aqui:</b> entrar antes numa empresa de ROIC alto cujo crescimento está voltando. Mas, como mostrou o gráfico anterior, isso exige acertar caso a caso, porque o padrão não funciona em grupo.</span></div>
</figure>

<h2 class="chap" style="margin-top:56px">5. Quanto vale o julgamento</h2>
<figure><figcaption class="t">Se você soubesse o futuro do negócio, ganharia pouco; se soubesse o futuro do preço, muito</figcaption>
<figcaption class="s">Ganho anual sobre a carteira original ao vetar, em cada rebalanceamento, as 20% das posições com o pior resultado futuro em cada critério (o veto vale por 4 trimestres). "Aleatório" = vetar 20% ao acaso (média de 30 sorteios).</figcaption>
<div class="legend" id="lg11"></div><div id="c11"></div>
<div class="sowhat"><b>E daí</b><span>É o resultado mais importante do relatório. Um oráculo que soubesse qual empresa ia perder ROIC no ano seguinte e a vetasse <b>não ganharia nada</b>. Mesmo sabendo o lucro dos 3 anos seguintes, o ganho fica entre {pp(min(eps3_gain))} e {pp(max(eps3_gain))} ao ano. Só quem soubesse o re-rating do ano seguinte ganharia muito ({pp(min(rr_gain), 0)} a {pp(max(rr_gain), 0)}), mas re-rating é humor de mercado, não análise de negócio. Nas Excepcionais, qualquer veto destrói valor: a carteira depende de poucas vencedoras.</span></div>
</figure>

<figure><figcaption class="t">Mesmo um analista bom ganharia, na melhor hipótese, uns 2 a 3 pontos ao ano</figcaption>
<figcaption class="s">Ganho anual por grau de habilidade: a correlação entre o julgamento do analista e o crescimento real do lucro nos 3 anos seguintes (0 = acaso, 1 = oráculo). Veto de 20%, média de 40 simulações.</figcaption>
<div class="legend" id="lg12"></div><div id="c12"></div>
<div class="sowhat"><b>E daí</b><span>Uma correlação de 0,3 com o lucro futuro já é o nível de um analista muito bom. Ela renderia perto de {pp(dict(d['skill']['Top 20'])[0.3])} ao ano na Top 20, antes de considerar o custo dos erros de comportamento: vender na hora errada, se apaixonar por uma tese. Não é zero, mas é pouco perto dos 4 a 6 pontos que a regra já entrega sobre o S&amp;P.</span></div>
</figure>

<figure><figcaption class="t">Não há um padrão dentro do padrão: nenhum sinal sobreviveu ao teste fora da amostra</figcaption>
<figcaption class="s">Dentro das ações OoL: o sinal ordena o excesso de retorno do ano seguinte? Correlação média e estatística t, descoberta em 2012–2018 e confirmação em 2019–2026. Para passar: |t| &gt; 2,9 na descoberta (correção para 12 testes) e o mesmo sinal com t &gt; 1,5 na confirmação.</figcaption>
<div id="c13" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>Nenhum dos 12 sinais passou. O mais próximo foi "ROIC marginal muito acima do ROIC médio" (pior retorno nos dois períodos, t de {nm2(next(r for r in sig if r['sinal'].startswith('ROIC marginal'))['t_desc'], 1)} e {nm2(next(r for r in sig if r['sinal'].startswith('ROIC marginal'))['t_conf'], 1)}). Ele captura lucros no pico de um ciclo, o que faz sentido econômico, mas não chega ao rigor estatístico. Dentro da OoL, a classe já é o sinal.</span></div>
</figure>

<section class="verdict"><h2>O veredito: regra como base, julgamento como freio, nunca como acelerador</h2>
<div class="vgrid">
 <div><span class="tag" style="--c:var(--teal)">Siga</span><h4>A regra determinística como espinha</h4><p>O ganho vem de ficar com empresas cujo ROIC persiste enquanto o mercado reprecifica. Isso pede disciplina, não previsão. Nenhum sinal adicional dentro das classes passou no teste.</p></div>
 <div><span class="tag" style="--c:var(--oxford)">Use o julgamento</span><h4>Como veto estreito, com checklist</h4><p>Vete apenas por razões que o modelo não enxerga: lucro no pico de um ciclo (ROIC marginal muito acima do médio), risco de evento (Boeing 2019), fraude ou contabilidade. No máximo 2 ou 3 das 20 ações.</p></div>
 <div><span class="tag" style="--c:var(--claret)">Não faça</span><h4>Discordar por projeção de crescimento ou por "está caro"</h4><p>Crescimento passado não prevê o futuro, e o múltiplo das melhores sobe por anos. Os maiores ganhos (NVIDIA, Meta, Applied Materials) teriam sido vetados por "caros".</p></div>
 <div><span class="tag" style="--c:var(--wheat)">Meça</span><h4>Registre cada veto e compare em 12 trimestres</h4><p>Mantenha uma carteira-sombra da regra pura. Se depois de 3 anos os vetos não tiverem somado, volte à regra. É o único jeito de saber se o seu julgamento tem a correlação que justifica o esforço.</p></div>
</div></section>

<p class="method" style="margin-top:36px"><b>Método.</b> Painel point-in-time do S&amp;P 500 ({d['periodo'][0]} a {d['periodo'][1]}, trimestral): ROIC triangulado e crescimento pela mediana de 5 anos, só com balanços arquivados até a data. Decomposição: log(retorno total) = log(EPS final ÷ inicial) + log(P/L final ÷ inicial) + resíduo (dividendos), com o EPS anual mais recente conhecido em cada data. Carteiras com a regra registrada no PROTOCOLO (Top 20 e Excepcionais pela raiz do valor de mercado; OoL, High ROIC e High Growth com peso igual). Correlações de Spearman por trimestre, com estatística t ajustada para a sobreposição das janelas. O veto oráculo usa informação futura de propósito, para medir o teto do que o julgamento poderia render. Limitações: um único período, dominado por megacaps de tecnologia; o EPS anual chega com até 15 meses de defasagem; posições sem 3 anos de futuro ficam fora da decomposição de 3 anos. Código: <code>relatorio/attrib.py</code>.</p>
</div>
'''

js = r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const D=__DATA__;
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const P=(x,n=1)=>x==null?'—':(x*100).toFixed(n).replace('.',',')+'%';
const PP=(x,n=1)=>x==null?'—':((x>=0?'+':'')+(x*100).toFixed(n)).replace('.',',')+' p.p.';
function svgBox(id,w,h){const el=d3.select('#'+id);el.selectAll('*').remove();return el.append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img');}
function legend(id,items){document.getElementById(id).innerHTML=items.map(([n,c])=>`<span><i style="--c:${c};height:10px"></i>${n}</span>`).join('');}
function stacked(id,rows,keys,cols){const W=1000,rh=34,m={l:200,r:70,t:10,b:28},H=m.t+m.b+rows.length*rh;const s=svgBox(id,W,H);
 let lo=0,hi=0;rows.forEach(r=>{let p=0,n=0;keys.forEach(k=>{r[k]>0?p+=r[k]:n+=r[k]});hi=Math.max(hi,p);lo=Math.min(lo,n)});
 const x=d3.scaleLinear().domain([Math.min(lo,0)*1.1,hi*1.08]).range([m.l,W-m.r]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(8).tickFormat(v=>P(v,0)).tickSize(-(H-m.t-m.b)));
 rows.forEach((r,i)=>{const y=m.t+i*rh;let p=0,n=0;s.append('text').attr('x',m.l-8).attr('y',y+rh/2+5).attr('text-anchor','end').style('font-size','14px').style('font-weight',r.bold?700:400).text(r.nome);
  keys.forEach((k,j)=>{const v=r[k];const a=v>=0?p:n+v;v>=0?p+=v:n+=v;s.append('rect').attr('x',x(a)).attr('y',y+6).attr('width',Math.abs(x(a+Math.abs(v))-x(a))).attr('height',rh-12).attr('fill',cols[j]);});
  s.append('text').attr('class','num').attr('x',x(p)+6).attr('y',y+rh/2+5).text(P(r.tot));});
 s.append('line').attr('x1',x(0)).attr('x2',x(0)).attr('y1',m.t).attr('y2',H-m.b).attr('stroke',css('--ink'));}
function bars(id,cats,series,cols,opt={}){const W=1000,H=opt.h||300,m={l:64,r:16,t:16,b:opt.b||44};const s=svgBox(id,W,H);
 const all=series.flat().filter(v=>v!=null);const x0=d3.scaleBand().domain(cats).range([m.l,W-m.r]).padding(.25);const x1=d3.scaleBand().domain(d3.range(series.length)).range([0,x0.bandwidth()]).padding(.08);
 const y=d3.scaleLinear().domain([Math.min(0,d3.min(all))*1.15,Math.max(0,d3.max(all))*1.15]).range([H-m.b,m.t]).nice();
 s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(opt.fmt||(v=>P(v,0))).tickSize(-(W-m.l-m.r)));
 s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x0).tickSize(0)).selectAll('text').style('font-size','13px').attr('dy','1.2em');
 series.forEach((ser,j)=>ser.forEach((v,i)=>{if(v==null)return;s.append('rect').attr('x',x0(cats[i])+x1(j)).attr('width',x1.bandwidth()).attr('y',y(Math.max(0,v))).attr('height',Math.abs(y(v)-y(0))).attr('fill',cols[j]);
  if(opt.labels)s.append('text').attr('class','num').attr('x',x0(cats[i])+x1(j)+x1.bandwidth()/2).attr('y',v>=0?y(v)-4:y(v)+13).attr('text-anchor','middle').style('font-size','11px').text((opt.lf||PP)(v,1).replace(' p.p.',''));}));
 s.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0)).attr('stroke',css('--ink'));}
function table(id,head,rows,cls){const el=document.getElementById(id);el.innerHTML='<table><thead><tr>'+head.map((h,i)=>`<th class="${i==0?'l':''}">${h}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map((c,i)=>`<td class="${(i==0||/^[A-Za-zÀ-ú]/.test(String(c)))?'l':'n'}">${c}</td>`).join('')+'</tr>').join('')+'</tbody></table>';}
function draw(){
 const C=[css('--oxford'),css('--mandarin'),css('--teal')];
 legend('lg1',[['Crescimento do EPS',C[0]],['Re-rating',C[1]],['Dividendos',C[2]]]);
 stacked('c1',D.decomp['12'].map((r,i)=>({...r,nome:r.nome.replace(' (S&P, peso igual)',''),bold:i==0})),['eps','rr','div'],C);
 legend('lg2',[['Lucro (EPS)',C[0]],['Múltiplo (P/L)',C[1]],['Dividendos',C[2]]]);
 const vd=['4','12','20'].map(h=>({nome:{4:'1 ano',12:'3 anos',20:'5 anos'}[h],eps:D.var_decomp[h].le,rr:D.var_decomp[h].lp,div:Math.max(0,D.var_decomp[h].ld),tot:1}));
 stacked('c2',vd,['eps','rr','div'],C);
 const L=D.roic_trans.labels,M=D.roic_trans.m['12'];
 const el=document.getElementById('c3');el.innerHTML='<table class="heat"><thead><tr><th class="l">ROIC hoje ↓ / em 3 anos →</th>'+L.map(l=>`<th>${l}</th>`).join('')+'</tr></thead><tbody>'+M.map((r,i)=>`<tr><td class="l">${L[i]}</td>`+r.map((v,j)=>`<td class="n" style="background:color-mix(in srgb, var(--oxford) ${Math.round(v*80)}%, transparent);${v>.5?'color:var(--paper);font-weight:700':''}">${P(v,0)}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
 table('c3b',['ROIC mediano das posições','Na compra','1 ano depois','3 anos','5 anos','Ainda ≥ 12% em 3 anos'],Object.entries(D.roic_port).map(([k,v])=>[k,P(v[0]),P(v[1]),P(v[2]),P(v[3]),P(v[4],0)]));
 const q=D.growth['12'].quint;legend('lg4',[['Previsto (mediana dos 5 anos anteriores)',css('--slate')],['Realizado nos 3 anos seguintes',C[0]]]);
 bars('c4',['1º quinto','2º','3º','4º','5º quinto'],[q.map(r=>r[0]),q.map(r=>r[1])],[css('--slate'),C[0]],{labels:true,lf:(v)=>P(v,0)});
 table('c4b',['Carteira','Crescimento previsto','Realizado em 3 anos','Realizado em 5 anos'],['Top 20','OoL','High ROIC','High Growth','Excepcionais'].map(k=>[k,P(D.growth['12'][k][0]),P(D.growth['12'][k][1]),P(D.growth['20'][k][1])]));
 const rq=['4','12','20'].map(h=>D.rerating[h].quint.map(r=>r[1]));legend('lg5',[['1 ano',css('--slate')],['3 anos',C[1]],['5 anos',css('--claret')]]);
 bars('c5',['Muito acima do justo','Acima','Perto','Abaixo','Muito abaixo do justo'],rq,[css('--slate'),C[1],css('--claret')],{fmt:v=>(v>=0?'+':'')+(v*100).toFixed(0)+'%',labels:true,lf:v=>((v>=0?'+':'')+(Math.expm1(v)*100).toFixed(0)+'%')});
 legend('lg6',[['1 ano',css('--slate')],['3 anos',C[0]]]);
 bars('c6',['Menor retorno esperado','2º','3º','4º','Maior retorno esperado'],[D.exp_ret['4'].quint_qual,D.exp_ret['12'].quint_qual],[css('--slate'),C[0]],{labels:true});
 const ic=D.exp_ret;table('c6b',['Ordenar as de qualidade por…','Correlação com o excesso em 1 ano','% dos trimestres positiva','Correlação em 3 anos','% positiva'],Object.keys(ic['4'].ic_qual).map(k=>[k,ic['4'].ic_qual[k].ic.toFixed(3).replace('.',','),P(ic['4'].ic_qual[k].pos,0),ic['12'].ic_qual[k].ic.toFixed(3).replace('.',','),P(ic['12'].ic_qual[k].pos,0)]));
 const f=D.fm;legend('lg7',[['1 ano',css('--slate')],['3 anos',C[0]]]);
 const ks=['ante','eps','roic','tudo'];bars('c7',['Conhecido na compra (ROIC, crescimento, P/L, retorno esperado)','Lucro realizado','Mudança do ROIC','Tudo junto'],[ks.map(k=>f['4'].r2[k]),ks.map(k=>f['12'].r2[k])],[css('--slate'),C[0]],{labels:true,lf:v=>P(v,0),b:60});
 const box=document.getElementById('c8');box.innerHTML='';const colsC={'Top 20':css('--oxford'),'OoL':css('--teal'),'Excepcionais':css('--claret')};
 Object.entries(D.contrib).forEach(([k,v])=>{const best=v.slice(10).reverse(),worst=v.slice(0,10);const row=r=>`<tr><td class="l">${r.t}</td><td class="n">${(r.contrib*100).toFixed(1).replace('.',',')}</td><td class="n">${r.tri}</td><td class="n">${P(r.eps,0)}</td><td class="n">${P(r.rr,0)}</td><td class="n">${P(r.roic0,0)} → ${P(r.roic1,0)}</td></tr>`;
  box.insertAdjacentHTML('beforeend',`<div style="--c:${colsC[k]}"><h4>${k}</h4><div class="tablebox"><table><thead><tr><th class="l">Ação</th><th>Pontos</th><th>Trim.</th><th>EPS a.a.</th><th>P/L a.a.</th><th>ROIC</th></tr></thead><tbody>${best.map(row).join('')}<tr><td colspan="6" class="l" style="color:var(--ink2);font-size:12px">… as 10 piores</td></tr>${worst.map(row).join('')}</tbody></table></div></div>`);});
 const why=Object.entries(D.misses.why).sort((a,b)=>b[1]-a[1]);
 const W=520,H=40+why.length*38,s=svgBox('c9',W,H),x=d3.scaleLinear().domain([0,d3.max(why,d=>d[1])*1.25]).range([0,W-200]);
 why.forEach(([k,v],i)=>{const y=10+i*38;s.append('text').attr('x',0).attr('y',y+12).style('font-size','13px').text(k);s.append('rect').attr('x',0).attr('y',y+18).attr('height',12).attr('width',x(v)).attr('fill',css('--claret'));s.append('text').attr('class','num').attr('x',x(v)+6).attr('y',y+29).text(P(v,0));});
 const pm=D.misses.por_motivo;table('c9b',['Motivo','ROIC antes → 3 anos depois','Crescimento antes → depois','Excesso a.a.'],why.map(([k])=>[k,`${P(pm[k].roic0,0)} → ${P(pm[k].roic3,0)}`,`${P(pm[k].g0,0)} → ${P(pm[k].g3,0)}`,P(pm[k].ex,0)]));
 table('c10',['Empresa','Multiplicou por','Por que não estava em 2016','ROIC 2016 → hoje','Crescimento em 2016','EPS a.a. em 10 anos','Trimestres na Top 20','Na OoL'],D.misses.nomes.map(r=>[`${r.nome} (${r.t})`,r.tr10.toFixed(1).replace('.',',')+'×',r.why,`${P(r.roic0,0)} → ${P(r.roic_hoje,0)}`,P(r.g0,0),P(r.eps10,0),r.tri_t20,r.tri_ool]));
 const ok=['ROIC em 1 ano','ROIC em 3 anos','EPS em 1 ano','EPS em 3 anos','Re-rating em 1 ano','Retorno total em 1 ano','Aleatório'];
 const ports=['Top 20','OoL','High ROIC','High Growth','Excepcionais'];const pc5=[css('--oxford'),css('--teal'),css('--velvet'),css('--mandarin'),css('--claret')];
 legend('lg11',ports.map((p,i)=>[p,pc5[i]]));
 bars('c11',['ROIC 1 ano','ROIC 3 anos','EPS 1 ano','EPS 3 anos','Re-rating 1 ano','Retorno total 1 ano','Aleatório'],ports.map(p=>ok.map(k=>D.oracle[p][k])),pc5,{h:340});
 legend('lg12',[['Top 20',css('--oxford')],['OoL',css('--teal')]]);
 {const W=1000,H=300,m={l:64,r:20,t:14,b:40};const s=svgBox('c12',W,H);const all=Object.values(D.skill).flat().map(r=>r[1]);
  const x=d3.scaleLinear().domain([0,1]).range([m.l,W-m.r]),y=d3.scaleLinear().domain([Math.min(0,d3.min(all))*1.2,d3.max(all)*1.2]).range([H-m.b,m.t]).nice();
  s.append('g').attr('class','ax').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(v=>PP(v,0)).tickSize(-(W-m.l-m.r)));
  s.append('g').attr('class','ax').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(10).tickFormat(v=>v.toFixed(1).replace('.',',')));
  s.append('text').attr('x',W-m.r).attr('y',H-4).attr('text-anchor','end').style('font-size','12px').style('fill',css('--ink2')).text('correlação do julgamento com o lucro futuro →');
  [['Top 20',css('--oxford')],['OoL',css('--teal')]].forEach(([k,c])=>{const pts=D.skill[k];s.append('path').attr('d',d3.line().x(r=>x(r[0])).y(r=>y(r[1]))(pts)).attr('fill','none').attr('stroke',c).attr('stroke-width',2.5);
   pts.forEach(r=>s.append('circle').attr('cx',x(r[0])).attr('cy',y(r[1])).attr('r',4).attr('fill',c));});
  s.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(0)).attr('y2',y(0)).attr('stroke',css('--ink'));}
 const T=v=>v==null?'—':v.toFixed(2).replace('.',',');
 table('c13',['Sinal (dentro das OoL)','Correlação 2012–18','t','Correlação 2019–26','t','Passou?'],D.sinais.filter(r=>r.ic_desc!=null).map(r=>[r.sinal,T(r.ic_desc),T(r.t_desc),T(r.ic_conf),T(r.t_conf),D.sinais_ok.includes(r.sinal)?'sim':'não']));
}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>O que o modelo acerta</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__DATA__', json.dumps(d, ensure_ascii=False))
(ROOT / 'o_que_o_modelo_acerta.html').write_text(html)
print('ok', len(html))
