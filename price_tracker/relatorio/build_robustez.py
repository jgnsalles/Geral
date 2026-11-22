"""Relatório FT do ramo M (robustez, Nota de boa empresa, oportunidades): relatorio/robustez.html.
Lê dados_robustez*.json (backtests) e painel/modelo_embutido.json (listas de hoje)."""
import json, pathlib, html
ROOT = pathlib.Path(__file__).parent
J = lambda n: json.loads((ROOT / n).read_text())
d1, d2, d3, dc, di = J('dados_robustez.json'), J('dados_robustez2.json'), J('dados_robustez3.json'), J('dados_robustez_combo.json'), J('dados_robustez_ind.json')
M = json.loads((ROOT.parent / 'painel' / 'modelo_embutido.json').read_text()); S = M['stocks']
css = (ROOT / 'qualidade_que_compoe.html').read_text(); css = css[css.index('<link'):css.index('</style>') + len('</style>')]
css = css.replace('</style>', '.pass{color:var(--teal);font-weight:700}.fail{color:var(--claret);font-weight:700}.info{color:var(--ink2)}'
                  '.f{font-family:var(--f-num);font-size:13px;background:var(--paper2);padding:10px 12px;display:block;white-space:pre-wrap;line-height:1.5}</style>')
e = html.escape
pc = lambda x, n=1: '—' if x is None else f'{x * 100:.{n}f}%'.replace('.', ',')
isn = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)


def get(name):
    for D in (d1['res'], d3, d2, dc, di):
        if name in D and D[name]: return D[name].get('res', D[name]) if isinstance(D[name], dict) else D[name]
    return None


base = {'Top 20': get('Top 20 (atual)'), 'Especiais': get('Especiais (atual)'), 'Excepcionais': get('Excepcionais (atual)')}


def verdict(m, b):
    if m is None or b is None: return None
    return (m['cagr'] >= b['cagr'] - 0.005) and (m['w3'] >= b['w3'] - 1e-9) and (m['maxdd'] >= b['maxdd'] - 1e-9)


ROWS = [  # (grupo, rótulo, chave, onde fica)
    ('Top 20', 'Atual', 'Top 20 (atual)', ''),
    ('Top 20', 'Valor ≥ US$ 20 bi', 'Top 20 · ≥ US$ 20 bi', 'Aplicada na Top 20'),
    ('Top 20', 'Valor ≥ US$ 50 bi', 'Top 20 · ≥ US$ 50 bi', 'Só a lista Compounders usa US$ 50 bi'),
    ('Top 20', 'Consistência (≥ 4 de 5 anos de alta, zGrowth ≤ 1)', 'Top 20 · consistência', 'Informativa'),
    ('Top 20', 'Escadinha ≥ 60', 'Top 20 · escadinha ≥ 60', 'Informativa (coluna Escad.)'),
    ('Top 20', 'Nota ≥ 3,5 como filtro (N1)', 'Top 20 · N1 filtro ≥ 3,5', 'Informativa'),
    ('Top 20', 'Nota na ordem (N2)', 'Top 20 · N2 ordem', 'Informativa'),
    ('Top 20', 'Nota no peso (N3)', 'Top 20 · N3 peso', 'Não aplicada: somada ao piso dá resultado pior que só o piso'),
    ('Top 20', 'Piso de US$ 20 bi + nota no peso', 'Top 20 · ≥ US$ 20 bi + N3 peso', 'Não aplicada (pior que só o piso)'),
    ('Top 20', 'Sem Application Software', 'Top 20 sem Application Software', 'Decisão sua (ver seção 5)'),
    ('Top 20', 'Sem as 3 indústrias perigosas', 'Top 20 sem 3 perigosas', 'Informativa'),
    ('Especiais', 'Atual', 'Especiais (atual)', ''),
    ('Especiais', 'Valor ≥ US$ 20 bi', 'Especiais · ≥ US$ 20 bi', 'Informativa'),
    ('Especiais', 'Valor ≥ US$ 50 bi', 'Especiais · ≥ US$ 50 bi', 'Informativa'),
    ('Especiais', 'Consistência', 'Especiais · consistência', 'Informativa'),
    ('Especiais', 'Escadinha ≥ 60', 'Especiais · escadinha ≥ 60', 'Informativa'),
    ('Especiais', 'Nota ≥ 3,5 como filtro (N1)', 'Especiais · N1 filtro', 'Informativa'),
    ('Especiais', 'Nota na ordem (N2)', 'Especiais · N2 ordem', 'Informativa'),
    ('Especiais', 'Nota no peso (N3)', 'Especiais · N3 peso', 'Aplicada nas Especiais'),
    ('Especiais', 'Sem Application Software', 'Especiais sem Application Software', 'Decisão sua (ver seção 5)'),
    ('Especiais', 'Sem as 3 indústrias perigosas', 'Especiais sem 3 perigosas', 'Informativa'),
    ('Excepcionais', 'Atual', 'Excepcionais (atual)', ''),
    ('Excepcionais', 'Nota ≥ 3,5 como filtro (N1)', 'Excepcionais · N1 filtro', 'Informativa'),
    ('Excepcionais', 'Nota no peso (N3)', 'Excepcionais · N3 peso', 'Informativa'),
]
trs = []; NT = NP = 0
for g, lab, k, onde in ROWS:
    m = get(k) or get(k.replace('sem 3 perigosas', 'sem 3 perigosas'))
    if m is None: continue
    v = verdict(m, base[g]) if onde else None
    NT += bool(onde); NP += bool(onde and v)
    vt = '—' if not onde else ('<span class="pass">passou</span>' if v else '<span class="fail">não passou</span>')
    w3m = m.get('w3min')
    trs.append(f'<tr><td class="l">{g}</td><td class="l">{e(lab)}</td><td class="n">{pc(m["cagr"])}</td><td class="n">{pc(m["maxdd"])}</td><td class="n">{pc(m["w3"], 0)}</td>'
               f'<td class="n">{pc(m.get("w5"), 0)}</td><td class="n">{pc(m.get("w10"), 0)}</td><td class="n">{"—" if w3m is None else f"{w3m * 100:+.1f}".replace(".", ",") + " p.p."}</td>'
               f'<td class="n">{pc(m.get("sev"))}</td><td class="n">{vt}</td><td class="l">{e(onde) if onde else "<i>base</i>"}</td></tr>')
