"""Metrica x retorno, com R2, para todas as acoes da OoL e da GCGR (sem zROIC, universo point-in-time, ROIC oficial corrigido).
Dois niveis: (1) empresa: mediana da metrica nas posicoes x excesso medio a.a. (min. 4 trimestres);
(2) posicao (acao x trimestre): metrica na data x excesso do trimestre seguinte (a.a.).
Metricas e excesso aparados nos percentis 1% e 99% antes do R2 (para um outlier nao dominar).
Le backtest/atributos.csv (gerado por atributos.py). Saidas: backtest/metrica_retorno.md, metrica_retorno_empresa.png, metrica_retorno_posicao.png
Uso: python3 backtest/metrica_retorno.py"""
import pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
ROOT = pathlib.Path(__file__).parent
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
COL = {OOL: '#1f6feb', GCGR: '#e8590c'}; SH = {OOL: 'OoL', GCGR: 'GCGR'}
M = [('growth', 'Crescimento do EPS (G)', 100), ('zgrowth', 'zGrowth', 1), ('roic', 'ROIC do modelo', 100), ('zroic', 'zROIC', 1),
     ('roic_y', 'ROIC do último ano', 100), ('roe_y', 'ROE do último ano (financeiras)', 100), ('roic_std', 'Desvio-padrão do ROIC (6a)', 100),
     ('pe', 'P/L', 1), ('fair_pe', 'P/E justo', 1), ('pe_gap', 'P/E justo ÷ P/L', 1), ('ret', 'Retorno esperado', 100),
     ('ret_fair', 'Retorno com convergência ao P/E justo', 100), ('ret_const', 'Retorno com múltiplo constante', 100), ('dy', 'Dividend yield', 100),
     ('g', 'g (perpetuidade)', 100), ('reinv', 'Reinvestimento (g ÷ ROIC)', 100), ('log_nopat', 'Tamanho: log10 NOPAT (US$ bi)', 1),
     ('t', 'Alíquota de imposto', 100), ('sh_gwi', 'Peso de ágio + intangíveis no capital', 100), ('cap_g', 'Crescimento do capital no ano', 100)]


def clip(s):
    lo, hi = s.quantile(.01), s.quantile(.99)
    return s.clip(lo, hi)


def fit(x, y):
    m = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 10: return np.nan, np.nan, np.nan, len(x)
    x, y = clip(x), clip(y)
    b, a = np.polyfit(x, y, 1); r = np.corrcoef(x, y)[0, 1]
    return r ** 2, b, a, len(x)


