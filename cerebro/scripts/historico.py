"""Gera cerebro/HISTORICO.md a partir da cópia do app (cerebro/app/dados)."""
import json, os, collections
R = os.path.join(os.path.dirname(__file__), "..")
D = os.path.join(R, "app", "dados")
j = lambda n: json.load(open(os.path.join(D, n), encoding="utf-8"))
ev = j("eventos.json")["eventos"]; cx = j("caixa.json")["itens"]; g = j("grade.json")
ins = j("inscricoes.json"); sess = {s["id"]: s for s in j("sessoes.json")["sessoes"]}
nov = j("novidades.json")
dia = lambda q: q[:10]
def nome(item):
    for e in ev:
        if e.get("item") == item and e.get("titulo"): return f'{e.get("fonte","")} · {e["titulo"]}'
    s = sess.get(item) or sess.get(item + ".01")
    return s["titulo"] if s else item
L = ["# Histórico do Cérebro", "",
     f"Cópia do app publicado em cerebro-joao.jgnsalles.workers.dev (versão {json.load(open(os.path.join(R,'app','versao.json')))['v']}).",
     f"O registro de eventos publicado vai de {dia(ev[0]['quando'])} a {dia(ev[-1]['quando'])} ({len(ev)} eventos).",
     "O que aconteceu depois disso, ou num aparelho sem token, não está nesta cópia: está no repositório jgnsalles/Claude-Code (cerebro/registro) ou só no aparelho.", ""]

L += ["## Notas e textos que você escreveu", ""]
for e in ev:
    t = e.get("nota") or e.get("texto")
    if t:
        L += [f"### {dia(e['quando'])} · {nome(e.get('item') or e.get('sessao','').split('.')[0])}", "", t.strip(), ""]
falas = [e for e in ev if e["evento"] == "falou"]
L += [f"Falas gravadas (áudio, ficam no repositório Claude-Code): {len(falas)}", ""]
for e in falas: L.append(f"- {dia(e['quando'])} · {e.get('seg')} s · `{e.get('arquivo')}`" + (f" · {nome(e['item'])}" if e.get("item") else ""))
L.append("")

L += ["## Podcasts salvos (movidos para Relevantes ou deixados para depois)", ""]
for e in ev:
    if e["evento"] in ("moveu", "depois"):
        L.append(f"- {dia(e['quando'])} · {e['evento']}{(' → ' + e['para']) if e.get('para') else ''} · {e.get('fonte','')} · {e.get('titulo','')}" + (f" · {e['url']}" if e.get("url") else ""))
L += ["", "## Podcasts ouvidos", ""]
ouv = collections.OrderedDict()
for e in ev:
    if e["evento"] == "ouviu":
        o = ouv.setdefault(e["item"], {"fonte": e.get("fonte"), "seg": 0, "ult": e["quando"], "pos": 0})
        o["seg"] += int(e.get("seg") or 0); o["ult"] = e["quando"]; o["pos"] = max(o["pos"], int(e.get("posicao") or 0))
for k, o in ouv.items():
    t = nov.get(k, {}).get("titulo") if isinstance(nov.get(k), dict) else None
    L.append(f"- {dia(o['ult'])} · {o['fonte']} · {t or nome(k)} · ouviu {o['seg']//60} min, parou em {o['pos']//60} min")
L += ["", "## Podcasts que você removeu (não salvos)", ""]
for e in ev:
    if e["evento"] == "removeu":
        L.append(f"- {dia(e['quando'])} · {e.get('fonte','')} · {e.get('titulo','')}" + (f" · {e['url']}" if e.get("url") else ""))
L += ["", "## Inscrições desfeitas", ""] + [f"- {dia(e['quando'])} · {e.get('nome')}" for e in ev if e["evento"] == "desinscreveu"]

L += ["", "## Resumos", ""]
for f in sorted(os.listdir(os.path.join(D, "resumos"))):
    p = open(os.path.join(D, "resumos", f), encoding="utf-8").readline().strip("# \n")
    L.append(f"- `app/dados/resumos/{f}` · {p}")
L += ["", "Resumos pedidos ou feitos fora do app:", ""]
for e in ev:
    if e["evento"] in ("pediu", "resumiu-fora"):
        L.append(f"- {dia(e['quando'])} · {e['evento']} · {nome((e.get('item') or e.get('sessao','')).split('.')[0])} · {e.get('minutos','')} min" + (f" · {e['destino']}" if e.get("destino") else ""))
L += ["", f"Transcrições guardadas: {len(os.listdir(os.path.join(D,'transcricoes')))} arquivos em `app/dados/transcricoes/`.", ""]

L += ["## Caixa (o que entrou e o que você decidiu)", ""]
for c in cx: L.append(f"- {c.get('quando','')} · **{c.get('estado','')}** · {c.get('titulo','')}" + (f" · {c['url']}" if c.get("url") else ""))

L += ["", f"## Séries ({len(g['series'])})", ""]
it = {i["cod"]: i for i in g["itens"]}
for s in g["series"]:
    L += [f"### Série {s['n']} · {s.get('titulo','')}", "", s.get("resumo", ""), ""]
    L += [f"- {c} · {it.get(c,{}).get('titulo','?')} — {it.get(c,{}).get('autor','')}" for c in s["itens"]]
    L.append("")
L += [f"## Inscrições atuais", "", f"{len(ins['podcasts'])} podcasts, {len(ins['cartas'])} cartas.", ""]
L += [f"- {p['nome']} ({p.get('grupo','')})" for p in ins["podcasts"]]
open(os.path.join(R, "HISTORICO.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(len(L), "linhas")
