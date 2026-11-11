"""Carteiras de HOJE (ultima data de rebalanceamento), EUA e Brasil, por classe nova: OoL, GCGR, OoL High ROIC, OoL High Growth.
Regra de montagem (a da candidata congelada aplicada dentro de cada classe): P/L >= 4; as 20 de maior retorno esperado (ou menos, se a classe
tiver menos); peso pela raiz do valor de mercado com teto de 10%. Saida: backtest/hoje_classes.md e backtest/hoje_classes.csv"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / 'brasil'))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
import engine  # noqa: E402
import oos_congelado as oc  # noqa: E402
from backtest import D  # noqa: E402
from pesos import DUAL  # noqa: E402

OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
CLS = ['Opportunity of Lifetime', 'Good Companies, Great Returns', 'OoL High ROIC (ROIC > 30%)', 'OoL High Growth (EPS > 30%)']


def masks(cat, ok, roic, growth):
    o = (cat == OOL) & ok
    return {CLS[0]: o, CLS[1]: (cat == GCGR) & ok, CLS[2]: o & (roic > .3), CLS[3]: o & (growth > .3)}


def top(x):
    x = x.assign(firm=x.ticker.map(lambda t: DUAL.get(t, t))).sort_values('mcap', ascending=False).drop_duplicates('firm')  # uma classe de acao por empresa
    x = x[x.pe >= 4].sort_values(['ret', 'roic'], ascending=False).head(20).copy()
    x['peso'] = top_n.cap(pd.Series(np.sqrt(x.mcap.values), index=x.index), 0.10).values if len(x) else []
    return x


def us():
    f, _ = bm.base_data(); c = bm.classify_new(f); c = c[c.date == c.date.max()].copy()
    c['mcap'] = top_n.mcap_us(c, c) * c.groupby(c.ticker.map(lambda t: DUAL.get(t, t))).ticker.transform('size'); c['pe'] = c.price / c.eps.where(c.eps > 0)
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    c['nome'] = c.ticker.map(u.name).fillna(c.ticker.map(lambda t: u.name.get(DUAL.get(t, t)))).fillna(c.ticker.map(lambda t: u.name.get(next((k for k, v in DUAL.items() if v == t), None)))).fillna(c.ticker.map({'TTD': 'The Trade Desk', 'GOOGL': 'Alphabet Inc.'})).fillna(c.ticker); c['setor'] = c.industry
    return c, masks(c.cat, ~c.excluded, c.roic, c.growth)


def br():
    BD = ROOT.parent / 'brasil' / 'data'
    u = pd.read_csv(BD / 'universe.csv'); idx = u.set_index('yf')
    b = pd.read_csv(BD / 'classes_pit.csv', parse_dates=['date']); b = b[b.date == b.date.max()].copy()
    r = b.roic.clip(upper=1.0); b['fair_pe'] = np.where(r > 0, (1 - b.g / r) / (oc.WACC - b.g), np.nan)
    base = b.fair_pe * b.eps * (1 + b.growth) ** 2 / b.price
    b['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + b.dy; b['ret_const'] = b.growth + b.dy
    both = b.ret_fair.notna() & b.ret_const.notna(); b['ret'] = np.where(both, (b.ret_fair + b.ret_const) / 2, b.growth)
    saved = dict(engine.TH); engine.TH.update({'zGrowth': 2.93, 'Roic_Hi': 0.12, 'Roic_Lo': 0.10, 'zRoic': 0.7})
    try: n = engine.classify(b.assign(zroic=0.0))
    finally: engine.TH.clear(); engine.TH.update(saved)
    b['cat'] = np.where(n.code.isna(), None, n.category)
    tk = b.ticker.map(idx.ticker)
    ok = ~(b.ticker.map(idx.Setor_Atividade).isin(oc.CYC_SECTORS) | tk.isin(oc.CYC_TICKERS) | tk.isin(oc.APPAREL))
    fund = pd.read_csv(BD / 'fund.csv.gz', parse_dates=['DT_REFER', 'DT_RECEB']); fund['fy'] = fund.DT_REFER.dt.year
    sh = []
    for rr in b.itertuples():
        ff = fund[(fund.CD_CVM == idx.Codigo_CVM.get(rr.ticker)) & (fund.DT_RECEB <= rr.date) & (fund.fy == rr.last_fy)]
        ni = ff.sort_values('DT_RECEB').ni.iloc[-1] if len(ff) else np.nan
        sh.append(ni / rr.eps if pd.notna(ni) and rr.eps and abs(rr.eps) > 1e-6 and np.sign(ni) == np.sign(rr.eps) else np.nan)
    b['mcap'] = (b.price * pd.Series(sh, index=b.index)).where(lambda s: s > 0); b['mcap'] = b.mcap.fillna(b.mcap.median())
    b['pe'] = b.price / b.eps.where(b.eps > 0)
    b['nome'] = b.ticker.map(idx.Nome_Empresarial).astype(str).str.title().str[:32]; b['setor'] = b.ticker.map(idx.Setor_Atividade)
    b['ticker'] = tk.fillna(b.ticker)
    return b, masks(b.cat, ok, b.roic, b.growth)


def main():
    pc = lambda v: '—' if pd.isna(v) else f'{v:.0%}'
    f1 = lambda v: '—' if pd.isna(v) else f'{v:.0f}'
    out = ['# Carteiras de hoje por classe (EUA e Brasil)\n', '> ⚠️ **O ROIC pode estar errado** — ele decide quem entra na classe, quem é High ROIC e o P/E justo (logo o retorno esperado e a ordem).\n',
           'Regra: dentro de cada classe, P/L ≥ 4; as 20 de maior retorno esperado (menos, se a classe tiver menos); peso pela raiz do valor de mercado, teto de 10%. '
           'Sem cíclicos e vestuário. Dados da última data trimestral; preços daquela data.\n']
    rows = []
    for pais, fn in (('EUA', us), ('Brasil', br)):
        c, M = fn()
        out.append(f'\n# {pais} — {pd.Timestamp(c.date.max()):%d/%m/%Y}\n')
        for k, m in M.items():
            x = top(c[m.fillna(False).values])
            out += [f'\n## {k}: {len(x)} ações (classe tem {int(m.sum())}; P/L < 4 fora: {int((c[m.fillna(False).values].pe < 4).sum())})\n',
                    '| # | Ação | Empresa | Setor | Peso | Retorno esperado | ROIC | Cresc. EPS | P/L | P/E justo |', '|---|---|---|---|---|---|---|---|---|---|']
            for i, r in enumerate(x.itertuples(), 1):
                out.append(f'| {i} | {r.ticker.replace(".SA", "")} | {r.nome} | {r.setor} | **{f'{r.peso:.1%}'.replace('.', ',')}** | {pc(r.ret)} | {pc(r.roic)} | {pc(r.growth)} | {f1(r.pe)} | {f1(r.fair_pe)} |')
                rows.append(dict(pais=pais, classe=k, pos=i, ticker=r.ticker, empresa=r.nome, setor=r.setor, peso=r.peso, ret=r.ret, roic=r.roic, growth=r.growth, pe=r.pe, fair_pe=r.fair_pe))
    (ROOT / 'hoje_classes.md').write_text('\n'.join(out)); pd.DataFrame(rows).to_csv(ROOT / 'hoje_classes.csv', index=False); print('\n'.join(out))


if __name__ == '__main__':
    main()
