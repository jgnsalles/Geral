"""Relatório FT do ramo N (combinações, anti-pânico, filho, indústrias, patamar). Saída: relatorio/filho.html"""
import json, pathlib
ROOT = pathlib.Path(__file__).parent
R = json.loads((ROOT / 'dados_filho.json').read_text()); I = json.loads((ROOT / 'dados_filho_ind.json').read_text())
PT = json.loads((ROOT / 'dados_filho_patamar.json').read_text())
css = (ROOT / 'qualidade_que_compoe.html').read_text(); css = css[css.index('<link'):css.index('</style>') + len('</style>')]
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
pp = lambda x, n=1: '—' if x is None else f'{x * 100:+.{n}f}'.replace('.', ',') + ' p.p.'
res = R['res']
BASE = {'Top 20': 'Top 20 (aplicada: ≥ US$ 20 bi)', 'Especiais': 'Especiais (aplicada: peso × nota)', 'Excepcionais': 'Excepcionais (atual)'}


def verdict(k):
    fam = 'Top 20' if k.startswith('Top 20') or k == 'Filho' else 'Especiais' if k.startswith('Especiais') else 'Excepcionais'
    b = res[BASE[fam]]; m = res[k]
    if k == BASE[fam]: return fam, '—'
    ok = (m['cagr'] >= b['cagr'] - .005 and m['w3'] >= b['w3'] - 1e-9 and m['maxdd'] >= b['maxdd'] - 1e-9
          and m['c_a'] >= b['c_a'] - .01 and m['c_b'] >= b['c_b'] - .01)
    neutral = ok and abs(m['cagr'] - b['cagr']) < .002 and abs(m['maxdd'] - b['maxdd']) < .002
    return fam, ('sim (neutra)' if neutral else 'sim') if ok else 'não'


rows = []
for k, m in res.items():
    fam, v = verdict(k)
    rows.append(f'<tr><td class="l">{k}</td><td class="n">{pc(m["cagr"])}</td><td class="n">{pc(m["c_a"])}</td><td class="n">{pc(m["c_b"])}</td>'
                f'<td class="n">{pc(m["maxdd"],0)}</td><td class="n">{pc(m["w3"],0)}</td><td class="n">{pc(m["sev"])}</td><td class="l">{v}</td></tr>')
irows = ''.join(f'<tr><td class="l">{r["industry"]}</td><td class="n">{int(r["n"])}</td><td class="n">{pc(r["perd"],0)}</td><td class="n">{pc(r["queda"],0)}</td><td class="n">{pc(r["med"],0)}</td>'
                f'<td class="n">{pp(I["eff"][r["industry"]][0]) if r["industry"] in I["eff"] else "—"}</td><td class="n">{pp(I["eff"][r["industry"]][1]) if r["industry"] in I["eff"] else "—"}</td></tr>'
                for r in I['ind'])
prow = ''.join(f'<tr><td class="l">{t}</td><td class="n">{pc(v["pat"],0)}</td><td class="n">{v["mult"]:.1f}×</td><td class="n">{pc(v["hist"],0)}</td><td class="n">{pc(v["ind_med"],0)}</td><td class="l">{"⚠ salto acima do histórico" if v["alerta"] else ""}</td></tr>'.replace('.', ',', 1) if False else
               f'<tr><td class="l">{t}</td><td class="n">{pc(v["pat"],0)}</td><td class="n">{str(round(v["mult"],1)).replace(".",",")}×</td><td class="n">{pc(v["hist"],0)}</td><td class="n">{pc(v["ind_med"],0)}</td><td class="l">{"⚠ salto acima do histórico" if v["alerta"] else ""}</td></tr>'
               for t, v in PT['sel'].items() if v['pat'] is not None)