dec_tbl = ('<table><thead><tr><th class="l">Carteira</th><th class="l">Mudança</th><th>Retorno a.a.</th><th>Pior queda</th><th>Jan. 3 anos &gt; S&amp;P</th><th>5 anos</th><th>10 anos</th>'
           '<th>Pior jan. 3 anos</th><th>Quedas ≥ 30% (4 tri)</th><th>Passou?</th><th class="l">Onde fica</th></tr></thead><tbody>' + ''.join(trs) + '</tbody></table>')

obs = [('Compounders redondos (carteira)', get('Compounders redondos')), ('Quase lá → entra quando o retorno chega a 20%', get('Quase lá → entra (ret ≥ 20%)')),
       ('Pequenas que compõem (carteira)', get('Pequenas que compõem')), ('Ótima em pânico (carteira)', get('Ótima em pânico'))]
obs_tbl = ('<table><thead><tr><th class="l">Lista testada como carteira</th><th>Retorno a.a.</th><th>Pior queda</th><th>Jan. 3 anos &gt; S&amp;P</th><th>Ações em média</th><th class="l">Uso</th></tr></thead><tbody>' +
           ''.join(f'<tr><td class="l">{e(n)}</td><td class="n">{pc(m["cagr"])}</td><td class="n">{pc(m["maxdd"])}</td><td class="n">{pc(m["w3"], 0)}</td><td class="n">{m["n"]:.1f}</td><td class="l">Só observação</td></tr>'.replace('.', ',', 0)
                   for n, m in obs if m) + '</tbody></table>')

b9 = d1['bench9']; order = ['S&P 500', 'S&P 500 equal weight', 'OoL antigo', 'GCGR antigo', 'OoL novo', 'GCGR novo', 'OoL High ROIC (novo)', 'OoL High Growth (novo)', 'Cyclicals']
b9_tbl = ('<table><thead><tr><th class="l">Comparativo</th><th>Retorno a.a.</th><th>Jan. 3 anos &gt; S&amp;P</th><th>5 anos</th><th>10 anos</th></tr></thead><tbody>' +
          ''.join(f'<tr><td class="l">{e(k)}</td><td class="n">{pc(b9[k][0])}</td><td class="n">{pc(b9[k][1], 0)}</td><td class="n">{pc(b9[k][2], 0)}</td><td class="n">{pc(b9[k][3], 0)}</td></tr>' for k in order if k in b9) +
          ''.join(f'<tr><td class="l"><b>{e(k)}</b></td><td class="n">{pc(m["cagr"])}</td><td class="n">{pc(m["w3"], 0)}</td><td class="n">{pc(m["w5"], 0)}</td><td class="n">{pc(m["w10"], 0)}</td></tr>'
                  for k, m in (('Top 20 nova (piso US$ 20 bi)', get('Top 20 · ≥ US$ 20 bi')), ('Especiais nova (peso × nota)', get('Especiais · N3 peso')))) + '</tbody></table>')