def main():
    c = pd.read_csv(ROOT / 'atributos.csv', parse_dates=['date'])
    c['log_nopat'] = np.log10((c.nopat.where(c.fin == False, c.ni)).where(lambda s: s > 0))  # noqa: E712
    c['ex_a'] = c.ex * 4
    cols = [m[0] for m in M]
    E, F = {}, {}
    for cat in (OOL, GCGR):
        x = c[c.cat == cat]; n = x.groupby('ticker').size()
        a = x.groupby('ticker')[cols].median(); a['ex_a'] = x.groupby('ticker').ex.mean() * 4
        E[cat] = a[n >= 4]
        f0 = x.sort_values('date').groupby('ticker')[cols].first(); f0['ex_a'] = a.ex_a
        F[cat] = f0[n >= 4]
    P = {cat: c[c.cat == cat] for cat in (OOL, GCGR)}
    rows = []
    for col, nm, k in M:
        r = {'Métrica': nm}
        for cat in (OOL, GCGR):
            r2, b, _, n = fit(E[cat][col], E[cat].ex_a); r[f'{SH[cat]} emp'] = (r2, b, n)
            r2f, bf, _, nf = fit(F[cat][col], F[cat].ex_a); r[f'{SH[cat]} f0'] = (r2f, bf, nf)
            r2p, bp, _, npos = fit(P[cat][col], P[cat].ex_a); r[f'{SH[cat]} pos'] = (r2p, bp, npos)
        rows.append(r)
    f2 = lambda t: '—' if not np.isfinite(t[0]) else (f"**{t[0]:.3f}** ({'+' if t[1] > 0 else '−'})" if t[0] >= 0.02 else f"{t[0]:.3f} ({'+' if t[1] > 0 else '−'})").replace('.', ',')
    out = ['# Métrica × retorno, com R² (OoL e GCGR, EUA, point-in-time)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). ROIC, zROIC, P/E justo, reinvestimento e retorno esperado dependem dele.\n',
           'Configuração: sem zROIC, OoL a partir de ROIC 12%. Retorno = excesso sobre a média do universo, anualizado. '
           '**Empresa**: mediana da métrica nas posições da empresa na classe × excesso médio (mín. 4 trimestres; '
           f'OoL {len(E[OOL])} empresas, GCGR {len(E[GCGR])}). **Posição**: métrica na data × excesso do trimestre seguinte '
           f'(OoL {len(P[OOL])}, GCGR {len(P[GCGR])} posições). Métrica e retorno aparados em 1%/99%. '
           'Entre parênteses, o sinal da inclinação (+ = métrica maior, retorno maior). Em negrito, R² ≥ 0,02.\n',
           '**Escala do R²:** 0,01 = a métrica explica 1% da variação do retorno. Em retorno de ações, um R² de 0,01 por posição já é '
           'relevante economicamente; por empresa (poucas observações), valores abaixo de ~0,04 não se distinguem de acaso.\n',
           '**Atenção ao R² por empresa (mediana):** a mediana da métrica inclui trimestres posteriores à compra. Se a ação sobe, o P/L sobe junto, '
           'então P/L, P/E justo ÷ P/L e retorno com convergência ficam mecanicamente ligados ao retorno. Por isso há a coluna **na primeira compra** '
           '(métrica no primeiro trimestre da empresa na classe), que não tem esse viés.\n',
           '| Métrica | OoL: empresa, na 1ª compra | GCGR: empresa, na 1ª compra | OoL: empresa, mediana | GCGR: empresa, mediana | OoL: por posição | GCGR: por posição |',
           '|---|---|---|---|---|---|---|']
    rows.sort(key=lambda r: -max(np.nan_to_num(r['OoL f0'][0]), np.nan_to_num(r['GCGR f0'][0])))
    for r in rows:
        out.append(f"| {r['Métrica']} | {f2(r['OoL f0'])} | {f2(r['GCGR f0'])} | {f2(r['OoL emp'])} | {f2(r['GCGR emp'])} | {f2(r['OoL pos'])} | {f2(r['GCGR pos'])} |")
    (ROOT / 'metrica_retorno.md').write_text('\n'.join(out))
    print('\n'.join(out))

    for lvl, data, fn, alpha, s in (('empresa', F, 'metrica_retorno_empresa.png', .6, 18), ('posicao', P, 'metrica_retorno_posicao.png', .12, 4)):
        fig, axs = plt.subplots(4, 5, figsize=(24, 18), dpi=110)
        for ax, (col, nm, k) in zip(axs.ravel(), M):
            for cat in (OOL, GCGR):
                d = data[cat][[col, 'ex_a']].replace([np.inf, -np.inf], np.nan).dropna()
                if len(d) < 10: continue
                x, y = clip(d[col]), clip(d.ex_a)
                r2, b, a, n = fit(d[col], d.ex_a)
                ax.scatter(x * k, y * 100, s=s, alpha=alpha, color=COL[cat], edgecolor='none')
                xs = np.linspace(x.min(), x.max(), 50)
                ax.plot(xs * k, (a + b * xs) * 100, color=COL[cat], lw=2.2, label=f'{SH[cat]}: R² = {r2:.3f}'.replace('.', ','))
            ax.axhline(0, color='black', lw=.7); ax.grid(alpha=.3); ax.set_title(nm, fontsize=10); ax.legend(fontsize=8, loc='upper right')
            ax.tick_params(labelsize=8)
        for ax in axs[:, 0]: ax.set_ylabel('Excesso sobre o universo (% a.a.)', fontsize=9)
        ttl = ('Cada ponto = uma empresa (métrica na primeira compra × excesso médio na classe)' if lvl == 'empresa'
               else 'Cada ponto = uma posição (métrica na data × excesso do trimestre seguinte, anualizado)')
        fig.suptitle(f'Métrica × retorno — OoL (azul) e GCGR (laranja), sem zROIC, universo point-in-time. {ttl}. Aparado em 1%/99%.', fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, .97)); fig.savefig(ROOT / fn); plt.close(fig)


if __name__ == '__main__':
    main()
