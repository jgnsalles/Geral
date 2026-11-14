"""Giro historico da estrategia candidata congelada (Top 20, P/L >= 4, raiz com teto de 10%, trimestral): EUA e Brasil.
Conta compras (nomes que entram), vendas (nomes que saem) e giro de peso (soma de |delta peso| / 2, com pesos-alvo). Saida: backtest/giro.md"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / 'mundo'))
import backtest_mundo as bmu  # noqa: E402
import top_n  # noqa: E402


def stats_giro(el):
    W = {}
    for d, g in el.groupby('date'):
        ch = g.sort_values(['ret', 'roic'], ascending=False).head(20)
        W[d] = top_n.cap(pd.Series(np.sqrt(ch.mcap.values), index=ch.ticker), .10)
    ds = sorted(W); rows = []
    for a, b in zip(ds[:-1], ds[1:]):
        A, B = set(W[a].index), set(W[b].index)
        dw = W[b].reindex(A | B, fill_value=0) - W[a].reindex(A | B, fill_value=0)
        rows.append(dict(date=b, compras=len(B - A), vendas=len(A - B), ajustes=len(A & B), giro=dw.abs().sum() / 2, n=len(B)))
    r = pd.DataFrame(rows); r['ano'] = pd.to_datetime(r.date).dt.year
    held = []  # tempo de permanencia (trimestres seguidos)
    for t in set().union(*[set(w.index) for w in W.values()]):
        run = 0
        for d in ds:
            if t in W[d].index: run += 1
            elif run: held.append(run); run = 0
        if run: held.append(run)
    return r, np.array(held)


def main():
    import yfinance as yf
    sp, _, _ = bmu.us_sp()
    fx = yf.download('BRL=X', start='2010-01-01', progress=False, auto_adjust=True)['Close'].squeeze(); fx.index = pd.to_datetime(fx.index).tz_localize(None)
    br, _ = bmu.brasil(fx)
    out = ['# Giro da estratégia candidata (Top 20, trimestral)\n', '> ⚠️ **O ROIC pode estar errado** — ele decide quem é elegível e a ordem; um ROIC que oscila gera trocas.\n',
           'Compras = ações que entram; vendas = ações que saem (cada troca completa = 1 compra + 1 venda). Ajustes de peso das que ficam não contam como trade aqui, '
           'mas entram no giro de peso (soma de |variação de peso| ÷ 2 nos pesos-alvo).\n']
    for lab, x in (('EUA', sp), ('Brasil', br)):
        el = x[x.elig.fillna(False).astype(bool) & x.ret.notna() & x.mcap.notna()]
        r, h = stats_giro(el)
        y = r.groupby('ano').agg(compras=('compras', 'sum'), vendas=('vendas', 'sum'), giro=('giro', 'sum'), n=('n', 'mean'), rebal=('date', 'size'))
        y = y[y.rebal >= 4]
        out += [f'\n## {lab}\n', '| Ano | Compras | Vendas | Trades (compras + vendas) | Giro de peso no ano | Ações (média) |', '|---|---|---|---|---|---|']
        out += [f'| {a} | {v.compras} | {v.vendas} | {v.compras + v.vendas} | {v.giro:.0%} | {v.n:.0f} |' for a, v in y.iterrows()]
        out += [f'| **Média por ano** | **{y.compras.mean():.0f}** | **{y.vendas.mean():.0f}** | **{(y.compras + y.vendas).mean():.0f}** | **{y.giro.mean():.0%}** | {y.n.mean():.0f} |',
                '', f'Por trimestre (média): {r.compras.mean():.1f} entram e {r.vendas.mean():.1f} saem. Tempo médio de permanência: {h.mean() * 3:.0f} meses '
                f'(mediana {np.median(h) * 3:.0f}); {np.mean(h == 1):.0%} das passagens duram só 1 trimestre.']
    (ROOT / 'giro.md').write_text('\n'.join(out)); print('\n'.join(out))


if __name__ == '__main__':
    main()
