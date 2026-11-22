"""Relatório FT do cenário bear (relatorio/cenario_bear.html) a partir de dados_bear.json."""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_bear.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text()
css = css[css.index('<link'):css.index('</style>') + len('</style>')]
N, B, A, R, F = d['names'], d['before'], d['after'], d['rob'], d['filt']
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
sp = d['bench9']['S&P 500']
FILTRADAS = {'top20c', 'ool', 'n2', 'n2t20', 'hroic', 'hgrowth'}


def t_main():
    h = ('<table><thead><tr><th class="l">Seleção</th><th>Retorno antes</th><th>Retorno depois</th><th>Diferença</th><th>Depois do IR</th><th>Volatilidade</th>'
         '<th>Pior queda</th><th>Sharpe antes → depois</th><th>Janelas 3a / 5a / 10a &gt; S&amp;P (depois)</th><th>Pior janela 3a (antes → depois)</th><th>Ações</th></tr></thead><tbody>')
    for k in sorted(N, key=lambda k: -A[k]['cagr']):
        b, a = B[k], A[k]; tag = '' if k in FILTRADAS else ' <span style="color:var(--ink2)">(sem filtro)</span>'
        h += (f'<tr><td class="l">{N[k]}{tag}</td><td class="n">{pc(b["cagr"])}</td><td class="n"><b>{pc(a["cagr"])}</b></td><td class="n">{pp(a["cagr"] - b["cagr"])}</td>'
              f'<td class="n">{pc(a["cagr_tax"])}</td><td class="n">{pc(a["vol"], 0)}</td><td class="n">{pc(a["maxdd"], 0)}</td><td class="n">{b["sharpe"]:.2f} → {a["sharpe"]:.2f}</td>'
              f'<td class="n">{pc(a["w3"], 0)} / {pc(a["w5"], 0)} / {pc(a["w10"], 0)}</td><td class="n">{pp(b["w3min"])} → {pp(a["w3min"])}</td><td class="n">{a["n_mean"]:.0f}</td></tr>')
    return h + '</tbody></table>'


def t_rob():
    h = '<table><thead><tr><th class="l">Seleção (depois)</th><th>Sem a maior</th><th>Sem as 3 maiores</th><th>Sem as 3 piores</th><th>Sem NVIDIA (antes → depois)</th></tr></thead><tbody>'
    for k in N:
        r = R[k]
        h += (f'<tr><td class="l">{N[k]}</td><td class="n">{pc(r["sem a maior"][0])} <span class="src">({", ".join(r["sem a maior"][1])})</span></td>'
              f'<td class="n">{pc(r["sem as 3 maiores"][0])} <span class="src">({", ".join(r["sem as 3 maiores"][1])})</span></td>'
              f'<td class="n">{pc(r["sem as 3 piores"][0])} <span class="src">({", ".join(r["sem as 3 piores"][1])})</span></td>'
              f'<td class="n">{pc(d["rob_b_nvda"][k])} → {pc(r["sem NVIDIA"][0])}</td></tr>')
    return h + '</tbody></table>'


def t_filt():
    h = ('<table><thead><tr><th class="l">Seleção</th><th>Saídas por trimestre</th><th>Retorno de 1 ano das que saíram (mediana)</th><th>Das que ficaram</th>'
         '<th>Saídas que caíram ≥ 30%</th><th>Saídas que subiram ≥ 50%</th><th>Posições com queda ≥ 30% em 1 ano (antes → depois)</th></tr></thead><tbody>')
    for k in ('top20c', 'ool', 'n2t20', 'n2', 'hroic', 'hgrowth'):
        f = F[k]
        h += (f'<tr><td class="l">{N[k]}</td><td class="n">{f["n_sai"]:.1f}</td><td class="n">{pc(f["r_med_saidas"], 0)}</td><td class="n">{pc(f["r_med_mantidas"], 0)}</td>'
              f'<td class="n">{pc(f["pct_saidas_queda30"], 0)}</td><td class="n">{pc(f["pct_saidas_alta50"], 0)}</td><td class="n">{pc(f["queda30_antes"])} → {pc(f["queda30_depois"])}</td></tr>')
    return h + '</tbody></table>'


def lst(rows):
    seen, out = set(), []
    for dt, t, r in rows:
        if t in seen: continue
        seen.add(t); out.append(f'{t} ({dt[:7]}: {pc(r, 0)})')
        if len(out) == 6: break
    return ', '.join(out)


