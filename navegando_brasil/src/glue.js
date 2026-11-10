// ===================== Navegando Brasil: cola entre as duas bases =====================
(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const MES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
  const ymL = (s) => MES[+s.slice(5, 7) - 1] + '/' + s.slice(2, 4);
  // Gestora do Navegando (fundos.csv) -> id da gestora nas carteiras consolidadas (CNPJ raiz)
  const FMAP = { 'Atmos Capital': '10957035', 'Alaska': '11752203', 'Nucleo': '14229647', 'Tempo Capital': '00533944', 'Oceana': '09326542', 'Moat Capital': '18730786', 'Velt': '23862803', 'Una': '05336089', 'Bahia Am Renda Variável': '13143849', 'Jgp': '53980469', 'Squadra': '09267871', 'Bogari': '08947719', 'Navi Capital': '27133825', 'Neo Private Equity': '42462859', 'Bc': '08752088', 'Constellation': '06182127', 'Stk Capital': '11888689', 'Perfin Infra': '43020918', 'Guepardo': '07078144', 'Indie Capital': '14359791' };
  const NICE = { 'Spx Equities': 'SPX', 'Dynamo': 'Dynamo', 'Apex': 'Apex', 'Drys': 'Drys (Equitas)' };
  const slug = (s) => 'nav-' + s.toLowerCase().normalize('NFD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const PERIODS = [
    { k: 'tudo', n: 'Tudo', a: '2012-01', b: '{{END}}' },
    { k: 'dilma1', n: 'Dilma 1', a: '2010-09', b: '2014-09' },
    { k: 'dilma2', n: 'Dilma 2', a: '2014-09', b: '2016-04' },
    { k: 'temer', n: 'Temer', a: '2016-04', b: '2018-09' },
    { k: 'bolsonaro', n: 'Bolsonaro', a: '2018-09', b: '2022-09' },
    { k: 'tb', n: 'Temer–Bolsonaro', a: '2016-04', b: '2022-09' },
    { k: 'lula3', n: 'Lula 3', a: '2022-09', b: '2026-09' },
    { k: 'lula4', n: 'Lula 4', a: '2026-09', b: null },
    { k: 'nd2', n: 'Navegando Dilma 2', a: '2013-12', b: '2018-12' },
  ];
  let FUNDOS = [], GEST = [], GBY = {}, fundGest = {}, DATA0 = '2012-01', DATA1 = '{{END}}';

  const NB = window.NB = {
    fundsOf: (gid) => FUNDOS.filter((f) => fundGest[f.id] === gid).map((f) => f.id),
    gestOf: (fid) => fundGest[fid] || null,
  };

  // ---- rotas: parâmetros extras antes de aplicar
  window.NB_route = (o, P) => {
    o = { ...o };
    if (o.pg === 'fundo') { o.pg = 'gestora'; const fid = String(o.fundo ?? P.fundo); o.fundo = fid; o.gid = NB.gestOf(fid); o.gsub = 'hist'; }
    const gid = o.gid !== undefined ? o.gid : P.gid;
    if (o.gid !== undefined && o.gid) {
      const fs = NB.fundsOf(o.gid);
      if (fs.length && !fs.includes(String(o.fundo ?? P.fundo))) { o.fundo = fs[0]; o.acao = null; }
      CW.setGestora(o.gid, o.keepMonth); delete o.keepMonth;
      if (o.gsub === undefined && o.gid !== P.gid && !CW.GI[o.gid]) o.gsub = 'hist';
      if (o.gsub === undefined && o.gid !== P.gid && CW.GI[o.gid] && P.gsub === 'hist' && !NB.fundsOf(o.gid).length) o.gsub = 'hoje';
    }
    if (o.pg === 'fundo' || (o.fundo !== undefined && o.pg === 'gestora' && o.gsub === undefined)) o.gsub = 'hist';
    if (o.er) CW.S.e = o.er;
    if (o.pg === 'gestora' && !gid) { const first = GEST.find((g) => g.funds.length); o.gid = first.id; const fs = NB.fundsOf(o.gid); o.fundo = fs[0]; CW.setGestora(o.gid); }
    return o;
  };
  const hooks = {
    openG: (id, keep) => { dash.setParams({ pg: 'gestora', gid: id, keepMonth: keep }); scrollTop(); },
    openE: (r) => { dash.setParams({ pg: 'empresa', er: r }); scrollTop(); },
    hasFunds: (id) => NB.fundsOf(id).length > 0,
    rerender: () => dash.setParams({}),
  };
  const scrollTop = () => requestAnimationFrame(() => $('topo').scrollIntoView({ block: 'start' }));

  // ---- hash: #hoje, #comparar, #g-<id>, #a-<ticker>
  let silent = false;
  const toHash = (p) => p.pg === 'gestora' && p.gid ? '#g-' + p.gid + (p.gsub === 'hist' ? '-historico' : '') : p.pg === 'empresa' && p.er ? '#a-' + p.er : '#' + (p.pg || 'hoje');
  const fromHash = () => {
    const h = decodeURIComponent(location.hash.slice(1));
    if (h.startsWith('g-')) { const hist = h.endsWith('-historico'); const id = hist ? h.slice(2, -10) : h.slice(2); if (GBY[id]) return hist ? { pg: 'gestora', gid: id, gsub: 'hist' } : (CW.GI[id] ? { pg: 'gestora', gid: id, gsub: 'hoje' } : { pg: 'gestora', gid: id }); }
    if (h.startsWith('a-') && CW.hasRoot(h.slice(2))) return { pg: 'empresa', er: h.slice(2) };
    if (['hoje', 'comparar', 'gestora', 'empresa'].includes(h)) return { pg: h };
    return null;
  };

  // ---- períodos
  const clip = (a, b) => [a < DATA0 ? DATA0 : a > DATA1 ? DATA1 : a, !b || b > DATA1 ? DATA1 : b < DATA0 ? DATA0 : b];
  const drawPresets = () => {
    const p = dash.params(); const el = $('nb-presets');
    el.innerHTML = PERIODS.map((x) => { const off = x.a >= DATA1; const [a, b] = clip(x.a, x.b); const on = !off && p.inicio === a && p.fim === b;
      return `<button type="button" class="rx-chip" data-k="${x.k}" aria-pressed="${on}"${off ? ' disabled title="Ainda sem dados de performance"' : ''}>${x.n}</button>`; }).join('');
    el.onclick = (e) => { const b = e.target.closest('button[data-k]'); if (!b || b.disabled) return; const x = PERIODS.find((q) => q.k === b.dataset.k); const [a, z] = clip(x.a, x.b); dash.setParams({ inicio: a, fim: z, per: x.k }); };
    const sel = PERIODS.find((x) => { const [a, b] = clip(x.a, x.b); return x.a < DATA1 && p.inicio === a && p.fim === b; });
    const notes = [];
    if (sel && (sel.a < DATA0 || (sel.b || '9') > DATA1)) notes.push(`${sel.n} vai de ${ymL(sel.a)} a ${sel.b ? ymL(sel.b) : 'hoje'}; a série de performance cobre ${ymL(DATA0)} a ${ymL(DATA1)}, então o período foi cortado.`);
    $('nb-period-note').textContent = notes.join(' ');
  };

  // ---- gestora: busca, atalhos e cabeçalho
  const drawGestora = () => {
    const p = dash.params(); const g = GBY[p.gid]; if (!g) return;
    $('gx-q').value = '';
    $('gx-q').placeholder = g.n;
    $('gx-nome').textContent = g.n;
    const fs = g.funds.map((id) => FUNDOS.find((f) => f.id === id));
    $('gx-sub').textContent = fs.length ? `${fs.length === 1 ? 'Fundo acompanhado' : 'Fundos acompanhados'}: ${fs.map((f) => f.fundo).join(' · ')}` : 'Sem fundo entre os 30 acompanhados: só as posições consolidadas da casa.';
    $('gx-quick').innerHTML = '<span class="rx-note" style="align-self:center">Com performance:</span>' + GEST.filter((x) => x.funds.length).sort((a, b) => a.n.localeCompare(b.n)).map((x) => `<button type="button" class="rx-chip" data-g="${x.id}" aria-pressed="${x.id === g.id}">${esc(x.n)}</button>`).join('');
    $('g-fundos-none').hidden = fs.length > 0; $('g-fundos-body').hidden = !fs.length;
    $('g-fundos-h').textContent = fs.length > 1 ? 'Fundos da gestora: performance e attribution' : 'Fundo da gestora: performance e attribution';
  };
  const findG = (q) => { q = q.trim().toLowerCase(); if (!q) return null; return GEST.find((g) => g.n.toLowerCase() === q) || GEST.find((g) => (g.n + ' ' + g.rs).toLowerCase().includes(q)); };

  // ---- carga dos dados
  const NAV = ['fundos', 'serie_mensal', 'posicoes_1', 'posicoes_2', 'precos', 'acoes', 'ibov', 'encerrados'];
  const show = (t) => { $('nb-loading').textContent = t; };
  const boot = async () => {
    try {
      show('Carregando dados…');
      const [cw, ...csv] = await Promise.all([fetch('data/carteiras.json').then((r) => r.json()), ...NAV.map((id) => fetch('data/' + id + '.csv').then((r) => r.text()))]);
      NAV.forEach((id, k) => dash._load(id, d3.csvParse(csv[k].trim())));
      CW.init(cw, hooks);
      FUNDOS = dash.data('fundos').data.map((f) => ({ ...f, id: String(f.id) }));
      const ms = [...new Set(dash.data('serie_mensal').data.map((r) => r.ym))].sort(); DATA0 = ms[0]; DATA1 = ms[ms.length - 1];
      CW.G.forEach((g) => { GBY[g.id] = { id: g.id, n: g.n, rs: g.rs, funds: [] }; });
      FUNDOS.forEach((f) => { let id = FMAP[f.gestora]; if (!id) { id = slug(f.gestora); if (!GBY[id]) GBY[id] = { id, n: NICE[f.gestora] || f.gestora, rs: 'fora do recorte de gestoras independentes das carteiras consolidadas', funds: [] }; } fundGest[f.id] = id; GBY[id].funds.push(f.id); });
      Object.values(GBY).forEach((g) => g.funds.sort((a, b) => (+FUNDOS.find((f) => f.id === b).pl_2018_mi) - (+FUNDOS.find((f) => f.id === a).pl_2018_mi)));
      GEST = Object.values(GBY);
      $('dl-g').innerHTML = GEST.slice().sort((a, b) => a.n.localeCompare(b.n)).map((g) => `<option value="${esc(g.n)}">${g.funds.length ? 'com performance · ' : ''}${esc(g.rs)}</option>`).join('');
      $('gx-q').addEventListener('change', () => { const g = findG($('gx-q').value); if (g) hooks.openG(g.id); });
      document.querySelectorAll('.nb-gtab').forEach((b) => b.addEventListener('click', () => dash.setParams({ gsub: b.dataset.gsub })));
      $('gx-quick').addEventListener('click', (e) => { const b = e.target.closest('[data-g]'); if (b) hooks.openG(b.dataset.g); });
      dash.onData(() => {
        const p = dash.params();
        const gsub = p.gsub || 'hoje';
        $('nb-period').hidden = p.pg === 'hoje' || (p.pg === 'gestora' && gsub === 'hoje');
        $('gs-hoje').hidden = gsub !== 'hoje'; $('gs-hist').hidden = gsub !== 'hist';
        document.querySelectorAll('.nb-gtab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.gsub === gsub)));
        $('g-hist-card').hidden = !CW.GI[p.gid];
        drawPresets();
        if (p.pg === 'hoje') CW.renderR();
        else if (p.pg === 'gestora') { drawGestora(); CW.renderG(); }
        else if (p.pg === 'empresa') CW.renderE();
        const h = toHash(p); if (location.hash !== h) { silent = true; try { history.replaceState(null, '', h); } catch (e) { location.hash = h; } silent = false; }
      });
      window.addEventListener('hashchange', () => { if (silent) return; const o = fromHash(); if (o) dash.setParams(o); });
      $('nb-loading').remove();
      const o = fromHash() || { pg: 'hoje' };
      dash.setParams(o);
    } catch (e) { console.error(e); show('Não foi possível carregar os dados: ' + e.message); }
  };
  boot();
})();
