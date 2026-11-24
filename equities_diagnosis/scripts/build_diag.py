"""Monta o Equities Diagnosis: helpers do Carteiras + performance + attribution + passivo."""
import json, re, sys, os
S = sys.argv[1]
code = open(os.path.join(S, 'carteiras_code.txt')).read()
css = re.search(r'<style>\n:root\{.*?</style>', code, re.S).group(0)
L = code.split('\n')
def grab(prefix):
    for l in L:
        if l.startswith(prefix): return l
    raise SystemExit('missing ' + prefix)
helpers = '\n'.join([grab("const $=id=>"), grab("const esc=s=>"), grab("const MES=["), grab("const nf=(v,d=1)=>"), grab("const pct=(v,d=1)=>"),
  grab("const SER=["), grab("const range=(a,b)=>"), grab("function niceStep("), grab("const serStyle=k=>"), grab("const kpis=arr=>")])
i = [k for k, l in enumerate(L) if l.startswith('function chipSelector(')][0]; chip = '\n'.join(L[i:i+5])
i = [k for k, l in enumerate(L) if l.startswith('function sTable(')][0]; j = i
while not L[j].startswith('}'): j += 1
stab = '\n'.join(L[i:j+1])
perf = open(os.path.join(S, 'perf_js.js')).read()
attr = open(os.path.join(S, 'diag/attr_js.js')).read() + '\n' + open(os.path.join(S, 'diag/emp_js.js')).read()
sec = open(os.path.join(S, 'perf_section.html')).read()
sec_style = re.search(r'<style>.*?</style>\n', sec, re.S).group(0); sec_body = sec.replace(sec_style, '')
asec = open(os.path.join(S, 'diag/attr_section.html')).read() + open(os.path.join(S, 'diag/emp_section.html')).read()
P = json.load(open(os.path.join(S, 'perf.json'))); G = json.load(open(os.path.join(S, 'gestoras_perf.json')))
P['gestoras'] = [{k: g[k] for k in ('id', 'n', 'rs', 'cnpj')} for g in G if g['id'] in P['g']]
# gestoras donas de linhas LatAm (attribution/passivo pelo fundo brasileiro) entram com nome
_have = {g['id'] for g in P['gestoras']}
for f in P.get('la', []):
    if f.get('gid') and f['gid'] not in _have:
        src = next((g for g in G if g['id'] == f['gid']), None)
        P['gestoras'].append({'id': f['gid'], 'n': f.get('nm') or (src['n'] if src else f['g']), 'rs': src['rs'] if src else f['g'], 'cnpj': src['cnpj'] if src else ''}); _have.add(f['gid'])
# setores: B3/CVM para ações brasileiras, mapa manual para as estrangeiras dos fundos LatAm
SEC = {k: v['b'] for k, v in json.load(open(os.path.join(S, 'emp/sectors_all.json'))).items()}
EXT = [('MELI', 'Varejo'), ('WALMEX', 'Varejo'), ('FALAB', 'Varejo'), ('CHDRAUI', 'Varejo'), ('CENCOSUD', 'Varejo'), ('LIVEPOL', 'Varejo'),
       ('AC ', 'Consumo'), ('GRUMA', 'Consumo'), ('ARCO', 'Consumo'), ('KOF', 'Consumo'), ('ANDINA', 'Consumo'), ('SPORTS', 'Consumo'), ('FEMSA', 'Consumo'), ('FMX', 'Consumo'), ('BIMBO', 'Consumo'), ('CCU', 'Consumo'),
       ('BOLSA', 'Financials'), ('ITAUCL', 'Financials'), ('COMPARC', 'Financials'), ('BAP', 'Financials'), ('GFNORTE', 'Financials'), ('XP ', 'Financials'), ('BSMX', 'Financials'), ('NU ', 'Financials'), ('RA ', 'Financials'), ('BSAC', 'Financials'), ('CHILE', 'Financials'), ('INBURSA', 'Financials'), ('BBAJIO', 'Financials'), ('IFS', 'Financials'),
       ('Q ', 'Seguros'), ('CPA', 'Transporte'), ('VAPORES', 'Transporte'), ('OMA', 'Transporte'), ('ASUR', 'Transporte'), ('GAP', 'Transporte'), ('PAC', 'Transporte'), ('VOLAR', 'Transporte'), ('LTM', 'Transporte'),
       ('FERREY', 'Industrials'), ('VESTA', 'Real Estate'), ('FIBRAPL', 'Real Estate'), ('FUNO', 'Real Estate'), ('FSHOP', 'Malls'), ('PARAUCO', 'Malls'), ('MALLPLAZA', 'Malls'),
       ('AGUAS', 'Utilities'), ('ECL', 'Utilities'), ('ENELAM', 'Utilities'), ('CMPC', 'Commodities'), ('SQM', 'Commodities'), ('AGRO', 'Commodities'), ('CSAN', 'Commodities'), ('CEMEX', 'Commodities'), ('GMEXICO', 'Commodities'), ('SCCO', 'Commodities'), ('PE&OLES', 'Commodities'), ('VIST', 'Commodities'), ('YPF', 'Commodities'), ('ECOPETL', 'Commodities'), ('BVN', 'Commodities'),
       ('VTEX', 'TMT'), ('SONDA', 'TMT'), ('AMX', 'TMT'), ('GLOB', 'TMT'), ('DLO', 'TMT'), ('STNE', 'Financials'), ('PAGS', 'Financials')]