def bars():
    ks = list(N); W, H, m = 900, 300, 60
    mx = max(max(B[k]['cagr'], A[k]['cagr']) for k in ks) * 1.15
    gw = (W - m) / len(ks); s = f'<svg viewBox="0 0 {W} {H}">'
    y = lambda v: H - 40 - v / mx * (H - 70)
    s += f'<line x1="{m}" x2="{W}" y1="{y(sp)}" y2="{y(sp)}" stroke="var(--ink)" stroke-dasharray="4 3"/><text x="{m}" y="{y(sp) - 4}" style="font-size:11px">S&amp;P 500 {pc(sp)}</text>'
    for i, k in enumerate(ks):
        x0 = m + i * gw
        for j, (v, c) in enumerate(((B[k]['cagr'], 'var(--slate)'), (A[k]['cagr'], 'var(--oxford)'))):
            s += f'<rect x="{x0 + 8 + j * (gw / 2 - 8)}" y="{y(v)}" width="{gw / 2 - 12}" height="{H - 40 - y(v)}" fill="{c}"/>'
            s += f'<text x="{x0 + 8 + j * (gw / 2 - 8) + (gw / 2 - 12) / 2}" y="{y(v) - 4}" text-anchor="middle" style="font-size:11px">{pc(v)}</text>'
        s += f'<text x="{x0 + gw / 2}" y="{H - 22}" text-anchor="middle" style="font-size:11px">{N[k].replace(" (máx. 8 por setor)", "")[:22]}</text>'
    return s + '</svg><div class="legend"><span><i style="--c:var(--slate);height:10px"></i>Antes</span><span><i style="--c:var(--oxford);height:10px"></i>Depois (filtro bear + Especiais nova)</span></div>'


