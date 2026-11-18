"""Relatório (FT) do ramo D: Top 20 no universo dos gestores sem viés. Saída: relatorio/gestores_sem_vies.html (+ PDF via Playwright à parte)."""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
d = json.loads((ROOT / 'dados_gestores_sv.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text(); css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
T, E, CV, L = d['carteiras'], d['extra'], d['cobertura']['5'], d['limites']
k0, kc, k5 = 'Top 20 · S&P (original)', 'Top 20 · lista do Navegando, ≥ 5 (ramo C, com viés)', 'Top 20 · 250 gestores, ≥ 5'
rows = [k0, kc, 'Top 20 · 250 gestores, ≥ 3', k5, 'Top 20 · 250 gestores, ≥ 10', 'ROIC alto descontado · S&P (original)', 'ROIC alto descontado · 250 gestores, ≥ 3',
        'ROIC alto descontado · 250 gestores, ≥ 5', 'ROIC alto descontado · 250 gestores, ≥ 10', 'OoL · S&P (original, peso igual)', 'OoL · lista do Navegando, ≥ 5 (ramo C, com viés; peso igual)',
        'OoL · 250 gestores, ≥ 5 (peso igual)']
bench = ['S&P 500', 'S&P 500 equal weight', 'OoL antigo', 'GCGR antigo', 'OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)', 'Cyclicals', 'IWM (Russell 2000)']
def tr(k):
    t = T[k]; e = E.get(k, {}); ew = T.get(k + ' (peso igual)', {})
    return (f'<tr><td class="l">{k}</td><td class="n">{pc(t["cagr"])}</td><td class="n">{pc(ew.get("cagr")) if "OoL" not in k else "—"}</td><td class="n">{pc(t["w3"], 0)}</td>'
            f'<td class="n">{pc(t["w5"], 0)}</td><td class="n">{pc(t["w10"], 0)}</td><td class="n">{pc(t["p3"])}</td><td class="n">{pc(t["dd"], 0)}</td><td class="n">{pc(t["vol"], 0)}</td>'
            f'<td class="n">{pc(e.get("fora_sp"), 0)}</td><td class="n">{pc(e.get("giro_trim"), 0)}</td></tr>')
tab = ''.join(tr(k) for k in rows) + '<tr><td colspan="11" class="l" style="color:var(--ink2);font-size:12px">Comparativos obrigatórios (mesmo período)</td></tr>' + ''.join(tr(k) for k in bench if k in T)
dec = ''.join(f'<tr><td class="l">{k}</td><td class="n">{pc(v["12"]["eps"])}</td><td class="n">{pc(v["12"]["rr"])}</td><td class="n">{pc(v["12"]["div"])}</td><td class="n">{pc(v["12"]["tot"])}</td></tr>'
              for k, v in d['decomp'].items() if k in (k0, kc, k5, 'OoL · 250 gestores, ≥ 5 (peso igual)', 'ROIC alto descontado · 250 gestores, ≥ 5'))
hoje = ''.join(f'<tr><td class="l">{r[0]}</td><td class="l">{r[1]}</td><td class="n">{pc(r[2])}</td><td class="n">{r[3]}</td><td class="n">{"sim" if r[4] else "não"}</td></tr>' for r in d['hoje'][k5])
outros = ', '.join(f'{t} ({pc(v)})' for t, _, v in d['outro_exemplos'][:10])
gain_c = T[kc]['cagr'] - T[k0]['cagr']; gain_5 = T[k5]['cagr'] - T[k0]['cagr']
PRINT = '<style>td.l{white-space:normal}@media print{table{font-size:9.5px}th,td{white-space:normal;padding:3px 4px}.page{max-width:none}}</style>'
html = f'''<title>Gestores sem viés</title>
<meta name="claude:viewport-fit-sides" content="cover">
{css}{PRINT}
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>{d['periodo'][0][:7]} a {d['periodo'][1][:7]}</span></div>
<div class="kicker">Teste de robustez</div>
<h1>Sem o viés da lista de hoje, o filtro dos gestores não soma nada</h1>
<p class="deck">Com os 250 maiores gestores ativos de cada trimestre, inclusive os que fecharam, a Top 20 no universo dos gestores rende o mesmo que a Top 20 original. O ganho do teste anterior vinha de olhar só quem sobreviveu.</p>
<div class="byline">Todos os 13F da SEC (Form 13F Data Sets), 2016–2026 · S&amp;P 500 + médias e pequenas acima de US$ 2 bi · em dólares</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele define o filtro (ROIC ≥ 12%) e o P/E justo. Backtest, sem custos; não é recomendação.</p>
<div class="big">
 <div><b>{pc(T[k5]['cagr'])}</b><span>Top 20 nos 250 gestores (≥ 5), sem viés</span></div>
 <div><b>{pc(T[k0]['cagr'])}</b><span>Top 20 original (só S&amp;P), mesmo período</span></div>
 <div><b>{pc(T[kc]['cagr'])}</b><span>Top 20 com a lista do Navegando (com viés)</span></div>
 <div><b>{pc(gain_c - gain_5, 1).replace('%', ' p.p.')}</b><span>do ganho da lista de hoje era viés de sobrevivência</span></div>
</div>
<h2 class="chap" style="margin-top:40px">A regra dos gestores</h2>
<p class="method">Em cada trimestre, todos os declarantes de 13F (formulário original, o último por gestor e período). Gestor ativo: 20 a 400 posições em ações, as 10 maiores somando ≥ 25%, fora indexadores, bancos, corretoras, seguradoras, fundos de pensão, soberanos, fundações e empresas que declaram a própria tesouraria (lista por nome, ajustada antes de olhar retornos). Ficam os 250 maiores pelo valor da carteira. Número de gestores por ação = quantos deles a detêm com peso ≥ 0,2%, contado por emissor (CUSIP de 6 dígitos). Cada carteira usa o 13F do trimestre anterior. Em média, {d.get('nav_no_250', 74):.0f} dos 250 de cada trimestre estão na lista do Navegando US; os outros {250 - d.get('nav_no_250', 74):.0f} são os que a lista de hoje não vê, incluindo os que fecharam.</p>
<figure><figcaption class="t">Cobertura: 73% do dinheiro dos gestores tem dado; o que falta é quase todo estrangeiro ou fundo</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Universo ≥ 5 gestores (média por trimestre)</th><th>Valor</th></tr></thead><tbody>
<tr><td class="l">Ações por trimestre (com ≥ US$ 2 bi e dado)</td><td class="n">{d['universo']['5']:.0f} ({pc(d['universo_fora_sp']['5'], 0)} fora do S&amp;P)</td></tr>
<tr><td class="l">Com dado no modelo (S&amp;P, médias e pequenas, Visa e Berkshire)</td><td class="n">{pc(CV['com dado'], 0)}</td></tr>
<tr><td class="l">ADRs</td><td class="n">{pc(CV['ADR/estrangeira'], 0)}</td></tr>
<tr><td class="l">Estrangeiras sem ADR, ETFs e empresas fechadas (ex.: {outros})</td><td class="n">{pc(CV['sem dado (outro)'], 0)}</td></tr>
<tr><td class="l">Deslistadas depois (sem preço hoje)</td><td class="n">{pc(CV['deslistada depois'], 0)}</td></tr>
<tr><td class="l">Sem ticker</td><td class="n">{pc(CV['sem ticker'], 0)}</td></tr></tbody></table></div>
<div class="sowhat"><b>Limites</b><span>Se as ações americanas do universo sem dado tivessem entrado na carteira na proporção delas, o retorno da Top 20 ≥ 5 ficaria entre {pc(L['pessimista'])} (as que somem valendo zero) e {pc(L['otimista'])} (rendendo como o S&amp;P); no cenário neutro, {pc(L['neutro'])}.</span></div></figure>
<figure><figcaption class="t">As carteiras: o ganho some quando a lista de gestores deixa de ser a de hoje</figcaption>
<figcaption class="s">Raiz do valor de mercado com teto de 10% (OoL com peso igual), trimestral. Janelas = % das janelas móveis em que a carteira bate o S&amp;P 500; pior janela de 3 anos em p.p. ao ano.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Carteira</th><th>Retorno anual</th><th>Peso igual</th><th>Janelas 3a</th><th>5a</th><th>10a</th><th>Pior janela 3a</th><th>Pior queda</th><th>Volatilidade</th><th>Fora do S&amp;P</th><th>Giro trim.</th></tr></thead><tbody>{tab}</tbody></table></div>
<div class="sowhat"><b>E daí</b><span>Refeito com a mesma contagem por emissor, o teste com a lista de hoje dá {pc(T[kc]['cagr'])} na Top 20 e {pc(T['OoL · lista do Navegando, ≥ 5 (ramo C, com viés; peso igual)']['cagr'])} na OoL. Trocando a lista pelos 250 maiores de cada trimestre, os números voltam ao nível das carteiras originais: {pc(T[k5]['cagr'])} contra {pc(T[k0]['cagr'])} na Top 20 (diferença de {pc(d['diferenca'][k5]['media_aa'])} ao ano, t = {d['diferenca'][k5]['t']:.2f}), {pc(T['OoL · 250 gestores, ≥ 5 (peso igual)']['cagr'])} contra {pc(T['OoL · S&P (original, peso igual)']['cagr'])} na OoL. Depois de 15% de imposto sobre o ganho realizado: {pc(d['imposto'][k5])} contra {pc(d['imposto'][k0])}. Sem NVIDIA: {pc(d['sem_nvda']['sem'])}.</span></div></figure>
<figure><figcaption class="t">De onde veio o retorno (3 anos, anualizado)</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Carteira</th><th>Lucro (EPS)</th><th>Re-rating</th><th>Dividendos</th><th>Total</th></tr></thead><tbody>{dec}</tbody></table></div></figure>
<section class="verdict"><h2>O veredito</h2><p>A regra "Top 20 no universo dos gestores" não passou no critério registrado: sem o viés, ela não ficou acima da Top 20 original. A lista de hoje do Navegando US escolhe, sem querer, gestores que deram certo, e as ações deles também deram. Fica a Top 20 original como regra; o universo dos gestores pode servir como informação na hora de olhar uma ação, não como filtro.</p></section>
<figure><figcaption class="t">Hoje: a Top 20 nos 250 gestores (≥ 5)</figcaption><figcaption class="s">Composição em {d['hoje_data']}; gestores = quantos dos 250 detinham no 13F de junho de 2026. Lista completa do universo em universo_gestores_atual.csv.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Ação</th><th class="l">Empresa</th><th>Peso</th><th>Gestores</th><th>No S&amp;P?</th></tr></thead><tbody>{hoje}</tbody></table></div></figure>
<p class="method" style="margin-top:30px"><b>Ressalvas.</b> Estrangeiras sem ADR e ADRs ficaram fora (o modelo usa balanços americanos). Visa e Berkshire entraram com LPA aproximado (lucro ÷ ações equivalentes constantes). O painel de médias e pequenas parte das empresas listadas hoje; o efeito das deslistadas está cercado pelo teste de limites acima. Código: relatorio/f13_sec.py, gestores_sv_universo.py, ramo_gestores_sv.py.</p>
</div>'''
(ROOT / 'gestores_sem_vies.html').write_text(html); print('ok', len(html))
