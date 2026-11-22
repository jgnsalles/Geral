"""Relatório FT do ramo L (bear v2 pela indústria): relatorio/bear_v2.html a partir de dados_bear_v2.json."""
import json, pathlib, html
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_bear_v2.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text(); css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=0: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
nm = lambda x, n=1: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')
e = html.escape
P, V, M = d['prof']['Perdedores'], d['prof']['Grandes vencedores'], d['prof']['Demais']
rc = d['reclass']; tl = rc['tipos_l']; ntl = sum(tl.values())

prof_rows = [('Crescimento previsto', 'g0', pc), ('Mediana da indústria', 'g_med', pc), ('Gap de crescimento vs indústria', 'gap_g', pp),
             ('P/L na entrada', 'pe0', nm), ('P/L mediano da indústria', 'pe_med', nm), ('P/L ÷ indústria', 'gap_pe', lambda v: nm(v, 2) + '×'),
             ('% que entregou 10 p.p.+ abaixo do previsto', 'entregue_menos_10', pc), ('Bear v2 (mediana) na entrada', 'rb2_med', pc)]
prof_tbl = '<table><thead><tr><th class="l">Na entrada (medianas)</th><th>Perdedores</th><th>Demais</th><th>Grandes vencedores</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{a}</td><td class="n">{f(P.get(k))}</td><td class="n">{f(M.get(k))}</td><td class="n">{f(V.get(k))}</td></tr>' for a, k, f in prof_rows) + '</tbody></table>'
tl_tbl = '<table><thead><tr><th class="l">Tipo (lente do crescimento vs indústria)</th><th>Episódios</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(k)}</td><td class="n">{v} ({pc(v / ntl)})</td></tr>' for k, v in sorted(tl.items(), key=lambda x: -x[1])) + '</tbody></table>'
w_tbl = '<table><thead><tr><th class="l">Ação</th><th>Entrada</th><th>Retorno</th><th>Cresc. previsto</th><th>Indústria</th><th>P/L</th><th>P/L indústria</th><th>P/L saída</th><th class="l">Leitura</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{w[0]}</td><td class="n">{w[2][:7]}</td><td class="n">{pc(w[4])}</td><td class="n">{pc(w[6])}</td><td class="n">{pc(w[7])}</td>'
            f'<td class="n">{nm(w[9])}</td><td class="n">{nm(w[10])}</td><td class="n">{nm(w[12])}</td><td class="l">{e(w[-1])}</td></tr>' for w in d['worst']) + '</tbody></table>'
sig_tbl = '<table><thead><tr><th class="l">Sinal (parâmetro escolhido em 2012–18)</th><th>Lift 12–18</th><th>Lift 19–26</th><th>Perdedores pegos 19–26</th><th>Vencedores cortados 19–26</th><th class="l">Vencedores que cortaria</th><th>Passou?</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(s["sinal"])}</td><td class="n">{nm(s["desc"]["lift"], 2)}</td><td class="n">{nm(s["conf"]["lift"], 2)}</td><td class="n">{pc(s["conf"]["rec_perd"])}</td>'
            f'<td class="n">{pc(s["conf"]["rec_venc"])}</td><td class="l">{", ".join(x[0] + " " + x[1][:4] for x in (s["conf"]["venc_cortados"] + s["desc"]["venc_cortados"])[:4])}</td><td class="n">{"sim" if s["passa"] else "não"}</td></tr>' for s in d['sinais']) + '</tbody></table>'
N = d['names']; vs = list(d['port'])
port_tbl = '<table><thead><tr><th class="l">Seleção</th>' + ''.join(f'<th>{e(v)}<br>retorno · quedas ≥30%</th>' for v in vs) + '</tr></thead><tbody>' + \
    ''.join('<tr><td class="l">' + e(N[k]) + '</td>' + ''.join(f'<td class="n">{pc(d["port"][v][k]["cagr"], 1)} · {pc(d["port"][v][k]["queda30"], 1)}</td>' for v in vs) + '</tr>' for k in N) + '</tbody></table>'