# gráfico: NAV mensal
nav = d1['nav']; ser = nav['series']; dates = nav['dates']
keys = [('S&P 500', 'var(--slate)'), ('Top 20 (atual)', 'var(--oxford)'), ('Top 20 · ≥ US$ 20 bi', 'var(--teal)'), ('Especiais (atual)', 'var(--claret)'), ('Compounders redondos', 'var(--wheat)')]
W, H, L_, R_, T_, B_ = 980, 340, 54, 170, 14, 28
vmax = max(max(x for x in ser[k] if x is not None) for k, _ in keys); top = 5 * (int(vmax / 5) + 1)
X = lambda i: L_ + (W - L_ - R_) * i / (len(dates) - 1); Y = lambda v: T_ + (H - T_ - B_) * (1 - v / top)
svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Retorno acumulado">'
for t in range(0, top + 1, 5):
    svg += f'<line x1="{L_}" x2="{W - R_}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="var(--rule)" stroke-width="0.6"/><text class="num" x="{L_ - 6}" y="{Y(t) + 4:.1f}" text-anchor="end" style="font-size:11px" fill="var(--ink2)">{t}×</text>'
for i, dt in enumerate(dates):
    if dt[5:7] == '12' and int(dt[:4]) % 2 == 1:
        svg += f'<text class="num" x="{X(i):.1f}" y="{H - 8}" text-anchor="middle" style="font-size:11px" fill="var(--ink2)">{int(dt[:4]) + 1}</text>'
for k, col in keys:
    pts = [(X(i), Y(v)) for i, v in enumerate(ser[k]) if v is not None]
    svg += f'<polyline fill="none" stroke="{col}" stroke-width="{2.2 if "Top 20 ·" in k else 1.6}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>'
    svg += f'<text x="{pts[-1][0] + 6:.1f}" y="{pts[-1][1] + 4:.1f}" style="font-size:12px" fill="{col}">{e(k)} {ser[k][-1]:.1f}×</text>'.replace('.', ',', 1) if False else \
        f'<text x="{pts[-1][0] + 6:.1f}" y="{pts[-1][1] + 4:.1f}" style="font-size:12px" fill="{col}">{e(k.replace(" (atual)", ""))} · {str(round(ser[k][-1], 1)).replace(".", ",")}×</text>'
svg += '</svg>'
# separa rótulos sobrepostos (ordem vertical)
import re
labs = sorted([(float(m.group(2)), m.group(0)) for m in re.finditer(r'<text x="([\d.]+)" y="([\d.]+)" style="font-size:12px"[^>]*>.*?</text>', svg)])
last = -99
for y, t in labs:
    ny = max(y, last + 15); svg = svg.replace(t, t.replace(f'y="{y:.1f}"', f'y="{ny:.1f}"'), 1); last = ny

