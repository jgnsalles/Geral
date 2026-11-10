"""Teste fora da amostra da estrategia candidata congelada (2026-11-10) nas acoes A da China.
Fundamentos anuais do Eastmoney com a data de divulgacao (usa so o que ja tinha sido divulgado na data); precos do Yahoo, em yuan.
Regra congelada: ROIC >= 12%, crescimento do lucro >= 15%, P/L >= 4, sem ciclicos e vestuario; as 20 de maior retorno esperado;
peso pela raiz do valor de mercado com teto de 10%; trimestral. Mesmos parametros dos EUA (WACC 8,5%, g 7% -> 3,5%).
Diferencas forcadas pelos dados (fixadas antes de rodar):
  - crescimento = mediana de 5 taxas anuais do LUCRO LIQUIDO (como no Brasil), nao do lucro por acao;
  - ROIC = lucro operacional x (lucro liquido / lucro antes do IR) / [patrimonio + (passivo total - fornecedores - adiantamentos) - caixa];
    financeiras (bancos, corretoras, outras financeiras): ROE;
  - setores pela classificacao Shenwan nivel 2 do Eastmoney (mapeamento em CYC e APP abaixo); sem dividendos no retorno esperado.
Universo: valor de mercado >= 5 bi de yuan, preco >= 2 yuan, giro mediano >= 50 mi de yuan/dia.
Saidas: china/resultado.md, china/resultado.png. Uso: python3 china/backtest_cn.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent; D = ROOT / 'data'
sys.path.insert(0, str(ROOT.parent / 'backtest')); sys.path.insert(0, str(ROOT.parent))
import engine  # noqa: E402
import combos as cb  # noqa: E402
import top_n  # noqa: E402
from pesos import run_weighted  # noqa: E402
from backtest import stats, rebalance_dates  # noqa: E402

CYC = {'油气开采Ⅱ', '油服工程', '炼化及贸易', '煤炭开采', '焦炭Ⅱ', '工业金属', '普钢', '特钢Ⅱ', '冶钢原料', '小金属', '能源金属', '贵金属',
       '农化制品', '一般零售', '航空机场', '摩托车及其他', '游戏Ⅱ', '保险Ⅱ', '医药商业', '文娱用品'}
APP = {'服装家纺', '纺织制造', '饰品'}
FIN = {'银行Ⅱ', '证券Ⅱ', '保险Ⅱ', '多元金融'}


def load():
    rows = []
    for y in range(2008, 2026):
        a = pd.read_csv(D / f'stock_yjbb_em_{y}.csv', dtype={'股票代码': str})
        b = pd.read_csv(D / f'stock_zcfz_em_{y}.csv', dtype={'股票代码': str})
        c = pd.read_csv(D / f'stock_lrb_em_{y}.csv', dtype={'股票代码': str})
        a = a.rename(columns={'股票代码': 'code', '每股收益': 'eps', '净利润-净利润': 'ni', '所处行业': 'ind', '最新公告日期': 'notice'})
        b = b.rename(columns={'股票代码': 'code', '资产-货币资金': 'cash', '负债-应付账款': 'ap', '负债-预收账款': 'adv', '负债-总负债': 'liab',
                              '股东权益合计': 'equity'})
        c = c.rename(columns={'股票代码': 'code', '营业利润': 'op', '利润总额': 'pretax', '净利润': 'ni_tot'})
        m = a[['code', 'eps', 'ni', 'ind', 'notice']].merge(b[['code', 'cash', 'ap', 'adv', 'liab', 'equity']], on='code', how='left') \
            .merge(c[['code', 'op', 'pretax', 'ni_tot']], on='code', how='left')
        m['fy'] = y; rows.append(m)
    F = pd.concat(rows)
    F['code'] = F.code.str.zfill(6)
    F['notice'] = pd.to_datetime(F.notice, errors='coerce')
    F['known'] = F.notice.fillna(pd.to_datetime(F.fy.astype(str) + '-04-30') + pd.DateOffset(years=1))
    for k in ('eps', 'ni', 'cash', 'ap', 'adv', 'liab', 'equity', 'op', 'pretax', 'ni_tot'):
        F[k] = pd.to_numeric(F[k], errors='coerce')
    F['fin'] = F.ind.isin(FIN)
    keep = F.pretax.where(F.pretax > 0)
    F['nopat'] = F.op * (F.ni_tot / keep).clip(0.5, 1.0).fillna(0.75)
    cap = F.equity + (F.liab - F.ap.fillna(0) - F.adv.fillna(0)) - F.cash.fillna(0)
    F['roic_y'] = np.where(F.fin, F.ni / F.equity.where(F.equity > 0), F.nopat / cap.where(cap > 0))
    F['yt'] = F.code.map(lambda c: c + ('.SS' if c[0] == '6' else '.SZ'))
    return F.sort_values(['code', 'fy'])


def main():
    F = load()
    read = lambda n: pd.read_csv(D / f'prices_{n}.csv.gz', index_col=0, parse_dates=True)
    close, adj, vol = read('close'), read('adj_close'), read('volume')
    spl = read('splits').fillna(0)
    dv = (close * vol).rolling(63, min_periods=20).median()
    dates = [d for d in rebalance_dates(close) if d >= pd.Timestamp('2013-06-28')]
    byc = {c: g.set_index('fy') for c, g in F.groupby('yt')}
    rows = []
    for d in dates:
        for yt, g in byc.items():
            if yt not in close: continue
            p = close.at[d, yt]
            if not np.isfinite(p) or p < 2 or not (dv.at[d, yt] >= 5e7): continue
            k = g[g.known <= d]
            if k.empty: continue
            last = k.index.max()
            if (d - pd.Timestamp(f'{last}-12-31')).days > 550: continue
            r0 = k.loc[last]
            ni = k.ni
            rates = [ni.get(y) / ni.get(y - 1) - 1 if pd.notna(ni.get(y)) and pd.notna(ni.get(y - 1)) and ni.get(y - 1) > 0 else np.nan
                     for y in range(last - 4, last + 1)]
            ok = [x for x in rates if np.isfinite(x)]
            growth = float(np.median(ok)) if len(ok) >= 3 else np.nan
            zg = engine.cv(rates, growth) if np.isfinite(growth) else np.nan
            ro = [k.roic_y.get(y, np.nan) for y in range(last - 5, last + 1)]
            roic = engine.roic_metric(ro); zr = engine.cv(ro, roic)
            if not (pd.notna(r0.eps) and r0.eps != 0 and pd.notna(r0.ni)): continue
            sh = r0.ni / r0.eps
            s = spl[yt] if yt in spl else pd.Series(dtype=float)
            s = s[(s > 0) & (s.index > pd.Timestamp(f'{last}-12-31'))]
            mcap = p * sh * (float(np.prod(s.values)) if len(s) else 1.0)
            if not (mcap >= 5e9): continue
            rows.append(dict(date=d, ticker=yt, fin=bool(r0.fin), price=mcap, eps=r0.ni, dy=0.0, growth=growth, zgrowth=zg, roic=roic, zroic=zr,
                             ind=r0.ind, mcap=mcap, last_fy=last))
        print(d.date(), sum(1 for x in rows if x['date'] == d), flush=True)
    f = pd.DataFrame(rows)
    parts = []
    for d, x in f.groupby('date'):
        x = x.copy(); x['g'] = cb.g_rank(x, 0.07)
        r = x.roic.clip(upper=1.0)
        x['fair_pe'] = np.where(r > 0, (1 - x.g / r) / (0.085 - x.g), np.nan)
        base = x.fair_pe * x.eps * (1 + x.growth) ** 2 / x.price
        x['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + x.dy; x['ret_const'] = x.growth + x.dy
        both = x.ret_fair.notna() & x.ret_const.notna(); x['ret'] = np.where(both, (x.ret_fair + x.ret_const) / 2, x.growth)
        parts.append(x)
    c = pd.concat(parts)
    c['pe'] = c.price / c.eps.where(c.eps > 0)
    c['cyc'] = c.ind.isin(CYC); c['app'] = c.ind.isin(APP)
    cnt = c.groupby('date').size(); start = cnt[cnt >= 100].index.min()
    c = c[c.date >= start]; dates = [d for d in dates if d >= start]
    el = c[~c.cyc & ~c.app & (c.roic >= .12) & (c.growth >= .15) & (c.pe >= 4)].copy()
    navs, nn, chosen = {}, {}, None
    for n in (20, 15, 10):
        ch = pd.concat([g.sort_values(['ret', 'roic'], ascending=False).head(n) for _, g in el.groupby('date')])
        navs[f'Top {n} — raiz com teto'] = run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), 2 / n) for d, g in ch.groupby('date')}, adj, dates)
        navs[f'Top {n} — peso igual'] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in ch.groupby('date')}, adj, dates)
        nn[f'Top {n} — raiz com teto'] = nn[f'Top {n} — peso igual'] = ch.groupby('date').size().mean()
        if n == 20: chosen = ch
    for lab, m in (('Elegíveis de qualidade (peso igual)', el), ('Universo (peso igual)', c)):
        navs[lab] = run_weighted({d: pd.Series(1.0, index=g.ticker) for d, g in m.groupby('date')}, adj, dates); nn[lab] = m.groupby('date').size().mean()
    navs['Elegíveis de qualidade (raiz com teto 10%)'] = run_weighted({d: top_n.cap(pd.Series(np.sqrt(g.mcap.values), index=g.ticker), 0.1) for d, g in el.groupby('date')}, adj, dates)
    nn['Elegíveis de qualidade (raiz com teto 10%)'] = nn['Elegíveis de qualidade (peso igual)']
    bm = pd.read_csv(D / 'indices.csv', index_col=0, parse_dates=True)
    for t, lab in (('000300.SS', 'CSI 300'), ('000905.SS', 'CSI 500')):
        s = bm[t].loc[dates[0]:dates[-1]].dropna(); navs[lab] = s / s.iloc[0]
    U = navs['Universo (peso igual)']; MU = U.resample('ME').last(); SU = stats(U)['CAGR']
    def win(nav, y):
        M = nav.resample('ME').last(); a = M / M.shift(12 * y); b = (MU / MU.shift(12 * y)).reindex(a.index); k = a.notna() & b.notna()
        return (a[k] > b[k]).mean() if k.any() else np.nan
    pc = lambda v: '—' if pd.isna(v) else f'{v:.1%}'.replace('.', ',')
    pp = lambda v: '—' if pd.isna(v) else f'{v * 100:+.1f}'.replace('.', ',')
    out = ['# Teste fora da amostra: ações A da China\n',
           '> ⚠️ **O ROIC pode estar errado** — aqui reconstruído com os poucos itens disponíveis em lote (ver as diferenças forçadas pelos dados).\n',
           f'Período {pd.Timestamp(dates[0]):%m/%Y} a {pd.Timestamp(dates[-1]):%m/%Y}, em yuan, trimestral, sem custos nem impostos. Regra congelada, sem ajuste. '
           f'Universo (mediana por data): {int(c.groupby("date").size().median())} ações com valor de mercado ≥ 5 bi de yuan e giro ≥ 50 mi/dia; '
           f'elegíveis de qualidade (mediana): {int(el.groupby("date").size().median())}.\n',
           '**Diferenças forçadas pelos dados (fixadas antes de rodar):** crescimento pelo lucro líquido (não por ação); ROIC = lucro operacional após '
           'imposto ÷ (patrimônio + passivo exceto fornecedores e adiantamentos − caixa); setores pela classificação Shenwan; sem dividendos no retorno esperado. '
           'Empresas que saíram da bolsa podem não ter preço no Yahoo.\n',
           '| Carteira | Ações (média) | Retorno anual | vs universo | Pior queda | Janelas 3a > universo | Janelas 5a > universo |', '|---|---|---|---|---|---|---|']
    for k, nav in navs.items():
        s = stats(nav)
        out.append(f"| {k} | {'—' if k not in nn else f'{nn[k]:.0f}'} | **{pc(s['CAGR'])}** | {pp(s['CAGR'] - SU)} | {pc(s['MaxDD'])} | {win(nav, 3):.0%} | {win(nav, 5):.0%} |")
    out += ['', '**Setores das escolhas da Top 20 (% das posições):** ' + ', '.join(f'{k} {v:.0%}' for k, v in chosen.ind.value_counts(normalize=True).head(10).items()),
            '', f'**Top 20 de hoje ({chosen.date.max():%m/%Y}):** ' + ', '.join(chosen[chosen.date == chosen.date.max()].ticker)]
    (ROOT / 'resultado.md').write_text('\n'.join(out)); print('\n'.join(out))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.ticker as mt
    fig, ax = plt.subplots(figsize=(11.5, 6), dpi=140)
    sty = {'Top 20 — raiz com teto': ('#1f6feb', '-', 2.6), 'Elegíveis de qualidade (raiz com teto 10%)': ('#2da44e', '-', 1.6),
           'Elegíveis de qualidade (peso igual)': ('#2da44e', ':', 1.4), 'Universo (peso igual)': ('#57606a', '--', 1.8),
           'CSI 300': ('#000000', '--', 1.6), 'CSI 500': ('#bf8700', '--', 1.4)}
    for k, (col, ls, lw) in sty.items():
        s = navs[k]; ax.plot(s.index, (s - 1) * 100, color=col, ls=ls, lw=lw, label=f'{k} (' + pc(stats(s)['CAGR']) + ' a.a.)')
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:,.0f}%'.replace(',', '.'))); ax.grid(alpha=.3); ax.legend(fontsize=8, loc='upper left')
    ax.set_title('China (ações A): estratégia candidata congelada × universo e índices — retorno total acumulado em yuan', fontsize=10)
    fig.tight_layout(); fig.savefig(ROOT / 'resultado.png'); plt.close(fig)


if __name__ == '__main__':
    main()