roots = set()
A = json.load(open(os.path.join(S, 'diag/attr.json'))) if os.path.exists(os.path.join(S, 'diag/attr.json')) else {'roots': []}
for r in A['roots']:
    if r.startswith('X:'):
        c = r[2:] + ' '
        SEC[r] = next((b for k, b in EXT if c.startswith(k)), 'Outros')
MAN = {'GGPS':'Industrials','EZTC':'Real Estate','WEGE':'Industrials','TRIS':'Real Estate','KROT':'Educação','AMBV':'Consumo','OHLB':'Transporte','ROXO':'Financials',
       'TEMP':'Saúde','WSON':'Transporte','PDGR':'Real Estate','RIPI':'Commodities','INBR':'Financials','MELI':'Varejo','M1TA':'TMT','UBBR':'Financials','AMZO':'Varejo',
       'LPSB':'Real Estate','BRTO':'TMT','RDCD':'Financials','MSFT':'TMT','PTIP':'Commodities','XPBR':'Financials','TSMC':'TMT','TMAR':'TMT','BELG':'Commodities',
       'CREM':'Saúde','TBLE':'Utilities','GOGL':'TMT','ARCE':'Commodities','GVTT':'TMT','JHSF':'Real Estate','ITAU':'Financials','GETI':'Utilities','TLPP':'TMT',
       'PRGA':'Consumo','CMET':'Commodities','STOC':'Financials','TNLP':'TMT','AAPL':'TMT','NVDC':'TMT','BERK':'Financials','VISA':'Financials','MSCD':'Financials',
       'TCNO':'TMT','BIDI':'Financials','PAGS':'Financials','STNE':'Financials','VVAR':'Varejo','BTOW':'Varejo','LAME':'Varejo','NATU':'Consumo','HYPE':'Saúde',
       'ESTC':'Educação','SEER':'Educação','YDUQ':'Educação','COGN':'Educação','ANIM':'Educação','CIEL':'Financials','BBSE':'Seguros','PSSA':'Seguros','SULA':'Seguros',
       'IRBR':'Seguros','CXSE':'Seguros','WIZS':'Seguros','EQTL':'Utilities','SBSP':'Utilities','CSMG':'Utilities','SAPR':'Utilities','RAIL':'Transporte','RENT':'Transporte',
       'MOVI':'Transporte','CCRO':'Transporte','ECOR':'Transporte','STBP':'Transporte','AZUL':'Transporte','GOLL':'Transporte','EMBR':'Industrials','RDOR':'Saúde',
       'HAPV':'Saúde','FLRY':'Saúde','QUAL':'Saúde','ODPV':'Saúde','RADL':'Saúde','PNVL':'Saúde','VIVT':'TMT','TIMS':'TMT','TOTS':'TMT','LWSA':'TMT','CASH':'TMT',
       'ITUB':'Financials','BBDC':'Financials','BBAS':'Financials','SANB':'Financials','BPAC':'Financials','ITSA':'Financials','B3SA':'Financials','BRSR':'Financials',
       'ABCB':'Financials','MULT':'Malls','IGTI':'Malls','ALOS':'Malls','BRML':'Malls','LREN':'Varejo','MGLU':'Varejo','AMER':'Varejo','ARZZ':'Varejo','SOMA':'Varejo',
       'AZZA':'Varejo','VIIA':'Varejo','BHIA':'Varejo','PETZ':'Varejo','ASAI':'Varejo','CRFB':'Varejo','PCAR':'Varejo','GMAT':'Varejo','VULC':'Varejo','GRND':'Varejo',
       'ALPA':'Varejo','CEAB':'Varejo','GUAR':'Varejo','ABEV':'Consumo','JBSS':'Consumo','BRFS':'Consumo','MRFG':'Consumo','BEEF':'Consumo','MDIA':'Consumo','CAML':'Consumo',
       'SMTO':'Commodities','SLCE':'Commodities','PETR':'Commodities','PRIO':'Commodities','VALE':'Commodities','GGBR':'Commodities','GOAU':'Commodities','CSNA':'Commodities',
       'USIM':'Commodities','SUZB':'Commodities','KLBN':'Commodities','BRKM':'Commodities','UNIP':'Commodities','CSAN':'Commodities','UGPA':'Commodities','VBBR':'Commodities',
       'RECV':'Commodities','ENEV':'Utilities','CPLE':'Utilities','CMIG':'Utilities','ELET':'Utilities','AXIA':'Utilities','EGIE':'Utilities','TAEE':'Utilities','ALUP':'Utilities',
       'AURE':'Utilities','NEOE':'Utilities','CPFE':'Utilities','ENGI':'Utilities','TRPL':'Utilities','ISAE':'Utilities','CYRE':'Real Estate','MRVE':'Real Estate',
       'EVEN':'Real Estate','DIRR':'Real Estate','CURY':'Real Estate','TEND':'Real Estate','PLPL':'Real Estate','GFSA':'Real Estate','RAPT':'Industrials','POMO':'Industrials',
       'TUPY':'Industrials','PRNR':'Industrials','RANI':'Commodities','KEPL':'Industrials','SHUL':'Industrials','FRAS':'Industrials','MYPK':'Industrials','LEVE':'Industrials','INTB':'TMT'}