# listas de hoje
tk = lambda L: ', '.join(L)
top20 = sorted([s for s in S if isn(s.get('wt'))], key=lambda s: -s['wt']); esp = sorted([s for s in S if isn(s.get('we'))], key=lambda s: -s['we'])
row = lambda s, extra: f'<tr><td class="l"><b>{s["t"]}</b></td><td class="l">{e(s["nm"][:34])}</td><td class="n">{str(round(s["nota"], 1)).replace(".", ",") if isn(s.get("nota")) else "—"}</td><td class="n">{pc(s.get("ru"), 0)}</td><td class="n">{pc(s.get("gc"), 0)}</td><td class="n">{pc(s.get("ret"), 0)}</td>{extra(s)}<td class="l" style="color:var(--claret);font-size:13px">{e(s.get("flag") or "")}</td></tr>'
hd = lambda x: f'<table><thead><tr><th class="l">Ação</th><th class="l">Empresa</th><th>Nota</th><th>ROIC</th><th>Cresc.</th><th>Retorno</th>{x}<th class="l">Alerta</th></tr></thead><tbody>'
T20 = hd('<th>Peso</th>') + ''.join(row(s, lambda s: f'<td class="n">{pc(s["wt"])}</td>') for s in top20) + '</tbody></table>'
TES = hd('<th>Peso</th>') + ''.join(row(s, lambda s: f'<td class="n">{pc(s["we"])}</td>') for s in esp) + '</tbody></table>'
comp = sorted([s for s in S if s.get('comp') == 1], key=lambda s: -(s['ret'] or 0))
TCO = hd('<th>Valor US$ bi</th><th>Falta cair</th>') + ''.join(row(s, lambda s: f'<td class="n">{s["mc"]:,.0f}</td><td class="n">{pc(s["falta"], 0) if isn(s.get("falta")) and s["falta"] < 0 else "—"}</td>'.replace(',', '.')) for s in comp) + '</tbody></table>'
ql = sorted([s for s in S if s.get('ql') == 1], key=lambda s: -s['falta'])
TQL = hd('<th>Preço</th><th>Entrada (20%)</th><th>Falta cair</th>') + ''.join(row(s, lambda s: f'<td class="n">{s["px"]:.0f}</td><td class="n">{s["pent"]:.0f}</td><td class="n">{pc(s["falta"], 0)}</td>') for s in ql) + '</tbody></table>'
pan = sorted([s for s in S if s.get('pan') == 1], key=lambda s: s['v12'])
TPA = hd('<th>12 meses</th><th>EPS último ano</th>') + ''.join(row(s, lambda s: f'<td class="n">{pc(s["v12"], 0)}</td><td class="n">{pc((s.get("er") or [None] * 8)[7], 0)}</td>') for s in pan) + '</tbody></table>'
peq = sorted([s for s in S if s.get('peq') == 1], key=lambda s: -(s['ret'] or 0))
TPQ = hd('<th>Valor US$ bi</th>') + ''.join(row(s, lambda s: f'<td class="n">{s["mc"]:.0f}</td>') for s in peq) + '</tbody></table>'
lly = next(s for s in S if s['t'] == 'LLY')
nf = sum(len(str(s['flag']).split(' · ')) for s in S if s.get('flag'))


def inany(s):
    return any(isn(s.get(k)) for k in ('wt', 'we', 'wj', 'wx')) or any(s.get(k) == 1 for k in ('comp', 'ql', 'pan', 'peq', 'hr', 'hg')) or (s.get('cls') in ('Opportunity of Lifetime', 'Good Companies, Great Returns') and not s.get('dup'))


na = sum(len(str(s['flag']).split(' · ')) for s in S if s.get('flag') and inany(s))
ind = d1['ind'][:8]
ind_tbl = ('<table><thead><tr><th class="l">Indústria (GICS)</th><th>Posições</th><th>Quedas ≥ 30%</th><th>× média 2012–18</th><th>× média 2019–26</th><th>Retorno 1 ano (mediana)</th></tr></thead><tbody>' +
           ''.join(f'<tr><td class="l">{e(r["industry"])}</td><td class="n">{r["n"]}</td><td class="n">{pc(r["sev"])}</td><td class="n">{"—" if not isn(r["lift_a"]) else str(round(r["lift_a"], 1)).replace(".", ",")}</td>'
                   f'<td class="n">{"—" if not isn(r["lift_b"]) else str(round(r["lift_b"], 1)).replace(".", ",")}</td><td class="n">{pc(r["med"], 0)}</td></tr>' for r in ind) + '</tbody></table>')
bio = d1['bio']

