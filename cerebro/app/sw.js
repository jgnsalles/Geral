// Offline: guarda o app na primeira visita. Arquivos do app vêm da rede quando ela responde rápido (para pegar
// atualizações) e da cópia guardada quando não há rede ou ela demora. Fontes do Google ficam no cache depois de baixadas uma vez.
const CACHE = "cerebro-v85";
const APP = ["./", "index.html", "estilo.css", "app.js", "manifest.webmanifest", "dados/grade.json", "dados/sessoes.json",
  "icones/icone.svg", "icones/icone-180.png", "icones/icone-192.png", "icones/icone-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(APP.map(u => new Request(u, { cache: "reload" })))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(resp => {
      const copia = resp.clone(); caches.open(CACHE).then(c => c.put(req, copia)); return resp;
    })));
    return;
  }
  if (url.origin !== location.origin) return;
  if (url.pathname.endsWith("versao.json")) return;   // a conferência de versão vai sempre à rede
  if (req.headers.get("range") || /\.(mp3|m4a|webm|ogg)$/i.test(url.pathname)) return;   // áudio vai direto (o player pede pedaços)
  // Rede primeiro, mas sem esperar mais que 1,5 s quando já há cópia guardada (revisão de 2026-10-19: sinal fraco no Uber);
  // a resposta da rede, quando chega, atualiza a cópia para a próxima abertura.
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(guardado => {
    const rede = fetch(req).then(resp => {
      if (resp.ok) { const copia = resp.clone(); caches.open(CACHE).then(c => c.put(req, copia)); }
      return resp;
    });
    if (!guardado) return rede.catch(() => caches.match("index.html"));
    return Promise.race([rede.catch(() => guardado), new Promise(r => setTimeout(() => r(guardado), 1500))]);
  }));
});
