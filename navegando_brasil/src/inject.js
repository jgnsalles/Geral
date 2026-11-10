
  // ===================== Navegando Brasil: acréscimos dentro do módulo do Navegando =====================
  window.NBX = { build: () => build(), model: (id) => model(id), ready: () => ready(), allMonths: () => allMonths() };
  // Códigos antigos do Navegando -> raiz da empresa nas carteiras consolidadas (trocas de código: ELET -> AXIA etc.)
  const NAV2CW = { ALSO: 'ALOS', PETZ: 'AUAU', CESP: 'AURE', ELET: 'AXIA', SOMA: 'AZZA', BRIT: 'BRST', EMBR: 'EMBJ', TRPL: 'ISAE', BRFS: 'MBRF', CCRO: 'MOTV', NINJ: 'REAG', GUAR: 'RIAA', ODPV: 'SAUD', MEGA: 'SRNA', OMGE: 'SRNA', CCPR: 'SYNE', TIMP: 'TIMS', LVTC: 'WDCN', BKBR: 'ZAMP' };
  window.NB_cwRoot = (tk) => NAV2CW[tk.slice(0, 4)] || tk.slice(0, 4);

  // Fundo: só os fundos da gestora escolhida
  dash.draw('sel-fundo', (sel) => {
    if (!ready()) { sel.replaceChildren(); return; }
    const C = build(); const ids = window.NB ? NB.fundsOf(dash.params().gid) : C.fundos.map((f) => f.id);
    const fs = C.fundos.filter((f) => ids.includes(f.id));
    fill(sel, fs.map((f) => [f.id, f.fundo]), params().fundo);
    sel.closest('label').hidden = fs.length <= 1;
    sel.onchange = () => dash.setParams({ fundo: sel.value, acao: null });
  });

  // Empresa: a ação no período e o que os 30 fundos fizeram
  dash.draw('emp-perf', (el) => {
    if (!status(el)) return;
    el.replaceChildren();
    const r = dash.params().er; if (!r) return;
    const C = build(); const [ini, fim] = window_();
    const months = allMonths().filter((m) => m >= ini && m <= fim);
    const root = window.NB_cwRoot;
    const tks = [...C.ret.keys()].filter((tk) => root(tk) === r);
    const note = (t) => { const p = document.createElement('p'); p.className = 'rx-note'; p.textContent = t; el.append(p); };
    // fluxo e peso dos 30 fundos
    const ibov = new Map(); const pl = new Map();
    for (const [fid, rows] of C.serie) { const m = new Map(); rows.forEach((x) => { if (Number.isFinite(x.PL)) m.set(x.ym, x.PL); if (Number.isFinite(x.ri) && !ibov.has(x.ym)) ibov.set(x.ym, x.ri); }); pl.set(fid, m); }
    const flow = new Map(months.map((m) => [m, 0])); let anyPos = false;
    for (const [fid, rows] of C.pos) for (const x of rows) {
      if (root(x.tk) !== r || x.ym < ini || x.ym > fim) continue; anyPos = true;
      if (x.ym > ini && Number.isFinite(x.t) && Number.isFinite(pl.get(fid)?.get(x.ym))) flow.set(x.ym, flow.get(x.ym) + x.t * pl.get(fid).get(x.ym));
    }
    if (!tks.length && !anyPos) { note('Nenhum dos 30 fundos acompanhados teve esta ação entre ' + ymLabel(ini) + ' e ' + ymLabel(fim) + ', e não há série de preço para ela (a série de performance vai de jan/2012 a {{END_L}}).'); return; }
    const tk = tks.slice().sort((a, b) => months.filter((m) => Number.isFinite(C.ret.get(b).get(m))).length - months.filter((m) => Number.isFinite(C.ret.get(a).get(m))).length)[0];
    let ga = 1, gi = 1; const rows = months.map((m, k) => { if (k) { const x = tk ? C.ret.get(tk).get(m) : NaN; if (Number.isFinite(x)) ga *= 1 + x; const y = ibov.get(m); if (Number.isFinite(y)) gi *= 1 + y; } return { ym: m, d: ymDate(m), a: tk ? ga - 1 : NaN, i: gi - 1, f: flow.get(m) / 1 }; });
    // por fundo
    const per = [];
    C.fundos.forEach((f) => { const m = model(f.id); if (!m) return; const ss = m.stocks.filter((s) => root(s.tk) === r); if (!ss.length) return;
      per.push({ f, contrib: d3.sum(ss, (s) => s.contrib), wmed: d3.sum(ss, (s) => s.wmed), wmax: d3.max(ss, (s) => s.wmax), buy: d3.sum(ss, (s) => s.buy), sell: d3.sum(ss, (s) => s.sell) }); });
    per.sort((a, b) => b.contrib - a.contrib);
    // números
    const kv = document.createElement('div'); kv.className = 'rx-split';
    const add = (l, v, s) => { const d = document.createElement('div'); d.className = 'rx-kv'; const a = document.createElement('span'); a.textContent = l; const b = document.createElement('span'); b.textContent = v; if (s) b.className = s > 0 ? 'rx-pos' : 'rx-neg'; d.append(a, b); kv.append(d); };
    const last = rows[rows.length - 1];
    add('Retorno ' + (tk || r) + ' no período', tk ? fPct(last.a) : '—', last.a);
    add('Ibovespa no período', fPct(last.i), last.i);
    add('Fundos que tiveram', String(per.length) + ' de ' + C.fundos.length);
    add('Compras − vendas dos fundos', L.format('+,.0f')(d3.sum(rows, (x) => x.f)) + ' mi', d3.sum(rows, (x) => x.f));
    el.append(kv);
    // gráfico
    const box = document.createElement('div'); box.className = 'rx-chart tall'; el.append(box);
    const H = 340, { svg, w } = svgFor(box, H); const t = tip(box);
    const ml = 52, mr = 14, h1 = 200, top = 10, gap = 34, h2 = H - top - h1 - gap - 26;
    const x = d3.scaleUtc(d3.extent(rows, (q) => q.d), [ml, w - mr]);
    const y1 = d3.scaleLinear(d3.extent(rows.flatMap((q) => [q.a, q.i]).filter(Number.isFinite).concat([0])), [top + h1, top]).nice();
    svg.append('g').attr('transform', `translate(${ml},0)`).call(d3.axisLeft(y1).ticks(5).tickFormat(L.format('+.0%')).tickSize(-(w - ml - mr))).call(axisClean).call((g) => g.select('.domain').remove());
    svg.append('path').datum(rows).attr('d', d3.line().defined((q) => Number.isFinite(q.i)).x((q) => x(q.d)).y((q) => y1(q.i))).attr('fill', 'none').attr('stroke', 'var(--cds-chart-muted)').attr('stroke-width', 2).attr('stroke-dasharray', '4 3');
    if (tk) svg.append('path').datum(rows).attr('d', d3.line().defined((q) => Number.isFinite(q.a)).x((q) => x(q.d)).y((q) => y1(q.a))).attr('fill', 'none').attr('stroke', dash.colors[0]).attr('stroke-width', 2.25);
    const t2 = top + h1 + gap; const fx = d3.max(rows, (q) => Math.abs(q.f)) || 1;
    const y2 = d3.scaleLinear([-fx, fx], [t2 + h2, t2]).nice();
    svg.append('text').attr('x', ml).attr('y', t2 - 8).attr('fill', 'var(--color-fg-muted)').style('font-size', '11px').text('Compras − vendas dos 30 fundos no mês (R$ mi)');
    svg.append('g').attr('transform', `translate(${ml},0)`).call(d3.axisLeft(y2).ticks(3).tickFormat(L.format(',.0f')).tickSize(-(w - ml - mr))).call(axisClean).call((g) => g.select('.domain').remove());
    const bw = Math.max(1, (w - ml - mr) / rows.length - 1);
    svg.append('g').selectAll('rect').data(rows.filter((q) => q.f)).join('rect').attr('x', (q) => x(q.d) - bw / 2).attr('width', bw).attr('y', (q) => y2(Math.max(0, q.f))).attr('height', (q) => Math.abs(y2(q.f) - y2(0))).attr('fill', (q) => q.f > 0 ? 'var(--color-ok)' : 'var(--color-bad)');
    svg.append('g').attr('transform', `translate(0,${H - 22})`).call(d3.axisBottom(x).ticks(Math.max(3, Math.floor(w / 90))).tickFormat(yearTickFmt).tickSizeOuter(0)).call(axisClean);
    const rule = svg.append('line').attr('y1', top).attr('y2', H - 22).attr('stroke', 'var(--color-fg-muted)').style('display', 'none');
    const bis = d3.bisector((q) => q.d).center;
    const mv = (ev) => { const [px, py] = d3.pointer(ev, box); const q = rows[bis(rows, x.invert(px * w / box.clientWidth))]; if (!q) return; rule.style('display', null).attr('x1', x(q.d)).attr('x2', x(q.d));
      showTip(box, t, px, py, ymLabel(q.ym), [[dash.colors[0], tk || r, Number.isFinite(q.a) ? fPct(q.a) : '—'], ['var(--cds-chart-muted)', 'Ibovespa', fPct(q.i)], [null, 'Fundos no mês', L.format('+,.0f')(q.f) + ' mi']]); };
    svg.append('rect').attr('x', ml).attr('y', 0).attr('width', Math.max(0, w - ml - mr)).attr('height', H).attr('fill', 'transparent').on('pointermove', mv).on('pointerdown', mv).on('pointerleave', () => { rule.style('display', 'none'); t.hidden = true; });
    const lg = document.createElement('div'); lg.className = 'rx-legend'; lg.innerHTML = `<span><i style="background:${dash.colors[0]}"></i>${tk || r}</span><span><i style="background:var(--cds-chart-muted)"></i>Ibovespa</span><span><i style="background:var(--color-ok)"></i>compras líquidas</span><span><i style="background:var(--color-bad)"></i>vendas líquidas</span>`; el.append(lg);
    // tabela por fundo
    if (!per.length) { note('Nenhum dos 30 fundos teve a ação no período.'); return; }
    const tb = document.createElement('div'); tb.className = 'rx-tablebox'; el.append(tb);
    const tbl = document.createElement('table'); tbl.className = 'rx-table'; tb.append(tbl);
    tbl.innerHTML = '<thead><tr><th>Fundo</th><th>Contribuição</th><th>Peso médio</th><th>Peso máx.</th><th>Comprou</th><th>Vendeu</th></tr></thead>';
    const body = tbl.createTBody();
    per.forEach((p) => { const tr = body.insertRow(); tr.dataset.key = p.f.id;
      const c0 = tr.insertCell(); c0.innerHTML = `<b>${p.f.fundo}</b> <span class="co">${p.f.gestora}</span>`; c0.style.whiteSpace = 'normal';
      [[fPct2(p.contrib), sc(p.contrib)], [fPct0(p.wmed)], [fPct0(p.wmax)], [L.format('.1%')(p.buy)], [L.format('.1%')(-p.sell)]].forEach(([v, cl]) => { const c = tr.insertCell(); c.textContent = v; if (cl) c.className = cl; }); });
    body.onclick = (ev) => { const tr = ev.target.closest('tr[data-key]'); if (tr) { dash.setParams({ pg: 'fundo', fundo: tr.dataset.key, acao: per.find((p) => p.f.id === tr.dataset.key) ? (C.fundos && [...(model(tr.dataset.key)?.stocks || [])].filter((s) => root(s.tk) === r).sort((a, b) => b.wmed - a.wmed)[0]?.tk) : null }); requestAnimationFrame(() => document.getElementById('compras-vendas')?.scrollIntoView({ behavior: 'smooth', block: 'start' })); } };
    note('Contribuição = quanto a ação somou ao retorno do fundo no período (peso do mês anterior × retorno, encadeado). Comprou e vendeu: soma dos fluxos mensais em % do PL. Toque num fundo para ver as compras e vendas dele contra o preço.');
  });

  // Comparar: risco
  dash.draw('cmp-risk', (el) => {
    if (!status(el)) return; el.replaceChildren(); const ms = cmpModels(); if (!ms || !ms.length) return;
    const stats = (S, key) => { const r = S.slice(1).map((q) => q[key]).filter(Number.isFinite); const n = r.length; if (n < 3) return null;
      const mu = d3.mean(r), sd = d3.deviation(r); let g = 1, pk = 1, dd = 0; r.forEach((x) => { g *= 1 + x; pk = Math.max(pk, g); dd = Math.min(dd, g / pk - 1); });
      return { vol: sd * Math.sqrt(12), ann: Math.pow(g, 12 / n) - 1, dd, worst: d3.min(r), n }; };
    const beta = (S) => { const pr = S.slice(1).filter((q) => Number.isFinite(q.rf) && Number.isFinite(q.ri)); if (pr.length < 6) return NaN; const mf = d3.mean(pr, (q) => q.rf), mi = d3.mean(pr, (q) => q.ri);
      return d3.sum(pr, (q) => (q.rf - mf) * (q.ri - mi)) / d3.sum(pr, (q) => (q.ri - mi) ** 2); };
    const tbl = document.createElement('table'); tbl.className = 'rx-table'; el.append(tbl);
    tbl.innerHTML = '<thead><tr><th>Fundo</th><th>Retorno ao ano</th><th>Volatilidade ao ano</th><th>Maior queda</th><th>Pior mês</th><th>Beta</th><th>Exposição média</th></tr></thead>';
    const body = tbl.createTBody(); const fmt = L.format('.1%');
    const row = (nome, cor, s, b, ex) => { const tr = body.insertRow(); const c0 = tr.insertCell(); c0.innerHTML = cor ? `<i style="display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;background:${cor}"></i>${nome}` : nome;
      [s ? [fPct(s.ann), sc(s.ann)] : ['—'], s ? [fmt(s.vol)] : ['—'], s ? [fmt(s.dd), 'rx-neg'] : ['—'], s ? [fmt(s.worst), 'rx-neg'] : ['—'], [Number.isFinite(b) ? L.format('.2f')(b) : '—'], [Number.isFinite(ex) ? fmt(ex) : '—']].forEach(([v, cl]) => { const c = tr.insertCell(); c.textContent = v; if (cl) c.className = cl; }); };
    const CC = ['#3b6fd8', '#e07b39', '#2a9d8f', '#d9679a'];
    ms.forEach((m, k) => row(m.fundo.fundo, CC[k], stats(m.S, 'rf'), beta(m.S), d3.mean(m.S, (q) => q.el)));
    row('Ibovespa', 'var(--cds-chart-muted)', stats(ms[0].S, 'ri'), 1, NaN);
  });

  // Comparar: attribution da média dos 30 fundos + maiores e piores individuais
  dash.draw('mkt-attr', (el) => {
    if (!status(el)) return; el.replaceChildren();
    const C = build(); const root = window.NB_cwRoot; const [ini, fim] = window_();
    const agg = new Map(); const pairs = []; let nF = 0;
    C.fundos.forEach((f) => {
      const m = model(f.id); if (!m || m.S.length < 2 || !m.S.some((q, k) => k && Number.isFinite(q.rf))) return; nF++;
      const by = new Map();
      m.stocks.forEach((s) => { const r = root(s.tk); const o = by.get(r) || { r, c: 0, w: 0, tk: s.tk, wbig: -1, ret: NaN }; o.c += s.contrib; o.w += s.wmed; if (s.wmed > o.wbig) { o.wbig = s.wmed; o.tk = s.tk; o.ret = s.ret; } by.set(r, o); });
      by.forEach((o) => {
        if (Math.abs(o.c) > 1e-5 || o.w > 0.001) pairs.push({ f, ...o });
        const a = agg.get(o.r) || { r: o.r, tk: o.tk, c: 0, n: 0, w: 0, ret: o.ret, wbig: -1 }; a.c += o.c; if (o.w > 0.005) a.n++; a.w += o.w; if (o.wbig > a.wbig) { a.wbig = o.wbig; a.tk = o.tk; a.ret = o.ret; } agg.set(o.r, a);
      });
    });
    const avg = [...agg.values()].map((a) => ({ ...a, c: a.c / nF, wHold: a.n ? a.w / a.n : NaN }));
    const pp_ = (x) => fPP(x * 100) + ' p.p.';
    const nm = (tk) => (C.nome.get(tk) || '');
    const lead = document.createElement('p'); lead.className = 'rx-note';
    lead.textContent = `${nF} fundos com cota entre ${ymLabel(ini)} e ${ymLabel(fim)}. Média: quanto cada empresa somou, em média, ao retorno dos ${nF} fundos (zero para quem não teve). Individual: o par fundo × empresa que mais somou ou tirou.`;
    el.append(lead);
    const grid = document.createElement('div'); grid.className = 'nb-attr-grid'; el.append(grid);
    const block = (title, cols, rows, onRow) => {
      const box = document.createElement('div'); box.className = 'nb-attr';
      const h = document.createElement('h3'); h.textContent = title; box.append(h);
      const wrap = document.createElement('div'); wrap.className = 'rx-tablebox rx-sumbox'; box.append(wrap); const tb = document.createElement('table'); tb.className = 'rx-table'; wrap.append(tb);
      tb.innerHTML = '<thead><tr>' + cols.map((c) => `<th${c.l ? ' style="text-align:left"' : ''}>${c.t}</th>`).join('') + '</tr></thead>';
      const body = tb.createTBody();
      rows.forEach((r, k) => { const tr = body.insertRow(); tr.dataset.k = k; cols.forEach((c) => { const td = tr.insertCell(); const v = c.f(r); td.innerHTML = v.h ?? ''; if (v.cls) td.className = v.cls; if (c.l) td.style.textAlign = 'left'; }); });
      body.onclick = (ev) => { const tr = ev.target.closest('tr[data-k]'); if (tr) onRow(rows[+tr.dataset.k]); };
      grid.append(box);
    };
    const emp = (r) => ({ h: `<b>${r.tk}</b><br><span class="co">${nm(r.tk)}</span>` });
    const goE = (r) => { dash.setParams({ pg: 'empresa', er: r.r }); document.getElementById('topo')?.scrollIntoView({ block: 'start' }); };
    const goF = (r) => { dash.setParams({ pg: 'fundo', fundo: r.f.id, acao: r.tk }); requestAnimationFrame(() => document.getElementById('compras-vendas')?.scrollIntoView({ behavior: 'smooth', block: 'start' })); };
    const colsA = [{ t: 'Empresa', l: 1, f: emp }, { t: 'Contribuição média', f: (r) => ({ h: pp_(r.c), cls: sc(r.c) }) }, { t: 'Fundos', f: (r) => ({ h: String(r.n) }) }, { t: 'Peso médio*', f: (r) => ({ h: Number.isFinite(r.wHold) ? fPct0(r.wHold) : '—' }) }, { t: 'Retorno da ação', f: (r) => ({ h: Number.isFinite(r.ret) ? fPct(r.ret) : '—', cls: sc(r.ret) }) }];
    const colsI = [{ t: 'Fundo', l: 1, f: (r) => ({ h: `<b>${r.f.fundo.replace(/ Master\b/, '')}</b>` }) }, { t: 'Empresa', l: 1, f: emp }, { t: 'Contribuição', f: (r) => ({ h: pp_(r.c), cls: sc(r.c) }) }, { t: 'Peso médio', f: (r) => ({ h: fPct0(r.w) }) }, { t: 'Retorno da ação', f: (r) => ({ h: Number.isFinite(r.ret) ? fPct(r.ret) : '—', cls: sc(r.ret) }) }];
    const N = 12;
    block('Onde acertaram juntos', colsA, avg.filter((a) => a.c > 0).sort((a, b) => b.c - a.c).slice(0, N), goE);
    block('Onde erraram juntos', colsA, avg.filter((a) => a.c < 0).sort((a, b) => a.c - b.c).slice(0, N), goE);
    block('Maiores acertos individuais', colsI, pairs.filter((p) => p.c > 0).sort((a, b) => b.c - a.c).slice(0, N), goF);
    block('Maiores erros individuais', colsI, pairs.filter((p) => p.c < 0).sort((a, b) => a.c - b.c).slice(0, N), goF);
    const n2 = document.createElement('p'); n2.className = 'rx-note';
    n2.textContent = '* Peso médio entre os fundos que tiveram a empresa com pelo menos 0,5% do PL. Contribuição = peso do mês anterior × retorno da ação, encadeado pelo crescimento da cota, em pontos percentuais do retorno do fundo no período. ON, PN e units da mesma empresa somadas. Toque numa empresa para abrir a página dela, ou num par fundo × empresa para ver as compras e vendas daquele fundo.';
    el.append(n2);
  });
