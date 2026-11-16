"""Relatório FT do ramo "ROIC descontado e setores estáveis" (relatorio/rerating_estavel.html), a partir de dados_rerating.json."""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_rerating.json').read_text())
src = (ROOT / 'qualidade_que_compoe.html').read_text()
css = src[src.index('<link'):src.index('</style>') + len('</style>')]
att = (ROOT / 'o_que_o_modelo_acerta.html').read_text()
helpers = att[att.index('const P=(x,n=1)'):att.index('function draw(){')].replace('m={l:200,', 'm={l:300,')
line = src[src.index('function lineChart('):src.index('function drawFull(){')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
T = d['carteiras']; DEC = d['decomp']
a3 = {r['nome']: r for r in d['a2']['12']}
e = d['b1_erro']
best_dsc = T['ROIC alto descontado']

LIT = [
    ('Brown, Hagerman, Griffin e Zmijewski (1987)', 'No lucro dos próximos 1 a 4 trimestres, os analistas erram menos que modelos de série temporal: 28,7% contra 33,0% de erro médio. A vantagem é pequena, e em cerca de 40% dos casos o modelo empata ou ganha.',
     'https://www.econbiz.de/Record/security-analyst-superiority-relative-to-univariate-time-series-models-in-forecasting-quarterly-earnings/10005492625'),
    ('Chan, Karceski e Lakonishok (2003)', 'Não há persistência no crescimento de longo prazo além do acaso. A previsão de longo prazo (LTG) do consenso é otimista (14,5% previstos contra cerca de 9% realizados) e quase não acrescenta informação.',
     'https://www.nber.org/papers/w8282'),
    ('La Porta (1996)', 'As ações com as menores previsões de crescimento de longo prazo rendem mais que as com as maiores: as expectativas são extremas demais.',
     'https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:5:p:1715-42'),
    ('Bordalo, Gennaioli, La Porta e Shleifer (2019)', 'Com mais 20 anos de dados, o resultado se mantém. Os analistas extrapolam o crescimento passado (expectativa "diagnóstica"), as previsões altas são revisadas para baixo e as ações delas rendem menos.',
     'https://www.nber.org/papers/w23863'),
    ('Richardson, Teoh e Wysocki (2004)', 'As previsões começam otimistas e vão sendo rebaixadas ao longo do ano até um número que a empresa consegue bater ("walk-down").',
     'https://ideas.repec.org/a/wly/coacre/v21y2004i4p885-924.html'),
    ('Hou, van Dijk e Zhang (2012) e réplicas', 'Um modelo mecânico entre empresas tem menos viés e mais cobertura que os analistas; em acurácia os analistas ainda ganham no curto prazo, e um passeio aleatório às vezes bate o modelo.',
     'https://econpapers.repec.org/RePEc:eee:jaecon:v:53:y:2012:i:3:p:504-526'),
]

body = f'''
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Ramo de análise · S&amp;P 500, 2011 a 2026</span></div>
<div class="kicker">ROIC, re-rating e previsibilidade</div>
<h1>Previsível já vem com preço: o ganho está no ROIC que o mercado desconta</h1>
<p class="deck">Comprar empresas de ROIC alto negociadas bem abaixo do P/E justo rendeu o mesmo que a Top 20, sem filtro de crescimento. Restringir às empresas e aos setores de lucro "redondinho" piorou tudo: o mercado já paga por essa previsibilidade.</p>
<div class="byline">S&amp;P 500 point-in-time, trimestral, raiz do valor de mercado com teto de 10% · pré-registrado no PROTOCOLO em 16/11/2026, antes de rodar</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra no filtro (ROIC ≥ 12%) e no P/E justo, que define o desconto. Usamos o ROIC triangulado oficial; financeiras usam ROE. Backtest, sem custos; não é recomendação de investimento.</p>
<div class="big">
 <div><b>{pc(best_dsc['cagr'])}</b><span>ao ano na "ROIC alto descontado", contra {pc(T['Top 20 (OoL)']['cagr'])} da Top 20 e {pc(T['S&P 500']['cagr'])} do S&amp;P</span></div>
 <div><b>{pc(T['Descontado, setores estáveis']['cagr'])}</b><span>a mesma regra só nos setores estáveis: pior</span></div>
 <div><b>{pc(T['Descontado, empresas estáveis']['cagr'])}</b><span>só nas empresas de crescimento estável: abaixo do S&amp;P</span></div>
 <div><b>{pc(a3['Constante de 8%']['mae'], 0)}</b><span>de erro mediano chutando 8% para todos, contra {pc(a3['Mediana de 5 anos (o nosso)']['mae'], 0)} da nossa mediana (3 anos)</span></div>
</div>

<div class="cols"><div class="prose">
<p>A atribuição anterior deixou uma pista forte: o ROIC alto persiste e o P/L anda na direção do P/E justo, fechando cerca de 30% da distância em três anos. Se isso é verdade, a regra mais pura possível seria comprar ROIC alto com o maior desconto em relação ao múltiplo justo, sem nenhum filtro de crescimento. É a ideia de Joel Greenblatt, mas medida pelo múltiplo justo em vez de um ranking de lucro sobre preço.</p>
<p>Funcionou: {pc(best_dsc['cagr'])} ao ano, com {pc(best_dsc['w3'], 0)} das janelas de 3 anos acima do S&amp;P. Mas o retorno chega do jeito esperado, inteiro pelo re-rating. O lucro dessas empresas <i>encolheu</i> {pc(-DEC['ROIC alto descontado']['12']['eps'])} ao ano em 3 anos, e o múltiplo subiu {pc(DEC['ROIC alto descontado']['12']['rr'])} ao ano.</p>
<p>A segunda hipótese era de que, onde o lucro cresce de forma previsível, bastaria acertar o re-rating. Aqui a resposta é não. Nas empresas de crescimento estável, o passado de fato prevê melhor (erro de {pc(e['Empresas estáveis']['mae'], 0)} contra {pc(e['Demais empresas']['mae'], 0)}). Só que elas já negociam perto do P/E justo: o desconto médio na compra é de {pc(DEC['Descontado, empresas estáveis']['12']['gap'] if False else None) if False else f"{DEC['Descontado, empresas estáveis']['12']['gap']:.2f}".replace('.', ',')} em log, contra {f"{DEC['ROIC alto descontado']['12']['gap']:.2f}".replace('.', ',')} na regra sem filtro. Sem desconto, não há re-rating para colher.</p>
</div>
<aside class="box"><h3>As respostas</h3><ol>
<li><b>O sell-side prevê o lucro?</b> No próximo ano, um pouco melhor que modelos simples. No longo prazo, não, e é otimista.</li>
<li><b>A nossa mediana prevê?</b> Não: chutar 8% para todos erra menos.</li>
<li><b>Há setores "redondinhos"?</b> Poucos, e a lista muda de um período para o outro.</li>
<li><b>ROIC alto descontado funciona?</b> Sim, igual à Top 20, só pelo re-rating.</li>
<li><b>E nos setores estáveis?</b> Pior: previsível já vem com preço.</li></ol></aside></div>

<h2 class="chap" style="margin-top:56px">A. O sell-side prevê o crescimento melhor que o passado?</h2>
<figure><figcaption class="t">A literatura: o analista ganha no curto prazo por pouco e perde no longo prazo pelo otimismo</figcaption>
<figcaption class="s">Os principais estudos sobre a acurácia das previsões de lucro dos analistas.</figcaption>
<div id="lit" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>A V2 usava o consenso de EPS de 2026 a 2029. A previsão do ano corrente e a do seguinte têm informação real: a empresa já reportou parte do ano e dá guidance. As de 2028 e 2029 se comportam como a previsão de longo prazo, otimistas e com pouca informação. Não temos histórico do consenso (só no plano Enterprise do Wisesheets ou no I/B/E/S), então não dá para testar a V2 diretamente. A literatura sugere usar o consenso no máximo para o próximo ano, com desconto para o otimismo.</span></div>
</figure>
<figure><figcaption class="t">Nos nossos dados, o melhor preditor do lucro é quase não prever</figcaption>
<figcaption class="s">Crescimento anual do EPS em 1 e 3 anos: correlação de ordem com o realizado (média por trimestre), erro absoluto mediano e viés (realizado menos previsto). S&amp;P 500 point-in-time.</figcaption>
<div id="a2" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>Usar o próprio passado da empresa dá correlação <i>negativa</i> com o futuro: quem cresceu muito cresce menos, e vice-versa. A mediana do setor erra menos que a da empresa, e uma constante de 8% erra menos que todas. Isso não destrói o modelo, porque ele usa o crescimento como filtro de qualidade e o g do P/E justo é conservador (7% a 3,5%). Mas confirma a literatura: crescimento alto não persiste. Se o consenso acerta melhor no próximo ano, é porque já tem o ano corrente na mão, não por saber prever.</span></div>
</figure>

<h2 class="chap" style="margin-top:56px">B. Existem setores de lucro "redondinho"?</h2>
<figure><figcaption class="t">A previsibilidade por setor existe, mas não se repete de um período para o outro</figcaption>
<figcaption class="s">Por grupo (subindústria com 5 ou mais empresas, senão o setor): correlação entre o crescimento previsto pela mediana e o realizado em 3 anos, |zGrowth| mediano e proporção de anos com crescimento entre 0% e 25%. Em 2012–2018 e em 2019–2026.</figcaption>
<div id="b1" class="tablebox"></div>
<div class="sowhat"><b>E daí</b><span>Bancos regionais, químicos especiais e o varejo de consumo básico são os mais previsíveis no período todo. Mas a correlação entre a previsibilidade de um grupo em 2012–2018 e em 2019–2026 é de só {f"{d['b1_persist']['corr_ic']:.2f}".replace('.', ',')}: a lista dos "redondinhos" de um período não é a do outro. A régua pré-registrada (|zGrowth| baixo no setor) não separou quem é mais previsível: a correlação foi parecida nos três terços.</span></div>
</figure>
<div id="terco" class="tablebox" style="margin-top:8px"></div>

<h2 class="chap" style="margin-top:56px">C. As carteiras</h2>
<figure><figcaption class="t">ROIC alto descontado empata com a Top 20; os filtros de estabilidade só tiram retorno</figcaption>
<figcaption class="s">Retorno acumulado (base 1) das carteiras pré-registradas, contra o S&amp;P 500, a Top 20 e a JG+G.</figcaption>
<div class="legend" id="lgnav"></div><div id="nav"></div>
<div id="tab" class="tablebox" style="margin-top:12px"></div>
<div class="src">Peso pela raiz do valor de mercado com teto de 10%; "(peso igual)" é o controle. Janelas móveis mensais contra o S&amp;P 500. Os 9 comparativos obrigatórios estão em relatorio/rerating_tabela.md.</div>
<div class="sowhat"><b>E daí</b><span>A "ROIC alto descontado" ({pc(best_dsc['cagr'])}) ficou colada na Top 20 ({pc(T['Top 20 (OoL)']['cagr'])}) e na JG+G ({pc(T['JG+G']['cagr'])}). As três são, no fundo, a mesma aposta: ROIC alto com preço baixo. Todas as versões com filtro de estabilidade renderam menos, e a de empresas estáveis ficou abaixo do S&amp;P ({pc(T['Descontado, empresas estáveis']['cagr'])}, com só {T['Descontado, empresas estáveis']['n']:.0f} ações em média).</span></div>
</figure>

<figure><figcaption class="t">O re-rating previsto aparece; nas empresas estáveis, não havia desconto para fechar</figcaption>
<figcaption class="s">Retorno anual das posições em 3 anos, decomposto em crescimento do EPS, re-rating e dividendos. Entre parênteses, o desconto médio na compra (log do P/E justo ÷ P/L).</figcaption>
<div class="legend" id="lgdec"></div><div id="dec"></div>
<div class="sowhat"><b>E daí</b><span>Quanto maior o desconto na compra, maior o re-rating depois. Na regra sem filtro, o desconto médio é de {f"{DEC['ROIC alto descontado']['12']['gap']:.2f}".replace('.', ',')} e o múltiplo subiu {pc(DEC['ROIC alto descontado']['12']['rr'])} ao ano. Nas empresas estáveis, o desconto é de {f"{DEC['Descontado, empresas estáveis']['12']['gap']:.2f}".replace('.', ',')} e o re-rating foi de zero: o retorno ficou só com o lucro ({pc(DEC['Descontado, empresas estáveis']['12']['eps'])}) e os dividendos. Um aviso: parte do "re-rating" é mecânica. O P/L usa o lucro do último ano, e quando o lucro cai, o P/L sobe. As empresas mais descontadas costumam estar num ano ruim de lucro.</span></div>
</figure>

<figure><figcaption class="t">E o PEG de Peter Lynch? Com o filtro de ROIC, ele também funciona</figcaption>
<figcaption class="s">Entre as ações de qualidade (ROIC ≥ 12% e crescimento ≥ 15%), as 20 de menor P/L ÷ crescimento.</figcaption>
<div class="sowhat"><b>E daí</b><span>O PEG rendeu {pc(T['PEG (contraste)']['cagr'])} ao ano ({pc(T['PEG (contraste)']['w3'], 0)} das janelas de 3 anos acima do S&amp;P); sem a NVIDIA, {pc(d['sem_nvda']['sem'])}. Foi a maior das seis, mas a diferença para a Top 20 (+{(T['PEG (contraste)']['cagr'] - T['Top 20 (OoL)']['cagr']) * 100:.1f} p.p.) está dentro do ruído. E este PEG não é o de Lynch puro: ele só olha empresas com ROIC acima de 12%, o filtro que você notou faltar no PEG. Sem esse filtro, o PEG compraria crescimento barato de negócios ruins. A lição é a mesma das outras carteiras: com o ROIC garantido, qualquer medida razoável de "barato" funciona.</span></div>
</figure>

<section class="verdict"><h2>O veredito</h2><div class="vgrid">
<div><span class="tag" style="--c:var(--teal)">Confirmado</span><h4>ROIC alto com preço baixo</h4><p>A versão "múltiplo justo" da ideia de Greenblatt funciona tão bem quanto a Top 20, sem precisar prever crescimento. O ganho vem do re-rating, como esperado.</p></div>
<div><span class="tag" style="--c:var(--claret)">Rejeitado</span><h4>Setores e empresas "redondinhos"</h4><p>Onde o lucro é previsível, o mercado já paga por isso. Não há desconto e não há re-rating. A previsibilidade por setor também não persiste.</p></div>
<div><span class="tag" style="--c:var(--oxford)">Sell-side</span><h4>Só para o próximo ano</h4><p>O consenso ganha no curto prazo porque já conhece parte do ano; de 2 anos em diante é otimista. A V2 com o consenso de 2028–2029 herdaria esse otimismo.</p></div>
<div><span class="tag" style="--c:var(--wheat)">Para decidir</span><h4>Simplificar a regra?</h4><p>A "ROIC alto descontado" é mais simples que a Top 20 (sem crescimento, sem zGrowth) e rende o mesmo. Status: exploratória, porque foi proposta depois da atribuição.</p></div>
</div></section>
<p class="method" style="margin-top:28px"><b>Método.</b> Pré-registro no PROTOCOLO (16/11/2026), antes de rodar. Desconto = log(P/E justo ÷ P/L), com P/E justo do modelo (ROIC limitado a 100%, g pelo ranking do crescimento). Setor estável = terço de grupos com a menor mediana de |zGrowth| na data; empresa estável = |zGrowth| &lt; 0,5 e crescimento entre 5% e 30%. Preditores medidos só com dados até a data. Código: <code>relatorio/ramo_rerating.py</code>.</p>
</div>'''

js = r'''
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const D=__DATA__;const LIT=__LIT__;
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
''' + helpers + line + r'''
function draw(){
 const T=v=>v==null?'—':v.toFixed(2).replace('.',',');
 document.getElementById('lit').innerHTML='<table><thead><tr><th class="l">Estudo</th><th class="l">O que encontrou</th></tr></thead><tbody>'+LIT.map(r=>`<tr><td class="l" style="white-space:normal;min-width:180px"><a href="${r[2]}" target="_blank" rel="noopener">${r[0]}</a></td><td class="l" style="white-space:normal">${r[1]}</td></tr>`).join('')+'</tbody></table>';
 const a1=D.a2['4'],a3=D.a2['12'];
 table('a2',['Preditor','Correlação 1 ano','Erro mediano 1 ano','Viés 1 ano','Correlação 3 anos','Erro mediano 3 anos','Viés 3 anos'],a1.map((r,i)=>[r.nome,r.ic==null?'—':T(r.ic),P(r.mae,0),PP(r.vies,0).replace(' p.p.',' p.p.'),a3[i].ic==null?'—':T(a3[i].ic),P(a3[i].mae,0),PP(a3[i].vies,0)]));
 const g=D.b1_grupos;const sel=g.slice(0,10).concat(g.slice(-6));
 table('b1',['Grupo','Correlação previsto × realizado','|zGrowth| mediano','Anos entre 0% e 25%','2012–2018','2019–2026'],sel.map(r=>[r.grupo,T(r.ic),T(r.azg),P(r.faixa,0),T(r.ic_a),T(r.ic_b)]));
 table('terco',['Terço pela régua pré-registrada (|zGrowth| do grupo)','Correlação previsto × realizado','|zGrowth| mediano'],D.b1_terco.map(r=>[r[0],T(r[1]),T(r[2])]));
 const K=[['S&P 500',css('--ink'),2,'5 4'],['Top 20 (OoL)',css('--oxford'),2],['JG+G',css('--jade'),1.6],['ROIC alto descontado',css('--claret'),2.8],['Descontado, setores estáveis',css('--mandarin'),1.6],['Descontado, empresas estáveis',css('--slate'),1.6],['PEG (contraste)',css('--velvet'),1.6]];
 legend('lgnav',K.map(k=>[k[0],k[1]]));
 lineChart('nav',D.nav.dates.map(x=>new Date(x)),K.map(k=>({v:D.nav.series[k[0]],c:k[1],w:k[2],dash:k[3]})),{fmt:v=>v.toFixed(0)+'×'});
 const rows=['S&P 500','Top 20 (OoL)','JG+G','ROIC alto descontado','ROIC alto descontado (peso igual)','Descontado, setores estáveis','Descontado, empresas estáveis','Descontado, setores previsíveis (robustez)','Top 20, setores estáveis','PEG (contraste)'];
 table('tab',['Carteira','Retorno anual','Volatilidade','Pior queda','Ações','Janelas 3a','5a','10a','Pior janela 3a'],rows.map(k=>{const t=D.carteiras[k];return [k,P(t.cagr),P(t.vol,0),P(t.dd,0),t.n==null?'—':t.n.toFixed(0),k==='S&P 500'?'—':P(t.w3,0),k==='S&P 500'?'—':P(t.w5,0),k==='S&P 500'?'—':P(t.w10,0),k==='S&P 500'?'—':PP(t.p3,1)]}));
 const C=[css('--oxford'),css('--mandarin'),css('--teal')];legend('lgdec',[['Crescimento do EPS',C[0]],['Re-rating',C[1]],['Dividendos',C[2]]]);
 const dk=['Universo','Top 20 (OoL)','JG+G','ROIC alto descontado','Descontado, setores estáveis','Descontado, empresas estáveis','Top 20, setores estáveis','PEG (contraste)'];
 stacked('dec',dk.map((k,i)=>{const x=D.decomp[k]['12'];return {nome:`${k} (${x.gap.toFixed(2).replace('.',',')})`,eps:x.eps,rr:x.rr,div:x.div,tot:x.tot,bold:k==='ROIC alto descontado'}}),['eps','rr','div'],C);
}
draw();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
</script>'''
html = '<title>ROIC descontado</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body + js.replace('__DATA__', json.dumps(d, ensure_ascii=False)).replace('__LIT__', json.dumps(LIT, ensure_ascii=False))
(ROOT / 'rerating_estavel.html').write_text(html)
print('ok', len(html))
