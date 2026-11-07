#!/usr/bin/env python3
"""
Monitor de anúncios de carros (Webmotors) com comparação à Tabela FIPE.

Uso:
    python monitor_carros.py buscar              # roda as buscas do config.json
    python monitor_carros.py importar anuncios.csv   # importa anúncios colados à mão
    python monitor_carros.py relatorio           # exporta CSV com tudo que está salvo

Os anúncios ficam em um banco SQLite (carros.db). A cada execução o script
mostra anúncios novos e quedas de preço desde a última vez.

Observação: o Webmotors não tem API pública. Este script usa o mesmo endpoint
que o site usa internamente, que pode mudar ou ser bloqueado a qualquer momento
(Cloudflare). Instalar `curl_cffi` aumenta muito a chance de funcionar.
Respeite os termos de uso do site: use com moderação (poucas páginas, intervalo
entre requisições) e apenas para uso pessoal.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
CONFIG_PADRAO = PASTA / "config.json"
BANCO_PADRAO = PASTA / "carros.db"

WEBMOTORS_API = "https://www.webmotors.com.br/api/search/car"
FIPE_API = "https://brasilapi.com.br/api/fipe/preco/v1/{codigo}"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://www.webmotors.com.br/",
}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class ErroAcesso(Exception):
    pass


def baixar_json(url: str, params: dict | None = None) -> dict | list:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    try:
        from curl_cffi import requests as creq  # imita o TLS do Chrome

        resp = creq.get(url, headers=CABECALHOS, impersonate="chrome", timeout=30)
        status, texto = resp.status_code, resp.text
    except ImportError:
        req = urllib.request.Request(url, headers=CABECALHOS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status, texto = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, texto = e.code, e.read().decode("utf-8", "replace")
        except urllib.error.URLError as e:
            raise ErroAcesso(f"Falha de conexão: {e.reason}") from e

    if status != 200:
        dica = ""
        if status in (403, 429) or "Just a moment" in texto[:2000]:
            dica = " (bloqueado pelo Cloudflare; tente `pip install curl_cffi` ou espere um pouco)"
        raise ErroAcesso(f"HTTP {status} em {url[:120]}{dica}")
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        raise ErroAcesso(f"Resposta não é JSON em {url[:120]}") from e


# --------------------------------------------------------------------------
# Webmotors
# --------------------------------------------------------------------------

def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def montar_url_busca(busca: dict) -> str:
    """URL de busca no formato do site. Se o config tiver 'url', usa ela."""
    if busca.get("url"):
        return busca["url"]
    partes = ["https://www.webmotors.com.br/carros"]
    if busca.get("estado"):
        partes.append(slug(busca["estado"]))
    else:
        partes.append("estoque")
    partes.append(slug(busca["marca"]))
    if busca.get("modelo"):
        partes.append(slug(busca["modelo"]))
    filtros = {
        "tipoveiculo": "carros",
        "marca1": busca["marca"].upper(),
    }
    if busca.get("modelo"):
        filtros["modelo1"] = busca["modelo"].upper()
    mapa = {"ano_min": "anode", "ano_max": "anoate", "preco_min": "precode",
            "preco_max": "precoate", "km_max": "kmate"}
    for chave, nome in mapa.items():
        if busca.get(chave) is not None:
            filtros[nome] = busca[chave]
    return "/".join(partes) + "?" + urllib.parse.urlencode(filtros)


def _valor(obj, *caminho, padrao=None):
    for chave in caminho:
        if isinstance(obj, dict):
            obj = obj.get(chave)
        else:
            return padrao
    return padrao if obj is None else obj


def _numero(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.-]", "", str(v))
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):  # "115.000" = cento e quinze mil
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def converter_anuncio_webmotors(item: dict) -> dict | None:
    id_ = item.get("UniqueId") or item.get("Id")
    if not id_:
        return None
    spec = item.get("Specification") or {}
    marca = _valor(spec, "Make", "Value", padrao="")
    modelo = _valor(spec, "Model", "Value", padrao="")
    versao = _valor(spec, "Version", "Value", padrao="")
    ano_fab = _numero(spec.get("YearFabrication"))
    ano_mod = _numero(spec.get("YearModel"))
    preco = _numero(_valor(item, "Prices", "Price")) or _numero(_valor(item, "Prices", "SearchPrice"))
    km = _numero(spec.get("Odometer"))
    cidade = _valor(item, "Seller", "City", padrao="")
    uf = _valor(item, "Seller", "State", padrao="")
    vendedor = _valor(item, "Seller", "SellerType", padrao="")

    anos = f"{int(ano_fab or 0)}-{int(ano_mod or 0)}"
    link = (
        f"https://www.webmotors.com.br/comprar/{slug(marca)}/{slug(modelo)}/"
        f"{slug(versao) or 'versao'}/{_valor(spec, 'NumberPorts', padrao='4')}-portas/{anos}/{id_}"
    )
    return {
        "id": f"webmotors:{id_}",
        "fonte": "webmotors",
        "titulo": spec.get("Title") or f"{marca} {modelo} {versao}".strip(),
        "marca": marca,
        "modelo": modelo,
        "versao": versao,
        "ano_fabricacao": int(ano_fab) if ano_fab else None,
        "ano_modelo": int(ano_mod) if ano_mod else None,
        "km": int(km) if km is not None else None,
        "preco": preco,
        "cidade": cidade,
        "uf": uf,
        "vendedor": vendedor,
        "link": link,
    }


def buscar_webmotors(busca: dict, intervalo: float) -> list[dict]:
    url_busca = montar_url_busca(busca)
    paginas = int(busca.get("paginas", 2))
    por_pagina = 24
    anuncios: list[dict] = []
    for pagina in range(1, paginas + 1):
        dados = baixar_json(WEBMOTORS_API, {
            "url": url_busca,
            "actualPage": pagina,
            "displayPerPage": por_pagina,
            "order": 1,
            "showMenu": "true",
            "showCount": "true",
            "showBreadCrumb": "true",
            "testAB": "false",
            "returnUrl": "false",
        })
        itens = dados.get("SearchResults") or [] if isinstance(dados, dict) else []
        for item in itens:
            a = converter_anuncio_webmotors(item)
            if a:
                anuncios.append(a)
        if len(itens) < por_pagina:
            break
        time.sleep(intervalo)
    return anuncios


def passa_filtros(a: dict, busca: dict) -> bool:
    """Filtra localmente também, caso o site ignore algum filtro da URL."""
    def fora(valor, minimo, maximo):
        if valor is None:
            return False
        return (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo)

    if fora(a.get("ano_modelo"), busca.get("ano_min"), busca.get("ano_max")):
        return False
    if fora(a.get("preco"), busca.get("preco_min"), busca.get("preco_max")):
        return False
    if fora(a.get("km"), None, busca.get("km_max")):
        return False
    termo = busca.get("versao_contem")
    if termo and slug(termo) not in slug(f"{a.get('versao', '')} {a.get('titulo', '')}"):
        return False
    return True


# --------------------------------------------------------------------------
# FIPE
# --------------------------------------------------------------------------

_cache_fipe: dict[str, list] = {}


def valor_fipe(codigo: str | None, ano_modelo: int | None, combustivel: str | None = None) -> float | None:
    if not codigo or not ano_modelo:
        return None
    if codigo not in _cache_fipe:
        try:
            dados = baixar_json(FIPE_API.format(codigo=codigo))
            _cache_fipe[codigo] = dados if isinstance(dados, list) else []
        except ErroAcesso as e:
            print(f"  [FIPE] não consegui consultar {codigo}: {e}", file=sys.stderr)
            _cache_fipe[codigo] = []
    candidatos = [d for d in _cache_fipe[codigo] if int(d.get("anoModelo", 0)) == int(ano_modelo)]
    if combustivel:
        filtrados = [d for d in candidatos if slug(combustivel) in slug(d.get("combustivel", ""))]
        candidatos = filtrados or candidatos
    if not candidatos:
        return None
    return _numero(candidatos[0].get("valor"))


def fipe_para_anuncio(a: dict, busca: dict) -> float | None:
    manual = busca.get("fipe_manual") or {}
    if a.get("ano_modelo") and str(a["ano_modelo"]) in manual:
        return float(manual[str(a["ano_modelo"])])
    return valor_fipe(busca.get("fipe_codigo"), a.get("ano_modelo"), busca.get("combustivel"))


# --------------------------------------------------------------------------
# Banco de dados
# --------------------------------------------------------------------------

def abrir_banco(caminho: Path) -> sqlite3.Connection:
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.executescript("""
        CREATE TABLE IF NOT EXISTS anuncios (
            id TEXT PRIMARY KEY,
            busca TEXT, fonte TEXT, titulo TEXT, marca TEXT, modelo TEXT, versao TEXT,
            ano_fabricacao INTEGER, ano_modelo INTEGER, km INTEGER,
            preco REAL, preco_inicial REAL, fipe REAL,
            cidade TEXT, uf TEXT, vendedor TEXT, link TEXT,
            primeira_vez TEXT, ultima_vez TEXT
        );
        CREATE TABLE IF NOT EXISTS historico_precos (
            id TEXT, data TEXT, preco REAL
        );
    """)
    return con


def salvar(con: sqlite3.Connection, a: dict, nome_busca: str, agora: str) -> tuple[str, float | None]:
    """Retorna ('novo'|'baixou'|'subiu'|'igual', preco_anterior)."""
    linha = con.execute("SELECT preco FROM anuncios WHERE id = ?", (a["id"],)).fetchone()
    campos = ("titulo", "marca", "modelo", "versao", "ano_fabricacao", "ano_modelo", "km",
              "preco", "fipe", "cidade", "uf", "vendedor", "link")
    if linha is None:
        con.execute(
            f"INSERT INTO anuncios (id, busca, fonte, {', '.join(campos)}, preco_inicial, primeira_vez, ultima_vez)"
            f" VALUES (?, ?, ?, {', '.join('?' * len(campos))}, ?, ?, ?)",
            (a["id"], nome_busca, a.get("fonte"), *(a.get(c) for c in campos), a.get("preco"), agora, agora),
        )
        con.execute("INSERT INTO historico_precos VALUES (?, ?, ?)", (a["id"], agora, a.get("preco")))
        return "novo", None

    anterior = linha["preco"]
    con.execute(
        f"UPDATE anuncios SET {', '.join(f'{c} = ?' for c in campos)}, ultima_vez = ? WHERE id = ?",
        (*(a.get(c) for c in campos), agora, a["id"]),
    )
    if a.get("preco") is not None and anterior is not None and a["preco"] != anterior:
        con.execute("INSERT INTO historico_precos VALUES (?, ?, ?)", (a["id"], agora, a["preco"]))
        return ("baixou" if a["preco"] < anterior else "subiu"), anterior
    return "igual", anterior


# --------------------------------------------------------------------------
# Saída
# --------------------------------------------------------------------------

def brl(v) -> str:
    if v is None:
        return "-"
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def pct_fipe(preco, fipe) -> str:
    if not preco or not fipe:
        return ""
    return f"{(preco / fipe - 1) * 100:+.1f}% FIPE"


def linha_resumo(a: dict) -> str:
    km = f"{a['km']:,} km".replace(",", ".") if a.get("km") is not None else "km ?"
    local = "/".join(x for x in (a.get("cidade"), a.get("uf")) if x)
    return (f"{a.get('titulo', '')[:55]:55} {a.get('ano_fabricacao') or '?'}/{a.get('ano_modelo') or '?'} "
            f"{km:>11} {brl(a.get('preco')):>12} {pct_fipe(a.get('preco'), a.get('fipe')):>13} {local}\n"
            f"    {a.get('link', '')}")


def exportar_csv(con: sqlite3.Connection, destino: Path) -> int:
    linhas = con.execute("""
        SELECT busca, titulo, versao, ano_fabricacao, ano_modelo, km, preco, preco_inicial, fipe,
               CASE WHEN fipe > 0 THEN ROUND((preco / fipe - 1) * 100, 1) END AS dif_fipe_pct,
               cidade, uf, vendedor, primeira_vez, ultima_vez, link
        FROM anuncios ORDER BY busca, dif_fipe_pct IS NULL, dif_fipe_pct, preco
    """).fetchall()
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig abre certo no Excel
        w = csv.writer(f, delimiter=";")
        w.writerow(linhas[0].keys() if linhas else [])
        for l in linhas:
            w.writerow([str(v).replace(".", ",") if isinstance(v, float) else v for v in l])
    return len(linhas)


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------

def carregar_config(caminho: Path) -> dict:
    if not caminho.exists():
        sys.exit(f"Config não encontrado: {caminho}\nCopie config.exemplo.json para config.json e ajuste.")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def cmd_buscar(args) -> None:
    cfg = carregar_config(args.config)
    con = abrir_banco(args.banco)
    intervalo = float(cfg.get("intervalo_segundos", 3))
    agora = datetime.now().isoformat(timespec="seconds")
    algum_erro = False

    for busca in cfg.get("buscas", []):
        nome = busca.get("nome") or f"{busca.get('marca')} {busca.get('modelo', '')}".strip()
        print(f"\n=== {nome} ===")
        try:
            brutos = buscar_webmotors(busca, intervalo)
        except ErroAcesso as e:
            print(f"  Erro: {e}")
            algum_erro = True
            continue
        anuncios = [a for a in brutos if passa_filtros(a, busca)]
        print(f"  {len(brutos)} anúncios recebidos, {len(anuncios)} dentro dos filtros")

        novos, quedas = [], []
        for a in anuncios:
            a["fipe"] = fipe_para_anuncio(a, busca)
            status, anterior = salvar(con, a, nome, agora)
            if status == "novo":
                novos.append(a)
            elif status == "baixou":
                quedas.append((a, anterior))
        con.commit()

        if novos:
            print(f"\n  NOVOS ({len(novos)}):")
            for a in sorted(novos, key=lambda x: x.get("preco") or 0):
                print("  " + linha_resumo(a))
        if quedas:
            print(f"\n  BAIXARAM DE PREÇO ({len(quedas)}):")
            for a, anterior in quedas:
                print(f"  {brl(anterior)} -> {brl(a['preco'])}  " + linha_resumo(a))
        if not novos and not quedas:
            print("  Nada novo desde a última busca.")
        time.sleep(intervalo)

    n = exportar_csv(con, args.saida)
    print(f"\nCSV atualizado: {args.saida} ({n} anúncios no total)")
    if algum_erro:
        print("Dica: se o Webmotors bloquear, rode `pip install curl_cffi` ou use o comando "
              "`importar` com um CSV montado à mão.")


def cmd_importar(args) -> None:
    """CSV com colunas: titulo;ano_modelo;km;preco;link  (opcionais: versao;cidade;uf;fipe;busca)."""
    con = abrir_banco(args.banco)
    agora = datetime.now().isoformat(timespec="seconds")
    with open(args.arquivo, encoding="utf-8-sig") as f:
        amostra = f.read(2048)
        f.seek(0)
        delim = ";" if amostra.count(";") >= amostra.count(",") else ","
        contagem = {"novo": 0, "baixou": 0, "subiu": 0, "igual": 0}
        for linha in csv.DictReader(f, delimiter=delim):
            linha = {k.strip().lower(): (v or "").strip() for k, v in linha.items() if k}
            link = linha.get("link", "")
            a = {
                "id": "manual:" + (link or slug(f"{linha.get('titulo')}-{linha.get('ano_modelo')}-{linha.get('km')}")),
                "fonte": "manual",
                "titulo": linha.get("titulo", ""),
                "versao": linha.get("versao", ""),
                "ano_modelo": int(_numero(linha.get("ano_modelo")) or 0) or None,
                "km": int(_numero(linha.get("km")) or 0) or None,
                "preco": _numero(linha.get("preco")),
                "fipe": _numero(linha.get("fipe")),
                "cidade": linha.get("cidade", ""),
                "uf": linha.get("uf", ""),
                "link": link,
            }
            status, _ = salvar(con, a, linha.get("busca") or "manual", agora)
            contagem[status] += 1
    con.commit()
    print(f"Importados: {contagem}")
    n = exportar_csv(con, args.saida)
    print(f"CSV atualizado: {args.saida} ({n} anúncios no total)")


def cmd_relatorio(args) -> None:
    con = abrir_banco(args.banco)
    n = exportar_csv(con, args.saida)
    print(f"CSV gerado: {args.saida} ({n} anúncios)")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Monitor de anúncios de carros com comparação FIPE.")
    p.add_argument("--config", type=Path, default=CONFIG_PADRAO)
    p.add_argument("--banco", type=Path, default=BANCO_PADRAO)
    p.add_argument("--saida", type=Path, default=PASTA / "anuncios.csv")
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("buscar", help="roda as buscas do config").set_defaults(func=cmd_buscar)
    imp = sub.add_parser("importar", help="importa anúncios de um CSV")
    imp.add_argument("arquivo", type=Path)
    imp.set_defaults(func=cmd_importar)
    sub.add_parser("relatorio", help="exporta o CSV").set_defaults(func=cmd_relatorio)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
