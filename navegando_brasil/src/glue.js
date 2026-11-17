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
    // retorno total (com dividendos) de um emissor em n meses até ym (limitado ao último preço da série)
    ret: (root, ym, n) => { const end = ym > DATA1 ? DATA1 : ym; const tk = tkOf(root, end); if (!tk) return null; const s = PR.get(tk); let g = 1;
      for (let k = 0; k < n; k++) { const m = addM(end, -k), v = s.get(m); if (v == null) return null; g *= 1 + v; } return g - 1; },
    retEnd: (ym) => ymL(ym > DATA1 ? DATA1 : ym),
    // retorno em 12 meses do maior fundo acompanhado da gestora (até o fim da série de performance)
    fundRet: (gid, ym) => { const fs = NB.fundsOf(gid); if (!fs.length) return null; const end = ym > DATA1 ? DATA1 : ym; const s = SR.get(fs[0]); if (!s) return null; let g = 1;
      for (let k = 0; k < 12; k++) { const v = s.get(addM(end, -k)); if (v == null) return null; g *= 1 + v; } return g - 1; },
  };
  const addM = (ym, k) => { let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + k; while (m < 1) { m += 12; y--; } while (m > 12) { m -= 12; y++; } return y + '-' + String(m).padStart(2, '0'); };
  let PR = new Map(), SR = new Map(); const TKC = {};
  const tkOf = (root, end) => { if (TKC[root] !== undefined) return TKC[root];
    const cands = [...PR.keys()].filter((t) => t.slice(0, 4) === root);
    let best = null, bn = -1; cands.forEach((t) => { const n = PR.get(t).size; if (n > bn) { bn = n; best = t; } }); return (TKC[root] = best); };
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

  // ---- ano a ano do fundo: retorno, Ibovespa, diferença, melhor e pior ação do ano (attribution)
  let POS = null;
  const drawYears = (p) => {
    const fid = String(p.fundo || ''); const card = $('nb-yr-card'); const s = SR.get(fid); card.hidden = !s || !NB.fundsOf(p.gid).length; if (card.hidden) return;
    if (!POS) { POS = new Map(); ['posicoes_1', 'posicoes_2'].forEach((n) => dash.data(n).data.forEach((r) => { if (r.contrib === '') return; const id = String(r.id); if (!POS.has(id)) POS.set(id, []); POS.get(id).push([r.ym, r.tk, +r.contrib]); })); }
    const ib = new Map(dash.data('serie_mensal').data.filter((r) => String(r.id) === fid && r.ret_ibov !== '').map((r) => [r.ym, +r.ret_ibov]));
    const Y = {}; [...s.entries()].forEach(([ym, v]) => { const y = ym.slice(0, 4); const o = Y[y] || (Y[y] = { y, f: 1, i: 1, n: 0, last: ym, c: {} }); o.f *= 1 + v; o.i *= 1 + (ib.get(ym) || 0); o.n++; if (ym > o.last) o.last = ym; });
    (POS.get(fid) || []).forEach(([ym, tk, c]) => { const o = Y[ym.slice(0, 4)]; if (o) o.c[tk] = (o.c[tk] || 0) + c; });
    const fund = (dash.data('fundos').data.find((f) => String(f.id) === fid) || {}).fundo || '';
    $('nb-yr-s').textContent = fund + ' · retorno da cota no ano contra o Ibovespa; melhor e pior ação pela contribuição no ano';
    const nm = (tk) => esc(tk);
    $('nb-yr').innerHTML = '<thead><tr><th style="text-align:left">Ano</th><th>Fundo</th><th>Ibovespa</th><th>Diferença</th><th style="text-align:left">Melhor ação</th><th style="text-align:left">Pior ação</th></tr></thead><tbody>' +
      Object.values(Y).sort((a, b) => b.y.localeCompare(a.y)).map((o) => { const cs = Object.entries(o.c).sort((a, b) => b[1] - a[1]); const bst = cs[0], wst = cs[cs.length - 1];
        const pc = (v) => `<span class="${v > 0 ? 'rx-pos' : v < 0 ? 'rx-neg' : 'zero'}">${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 1 })}%</span>`;
        const pp = (v) => `<span class="${v > 0 ? 'rx-pos' : 'rx-neg'}">${v > 0 ? '+' : '−'}${Math.abs(v * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 1 })}</span>`;
        return `<tr><td style="text-align:left">${o.y}${o.n < 12 ? ` <span class="zero">(${o.n} ${o.n === 1 ? 'mês' : 'meses'})</span>` : ''}</td><td>${pc(o.f - 1)}</td><td>${pc(o.i - 1)}</td><td>${pp(o.f - o.i)} p.p.</td>` +
          `<td style="text-align:left">${bst && bst[1] > 0 ? nm(bst[0]) + ' ' + pp(bst[1]) : '<span class="zero">–</span>'}</td><td style="text-align:left">${wst && wst[1] < 0 ? nm(wst[0]) + ' ' + pp(wst[1]) : '<span class="zero">–</span>'}</td></tr>`; }).join('') + '</tbody>';
  };

  // ---- regra: toda tabela é ordenável por qualquer coluna (as que não têm ordenação própria)
  const SORTS = {};
  const cellVal = (td) => { if (!td) return null; let t = td.innerText.replace(/\s+/g, ' ').trim(); if (!t || t === '–' || t === '-') return null;
    if (/^nova\b/i.test(t)) return 1e12; if (/^zerou\b/i.test(t)) return -1e12;
    const m = t.replace(/^[−-]?\s*R\$\s*/, (x) => (/[−-]/.test(x) ? '−' : '')).match(/^([+−-]?)\s*([\d.]+(?:,\d+)?)\s*(bi|mi|mil|%|p\.p\.)?/);
    if (m) { let v = parseFloat(m[2].replace(/\./g, '').replace(',', '.')); if (m[1] === '−' || m[1] === '-') v = -v; if (m[3] === 'bi') v *= 1e9; else if (m[3] === 'mi') v *= 1e6; else if (m[3] === 'mil') v *= 1e3; return v; }
    return t.toLowerCase(); };
  const sortRows = (tbl, i, dir) => { const tb = tbl.tBodies[0]; if (!tb) return; const rows = [...tb.rows];
    rows.sort((a, b) => { const x = cellVal(a.cells[i]), y = cellVal(b.cells[i]); if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
      if (typeof x === 'number' && typeof y === 'number') return dir * (x - y); if (typeof x === 'number') return -1; if (typeof y === 'number') return 1; return dir * x.localeCompare(y, 'pt-BR'); });
    rows.forEach((r) => tb.appendChild(r)); };
  const label = (th) => th.innerText.replace(/[↑↓]/g, '').replace(/\s+/g, ' ').trim();
  // celular: as linhas viram cartões e o cabeçalho some; um seletor "Ordenar por" faz o mesmo papel
  const sortSel = (tbl, ths, own, key) => { const host = tbl.closest('.rx-tablebox') || tbl.parentElement; let wrap = host.previousElementSibling;
    if (!wrap || !wrap.classList || !wrap.classList.contains('nb-sortsel')) { wrap = document.createElement('label'); wrap.className = 'nb-sortsel'; host.parentElement.insertBefore(wrap, host); }
    const cols = ths.map((th, i) => [i, label(th)]).filter(([, l]) => l);
    wrap.innerHTML = '<span>Ordenar por</span><select aria-label="Ordenar por">' + (own ? '<option value="">—</option>' + cols.map(([i, l]) => `<option value="${i}">${esc(l)}</option>`).join('')
      : cols.flatMap(([i, l]) => [`<option value="${i}:-1">${esc(l)} ↓</option>`, `<option value="${i}:1">${esc(l)} ↑</option>`]).join('')) + '</select>';
    const sel = wrap.querySelector('select');
    if (!own && SORTS[key]) sel.value = SORTS[key].i + ':' + SORTS[key].dir;
    sel.onchange = () => { if (own) { const th = (tbl.tHead || {}).rows ? tbl.tHead.rows[0].cells[+sel.value] : null; if (th) (th.querySelector('button') || th).click(); return; }
      const [i, dir] = sel.value.split(':').map(Number); SORTS[key] = { i, dir }; sortRows(tbl, i, dir); ths.forEach((h, j) => h.dataset.arrow = j === i ? (dir < 0 ? ' ↓' : ' ↑') : ''); }; };
  const enhance = (tbl, k) => { const head = tbl.tHead; if (!head || head.dataset.s) return; head.dataset.s = '1'; const ths = [...head.rows[0].cells];
    const own = !!tbl.dataset.own || ths.some((th) => th.querySelector('button') || th.hasAttribute('aria-sort') || th.dataset.k);
    const key = tbl.id || 'tb' + k; sortSel(tbl, ths, own, key); if (own) return;
    ths.forEach((th, i) => { th.classList.add('nb-srt'); th.onclick = () => { const st = SORTS[key] || {}; const dir = st.i === i ? -st.dir : (i === 0 ? 1 : -1); SORTS[key] = { i, dir }; sortRows(tbl, i, dir);
      ths.forEach((h, j) => h.dataset.arrow = j === i ? (dir < 0 ? ' ↓' : ' ↑') : ''); }; });
    const st = SORTS[key]; if (st && st.i < ths.length) { sortRows(tbl, st.i, st.dir); ths.forEach((h, j) => h.dataset.arrow = j === st.i ? (st.dir < 0 ? ' ↓' : ' ↑') : ''); } };
  new MutationObserver(() => document.querySelectorAll('#dash-root table.rx-table').forEach(enhance)).observe(document.getElementById('dash-root'), { childList: true, subtree: true });

  // ---- carga dos dados
  const NAV = ['fundos', 'serie_mensal', 'posicoes_1', 'posicoes_2', 'precos', 'acoes', 'ibov', 'encerrados'];
  const show = (t) => { $('nb-loading').textContent = t; };
  const boot = async () => {
    try {
      show('Carregando dados…');
      // arquivos grandes vão em partes (PARTS, gerado no build); cada parte é conferida e baixada de novo se falhar
      // os dados vêm embutidos na página (gzip + base64), sem downloads
      const canGz = typeof DecompressionStream === 'function';
      if (!canGz) throw new Error('este navegador não descomprime dados (atualize o iOS/navegador)');
      const getFile = async (name) => {
        const el = document.getElementById('nbd-' + name); if (!el) throw new Error(name + ' não está na página');
        const s = atob(el.textContent.trim()); const u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
        el.remove();
        return new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
      };
      const cwTxt = await getFile('carteiras.json'); const setTxt = await getFile('setores.json'); const csv = []; for (const id of NAV) csv.push(await getFile(id + '.csv'));
      let cw; try { cw = JSON.parse(cwTxt); } catch (e) { throw new Error('carteiras.json chegou incompleto (' + cwTxt.length + ' caracteres): ' + e.message); }
      NAV.forEach((id, k) => dash._load(id, d3.csvParse(csv[k].trim())));
      cw.setores = JSON.parse(setTxt);
      dash.data('precos').data.forEach((r) => { const v = +r.ret_total; if (r.ret_total === '' || !isFinite(v)) return; if (!PR.has(r.tk)) PR.set(r.tk, new Map()); PR.get(r.tk).set(r.ym, v); });
      dash.data('serie_mensal').data.forEach((r) => { const v = +r.ret_fundo; if (r.ret_fundo === '' || !isFinite(v)) return; const id = String(r.id); if (!SR.has(id)) SR.set(id, new Map()); SR.get(id).set(r.ym, v); });
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
        else if (p.pg === 'gestora') { drawGestora(); CW.renderG(); if (gsub === 'hist') drawYears(p); }
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
