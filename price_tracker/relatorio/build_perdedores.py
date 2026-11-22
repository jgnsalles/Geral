"""Relatório FT do ramo K (perdedores): relatorio/perdedores.html a partir de dados_perdedores.json."""
import json, pathlib, html
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_perdedores.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text(); css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=0: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
nm = lambda x, n=1: '—' if x is None else f'{x:.{n}f}'.replace('.', ',')
e = html.escape
P, V, M = d['prof']['Perdedores'], d['prof']['Grandes vencedores'], d['prof']['Demais']


def bars(items, color='var(--claret)', fmt=lambda v: str(v), w=640):
    mx = max(v for _, v in items) or 1; h = 26 * len(items) + 8; s = f'<svg viewBox="0 0 {w} {h}" role="img">'
    for i, (lab, v) in enumerate(items):
        y = 6 + i * 26; bw = (w - 330) * v / mx
        s += f'<text x="0" y="{y + 14}" style="font-size:13px">{e(lab)}</text><rect x="300" y="{y + 3}" width="{bw:.1f}" height="14" fill="{color}"/>'
        s += f'<text class="num" x="{306 + bw:.1f}" y="{y + 15}">{fmt(v)}</text>'
    return s + '</svg>'


rows = [('P/L na entrada', 'pe0', nm), ('P/L na saída', 'pe1', nm), ('P/E justo na entrada', 'fpe0', nm), ('ROIC na entrada', 'roic0', pc),
        ('ROIC na saída', 'roic1', pc), ('ROIC 2 anos depois', 'roic2y', pc), ('Crescimento previsto (mediana)', 'g0', pc),
        ('EPS: crescimento anual nos 2 anos seguintes', 'eps2y_cagr', pc), ('% com EPS 10%+ menor 2 anos depois', 'eps2y_queda', pc),
        ('Retorno esperado na entrada', 'ret0', pc), ('Bear (regra atual) na entrada', 'rb0', pc), ('Alta dos 12 meses anteriores', 'mom12', pc),
        ('zGrowth', 'zg0', lambda v: nm(v, 2)), ('Permanência (trimestres, mediana)', 'q_med', lambda v: nm(v, 0)), ('TIR do episódio (mediana)', 'tir_med', pc)]
prof_tbl = '<table><thead><tr><th class="l">Na entrada e depois (medianas)</th><th>Perdedores</th><th>Demais</th><th>Grandes vencedores</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{lab}</td><td class="n">{f(P.get(k))}</td><td class="n">{f(M.get(k))}</td><td class="n">{f(V.get(k))}</td></tr>' for lab, k, f in rows) + '</tbody></table>'
tipos = sorted(d['tipos'].items(), key=lambda x: -x[1]); ntot = sum(v for _, v in tipos)
tp = d['tipo_prof']
tipo_tbl = '<table><thead><tr><th class="l">Tipo de perda</th><th>Episódios</th><th>Perda mediana</th><th>P/L entrada → saída</th><th>ROIC entrada → saída</th><th>Exemplos</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(k)}</td><td class="n">{v} ({pc(v / ntot)})</td><td class="n">{pc(tp[k]["R_med"])}</td><td class="n">{nm(tp[k]["pe0"])} → {nm(tp[k]["pe1"])}</td>'
            f'<td class="n">{pc(tp[k]["roic0"])} → {pc(tp[k]["roic1"])}</td><td class="l">{", ".join(sorted({x[0] + " " + x[1][:4] for x in d["tipo_ex"][k]}))[:90]}</td></tr>' for k, v in tipos) + '</tbody></table>'
sig_tbl = '<table><thead><tr><th class="l">Sinal na entrada</th><th>Marcados 12–18</th><th>Lift 12–18</th><th>Lift 19–26</th><th>Perdedores pegos 19–26</th><th>Vencedores perdidos 19–26</th><th>Passou?</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(r["sinal"])}</td><td class="n">{pc(r["desc"]["marcados"], 1)}</td><td class="n">{nm(r["desc"]["lift"], 2)}</td><td class="n">{nm(r["conf"]["lift"], 2)}</td>'
            f'<td class="n">{pc(r["conf"]["rec_perd"])}</td><td class="n">{pc(r["conf"]["rec_venc"])}</td><td class="n">{"sim" if r["passa"] else "não"}</td></tr>' for r in d['sinais']) + '</tbody></table>'
