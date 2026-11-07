// Cérebro, ciclo mínimo: Hoje (tempo + texto ou áudio), sessão (GoodNotes, player de áudio ou link), fechamento com nota,
// Estante (Mapa e Fluxo), Caixa (aprovar propostas, pedir resumo, "quero aprender") e sincronização do registro com o GitHub.
let D, IT, MAT, SESS = [], SES = {}, FLUXO = [], CAIXA = [], FUNDO = [], MONITOR = [], APELIDOS = {}, GUIAS = {}, ESTAT = [], FEED = [], CONTEUDOS = {}, TENHO = new Set(), PRECOS = {}, PLANO = { sessoes: [] }, RESUMOS_NOV = {}, INSCRICOES = null, ACERVO_IDX = null, BIO = null, SEMANA = null;
const ORDEM = ["FIL", "COM", "BEH", "BUS", "INV", "MM", "MKT", "GEO", "BRA", "FRA", "IND"];
const NOME_CURTO = { INV: "Investing", MM: "Mental Models", BEH: "Behavioral", BUS: "Business", MKT: "Markets", GEO: "Geopolítica e Economia",
  BRA: "Brasil", FRA: "Fraudes e Crises", IND: "Indústrias", COM: "Persuasão", FIL: "Filosofia e Ciência" };
const cor = c => c.startsWith("FX") ? "var(--aceso)" : `var(--l-${c.split("-")[0]})`;
const esc = s => String(s ?? "").replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
const pontos = n => `<span class="pontos" aria-label="${n} de 5">${[0, 1, 2, 3, 4].map(k => `<i class="${k < n ? "on" : ""}"></i>`).join("")}</span>`;
const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
const hms = s => { s = Math.max(0, Math.floor(s || 0)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), ss = String(s % 60).padStart(2, "0"); return h ? `${h}:${String(m).padStart(2, "0")}:${ss}` : `${m}:${ss}`; };
function fmtMin(m) { if (m < 60) return `${m} min`; const h = Math.floor(m / 60), r = m % 60; return r ? `${h} h ${r} min` : `${h} h`; }
function fmtTempo(t) {
  if (!t) return "a estimar na curadoria";
  if (t.min === t.max) return `${fmtMin(t.min)} (duração real)`;
  return `${t.min / 60}–${t.max / 60} h (padrão até a curadoria)`;
}

// ---------- estado do aparelho ----------
// feitas: sessões concluídas; lidas: itens concluídos; fila: eventos ainda não enviados ao GitHub.
const CHAVE = "cerebro.estado";
const VERSAO = 85;
const E = { trazidos: {}, acervoTocados: {}, revisoes: {}, atividade: {}, serie: 1, lidas: new Set(), feitas: new Set(), fila: [], desejos: [], decisoes: {}, falas: [], envios: [], regTipo: "youtube", hist: [], posicoes: {}, ouvidos: [], andamento: {}, vel: 1, notas: {}, episodio: null, config: { token: "", repo: "jgnsalles/Claude-Code", ramo: "main" },
  tempo: "30", formato: "texto", alt: 0, aba: "series", dom: "series", visao: { series: "tempo", conteudos: "tempo" }, sub: "fluxo", busca: "", fase: 0, sessao: null, inicio: 0, seg: 0, recortes: [], sync: "" };
function carregar() {
  try {
    const s = JSON.parse(localStorage.getItem(CHAVE) || "null");
    if (!s) return;
    E.serie = s.serie || 1; E.lidas = new Set(s.lidas || []); E.feitas = new Set(s.feitas || []);
    E.fila = s.fila || []; E.hist = s.hist || []; E.posicoes = s.posicoes || {}; E.ouvidos = s.ouvidos || []; E.andamento = s.andamento || {}; E.vel = s.vel || 1; E.notas = s.notas || {}; E.desejos = s.desejos || []; E.decisoes = s.decisoes || {}; E.falas = s.falas || []; E.envios = s.envios || []; E.regTipo = s.regTipo || E.regTipo; Object.assign(E.config, s.config || {}); E.rascunhos = s.rascunhos || {}; E.movidos = s.movidos || {}; E.trazidos = s.trazidos || {}; E.acervoTocados = s.acervoTocados || {}; E.revisoes = s.revisoes || {}; E.atividade = s.atividade || {};
    E.tempo = s.tempo || E.tempo; E.formato = s.formato || E.formato;
  } catch (_) {}
}
// Rascunho (pedido de 2026-10-21: "saí por 1 min e perdi tudo"): todo campo de nota guarda o que você digita no aparelho;
// volta mesmo se o app redesenhar a tela ou o iPhone fechar o app. Some quando você manda/salva.
const rascunho = k => (E.rascunhos || {})[k] || "";
let rascunhoTimer = null;
document.addEventListener("input", e => {
  const k = e.target.dataset && e.target.dataset.rascunho; if (!k) return;
  E.rascunhos = E.rascunhos || {}; if (e.target.value) E.rascunhos[k] = e.target.value; else delete E.rascunhos[k];
  clearTimeout(rascunhoTimer); rascunhoTimer = setTimeout(salvar, 300);
});
document.addEventListener("visibilitychange", () => { if (document.hidden) salvar(); });
function salvar() {
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ serie: E.serie, lidas: [...E.lidas], feitas: [...E.feitas], fila: E.fila, hist: E.hist, posicoes: E.posicoes, ouvidos: E.ouvidos, andamento: E.andamento, vel: E.vel, notas: E.notas, desejos: E.desejos,
      decisoes: E.decisoes, falas: E.falas, envios: E.envios.slice(0, 30), regTipo: E.regTipo, config: E.config, tempo: E.tempo, formato: E.formato, rascunhos: E.rascunhos, movidos: E.movidos, trazidos: E.trazidos, acervoTocados: E.acervoTocados, revisoes: E.revisoes, atividade: E.atividade }));
  } catch (_) {}
}
function registrar(ev) {
  const x = { quando: new Date().toISOString(), ...ev };
  E.fila.push(x); contarAtividade(x);
  if (ev.evento === "terminou") E.hist = E.hist.concat({ quando: x.quando, sessao: ev.sessao }).slice(-300);
  salvar(); sincronizar();
}

