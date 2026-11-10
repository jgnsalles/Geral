<script>
window.dash = (() => {
  const data = {};
  const DEF = { fundo: '1', inicio: '2012-01', fim: '{{END}}', acao: null, pg: 'hoje', aba: 'perf', emp: 'ano', anoEmp: null, graf: 'stack', gestora: null, gid: null, er: null, gsub: 'hoje' };
  let P = { ...DEF }; const draws = new Map(); const hooks = []; let started = false;
  const runOne = (name) => { if (!started) return; const fn = draws.get(name); if (!fn) return; document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => { if (el.closest('[hidden]')) return; try { fn(el); } catch (e) { console.error(name, e); } }); };
  const runAll = () => { if (!started) return; hooks.forEach((f) => { try { f(); } catch (e) { console.error(e); } }); for (const n of draws.keys()) runOne(n); };
  let t; let lastW = window.innerWidth; window.addEventListener('resize', () => { if (window.innerWidth === lastW) return; lastW = window.innerWidth; clearTimeout(t); t = setTimeout(runAll, 150); });
  return {
    data: (id) => ({ status: data[id] ? 'ok' : 'loading', data: data[id] || [] }),
    params: () => ({ ...P }),
    setParams: (o) => { o = window.NB_route ? window.NB_route(o, P) : o; P = { ...P, ...o }; started = true; runAll(); },
    resetParams: () => { P = { ...DEF }; runAll(); },
    draw: (name, fn) => { if (fn) draws.set(name, fn); else runOne(name); },
    onData: (f) => { hooks.push(f); }, refresh: () => {}, setLink: () => {},
    colors: ['#2f6fd0', '#d9822b', '#2a9d8f', '#c4467a', '#7a5cc4', '#8a9a2b', '#b5523b', '#4a90a4'],
    _load: (id, rows) => { data[id] = rows; },
    _run: runAll,
  };
})();
</script>