cart_tbl = '<table><thead><tr><th class="l">Carteira</th><th>Episódios</th><th>% perdedores</th><th>TIR mediana</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{e(k)}</td><td class="n">{v["n"]}</td><td class="n">{pc(v["perd"])}</td><td class="n">{pc(v["tir_med"])}</td></tr>' for k, v in sorted(d['por_cart'].items(), key=lambda x: x[1]['perd'])) + '</tbody></table>'
worst_tbl = '<table><thead><tr><th class="l">Ação</th><th class="l">Carteira</th><th>Entrada → saída</th><th>Retorno</th><th>P/L entrada → saída</th><th>ROIC entrada → saída</th><th>Cresc. previsto</th><th class="l">Tipo</th></tr></thead><tbody>' + \
    ''.join(f'<tr><td class="l">{w[0]}</td><td class="l">{w[1]}</td><td class="n">{w[2][:7]} → {w[3][:7]}</td><td class="n">{pc(w[5])}</td><td class="n">{nm(w[8])} → {nm(w[9])}</td>'
            f'<td class="n">{pc(w[10])} → {pc(w[11])}</td><td class="n">{pc(w[12])}</td><td class="l">{e(w[7])}</td></tr>' for w in d['worst'][:15]) + '</tbody></table>'

body = f'''<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Diagnóstico das perdas · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">Quando perdemos dinheiro</div>
<h1>Os perdedores pareciam iguais aos vencedores no dia da compra</h1>
<p class="deck">Em {str(d['n_ep'])[:-3] + '.' + str(d['n_ep'])[-3:]} posições das sete carteiras, {pc(d['pct_perd'])} renderam menos de −10% ao ano. Na entrada, tinham o mesmo P/L, o mesmo crescimento e quase o mesmo ROIC das vencedoras. O que as separou veio depois: o lucro não veio e o múltiplo encolheu. Nenhum dos nove sinais testados as identifica com antecedência.</p>
<div class="byline">S&amp;P 500 point-in-time · Top 20, Especiais, OoL, High ROIC, High Growth, Excepcionais e JG+G · crescimento histórico (regra testada)</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele define a qualidade, o P/E justo e o cenário bear. Episódio = permanência contínua da ação na carteira; perdedor = TIR do episódio abaixo de −10% ao ano. Critérios registrados no PROTOCOLO antes de rodar.</p>
<div class="big">
 <div><b>{d['n_perd_unicos']}</b><span>episódios perdedores únicos (ação × data), {pc(d['pct_perd'])} do total</span></div>
 <div><b>{nm(P['pe0'])} × {nm(V['pe0'])}</b><span>P/L de entrada: perdedores × grandes vencedores</span></div>
 <div><b>{pc(P['eps2y_queda'])}</b><span>dos perdedores tinham lucro 10%+ menor dois anos depois (vencedores: {pc(V['eps2y_queda'])})</span></div>
 <div><b>0 de 9</b><span>sinais conhecidos na entrada passaram no teste</span></div>
</div>

<h2 class="chap" style="margin-top:40px">1. No dia da compra, nada os diferenciava</h2>
<figure><figcaption class="t">Perdedores, medianos e grandes vencedores tinham perfis quase idênticos na entrada</figcaption>
<figcaption class="s">Medianas por grupo. Perdedores: TIR do episódio abaixo de −10% ao ano; grandes vencedores: acima de 30%.</figcaption>
<div class="tablebox">{prof_tbl}</div>
<div class="sowhat"><b>E daí</b><span>O P/L de entrada era o mesmo (~20) e o crescimento previsto também (~31%). Os perdedores tinham ROIC um pouco menor ({pc(P['roic0'])} contra {pc(V['roic0'])}) e retorno esperado menor ({pc(P['ret0'])} contra {pc(V['ret0'])}), mas a diferença é pequena demais para separar um grupo do outro. A diferença está no que aconteceu depois: o P/L dos perdedores caiu, o dos vencedores subiu de {nm(V['pe0'])} para {nm(V['pe1'])}, e o lucro dos perdedores encolheu em metade dos casos.</span></div>
</figure>

<h2 class="chap" style="margin-top:40px">2. Que tipo de perda foi</h2>
<figure><figcaption class="t">Um terço foi múltiplo comprimindo em ação cara; outro terço, o lucro que não veio</figcaption>
<figcaption class="s">Classificação de cada episódio perdedor pelo que mudou entre a entrada e a saída (EPS anual, P/L e ROIC).</figcaption>
{bars([(k, v) for k, v in tipos], fmt=lambda v: f'{v} ({pc(v / ntot)})')}
<div class="tablebox" style="margin-top:10px">{tipo_tbl}</div>
<div class="sowhat"><b>E daí</b><span><b>Múltiplo comprimiu:</b> eram as ações caras do grupo (P/L mediano de {nm(tp['Múltiplo comprimiu (lucro ok)']['pe0'])} na entrada), que perderam o prêmio mesmo com o lucro crescendo (SMCI, TTD). <b>Lucro caiu:</b> curiosamente eram as baratas (P/L de {nm(tp['Lucro caiu (crescimento não veio)']['pe0'])}): o mercado já desconfiava, e o lucro de fato caiu (BA, GNRC, BLDR). <b>Quedas curtas:</b> um trimestre de choque, como a Boeing no começo de 2020 e a Netflix em 2022, não dá para antecipar com números de balanço.</span></div>
</figure>

<h2 class="chap" style="margin-top:40px">3. Onde aparecem</h2>
<figure><figcaption class="t">A High ROIC é a que menos tem perdedores; Top 20 e High Growth, as que mais</figcaption>
<div class="tablebox">{cart_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Exigir ROIC acima de 30% reduz a frequência de perdas quase pela metade. Os setores dos perdedores são os mesmos do conjunto: não há um setor-vilão para excluir.</span></div>
</figure>

<h2 class="chap" style="margin-top:40px">4. Dá para evitar com o que se sabe na compra?</h2>
<figure><figcaption class="t">Nenhum dos nove sinais funcionou nos dois períodos</figcaption>
<figcaption class="s">Lift = taxa de perdedores entre as marcadas ÷ taxa geral. Para passar, lift ≥ 1,5 nos dois períodos, TIR dos marcados 10 p.p. abaixo e pegar 1,5× mais perdedores que grandes vencedores.</figcaption>
<div class="tablebox">{sig_tbl}</div>
<div class="sowhat"><b>E daí</b><span>O bear atual e a versão mais dura (piso de 50%) só funcionaram de 2019 em diante; em 2012–2018 barravam mais vencedores que perdedores. "P/L acima de 1,5× o justo" vai na direção certa, mas fraco e sem passar no primeiro período. Como nada passou, nenhuma regra nova foi testada nas carteiras, como manda o pré-registro.</span></div>
</figure>

<h2 class="chap" style="margin-top:40px">As 15 piores</h2>
<div class="tablebox">{worst_tbl}</div>

<section class="verdict"><h2>O veredito: perder dinheiro aqui é risco de execução do lucro, não de entrada</h2>
<div class="vgrid">
 <div><span class="tag" style="--c:var(--claret)">Não adotar</span><h4>Bear como corte automático</h4><p>Nem o atual nem o mais duro separam perdedores na entrada. Barram vencedores na mesma proporção.</p></div>
 <div><span class="tag" style="--c:var(--oxford)">Usar</span><h4>Bear como informação</h4><p>Coluna na ficha para o julgamento, junto com o alerta de P/L acima de 1,5× o justo.</p></div>
 <div><span class="tag" style="--c:var(--teal)">O que protege</span><h4>Vender quando o lucro decepciona</h4><p>Metade dos perdedores teve lucro menor dois anos depois. A regra trimestral já tira a ação quando o crescimento cai; a perda acontece no intervalo. Monitorar revisões do consenso é o próximo teste natural.</p></div>
 <div><span class="tag" style="--c:var(--wheat)">Concentração</span><h4>ROIC alto reduz perdas</h4><p>A High ROIC tem a menor taxa de perdedores ({pc(d['por_cart']['High ROIC']['perd'])}). Peso maior em ROIC acima de 30% é a defesa mais simples que os dados mostram.</p></div>
</div></section>
<p class="method" style="margin-top:30px"><b>Método.</b> Episódios por carteira (a mesma ação em várias carteiras conta em cada uma; nos sinais, episódios únicos). Retorno total ajustado do 1º trimestre em carteira ao 1º trimestre fora; TIR anualizada (episódios de 1 trimestre têm TIR exagerada; o retorno simples aparece nas tabelas). EPS anual mais recente conhecido em cada data (defasagem de até 15 meses). Código: <code>relatorio/perdedores.py</code>.</p>
</div>'''
(ROOT / 'perdedores.html').write_text('<title>Quando perdemos dinheiro</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body)
print('ok')