// ---------- sincronização: acrescenta a fila em cerebro/registro/AAAA-MM.jsonl pela API do GitHub ----------
const b64 = s => btoa(String.fromCharCode(...new TextEncoder().encode(s)));
const deB64 = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, "")), c => c.charCodeAt(0)));
let sincronizando = false;
async function sincronizar() {
  const { token, repo, ramo } = E.config;
  if (!token || !E.fila.length || sincronizando || !navigator.onLine) return;
  sincronizando = true;
  const lote = E.fila.slice(), mes = lote[0].quando.slice(0, 7), caminho = `cerebro/registro/${mes}.jsonl`;
  const url = `https://api.github.com/repos/${repo}/contents/${caminho}`;
  const h = { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" };
  try {
    const r = await fetch(`${url}?ref=${encodeURIComponent(ramo)}`, { headers: h, cache: "no-store" });
    let atual = "", sha;
    if (r.ok) { const j = await r.json(); atual = deB64(j.content); sha = j.sha; }
    else if (r.status !== 404) throw new Error(`leitura: HTTP ${r.status}`);
    const doMes = lote.filter(ev => ev.quando.startsWith(mes));
    const corpo = { message: `Cérebro: registro do app (${doMes.length} evento${doMes.length > 1 ? "s" : ""})`, branch: ramo,
      content: b64(atual + doMes.map(ev => JSON.stringify(ev)).join("\n") + "\n"), ...(sha ? { sha } : {}) };
    const w = await fetch(url, { method: "PUT", headers: h, body: JSON.stringify(corpo) });
    if (!w.ok) throw new Error(`gravação: HTTP ${w.status}`);
    E.fila = E.fila.filter(ev => !doMes.includes(ev));
    E.sync = `Sincronizado às ${new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
  } catch (err) {
    E.sync = `Não sincronizou (${err.message}). Os eventos ficam guardados e vão na próxima vez.`;
  }
  sincronizando = false; salvar();
  if (E.aba === "caixa") telaCaixa();
  if (E.fila.length && !E.sync.startsWith("Não")) sincronizar();
}
addEventListener("online", () => { sincronizar(); enviarFalas(); enviarRegistros(); });

// ---------- outro aparelho (iPad): ao abrir, lê o registro do GitHub e junta com o que este aparelho já sabe ----------
// Só acrescenta (nunca apaga nada local). Assim o iPad e o iPhone mostram o mesmo progresso, notas e falas.
async function restaurar() {
  const { token, repo, ramo } = E.config;
  if (!token || !navigator.onLine) return;
  const h = { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" }, base = `https://api.github.com/repos/${repo}/contents/cerebro/registro`;
  try {
    const r = await fetch(`${base}?ref=${encodeURIComponent(ramo)}`, { headers: h, cache: "no-store" });
    if (!r.ok) return;
    const meses = (await r.json()).filter(x => x.name.endsWith(".jsonl")).map(x => x.name).sort();
    let mudou = false;
    for (const mes of meses) {
      const a = await fetch(`${base}/${mes}?ref=${encodeURIComponent(ramo)}`, { headers: h, cache: "no-store" });
      if (!a.ok) continue;
      for (const linha of deB64((await a.json()).content).split("\n")) {
        if (!linha.trim()) continue;
        let ev; try { ev = JSON.parse(linha); } catch (_) { continue; }
        mudou = aplicar(ev) || mudou;
      }
    }
    if (!mudou) return;
    aplicarMovidos(); aplicarTrazidos(); tirarRemovidos();
    for (const c of Object.keys(IT)) if (IT[c].serie && SESS.some(y => y.item === c) && !proximaDoItem(c)) E.lidas.add(c);
    salvar(); badgeCaixa();
    if (E.fase === 0) { if (E.aba === "feed") telaFeed(); else if (E.aba === "caixa") telaCaixa(); else if (naHoje()) telaHoje(); }
  } catch (_) {}
}
function idsDoBloco(ev) {
  if (ev.bloco) return ev.bloco;
  const m = String(ev.sessao).match(/^(.+)\+(\d+)$/);   // registros antigos: "<primeira peça>+<quantas>"
  if (!m) return [ev.sessao];
  const p = SESS.find(y => y.id === m[1].replace("#txt", ""));
  return p ? pecasDoItem(p.item).filter(y => y.ordem >= p.ordem).slice(0, +m[2]).map(y => y.id) : [m[1]];
}
// código antigo de peça → peças novas (app/dados/apelidos.json, gerado pelo sessoes.py): o progresso não se perde
const traduz = ids => ids.flatMap(id => APELIDOS[id] || [id]);
const pecasDoItem = cod => SESS.filter(y => y.item === cod).sort((a, b) => a.ordem - b.ordem);
function aplicar(ev) {
  E.movidos = E.movidos || {};
  const antes = JSON.stringify([E.feitas.size, Object.keys(E.notas).length, E.falas.length, Object.keys(E.decisoes).length, E.andamento, Object.keys(E.movidos).length]);
  const ids = ev.sessao ? traduz(idsDoBloco(ev).map(id => id.replace("#txt", ""))) : [];
  if (ev.evento === "terminou" && !/^resumo|@/.test(ev.sessao)) {
    ids.forEach(id => { E.feitas.add(id); delete E.andamento[id]; }); const px = SESS.find(y => y.id === ids[0]); if (px) cobrir(px.item);
    if (!E.hist.some(x => x.quando === ev.quando)) E.hist = E.hist.concat({ quando: ev.quando, sessao: ev.sessao }).sort((a, b) => a.quando.localeCompare(b.quando)).slice(-300);
  }
  if ((ev.evento === "terminou" || ev.evento === "parou") && ev.nota) ids.forEach(id => { if (!E.notas[id]) E.notas[id] = ev.nota; });
  if ((ev.evento === "falou" || ev.evento === "escreveu") && !E.falas.some(f => f.id === ev.fala) && !FEED.some(x => x.id === ev.fala))
    E.falas.push({ id: ev.fala, quando: ev.quando, seg: ev.seg || 0, enviada: true, ...(ev.texto ? { texto: ev.texto } : {}), ...(ev.item ? { item: ev.item } : {}) });
  if (["aprovou", "mudar", "descartou"].includes(ev.evento) && (ev.item || ev.sessao) && !E.decisoes[ev.item || ev.sessao]) E.decisoes[ev.item || ev.sessao] = ev.evento;
  if (ev.evento === "arquivou" || ev.evento === "removeu") E.decisoes["arquivar:" + ev.item] = true;
  if (ev.evento === "pediu-guia") E.decisoes["guia:" + ev.item] = true;
  if (ev.evento === "desinscreveu" && ev.nome && !E.decisoes["desinscreveu:" + ev.nome]) E.decisoes["desinscreveu:" + ev.nome] = true;
  if (ev.evento === "depois" && ev.item) E.decisoes["depois:" + ev.item] = !!ev.ligado;
  contarAtividade(ev);
  if (ev.evento === "semana" && ev.chave) E.decisoes[ev.chave] = ev.escolha;
  if (ev.evento === "revisou" && ev.chave) { E.revisoes = E.revisoes || {}; const r = E.revisoes[ev.chave]; if (!r || !r.quando || r.quando < ev.quando) E.revisoes[ev.chave] = { nivel: ev.nivel, proxima: ev.proxima, quando: ev.quando }; }
  if (ev.evento === "trouxe" && ev.item && !(E.trazidos || {})[ev.item]) { E.trazidos = E.trazidos || {}; E.trazidos[ev.item] = { cod: ev.item, fonte: ev.fonte, titulo: ev.titulo, url: ev.url, minutos: ev.minutos, publicado: ev.publicado, tema: "trazido" }; }
  if (ev.evento === "moveu" && ev.item && (!E.movidos[ev.item] || E.movidos[ev.item].quando < ev.quando)) { E.movidos[ev.item] = { ...ev, para: ev.para }; if (ev.desfaz) delete E.movidos[ev.desfaz]; }
  // começou num aparelho, aparece em "Em andamento" no outro (pedido de 2026-10-24); "terminou" tira
  if (ev.evento === "comecou" && ev.sessao && !/^resumo|@|#txt/.test(ev.sessao) && !E.andamento[ev.sessao] && !ids.every(id => E.feitas.has(id)))
    E.andamento[ev.sessao] = { pos: ev.de || 0, quando: ev.quando };
  if (ev.evento === "ouviu" && ev.sessao && ev.posicao && !E.feitas.has(ev.sessao) && (!E.andamento[ev.sessao] || E.andamento[ev.sessao].quando < ev.quando))
    E.andamento[ev.sessao] = { pos: ev.posicao, quando: ev.quando };
  if (ev.evento === "parou" && ev.pagina && SESS.some(y => y.id === ev.sessao) && !E.feitas.has(ev.sessao) && (!E.andamento[ev.sessao] || E.andamento[ev.sessao].quando < ev.quando))
    E.andamento[ev.sessao] = { pag: ev.pagina, quando: ev.quando };
  if (ev.evento === "parou" && ev.posicao && SESS.some(y => y.id === ev.sessao) && !E.feitas.has(ev.sessao) && (!E.andamento[ev.sessao] || E.andamento[ev.sessao].quando < ev.quando))
    E.andamento[ev.sessao] = { pos: ev.posicao, quando: ev.quando };
  const chaveP = ev.chave || ev.item || ev.sessao;
  if (ev.evento === "pediu" && !E.decisoes["pedido:" + chaveP]) E.decisoes["pedido:" + chaveP] = ev.minutos;
  if (ev.evento === "cancelou") delete E.decisoes[ev.chave];
  return antes !== JSON.stringify([E.feitas.size, Object.keys(E.notas).length, E.falas.length, Object.keys(E.decisoes).length, E.andamento, Object.keys(E.movidos).length]);
}

// ---------- escolha do Hoje ----------
const SERIE = () => D.series[E.serie - 1];
// séries por tema (2026-10-20): "Série 3 · Value investing: os primeiros princípios"
const serieNome = n => { const s = D.series[n - 1]; return s && s.titulo ? `Série ${n} · ${s.titulo}` : `Série ${n}`; };
const naGrade = c => IT[c] && IT[c].serie;
const liberado = it => !it || !it.pre || E.lidas.has(it.pre) || !naGrade(it.pre) || IT[it.pre].serie > E.serie;
const TETO = { "15": 15, "30": 30, "60": 60, "120": 180 };
// Fundo saiu do Hoje e virou a aba Novidades (decisão de 2026-10-22)
const FORMATOS = [["texto", "Texto"], ["audio", "Áudio"]];
// livro da grade que o usuário não tem: sai do Hoje e vai para "Comprar" (só vale depois que a lista de livros chegar)
const semLivro = cod => TENHO.size > 0 && IT[cod]?.formato === "livro" && !TENHO.has(cod);
const ehFluxo = s => /^(FX|CL|EM)-/.test(s.item);   // Fluxo (novidade) ou coleção: itens fora da grade
const ehColecao = s => /^(CL|EM)-/.test(s.item);
const fluxoDe = s => FLUXO.find(f => f.cod === s.item);
// nomes na tela (renomeados pelo usuário em 2026-10-21); por dentro o código continua "Fluxo" e "Coleções"
const ROTULO = { Fluxo: "Relevantes", "Coleções": "Assets" }, rotulo = g => ROTULO[g] || g;
function semana() { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString(); }
function proximaDoItem(item) {
  return SESS.filter(s => s.item === item && !E.feitas.has(s.id)).sort((a, b) => a.ordem - b.ordem)[0];
}
// Hoje: cada item oferece as próximas peças seguidas (~15 min cada) até chegar perto do tempo escolhido.
// Ordem: o que preenche melhor o tempo; um empurrão leve para o que você já começou. Sem outras regras.
const ALVO = { "15": 15, "30": 30, "60": 60, "120": 120 };
const soma = l => l.reduce((t, x) => t + x.minutos, 0);
// voz do Alex de uma carta: outra forma de fazer as mesmas páginas. Não soma no total; ler ou ouvir as páginas conta para as duas.
const ehVoz = x => x.tipo === "audio" && !!x.paginas;
const contaveis = cod => SESS.filter(x => x.item === cod && !ehVoz(x));
const faixa = x => String(x.paginas).split("-").map(Number);
function cobrir(cod) {
  const ps = SESS.filter(x => x.item === cod && x.paginas), feitas = ps.filter(x => E.feitas.has(x.id)).map(faixa);
  if (!feitas.length || !ps.some(ehVoz)) return;
  const coberta = pg => feitas.some(([a, b]) => pg >= a && pg <= (b || a));
  for (const x of ps) { const [a, b] = faixa(x); let ok = true; for (let pg = a; pg <= (b || a); pg++) if (!coberta(pg)) { ok = false; break; } if (ok) E.feitas.add(x.id); }
}
function pecasPendentes(cod) { return SESS.filter(x => x.item === cod && !E.feitas.has(x.id)).sort((a, b) => a.ordem - b.ordem); }
// parou de ler no meio: a peça de voz (gerada quando a carta chegou) que cobre as páginas onde você estava
function vozSeguinte(o) {
  const ini = Math.min(...(o.bloco || [o.id]).map(id => +((SESS.find(y => y.id === id.replace("#txt", "")) || o).paginas || "0").split("-")[0]));
  return SESS.filter(x => x.item === o.item && x.tipo === "audio" && x.paginas && !E.feitas.has(x.id) && +x.paginas.split("-")[1] >= ini)
    .sort((a, b) => +a.paginas.split("-")[0] - +b.paginas.split("-")[0])[0];
}
function comoTexto(x) {
  // trecho de áudio com transcrição vira leitura
  if (x.modo !== "audio") return x;
  return fluxoDe(x)?.transcricao && x.ate ? { ...x, id: `${x.id}#txt`, base: x.id, tipo: "transcricao", modo: "leitura", onde: "transcricao",
    minutos: Math.max(1, Math.round((x.ate - x.de) / 60 * 0.8)), titulo: `Ler: ${x.titulo}` } : null;
}
const comecado = cod => SESS.some(y => y.item === cod && E.feitas.has(y.id)) || Object.keys(E.andamento).some(id => id.startsWith(cod + "."));
function opcoes() {
  const alvo = ALVO[E.tempo], limite = alvo * 1.15, audio = E.formato === "audio";
  const itens = D.series.flatMap(x => x.itens).filter(c => !E.lidas.has(c) && !semLivro(c) && SESS.some(y => y.item === c)).concat(FLUXO.map(f => f.cod));
  const ofertas = [];
  for (const cod of itens) {
    const pecas = pecasPendentes(cod).filter(x => !x.fluxo).map(x => audio ? (x.modo === "audio" ? x : null) : comoTexto(x)).filter(Boolean), bloco = [];
    for (const x of pecas) { if (soma(bloco) + x.minutos > limite || (bloco.length && x.tipo === "audio" && x.url !== bloco[0].url)) break; bloco.push(x); }
    if (bloco.length) ofertas.push(juntar(bloco));
  }
  // resumos não entram na lista: são uma ação dentro do item (com o tempo que você escolher)
  const nota = x => Math.abs(alvo - x.minutos) / alvo - (comecado(x.item) ? 0.2 : 0);
  return ofertas.sort((a, b) => nota(a) - nota(b));
}
// Progresso da série medido em minutos de peças: quanto já foi feito e quanto cada oferta acrescenta.
function minutosDe(cods) { const ps = SESS.filter(x => cods.includes(x.item)); return { total: soma(ps), feito: soma(ps.filter(x => E.feitas.has(x.id))) }; }
function progressoSerie(n) { const m = minutosDe(D.series[n - 1].itens); return m.total ? m.feito / m.total : 0; }
const pct = x => `${Math.round(x * 100)}%`;
function grupoDe(o) { return o.item.startsWith("EM-") ? "Empresas" : ehColecao(o) ? "Coleções" : fluxoDe(o)?.semana ? "Top da semana" : ehFluxo(o) ? "Fluxo" : `Série ${IT[o.item].serie}`; }
function ganho(o) {
  if (ehFluxo(o) || ["resumo", "resumo-audio"].includes(o.tipo)) return null;
  const tot = minutosDe(D.series[IT[o.item].serie - 1].itens).total;
  return tot ? o.minutos / tot : null;
}
function trechosDe(cod) { return SESS.filter(x => x.item === cod && x.tipo === "audio").sort((a, b) => a.ordem - b.ordem); }
function tituloBloco(l) {
  const a = l[0], z = l[l.length - 1];
  if (a.tipo === "audio") return l.length === trechosDe(a.item).length ? "Episódio inteiro" : `Trechos ${a.ordem} a ${z.ordem}`;
  if (a.tipo === "transcricao") return `Ler: trechos ${a.ordem} a ${z.ordem}`;
  if (a.tipo !== "audio" && l.length === contaveis(a.item).length && a.cap == null) return IT[a.item]?.titulo || fluxoDe(a)?.titulo || a.titulo.replace(/ \(1ª metade\)$/, "");
  const mesmo = (a.cap != null && a.cap === z.cap) || (a.doc_n != null && a.doc_n === z.doc_n);
  if (mesmo) {   // partes do mesmo capítulo ou da mesma carta
    const base = a.titulo.replace(/,? \(?parte \d+ de \d+\)?.*$|,? \(\dª metade\)$/, ""), m = a.titulo.match(/parte (\d+) de (\d+)/), mz = z.titulo.match(/parte (\d+) de (\d+)/);
    const pg = a.paginas && z.paginas ? `, págs. ${String(a.paginas).split("-")[0]}–${String(z.paginas).split("-").pop()}` : "";
    return m && mz && !(+m[1] === 1 && +mz[1] === +mz[2]) ? `${base} (partes ${m[1]} a ${mz[1]} de ${m[2]}${pg})` : base;
  }
  if (a.cap != null && z.cap != null) return `Caps. ${a.cap} a ${z.cap}`;
  return `${a.titulo} e mais ${l.length - 1} em seguida`;
}
function juntar(lista) {
  if (lista.length === 1) return lista[0];
  const a = lista[0], z = lista[lista.length - 1];
  const pg = a.paginas && z.paginas ? `${String(a.paginas).split("-")[0]}-${String(z.paginas).split("-").pop()}` : null;
  return { ...a, id: `${a.id}+${lista.length}`, bloco: lista.map(x => x.id), ate: z.ate, minutos: soma(lista), paginas: pg,
    estimado: lista.some(x => x.estimado), titulo: tituloBloco(lista), esboco: lista.flatMap(x => x.esboco || []), pergunta: z.pergunta };
}
const doQue = f => f.tipo === "podcast" ? "do episódio" : f.tipo === "carta" ? "da carta" : "";
function sessaoResumoItem(f, k) {
  return { id: `${f.cod}@${k}`, item: f.cod, base: f.cod, ordem: 0, tipo: "resumo", modo: "leitura", onde: "resumo",
    minutos: +k, estimado: false, titulo: `Resumo ${doQue(f)} · ${k} min`, pergunta: "" };
}
// Resumo em áudio (voz Alex, gerada na máquina pela esteira): toca no player como qualquer áudio
function sessaoResumoAudio(f, k) {
  const a = f.audios[k];
  return { id: `${f.cod}@${k}~voz`, item: f.cod, ordem: 0, tipo: "resumo-audio", modo: "audio", onde: "app", url: a.url, de: 0, ate: null,
    minutos: a.min, estimado: false, titulo: `Resumo ${doQue(f)} · ${k} min (voz)`, pergunta: "" };
}
function porque(o) {
  const r = [];
  if (PLANO.sessoes.includes(o.id)) r.push("Está no plano da semana");
  if (ehFluxo(o)) {
    const f = fluxoDe(o);
    if (f.tipo === "empresa") r.push(o.doc === "mencao" ? `Empresa ${f.titulo}: uma gestora analisando a empresa` : `Empresa ${f.titulo}: texto do próprio management`);
    else if (f.tipo === "colecao") { const lidas = SESS.filter(x => x.item === f.cod && E.feitas.has(x.id)).length; r.push(`Coleção ${f.titulo}: ${lidas} de ${f.total} lidas`); }
    else { const dias = Math.round((new Date(f.vence) - new Date()) / 86400000); r.push(`Relevantes: ${dias >= 0 ? `vence em ${dias} dias` : "venceu; decida na Caixa"}`); }
  } else {
    const n = IT[o.item].serie, g = ganho(o);
    r.push(`Série ${n}: ${pct(progressoSerie(n))} concluída${g ? `; esta leitura acrescenta ${pct(g)}` : ""}`);
    const dep = D.itens.filter(x => x.pre === o.item && x.serie);
    if (dep.length) r.push(`Abre caminho para ${dep.map(x => x.titulo).slice(0, 2).join(" e ")}`);
  }
  if (!ehFluxo(o) && IT[o.item].nota) r.push(IT[o.item].nota);
  r.push(`${o.estimado ? "Cerca de" : "Leva"} ${fmtMin(o.minutos)}${o.paginas ? ` · págs. ${o.paginas}` : ""}`);
  return r;
}
// O que é e onde está (pedido de 2026-10-19: "não sei se é vídeo, PDF ou livro")
const FMT = { livro: "Livro", palestra: "Palestra", paper: "Paper", artigo: "Artigo", memos: "Memos", "vídeo": "Vídeo", ensaio: "Ensaio", "áudio": "Áudio" };
function comoE(o) {
  if (o.tipo === "fundo") return "Podcast · toca aqui no Cérebro";
  const f = ehFluxo(o) ? fluxoDe(o) : null, u = o.url || "";
  const fmt = f ? (f.tipo === "podcast" ? "Podcast" : f.tipo === "carta" ? "Carta" : o.tipo === "audio" ? "Áudio" : "Texto") : FMT[IT[o.item].formato] || "Texto";
  const onde = o.onde === "livro" ? (TENHO.has(o.item) ? "o seu livro físico, da estante" : "livro físico") : o.onde === "goodnotes" ? "PDF no seu GoodNotes"
    : o.onde === "semlink" ? "ainda sem link conferido (a verificar)" : o.onde === "app" ? "toca aqui no Cérebro" : o.onde === "transcricao" ? "transcrição para ler aqui" : o.onde === "resumo" ? "resumo para ler aqui"
    : /youtube\.com|youtu\.be/.test(u) ? "vídeo no YouTube (abre o link)" : /\.pdf($|[?#])/i.test(u) ? (["Vídeo", "Palestra"].includes(fmt) ? "transcrição em PDF (abre o link)" : "PDF na internet (abre o link)") : "página na internet (abre o link)";
  return `${fmt} · ${onde}${/hbr\.org/.test(u) ? " · a HBR pode pedir assinatura (a verificar)" : ""}`;
}
// link com o ponto onde parou (YouTube aceita t=)
function linkDe(o) {
  const pos = E.andamento[o.id]?.pos || (o.tipo === "video" ? o.de : 0);   // vídeo em partes: abre no minuto da parte
  return pos && /youtube\.com|youtu\.be/.test(o.url || "") ? `${o.url}${o.url.includes("?") ? "&" : "?"}t=${pos}s` : o.url;
}
function nomeDoItem(o) {
  if (o.tipo === "fundo") return o.fonte;
  if (ehFluxo(o)) { const f = fluxoDe(o); return `${f.titulo} · ${f.fonte}`; }
  return `${IT[o.item].titulo} · ${IT[o.item].autor}`;
}
function cartao(o, n) {
  const c = cor(o.item), rot = { capitulo: "Capítulo", texto: "Texto", audio: "Áudio", video: "Vídeo", resumo: "Resumo", transcricao: "Transcrição" }[o.tipo] || "Sessão";
  return `<div class="pilula"><div class="faixa" style="background:${c}"></div><div class="corpo">
    <div class="linha1"><span class="etiq" style="background:${ehFluxo(o) ? "var(--aceso-tinta)" : c}">${rot}</span>
      ${ehFluxo(o) ? `<span class="chip fluxo-tag">${ehColecao(o) ? "Asset" : "Relevantes"}</span>` : `<span class="cod">${o.item} · ${esc(NOME_CURTO[IT[o.item].mat])}</span>`}</div>
    <h2>${esc(o.titulo)}</h2>
    <p class="autor">${esc(nomeDoItem(o))}</p>
    <p class="como">${esc(comoE(o))}</p>
    <ul class="porque">${porque(o).map(x => `<li>${esc(x)}</li>`).join("")}</ul>
    <div class="acoes">
      <button class="bt" type="button" data-acao="comecar">Começar</button>
      <button class="bt sec" type="button" data-acao="trocar" ${n < 2 ? "disabled" : ""}>Outra opção</button>
      ${ehFluxo(o) ? `<button class="bt sec" type="button" data-episodio="${esc(o.item)}">${o.modo === "audio" || o.tipo === "transcricao" ? "Trechos e resumo" : "Partes e resumo"}</button>` : `<button class="bt sec" type="button" data-ficha="${o.item}">Ficha</button>`}

    </div></div></div>`;
}
function telaHoje() {
  const el = document.getElementById("tela-hoje");
  if (E.fase) { el.innerHTML = sessaoEmCurso(); return; }
  if (E.bio) { telaBio(el); return; }
  if (E.episodio) { el.innerHTML = telaItem(E.episodio); return; }
  if (E.formato === "fundo") E.formato = "audio";
  const dom = E.dom = E.aba === "conteudos" ? "conteudos" : "series", emLista = E.visao[dom] === "lista";
  const ops = opcoes().filter(x => dominioDe(x) === dom); E.ofertas = ops;
  const dia = new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" });
  const rot = E.tempo === "120" ? "2 h+" : E.tempo + " min";
  const vazio = `<div class="aviso"><b>Nada ${E.formato === "audio" ? "em áudio " : ""}cabe em ${rot} agora.</b><p>${E.formato === "audio" ? "Por enquanto o acervo de áudio é só o Vélez; o lote de podcasts vai encher esta lista." : "Tente outro tempo."}</p></div>`;
  // todas as ofertas, agrupadas: Fluxo primeiro, depois as séries em ordem
  const grupos = {};
  ops.forEach((x, i) => (grupos[grupoDe(x)] = grupos[grupoDe(x)] || []).push(i));
  // ordem pedida pelo usuário: Fluxo, séries, e por fim coleções e empresas fechadas (abrem com um toque)
  const peso = g => ({ "Top da semana": -2, Fluxo: -1, "Coleções": 1000, Empresas: 1001 })[g] ?? parseInt(g.slice(6));
  // toda série aparece, mesmo sem nada que caiba no tempo escolhido (pedido de 2026-10-21: "cadê a série 2?")
  if (dom === "series") D.series.forEach(s => { if (!grupos["Série " + s.n] && s.itens.some(c => !E.lidas.has(c))) grupos["Série " + s.n] = []; });
  const ordem = Object.keys(grupos).sort((a, b) => peso(a) - peso(b));
  if (emLista) { el.innerHTML = `${blocoAndamento(dom)}<div><p class="olho">${dom === "series" ? "Séries" : "Conteúdos"}</p><h1 class="titulo-tela">${dom === "series" ? "Por tema" : "Biblioteca"}</h1></div>${blocoVisao(dom)}${blocoBiblioteca(dom)}`; listaCatalogo(); return; }
  el.innerHTML = `
    ${avisoToken()}${blocoAndamento(dom)}
    <div><p class="olho">${dom === "series" ? "Séries" : "Conteúdos"} · ${esc(dia)}</p><h1 class="titulo-tela">Quanto tempo você tem?</h1></div>
    ${blocoVisao(dom)}
    <div class="tempos" role="group" aria-label="Tempo disponível">
      ${[["15", "15", "min"], ["30", "30", "min"], ["60", "60", "min"], ["120", "2 h+", "fim de semana"]].map(([k, b, sp]) =>
        `<button type="button" data-tempo="${k}" aria-pressed="${E.tempo === k}"><b>${b}</b><span>${sp}</span></button>`).join("")}
    </div>
    <div class="sub" role="group" aria-label="Texto ou áudio">
      ${FORMATOS.map(([k, n]) => `<button type="button" data-formato="${k}" aria-pressed="${E.formato === k}">${n}</button>`).join("")}
    </div>
    ${!ops.length ? vazio : `<h3>Tudo que cabe em ${rot} · ${ops.length} opções</h3>
      ${ordem.map(g => {
        const n = g.startsWith("Série") ? parseInt(g.slice(6)) : null, fechado = g !== "Fluxo";   // revisão de 2026-10-19: só o Fluxo aberto; o resto abre com um toque
        const cods = codsDoGrupo(g), mg = n ? minutosDe(cods) : minutosConteudo(cods), prog = mg.total ? mg.feito / mg.total : 0;
        const medida = `${mg.total ? fmtMin(mg.total) : "sem tempo ainda"} · ${pct(prog)} ${n ? "concluída" : "concluído"}`;
        const cab = `<b>${n ? esc(serieNome(n)) : rotulo(g)}</b><span class="cod">${n ? medida : `${g === "Fluxo" ? "novidades" : g === "Top da semana" ? "escolhidos com o motivo" : g === "Empresas" ? "empresa e gestoras" : "cartas e papers"} · ${cods.length} ${cods.length === 1 ? "item" : "itens"} · ${medida}`}</span>`;
        const lista = grupos[g].length ? `<div class="ofertas">${grupos[g].map(i => linhaOferta(ops[i], i)).join("")}</div>`
          : `<p class="cod">${D.series[n - 1].itens.some(c => !semLivro(c) && contaveis(c).length) ? `Nada desta série cabe em ${rot}; tente mais tempo.` : "Por enquanto, tudo desta série é livro para comprar (lista abaixo)."}</p>`;
        const sr = n && D.series[n - 1], sobre = sr && sr.resumo ? `<p class="resumo-serie"><b>Abordagem ${esc(sr.abordagem)}.</b> ${esc(sr.resumo)}</p>` : "";
        const atual = n && g === ordem.filter(x => x.startsWith("Série"))[0] ? " open" : "";   // a série em que você está já vem aberta (revisão de 2026-10-24)
        return fechado ? `<details class="grupo"${atual}><summary class="cab-serie">${cab}</summary>${sobre}<div class="barra-serie"><i style="width:${pct(prog)}"></i></div>${lista}${n ? extrasSerie(n) : ""}</details>`
          : `<div class="grupo"><div class="cab-serie">${cab}</div><div class="barra-serie"><i style="width:${pct(prog)}"></i></div>${lista}${n ? extrasSerie(n) : ""}</div>`;
      }).join("")}`}`;
}
// Hoje enxuto (revisão de 2026-10-19): 1 sugestão principal e até 3 alternativas. A principal alterna de propósito
// entre Fluxo e série: se a última coisa feita foi do Fluxo, a principal é da série, e vice-versa (para a trilha andar).
function destaque(ops, grupos, ordem) {
  const h = E.hist[E.hist.length - 1], ult = h && SESS.find(y => y.id === String(h.sessao).split("+")[0].replace("#txt", ""));
  const primeiro = g => (grupos[g] || [])[0], series = ordem.filter(g => g.startsWith("Série"));
  // só a série atual (a primeira que ainda tem o que fazer) entra no destaque: as seguintes ficam na lista, fechadas (pedido de 2026-10-21)
  const pref = ult && ehFluxo(ult) ? [series[0], "Fluxo"] : ["Fluxo", series[0]];
  const daSerie = (grupos[series[0]] || []).slice(1);
  const cand = [...pref.map(primeiro), ...daSerie, primeiro("Top da semana"), ...(grupos.Fluxo || []).slice(1)].filter(i => i != null);
  if (!cand.length) cand.push(...ordem.flatMap(g => grupos[g] || []));   // Conteúdos: só coleções ou empresas cabem agora
  const esc1 = [...new Set(cand)].slice(0, 4);
  return `<div class="destaque"><p class="olho">Sugestão para agora</p>${linhaOferta(ops[esc1[0]], esc1[0], true)}
    ${esc1.length > 1 ? `<p class="olho" style="margin-top:12px">Ou</p><div class="ofertas">${esc1.slice(1).map(i => linhaOferta(ops[i], i, false, true)).join("")}</div>` : ""}</div>`;
}
// Embaixo de cada série no Hoje: o que ainda não tem sumário e os livros a comprar (pela posição original na grade), com preço
function extrasSerie(n) {
  const semSum = D.itens.filter(i => i.serie === n && !semLivro(i.cod) && !contaveis(i.cod).length && !E.lidas.has(i.cod));
  const comprar = D.itens.filter(i => semLivro(i.cod) && (i.serie_original || i.serie) === n).map(i => i.cod);
  const total = comprar.reduce((t, c) => t + (PRECOS[c] ? PRECOS[c].valor : 0), 0);
  const gs = geniosDaSerie(n);   // séries ↔ Biografias (revisão de 2026-10-24)
  return `${gs.length ? `<div class="acoes"><span class="cod">Gênios desta série:</span>${gs.map(c => `<button class="bt sec" type="button" data-bio="${esc(c)}">${esc(BIO.genios[c].nome)}</button>`).join("")}</div>` : ""}
    ${semSum.length ? `<p class="cod">Sem sumário ainda (entram quando chegar): ${semSum.map(i => esc(i.titulo)).join(" · ")}</p>` : ""}
    ${comprar.length ? `<details class="comprar"><summary class="cod">Para comprar nesta série: ${comprar.length} livro${comprar.length > 1 ? "s" : ""}${total ? ` · R$ ${total.toFixed(2).replace(".", ",")} na Amazon` : ""}${comprar.some(c => !PRECOS[c]) && total ? ` (${comprar.filter(c => !PRECOS[c]).length} sem preço ainda)` : ""}</summary>
      <div class="ofertas">${comprar.map(linhaCompra).join("")}</div></details>` : ""}`;
}
function linhaOferta(x, i, principal, comGrupo) {
  const g = ganho(x), nome = ehFluxo(x) ? fluxoDe(x).fonte : IT[x.item].titulo, total = soma(contaveis(x.item)), mot = fluxoDe(x)?.motivo;
  const ap = E.andamento[(x.bloco || [x.id])[0]], grupo = grupoDe(x);
  const capa = fluxoDe(x)?.imagem;
  return `<button class="oferta${principal ? " principal" : ""}${capa ? " com-capa" : ""}" type="button" data-oferta="${i}" style="--cor:${cor(x.item)}">${capa ? `<img class="capa" src="${esc(capa)}" alt="" loading="lazy">` : ""}
    <span class="nome"><b>${esc(nome)}</b>${(mot ? fluxoDe(x).titulo : x.titulo) !== nome ? `<span>${esc(mot ? fluxoDe(x).titulo : x.titulo)}${x.paginas && !/págs/.test(x.titulo) ? ` · págs. ${esc(x.paginas)}` : ""}</span>` : ""}<span class="como">${ehFluxo(x) ? "" : esc(IT[x.item].autor) + " · "}${esc(comoE(x))}${IT[x.item] && IT[x.item].nivel === "Eletiva" ? " · <b>opcional</b>" : ""}</span>${ap && (ap.pag || ap.pos) ? `<span><b>Continuar: ${ondeParou(ap)}</b></span>` : ""}${principal || comGrupo ? `<span class="cod">${esc(/^Série \d+$/.test(grupo) ? serieNome(+grupo.slice(6)) : rotulo(grupo))}</span>` : ""}${mot ? `<span><i>${esc(mot)}</i></span>` : ""}</span>
    <span class="num"><b>${x.estimado ? "~" : ""}${x.minutos} min</b>${total > x.minutos ? `<i>de ${fmtMin(total)}</i>` : ""}${g ? `<span>+${pct(g)}</span>` : ""}</span></button>`;
}
// Página da empresa: o que mora em outra casa mas tem a etiqueta dela (itens do Fluxo e episódios de podcast)
function outrosSobre(cod) {
  const fx = FLUXO.filter(x => (x.etiquetas || []).includes(cod));
  const eps = SESS.filter(x => (x.etiquetas || []).includes(cod) && !/\(trecho [2-9]|\(trecho \d\d/.test(x.titulo));
  const fd = FUNDO.filter(x => (x.etiquetas || []).includes(cod));
  if (!fx.length && !eps.length && !fd.length) return "";
  return `<h3>Outros sobre a empresa</h3><div class="ofertas">${fx.map(x => linhaItem(x.cod)).join("")}
    ${fd.map(x => `<button class="oferta" type="button" data-fundo="${esc(x.cod)}" style="--cor:var(--aceso)"><span class="nome"><b>${esc(x.fonte)} (Fundo)</b><span>${esc(x.titulo)}</span></span><span class="num"><b>▶</b>${x.minutos ? `<i>${fmtMin(x.minutos)}</i>` : ""}</span></button>`).join("")}
    ${eps.map(x => `<button class="oferta" type="button" data-trecho="${esc(x.id)}" style="--cor:${cor(x.item)}"><span class="nome"><b>${esc(FLUXO.find(f => f.cod === x.item)?.titulo || x.item)}</b><span>${esc(x.titulo.replace(/ \(trecho 1 de \d+\)/, ""))}</span></span><span class="num"><b>▶</b></span></button>`).join("")}</div>`;
}
// ---------- Página do episódio: todos os trechos, com estado, nota anterior e navegação ----------
function telaItem(cod) {
  const f = FLUXO.find(x => x.cod === cod), it = IT[cod];
  const ps = SESS.filter(x => x.item === cod).sort((a, b) => a.ordem - b.ordem), feitas = ps.filter(x => E.feitas.has(x.id));
  const falta = ps.filter(x => !E.feitas.has(x.id)), proximo = falta[0], audio = ps.some(x => x.tipo === "audio");
  const fonte = f ? f.fonte : `${it.autor} · ${it.formato} · Série ${it.serie || "–"} · ${NOME_CURTO[it.mat]}`;
  const link = f ? f.url : (ps.find(x => x.url) || {}).url;
  const cs = ps.filter(x => !ehVoz(x)), media = cs.length ? Math.round(soma(cs) / cs.length) : 0, feitasC = cs.filter(x => E.feitas.has(x.id));
  return `<button class="voltar" type="button" data-acao="fechar-episodio">← Voltar</button>
    <div><p class="olho">${esc(fonte)}</p><h1 class="titulo-tela" style="font-size:24px">${esc(f ? f.titulo : it.titulo)}</h1>
      <p class="cod">${cs.length ? `${cs.length} ${cs.some(x => x.tipo === "audio") ? "trechos" : "partes"} · média de ${media} min · ${fmtMin(soma(cs))} no total · ${feitasC.length} de ${cs.length} feitas (${pct(soma(feitasC) / Math.max(1, soma(cs)))})${ps.some(ehVoz) ? " · também na voz do Alex" : ""}` : "Ainda sem sumário: as partes aparecem quando a curadoria fizer o sumário."}</p></div>
    ${f && /^FX-/.test(cod) ? `<div class="acoes">${f.tipo === "podcast" ? `<button class="bt sec" type="button" data-mover="fundo" data-cod="${esc(cod)}">Mandar para o Fundo</button>` : ""}<button class="bt sec" type="button" data-remover="${esc(cod)}">Remover de Relevantes</button></div>` : ""}
    ${it && !f ? `<div class="acoes"><button class="bt sec" type="button" data-ficha="${esc(cod)}">Ficha</button>${link ? `<a class="bt sec" href="${esc(link)}" target="_blank" rel="noopener" style="text-decoration:none">Abrir a fonte</a>` : ""}</div>` : ""}
    ${sugestaoAqui(cod)}${lembrete(cod)}${painelRegistro(cod)}
    ${cod.startsWith("EM-") ? outrosSobre(cod) : ""}
    ${f && f.tipo === "colecao" ? `<p class="cod">Ordem: as 3 mais recentes primeiro, depois da primeira em diante. Minutos estimados (~20) até cada carta ser medida.${f.url ? ` <a href="${esc(f.url)}" target="_blank" rel="noopener">Site</a>` : ""}</p>` : ""}
    ${ps.length ? `<details class="grupo"${E.sugestao || ps.length < 2 ? "" : " open"}><summary class="cab-serie"><b>Todas as partes</b><span class="cod">uma a uma, com as notas</span></summary>
    ${falta.length > 1 ? `<div class="acoes"><button class="bt" type="button" data-bloco="${esc(falta.slice(0, 8).map(x => x.id).join(","))}">${audio ? "Ouvir" : "Ler"} as próximas (${fmtMin(soma(falta.slice(0, 8)))})</button></div>` : ""}
    <div class="lista">${ps.map(x => {
      const feito = E.feitas.has(x.id), and = E.andamento[x.id], nota = E.notas[x.id];
      const estado = feito ? '<span class="chip lida">feito</span>' : and && and.pos ? `<span class="chip fluxo-tag">parou em ${mmss(and.pos)}</span>` : x === proximo ? '<span class="chip aceso">próximo</span>' : "";
      return `<div class="item"><div class="meta"><span class="cod">${x.ordem}</span>
          <span>${x.tipo === "audio" ? `${mmss(x.de)}–${mmss(x.ate)} · ` : x.paginas ? `págs. ${esc(x.paginas)} · ` : ""}${x.estimado ? "~" : ""}${x.minutos} min</span>${estado}</div>
        <h3>${esc(x.titulo.replace(/^Trecho \d+ · /, ""))}</h3>
        ${x.esboco ? `<div class="meta">${x.esboco.map(e => esc(e[1])).join(" · ")}</div>` : ""}
        ${x.doc ? `<div class="meta"><span class="chip ${x.doc === "mencao" ? "" : "aceso"}">${x.doc === "mencao" ? "gestora sobre a empresa" : x.doc === "entrevista" ? "fundador/CEO em entrevista" : x.doc === "trimestral" ? "carta trimestral da empresa" : "carta anual da empresa"}</span></div>` : ""}
        ${x.trecho ? `<p class="cita">${esc(x.trecho)}</p>` : ""}
        ${nota ? `<p class="cita">${esc(nota)}</p>` : ""}
        <div class="acoes"><button class="bt ${feito ? "sec" : ""}" type="button" data-trecho="${esc(x.id)}">${feito ? (audio ? "Ouvir de novo" : "Ler de novo") : and && and.pos ? "Continuar" : audio ? "Ouvir" : "Começar"}</button>${feito ? "" : `<button class="bt sec" type="button" data-ja-li="${esc(x.id)}">${x.tipo === "audio" ? "Já ouvi" : "Já li"}</button>`}
          ${f && f.transcricao && x.tipo === "audio" ? `<button class="bt sec" type="button" data-texto="${esc(x.id)}">Ler</button>` : ""}</div></div>`;
    }).join("")}</div></details>` : ""}
    ${f && !["colecao", "empresa"].includes(f.tipo) && (f.transcricao || f.resumos || ps.some(x => x.url)) ? tamanhosDeResumo(f) : ""}`;
}

// ---------- Biografias (pedido de 2026-10-24): página de cada gênio, com livros, podcasts do acervo e ligações ----------
function linhaBio(c) {
  const g = BIO.genios[c];
  return `<button class="oferta" type="button" data-bio="${esc(c)}"><span class="nome"><b>${esc(g.nome)}${g.sugestao ? " · sugestão" : ""}</b>
    <span>${g.livros.filter(l => !l.depois).length} livro${g.livros.filter(l => !l.depois).length === 1 ? "" : "s"}${g.pods.length ? ` · ${g.pods.length} episódio${g.pods.length === 1 ? "" : "s"}` : ""}</span></span></button>`;
}
// trechos da sua grade e páginas de empresa sobre o gênio: o mesmo conteúdo em dois lugares, de propósito
function sobreOGenio(g) {
  const ps = g.busca.map(b => semAcento(b.trim())).filter(b => b.length > 3);
  return D.itens.filter(i => { const t = " " + semAcento([i.titulo, i.autor].join(" ")) + " "; return ps.some(b => t.includes(b)); }).slice(0, 8);
}
// gênios cujo nome aparece no título ou no autor de um item da série
function geniosDaSerie(n) {
  if (!BIO) return [];
  const its = D.itens.filter(i => i.serie === n).map(i => " " + semAcento([i.titulo, i.autor].join(" ")) + " ");
  return Object.entries(BIO.genios).filter(([, g]) => g.busca.map(b => semAcento(b.trim())).filter(b => b.length > 3).some(b => its.some(t => t.includes(b)))).map(([c]) => c);
}
async function telaBio(el) {
  const cod = E.bio, g = BIO.genios[cod], mv = BIO.movimentos[g.movimento - 1], roi = new Set(BIO.roi);
  const livro = l => `<div class="item"><div class="meta">${l.voce ? '<span class="chip aceso">você mandou</span>' : ""}${l.curto ? '<span class="chip aceso">versão curta, antes dos livros</span>' : ""}${roi.has(l.titulo) ? '<span class="chip aceso">comece por aqui</span>' : ""}${l.pt ? '<span class="chip">edição em PT</span>' : l.conferido ? '<span class="chip">sem edição em PT no catálogo</span>' : ""}${l.conferido === false ? '<span class="chip">a verificar</span>' : ""}</div>
    <h3>${esc(l.titulo)}</h3><div class="meta">${esc(l.autor)}${l.obs ? ` · ${esc(l.obs)}` : ""}${l.pt_titulo && l.pt_titulo !== l.titulo ? ` · em PT: ${esc(l.pt_titulo)}` : ""}</div>
    ${l.escolha ? `<p class="cod">Por que esta: ${esc(l.escolha.por_que)}${l.escolha.fonte ? ` <a href="${esc(l.escolha.fonte)}" target="_blank" rel="noopener">Fonte</a>` : ""}</p>` : ""}
    ${l.url || l.url_pt ? `<div class="acoes">${l.url_pt ? `<a class="bt sec" href="${esc(l.url_pt)}" target="_blank" rel="noopener">Edição em PT</a>` : ""}${l.url ? `<a class="bt sec" href="${esc(l.url)}" target="_blank" rel="noopener">Ver o livro</a>` : ""}</div>` : ""}</div>`;
  const grade = sobreOGenio(g), emp = (g.ligacoes || []).filter(c => FLUXO.some(f => f.cod === c));
  const cab = `<button class="voltar" type="button" data-acao="fechar-bio">← Voltar</button>
    <div><p class="olho">${esc(mv.nome)} · ${esc(mv.periodo)} · ${esc(mv.area)}</p><h1 class="titulo-tela" style="font-size:24px">${esc(g.nome)}</h1>${g.sugestao ? `<p class="cod"><span class="chip">sugestão</span> ${esc(g.sugestao)}</p>` : ""}</div>
    <h3>${g.livros.some(l => l.depois) ? "A biografia" : "Livros"}</h3><div class="lista">${g.livros.filter(l => !l.depois).map(livro).join("")}</div>
    ${g.livros.some(l => l.depois) ? `<details class="caixinha"><summary class="cab-serie"><h3>Para ir mais fundo · ${g.livros.filter(l => l.depois).length}</h3></summary><p class="cod">Fora da conta e da fila: uma biografia por gênio.</p><div class="lista">${g.livros.filter(l => l.depois).map(livro).join("")}</div></details>` : ""}
    ${[...new Set(grade.map(i => i.serie).filter(Boolean))].length ? `<p class="cod">Nas suas séries: ${[...new Set(grade.map(i => i.serie).filter(Boolean))].sort((a, b) => a - b).map(n => esc(serieNome(n))).join(" · ")}.</p>` : ""}
    ${grade.length || emp.length ? `<h3>Também no Cérebro</h3><div class="ofertas">${emp.map(c => linhaItem(c)).join("")}${grade.map(i => linhaItem(i.cod)).join("")}</div>` : ""}
    ${g.citados.length ? `<p class="cod">Citado na sua lista: ${g.citados.map(c => `${esc(c.programa)}, ${esc(c.titulo)}`).join("; ")}.</p>` : ""}`;
  el.innerHTML = cab + (g.pods.length ? `<h3>Podcasts · ${g.pods.length}</h3><p class="cod">Carregando…</p>` : `<p class="cod">Nenhum episódio sobre ${esc(g.nome)} no acervo dos seus podcasts ainda.</p>`);
  if (!g.pods.length) return;
  const progs = [...new Set(g.pods.map(x => x.programa))]; await Promise.all(progs.map(carregarAcervo));
  if (E.bio !== cod) return;
  const linhas = g.pods.map(x => { const e = (ACERVO[x.programa] || []).find(y => y.id === x.id); return e ? linhaAcervo(x.programa, e, true) : ""; }).join("");
  el.innerHTML = cab + `<h3>Podcasts · ${g.pods.length}</h3><p class="cod">Episódios dos seus podcasts sobre ${esc(g.nome)}, do mais novo ao mais velho. Tocar toca aqui; Ouvir depois manda para as Novidades, onde ganha resumo.</p><div class="lista">${linhas}</div>`;
}

// Sugestão que trouxe você até aqui (o Hoje recomenda; a página é do conteúdo)
function sugestaoAqui(cod) {
  const o = E.sugestao; if (!o || o.item !== cod || (o.bloco || [o.id]).every(id => E.feitas.has(id))) return "";   // já registrou o que foi sugerido
  return `<div class="sugestao"><p class="olho">Sugestão para agora · ${o.estimado ? "~" : ""}${fmtMin(o.minutos)}</p><h3>${esc(o.titulo)}${o.paginas && !/págs/.test(o.titulo) ? ` · págs. ${esc(o.paginas)}` : ""}</h3>
    <p class="cod">${esc(comoE(o))}</p><div class="acoes"><button class="bt" type="button" data-acao="comecar-sugestao">Começar (conta o tempo)</button></div></div>`;
}
// Lembrete de custo zero (pedido de 2026-10-19: curto, só para situar): onde você está, sua última nota e uma pergunta
function lembrete(cod) {
  const ps = contaveis(cod).sort((a, b) => a.ordem - b.ordem), prox = ps.find(x => !E.feitas.has(x.id));
  const notas = [...ps.filter(x => E.notas[x.id]).map(x => ({ q: (E.hist.find(h => h.sessao === x.id) || {}).quando || "", t: E.notas[x.id] })),
    ...E.falas.filter(f => f.item === cod && f.texto).map(f => ({ q: f.quando, t: f.texto }))].sort((a, b) => b.q.localeCompare(a.q));
  const linhas = [];
  const ap = prox && E.andamento[prox.id];
  if (prox && (ps.some(x => E.feitas.has(x.id)) || ap)) linhas.push(`<b>Você está em:</b> ${esc(prox.titulo)}${ap && ap.pag ? ` · continuar da pág. ${ap.pag}` : ap && ap.pos ? ` · continuar de ${mmss(ap.pos)}` : prox.paginas ? ` (págs. ${esc(prox.paginas)})` : ""}`);
  if (notas.length) linhas.push(`<b>Sua última nota:</b> “${esc(notas[0].t.length > 180 ? notas[0].t.slice(0, 180) + "…" : notas[0].t)}”`);
  if (prox && prox.pergunta) linhas.push(`<b>Para guiar:</b> ${esc(prox.pergunta)}`);
  return linhas.length ? `<div class="lembrete">${linhas.map(l => `<p>${l}</p>`).join("")}</div>` : "";
}
// Registro na própria página, sem precisar cronometrar: o que fez (inteiro ou picado), até onde foi, e uma nota em texto ou voz
function painelRegistro(cod) {
  const ps = contaveis(cod); if (!ps.length) return "";
  const g = gruposDoItem({ item: cod }), comPag = ps.some(x => x.paginas), comMin = ps.some(x => x.tipo === "audio" || x.tipo === "video");
  const minhas = E.falas.filter(f => f.item === cod), gravandoAqui = gravacao && gravacao.item === cod;
  return `<div class="painel-registro" id="registro-item"><div class="txt"><b>Registrar</b>
    <small>Marque o que fez (inteiro ou só uma parte), ou diga até onde chegou. Pode anotar sem marcar nada.</small>
    ${g.length ? `<div class="marcas">${g.map(({ ps }) => `<label class="marca"><input type="checkbox" value="${ps.map(x => x.id).join(",")}" data-ate="${Math.max(...ps.map(x => x.paginas ? faixa(x)[1] || faixa(x)[0] : Infinity))}"> <span>${esc(ps.length === 1 ? ps[0].titulo : ps[0].titulo.replace(/,? \(?(parte \d+ de \d+|\dª metade)\)?$/, "") + ` (${ps.length} partes)`)}</span></label>`).join("")}</div>` : `<p class="cod">Tudo feito por aqui.</p>`}
    <div class="campos">${comPag ? `<label class="cod">Li até a página <input id="ate-pag" class="campo-texto" type="number" inputmode="numeric" min="1" style="max-width:90px"></label>` : ""}
      ${comMin ? `<label class="cod">Parei no minuto <input id="ri-min" class="campo-texto" type="number" inputmode="decimal" min="0" step="0.5" style="max-width:90px"></label>` : ""}</div>
    <label class="cod" for="ri-nota">Nota (opcional)</label><textarea id="ri-nota" rows="3" class="campo-texto" placeholder="O que ficou, nas suas palavras." data-rascunho="item:${esc(cod)}">${esc(rascunho("item:" + cod))}</textarea>
    <div class="acoes"><button class="bt" type="button" data-acao="registrar-item">Salvar</button>${g.length > 1 ? `<button class="bt sec" type="button" data-acao="marcar-tudo">Já li inteiro</button>` : ""}
      ${gravandoAqui ? `<button class="bt rec" type="button" data-acao="parar-item">■ Parar · <span id="rec-tempo">${mmss((Date.now() - gravacao.inicio) / 1000)}</span></button>`
        : `<button class="bt sec" type="button" data-acao="gravar-item" ${gravacao ? "disabled" : ""}>🎙 Nota em voz</button>`}</div>
    ${E.erroFala ? `<p class="erro">${esc(E.erroFala)}</p>` : ""}
    ${minhas.length ? `<div class="minhas">${minhas.map(f => `<p class="cita">${f.texto ? esc(f.texto) : `🎙 nota de ${mmss(f.seg)} · ${f.enviada ? "a transcrição chega de madrugada" : "aguardando envio"}`}</p>`).join("")}</div>` : ""}
    ${E.registrouItem === cod ? `<p class="cod ok">Registrado.</p>` : ""}</div></div>`;
}
function registrarItem() {
  const cod = E.episodio, el = document.getElementById("registro-item");
  const feitos = [...el.querySelectorAll("input[type=checkbox]:checked")].flatMap(c => c.value.split(","));
  delete E.rascunhos["item:" + cod];
  const nota = document.getElementById("ri-nota").value.trim(), m = parseFloat(String(document.getElementById("ri-min")?.value || "").replace(",", "."));
  feitos.forEach(id => { E.feitas.add(id); delete E.andamento[id]; }); cobrir(cod);
  if (feitos.length && IT[cod] && !proximaDoItem(cod)) E.lidas.add(cod);
  if (feitos.length) registrar({ evento: "terminou", sessao: feitos[0], bloco: feitos, min: 0, formato: E.formato, fora: true, ...(nota ? { nota } : {}) });
  if (feitos.length && nota) feitos.forEach(id => { E.notas[id] = nota; });
  if (!isNaN(m)) {   // parou no meio de um vídeo ou áudio: guarda o ponto na peça em que parou
    const pos = Math.round(m * 60), resto = contaveis(cod).filter(x => !E.feitas.has(x.id)).sort((a, b) => a.ordem - b.ordem);
    const x = resto.find(y => y.de != null && y.ate != null && y.de <= pos && pos < y.ate) || resto[0];
    if (x) { E.andamento[x.id] = { pos, quando: new Date().toISOString() }; registrar({ evento: "parou", sessao: x.id, min: 0, posicao: pos }); }
  }
  const pg = parseInt(document.getElementById("ate-pag")?.value), naPag = pg && isNaN(m) ? pecaDaPagina(cod, pg) : null;
  if (naPag) { E.andamento[naPag.id] = { pag: pg, quando: new Date().toISOString() }; registrar({ evento: "parou", sessao: naPag.id, min: 0, pagina: pg }); }
  if (nota && !feitos.length) {   // nota solta sobre o conteúdo: vai para o Notes já ligada ao item
    const agora = new Date(), id = agora.toISOString().slice(0, 19).replace(/[-:]/g, "").replace("T", "-");
    E.falas.unshift({ id, texto: nota, quando: agora.toISOString(), enviada: true, item: cod }); registrar({ evento: "escreveu", fala: id, texto: nota, item: cod });
  }
  E.registrouItem = cod; salvar(); telaHoje();
}
// Resumo de um item com o tempo que você escolher: se já existe um desse tamanho, lê ou ouve; senão, pede.
// Guia de um áudio (decisão de 2026-10-20, sob pedido): o do próprio trecho, ou o que a esteira fez em dados/guias.json
function esbocoDe(o) {
  if (o.esboco && o.esboco.length) return o.esboco;
  const r = o.tipo === "fundo" && !GUIAS[o.item] ? resumoNov(o) : null;   // episódio das Novidades: os pontos do resumo médio
  return (r ? r.pontos : (GUIAS[o.item] || GUIAS[(fluxoDe(o) || {}).origem] || {}).esboco || []).filter(([t]) => t >= (o.de || 0) - 1 && (!o.ate || t < o.ate));
}
// Resumo do conteúdo inteiro para guardar (pedido de 2026-10-20): três tamanhos fixos, feitos pela esteira a partir
// do texto original. Curto ~1 min 30 de leitura, médio 3–5 min, completo 5–10 min (200 palavras por minuto).
const TAMANHOS = [["2", "Curto", "~1 min 30 de leitura"], ["4", "Médio", "3–5 min"], ["8", "Completo", "5–10 min"]];
function tamanhosDeResumo(f) {
  const prontos = f.resumos || [];
  return `<h3>Resumo ${doQue(f)} inteiro</h3><p class="cod">Se valeu a pena, peça um resumo para guardar. Fica pronto de madrugada, a partir da transcrição.</p>
    <div class="tamanhos">${TAMANHOS.map(([k, nome, tempo]) => {
      const pronto = prontos.includes(k), pedido = E.decisoes["pedido:" + f.cod + "@" + k];
      return pronto ? `<button class="bt" type="button" data-resumo-item="${esc(f.cod)}" data-k="${k}">Ler o ${nome.toLowerCase()} <small>${tempo}</small></button>`
        : pedido ? `<button class="bt sec desligado" type="button" data-cancelar="pedido:${esc(f.cod)}@${k}">${nome}: pedido, chega de madrugada <small>tocar para cancelar</small></button>`
        : `<button class="bt sec" type="button" data-pedir-item="${esc(f.cod)}" data-k="${k}">${nome} <small>${tempo}</small></button>`;
    }).join("")}</div>
    ${prontos.filter(k => !TAMANHOS.some(t => t[0] === k)).map(k => `<button class="bt sec" type="button" data-resumo-item="${esc(f.cod)}" data-k="${k}">Já pronto: resumo de ${k} min</button>`).join("")}`;
}
function blocoResumoItem(f, ps) {
  const total = soma(ps), sug = Math.max(1, Math.min(ALVO[E.tempo], Math.floor(total / 2))), prontos = f.resumos || [];
  const k = String(E.rzItem && E.rzItem.cod === f.cod ? E.rzItem.min : sug), pronto = prontos.includes(k), voz = f.audios && f.audios[k];
  return `<h3>Resumo</h3><div class="resumir">
    <p class="cod">O ${f.tipo === "podcast" ? "episódio" : "texto"} inteiro leva ${fmtMin(total)}. Escolha o tamanho do resumo (até a metade).</p>
    <div class="campo pedir"><label class="cod" for="rzi-min">Resumo de</label>
      <input id="rzi-min" type="number" inputmode="numeric" min="1" max="${Math.max(1, Math.floor(total / 2))}" value="${k}" style="max-width:70px" data-rz-item="${esc(f.cod)}"><span class="cod">min</span></div>
    <div class="acoes">${pronto ? `<button class="bt" type="button" data-resumo-item="${esc(f.cod)}" data-k="${k}">Ler</button>${voz ? `<button class="bt sec" type="button" data-ouvir-resumo="${esc(f.cod)}" data-k="${k}">▶ Ouvir (${voz.min} min)</button>` : ""}`
      : E.decisoes["pedido:" + f.cod + "@" + k] ? `<span class="cod">Resumo de ${k} min pedido: chega na próxima madrugada.</span>`
      : `<button class="bt" type="button" data-pedir-item="${esc(f.cod)}" data-k="${k}">Pedir resumo de ${k} min</button>`}</div>
    ${prontos.length ? `<p class="cod">Já prontos: ${prontos.map(x => `${x} min`).join(", ")}. Escritos pelo Claude a partir do texto original.</p>` : ""}</div>`;
}

// ---------- Em andamento: sessões começadas e não terminadas, no topo do Hoje ----------
function acharSessao(id) {
  const x = SESS.find(y => y.id === id); if (x) return x;
  if (id.includes("+")) {   // bloco de trechos: "FX-X.02+3" = 3 trechos a partir do 02
    const [ini, n] = id.split("+"), a = SESS.find(y => y.id === ini);
    if (a) { const ts = SESS.filter(y => y.item === a.item).sort((x, y) => x.ordem - y.ordem), i = ts.indexOf(a); return juntar(ts.slice(i, i + +n)); }
  }
  const fd = FUNDO.find(y => y.cod === id);
  if (fd) return { ...fd, id: fd.cod, item: fd.cod, tipo: "fundo", modo: "audio", onde: "app", ate: null };
  return null;
}
// Séries e Conteúdos (reestruturação de 2026-10-23): as duas abas usam a mesma tela (tela-hoje) e a mesma escolha por tempo.
// Séries = livros da grade; Conteúdos = cartas, empresas, assets e Relevantes (o que o código chama de Fluxo e Coleções).
const naHoje = () => E.aba === "series" || E.aba === "conteudos";
const dominioDe = o => ehFluxo(o) ? "conteudos" : "series";   // o: oferta ou sessão (precisa de .item)
const dominioItem = cod => /^(FX|CL|EM)-/.test(cod) ? "conteudos" : "series";
// horas e conclusão de um grupo de conteúdos (só o que conta: a voz do Alex repete as mesmas páginas)
function minutosConteudo(cods) { const ps = cods.flatMap(contaveis); return { total: soma(ps), feito: soma(ps.filter(x => E.feitas.has(x.id))) }; }
const codsDoGrupo = g => g.startsWith("Série ") ? D.series[parseInt(g.slice(6)) - 1].itens : FLUXO.filter(f => !E.decisoes["arquivar:" + f.cod] && grupoDe({ item: f.cod }) === g).map(f => f.cod);
// um cartão por livro ou conteúdo (pedido de 2026-10-24: o iPad mostrava "Caps. 1 a 2" e "Caps. 1 a 4" do mesmo livro);
// Continuar abre o trecho mais recente; Finalizar fecha tudo o que está aberto daquele livro
// aparelho sem token não sincroniza: o que você faz nele não chega ao outro aparelho nem à madrugada (revisão de 2026-10-24)
function avisoToken() {
  if (E.config.token) return "";
  return `<div class="aviso"><b>Este aparelho não está sincronizando.</b><p>O que você faz aqui fica só aqui: não aparece no outro aparelho e não entra no registro. Cole o token em Caixa → Ajustes.</p>
    <div class="acoes"><a class="bt sec" href="#caixa">Abrir Ajustes</a></div></div>`;
}
function blocoAndamento(dom) {
  const abertos = Object.entries(E.andamento).sort((a, b) => b[1].quando.localeCompare(a[1].quando))
    .map(([id, a]) => ({ id, a, s: acharSessao(id) })).filter(x => x.s && x.s.tipo !== "fundo" && dominioDe(x.s) === dom);
  const porItem = new Map();
  for (const x of abertos) { const k = x.s.item || x.id; if (!porItem.has(k)) porItem.set(k, { ...x, ids: [] }); porItem.get(k).ids.push(x.id); }
  const todos = [...porItem.values()], lista = todos.slice(0, 3);
  if (!lista.length) return "";
  return `<div class="andamento"><p class="olho">Em andamento${todos.length > 3 ? ` · mais ${todos.length - 3} depois destes` : ""}</p>${lista.map(({ id, a, s, ids }) => `
    <div class="item"><div class="meta"><span class="chip fluxo-tag">${s.modo === "audio" ? "áudio" : "leitura"}</span>
      <span>${esc(s.titulo)}</span>${a.pag || a.pos ? `<span>${ondeParou(a)}</span>` : ""}</div>
      <h3>${esc(nomeDoItem(s))}</h3>
      <div class="acoes"><button class="bt" type="button" data-continuar="${esc(id)}">Continuar</button>
        <button class="bt sec" type="button" data-finalizar="${esc(ids.join("|"))}">Finalizar</button></div></div>`).join("")}</div>`;
}

// ---------- Fundo (easy listening): áudio longo para ouvir trabalhando; sem tempo, sem trechos, sem nota ----------
const diasDesde = d => Math.floor((Date.now() - new Date(d)) / 86400000);
function filaFundo() {
  const emRelevantes = new Set([...FLUXO.filter(f => f.url).map(f => f.url), ...SESS.filter(x => /^FX-/.test(x.item) && x.url).map(x => x.url)]);   // já está (ou esteve) em Relevantes: não repete no Fundo
  return FUNDO.filter(x => !E.ouvidos.includes(x.cod) && !E.feitas.has(x.cod) && E.decisoes["arquivar:" + x.cod] !== true && !emRelevantes.has(x.url) && (x.tema === "acervo" || depois(x) || !x.publicado || diasDesde(x.publicado) <= 30))   // Fundo: só o novo (30 dias)
    .sort((a, b) => (E.posicoes[b.cod] ? 1 : 0) - (E.posicoes[a.cod] ? 1 : 0) || (b.destaque ? 1 : 0) - (a.destaque ? 1 : 0) || new Date(b.publicado) - new Date(a.publicado));
}
function telaFundo() {
  return `
    <div><p class="olho">Para ouvir trabalhando</p><h1 class="titulo-tela">Fundo</h1></div>
    <div class="sub" role="group" aria-label="Texto, áudio ou fundo">
      ${FORMATOS.map(([k, n]) => `<button type="button" data-formato="${k}" aria-pressed="${E.formato === k}">${n}</button>`).join("")}
    </div>
    ${listaFundo()}`;
}
function listaFundo() {
  const fila = filaFundo();
  return `${fila.length ? [["Novidades", fila.filter(x => !["acervo", "trabalho"].includes(x.tema)), false], ...[...new Set(fila.filter(x => x.tema === "acervo").map(x => x.fonte))].map(f => [f, fila.filter(x => x.fonte === f && x.tema === "acervo"), true]), ["Trabalho (energia e utilities)", fila.filter(x => x.tema === "trabalho"), true]]
      .filter(g => g[1].length).map(([nome, its, fechado]) => `${fechado ? `<details class="grupo"><summary class="cab-serie"><b>${esc(nome)}</b><span class="cod">${its.length} episódios${its[0].tema === "acervo" ? " · acervo" : ""}</span></summary>` : `<h3>${nome}</h3>`}<div class="lista">${its.map(x => {
      const pos = E.posicoes[x.cod], velho = x.tema !== "acervo" && diasDesde(x.publicado) > 7;
      return `<div class="item${x.imagem ? " com-capa" : ""}">${x.imagem ? `<img class="capa" src="${esc(x.imagem)}" alt="" loading="lazy">` : ""}<div class="meta"><span class="origem">${esc(x.fonte)}</span><span>${new Date(x.publicado).toLocaleDateString("pt-BR")}</span>
          ${x.minutos ? `<span>${fmtMin(x.minutos)}</span>` : ""}${pos ? `<span class="chip fluxo-tag">parou em ${mmss(pos)}</span>` : ""}${velho ? '<span class="chip">mais de 7 dias</span>' : ""}${x.destaque ? '<span class="chip aceso">Recomendado</span>' : ""}${GUIAS[x.cod] ? '<span class="chip">com guia</span>' : ""}</div>
        <h3>${esc(x.titulo)}</h3>${x.destaque && x.motivo ? `<p class="resumo-ep"><i>${esc(x.motivo)}</i></p>` : x.resumo ? `<p class="resumo-ep">${esc(x.resumo)}</p>` : ""}
        <div class="acoes"><button class="bt" type="button" data-fundo="${esc(x.cod)}">${pos ? "Continuar" : "Ouvir"}</button>
          ${velho || x.tema === "acervo" ? `<button class="bt sec" type="button" data-arquivar="${esc(x.cod)}">Arquivar</button>` : ""}
          <button class="bt sec" type="button" data-mover="relevantes" data-cod="${esc(x.cod)}">→ Relevantes</button>
          <button class="bt sec" type="button" data-remover="${esc(x.cod)}">Remover</button></div></div>`;
    }).join("")}</div>${fechado ? "</details>" : ""}`).join("")
    : `<div class="aviso"><b>Nada na fila de fundo.</b><p>Os episódios novos chegam de madrugada.</p></div>`}`;
}

// ---------- Novidades (decisão de 2026-10-22): o feed dos podcasts (depois Substack e YouTube), episódio inteiro, sem trechos.
// Cada episódio traz um resumo médio com os minutos clicáveis, que tocam no player do próprio Cérebro.
// Saídas: Ouvir depois (fica guardado), Terminei (era bom) e Rejeitar (era ruim); as duas últimas entram no placar dos programas.
const depois = x => E.decisoes["depois:" + x.cod] ?? !!x.salvo;
const resumoNov = x => RESUMOS_NOV[x.cod] || RESUMOS_NOV[x.origem] || RESUMOS_NOV[x.cod.replace(/^FX-/, "")];
// Podcasts que estavam em Relevantes, em trechos, passam para Novidades como "Ouvir depois"; o progresso dos trechos vira o ponto de escuta.
function podcastsParaNovidades() {
  for (const f of FLUXO.filter(x => x.tipo === "podcast")) {
    const ts = SESS.filter(x => x.item === f.cod && x.tipo === "audio").sort((a, b) => a.ordem - b.ordem);
    const url = ts.length ? ts[0].url : f.movido || /\.(mp3|m4a)(\?|$)/i.test(f.url || "") ? f.url : null;
    if (!url) continue;   // sem áudio no app: continua em Relevantes
    const feitos = ts.filter(x => E.feitas.has(x.id)), falta = ts.find(x => !E.feitas.has(x.id));
    if (ts.length && !falta) E.feitas.add(f.cod);   // todos os trechos ouvidos: episódio terminado
    const pos = Math.max(0, ...ts.map(x => E.andamento[x.id]?.pos || 0), feitos.length && falta ? falta.de || 0 : 0);
    if (pos && !E.posicoes[f.cod]) E.posicoes[f.cod] = pos;
    FUNDO = FUNDO.filter(x => x.url !== url);
    FUNDO.push({ cod: f.cod, origem: f.origem, fonte: f.fonte, titulo: f.titulo, url, minutos: f.minutos, publicado: f.publicado || f.entrou, tema: "top",
      imagem: f.imagem, resumo: f.resumo || f.motivo, salvo: true });
    FLUXO = FLUXO.filter(x => x !== f); SESS = SESS.filter(x => x.item !== f.cod);
  }
}
function ouvirNovidade(cod, seg) {
  const s = acharSessao(cod); if (!s) return;
  if (E.tocando && E.tocando.id === cod) { const a = document.getElementById("audio"); a.currentTime = seg; a.play().catch(() => {}); return; }
  E.andamento[cod] = { pos: seg, quando: new Date().toISOString() };
  registrar({ evento: "comecou", sessao: cod, formato: "audio", ...(seg ? { de: Math.round(seg) } : {}) });
  tocar(s, seg); telaNovidades(); if (E.aba === "semana") telaSemana();
}
function cartaoNovidade(x) {
  if (x.spotify) return cartaoSpotify(x);
  const pos = E.posicoes[x.cod], r = resumoNov(x), guia = !r && (GUIAS[x.cod] || GUIAS[x.origem]), salvo = depois(x);
  const pontos = r ? r.pontos : guia ? guia.esboco : [];
  const tocando = E.tocando && E.tocando.id === x.cod;
  return `<div class="item nov${x.imagem ? " com-capa" : ""}">${x.imagem ? `<img class="capa" src="${esc(x.imagem)}" alt="" loading="lazy">` : ""}
    <div class="meta">${ACERVO_IDX && ACERVO_IDX.programas[x.fonte] ? `<button type="button" class="origem canal" data-canal="${esc(x.fonte)}">${esc(x.fonte)} ›</button>` : `<span class="origem">${esc(x.fonte)}</span>`}${x.publicado ? `<span>${new Date(x.publicado).toLocaleDateString("pt-BR")}</span>` : ""}
      ${x.minutos ? `<span>${fmtMin(x.minutos)}</span>` : ""}${pos ? `<span class="chip fluxo-tag">parou em ${mmss(pos)}</span>` : ""}${x.destaque ? '<span class="chip aceso">Recomendado</span>' : ""}</div>
    <h3>${esc(x.titulo)}</h3>${x.destaque && x.motivo ? `<p class="resumo-ep"><i>${esc(x.motivo)}</i></p>` : x.resumo ? `<p class="resumo-ep">${esc(x.resumo)}</p>` : ""}
    ${pontos.length ? `<details class="resumo-nov" data-cod="${esc(x.cod)}"><summary>${r ? `Resumo · ${Math.max(1, Math.round((r.palavras || 0) / 200))} min de leitura` : "Guia com minutos"}</summary>
      <div class="esboco">${pontos.map(([t, nome, txt]) => `<button type="button" data-ouvir-em="${esc(x.cod)}" data-seg="${Math.floor(t)}"><span class="cod">▶ ${mmss(t)}</span><span><b>${esc(nome)}</b>${txt ? `<small>${esc(txt)}</small>` : ""}</span></button>`).join("")}</div>
      ${r && r.fonte ? `<p class="cod">${esc(r.fonte)}</p>` : ""}</details>`
      : (x.minutos || 0) > 150 ? `<p class="cod">Sem resumo: episódio longo demais (${fmtMin(x.minutos)}) para transcrever aqui.</p>`   // acima de 150 min a transcrição estoura a memória (2026-10-23)
      : `<p class="cod">Resumo: fica pronto numa das próximas madrugadas.</p>`}
    ${blocoAnotar(x)}
    <div class="acoes"><button class="bt" type="button" data-ouvir-em="${esc(x.cod)}" data-seg="${Math.floor(pos || 0)}">${tocando ? "Tocando" : pos ? "Continuar" : "Ouvir"}</button>
      <button class="bt sec" type="button" data-depois="${esc(x.cod)}" aria-pressed="${salvo}">${salvo ? "✓ Ouvir depois" : "Ouvir depois"}</button>
      <button class="bt sec" type="button" data-concluir="${esc(x.cod)}">Terminei</button>
      <button class="bt sec" type="button" data-remover="${esc(x.cod)}">Rejeitar</button></div></div>`;
}
// Programa só do Spotify (2026-10-24): áudio protegido, sem resumo nem player; só o aviso de episódio novo
function cartaoSpotify(x) {
  return `<div class="item nov${x.imagem ? " com-capa" : ""}">${x.imagem ? `<img class="capa" src="${esc(x.imagem)}" alt="" loading="lazy">` : ""}
    <div class="meta"><span class="origem">${esc(x.fonte)}</span>${x.publicado ? `<span>${new Date(x.publicado).toLocaleDateString("pt-BR")}</span>` : ""}${x.minutos ? `<span>${fmtMin(x.minutos)}</span>` : ""}<span class="chip">só Spotify</span></div>
    <h3>${esc(x.titulo)}</h3><p class="cod">Sem resumo: o programa só existe no Spotify, que não deixa baixar o áudio para transcrever.</p>
    ${blocoAnotar(x)}
    <div class="acoes"><a class="bt" href="${esc(x.url)}" target="_blank" rel="noopener">Abrir no Spotify</a>
      <button class="bt sec" type="button" data-concluir="${esc(x.cod)}">Terminei</button>
      <button class="bt sec" type="button" data-remover="${esc(x.cod)}">Rejeitar</button></div></div>`;
}
// Nota sobre o episódio (pedido de 2026-10-22): escrita ou em voz; a esteira junta tudo no Feed, um cartão por conteúdo
function blocoAnotar(x, aberto) {
  const minhas = E.falas.filter(f => f.item === x.cod), aqui = gravacao && gravacao.item === x.cod;
  return `<details class="anotar" data-cod="${esc(x.cod)}"${aberto ? " open" : ""}><summary>Anotar${minhas.length ? ` · ${minhas.length} nota${minhas.length > 1 ? "s" : ""}` : ""}</summary>
    <textarea class="campo-texto" rows="3" placeholder="O que ficou, nas suas palavras. Para falar, use o microfone do teclado ou o botão de voz." data-rascunho="nov:${esc(x.cod)}">${esc(rascunho("nov:" + x.cod))}</textarea>
    <div class="acoes"><button class="bt" type="button" data-nota-nov="${esc(x.cod)}">Salvar nota</button>
      ${aqui ? `<button class="bt rec" type="button" data-acao="parar-item">■ Parar · <span id="rec-tempo">${mmss((Date.now() - gravacao.inicio) / 1000)}</span></button>`
        : `<button class="bt sec" type="button" data-gravar-nov="${esc(x.cod)}" ${gravacao ? "disabled" : ""}>🎙 Nota em voz</button>`}</div>
    ${aqui && E.erroFala ? `<p class="erro">${esc(E.erroFala)}</p>` : ""}
    ${minhas.map(f => `<p class="cita">${f.texto ? esc(f.texto) : `🎙 nota de ${mmss(f.seg)} · ${f.enviada ? "a transcrição chega de madrugada" : "aguardando envio"}`}</p>`).join("")}
    <p class="cod">Vai para o Notes, junto com o resumo do episódio.</p></details>`;
}
function telaNovidades() {
  const fila = filaFundo(), novos = fila.filter(x => !["acervo", "trabalho"].includes(x.tema));
  // Só entra com resumo (pedido de 2026-10-26): o episódio aparece em "Novos" quando o resumo fica pronto; antes disso
  // espera em "Chegando", fechado. Spotify e episódio acima de 150 min nunca terão resumo, então entram direto.
  const comResumo = x => resumoNov(x) || x.spotify || (x.minutos || 0) > 150;
  const salvos = novos.filter(depois), resto = novos.filter(x => !depois(x) && comResumo(x)), chegando = novos.filter(x => !depois(x) && !comResumo(x));
  // redesenhar não fecha o resumo que você está lendo nem tira a tela do lugar
  const el = document.getElementById("tela-novidades"), m = document.getElementById("main"), topo = m.scrollTop;
  const abertos = new Set([...el.querySelectorAll("details[data-cod][open]")].map(d => d.className + ":" + d.dataset.cod));
  const fechado = (nome, its, nota) => its.length ? `<details class="grupo"><summary class="cab-serie"><b>${esc(nome)}</b><span class="cod">${its.length} episódios${nota}</span></summary><div class="lista">${its.map(cartaoNovidade).join("")}</div></details>` : "";
  el.innerHTML = `${avisoToken()}
    <div><p class="olho">Podcasts das suas fontes</p><h1 class="titulo-tela">Novidades</h1></div>
    <p class="cod">Leia o resumo, toque num minuto para ouvir dali. Terminei = era bom; Rejeitar = era ruim.</p>
    ${salvos.length ? `<h3>Ouvir depois</h3><div class="lista">${salvos.map(cartaoNovidade).join("")}</div>` : ""}
    <div class="cab-serie"><h3>Novos</h3><span class="cod">${resto.length} episódio${resto.length === 1 ? "" : "s"}</span></div>
    ${resto.length ? `<div class="lista">${resto.map(cartaoNovidade).join("")}</div>` : `<div class="aviso"><b>Nada novo por agora.</b><p>Os episódios novos chegam de madrugada, já com resumo.</p></div>`}
    ${chegando.length ? `<details class="grupo"><summary class="cab-serie"><b>Chegando</b><span class="cod">${chegando.length} sem resumo ainda</span></summary>
      <p class="cod">Entram em Novos quando o resumo ficar pronto, na próxima madrugada.</p>
      <div class="ofertas">${chegando.map(x => `<div class="oferta"><span class="nome"><b>${esc(x.titulo)}</b><span>${esc(x.fonte)}${x.minutos ? ` · ${fmtMin(x.minutos)}` : ""}${x.destaque ? " · Recomendado" : ""}</span></span></div>`).join("")}</div></details>` : ""}
    ${fechado("Trabalho (energia e utilities)", fila.filter(x => x.tema === "trabalho"), "")}
    ${[...new Set(fila.filter(x => x.tema === "acervo").map(x => x.fonte))].map(f => fechado(f, fila.filter(x => x.fonte === f && x.tema === "acervo"), " · acervo")).join("")}
`;   // placar dos programas saiu do app (pedido de 2026-10-23); a esteira segue gerando estatisticas.json
  el.querySelectorAll("details[data-cod]").forEach(d => { if (abertos.has(d.className + ":" + d.dataset.cod)) d.open = true; });
  if (E.aba === "novidades") m.scrollTop = topo;
}

// ---------- Inscrições (pedido de 2026-10-22): tudo o que o Cérebro puxa sozinho, só para ver (mudanças pelo chat) ----------
const MODO = { todos: "todos", curadoria: "filtrado", pausado: "pausado", "sem-feed": "sem feed", spotify: "só Spotify" };
function linhaInscricao(x) {
  const u = x.ultimo, dias = u && /^\d{4}-\d{2}-\d{2}$/.test(u.data || "") ? diasDesde(u.data) : null;
  const ac = ACERVO_IDX && ACERVO_IDX.programas[x.nome];
  return `<div class="oferta inscricao"><span class="nome"><b>${esc(x.nome)}</b>${x.autor ? `<span>${esc(x.autor)}</span>` : ""}
      ${u ? `<span>Último: ${esc(u.titulo || "")}${u.data ? ` · ${dias != null ? (dias === 0 ? "hoje" : dias === 1 ? "ontem" : `há ${dias} dias`) : esc(u.data)}` : ""}</span>` : ""}
      ${ac ? `<button class="bt sec" type="button" data-acervo="${esc(x.nome)}">Todos os episódios · ${ac.n.toLocaleString("pt-BR")}</button>` : ""}</span>
    ${E.decisoes["desinscreveu:" + x.nome]
      ? `<span class="inscricao-acao"><span class="chip">a cancelar</span><button class="bt sec" type="button" data-cancelar="${esc("desinscreveu:" + x.nome)}">Desfazer</button></span>`
      : `<span class="inscricao-acao"><span class="chip${x.modo === "pausado" || x.modo === "sem-feed" ? "" : " aceso"}">${esc(MODO[x.modo] || x.modo)}</span>
        <button class="bt sec" type="button" data-desinscrever="${INSCRICOES && INSCRICOES.cartas.includes(x) ? "carta" : "podcast"}" data-nome="${esc(x.nome)}">Cancelar inscrição</button></span>`}</div>`;
}
function telaInscricoes() {
  const el = document.getElementById("tela-inscricoes"), I = INSCRICOES;
  if (E.acervo) { telaAcervo(el); return; }
  if (!I) { el.innerHTML = `<div><h1 class="titulo-tela">Inscrições</h1></div><p class="erro">Lista ainda não gerada (projeto/gerador/inscricoes.py).</p>`; return; }
  const grupos = [...new Set(I.podcasts.map(x => x.grupo))];
  const bloco = (nome, its, aberto) => `<details class="grupo"${aberto ? " open" : ""}><summary class="cab-serie"><b>${esc(nome)}</b><span class="cod">${its.length}</span></summary><div class="ofertas">${its.map(linhaInscricao).join("")}</div></details>`;
  const ativos = I.podcasts.filter(x => x.modo !== "pausado" && x.modo !== "sem-feed").length;
  el.innerHTML = `
    <div><p class="olho">O que o Cérebro puxa sozinho, toda madrugada</p><h1 class="titulo-tela">Inscrições</h1></div>
    <p class="cod">${ativos} podcasts ativos · ${I.cartas.length} fontes de cartas e memos · lista de ${esc(I.gerado)}.<br>Todo episódio novo entra nas Novidades e você decide o que fica (sem filtro desde 2026-10-24) · Só Spotify = avisa episódio novo, sem resumo · Sem feed = ainda não puxa. Toque em "Todos os episódios" para ver o acervo inteiro de um programa, ou busque em todos acima. Para cancelar, use o botão da linha (vale a partir da próxima madrugada); para incluir ou mudar o modo, peça no chat.</p>
    ${ACERVO_IDX ? `<form class="campo" id="form-busca-acervo"><input id="busca-acervo" type="search" placeholder="Buscar em todos os episódios (ex.: Mercado Libre)" autocomplete="off" class="campo-texto" value="${esc(E.buscaAcervo || "")}"><button class="bt" type="submit">Buscar</button></form>
      <div id="resultado-acervo"></div>` : ""}
    <h3>Podcasts</h3>${grupos.map((g, i) => bloco(g, I.podcasts.filter(x => x.grupo === g), i === 0)).join("")}
    <h3>Cartas e memos</h3>${bloco("Gestoras, empresas e autores", I.cartas, false)}
    <h3>Substack</h3><div class="aviso"><p>Nenhum ainda. Mande os nomes no chat e eles passam a entrar nas Novidades.</p></div>
    <h3>YouTube</h3><div class="aviso"><p>Nenhum canal ainda. A playlist "Cérebro" aguarda o link (o YouTube bloqueia a transcrição daqui; entra só título e duração).</p></div>`;
  if (E.buscaAcervo) buscarAcervo(E.buscaAcervo);
}

// ---------- Acervo (pedido de 2026-10-24): todos os episódios de cada podcast inscrito, só título; busca em todos ----------
// Arquivos em dados/acervo/ (projeto/gerador/acervo.py); baixados só quando você abre um programa ou busca.
// Tocar = toca aqui sem mandar para as Novidades; Ouvir depois = entra nas Novidades e ganha resumo como os outros.
const ACERVO = {};
async function carregarAcervo(nome) {
  if (ACERVO[nome]) return ACERVO[nome];
  const a = ACERVO_IDX.programas[nome]; if (!a) return [];
  try { const d = await (await fetch("dados/acervo/" + a.arq)).json(); ACERVO[nome] = d.eps.map(e => ({ id: e[0], data: e[1], titulo: e[2], min: e[3], url: e[4], desc: e[5] || "", q: semAcento(e[2] + " " + (e[5] || "")) })).map(e => ({ ...e, j: e.q.replace(/[^a-z0-9]/g, "") })); }
  catch (err) { return null; }
  return ACERVO[nome];
}
const codAcervo = id => "FD-AC-" + id;
// todas as palavras, ou a busca colada ("mercado libre" também acha "MercadoLibre")
const casaAcervo = (e, ws) => ws.every(w => e.q.includes(w)) || (ws.length > 1 && e.j.includes(ws.join("")));
function itemAcervo(nome, e, tema) { return { cod: codAcervo(e.id), fonte: nome, titulo: e.titulo, url: e.url, minutos: e.min, publicado: e.data, tema }; }
function aplicarTrazidos() {
  for (const x of [...Object.values(E.trazidos || {}), ...Object.values(E.acervoTocados || {})])
    if (!FUNDO.some(y => y.cod === x.cod || y.url === x.url)) FUNDO.push({ ...x });
}
function linhaAcervo(nome, e, comPrograma) {
  const cod = codAcervo(e.id), x = FUNDO.find(y => y.cod === cod || y.url === e.url), naNov = x && (x.tema !== "tocado" || depois(x)), tocando = E.tocando && x && E.tocando.id === x.cod;
  const fora = /youtube\.com|open\.spotify\.com/.test(e.url);   // programa só do Spotify: lista do YouTube ou do Spotify, sem áudio aqui (2026-10-24)
  const quando = e.data.length === 10 ? new Date(e.data + "T12:00").toLocaleDateString("pt-BR") : e.data ? `≈ ${e.data.slice(5)}/${e.data.slice(0, 4)}` : "";
  if (fora) return `<div class="item"><div class="meta">${comPrograma ? `<span class="origem">${esc(nome)}</span>` : ""}${quando ? `<span>${quando}</span>` : ""}${e.min ? `<span>${fmtMin(e.min)}</span>` : ""}</div>
    <h3>${esc(e.titulo)}</h3>${e.desc ? `<p class="cod">${esc(e.desc.slice(0, 180))}${e.desc.length > 180 ? "…" : ""}</p>` : ""}
    <div class="acoes"><a class="bt" href="${esc(e.url)}" target="_blank" rel="noopener">${/youtube/.test(e.url) ? "Abrir no YouTube" : "Abrir no Spotify"}</a></div></div>`;
  return `<div class="item"><div class="meta">${comPrograma ? `<span class="origem">${esc(nome)}</span>` : ""}${quando ? `<span>${quando}</span>` : ""}${e.min ? `<span>${fmtMin(e.min)}</span>` : ""}${x && E.posicoes[x.cod] ? `<span class="chip fluxo-tag">parou em ${mmss(E.posicoes[x.cod])}</span>` : ""}</div>
    <h3>${esc(e.titulo)}</h3>${e.desc ? `<p class="cod">${esc(e.desc.slice(0, 180))}${e.desc.length > 180 ? "…" : ""}</p>` : ""}
    <div class="acoes"><button class="bt" type="button" data-ac-tocar="${esc(nome)}" data-id="${e.id}">${tocando ? "Tocando" : x && E.posicoes[x.cod] ? "Continuar" : "Tocar"}</button>
      ${naNov ? `<span class="chip aceso">nas Novidades</span>` : `<button class="bt sec" type="button" data-ac-depois="${esc(nome)}" data-id="${e.id}">Ouvir depois</button>`}</div></div>`;
}
async function acaoAcervo(nome, id, paraNovidades) {
  const e = (await carregarAcervo(nome) || []).find(y => y.id === id); if (!e) return;
  let x = FUNDO.find(y => y.cod === codAcervo(id) || y.url === e.url);
  if (paraNovidades) {
    if (!x || x.tema === "tocado") {
      const novo = itemAcervo(nome, e, "trazido"); E.trazidos[novo.cod] = novo; delete E.acervoTocados[novo.cod];
      FUNDO = FUNDO.filter(y => y.cod !== novo.cod); FUNDO.push(novo); x = novo;
      registrar({ evento: "trouxe", item: novo.cod, fonte: nome, titulo: e.titulo, url: e.url, minutos: e.min, publicado: e.data });
    }
    E.decisoes["depois:" + x.cod] = true; registrar({ evento: "depois", item: x.cod, ligado: true, fonte: x.fonte, titulo: x.titulo });
  } else {
    if (!x) { x = itemAcervo(nome, e, "tocado"); E.acervoTocados[x.cod] = x; FUNDO.push(x);
      const ks = Object.keys(E.acervoTocados); if (ks.length > 20) delete E.acervoTocados[ks[0]]; }
    ouvirNovidade(x.cod, E.posicoes[x.cod] || 0);
  }
  salvar(); if (E.bio && naHoje()) telaHoje(); else telaInscricoes();
}
async function telaAcervo(el) {
  const nome = E.acervo, a = ACERVO_IDX.programas[nome] || {}, topo = document.getElementById("main").scrollTop;
  el.innerHTML = `<div><button class="bt sec" type="button" data-acervo="">← ${E.voltarAcervo && E.voltarAcervo.aba === "novidades" ? "Novidades" : "Inscrições"}</button><p class="olho">Todos os episódios</p><h1 class="titulo-tela">${esc(nome)}</h1></div><p class="cod">Carregando…</p>`;
  const eps = await carregarAcervo(nome);
  if (!eps) { el.innerHTML += `<p class="erro">Não consegui baixar a lista. Abra com internet.</p>`; return; }
  const q = semAcento(E.acervoQ || ""), achados = q ? eps.filter(e => casaAcervo(e, q.split(/\s+/))) : eps, n = E.acervoN || 50;
  el.innerHTML = `<div><button class="bt sec" type="button" data-acervo="">← ${E.voltarAcervo && E.voltarAcervo.aba === "novidades" ? "Novidades" : "Inscrições"}</button><p class="olho">Todos os episódios</p><h1 class="titulo-tela">${esc(nome)}</h1></div>
    <p class="cod">${eps.length.toLocaleString("pt-BR")} episódios${a.desde ? ` desde ${new Date(a.desde + "T12:00").getFullYear()}` : ""}, do mais novo ao mais velho. ${eps.every(e => /youtube\.com|open\.spotify\.com/.test(e.url)) ? "Programa só do Spotify: a lista vem do YouTube e do Spotify, e cada episódio abre lá (sem resumo, o áudio não pode ser baixado)." : 'Sem resumo: "Ouvir depois" manda para as Novidades, onde ele ganha resumo.'}</p>
    <form class="campo" id="form-busca-programa"><input id="busca-programa" type="search" placeholder="Buscar neste programa" autocomplete="off" class="campo-texto" value="${esc(E.acervoQ || "")}"><button class="bt" type="submit">Buscar</button></form>
    ${q ? `<p class="cod">${achados.length} episódio${achados.length === 1 ? "" : "s"} com "${esc(E.acervoQ)}".</p>` : ""}
    <div class="lista">${achados.slice(0, n).map(e => linhaAcervo(nome, e, false)).join("")}</div>
    ${achados.length > n ? `<div class="acoes"><button class="bt sec" type="button" data-ac-mais="1">Mostrar mais ${Math.min(50, achados.length - n)}</button></div>` : ""}`;
  document.getElementById("main").scrollTop = topo;
}
async function buscarAcervo(texto) {
  const caixa = document.getElementById("resultado-acervo"); if (!caixa) return;
  const q = semAcento(texto.trim()); if (!q) { caixa.innerHTML = ""; return; }
  const nomes = Object.keys(ACERVO_IDX.programas);
  if (nomes.some(n => !ACERVO[n])) caixa.innerHTML = `<p class="cod">Baixando o acervo (${nomes.length} programas, só na primeira busca)…</p>`;
  await Promise.all(nomes.map(carregarAcervo));
  const ws = q.split(/\s+/), achados = nomes.flatMap(n => (ACERVO[n] || []).filter(e => casaAcervo(e, ws)).map(e => [n, e])).sort((a, b) => b[1].data.localeCompare(a[1].data));
  if (!document.getElementById("resultado-acervo")) return;
  document.getElementById("resultado-acervo").innerHTML = `<div class="cab-serie"><h3>${achados.length.toLocaleString("pt-BR")} episódio${achados.length === 1 ? "" : "s"} com "${esc(texto.trim())}"</h3>
    <button class="bt sec" type="button" data-acao="limpar-busca-acervo">Limpar</button></div>
    <div class="lista">${achados.slice(0, 60).map(([n, e]) => linhaAcervo(n, e, true)).join("")}</div>
    ${achados.length > 60 ? `<p class="cod">Mostrando os 60 mais novos. Use mais palavras para afinar.</p>` : ""}`;
}

function estacaoLinha(it) {
  const lida = E.lidas.has(it.cod), tot = contaveis(it.cod).length, f = contaveis(it.cod).filter(x => E.feitas.has(x.id)).length;
  return `<button class="est ${lida ? "lida" : ""}" type="button" data-ficha="${it.cod}" style="color:${cor(it.cod)}">
    <span class="pino"></span>
    <span class="nome"><b>${esc(it.titulo)}</b><span>${it.cod} · ${esc(it.leitura)}${tot > 1 ? ` · ${f} de ${tot} sessões` : ""}</span></span>
    <span class="st">${lida ? "lido" : liberado(it) ? "" : "depois de " + it.pre}</span></button>`;
}

// ---------- sessão em curso ----------
let relogio = null;
function sessaoEmCurso() {
  const o = E.sessao, f = ehFluxo(o) ? fluxoDe(o) : null;
  let corpo;
  if (E.fase === 1 && o.onde === "resumo") {
    const fr = fluxoDe(o), k = o.id.split("@")[1], voz = fr && fr.audios && fr.audios[k];
    corpo = `${voz ? `<div class="acoes"><button class="bt" type="button" data-ouvir-resumo="${esc(fr.cod)}" data-k="${k}">▶ Ouvir este resumo (voz, ${voz.min} min)</button></div>` : ""}
      <article class="resumo" id="resumo">${E.resumo == null ? "<p>Carregando...</p>" : md(E.resumo)}</article>
      <div class="acoes"><button class="bt" type="button" data-acao="terminei">Terminei</button><button class="bt sec" type="button" data-acao="parei">Parei aqui</button></div>`;
  } else if (E.fase === 1 && o.onde === "transcricao") {
    corpo = `<article class="resumo" id="resumo">${E.resumo == null ? "<p>Carregando...</p>" : md(E.resumo)}</article>
      <div class="acoes"><button class="bt" type="button" data-acao="terminei">Terminei</button><button class="bt sec" type="button" data-acao="parei">Parei aqui</button></div>`;
  } else if (E.fase === 1 && o.onde === "app") {
    const fi = fluxoDe(o);
    const ts = fi ? trechosDe(fi.cod) : [], primeiro = (o.bloco || [o.id])[0], ultimo = (o.bloco || [o.id]).slice(-1)[0];
    const ia = ts.findIndex(x => x.id === primeiro), iz = ts.findIndex(x => x.id === ultimo);
    const nav = ts.length > 1 && o.tipo === "audio" ? `<div class="nav-trechos">
        ${ia > 0 ? `<button class="bt sec" type="button" data-trecho="${esc(ts[ia - 1].id)}">◀ Anterior</button>` : "<span></span>"}
        <button class="bt sec" type="button" data-episodio="${esc(fi.cod)}">Trechos (${iz + 1} de ${ts.length})</button>
        ${iz >= 0 && iz < ts.length - 1 ? `<button class="bt sec" type="button" data-trecho="${esc(ts[iz + 1].id)}">Próximo ▶</button>` : "<span></span>"}</div>` : "";
    corpo = `${nav}<p class="cod">O player fica fixo embaixo: pode trocar de aba que o áudio continua.</p><p class="pos-agora" id="pos-agora"></p>
      ${o.tipo === "fundo" ? `<p class="cod">${o.de ? `Continua de ${mmss(o.de)}. ` : ""}"Parei aqui" guarda o ponto para a próxima vez.</p>`
        : `<p class="cod">Trecho de ${mmss(o.de || 0)} a ${mmss(o.ate || 0)}.</p>`}
      <div class="acoes"><button class="bt sec" type="button" data-acao="recortar">✂ Recortar último minuto</button></div>
      ${E.recortes.length ? `<div class="recortes"><b>Recortes</b>${E.recortes.map(r => `<div><span class="cod">${mmss(Math.max(0, r - 60))}–${mmss(r)}</span></div>`).join("")}</div>` : ""}
      ${esbocoDe(o).length ? `<h3>Esboço com minutos</h3><div class="esboco">${esbocoDe(o).map(([t, nome, rz]) =>
        `<button type="button" data-ir="${t}" data-esb="${t}"><span class="cod">${mmss(t)}</span><span><b>${esc(nome)}</b>${rz ? `<small>${esc(rz)}</small>` : ""}</span></button>`).join("")}</div>` : ""}
      ${fi && fi.segmentos && o.tipo === "audio" ? `<div class="acoes"><button class="bt sec" type="button" data-acao="acompanhar">${E.acompanhar ? "Esconder a transcrição" : "Acompanhar a transcrição"}</button></div>
        ${E.acompanhar ? `<div class="acomp" id="acomp">${SEGS[fi.cod] ? SEGS[fi.cod].filter(([t]) => t >= (o.de || 0) - 1 && (!o.ate || t < o.ate)).map(([t, txt]) => `<span data-ir="${t}" data-t="${t}">${esc(txt)} </span>`).join("") : "Carregando..."}</div>` : ""}` : ""}
      ${o.tipo === "fundo" && FUNDO.some(y => y.cod === o.cod) ? `<h3>Comentar</h3>${blocoAnotar(FUNDO.find(y => y.cod === o.cod), true)}` : ""}
      ${o.tipo === "fundo" ? `<div class="acoes"><button class="bt sec" type="button" data-remover="${esc(o.cod)}">Rejeitar</button></div>`
        : f && /^FX-/.test(f.cod) ? `<div class="acoes">${f.tipo === "podcast" ? `<button class="bt sec" type="button" data-mover="fundo" data-cod="${esc(f.cod)}">Mandar para o Fundo</button>` : ""}<button class="bt sec" type="button" data-remover="${esc(f.cod)}">Remover de Relevantes</button></div>` : ""}
      ${!esbocoDe(o).length && o.tipo !== "fundo" && o.url && !String(o.url).startsWith("dados/") ? (E.decisoes["guia:" + o.item]
        ? `<p class="cod">Guia pedido (minutos + resumo de cada parte): fica pronto na próxima madrugada.</p>`
        : `<div class="acoes"><button class="bt sec" type="button" data-acao="pedir-guia">Fazer o guia: minutos + resumo de cada parte</button></div>`) : ""}
      ${!esbocoDe(o).length && E.decisoes["guia:" + o.item] ? `<div class="acoes"><button class="bt sec" type="button" data-cancelar="guia:${esc(o.item)}">Cancelar o guia</button></div>` : ""}
      <div class="acoes"><button class="bt" type="button" data-acao="terminei">${o.tipo === "fundo" ? "Terminei" : "Terminei o trecho"}</button><button class="bt sec" type="button" data-acao="parei">Parei aqui</button></div>
      ${fi && o.tipo === "audio" && fi.transcricao ? tamanhosDeResumo(fi) : ""}`;
  } else if (E.fase === 1) {
    const link = o.onde === "link" ? linkDe(o) : o.onde === "goodnotes" ? "goodnotes://" : null, como = comoE(o);
    const abrir = o.onde === "goodnotes" ? "Abrir o GoodNotes" : /YouTube/.test(como) ? "Abrir o vídeo" : /PDF/.test(como) ? "Abrir o PDF" : "Abrir a página";
    corpo = `<div class="aviso"><b>${o.onde === "livro" ? "Pegue o livro" : o.onde === "goodnotes" ? "Abra no GoodNotes" : o.onde === "semlink" ? "Ainda sem link" : "Abra o link"}: ${esc(o.titulo)}${o.paginas ? ` (págs. ${o.paginas})` : ""}</b>
        <p>${esc(como)}. ${o.onde === "link" ? "Volte aqui quando terminar." : "O Cérebro conta o tempo enquanto você lê."}${E.andamento[o.id]?.pag ? ` Você parou na pág. ${E.andamento[o.id].pag}.` : E.andamento[o.id]?.pos ? ` Você parou em ${mmss(E.andamento[o.id].pos)}.` : ""}</p></div>
      ${link ? `<div class="acoes"><a class="bt" href="${esc(link)}" target="_blank" rel="noopener" style="text-decoration:none">${abrir}</a></div>` : ""}
      <p class="olho">Já se passaram</p><p class="relogio" id="relogio">${mmss(E.seg)}</p>
      <div class="acoes"><button class="bt" type="button" data-acao="terminei">Terminei</button><button class="bt sec" type="button" data-acao="parei">Parei aqui</button></div>`;
  } else if (E.fase === 2) {
    corpo = `<div class="ritual">
      <div class="passo feito"><span class="bola">✓</span><div class="txt"><b>${o.modo === "audio" ? "Ouvir" : "Ler"}</b><small>${fmtMin(Math.max(1, Math.round(E.seg / 60)))}${E.recortes.length ? ` · ${E.recortes.length} recorte(s)` : ""}</small></div></div>
      ${painelFeito(o)}
      <div class="passo ativo"><span class="bola">2</span><div class="txt"><b>Escrever ou falar</b>
        <small>${esc(o.pergunta || "Qual é a ideia central, nas suas palavras?")}</small>
        <label class="cod" for="nota">Sua nota. Para falar, toque no microfone do teclado.</label>
        <textarea id="nota" placeholder="Duas ou três linhas bastam." data-rascunho="nota:${esc(o.id)}">${esc(rascunho("nota:" + o.id))}</textarea>
        <div class="acoes"><button class="bt" type="button" data-acao="salvar">Salvar</button><button class="bt sec" type="button" data-acao="salvar">Pular a nota</button></div></div></div>
    </div>`;
  } else {
    corpo = `<p class="registro">Registrado: ${esc(o.titulo)} · ${new Date().toLocaleDateString("pt-BR")} · ${fmtMin(Math.max(1, Math.round(E.seg / 60)))}${E.parou ? " · parou no meio" : ""}</p>
      <p class="cod">${E.config.token ? "Vai para o GitHub na sincronização." : "Fica guardado neste aparelho até você configurar a sincronização (Caixa → Ajustes)."}</p>
      ${E.parou && vozSeguinte(o) ? `<div class="acoes"><button class="bt" type="button" data-trecho="${esc(vozSeguinte(o).id)}">▶ Continuar ouvindo no Alex (págs. ${esc(vozSeguinte(o).paginas.replace("-", "–"))})</button></div>` : ""}
      <div class="acoes"><button class="bt${E.parou && vozSeguinte(o) ? " sec" : ""}" type="button" data-acao="voltar">Voltar ao Hoje</button></div>`;
  }
  const voltar = E.fase === 1 ? `<button class="voltar" type="button" data-acao="voltar-hoje">← Voltar</button>` : "";
  return `${voltar}<div><p class="olho">${E.fase === 3 ? "Sessão concluída" : o.tipo === "fundo" ? "Novidades" : f ? "Relevantes" : "Série " + (IT[o.item]?.serie || SERIE().n)}</p><h1 class="titulo-tela">${esc(o.titulo)}</h1>
    <p class="autor" style="font-family:var(--f-texto);color:var(--apagado)">${esc(nomeDoItem(o))}</p></div>${corpo}`;
}
// Registro livre (pedido de 2026-10-19): ao parar ou terminar, marque o que leu de fato (capítulos, partes, trechos),
// ou diga até que página/minuto chegou. A próxima sugestão começa do que falta.
function gruposDoItem(o) {
  const g = [];
  contaveis(o.item).filter(x => !E.feitas.has(x.id)).sort((a, b) => a.ordem - b.ordem).forEach(x => {
    const k = x.cap != null ? "c" + x.cap : x.doc_n != null ? "d" + x.doc_n : x.id, u = g.find(y => y.k === k);
    if (u) u.ps.push(x); else g.push({ k, ps: [x] });
  });
  return g;
}
// peça (ainda não feita) que contém a página N: é onde ele parou
function pecaDaPagina(cod, n) {
  return contaveis(cod).filter(x => x.paginas && !E.feitas.has(x.id)).find(x => { const [a, b] = faixa(x); return a <= n && n <= (b || a); });
}
const ondeParou = a => a ? (a.pag ? `parou na pág. ${a.pag}` : a.pos ? `parou em ${mmss(a.pos)}` : "começou") : "";
function painelFeito(o) {
  if (["resumo", "resumo-audio", "transcricao", "fundo"].includes(o.tipo) || !IT[o.item] && !ehFluxo(o)) return "";
  const bl = new Set(o.bloco || [o.id]), pos = E.posicao;
  const feito = x => E.parou ? o.onde === "app" && pos != null && x.ate != null && x.ate <= pos : bl.has(x.id);
  const caixa = (ps, rotulo) => `<label class="marca"><input type="checkbox" value="${ps.map(x => x.id).join(",")}" data-ate="${Math.max(...ps.map(x => x.paginas ? faixa(x)[1] || faixa(x)[0] : Infinity))}"${ps.every(feito) ? " checked" : ""}> <span>${esc(rotulo)}</span></label>`;
  const linhas = gruposDoItem(o).map(({ ps }) => {
    const todos = ps.every(x => bl.has(x.id)), nenhum = !ps.some(x => bl.has(x.id));
    if (ps.length === 1 || todos || nenhum) return caixa(ps, ps.length === 1 ? ps[0].titulo : ps[0].titulo.replace(/,? \(?(parte \d+ de \d+|\dª metade)\)?$/, "") + ` (${ps.length} partes)`);
    return ps.map(x => caixa([x], x.titulo)).join("");
  }).join("");
  if (!linhas) return "";
  const comMin = o.onde === "app" || o.tipo === "video" || /YouTube/.test(comoE(o)), comPag = contaveis(o.item).some(x => x.paginas && !ehVoz(x));
  return `<div class="passo ativo" id="feito"><span class="bola">✓</span><div class="txt"><b>O que você ${o.modo === "audio" || o.tipo === "video" ? "ouviu ou viu" : "leu"}?</b>
    <small>A sugestão era ${esc(o.titulo)}. Marque o que fez de fato; o resto volta nas próximas sugestões.</small>
    ${comPag ? `<label class="cod" for="ate-pag">Li até a página</label><input id="ate-pag" class="campo-texto" type="number" inputmode="numeric" min="1" style="max-width:110px">` : ""}
    ${comMin ? `<label class="cod" for="ate-min">${E.parou ? "Parei no minuto" : "Se parou no meio, o minuto"}</label><input id="ate-min" class="campo-texto" type="number" inputmode="decimal" min="0" step="0.5" style="max-width:110px" value="${E.parou && pos ? Math.floor(pos / 60) : ""}">` : ""}
    <div class="marcas">${linhas}</div></div></div>`;
}
document.addEventListener("input", e => {   // "li até a página N" marca o que termina até ela
  if (e.target.id !== "ate-pag") return;
  const n = +e.target.value; e.target.closest(".passo, .painel-registro").querySelectorAll("input[type=checkbox]").forEach(c => { if (n) c.checked = +c.dataset.ate <= n; });
});
// Markdown mínimo dos resumos: títulos, listas, negrito e links.
function md(t) {
  const inl = x => esc(x).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[(.+?)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  let h = "", lista = false;
  for (const l of t.split("\n")) {
    const m = l.match(/^(#{1,4})\s+(.*)/), li = l.match(/^\s*[-*]\s+(.*)/);
    if (!li && lista) { h += "</ul>"; lista = false; }
    if (m) h += `<h${Math.min(4, m[1].length + 1)}>${inl(m[2])}</h${Math.min(4, m[1].length + 1)}>`;
    else if (li) { if (!lista) { h += "<ul>"; lista = true; } h += `<li>${inl(li[1])}</li>`; }
    else if (l.trim()) h += `<p>${inl(l)}</p>`;
  }
  return h + (lista ? "</ul>" : "");
}
async function carregarTranscricao(o) {
  E.resumo = null;
  try {
    const r = await fetch(`dados/transcricoes/${o.item}.md`, { cache: "no-cache" }), t = await r.text();
    // linhas "[mm:00] texto": fica só o que está dentro do trecho
    const linhas = t.split("\n").filter(l => { const m = l.match(/^\[(\d+):(\d+)\]/); if (!m) return false; const s = +m[1] * 60 + +m[2]; return s >= o.de - 59 && s < o.ate; });
    E.resumo = `## Transcrição automática\nPode ter erros de nomes e termos.\n\n` + linhas.join("\n\n");
  } catch (_) { E.resumo = "Sem internet e sem cópia guardada desta transcrição."; }
  if (E.fase === 1) telaHoje();
}
async function carregarResumo(o) {
  E.resumo = null;
  try {
    const r = await fetch(`dados/resumos/${o.base}.md`, { cache: "no-cache" });
    const t = await r.text(), k = o.id.split("@")[1];
    const sec = t.split(/\n(?=## )/).find(x => x.startsWith(`## ${k} min`)) || "";
    const cab = t.split(/\n(?=## )/)[0];
    E.resumo = sec ? cab + "\n" + sec : "Resumo não encontrado.";
  } catch (_) { E.resumo = "Sem internet e sem cópia guardada deste resumo."; }
  if (E.fase === 1) telaHoje();
}
function ligarRelogio() {
  clearInterval(relogio);
  relogio = setInterval(() => {
    if (E.fase !== 1 && !E.tocando) return;
    E.seg = Math.round((Date.now() - E.inicio) / 1000);
    const r = document.getElementById("relogio"); if (r) r.textContent = mmss(E.seg);
    const a = document.getElementById("audio");
    if (E.tocando && E.tocando.ate && a.currentTime >= E.tocando.ate - 0.5) seguirTrecho(a);
  }, 1000);
}
// Fim do trecho: o áudio segue sem pausa para o próximo trecho do mesmo episódio (pedido do usuário).
// Mesmo arquivo: a sessão vira "trechos 1 a 2" e a nota do fim vale para todos. Arquivo diferente (voz do Alex):
// o trecho anterior conta como ouvido e o próximo começa logo em seguida.
function proximoTrecho(o) {
  const ts = SESS.filter(x => x.item === o.item && x.tipo === "audio").sort((x, y) => x.ordem - y.ordem);
  return ts[ts.findIndex(x => x.id === (o.bloco || [o.id]).slice(-1)[0]) + 1];
}
function seguirTrecho(a) {
  const o = E.tocando, n = proximoTrecho(o), naTela = E.sessao === o;
  if (!n) { a.pause(); return; }
  let novo;
  if (n.url === o.url) {
    novo = juntar((o.bloco || [o.id]).map(id => SESS.find(y => y.id === id)).concat(n));
    E.tocando = novo; E.andamento[novo.id] = { pos: Math.round(a.currentTime), quando: new Date().toISOString() }; delete E.andamento[o.id];
  } else {
    (o.bloco || [o.id]).forEach(id => E.feitas.add(id)); cobrir(o.item); delete E.andamento[o.id];
    registrar({ evento: "terminou", sessao: o.id, ...(o.bloco ? { bloco: o.bloco } : {}), min: Math.max(1, Math.round(E.seg / 60)), formato: "audio", seguiu: true });
    novo = n; E.andamento[n.id] = { pos: n.de || 0, quando: new Date().toISOString() }; tocar(n, n.de || 0);
  }
  document.getElementById("mp-titulo").textContent = novo.titulo;
  if (naTela) { E.sessao = novo; if (E.fase === 1 && naHoje()) telaHoje(); }
  salvar();
}

// Resumo na hora, sem API paga: o app copia a transcrição com o pedido e abre o Atalho da Apple ou o app do Claude.
const TRANSCR = {};
async function precarregarTranscricao(cod) {
  if (TRANSCR[cod]) return;
  try { const r = await fetch(`dados/transcricoes/${cod}.md`, { cache: "no-cache" }); if (r.ok) TRANSCR[cod] = await r.text(); } catch (_) {}
}
function blocoResumir(o) {
  precarregarTranscricao(o.item);
  return `<div class="resumir"><div class="campo pedir"><label class="cod" for="rz-min">Resumo de</label>
      <input id="rz-min" type="number" inputmode="numeric" min="1" max="60" value="5" style="max-width:70px"><span class="cod">min</span>
      <span class="cod">do episódio inteiro</span><input type="hidden" id="rz-esc" value="episodio"></div>
    <div class="acoes"><button class="bt" type="button" data-acao="resumir-apple" data-cod="${esc(o.item)}">Resumir agora (Apple)</button>
      <button class="bt sec" type="button" data-acao="resumir-claude" data-cod="${esc(o.item)}">Resumir no Claude</button></div>
    <div id="rz-aviso"></div>
    <details class="aviso"><summary><b>Como criar o Atalho "Cérebro Resumo"</b> (uma vez, 3 min)</summary>
      <ol><li>Abra o app <b>Atalhos</b> e toque no <b>+</b> lá em cima.</li>
        <li>Toque no nome no topo e renomeie para exatamente <b>Cérebro Resumo</b>.</li>
        <li><b>Buscar ações</b> → digite <i>área de transferência</i> → <b>Obter Área de Transferência</b>.</li>
        <li><b>Buscar ações</b> → <i>modelo</i> → <b>Usar Modelo</b>. Em modelo, escolha <b>Private Cloud Compute</b>; no pedido, toque e escolha a variável <b>Área de Transferência</b>. Se houver "Continuar conversa", deixe desligado.</li>
        <li><b>Buscar ações</b> → <i>mostrar</i> → <b>Mostrar Resultado</b>.</li>
        <li>Toque em <b>OK</b>. Pronto: volte aqui e use "Resumir agora (Apple)".</li></ol>
      <p>Precisa de Apple Intelligence ligado (Ajustes → Apple Intelligence e Siri).</p></details></div>`;
}
function pedidoDeResumo(cod, min, escopo) {
  const o = E.sessao, t = TRANSCR[cod] || "";
  let linhas = t.split("\n").filter(l => /^\[\d+:\d+\]/.test(l));
  if (escopo === "trecho" && o.ate) linhas = linhas.filter(l => { const m = l.match(/^\[(\d+):(\d+)\]/), s = +m[1] * 60 + +m[2]; return s >= o.de - 59 && s < o.ate; });
  const titulo = nomeDoItem(o), palavras = linhas.join(" ").split(/\s+/).length, teto = Math.max(1, Math.floor(palavras / 400));
  // resumo maior que metade do original não é resumo: limita e explica
  const pedido = min; if (min > teto) min = teto;
  const aviso = pedido > min ? `Você pediu ${pedido} min, mas ${escopo === "trecho" ? "o trecho inteiro" : "o episódio inteiro"} tem ~${Math.round(palavras / 200)} min de leitura; um resumo fica em no máximo metade disso.` : "";
  return { min, aviso, texto: `Resuma em português o texto abaixo, a transcrição automática de "${titulo}"${escopo === "trecho" ? ` (${o.titulo})` : ""}. ` +
    `Tamanho: cerca de ${min * 200} palavras (${min} minutos de leitura). Organize em tópicos curtos, com o minuto de cada ponto entre parênteses, usando as marcas [mm:ss] do texto. ` +
    `Ignore anúncios. Não acrescente nada que não esteja no texto; a transcrição pode ter erros de nomes.\n\n` + linhas.join("\n") };
}
async function resumirFora(destino, cod) {
  const aviso = document.getElementById("rz-aviso");
  if (!TRANSCR[cod]) { aviso.textContent = "Carregando a transcrição... toque de novo em 2 segundos."; precarregarTranscricao(cod); return; }
  aviso.textContent = "";
  const min = Math.max(1, Math.min(60, +document.getElementById("rz-min").value || 5)), escopo = document.getElementById("rz-esc").value;
  const pedido = pedidoDeResumo(cod, min, escopo), texto = pedido.texto;
  try { await navigator.clipboard.writeText(texto); }
  catch (_) { aviso.textContent = "Não consegui copiar. Toque de novo no botão."; return; }

  registrar({ evento: "resumiu-fora", sessao: E.sessao.id, minutos: pedido.min, escopo, destino });
  // primeiro explica o que fazer do outro lado; só depois abre o outro app
  const passos = destino === "apple"
    ? `<ol><li>Toque em <b>Abrir o Atalho</b>.</li><li>O resumo aparece em alguns segundos.</li><li>Para voltar, toque em <b>◀ Cérebro</b> no canto de cima.</li></ol>
       <p>Ainda não criou o Atalho "Cérebro Resumo"? Veja o passo a passo abaixo.</p>`
    : `<ol><li>Toque em <b>Abrir o Claude</b>.</li><li>No Claude, <b>segure o dedo</b> no campo "Converse com o Claude" e toque em <b>Colar</b>.</li><li>Envie. Para voltar, toque em <b>◀ Cérebro</b> no canto de cima.</li></ol>`;
  const link = destino === "apple" ? "shortcuts://run-shortcut?name=" + encodeURIComponent("Cérebro Resumo") : "https://claude.ai/new";
  aviso.innerHTML = `<div class="aviso"><b>Copiado ✓ Pedido de resumo de ${pedido.min} min ${escopo === "trecho" ? "deste trecho" : "do episódio inteiro"}.</b>
    ${pedido.aviso ? `<p>${esc(pedido.aviso)}</p>` : ""}${passos}
    <div class="acoes"><a class="bt" href="${link}" style="text-decoration:none">${destino === "apple" ? "Abrir o Atalho" : "Abrir o Claude"}</a></div></div>`;
}

// Pedido de resumo: o usuário escolhe os minutos; a esteira escreve minutos × 200 palavras.
function formPedido(id, sugestao) {
  return `<form class="campo pedir" data-id="${esc(id)}"><label class="cod" for="min-${esc(id)}">Resumo de</label>
    <input id="min-${esc(id)}" type="number" inputmode="numeric" min="1" max="120" value="${Math.max(1, sugestao || 5)}" style="max-width:70px">
    <span class="cod">min</span><button class="bt sec" type="submit">Pedir</button></form>`;
}

// ---------- Estante ----------
// ---------- Catálogo: tudo o que existe, com busca; e o mapa de metrô ----------
// Visões alternativas (2026-10-23): o Catálogo foi absorvido. Séries ganha "Por tema"; Conteúdos ganha "Biblioteca" (Empresas e assets, Relevantes)
function blocoVisao(dom) {
  const lista = E.visao[dom] === "lista";
  return `<div class="sub" role="group" aria-label="Como ver">
    <button type="button" data-visao="tempo" aria-pressed="${!lista}">Por tempo</button>
    <button type="button" data-visao="lista" aria-pressed="${lista}">${dom === "series" ? "Por tema" : "Biblioteca"}</button></div>`;
}
function blocoBiblioteca(dom) {
  // Biblioteca de Conteúdos (2026-10-23): só Recentes (até 2 meses), Empresas e Assets; Relevantes e Fundo saíram porque repetiam
  E.sub = dom === "series" ? "tema" : "colecoes";
  return `<input id="busca" class="campo-texto" type="search" placeholder="Buscar: Squadra, Marks, Nubank, risco..." value="${esc(E.busca)}" autocomplete="off">
    <div id="estante-corpo" style="display:grid;gap:18px"></div>`;
}
// Recentes: documentos publicados nos últimos 2 meses, das empresas, das gestoras e das cartas que a vigia trouxe
const dataDoc = t => (String(t).match(/\((\d{4}-\d{2}(?:-\d{2})?)\)\s*$/) || [])[1];
function recentes(q) {
  const corte = new Date(Date.now() - 61 * 86400000).toISOString().slice(0, 10), achou = t => !q || q.split(/\s+/).every(w => semAcento(t).includes(w));
  const out = [], urls = new Set();
  FLUXO.filter(f => f.tipo === "carta" && !E.decisoes["arquivar:" + f.cod] && (f.entrou || "") >= corte && achou([f.titulo, f.fonte].join(" "))).forEach(f => {
    if (f.url) urls.add(f.url); urls.add(semAcento(f.titulo));   // o mesmo documento pode estar na coleção com outro link
    out.push({ data: f.entrou, html: linhaItem(f.cod, `entrou em ${fmtData(f.entrou)}`) });
  });
  const docs = {};
  SESS.filter(x => /^(CL|EM)-/.test(x.item)).forEach(x => { const d = dataDoc(x.titulo); if (d && d >= corte) (docs[x.item + "|" + (x.doc ?? x.url ?? x.titulo)] = docs[x.item + "|" + (x.doc ?? x.url ?? x.titulo)] || []).push(x); });
  Object.values(docs).forEach(ps => {
    ps.sort((a, b) => a.ordem - b.ordem);
    const c = ps.filter(x => !ehVoz(x)), m = soma(c), feito = soma(c.filter(x => E.feitas.has(x.id))), prox = c.find(x => !E.feitas.has(x.id)) || c[0];
    const f = FLUXO.find(y => y.cod === ps[0].item), d = dataDoc(ps[0].titulo), nome = ps[0].titulo.replace(/\s*\(\d{4}-\d{2}(-\d{2})?\)\s*$/, "").replace(/,? \(?parte \d+ de \d+\)?/, "");
    if (!prox || (ps[0].url && urls.has(ps[0].url)) || urls.has(semAcento(nome)) || !achou([nome, f && f.fonte, f && f.autor].join(" "))) return;
    out.push({ data: d, html: `<button class="oferta" type="button" data-trecho="${esc(prox.id)}" style="--cor:${cor(prox.item)}">
      <span class="nome"><b>${esc(nome)}</b><span>${esc(f ? f.fonte : prox.item)} · ${fmtData(d)}</span><span>${c.length} ${c.length === 1 ? "parte" : "partes"}${feito && feito < m ? " · continua de onde parou" : ""}</span></span>
      <span class="num"><b>${fmtMin(m)}</b><span>${pct(m ? feito / m : 0)}</span></span></button>` });
  });
  return out.sort((a, b) => String(b.data).localeCompare(String(a.data))).map(x => x.html);
}
// sem acento e sem o "e" que o português põe antes de s + consoante ("esquadra" acha Squadra, "espotify" acha Spotify)
const semAcento = t => String(t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\be(?=s[bcdfgklmnpqtvw])/g, "");
function linhaItem(cod, extra) {
  const f = FLUXO.find(x => x.cod === cod), it = IT[cod];
  const ps = contaveis(cod), m = soma(ps), feito = soma(ps.filter(x => E.feitas.has(x.id)));
  const nome = f ? f.titulo : it.titulo, sub = f ? (f.tipo === "empresa" ? f.autor : f.tipo === "colecao" ? `${f.autor} · ${f.total} documentos` : `${f.fonte} · ${f.tipo}`) : `${it.autor} · ${it.formato} · ${it.leitura}`;
  const info = ps.length ? `${ps.length} ${ps.some(x => x.tipo === "audio") ? "trechos" : "partes"} · ~${Math.round(m / ps.length)} min cada` : "sem sumário ainda";
  return `<button class="oferta${f && f.imagem ? " com-capa" : ""}" type="button" data-item="${esc(cod)}" style="--cor:${cor(cod)}">${f && f.imagem ? `<img class="capa" src="${esc(f.imagem)}" alt="" loading="lazy">` : ""}
    <span class="nome"><b>${esc(nome)}</b><span>${esc(sub)}</span><span>${info}</span>${typeof extra === "string" ? `<span>${extra}</span>` : ""}</span>
    <span class="num"><b>${m ? fmtMin(m) : "–"}</b>${m ? `<span>${pct(feito / m)}</span>` : ""}</span></button>`;
}
// data da fonte como ela vem: dia, mês ou só o ano
const fmtData = d => { const p = String(d || "").slice(0, 10).split("-"); return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : p.length === 2 ? `${p[1]}/${p[0]}` : p[0]; };
// Placar dos programas (2026-10-21): os que você mais promove para Relevantes e mais ouve; atualizado de madrugada
function placar() {
  if (!ESTAT.length) return "";
  return `<details class="grupo"><summary class="cab-serie"><b>Seus programas</b><span class="cod">favoritos ao longo do tempo</span></summary>
    <p class="cod">✓ = terminou · min = tempo ouvido de verdade · ✕ = rejeitou · → R = mandou para Relevantes (antes de 22/10). Atualiza de madrugada.</p>
    <div class="ofertas">${ESTAT.map(x => `<div class="oferta"><span class="nome"><b>${esc(x.programa)}</b></span>
      <span class="num"><b>${x.terminou ? `✓ ${x.terminou}` : x.relevantes ? `→ R ${x.relevantes}` : "–"}</b><i>${x.ouviu_min ? fmtMin(x.ouviu_min) : "0 min"}</i>${x.removeu ? `<span>✕ ${x.removeu}</span>` : ""}</span></div>`).join("")}</div></details>`;
}
// fonte monitorada: o documento mais recente e há quanto tempo saiu; toca para abrir (no app, se já estiver aqui)
function linhaMonitor(m) {
  const dentro = m.cod && FLUXO.some(f => f.cod === m.cod) ? m.cod : (FLUXO.find(f => f.url && f.url === m.url) || {}).cod;
  const dias = /^\d{4}-\d{2}-\d{2}$/.test(m.data) ? diasDesde(m.data) : null;
  const corpo = `<span class="nome"><b>${esc(m.fonte)}</b><span>${esc(m.titulo)}</span></span>
    <span class="num"><b>${fmtData(m.data)}</b>${dias != null ? `<span>${dias === 0 ? "hoje" : dias === 1 ? "ontem" : `há ${dias} dias`}</span>` : ""}</span>`;
  return dentro ? `<button class="oferta" type="button" data-item="${esc(dentro)}" style="--cor:${cor(dentro)}">${corpo}</button>`
    : m.url ? `<a class="oferta" href="${esc(m.url)}" target="_blank" rel="noopener" style="text-decoration:none">${corpo}</a>` : `<div class="oferta">${corpo}</div>`;
}
function listaCatalogo() {
  const q = semAcento(E.busca).trim(), corpo = document.getElementById("estante-corpo");
  const bate = cod => { const f = FLUXO.find(x => x.cod === cod), it = IT[cod];
    const t = semAcento([cod, f && f.titulo, f && f.fonte, it && it.titulo, it && it.autor, it && it.nota, it && MAT[it.mat].nome].join(" "));
    return !q || q.split(/\s+/).every(w => t.includes(w)); };   // todas as palavras, em qualquer ordem
  const grupo = (titulo, sub, itens) => `<div class="grupo"><div class="cab-serie"><b>${titulo}</b><span class="cod">${sub}</span></div><div class="ofertas">${itens}</div></div>`;
  const blocos = [];
  if (E.sub === "fundo") {
    // Fundo: a fila de sempre e, embaixo, de quando é o episódio mais novo de cada fonte
    const ult = {}; FUNDO.filter(x => x.tema !== "acervo").forEach(x => { if (!ult[x.fonte] || x.publicado > ult[x.fonte].publicado) ult[x.fonte] = x; });
    corpo.innerHTML = listaFundo() + placar() + grupo("Fontes do Fundo", "episódio mais novo de cada uma", Object.values(ult).sort((x, y) => y.publicado.localeCompare(x.publicado))
      .map(x => linhaMonitor({ fonte: x.fonte, titulo: x.titulo, data: x.publicado.slice(0, 10) })).join(""));
    return;
  }
  if (E.sub === "fluxo") {
    // Fluxo (pedido de 2026-10-19): o que está no Fluxo, por prazo; e tudo o que é monitorado, com o documento mais recente e a data
    const concluido = f => contaveis(f.cod).length && contaveis(f.cod).every(x => E.feitas.has(x.id));
    const fx = FLUXO.filter(f => !["colecao", "empresa"].includes(f.tipo) && bate(f.cod) && !concluido(f)).sort((x, y) => (x.vence || "9").localeCompare(y.vence || "9"));
    const prontos = FLUXO.filter(f => !["colecao", "empresa"].includes(f.tipo) && bate(f.cod) && concluido(f));
    if (fx.length) blocos.push(grupo("Em Relevantes agora", "por prazo", fx.map(f => {
      const d = f.vence ? Math.ceil((new Date(f.vence + "T23:59") - Date.now()) / 86400000) : null;
      return linhaItem(f.cod, `entrou ${fmtData(f.entrou)}${d == null ? "" : d < 0 ? ` · <b class="vence">venceu em ${fmtData(f.vence)}</b>` : ` · ${d <= 7 ? '<b class="vence">' : ""}vence em ${d} dia${d === 1 ? "" : "s"}${d <= 7 ? "</b>" : ""}`}`);
    }).join("")));
    if (prontos.length) blocos.push(`<details class="grupo"><summary class="cab-serie"><b>Concluídos</b><span class="cod">${prontos.length} · já ouvidos ou lidos</span></summary><div class="ofertas">${prontos.map(f => linhaItem(f.cod)).join("")}</div></details>`);
    const mon = MONITOR.filter(m => !q || q.split(/\s+/).every(w => semAcento(m.fonte + " " + m.titulo).includes(w)));
    [["cartas e memos", "Cartas e memos", "último que temos de cada fonte"], ["podcast", "Podcasts", "os que alimentam o Top 10 da semana"]].forEach(([t, nome, sub]) => {
      const ms = mon.filter(m => m.tipo === t);
      if (ms.length) blocos.push(grupo(`Monitorados: ${nome}`, sub, ms.map(linhaMonitor).join("")));
    });
  } else if (E.sub !== "tema") {
    // Empresas e coleções: o que não segue a grade
    const cl = FLUXO.filter(f => f.tipo === "colecao").map(f => f.cod).filter(bate), em = FLUXO.filter(f => f.tipo === "empresa").map(f => f.cod).filter(bate), rec = recentes(q);
    if (rec.length) blocos.push(grupo("Recentes", "publicados nos últimos 2 meses", rec.join("")));
    if (em.length) blocos.push(grupo("Empresas", "fundador e CEO, em ordem histórica", em.map(c => linhaItem(c)).join("")));
    if (cl.length) blocos.push(grupo("Assets", "cartas de gestoras, papers e podcasts", cl.map(c => linhaItem(c)).join("")));
    if (BIO) {   // Biografias (2026-10-24): os gênios da história por movimento, em ordem cronológica
      const bateBio = c => { const g = BIO.genios[c], mv = BIO.movimentos[g.movimento - 1];
        const t = semAcento([g.nome, ...g.busca, mv.nome, mv.area, ...g.livros.map(l => l.titulo + " " + l.autor)].join(" ")); return !q || q.split(/\s+/).every(w => t.includes(w)); };
      const mvs = BIO.movimentos.map(m => ({ m, gs: m.genios.filter(bateBio) })).filter(x => x.gs.length);
      if (mvs.length) blocos.push(`<div class="grupo"><div class="cab-serie"><b>Biografias</b><span class="cod">${Object.keys(BIO.genios).length} gênios em ${BIO.movimentos.length} movimentos</span></div>
        ${mvs.map(({ m, gs }) => `<details class="grupo"${q ? " open" : ""}><summary class="cab-serie"><b>${esc(m.nome)}</b><span class="cod">${esc(m.periodo)} · ${esc(m.area)}</span></summary>
          <div class="ofertas">${gs.map(linhaBio).join("")}</div>${m.obs ? `<p class="cod">${esc(m.obs)}</p>` : ""}</details>`).join("")}</div>`);
    }
  } else {
    // Por tema: Principles, Understanding e Digging, nesta ordem (a ideia original das listas da Amazon); cada matéria com o avanço
    // dela e os itens separados por série, na ordem da série (camada, depois do mais fácil ao mais difícil); o que falta comprar fica na série de origem
    const posNaSerie = c => { const s = D.series[(IT[c].serie || 1) - 1]; return s ? s.itens.indexOf(c) : 0; };
    [["P", "Principles"], ["U", "Understanding"], ["D", "Digging"]].forEach(([k, nomeCamada]) => {
      const mats = D.materias.filter(m => (m.camada || "U") === k).map(m => m.cod).sort((x, y) => (MAT[y].nucleo ? 1 : 0) - (MAT[x].nucleo ? 1 : 0) || ORDEM.indexOf(x) - ORDEM.indexOf(y));
      const doCamada = [];
      mats.filter(m => D.itens.some(i => i.mat === m && i.serie)).forEach(m => {
        const disp = D.itens.filter(i => i.mat === m && i.serie && !semLivro(i.cod)).map(i => i.cod), mm = minutosDe(disp);
        const series = [...new Set(D.itens.filter(i => i.mat === m && (i.serie || i.serie_original)).map(i => semLivro(i.cod) ? i.serie_original || i.serie : i.serie))].sort((a, b) => a - b);
        const corpoMat = series.map(n => {
          const its = disp.filter(c => IT[c].serie === n && bate(c)).sort((x, y) => posNaSerie(x) - posNaSerie(y));
          const comprar = D.itens.filter(i => i.mat === m && semLivro(i.cod) && (i.serie_original || i.serie) === n && bate(i.cod)).map(i => i.cod);
          if (!its.length && !comprar.length) return "";
          return `<p class="olho" style="margin-top:6px">${esc(serieNome(n))}</p><div class="ofertas">${its.map(c => linhaItem(c)).join("")}${comprar.map(linhaCompra).join("")}</div>`;
        }).join("");
        if (!corpoMat) return;
        doCamada.push(`<details class="grupo"${q ? " open" : ""}><summary class="cab-serie"><b><i class="bolinha" style="background:${cor(m)}"></i>${esc(MAT[m].nome.replace(/^(Principles|Understanding|Digging) - /, ""))}</b><span class="cod">${mm.total ? `${pct(mm.feito / mm.total)} · ${fmtMin(mm.total)}` : "sem sumários ainda"}</span></summary>
          ${mm.total ? `<div class="barra-serie"><i style="width:${pct(mm.feito / mm.total)};background:${cor(m)}"></i></div>` : ""}${corpoMat}</details>`);
      });
      if (doCamada.length) blocos.push(`<h2 class="camada">${nomeCamada}</h2>` + doCamada.join(""));
    });
  }
  if (q) {   // revisão de 2026-10-19: a busca avisa o que achou nas outras abas
    const n = { colecoes: FLUXO.filter(f => ["colecao", "empresa"].includes(f.tipo) && bate(f.cod)).length,
      tema: D.itens.filter(i => (i.serie || i.serie_original) && bate(i.cod)).length,
      fluxo: FLUXO.filter(f => !["colecao", "empresa"].includes(f.tipo) && bate(f.cod)).length + MONITOR.filter(m => q.split(/\s+/).every(w => semAcento(m.fonte + " " + m.titulo).includes(w))).length };
    const nomes = { colecoes: "Empresas e assets", tema: "Por tema", fluxo: "Relevantes" }, outras = Object.keys(n).filter(k => k !== E.sub && n[k] && (E.dom === "series" ? k === "tema" : k === "colecoes"));
    if (outras.length) blocos.push(`<div class="aviso"><b>Também em:</b> ${outras.map(k => `<button class="bt sec" type="button" data-sub="${k}">${nomes[k]} (${n[k]})</button>`).join(" ")}</div>`);
  }
  corpo.innerHTML = blocos.join("") || `<div class="aviso"><b>Nada encontrado para "${esc(E.busca)}".</b><p>Se for algo que você quer ler, mande pela Caixa: de madrugada ele entra aqui.</p></div>`;
}
// livro que você não tem: aparece na série de origem, com o preço da Amazon (data da consulta) e o link
function linhaCompra(c) {
  const p = PRECOS[c];
  return `<${p ? `a href="${esc(p.url)}" target="_blank" rel="noopener"` : `button type="button" data-ficha="${c}"`} class="oferta compra" style="--cor:${cor(c)};text-decoration:none">
    <span class="nome"><b>${esc(IT[c].titulo)}</b><span>${esc(IT[c].autor)} · <b>comprar</b>${p && !p.confere ? ` · Amazon: ${esc(p.titulo_amazon.slice(0, 60))} (a verificar)` : ""}</span></span>
    <span class="num">${p ? `<b>R$ ${p.valor.toFixed(2).replace(".", ",")}</b><i>Amazon, ${esc(p.data.slice(8, 10) + "/" + p.data.slice(5, 7))}</i>` : "<i>sem preço</i>"}</span></${p ? "a" : "button"}>`;
}
document.addEventListener("input", e => { if (e.target.id === "busca") { E.busca = e.target.value; listaCatalogo(); } });
document.addEventListener("change", e => {
  if (e.target.dataset.rzItem) { E.rzItem = { cod: e.target.dataset.rzItem, min: Math.max(1, Math.min(+e.target.max, +e.target.value || 1)) }; telaHoje(); }
});

// ---------- Feed: você grava uma fala sobre o que viu ou ouviu; a esteira transcreve, acha o vídeo e escreve o log ----------
// O áudio fica no aparelho (IndexedDB) até subir para cerebro/registro/falas/ no GitHub.
const idb = () => new Promise((ok, erro) => {
  const r = indexedDB.open("cerebro", 1);
  r.onupgradeneeded = () => r.result.createObjectStore("falas");
  r.onsuccess = () => ok(r.result); r.onerror = () => erro(r.error);
});
async function guardado(modo, faz) {
  const db = await idb();
  return new Promise((ok, erro) => { const t = db.transaction("falas", modo), r = faz(t.objectStore("falas")); t.oncomplete = () => ok(r.result); t.onerror = () => erro(t.error); });
}
const paraB64 = blob => new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result.split(",")[1]); f.readAsDataURL(blob); });
let gravacao = null, enviando = false;
const redesenhar = () => E.aba === "feed" ? telaFeed() : E.aba === "novidades" ? telaNovidades() : telaHoje();
async function gravar(item) {
  try {
    const fluxo = await navigator.mediaDevices.getUserMedia({ audio: true });
    const rec = new MediaRecorder(fluxo), partes = [];
    rec.ondataavailable = e => e.data.size && partes.push(e.data);
    rec.onstop = async () => {
      fluxo.getTracks().forEach(t => t.stop());
      const tipo = rec.mimeType || "audio/mp4", blob = new Blob(partes, { type: tipo });
      const ext = tipo.includes("webm") ? "webm" : tipo.includes("ogg") ? "ogg" : "m4a";
      const agora = new Date(), id = agora.toISOString().slice(0, 19).replace(/[-:]/g, "").replace("T", "-");
      const seg = Math.round((Date.now() - gravacao.inicio) / 1000);
      clearInterval(gravacao.relogio); gravacao = null;
      if (seg < 2) { redesenhar(); return; }
      await guardado("readwrite", st => st.put(blob, id));
      E.falas.unshift({ id, ext, seg, quando: agora.toISOString(), enviada: false, ...(item ? { item } : {}) }); salvar();
      redesenhar(); enviarFalas();
    };
    rec.start();
    gravacao = { rec, item, inicio: Date.now(), relogio: setInterval(() => { const el = document.getElementById("rec-tempo"); if (el) el.textContent = mmss((Date.now() - gravacao.inicio) / 1000); }, 500) };
  } catch (err) { E.erroFala = `Não consegui usar o microfone (${err.name || err.message}). Confira a permissão do microfone para o app.`; }
  redesenhar();
}
async function enviarFalas() {
  const { token, repo, ramo } = E.config;
  if (!token || enviando || !navigator.onLine) return;
  enviando = true;
  for (const f of E.falas.filter(x => !x.enviada)) {
    try {
      const blob = await guardado("readonly", st => st.get(f.id));
      if (!blob) { f.enviada = true; continue; }
      const caminho = `cerebro/registro/falas/${f.id}.${f.ext}`;
      const w = await fetch(`https://api.github.com/repos/${repo}/contents/${caminho}`, { method: "PUT",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" },
        body: JSON.stringify({ message: `Cérebro: fala de ${mmss(f.seg)}`, branch: ramo, content: await paraB64(blob) }) });
      if (!w.ok && w.status !== 422) throw new Error(`HTTP ${w.status}`);   // 422: o arquivo já subiu antes
      f.enviada = true; delete f.erro;
      await guardado("readwrite", st => st.delete(f.id));
      registrar({ evento: "falou", fala: f.id, arquivo: caminho, seg: f.seg, ...(f.item ? { item: f.item } : {}) });
    } catch (err) { f.erro = err.message; }
  }
  enviando = false; salvar();
  if (E.aba === "feed") telaFeed();
}
// junta as notas do mesmo conteúdo (mesmo link) num cartão; o grupo mais recente vem primeiro
// conteúdo de uma nota feita num episódio (Novidades ou Conteúdos): título, programa e link do episódio
function conteudoDe(cod) { const x = FUNDO.find(y => y.cod === cod) || FLUXO.find(y => y.cod === cod); return x ? { titulo: x.titulo, canal: x.fonte, url: x.url, conferido: true } : null; }
function grupos(pendentes) {
  // falas e notas escritas (FEED, e as ainda não processadas que já sabem o episódio) + notas de fechamento das sessões (E.notas), juntas por conteúdo
  const m = new Map(), quandoDe = id => (E.hist.filter(h => h.sessao === id || h.sessao === id + "#txt").pop() || {}).quando || "";
  const grupo = (k, base) => { if (!m.has(k)) m.set(k, { ...base, itens: [], notas: [] }); return m.get(k); };
  for (const x of FEED) { const v = x.video || (x.item && conteudoDe(x.item)); grupo(v?.url || x.id, { video: v }).itens.push(x); }
  for (const f of pendentes || []) { const v = f.item && conteudoDe(f.item); if (v) grupo(v.url || "item:" + f.item, { video: v }).itens.push({ id: f.id, quando: f.quando, fala: f.texto || "", voz: !f.texto, seg: f.seg, aguardando: true }); }
  for (const [id, nota] of Object.entries(E.notas)) {
    const sx = SESS.find(y => y.id === id.replace("#txt", "")); if (!sx || !nota) continue;
    const f = fluxoDe(sx), it = IT[sx.item], g = grupo(f?.url || "item:" + sx.item, { video: { titulo: f ? f.fonte || f.titulo : it?.titulo || sx.item, url: f?.url, conferido: true } });
    g.cod = sx.item; if (!g.notas.some(n => n.nota === nota)) g.notas.push({ titulo: sx.titulo, nota, quando: quandoDe(sx.id) });
  }
  const ult = g => [...g.itens.map(x => x.quando), ...g.notas.map(x => x.quando)].sort().pop() || "";
  return [...m.values()].sort((a, b) => ult(b).localeCompare(ult(a)));
}
// ---------- Semana (pedido de 2026-10-24): o plano por horário, o placar e o balanço de domingo ----------
// A semana vai de domingo a sábado. Séries só no fim de semana; manhã, almoço e noite com os conteúdos que você aprovou;
// carro para ouvir. O placar soma o que o registro mostra (dos dois aparelhos, se os dois tiverem token).
const tipoDe = id => { const item = String(id || "").split(/[.#@+]/)[0]; return IT[item] && IT[item].serie ? "serie" : /^(FX-)?FD-/.test(item) ? "ouvir" : "conteudo"; };
function contarAtividade(ev) {
  if (!ev || !ev.quando) return;
  const alvo = ev.sessao || ev.item; if (!alvo) return;
  let t = tipoDe(alvo), min = 0;
  if (ev.evento === "ouviu") { min = (ev.seg || 0) / 60; if (t !== "serie") t = "ouvir"; }
  else if (ev.evento === "terminou" && !["audio", "fundo"].includes(ev.formato)) {
    const ids = ev.bloco || [ev.sessao]; min = Math.min(ev.min || ids.reduce((s, i) => s + ((SESS.find(x => x.id === i) || {}).minutos || 0), 0), 180);
  } else return;
  if (min > 0) E.atividade[ev.quando + ev.evento] = { quando: ev.quando, t, min: Math.round(min * 10) / 10 };
}
const DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"], NOME_DIA = { dom: "Domingo", seg: "Segunda", ter: "Terça", qua: "Quarta", qui: "Quinta", sex: "Sexta", sab: "Sábado" };
const NOME_SLOT = { manha: "Manhã", carro: "Carro", almoco: "Pós-almoço", noite: "Noite", tarde: "Tarde" };
const diaLocal = q => { const d = new Date(q); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
function feitoNaSemana() {
  const out = { serie: 0, conteudo: 0, ouvir: 0, dias: {} };
  for (const a of Object.values(E.atividade || {})) {
    const d = diaLocal(a.quando); if (d < SEMANA.inicio || d > SEMANA.fim) continue;
    out[a.t] += a.min; out.dias[d] = (out.dias[d] || 0) + a.min;
  }
  return out;
}
// próximo trecho de cada trilha da semana
function proximaDaSerie() { const s = D.series[(SEMANA.serie || 1) - 1]; for (const c of s ? s.itens : []) { const p = proximaDoItem(c); if (p) return p; } return null; }
const escolha = c => E.decisoes["semana:" + SEMANA.inicio + ":" + c.id];
// o n-ésimo trecho ainda não lido dos conteúdos da semana (manhã, almoço e noite pegam trechos seguidos)
function proximaDosConteudos(n = 0) {
  for (const c of SEMANA.conteudos.filter(c => escolha(c) !== "trocar")) for (const id of c.pecas) if (!E.feitas.has(id) && n-- === 0) return { c, p: SESS.find(x => x.id === id) };
  return null;
}
function proximoOuvir() {
  const f = filaFundo(); return f.find(x => E.posicoes[x.cod]) || f.find(depois) || f[0];
}
function linhaSlot([slot, tipo, min], k) {
  let corpo = "", acao = "";
  if (tipo === "serie") { const p = proximaDaSerie(); corpo = p ? `${esc(IT[p.item].titulo)} · ${esc(p.titulo)}` : "Série terminada: o domingo traz a próxima."; if (p) acao = `<button class="bt" type="button" data-trecho="${esc(p.id)}">Continuar</button>`; }
  else if (tipo === "conteudo") { const x = proximaDosConteudos(k); corpo = x ? `${esc(x.c.titulo)} · ${esc(x.p ? x.p.titulo : "")}` : "Conteúdo da semana terminado. Bônus: escolha na Biblioteca."; if (x && x.p) acao = `<button class="bt" type="button" data-trecho="${esc(x.p.id)}">Continuar</button>`; }
  else { const x = proximoOuvir(); corpo = x ? `${esc(x.fonte)} · ${esc(x.titulo)}` : "Nada na fila: veja as Novidades."; if (x) acao = `<button class="bt" type="button" data-ouvir-em="${esc(x.cod)}" data-seg="${Math.floor(E.posicoes[x.cod] || 0)}">${E.posicoes[x.cod] ? "Continuar" : "Ouvir"}</button>`; }
  return `<div class="item"><div class="meta"><span class="chip ${tipo === "serie" ? "aceso" : ""}">${NOME_SLOT[slot] || slot}</span><span>${min} min · ${tipo === "serie" ? "série" : tipo === "ouvir" ? "ouvir" : "conteúdo"}</span></div>
    <h3 style="font-size:16px">${corpo}</h3>${acao ? `<div class="acoes">${acao}</div>` : ""}</div>`;
}
function barra(nome, feito, meta) {
  const p = meta ? Math.min(1, feito / meta) : 0;
  return `<div class="placar-linha"><div class="cab-serie"><b>${nome}</b><span class="cod">${fmtMin(Math.round(feito))}${meta ? ` de ${fmtMin(meta)}` : " · bônus"}</span></div>${meta ? `<div class="barra-serie"><i style="width:${pct(p)}"></i></div>` : ""}</div>`;
}
function telaSemana() {
  const el = document.getElementById("tela-semana");
  if (!SEMANA) { el.innerHTML = `<div><h1 class="titulo-tela">Semana</h1></div><p class="cod">O plano da semana aparece no domingo.</p>`; return; }
  const f = feitoNaSemana(), hoje = diaLocal(new Date().toISOString()), dHoje = DIAS[new Date().getDay()], fora = hoje < SEMANA.inicio || hoje > SEMANA.fim;
  const fmtD = d => `${d.slice(8, 10)}/${d.slice(5, 7)}`;
  const dias = DIAS.map((k, i) => { const d = new Date(Date.parse(SEMANA.inicio + "T12:00") + i * 86400000).toISOString().slice(0, 10), pl = (SEMANA.horarios[k] || []).filter(x => x[1] !== "ouvir").reduce((s, x) => s + x[2], 0), fe = f.dias[d] || 0;
    return `<div class="dia${d === hoje ? " hoje" : ""}"><b>${NOME_DIA[k].slice(0, 3)}</b><span>${Math.round(fe)}′</span><i>${pl ? `de ${pl}′` : "livre"}</i></div>`; }).join("");
  const sr = D.series[(SEMANA.serie || 1) - 1], ps = sr ? sr.itens.flatMap(c => contaveis(c)) : [], feitoS = soma(ps.filter(x => E.feitas.has(x.id))), totS = soma(ps);
  el.innerHTML = `${avisoToken()}
    <div><p class="olho">Semana de ${fmtD(SEMANA.inicio)} a ${fmtD(SEMANA.fim)}</p><h1 class="titulo-tela">${fora ? "Plano da semana" : `${NOME_DIA[dHoje]}: o que é hoje`}</h1></div>
    ${fora ? `<p class="cod">Esta semana começa em ${fmtD(SEMANA.inicio)}.</p>` : `<div class="lista">${(() => { let k = 0; return (SEMANA.horarios[dHoje] || []).map(h => linhaSlot(h, h[1] === "conteudo" ? k++ : 0)).join(""); })() || `<p class="cod">Hoje está livre no plano.</p>`}</div>`}
    <section class="caixinha"><div class="cab-serie"><h3>Placar</h3><span class="cod">meta ${fmtMin(SEMANA.meta.serie + SEMANA.meta.conteudo)} de leitura</span></div>
      ${barra("Série (fim de semana)", f.serie, SEMANA.meta.serie)}${barra("Conteúdo da vez", f.conteudo, SEMANA.meta.conteudo)}${barra("Ouvir (carro)", f.ouvir, 0)}
      <div class="dias-semana">${dias}</div></section>
    <section class="caixinha"><div class="cab-serie"><h3>Série do fim de semana</h3><span class="cod">${SEMANA.serie_inicio > hoje ? `começa em ${fmtD(SEMANA.serie_inicio)}` : totS ? `${pct(feitoS / totS)} · ${fmtMin(totS - feitoS)} faltam` : ""}</span></div>
      <p><b>${esc(serieNome(SEMANA.serie || 1))}</b></p>${sr && sr.resumo ? `<p class="cod">${esc(sr.resumo)}</p>` : ""}</section>
    <section class="caixinha"><div class="cab-serie"><h3>${SEMANA.conteudos.length > 1 ? "Conteúdos da semana" : "Conteúdo da vez"}</h3><span class="cod">você aprova ou troca</span></div>
      ${SEMANA.conteudos.map(c => { const e = escolha(c), tot = soma(c.pecas.map(i => SESS.find(x => x.id === i)).filter(Boolean)), fe = soma(c.pecas.filter(i => E.feitas.has(i)).map(i => SESS.find(x => x.id === i)).filter(Boolean));
        return `<div class="item"><div class="meta">${e === "ok" ? '<span class="chip aceso">aprovado</span>' : e === "trocar" ? '<span class="chip">trocar: diga no chat o que prefere</span>' : '<span class="chip">proposta</span>'}<span>${fmtMin(tot)}${fe ? ` · ${pct(fe / tot)} feito` : ""}</span></div>
          <h3>${esc(c.titulo)}</h3><p class="cod">${esc(c.motivo)}</p>
          <div class="acoes"><button class="bt${e === "ok" ? "" : " sec"}" type="button" data-semana="${esc(c.id)}" data-escolha="ok">${e === "ok" ? "✓ Aprovado" : "Aprovar"}</button><button class="bt sec" type="button" data-semana="${esc(c.id)}" data-escolha="trocar">Trocar</button></div></div>`; }).join("")}</section>
    ${SEMANA.balanco ? `<details class="caixinha" open><summary class="cab-serie"><h3>Balanço · ${esc(SEMANA.balanco.semana)}</h3></summary><p>${esc(SEMANA.balanco.texto)}</p></details>` : ""}
    <p class="cod">Check-in das 21h30: um lembrete no app Lembretes do iPhone (o passo a passo está no chat). No domingo sai o balanço e a proposta da semana nova.</p>`;
}

// Revisão espaçada (revisão de 2026-10-24): o que você anotou volta depois de 7, 30, 90 e 180 dias. "Lembrava" adia para o
// próximo intervalo; "Tinha esquecido" volta para 7 dias. Vale nos dois aparelhos pelo evento "revisou".
const INTERVALOS = [7, 30, 90, 180];
const chaveGrupo = g => g.video?.url || g.cod || (g.itens[0] && g.itens[0].id) || "";
function proximaRevisao(g) {
  const r = E.revisoes[chaveGrupo(g)];
  if (r) return r.proxima;
  const primeira = [...g.itens.map(x => x.quando), ...g.notas.map(x => x.quando)].filter(Boolean).sort()[0];
  return primeira ? new Date(Date.parse(primeira) + INTERVALOS[0] * 86400000).toISOString().slice(0, 10) : "9999";
}
function blocoRelembrar(gs) {
  const hoje = new Date().toISOString().slice(0, 10);
  const devidos = gs.filter(g => notasDoGrupo(g).length && proximaRevisao(g) <= hoje).slice(0, 3);
  if (!devidos.length) return "";
  return `<section class="caixinha"><div class="cab-serie"><h3>Para relembrar</h3><span class="cod">${devidos.length} de hoje</span></div>
    <p class="cod">O que você anotou volta depois de 7, 30, 90 e 180 dias. Leia, lembre e marque.</p>
    ${devidos.map(g => { const k = chaveGrupo(g), c = CONTEUDOS[g.video?.url] || {}, n = (E.revisoes[k] || {}).nivel || 0;
      const primeira = notasDoGrupo(g).map(x => x.quando).filter(Boolean).sort()[0];
      return `<div class="item"><div class="meta">${primeira ? `<span>anotado em ${dataFeed(primeira)}</span>` : ""}<span class="chip">${n ? `${n + 1}ª revisão` : "1ª revisão"}</span></div>
        ${tituloFeed(g.video)}${c.notas ? topicos(c.notas) : notasDoGrupo(g).map(x => x.html).join("")}
        <div class="acoes"><button class="bt" type="button" data-revisou="${esc(k)}" data-lembrou="1">Lembrava</button><button class="bt sec" type="button" data-revisou="${esc(k)}" data-lembrou="0">Tinha esquecido</button></div></div>`; }).join("")}</section>`;
}
function telaFeed() {
  if (document.activeElement && document.activeElement.id === "nota-feed") return;   // não apaga a tela enquanto você escreve
  const prontos = new Set(FEED.map(x => x.id));
  const naoProcessadas = E.falas.filter(f => !prontos.has(f.id));
  const pendentes = naoProcessadas.filter(f => !(f.item && conteudoDe(f.item))), gs = grupos(naoProcessadas);   // nota feita num episódio já entra no cartão dele
  document.getElementById("tela-feed").innerHTML = `
    <div><p class="olho">Suas notas e resumos, por conteúdo</p><h1 class="titulo-tela">Notes</h1></div>
    ${blocoRelembrar(gs)}
    <div class="aviso gravar">
      ${gravacao ? `<button class="bt rec" type="button" data-acao="parar-fala">■ Parar · <span id="rec-tempo">${mmss((Date.now() - gravacao.inicio) / 1000)}</span></button>
        <p class="cod">Gravando. Fale o que viu, onde parou e o que achou.</p>`
      : `<button class="bt" type="button" data-acao="gravar-fala">🎙 Gravar uma fala</button>
        <p class="cod">Ex.: "J-Curve com o Stélio Tolda, parei no minuto 35. O ponto dele é…"</p>`}
      ${E.erroFala ? `<p class="erro">${esc(E.erroFala)}</p>` : ""}
      <form class="campo" id="form-nota"><textarea id="nota-feed" rows="3" placeholder="Ou escreva aqui (no Uber, sem poder falar)" class="campo-texto" data-rascunho="feed">${esc(rascunho("feed"))}</textarea><button class="bt" type="submit">Mandar</button></form>
      ${!E.config.token ? `<p class="cod">Sem token, a fala fica guardada no aparelho. Cole o token na Caixa → Ajustes.</p>` : ""}
    </div>
    <div class="sub" role="group" aria-label="Visão do Notes">${[["recentes", "Recentes"], ["assunto", "Por assunto"]].map(([k, n]) => `<button type="button" data-feedvis="${k}" aria-pressed="${(E.feedVis || "recentes") === k}">${n}</button>`).join("")}</div>
    <div class="lista">
      ${(E.feedVis || "recentes") === "recentes" ? feedRecentes(gs, pendentes) : feedAssunto(gs, pendentes)}
      ${!pendentes.length && !gs.length ? `<p class="cod">Nada ainda. A primeira fala aparece aqui.</p>` : ""}
    </div>`;
}
// Feed em duas visões (pedido de 2026-10-24): Recentes, nota a nota da mais nova para a mais velha, todas abertas;
// Por assunto, um cartão consolidado por conteúdo, separado por natureza (Séries, Conteúdos, Novidades).
// Fala em voz aparece só pelo resumo que a esteira escreve (resumo_fala); a transcrição inteira fica só no repositório.
const NATUREZA = { series: "Séries", conteudos: "Conteúdos", novidades: "Novidades" };
function naturezaDe(cod, url) {
  if (cod) return /^(FX-)?FD-/.test(cod) ? "novidades" : /^(FX|CL|EM)-/.test(cod) ? "conteudos" : "series";
  if (url && FUNDO.some(y => y.url === url)) return "novidades";
  const f = url && FLUXO.find(y => y.url === url);
  return f && /^FX-FD-/.test(f.cod) ? "novidades" : "conteudos";
}
const naturezaGrupo = g => naturezaDe(g.cod || g.itens.find(x => x.item)?.item, g.video?.url);
const dataFeed = q => new Date(q).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
const parasFeed = t => `<p>${esc(t).replace(/\n\n+/g, "</p><p>").replace(/\n/g, "<br>")}</p>`;
// tópicos ("- ...") viram lista; o resto, parágrafos
function topicos(t) {
  const ls = t.split("\n").map(l => l.trim()).filter(Boolean);
  if (!ls.some(l => l.startsWith("- "))) return parasFeed(t);
  let html = "", lista = [];
  const fecha = () => { if (lista.length) html += `<ul>${lista.map(l => `<li>${esc(l)}</li>`).join("")}</ul>`; lista = []; };
  for (const l of ls) { if (l.startsWith("- ")) lista.push(l.slice(2)); else { fecha(); html += `<p>${esc(l)}</p>`; } }
  fecha(); return html;
}
// o que mostrar de uma nota: resumo da fala, texto escrito (ou fala curta) inteiro, ou aviso de que o resumo vem de madrugada
function textoNota(x) {
  if (x.resumo_fala) return topicos(x.resumo_fala);
  const curta = x.fala && (x.escrita || x.fala.split(/\s+/).length <= 60);
  if (x.fala && (curta || !x.segundos)) return parasFeed(x.fala);
  if (x.voz || x.fala) return `<p class="cod">🎙 nota em voz de ${mmss(x.seg || x.segundos || 0)} · o resumo chega de madrugada</p>`;
  return "";
}
function notasDoGrupo(g) {
  return [...g.itens.map(x => ({ quando: x.quando || "", html: textoNota(x), espera: x.aguardando, resposta: x.resposta })),
    ...g.notas.map(n => ({ quando: n.quando || "", html: `<p><b class="cod">${esc(n.titulo)}</b></p>${parasFeed(n.nota)}` }))].filter(x => x.html);
}
function tituloFeed(v) {
  if (!v) return "";
  return `<h3>${v.url && /^https?:/.test(v.url) ? `<a href="${esc(v.url)}" target="_blank" rel="noopener">${esc(v.titulo)}</a>` : esc(v.titulo)}</h3>${v.canal ? `<div class="meta">${esc(v.canal)}</div>` : ""}`;
}
function cartaoPendente(f) {
  return `<div class="item"><div class="meta"><span class="origem">você</span><span>${dataFeed(f.quando)}</span><span>${f.texto ? "escrita" : mmss(f.seg)}</span>
    <span class="chip">${f.enviada ? "enviada" : f.erro ? "não subiu" : "no aparelho"}</span></div>
    ${f.texto ? parasFeed(f.texto) : ""}
    <div class="meta">${f.texto ? "De madrugada o Cérebro acha a fonte." : f.enviada ? "De madrugada o Cérebro transcreve, acha o conteúdo e resume." : f.erro ? `Erro: ${esc(f.erro)}. Tenta de novo sozinho quando houver internet.` : "Sobe quando houver internet e token."}</div></div>`;
}
function feedRecentes(gs, pendentes) {
  const notas = gs.flatMap(g => notasDoGrupo(g).map(n => ({ ...n, g })));
  const todas = [...notas, ...pendentes.map(f => ({ quando: f.quando || "", pendente: f }))].sort((a, b) => b.quando.localeCompare(a.quando));
  return todas.map(n => n.pendente ? cartaoPendente(n.pendente) : `<div class="item"><div class="meta"><span class="origem">você</span>${n.quando ? `<span>${dataFeed(n.quando)}</span>` : ""}<span class="chip">${NATUREZA[naturezaGrupo(n.g)]}</span>${n.espera ? "<span>processa de madrugada</span>" : ""}</div>
    ${tituloFeed(n.g.video)}${n.html}${n.resposta ? `<div class="meta"><b>Claude:</b> ${esc(n.resposta)}</div>` : ""}</div>`).join("");
}
function feedAssunto(gs, pendentes) {
  const cartao = g => {
    const v = g.video, c = CONTEUDOS[v?.url] || {}, r = c.resumo || g.itens.find(x => x.resumo)?.resumo, sem = g.itens.find(x => x.sem_resumo)?.sem_resumo;
    const linha = notasDoGrupo(g).sort((a, b) => a.quando.localeCompare(b.quando)), ultima = linha.map(x => x.quando).filter(Boolean).pop();
    return `<div class="item"><div class="meta">${ultima ? `<span>${dataFeed(ultima)}</span>` : ""}<span>${linha.length} nota${linha.length > 1 ? "s" : ""}</span>
      ${g.itens.find(x => x.parou) ? `<span>parou em ${esc(g.itens.find(x => x.parou).parou)}</span>` : ""}${v && !v.conferido ? '<span class="chip">a verificar</span>' : ""}</div>
      ${tituloFeed(v)}
      ${c.notas ? topicos(c.notas) : linha.map(x => `<div class="fala"><p class="cod">${x.quando ? dataFeed(x.quando) : ""}</p>${x.html}</div>`).join("")}
      ${g.itens.filter(x => x.resposta).map(x => `<div class="meta"><b>Claude:</b> ${esc(x.resposta)}</div>`).join("")}
      ${g.cod ? `<div class="acoes"><button class="bt sec" type="button" ${ehFluxo({ item: g.cod }) ? `data-episodio="${esc(g.cod)}"` : `data-ficha="${esc(g.cod)}"`}>Abrir</button></div>` : ""}
      ${r ? `<details><summary>Resumo do conteúdo inteiro · ${r.min} min</summary>${parasFeed(r.texto)}${r.fonte ? `<p class="cod">Fonte: ${esc(r.fonte)}</p>` : ""}</details>`
        : sem ? `<div class="meta">Sem resumo: ${esc(sem)}</div>` : ""}</div>`;
  };
  // caixas (pedido de 2026-10-24): Assets → gestora, Empresas → empresa, Podcasts → programa, Séries → livro
  const caixas = {};
  for (const g of gs) { const { caixa, fonte } = lugarDe(g); ((caixas[caixa] = caixas[caixa] || {})[fonte] = caixas[caixa][fonte] || []).push(g); }
  const ult = g => notasDoGrupo(g).map(x => x.quando).sort().pop() || "";
  return [...CAIXAS_NOTES.filter(k => caixas[k]).map(k => {
      const fontes = Object.entries(caixas[k]).sort((a, b) => Math.max(...b[1].map(g => ult(g)).map(Date.parse).filter(Boolean), 0) - Math.max(...a[1].map(g => ult(g)).map(Date.parse).filter(Boolean), 0));
      const n = fontes.reduce((t, [, gg]) => t + gg.reduce((u, g) => u + notasDoGrupo(g).length, 0), 0);
      return `<section class="caixinha"><div class="cab-serie"><h3>${k}</h3><span class="cod">${n} nota${n > 1 ? "s" : ""}</span></div>
        ${fontes.map(([f, gg]) => `<p class="olho">${esc(f)}</p>${gg.map(cartao).join("")}`).join("")}</section>`;
    }),
    pendentes.length ? `<section class="caixinha"><div class="cab-serie"><h3>Sem conteúdo ainda</h3></div><p class="cod">De madrugada o Cérebro acha a fonte.</p>${pendentes.map(cartaoPendente).join("")}</section>` : ""].join("");
}
const CAIXAS_NOTES = ["Assets", "Empresas", "Podcasts", "Séries", "Outros"];
// onde a nota mora: empresa citada no título > gestora (coleção de cartas) > programa do podcast > livro da grade
const APELIDO_EMPRESA = { "Mercado Livre": ["mercado livre", "mercado libre", "mercadolibre", "meli"], "Alphabet (Google)": ["alphabet", "google"], "Nubank": ["nubank"], "Berkshire Hathaway": ["berkshire"], "JPMorgan Chase": ["jpmorgan", "jp morgan"] };
function lugarDe(g) {
  const v = g.video || {}, url = v.url, cod = g.cod || g.itens.find(x => x.item)?.item, t = " " + semAcento(v.titulo || "") + " ";
  const emp = FLUXO.filter(f => f.tipo === "empresa").find(f => (APELIDO_EMPRESA[f.titulo] || [semAcento(f.titulo)]).some(a => t.includes(" " + a)));
  if (emp || /^EM-/.test(cod || "")) return { caixa: "Empresas", fonte: emp ? emp.titulo : (FLUXO.find(f => f.cod === cod) || {}).titulo || cod };
  const podcasts = new Set((INSCRICOES?.podcasts || []).map(p => semAcento(p.nome)));
  const col = FLUXO.filter(f => f.tipo === "colecao").find(c => (url && SESS.some(x => x.item === c.cod && x.url === url)) || cod === c.cod);
  if (col && !podcasts.has(semAcento(col.titulo)) && !/podcast/i.test(col.titulo)) return { caixa: "Assets", fonte: col.titulo.replace(/ Investimentos$/, "") };
  if (cod && !/^(FX|CL|EM|FD)-/.test(cod) && IT[cod]) return { caixa: "Séries", fonte: IT[cod].titulo };
  const x = cod && (FUNDO.find(y => y.cod === cod) || FLUXO.find(y => y.cod === cod));
  const prog = (x && x.fonte) || v.canal || (col && col.titulo);
  if (prog && (x || col || /podcast|episode|\.mp3/i.test(url || ""))) return { caixa: "Podcasts", fonte: prog };
  return { caixa: "Outros", fonte: v.canal || "Sem fonte" };
}

// ---------- Registrar conteúdo (topo da Caixa): PDF, vídeo do YouTube, podcast ou print ----------
// Link vai direto para o registro; arquivo (PDF ou print) fica no aparelho até subir para cerebro/registro/entrada/.
// A esteira da madrugada processa tudo (decisão do usuário em 2026-10-18).
const REG = {
  youtube: { nome: "YouTube", como: "No YouTube: Compartilhar → Copiar link, e cole aqui. De madrugada eu pego título e canal e procuro a versão em podcast; se existir, o áudio toca aqui e eu transcrevo.", link: "Link do vídeo" },
  podcast: { nome: "Podcast", como: "No Spotify ou no Apple Podcasts: Compartilhar → Copiar link, e cole aqui. Eu acho o episódio no feed, ele toca aqui em trechos e eu transcrevo.", link: "Link do episódio" },
  pdf: { nome: "PDF", como: "Se o PDF é público, cole o link. Se não, escolha o arquivo (no Arquivos ou no GoodNotes: Compartilhar → Salvar em Arquivos). Eu extraio o texto e corto em partes de ~15 min.", link: "Link do PDF (se for público)", arquivo: "application/pdf" },
  print: { nome: "Print", como: "Para listas: playlist, pasta de PDFs, estante. Escolha os prints; eu leio os itens e proponho cada um aqui na Caixa.", arquivo: "image/*" }
};
function blocoRegistrar() {
  const t = REG[E.regTipo], recentes = E.envios.slice(0, 5);
  return `<details class="aviso registrar"${E.regAberto ? " open" : ""}><summary><b>Registrar conteúdo</b> · YouTube, podcast, PDF ou print</summary>
    <div class="sub" role="group" aria-label="Tipo">${Object.entries(REG).map(([k, r]) => `<button type="button" data-reg="${k}" aria-pressed="${E.regTipo === k}">${r.nome}</button>`).join("")}</div>
    <p>${esc(t.como)}</p>
    <form id="form-reg" class="campo" style="flex-direction:column;align-items:stretch">
      ${t.link ? `<input id="reg-link" type="url" inputmode="url" placeholder="${esc(t.link)}" autocomplete="off">` : ""}
      ${t.arquivo ? `<input id="reg-arq" type="file" accept="${t.arquivo}" ${E.regTipo === "print" ? "multiple" : ""}>` : ""}
      <input id="reg-nota" placeholder="Nota (opcional): por que, onde parou, de que empresa" autocomplete="off">
      <button class="bt" type="submit">Registrar</button></form>
    ${E.erroReg ? `<p class="erro">${esc(E.erroReg)}</p>` : ""}
    ${recentes.length ? `<div class="meta">${recentes.map(x => `<span class="chip">${esc(REG[x.tipo].nome)} · ${x.enviada ? "enviado" : x.erro ? "não subiu" : "no aparelho"}</span>`).join("")}</div>` : ""}
  </details>`;
}
let enviandoReg = false;
async function enviarRegistros() {
  const { token, repo, ramo } = E.config;
  if (!token || enviandoReg || !navigator.onLine) return;
  enviandoReg = true;
  for (const x of E.envios.filter(y => !y.enviada && y.arquivos)) {
    try {
      const caminhos = [];
      for (const [i, a] of x.arquivos.entries()) {
        const blob = await guardado("readonly", st => st.get(a.chave)); if (!blob) continue;
        const caminho = `cerebro/registro/entrada/${x.id}-${i + 1}.${a.ext}`;
        const w = await fetch(`https://api.github.com/repos/${repo}/contents/${caminho}`, { method: "PUT",
          headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" },
          body: JSON.stringify({ message: `Cérebro: ${REG[x.tipo].nome} registrado`, branch: ramo, content: await paraB64(blob) }) });
        if (!w.ok && w.status !== 422) throw new Error(`HTTP ${w.status}`);
        caminhos.push(caminho); await guardado("readwrite", st => st.delete(a.chave));
      }
      x.enviada = true; delete x.erro;
      registrar({ evento: "registrou", tipo: x.tipo, id: x.id, arquivos: caminhos, ...(x.link ? { link: x.link } : {}), ...(x.nota ? { nota: x.nota } : {}) });
    } catch (err) { x.erro = err.message; }
  }
  enviandoReg = false; salvar();
  if (E.aba === "caixa") telaCaixa();
}
async function registrarConteudo() {
  const link = document.getElementById("reg-link")?.value.trim() || "", nota = document.getElementById("reg-nota")?.value.trim() || "";
  const files = [...(document.getElementById("reg-arq")?.files || [])];
  if (!link && !files.length) { E.erroReg = "Cole um link ou escolha um arquivo."; telaCaixa(); return; }
  E.erroReg = "";
  const id = new Date().toISOString().slice(0, 19).replace(/[-:]/g, "").replace("T", "-"), x = { id, tipo: E.regTipo, quando: new Date().toISOString(), ...(link ? { link } : {}), ...(nota ? { nota } : {}) };
  if (files.length) {
    x.arquivos = [];
    for (const [i, f] of files.entries()) {
      const chave = `reg-${id}-${i}`, ext = (f.name.split(".").pop() || (E.regTipo === "pdf" ? "pdf" : "jpg")).toLowerCase().slice(0, 5);
      await guardado("readwrite", st => st.put(f, chave)); x.arquivos.push({ chave, ext, nome: f.name });
    }
    x.enviada = false;
  } else {
    x.enviada = true; registrar({ evento: "registrou", tipo: x.tipo, id, link, ...(nota ? { nota } : {}) });
  }
  E.envios.unshift(x); salvar(); telaCaixa(); enviarRegistros();
}

// ---------- Caixa ----------
const DESTINO = { fluxo: "Relevantes", estante: "Estante (séries)", colecao: "Assets", sair: "Sair", ajuste: "Ajuste (vale a partir da próxima madrugada)" };
// Fundo ⇄ Relevantes (pedido de 2026-10-21): você manda um episódio de um lado para o outro. Vale na hora neste aparelho;
// a esteira grava de vez (projeto/gerador/movidos.py) e os outros aparelhos recebem pelo registro.
// item de Relevantes removido por você (botão Remover; pedido de 2026-10-21): some daqui e a esteira tira de vez
function tirarRemovidos() { FLUXO = FLUXO.filter(f => !(/^FX-/.test(f.cod) && E.decisoes["arquivar:" + f.cod])); }
function aplicarMovidos() {
  for (const [cod, m] of Object.entries(E.movidos || {})) {
    if (m.para === "relevantes") {
      const novo = cod.startsWith("FX-") ? cod : "FX-" + cod;
      FUNDO = FUNDO.filter(x => x.cod !== cod && x.url !== m.url);
      if (FLUXO.some(f => f.cod === novo || (m.url && f.url === m.url && !["colecao", "empresa"].includes(f.tipo)))) continue;   // já está lá
      const seg = (m.minutos || 60) * 60, n = Math.max(1, Math.round(seg / 900)), dia = String(m.quando).slice(0, 10);
      FLUXO.push({ cod: novo, origem: cod, fonte: m.fonte, titulo: m.titulo, tipo: "podcast", url: m.url, minutos: m.minutos, imagem: m.imagem, resumo: m.resumo,
        entrou: dia, vence: new Date(Date.parse(dia) + 21 * 86400000).toISOString().slice(0, 10), selo: "completo", movido: true });
      for (let j = 0; j < n; j++) { const de = Math.round(seg * j / n), ate = Math.round(seg * (j + 1) / n);
        SESS.push({ id: `${novo}.${String(j + 1).padStart(2, "0")}`, item: novo, ordem: j + 1, tipo: "audio", modo: "audio", onde: "app", url: m.url, titulo: `Trecho ${j + 1} de ${n}`,
          de, ate, minutos: Math.max(1, Math.round((ate - de) / 60)), estimado: !m.minutos, pergunta: "O que você leva deste trecho?" }); }
    } else if (m.para === "fundo") {
      const f = FLUXO.find(x => x.cod === cod);
      FLUXO = FLUXO.filter(x => x.cod !== cod); SESS = SESS.filter(x => x.item !== cod);
      if (!FUNDO.some(x => x.url === m.url)) FUNDO.push({ cod: (f && f.origem) || m.origem || cod, fonte: m.fonte, titulo: m.titulo, url: m.url, minutos: m.minutos,
        publicado: m.quando, tema: "top", imagem: m.imagem, resumo: m.resumo });
    }
  }
  podcastsParaNovidades();
}
function mover(cod, para) {
  const x = para === "relevantes" ? FUNDO.find(y => y.cod === cod) : FLUXO.find(y => y.cod === cod); if (!x) return;
  const ev = { evento: "moveu", item: cod, para, fonte: x.fonte, titulo: x.titulo, url: x.url, minutos: x.minutos, imagem: x.imagem || null, resumo: x.resumo || x.motivo || null,
    ...(x.origem ? { origem: x.origem, desfaz: x.origem } : {}), quando: new Date().toISOString() };
  if (x.origem) delete E.movidos[x.origem];   // volta para o Fundo de onde veio
  E.movidos[cod] = ev; registrar(ev); aplicarMovidos(); salvar();
  if (E.tocando && E.tocando.item === cod) pararPlayer();
  E.fase = 0; E.sessao = null; E.episodio = null;
}
// O que você pediu e a esteira ainda vai fazer de madrugada, com "Cancelar" (pedido de 2026-10-21)
function blocoPendentes() {
  const nomeDe = cod => { const f = FLUXO.find(x => x.cod === cod), d = FUNDO.find(x => x.cod === cod), c = CAIXA.find(x => x.id === cod);
    return f ? `${f.fonte} · ${f.titulo}` : d ? `${d.fonte} · ${d.titulo}` : IT[cod] ? IT[cod].titulo : c ? c.titulo : cod; };
  const tam = k => (TAMANHOS.find(t => t[0] === String(k)) || [, `de ${k} min`])[1].toLowerCase();
  const ps = Object.entries(E.decisoes).flatMap(([k, v]) => {
    if (k.startsWith("guia:")) { const cod = k.slice(5); return GUIAS[cod] ? [] : [{ k, txt: `Guia (minutos + resumo): ${nomeDe(cod)}` }]; }
    if (!k.startsWith("pedido:")) return [];
    const [cod, m] = k.slice(7).split("@"), f = FLUXO.find(x => x.cod === cod);
    if (f && m && (f.resumos || []).includes(m)) return [];   // já ficou pronto
    return [{ k, txt: `Resumo ${m ? tam(m) : `de ${v} min`}: ${nomeDe(cod)}` }];
  });
  if (!ps.length) return "";
  return `<div class="aviso"><b>Pendente para a madrugada</b><div class="lista">${ps.map(p => `<div class="item"><h3>${esc(p.txt)}</h3>
    <div class="acoes"><button class="bt sec" type="button" data-cancelar="${esc(p.k)}">Cancelar</button></div></div>`).join("")}</div></div>`;
}
function telaCaixa() {
  // Caixa reorganizada (2026-10-21): primeiro o que pede decisão sua, explicado; o resto embaixo e fechado
  const resolvido = c => ["aprovado", "descartado", "aprovou", "descartou"].includes(E.decisoes[c.id] || c.estado);
  const decidir = CAIXA.filter(c => !resolvido(c) && c.proposta && !E.decisoes[c.id]);
  const esperando = CAIXA.filter(c => !resolvido(c) && (!c.proposta || E.decisoes[c.id]));
  const ORIGEM = { vigia: "a vigia achou", "você": "você mandou", "sua estante": "da sua estante", "revisão de domingo": "revisão de domingo" };
  document.getElementById("tela-caixa").innerHTML = `
    <div><p class="olho">Atualiza toda madrugada</p><h1 class="titulo-tela">Caixa</h1></div>
    ${decidir.length ? `<div class="grupo"><div class="cab-serie"><b>Para você decidir</b><span class="cod">${decidir.length}</span></div>
      <p class="cod">Novidades que o Cérebro achou nas fontes que vigia. Aprovar põe no destino proposto; descartar tira daqui. O que você decide aqui vale a partir da próxima madrugada; mudanças no próprio app não passam por aqui, peça no chat.</p>
      <div class="lista caixa-lista">${decidir.map(c => { const p = c.proposta; return `<div class="item">
        <div class="meta"><span class="origem">${esc(ORIGEM[c.origem] || c.origem)}</span><span>${esc(c.quando)}</span></div>
        <h3>${esc(c.titulo)}</h3>
        <p class="cod">Vai para <b>${esc(DESTINO[p.destino] || p.destino)}</b>${p.motivo ? ` · ${esc(p.motivo)}` : ""}</p>
        <div class="acoes"><button class="bt" type="button" data-decidir="aprovou" data-id="${esc(c.id)}">Aprovar</button>
          <button class="bt sec" type="button" data-decidir="descartou" data-id="${esc(c.id)}">Descartar</button>
          ${c.url ? `<a class="bt sec" href="${esc(c.url)}" target="_blank" rel="noopener" style="text-decoration:none">Abrir</a>` : ""}</div></div>`; }).join("")}</div></div>`
      : `<p class="cod">Nada esperando decisão sua.</p>`}
    ${blocoPendentes()}
    <form class="campo" id="form-desejo"><label class="cod" for="desejo" hidden>Quero aprender sobre</label>
      <input id="desejo" placeholder="Quero aprender sobre... ou cole um link" autocomplete="off"><button class="bt" type="submit">Mandar</button></form>
    ${blocoRegistrar()}
    ${esperando.length + E.desejos.length ? `<details class="grupo"><summary class="cab-serie"><b>Esperando a madrugada</b><span class="cod">${esperando.length + E.desejos.length}</span></summary>
      <div class="lista caixa-lista">${E.desejos.map(d => `<div class="item"><div class="meta"><span class="origem">você mandou</span><span>${esc(d.quando)}</span></div><h3>${esc(d.texto)}</h3></div>`).join("")}
      ${esperando.map(c => `<div class="item"><div class="meta"><span class="origem">${esc(ORIGEM[c.origem] || c.origem)}</span><span>${esc(c.quando)}</span>${E.decisoes[c.id] ? `<span class="chip">${E.decisoes[c.id] === "mudar" ? "pediu para mudar" : "aprovado"}</span>` : ""}</div>
        <h3>${esc(c.titulo)}</h3>${E.decisoes[c.id] === "mudar" ? `<p class="cod">"Mudar" não diz o que mudar. Se ainda quer decidir, volte o item para cima.</p>
          <div class="acoes"><button class="bt sec" type="button" data-cancelar="${esc(c.id)}">Voltar para decidir</button></div>` : ""}</div>`).join("")}</div></details>` : ""}
    <details class="aviso" id="ajustes"${E.config.token ? "" : " open"}><summary><b>Ajustes</b> · ${E.config.token ? "sincronização ligada" : "sincronização desligada"}</summary>
      <p>Cole um token do GitHub com acesso só a este repositório (permissão Contents: leitura e escrita). Ele fica só neste aparelho.</p>
      <label class="cod" for="token">Token</label><input id="token" type="password" autocomplete="off" value="${esc(E.config.token)}" class="campo-texto">
      <label class="cod" for="repo">Repositório</label><input id="repo" value="${esc(E.config.repo)}" class="campo-texto">
      <div class="acoes"><button class="bt" type="button" data-acao="guardar-ajustes">Guardar</button><button class="bt sec" type="button" data-acao="sincronizar">Sincronizar agora</button></div>
      <p class="cod">${E.fila.length} evento(s) esperando envio. ${esc(E.sync)}</p>
      <p class="cod">Versão do app: ${VERSAO}. Deve ser a mesma no iPhone e no iPad.</p>
    </details>`;
}

// ---------- mapa de metrô ----------
const W = 400, X0 = 46, X1 = 386, PASSO = (X1 - X0) / (ORDEM.length - 1);
const colX = m => X0 + ORDEM.indexOf(m) * PASSO;
function telaMapa() {
  const pos = {}, faixas = [];
  let y = 38;
  for (const s of D.series) {
    const aceso = s.n === E.serie;
    const top = y;
    if (aceso) {
      s.itens.forEach((c, j) => { pos[c] = { x: colX(IT[c].mat), y: top + 18 + j * 30 }; });
      y = top + 18 + (s.itens.length - 1) * 30 + 18;
    } else {
      const k = {};
      s.itens.forEach(c => { const m = IT[c].mat; k[m] = (k[m] || 0) + 1; pos[c] = { x: colX(m), y: top + 9 + (k[m] - 1) * 8 }; });
      y = top + 9 + (Math.max(...Object.values(k)) - 1) * 8 + 9;
    }
    faixas.push({ s, top, bot: y, aceso });
    y += 3;
  }
  const H = y + 8, atual = faixas[E.serie - 1];
  const svg = [];
  // faixas das séries
  faixas.forEach(f => {
    if (f.aceso) svg.push(`<rect x="0" y="${f.top}" width="${W}" height="${f.bot - f.top}" style="fill:var(--aceso-fundo)"/><rect x="0" y="${f.top}" width="4" height="${f.bot - f.top}" style="fill:var(--aceso)"/>`);
    else svg.push(`<line x1="34" x2="${W}" y1="${f.bot + 1.5}" y2="${f.bot + 1.5}" style="stroke:var(--fio)" stroke-width="1"/>`);
    svg.push(`<text x="10" y="${(f.top + f.bot) / 2 + 3.5}" style="fill:${f.aceso ? "var(--aceso-tinta)" : "var(--apagado)"};font:${f.aceso ? 700 : 500} 10px var(--f-codigo)">S${f.s.n}</text>`);
  });
  // linhas
  ORDEM.forEach(m => {
    const ys = D.itens.filter(i => i.mat === m && pos[i.cod]).map(i => pos[i.cod].y);
    if (!ys.length) return;
    const nuc = MAT[m].nucleo, w = nuc ? 6 : 4, x = colX(m), y0 = Math.min(...ys), y1 = Math.max(...ys);
    svg.push(`<line x1="${x}" x2="${x}" y1="${nuc ? 30 : y0}" y2="${y1}" stroke-linecap="round" stroke-width="${w}" style="stroke:${cor(m)};opacity:.28"/>`);
    const corte = Math.min(y1, atual.bot);
    if (corte > y0 || nuc) svg.push(`<line x1="${x}" x2="${x}" y1="${nuc ? 30 : y0}" y2="${Math.max(corte, y0)}" stroke-linecap="round" stroke-width="${w}" style="stroke:${cor(m)}"/>`);
  });
  // cabeçalho das linhas
  ORDEM.forEach(m => svg.push(`<rect x="${colX(m) - 13}" y="8" width="26" height="15" rx="3" style="fill:${cor(m)}"/>
    <text x="${colX(m)}" y="19" text-anchor="middle" style="fill:var(--cartao);font:600 9px var(--f-codigo)">${m}</text>`));
  // baldeações (pré-requisitos entre matérias)
  const bald = new Set();
  D.itens.forEach(i => {
    if (!pos[i.cod] || !i.pre || !pos[i.pre] || IT[i.pre].mat === i.mat) return;
    const a = pos[i.pre], b = pos[i.cod], my = (a.y + b.y) / 2;
    bald.add(i.cod); bald.add(i.pre);
    const perto = i.serie === E.serie || IT[i.pre].serie === E.serie;   // as da série atual ficam mais fortes
    svg.push(`<path d="M${a.x} ${a.y} C${a.x} ${my} ${b.x} ${my} ${b.x} ${b.y}" fill="none" stroke-width="${perto ? 1.6 : 1.1}" stroke-dasharray="3 3" style="stroke:var(--tinta);opacity:${perto ? .7 : .3}"/>`);
  });
  // estações
  for (const f of faixas) for (const c of f.s.itens) {
    const it = IT[c], p = pos[c], lida = E.lidas.has(c), r = f.aceso ? 6.5 : 3.6;
    const fill = lida ? cor(c) : "var(--cartao)", sw = f.aceso ? 3 : 1.6;
    let g = `<g class="est-svg" tabindex="0" role="button" data-ficha="${c}" aria-label="${esc(it.titulo)}, ${c}${lida ? ", lida" : ""}">
      <circle class="alvo" cx="${p.x}" cy="${p.y}" r="${f.aceso ? 14 : 7}" style="fill:transparent"/>`;
    if (bald.has(c)) g += `<circle cx="${p.x}" cy="${p.y}" r="${r + 2.6}" fill="none" stroke-width="1.3" style="stroke:var(--tinta)"/>`;
    g += `<circle cx="${p.x}" cy="${p.y}" r="${r}" stroke-width="${sw}" style="fill:${fill};stroke:${cor(c)}"/>`;
    if (f.aceso) {
      const dir = p.x > W * .55, tx = dir ? p.x - 14 : p.x + 14, cabe = Math.floor((dir ? tx - 4 : W - tx - 4) / 5.9);
      const t = it.titulo.length > cabe ? it.titulo.slice(0, cabe - 1).trimEnd() + "…" : it.titulo;
      g += `<text x="${tx}" y="${p.y + 3.8}" text-anchor="${dir ? "end" : "start"}" stroke-width="4" paint-order="stroke"
        style="fill:var(--tinta);stroke:var(--aceso-fundo);font:600 11px var(--f-placa)">${esc(t)}</text>`;
    }
    svg.push(g + "</g>");
  }
  const total = D.series.reduce((a, s) => a + s.itens.length, 0);
  document.getElementById("estante-corpo").innerHTML = `
    <p class="olho">Série ${E.serie} de ${D.series.length} · ${E.lidas.size} de ${total} estações</p>
    <div class="estados">
      <span><svg width="14" height="14"><circle cx="7" cy="7" r="5" style="fill:var(--tinta)"/></svg>lida</span>
      <span><svg width="14" height="14"><circle cx="7" cy="7" r="5" stroke-width="2.5" style="fill:var(--aceso-fundo);stroke:var(--aceso)"/></svg>série atual</span>
      <span><svg width="14" height="14"><circle cx="7" cy="7" r="4" stroke-width="1.5" style="fill:var(--cartao);stroke:var(--apagado)"/></svg>próximas</span>
      <span><svg width="26" height="14"><path d="M2 7h22" stroke-dasharray="3 3" stroke-width="1.3" style="stroke:var(--tinta)"/></svg>baldeação</span>
    </div>
    <div class="mapa-wrap"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Mapa de metrô das séries">${svg.join("")}</svg></div>
    <h3>Linhas</h3>
    <div class="legenda">${ORDEM.map(m => `<div><i style="background:${cor(m)}"></i><span class="cod">${m}</span><span>${esc(MAT[m].nome)}${MAT[m].nucleo ? " · núcleo" : ""}</span></div>`).join("")}</div>
    <p class="cod">Toque numa estação para abrir a ficha. Médio e eletivas das matérias rotativas entram depois como ramais.</p>`;
  if (E.aba === "estante") requestAnimationFrame(() => {
    const m = document.getElementById("main"), el = document.querySelector(`[data-ficha="${SERIE().itens[0]}"]`);
    if (el) m.scrollTop = Math.max(0, el.getBoundingClientRect().top - m.getBoundingClientRect().top + m.scrollTop - 160);
  });
}

// ---------- ficha ----------
function abrirFicha(c) {
  const it = IT[c], lida = E.lidas.has(c), atual = it.serie === E.serie;
  const pre = it.pre && IT[it.pre];
  document.getElementById("sobre").innerHTML = `<div class="veu" data-acao="fechar"></div>
    <div class="ficha" role="dialog" aria-modal="true" aria-label="Ficha de ${esc(it.titulo)}">
      <span class="alca"></span>
      <div class="chips">
        <span class="chip" style="background:${cor(c)};color:var(--cartao)">${esc(NOME_CURTO[it.mat])}</span>
        <span class="chip">${c}</span><span class="chip">${esc(it.nivel)}</span>
        ${lida ? '<span class="chip lida">lida</span>' : atual ? '<span class="chip aceso">série atual</span>' : it.serie ? `<span class="chip">série ${it.serie}</span>` : ""}
        ${it.marca === "sug" ? '<span class="chip">sugestão do Claude</span>' : ""}
      </div>
      <div><h2>${esc(it.titulo)}</h2><p class="autor">${esc(it.autor)} · ${esc(it.formato)}</p></div>
      <dl>
        <dt>Robustez</dt><dd>${pontos(it.robustez)}</dd>
        <dt>Facilidade</dt><dd>${pontos(it.facilidade)}</dd>
        <dt>Tempo</dt><dd>${esc(fmtTempo(it.tempo))}</dd>
        <dt>Leitura</dt><dd>${esc(it.leitura)}</dd>
        <dt>Pré-requisito</dt><dd>${pre ? `<button class="link" type="button" data-ficha="${pre.cod}">${pre.cod} · ${esc(pre.titulo)}</button>` : "nenhum"}</dd>
        ${it.nota ? `<dt>Nota</dt><dd>${esc(it.nota)}</dd>` : ""}
      </dl>
      <div class="acoes">${atual && !lida ? `<a class="bt" href="#hoje" data-acao="fechar" style="text-decoration:none">Ir para o Hoje</a>` : ""}<button class="bt sec" type="button" data-acao="fechar">Fechar</button></div>
    </div>`;
  document.querySelector(".ficha .bt.sec").focus();
}


// ---------- navegação e eventos ----------
const ABAS = ["semana", "series", "conteudos", "novidades", "feed", "caixa", "inscricoes"], LEGADO = { hoje: "series", estante: "conteudos" };
function aba() {
  const h = location.hash.slice(1), a = LEGADO[h] || (ABAS.includes(h) ? h : "semana");
  E.aba = a; if (a === "series" || a === "conteudos") E.dom = a;
  document.querySelectorAll("nav.abas a").forEach(el => el.dataset.aba === a ? el.setAttribute("aria-current", "page") : el.removeAttribute("aria-current"));
  const tela = a === "series" || a === "conteudos" ? "hoje" : a;   // Séries e Conteúdos moram na mesma tela
  ["semana", "hoje", "novidades", "feed", "caixa", "inscricoes"].forEach(t => document.getElementById("tela-" + t).hidden = t !== tela);
  document.getElementById("sobre").innerHTML = "";
  if (a === "semana") { telaSemana(); document.getElementById("main").scrollTop = 0; return; }
  if (a === "novidades") { telaNovidades(); document.getElementById("main").scrollTop = 0; } else if (a === "inscricoes") telaInscricoes(); else if (a === "feed") telaFeed(); else if (a === "caixa") telaCaixa(); else { telaHoje(); document.getElementById("main").scrollTop = 0; }
}
function iniciarSessao(o, pos) {
  E.sessao = o; E.fase = 1; E.inicio = Date.now(); E.seg = 0; E.recortes = []; E.parou = false;
  if (!["resumo", "transcricao", "resumo-audio"].includes(o.tipo)) E.andamento[o.id] = { ...(E.andamento[o.id]?.pag ? { pag: E.andamento[o.id].pag } : {}), pos: pos || 0, quando: new Date().toISOString() };
  registrar({ evento: "comecou", sessao: o.id, formato: E.formato });
  if (o.onde === "app") tocar(o, pos != null ? pos : o.de || 0);
  ligarRelogio(); telaHoje();
  if (o.onde === "resumo") carregarResumo(o);
  if (o.onde === "transcricao") carregarTranscricao(o);
}
// Transcrição por frase (com o segundo de início), para acompanhar o áudio grifando a frase atual
const SEGS = {};
async function carregarSegmentos(cod) {
  if (SEGS[cod]) return;
  try { const r = await fetch(`dados/transcricoes/${cod}.json`); if (r.ok) SEGS[cod] = await r.json(); } catch (_) {}
  if (E.fase === 1) telaHoje();
}
let fraseAtual = null, toqueNaCaixa = 0;   // se você rolar a transcrição com o dedo, ela espera 4 s antes de voltar a seguir o áudio
document.addEventListener("touchstart", e => { if (e.target.closest && e.target.closest("#acomp")) toqueNaCaixa = Date.now(); }, { passive: true });
function grifar() {
  const box = document.getElementById("acomp"); if (!box) return;
  const t = document.getElementById("audio").currentTime, spans = box.querySelectorAll("span[data-t]");
  let atual = null;
  for (const sp of spans) { if (+sp.dataset.t <= t + 0.2) atual = sp; else break; }
  if (atual && atual !== fraseAtual) {
    if (fraseAtual) fraseAtual.classList.remove("agora");
    atual.classList.add("agora"); fraseAtual = atual;
    // posição pela tela (offsetTop dependia de qual elemento era a referência e às vezes dava 0: a caixa não rolava)
    const top = box.scrollTop + atual.getBoundingClientRect().top - box.getBoundingClientRect().top - box.clientHeight / 3;
    if (Date.now() - toqueNaCaixa > 4000) box.scrollTo({ top, behavior: Math.abs(top - box.scrollTop) > box.clientHeight ? "auto" : "smooth" });
  }
}
document.getElementById("audio").addEventListener("timeupdate", grifar);
// Em que tempo estou (pedido de 2026-10-23): posição no miniplayer e na tela do episódio, e o capítulo do esboço aceso
function mostrarPosicao() {
  const a = document.getElementById("audio"), cur = a.currentTime || 0, dur = isFinite(a.duration) ? a.duration : 0;
  const txt = dur ? `${hms(cur)} de ${hms(dur)}` : hms(cur);
  const mp = document.getElementById("mp-tempo"); if (mp) mp.textContent = txt;
  const pa = document.getElementById("pos-agora"); if (pa) pa.textContent = `Você está em ${txt}`;
  const bs = [...document.querySelectorAll(".esboco [data-esb]")]; let atual = null;
  bs.forEach(b => { if (+b.dataset.esb <= cur + 0.5) atual = b; });
  bs.forEach(b => b.classList.toggle("agora", b === atual));
}
["timeupdate", "loadedmetadata", "seeked"].forEach(ev => document.getElementById("audio").addEventListener(ev, mostrarPosicao));

// Player fixo: o áudio vive fora das telas, então continua quando você volta ao Hoje ou troca de aba.
function tocar(o, desde) {
  const a = document.getElementById("audio");
  registrarOuvido();
  E.tocando = o;
  const fx = FLUXO.find(f => f.cod === o.item);
  ouvindo = { item: o.item, fonte: o.tipo === "fundo" ? o.fonte : fx ? fx.fonte : o.fonte || null, seg: 0, ultimo: null };
  if (a.dataset.url !== o.url) { a.src = o.url; a.dataset.url = o.url; }
  const ir = () => { a.currentTime = desde; a.playbackRate = E.vel; a.play().catch(() => {}); };
  if (a.readyState >= 1) ir(); else a.addEventListener("loadedmetadata", ir, { once: true });
  document.getElementById("mp-titulo").textContent = o.titulo;
  document.getElementById("mp-vel").textContent = `${String(E.vel).replace(".", ",")}×`;
  document.getElementById("miniplayer").hidden = false;
}
// Tempo ouvido de verdade (pedido de 2026-10-21: estatística dos programas favoritos): o player soma os segundos tocando
// e registra {"evento": "ouviu", item, fonte, seg} ao pausar, ao terminar, a cada 10 min e ao fechar o app.
let ouvindo = { item: null, fonte: null, seg: 0, ultimo: null };
function contarOuvido() {
  const a = document.getElementById("audio"), agora = a.currentTime;
  if (!a.paused && ouvindo.ultimo != null) { const d = agora - ouvindo.ultimo; if (d > 0 && d < 5) ouvindo.seg += d; }   // segundos do episódio (pular adiante não conta)
  ouvindo.ultimo = agora;
  if (ouvindo.seg >= 600) registrarOuvido();
}
function registrarOuvido() {
  // leva também o trecho e o ponto: assim o "Em andamento" aparece em qualquer aparelho, mesmo sem tocar em "Parei aqui"
  const a = document.getElementById("audio"), t = E.tocando;
  if (ouvindo.item && ouvindo.seg >= 30) registrar({ evento: "ouviu", item: ouvindo.item, fonte: ouvindo.fonte, seg: Math.round(ouvindo.seg),
    ...(t && t.id && t.tipo !== "resumo-audio" ? { sessao: (t.bloco ? (SESS.filter(x => t.bloco.includes(x.id)).find(x => x.de <= a.currentTime && (x.ate == null || a.currentTime < x.ate)) || t).id : t.id), posicao: Math.round(a.currentTime) } : {}) });
  ouvindo.seg = 0;
}
["pause", "ended"].forEach(ev => document.getElementById("audio").addEventListener(ev, () => { registrarOuvido(); ouvindo.ultimo = null; }));
document.getElementById("audio").addEventListener("pause", () => {   // episódio das Novidades: o ponto fica guardado ao pausar
  const t = E.tocando, a = document.getElementById("audio");
  if (t && t.tipo === "fundo" && a.currentTime > 5) { E.posicoes[t.id] = Math.round(a.currentTime); salvar(); }
});
document.getElementById("audio").addEventListener("timeupdate", contarOuvido);
document.addEventListener("visibilitychange", () => { if (document.hidden) registrarOuvido(); });
function pararPlayer() {
  const a = document.getElementById("audio"); a.pause();
  document.getElementById("miniplayer").hidden = true; E.tocando = null;
}
function voltarAoHoje() {
  const o = E.sessao, a = document.getElementById("audio");
  if (E.andamento[o.id]) E.andamento[o.id] = { pos: o.onde === "app" && E.tocando === o ? Math.round(a.currentTime) : E.andamento[o.id].pos, quando: new Date().toISOString() };
  salvar(); E.fase = 0; E.alt = 0; telaHoje(); document.getElementById("main").scrollTop = 0;
}
function terminarSessao(parou) {
  const o = E.sessao, a = document.getElementById("audio");
  E.parou = parou; E.fase = 2; clearInterval(relogio);
  E.posicao = o.onde === "app" && a ? Math.round(a.currentTime) : null;
  if (o.onde === "app") pararPlayer();
  if (parou && E.andamento[o.id]) E.andamento[o.id] = { pos: E.posicao || 0, quando: new Date().toISOString() };
  if (!parou) delete E.andamento[o.id];
  if (o.tipo === "fundo") {
    // fundo não tem nota: registra o tempo e guarda o ponto
    if (parou) { if (E.posicao) E.posicoes[o.cod] = E.posicao; } else { delete E.posicoes[o.cod]; E.ouvidos = E.ouvidos.concat(o.cod).slice(-500); }
    registrar({ evento: parou ? "parou" : "terminou", sessao: o.cod, min: Math.max(1, Math.round(E.seg / 60)), formato: "fundo",
      ...(E.recortes.length ? { recortes: E.recortes } : {}), ...(E.posicao != null ? { posicao: E.posicao } : {}) });
    E.fase = 3; telaHoje(); return;
  }
  telaHoje(); document.getElementById("nota")?.focus();
}

document.addEventListener("click", e => {
  if (e.target.closest("button") && document.activeElement && document.activeElement.id === "nota-feed") document.activeElement.blur();   // o Safari não tira o foco ao tocar num botão
  const t = e.target.closest("[data-tempo],[data-formato],[data-acao],[data-ficha],[data-sub],[data-ir],[data-decidir],[data-fundo],[data-arquivar],[data-remover],[data-cancelar],[data-mover],[data-continuar],[data-finalizar],[data-visao],[data-desinscrever],[data-texto],[data-resumo-item],[data-pular],[data-episodio],[data-trecho],[data-bloco],[data-ouvir-resumo],[data-oferta],[data-item],[data-pedir-item],[data-ja-li],[data-reg],[data-ouvir-em],[data-depois],[data-concluir],[data-nota-nov],[data-gravar-nov],[data-feedvis],[data-acervo],[data-ac-tocar],[data-ac-depois],[data-ac-mais],[data-canal],[data-bio],[data-revisou],[data-semana]");
  if (!t) return;
  if (t.dataset.item) { E.voltarPara = E.aba; E.sugestao = null; E.registrouItem = null; E.episodio = t.dataset.item; E.fase = 0; if (!naHoje()) location.hash = "#" + dominioItem(t.dataset.item); telaHoje(); document.getElementById("main").scrollTop = 0; return; }
  if (t.dataset.episodio) { E.episodio = t.dataset.episodio; E.fase = 0; document.getElementById("sobre").innerHTML = ""; if (!naHoje()) location.hash = "#" + dominioItem(t.dataset.episodio); telaHoje(); document.getElementById("main").scrollTop = 0; return; }
  if (t.dataset.reg) { E.regAberto = true; E.regTipo = t.dataset.reg; E.erroReg = ""; salvar(); telaCaixa(); return; }
  if (t.dataset.jaLi) {   // leu fora do app (GoodNotes, Safari): marca sem cronometrar
    const x = SESS.find(y => y.id === t.dataset.jaLi); E.feitas.add(x.id); cobrir(x.item);
    if (!ehFluxo(x) && !proximaDoItem(x.item)) E.lidas.add(x.item);
    registrar({ evento: "terminou", sessao: x.id, min: 0, formato: x.tipo === "audio" ? "audio" : "texto", fora: true }); telaHoje(); return;
  }
  if (t.dataset.trecho && E.aba === "semana") { const x = SESS.find(y => y.id === t.dataset.trecho); if (x) location.hash = "#" + dominioItem(x.item); }
  if (t.dataset.trecho) { const x = SESS.find(y => y.id === t.dataset.trecho), and = E.andamento[x.id]; E.episodio = null; iniciarSessao(x, x.onde === "app" ? (and && and.pos ? and.pos : x.de) : undefined); return; }
  if (t.dataset.bloco) { E.episodio = null; iniciarSessao(juntar(t.dataset.bloco.split(",").map(id => SESS.find(y => y.id === id)))); return; }
  if (t.dataset.pedirItem) {
    const id = `${t.dataset.pedirItem}@${t.dataset.k}`; E.decisoes["pedido:" + id] = +t.dataset.k;
    registrar({ evento: "pediu", item: t.dataset.pedirItem, minutos: +t.dataset.k, chave: id }); telaHoje(); if (E.fase === 1) document.querySelector(".tamanhos")?.scrollIntoView({ block: "center" }); return;
  }
  if (t.dataset.oferta) { const o = E.ofertas[+t.dataset.oferta]; E.sugestao = o; E.registrouItem = null; E.voltarPara = null; E.episodio = o.item; E.fase = 0; telaHoje(); document.getElementById("main").scrollTop = 0; return; }
  if (t.dataset.ouvirResumo) { const f = FLUXO.find(y => y.cod === t.dataset.ouvirResumo); iniciarSessao(sessaoResumoAudio(f, t.dataset.k)); return; }
  if (t.dataset.pular) { const au = document.getElementById("audio"); au.currentTime = Math.max(0, au.currentTime + +t.dataset.pular); return; }
  if (t.dataset.notaNov) {
    const cod = t.dataset.notaNov, x = FUNDO.find(y => y.cod === cod), campo = t.closest(".anotar").querySelector("textarea"), nota = campo.value.trim();
    if (!nota) return;
    const agora = new Date(), id = agora.toISOString().slice(0, 19).replace(/[-:]/g, "").replace("T", "-");
    delete E.rascunhos["nov:" + cod];
    E.falas.unshift({ id, texto: nota, quando: agora.toISOString(), enviada: true, item: cod });
    registrar({ evento: "escreveu", fala: id, texto: nota, item: cod, ...(x ? { fonte: x.fonte, titulo: x.titulo, url: x.url } : {}) });
    E.aba === "novidades" ? telaNovidades() : telaHoje(); return;
  }
  if (t.dataset.gravarNov) { E.erroFala = ""; gravar(t.dataset.gravarNov); return; }
  if (t.dataset.ouvirEm) { ouvirNovidade(t.dataset.ouvirEm, +t.dataset.seg || 0); return; }
  if (t.dataset.depois) {
    const cod = t.dataset.depois, x = FUNDO.find(y => y.cod === cod), ligado = !depois(x);
    E.decisoes["depois:" + cod] = ligado; registrar({ evento: "depois", item: cod, ligado, fonte: x.fonte, titulo: x.titulo }); telaNovidades(); return;
  }
  if (t.dataset.concluir) {   // Terminei: o episódio era bom (conta no placar como terminado)
    const cod = t.dataset.concluir, x = FUNDO.find(y => y.cod === cod), a = document.getElementById("audio");
    const pos = E.tocando && E.tocando.id === cod ? Math.round(a.currentTime) : E.posicoes[cod];
    if (E.tocando && E.tocando.id === cod) pararPlayer();
    delete E.posicoes[cod]; delete E.andamento[cod]; E.ouvidos = E.ouvidos.concat(cod).slice(-500); E.feitas.add(cod);
    registrar({ evento: "terminou", sessao: cod, min: 0, formato: "fundo", fonte: x && x.fonte, ...(pos ? { posicao: pos } : {}) });
    telaNovidades(); return;
  }
  if (t.dataset.fundo) { const s = acharSessao(t.dataset.fundo); iniciarSessao(s, E.posicoes[s.id] || 0); return; }
  if (t.dataset.desinscrever) {   // sair de uma inscrição pelo app (pedido de 2026-10-23); a esteira aplica na madrugada
    const nome = t.dataset.nome, tipo = t.dataset.desinscrever;
    if (!confirm(`Cancelar a inscrição em "${nome}"? O Cérebro deixa de puxar essa fonte na próxima madrugada. Até lá, dá para desfazer.`)) return;
    E.decisoes["desinscreveu:" + nome] = true; registrar({ evento: "desinscreveu", tipo, nome }); salvar(); telaInscricoes(); return;
  }
  if (t.dataset.finalizar) {   // Finalizar (pedido de 2026-10-23): conta como feito e sai de "Em andamento"
    const abertos = t.dataset.finalizar.split("|"), x0 = acharSessao(abertos[0]);
    if (x0 && !confirm(`Finalizar "${nomeDoItem(x0)}"? O que está aberto conta como feito e sai de "Em andamento".`)) return;
    for (const id of abertos) {
      const x = acharSessao(id); if (!x) { delete E.andamento[id]; continue; }
      const ids = (x.bloco || [id]).map(i => i.replace("#txt", ""));
      ids.forEach(i => E.feitas.add(i)); delete E.andamento[id]; ids.forEach(i => delete E.andamento[i]); cobrir(x.item);
      if (!ehFluxo(x) && !proximaDoItem(x.item)) E.lidas.add(x.item);
      registrar({ evento: "terminou", sessao: ids[0], ...(ids.length > 1 ? { bloco: ids } : {}), min: 0, formato: "finalizado", fora: true });
    }
    telaHoje(); return;
  }
  if (t.dataset.continuar) {
    const id = t.dataset.continuar, s = acharSessao(id), pos = E.andamento[id]?.pos;
    if (E.tocando && E.tocando.id === id) { E.sessao = E.tocando; E.fase = 1; telaHoje(); return; }
    iniciarSessao(s, s.onde === "app" ? (pos || s.de || 0) : undefined); return;
  }
  if (t.dataset.texto) { const s = SESS.find(y => y.id === t.dataset.texto); iniciarSessao({ ...s, id: `${s.id}#txt`, base: s.id, tipo: "transcricao", modo: "leitura", onde: "transcricao", titulo: `Ler: ${s.titulo}` }); return; }
  if (t.dataset.resumoItem) { const f = FLUXO.find(y => y.cod === t.dataset.resumoItem); iniciarSessao(sessaoResumoItem(f, t.dataset.k)); return; }
  if (t.dataset.mover) { mover(t.dataset.cod, t.dataset.mover); telaHoje(); return; }
  if (t.dataset.cancelar) {   // pedido para a madrugada (resumo ou guia) desfeito antes da esteira rodar (pedido de 2026-10-21)
    const k = t.dataset.cancelar; delete E.decisoes[k]; registrar({ evento: "cancelou", chave: k });
    E.aba === "caixa" ? telaCaixa() : E.aba === "inscricoes" ? telaInscricoes() : telaHoje(); return;
  }
  if (t.dataset.remover) {
    // remover (pedido de 2026-10-20): "não quero isto no Fundo"; sai da fila e a esteira usa para afinar a curadoria
    const x = FUNDO.find(y => y.cod === t.dataset.remover);
    const fx = FLUXO.find(y => y.cod === t.dataset.remover), alvo = x || fx;
    E.decisoes["arquivar:" + t.dataset.remover] = true; registrar({ evento: "removeu", item: t.dataset.remover, ...(alvo ? { fonte: alvo.fonte, titulo: alvo.titulo, url: alvo.url } : {}) });
    if (fx) { tirarRemovidos(); E.episodio = null; salvar(); }
    if (E.tocando && (E.tocando.id === t.dataset.remover || E.tocando.item === t.dataset.remover)) pararPlayer();
    if (E.fase && E.sessao && (E.sessao.id === t.dataset.remover || E.sessao.item === t.dataset.remover)) { E.fase = 0; E.sessao = null; }
    E.aba === "novidades" ? telaNovidades() : telaHoje(); return;
  }
  if (t.dataset.arquivar) {
    // arquivar é a confirmação: nada sai da fila de fundo sem esse toque
    E.decisoes["arquivar:" + t.dataset.arquivar] = true; registrar({ evento: "arquivou", item: t.dataset.arquivar }); telaHoje(); return;
  }
  if (t.dataset.tempo) { E.tempo = t.dataset.tempo; E.alt = 0; salvar(); telaHoje(); return; }
  if (t.dataset.formato) { E.formato = t.dataset.formato; E.alt = 0; salvar(); telaHoje(); return; }
  if (t.dataset.semana) {
    const k = "semana:" + SEMANA.inicio + ":" + t.dataset.semana, v = E.decisoes[k] === t.dataset.escolha ? null : t.dataset.escolha;
    if (v) E.decisoes[k] = v; else delete E.decisoes[k];
    registrar({ evento: "semana", chave: k, escolha: v || "desfez" }); telaSemana(); return;
  }
  if (t.dataset.revisou) {
    const k = t.dataset.revisou, lembrou = t.dataset.lembrou === "1", n = lembrou ? Math.min(((E.revisoes[k] || {}).nivel || 0) + 1, INTERVALOS.length - 1) : 0;
    const dias = lembrou ? INTERVALOS[n] : INTERVALOS[0], proxima = new Date(Date.now() + dias * 86400000).toISOString().slice(0, 10);
    E.revisoes[k] = { nivel: n, proxima }; registrar({ evento: "revisou", chave: k, lembrou, nivel: n, proxima }); salvar(); telaFeed(); return;
  }
  if (t.dataset.bio) { E.bio = t.dataset.bio; E.fase = 0; document.getElementById("main").scrollTop = 0; telaHoje(); return; }
  if (t.dataset.canal) {   // nome do programa nas Novidades abre a página dele nas Inscrições; "← Novidades" volta ao mesmo lugar (2026-10-24)
    E.voltarAcervo = { aba: E.aba, topo: document.getElementById("main").scrollTop }; E.acervo = t.dataset.canal; E.acervoN = 50; E.acervoQ = "";
    document.getElementById("main").scrollTop = 0; if (E.aba === "inscricoes") telaInscricoes(); else location.hash = "#inscricoes"; return;
  }
  if (t.dataset.acervo !== undefined) {
    const v = !t.dataset.acervo && E.voltarAcervo; E.voltarAcervo = null;
    E.acervo = t.dataset.acervo || null; E.acervoN = 50; E.acervoQ = ""; document.getElementById("main").scrollTop = 0;
    if (v && v.aba !== "inscricoes") { E.acervo = null; location.hash = "#" + v.aba; setTimeout(() => { document.getElementById("main").scrollTop = v.topo; }, 150); return; }
    telaInscricoes(); return;
  }
  if (t.dataset.acMais) { E.acervoN = (E.acervoN || 50) + 50; telaInscricoes(); return; }
  if (t.dataset.acTocar || t.dataset.acDepois) { acaoAcervo(t.dataset.acTocar || t.dataset.acDepois, t.dataset.id, !!t.dataset.acDepois); return; }
  if (t.dataset.feedvis) { E.feedVis = t.dataset.feedvis; salvar(); telaFeed(); return; }
  if (t.dataset.sub) { E.sub = t.dataset.sub; telaHoje(); return; }
  if (t.dataset.visao) { E.visao[E.dom] = t.dataset.visao; telaHoje(); document.getElementById("main").scrollTop = 0; return; }
  if (t.dataset.ir) { const a = document.getElementById("audio"); if (a) { a.currentTime = +t.dataset.ir; a.play().catch(() => {}); } return; }
  if (t.dataset.ficha) { abrirFicha(t.dataset.ficha); return; }
  if (t.dataset.decidir) {
    const id = t.dataset.id, ev = t.dataset.decidir;
    E.decisoes[id] = ev; registrar({ evento: ev, [id.includes(".") ? "sessao" : "item"]: id }); badgeCaixa();
    if (E.aba === "caixa") telaCaixa(); else telaHoje();
    return;
  }
  const a = t.dataset.acao;
  if (a === "fechar") { document.getElementById("sobre").innerHTML = ""; return; }
  if (a === "gravar-fala") { E.erroFala = ""; gravar(); return; }
  if (a === "parar-fala" || a === "parar-item") { if (gravacao) gravacao.rec.stop(); return; }
  if (a === "trocar") { E.alt++; telaHoje(); return; }
  if (a === "comecar") { const ops = opcoes(); iniciarSessao(ops[E.alt % ops.length]); return; }
  if (a === "voltar-hoje") { voltarAoHoje(); return; }
  if (a === "acompanhar") { E.acompanhar = !E.acompanhar; fraseAtual = null; if (E.acompanhar) carregarSegmentos(E.sessao.item); telaHoje(); grifar(); return; }
  if (a === "comecar-sugestao") { const o = E.sugestao; E.episodio = null; iniciarSessao(o); return; }
  if (a === "gravar-item") { E.erroFala = ""; gravar(E.episodio); return; }
  if (a === "registrar-item") { registrarItem(); return; }
  if (a === "pedir-guia") { const o = E.sessao; E.decisoes["guia:" + o.item] = true; registrar({ evento: "pediu-guia", item: o.item, url: o.url, titulo: o.titulo }); telaHoje(); return; }
  if (a === "marcar-tudo") { document.querySelectorAll("#registro-item input[type=checkbox]").forEach(c => { c.checked = true; }); return; }
  if (a === "fechar-bio") { E.bio = null; telaHoje(); return; }
  if (a === "fechar-episodio") { E.episodio = null; E.sugestao = null; const v = E.voltarPara; E.voltarPara = null; if (v && v !== E.aba && ABAS.includes(v)) location.hash = "#" + v; else telaHoje(); return; }
  if (a === "resumir-apple" || a === "resumir-claude") { resumirFora(a === "resumir-apple" ? "apple" : "claude", t.dataset.cod); return; }
  if (a === "velocidade") {
    const VEL = [1, 1.25, 1.5, 1.75, 2], au = document.getElementById("audio");
    E.vel = VEL[(VEL.indexOf(E.vel) + 1) % VEL.length]; au.playbackRate = E.vel; salvar();
    document.getElementById("mp-vel").textContent = `${String(E.vel).replace(".", ",")}×`; return;
  }
  if (a === "abrir-player") { if (E.tocando) { E.sessao = E.tocando; E.fase = 1; if (!naHoje()) location.hash = "#" + dominioItem(E.tocando.item || ""); telaHoje(); } return; }
  if (a === "recortar") { const au = document.getElementById("audio"); if (au) { E.recortes.push(Math.round(au.currentTime)); telaHoje(); } return; }
  if (a === "terminei") { terminarSessao(false); return; }
  if (a === "parei") { terminarSessao(true); return; }
  if (a === "salvar") {
    const o = E.sessao, nota = document.getElementById("nota")?.value.trim() || "", painel = document.getElementById("feito"); delete E.rascunhos["nota:" + o.id];
    const min = Math.max(1, Math.round(E.seg / 60)), extra = { ...(E.recortes.length ? { recortes: E.recortes } : {}) };
    if (!painel) {   // resumos e transcrições: como antes
      if (!E.parou) delete E.andamento[o.id];
      if (nota) (o.bloco || [o.id]).forEach(id => { E.notas[id] = nota; });
      if (!E.parou && !["resumo", "resumo-audio"].includes(o.tipo)) { (o.bloco || [o.id]).forEach(id => E.feitas.add(id.replace("#txt", ""))); cobrir(o.item); }
      registrar({ evento: E.parou ? "parou" : "terminou", sessao: o.id, ...(o.bloco ? { bloco: o.bloco } : {}), min, formato: E.formato, ...(nota ? { nota } : {}), ...extra, ...(E.posicao != null ? { posicao: E.posicao } : {}) });
      E.fase = 3; telaHoje(); return;
    }
    const feitos = [...painel.querySelectorAll("input[type=checkbox]:checked")].flatMap(c => c.value.split(","));
    const m = parseFloat(String(document.getElementById("ate-min")?.value || "").replace(",", "."));
    let pos = isNaN(m) ? (o.onde === "app" && E.parou ? E.posicao : null) : Math.round(m * 60);
    delete E.andamento[o.id];
    feitos.forEach(id => E.feitas.add(id)); cobrir(o.item);
    if (!ehFluxo(o) && !proximaDoItem(o.item)) E.lidas.add(o.item);
    if (nota) (feitos.length ? feitos : o.bloco || [o.id]).forEach(id => { E.notas[id] = nota; });
    if (feitos.length) registrar({ evento: "terminou", sessao: feitos[0], bloco: feitos, min, formato: E.formato, sugerido: o.id, ...(nota ? { nota } : {}), ...extra });
    // parou no meio de um áudio ou vídeo: guarda o ponto na peça em que parou
    const resto = (o.bloco || [o.id]).map(id => SESS.find(y => y.id === id) || o).filter(x => !E.feitas.has(x.id));
    const onde = pos ? (o.onde === "app" ? resto.find(x => x.de <= pos && (x.ate == null || pos < x.ate)) : resto[0]) : null;
    const pg = parseInt(document.getElementById("ate-pag")?.value), naPag = pg ? pecaDaPagina(o.item, pg) : null;
    const quando = new Date().toISOString();
    if (onde) E.andamento[onde.id] = { pos, quando };
    else if (naPag) E.andamento[naPag.id] = { pag: pg, quando };
    else if (E.parou && !feitos.length) E.andamento[o.id] = { pos: 0, quando };   // parou sem dizer onde: continua "em andamento"
    if (onde || naPag || !feitos.length) registrar({ evento: "parou", sessao: onde ? onde.id : naPag ? naPag.id : o.id, min: feitos.length ? 0 : min, formato: E.formato,
      ...(onde ? { posicao: pos } : {}), ...(naPag ? { pagina: pg } : {}), ...(!feitos.length && nota ? { nota } : {}), ...(feitos.length ? {} : extra) });
    E.fase = 3; telaHoje(); return;
  }
  if (a === "voltar") { E.fase = 0; E.alt = 0; telaHoje(); return; }
  if (a === "guardar-ajustes") {
    E.config.token = document.getElementById("token").value.trim(); E.config.repo = document.getElementById("repo").value.trim() || E.config.repo;
    E.sync = E.config.token ? "Token guardado." : "Sincronização desligada."; salvar(); sincronizar(); enviarFalas(); telaCaixa(); return;
  }
  if (a === "limpar-busca-acervo") { E.buscaAcervo = ""; telaInscricoes(); return; }
  if (a === "sincronizar") { E.sync = "Sincronizando..."; telaCaixa(); sincronizar(); enviarFalas(); return; }
});
document.addEventListener("submit", e => {
  if (e.target.matches("form.pedir")) {
    e.preventDefault();
    const id = e.target.dataset.id, min = Math.max(1, Math.min(120, +e.target.querySelector("input").value || 5));
    E.decisoes["pedido:" + id] = min; registrar({ evento: "pediu", [id.includes(".") ? "sessao" : "item"]: id, minutos: min });
    if (E.aba === "caixa") telaCaixa(); else telaHoje();
    return;
  }
  if (e.target.id === "form-reg") { e.preventDefault(); registrarConteudo(); return; }
  if (e.target.id === "form-busca-acervo") { e.preventDefault(); E.buscaAcervo = document.getElementById("busca-acervo").value.trim(); document.activeElement?.blur?.(); buscarAcervo(E.buscaAcervo); return; }
  if (e.target.id === "form-busca-programa") { e.preventDefault(); E.acervoQ = document.getElementById("busca-programa").value.trim(); E.acervoN = 50; document.activeElement?.blur?.(); telaInscricoes(); return; }
  if (e.target.id === "form-nota") {
    e.preventDefault();
    const v = document.getElementById("nota-feed").value.trim(); delete E.rascunhos.feed; document.activeElement?.blur?.();
    if (!v) return;
    const agora = new Date(), id = agora.toISOString().slice(0, 19).replace(/[-:]/g, "").replace("T", "-");
    E.falas.unshift({ id, texto: v, quando: agora.toISOString(), enviada: true });   // o texto vai no próprio registro
    registrar({ evento: "escreveu", fala: id, texto: v }); telaFeed(); return;
  }
  if (e.target.id !== "form-desejo") return;
  e.preventDefault();
  const v = document.getElementById("desejo").value.trim();
  if (!v) return;
  E.desejos.unshift({ texto: v, quando: new Date().toLocaleDateString("pt-BR") });
  registrar({ evento: "caixa", texto: v }); telaCaixa();
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") document.getElementById("sobre").innerHTML = "";
  if ((e.key === "Enter" || e.key === " ") && e.target.matches(".est-svg")) { e.preventDefault(); abrirFicha(e.target.dataset.ficha); }
});
addEventListener("hashchange", aba);
// tocar na aba Hoje sempre volta para a tela principal do Hoje
["series", "conteudos"].forEach(d => document.querySelector(`nav a[data-aba="${d}"]`).addEventListener("click", () => { E.episodio = null; if (E.fase === 0 && location.hash === "#" + d) telaHoje(); }));

function badgeCaixa() {
  const n = CAIXA.filter(c => !["aprovado", "descartado", "aprovou", "descartou", "mudar"].includes(E.decisoes[c.id] || c.estado) && c.proposta).length;   // só o que pede decisão sua
  const badge = document.getElementById("badge-caixa"); if (badge) { badge.textContent = n; badge.hidden = !n; }
}
let ler = async function (arq, padrao) {
  try { const r = await fetch(arq, { cache: "no-cache" }); if (r.ok) return await r.json(); } catch (_) {}
  return padrao;
};
async function iniciar() {
  carregar();
  // tudo baixa ao mesmo tempo (revisão de 2026-10-19: com sinal fraco, um depois do outro levava ~9 s)
  const pre = Object.fromEntries(["grade", "sessoes", "fluxo", "fundo", "monitor", "apelidos", "livros", "feed", "colecoes", "empresas", "caixa", "plano", "eventos", "guias", "estatisticas", "novidades", "inscricoes", "acervo/indice", "biografias", "semana"]
    .map(k => [k, ler(`dados/${k}.json`, null)]));
  const lerP = ler; ler = (arq, padrao) => { const k = arq.replace(/^dados\/|\.json$/g, ""); const p = pre[k]; if (!p) return lerP(arq, padrao); delete pre[k]; return p.then(v => v ?? padrao); };
  D = await ler("dados/grade.json", null);
  if (!D) { document.getElementById("tela-hoje").innerHTML = `<p class="erro">Não consegui carregar a grade. Abra o app com internet uma vez.</p>`; return; }
  SESS = (await ler("dados/sessoes.json", { sessoes: [] })).sessoes;
  FLUXO = (await ler("dados/fluxo.json", { itens: [] })).itens;
  FUNDO = (await ler("dados/fundo.json", { itens: [] })).itens;
  MONITOR = (await ler("dados/monitor.json", { fontes: [] })).fontes;
  APELIDOS = await ler("dados/apelidos.json", {});
  GUIAS = await ler("dados/guias.json", {});
  RESUMOS_NOV = await ler("dados/novidades.json", {});
  INSCRICOES = await ler("dados/inscricoes.json", null);
  ACERVO_IDX = await ler("dados/acervo/indice.json", null);
  BIO = await ler("dados/biografias.json", null);
  SEMANA = await ler("dados/semana.json", null);
  ESTAT = (await ler("dados/estatisticas.json", { programas: [] })).programas;
  E.feitas = new Set(traduz([...E.feitas]));
  for (const [id, a] of Object.entries(E.andamento)) if (APELIDOS[id]) { delete E.andamento[id]; E.andamento[APELIDOS[id][0]] = a; }
  const livros = await ler("dados/livros.json", { tenho: [] }); TENHO = new Set(livros.ativo ? livros.tenho : []); PRECOS = livros.precos || {};
  const feed = await ler("dados/feed.json", { itens: [] });
  FEED = feed.itens.sort((a, b) => b.quando.localeCompare(a.quando)); CONTEUDOS = feed.conteudos || {};
  const noFeed = new Set(FEED.map(x => x.id)); E.falas = E.falas.filter(f => !noFeed.has(f.id));   // já viraram log
  // coleções entram na mesma lista do Fluxo, sem prazo
  (await ler("dados/colecoes.json", { colecoes: [] })).colecoes.forEach(c => FLUXO.push({ cod: c.cod, fonte: c.nome, titulo: c.nome, autor: c.autor, tipo: "colecao", url: c.site, total: c.total }));
  (await ler("dados/empresas.json", { empresas: [] })).empresas.filter(c => c.total).forEach(c => FLUXO.push({ cod: c.cod, fonte: c.nome, titulo: c.nome, autor: `${c.proprias} textos da empresa · ${c.total - c.proprias} menções em cartas de gestoras`, tipo: "empresa", total: c.total }));
  CAIXA = (await ler("dados/caixa.json", { itens: [] })).itens;
  PLANO = await ler("dados/plano.json", { sessoes: [] });
  IT = Object.fromEntries(D.itens.map(i => [i.cod, i]));
  MAT = Object.fromEntries(D.materias.map(m => [m.cod, m]));
  E.serie = Math.min(Math.max(1, E.serie), D.series.length);
  badgeCaixa();
  // o que você fez em outro aparelho (cópia do registro publicada com o app): vale mesmo sem o token
  const evs = (await ler("dados/eventos.json", { eventos: [] })).eventos;
  if (evs.length) { let m = false; evs.forEach(ev => { m = aplicar(ev) || m; }); if (m) { for (const c of Object.keys(IT)) if (IT[c].serie && SESS.some(y => y.item === c) && !proximaDoItem(c)) E.lidas.add(c); salvar(); badgeCaixa(); } }
  aplicarMovidos();   // Fundo ⇄ Relevantes, mesmo antes da esteira gravar
  aplicarTrazidos();   // episódios antigos trazidos do acervo
  tirarRemovidos();
  aba(); sincronizar(); enviarFalas(); enviarRegistros(); restaurar();
}
iniciar();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
// iPhone e iPad na mesma versão (pedido de 2026-10-24): o app instalado fica dias aberto em segundo plano sem recarregar.
// Ao abrir ou voltar ao app, confere versao.json; se mudou, apaga as cópias guardadas e recarrega uma vez (progresso e notas ficam).
// Ao publicar, suba o número aqui, em versao.json e no CACHE do sw.js.
async function conferirVersao() {
  try {
    if (!navigator.onLine || gravacao || !document.getElementById("audio").paused) return;
    const v = (await (await fetch("versao.json?t=" + Date.now(), { cache: "no-store" })).json()).v;
    if (!v || v === VERSAO || sessionStorage.getItem("recarregou-" + v)) return;
    sessionStorage.setItem("recarregou-" + v, "1");
    salvar();
    if (window.caches) for (const k of await caches.keys()) await caches.delete(k);
    location.reload();
  } catch (err) {}
}
conferirVersao();
document.addEventListener("visibilitychange", () => { if (!document.hidden) conferirVersao(); });