dt, dn = B['top20c'], A['top20c']
body = f'''<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Cenário bear · {d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">Evitar perdedores</div>
<h1>O filtro do cenário ruim quase não protege, e corta vencedoras tanto quanto perdedoras</h1>
<p class="deck">Barrar as ações cujo retorno num cenário de frustração ficaria abaixo de −10% não reduziu as quedas fortes das carteiras. A Especiais nova, que prioriza ROIC e crescimento acima de 30%, foi o que melhorou.</p>
<div class="byline">S&amp;P 500 point-in-time, rebalanceamento trimestral, retorno total em dólares · crescimento histórico (mediana de 5 anos), ROIC triangulado, regras de 22/11/2026</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra na qualidade, no P/E justo e, por ele, no cenário bear. Backtest com o crescimento <b>histórico</b>; a planilha usa o consenso com haircut, que não tem histórico para testar.</p>
<div class="big">
 <div><b>{pp(dn['cagr'] - dt['cagr'])}</b><span>efeito do filtro na Top 20 ({pc(dt['cagr'])} → {pc(dn['cagr'])})</span></div>
 <div><b>{pc(F['top20c']['queda30_antes'])} → {pc(F['top20c']['queda30_depois'])}</b><span>posições da Top 20 que caíram 30% ou mais no ano seguinte</span></div>
 <div><b>{pc(F['ool']['r_med_saidas'], 0)}</b><span>retorno mediano, no ano seguinte, das ações que o filtro tirou da OoL (as que ficaram: {pc(F['ool']['r_med_mantidas'], 0)})</span></div>
 <div><b>{pc(B['n2t20']['cagr'])} → {pc(A['n2t20']['cagr'])}</b><span>Especiais antes e depois (Sharpe {B['n2t20']['sharpe']:.2f} → {A['n2t20']['sharpe']:.2f})</span></div>
</div>
<div class="cols"><div class="prose">
<p>A ideia é boa e é de qualquer gestor experiente: antes de comprar, imagine o cenário em que a tese frustra. O crescimento cai para o menor entre o da empresa e o maior entre o percentil 70 da indústria, 70% do próprio crescimento e 6%; o múltiplo vai para o menor entre 80% do P/E justo e o atual. Se mesmo assim a ação perder mais de 10% em dois anos, ela fica de fora.</p>
<p>O problema é que, no histórico, esse cenário separa mal. Na Top 20, que já escolhe as de maior retorno esperado, o filtro quase nunca atua: tira em média {F['top20c']['n_sai']:.1f} ação por trimestre. Na OoL e na High Growth ele atua mais, mas as ações que saíram renderam, no ano seguinte, tanto ou mais que as que ficaram. O filtro barra, por exemplo, NVIDIA em 2023, a maior alta do período, porque o múltiplo já estava acima do justo.</p>
<p>O que melhorou foi a outra regra: a Especiais que primeiro pega as empresas com ROIC acima de 30% e crescimento acima de 30%, exige retorno esperado acima de 20% e completa pela nota 1,5 × ROIC + crescimento. Ela rende mais, com mais estabilidade, e deixa de depender só do crescimento do lucro.</p>
</div><aside class="box"><h3>Em uma linha</h3><ol>
<li><b>Top 20:</b> {pp(dn['cagr'] - dt['cagr'])}; o filtro quase não atua.</li>
<li><b>OoL / High Growth / Excepcionais:</b> {pp(A['ool']['cagr'] - B['ool']['cagr'])} / {pp(A['hgrowth']['cagr'] - B['hgrowth']['cagr'])} / {pp(A['n2']['cagr'] - B['n2']['cagr'])}.</li>
<li><b>Quedas fortes:</b> praticamente iguais.</li>
<li><b>Especiais nova:</b> {pp(A['n2t20']['cagr'] - B['n2t20']['cagr'])}, Sharpe maior, 100% das janelas de 3 anos.</li></ol></aside></div>

<figure><figcaption class="t">Retorno anual antes e depois</figcaption><figcaption class="s">GCGR e JG+G não passam pelo filtro (servem de controle).</figcaption>{bars()}</figure>
<figure><figcaption class="t">A tabela principal</figcaption><figcaption class="s">Imposto de 15% sobre o ganho realizado; janelas móveis mensais contra o S&amp;P 500 ({pc(sp)} ao ano).</figcaption><div class="tablebox">{t_main()}</div></figure>
<figure><figcaption class="t">Perdedores evitados contra vencedores perdidos</figcaption><figcaption class="s">Ações que estavam na carteira antes e saíram por causa do filtro (ou da regra nova, na Especiais): retorno total no ano seguinte.</figcaption>
<div class="tablebox">{t_filt()}</div>
<p class="note"><b>Maiores perdedores evitados (OoL):</b> {lst(F['ool']['evitados'])}.<br><b>Maiores vencedores perdidos (OoL):</b> {lst(F['ool']['perdidos'])}.<br>
<b>Especiais — evitados:</b> {lst(F['n2t20']['evitados'])}.<br><b>Especiais — perdidos:</b> {lst(F['n2t20']['perdidos'])}.</p>
<div class="sowhat"><b>E daí</b><span>Um bom filtro de risco tira mais perdedoras que vencedoras. Este tira dos dois lados na mesma proporção: na OoL, {pc(F['ool']['pct_saidas_queda30'], 0)} das saídas caíram 30% ou mais, mas {pc(F['ool']['pct_saidas_alta50'], 0)} subiram 50% ou mais. É o padrão de um critério que pune o múltiplo alto, que no período foi justamente o das vencedoras.</span></div></figure>
<figure><figcaption class="t">Tirando as vencedoras e as perdedoras (depois)</figcaption><figcaption class="s">Retorno anual refazendo a carteira sem as ações indicadas no universo inteiro.</figcaption><div class="tablebox">{t_rob()}</div></figure>
<figure><figcaption class="t">De onde vem o retorno (3 anos, ao ano)</figcaption><figcaption class="s">Crescimento do EPS, re-rating e dividendos das posições.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Seleção</th><th>EPS antes → depois</th><th>Re-rating antes → depois</th><th>Dividendos</th></tr></thead><tbody>
{''.join(f'<tr><td class="l">{N[k]}</td><td class="n">{pc((B[k]["decomp"] or {}).get("le"))} → {pc((A[k]["decomp"] or {}).get("le"))}</td><td class="n">{pc((B[k]["decomp"] or {}).get("lp"))} → {pc((A[k]["decomp"] or {}).get("lp"))}</td><td class="n">{pc((A[k]["decomp"] or {}).get("ld"))}</td></tr>' for k in N)}
</tbody></table></div>
<div class="sowhat"><b>E daí</b><span>A Especiais nova troca crescimento do lucro por re-rating: o lucro das posições passa a crescer {pc(A['n2t20']['decomp']['le'])} ao ano (antes {pc(B['n2t20']['decomp']['le'])}) e o múltiplo sobe {pc(A['n2t20']['decomp']['lp'])} (antes {pc(B['n2t20']['decomp']['lp'])}). Fica mais parecida com a Top 20, o que reduz a diversificação entre as duas.</span></div></figure>
<section class="verdict"><h2>O veredito</h2><div class="vgrid">
<div><span class="tag" style="--c:var(--claret)">Não adotar</span><h4>O filtro bear como regra</h4><p>Pelo critério registrado antes do teste (reduzir as quedas fortes sem tirar mais de 0,5 p.p. da Top 20), ele não passa: as quedas fortes não caíram.</p></div>
<div><span class="tag" style="--c:var(--teal)">Adotar</span><h4>A Especiais nova</h4><p>{pc(B['n2t20']['cagr'])} → {pc(A['n2t20']['cagr'])}, Sharpe {B['n2t20']['sharpe']:.2f} → {A['n2t20']['sharpe']:.2f}, pior janela de 3 anos {pp(B['n2t20']['w3min'])} → {pp(A['n2t20']['w3min'])}. Exploratória (proposta depois dos resultados anteriores).</p></div>
<div><span class="tag" style="--c:var(--oxford)">Usar como informação</span><h4>O retorno bear na ficha</h4><p>Como coluna de risco para o julgamento (o "quanto perco se frustrar"), não como corte automático.</p></div></div></section>
<p class="method"><b>Método.</b> Regras pré-registradas no PROTOCOLO em 22/11/2026, antes de rodar. Bear: g_bear = mín(g, máx(p70 da indústria GICS na data, 0,7·g, 6%)); múltiplo_bear = mín(0,8·P/E justo, P/L); retorno_bear = (múltiplo_bear·EPS·(1+g_bear)²/preço)^½ − 1 + dy; sem P/E justo ou com prejuízo, barrada. Filtro em OoL (e High ROIC/High Growth), Top 20, Especiais e Excepcionais. Código: relatorio/backtest_bear.py.</p>
</div>'''
html = '<title>Cenário bear</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + css + body
(ROOT / 'cenario_bear.html').write_text(html)
print('ok', len(html))
