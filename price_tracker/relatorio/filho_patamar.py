"""Ramo N: 'salto de patamar' com os dados do usuário (planilha v4 de 22/11). Mediana do EPS projetado 2026–28 ÷ mediana do EPS 2022–25, anualizado em 3 anos;
comparado com a mediana histórica de crescimento (3 crescimentos 2022–25, os anos que o arquivo tem) e com a mediana da indústria. Saída: dados_filho_patamar.json"""
import sys, json, statistics as st, pathlib
import openpyxl
F = sys.argv[1]
d = openpyxl.load_workbook(F, data_only=True)['Dados']
blk, cur = {}, None
for c in range(2, d.max_column + 1):
    h = d.cell(3, c).value
    if h: cur = h
    if cur: blk.setdefault(cur, []).append((d.cell(4, c).value, c))
rows, ind = {}, {}
for r in range(5, d.max_row + 1):
    t = d[f'A{r}'].value
    if not t: continue
    est = [d.cell(r, c).value for y, c in blk['Estimated EPS AVG'] if y in (2026, 2027, 2028)]
    eps = [d.cell(r, c).value for y, c in blk['EPS Diluted'] if y in (2022, 2023, 2024, 2025)]
    est = [x for x in est if isinstance(x, (int, float))]; eps = [x for x in eps if isinstance(x, (int, float))]
    I = d.cell(r, blk['Cadastro e preço'][2][1]).value
    gh = [eps[i + 1] / eps[i] - 1 for i in range(len(eps) - 1) if eps[i] > 0]
    ghm = st.median(gh) if len(gh) >= 2 else None
    pat = (st.median(est) / st.median(eps)) ** (1 / 3) - 1 if len(est) >= 2 and len(eps) >= 3 and st.median(eps) > 0 and st.median(est) > 0 else None
    mult = st.median(est) / st.median(eps) if pat is not None else None
    rows[t] = dict(pat=pat, hist=ghm, ind=I, mult=mult); ind.setdefault(I, []).append(ghm)
indm = {k: (st.median([x for x in v if x is not None]) if any(x is not None for x in v) else None) for k, v in ind.items()}
for t, v in rows.items():
    v['ind_med'] = indm.get(v['ind'])
    ref = max(v['hist'] if v['hist'] is not None else -9, v['ind_med'] if v['ind_med'] is not None else -9)
    v['alerta'] = bool(v['pat'] is not None and v['pat'] - ref > .15 and v['pat'] > 1.5 * max(ref, .01))
pick = ['LLY', 'MA', 'TDG', 'NVDA', 'MSFT', 'META', 'GOOG', 'AVGO', 'COST', 'V', 'NFLX', 'UBS', 'AMZN', 'ISRG', 'STX']
out = dict(sel={t: rows[t] for t in pick if t in rows}, n_alerta=sum(v['alerta'] for v in rows.values()), n=len(rows))
pathlib.Path(__file__).with_name('dados_filho_patamar.json').write_text(json.dumps(out, ensure_ascii=False, default=float))
for t in pick:
    v = rows.get(t)
    if v and v['pat'] is not None: print(t, round(v['pat'], 3), 'x', round(v['mult'], 2), 'hist', v['hist'] and round(v['hist'], 3), 'ind', v['ind_med'] and round(v['ind_med'], 3), 'ALERTA' if v['alerta'] else '')
print('alertas', out['n_alerta'], 'de', out['n'])