for k, v in MAN.items():
    if SEC.get(k, 'Outros') == 'Outros' or k in ('PRNR',): SEC[k] = v
P['sec'] = SEC
TM = json.load(open(os.path.join(S, 'emp/tickermap.json')))
def _ren(r):
    seen = set()
    while r in TM['rename'] and r not in seen: seen.add(r); r = TM['rename'][r]
    return r
P['tmerge'] = {k: _ren(v) for k, v in TM['merge'].items()}
json.dump(P, open(os.path.join(S, 'diag/data.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
json.dump(P, open(os.path.join(S, 'diag/data.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
VIEWS = [('p', 'performance', 'Performance'), ('a', 'attribution', 'Attribution'), ('e', 'empresas', 'Empresas'), ('l', 'passivo', 'Passivo'), ('g', None, 'Gestora')]
tabs = '\n'.join(f'    <button role="tab" id="t-{v}" aria-selected="{"true" if v=="p" else "false"}" data-v="{v}">{l}</button>' for v, h, l in VIEWS)
page = f'''<title>Equities Diagnosis</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Diagnóstico das gestoras de ações brasileiras e LatAm: performance líquida, attribution e passivo, a partir dos dados abertos da CVM e da B3">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap">
{css}
<style>
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.top{{margin-inline:calc(-1 * max(16px,env(safe-area-inset-left,0px)));padding-inline:max(16px,env(safe-area-inset-left,0px))}}
body::before{{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:30;background:var(--plane)}}
.brand b{{font-size:16px;letter-spacing:-.01em}}
.brand b span{{color:var(--accent-ink);font-weight:600;font-size:inherit;display:inline}}
.loading{{padding:60px 0;color:var(--muted)}}
.grid2>*{{min-width:0}}
@media (max-width:980px){{.grid2{{grid-template-columns:minmax(0,1fr)}}}}
.tabs{{flex-wrap:wrap}}
[hidden]{{display:none!important}}
</style>
{sec_style}
<div class="wrap">
<header class="top"><div class="top-in">
  <div class="brand"><b>Equities <span>Diagnosis</span></b><span id="gen">gestoras de ações · Brasil e LatAm</span></div>
  <nav class="tabs" role="tablist">
{tabs}
  </nav>
</div></header>
<p class="loading" id="loading">Carregando dados…</p>
{sec_body}
{asec}
<section id="v-g" hidden>
  <div class="bar">
    <div class="f"><label class="lbl" for="g-q">Gestora</label><input id="g-q" class="gsearch" list="dl-g" placeholder="Buscar gestora…" autocomplete="off"><datalist id="dl-g"></datalist></div>
  </div>
  <div class="ghead"><div><h1 id="g-nome"></h1><div class="sub" id="g-rs"></div></div></div>
  <div class="card" id="g-perf"></div>
</section>
</div>
<script>
{helpers}
{chip}
const S={{sort:{{}}, view:'p', g:null}};
{stab}
function boot(PF){{
const G=PF.gestoras, GI={{}}; G.forEach(g=>GI[g.id]=g);
{perf}
{attr}
// ---------- navegação (#performance, #attribution, #passivo, #g-<id>)
const VH={json.dumps({v: h for v, h, l in VIEWS if h})};
const RENDER={{p:()=>renderP(), a:()=>renderA(), e:()=>renderE(), l:()=>renderL(), g:()=>renderGV()}};
function setView(v){{ S.view=v; {json.dumps([v for v,_,_ in VIEWS])}.forEach(x=>{{ $('v-'+x).hidden=x!==v; $('t-'+x).setAttribute('aria-selected',x===v); }});
  const h=v==='g'&&S.g?`#g-${{S.g}}`:'#'+(VH[v]||'performance'); if(location.hash!==h){{ try{{ history.replaceState(null,'',h); }}catch(e){{}} }} window.scrollTo({{top:0}}); }}
function openG(id){{ const g=PGI[id]||GI[id]; if(!g) return; S.g=id; setView('g'); renderGV(); }}
function renderGV(){{ const g=PGI[S.g]||GI[S.g]; if(!g) return; $('g-q').value=g.n; $('g-nome').textContent=g.n; $('g-rs').innerHTML=esc(g.rs)+(g.cnpj&&!/LLC/.test(g.cnpj)?' · CNPJ '+esc(g.cnpj):'')+` · <a href="#attribution" id="g-ta">attribution</a> · <a href="#passivo" id="g-tl">passivo</a>`; renderGP(g);
  $('g-ta').onclick=e=>{{e.preventDefault(); setView('a'); renderA();}}; $('g-tl').onclick=e=>{{e.preventDefault(); setView('l'); renderL();}}; }}
$('dl-g').innerHTML=PG.filter(g=>PR[g.id]).map(g=>`<option value="${{esc(g.n)}}">${{esc(g.rs)}}</option>`).join('');
$('g-q').addEventListener('change',()=>{{ const q=$('g-q').value.trim().toLowerCase(); const g=PG.find(x=>x.n.toLowerCase()===q)||PG.find(x=>PR[x.id]&&(x.n.toLowerCase().includes(q)||x.rs.toLowerCase().includes(q))); if(g) openG(g.id); }});
document.querySelector('.tabs').addEventListener('click',e=>{{ const b=e.target.closest('button'); if(!b) return; const v=b.dataset.v; if(v==='g'&&!S.g) S.g=(S.psel&&S.psel[0])||PG.find(g=>PR[g.id]).id; setView(v); RENDER[v](); }});
function fromHash(){{ const h=decodeURIComponent(location.hash.slice(1)); if(h.startsWith('g-')&&(PGI[h.slice(2)]||GI[h.slice(2)])){{ openG(h.slice(2)); return; }}
  const v=Object.keys(VH).find(k=>VH[k]===h)||'p'; setView(v); RENDER[v](); }}
window.addEventListener('hashchange',fromHash);
$('loading').hidden=true;
fromHash();
}}
fetch('data.json').then(r=>{{ if(!r.ok) throw new Error(r.status); return r.json(); }}).then(boot).catch(e=>{{ document.getElementById('loading').textContent='Não foi possível carregar os dados ('+e.message+'). Recarregue a página.'; console.error(e); }});
</script>
'''
open(os.path.join(S, 'diag/equities_diagnosis.html'), 'w').write(page)
print('ok', len(page))
