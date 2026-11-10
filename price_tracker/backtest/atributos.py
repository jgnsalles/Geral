"""Dicionario de atributos do modelo (valor final, com decomposicao) e dispersao por desempenho.
OoL e GCGR sem zROIC, universo point-in-time, ROIC oficial (corrigido em 2026-11-10), esboco (OoL a partir de ROIC 12%).
Grupos: posicoes (acao x trimestre) de cada classe ordenadas pelo excesso do trimestre seguinte sobre o universo:
20% piores, 60% do meio, 20% melhores. Celula = mediana [p25 – p75].
Saidas: backtest/atributos.md, backtest/atributos.csv
Uso: python3 backtest/atributos.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from backtest import load_pit, asof, D  # noqa: E402
import validation_portfolios as vp  # noqa: E402
from validation_core import load_prices  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
KEYS = ('op_income', 'pretax', 'tax', 'equity', 'lt_debt', 'cash', 'net_income', 'ppe', 'assets_cur', 'cur_liab', 'debt_cur', 'goodwill', 'intangibles')

# (coluna, nome, formula, formato) — formato: p = %, x = multiplo, b = US$ bi, n = numero
VARS = [
    ('__s', 'Entradas de mercado', None, None),
    ('price', 'Preço', 'Fechamento no último pregão do trimestre (Yahoo)', 'n'),
    ('dy', 'Dividend yield', 'Soma dos dividendos dos últimos 730 dias ÷ 2 ÷ preço', 'p'),
    ('__s', 'Lucro por ação e crescimento', None, None),
    ('eps', 'EPS (último exercício)', 'Lucro por ação diluído do último 10-K arquivado até a data, ajustado por desdobramentos', 'n'),
    ('pe', 'P/L', 'Preço ÷ EPS (só EPS > 0)', 'x'),
    ('gr_med', 'Crescimento do EPS (métrica do modelo)', 'Mediana das 5 taxas anuais do EPS (mín. 3 válidas; taxa só quando o EPS do ano anterior > 0)', 'p'),
    ('gr_mean', '  · média das 5 taxas', 'Média simples das taxas válidas (referência; não entra no modelo)', 'p'),
    ('gr_std', '  · desvio-padrão das 5 taxas', 'Desvio-padrão populacional das taxas válidas', 'p'),
    ('zgrowth', 'zGrowth', 'Desvio-padrão das taxas ÷ crescimento (mediana). Corte 2,93', 'n'),
    ('__s', 'ROIC (operacionais) — último exercício decomposto', None, None),
    ('ebit', 'Lucro operacional (EBIT)', 'OperatingIncomeLoss', 'b'),
    ('t', 'Alíquota de imposto', 'Imposto ÷ lucro antes do IR, limitada a 0–50%; 21% se não calculável', 'p'),
    ('nopat', 'NOPAT', 'EBIT × (1 − alíquota)', 'b'),
    ('ppe', 'Imobilizado líquido', 'PropertyPlantAndEquipmentNet (utilities/REITs: conceitos próprios)', 'b'),
    ('gw', 'Ágio (goodwill)', 'Goodwill', 'b'),
    ('intang', 'Intangíveis', 'Intangíveis líquidos excluindo ágio', 'b'),
    ('nwc', 'Capital de giro operacional', '(Ativo circulante − caixa) − (passivo circulante − dívida de curto prazo)', 'b'),
    ('cap', 'Capital B (fim do ano)', 'Imobilizado + ágio + intangíveis + capital de giro operacional', 'b'),
    ('cap_avg', 'Capital B médio', '(Capital B do ano + do ano anterior) ÷ 2', 'b'),
    ('sh_ppe', '  · peso do imobilizado no capital', 'Imobilizado ÷ capital B', 'p'),
    ('sh_gwi', '  · peso de ágio + intangíveis no capital', '(Ágio + intangíveis) ÷ capital B', 'p'),
    ('sh_nwc', '  · peso do capital de giro no capital', 'Capital de giro ÷ capital B', 'p'),
    ('cap_g', 'Crescimento do capital B no ano', 'Capital B do ano ÷ do ano anterior − 1', 'p'),
    ('roic_y', 'ROIC do último ano (B)', 'NOPAT ÷ capital B médio (se ≤ 0 ou ausente, usa A)', 'p'),
    ('equity', 'Patrimônio líquido', 'StockholdersEquity', 'b'),
    ('debt', 'Dívida de longo prazo', 'LongTermDebt e equivalentes', 'b'),
    ('cash', 'Caixa', 'Caixa e equivalentes', 'b'),
    ('roic_ay', 'ROIC do último ano (A, reserva)', 'NOPAT ÷ (patrimônio + dívida − caixa); capital operacional se ≤ 0', 'p'),
    ('__s', 'ROE (financeiras e seguradoras de saúde)', None, None),
    ('ni', 'Lucro líquido', 'NetIncomeLoss', 'b'),
    ('roe_y', 'ROE do último ano', 'Lucro líquido ÷ patrimônio', 'p'),
    ('__s', 'Métricas de ROIC do modelo (série de 6 anos resumida)', None, None),
    ('roic_l3', '  · média dos 3 últimos anos', 'Média do ROIC anual dos 3 últimos exercícios', 'p'),
    ('roic_6', '  · média dos 6 anos', 'Média do ROIC anual dos 6 exercícios', 'p'),
    ('roic', 'ROIC (métrica do modelo)', 'Média de (média 3 anos, média 6 anos). Cortes: 12% / 10% (esboço)', 'p'),
    ('roic_std', '  · desvio-padrão dos 6 anos', 'Desvio-padrão populacional do ROIC anual', 'p'),
    ('zroic', 'zROIC', 'Desvio-padrão ÷ ROIC do modelo (desligado nesta versão)', 'n'),
    ('__s', 'Valor justo e retorno esperado', None, None),
    ('g', 'g (crescimento na perpetuidade)', 'Ranking do crescimento entre as ações da data: 7% (1º) a 3,5% (último); financeiras 6,5% a 3%', 'p'),
    ('roic_cap', 'ROIC usado no P/E justo', 'ROIC do modelo limitado a 100%', 'p'),
    ('reinv', '  · taxa de reinvestimento', 'g ÷ ROIC usado', 'p'),
    ('fair_pe', 'P/E justo', '(1 − g ÷ ROIC) ÷ (8,5% − g)', 'x'),
    ('pe_gap', '  · P/E justo ÷ P/L', 'Quanto o múltiplo teria de subir para chegar ao justo', 'x'),
    ('fair_px2', '  · preço justo em 2 anos ÷ preço', 'P/E justo × EPS × (1 + crescimento)² ÷ preço', 'x'),
    ('ret_fair', 'Retorno com convergência ao P/E justo', '√(preço justo em 2 anos ÷ preço) − 1 + dividend yield', 'p'),
    ('ret_const', 'Retorno com múltiplo constante', 'Crescimento + dividend yield', 'p'),
    ('ret', 'Retorno esperado (métrica do modelo)', 'Média dos dois retornos acima. Cortes: 20% / 8%', 'p'),
]


def comps(pit, t, last):
    s = {k: asof(pit.get(k, []), t)[0] for k in KEYS}
    g = lambda k, y: s[k][y][0] if y in s[k] else np.nan
    z = lambda v: 0.0 if not np.isfinite(v) else v
    def capb(y):
        ac, cl, pp = g('assets_cur', y), g('cur_liab', y), g('ppe', y)
        if not (np.isfinite(ac) and np.isfinite(cl) and np.isfinite(pp)): return np.nan, np.nan
        nwc = (ac - z(g('cash', y))) - (cl - z(g('debt_cur', y)))
        return pp + z(g('goodwill', y)) + z(g('intangibles', y)) + nwc, nwc
    y = last
    oi, pt, tx = g('op_income', y), g('pretax', y), g('tax', y)
    tr = min(max(tx / pt, 0), .5) if np.isfinite(pt) and np.isfinite(tx) and pt > 0 else .21
    cb, nwc = capb(y); cp, _ = capb(y - 1)
    cav = (cb + cp) / 2 if np.isfinite(cb) and np.isfinite(cp) else cb
    eq, debt, cash = g('equity', y), g('lt_debt', y), g('cash', y)
    ia = z(eq) + z(debt) - z(cash) if np.isfinite(eq) and eq > 0 else np.nan
    nop = oi * (1 - tr)
    gw, it = z(g('goodwill', y)), z(g('intangibles', y))
    return dict(ebit=oi, t=tr, nopat=nop, ppe=g('ppe', y), gw=gw, intang=it, nwc=nwc, cap=cb, cap_avg=cav,
                sh_ppe=g('ppe', y) / cb if cb and cb > 0 else np.nan, sh_gwi=(gw + it) / cb if cb and cb > 0 else np.nan,
                sh_nwc=nwc / cb if cb and cb > 0 else np.nan, cap_g=cb / cp - 1 if cp and cp > 0 else np.nan,
                roic_y=nop / cav if cav and cav > 0 else (nop / ia if ia and ia > 0 else np.nan),
                equity=eq, debt=debt, cash=cash, roic_ay=nop / ia if ia and ia > 0 else np.nan,
                ni=g('net_income', y), roe_y=g('net_income', y) / eq if eq and eq > 0 else np.nan)


def main():
    f = pd.read_csv(D / 'val_features.csv', parse_dates=['date'])
    first = f[f.pit_member].groupby('date').size(); start = first[first >= 300].index.min()
    dates = sorted(d for d in f.date.unique() if d >= start)
    f = f[f.date.isin(dates) & f.pit_member].assign(zroic=0.0)
    zr = pd.read_csv(D / 'val_features.csv', parse_dates=['date'], usecols=['date', 'ticker', 'zroic']).rename(columns={'zroic': 'zroic_real'})
    adj = load_prices()['adj_close']
    c = vp.classify(f, 'sketch', 'B').merge(zr, on=['date', 'ticker'], how='left')
    px = adj.reindex(pd.DatetimeIndex(dates), method='ffill'); fwd = px.shift(-1) / px - 1
    c['rq'] = [fwd.at[d, t] for d, t in zip(c.date, c.ticker)]
    c = c[c.date < dates[-1]].copy()
    uq = c[c.cat.notna()].groupby('date').rq.mean(); c['ex'] = c.rq - c.date.map(uq)
    c = c[c.cat.isin([OOL, GCGR])].copy()
    RY = [f'ry{i}' for i in range(1, 7)]; GY = [f'gy{i}' for i in range(1, 6)]
    R, G = c[RY], c[GY]
    c['zroic'] = c.zroic_real
    c['gr_med'] = c.growth; c['gr_mean'] = G.mean(axis=1); c['gr_std'] = G.std(axis=1, ddof=0)
    c['roic_l3'] = R.apply(lambda r: np.mean(r.dropna().values[-3:]) if r.notna().any() else np.nan, axis=1)
    c['roic_6'] = R.mean(axis=1); c['roic_std'] = R.std(axis=1, ddof=0)
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c['roic_cap'] = c.roic.clip(upper=1.0); c['reinv'] = c.g / c.roic_cap.where(c.roic_cap > 0)
    c['pe_gap'] = c.fair_pe / c.pe; c['fair_px2'] = c.fair_pe * c.eps * (1 + c.growth) ** 2 / c.price
    cache, rows = {}, []
    for r in c.itertuples():
        if r.ticker not in cache: cache[r.ticker] = load_pit(r.ticker)
        rows.append(comps(cache[r.ticker], r.date, int(r.last_fy)))
    c = pd.concat([c.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    opcols = ['ebit', 't', 'nopat', 'ppe', 'gw', 'intang', 'nwc', 'cap', 'cap_avg', 'sh_ppe', 'sh_gwi', 'sh_nwc', 'cap_g', 'roic_y', 'debt', 'cash', 'roic_ay']
    c.loc[c.fin, opcols] = np.nan
    c.loc[~c.fin, ['roe_y']] = np.nan
    for k in ('ebit', 'nopat', 'ppe', 'gw', 'intang', 'nwc', 'cap', 'cap_avg', 'equity', 'debt', 'cash', 'ni'):
        c[k] = c[k] / 1e9
    # grupos
    def grp(x):
        q20, q80 = x.ex.quantile(.2), x.ex.quantile(.8)
        return pd.Series(np.where(x.ex <= q20, '20% piores', np.where(x.ex >= q80, '20% melhores', '60% do meio')), index=x.index)
    c['grupo'] = c.groupby('cat', group_keys=False).apply(grp)
    c.to_csv(ROOT / 'atributos.csv', index=False)

    def fmt(v, k):
        if not np.isfinite(v): return '—'
        if k == 'p': return f'{v:.0%}' if abs(v) >= 0.1 else f'{v:.1%}'.replace('.', ',')
        if k == 'x': return f'{v:.1f}'.replace('.', ',')
        if k == 'b': return f'{v:.2f}'.replace('.', ',')
        return f'{v:.2f}'.replace('.', ',')
    GR = ['20% piores', '60% do meio', '20% melhores']
    out = ['# Atributos do modelo: fórmulas, decomposição e dispersão por desempenho (OoL e GCGR)\n',
           '> ⚠️ **ROIC:** ROIC oficial (B com reserva em A; seguradoras de saúde e financeiras com ROE; imobilizado de utilities/REITs '
           'corrigido em 2026-11-10). Ainda há casos suspeitos (patrimônio negativo, ROIC > 100% em empresas leves em ativos).\n',
           'Configuração: universo point-in-time (S&P 500 de cada trimestre), sem zROIC, OoL a partir de ROIC 12%. Todos os valores são os que '
           'o modelo via na data (só balanços já arquivados). Séries anuais não aparecem; só o valor final e seus componentes.\n',
           'Grupos: as posições (ação × trimestre) de cada classe foram ordenadas pelo excesso de retorno do trimestre seguinte sobre a média do '
           'universo. Célula = **mediana** [percentil 25 – percentil 75]. Valores em US$ bi quando indicado. Componentes de ROIC só para '
           'operacionais; ROE só para financeiras e seguradoras de saúde.\n']
    hdr = '| Variável | Fórmula | ' + ' | '.join(f'OoL: {g}' for g in GR) + ' | ' + ' | '.join(f'GCGR: {g}' for g in GR) + ' |'
    sep = '|---|---|' + '---|' * 6
    out += ['## Resultado de cada grupo\n', hdr, sep]
    cell = lambda s, k: f'{fmt(s.median(), k)} [{fmt(s.quantile(.25), k)} – {fmt(s.quantile(.75), k)}]' if s.notna().sum() >= 10 else '—'
    row = ['Posições', '']
    for cat in (OOL, GCGR):
        for g in GR: row.append(str(((c.cat == cat) & (c.grupo == g)).sum()))
    out.append('| ' + ' | '.join(row) + ' |')
    row = ['Excesso no trimestre seguinte (a.a.)', 'Retorno da ação − média do universo, × 4']
    for cat in (OOL, GCGR):
        for g in GR:
            s = c[(c.cat == cat) & (c.grupo == g)].ex * 4; row.append(cell(s, 'p'))
    out.append('| ' + ' | '.join(row) + ' |')
    row = ['% financeiras/seguradoras', '']
    for cat in (OOL, GCGR):
        for g in GR: row.append(f"{c[(c.cat == cat) & (c.grupo == g)].fin.mean():.0%}")
    out.append('| ' + ' | '.join(row) + ' |')
    for col, nm, formula, k in VARS:
        if col == '__s':
            out.append(f'| **{nm}** | | | | | | | |'); continue
        row = [nm, formula]
        for cat in (OOL, GCGR):
            for g in GR:
                row.append(cell(c[(c.cat == cat) & (c.grupo == g)][col].replace([np.inf, -np.inf], np.nan), k))
        out.append('| ' + ' | '.join(row) + ' |')
    # diferencas mais fortes: melhores vs piores (mediana) em escala de IQR
    out += ['', '## Onde melhores e piores mais diferem\n',
            'Diferença das medianas (20% melhores − 20% piores) dividida pelo intervalo interquartil da classe inteira. '
            'Acima de ±0,25 já é uma separação perceptível; abaixo de ±0,1 é ruído.\n',
            '| Variável | OoL: diferença ÷ IQR | GCGR: diferença ÷ IQR |', '|---|---|---|']
    eff = []
    for col, nm, _, k in VARS:
        if col == '__s': continue
        e = []
        for cat in (OOL, GCGR):
            x = c[c.cat == cat][col].replace([np.inf, -np.inf], np.nan)
            iqr = x.quantile(.75) - x.quantile(.25)
            b, w = c[(c.cat == cat) & (c.grupo == '20% melhores')][col], c[(c.cat == cat) & (c.grupo == '20% piores')][col]
            e.append((b.median() - w.median()) / iqr if iqr and np.isfinite(iqr) and iqr > 0 else np.nan)
        eff.append((nm.strip(' ·'), e[0], e[1]))
    for nm, a, b in sorted(eff, key=lambda r: -max(abs(np.nan_to_num(r[1])), abs(np.nan_to_num(r[2])))):
        f2 = lambda v: '—' if not np.isfinite(v) else (f'**{v:+.2f}**' if abs(v) >= .25 else f'{v:+.2f}').replace('.', ',')
        out.append(f'| {nm} | {f2(a)} | {f2(b)} |')
    (ROOT / 'atributos.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