FORM = '''Nota de boa empresa = média de C1 a C7 (as que existirem), cada uma de 1 a 5. WACC = 8,5%.
C1 ROIC vs pares   spread = ROIC − mediana do ROIC da indústria (planilha inteira)
                   nota = 1 + 4 × PERCENTRANK(spread); máximo 3 se ROIC < WACC + 10 p.p. ou ROIC < 1,5 × mediana
C2 ROIC incremental (ROIC marginal = Δ NOPAT ÷ reinvestimento)
                   5 se ≥ 0,8 × ROIC e ≥ WACC · 4 se ≥ 0,5 × ROIC · 3 se ≥ WACC (ou sem dado) · 2 se ≥ 0 · 1 se < 0
C3 Pista marginal  g implícito = (WACC × P/L − 1) ÷ (P/L − 1/mín(ROIC; 1))
                   pista = mín(crescimento do consenso; 15%) − g implícito
                   5 se ≥ +5 p.p. ou P/L < 1/ROIC · 4 se ≥ +2 · 3 se ≥ 0 · 2 se ≥ −3 · 1 abaixo · 1 se P/L ≤ 0
                   (g sustentável = Δ capital ÷ Σ NOPAT × ROIC incremental: só informação)
C4 Moat            ROIC dos 4 anos: 5 se todos ≥ 20% e o pior ≥ 70% da média · 4 se todos ≥ 15% · 3 se todos ≥ WACC
                   · 2 se mais da metade ≥ WACC · 1 senão; +1 (máx. 5) se ROIC sem ágio e intangíveis ≥ 40%
C5 Gestão por ação 3 + 1 se nº de ações cai ≥ 1% a.a. − 1 se sobe ≥ 2% a.a. + 1 se ágio cresce menos que o lucro operacional
                   − 1 se cresce mais de 1,2× (só planilha: sem histórico no backtest)
C6 Existir 15 anos 1 se cíclica; senão 1 + EPS > 0 em todos os anos (≥ 6) + dívida ≤ 2 × lucro operacional (financeira conta)
                   + escadinha ≥ 70 + valor ≥ US$ 10 bi
C7 Qualitativa     sua nota de 1 a 5 na aba Regras (tabela "Nota qualitativa"); vazia não entra
Escadinha (0–100)  sobre os 8 crescimentos anuais do EPS (mín. 6): 40 × % de altas + 20 × maior sequência ÷ n
                   + 20 × (nenhum ano < −10%) + 20 × máx(0; 1 − mín(1; desvio ÷ mediana ÷ 1,5)); zero se mediana ≤ 0
Teste de compounder ROIC sem ágio ≥ 30% e lucro operacional crescendo ≥ 10% em pelo menos 2 dos 3 anos (selo, não entra na nota)
Backtest           usa C1, C2, C3, C4 e C6 (versão histórica); nas Especiais o peso é raiz(valor de mercado) × nota sem C5/C7.'''
LISTF = '''Compounders redondos  valor ≥ US$ 50 bi · nota ≥ 4 · sem cíclica, vestuário, consenso atípico sem apoio ou step change reprovado
Quase lá              compounder · retorno < 20% · falta cair ≥ −30%
                      preço de entrada = P/E justo × EPS 2027 × fator ÷ (1 + 2 × 20% − retorno a múltiplo constante − dividend yield)²
Ótima em pânico       nota ≥ 3,5 · queda ≥ 25% em 12 meses · EPS do último ano subiu · crescimento previsto > 0
Pequenas que compõem  valor US$ 2–30 bi · nota ≥ 4 · crescimento ≥ 12% · P/L ≤ 1,3 × P/E justo
Consenso acima da história   consenso > máx(mediana do crescimento histórico do EPS; mediana do lucro operacional) + 10 p.p.
Consenso atípico sem apoio   um ano do consenso se afasta da mediana mais que máx(30 p.p.; |mediana|) e o lucro operacional não sustenta
Step change           EPS 2028 ≥ 1,8 × EPS 2025 → retorno com fade (múltiplo maduro, g 4,5%) e com devolução de 1/3 do salto; reprova se < −10%'''

