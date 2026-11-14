"""Conferencia do ROIC triangulado contra o oficial (etapa 2, antes do backtest). Saida: backtest/roic3_relatorio.md e .csv"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import benchmarks as bm  # noqa: E402
import top_n  # noqa: E402
from backtest import D  # noqa: E402

pc = lambda v: '—' if v is None or pd.isna(v) else f'{v:.0%}'
OOL, GCGR = bm.OOL, bm.GCGR


def with_tri(f, r3):
    m = f.merge(r3[['date', 'ticker', 'roic_tri']], on=['date', 'ticker'], how='left')
    m['roic_oficial'] = m.roic
    m['roic'] = np.where(m.fin, m.roic, m.roic_tri)
    return m


def top20(c):
    el = c[~c.excluded & (c.roic >= .12) & (c.growth >= .15) & c.roic.notna() & c.growth.notna()].copy()
    el['pe'] = el.price / el.eps.where(el.eps > 0); el = el[el.pe >= 4]
    return el.sort_values(['ret', 'roic'], ascending=False).head(20)


def main():
    f, dates = bm.base_data(); r3 = pd.read_csv(D / 'roic3.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    m = with_tri(f, r3)
    op = m[~m.fin]
    last = m.date.max()
    c_off = bm.classify_new(f); c_tri = bm.classify_new(m.drop(columns=['roic_tri', 'roic_oficial']))
    lo, lt = c_off[c_off.date == last], c_tri[c_tri.date == last]
    out = ['# ROIC triangulado — conferência contra o oficial (antes do backtest)\n',
           '> ⚠️ **O ROIC pode estar errado** — esta é a revisão. Financeiras e seguradoras de saúde continuam com ROE e ficam fora das comparações.\n',
           '## 1. Visão geral (empresas operacionais do S&P 500, todas as datas 2011–2026)\n',
           '| | Oficial (antigo) | Triangulado (novo) |', '|---|---|---|',
           f"| Mediana | {pc(op.roic_oficial.median())} | {pc(op.roic_tri.median())} |",
           f"| Acima de 100% | {(op.roic_oficial > 1).mean():.1%} | {(op.roic_tri > 1).mean():.1%} |".replace('.', ','),
           f"| Sem valor | {op.roic_oficial.isna().mean():.1%} | {op.roic_tri.isna().mean():.1%} |".replace('.', ','),
           f"| Passam no corte de 12% | {(op.roic_oficial >= .12).mean():.0%} | {(op.roic_tri >= .12).mean():.0%} |",
           '', f"Mudaram de lado no corte de 12%: {(((op.roic_oficial >= .12) != (op.roic_tri >= .12)) & op.roic_tri.notna() & op.roic_oficial.notna()).mean():.1%} das observações "
           f"(entram: {((op.roic_oficial < .12) & (op.roic_tri >= .12)).sum()}, saem: {((op.roic_oficial >= .12) & (op.roic_tri < .12)).sum()}).".replace('.', ',', 1), '']
    rr = r3[r3.ticker.isin(op.ticker.unique())]
    out += ['**Regra de combinação usada (todas as datas):** ' + ', '.join(f'{k} {v:.0%}' for k, v in rr.regra.value_counts(normalize=True).items()),
            f"\n**Alerta de qualidade caindo (marginal < 12% com pouco reinvestimento):** {rr.alerta_qualidade.mean():.1%} das observações.".replace('.', ',', 1)]
    # 2. classes hoje
    def cls(c):
        return {OOL: set(c[(c.cat == OOL) & ~c.excluded].ticker), GCGR: set(c[(c.cat == GCGR) & ~c.excluded].ticker)}
    a, b = cls(lo), cls(lt); ta, tb = set(top20(lo).ticker), set(top20(lt).ticker)
    nm = lambda t: f"{t} ({str(u.name.get(t, t))[:22]})"
    out += ['', f'## 2. O que muda hoje ({last:%m/%Y})\n', '| Grupo | Antes | Depois | Saem | Entram |', '|---|---|---|---|---|']
    for k, x, y in (('Opportunity of Lifetime', a[OOL], b[OOL]), ('Good Companies, Great Returns', a[GCGR], b[GCGR]), ('**Top 20 da estratégia**', ta, tb)):
        out.append(f"| {k} | {len(x)} | {len(y)} | {', '.join(nm(t) for t in sorted(x - y)) or '—'} | {', '.join(nm(t) for t in sorted(y - x)) or '—'} |")
    # 3. empresa por empresa
    h = pd.read_csv(ROOT / 'hoje_classes.csv'); h = h[h.pais == 'EUA']
    lr = r3[r3.date == last].set_index('ticker'); lf = m[m.date == last].set_index('ticker')
    famous = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'COST', 'WMT', 'HD', 'MCD', 'KO', 'PEP', 'V', 'MA', 'LLY', 'UNH', 'XOM', 'CVX', 'CAT', 'DE',
              'ORCL', 'ADBE', 'CRM', 'INTU', 'TXN', 'AVGO', 'NFLX', 'BKNG', 'CMCSA', 'CMG', 'AZO', 'ORLY', 'DPZ', 'OTIS', 'FTNT', 'MO', 'PM', 'LULU', 'NKE', 'SBUX']
    tks = list(dict.fromkeys(list(h.ticker) + famous + list((lf[~lf.fin].roic_oficial - lf[~lf.fin].roic_tri).abs().sort_values(ascending=False).head(15).index)))
    rows = []
    for t in tks:
        if t not in lf.index or t not in lr.index or lf.loc[t].fin: continue
        x, y = lr.loc[t], lf.loc[t]
        rows.append(dict(ticker=t, empresa=str(u.name.get(t, t))[:28], setor=str(u.industry.get(t, ''))[:30], na_carteira=t in set(h.ticker), oficial=y.roic_oficial,
                         ativo=x.roic_ativo, passivo=x.roic_passivo, marginal=x.roic_marg, triangulado=x.roic_tri, regra=x.regra, alerta=x.alerta_qualidade))
    R = pd.DataFrame(rows).drop_duplicates('ticker'); R['dif'] = R.triangulado - R.oficial; R.to_csv(ROOT / 'roic3_relatorio.csv', index=False)
    out += ['', '## 3. Empresa por empresa (exercício mais recente, resumo de 6 anos)\n',
            'Carteiras de hoje, empresas conhecidas e as 15 maiores diferenças. "Corte" = muda de lado nos 12%.\n',
            '| Ação | Empresa | Setor | Carteira | Oficial (antigo) | Ativo | Passivo | Marginal | **Triangulado** | Regra | Alerta |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in R.sort_values('triangulado', ascending=False).itertuples():
        cut = ' ⚠️ corte' if (pd.notna(r.oficial) and pd.notna(r.triangulado) and ((r.oficial >= .12) != (r.triangulado >= .12))) else ''
        out.append(f"| {r.ticker} | {r.empresa} | {r.setor} | {'sim' if r.na_carteira else ''} | {pc(r.oficial)} | {pc(r.ativo)} | {pc(r.passivo)} | {pc(r.marginal)} | **{pc(r.triangulado)}**{cut} | {r.regra} | {'qualidade caindo' if r.alerta else ''} |")
    (ROOT / 'roic3_relatorio.md').write_text('\n'.join(out)); print('\n'.join(out[:40]))


if __name__ == '__main__':
    main()