ic = R['ic']; sp = R['spy']
html = f'''<title>O filho de Buffett, Simons e Greenblatt</title>
<meta name="claude:viewport-fit-sides" content="cover">
{css}
<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Combinações, anti-pânico e patamar · 22/11/2026</span></div>
<div class="kicker">Revisão de PM</div>
<h1>Juntar bons sinais não bateu a regra simples</h1>
<p class="deck">Testamos 30 combinações: nota composta ao estilo Simons, grupos com a escadinha, filtros anti-pânico e um "filho" de Buffett, Simons e Greenblatt. Nenhuma superou a Top 20 e a Especiais atuais pela restrição dura. A regra que já temos é, ela mesma, uma combinação enxuta que funciona.</p>
<div class="byline">S&amp;P 500 point-in-time, 2011–2026, crescimento histórico, ROIC triangulado · descoberta 2012–2018, confirmação 2019–2026 · S&amp;P: {pc(sp["cagr"])} a.a. ({pc(sp["c_a"])} / {pc(sp["c_b"])})</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra no corte de qualidade, no P/E justo, na nota de boa empresa e em três dos oito sinais da nota composta. Backtest sem custos de transação; não é recomendação. Nada foi alterado na planilha, no painel ou nas carteiras: tudo aqui são propostas.</p>
<figure><figcaption class="t">Mudança → passou? (restrição dura + não perder mais de 1 p.p. em nenhum subperíodo)</figcaption>
<figcaption class="s">Retorno anual no período todo e nos dois subperíodos, pior queda, % das janelas de 3 anos acima do S&amp;P e % de posições que caem 30% ou mais em 1 ano.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Variante</th><th>Retorno</th><th>2012–18</th><th>2019–26</th><th>Pior queda</th><th>Jan. 3a</th><th>Quedas ≥30%</th><th class="l">Passou?</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<div class="sowhat"><b>E daí</b><span>A nota composta com pesos iguais (S0) perde 1,8 p.p. na Top 20 e 3,3 p.p. na Especiais. A versão com pesos tirados de 2012–2018 (SW) chega a 21,1% na Top 20 (contra 20,7%), mas aumenta a pior queda de −30% para −36%, então não passa. Os grupos com escadinha (G1, G2) caem para 14–16% ao ano: a escadinha seleciona empresas "bonitas" que já estão caras. O anti-pânico corta 1 a 2 p.p. em todas as versões: o pânico, na média, NÃO estava certo nas carteiras (estava certo na lista "Ótima em pânico", que não tinha o filtro de preço). O filho rendeu 17,3%.</span></div>
</figure>
<figure><figcaption class="t">Por que a nota composta não ajuda: dentro das já escolhidas, quase nada ordena o futuro</figcaption>
<figcaption class="s">Correlação de ordem média (2012–2018) entre cada sinal e o retorno dos 4 trimestres seguintes, entre as elegíveis da Top 20.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Sinal</th><th>IC</th></tr></thead><tbody>{"".join(f'<tr><td class="l">{k[2:]}</td><td class="n">{str(round(v,3)).replace(".",",")}</td></tr>' for k,v in ic.items())}</tbody></table></div>
<div class="sowhat"><b>E daí</b><span>Depois do filtro de qualidade, os sinais têm correlação perto de zero (o maior é o ROIC, 0,06). É o "sinal fraco" de Simons, mas Simons opera milhares de ativos e giro altíssimo; com 20 ações por trimestre o ruído domina. O ganho da estratégia vem do filtro (ROIC + crescimento + preço) e do peso pelo tamanho, não da ordem fina.</span></div>
</figure>
<figure><figcaption class="t">Indústrias: mais quedas fortes não significa pior carteira</figcaption>
<figcaption class="s">Posições das 3 carteiras aplicadas (média de todas: {pc(I["base"]["perd"],0)} perdedoras, {pc(I["base"]["queda"],0)} quedas ≥ 30%). Efeito de excluir a indústria no retorno anual da Top 20 e da Especiais.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Indústria</th><th>Posições</th><th>Perdedoras (&lt;−10%)</th><th>Quedas ≥30%</th><th>Retorno mediano 1a</th><th>Excluir: Top 20</th><th>Excluir: Especiais</th></tr></thead><tbody>{irows}</tbody></table></div>
<div class="sowhat"><b>Em uma frase</b><span>Software aplicativo, hardware, autopeças e varejo amplo caem forte 2 a 3 vezes mais que a média, mas excluí-las não melhora o retorno (−0,8 a +0,3 p.p.), porque as vencedoras dessas indústrias compensam; biotecnologia e semicondutores não são perigosas para esta estratégia (excluir custaria ~1 p.p.).</span></div>
</figure>
<figure><figcaption class="t">"Salto de patamar": quanto o lucro precisa subir de nível</figcaption>
<figcaption class="s">Mediana do EPS projetado (2026–28) ÷ mediana do EPS de 2022–25, anualizado em 3 anos; comparado com a mediana dos crescimentos históricos (só 2022–25 no arquivo v4) e com a mediana da indústria. Dados da planilha do usuário.</figcaption>
<div class="tablebox"><table><thead><tr><th class="l">Ação</th><th>Crescimento necessário</th><th>Lucro vezes</th><th>Histórico</th><th>Indústria</th><th class="l">Alerta</th></tr></thead><tbody>{prow}</tbody></table></div>
<div class="sowhat"><b>E daí</b><span>A LLY precisa de 76% ao ano por 3 anos (lucro 5,5× maior entre os centros), 5× a indústria. Só não dispara o alerta porque o histórico de 2022–25 já foi explosivo (96%). Com o histórico de 5 anos (2021–25, que a planilha nova puxa), a mediana da LLY cai para ~13% e o alerta dispara. MA, V, TDG e COST mostram o que é "redondo": o salto necessário é quase igual ao histórico. Corte proposto: alerta quando o salto passar o maior entre histórico e indústria em 15 p.p. e for 1,5× maior; com o arquivo v4 isso marca {PT["n_alerta"]} de {PT["n"]} ações (fica mais seletivo com 5 anos de histórico). Não dá para backtestar (não há consenso histórico).</span></div>
</figure>
<section class="verdict"><h2>Propostas (nada aplicado; decisão sua)</h2><div class="vgrid">
<div><span class="tag" style="--c:var(--teal)">Proposta 1</span><h4>Coluna e alerta "salto de patamar"</h4><p>Informativa na planilha e no painel. Muda só o que aparece na Central de alertas; não mexe nas carteiras.</p></div>
<div><span class="tag" style="--c:var(--oxford)">Proposta 2</span><h4>Manter as carteiras como estão</h4><p>Nenhuma combinação passou. A Top 20 (≥ US$ 20 bi) e a Especiais (peso × nota) seguem as melhores pela restrição dura.</p></div>
<div><span class="tag" style="--c:var(--wheat)">Proposta 3</span><h4>Nota composta e escadinha como colunas de leitura</h4><p>Ajudam a julgar "orgulho de ter", mas não ordenam o retorno. Ficariam como informação na ficha.</p></div>
<div><span class="tag" style="--c:var(--claret)">Não fazer</span><h4>Excluir pânico ou indústrias</h4><p>Custa 1 a 2 p.p. ao ano. A queda de 12 meses não separa perdedoras nas carteiras.</p></div>
</div></section>
<p class="method" style="margin-top:30px"><b>Método.</b> Pré-registro no PROTOCOLO (ramo N). Nota composta = média de percentis por data no universo: ROIC, spread sobre a mediana da indústria, escadinha do EPS, min(crescimento, 35%), retorno esperado, log do valor, −zGrowth, nota de boa empresa (+ momento de 12 meses nas versões S+/S−). Pesos SW ∝ max(IC, 0) medidos só em 2012–2018. Carteiras com 8 ações por setor, teto de 10% por ação e 40% por setor. Código: relatorio/filho.py, filho_ind.py, filho_patamar.py.</p>
</div>'''
(ROOT / 'filho.html').write_text(html)
print('ok', len(html))