rob = d['rob']
rob_tbl = '<table><thead><tr><th class="l">Retorno anual</th><th>Top 20</th><th>Especiais</th><th>OoL</th><th>High ROIC</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(v)} · {e(lab)}</td>' + ''.join(f'<td class="n">{pc(rob[v][lab][k], 1)}</td>' for k in ('top20c', 'n2t20', 'ool', 'hroic')) + '</tr>' for v in rob for lab in rob[v]) + '</tbody></table>'
venda = d['port']['Regra de venda (EPS < 80% da trajetória)']; atual = d['port']['Atual (sem filtro)']

body = f'''<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Bear v2 · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">Rever o bear</div>
<h1>Quase todo mundo deixa de entregar o crescimento previsto; os perdedores não eram os mais caros da indústria</h1>
<p class="deck">A lente "crescimento muito acima da indústria, não entregue" explica casos marcantes, como SMCI e Chipotle, mas não a maioria das perdas. Nenhuma versão do bear pela indústria passou no teste, e vender quando o lucro decepciona custou retorno.</p>
<div class="byline">S&amp;P 500 point-in-time · episódios do ramo K (Top 20, Especiais, OoL, High ROIC, High Growth, Excepcionais, JG+G) · crescimento histórico (regra testada)</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra na qualidade e no P/E justo do bear. Critérios, parâmetros e o teste de adoção foram registrados no PROTOCOLO antes de rodar. Indústria = GICS na data (setor quando a indústria tem menos de 5 ações).</p>
<div class="big">
 <div><b>{tl.get('Crescimento não entregue, precificada acima da indústria', 0)} de {ntl}</b><span>perdas eram "crescimento acima da indústria, não entregue, com P/L acima da indústria"</span></div>
 <div><b>{pc(P['entregue_menos_10'])} × {pc(V['entregue_menos_10'])}</b><span>entregaram 10 p.p.+ abaixo do previsto: perdedores × grandes vencedores</span></div>
 <div><b>{nm(P['gap_pe'], 2)}× × {nm(V['gap_pe'], 2)}×</b><span>P/L ÷ indústria na entrada: perdedores × vencedores</span></div>
 <div><b>0 de 5</b><span>versões do bear pela indústria passaram</span></div>
</div>

<h2 class="chap" style="margin-top:40px">1. A lente do crescimento vs indústria</h2>
<figure><figcaption class="t">Perdedores e vencedores prometiam o mesmo gap de crescimento sobre a indústria, e os perdedores eram até mais baratos que a indústria</figcaption>
<div class="tablebox">{prof_tbl}</div>
<div class="sowhat"><b>E daí</b><span>O crescimento previsto pela mediana histórica fica ~{pc(P['gap_g'])} acima da indústria em todos os grupos, e quase todos (perdedores e vencedores) entregam menos do que a mediana prometia: é a volta à média que já tínhamos medido. O que separa o perdedor não é ter prometido mais, é o lucro de fato cair. O P/L relativo à indústria não ajuda: os perdedores estavam a {nm(P['gap_pe'], 2)}× a indústria, os vencedores a {nm(V['gap_pe'], 2)}×.</span></div>
</figure>
<figure><figcaption class="t">Reclassificação das perdas</figcaption><div class="tablebox">{tl_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Dos {rc['n_mult']} episódios que o ramo K chamou de "múltiplo comprimiu", {pc(rc['mult_era_nao_entregue'])} eram de fato o caso que você descreveu (crescimento muito acima da indústria, P/L muito acima da indústria, crescimento não entregue): SMCI 2024, Chipotle 2024. Os demais "não entregues" tinham preço normal; a decepção de lucro aconteceu em ações que não pareciam caras.</span></div>
</figure>
<figure><figcaption class="t">As 20 piores pela lente da indústria</figcaption><div class="tablebox">{w_tbl}</div></figure>

<h2 class="chap" style="margin-top:40px">2. O bear pela indústria funciona?</h2>
<figure><figcaption class="t">Nenhuma das cinco versões passou nos dois períodos</figcaption>
<figcaption class="s">Lift = taxa de perdedores entre os marcados ÷ taxa geral. Para passar: lift ≥ 1,5 nos dois períodos, TIR dos marcados 10 p.p. abaixo e pegar 1,5× mais perdedores que grandes vencedores.</figcaption>
<div class="tablebox">{sig_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Todas melhoram de 2019 em diante (lift de 1,4 a 2,5), mas nenhuma chega a 1,5 em 2012–2018, quando barravam NFLX 2015 (+518%) e NFLX 2018 (+215%). De 2019 em diante, os mesmos sinais teriam barrado NVDA 2021 e 2024. A versão com P/L > 3× a indústria e gap de 30 p.p. é a mais limpa (não corta nenhum grande vencedor depois de 2019), mas marca tão poucos casos (1% a 2%) que não muda a carteira.</span></div>
</figure>

<h2 class="chap" style="margin-top:40px">3. E a regra de venda?</h2>
<figure><figcaption class="t">Vender quando o EPS fica 20% abaixo da trajetória prevista custou de 1 a 4 pontos ao ano e não reduziu as quedas</figcaption>
<figcaption class="s">Retorno anual e % das posições com queda de 30% ou mais no ano seguinte. Bear antigo = filtro atual da planilha (retorno bear > −10%).</figcaption>
<div class="tablebox">{port_tbl}</div>
<div class="tablebox" style="margin-top:10px">{rob_tbl}</div>
<div class="sowhat"><b>E daí</b><span>A regra de venda vende depois que o preço já caiu e perde a recuperação: a Top 20 vai de {pc(atual['top20c']['cagr'], 1)} para {pc(venda['top20c']['cagr'], 1)} e a Excepcionais de {pc(atual['n2']['cagr'], 1)} para {pc(venda['n2']['cagr'], 1)}, com quedas fortes iguais ou maiores. Só a GCGR melhora. Pelo critério registrado (retorno ≥ e menos quedas em 5 das 8 seleções), nem a regra de venda nem o bear antigo passam (1 de 8 cada). O rebalanceamento trimestral já tira a ação quando o crescimento histórico cai.</span></div>
</figure>

<section class="verdict"><h2>O veredito: o bear vira informação, não corte</h2>
<div class="vgrid">
 <div><span class="tag" style="--c:var(--claret)">Não adotar</span><h4>Corte pelo bear (antigo ou v2) e regra de venda</h4><p>Nenhum passou. Barram vencedores na mesma proporção dos perdedores ou vendem tarde.</p></div>
 <div><span class="tag" style="--c:var(--oxford)">Mostrar</span><h4>Bear v2 e gaps vs indústria na ficha</h4><p>Retorno bear pela indústria, gap de crescimento e P/L ÷ indústria como colunas de julgamento; alerta quando gap > 30 p.p. e P/L > 3× a indústria (o perfil SMCI/CMG).</p></div>
 <div><span class="tag" style="--c:var(--teal)">O que funciona</span><h4>Regra como está</h4><p>As perdas vêm do lucro que cai depois da compra, e isso não se vê na entrada. A diversificação e o teto por ação/setor são a defesa.</p></div>
</div></section>
<p class="method" style="margin-top:30px"><b>Método.</b> Episódios e critério do ramo K. Gap de crescimento = mediana histórica do EPS − mediana da indústria na data; P/L relativo = P/L ÷ mediana do P/L positivo da indústria. Bear v2: g_bear = MIN(g, MAX(mediana ou p70 da indústria, 6%)); P/E justo com g_bear; múltiplo_bear = MIN(P/L, MAX(P/L da indústria, P/E justo_bear)); retorno em 2 anos + dividendos. Parâmetros escolhidos em 2012–2018 e conferidos em 2019–2026. Regra de venda: EPS anual < 80% de EPS_entrada × (1+g)^anos; não volta enquanto seguir selecionada. Código: relatorio/bear_v2.py.</p>
</div>'''
(ROOT / 'bear_v2.html').write_text('<title>Bear pela indústria</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body)
print('ok')