body = f'''<div class="page">
<div class="mast"><span>Price Tracker · Mercados</span><span>Robustez e Nota de boa empresa · {d1['periodo'][0][:7]} a {d1['periodo'][1][:7]}</span></div>
<div class="kicker">O que muda nas carteiras e o que vira lista de observação</div>
<h1>Duas mudanças entram nas carteiras; o resto vira alerta ou lista de observação</h1>
<p class="deck">De {NT} variantes testadas, {NP} mantiveram retorno, janelas de 3 anos e pior queda. Apliquei duas: piso de US$ 20 bi na Top 20 e peso pela Nota de boa empresa nas Especiais. As outras que passaram eram redundantes com essas ou dependem de uma decisão sua. A limpeza do consenso e o corte da LLY não têm como ser testados no passado e ficaram como alerta. Compounders, Quase lá, Ótima em pânico e Pequenas viraram listas de observação, porque como carteira rendem abaixo do S&amp;P.</p>
<div class="byline">S&amp;P 500 point-in-time · crescimento histórico · ROIC triangulado · rebalanceamento trimestral · regras pré-registradas no PROTOCOLO</div>
<p class="warn"><b>⚠️ O ROIC pode estar errado.</b> Ele entra no corte de qualidade, no P/E justo e em quatro das sete notas (C1–C4). Uma revisão do ROIC pode mudar todas as conclusões abaixo.</p>
<div class="big">
 <div><b>{NP} de {NT}</b><span>variantes passaram na regra (retorno ≥ atual − 0,5 p.p., janelas de 3 anos e pior queda iguais ou melhores); 2 aplicadas</span></div>
 <div><b>{pc(get('Top 20 · ≥ US$ 20 bi')['maxdd'], 0)}</b><span>pior queda da Top 20 com o piso de US$ 20 bi (antes {pc(base['Top 20']['maxdd'], 0)}), com o mesmo retorno</span></div>
 <div><b>{len(comp)}</b><span>compounders redondos hoje; {len(ql)} estão "quase lá"</span></div>
 <div><b>{na} de {nf}</b><span>alertas que a Central mostra (só ações em alguma lista)</span></div>
</div>

<h2 class="chap" style="margin-top:40px">1. Mudança por mudança</h2>
<figure><figcaption class="t">Piso de US$ 20 bi e peso pela nota passaram; filtros de nota, escadinha e consistência derrubam o retorno</figcaption>
<figcaption class="s">Regra do usuário: passa se retorno ≥ atual − 0,5 p.p. ao ano, % de janelas de 3 anos acima do S&amp;P ≥ atual e pior queda não pior. Quedas ≥ 30% = posições que caíram 30% ou mais nos 4 trimestres seguintes.</figcaption>
<div class="tablebox">{dec_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Os filtros de "qualidade bonita" (nota ≥ 3,5, escadinha, consistência) tiram justamente as ações com lucro irregular que mais subiram: a Top 20 cai de {pc(base['Top 20']['cagr'])} para 17–20% ao ano. Usar a nota para dar peso, sem tirar ninguém, custa 0,1 p.p. nas Especiais e mantém tudo o mais. O piso de US$ 20 bi tira as pequenas mais arriscadas da Top 20 e reduz a pior queda em 4 p.p. O de US$ 50 bi rende mais (22,6%), mas perde uma janela de 3 anos e por isso não passou.</span></div>
<div class="src">Fonte: relatorio/robustez.py, robustez2.py, robustez3.py; testes extras do piso com nota e das indústrias.</div></figure>

<figure><figcaption class="t">Com o piso, a Top 20 fica igual em retorno e mais rasa nas quedas</figcaption>
<figcaption class="s">Retorno total acumulado (1 = início), mensal. A carteira de Compounders redondos aparece para mostrar por que ela ficou como lista.</figcaption>
<div class="tablebox">{svg}</div>
<div class="src">S&amp;P 500 = SPY com dividendos.</div></figure>

<h2 class="chap">2. Os nove comparativos</h2>
<figure><figcaption class="t">As carteiras novas seguem acima de todos os comparativos em todas as janelas de 5 e 10 anos</figcaption>
<figcaption class="s">Retorno anual e % das janelas móveis que batem o S&amp;P 500.</figcaption>
<div class="tablebox">{b9_tbl}</div></figure>

<h2 class="chap">3. Listas de observação</h2>
<figure><figcaption class="t">Como carteira, nenhuma das listas novas bate o S&amp;P</figcaption>
<figcaption class="s">Mesmo período e mesma régua. Por isso aparecem no painel como observação, sem peso e sem mudar as carteiras.</figcaption>
<div class="tablebox">{obs_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Comprar "a melhor empresa grande" quando ela fica barata (Quase lá → entra) rendeu {pc(get('Quase lá → entra (ret ≥ 20%)')['cagr'])} ao ano: os compounders raramente chegam a 20% de retorno esperado, e quando chegam costuma ser por um motivo. As listas servem para estudar, não para comprar no automático.</span></div></figure>

<h2 class="chap">4. LLY e o step change</h2>
<p class="prose">O consenso prevê EPS de 2028 {str(round(1 + lly['gc'], 2)).replace('.', ',')}× ao ano acima de 2025 (crescimento de {pc(lly['gc'], 0)}). O teto de credibilidade não pega a LLY, porque o histórico também é explosivo (teto de {pc(lly['gcap'], 0)}). A regra de step change pega: retorno-base {pc(lly['ret'], 0)}; se o múltiplo voltar ao P/E justo maduro ({str(round(lly['pejlt'], 1)).replace('.', ',')}) o retorno vai a {pc(lly['rfade'], 0)}; se, além disso, um terço do salto do lucro for devolvido, a {pc(lly['rdev'], 0)}. Pela regra a LLY sairia das carteiras. Mas não existe consenso histórico para testar a regra, então pela sua restrição ela <b>fica como alerta</b> e a LLY continua com 10% na Top 20 e nas Especiais. A chave <b>Limpeza do consenso nas carteiras</b> (aba Regras) liga a exclusão se você quiser.</p>

<h2 class="chap">5. Indústrias perigosas</h2>
<figure><figcaption class="t">Só Application Software passa sozinha na regra, por pouco; biotecnologia não é perigosa</figcaption>
<figcaption class="s">Posições das carteiras principais; queda ≥ 30% nos 4 trimestres seguintes. Média: {pc(d1['base_sev']['a'])} em 2012–18 e {pc(d1['base_sev']['b'])} em 2019–26. Perigosa = ≥ 1,5× a média nos dois períodos e n ≥ 30.</figcaption>
<div class="tablebox">{ind_tbl}</div>
<div class="sowhat"><b>E daí</b><span>Tirar Application Software passa na sua regra (Top 20 {pc(get('Top 20 sem Application Software')['cagr'])}, Especiais {pc(get('Especiais sem Application Software')['cagr'])}, mesmas janelas, pior queda igual ou melhor), mas o ganho é de 0,1–0,3 p.p. e o corte proíbe um setor inteiro olhando para trás. Hoje ele tiraria ADBE, NOW, INTU e ADSK, que estão na lista de pânico depois de caírem 27–47%. Não apliquei: a decisão é sua. Biotecnologia: {bio['n']} posições, {pc(bio['sev'])} de quedas fortes e mediana de {pc(bio['med'], 0)} em um ano.</span></div></figure>

<h2 class="chap">6. As listas de hoje</h2>
<figure><figcaption class="t">Top 20 (carteira, piso de US$ 20 bi)</figcaption><div class="tablebox">{T20}</div></figure>
<figure><figcaption class="t">Especiais (carteira, peso × nota)</figcaption><div class="tablebox">{TES}</div></figure>
<figure><figcaption class="t">Compounders redondos (observação), pelo retorno esperado</figcaption><div class="tablebox">{TCO}</div></figure>
<figure><figcaption class="t">Quase lá: quanto falta cair para o retorno chegar a 20%</figcaption><div class="tablebox">{TQL}</div></figure>
<figure><figcaption class="t">Ótima em pânico</figcaption><div class="tablebox">{TPA}</div></figure>
<figure><figcaption class="t">Pequenas que compõem</figcaption><div class="tablebox">{TPQ}</div>
<div class="src">Dados da planilha de 22/11/2026. Os anos de EPS de 2017–2021 vieram dos 10-K da SEC só para esta validação (o arquivo enviado em 22/11 tinha só 2022–2025); no Excel o Wisesheets preenche. Variação de 12 meses calculada com preços até 06/11/2026.</div></figure>

<h2 class="chap">7. Fórmulas exatas</h2>
<span class="f">{e(FORM)}</span>
<span class="f" style="margin-top:12px">{e(LISTF)}</span>

<h2 class="chap">8. Alertas</h2>
<p class="prose">Antes: 232 alertas no arquivo (consenso atípico 115, consenso muito acima do histórico 94, sem estimativa 12, teto 8, lucro negativo 3). Agora o arquivo tem {nf} (o atípico ficou mais preciso, 55, e entrou o step change, 86), mas a Central de alertas mostra só as ações que estão em alguma lista: <b>{na}</b>. Todos pedem uma conferência concreta antes de comprar: consenso acima do histórico + 10 p.p. (ex.: AVGO, LRCX, CAT, AMAT), step change (LLY, ANET, MPWR) e consenso atípico sem apoio operacional (KLAC, DELL).</p>

<h2 class="chap">9. Decisões pendentes</h2>
<p class="prose">(1) Ligar a limpeza do consenso nas carteiras (tiraria LLY e as de consenso inflado; sem backtest possível). (2) Excluir Application Software. (3) Preencher a nota qualitativa (C7) das empresas que você conhece. (4) A investigação do ROIC, que afeta tudo isto.</p>
</div>'''
head = '<title>Robustez do Price Tracker</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
(ROOT / 'robustez.html').write_text(head + css + '\n' + body)
print('ok', len(css + body) // 1024, 'KB')
